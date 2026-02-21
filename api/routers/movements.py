# api/routers/movements.py
"""
Endpoint Movimenti Cassa — Ledger con Bouncer Pattern.

Sicurezza multi-tenant:
- trainer_id diretto su movimenti_cassa (Bouncer filtra per trainer)
- trainer_id iniettato dal JWT, mai dal body

Ledger Integrity:
- POST crea SOLO movimenti manuali (niente id_contratto/id_rata/id_cliente)
- DELETE elimina SOLO movimenti manuali (quelli di sistema sono intoccabili)
- I movimenti di sistema (ACCONTO_CONTRATTO, PAGAMENTO_RATA, SPESA_FISSA)
  vengono creati esclusivamente da create_contract, pay_rate, e sync engine.

Sync Engine (spese ricorrenti):
- Prima di ogni GET (lista e stats), sync_recurring_expenses_for_month()
  genera CashMovement reali dalle RecurringExpense attive.
- Idempotente: se il movimento per quel mese esiste gia', lo salta.
- Single Source of Truth: le stats derivano SOLO da CashMovement.
"""

import calendar
import logging
from collections import defaultdict
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import extract
from sqlmodel import Session, select, func

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.movement import CashMovement
from api.models.recurring_expense import RecurringExpense
from api.schemas.financial import (
    MovementManualCreate, MovementResponse,
)

logger = logging.getLogger("fitmanager.api")
router = APIRouter(prefix="/movements", tags=["movements"])


# ════════════════════════════════════════════════════════════
# SYNC ENGINE: Spese Ricorrenti → CashMovement (idempotente)
# ════════════════════════════════════════════════════════════

def sync_recurring_expenses_for_month(
    session: Session, trainer_id: int, anno: int, mese: int
) -> int:
    """
    Genera CashMovement reali per le spese ricorrenti attive del mese.

    Idempotenza: per ogni RecurringExpense, controlla se esiste gia'
    un CashMovement con lo stesso id_spesa_ricorrente nello stesso mese.
    Se esiste, lo salta. Se non esiste, lo crea.

    Returns: numero di movimenti creati (0 = nessun lavoro da fare).
    """
    recurring = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.trainer_id == trainer_id,
            RecurringExpense.attiva == True,
        )
    ).all()

    if not recurring:
        return 0

    created = 0
    days_in_month = calendar.monthrange(anno, mese)[1]

    for expense in recurring:
        # Check idempotenza: esiste gia' un movimento per questa spesa in questo mese?
        existing = session.exec(
            select(CashMovement.id).where(
                CashMovement.trainer_id == trainer_id,
                CashMovement.id_spesa_ricorrente == expense.id,
                extract("year", CashMovement.data_effettiva) == anno,
                extract("month", CashMovement.data_effettiva) == mese,
            )
        ).first()

        if existing is not None:
            continue

        # Giorno scadenza capped al massimo del mese (es. 31 in feb -> 28/29)
        giorno = min(expense.giorno_scadenza, days_in_month)

        movement = CashMovement(
            trainer_id=trainer_id,
            data_effettiva=date(anno, mese, giorno),
            tipo="USCITA",
            categoria="SPESA_FISSA",
            importo=expense.importo,
            note=f"Spesa ricorrente: {expense.nome}",
            operatore="SISTEMA_RECURRING",
            id_spesa_ricorrente=expense.id,
        )
        session.add(movement)
        created += 1

    if created > 0:
        session.commit()
        logger.info(
            "Sync: %d movimenti spese fisse creati per %d/%d (trainer %d)",
            created, mese, anno, trainer_id,
        )

    return created


# ════════════════════════════════════════════════════════════
# GET: Lista movimenti con filtri
# ════════════════════════════════════════════════════════════

