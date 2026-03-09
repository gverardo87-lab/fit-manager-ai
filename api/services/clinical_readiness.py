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
    ClinicalReadinessSummary,
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


def _parse_iso_date(value: str | date | datetime | None) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    normalized = value.strip()
    if not normalized:
        return None

    try:
        return date.fromisoformat(normalized[:10])
    except ValueError:
        return None


def _extract_anamnesi_reference_date(anamnesi_json: str | None) -> date | None:
    if not anamnesi_json:
        return None

    try:
        data = json.loads(anamnesi_json)
    except (TypeError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    updated = _parse_iso_date(data.get("data_ultimo_aggiornamento"))
    if updated:
        return updated
    return _parse_iso_date(data.get("data_compilazione"))


def _compute_timeline_due(
    *,
    reference_date: date,
    anamnesi_state: str,
    has_measurements: bool,
    has_workout_plan: bool,
    latest_measurement_date: date | None,
    latest_workout_updated_at: str | date | datetime | None,
    anamnesi_reference_date: date | None,
) -> tuple[date | None, int | None, str, str | None]:
    if anamnesi_state == "missing":
        return reference_date, 0, "today", "anamnesi_missing"

    if anamnesi_state == "legacy":
        return reference_date, 0, "today", "anamnesi_legacy"

    if not has_measurements:
        return reference_date, 0, "today", "baseline_missing"

    if not has_workout_plan:
        return reference_date, 0, "today", "workout_missing"

    candidates: list[tuple[date, str]] = []

    if latest_measurement_date is not None:
        candidates.append((latest_measurement_date + timedelta(days=30), "measurement_review"))

    latest_workout_date = _parse_iso_date(latest_workout_updated_at)
    if latest_workout_date is not None:
        candidates.append((latest_workout_date + timedelta(days=21), "workout_review"))

    if anamnesi_reference_date is not None:
        candidates.append((anamnesi_reference_date + timedelta(days=180), "anamnesi_review"))

    if not candidates:
        return None, None, "none", "monitoring"

    due_date, reason = min(candidates, key=lambda item: item[0])
    days_to_due = (due_date - reference_date).days

    if days_to_due < 0:
        status = "overdue"
    elif days_to_due == 0:
        status = "today"
    elif days_to_due <= 7:
        status = "upcoming_7d"
    elif days_to_due <= 14:
        status = "upcoming_14d"
    else:
        status = "future"

    return due_date, days_to_due, status, reason


def _build_clinical_readiness_item(
    client: Client,
    *,
    has_measurements: bool,
    has_workout_plan: bool,
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
        readiness_score += 30
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

    next_due_date, days_to_due, timeline_status, timeline_reason = _compute_timeline_due(
        reference_date=reference_date,
        anamnesi_state=anamnesi_state,
        has_measurements=has_measurements,
        has_workout_plan=has_workout_plan,
        latest_measurement_date=latest_measurement_date,
        latest_workout_updated_at=latest_workout_updated_at,
        anamnesi_reference_date=anamnesi_reference_date,
    )

    return ClinicalReadinessClientItem(
        client_id=client_id,
        client_nome=client.nome,
        client_cognome=client.cognome,
        anamnesi_state=anamnesi_state,
        has_measurements=has_measurements,
        has_workout_plan=has_workout_plan,
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

    items: list[ClinicalReadinessClientItem] = []
    for client in active_clients:
        if client.id is None:
            continue
        client_id = client.id
        items.append(
            _build_clinical_readiness_item(
                client,
                has_measurements=client_id in clients_with_measurements,
                has_workout_plan=client_id in clients_with_workout,
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
