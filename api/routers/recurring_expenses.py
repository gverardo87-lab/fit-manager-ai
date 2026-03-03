# api/routers/recurring_expenses.py
"""
Endpoint Spese Ricorrenti — CRUD base con Bouncer Pattern.

Permette al trainer di gestire le spese fisse mensili
(affitto, assicurazione, utenze, abbonamenti).

Queste spese contribuiscono al calcolo del Margine Netto Mensile
nell'endpoint /movements/stats.
"""

import calendar
from typing import Optional
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import case
from sqlmodel import Session, select, func

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.recurring_expense import RecurringExpense
from api.models.movement import CashMovement
from api.routers._audit import log_audit

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])

VALID_FREQUENCIES = {"MENSILE", "SETTIMANALE", "TRIMESTRALE", "SEMESTRALE", "ANNUALE"}


def _get_start_date(expense: RecurringExpense) -> date:
    """Data di ancoraggio della spesa ricorrente."""
    if expense.data_inizio:
        return expense.data_inizio
    if expense.data_creazione:
        return expense.data_creazione.date()
    return date.today()


def _get_occurrences_in_month(expense: RecurringExpense, anno: int, mese: int) -> list[tuple[date, str]]:
    """
    Occorrenze della spesa in un mese specifico.

    Ritorna lista di tuple (data_effettiva, mese_anno_key).
    """
    days_in_month = calendar.monthrange(anno, mese)[1]
    freq = expense.frequenza or "MENSILE"
    start = _get_start_date(expense)

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


def _resolve_occurrence_date(expense: RecurringExpense, key: str) -> Optional[date]:
    """
    Risolve la data di un'occorrenza partendo dalla key periodo.

    La key deve essere coerente con il ciclo reale della spesa.
    """
    parts = key.split("-")
    try:
        anno = int(parts[0])
        if len(parts) == 1:
            mese = _get_start_date(expense).month
        else:
            mese = int(parts[1])
    except (ValueError, IndexError):
        return None

    for occ_date, occ_key in _get_occurrences_in_month(expense, anno, mese):
        if occ_key == key:
            return occ_date
    return None


_signed_importo = case(
    (CashMovement.tipo == "ENTRATA", CashMovement.importo),
    else_=-CashMovement.importo,
)


def _compute_saldo_for_preview(
    session: Session,
    trainer: Trainer,
    *,
    as_of: Optional[date] = None,
) -> float:
    """Saldo cassa cumulativo (stessa semantica di /movements/balance)."""
    filters = [
        CashMovement.trainer_id == trainer.id,
        CashMovement.deleted_at == None,
    ]
    if trainer.data_saldo_iniziale:
        filters.append(CashMovement.data_effettiva >= trainer.data_saldo_iniziale)
    if as_of is not None:
        filters.append(CashMovement.data_effettiva <= as_of)

    result = float(
        session.exec(
            select(func.coalesce(func.sum(_signed_importo), 0)).where(*filters)
        ).one()
    )
    return round(trainer.saldo_iniziale_cassa + result, 2)


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


class RecurringExpenseDeleteResponse(BaseModel):
    """Output delete spesa ricorrente con cleanup opzionale ledger."""
    deleted_movements: int = 0


class RecurringExpenseCloseRequest(BaseModel):
    """Input chiusura spesa ricorrente con cutoff e strategia ultimo periodo."""
    model_config = {"extra": "forbid"}

    effective_mese_anno_key: str = Field(
        min_length=4,
        max_length=20,
        description="Occorrenza cutoff (es. 2026-03, 2026-03-W2, 2026)",
    )
    last_occurrence_due: bool = Field(
        default=True,
        description="Se true l'occorrenza cutoff resta dovuta; se false viene stornata",
    )


class RecurringExpenseCloseResponse(BaseModel):
    """Output chiusura spesa ricorrente con effetti contabili applicati."""
    cutoff_key: str
    cutoff_data: date
    created_last_due_movement: bool
    storni_creati: int
    storni_rimossi: int = 0


