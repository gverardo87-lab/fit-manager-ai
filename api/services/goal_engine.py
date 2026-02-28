# api/services/goal_engine.py
"""
Goal Completion Engine — auto-completa obiettivi corporei quando le misurazioni
raggiungono il target.

Pattern: mirrors _sync_contract_chiuso() — funzione pura chiamata dal punto di
mutazione (measurements router). NON committa — il caller committa atomicamente.

Regole:
  - diminuire + target: valore_corrente <= target → RAGGIUNTO
  - aumentare + target: valore_corrente >= target → RAGGIUNTO
  - mantenere: MAI auto-completa (obiettivo continuo)
  - senza target: MAI auto-completa (nessun criterio oggettivo)
"""

from datetime import datetime, timezone

from sqlmodel import Session, select

from api.models.goal import ClientGoal
from api.models.measurement import Metric, ClientMeasurement, MeasurementValue


def _is_goal_reached(goal: ClientGoal, current_value: float) -> bool:
    """Predicato puro: l'obiettivo e' raggiunto?"""
    if goal.valore_target is None:
        return False
    if goal.direzione == "diminuire":
        return current_value <= goal.valore_target
    if goal.direzione == "aumentare":
        return current_value >= goal.valore_target
    # mantenere → mai auto-completa
    return False


def sync_goal_completion(
    session: Session,
    client_id: int,
    trainer_id: int,
) -> list[dict]:
    """
    Controlla obiettivi corporei attivi vs misurazioni piu' recenti.
    Auto-completa quelli che raggiungono il target.

    Returns: lista di {id, nome_metrica, valore_target, valore_raggiunto}
             per toast/notification nella response.

    NON committa — il caller committa atomicamente.
    """
    # 1. Fetch obiettivi attivi corporei
    active_goals = session.exec(
        select(ClientGoal).where(
            ClientGoal.id_cliente == client_id,
            ClientGoal.trainer_id == trainer_id,
            ClientGoal.stato == "attivo",
            ClientGoal.tipo_obiettivo == "corporeo",
            ClientGoal.deleted_at == None,
        )
    ).all()

    if not active_goals:
        return []

    # 2. Fetch sessione piu' recente (anti-N+1)
    latest_session = session.exec(
        select(ClientMeasurement)
        .where(
            ClientMeasurement.id_cliente == client_id,
            ClientMeasurement.trainer_id == trainer_id,
            ClientMeasurement.deleted_at == None,
        )
        .order_by(ClientMeasurement.data_misurazione.desc())
        .limit(1)
    ).first()

    if not latest_session:
        return []

    # 3. Valori dalla sessione piu' recente
    values = session.exec(
        select(MeasurementValue).where(
            MeasurementValue.id_misurazione == latest_session.id
        )
    ).all()
    value_map = {v.id_metrica: v.valore for v in values}

    # 4. Catalogo metriche per enrichment response
    metric_ids = {g.id_metrica for g in active_goals}
    metrics = session.exec(
        select(Metric).where(Metric.id.in_(metric_ids))
    ).all()
    metric_map = {m.id: m for m in metrics}

    # 5. Controlla ogni obiettivo
    completed = []
    now = datetime.now(timezone.utc)

    for goal in active_goals:
        current_value = value_map.get(goal.id_metrica)
        if current_value is None:
            continue

        if _is_goal_reached(goal, current_value):
            goal.stato = "raggiunto"
            goal.completed_at = now
            goal.completato_automaticamente = True
            session.add(goal)

            metric = metric_map.get(goal.id_metrica)
            completed.append({
                "id": goal.id,
                "nome_metrica": metric.nome if metric else f"Metrica #{goal.id_metrica}",
                "valore_target": goal.valore_target,
                "valore_raggiunto": current_value,
            })

    return completed
