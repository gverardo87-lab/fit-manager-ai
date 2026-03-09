"""Read-only orchestration layer for the operational workspace."""

from collections import defaultdict
from datetime import date, datetime, timedelta
import unicodedata

from sqlalchemy import bindparam
from sqlmodel import Session, select, text

from api.models.client import Client
from api.models.contract import Contract
from api.models.event import Event
from api.models.recurring_expense import RecurringExpense
from api.models.rate import Rate
from api.models.todo import Todo
from api.schemas.clinical import ClinicalReadinessClientItem
from api.schemas.workspace import (
    OperationalCase,
    WorkspaceAction,
    WorkspaceAgendaItem,
    WorkspaceCaseActivityItem,
    WorkspaceCaseDetailResponse,
    WorkspaceCaseListFilters,
    WorkspaceCaseListResponse,
    WorkspaceFinanceContext,
    WorkspaceRootEntity,
    WorkspaceSignal,
    WorkspaceSummary,
    WorkspaceTodayAgenda,
    WorkspaceTodayResponse,
    WorkspaceTodaySection,
)
from api.services.clinical_readiness import compute_clinical_readiness_data
from api.services.recurring_expense_schedule import (
    list_pending_recurring_expense_occurrences,
)

_SECTION_ORDER = ("now", "today", "upcoming_3d", "upcoming_7d", "waiting")
_SECTION_LABELS = {
    "now": "Adesso",
    "today": "Oggi",
    "upcoming_3d": "Entro 3 giorni",
    "upcoming_7d": "Entro 7 giorni",
    "waiting": "In attesa",
}
_TODAY_VIEWPORT_LIMITS = {
    "now": 2,
    "today": 4,
}
_TODAY_EXCLUDED_CASE_KINDS = {"payment_due_soon", "recurring_expense_due"}
_READINESS_UPCOMING_EVENT_WINDOW_DAYS = 7
_READINESS_RECENT_CONTRACT_WINDOW_DAYS = 7
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_BUCKET_ORDER = {bucket: idx for idx, bucket in enumerate(_SECTION_ORDER)}
_CASE_PRIORITY = {
    "session_imminent": 0,
    "payment_overdue": 1,
    "payment_due_soon": 2,
    "onboarding_readiness": 3,
    "contract_renewal_due": 4,
    "recurring_expense_due": 5,
    "client_reactivation": 6,
    "todo_manual": 7,
}
_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
_READINESS_SIGNAL_LABELS = {
    "anamnesi_missing": "Anamnesi mancante",
    "anamnesi_legacy": "Anamnesi legacy da rivedere",
    "baseline": "Baseline misure mancante",
    "workout": "Scheda mancante",
}


def _now_local() -> datetime:
    # The CRM stores agenda datetimes as naive local values, so workspace ordering
    # must use the same local-naive clock to avoid shifting the operational day.
    return datetime.now()


def _normalize_search_text(value: str | None) -> str:
    normalized = unicodedata.normalize("NFD", value or "")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower().strip()


def _as_local_day_bounds(reference_dt: datetime) -> tuple[datetime, datetime]:
    day = reference_dt.date()
    return (
        datetime.combine(day, datetime.min.time()),
        datetime.combine(day, datetime.max.time()),
    )


def _link_action(action_id: str, label: str, href: str | None, *, primary: bool) -> WorkspaceAction:
    return WorkspaceAction(
        id=action_id,
        label=label,
        kind="navigate" if href else "deep_link",
        href=href,
        enabled=href is not None,
        availability_note=None if href else "Disponibile nel prossimo microstep",
        is_primary=primary,
    )


def _full_name(nome: str | None, cognome: str | None) -> str:
    return " ".join(part for part in [nome, cognome] if part).strip()


def _max_severity(*values: str) -> str:
    ranked = max(values, key=lambda value: _SEVERITY_RANK.get(value, -1), default="low")
    return ranked


def _todo_due_delta_days(todo: Todo, today: date) -> int | None:
    if todo.data_scadenza is None:
        return None
    return (todo.data_scadenza - today).days


def _todo_created_local_datetime(todo: Todo) -> datetime:
    if todo.created_at.tzinfo is not None:
        return todo.created_at.astimezone().replace(tzinfo=None)
    return todo.created_at


def _todo_age_days(todo: Todo, today: date) -> int:
    return (today - _todo_created_local_datetime(todo).date()).days


def _todo_age_bonus(todo: Todo, today: date) -> int:
    age_days = _todo_age_days(todo, today)
    if age_days >= 21:
        return 15
    if age_days >= 14:
        return 10
    if age_days >= 7:
        return 5
    return 0


def _todo_urgency_score(todo: Todo, today: date) -> int:
    days = _todo_due_delta_days(todo, today)
    if days is None or days > 7:
        return 0
    if days <= -7:
        return 60
    if days <= -1:
        return 45
    if days == 0:
        return 35
    if days <= 3:
        return 20
    return 10


def _todo_score(todo: Todo, today: date) -> int:
    return _todo_urgency_score(todo, today) + _todo_age_bonus(todo, today)


def _todo_sort_key(todo: Todo, today: date) -> tuple[int, bool, date, datetime, int]:
    return (
        -_todo_score(todo, today),
        todo.data_scadenza is None,
        todo.data_scadenza or date.max,
        _todo_created_local_datetime(todo),
        todo.id or 0,
    )


def _todo_reason(todo: Todo, today: date) -> str:
    days = _todo_due_delta_days(todo, today)
    if days is None:
        return "Promemoria senza scadenza"
    if days < 0:
        return f"Scaduto il {todo.data_scadenza.isoformat()}"
    if days == 0:
        return "Scade oggi"
    return f"Scade il {todo.data_scadenza.isoformat()}"


def _todo_bucket(todo: Todo, today: date) -> tuple[str, int | None]:
    days = _todo_due_delta_days(todo, today)
    if days is None:
        return "waiting", None
    if days <= 0:
        return "today", days
    if days <= 3:
        return "upcoming_3d", days
    if days <= 7:
        return "upcoming_7d", days
    return "waiting", days


def _todo_severity(todo: Todo, today: date) -> str:
    days = _todo_due_delta_days(todo, today)
    if days is None:
        return "low"
    if days <= -7:
        return "high"
    if days <= 0:
        return "medium"
    return "low"


def _event_status(event: Event, reference_dt: datetime) -> str:
    if event.data_inizio <= reference_dt <= event.data_fine:
        return "current"
    if event.data_inizio > reference_dt:
        return "upcoming"
    return "past"


def _event_bucket(event: Event, reference_dt: datetime) -> tuple[str, str]:
    if event.data_inizio <= reference_dt <= event.data_fine:
        return "now", "critical"
    delta = event.data_inizio - reference_dt
    if delta <= timedelta(hours=2):
        return "now", "high"
    return "today", "medium"


def _readiness_bucket(item: ClinicalReadinessClientItem) -> str:
    if _is_readiness_maintenance_only(item):
        return "waiting"
    if item.timeline_status in {"overdue", "today", "none"}:
        return "today"
    if item.timeline_status == "upcoming_7d":
        return "upcoming_7d"
    return "waiting"


def _readiness_severity(item: ClinicalReadinessClientItem) -> str:
    if _is_readiness_maintenance_only(item):
        return "low"
    if item.priority == "high":
        return "high"
    if item.priority == "medium":
        return "medium"
    return "low"


def _is_readiness_maintenance_only(item: ClinicalReadinessClientItem) -> bool:
    return (
        item.anamnesi_state == "legacy"
        and item.has_measurements
        and item.has_workout_plan
        and set(item.missing_steps) == {"anamnesi_legacy"}
    )


def _readiness_case_title(item: ClinicalReadinessClientItem, client_label: str) -> str:
    if _is_readiness_maintenance_only(item):
        return f"Anamnesi da rivedere: {client_label}"
    return f"Onboarding da completare: {client_label}"


def _recent_readiness_contract_client_ids(
    *,
    trainer_id: int,
    session: Session,
    client_ids: set[int],
    reference_dt: datetime,
) -> set[int]:
    if not client_ids:
        return set()

    recent_threshold = reference_dt.date() - timedelta(days=_READINESS_RECENT_CONTRACT_WINDOW_DAYS)
    contracts = session.exec(
        select(Contract).where(
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
            Contract.chiuso == False,
            Contract.id_cliente.in_(client_ids),
        )
    ).all()
    recent_ids: set[int] = set()
    for contract in contracts:
        contract_reference = contract.data_inizio or contract.data_vendita
        if contract_reference is not None and contract_reference >= recent_threshold:
            recent_ids.add(contract.id_cliente)
    return recent_ids


def _upcoming_readiness_event_client_ids(
    *,
    trainer_id: int,
    session: Session,
    client_ids: set[int],
    reference_dt: datetime,
) -> set[int]:
    if not client_ids:
        return set()

    deadline = reference_dt + timedelta(days=_READINESS_UPCOMING_EVENT_WINDOW_DAYS)
    rows = session.exec(
        select(Event.id_cliente).where(
            Event.trainer_id == trainer_id,
            Event.deleted_at == None,
            Event.stato != "Cancellato",
            Event.id_cliente != None,
            Event.id_cliente.in_(client_ids),
            Event.data_inizio >= reference_dt,
            Event.data_inizio <= deadline,
        )
    ).all()
    return {client_id for client_id in rows if client_id is not None}


