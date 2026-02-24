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
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.contract import Contract
from api.models.rate import Rate
from api.models.movement import CashMovement
from api.models.event import Event
from api.schemas.financial import (
    ContractCreate, ContractUpdate,
    ContractResponse, ContractListResponse, ContractWithRatesResponse,
    RateResponse, RatePaymentReceipt,
)
from api.routers._audit import log_audit

# Categoria movimento cassa per acconto (allineata a ContractRepository)
CATEGORIA_ACCONTO = "ACCONTO_CONTRATTO"

router = APIRouter(prefix="/contracts", tags=["contracts"])


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _to_response(contract: Contract) -> ContractResponse:
    """Converte un Contract ORM in ContractResponse."""
    return ContractResponse.model_validate(contract)


def _to_response_with_rates(
    contract: Contract,
    rates: list[Rate],
    receipt_map: dict[int, list[CashMovement]] | None = None,
    credit_breakdown: dict[str, int] | None = None,
) -> ContractWithRatesResponse:
    """
    Converte Contract + Rate in ContractWithRatesResponse con KPI computati.

    Unica fonte di verita' per tutti i valori finanziari.
    Il frontend legge i campi, non calcola nulla.

    receipt_map: {rate_id: [CashMovement, ...]} — storico pagamenti per ogni rata,
    ordinato cronologicamente (piu' vecchio prima).
    """
    today = date.today()

    # ── Enrich rate con campi computati ──
    enriched_rates = []
    somma_saldate = 0.0
    somma_pendenti = 0.0
    somma_tutte = 0.0
    n_pagate = 0
    n_scadute = 0

    for r in rates:
        rate_data = RateResponse.model_validate(r).model_dump()

        # Storico pagamenti (tutti i CashMovement di questa rata)
        movements = receipt_map.get(r.id, []) if receipt_map else []
        if movements:
            # Ultimo pagamento per backward-compat
            last = movements[-1]
            rate_data["data_pagamento"] = last.data_effettiva
            rate_data["metodo_pagamento"] = last.metodo
            # Lista completa cronologica
            rate_data["pagamenti"] = [
                RatePaymentReceipt(
                    id=m.id,
                    importo=m.importo,
                    metodo=m.metodo,
                    data_pagamento=m.data_effettiva,
                    note=m.note,
                ).model_dump()
                for m in movements
            ]

        # Campi computati per singola rata
        rate_data["importo_residuo"] = round(r.importo_previsto - r.importo_saldato, 2)
        is_scaduta = r.stato != "SALDATA" and r.data_scadenza < today
        rate_data["is_scaduta"] = is_scaduta
        rate_data["giorni_ritardo"] = max(0, (today - r.data_scadenza).days) if is_scaduta else 0

        enriched_rates.append(RateResponse(**rate_data))

        # Accumula aggregati
        somma_tutte += r.importo_previsto
        if r.stato == "SALDATA":
            somma_saldate += r.importo_previsto
            n_pagate += 1
        else:
            # Usa importo_residuo (previsto - saldato) per rate PARZIALI.
            # Es: previsto=400, saldato=100 → conta 300, non 400.
            somma_pendenti += r.importo_previsto - r.importo_saldato
        if is_scaduta:
            n_scadute += 1

    # ── KPI contratto ──
    prezzo = contract.prezzo_totale or 0
    versato = contract.totale_versato or 0
    acconto = contract.acconto or 0

    residuo = round(max(0, prezzo - versato), 2)
    percentuale = round((versato / prezzo) * 100) if prezzo > 0 else 0
    # totale_versato e' la fonte di verita' (include acconto + rate + pagamenti legacy)
    importo_da_rateizzare = residuo
    disallineamento = round(importo_da_rateizzare - somma_pendenti, 2)

    # ── Credit breakdown (computed on read) ──
    cb = credit_breakdown or {}
    programmate = cb.get("Programmato", 0)
    completate = cb.get("Completato", 0)
    rinviate = cb.get("Rinviato", 0)
    crediti_totali = contract.crediti_totali or 0
    crediti_usati_computed = programmate + completate + rinviate

    # Override crediti_usati nel dict base (sovrascrive il valore ORM = 0)
    contract_data = ContractResponse.model_validate(contract).model_dump()
    contract_data["crediti_usati"] = crediti_usati_computed

    return ContractWithRatesResponse(
        **contract_data,
        rate=enriched_rates,
        residuo=residuo,
        percentuale_versata=percentuale,
        importo_da_rateizzare=importo_da_rateizzare,
        somma_rate_previste=round(somma_tutte, 2),
        somma_rate_saldate=round(somma_saldate, 2),
        somma_rate_pendenti=round(somma_pendenti, 2),
        piano_allineato=abs(disallineamento) < 0.01,
        importo_disallineamento=disallineamento,
        rate_totali=len(rates),
        rate_pagate=n_pagate,
        rate_scadute=n_scadute,
        sedute_programmate=programmate,
        sedute_completate=completate,
        sedute_rinviate=rinviate,
        crediti_residui=max(0, crediti_totali - crediti_usati_computed),
    )