@router.get("", response_model=dict)
def list_movements(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    anno: Optional[int] = Query(default=None, ge=2000, le=2100, description="Filtra per anno"),
    mese: Optional[int] = Query(default=None, ge=1, le=12, description="Filtra per mese (1-12)"),
    tipo: Optional[str] = Query(default=None, description="Filtra per tipo (ENTRATA/USCITA)"),
):
    """
    Lista movimenti del trainer autenticato con paginazione e filtri.

    Sync Engine: se anno+mese sono forniti, sincronizza le spese ricorrenti
    prima di restituire i risultati (idempotente, zero-cost se gia' sincronizzato).
    """
    # Sync spese ricorrenti per il mese richiesto
    if anno is not None and mese is not None:
        sync_recurring_expenses_for_month(session, trainer.id, anno, mese)

    # Base query con Bouncer
    query = select(CashMovement).where(CashMovement.trainer_id == trainer.id)
    count_q = select(func.count(CashMovement.id)).where(CashMovement.trainer_id == trainer.id)

    # Filtro anno
    if anno is not None:
        query = query.where(extract("year", CashMovement.data_effettiva) == anno)
        count_q = count_q.where(extract("year", CashMovement.data_effettiva) == anno)

    # Filtro mese
    if mese is not None:
        query = query.where(extract("month", CashMovement.data_effettiva) == mese)
        count_q = count_q.where(extract("month", CashMovement.data_effettiva) == mese)

    # Filtro tipo
    if tipo is not None:
        query = query.where(CashMovement.tipo == tipo)
        count_q = count_q.where(CashMovement.tipo == tipo)

    # Count totale
    total = session.exec(count_q).one()

    # Paginazione
    offset = (page - 1) * page_size
    query = query.order_by(CashMovement.data_effettiva.desc()).offset(offset).limit(page_size)
    movements = session.exec(query).all()

    return {
        "items": [MovementResponse.model_validate(m) for m in movements],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ════════════════════════════════════════════════════════════
# GET: Statistiche mensili — Single Source of Truth
# ════════════════════════════════════════════════════════════

class ChartDataPoint(BaseModel):
    giorno: int
    entrate: float
    uscite: float

class MovementStatsResponse(BaseModel):
    totale_entrate: float
    totale_uscite_variabili: float
    totale_uscite_fisse: float
    margine_netto: float
    chart_data: list[ChartDataPoint]


@router.get("/stats", response_model=MovementStatsResponse)
def get_movement_stats(
    anno: int = Query(ge=2000, le=2100),
    mese: int = Query(ge=1, le=12),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Statistiche finanziarie del mese — Single Source of Truth.

    Sync Engine: sincronizza le spese ricorrenti prima di calcolare.
    Poi TUTTE le cifre derivano da CashMovement:
    - entrate: tipo=ENTRATA
    - uscite variabili: tipo=USCITA AND id_spesa_ricorrente IS NULL
    - uscite fisse: tipo=USCITA AND id_spesa_ricorrente IS NOT NULL
    - margine netto: entrate - uscite_variabili - uscite_fisse
    """
    # Sync spese ricorrenti (idempotente)
    sync_recurring_expenses_for_month(session, trainer.id, anno, mese)

    # Tutti i movimenti del mese (single query)
    movements = session.exec(
        select(CashMovement).where(
            CashMovement.trainer_id == trainer.id,
            extract("year", CashMovement.data_effettiva) == anno,
            extract("month", CashMovement.data_effettiva) == mese,
        )
    ).all()

    # Single Source of Truth: tutto da CashMovement
    totale_entrate = sum(m.importo for m in movements if m.tipo == "ENTRATA")
    totale_uscite_variabili = sum(
        m.importo for m in movements
        if m.tipo == "USCITA" and m.id_spesa_ricorrente is None
    )
    totale_uscite_fisse = sum(
        m.importo for m in movements
        if m.tipo == "USCITA" and m.id_spesa_ricorrente is not None
    )

    margine_netto = totale_entrate - totale_uscite_variabili - totale_uscite_fisse

    # Chart data: raggruppamento per giorno del mese
    days_in_month = calendar.monthrange(anno, mese)[1]
    entrate_per_giorno: dict[int, float] = defaultdict(float)
    uscite_per_giorno: dict[int, float] = defaultdict(float)

    for m in movements:
        day = m.data_effettiva.day
        if m.tipo == "ENTRATA":
            entrate_per_giorno[day] += m.importo
        else:
            uscite_per_giorno[day] += m.importo

    chart_data = [
        ChartDataPoint(
            giorno=d,
            entrate=round(entrate_per_giorno.get(d, 0), 2),
            uscite=round(uscite_per_giorno.get(d, 0), 2),
        )
        for d in range(1, days_in_month + 1)
    ]

    return MovementStatsResponse(
        totale_entrate=round(totale_entrate, 2),
        totale_uscite_variabili=round(totale_uscite_variabili, 2),
        totale_uscite_fisse=round(totale_uscite_fisse, 2),
        margine_netto=round(margine_netto, 2),
        chart_data=chart_data,
    )


# ════════════════════════════════════════════════════════════
# POST: Crea movimento manuale
# ════════════════════════════════════════════════════════════

@router.post("", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
def create_manual_movement(
    data: MovementManualCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Crea un movimento manuale (spesa affitto, attrezzatura, incasso extra, ecc.).

    Ledger Integrity: lo schema MovementManualCreate (extra: forbid)
    blocca l'inserimento di id_contratto, id_rata, id_cliente e id_spesa_ricorrente.
    Solo il sistema puo' creare movimenti legati a contratti o spese ricorrenti.
    """
    movement = CashMovement(
        trainer_id=trainer.id,
        data_effettiva=data.data_effettiva,
        tipo=data.tipo,
        categoria=data.categoria,
        importo=data.importo,
        metodo=data.metodo,
        note=data.note,
        operatore="MANUALE",
    )
    session.add(movement)
    session.commit()
    session.refresh(movement)

    return MovementResponse.model_validate(movement)


# ════════════════════════════════════════════════════════════
# DELETE: Elimina movimento (solo manuali)
# ════════════════════════════════════════════════════════════

@router.delete("/{movement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movement(
    movement_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Elimina un movimento — SOLO se manuale.

    Bouncer: query singola movement.id + trainer_id.
    Business Rules:
    - Movimenti legati a contratti (id_contratto != null) -> 400
    - Movimenti generati da spese ricorrenti (id_spesa_ricorrente != null) -> 400
    """
    movement = session.exec(
        select(CashMovement).where(
            CashMovement.id == movement_id,
            CashMovement.trainer_id == trainer.id,
        )
    ).first()

    if not movement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimento non trovato",
        )

    # Business Rule: movimenti di sistema sono protetti
    if movement.id_contratto is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile eliminare un movimento di sistema (legato a un contratto)",
        )

    if movement.id_spesa_ricorrente is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile eliminare un movimento di spesa fissa (generato automaticamente)",
        )

    session.delete(movement)
    session.commit()
