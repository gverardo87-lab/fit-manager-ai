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

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract
from sqlmodel import Session, select, func

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.movement import CashMovement
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
