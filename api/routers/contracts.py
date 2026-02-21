# api/routers/contracts.py
"""
Endpoint Contratti — CRUD con Bouncer Pattern + Relational IDOR.

Sicurezza multi-tenant:
- trainer_id diretto su contratti (aggiunto via migration)
- Relational IDOR: su POST, verifica che id_cliente appartenga al trainer
- trainer_id iniettato dal JWT, mai dal body (Mass Assignment prevention)

Regola 404: se il contratto non esiste O non appartiene al trainer -> 404.
Mai 403, mai rivelare l'esistenza di dati altrui.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.contract import Contract
from api.models.rate import Rate
from api.schemas.financial import (
    ContractCreate, ContractUpdate,
    ContractResponse, ContractWithRatesResponse, RateResponse,
)

router = APIRouter(prefix="/contracts", tags=["contracts"])


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _to_response(contract: Contract) -> ContractResponse:
    """Converte un Contract ORM in ContractResponse."""
    return ContractResponse.model_validate(contract)


def _to_response_with_rates(contract: Contract, rates: list[Rate]) -> ContractWithRatesResponse:
    """Converte Contract + Rate in ContractWithRatesResponse."""
    return ContractWithRatesResponse(
        **ContractResponse.model_validate(contract).model_dump(),
        rate=[RateResponse.model_validate(r) for r in rates],
    )


def _check_client_ownership(session: Session, client_id: int, trainer_id: int) -> None:
    """
    Relational IDOR: verifica che il cliente appartenga al trainer.
    Se non trovato -> 404 (mai 403).
    """
    client = session.exec(
        select(Client).where(Client.id == client_id, Client.trainer_id == trainer_id)
    ).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente non trovato",
        )


# ════════════════════════════════════════════════════════════
# GET: Lista contratti
# ════════════════════════════════════════════════════════════

@router.get("", response_model=dict)
def list_contracts(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    id_cliente: Optional[int] = Query(default=None, description="Filtra per cliente"),
    chiuso: Optional[bool] = Query(default=None, description="Filtra per stato chiuso"),
):
    """Lista contratti del trainer autenticato con paginazione e filtri."""
    query = select(Contract).where(Contract.trainer_id == trainer.id)

    if id_cliente is not None:
        query = query.where(Contract.id_cliente == id_cliente)
    if chiuso is not None:
        query = query.where(Contract.chiuso == chiuso)

    # Count totale
    count_q = select(func.count(Contract.id)).where(Contract.trainer_id == trainer.id)
    if id_cliente is not None:
        count_q = count_q.where(Contract.id_cliente == id_cliente)
    if chiuso is not None:
        count_q = count_q.where(Contract.chiuso == chiuso)
    total = session.exec(count_q).one()

    # Paginazione
    offset = (page - 1) * page_size
    query = query.order_by(Contract.data_vendita.desc()).offset(offset).limit(page_size)
    contracts = session.exec(query).all()

    return {
        "items": [_to_response(c) for c in contracts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ════════════════════════════════════════════════════════════
# GET: Dettaglio contratto (con rate embedded)
# ════════════════════════════════════════════════════════════

@router.get("/{contract_id}", response_model=ContractWithRatesResponse)
def get_contract(
    contract_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Dettaglio contratto con rate.

    Bouncer: query singola contract.id + trainer_id.
    """
    contract = session.exec(
        select(Contract).where(Contract.id == contract_id, Contract.trainer_id == trainer.id)
    ).first()

    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")

    # Fetch rate associate
    rates = list(session.exec(
        select(Rate).where(Rate.id_contratto == contract_id).order_by(Rate.data_scadenza)
    ).all())

    return _to_response_with_rates(contract, rates)


# ════════════════════════════════════════════════════════════
# POST: Crea contratto
# ════════════════════════════════════════════════════════════

@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    data: ContractCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Crea un nuovo contratto.

    Bouncer chain:
    1. Relational IDOR: verifica che id_cliente appartenga al trainer
    2. Iniezione sicura trainer_id dal JWT
    """
    # 1. Relational IDOR — il cliente deve appartenere a questo trainer
    _check_client_ownership(session, data.id_cliente, trainer.id)

    # 2. Crea contratto con trainer_id iniettato
    contract = Contract(
        trainer_id=trainer.id,
        id_cliente=data.id_cliente,
        tipo_pacchetto=data.tipo_pacchetto,
        crediti_totali=data.crediti_totali,
        prezzo_totale=data.prezzo_totale,
        data_inizio=data.data_inizio,
        data_scadenza=data.data_scadenza,
        totale_versato=data.acconto,
        stato_pagamento="PENDENTE",
        note=data.note,
    )
    session.add(contract)
    session.commit()
    session.refresh(contract)

    return _to_response(contract)


# ════════════════════════════════════════════════════════════
# PUT: Aggiorna contratto (partial update)
# ════════════════════════════════════════════════════════════

@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    data: ContractUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Aggiorna un contratto esistente (partial update).

    Bouncer: query singola contract.id + trainer_id.
    Campi protetti: trainer_id, id_cliente, crediti_usati, totale_versato, chiuso.
    """
    contract = session.exec(
        select(Contract).where(Contract.id == contract_id, Contract.trainer_id == trainer.id)
    ).first()

    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")

    # Partial update
    update_data = data.model_dump(exclude_unset=True)

    # Cross-field validation: se entrambe le date sono fornite, verifica ordine
    new_inizio = update_data.get("data_inizio", contract.data_inizio)
    new_scadenza = update_data.get("data_scadenza", contract.data_scadenza)
    if new_inizio and new_scadenza and new_scadenza <= new_inizio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="data_scadenza deve essere dopo data_inizio",
        )

    for field, value in update_data.items():
        setattr(contract, field, value)

    session.add(contract)
    session.commit()
    session.refresh(contract)

    return _to_response(contract)


# ════════════════════════════════════════════════════════════
# DELETE: Elimina contratto
# ════════════════════════════════════════════════════════════

@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Elimina contratto e rate associate.

    Bouncer: query singola contract.id + trainer_id.
    CASCADE: elimina anche le rate associate.
    """
    contract = session.exec(
        select(Contract).where(Contract.id == contract_id, Contract.trainer_id == trainer.id)
    ).first()

    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")

    # Elimina rate associate prima del contratto
    rates = session.exec(select(Rate).where(Rate.id_contratto == contract_id)).all()
    for rate in rates:
        session.delete(rate)

    session.delete(contract)
    session.commit()
