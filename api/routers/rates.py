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
    RateCreate, RateUpdate, RatePayment,
    RateResponse, PaymentPlanCreate,
    AgingItem, AgingBucket, AgingResponse,
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


def _cap_rateizzabile(session: Session, contract: Contract, exclude_rate_id: int | None = None) -> float:
    """
    Calcola lo spazio disponibile per rate su un contratto.

    Formula: cap = prezzo_totale - acconto_effettivo
    Dove: acconto_effettivo = totale_versato - sum(importo_saldato di tutte le rate)

    Questo esclude i pagamenti rate dal calcolo del cap, evitando il
    double-counting quando rate pagate hanno importo_previsto > 0.
    """
    # Somma importo_previsto delle rate attive (esclusa eventuale rate corrente)
    previsto_query = select(func.coalesce(func.sum(Rate.importo_previsto), 0)).where(
        Rate.id_contratto == contract.id, Rate.deleted_at == None,
    )
    if exclude_rate_id:
        previsto_query = previsto_query.where(Rate.id != exclude_rate_id)
    somma_previsto = float(session.exec(previsto_query).one())

    # Acconto effettivo = totale_versato - pagamenti rate (evita double-counting)
    somma_saldato = float(session.exec(
        select(func.coalesce(func.sum(Rate.importo_saldato), 0)).where(
            Rate.id_contratto == contract.id, Rate.deleted_at == None,
        )
    ).one())
    acconto = max(0, round((contract.totale_versato or 0) - somma_saldato, 2))
    cap = round((contract.prezzo_totale or 0) - acconto, 2)
    spazio = round(cap - somma_previsto, 2)

    return spazio


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
# GET: Aging Report — Orizzonte Finanziario bidirezionale
# ════════════════════════════════════════════════════════════

# Bucket definitions: (label, min_days_inclusive, max_days_exclusive)
OVERDUE_BUCKETS = [("0-30", 0, 31), ("31-60", 31, 61), ("61-90", 61, 91), ("90+", 91, 999_999)]
UPCOMING_BUCKETS = [("0-7", 0, 8), ("8-30", 8, 31), ("31-60", 31, 61), ("61-90", 61, 91)]


@router.get("/aging", response_model=AgingResponse)
def get_aging_report(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Orizzonte finanziario: rate scadute (passato) + in arrivo (futuro).

    Una sola query con 2 JOIN (Rate → Contract → Client).
    Bucket scaduti: 0-30, 31-60, 61-90, 90+ giorni.
    Bucket in arrivo: 0-7, 8-30, 31-60, 61-90 giorni.
    Confini: min_days incluso, max_days escluso.
    """
    today = date.today()

    # Query unica: tutte le rate non saldate di contratti attivi
    results = session.exec(
        select(Rate, Contract, Client)
        .join(Contract, Rate.id_contratto == Contract.id)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.trainer_id == trainer.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.deleted_at == None,
            Contract.deleted_at == None,
            Contract.chiuso == False,
        )
        .order_by(Rate.data_scadenza)
    ).all()

    # Classifica ogni rata in overdue o upcoming
    overdue_items: list[list[AgingItem]] = [[] for _ in OVERDUE_BUCKETS]
    upcoming_items: list[list[AgingItem]] = [[] for _ in UPCOMING_BUCKETS]
    clienti_scaduto: set[int] = set()

    for rate, contract, client in results:
        giorni = (today - rate.data_scadenza).days
        residuo = round(rate.importo_previsto - rate.importo_saldato, 2)

        item = AgingItem(
            rate_id=rate.id,
            contract_id=contract.id,
            client_id=client.id,
            client_nome=client.nome,
            client_cognome=client.cognome,
            data_scadenza=rate.data_scadenza,
            giorni=giorni,
            importo_previsto=rate.importo_previsto,
            importo_saldato=rate.importo_saldato,
            importo_residuo=residuo,
            stato=rate.stato,
        )

        if giorni > 0:
            # Scaduta — assegna al bucket corretto
            clienti_scaduto.add(client.id)
            for i, (_, min_d, max_d) in enumerate(OVERDUE_BUCKETS):
                if min_d <= giorni < max_d:
                    overdue_items[i].append(item)
                    break
        else:
            # Futura — giorni_mancanti = abs(giorni)
            giorni_mancanti = abs(giorni)
            for i, (_, min_d, max_d) in enumerate(UPCOMING_BUCKETS):
                if min_d <= giorni_mancanti < max_d:
                    upcoming_items[i].append(item)
                    break

    # Costruisci bucket response
    overdue_buckets = []
    for i, (label, min_d, max_d) in enumerate(OVERDUE_BUCKETS):
        items = overdue_items[i]
        overdue_buckets.append(AgingBucket(
            label=label,
            min_days=min_d,
            max_days=max_d,
            totale=round(sum(it.importo_residuo for it in items), 2),
            count=len(items),
            items=items,
        ))

    upcoming_buckets = []
    for i, (label, min_d, max_d) in enumerate(UPCOMING_BUCKETS):
        items = upcoming_items[i]
        upcoming_buckets.append(AgingBucket(
            label=label,
            min_days=min_d,
            max_days=max_d,
            totale=round(sum(it.importo_residuo for it in items), 2),
            count=len(items),
            items=items,
        ))

    totale_scaduto = round(sum(b.totale for b in overdue_buckets), 2)
    totale_in_arrivo = round(sum(b.totale for b in upcoming_buckets), 2)

    return AgingResponse(
        totale_scaduto=totale_scaduto,
        totale_in_arrivo=totale_in_arrivo,
        rate_scadute=sum(b.count for b in overdue_buckets),
        rate_in_arrivo=sum(b.count for b in upcoming_buckets),
        clienti_con_scaduto=len(clienti_scaduto),
        overdue_buckets=overdue_buckets,
        upcoming_buckets=upcoming_buckets,
    )


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
    Validazione: importo non supera il residuo rateizzabile del contratto.
    """
    # Bouncer sul contratto
    contract = _bouncer_contract(session, data.id_contratto, trainer.id)

    # Contratto chiuso: no nuove rate
    if contract.chiuso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile aggiungere rate a un contratto chiuso",
        )

    # Data rata entro scadenza contratto (prevenzione Salesforce-style)
    if contract.data_scadenza and data.data_scadenza > contract.data_scadenza:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data scadenza rata ({data.data_scadenza}) oltre la scadenza "
                   f"del contratto ({contract.data_scadenza})",
        )

    # Validazione residuo: importo non supera lo spazio disponibile
    if contract.prezzo_totale:
        spazio = _cap_rateizzabile(session, contract)
        if data.importo_previsto > spazio + 0.01:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Importo ({data.importo_previsto:.2f}) eccede il residuo rateizzabile ({max(0, spazio):.2f})",
            )

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
# PUT: Aggiorna rata (tutte le rate)
# ════════════════════════════════════════════════════════════

