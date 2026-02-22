# api/routers/rates.py
"""
Endpoint Rate — CRUD con Deep Relational IDOR + Pagamento Atomico.

Sicurezza — Deep Relational IDOR:
  Ogni operazione su una Rata verifica l'ownership attraverso la catena:
    Rate.id_contratto -> Contract.trainer_id == current_trainer.id

  Implementazione: JOIN esplicita nella query SQL.
  Se la query non restituisce nulla -> 404 (mai 403).

Pagamento Atomico (POST /api/rates/{id}/pay):
  Operazione transazionale in 6 passi:
  A) Deep IDOR check
  B) Verifica rata non gia' SALDATA
  C) Aggiorna importo_saldato e stato rata
  D) Aggiorna totale_versato contratto (incrementale, preserva acconto)
  E) Se totale_versato >= prezzo_totale -> stato_pagamento = SALDATO
  E-bis) Registra CashMovement ENTRATA nel libro mastro
  F) session.commit() SOLO alla fine (rollback automatico su eccezione)
"""

from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.contract import Contract
from api.models.rate import Rate
from api.models.movement import CashMovement
from api.schemas.financial import (
    RateCreate, RateUpdate, RatePayment,
    RateResponse, PaymentPlanCreate,
)
from api.routers._audit import log_audit

# Categorie movimento cassa (allineate a ContractRepository)
CATEGORIA_PAGAMENTO_RATA = "PAGAMENTO_RATA"

router = APIRouter(prefix="/rates", tags=["rates"])


# ════════════════════════════════════════════════════════════
# HELPERS — Deep Relational IDOR
# ════════════════════════════════════════════════════════════

def _bouncer_rate(session: Session, rate_id: int, trainer_id: int) -> Rate:
    """
    Deep Relational IDOR: Rate -> Contract -> trainer_id.

    JOIN esplicita: una sola query per verificare ownership.
    Se non trovata -> HTTPException 404.
    """
    rate = session.exec(
        select(Rate)
        .join(Contract, Rate.id_contratto == Contract.id)
        .where(Rate.id == rate_id, Contract.trainer_id == trainer_id, Rate.deleted_at == None)
    ).first()

    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rata non trovata")

    return rate


def _bouncer_contract(session: Session, contract_id: int, trainer_id: int) -> Contract:
    """
    Bouncer diretto su Contract: verifica trainer_id.
    Usato per operazioni che partono dal contratto (POST rata, genera piano).
    """
    contract = session.exec(
        select(Contract).where(
            Contract.id == contract_id, Contract.trainer_id == trainer_id, Contract.deleted_at == None
        )
    ).first()

    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")

    return contract


# ════════════════════════════════════════════════════════════
# GET: Lista rate per contratto
# ════════════════════════════════════════════════════════════

@router.get("", response_model=dict)
def list_rates(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    id_contratto: int = Query(..., description="ID contratto (obbligatorio)"),
    stato: Optional[str] = Query(default=None, description="Filtra per stato (PENDENTE, PARZIALE, SALDATA)"),
):
    """
    Lista rate di un contratto.

    Bouncer: verifica che il contratto appartenga al trainer.
    """
    # Bouncer sul contratto
    _bouncer_contract(session, id_contratto, trainer.id)

    # Fetch rate
    query = select(Rate).where(Rate.id_contratto == id_contratto, Rate.deleted_at == None)
    if stato:
        query = query.where(Rate.stato == stato)
    query = query.order_by(Rate.data_scadenza)

    rates = session.exec(query).all()

    return {
        "items": [RateResponse.model_validate(r) for r in rates],
        "total": len(rates),
    }


# ════════════════════════════════════════════════════════════
# GET: Dettaglio singola rata
# ════════════════════════════════════════════════════════════

