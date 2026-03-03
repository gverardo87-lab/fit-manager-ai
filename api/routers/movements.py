# api/routers/movements.py
"""
Endpoint Movimenti Cassa — Ledger con Bouncer Pattern.

Sicurezza multi-tenant:
- trainer_id diretto su movimenti_cassa (Bouncer filtra per trainer)
- trainer_id iniettato dal JWT, mai dal body

Ledger Integrity:
- POST crea SOLO movimenti manuali (niente id_contratto/id_rata/id_cliente)
- DELETE elimina movimenti manuali e spese fisse (contratti protetti)
- I movimenti di sistema (ACCONTO_CONTRATTO, PAGAMENTO_RATA)
  vengono creati esclusivamente da create_contract e pay_rate.

Spese Ricorrenti — Paradigma "Conferma & Registra":
- GET /pending-expenses: calcola quali spese sono dovute per un mese
  ma non hanno ancora un CashMovement confermato.
- POST /confirm-expenses: l'utente conferma esplicitamente le spese,
  creando CashMovement reali nel ledger.
- GET /stats: pure read-only, zero side effects. Le cifre derivano
  SOLO da CashMovement confermati.
"""

import calendar
import logging
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import extract, case
from sqlmodel import Session, select, func, text

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.movement import CashMovement
from api.models.rate import Rate
from api.models.contract import Contract
from api.models.recurring_expense import RecurringExpense
from api.schemas.financial import (
    MovementManualCreate, MovementResponse,
)
from api.routers._audit import log_audit

logger = logging.getLogger("fitmanager.api")
router = APIRouter(prefix="/movements", tags=["movements"])


# ════════════════════════════════════════════════════════════
# SALDO ENGINE: Calcolo saldo cassa cumulativo
# ════════════════════════════════════════════════════════════

_signed_importo = case(
    (CashMovement.tipo == "ENTRATA", CashMovement.importo),
    else_=-CashMovement.importo,
)


def _build_movement_filters(
    trainer: Trainer,
    *,
    as_of: Optional[date] = None,
) -> list:
    """Filtri base movimenti per trainer con opzionale limite data."""
    filters = [
        CashMovement.trainer_id == trainer.id,
        CashMovement.deleted_at == None,
    ]
    if trainer.data_saldo_iniziale:
        filters.append(CashMovement.data_effettiva >= trainer.data_saldo_iniziale)
    if as_of is not None:
        filters.append(CashMovement.data_effettiva <= as_of)
    return filters


def _compute_saldo(
    session: Session,
    trainer: Trainer,
    *,
    as_of: Optional[date] = None,
) -> float:
    """
    Saldo cassa = saldo_iniziale + SUM(signed movements).

    - as_of=None: include anche movimenti futuri (saldo proiettato)
    - as_of=today: saldo reale disponibile a oggi
    """
    q = select(func.coalesce(func.sum(_signed_importo), 0)).where(
        *_build_movement_filters(trainer, as_of=as_of)
    )
    result = float(session.exec(q).one())
    return round(trainer.saldo_iniziale_cassa + result, 2)


def _compute_saldo_before(session: Session, trainer: Trainer, before_date: date) -> float:
    """Saldo cumulativo fino a (esclusa) una data specifica."""
    q = select(func.coalesce(func.sum(_signed_importo), 0)).where(
        CashMovement.trainer_id == trainer.id,
        CashMovement.deleted_at == None,
        CashMovement.data_effettiva < before_date,
    )
    if trainer.data_saldo_iniziale:
        q = q.where(CashMovement.data_effettiva >= trainer.data_saldo_iniziale)
    result = float(session.exec(q).one())
    return round(trainer.saldo_iniziale_cassa + result, 2)


# ════════════════════════════════════════════════════════════
# GET: Saldo di cassa attuale
# ════════════════════════════════════════════════════════════

class CashProtectionResponse(BaseModel):
    stato: str
    soglia_sicurezza: float
    margine_sicurezza: float
    copertura_giorni: float
    uscite_fisse_mensili_stimate: float
    burn_rate_variabile_mensile: float
    costo_operativo_mensile: float


class BalanceResponse(BaseModel):
    saldo_attuale: float
    saldo_previsto: float
    delta_movimenti_futuri: float
    saldo_iniziale: float
    totale_entrate_storico: float
    totale_uscite_storico: float
    totale_entrate_future_confermate: float
    totale_uscite_future_confermate: float
    data_riferimento: date
    data_saldo_iniziale: Optional[date]
    protezione_cassa: CashProtectionResponse


def _estimate_monthly_expense(expense: RecurringExpense) -> float:
    """Stima mensile pesata della spesa ricorrente in base alla frequenza."""
    freq = expense.frequenza or "MENSILE"
    if freq == "SETTIMANALE":
        return expense.importo * 4.33
    if freq == "TRIMESTRALE":
        return expense.importo / 3
    if freq == "SEMESTRALE":
        return expense.importo / 6
    if freq == "ANNUALE":
        return expense.importo / 12
    return expense.importo