def _renewal_bucket(days_left: int) -> str:
    if days_left <= 0:
        return "today"
    if days_left <= 3:
        return "upcoming_3d"
    if days_left <= 7:
        return "upcoming_7d"
    return "waiting"


def _renewal_severity(days_left: int) -> str:
    if days_left <= 0:
        return "critical"
    if days_left <= 3:
        return "high"
    return "medium"


def _payment_due_soon_bucket(days_left: int) -> str:
    if days_left <= 0:
        return "today"
    if days_left <= 3:
        return "upcoming_3d"
    return "upcoming_7d"


def _payment_due_soon_severity(days_left: int) -> str:
    if days_left <= 0:
        return "high"
    if days_left <= 3:
        return "medium"
    return "low"


def _recurring_expense_bucket(days_left: int) -> str:
    if days_left <= 0:
        return "today"
    if days_left <= 3:
        return "upcoming_3d"
    return "upcoming_7d"


def _recurring_expense_severity(days_left: int) -> str:
    if days_left <= 0:
        return "high"
    if days_left <= 3:
        return "medium"
    return "low"


def _reactivation_severity(days_inactive: int) -> str:
    if days_inactive >= 45:
        return "high"
    if days_inactive >= 21:
        return "medium"
    return "low"


def _reactivation_bucket(days_inactive: int) -> str:
    return "upcoming_7d"


def _case_due_moment(case: OperationalCase) -> datetime | None:
    if case.due_at is not None:
        return case.due_at
    if case.due_date is not None:
        return datetime.combine(case.due_date, datetime.min.time())
    return None


def _sort_case(case: OperationalCase) -> tuple[int, int, datetime, int, str] | tuple[int, int, int, datetime, str]:
    due_moment = _case_due_moment(case) or datetime.max
    if case.case_kind == "session_imminent":
        return (
            _CASE_PRIORITY.get(case.case_kind, 99),
            _BUCKET_ORDER.get(case.bucket, 99),
            due_moment,
            _SEVERITY_ORDER.get(case.severity, 99),
            case.title.lower(),
        )
    if case.case_kind == "todo_manual":
        return (
            _CASE_PRIORITY.get(case.case_kind, 99),
            _SEVERITY_ORDER.get(case.severity, 99),
            _BUCKET_ORDER.get(case.bucket, 99),
            due_moment,
            "",
        )
    return (
        _CASE_PRIORITY.get(case.case_kind, 99),
        _SEVERITY_ORDER.get(case.severity, 99),
        _BUCKET_ORDER.get(case.bucket, 99),
        due_moment,
        case.title.lower(),
    )


def _summarize_cases(cases: list[OperationalCase], *, workspace: str, generated_at: datetime) -> WorkspaceSummary:
    grouped: dict[str, list[OperationalCase]] = defaultdict(list)
    for case in cases:
        grouped[case.bucket].append(case)

    return WorkspaceSummary(
        workspace=workspace,
        generated_at=generated_at,
        critical_count=sum(1 for case in cases if case.severity == "critical"),
        now_count=len(grouped["now"]),
        today_count=len(grouped["today"]),
        upcoming_7d_count=len(grouped["upcoming_3d"]) + len(grouped["upcoming_7d"]),
        waiting_count=len(grouped["waiting"]),
    )


def _apply_finance_visibility(case: OperationalCase, visibility: str) -> OperationalCase:
    if case.finance_context is None or case.finance_context.visibility == visibility:
        return case

    finance_context = case.finance_context.model_copy()
    finance_context.visibility = visibility
    if visibility != "full":
        finance_context.total_due_amount = None
        finance_context.total_residual_amount = None

    return case.model_copy(update={"finance_context": finance_context})


def _case_matches_workspace(case: OperationalCase, workspace: str) -> bool:
    if workspace == "today":
        return case.bucket != "waiting" and case.case_kind not in _TODAY_EXCLUDED_CASE_KINDS
    return case.workspace == workspace


def _filter_cases(
    cases: list[OperationalCase],
    *,
    workspace: str,
    bucket: str | None,
    severity: str | None,
    case_kind: str | None,
    search: str | None,
) -> list[OperationalCase]:
    filtered = [case for case in cases if _case_matches_workspace(case, workspace)]

    if bucket:
        filtered = [case for case in filtered if case.bucket == bucket]

    if severity:
        filtered = [case for case in filtered if case.severity == severity]

    if case_kind:
        filtered = [case for case in filtered if case.case_kind == case_kind]

    if search:
        query = _normalize_search_text(search)
        if query:
            filtered = [
                case
                for case in filtered
                if query in _normalize_search_text(
                    f"{case.title} {case.reason} {case.root_entity.label}"
                )
            ]

    return filtered


def _sort_cases(cases: list[OperationalCase], *, sort_by: str) -> list[OperationalCase]:
    if sort_by == "due_date":
        return sorted(
            cases,
            key=lambda case: (
                _case_due_moment(case) is None,
                _case_due_moment(case) or datetime.max,
                _CASE_PRIORITY.get(case.case_kind, 99),
                _SEVERITY_ORDER.get(case.severity, 99),
                case.title.lower(),
            ),
        )
    return sorted(cases, key=_sort_case)


def _case_viewport_identity(case: OperationalCase) -> tuple[str, str]:
    return (case.root_entity.type, str(case.root_entity.id))


def _apply_today_viewport_budget(
    grouped_cases: dict[str, list[OperationalCase]],
) -> dict[str, list[OperationalCase]]:
    visible_by_bucket: dict[str, list[OperationalCase]] = {}
    seen_identities: set[tuple[str, str]] = set()
    structural_now_count = sum(
        1 for case in grouped_cases.get("now", []) if case.case_kind not in {"todo_manual", "client_reactivation"}
    )
    structural_today_count = sum(
        1
        for case in grouped_cases.get("today", [])
        if case.case_kind not in {"todo_manual", "client_reactivation"}
    )
    manual_today_cap = _manual_today_cap(
        structural_now_count=structural_now_count,
        structural_today_count=structural_today_count,
    )
    visible_manual_today_count = 0
    reactivation_upcoming_cap = _reactivation_upcoming_cap(
        structural_now_count=structural_now_count,
        structural_today_count=structural_today_count,
    )
    visible_reactivation_upcoming_count = 0

    for bucket in _SECTION_ORDER:
        items = grouped_cases.get(bucket, [])
        limit = _TODAY_VIEWPORT_LIMITS.get(bucket)

        selected_items: list[OperationalCase] = []
        for case in items:
            if (
                bucket == "today"
                and case.case_kind == "todo_manual"
                and visible_manual_today_count >= manual_today_cap
            ):
                continue
            if (
                bucket == "upcoming_7d"
                and case.case_kind == "client_reactivation"
                and visible_reactivation_upcoming_count >= reactivation_upcoming_cap
            ):
                continue
            identity = _case_viewport_identity(case)
            if identity in seen_identities:
                continue
            selected_items.append(case)
            seen_identities.add(identity)
            if bucket == "today" and case.case_kind == "todo_manual":
                visible_manual_today_count += 1
            if bucket == "upcoming_7d" and case.case_kind == "client_reactivation":
                visible_reactivation_upcoming_count += 1
            if limit is not None and len(selected_items) >= limit:
                break
        visible_by_bucket[bucket] = selected_items

    return visible_by_bucket


def _manual_today_cap(*, structural_now_count: int, structural_today_count: int) -> int:
    if structural_now_count >= 1:
        return 0
    if structural_today_count >= 2:
        return 1
    return 2


def _reactivation_upcoming_cap(*, structural_now_count: int, structural_today_count: int) -> int:
    if structural_now_count >= 1 or structural_today_count >= 3:
        return 1
    return 2


def _first_visible_case(grouped_cases: dict[str, list[OperationalCase]]) -> OperationalCase | None:
    for bucket in _SECTION_ORDER:
        items = grouped_cases.get(bucket, [])
        if items:
            return items[0]
    return None


def _coerce_entity_id(value: int | str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_activity_datetime(value: date | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, datetime.min.time())


def _make_activity_item(
    *,
    at: date | datetime | None,
    label: str,
    href: str | None,
) -> WorkspaceCaseActivityItem | None:
    activity_at = _as_activity_datetime(at)
    if activity_at is None:
        return None
    return WorkspaceCaseActivityItem(at=activity_at, label=label, href=href)


def _dedupe_entities(*entities: WorkspaceRootEntity | None) -> list[WorkspaceRootEntity]:
    deduped: list[WorkspaceRootEntity] = []
    seen: set[tuple[str, str]] = set()
    for entity in entities:
        if entity is None:
            continue
        key = (entity.type, str(entity.id))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entity)
    return deduped


