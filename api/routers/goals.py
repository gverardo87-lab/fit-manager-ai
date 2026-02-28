# api/routers/goals.py
"""
Endpoint Obiettivi Cliente — CRUD con Bouncer Pattern + Progress Computation.

Endpoint:
  GET    /clients/{id}/goals                -> lista obiettivi con progresso
  POST   /clients/{id}/goals                -> crea obiettivo (auto-baseline)
  PUT    /clients/{id}/goals/{goal_id}      -> aggiorna obiettivo
  DELETE /clients/{id}/goals/{goal_id}      -> soft-delete obiettivo

Deep IDOR: id_cliente -> Client.trainer_id == JWT trainer_id
           goal_id -> ClientGoal.trainer_id == JWT trainer_id

Progress computation: enrichment dalla misurazione piu' recente per ogni metrica.
Anti-N+1: 3 query batch (obiettivi + metriche + valori recenti).
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.goal import ClientGoal
from api.models.measurement import Metric, ClientMeasurement, MeasurementValue
from api.schemas.goal import (
    GoalCreate, GoalUpdate,
    GoalResponse, GoalProgress, GoalListResponse,
)

router = APIRouter(tags=["goals"])


# ════════════════════════════════════════════════════════════
# HELPERS — Bouncer Pattern
# ════════════════════════════════════════════════════════════

def _bouncer_client(session: Session, client_id: int, trainer_id: int) -> Client:
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
    return client


def _bouncer_goal(
    session: Session, goal_id: int, trainer_id: int
) -> ClientGoal:
    """Bouncer: verifica ownership obiettivo. 404 se non trovato."""
    goal = session.exec(
        select(ClientGoal).where(
            ClientGoal.id == goal_id,
            ClientGoal.trainer_id == trainer_id,
            ClientGoal.deleted_at == None,
        )
    ).first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Obiettivo non trovato",
        )
    return goal


def _load_metric_map(session: Session) -> dict[int, Metric]:
    """Carica catalogo metriche in memoria per enrichment (anti-N+1)."""
    metrics = session.exec(select(Metric)).all()
    return {m.id: m for m in metrics}


def _get_latest_values(
    session: Session, client_id: int, trainer_id: int
) -> dict[int, tuple[float, str]]:
    """
    Ritorna il valore piu' recente per ogni metrica del cliente.
    Returns: {metric_id: (valore, data_misurazione_str)}
    Anti-N+1: singola query con subquery per sessione piu' recente.
    """
    # Subquery: ID della sessione piu' recente per questo cliente
    latest_session_id = (
        select(ClientMeasurement.id)
        .where(
            ClientMeasurement.id_cliente == client_id,
            ClientMeasurement.trainer_id == trainer_id,
            ClientMeasurement.deleted_at == None,
        )
        .order_by(ClientMeasurement.data_misurazione.desc())
        .limit(1)
        .scalar_subquery()
    )

    # Query valori dalla sessione piu' recente
    values = session.exec(
        select(MeasurementValue, ClientMeasurement.data_misurazione)
        .join(ClientMeasurement, MeasurementValue.id_misurazione == ClientMeasurement.id)
        .where(MeasurementValue.id_misurazione == latest_session_id)
    ).all()

    result: dict[int, tuple[float, str]] = {}
    for val, data in values:
        result[val.id_metrica] = (val.valore, str(data))

    return result


def _get_metric_history(
    session: Session, client_id: int, trainer_id: int, metric_ids: set[int]
) -> dict[int, list[tuple[date, float]]]:
    """
    Time series per metriche specifiche. Anti-N+1: 2 query batch.
    Returns: {metric_id: [(date, value), ...]} ordinato ASC per data.
    """
    if not metric_ids:
        return {}

    # Query 1: sessioni attive (ID + date) ordinate ASC
    rows = session.exec(
        select(ClientMeasurement.id, ClientMeasurement.data_misurazione)
        .where(
            ClientMeasurement.id_cliente == client_id,
            ClientMeasurement.trainer_id == trainer_id,
            ClientMeasurement.deleted_at == None,
        )
        .order_by(ClientMeasurement.data_misurazione.asc())
    ).all()

    if not rows:
        return {}

    measurement_ids = [r[0] for r in rows]
    date_by_id: dict[int, date] = {r[0]: r[1] for r in rows}

    # Query 2: valori per metric_ids nelle sessioni trovate
    values = session.exec(
        select(MeasurementValue).where(
            MeasurementValue.id_misurazione.in_(measurement_ids),
            MeasurementValue.id_metrica.in_(metric_ids),
        )
    ).all()

    # Group by metric_id, sort by date ASC
    result: dict[int, list[tuple[date, float]]] = {}
    for v in values:
        d = date_by_id.get(v.id_misurazione)
        if d:
            result.setdefault(v.id_metrica, []).append((d, v.valore))

    for metric_id in result:
        result[metric_id].sort(key=lambda x: x[0])

    return result


def _compute_weekly_rate(history: list[tuple[date, float]]) -> Optional[float]:
    """
    Velocita' settimanale: pendenza su ultimi 30 giorni.
    Fallback: primo + ultimo se < 2 punti nel window.
    """
    if len(history) < 2:
        return None

    latest = history[-1]
    cutoff = latest[0] - timedelta(days=30)
    recent = [p for p in history if p[0] >= cutoff]

    # Fallback a range completo se < 2 punti in 30gg
    if len(recent) < 2:
        recent = [history[0], history[-1]]

    first, last = recent[0], recent[-1]
    days = (last[0] - first[0]).days
    if days == 0:
        return None

    delta = last[1] - first[1]
    weekly_rate = delta / days * 7
    return round(weekly_rate, 2)


def _compute_progress(
    goal: ClientGoal,
    latest_value: Optional[float],
    latest_date: Optional[str],
    history: Optional[list[tuple[date, float]]] = None,
) -> GoalProgress:
    """Computa progresso obiettivo dalla misurazione piu' recente + rate."""
    num = len(history) if history else 0

    if latest_value is None:
        return GoalProgress(num_misurazioni=num)

    delta = None
    pct = None
    trend = None

    if goal.valore_baseline is not None:
        delta = latest_value - goal.valore_baseline

        # Tendenza positiva: dipende dalla direzione
        if goal.direzione == "diminuire":
            trend = delta < 0
        elif goal.direzione == "aumentare":
            trend = delta > 0
        else:  # mantenere
            trend = abs(delta) < (goal.valore_baseline * 0.05)  # entro 5%

        # Percentuale progresso (solo se c'e' un target)
        if goal.valore_target is not None:
            span = goal.valore_target - goal.valore_baseline
            if span != 0:
                raw_pct = (latest_value - goal.valore_baseline) / span * 100
                pct = max(0.0, min(100.0, raw_pct))

    rate = _compute_weekly_rate(history) if history else None

    return GoalProgress(
        valore_corrente=latest_value,
        data_corrente=latest_date,
        delta_da_baseline=round(delta, 2) if delta is not None else None,
        percentuale_progresso=round(pct, 1) if pct is not None else None,
        tendenza_positiva=trend,
        velocita_settimanale=rate,
        num_misurazioni=num,
    )