@router.put("/{rate_id}", response_model=RateResponse)
def update_rate(
    rate_id: int,
    data: RateUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Aggiorna una rata (partial update, tutte le rate).

    Deep Relational IDOR + business rules:
    - data_scadenza e descrizione: sempre modificabili (zero impatto finanziario)
    - importo_previsto su rate con pagamenti: consentito se nuovo >= importo_saldato
    - Se importo_previsto cambia, re-validazione residuo contratto + ricalcolo stato
    """
    rate = _bouncer_rate(session, rate_id, trainer.id)

    update_data = data.model_dump(exclude_unset=True)

    # Data rata entro scadenza contratto
    if "data_scadenza" in update_data:
        contract = session.get(Contract, rate.id_contratto)
        if contract and contract.data_scadenza and update_data["data_scadenza"] > contract.data_scadenza:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Data scadenza rata ({update_data['data_scadenza']}) oltre la scadenza "
                       f"del contratto ({contract.data_scadenza})",
            )

    # Validazione importo_previsto su rate con pagamenti
    if "importo_previsto" in update_data and rate.importo_saldato > 0:
        nuovo_importo = update_data["importo_previsto"]
        if nuovo_importo < rate.importo_saldato - 0.01:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Importo ({nuovo_importo:.2f}) inferiore al gia' versato "
                       f"({rate.importo_saldato:.2f}). "
                       f"Per ridurre sotto il versato, revoca prima il pagamento.",
            )

    # Re-validazione residuo contratto se importo_previsto cambia
    if "importo_previsto" in update_data:
        contract = session.get(Contract, rate.id_contratto)
        if contract and contract.prezzo_totale:
            # Spazio disponibile escludendo questa rata
            spazio = _cap_rateizzabile(session, contract, exclude_rate_id=rate.id)
            if update_data["importo_previsto"] > spazio + 0.01:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Importo ({update_data['importo_previsto']:.2f}) eccede il "
                           f"residuo rateizzabile ({max(0, spazio):.2f})",
                )

    changes = {}
    for field, value in update_data.items():
        old_val = getattr(rate, field)
        setattr(rate, field, value)
        if value != old_val:
            changes[field] = {"old": old_val, "new": value}

    # Ricalcola stato se importo_previsto e' cambiato su rata con pagamenti
    if "importo_previsto" in changes and rate.importo_saldato > 0:
        old_stato = rate.stato
        if rate.importo_saldato >= rate.importo_previsto - 0.01:
            rate.stato = "SALDATA"
        else:
            rate.stato = "PARZIALE"
        if rate.stato != old_stato:
            changes["stato"] = {"old": old_stato, "new": rate.stato}

    # Sync data_effettiva CashMovement quando data_scadenza cambia su rata pagata
    if "data_scadenza" in changes and rate.importo_saldato > 0:
        movements = session.exec(
            select(CashMovement).where(
                CashMovement.id_rata == rate.id,
                CashMovement.tipo == "ENTRATA",
                CashMovement.deleted_at == None,
            )
        ).all()
        for mv in movements:
            old_data = mv.data_effettiva
            mv.data_effettiva = rate.data_scadenza
            session.add(mv)
            log_audit(session, "movement", mv.id, "UPDATE", trainer.id, {
                "data_effettiva": {"old": str(old_data), "new": str(rate.data_scadenza)},
            })

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
    Elimina una rata (solo PENDENTI senza pagamenti).

    Deep Relational IDOR + business rule:
    rate con qualsiasi pagamento (PARZIALE/SALDATA) non eliminabili.
    Revoca prima il pagamento (unpay), poi elimina.
    """
    rate = _bouncer_rate(session, rate_id, trainer.id)

    if rate.importo_saldato > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile eliminare una rata con pagamenti. "
                   "Revoca prima il pagamento.",
        )

    rate.deleted_at = datetime.now(timezone.utc)
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
    B-bis) Validazione: importo non supera residuo rata
    B-ter) Validazione: importo non supera residuo contratto
    C) Aggiorna importo_saldato e stato rata
    D) Aggiorna totale_versato contratto (incrementale)
    E) Se totale_versato >= prezzo_totale -> stato_pagamento = SALDATO
    E-auto) Auto-close: se saldato + crediti esauriti -> chiuso
    E-bis) Registra CashMovement ENTRATA nel libro mastro
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

    # B-bis) Validazione importo: non superare il residuo della rata
    importo_residuo = round(rate.importo_previsto - rate.importo_saldato, 2)
    if data.importo > importo_residuo + 0.01:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Importo ({data.importo:.2f}) supera il residuo della rata ({importo_residuo:.2f})",
        )

    # B-ter) Validazione livello contratto: pagamento non eccede prezzo totale
    contract = session.get(Contract, rate.id_contratto)
    if contract.prezzo_totale:
        residuo_contratto = round(contract.prezzo_totale - contract.totale_versato, 2)
        if data.importo > residuo_contratto + 0.01:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Importo ({data.importo:.2f}) supera il residuo del contratto ({residuo_contratto:.2f})",
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
    #    contract gia' fetchato in B-ter. Approccio incrementale: totale_versato += importo.
    old_totale_versato = contract.totale_versato
    old_stato_pagamento = contract.stato_pagamento
    contract.totale_versato = contract.totale_versato + data.importo

    # E) Stato contratto: SALDATO se totale pagato copre il prezzo
    if contract.prezzo_totale and contract.totale_versato >= contract.prezzo_totale - 0.01:
        contract.stato_pagamento = "SALDATO"
    elif contract.totale_versato > 0:
        contract.stato_pagamento = "PARZIALE"

    # E-auto) Auto-close: contratto saldato + crediti esauriti → chiuso
    if contract.stato_pagamento == "SALDATO" and contract.crediti_totali:
        crediti_usati = session.exec(
            select(func.count(Event.id)).where(
                Event.id_contratto == contract.id,
                Event.categoria == "PT",
                Event.stato != "Cancellato",
                Event.deleted_at == None,
            )
        ).one()
        if crediti_usati >= contract.crediti_totali:
            contract.chiuso = True

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
    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, {
        "totale_versato": {"old": old_totale_versato, "new": contract.totale_versato},
        "stato_pagamento": {"old": old_stato_pagamento, "new": contract.stato_pagamento},
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
    old_totale_versato = contract.totale_versato
    old_stato_pagamento = contract.stato_pagamento
    contract.totale_versato = max(0, contract.totale_versato - importo_da_stornare)

    # E) Ricalcola stato_pagamento
    if contract.totale_versato <= 0:
        contract.stato_pagamento = "PENDENTE"
    elif contract.prezzo_totale and contract.totale_versato >= contract.prezzo_totale - 0.01:
        contract.stato_pagamento = "SALDATO"
    else:
        contract.stato_pagamento = "PARZIALE"

    # E-auto) Auto-reopen: se non piu' saldato, riapri contratto chiuso
    if contract.chiuso and contract.stato_pagamento != "SALDATO":
        contract.chiuso = False

    session.add(contract)

    # F) Soft-delete TUTTI i CashMovement associati (puo' averne piu' di uno
    #    se la rata ha ricevuto pagamenti parziali multipli)
    now = datetime.now(timezone.utc)
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
    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, {
        "totale_versato": {"old": old_totale_versato, "new": contract.totale_versato},
        "stato_pagamento": {"old": old_stato_pagamento, "new": contract.stato_pagamento},
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

    # Contratto chiuso: no piano rate
    if contract.chiuso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile generare piano rate per un contratto chiuso",
        )

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
    now = datetime.now(timezone.utc)
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

        # Auto-cap: rata non puo' superare scadenza contratto (Chargebee-style)
        if contract.data_scadenza and due_date > contract.data_scadenza:
            due_date = contract.data_scadenza

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