def _default_case_detail(case: OperationalCase) -> tuple[
    list[WorkspaceSignal],
    list[WorkspaceRootEntity],
    list[WorkspaceCaseActivityItem],
]:
    activity_items = [
        item
        for item in [
            _make_activity_item(
                at=case.due_date,
                label=case.reason,
                href=(case.suggested_actions[0].href if case.suggested_actions else case.root_entity.href),
            ),
            *[
                _make_activity_item(
                    at=signal.due_date,
                    label=signal.label,
                    href=case.root_entity.href,
                )
                for signal in case.preview_signals
            ],
        ]
        if item is not None
    ]
    return (
        list(case.preview_signals),
        _dedupe_entities(case.root_entity, case.secondary_entity),
        activity_items,
    )


def _build_session_cases(
    *,
    trainer_id: int,
    session: Session,
    reference_dt: datetime,
    readiness_by_client: dict[int, ClinicalReadinessClientItem] | None = None,
) -> tuple[list[OperationalCase], list[WorkspaceAgendaItem], set[int]]:
    start_dt, end_dt = _as_local_day_bounds(reference_dt)
    events = session.exec(
        select(Event, Client)
        .join(Client, Event.id_cliente == Client.id, isouter=True)
        .where(
            Event.trainer_id == trainer_id,
            Event.data_inizio >= start_dt,
            Event.data_inizio <= end_dt,
            Event.stato != "Cancellato",
            Event.deleted_at == None,
        )
        .order_by(Event.data_inizio.asc())
    ).all()

    cases: list[OperationalCase] = []
    agenda_items: list[WorkspaceAgendaItem] = []
    covered_client_ids: set[int] = set()

    for event, client in events:
        bucket, severity = _event_bucket(event, reference_dt)
        client_label = _full_name(client.nome, client.cognome) if client else None
        readiness_item = (
            readiness_by_client.get(client.id)
            if client and client.id is not None and readiness_by_client is not None
            else None
        )
        blocked_readiness = readiness_item is not None and readiness_item.next_action_code != "ready"
        title = event.titolo or client_label or event.categoria
        reason = (
            f"{event.categoria} oggi alle {event.data_inizio.strftime('%H:%M')}"
            if event.data_inizio.date() == reference_dt.date()
            else f"{event.categoria} pianificato"
        )
        preview_signals = [
            WorkspaceSignal(
                signal_code="event_today",
                source="events",
                label=event.categoria,
                severity=severity,
                due_date=event.data_inizio.date(),
                reason=reason,
            )
        ]
        signal_count = 1
        if blocked_readiness and readiness_item is not None:
            covered_client_ids.add(readiness_item.client_id)
            severity = _max_severity(severity, _readiness_severity(readiness_item))
            reason = f"{reason} - cliente da preparare"
            preview_signals.extend(
                WorkspaceSignal(
                    signal_code=step,
                    source="clinical_readiness",
                    label=_READINESS_SIGNAL_LABELS.get(step, step),
                    severity=_readiness_severity(readiness_item),
                    due_date=readiness_item.next_due_date,
                    reason=readiness_item.next_action_label,
                )
                for step in readiness_item.missing_steps[:2]
            )
            signal_count += len(readiness_item.missing_steps)
        case_id = f"case:session_imminent:event:{event.id}"
        actions = [_link_action("open-agenda", "Apri agenda", "/agenda", primary=True)]
        secondary_entity = None
        if client and client.id is not None:
            secondary_entity = WorkspaceRootEntity(
                type="client",
                id=client.id,
                label=client_label or f"Cliente {client.id}",
                href=f"/clienti/{client.id}",
            )
            actions.append(
                _link_action("open-client", "Apri cliente", f"/clienti/{client.id}", primary=False)
            )

        cases.append(
            OperationalCase(
                case_id=case_id,
                merge_key=case_id,
                workspace="today",
                case_kind="session_imminent",
                title=title,
                reason=reason,
                severity=severity,
                bucket=bucket,
                due_date=event.data_inizio.date(),
                due_at=event.data_inizio,
                days_to_due=0,
                root_entity=WorkspaceRootEntity(
                    type="event",
                    id=event.id or 0,
                    label=title,
                    href="/agenda",
                ),
                secondary_entity=secondary_entity,
                signal_count=signal_count,
                preview_signals=preview_signals,
                suggested_actions=actions,
                source_refs=[f"event:{event.id}"],
            )
        )

        agenda_items.append(
            WorkspaceAgendaItem(
                event_id=event.id or 0,
                client_id=client.id if client else None,
                client_label=client_label,
                title=title,
                category=event.categoria,
                status=_event_status(event, reference_dt),
                starts_at=event.data_inizio,
                ends_at=event.data_fine,
                href="/agenda",
                has_case_warning=True,
            )
        )

    return cases, agenda_items, covered_client_ids


def _build_readiness_cases(
    *,
    trainer_id: int,
    session: Session,
    reference_dt: datetime,
    readiness_items: list[ClinicalReadinessClientItem],
    session_blocked_client_ids: set[int] | None = None,
) -> list[OperationalCase]:
    readiness_client_ids = {item.client_id for item in readiness_items}
    operational_pressure_client_ids = _upcoming_readiness_event_client_ids(
        trainer_id=trainer_id,
        session=session,
        client_ids=readiness_client_ids,
        reference_dt=reference_dt,
    ) | _recent_readiness_contract_client_ids(
        trainer_id=trainer_id,
        session=session,
        client_ids=readiness_client_ids,
        reference_dt=reference_dt,
    )
    cases: list[OperationalCase] = []
    for item in readiness_items:
        if item.next_action_code == "ready":
            continue
        bucket = _readiness_bucket(item)
        if item.client_id in (session_blocked_client_ids or set()):
            bucket = "waiting"
        elif bucket == "today" and item.client_id not in operational_pressure_client_ids:
            bucket = "waiting"
        client_label = _full_name(item.client_nome, item.client_cognome)
        case_id = f"case:onboarding_readiness:client:{item.client_id}"
        signals = [
            WorkspaceSignal(
                signal_code=step,
                source="clinical_readiness",
                label=_READINESS_SIGNAL_LABELS.get(step, step),
                severity=_readiness_severity(item),
                due_date=item.next_due_date,
                reason=item.next_action_label,
            )
            for step in item.missing_steps[:3]
        ]
        cases.append(
            OperationalCase(
                case_id=case_id,
                merge_key=case_id,
                workspace="onboarding",
                case_kind="onboarding_readiness",
                title=_readiness_case_title(item, client_label),
                reason=item.next_action_label,
                severity=_readiness_severity(item),
                bucket=bucket,
                due_date=item.next_due_date,
                days_to_due=item.days_to_due,
                root_entity=WorkspaceRootEntity(
                    type="client",
                    id=item.client_id,
                    label=client_label,
                    href=f"/clienti/{item.client_id}",
                ),
                secondary_entity=None,
                signal_count=len(item.missing_steps),
                preview_signals=signals,
                suggested_actions=[
                    _link_action("next-step", item.next_action_label, item.next_action_href, primary=True),
                    _link_action("open-client", "Apri cliente", f"/clienti/{item.client_id}", primary=False),
                ],
                source_refs=[f"clinical_readiness:client:{item.client_id}"],
            )
        )

    return cases


def _build_todo_cases(
    *,
    trainer_id: int,
    session: Session,
    reference_date: date,
) -> tuple[list[OperationalCase], int]:
    todos = session.exec(
        select(Todo).where(
            Todo.trainer_id == trainer_id,
            Todo.deleted_at == None,
            Todo.completato == False,
        )
    ).all()
    completed_today = session.exec(
        select(Todo).where(
            Todo.trainer_id == trainer_id,
            Todo.deleted_at == None,
            Todo.completato == True,
            Todo.completed_at != None,
        )
    ).all()

    completed_today_count = sum(
        1
        for todo in completed_today
        if todo.completed_at and todo.completed_at.date() == reference_date
    )

    cases: list[OperationalCase] = []
    ordered_todos = sorted(todos, key=lambda todo: _todo_sort_key(todo, reference_date))
    for todo in ordered_todos:
        bucket, days_to_due = _todo_bucket(todo, reference_date)
        severity = _todo_severity(todo, reference_date)
        case_id = f"case:todo_manual:todo:{todo.id}"
        reason = _todo_reason(todo, reference_date)
        cases.append(
            OperationalCase(
                case_id=case_id,
                merge_key=case_id,
                workspace="today",
                case_kind="todo_manual",
                title=todo.titolo,
                reason=reason,
                severity=severity,
                bucket=bucket,
                due_date=todo.data_scadenza,
                days_to_due=days_to_due,
                root_entity=WorkspaceRootEntity(
                    type="todo",
                    id=todo.id or 0,
                    label=todo.titolo,
                    href="/",
                ),
                secondary_entity=None,
                signal_count=1,
                preview_signals=[
                    WorkspaceSignal(
                        signal_code="todo_open",
                        source="todos",
                        label="Todo aperto",
                        severity=severity,
                        due_date=todo.data_scadenza,
                        reason=reason,
                    )
                ],
                suggested_actions=[
                    _link_action("open-dashboard", "Apri dashboard", "/", primary=True),
                ],
                source_refs=[f"todo:{todo.id}"],
            )
        )

    return cases, completed_today_count