@router.get("/{rate_id}", response_model=RateResponse)
def get_rate(
    rate_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Dettaglio rata.

    Deep Relational IDOR: Rate -> Contract -> trainer_id via JOIN.
    """
    rate = _bouncer_rate(session, rate_id, trainer.id)
    return RateResponse.model_validate(rate)


# ════════════════════════════════════════════════════════════
# POST: Crea rata manuale
# ════════════════════════════════════════════════════════════

@router.post("", response_model=RateResponse, status_code=status.HTTP_201_CREATED)
def create_rate(
    data: RateCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Crea rata manuale per un contratto.

    Bouncer: verifica che il contratto appartenga al trainer.
    """
    # Bouncer sul contratto
    _bouncer_contract(session, data.id_contratto, trainer.id)

    rate = Rate(
        id_contratto=data.id_contratto,
        data_scadenza=data.data_scadenza,
        importo_previsto=data.importo_previsto,
        descrizione=data.descrizione,
    )
    session.add(rate)
    session.flush()
    log_audit(session, "rate", rate.id, "CREATE", trainer.id)
    session.commit()
    session.refresh(rate)

    return RateResponse.model_validate(rate)


# ════════════════════════════════════════════════════════════
# PUT: Aggiorna rata (solo PENDENTI)
# ════════════════════════════════════════════════════════════

@router.put("/{rate_id}", response_model=RateResponse)
def update_rate(
    rate_id: int,
    data: RateUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Aggiorna una rata (partial update, solo rate PENDENTI).

    Deep Relational IDOR + business rule: rate SALDATE sono immutabili.
    """
    rate = _bouncer_rate(session, rate_id, trainer.id)

    # Business rule: rate gia' saldate non si modificano
    if rate.stato == "SALDATA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile modificare una rata gia' saldata",
        )

    update_data = data.model_dump(exclude_unset=True)
    changes = {}
    for field, value in update_data.items():
        old_val = getattr(rate, field)
        setattr(rate, field, value)
        if value != old_val:
            changes[field] = {"old": old_val, "new": value}

    log_audit(session, "rate", rate.id, "UPDATE", trainer.id, changes or None)
    session.add(rate)
    session.commit()
    session.refresh(rate)

    return RateResponse.model_validate(rate)


# ════════════════════════════════════════════════════════════
# DELETE: Elimina rata (solo PENDENTI)
# ════════════════════════════════════════════════════════════

@router.delete("/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rate(
    rate_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Elimina una rata.

    Deep Relational IDOR + business rule: rate SALDATE non si eliminano.
    """
    rate = _bouncer_rate(session, rate_id, trainer.id)

    if rate.stato == "SALDATA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile eliminare una rata gia' saldata",
        )

    rate.deleted_at = datetime.utcnow()
    session.add(rate)
    log_audit(session, "rate", rate.id, "DELETE", trainer.id)
    session.commit()


# ════════════════════════════════════════════════════════════
# POST /{id}/pay — PAGAMENTO ATOMICO (Unit of Work)
# ════════════════════════════════════════════════════════════

@router.post("/{rate_id}/pay", response_model=RateResponse)
def pay_rate(
    rate_id: int,
    data: RatePayment,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Pagamento rata — Operazione atomica transazionale.

    Step:
    A) Deep IDOR: verifica Rate -> Contract -> trainer_id
    B) Business rule: rata gia' SALDATA -> 400
    C) Aggiorna importo_saldato e stato rata
    D) Ricalcola totale_versato contratto (somma importo_saldato di TUTTE le rate)
    E) Se totale_versato >= prezzo_totale -> stato_pagamento = SALDATO
    F) session.commit() SOLO qui (atomicita')

    Rollback automatico: se qualsiasi step solleva eccezione,
    FastAPI chiude la session senza commit -> nessuna modifica salvata.
    """
    # A) Deep Relational IDOR
    rate = _bouncer_rate(session, rate_id, trainer.id)

    # B) Rata gia' saldata?
    if rate.stato == "SALDATA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rata gia' saldata",
        )

    # C) Aggiorna rata (cattura old values per audit)
    old_importo_saldato = rate.importo_saldato
    old_stato = rate.stato
    rate.importo_saldato = rate.importo_saldato + data.importo

    # Stato: SALDATA se pagato >= previsto (tolleranza 0.01€), altrimenti PARZIALE
    if rate.importo_saldato >= rate.importo_previsto - 0.01:
        rate.stato = "SALDATA"
    else:
        rate.stato = "PARZIALE"

    session.add(rate)

    # D) Aggiorna totale_versato contratto (incrementale)
    #    Approccio incrementale: totale_versato += importo pagato.
    #    Questo preserva l'acconto iniziale (gia' nel totale_versato alla creazione).
    contract = session.get(Contract, rate.id_contratto)
    contract.totale_versato = contract.totale_versato + data.importo

    # E) Stato contratto: SALDATO se totale pagato copre il prezzo
    if contract.prezzo_totale and contract.totale_versato >= contract.prezzo_totale - 0.01:
        contract.stato_pagamento = "SALDATO"
    elif contract.totale_versato > 0:
        contract.stato_pagamento = "PARZIALE"

    session.add(contract)

    # E-bis) Registra nel libro mastro (CashMovement ENTRATA)
    # Nome cliente per descrizione contestuale nel Libro Mastro
    client = session.get(Client, contract.id_cliente)
    client_label = f"{client.nome} {client.cognome}" if client else f"Cliente #{contract.id_cliente}"

    movement = CashMovement(
        trainer_id=trainer.id,
        data_effettiva=data.data_pagamento,
        tipo="ENTRATA",
        categoria=CATEGORIA_PAGAMENTO_RATA,
        importo=data.importo,
        metodo=data.metodo,
        id_cliente=contract.id_cliente,
        id_contratto=contract.id,
        id_rata=rate.id,
        note=data.note or f"Pagamento Rata - {client_label}",
    )
    session.add(movement)

    # F) Audit + Commit atomico — tutto o niente
    log_audit(session, "rate", rate.id, "UPDATE", trainer.id, {
        "importo_saldato": {"old": old_importo_saldato, "new": rate.importo_saldato},
        "stato": {"old": old_stato, "new": rate.stato},
    })
    session.commit()
    session.refresh(rate)

    return RateResponse.model_validate(rate)


# ════════════════════════════════════════════════════════════
# POST /{id}/unpay — REVOCA PAGAMENTO (Unit of Work inversa)
# ════════════════════════════════════════════════════════════

@router.post("/{rate_id}/unpay", response_model=RateResponse)
def unpay_rate(
    rate_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Revoca pagamento rata — Operazione atomica inversa.

    Step:
    A) Deep IDOR: verifica Rate -> Contract -> trainer_id
    B) Business rule: rata PENDENTE (nulla da stornare) -> 400
    C) Riporta rata a PENDENTE, azzera importo_saldato
    D) Sottrai importo dal totale_versato contratto
    E) Ricalcola stato_pagamento contratto
    F) Trova ed elimina i CashMovement associati (id_rata + tipo=ENTRATA)
    G) session.commit() SOLO qui (atomicita')
    """
    # A) Deep Relational IDOR
    rate = _bouncer_rate(session, rate_id, trainer.id)

    # B) Nulla da stornare se importo_saldato == 0
    if rate.importo_saldato <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nessun pagamento da revocare su questa rata",
        )

    # C) Riporta rata a PENDENTE (cattura old values per audit)
    old_importo_saldato = rate.importo_saldato
    old_stato = rate.stato
    importo_da_stornare = rate.importo_saldato
    rate.importo_saldato = 0
    rate.stato = "PENDENTE"
    session.add(rate)

    # D) Aggiorna totale_versato contratto
    contract = session.get(Contract, rate.id_contratto)
    contract.totale_versato = max(0, contract.totale_versato - importo_da_stornare)

    # E) Ricalcola stato_pagamento
    if contract.totale_versato <= 0:
        contract.stato_pagamento = "PENDENTE"
    elif contract.prezzo_totale and contract.totale_versato >= contract.prezzo_totale - 0.01:
        contract.stato_pagamento = "SALDATO"
    else:
        contract.stato_pagamento = "PARZIALE"
    session.add(contract)

    # F) Soft-delete TUTTI i CashMovement associati (puo' averne piu' di uno
    #    se la rata ha ricevuto pagamenti parziali multipli)
    now = datetime.utcnow()
    movements = session.exec(
        select(CashMovement).where(
            CashMovement.id_rata == rate_id,
            CashMovement.tipo == "ENTRATA",
            CashMovement.trainer_id == trainer.id,
            CashMovement.deleted_at == None,
        )
    ).all()
    for movement in movements:
        movement.deleted_at = now
        session.add(movement)
        log_audit(session, "movement", movement.id, "DELETE", trainer.id)

    # G) Audit + Commit atomico
    log_audit(session, "rate", rate.id, "UPDATE", trainer.id, {
        "importo_saldato": {"old": old_importo_saldato, "new": 0},
        "stato": {"old": old_stato, "new": "PENDENTE"},
    })
    session.commit()
    session.refresh(rate)

    return RateResponse.model_validate(rate)