class RecurringExpenseClosePreviewResponse(BaseModel):
    """Anteprima impatto contabile per chiusura/rettifica spesa ricorrente."""
    cutoff_key: str
    cutoff_data: date
    created_last_due_movement: bool
    storni_creati_previsti: int
    storni_rimossi_previsti: int
    saldo_attuale_before: float
    saldo_attuale_after: float
    saldo_previsto_before: float
    saldo_previsto_after: float
    delta_saldo_attuale: float
    delta_saldo_previsto: float
    delta_netto: float

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


def _estimate_close_deltas(
    session: Session,
    trainer: Trainer,
    expense: RecurringExpense,
    data: RecurringExpenseCloseRequest,
) -> tuple[date, bool, int, int, list[tuple[date, float]]]:
    """
    Stima gli effetti di chiusura/rettifica senza scrivere su DB.

    Ritorna:
    - cutoff_occurrence_date
    - created_last_due_movement
    - storni_creati_previsti
    - storni_rimossi_previsti
    - deltas firmati [(data, signed_amount)]
    """
    cutoff_occurrence_date = _resolve_occurrence_date(expense, data.effective_mese_anno_key)
    if not cutoff_occurrence_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Occorrenza cutoff non valida per questa spesa ricorrente",
        )

    cutoff_date = (
        cutoff_occurrence_date
        if data.last_occurrence_due
        else cutoff_occurrence_date - timedelta(days=1)
    )

    deltas: list[tuple[date, float]] = []
    created_last_due_movement = False

    if data.last_occurrence_due:
        already_present = session.exec(
            select(CashMovement.id).where(
                CashMovement.trainer_id == trainer.id,
                CashMovement.id_spesa_ricorrente == expense.id,
                CashMovement.mese_anno == data.effective_mese_anno_key,
                CashMovement.deleted_at == None,
            )
        ).first()
        if not already_present:
            # Inserimento uscita di cutoff: effetto negativo.
            deltas.append((cutoff_occurrence_date, -expense.importo))
            created_last_due_movement = True

    linked_expense_movements = session.exec(
        select(CashMovement).where(
            CashMovement.trainer_id == trainer.id,
            CashMovement.id_spesa_ricorrente == expense.id,
            CashMovement.id_contratto == None,
            CashMovement.tipo == "USCITA",
            CashMovement.deleted_at == None,
        )
    ).all()

    storni_creati_previsti = 0
    storni_rimossi_previsti = 0

    for movement in linked_expense_movements:
        should_be_storned = movement.data_effettiva > cutoff_date
        storno_key = f"STORNO:{movement.id}"

        active_storno = session.exec(
            select(CashMovement).where(
                CashMovement.trainer_id == trainer.id,
                CashMovement.id_spesa_ricorrente == expense.id,
                CashMovement.tipo == "ENTRATA",
                CashMovement.mese_anno == storno_key,
                CashMovement.deleted_at == None,
            )
        ).first()

        if should_be_storned:
            if active_storno:
                continue
            # Creazione/restore storno: effetto positivo.
            deltas.append((movement.data_effettiva, movement.importo))
            storni_creati_previsti += 1
            continue

        if active_storno:
            # Rimozione storno attivo: effetto negativo.
            deltas.append((movement.data_effettiva, -active_storno.importo))
            storni_rimossi_previsti += 1

    return (
        cutoff_occurrence_date,
        created_last_due_movement,
        storni_creati_previsti,
        storni_rimossi_previsti,
        deltas,
    )