def _load_overdue_rows(
    *,
    trainer_id: int,
    session: Session,
    reference_date: date,
):
    return session.exec(
        select(Rate, Contract, Client)
        .join(Contract, Rate.id_contratto == Contract.id)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.trainer_id == trainer_id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.data_scadenza < reference_date,
            Rate.deleted_at == None,
            Contract.deleted_at == None,
            Contract.chiuso == False,
        )
        .order_by(Rate.data_scadenza.asc())
    ).all()


def _build_payment_overdue_cases(
    *,
    trainer_id: int,
    session: Session,
    reference_date: date,
) -> list[OperationalCase]:
    grouped: dict[int, dict] = {}
    for rate, contract, client in _load_overdue_rows(
        trainer_id=trainer_id,
        session=session,
        reference_date=reference_date,
    ):
        contract_id = contract.id or 0
        bucket = grouped.setdefault(
            contract_id,
            {
                "contract": contract,
                "client": client,
                "rates": [],
                "earliest_due": rate.data_scadenza,
            },
        )
        bucket["rates"].append(rate)
        if rate.data_scadenza < bucket["earliest_due"]:
            bucket["earliest_due"] = rate.data_scadenza

    cases: list[OperationalCase] = []
    for contract_id, data in grouped.items():
        contract = data["contract"]
        client = data["client"]
        rates = data["rates"]
        earliest_due = data["earliest_due"]
        overdue_count = len(rates)
        client_label = _full_name(client.nome, client.cognome)
        case_id = f"case:payment_overdue:contract:{contract_id}"
        signals = [
            WorkspaceSignal(
                signal_code="rate_overdue",
                source="overdue_rates",
                label=f"Rata scaduta del {rate.data_scadenza.isoformat()}",
                severity="critical",
                due_date=rate.data_scadenza,
                reason="Incasso non ancora registrato",
            )
            for rate in rates[:3]
        ]
        total_due_amount = round(sum(rate.importo_previsto for rate in rates), 2)
        total_residual_amount = round(
            sum(rate.importo_previsto - rate.importo_saldato for rate in rates),
            2,
        )
        cases.append(
            OperationalCase(
                case_id=case_id,
                merge_key=case_id,
                workspace="renewals_cash",
                case_kind="payment_overdue",
                title=f"Incasso in ritardo: {client_label}",
                reason=f"{overdue_count} rate scadute sul contratto",
                severity="critical",
                bucket="now",
                due_date=earliest_due,
                days_to_due=(earliest_due - reference_date).days,
                root_entity=WorkspaceRootEntity(
                    type="contract",
                    id=contract_id,
                    label=contract.tipo_pacchetto or f"Contratto {contract_id}",
                    href=f"/contratti/{contract_id}",
                ),
                secondary_entity=WorkspaceRootEntity(
                    type="client",
                    id=client.id or 0,
                    label=client_label,
                    href=f"/clienti/{client.id}",
                ),
                signal_count=overdue_count,
                preview_signals=signals,
                finance_context=WorkspaceFinanceContext(
                    visibility="full",
                    due_date=earliest_due,
                    overdue_count=overdue_count,
                    currency="EUR",
                    total_due_amount=total_due_amount,
                    total_residual_amount=total_residual_amount,
                    contract_id=contract_id,
                ),
                suggested_actions=[
                    _link_action("open-cash", "Apri cassa", "/cassa", primary=True),
                    _link_action("open-contract", "Apri contratto", f"/contratti/{contract_id}", primary=False),
                ],
                source_refs=[f"contract:{contract_id}", *(f"rate:{rate.id}" for rate in rates)],
            )
        )

    return cases


def _load_due_soon_rows(
    *,
    trainer_id: int,
    session: Session,
    reference_date: date,
):
    deadline = reference_date + timedelta(days=7)
    return session.exec(
        select(Rate, Contract, Client)
        .join(Contract, Rate.id_contratto == Contract.id)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.trainer_id == trainer_id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.data_scadenza >= reference_date,
            Rate.data_scadenza <= deadline,
            Rate.deleted_at == None,
            Contract.deleted_at == None,
            Contract.chiuso == False,
        )
        .order_by(Rate.data_scadenza.asc())
    ).all()


def _build_payment_due_soon_cases(
    *,
    trainer_id: int,
    session: Session,
    reference_date: date,
    overdue_contract_ids: set[int] | None = None,
) -> list[OperationalCase]:
    grouped: dict[int, dict] = {}
    for rate, contract, client in _load_due_soon_rows(
        trainer_id=trainer_id,
        session=session,
        reference_date=reference_date,
    ):
        contract_id = contract.id or 0
        if contract_id in (overdue_contract_ids or set()):
            continue
        bucket = grouped.setdefault(
            contract_id,
            {
                "contract": contract,
                "client": client,
                "rates": [],
                "earliest_due": rate.data_scadenza,
            },
        )
        bucket["rates"].append(rate)
        if rate.data_scadenza < bucket["earliest_due"]:
            bucket["earliest_due"] = rate.data_scadenza

    cases: list[OperationalCase] = []
    for contract_id, data in grouped.items():
        contract = data["contract"]
        client = data["client"]
        rates = data["rates"]
        earliest_due = data["earliest_due"]
        days_left = (earliest_due - reference_date).days
        due_count = len(rates)
        client_label = _full_name(client.nome, client.cognome)
        total_due_amount = round(
            sum(rate.importo_previsto - rate.importo_saldato for rate in rates),
            2,
        )
        contract_residual_amount = round(
            max((contract.prezzo_totale or 0) - contract.totale_versato, 0),
            2,
        )
        reason = (
            f"1 rata in scadenza il {earliest_due.isoformat()}"
            if due_count == 1
            else f"{due_count} rate in scadenza entro 7 giorni"
        )
        case_id = f"case:payment_due_soon:contract:{contract_id}"
        cases.append(
            OperationalCase(
                case_id=case_id,
                merge_key=case_id,
                workspace="renewals_cash",
                case_kind="payment_due_soon",
                title=f"Incasso in arrivo: {client_label}",
                reason=reason,
                severity=_payment_due_soon_severity(days_left),
                bucket=_payment_due_soon_bucket(days_left),
                due_date=earliest_due,
                days_to_due=days_left,
                root_entity=WorkspaceRootEntity(
                    type="contract",
                    id=contract_id,
                    label=contract.tipo_pacchetto or f"Contratto {contract_id}",
                    href=f"/contratti/{contract_id}",
                ),
                secondary_entity=WorkspaceRootEntity(
                    type="client",
                    id=client.id or 0,
                    label=client_label,
                    href=f"/clienti/{client.id}",
                ),
                signal_count=due_count,
                preview_signals=[
                    WorkspaceSignal(
                        signal_code="rate_due_soon",
                        source="upcoming_rates",
                        label=f"Rata in scadenza il {rate.data_scadenza.isoformat()}",
                        severity=_payment_due_soon_severity((rate.data_scadenza - reference_date).days),
                        due_date=rate.data_scadenza,
                        reason="Incasso da pianificare",
                    )
                    for rate in rates[:3]
                ],
                finance_context=WorkspaceFinanceContext(
                    visibility="full",
                    due_date=earliest_due,
                    overdue_count=None,
                    currency="EUR",
                    total_due_amount=total_due_amount,
                    total_residual_amount=contract_residual_amount,
                    contract_id=contract_id,
                ),
                suggested_actions=[
                    _link_action("open-cash", "Apri cassa", "/cassa", primary=True),
                    _link_action("open-contract", "Apri contratto", f"/contratti/{contract_id}", primary=False),
                ],
                source_refs=[f"contract:{contract_id}", *(f"rate:{rate.id}" for rate in rates)],
            )
        )

    return cases


def _load_expiring_contract_rows(
    *,
    trainer_id: int,
    session: Session,
    reference_date: date,
):
    deadline = reference_date + timedelta(days=30)
    contracts = session.exec(
        select(Contract, Client)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
            Contract.chiuso == False,
            Contract.data_scadenza != None,
            Contract.data_scadenza <= deadline,
            Contract.data_scadenza >= reference_date,
            Contract.crediti_totali != None,
        )
        .order_by(Contract.data_scadenza.asc())
    ).all()

    if not contracts:
        return []

    contract_ids = [contract.id for contract, _ in contracts if contract.id is not None]
    credit_rows = session.execute(
        text(
            """
            SELECT e.id_contratto, COUNT(*) as usati
            FROM agenda e
            WHERE e.id_contratto IN :contract_ids
              AND e.categoria = 'PT'
              AND e.stato != 'Cancellato'
              AND e.deleted_at IS NULL
            GROUP BY e.id_contratto
            """
        ).bindparams(bindparam("contract_ids", expanding=True)),
        {"contract_ids": contract_ids},
    ).fetchall()
    credits_map = {row[0]: row[1] for row in credit_rows}

    items = []
    for contract, client in contracts:
        contract_id = contract.id or 0
        used = credits_map.get(contract_id, 0)
        total = contract.crediti_totali or 0
        residual = max(total - used, 0)
        if residual <= 0:
            continue
        due_date = contract.data_scadenza
        if due_date is None:
            continue
        days_left = (due_date - reference_date).days
        items.append((contract, client, residual, days_left, due_date))

    return items