def _build_goal_response(
    goal: ClientGoal,
    metric_map: dict[int, Metric],
    latest_values: dict[int, tuple[float, str]],
    metric_histories: Optional[dict[int, list[tuple[date, float]]]] = None,
) -> GoalResponse:
    """Assembla response enriched con nome metrica e progresso."""
    metric = metric_map.get(goal.id_metrica)
    latest = latest_values.get(goal.id_metrica)
    history = metric_histories.get(goal.id_metrica) if metric_histories else None

    progress = _compute_progress(
        goal,
        latest[0] if latest else None,
        latest[1] if latest else None,
        history=history,
    )

    return GoalResponse(
        id=goal.id,
        id_cliente=goal.id_cliente,
        id_metrica=goal.id_metrica,
        nome_metrica=metric.nome if metric else f"Metrica #{goal.id_metrica}",
        unita_misura=metric.unita_misura if metric else "",
        categoria_metrica=metric.categoria if metric else "",
        tipo_obiettivo=goal.tipo_obiettivo,
        direzione=goal.direzione,
        valore_target=goal.valore_target,
        valore_baseline=goal.valore_baseline,
        data_baseline=str(goal.data_baseline) if goal.data_baseline else None,
        data_inizio=str(goal.data_inizio),
        data_scadenza=str(goal.data_scadenza) if goal.data_scadenza else None,
        priorita=goal.priorita,
        stato=goal.stato,
        completed_at=str(goal.completed_at) if goal.completed_at else None,
        completato_automaticamente=goal.completato_automaticamente,
        note=goal.note,
        progresso=progress,
    )


# ════════════════════════════════════════════════════════════
# CRUD OBIETTIVI
# ════════════════════════════════════════════════════════════

