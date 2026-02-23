# api/routers/recurring_expenses.py
"""
Endpoint Spese Ricorrenti — CRUD base con Bouncer Pattern.

Permette al trainer di gestire le spese fisse mensili
(affitto, assicurazione, utenze, abbonamenti).

Queste spese contribuiscono al calcolo del Margine Netto Mensile
nell'endpoint /movements/stats.
"""

from typing import Optional
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, select, func

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.recurring_expense import RecurringExpense
from api.routers._audit import log_audit

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])

VALID_FREQUENCIES = {"MENSILE", "SETTIMANALE", "TRIMESTRALE", "SEMESTRALE", "ANNUALE"}


# ── Schemas ──

class RecurringExpenseCreate(BaseModel):
    """Input per creazione spesa ricorrente."""
    model_config = {"extra": "forbid"}

    nome: str = Field(min_length=1, max_length=100)
    categoria: Optional[str] = Field(default=None, max_length=100)
    importo: float = Field(gt=0, le=100_000)
    giorno_scadenza: int = Field(default=1, ge=1, le=31)
    frequenza: str = Field(default="MENSILE")
    data_inizio: Optional[date] = None

    @field_validator("categoria", mode="before")
    @classmethod
    def sanitize_categoria(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v if v else None

    @field_validator("frequenza")
    @classmethod
    def validate_frequenza(cls, v: str) -> str:
        if v not in VALID_FREQUENCIES:
            raise ValueError(f"Frequenza invalida. Valide: {sorted(VALID_FREQUENCIES)}")
        return v


class RecurringExpenseUpdate(BaseModel):
    """Input per aggiornamento spesa ricorrente."""
    model_config = {"extra": "forbid"}

    nome: Optional[str] = Field(default=None, min_length=1, max_length=100)
    categoria: Optional[str] = Field(default=None, max_length=100)
    importo: Optional[float] = Field(default=None, gt=0, le=100_000)
    giorno_scadenza: Optional[int] = Field(default=None, ge=1, le=31)
    frequenza: Optional[str] = None
    data_inizio: Optional[date] = None
    attiva: Optional[bool] = None

    @field_validator("categoria", mode="before")
    @classmethod
    def sanitize_categoria(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v if v else None

    @field_validator("frequenza")
    @classmethod
    def validate_frequenza(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_FREQUENCIES:
            raise ValueError(f"Frequenza invalida. Valide: {sorted(VALID_FREQUENCIES)}")
        return v


class RecurringExpenseResponse(BaseModel):
    """Output — singola spesa ricorrente."""
    model_config = {"from_attributes": True}

    id: int
    nome: str
    categoria: Optional[str] = None
    importo: float
    frequenza: str = "MENSILE"
    giorno_scadenza: int
    data_inizio: Optional[date] = None
    attiva: bool
    data_creazione: Optional[datetime] = None
    data_disattivazione: Optional[datetime] = None


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
    query = select(RecurringExpense).where(RecurringExpense.trainer_id == trainer.id, RecurringExpense.deleted_at == None)

    if attiva is not None:
        query = query.where(RecurringExpense.attiva == attiva)

    # Count dalla stessa query base (zero duplicazione filtri)
    total = session.exec(
        select(func.count()).select_from(query.subquery())
    ).one()

    query = query.order_by(RecurringExpense.nome)
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
        frequenza=data.frequenza,
        data_inizio=data.data_inizio or date.today(),
    )
    session.add(expense)
    session.flush()
    log_audit(session, "recurring_expense", expense.id, "CREATE", trainer.id)
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
            RecurringExpense.deleted_at == None,
        )
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spesa ricorrente non trovata",
        )

    update_data = data.model_dump(exclude_unset=True)

    # Storico disattivazione: timestamp quando passa da attiva a disattiva
    if "attiva" in update_data:
        if update_data["attiva"] is False and expense.attiva:
            expense.data_disattivazione = datetime.now(timezone.utc)
        elif update_data["attiva"] is True and not expense.attiva:
            expense.data_disattivazione = None

    changes = {}
    for key, value in update_data.items():
        old_val = getattr(expense, key)
        setattr(expense, key, value)
        if value != old_val:
            changes[key] = {"old": old_val, "new": value}

    log_audit(session, "recurring_expense", expense.id, "UPDATE", trainer.id, changes or None)
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
            RecurringExpense.deleted_at == None,
        )
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spesa ricorrente non trovata",
        )

    expense.deleted_at = datetime.now(timezone.utc)
    session.add(expense)
    log_audit(session, "recurring_expense", expense.id, "DELETE", trainer.id)
    session.commit()