def _build_contract_renewal_cases(
    *,
    trainer_id: int,
    session: Session,
    reference_date: date,
    overdue_contract_ids: set[int] | None = None,
    due_soon_contract_ids: set[int] | None = None,
) -> list[OperationalCase]:
    cases: list[OperationalCase] = []
    for contract, client, residual, days_left, due_date in _load_expiring_contract_rows(
        trainer_id=trainer_id,
        session=session,
        reference_date=reference_date,
    ):
        bucket = _renewal_bucket(days_left)
        contract_id = contract.id or 0
        if contract_id in (due_soon_contract_ids or set()):
            continue
        if contract_id in (overdue_contract_ids or set()):
            bucket = "waiting"
        client_id = client.id or 0
        client_label = _full_name(client.nome, client.cognome)
        case_id = f"case:contract_renewal_due:contract:{contract_id}"
        severity = _renewal_severity(days_left)
        cases.append(
            OperationalCase(
                case_id=case_id,
                merge_key=case_id,
                workspace="renewals_cash",
                case_kind="contract_renewal_due",
                title=f"Rinnovo in arrivo: {client_label}",
                reason=f"{residual} crediti residui, scadenza {due_date.isoformat()}",
                severity=severity,
                bucket=bucket,
                due_date=due_date,
                days_to_due=days_left,
                root_entity=WorkspaceRootEntity(
                    type="contract",
                    id=contract_id,
                    label=contract.tipo_pacchetto or f"Contratto {contract_id}",
                    href=f"/contratti/{contract_id}",
                ),
                secondary_entity=WorkspaceRootEntity(
                    type="client",
                    id=client_id,
                    label=client_label,
                    href=f"/clienti/{client_id}",
                ),
                signal_count=1,
                preview_signals=[
                    WorkspaceSignal(
                        signal_code="contract_renewal_due",
                        source="expiring_contracts",
                        label="Contratto in scadenza",
                        severity=severity,
                        due_date=due_date,
                        reason=f"{residual} crediti residui",
                    )
                ],
                finance_context=WorkspaceFinanceContext(
                    visibility="full",
                    due_date=due_date,
                    overdue_count=None,
                    currency="EUR",
                    total_due_amount=contract.prezzo_totale,
                    total_residual_amount=round(max((contract.prezzo_totale or 0) - contract.totale_versato, 0), 2),
                    contract_id=contract_id,
                ),
                suggested_actions=[
                    _link_action("open-contract", "Apri contratto", f"/contratti/{contract_id}", primary=True),
                ],
                source_refs=[f"contract:{contract_id}"],
            )
        )

    return cases


def _recurring_expense_href(due_date: date) -> str:
    return f"/cassa?tab=recurring&anno={due_date.year}&mese={due_date.month}"


def _build_recurring_expense_due_cases(
    *,
    trainer_id: int,
    session: Session,
    reference_date: date,
) -> list[OperationalCase]:
    deadlines = {reference_date.month: reference_date.year}
    future_deadline = reference_date + timedelta(days=7)
    deadlines[future_deadline.month] = future_deadline.year

    pending_occurrences: list = []
    for mese, anno in deadlines.items():
        pending_occurrences.extend(
            list_pending_recurring_expense_occurrences(
                trainer_id=trainer_id,
                session=session,
                anno=anno,
                mese=mese,
            )
        )

    cases: list[OperationalCase] = []
    seen_keys: set[tuple[int, str]] = set()
    window_end = reference_date + timedelta(days=7)

    for occurrence in pending_occurrences:
        identity = (occurrence.expense_id, occurrence.occurrence_key)
        if identity in seen_keys:
            continue
        seen_keys.add(identity)
        if occurrence.due_date > window_end:
            continue

        days_left = (occurrence.due_date - reference_date).days
        href = _recurring_expense_href(occurrence.due_date)
        case_id = f"case:recurring_expense_due:expense:{occurrence.expense_id}:{occurrence.occurrence_key}"
        cases.append(
            OperationalCase(
                case_id=case_id,
                merge_key=case_id,
                workspace="renewals_cash",
                case_kind="recurring_expense_due",
                title=f"Spesa da confermare: {occurrence.nome}",
                reason=f"Occorrenza prevista il {occurrence.due_date.isoformat()}",
                severity=_recurring_expense_severity(days_left),
                bucket=_recurring_expense_bucket(days_left),
                due_date=occurrence.due_date,
                days_to_due=days_left,
                root_entity=WorkspaceRootEntity(
                    type="expense",
                    id=occurrence.expense_id,
                    label=occurrence.nome,
                    href=href,
                ),
                signal_count=1,
                preview_signals=[
                    WorkspaceSignal(
                        signal_code="recurring_expense_due",
                        source="pending_expenses",
                        label="Spesa ricorrente in attesa di conferma",
                        severity=_recurring_expense_severity(days_left),
                        due_date=occurrence.due_date,
                        reason=occurrence.occurrence_key,
                    )
                ],
                finance_context=WorkspaceFinanceContext(
                    visibility="full",
                    due_date=occurrence.due_date,
                    overdue_count=None,
                    currency="EUR",
                    total_due_amount=occurrence.importo,
                    total_residual_amount=None,
                    contract_id=None,
                ),
                suggested_actions=[
                    _link_action("open-cash", "Apri cassa", href, primary=True),
                ],
                source_refs=[
                    f"recurring_expense:{occurrence.expense_id}",
                    f"recurring_occurrence:{occurrence.occurrence_key}",
                ],
            )
        )

    return cases


def _build_reactivation_cases(
    *,
    trainer_id: int,
    session: Session,
    reference_date: date,
) -> list[OperationalCase]:
    cutoff_14 = reference_date - timedelta(days=14)
    cutoff_start = datetime.combine(cutoff_14, datetime.min.time())
    inactive_clients = session.execute(
        text(
            """
            SELECT cl.id, cl.nome, cl.cognome, cl.telefono, cl.email
            FROM clienti cl
            WHERE cl.trainer_id = :tid
              AND cl.stato = 'Attivo'
              AND cl.deleted_at IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM agenda e
                  WHERE e.id_cliente = cl.id
                    AND e.data_inizio >= :cutoff
                    AND e.stato != 'Cancellato'
                    AND e.deleted_at IS NULL
              )
            ORDER BY cl.nome, cl.cognome
            """
        ),
        {"tid": trainer_id, "cutoff": cutoff_start.isoformat()},
    ).fetchall()

    if not inactive_clients:
        return []

    client_ids = [row[0] for row in inactive_clients]
    last_events = session.execute(
        text(
            """
            SELECT e.id_cliente, e.data_inizio, e.categoria
            FROM agenda e
            INNER JOIN (
                SELECT id_cliente, MAX(data_inizio) as max_data
                FROM agenda
                WHERE id_cliente IN :client_ids
                  AND stato != 'Cancellato'
                  AND deleted_at IS NULL
                GROUP BY id_cliente
            ) latest ON e.id_cliente = latest.id_cliente AND e.data_inizio = latest.max_data
            WHERE e.deleted_at IS NULL AND e.stato != 'Cancellato'
            """
        ).bindparams(bindparam("client_ids", expanding=True)),
        {"client_ids": client_ids},
    ).fetchall()
    last_event_map = {row[0]: (row[1], row[2]) for row in last_events}

    cases: list[OperationalCase] = []
    for client_id, nome, cognome, _telefono, _email in inactive_clients:
        last = last_event_map.get(client_id)
        days_inactive = 14
        if last:
            raw = last[0]
            if isinstance(raw, str):
                last_dt = datetime.fromisoformat(raw.replace(" ", "T"))
                days_inactive = (reference_date - last_dt.date()).days
            elif isinstance(raw, datetime):
                days_inactive = (reference_date - raw.date()).days
            elif isinstance(raw, date):
                days_inactive = (reference_date - raw).days
        client_label = _full_name(nome, cognome)
        severity = _reactivation_severity(days_inactive)
        bucket = _reactivation_bucket(days_inactive)
        case_id = f"case:client_reactivation:client:{client_id}"
        cases.append(
            OperationalCase(
                case_id=case_id,
                merge_key=case_id,
                workspace="today",
                case_kind="client_reactivation",
                title=f"Cliente da riattivare: {client_label}",
                reason=f"Nessuna sessione da {days_inactive} giorni",
                severity=severity,
                bucket=bucket,
                due_date=reference_date,
                days_to_due=0,
                root_entity=WorkspaceRootEntity(
                    type="client",
                    id=client_id,
                    label=client_label,
                    href=f"/clienti/{client_id}",
                ),
                secondary_entity=None,
                signal_count=1,
                preview_signals=[
                    WorkspaceSignal(
                        signal_code="client_inactive",
                        source="inactive_clients",
                        label="Cliente inattivo",
                        severity=severity,
                        due_date=reference_date,
                        reason=f"{days_inactive} giorni senza eventi",
                    )
                ],
                suggested_actions=[
                    _link_action(
                        "schedule-followup",
                        "Pianifica contatto",
                        f"/agenda?newEvent=1&clientId={client_id}",
                        primary=True,
                    ),
                    _link_action("open-client", "Apri cliente", f"/clienti/{client_id}", primary=False),
                ],
                source_refs=[f"client:{client_id}"],
            )
        )

    return cases


