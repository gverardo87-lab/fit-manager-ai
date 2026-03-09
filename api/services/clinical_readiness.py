"""
Shared service for clinical readiness worklists.

The logic originally lived inside the dashboard router. It is extracted here
so dashboard and workspace can consume the same deterministic rules without
drift.
"""

import json
import unicodedata
from datetime import date, datetime, timedelta

from sqlmodel import Session, select, func

from api.models.client import Client
from api.models.measurement import ClientMeasurement
from api.models.workout import WorkoutPlan
from api.schemas.clinical import (
    ClinicalReadinessClientItem,
    ClinicalFreshnessSignal,
    ClinicalReadinessSummary,
)
from api.services.client_freshness import (
    build_measurement_freshness,
    build_workout_freshness,
    parse_reference_date,
)


def _get_anamnesi_state(anamnesi_json: str | None) -> str:
    if not anamnesi_json:
        return "missing"

    try:
        data = json.loads(anamnesi_json)
    except (TypeError, json.JSONDecodeError):
        return "legacy"

    if isinstance(data, dict) and "data_compilazione" in data and (
        "obiettivo_principale" in data
    ):
        return "structured"

    return "legacy"


def _extract_anamnesi_reference_date(anamnesi_json: str | None) -> date | None:
    if not anamnesi_json:
        return None

    try:
        data = json.loads(anamnesi_json)
    except (TypeError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    updated = parse_reference_date(data.get("data_ultimo_aggiornamento"))
    if updated:
        return updated
    return parse_reference_date(data.get("data_compilazione"))


def _timeline_status(days_to_due: int | None) -> str:
    if days_to_due is None:
        return "none"
    if days_to_due < 0:
        return "overdue"
    if days_to_due == 0:
        return "today"
    if days_to_due <= 7:
        return "upcoming_7d"
    if days_to_due <= 14:
        return "upcoming_14d"
    return "future"


def _build_anamnesi_timeline(
    *,
    anamnesi_state: str,
    anamnesi_reference_date: date | None,
    reference_date: date,
) -> tuple[date | None, int | None, str, str | None, str | None]:
    if anamnesi_state == "missing":
        return reference_date, 0, "today", "anamnesi_missing", "Anamnesi mancante"

    if anamnesi_state == "legacy":
        return reference_date, 0, "today", "anamnesi_legacy", "Anamnesi legacy da rivedere"

    if anamnesi_reference_date is None:
        return None, None, "none", None, None

    due_date = anamnesi_reference_date + timedelta(days=180)
    days_to_due = (due_date - reference_date).days
    return (
        due_date,
        days_to_due,
        _timeline_status(days_to_due),
        "anamnesi_review",
        "Review anamnesi programmata",
    )


def _compute_timeline_due(
    *,
    anamnesi_timeline: tuple[date | None, int | None, str, str | None, str | None],
    measurement_freshness: ClinicalFreshnessSignal,
    workout_freshness: ClinicalFreshnessSignal,
) -> tuple[date | None, int | None, str, str | None, str | None]:
    if anamnesi_timeline[0] is not None and anamnesi_timeline[3] in {"anamnesi_missing", "anamnesi_legacy"}:
        return anamnesi_timeline

    if measurement_freshness.status == "missing":
        return (
            measurement_freshness.due_date,
            measurement_freshness.days_to_due,
            measurement_freshness.timeline_status,
            "baseline_missing",
            measurement_freshness.label,
        )

    if workout_freshness.status == "missing":
        return (
            workout_freshness.due_date,
            workout_freshness.days_to_due,
            workout_freshness.timeline_status,
            "workout_missing",
            workout_freshness.label,
        )

    candidates: list[tuple[date, int, str, str | None, str | None]] = []

    if measurement_freshness.due_date is not None and measurement_freshness.days_to_due is not None:
        candidates.append(
            (
                measurement_freshness.due_date,
                measurement_freshness.days_to_due,
                measurement_freshness.timeline_status,
                measurement_freshness.reason_code,
                measurement_freshness.label,
            )
        )

    if workout_freshness.due_date is not None and workout_freshness.days_to_due is not None:
        candidates.append(
            (
                workout_freshness.due_date,
                workout_freshness.days_to_due,
                workout_freshness.timeline_status,
                workout_freshness.reason_code,
                workout_freshness.label,
            )
        )

    if anamnesi_timeline[0] is not None and anamnesi_timeline[1] is not None:
        candidates.append(
            (
                anamnesi_timeline[0],
                anamnesi_timeline[1],
                anamnesi_timeline[2],
                anamnesi_timeline[3],
                anamnesi_timeline[4],
            )
        )

    if not candidates:
        return None, None, "none", "monitoring", None

    due_date, days_to_due, status, reason, label = min(candidates, key=lambda item: item[0])
    return due_date, days_to_due, status, reason, label


def _build_clinical_readiness_item(
    client: Client,
    *,
    has_measurements: bool,
    has_workout_plan: bool,
    workout_plan_name: str | None = None,
    workout_activated: bool = False,
    latest_measurement_date: date | None,
    latest_workout_updated_at: str | date | datetime | None,
    anamnesi_reference_date: date | None,
    reference_date: date,
) -> ClinicalReadinessClientItem:
    anamnesi_state = _get_anamnesi_state(client.anamnesi_json)

    missing_steps: list[str] = []
    readiness_score = 0
    priority_score = 0

    if anamnesi_state == "structured":
        readiness_score += 40
    elif anamnesi_state == "legacy":
        readiness_score += 15
        missing_steps.append("anamnesi_legacy")
        priority_score += 80
    else:
        missing_steps.append("anamnesi_missing")
        priority_score += 100

    if has_measurements:
        readiness_score += 30
    else:
        missing_steps.append("baseline")
        priority_score += 60

    if has_workout_plan:
        readiness_score += 20
        if workout_activated:
            readiness_score += 10
        else:
            missing_steps.append("workout_not_activated")
            priority_score += 20
    else:
        missing_steps.append("workout")
        priority_score += 40

    client_id = client.id or 0

    if anamnesi_state == "missing":
        next_action_code = "collect_anamnesi"
        next_action_label = "Compila anamnesi"
        next_action_href = f"/clienti/{client_id}/anamnesi?startWizard=1"
    elif anamnesi_state == "legacy":
        next_action_code = "migrate_anamnesi"
        next_action_label = "Rivedi anamnesi"
        next_action_href = f"/clienti/{client_id}/anamnesi?startWizard=1"
    elif not has_measurements:
        next_action_code = "collect_baseline"
        next_action_label = "Registra baseline"
        next_action_href = f"/clienti/{client_id}/misurazioni"
    elif not has_workout_plan:
        next_action_code = "assign_workout"
        next_action_label = "Assegna scheda"
        next_action_href = f"/clienti/{client_id}?tab=schede&startScheda=1"
    elif not workout_activated:
        next_action_code = "activate_workout"
        next_action_label = "Attiva programma"
        next_action_href = f"/allenamenti?idCliente={client_id}"
    else:
        next_action_code = "ready"
        next_action_label = "Profilo pronto"
        next_action_href = f"/clienti/{client_id}"

    if priority_score >= 80:
        priority = "high"
    elif priority_score >= 40:
        priority = "medium"
    else:
        priority = "low"

    measurement_freshness = build_measurement_freshness(
        client_id=client_id,
        latest_measurement_date=latest_measurement_date,
        reference_date=reference_date,
    )
    workout_freshness = build_workout_freshness(
        client_id=client_id,
        latest_workout_reference=latest_workout_updated_at,
        reference_date=reference_date,
    )
    anamnesi_timeline = _build_anamnesi_timeline(
        anamnesi_state=anamnesi_state,
        anamnesi_reference_date=anamnesi_reference_date,
        reference_date=reference_date,
    )
    next_due_date, days_to_due, timeline_status, timeline_reason, timeline_label = _compute_timeline_due(
        anamnesi_timeline=anamnesi_timeline,
        measurement_freshness=measurement_freshness,
        workout_freshness=workout_freshness,
    )

    return ClinicalReadinessClientItem(
        client_id=client_id,
        client_nome=client.nome,
        client_cognome=client.cognome,
        anamnesi_state=anamnesi_state,
        has_measurements=has_measurements,
        has_workout_plan=has_workout_plan,
        workout_activated=workout_activated,
        workout_plan_name=workout_plan_name,
        missing_steps=missing_steps,
        readiness_score=readiness_score,
        priority=priority,
        priority_score=priority_score,
        next_action_code=next_action_code,
        next_action_label=next_action_label,
        next_action_href=next_action_href,
        next_due_date=next_due_date,
        days_to_due=days_to_due,
        timeline_status=timeline_status,
        timeline_reason=timeline_reason,
        timeline_label=timeline_label,
        measurement_freshness=measurement_freshness,
        workout_freshness=workout_freshness,
    )


def _normalize_search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value or "")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower().strip()


