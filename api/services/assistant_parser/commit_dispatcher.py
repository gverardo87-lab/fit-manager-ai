"""
Commit Dispatcher — route operazioni confermate ai domain endpoint.

Chiama direttamente le funzioni router esistenti (create_event,
create_manual_movement, create_measurement) riusando TUTTA la
business logic: bouncer, IDOR, audit, atomic commit.
"""

import logging
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session

from api.models.trainer import Trainer
from api.schemas.assistant import CommitResponse

logger = logging.getLogger(__name__)

# ── Invalidation keys per dominio (coerenti con hook frontend) ──

_INVALIDATION_MAP: dict[str, list[str]] = {
    "agenda.create_event": [
        "events", "dashboard", "clients", "contracts", "contract",
    ],
    "movement.create_manual": [
        "movements", "movement-stats", "dashboard",
        "aging-report", "cash-balance",
    ],
    "measurement.create": [
        "measurements", "goals", "dashboard",
    ],
}


def dispatch(
    intent: str,
    payload: dict[str, Any],
    trainer: Trainer,
    session: Session,
    catalog_session: Session,
) -> CommitResponse:
    """Esegue operazione confermata via funzione di dominio esistente."""
    dispatchers = {
        "agenda.create_event": _commit_event,
        "movement.create_manual": _commit_movement,
        "measurement.create": _commit_measurement,
    }

    handler = dispatchers.get(intent)
    if not handler:
        return CommitResponse(
            success=False,
            message=f"Comando '{intent}' non supportato.",
            entity_type="unknown",
        )

    try:
        return handler(payload, trainer, session, catalog_session)
    except HTTPException as e:
        logger.warning("Assistant commit failed: %s — %s", intent, e.detail)
        return CommitResponse(
            success=False,
            message=str(e.detail),
            entity_type=intent.split(".")[0],
            invalidate=[],
        )
    except Exception:
        logger.exception("Assistant commit unexpected error: %s", intent)
        return CommitResponse(
            success=False,
            message="Errore imprevisto durante l'operazione.",
            entity_type=intent.split(".")[0],
            invalidate=[],
        )


def _commit_event(
    payload: dict[str, Any],
    trainer: Trainer,
    session: Session,
    catalog_session: Session,
) -> CommitResponse:
    """Crea evento via agenda.create_event()."""
    from api.routers.agenda import EventCreate, create_event

    data = EventCreate(**payload)
    result = create_event(data=data, trainer=trainer, session=session)

    return CommitResponse(
        success=True,
        message=f"Evento creato: {result.titolo or result.categoria}",
        created_id=result.id,
        entity_type="event",
        invalidate=_INVALIDATION_MAP["agenda.create_event"],
        navigate_to="/agenda",
    )


def _commit_movement(
    payload: dict[str, Any],
    trainer: Trainer,
    session: Session,
    catalog_session: Session,
) -> CommitResponse:
    """Crea movimento via movements.create_manual_movement()."""
    from api.routers.movements import create_manual_movement
    from api.schemas.financial import MovementManualCreate

    data = MovementManualCreate(**payload)
    result = create_manual_movement(data=data, trainer=trainer, session=session)

    tipo_label = "Entrata" if result.tipo == "ENTRATA" else "Uscita"
    return CommitResponse(
        success=True,
        message=f"{tipo_label} registrata: €{result.importo:.2f}",
        created_id=result.id,
        entity_type="movement",
        invalidate=_INVALIDATION_MAP["movement.create_manual"],
        navigate_to="/cassa",
    )


def _commit_measurement(
    payload: dict[str, Any],
    trainer: Trainer,
    session: Session,
    catalog_session: Session,
) -> CommitResponse:
    """Crea misurazione via measurements.create_measurement()."""
    from api.routers.measurements import create_measurement
    from api.schemas.measurement import MeasurementCreate

    # client_id e' nel payload ma non nello schema MeasurementCreate
    client_id = payload.pop("client_id")
    data = MeasurementCreate(**payload)
    result = create_measurement(
        client_id=client_id,
        data=data,
        session=session,
        catalog_session=catalog_session,
        trainer=trainer,
    )

    return CommitResponse(
        success=True,
        message="Misurazione registrata.",
        created_id=result.id,
        entity_type="measurement",
        invalidate=_INVALIDATION_MAP["measurement.create"],
        navigate_to=f"/clienti/{client_id}/progressi",
    )
