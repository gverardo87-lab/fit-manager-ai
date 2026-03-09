"""Shared occurrence and pending logic for recurring expenses."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

from sqlmodel import Session, select

from api.models.movement import CashMovement
from api.models.recurring_expense import RecurringExpense

VALID_RECURRING_EXPENSE_FREQUENCIES = {
    "MENSILE",
    "SETTIMANALE",
    "TRIMESTRALE",
    "SEMESTRALE",
    "ANNUALE",
}


@dataclass(frozen=True)
class PendingRecurringExpenseOccurrence:
    expense_id: int
    nome: str
    categoria: str | None
    importo: float
    frequenza: str
    due_date: date
    occurrence_key: str


def get_recurring_expense_start_date(expense: RecurringExpense) -> date:
    """Return the anchoring date for the recurrence cycle."""
    if expense.data_inizio:
        return expense.data_inizio
    if expense.data_creazione:
        return expense.data_creazione.date()
    return date.today()


def get_recurring_expense_occurrences_in_month(
    expense: RecurringExpense,
    anno: int,
    mese: int,
) -> list[tuple[date, str]]:
    """Return all occurrence dates and dedupe keys for a target month."""
    days_in_month = calendar.monthrange(anno, mese)[1]
    freq = expense.frequenza or "MENSILE"
    start = get_recurring_expense_start_date(expense)

    last_day_of_month = date(anno, mese, days_in_month)
    if start > last_day_of_month:
        return []

    if freq == "MENSILE":
        giorno = min(expense.giorno_scadenza, days_in_month)
        return [(date(anno, mese, giorno), f"{anno:04d}-{mese:02d}")]

    if freq == "SETTIMANALE":
        base = min(expense.giorno_scadenza, 7)
        occurrences: list[tuple[date, str]] = []
        day = base
        week = 1
        while day <= days_in_month:
            key = f"{anno:04d}-{mese:02d}-W{week}"
            occurrences.append((date(anno, mese, day), key))
            day += 7
            week += 1
        return occurrences

    abs_target = anno * 12 + mese
    abs_start = start.year * 12 + start.month

    if freq == "TRIMESTRALE":
        if (abs_target - abs_start) % 3 != 0:
            return []
        giorno = min(expense.giorno_scadenza, days_in_month)
        return [(date(anno, mese, giorno), f"{anno:04d}-{mese:02d}")]

    if freq == "SEMESTRALE":
        if (abs_target - abs_start) % 6 != 0:
            return []
        giorno = min(expense.giorno_scadenza, days_in_month)
        return [(date(anno, mese, giorno), f"{anno:04d}-{mese:02d}")]

    if freq == "ANNUALE":
        if mese != start.month:
            return []
        giorno = min(expense.giorno_scadenza, days_in_month)
        return [(date(anno, mese, giorno), f"{anno:04d}")]

    giorno = min(expense.giorno_scadenza, days_in_month)
    return [(date(anno, mese, giorno), f"{anno:04d}-{mese:02d}")]


def resolve_recurring_expense_occurrence_date(
    expense: RecurringExpense,
    occurrence_key: str,
) -> date | None:
    """Resolve a concrete date from an occurrence dedupe key."""
    parts = occurrence_key.split("-")
    try:
        anno = int(parts[0])
        if len(parts) == 1:
            mese = get_recurring_expense_start_date(expense).month
        else:
            mese = int(parts[1])
    except (ValueError, IndexError):
        return None

    for occ_date, occ_key in get_recurring_expense_occurrences_in_month(expense, anno, mese):
        if occ_key == occurrence_key:
            return occ_date
    return None


def list_pending_recurring_expense_occurrences(
    *,
    trainer_id: int,
    session: Session,
    anno: int,
    mese: int,
) -> list[PendingRecurringExpenseOccurrence]:
    """List active recurring expense occurrences not yet confirmed in the ledger."""
    recurring = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.trainer_id == trainer_id,
            RecurringExpense.attiva == True,
            RecurringExpense.deleted_at == None,
        )
    ).all()

    if not recurring:
        return []

    existing = session.exec(
        select(CashMovement.id_spesa_ricorrente, CashMovement.mese_anno).where(
            CashMovement.trainer_id == trainer_id,
            CashMovement.id_spesa_ricorrente != None,
            CashMovement.deleted_at == None,
        )
    ).all()
    existing_keys: set[tuple[int, str]] = {(row[0], row[1]) for row in existing}

    pending: list[PendingRecurringExpenseOccurrence] = []
    for expense in recurring:
        if expense.id is None:
            continue
        occurrences = get_recurring_expense_occurrences_in_month(expense, anno, mese)
        for due_date, occurrence_key in occurrences:
            if (expense.id, occurrence_key) in existing_keys:
                continue
            pending.append(
                PendingRecurringExpenseOccurrence(
                    expense_id=expense.id,
                    nome=expense.nome,
                    categoria=expense.categoria,
                    importo=expense.importo,
                    frequenza=expense.frequenza or "MENSILE",
                    due_date=due_date,
                    occurrence_key=occurrence_key,
                )
            )

    pending.sort(key=lambda item: (item.due_date, item.nome.lower(), item.expense_id, item.occurrence_key))
    return pending