def _build_session_case_detail(
    *,
    case: OperationalCase,
    trainer_id: int,
    session: Session,
) -> tuple[list[WorkspaceSignal], list[WorkspaceRootEntity], list[WorkspaceCaseActivityItem]]:
    event_id = _coerce_entity_id(case.root_entity.id)
    if event_id is None:
        return _default_case_detail(case)

    row = session.exec(
        select(Event, Client, Contract)
        .join(Client, Event.id_cliente == Client.id, isouter=True)
        .join(Contract, Event.id_contratto == Contract.id, isouter=True)
        .where(
            Event.trainer_id == trainer_id,
            Event.id == event_id,
            Event.deleted_at == None,
        )
    ).first()
    if row is None:
        return _default_case_detail(case)

    event, client, contract = row
    client_label = _full_name(client.nome, client.cognome) if client else None
    signals = [
        WorkspaceSignal(
            signal_code="event_scheduled",
            source="events",
            label=f"{event.categoria} alle {event.data_inizio.strftime('%H:%M')}",
            severity=case.severity,
            due_date=event.data_inizio.date(),
            reason=case.reason,
        )
    ]
    if client and client.id is not None:
        signals.append(
            WorkspaceSignal(
                signal_code="event_client_attached",
                source="events",
                label="Cliente collegato alla sessione",
                severity="low",
                due_date=event.data_inizio.date(),
                reason=client_label or f"Cliente {client.id}",
            )
        )
    if contract and contract.id is not None:
        signals.append(
            WorkspaceSignal(
                signal_code="event_contract_attached",
                source="events",
                label="Contratto collegato alla sessione",
                severity="low",
                due_date=event.data_inizio.date(),
                reason=contract.tipo_pacchetto or f"Contratto {contract.id}",
            )
        )
    if client and client.id is not None:
        _summary, readiness_items = compute_clinical_readiness_data(
            trainer_id=trainer_id,
            session=session,
            reference_date=event.data_inizio.date(),
        )
        readiness_item = next(
            (
                entry
                for entry in readiness_items
                if entry.client_id == client.id and entry.next_action_code != "ready"
            ),
            None,
        )
        if readiness_item is not None:
            signals.extend(
                WorkspaceSignal(
                    signal_code=step,
                    source="clinical_readiness",
                    label=_READINESS_SIGNAL_LABELS.get(step, step),
                    severity=_readiness_severity(readiness_item),
                    due_date=readiness_item.next_due_date,
                    reason=readiness_item.next_action_label,
                )
                for step in readiness_item.missing_steps
            )

    related_entities = _dedupe_entities(
        case.root_entity,
        case.secondary_entity,
        WorkspaceRootEntity(
            type="contract",
            id=contract.id,
            label=contract.tipo_pacchetto or f"Contratto {contract.id}",
            href=f"/contratti/{contract.id}",
        )
        if contract and contract.id is not None
        else None,
    )
    activity_preview = [
        item
        for item in [
            _make_activity_item(
                at=event.data_creazione,
                label="Evento creato",
                href="/agenda",
            ),
            _make_activity_item(
                at=event.data_inizio,
                label=f"Inizio sessione: {event.categoria}",
                href="/agenda",
            ),
            _make_activity_item(
                at=event.data_fine,
                label="Fine sessione prevista",
                href="/agenda",
            ),
        ]
        if item is not None
    ]
    return signals, related_entities, activity_preview


def _build_readiness_case_detail(
    *,
    case: OperationalCase,
    trainer_id: int,
    session: Session,
    reference_date: date,
) -> tuple[list[WorkspaceSignal], list[WorkspaceRootEntity], list[WorkspaceCaseActivityItem]]:
    client_id = _coerce_entity_id(case.root_entity.id)
    if client_id is None:
        return _default_case_detail(case)

    client = session.get(Client, client_id)
    if client is None or client.trainer_id != trainer_id or client.deleted_at is not None:
        return _default_case_detail(case)

    _summary, items = compute_clinical_readiness_data(
        trainer_id=trainer_id,
        session=session,
        reference_date=reference_date,
    )
    item = next((entry for entry in items if entry.client_id == client_id), None)
    if item is None:
        return _default_case_detail(case)

    signal_labels = {
        "anamnesi_missing": "Anamnesi mancante",
        "anamnesi_legacy": "Anamnesi legacy da rivedere",
        "baseline": "Baseline misure mancante",
        "workout": "Scheda mancante",
    }
    signals = [
        WorkspaceSignal(
            signal_code=step,
            source="clinical_readiness",
            label=signal_labels.get(step, step),
            severity=_readiness_severity(item),
            due_date=item.next_due_date,
            reason=item.next_action_label,
        )
        for step in item.missing_steps
    ]
    activity_preview = [
        item_
        for item_ in [
            _make_activity_item(
                at=client.data_creazione,
                label="Cliente creato",
                href=f"/clienti/{client_id}",
            ),
            _make_activity_item(
                at=item.next_due_date or reference_date,
                label=f"Prossimo step: {item.next_action_label}",
                href=item.next_action_href,
            ),
        ]
        if item_ is not None
    ]
    return signals, _dedupe_entities(case.root_entity), activity_preview


def _build_todo_case_detail(
    *,
    case: OperationalCase,
    trainer_id: int,
    session: Session,
    reference_date: date,
) -> tuple[list[WorkspaceSignal], list[WorkspaceRootEntity], list[WorkspaceCaseActivityItem]]:
    todo_id = _coerce_entity_id(case.root_entity.id)
    if todo_id is None:
        return _default_case_detail(case)

    todo = session.get(Todo, todo_id)
    if todo is None or todo.trainer_id != trainer_id or todo.deleted_at is not None:
        return _default_case_detail(case)

    reason = (
        f"Scade il {todo.data_scadenza.isoformat()}"
        if todo.data_scadenza
        else "Promemoria senza scadenza"
    )
    signals = [
        WorkspaceSignal(
            signal_code="todo_open",
            source="todos",
            label="Todo aperto",
            severity=_todo_severity(todo, reference_date),
            due_date=todo.data_scadenza,
            reason=reason,
        )
    ]
    if todo.descrizione:
        signals.append(
            WorkspaceSignal(
                signal_code="todo_description_present",
                source="todos",
                label="Note operative presenti",
                severity="low",
                due_date=todo.data_scadenza,
                reason=todo.descrizione,
            )
        )
    activity_preview = [
        item
        for item in [
            _make_activity_item(
                at=todo.created_at,
                label="Todo creato",
                href="/",
            ),
            _make_activity_item(
                at=todo.data_scadenza,
                label="Scadenza promemoria",
                href="/",
            ),
        ]
        if item is not None
    ]
    return signals, _dedupe_entities(case.root_entity), activity_preview


def _build_payment_overdue_case_detail(
    *,
    case: OperationalCase,
    trainer_id: int,
    session: Session,
    reference_date: date,
) -> tuple[list[WorkspaceSignal], list[WorkspaceRootEntity], list[WorkspaceCaseActivityItem]]:
    contract_id = _coerce_entity_id(case.root_entity.id)
    if contract_id is None:
        return _default_case_detail(case)

    contract_row = session.exec(
        select(Contract, Client)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.id == contract_id,
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
        )
    ).first()
    if contract_row is None:
        return _default_case_detail(case)

    contract, client = contract_row
    rates = session.exec(
        select(Rate)
        .where(
            Rate.id_contratto == contract_id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.data_scadenza < reference_date,
            Rate.deleted_at == None,
        )
        .order_by(Rate.data_scadenza.asc())
    ).all()
    client_label = _full_name(client.nome, client.cognome)
    signals = [
        WorkspaceSignal(
            signal_code=f"rate_overdue_{rate.id}",
            source="overdue_rates",
            label=f"Rata scaduta del {rate.data_scadenza.isoformat()}",
            severity="critical",
            due_date=rate.data_scadenza,
            reason="Incasso non ancora registrato",
        )
        for rate in rates
    ]
    related_entities = _dedupe_entities(
        case.root_entity,
        case.secondary_entity,
        WorkspaceRootEntity(
            type="client",
            id=client.id or 0,
            label=client_label,
            href=f"/clienti/{client.id}",
        ),
    )
    activity_preview = [
        item
        for item in [
            _make_activity_item(
                at=contract.data_vendita,
                label="Contratto registrato",
                href=f"/contratti/{contract_id}",
            ),
            *[
                _make_activity_item(
                    at=rate.data_scadenza,
                    label=f"Scadenza rata: {rate.data_scadenza.isoformat()}",
                    href=f"/contratti/{contract_id}",
                )
                for rate in rates[:5]
            ],
            _make_activity_item(
                at=contract.data_scadenza,
                label="Scadenza contratto",
                href=f"/contratti/{contract_id}",
            ),
        ]
        if item is not None
    ]
    return signals or list(case.preview_signals), related_entities, activity_preview


