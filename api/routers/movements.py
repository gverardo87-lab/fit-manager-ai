# api/routers/movements.py
"""
Endpoint Movimenti Cassa — Ledger con Bouncer Pattern.

Sicurezza multi-tenant:
- trainer_id diretto su movimenti_cassa (Bouncer filtra per trainer)
- trainer_id iniettato dal JWT, mai dal body

Ledger Integrity:
- POST crea SOLO movimenti manuali (niente id_contratto/id_rata/id_cliente)
- DELETE elimina movimenti manuali e spese fisse (contratti protetti)
- I movimenti di sistema (ACCONTO_CONTRATTO, PAGAMENTO_RATA, SPESA_FISSA)
  vengono creati esclusivamente da create_contract, pay_rate, e sync engine.

Sync Engine (spese ricorrenti):
- Prima di GET /stats, sync_recurring_expenses_for_month()
  genera CashMovement reali dalle RecurringExpense attive.
- Immune a race condition: INSERT atomico con NOT EXISTS + UNIQUE constraint DB.
- Single Source of Truth: le stats derivano SOLO da CashMovement.
"""

import calendar
import logging
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import extract
from sqlmodel import Session, select, func, text

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.movement import CashMovement
from api.models.recurring_expense import RecurringExpense
from api.schemas.financial import (
    MovementManualCreate, MovementResponse,
)
from api.routers._audit import log_audit

logger = logging.getLogger("fitmanager.api")
router = APIRouter(prefix="/movements", tags=["movements"])


# ════════════════════════════════════════════════════════════
# SYNC ENGINE: Spese Ricorrenti → CashMovement (idempotente)
# ════════════════════════════════════════════════════════════

VALID_FREQUENCIES = {"MENSILE", "SETTIMANALE", "TRIMESTRALE"}


def _get_occurrences_in_month(
    expense: RecurringExpense, anno: int, mese: int
) -> list[tuple[date, str]]:
    """
    Calcola le occorrenze di una spesa ricorrente in un dato mese.

    Returns: lista di (data_effettiva, mese_anno_key) per ogni occorrenza.
    La chiave mese_anno e' usata per la deduplicazione (UNIQUE constraint).

    Frequenze supportate:
    - MENSILE: 1 occorrenza per mese, key = "2026-02"
    - SETTIMANALE: ~4 per mese (ogni 7 giorni), key = "2026-02-W1", "2026-02-W2"...
    - TRIMESTRALE: 1 ogni 3 mesi (ancorata al mese di creazione), key = "2026-02"
    """
    days_in_month = calendar.monthrange(anno, mese)[1]
    freq = expense.frequenza or "MENSILE"

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

    if freq == "TRIMESTRALE":
        creation_month = expense.data_creazione.month if expense.data_creazione else 1
        if (mese - creation_month) % 3 != 0:
            return []
        giorno = min(expense.giorno_scadenza, days_in_month)
        return [(date(anno, mese, giorno), f"{anno:04d}-{mese:02d}")]

    # Frequenza sconosciuta: fallback a MENSILE
    giorno = min(expense.giorno_scadenza, days_in_month)
    return [(date(anno, mese, giorno), f"{anno:04d}-{mese:02d}")]


def sync_recurring_expenses_for_month(
    session: Session, trainer_id: int, anno: int, mese: int
) -> int:
    """
    Genera CashMovement reali per le spese ricorrenti attive.

    Backfill automatico: per ogni spesa, genera i movimenti mancanti
    da gennaio dell'anno target (o dal mese di creazione, se successivo)
    fino al mese richiesto. Grazie al guard NOT EXISTS, i mesi gia'
    sincronizzati non generano duplicati (~0.1ms per check).

    Supporto frequenze: MENSILE (1/mese), SETTIMANALE (~4/mese),
    TRIMESTRALE (1 ogni 3 mesi).

    Returns: numero di movimenti creati (0 = nessun lavoro da fare).
    """
    recurring = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.trainer_id == trainer_id,
            RecurringExpense.attiva == True,
            RecurringExpense.deleted_at == None,
        )
    ).all()

    if not recurring:
        return 0

    created = 0

    for expense in recurring:
        # Backfill: da inizio anno (o mese creazione) fino al mese target
        start_month = 1
        if expense.data_creazione:
            if expense.data_creazione.year == anno:
                start_month = expense.data_creazione.month
            elif expense.data_creazione.year > anno:
                continue  # Spesa creata dopo l'anno target

        for m in range(start_month, mese + 1):
            occurrences = _get_occurrences_in_month(expense, anno, m)
            for data_effettiva, mese_anno_key in occurrences:
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
                        "trainer_id": trainer_id,
                        "data_effettiva": data_effettiva.isoformat(),
                        "tipo": "USCITA",
                        "categoria": "SPESA_FISSA",
                        "importo": expense.importo,
                        "note": f"Spesa ricorrente: {expense.nome}",
                        "operatore": "SISTEMA_RECURRING",
                        "id_spesa": expense.id,
                        "mese_anno": mese_anno_key,
                    },
                )
                if result.rowcount > 0:
                    created += 1

    if created > 0:
        session.commit()
        logger.info(
            "Sync: %d movimenti spese fisse creati (target %d/%d, trainer %d)",
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

    Il sync delle spese ricorrenti avviene in GET /stats (che il frontend
    chiama sempre insieme a questo endpoint). Nessun sync qui — evita
    race condition da chiamate parallele.
    """

    # Base query con Bouncer (escludi eliminati)
    query = select(CashMovement).where(CashMovement.trainer_id == trainer.id, CashMovement.deleted_at == None)
    count_q = select(func.count(CashMovement.id)).where(CashMovement.trainer_id == trainer.id, CashMovement.deleted_at == None)

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
    session.flush()
    log_audit(session, "movement", movement.id, "CREATE", trainer.id)
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
