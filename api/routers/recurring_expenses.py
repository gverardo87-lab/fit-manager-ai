# api/routers/recurring_expenses.py
"""
Endpoint Spese Ricorrenti — CRUD base con Bouncer Pattern.

Permette al trainer di gestire le spese fisse mensili
(affitto, assicurazione, utenze, abbonamenti).

Queste spese contribuiscono al calcolo del Margine Netto Mensile
nell'endpoint /movements/stats.
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select, func

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.recurring_expense import RecurringExpense

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])


# ── Schemas ──

class RecurringExpenseCreate(BaseModel):
    """Input per creazione spesa ricorrente."""
    model_config = {"extra": "forbid"}

    nome: str = Field(min_length=1, max_length=100)
    categoria: Optional[str] = Field(default=None, max_length=100)
    importo: float = Field(gt=0, le=100_000)
    giorno_scadenza: int = Field(default=1, ge=1, le=31)


class RecurringExpenseUpdate(BaseModel):
    """Input per aggiornamento spesa ricorrente."""
    model_config = {"extra": "forbid"}

    nome: Optional[str] = Field(default=None, min_length=1, max_length=100)
    categoria: Optional[str] = Field(default=None, max_length=100)
    importo: Optional[float] = Field(default=None, gt=0, le=100_000)
    giorno_scadenza: Optional[int] = Field(default=None, ge=1, le=31)
    attiva: Optional[bool] = None


class RecurringExpenseResponse(BaseModel):
    """Output — singola spesa ricorrente."""
    model_config = {"from_attributes": True}

    id: int
    nome: str
    categoria: Optional[str] = None
    importo: float
    giorno_scadenza: int
    attiva: bool
    data_creazione: Optional[datetime] = None


# ════════════════════════════════════════════════════════════
# GET: Lista spese ricorrenti
# ════════════════════════════════════════════════════════════

@router.get("", response_model=dict)
def list_recurring_expenses(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    attiva: Optional[bool] = Query(default=None, description="Filtra per stato attiva/disattiva"),
):
    """Lista spese ricorrenti del trainer autenticato."""
    query = select(RecurringExpense).where(RecurringExpense.trainer_id == trainer.id)
    count_q = select(func.count(RecurringExpense.id)).where(RecurringExpense.trainer_id == trainer.id)

    if attiva is not None:
        query = query.where(RecurringExpense.attiva == attiva)
        count_q = count_q.where(RecurringExpense.attiva == attiva)

    query = query.order_by(RecurringExpense.nome)
    total = session.exec(count_q).one()
    expenses = session.exec(query).all()

    return {
        "items": [RecurringExpenseResponse.model_validate(e) for e in expenses],
        "total": total,
    }


# ════════════════════════════════════════════════════════════
# POST: Crea spesa ricorrente
# ════════════════════════════════════════════════════════════

@router.post("", response_model=RecurringExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_expense(
    data: RecurringExpenseCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Crea una nuova spesa ricorrente."""
    expense = RecurringExpense(
        trainer_id=trainer.id,
        nome=data.nome,
        categoria=data.categoria,
        importo=data.importo,
        giorno_scadenza=data.giorno_scadenza,
    )
    session.add(expense)
    session.commit()
    session.refresh(expense)

    return RecurringExpenseResponse.model_validate(expense)


# ════════════════════════════════════════════════════════════
# PUT: Aggiorna spesa ricorrente
# ════════════════════════════════════════════════════════════

@router.put("/{expense_id}", response_model=RecurringExpenseResponse)
def update_recurring_expense(
    expense_id: int,
    data: RecurringExpenseUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Aggiorna una spesa ricorrente esistente."""
    expense = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.id == expense_id,
            RecurringExpense.trainer_id == trainer.id,
        )
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spesa ricorrente non trovata",
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(expense, key, value)

    session.add(expense)
    session.commit()
    session.refresh(expense)

    return RecurringExpenseResponse.model_validate(expense)


# ════════════════════════════════════════════════════════════
# DELETE: Elimina spesa ricorrente
# ════════════════════════════════════════════════════════════

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_expense(
    expense_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Elimina una spesa ricorrente."""
    expense = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.id == expense_id,
            RecurringExpense.trainer_id == trainer.id,
        )
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spesa ricorrente non trovata",
        )

    session.delete(expense)
    session.commit()