def _compute_variable_burn_rate(session: Session, trainer: Trainer, today: date) -> float:
    """Media uscite variabili/mese sugli ultimi 3 mesi chiusi."""
    past_months = _prev_months(today.year, today.month, 3)
    if not past_months:
        return 0.0

    totals: list[float] = []
    for anno, mese in past_months:
        month_total = session.exec(
            select(func.coalesce(func.sum(CashMovement.importo), 0)).where(
                CashMovement.trainer_id == trainer.id,
                CashMovement.tipo == "USCITA",
                CashMovement.id_spesa_ricorrente == None,
                extract("year", CashMovement.data_effettiva) == anno,
                extract("month", CashMovement.data_effettiva) == mese,
                CashMovement.deleted_at == None,
            )
        ).one()
        totals.append(float(month_total))

    return round(sum(totals) / len(totals), 2) if totals else 0.0


def _build_cash_protection(
    session: Session,
    trainer: Trainer,
    *,
    today: date,
    saldo_attuale: float,
) -> CashProtectionResponse:
    """
    Protezione Cassa:
    - soglia_sicurezza: 45 giorni di costo operativo medio (fisse + burn variabile)
    - margine_sicurezza: saldo reale - soglia
    - copertura_giorni: autonomia stimata con saldo reale corrente
    """
    recurring = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.trainer_id == trainer.id,
            RecurringExpense.attiva == True,
            RecurringExpense.deleted_at == None,
        )
    ).all()

    uscite_fisse_stimate = round(sum(_estimate_monthly_expense(e) for e in recurring), 2)
    burn_rate = _compute_variable_burn_rate(session, trainer, today)
    costo_operativo_mensile = round(uscite_fisse_stimate + burn_rate, 2)

    if costo_operativo_mensile <= 0:
        return CashProtectionResponse(
            stato="OK",
            soglia_sicurezza=0.0,
            margine_sicurezza=round(saldo_attuale, 2),
            copertura_giorni=9999.0,
            uscite_fisse_mensili_stimate=uscite_fisse_stimate,
            burn_rate_variabile_mensile=burn_rate,
            costo_operativo_mensile=costo_operativo_mensile,
        )

    soglia_sicurezza = round(costo_operativo_mensile * 1.5, 2)  # 45 giorni
    margine_sicurezza = round(saldo_attuale - soglia_sicurezza, 2)
    costo_giornaliero = costo_operativo_mensile / 30
    copertura_giorni = round(saldo_attuale / costo_giornaliero, 1)

    if saldo_attuale < 0 or copertura_giorni < 15:
        stato = "CRITICO"
    elif copertura_giorni < 45:
        stato = "ATTENZIONE"
    else:
        stato = "OK"

    return CashProtectionResponse(
        stato=stato,
        soglia_sicurezza=soglia_sicurezza,
        margine_sicurezza=margine_sicurezza,
        copertura_giorni=copertura_giorni,
        uscite_fisse_mensili_stimate=uscite_fisse_stimate,
        burn_rate_variabile_mensile=burn_rate,
        costo_operativo_mensile=costo_operativo_mensile,
    )


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Saldo di cassa attuale — computed on read."""
    today = date.today()

    real_filters = _build_movement_filters(trainer, as_of=today)
    future_filters = [
        CashMovement.trainer_id == trainer.id,
        CashMovement.deleted_at == None,
        CashMovement.data_effettiva > today,
    ]
    if trainer.data_saldo_iniziale:
        future_filters.append(CashMovement.data_effettiva >= trainer.data_saldo_iniziale)

    totale_entrate_reali = float(session.exec(
        select(func.coalesce(func.sum(CashMovement.importo), 0)).where(
            *real_filters,
            CashMovement.tipo == "ENTRATA",
        )
    ).one())

    totale_uscite_reali = float(session.exec(
        select(func.coalesce(func.sum(CashMovement.importo), 0)).where(
            *real_filters,
            CashMovement.tipo == "USCITA",
        )
    ).one())

    totale_entrate_future = float(session.exec(
        select(func.coalesce(func.sum(CashMovement.importo), 0)).where(
            *future_filters,
            CashMovement.tipo == "ENTRATA",
        )
    ).one())

    totale_uscite_future = float(session.exec(
        select(func.coalesce(func.sum(CashMovement.importo), 0)).where(
            *future_filters,
            CashMovement.tipo == "USCITA",
        )
    ).one())

    saldo_attuale = _compute_saldo(session, trainer, as_of=today)
    saldo_previsto = _compute_saldo(session, trainer)
    delta_future = round(saldo_previsto - saldo_attuale, 2)
    protezione = _build_cash_protection(
        session,
        trainer,
        today=today,
        saldo_attuale=saldo_attuale,
    )

    return BalanceResponse(
        saldo_attuale=saldo_attuale,
        saldo_previsto=saldo_previsto,
        delta_movimenti_futuri=delta_future,
        saldo_iniziale=trainer.saldo_iniziale_cassa,
        totale_entrate_storico=round(totale_entrate_reali, 2),
        totale_uscite_storico=round(totale_uscite_reali, 2),
        totale_entrate_future_confermate=round(totale_entrate_future, 2),
        totale_uscite_future_confermate=round(totale_uscite_future, 2),
        data_riferimento=today,
        data_saldo_iniziale=trainer.data_saldo_iniziale,
        protezione_cassa=protezione,
    )


# ════════════════════════════════════════════════════════════
# OCCURRENCE ENGINE: Calcolo scadenze spese ricorrenti
# ════════════════════════════════════════════════════════════

VALID_FREQUENCIES = {"MENSILE", "SETTIMANALE", "TRIMESTRALE", "SEMESTRALE", "ANNUALE"}


def _get_start_date(expense: RecurringExpense) -> date:
    """Restituisce la data di ancoraggio per la spesa (data_inizio > data_creazione > fallback)."""
    if expense.data_inizio:
        return expense.data_inizio
    if expense.data_creazione:
        return expense.data_creazione.date() if hasattr(expense.data_creazione, 'date') else expense.data_creazione
    return date(2026, 1, 1)


def _get_occurrences_in_month(
    expense: RecurringExpense, anno: int, mese: int
) -> list[tuple[date, str]]:
    """
    Calcola le occorrenze di una spesa ricorrente in un dato mese.

    Returns: lista di (data_effettiva, mese_anno_key) per ogni occorrenza.
    La chiave mese_anno e' usata per la deduplicazione (UNIQUE constraint).

    Ancoraggio: usa data_inizio (scelta dall'utente) per determinare
    il mese di partenza e il ciclo delle frequenze non-mensili.
    Cross-year safe: usa mese assoluto (anno*12 + mese) per modular arithmetic.

    Frequenze supportate:
    - MENSILE: 1 occorrenza per mese, key = "2026-02"
    - SETTIMANALE: ~4 per mese (ogni 7 giorni), key = "2026-02-W1"...
    - TRIMESTRALE: 1 ogni 3 mesi (ancorata a data_inizio), key = "2026-02"
    - SEMESTRALE: 1 ogni 6 mesi (ancorata a data_inizio), key = "2026-02"
    - ANNUALE: 1 per anno (mese anniversario di data_inizio), key = "2026"
    """
    days_in_month = calendar.monthrange(anno, mese)[1]
    freq = expense.frequenza or "MENSILE"
    start = _get_start_date(expense)

    # Guard: spesa non ancora attiva nel mese target
    last_day_of_month = date(anno, mese, days_in_month)
    if start > last_day_of_month:
        return []

    if freq == "MENSILE":
        giorno = min(expense.giorno_scadenza, days_in_month)
        return [(date(anno, mese, giorno), f"{anno:04d}-{mese:02d}")]

    if freq == "SETTIMANALE":
        base = min(expense.giorno_scadenza, 7)
        occurrences = []
        day = base
        week = 1
        while day <= days_in_month:
            key = f"{anno:04d}-{mese:02d}-W{week}"
            occurrences.append((date(anno, mese, day), key))
            day += 7
            week += 1
        return occurrences

    # Cross-year safe: mese assoluto per TRIM/SEM/ANN
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

    # Frequenza sconosciuta: fallback a MENSILE
    giorno = min(expense.giorno_scadenza, days_in_month)
    return [(date(anno, mese, giorno), f"{anno:04d}-{mese:02d}")]


# ════════════════════════════════════════════════════════════
# GET: Spese ricorrenti in attesa di conferma per un mese
# ════════════════════════════════════════════════════════════

class PendingExpenseItem(BaseModel):
    """Singola occorrenza di spesa ricorrente non ancora confermata."""
    id_spesa: int
    nome: str
    categoria: Optional[str] = None
    importo: float
    frequenza: str
    data_prevista: date
    mese_anno_key: str


class PendingExpensesResponse(BaseModel):
    """Risposta: lista spese in attesa + totale."""
    items: list[PendingExpenseItem]
    totale_pending: float


@router.get("/pending-expenses", response_model=PendingExpensesResponse)
def get_pending_expenses(
    anno: int = Query(ge=2000, le=2100),
    mese: int = Query(ge=1, le=12),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Calcola le spese ricorrenti in attesa di conferma per il mese specificato.

    Per ogni spesa attiva, verifica se esiste gia' un CashMovement
    per quella occorrenza. Se non esiste, la include nella lista pending.
    L'utente puo' poi confermare con POST /confirm-expenses.
    """
    recurring = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.trainer_id == trainer.id,
            RecurringExpense.attiva == True,
            RecurringExpense.deleted_at == None,
        )
    ).all()

    if not recurring:
        return PendingExpensesResponse(items=[], totale_pending=0)

    # Batch fetch: tutti i CashMovement ricorrenti del mese per il trainer
    existing = session.exec(
        select(CashMovement.id_spesa_ricorrente, CashMovement.mese_anno).where(
            CashMovement.trainer_id == trainer.id,
            CashMovement.id_spesa_ricorrente != None,
            CashMovement.deleted_at == None,
        )
    ).all()
    existing_keys: set[tuple[int, str]] = {(r[0], r[1]) for r in existing}

    pending_items: list[PendingExpenseItem] = []

    for expense in recurring:
        occurrences = _get_occurrences_in_month(expense, anno, mese)
        for data_prevista, mese_anno_key in occurrences:
            if (expense.id, mese_anno_key) not in existing_keys:
                pending_items.append(PendingExpenseItem(
                    id_spesa=expense.id,
                    nome=expense.nome,
                    categoria=expense.categoria,
                    importo=expense.importo,
                    frequenza=expense.frequenza or "MENSILE",
                    data_prevista=data_prevista,
                    mese_anno_key=mese_anno_key,
                ))

    pending_items.sort(key=lambda x: (x.data_prevista, x.nome.lower()))
    totale = sum(item.importo for item in pending_items)

    return PendingExpensesResponse(items=pending_items, totale_pending=round(totale, 2))