@router.post("/{expense_id}/close-preview", response_model=RecurringExpenseClosePreviewResponse)
def preview_close_recurring_expense(
    expense_id: int,
    data: RecurringExpenseCloseRequest,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Anteprima impatto chiusura/rettifica spesa ricorrente."""
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

    (
        cutoff_occurrence_date,
        created_last_due_movement,
        storni_creati_previsti,
        storni_rimossi_previsti,
        deltas,
    ) = _estimate_close_deltas(session, trainer, expense, data)

    today = date.today()
    saldo_attuale_before = _compute_saldo_for_preview(session, trainer, as_of=today)
    saldo_previsto_before = _compute_saldo_for_preview(session, trainer, as_of=None)
    delta_saldo_attuale = round(sum(amount for when, amount in deltas if when <= today), 2)
    delta_saldo_previsto = round(sum(amount for _, amount in deltas), 2)

    return RecurringExpenseClosePreviewResponse(
        cutoff_key=data.effective_mese_anno_key,
        cutoff_data=cutoff_occurrence_date,
        created_last_due_movement=created_last_due_movement,
        storni_creati_previsti=storni_creati_previsti,
        storni_rimossi_previsti=storni_rimossi_previsti,
        saldo_attuale_before=saldo_attuale_before,
        saldo_attuale_after=round(saldo_attuale_before + delta_saldo_attuale, 2),
        saldo_previsto_before=saldo_previsto_before,
        saldo_previsto_after=round(saldo_previsto_before + delta_saldo_previsto, 2),
        delta_saldo_attuale=delta_saldo_attuale,
        delta_saldo_previsto=delta_saldo_previsto,
        delta_netto=delta_saldo_previsto,
    )


# ════════════════════════════════════════════════════════════
# POST: Chiudi spesa ricorrente (con storno selettivo)
# ════════════════════════════════════════════════════════════

@router.post("/{expense_id}/close", response_model=RecurringExpenseCloseResponse)
def close_recurring_expense(
    expense_id: int,
    data: RecurringExpenseCloseRequest,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Chiude o rettifica una spesa ricorrente preservando lo storico reale.

    Regole:
    - Movimenti > cutoff: devono essere stornati (ENTRATA speculare)
    - Movimenti <= cutoff: NON devono avere storno attivo
    - Se `last_occurrence_due=true`, l'occorrenza cutoff viene assicurata nel ledger
    - Endpoint idempotente: puo' essere richiamato anche su spesa gia' disattivata
      per rettificare il cutoff senza errori bloccanti.
    """
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

    cutoff_occurrence_date = _resolve_occurrence_date(expense, data.effective_mese_anno_key)
    if not cutoff_occurrence_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Occorrenza cutoff non valida per questa spesa ricorrente",
        )

    cutoff_date = (
        cutoff_occurrence_date
        if data.last_occurrence_due
        else cutoff_occurrence_date - timedelta(days=1)
    )

    created_last_due_movement = False

    # Se il cutoff resta dovuto, garantisci la presenza del movimento di cutoff.
    if data.last_occurrence_due:
        already_present = session.exec(
            select(CashMovement.id).where(
                CashMovement.trainer_id == trainer.id,
                CashMovement.id_spesa_ricorrente == expense.id,
                CashMovement.mese_anno == data.effective_mese_anno_key,
                CashMovement.deleted_at == None,
            )
        ).first()

        if not already_present:
            movement = CashMovement(
                trainer_id=trainer.id,
                data_effettiva=cutoff_occurrence_date,
                tipo="USCITA",
                categoria=expense.categoria or "SPESA_FISSA",
                importo=expense.importo,
                note=f"Spesa ricorrente (chiusura): {expense.nome}",
                operatore="CONFERMA_CHIUSURA",
                id_spesa_ricorrente=expense.id,
                mese_anno=data.effective_mese_anno_key,
            )
            session.add(movement)
            session.flush()
            log_audit(session, "movement", movement.id, "CREATE", trainer.id)
            created_last_due_movement = True

    linked_expense_movements = session.exec(
        select(CashMovement).where(
            CashMovement.trainer_id == trainer.id,
            CashMovement.id_spesa_ricorrente == expense.id,
            CashMovement.id_contratto == None,
            CashMovement.tipo == "USCITA",
            CashMovement.deleted_at == None,
        )
    ).all()

    storni_creati = 0
    storni_rimossi = 0
    now = datetime.now(timezone.utc)

    for movement in linked_expense_movements:
        should_be_storned = movement.data_effettiva > cutoff_date
        storno_key = f"STORNO:{movement.id}"

        active_storno = session.exec(
            select(CashMovement).where(
                CashMovement.trainer_id == trainer.id,
                CashMovement.id_spesa_ricorrente == expense.id,
                CashMovement.tipo == "ENTRATA",
                CashMovement.mese_anno == storno_key,
                CashMovement.deleted_at == None,
            )
        ).first()

        if should_be_storned:
            if active_storno:
                continue

            deleted_storno = session.exec(
                select(CashMovement).where(
                    CashMovement.trainer_id == trainer.id,
                    CashMovement.id_spesa_ricorrente == expense.id,
                    CashMovement.tipo == "ENTRATA",
                    CashMovement.mese_anno == storno_key,
                    CashMovement.deleted_at != None,
                )
            ).first()

            if deleted_storno:
                old_deleted_at = deleted_storno.deleted_at
                deleted_storno.deleted_at = None
                deleted_storno.data_effettiva = movement.data_effettiva
                deleted_storno.importo = movement.importo
                deleted_storno.categoria = "STORNO_SPESA_FISSA"
                deleted_storno.note = f"Storno spesa ricorrente: {expense.nome} ({movement.mese_anno})"
                deleted_storno.operatore = "STORNO_UTENTE"
                session.add(deleted_storno)
                log_audit(session, "movement", deleted_storno.id, "RESTORE", trainer.id, {
                    "deleted_at": {"old": str(old_deleted_at), "new": None},
                })
                storni_creati += 1
                continue

            storno = CashMovement(
                trainer_id=trainer.id,
                data_effettiva=movement.data_effettiva,
                tipo="ENTRATA",
                categoria="STORNO_SPESA_FISSA",
                importo=movement.importo,
                note=f"Storno spesa ricorrente: {expense.nome} ({movement.mese_anno})",
                operatore="STORNO_UTENTE",
                id_spesa_ricorrente=expense.id,
                mese_anno=storno_key,
            )
            session.add(storno)
            session.flush()
            log_audit(session, "movement", storno.id, "CREATE", trainer.id)
            storni_creati += 1
            continue

        if active_storno:
            active_storno.deleted_at = now
            session.add(active_storno)
            log_audit(session, "movement", active_storno.id, "DELETE", trainer.id)
            storni_rimossi += 1

    was_active = expense.attiva
    old_disattivazione = expense.data_disattivazione
    expense.attiva = False
    if was_active:
        expense.data_disattivazione = now
    session.add(expense)
    changes = {
        "close_strategy": {
            "effective_mese_anno_key": data.effective_mese_anno_key,
            "last_occurrence_due": data.last_occurrence_due,
            "cutoff_data": str(cutoff_occurrence_date),
            "storni_creati": storni_creati,
            "storni_rimossi": storni_rimossi,
        },
    }
    if was_active:
        changes["attiva"] = {"old": True, "new": False}
    if old_disattivazione != expense.data_disattivazione:
        changes["data_disattivazione"] = {
            "old": str(old_disattivazione) if old_disattivazione else None,
            "new": str(expense.data_disattivazione) if expense.data_disattivazione else None,
        }
    log_audit(session, "recurring_expense", expense.id, "UPDATE", trainer.id, changes)
    session.commit()

    return RecurringExpenseCloseResponse(
        cutoff_key=data.effective_mese_anno_key,
        cutoff_data=cutoff_occurrence_date,
        created_last_due_movement=created_last_due_movement,
        storni_creati=storni_creati,
        storni_rimossi=storni_rimossi,
    )