# ════════════════════════════════════════════════════════════
# POST /contracts/{id}/payment-plan — Genera piano rate
# ════════════════════════════════════════════════════════════

@router.post("/generate-plan/{contract_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
def generate_payment_plan(
    contract_id: int,
    data: PaymentPlanCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Genera piano rate automatico per un contratto.

    Bouncer: verifica che il contratto appartenga al trainer.
    Elimina rate PENDENTI esistenti, mantiene SALDATE.
    """
    from dateutil.relativedelta import relativedelta

    # Bouncer sul contratto
    contract = _bouncer_contract(session, contract_id, trainer.id)

    # Validazione: importo_da_rateizzare deve corrispondere al residuo reale
    # totale_versato e' la fonte di verita' (include acconto + rate + pagamenti legacy)
    residuo_atteso = round(max(0, (contract.prezzo_totale or 0) - (contract.totale_versato or 0)), 2)

    if abs(data.importo_da_rateizzare - residuo_atteso) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"importo_da_rateizzare ({data.importo_da_rateizzare:.2f}) "
                f"non corrisponde al residuo ({residuo_atteso:.2f}). "
                f"Formula: prezzo_totale ({contract.prezzo_totale}) "
                f"- totale_versato ({contract.totale_versato})"
            ),
        )

    # Soft-delete rate PENDENTI esistenti
    now = datetime.utcnow()
    pending_rates = session.exec(
        select(Rate).where(
            Rate.id_contratto == contract_id, Rate.stato == "PENDENTE", Rate.deleted_at == None
        )
    ).all()
    for r in pending_rates:
        r.deleted_at = now
        session.add(r)
        log_audit(session, "rate", r.id, "DELETE", trainer.id)

    # Genera nuove rate — aritmetica corretta per evitare il centesimo perduto
    # Es: 100€ / 3 rate -> 33.34 + 33.33 + 33.33 = 100.00
    base_amount = round(data.importo_da_rateizzare / data.numero_rate, 2)
    remainder = round(data.importo_da_rateizzare - (base_amount * data.numero_rate), 2)
    created = []

    for i in range(data.numero_rate):
        if data.frequenza == "MENSILE":
            due_date = data.data_prima_rata + relativedelta(months=i)
        elif data.frequenza == "SETTIMANALE":
            due_date = data.data_prima_rata + relativedelta(weeks=i)
        elif data.frequenza == "TRIMESTRALE":
            due_date = data.data_prima_rata + relativedelta(months=i * 3)
        else:
            due_date = data.data_prima_rata + relativedelta(months=i)

        # Il resto va sulla prima rata
        amount = base_amount + remainder if i == 0 else base_amount

        rate = Rate(
            id_contratto=contract_id,
            data_scadenza=due_date,
            importo_previsto=amount,
            descrizione=f"Rata {i + 1}/{data.numero_rate}",
        )
        session.add(rate)
        created.append(rate)

    session.flush()
    for r in created:
        log_audit(session, "rate", r.id, "CREATE", trainer.id)
    session.commit()

    # Refresh per avere gli ID
    for r in created:
        session.refresh(r)

    return {
        "items": [RateResponse.model_validate(r) for r in created],
        "total": len(created),
        "contract_id": contract_id,
    }
