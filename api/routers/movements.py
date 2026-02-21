# api/routers/movements.py
"""
Endpoint Movimenti Cassa — Ledger con Bouncer Pattern.

Sicurezza multi-tenant:
- trainer_id diretto su movimenti_cassa (Bouncer filtra per trainer)
- trainer_id iniettato dal JWT, mai dal body

Ledger Integrity:
- POST crea SOLO movimenti manuali (niente id_contratto/id_rata/id_cliente)
- DELETE elimina SOLO movimenti manuali (quelli di sistema sono intoccabili)
- I movimenti di sistema (ACCONTO_CONTRATTO, PAGAMENTO_RATA) vengono
  creati esclusivamente da create_contract e pay_rate.
"""

import calendar
from collections import defaultdict
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

router = APIRouter(prefix="/movements", tags=["movements"])


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

    Filtri combinabili: anno + mese per vista mensile, tipo per entrate/uscite.
    """
    # Base query con Bouncer
    query = select(CashMovement).where(CashMovement.trainer_id == trainer.id)
    count_q = select(func.count(CashMovement.id)).where(CashMovement.trainer_id == trainer.id)

    # Filtro anno (db-agnostic: extract funziona su SQLite, PostgreSQL, MySQL)
    if anno is not None:
        query = query.where(extract("year", CashMovement.data_effettiva) == anno)
        count_q = count_q.where(extract("year", CashMovement.data_effettiva) == anno)

    # Filtro mese (db-agnostic)
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
# GET: Statistiche mensili con chart_data
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
    Statistiche finanziarie del mese: entrate, uscite variabili,
    uscite fisse (spese ricorrenti attive), margine netto.

    Restituisce anche chart_data: array giornaliero entrate/uscite
    per il grafico a barre.
    """
    # Movimenti del mese
    movements = session.exec(
        select(CashMovement).where(
            CashMovement.trainer_id == trainer.id,
            extract("year", CashMovement.data_effettiva) == anno,
            extract("month", CashMovement.data_effettiva) == mese,
        )
    ).all()

    # Somme
    totale_entrate = sum(m.importo for m in movements if m.tipo == "ENTRATA")
    totale_uscite_variabili = sum(m.importo for m in movements if m.tipo == "USCITA")

    # Spese fisse attive del trainer
    recurring = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.trainer_id == trainer.id,
            RecurringExpense.attiva == True,
        )
    ).all()
    totale_uscite_fisse = sum(r.importo for r in recurring)

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
    blocca l'inserimento di id_contratto, id_rata e id_cliente.
    Solo il sistema puo' creare movimenti legati a contratti.
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
    Business Rule: movimenti di sistema (con id_contratto) sono intoccabili.
    Se il movimento e' di sistema -> 400 Bad Request.
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

    session.delete(movement)
    session.commit()