# ════════════════════════════════════════════════════════════
# DELETE: Elimina spesa ricorrente
# ════════════════════════════════════════════════════════════

@router.delete("/{expense_id}", response_model=RecurringExpenseDeleteResponse)
def delete_recurring_expense(
    expense_id: int,
    delete_movements: bool = Query(
        default=False,
        description="Se true, elimina anche i movimenti ledger collegati alla spesa ricorrente",
    ),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Elimina una spesa ricorrente con cleanup ledger opzionale."""
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

    deleted_movements = 0
    now = datetime.now(timezone.utc)

    if delete_movements:
        linked_movements = session.exec(
            select(CashMovement).where(
                CashMovement.trainer_id == trainer.id,
                CashMovement.id_spesa_ricorrente == expense.id,
                CashMovement.id_contratto == None,
                CashMovement.deleted_at == None,
            )
        ).all()

        for movement in linked_movements:
            movement.deleted_at = now
            session.add(movement)
            log_audit(session, "movement", movement.id, "DELETE", trainer.id)

        deleted_movements = len(linked_movements)

    expense.deleted_at = now
    session.add(expense)
    log_audit(session, "recurring_expense", expense.id, "DELETE", trainer.id)
    session.commit()

    return RecurringExpenseDeleteResponse(deleted_movements=deleted_movements)