def _build_payment_due_soon_case_detail(
    *,
    case: OperationalCase,
    trainer_id: int,
    session: Session,
    reference_date: date,
) -> tuple[list[WorkspaceSignal], list[WorkspaceRootEntity], list[WorkspaceCaseActivityItem]]:
    contract_id = _coerce_entity_id(case.root_entity.id)
    if contract_id is None:
        return _default_case_detail(case)

    contract_row = session.exec(
        select(Contract, Client)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.id == contract_id,
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
        )
    ).first()
    if contract_row is None:
        return _default_case_detail(case)

    contract, client = contract_row
    deadline = reference_date + timedelta(days=7)
    rates = session.exec(
        select(Rate)
        .where(
            Rate.id_contratto == contract_id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.data_scadenza >= reference_date,
            Rate.data_scadenza <= deadline,
            Rate.deleted_at == None,
        )
        .order_by(Rate.data_scadenza.asc())
    ).all()
    client_label = _full_name(client.nome, client.cognome)
    signals = [
        WorkspaceSignal(
            signal_code=f"rate_due_soon_{rate.id}",
            source="upcoming_rates",
            label=f"Rata in scadenza il {rate.data_scadenza.isoformat()}",
            severity=_payment_due_soon_severity((rate.data_scadenza - reference_date).days),
            due_date=rate.data_scadenza,
            reason="Incasso da pianificare",
        )
        for rate in rates
    ]
    related_entities = _dedupe_entities(
        case.root_entity,
        case.secondary_entity,
        WorkspaceRootEntity(
            type="client",
            id=client.id or 0,
            label=client_label,
            href=f"/clienti/{client.id}",
        ),
    )
    activity_preview = [
        item
        for item in [
            _make_activity_item(
                at=contract.data_vendita,
                label="Contratto registrato",
                href=f"/contratti/{contract_id}",
            ),
            *[
                _make_activity_item(
                    at=rate.data_scadenza,
                    label=f"Scadenza rata: {rate.data_scadenza.isoformat()}",
                    href=f"/contratti/{contract_id}",
                )
                for rate in rates[:5]
            ],
            _make_activity_item(
                at=contract.data_scadenza,
                label="Scadenza contratto",
                href=f"/contratti/{contract_id}",
            ),
        ]
        if item is not None
    ]
    return signals or list(case.preview_signals), related_entities, activity_preview


