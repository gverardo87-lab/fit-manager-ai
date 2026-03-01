# api/routers/workout_logs.py
"""
Endpoint Workout Logs — log di esecuzione sessioni allenamento.

Registra QUANDO una sessione template viene effettivamente eseguita.
Fase 1: session-level only, volume calcolato dal template.

Pattern: APIRouter senza prefix (come measurements.py).
Endpoints:
  POST   /clients/{client_id}/workout-logs
  GET    /clients/{client_id}/workout-logs?id_scheda=X
  GET    /workouts/{workout_id}/logs
  DELETE /clients/{client_id}/workout-logs/{log_id}
"""

from datetime import date as date_type, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.workout import WorkoutPlan, WorkoutSession
from api.models.workout_log import WorkoutLog
from api.schemas.workout_log import (
    WorkoutLogCreate,
    WorkoutLogResponse,
    WorkoutLogListResponse,
)
from api.routers._audit import log_audit

router = APIRouter(tags=["workout-logs"])


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _bouncer_client(session: Session, client_id: int, trainer_id: int) -> None:
    """Bouncer: verifica ownership cliente. 404 se non trovato o non proprio."""
    client = session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.trainer_id == trainer_id,
            Client.deleted_at == None,
        )
    ).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente non trovato",
        )


def _bouncer_workout(session: Session, workout_id: int, trainer_id: int) -> WorkoutPlan:
    """Bouncer: verifica ownership scheda. 404 se non trovata o non propria."""
    plan = session.exec(
        select(WorkoutPlan).where(
            WorkoutPlan.id == workout_id,
            WorkoutPlan.trainer_id == trainer_id,
            WorkoutPlan.deleted_at == None,
        )
    ).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheda non trovata",
        )
    return plan


def _build_log_response(
    log: WorkoutLog,
    plan_map: dict[int, WorkoutPlan],
    session_map: dict[int, WorkoutSession],
) -> WorkoutLogResponse:
    """Costruisce response enriched con nomi scheda e sessione."""
    plan = plan_map.get(log.id_scheda)
    ws = session_map.get(log.id_sessione)
    return WorkoutLogResponse(
        id=log.id,
        id_scheda=log.id_scheda,
        id_sessione=log.id_sessione,
        id_cliente=log.id_cliente,
        data_esecuzione=str(log.data_esecuzione),
        id_evento=log.id_evento,
        note=log.note,
        created_at=log.created_at,
        scheda_nome=plan.nome if plan else f"Scheda #{log.id_scheda}",
        sessione_nome=ws.nome_sessione if ws else f"Sessione #{log.id_sessione}",
    )


# ════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════

@router.post(
    "/clients/{client_id}/workout-logs",
    response_model=WorkoutLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workout_log(
    client_id: int,
    data: WorkoutLogCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Registra l'esecuzione di una sessione di allenamento."""
    # Bouncer: cliente appartiene al trainer
    _bouncer_client(session, client_id, trainer.id)

    # Bouncer: scheda appartiene al trainer
    plan = _bouncer_workout(session, data.id_scheda, trainer.id)

    # Verifica: la scheda e' assegnata a questo cliente
    if plan.id_cliente != client_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La scheda non e' assegnata a questo cliente",
        )

    # Verifica: la sessione appartiene alla scheda
    ws = session.exec(
        select(WorkoutSession).where(
            WorkoutSession.id == data.id_sessione,
            WorkoutSession.id_scheda == data.id_scheda,
        )
    ).first()
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessione non trovata nella scheda",
        )

    # Valida data
    try:
        parsed_date = date_type.fromisoformat(data.data_esecuzione)
    except ValueError:
        raise HTTPException(status_code=422, detail="Data non valida")
    if parsed_date > date_type.today():
        raise HTTPException(status_code=422, detail="Data futura non ammessa")

    # Crea log
    log = WorkoutLog(
        id_scheda=data.id_scheda,
        id_sessione=data.id_sessione,
        id_cliente=client_id,
        trainer_id=trainer.id,
        data_esecuzione=parsed_date,
        id_evento=data.id_evento,
        note=data.note,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    session.add(log)
    session.flush()
    log_audit(session, "workout_log", log.id, "CREATE", trainer.id)
    session.commit()
    session.refresh(log)

    return _build_log_response(log, {plan.id: plan}, {ws.id: ws})


@router.get(
    "/clients/{client_id}/workout-logs",
    response_model=WorkoutLogListResponse,
)
def list_client_workout_logs(
    client_id: int,
    id_scheda: Optional[int] = Query(default=None),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Lista log esecuzione per cliente, con filtro opzionale per scheda."""
    _bouncer_client(session, client_id, trainer.id)

    query = select(WorkoutLog).where(
        WorkoutLog.id_cliente == client_id,
        WorkoutLog.trainer_id == trainer.id,
        WorkoutLog.deleted_at == None,
    )
    if id_scheda is not None:
        query = query.where(WorkoutLog.id_scheda == id_scheda)

    logs = session.exec(
        query.order_by(WorkoutLog.data_esecuzione.desc())
    ).all()

    if not logs:
        return WorkoutLogListResponse(items=[], total=0)

    # Batch fetch plans + sessions (anti-N+1)
    plan_ids = list({log.id_scheda for log in logs})
    plans = session.exec(
        select(WorkoutPlan).where(WorkoutPlan.id.in_(plan_ids))
    ).all()
    plan_map = {p.id: p for p in plans}

    session_ids = list({log.id_sessione for log in logs})
    ws_list = session.exec(
        select(WorkoutSession).where(WorkoutSession.id.in_(session_ids))
    ).all()
    session_map = {s.id: s for s in ws_list}

    items = [_build_log_response(log, plan_map, session_map) for log in logs]
    return WorkoutLogListResponse(items=items, total=len(items))


@router.get(
    "/workouts/{workout_id}/logs",
    response_model=WorkoutLogListResponse,
)
def list_workout_logs(
    workout_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Lista log esecuzione per una scheda specifica (usato nel builder)."""
    plan = _bouncer_workout(session, workout_id, trainer.id)

    logs = session.exec(
        select(WorkoutLog).where(
            WorkoutLog.id_scheda == workout_id,
            WorkoutLog.trainer_id == trainer.id,
            WorkoutLog.deleted_at == None,
        ).order_by(WorkoutLog.data_esecuzione.desc())
    ).all()

    if not logs:
        return WorkoutLogListResponse(items=[], total=0)

    # Batch fetch sessions (anti-N+1)
    session_ids = list({log.id_sessione for log in logs})
    ws_list = session.exec(
        select(WorkoutSession).where(WorkoutSession.id.in_(session_ids))
    ).all()
    session_map = {s.id: s for s in ws_list}

    plan_map = {plan.id: plan}
    items = [_build_log_response(log, plan_map, session_map) for log in logs]
    return WorkoutLogListResponse(items=items, total=len(items))


@router.delete(
    "/clients/{client_id}/workout-logs/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_workout_log(
    client_id: int,
    log_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Soft-delete log esecuzione."""
    _bouncer_client(session, client_id, trainer.id)

    log = session.exec(
        select(WorkoutLog).where(
            WorkoutLog.id == log_id,
            WorkoutLog.trainer_id == trainer.id,
            WorkoutLog.id_cliente == client_id,
            WorkoutLog.deleted_at == None,
        )
    ).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log non trovato",
        )

    log.deleted_at = datetime.now(timezone.utc)
    log_audit(session, "workout_log", log.id, "DELETE", trainer.id)
    session.commit()