def _check_client_ownership(session: Session, client_id: int, trainer_id: int) -> None:
    """
    Relational IDOR: verifica che il cliente appartenga al trainer.
    Se non trovato -> 404 (mai 403).
    """
    client = session.exec(
        select(Client).where(
            Client.id == client_id, Client.trainer_id == trainer_id, Client.deleted_at == None
        )
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
    """
    Lista contratti enriched con KPI aggregati.

    3 query batch (zero N+1):
    1. Contratti (paginati + filtrati)
    2. Rate per quei contratti (batch IN)
    3. Clienti per quei contratti (batch IN)

    Response arricchita: nome cliente, conteggi rate, flag scaduti.
    """
    query = select(Contract).where(Contract.trainer_id == trainer.id, Contract.deleted_at == None)

    if id_cliente is not None:
        query = query.where(Contract.id_cliente == id_cliente)
    if chiuso is not None:
        query = query.where(Contract.chiuso == chiuso)

    # Count dalla stessa query base (zero duplicazione filtri)
    total = session.exec(
        select(func.count()).select_from(query.subquery())
    ).one()

    # Paginazione
    offset = (page - 1) * page_size
    query = query.order_by(Contract.data_vendita.desc()).offset(offset).limit(page_size)
    contracts = session.exec(query).all()

    # ── KPI aggregati (calcolati sull'intero set del trainer, pre-filtro) ──
    today = date.today()
    all_contracts_q = select(Contract).where(
        Contract.trainer_id == trainer.id, Contract.deleted_at == None
    )
    all_contracts = session.exec(all_contracts_q).all()

    kpi_attivi = sum(1 for c in all_contracts if not c.chiuso)
    kpi_chiusi = sum(1 for c in all_contracts if c.chiuso)
    kpi_fatturato = round(sum(c.prezzo_totale or 0 for c in all_contracts if not c.chiuso), 2)
    kpi_incassato = round(sum(c.totale_versato for c in all_contracts if not c.chiuso), 2)

    # Rate scadute: contratti attivi con almeno 1 rata scaduta non saldata
    active_ids = [c.id for c in all_contracts if not c.chiuso]
    kpi_rate_scadute = 0
    if active_ids:
        overdue_contracts = session.exec(
            select(func.count(func.distinct(Rate.id_contratto)))
            .where(
                Rate.id_contratto.in_(active_ids),
                Rate.deleted_at == None,
                Rate.stato != "SALDATA",
                Rate.data_scadenza < today,
            )
        ).one()
        kpi_rate_scadute = overdue_contracts or 0

    kpi_data = {
        "kpi_attivi": kpi_attivi,
        "kpi_chiusi": kpi_chiusi,
        "kpi_fatturato": kpi_fatturato,
        "kpi_incassato": kpi_incassato,
        "kpi_rate_scadute": kpi_rate_scadute,
    }

    if not contracts:
        return {"items": [], "total": total, "page": page, "page_size": page_size, **kpi_data}

    # ── Batch fetch: rate per tutti i contratti (1 query) ──
    contract_ids = [c.id for c in contracts]
    all_rates = session.exec(
        select(Rate).where(Rate.id_contratto.in_(contract_ids), Rate.deleted_at == None)
    ).all()

    rates_by_contract: dict[int, list[Rate]] = {}
    for r in all_rates:
        rates_by_contract.setdefault(r.id_contratto, []).append(r)

    # ── Batch fetch: clienti per tutti i contratti (1 query) ──
    client_ids = list({c.id_cliente for c in contracts})
    clients = session.exec(
        select(Client).where(Client.id.in_(client_ids))
    ).all()
    client_map = {c.id: c for c in clients}

    # ── Batch fetch: crediti usati per contratto (1 query, zero N+1) ──
    credit_rows = session.exec(
        select(Event.id_contratto, func.count(Event.id))
        .where(
            Event.id_contratto.in_(contract_ids),
            Event.categoria == "PT",
            Event.stato != "Cancellato",
            Event.deleted_at == None,
        )
        .group_by(Event.id_contratto)
    ).all()
    credits_used_map: dict[int, int] = {row[0]: int(row[1]) for row in credit_rows}

    # ── Build enriched responses ──
    results = []

    for contract in contracts:
        client = client_map.get(contract.id_cliente)
        rates = rates_by_contract.get(contract.id, [])

        # Override crediti_usati: computed on read (non dal valore ORM)
        contract_data = ContractResponse.model_validate(contract).model_dump()
        contract_data["crediti_usati"] = credits_used_map.get(contract.id, 0)

        results.append(ContractListResponse(
            **contract_data,
            client_nome=client.nome if client else "",
            client_cognome=client.cognome if client else "",
            rate_totali=len(rates),
            rate_pagate=sum(1 for r in rates if r.stato == "SALDATA"),
            ha_rate_scadute=any(
                r.data_scadenza < today and r.stato != "SALDATA"
                for r in rates
            ),
        ))

    return {
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
        **kpi_data,
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
        select(Contract).where(
            Contract.id == contract_id, Contract.trainer_id == trainer.id, Contract.deleted_at == None
        )
    ).first()

    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")

    # Fetch rate associate (non eliminate)
    rates = list(session.exec(
        select(Rate).where(
            Rate.id_contratto == contract_id, Rate.deleted_at == None
        ).order_by(Rate.data_scadenza)
    ).all())

    # Batch fetch storico pagamenti per TUTTE le rate con id_rata (1 query, zero N+1)
    rate_ids = [r.id for r in rates]
    receipt_map: dict[int, list[CashMovement]] = {}
    if rate_ids:
        movements = session.exec(
            select(CashMovement).where(
                CashMovement.id_rata.in_(rate_ids),
                CashMovement.tipo == "ENTRATA",
                CashMovement.trainer_id == trainer.id,
                CashMovement.deleted_at == None,
            ).order_by(CashMovement.data_effettiva.asc())
        ).all()
        for mov in movements:
            if mov.id_rata:
                receipt_map.setdefault(mov.id_rata, []).append(mov)

    # Credit breakdown: PT events GROUP BY stato (1 query)
    credit_breakdown: dict[str, int] = {}
    credit_rows = session.exec(
        select(Event.stato, func.count(Event.id))
        .where(
            Event.id_contratto == contract_id,
            Event.categoria == "PT",
            Event.stato != "Cancellato",
            Event.deleted_at == None,
        )
        .group_by(Event.stato)
    ).all()
    for row in credit_rows:
        credit_breakdown[row[0]] = int(row[1])

    return _to_response_with_rates(contract, rates, receipt_map, credit_breakdown)


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
        acconto=data.acconto,
        totale_versato=data.acconto,
        stato_pagamento="PENDENTE",
        note=data.note,
    )
    session.add(contract)

    # Flush per ottenere l'ID del contratto (necessario per il CashMovement)
    session.flush()

    # 3. Se acconto > 0, registra nel libro mastro (CashMovement ENTRATA)
    if data.acconto > 0:
        client = session.get(Client, data.id_cliente)
        client_label = f"{client.nome} {client.cognome}" if client else f"Cliente #{data.id_cliente}"

        movement = CashMovement(
            trainer_id=trainer.id,
            data_effettiva=data.data_inizio,
            tipo="ENTRATA",
            categoria=CATEGORIA_ACCONTO,
            importo=data.acconto,
            metodo=data.metodo_acconto,
            id_cliente=data.id_cliente,
            id_contratto=contract.id,
            note=f"Acconto Contratto - {client_label}",
        )
        session.add(movement)

    log_audit(session, "contract", contract.id, "CREATE", trainer.id)
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
    Campi protetti: trainer_id, id_cliente, crediti_usati, totale_versato.
    """
    contract = session.exec(
        select(Contract).where(
            Contract.id == contract_id, Contract.trainer_id == trainer.id, Contract.deleted_at == None
        )
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

    changes = {}
    for field, value in update_data.items():
        old_val = getattr(contract, field)
        setattr(contract, field, value)
        if value != old_val:
            changes[field] = {"old": old_val, "new": value}

    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, changes or None)
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
    Soft-delete contratto — per errori o contratti completati.

    Bouncer: contract.id + trainer_id + non eliminato.
    RESTRICT (obbligazioni pendenti):
    - Rate non saldate (PENDENTE/PARZIALE) -> 409
    - Crediti residui (sedute PT non consumate) -> 409
    CASCADE (pulizia completa):
    - Soft-delete rate SALDATE + tutti CashMovement
    - Detach eventi (id_contratto = NULL, restano in agenda)
    """
    contract = session.exec(
        select(Contract).where(
            Contract.id == contract_id, Contract.trainer_id == trainer.id, Contract.deleted_at == None
        )
    ).first()

    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")

    # RESTRICT 1: rate con obbligazioni pendenti (PENDENTE o PARZIALE)
    rate_pendenti = session.exec(
        select(func.count(Rate.id)).where(
            Rate.id_contratto == contract_id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.deleted_at == None,
        )
    ).one()
    if rate_pendenti > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Impossibile eliminare: il contratto ha {rate_pendenti} rate non saldate. "
                   f"Usa la chiusura (chiuso) per archiviarlo.",
        )

    # RESTRICT 2: crediti residui (sedute PT non ancora consumate)
    crediti_totali = contract.crediti_totali or 0
    if crediti_totali > 0:
        crediti_usati = session.exec(
            select(func.count(Event.id)).where(
                Event.id_contratto == contract_id,
                Event.categoria == "PT",
                Event.stato != "Cancellato",
                Event.deleted_at == None,
            )
        ).one()
        crediti_residui = crediti_totali - crediti_usati
        if crediti_residui > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Impossibile eliminare: il contratto ha {crediti_residui} crediti residui "
                       f"({crediti_usati}/{crediti_totali} usati). "
                       f"Usa la chiusura (chiuso) per archiviarlo.",
            )

    now = datetime.now(timezone.utc)

    # CASCADE 1: soft-delete rate SALDATE (record storico completato)
    saldate_rates = session.exec(
        select(Rate).where(
            Rate.id_contratto == contract_id,
            Rate.deleted_at == None,
        )
    ).all()
    for r in saldate_rates:
        r.deleted_at = now
        session.add(r)
        log_audit(session, "rate", r.id, "DELETE", trainer.id)

    # CASCADE 2: soft-delete TUTTI i CashMovement (acconto + pagamenti rate)
    movements = session.exec(
        select(CashMovement).where(
            CashMovement.id_contratto == contract_id,
            CashMovement.trainer_id == trainer.id,
            CashMovement.deleted_at == None,
        )
    ).all()
    for mov in movements:
        mov.deleted_at = now
        session.add(mov)
        log_audit(session, "movement", mov.id, "DELETE", trainer.id)

    # CASCADE 3: detach eventi (mantieni in agenda, rimuovi link contratto)
    linked_events = session.exec(
        select(Event).where(
            Event.id_contratto == contract_id,
            Event.deleted_at == None,
        )
    ).all()
    for ev in linked_events:
        ev.id_contratto = None
        session.add(ev)

    contract.deleted_at = now
    session.add(contract)
    log_audit(session, "contract", contract.id, "DELETE", trainer.id)
    session.commit()