# ════════════════════════════════════════════════════════════
# POST: Conferma spese ricorrenti → crea CashMovement
# ════════════════════════════════════════════════════════════

class ConfirmExpenseItem(BaseModel):
    """Singolo item da confermare (id_spesa + chiave deduplicazione)."""
    model_config = {"extra": "forbid"}
    id_spesa: int
    mese_anno_key: str


class ConfirmExpensesRequest(BaseModel):
    """Body per conferma spese ricorrenti."""
    model_config = {"extra": "forbid"}
    items: list[ConfirmExpenseItem]


class ConfirmExpensesResponse(BaseModel):
    """Risposta: quanti CashMovement creati + totale importo."""
    created: int
    totale: float


@router.post("/confirm-expenses", response_model=ConfirmExpensesResponse)
def confirm_expenses(
    data: ConfirmExpensesRequest,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Conferma una o piu' spese ricorrenti per un mese, creando CashMovement nel ledger.

    Bouncer: verifica che ogni id_spesa appartenga al trainer.
    Idempotente: INSERT con NOT EXISTS previene duplicati.
    Atomico: singolo commit per tutti i movimenti.
    """
    if not data.items:
        return ConfirmExpensesResponse(created=0, totale=0)

    # Batch fetch spese del trainer (Bouncer)
    expense_ids = list({item.id_spesa for item in data.items})
    expenses = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.id.in_(expense_ids),
            RecurringExpense.trainer_id == trainer.id,
            RecurringExpense.attiva == True,
            RecurringExpense.deleted_at == None,
        )
    ).all()
    expense_map: dict[int, RecurringExpense] = {e.id: e for e in expenses}

    created = 0
    totale = 0.0

    for item in data.items:
        expense = expense_map.get(item.id_spesa)
        if not expense:
            continue  # Silently skip: spesa non trovata o non del trainer

        # Calcola data_effettiva dalla chiave (la key codifica il periodo)
        # Per spese annuali, start_month e' necessario (la key "YYYY" non contiene il mese)
        start = _get_start_date(expense)
        data_effettiva = _date_from_mese_anno_key(
            item.mese_anno_key, expense.giorno_scadenza, start.month
        )
        if not data_effettiva:
            continue

        # Hardening: accetta solo chiavi coerenti con il ciclo reale della spesa.
        expected_keys = {
            key
            for _, key in _get_occurrences_in_month(
                expense, data_effettiva.year, data_effettiva.month
            )
        }
        if item.mese_anno_key not in expected_keys:
            continue

        result = session.execute(
            text("""
                INSERT INTO movimenti_cassa
                    (trainer_id, data_effettiva, tipo, categoria, importo,
                     note, operatore, id_spesa_ricorrente, mese_anno)
                SELECT :trainer_id, :data_effettiva, :tipo, :categoria, :importo,
                       :note, :operatore, :id_spesa, :mese_anno
                WHERE NOT EXISTS (
                    SELECT 1 FROM movimenti_cassa
                    WHERE trainer_id = :trainer_id
                      AND id_spesa_ricorrente = :id_spesa
                      AND mese_anno = :mese_anno
                      AND deleted_at IS NULL
                )
            """),
            {
                "trainer_id": trainer.id,
                "data_effettiva": data_effettiva.isoformat(),
                "tipo": "USCITA",
                "categoria": expense.categoria or "SPESA_FISSA",
                "importo": expense.importo,
                "note": f"Spesa ricorrente: {expense.nome}",
                "operatore": "CONFERMA_UTENTE",
                "id_spesa": expense.id,
                "mese_anno": item.mese_anno_key,
            },
        )
        if result.rowcount > 0:
            created += 1
            totale += expense.importo

    if created > 0:
        session.commit()
        logger.info(
            "Confirm: %d spese fisse confermate (trainer %d, totale %.2f)",
            created, trainer.id, totale,
        )

    return ConfirmExpensesResponse(created=created, totale=round(totale, 2))


def _date_from_mese_anno_key(
    key: str, giorno_scadenza: int, start_month: Optional[int] = None
) -> Optional[date]:
    """
    Ricostruisce data_effettiva dalla chiave mese_anno.

    Formati: "2026-02" (mensile/trim/sem), "2026-02-W1" (settimanale), "2026" (annuale).
    Per chiavi annuali ("YYYY"), start_month e' necessario per ricostruire la data.
    """
    parts = key.split("-")
    try:
        anno = int(parts[0])
        if len(parts) == 1:
            # ANNUALE: "2026" — usa start_month dalla spesa ricorrente
            if not start_month:
                return None
            days_in_month = calendar.monthrange(anno, start_month)[1]
            giorno = min(giorno_scadenza, days_in_month)
            return date(anno, start_month, giorno)
        mese = int(parts[1])
        days_in_month = calendar.monthrange(anno, mese)[1]
        if len(parts) == 3 and parts[2].startswith("W"):
            # SETTIMANALE: "2026-02-W1"
            week_num = int(parts[2][1:])
            base = min(giorno_scadenza, 7)
            day = base + (week_num - 1) * 7
            if day > days_in_month:
                return None
            return date(anno, mese, day)
        # MENSILE/TRIM/SEM: "2026-02"
        giorno = min(giorno_scadenza, days_in_month)
        return date(anno, mese, giorno)
    except (ValueError, IndexError):
        return None


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
    data_da: Optional[date] = Query(default=None, description="Range date: da (override anno/mese)"),
    data_a: Optional[date] = Query(default=None, description="Range date: a (override anno/mese)"),
    id_cliente: Optional[int] = Query(default=None, description="Filtra per cliente"),
):
    """
    Lista movimenti del trainer autenticato con paginazione e filtri.

    Filtri date: data_da/data_a hanno priorita' su anno/mese.
    Se data_da/data_a sono forniti, anno e mese vengono ignorati.
    """

    # Base query con Bouncer (escludi eliminati)
    query = select(CashMovement).where(CashMovement.trainer_id == trainer.id, CashMovement.deleted_at == None)

    # Filtri date: range ha priorita' su anno/mese
    if data_da is not None or data_a is not None:
        if data_da is not None:
            query = query.where(CashMovement.data_effettiva >= data_da)
        if data_a is not None:
            query = query.where(CashMovement.data_effettiva <= data_a)
    else:
        if anno is not None:
            query = query.where(extract("year", CashMovement.data_effettiva) == anno)
        if mese is not None:
            query = query.where(extract("month", CashMovement.data_effettiva) == mese)
    if tipo is not None:
        query = query.where(CashMovement.tipo == tipo)
    if id_cliente is not None:
        query = query.where(CashMovement.id_cliente == id_cliente)

    # Subquery una sola volta — riusata per count e sum
    subq = query.subquery()

    # Count dalla stessa query base (zero duplicazione filtri)
    total = session.exec(
        select(func.count()).select_from(subq)
    ).one()

    # Saldo totale del periodo filtrato (per running balance)
    # IMPORTANTE: usare subq.c.* (colonne del subquery) e NON CashMovement.*
    # per evitare cross-join implicito con la tabella originale
    saldo_totale_periodo = float(session.exec(
        select(func.coalesce(func.sum(
            case(
                (subq.c.tipo == "ENTRATA", subq.c.importo),
                else_=-subq.c.importo,
            )
        ), 0))
    ).one())

    # Saldo pre-periodo: tutto cio' che viene prima del periodo filtrato
    saldo_pre = _compute_saldo_before(session, trainer, date(anno or 2000, mese or 1, 1)) if anno and mese else 0.0

    # Paginazione
    offset = (page - 1) * page_size
    query = query.order_by(CashMovement.data_effettiva.desc(), CashMovement.id.desc()).offset(offset).limit(page_size)
    movements = session.exec(query).all()

    # saldo_fine_periodo: saldo alla fine di tutte le righe del periodo
    saldo_fine_periodo = round(saldo_pre + saldo_totale_periodo, 2)

    return {
        "items": [MovementResponse.model_validate(m) for m in movements],
        "total": total,
        "page": page,
        "page_size": page_size,
        "saldo_fine_periodo": saldo_fine_periodo,
    }


# ════════════════════════════════════════════════════════════
# GET: Statistiche mensili — Single Source of Truth (pure read)
# ════════════════════════════════════════════════════════════

class ChartDataPoint(BaseModel):
    giorno: int
    entrate: float
    uscite: float
    saldo: float = 0.0

class MovementStatsResponse(BaseModel):
    totale_entrate: float
    totale_uscite_variabili: float
    totale_uscite_fisse: float
    margine_netto: float
    saldo_inizio_mese: float = 0.0
    saldo_fine_mese: float = 0.0
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

    Pure read-only: zero side effects. TUTTE le cifre derivano
    da CashMovement gia' confermati dall'utente:
    - entrate: tipo=ENTRATA
    - uscite variabili: tipo=USCITA AND id_spesa_ricorrente IS NULL
    - uscite fisse: tipo=USCITA AND id_spesa_ricorrente IS NOT NULL
    - margine netto: entrate - uscite_variabili - uscite_fisse
    """
    # Tutti i movimenti del mese (single query, escludi eliminati)
    movements = session.exec(
        select(CashMovement).where(
            CashMovement.trainer_id == trainer.id,
            extract("year", CashMovement.data_effettiva) == anno,
            extract("month", CashMovement.data_effettiva) == mese,
            CashMovement.deleted_at == None,
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

    # Saldo inizio mese: saldo cumulativo fino alla fine del mese precedente
    primo_giorno = date(anno, mese, 1)
    saldo_inizio_mese = _compute_saldo_before(session, trainer, primo_giorno)
    saldo_fine_mese = round(saldo_inizio_mese + margine_netto, 2)

    # Chart data: raggruppamento per giorno del mese + running balance
    days_in_month = calendar.monthrange(anno, mese)[1]
    entrate_per_giorno: dict[int, float] = defaultdict(float)
    uscite_per_giorno: dict[int, float] = defaultdict(float)

    for m in movements:
        day = m.data_effettiva.day
        if m.tipo == "ENTRATA":
            entrate_per_giorno[day] += m.importo
        else:
            uscite_per_giorno[day] += m.importo

    running = saldo_inizio_mese
    chart_data = []
    for d in range(1, days_in_month + 1):
        e = round(entrate_per_giorno.get(d, 0), 2)
        u = round(uscite_per_giorno.get(d, 0), 2)
        running = round(running + e - u, 2)
        chart_data.append(ChartDataPoint(giorno=d, entrate=e, uscite=u, saldo=running))

    return MovementStatsResponse(
        totale_entrate=round(totale_entrate, 2),
        totale_uscite_variabili=round(totale_uscite_variabili, 2),
        totale_uscite_fisse=round(totale_uscite_fisse, 2),
        margine_netto=round(margine_netto, 2),
        saldo_inizio_mese=saldo_inizio_mese,
        saldo_fine_mese=saldo_fine_mese,
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
    session.flush()
    log_audit(session, "movement", movement.id, "CREATE", trainer.id)
    session.commit()
    session.refresh(movement)

    return MovementResponse.model_validate(movement)


# ════════════════════════════════════════════════════════════
# DELETE: Elimina movimento (solo manuali e spese fisse)
# ════════════════════════════════════════════════════════════

@router.delete("/{movement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movement(
    movement_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Elimina un movimento — manuali e spese fisse.

    Bouncer: query singola movement.id + trainer_id.
    Business Rules:
    - Movimenti legati a contratti (id_contratto != null) -> 400 (protetti)
    - Movimenti manuali e spese fisse -> eliminabili
    """
    movement = session.exec(
        select(CashMovement).where(
            CashMovement.id == movement_id,
            CashMovement.trainer_id == trainer.id,
            CashMovement.deleted_at == None,
        )
    ).first()

    if not movement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimento non trovato",
        )

    # Business Rule: movimenti contrattuali sono protetti (acconto, pagamento rata)
    if movement.id_contratto is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile eliminare un movimento di sistema (legato a un contratto)",
        )

    movement.deleted_at = datetime.now(timezone.utc)
    session.add(movement)
    log_audit(session, "movement", movement.id, "DELETE", trainer.id)
    session.commit()


# ════════════════════════════════════════════════════════════
# PUT: Configura saldo iniziale di cassa
# ════════════════════════════════════════════════════════════

class SaldoInizialeUpdate(BaseModel):
    model_config = {"extra": "forbid"}
    saldo_iniziale_cassa: float = Field(ge=-1_000_000, le=1_000_000)
    data_saldo_iniziale: Optional[date] = None


class SaldoInizialeResponse(BaseModel):
    saldo_iniziale_cassa: float
    data_saldo_iniziale: Optional[date]


@router.put("/saldo-iniziale", response_model=SaldoInizialeResponse)
def update_saldo_iniziale(
    data: SaldoInizialeUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Configura il saldo iniziale di cassa del trainer."""
    trainer.saldo_iniziale_cassa = data.saldo_iniziale_cassa
    trainer.data_saldo_iniziale = data.data_saldo_iniziale
    session.add(trainer)
    session.commit()
    session.refresh(trainer)

    return SaldoInizialeResponse(
        saldo_iniziale_cassa=trainer.saldo_iniziale_cassa,
        data_saldo_iniziale=trainer.data_saldo_iniziale,
    )


@router.get("/saldo-iniziale", response_model=SaldoInizialeResponse)
def get_saldo_iniziale(
    trainer: Trainer = Depends(get_current_trainer),
):
    """Ritorna la configurazione saldo iniziale del trainer."""
    return SaldoInizialeResponse(
        saldo_iniziale_cassa=trainer.saldo_iniziale_cassa,
        data_saldo_iniziale=trainer.data_saldo_iniziale,
    )


# ════════════════════════════════════════════════════════════
# GET: Forecast — Proiezione finanziaria prossimi N mesi
# ════════════════════════════════════════════════════════════

MONTH_LABELS = [
    "", "Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
    "Lug", "Ago", "Set", "Ott", "Nov", "Dic",
]


class ForecastMonthData(BaseModel):
    """Proiezione per un singolo mese futuro."""
    mese: int
    anno: int
    label: str                         # "Mar 2026"
    entrate_certe: float               # rate pendenti/parziali
    uscite_fisse: float                # spese ricorrenti
    uscite_variabili_stimate: float    # media storica
    margine_proiettato: float          # entrate - uscite


class ForecastTimelineItem(BaseModel):
    """Singolo evento finanziario futuro nella timeline."""
    data: date
    descrizione: str
    tipo: str                          # "ENTRATA" | "USCITA"
    importo: float
    saldo_cumulativo: float


class ForecastKpi(BaseModel):
    """KPI predittivi di alto livello."""
    entrate_attese_90gg: float
    uscite_previste_90gg: float
    burn_rate_mensile: float           # media uscite ultimi 3 mesi
    margine_proiettato_90gg: float


class ForecastResponse(BaseModel):
    """Proiezione finanziaria completa."""
    kpi: ForecastKpi
    monthly_projection: list[ForecastMonthData]
    timeline: list[ForecastTimelineItem]
    saldo_iniziale: float              # margine del mese corrente


def _next_months(anno: int, mese: int, count: int) -> list[tuple[int, int]]:
    """Restituisce i prossimi N mesi come lista (anno, mese)."""
    result = []
    for _ in range(count):
        mese += 1
        if mese > 12:
            mese = 1
            anno += 1
        result.append((anno, mese))
    return result


def _prev_months(anno: int, mese: int, count: int) -> list[tuple[int, int]]:
    """Restituisce i precedenti N mesi come lista (anno, mese)."""
    result = []
    for _ in range(count):
        mese -= 1
        if mese < 1:
            mese = 12
            anno -= 1
        result.append((anno, mese))
    return result


@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(
    mesi: int = Query(default=3, ge=1, le=6),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Proiezione finanziaria per i prossimi N mesi.

    Pure read-only, zero side effects. Aggrega 3 fonti:
    1. Rate PENDENTE/PARZIALE — entrate certe, raggruppate per mese scadenza
    2. Spese ricorrenti attive — uscite fisse calcolate con occurrence engine
    3. Storico movimenti ultimi 3 mesi — media uscite variabili

    Produce:
    - KPI predittivi (90gg)
    - Proiezione mensile (entrate vs uscite per mese)
    - Timeline cronologica con saldo cumulativo
    """
    today = date.today()
    current_anno, current_mese = today.year, today.month
    future_months = _next_months(current_anno, current_mese, mesi)

    # ── 1. Saldo iniziale: saldo di cassa reale (non piu' margine mese corrente) ──
    saldo_iniziale = _compute_saldo(session, trainer, as_of=today)

    # ── 2. Entrate certe: rate PENDENTE/PARZIALE nei mesi futuri ──
    rates = session.exec(
        select(Rate).join(Contract, Rate.id_contratto == Contract.id).where(
            Contract.trainer_id == trainer.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.data_scadenza > today,
            Rate.deleted_at == None,
            Contract.deleted_at == None,
        )
    ).all()

    entrate_per_mese: dict[tuple[int, int], float] = defaultdict(float)
    timeline_items: list[dict] = []

    for rate in rates:
        key = (rate.data_scadenza.year, rate.data_scadenza.month)
        residuo = round(rate.importo_previsto - rate.importo_saldato, 2)
        entrate_per_mese[key] += residuo
        timeline_items.append({
            "data": rate.data_scadenza,
            "descrizione": f"Rata #{rate.id} — €{residuo:.0f}",
            "tipo": "ENTRATA",
            "importo": residuo,
        })

    # ── 3. Uscite fisse: spese ricorrenti per ogni mese futuro ──
    recurring = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.trainer_id == trainer.id,
            RecurringExpense.attiva == True,
            RecurringExpense.deleted_at == None,
        )
    ).all()

    uscite_fisse_per_mese: dict[tuple[int, int], float] = defaultdict(float)

    for a, m in future_months:
        for expense in recurring:
            occurrences = _get_occurrences_in_month(expense, a, m)
            for data_prevista, _key in occurrences:
                importo = expense.importo
                uscite_fisse_per_mese[(a, m)] += importo
                timeline_items.append({
                    "data": data_prevista,
                    "descrizione": expense.nome,
                    "tipo": "USCITA",
                    "importo": importo,
                })

    # ── 4. Uscite variabili stimate: media ultimi 3 mesi ──
    past_months = _prev_months(current_anno, current_mese, 3)
    past_var_totals: list[float] = []

    for pa, pm in past_months:
        month_var = session.exec(
            select(func.coalesce(func.sum(CashMovement.importo), 0)).where(
                CashMovement.trainer_id == trainer.id,
                CashMovement.tipo == "USCITA",
                CashMovement.id_spesa_ricorrente == None,
                extract("year", CashMovement.data_effettiva) == pa,
                extract("month", CashMovement.data_effettiva) == pm,
                CashMovement.deleted_at == None,
            )
        ).one()
        past_var_totals.append(float(month_var))

    avg_variabili = round(sum(past_var_totals) / len(past_var_totals), 2) if past_var_totals else 0

    # ── 5. Assembla proiezione mensile ──
    monthly_projection: list[ForecastMonthData] = []

    for a, m in future_months:
        entrate = round(entrate_per_mese.get((a, m), 0), 2)
        fisse = round(uscite_fisse_per_mese.get((a, m), 0), 2)
        variabili = avg_variabili
        margine = round(entrate - fisse - variabili, 2)

        monthly_projection.append(ForecastMonthData(
            mese=m,
            anno=a,
            label=f"{MONTH_LABELS[m]} {a}",
            entrate_certe=entrate,
            uscite_fisse=fisse,
            uscite_variabili_stimate=variabili,
            margine_proiettato=margine,
        ))

    # ── 6. KPI predittivi ──
    entrate_90 = sum(mp.entrate_certe for mp in monthly_projection)
    uscite_90 = sum(mp.uscite_fisse + mp.uscite_variabili_stimate for mp in monthly_projection)
    past_total_uscite = []
    for pa, pm in past_months:
        month_tot = session.exec(
            select(func.coalesce(func.sum(CashMovement.importo), 0)).where(
                CashMovement.trainer_id == trainer.id,
                CashMovement.tipo == "USCITA",
                extract("year", CashMovement.data_effettiva) == pa,
                extract("month", CashMovement.data_effettiva) == pm,
                CashMovement.deleted_at == None,
            )
        ).one()
        past_total_uscite.append(float(month_tot))

    burn_rate = round(sum(past_total_uscite) / len(past_total_uscite), 2) if past_total_uscite else 0

    kpi = ForecastKpi(
        entrate_attese_90gg=round(entrate_90, 2),
        uscite_previste_90gg=round(uscite_90, 2),
        burn_rate_mensile=burn_rate,
        margine_proiettato_90gg=round(entrate_90 - uscite_90, 2),
    )

    # ── 7. Timeline cronologica con saldo cumulativo ──
    # Filtra solo eventi nei mesi futuri selezionati
    future_month_set = set(future_months)
    filtered_timeline = [
        t for t in timeline_items
        if (t["data"].year, t["data"].month) in future_month_set
    ]
    filtered_timeline.sort(key=lambda t: t["data"])

    running_balance = saldo_iniziale
    timeline: list[ForecastTimelineItem] = []
    for t in filtered_timeline:
        if t["tipo"] == "ENTRATA":
            running_balance += t["importo"]
        else:
            running_balance -= t["importo"]

        timeline.append(ForecastTimelineItem(
            data=t["data"],
            descrizione=t["descrizione"],
            tipo=t["tipo"],
            importo=round(t["importo"], 2),
            saldo_cumulativo=round(running_balance, 2),
        ))

    return ForecastResponse(
        kpi=kpi,
        monthly_projection=monthly_projection,
        timeline=timeline,
        saldo_iniziale=saldo_iniziale,
    )