def _build_contract_renewal_case_detail(
    *,
    case: OperationalCase,
    trainer_id: int,
    session: Session,
) -> tuple[list[WorkspaceSignal], list[WorkspaceRootEntity], list[WorkspaceCaseActivityItem]]:
    contract_id = _coerce_entity_id(case.root_entity.id)
    if contract_id is None:
        return _default_case_detail(case)

    contract_row = session.exec(
        select(Contract, Client)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.id == contract_id,
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
        )
    ).first()
    if contract_row is None:
        return _default_case_detail(case)

    contract, client = contract_row
    used_credits = session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM agenda e
            WHERE e.id_contratto = :contract_id
              AND e.categoria = 'PT'
              AND e.stato != 'Cancellato'
              AND e.deleted_at IS NULL
            """
        ),
        {"contract_id": contract_id},
    ).scalar_one()
    total_credits = contract.crediti_totali or 0
    residual_credits = max(total_credits - used_credits, 0)
    due_date = contract.data_scadenza
    signals = [
        WorkspaceSignal(
            signal_code="contract_expiring",
            source="expiring_contracts",
            label="Contratto in scadenza",
            severity=case.severity,
            due_date=due_date,
            reason=case.reason,
        ),
        WorkspaceSignal(
            signal_code="contract_residual_credits",
            source="expiring_contracts",
            label="Crediti residui da gestire",
            severity="medium" if residual_credits > 0 else "low",
            due_date=due_date,
            reason=f"{residual_credits} crediti residui",
        ),
    ]
    related_entities = _dedupe_entities(
        case.root_entity,
        case.secondary_entity,
        WorkspaceRootEntity(
            type="client",
            id=client.id or 0,
            label=_full_name(client.nome, client.cognome),
            href=f"/clienti/{client.id}",
        ),
    )
    activity_preview = [
        item
        for item in [
            _make_activity_item(
                at=contract.data_vendita,
                label="Contratto venduto",
                href=f"/contratti/{contract_id}",
            ),
            _make_activity_item(
                at=contract.data_inizio,
                label="Inizio contratto",
                href=f"/contratti/{contract_id}",
            ),
            _make_activity_item(
                at=contract.data_scadenza,
                label="Scadenza contratto",
                href=f"/contratti/{contract_id}",
            ),
        ]
        if item is not None
    ]
    return signals, related_entities, activity_preview


def _extract_recurring_occurrence_key(case: OperationalCase) -> str | None:
    for ref in case.source_refs:
        if ref.startswith("recurring_occurrence:"):
            return ref.split(":", 1)[1]
    return None


def _build_recurring_expense_case_detail(
    *,
    case: OperationalCase,
    trainer_id: int,
    session: Session,
) -> tuple[list[WorkspaceSignal], list[WorkspaceRootEntity], list[WorkspaceCaseActivityItem]]:
    expense_id = _coerce_entity_id(case.root_entity.id)
    occurrence_key = _extract_recurring_occurrence_key(case)
    if expense_id is None or not occurrence_key:
        return _default_case_detail(case)

    expense = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.id == expense_id,
            RecurringExpense.trainer_id == trainer_id,
            RecurringExpense.deleted_at == None,
        )
    ).first()
    if expense is None:
        return _default_case_detail(case)

    signals = [
        WorkspaceSignal(
            signal_code="recurring_expense_due",
            source="pending_expenses",
            label="Spesa ricorrente in attesa di conferma",
            severity=case.severity,
            due_date=case.due_date,
            reason=occurrence_key,
        )
    ]
    if expense.categoria:
        signals.append(
            WorkspaceSignal(
                signal_code="recurring_expense_category",
                source="pending_expenses",
                label="Categoria spesa",
                severity="low",
                due_date=case.due_date,
                reason=expense.categoria,
            )
        )

    related_entities = _dedupe_entities(case.root_entity)
    activity_preview = [
        item
        for item in [
            _make_activity_item(
                at=expense.data_creazione,
                label="Spesa ricorrente creata",
                href=case.root_entity.href,
            ),
            _make_activity_item(
                at=expense.data_inizio,
                label="Inizio ciclo",
                href=case.root_entity.href,
            ),
            _make_activity_item(
                at=case.due_date,
                label=f"Occorrenza dovuta: {case.due_date.isoformat()}" if case.due_date else "",
                href=case.root_entity.href,
            ),
        ]
        if item is not None
    ]
    return signals, related_entities, activity_preview


def _build_reactivation_case_detail(
    *,
    case: OperationalCase,
    trainer_id: int,
    session: Session,
    reference_date: date,
) -> tuple[list[WorkspaceSignal], list[WorkspaceRootEntity], list[WorkspaceCaseActivityItem]]:
    client_id = _coerce_entity_id(case.root_entity.id)
    if client_id is None:
        return _default_case_detail(case)

    client = session.get(Client, client_id)
    if client is None or client.trainer_id != trainer_id or client.deleted_at is not None:
        return _default_case_detail(case)

    last_event = session.exec(
        select(Event)
        .where(
            Event.trainer_id == trainer_id,
            Event.id_cliente == client_id,
            Event.stato != "Cancellato",
            Event.deleted_at == None,
        )
        .order_by(Event.data_inizio.desc())
    ).first()

    days_inactive = 14
    if last_event is not None:
        days_inactive = (reference_date - last_event.data_inizio.date()).days

    signals = [
        WorkspaceSignal(
            signal_code="client_inactive",
            source="inactive_clients",
            label="Cliente inattivo",
            severity=_reactivation_severity(days_inactive),
            due_date=reference_date,
            reason=f"{days_inactive} giorni senza eventi",
        )
    ]
    if last_event is not None:
        signals.append(
            WorkspaceSignal(
                signal_code="last_client_event",
                source="inactive_clients",
                label="Ultimo evento registrato",
                severity="low",
                due_date=last_event.data_inizio.date(),
                reason=f"{last_event.categoria} del {last_event.data_inizio.date().isoformat()}",
            )
        )

    related_entities = _dedupe_entities(
        case.root_entity,
        WorkspaceRootEntity(
            type="event",
            id=last_event.id or 0,
            label=last_event.titolo or last_event.categoria,
            href="/agenda",
        )
        if last_event is not None
        else None,
    )
    activity_preview = [
        item
        for item in [
            _make_activity_item(
                at=client.data_creazione,
                label="Cliente creato",
                href=f"/clienti/{client_id}",
            ),
            _make_activity_item(
                at=last_event.data_inizio if last_event is not None else None,
                label=f"Ultimo evento: {(last_event.titolo or last_event.categoria) if last_event is not None else ''}",
                href="/agenda" if last_event is not None else None,
            ),
        ]
        if item is not None
    ]
    return signals, related_entities, activity_preview


def _build_case_detail_payload(
    *,
    case: OperationalCase,
    trainer_id: int,
    session: Session,
    reference_dt: datetime,
) -> tuple[list[WorkspaceSignal], list[WorkspaceRootEntity], list[WorkspaceCaseActivityItem]]:
    reference_date = reference_dt.date()
    if case.case_kind == "session_imminent":
        return _build_session_case_detail(case=case, trainer_id=trainer_id, session=session)
    if case.case_kind == "onboarding_readiness":
        return _build_readiness_case_detail(
            case=case,
            trainer_id=trainer_id,
            session=session,
            reference_date=reference_date,
        )
    if case.case_kind == "todo_manual":
        return _build_todo_case_detail(
            case=case,
            trainer_id=trainer_id,
            session=session,
            reference_date=reference_date,
        )
    if case.case_kind == "payment_overdue":
        return _build_payment_overdue_case_detail(
            case=case,
            trainer_id=trainer_id,
            session=session,
            reference_date=reference_date,
        )
    if case.case_kind == "payment_due_soon":
        return _build_payment_due_soon_case_detail(
            case=case,
            trainer_id=trainer_id,
            session=session,
            reference_date=reference_date,
        )
    if case.case_kind == "contract_renewal_due":
        return _build_contract_renewal_case_detail(
            case=case,
            trainer_id=trainer_id,
            session=session,
        )
    if case.case_kind == "recurring_expense_due":
        return _build_recurring_expense_case_detail(
            case=case,
            trainer_id=trainer_id,
            session=session,
        )
    if case.case_kind == "client_reactivation":
        return _build_reactivation_case_detail(
            case=case,
            trainer_id=trainer_id,
            session=session,
            reference_date=reference_date,
        )
    return _default_case_detail(case)


def collect_workspace_snapshot(
    *,
    trainer_id: int,
    session: Session,
    reference_dt: datetime | None = None,
) -> tuple[list[OperationalCase], list[WorkspaceAgendaItem], int, datetime]:
    now_dt = reference_dt or _now_local()
    today = now_dt.date()
    _readiness_summary, readiness_items = compute_clinical_readiness_data(
        trainer_id=trainer_id,
        session=session,
        reference_date=today,
    )
    readiness_by_client = {item.client_id: item for item in readiness_items}

    session_cases, agenda_items, session_blocked_client_ids = _build_session_cases(
        trainer_id=trainer_id,
        session=session,
        reference_dt=now_dt,
        readiness_by_client=readiness_by_client,
    )
    onboarding_cases = _build_readiness_cases(
        trainer_id=trainer_id,
        session=session,
        reference_dt=now_dt,
        readiness_items=readiness_items,
        session_blocked_client_ids=session_blocked_client_ids,
    )
    todo_cases, completed_today_count = _build_todo_cases(
        trainer_id=trainer_id,
        session=session,
        reference_date=today,
    )
    overdue_cases = _build_payment_overdue_cases(
        trainer_id=trainer_id,
        session=session,
        reference_date=today,
    )
    overdue_contract_ids = {
        int(case.root_entity.id)
        for case in overdue_cases
        if case.root_entity.type == "contract" and _coerce_entity_id(case.root_entity.id) is not None
    }
    due_soon_cases = _build_payment_due_soon_cases(
        trainer_id=trainer_id,
        session=session,
        reference_date=today,
        overdue_contract_ids=overdue_contract_ids,
    )
    due_soon_contract_ids = {
        int(case.root_entity.id)
        for case in due_soon_cases
        if case.root_entity.type == "contract" and _coerce_entity_id(case.root_entity.id) is not None
    }
    renewal_cases = _build_contract_renewal_cases(
        trainer_id=trainer_id,
        session=session,
        reference_date=today,
        overdue_contract_ids=overdue_contract_ids,
        due_soon_contract_ids=due_soon_contract_ids,
    )
    recurring_expense_cases = _build_recurring_expense_due_cases(
        trainer_id=trainer_id,
        session=session,
        reference_date=today,
    )
    reactivation_cases = _build_reactivation_cases(
        trainer_id=trainer_id,
        session=session,
        reference_date=today,
    )

    all_cases = [
        *session_cases,
        *onboarding_cases,
        *todo_cases,
        *overdue_cases,
        *due_soon_cases,
        *renewal_cases,
        *recurring_expense_cases,
        *reactivation_cases,
    ]
    all_cases.sort(key=_sort_case)

    return all_cases, agenda_items, completed_today_count, now_dt


def build_workspace_today(
    *,
    trainer_id: int,
    session: Session,
    reference_dt: datetime | None = None,
) -> WorkspaceTodayResponse:
    all_cases, agenda_items, completed_today_count, now_dt = collect_workspace_snapshot(
        trainer_id=trainer_id,
        session=session,
        reference_dt=reference_dt,
    )
    today = now_dt.date()
    visible_cases = [
        _apply_finance_visibility(case, "redacted")
        for case in all_cases
        if _case_matches_workspace(case, "today")
    ]

    grouped: dict[str, list[OperationalCase]] = defaultdict(list)
    for case in visible_cases:
        grouped[case.bucket].append(case)
    visible_by_bucket = _apply_today_viewport_budget(grouped)

    sections = [
        WorkspaceTodaySection(
            bucket=bucket,
            label=_SECTION_LABELS[bucket],
            total=len(grouped[bucket]),
            items=visible_by_bucket.get(bucket, []),
        )
        for bucket in _SECTION_ORDER
    ]

    next_event_id = next(
        (item.event_id for item in agenda_items if item.status in {"current", "upcoming"}),
        None,
    )

    summary = _summarize_cases(visible_cases, workspace="today", generated_at=now_dt)

    return WorkspaceTodayResponse(
        summary=summary,
        focus_case=_first_visible_case(visible_by_bucket),
        agenda=WorkspaceTodayAgenda(
            date=today,
            current_time=now_dt,
            next_event_id=next_event_id,
            items=agenda_items,
        ),
        sections=sections,
        completed_today_count=completed_today_count,
        snoozed_count=0,
    )


def build_workspace_case_list(
    *,
    trainer_id: int,
    session: Session,
    workspace: str,
    page: int = 1,
    page_size: int = 25,
    bucket: str | None = None,
    severity: str | None = None,
    case_kind: str | None = None,
    search: str | None = None,
    sort_by: str = "priority",
    reference_dt: datetime | None = None,
) -> WorkspaceCaseListResponse:
    all_cases, _agenda_items, _completed_today_count, now_dt = collect_workspace_snapshot(
        trainer_id=trainer_id,
        session=session,
        reference_dt=reference_dt,
    )

    workspace_cases = [
        _apply_finance_visibility(case, "full" if workspace == "renewals_cash" else "redacted")
        for case in all_cases
        if _case_matches_workspace(case, workspace)
    ]
    summary = _summarize_cases(workspace_cases, workspace=workspace, generated_at=now_dt)

    filtered = _filter_cases(
        all_cases,
        workspace=workspace,
        bucket=bucket,
        severity=severity,
        case_kind=case_kind,
        search=search,
    )
    filtered = [
        _apply_finance_visibility(case, "full" if workspace == "renewals_cash" else "redacted")
        for case in filtered
    ]
    sorted_cases = _sort_cases(filtered, sort_by=sort_by)

    total = len(sorted_cases)
    offset = (page - 1) * page_size
    paged_items = sorted_cases[offset: offset + page_size]

    return WorkspaceCaseListResponse(
        summary=summary,
        items=paged_items,
        total=total,
        page=page,
        page_size=page_size,
        filters_applied=WorkspaceCaseListFilters(
            workspace=workspace,
            bucket=bucket,
            severity=severity,
            case_kind=case_kind,
            search=search,
            sort_by=sort_by,
        ),
    )


def build_workspace_case_detail(
    *,
    trainer_id: int,
    session: Session,
    workspace: str,
    case_id: str,
    reference_dt: datetime | None = None,
) -> WorkspaceCaseDetailResponse | None:
    all_cases, _agenda_items, _completed_today_count, now_dt = collect_workspace_snapshot(
        trainer_id=trainer_id,
        session=session,
        reference_dt=reference_dt,
    )
    visibility = "full" if workspace == "renewals_cash" else "redacted"
    selected_case = next(
        (
            _apply_finance_visibility(case, visibility)
            for case in all_cases
            if case.case_id == case_id and _case_matches_workspace(case, workspace)
        ),
        None,
    )
    if selected_case is None:
        return None

    signals, related_entities, activity_preview = _build_case_detail_payload(
        case=selected_case,
        trainer_id=trainer_id,
        session=session,
        reference_dt=now_dt,
    )

    return WorkspaceCaseDetailResponse(
        case=selected_case,
        signals=signals,
        related_entities=related_entities,
        activity_preview=activity_preview,
    )