@router.get(
    "/clients/{client_id}/goals",
    response_model=GoalListResponse,
)
def list_goals(
    client_id: int,
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Lista obiettivi per cliente — enriched con progresso da misurazioni."""
    _bouncer_client(session, client_id, trainer.id)

    goals = session.exec(
        select(ClientGoal).where(
            ClientGoal.id_cliente == client_id,
            ClientGoal.trainer_id == trainer.id,
            ClientGoal.deleted_at == None,
        ).order_by(ClientGoal.priorita, ClientGoal.data_inizio.desc())
    ).all()

    if not goals:
        return GoalListResponse(items=[], total=0, attivi=0, raggiunti=0)

    # Batch enrichment (anti-N+1)
    metric_map = _load_metric_map(session)
    latest_values = _get_latest_values(session, client_id, trainer.id)

    # Fetch storico metriche per rate of change (anti-N+1: 2 query batch)
    goal_metric_ids = {g.id_metrica for g in goals}
    metric_histories = _get_metric_history(session, client_id, trainer.id, goal_metric_ids)

    items = [
        _build_goal_response(g, metric_map, latest_values, metric_histories)
        for g in goals
    ]

    attivi = sum(1 for g in goals if g.stato == "attivo")
    raggiunti = sum(1 for g in goals if g.stato == "raggiunto")

    return GoalListResponse(
        items=items,
        total=len(items),
        attivi=attivi,
        raggiunti=raggiunti,
    )


@router.post(
    "/clients/{client_id}/goals",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_goal(
    client_id: int,
    data: GoalCreate,
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Crea obiettivo — auto-cattura baseline dalla misurazione piu' recente."""
    _bouncer_client(session, client_id, trainer.id)

    # Verifica che la metrica esista
    metric = session.get(Metric, data.id_metrica)
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Metrica {data.id_metrica} non trovata nel catalogo",
        )

    # ── Validazione max 3 obiettivi attivi ──
    active_goals = session.exec(
        select(ClientGoal).where(
            ClientGoal.id_cliente == client_id,
            ClientGoal.trainer_id == trainer.id,
            ClientGoal.stato == "attivo",
            ClientGoal.deleted_at == None,
        )
    ).all()

    if len(active_goals) >= 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Massimo 3 obiettivi attivi per cliente",
        )

    # ── Validazione metrica unica tra attivi ──
    active_metric_ids = {g.id_metrica for g in active_goals}
    if data.id_metrica in active_metric_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Esiste gia' un obiettivo attivo per la metrica '{metric.nome}'",
        )

    # Auto-cattura baseline
    latest_values = _get_latest_values(session, client_id, trainer.id)
    baseline_entry = latest_values.get(data.id_metrica)

    goal = ClientGoal(
        id_cliente=client_id,
        trainer_id=trainer.id,
        id_metrica=data.id_metrica,
        direzione=data.direzione,
        valore_target=data.valore_target,
        valore_baseline=baseline_entry[0] if baseline_entry else None,
        data_baseline=date.fromisoformat(baseline_entry[1]) if baseline_entry else None,
        data_inizio=date.fromisoformat(data.data_inizio),
        data_scadenza=date.fromisoformat(data.data_scadenza) if data.data_scadenza else None,
        priorita=data.priorita,
        note=data.note,
    )

    session.add(goal)
    session.commit()
    session.refresh(goal)

    metric_map = _load_metric_map(session)
    return _build_goal_response(goal, metric_map, latest_values)


@router.put(
    "/clients/{client_id}/goals/{goal_id}",
    response_model=GoalResponse,
)
def update_goal(
    client_id: int,
    goal_id: int,
    data: GoalUpdate,
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Aggiorna obiettivo (partial update). Setta completed_at su cambio stato."""
    _bouncer_client(session, client_id, trainer.id)
    goal = _bouncer_goal(session, goal_id, trainer.id)

    # Verifica che l'obiettivo appartenga al cliente
    if goal.id_cliente != client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Obiettivo non trovato per questo cliente",
        )

    # Applica aggiornamenti
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "data_scadenza" and value is not None:
            setattr(goal, field, date.fromisoformat(value))
        elif field == "stato" and value is not None:
            goal.stato = value
            if value in ("raggiunto", "abbandonato"):
                goal.completed_at = datetime.now(timezone.utc)
            elif value == "attivo":
                goal.completed_at = None
                goal.completato_automaticamente = False
        else:
            setattr(goal, field, value)

    session.add(goal)
    session.commit()
    session.refresh(goal)

    metric_map = _load_metric_map(session)
    latest_values = _get_latest_values(session, client_id, trainer.id)
    return _build_goal_response(goal, metric_map, latest_values)


@router.delete(
    "/clients/{client_id}/goals/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_goal(
    client_id: int,
    goal_id: int,
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Soft-delete obiettivo."""
    _bouncer_client(session, client_id, trainer.id)
    goal = _bouncer_goal(session, goal_id, trainer.id)

    if goal.id_cliente != client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Obiettivo non trovato per questo cliente",
        )

    goal.deleted_at = datetime.now(timezone.utc)
    session.add(goal)
    session.commit()