def compute_clinical_readiness_data(
    trainer_id: int,
    session: Session,
    reference_date: date,
) -> tuple[ClinicalReadinessSummary, list[ClinicalReadinessClientItem]]:
    active_clients = session.exec(
        select(Client).where(
            Client.trainer_id == trainer_id,
            Client.stato == "Attivo",
            Client.deleted_at == None,
        )
    ).all()

    client_ids = [c.id for c in active_clients if c.id is not None]
    if not client_ids:
        return ClinicalReadinessSummary(), []

    measurement_rows = session.exec(
        select(ClientMeasurement.id_cliente, func.max(ClientMeasurement.data_misurazione))
        .where(
            ClientMeasurement.trainer_id == trainer_id,
            ClientMeasurement.deleted_at == None,
            ClientMeasurement.id_cliente.in_(client_ids),
        )
        .group_by(ClientMeasurement.id_cliente)
    ).all()
    latest_measurement_by_client = {
        row[0]: row[1]
        for row in measurement_rows
        if row[0] is not None
    }
    clients_with_measurements = set(latest_measurement_by_client.keys())

    workout_rows = session.exec(
        select(
            WorkoutPlan.id_cliente,
            func.max(func.coalesce(WorkoutPlan.updated_at, WorkoutPlan.created_at)),
        )
        .where(
            WorkoutPlan.trainer_id == trainer_id,
            WorkoutPlan.deleted_at == None,
            WorkoutPlan.id_cliente != None,
            WorkoutPlan.id_cliente.in_(client_ids),
        )
        .group_by(WorkoutPlan.id_cliente)
    ).all()
    latest_workout_by_client = {
        row[0]: row[1]
        for row in workout_rows
        if row[0] is not None
    }
    clients_with_workout = set(latest_workout_by_client.keys())

    # Fetch latest plan per client for activation status + name (anti-N+1)
    workout_detail_rows = session.exec(
        select(
            WorkoutPlan.id_cliente,
            WorkoutPlan.nome,
            WorkoutPlan.data_inizio,
            WorkoutPlan.data_fine,
        )
        .where(
            WorkoutPlan.trainer_id == trainer_id,
            WorkoutPlan.deleted_at == None,
            WorkoutPlan.id_cliente != None,
            WorkoutPlan.id_cliente.in_(client_ids),
        )
        .order_by(
            WorkoutPlan.id_cliente,
            func.coalesce(WorkoutPlan.updated_at, WorkoutPlan.created_at).desc(),
        )
    ).all()
    # Keep only the latest plan per client (first row per id_cliente after ORDER BY desc)
    # Tuple: (nome, data_inizio, data_fine)
    latest_plan_info: dict[int, tuple[str | None, date | None, date | None]] = {}
    for row in workout_detail_rows:
        cid = row[0]
        if cid is not None and cid not in latest_plan_info:
            latest_plan_info[cid] = (row[1], row[2], row[3])

    items: list[ClinicalReadinessClientItem] = []
    for client in active_clients:
        if client.id is None:
            continue
        client_id = client.id
        plan_info = latest_plan_info.get(client_id)
        items.append(
            _build_clinical_readiness_item(
                client,
                has_measurements=client_id in clients_with_measurements,
                has_workout_plan=client_id in clients_with_workout,
                workout_plan_name=plan_info[0] if plan_info else None,
                # Activated = both data_inizio AND data_fine set (matches frontend getProgramStatus)
                workout_activated=(
                    plan_info[1] is not None and plan_info[2] is not None
                ) if plan_info else False,
                latest_measurement_date=latest_measurement_by_client.get(client_id),
                latest_workout_updated_at=latest_workout_by_client.get(client_id),
                anamnesi_reference_date=_extract_anamnesi_reference_date(client.anamnesi_json),
                reference_date=reference_date,
            )
        )

    items.sort(
        key=lambda item: (
            -item.priority_score,
            item.readiness_score,
            item.client_cognome.lower(),
            item.client_nome.lower(),
        )
    )

    summary = ClinicalReadinessSummary(
        total_clients=len(items),
        ready_clients=sum(1 for i in items if i.next_action_code == "ready"),
        missing_anamnesi=sum(1 for i in items if i.anamnesi_state == "missing"),
        legacy_anamnesi=sum(1 for i in items if i.anamnesi_state == "legacy"),
        missing_measurements=sum(1 for i in items if not i.has_measurements),
        missing_workout_plan=sum(1 for i in items if not i.has_workout_plan),
        high_priority=sum(1 for i in items if i.priority == "high"),
        medium_priority=sum(1 for i in items if i.priority == "medium"),
        low_priority=sum(1 for i in items if i.priority == "low"),
    )
    return summary, items


def filter_clinical_readiness_items(
    items: list[ClinicalReadinessClientItem],
    *,
    view: str,
    priority: str | None,
    timeline_status: str | None,
    search: str | None,
) -> list[ClinicalReadinessClientItem]:
    filtered = items

    if view == "todo":
        filtered = [item for item in filtered if item.next_action_code != "ready"]
    elif view == "ready":
        filtered = [item for item in filtered if item.next_action_code == "ready"]

    if priority:
        filtered = [item for item in filtered if item.priority == priority]

    if timeline_status:
        filtered = [item for item in filtered if item.timeline_status == timeline_status]

    if search:
        query = _normalize_search_text(search)
        if query:
            filtered = [
                item
                for item in filtered
                if query in _normalize_search_text(f"{item.client_nome} {item.client_cognome}")
            ]

    return filtered


def sort_clinical_readiness_items(
    items: list[ClinicalReadinessClientItem],
    *,
    sort_by: str,
) -> list[ClinicalReadinessClientItem]:
    if sort_by != "due_date":
        return items

    return sorted(
        items,
        key=lambda item: (
            item.next_due_date is None,
            item.next_due_date or date.max,
            -item.priority_score,
            item.client_cognome.lower(),
            item.client_nome.lower(),
        ),
    )
