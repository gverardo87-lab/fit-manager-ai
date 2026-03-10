"""Schemas for operational workspace payloads."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


WorkspaceId = Literal["today", "onboarding", "programmi", "renewals_cash"]
CaseSeverity = Literal["critical", "high", "medium", "low"]
CaseBucket = Literal["now", "today", "upcoming_3d", "upcoming_7d", "waiting"]
AgendaStatus = Literal["past", "current", "upcoming"]
RootEntityType = Literal[
    "client",
    "contract",
    "plan",
    "event",
    "todo",
    "expense",
    "portal_share",
    "system",
]
CaseKind = Literal[
    "onboarding_readiness",
    "session_imminent",
    "followup_post_session",
    "todo_manual",
    "plan_activation",
    "plan_review_due",
    "plan_compliance_risk",
    "plan_cycle_closing",
    "payment_overdue",
    "payment_due_soon",
    "contract_renewal_due",
    "recurring_expense_due",
    "client_reactivation",
    "ops_anomaly",
    "portal_questionnaire_pending",
]
WorkspaceActionKind = Literal[
    "navigate",
    "deep_link",
    "snooze_future",
    "mark_managed_future",
    "convert_todo_future",
]
FinanceVisibility = Literal["hidden", "redacted", "full"]
CaseSortBy = Literal["priority", "due_date"]


class WorkspaceRootEntity(BaseModel):
    type: RootEntityType
    id: int | str
    label: str
    href: str | None = None


class WorkspaceAction(BaseModel):
    id: str
    label: str
    kind: WorkspaceActionKind
    href: str | None = None
    enabled: bool = True
    availability_note: str | None = None
    is_primary: bool = False


class WorkspaceSignal(BaseModel):
    signal_code: str
    source: str
    label: str
    severity: CaseSeverity
    due_date: date | None = None
    reason: str


class WorkspaceFinanceContext(BaseModel):
    visibility: FinanceVisibility = "hidden"
    due_date: date | None = None
    overdue_count: int | None = None
    currency: Literal["EUR"] | None = None
    total_due_amount: float | None = None
    total_residual_amount: float | None = None
    contract_id: int | None = None


class OperationalCase(BaseModel):
    case_id: str
    merge_key: str
    workspace: WorkspaceId
    case_kind: CaseKind
    title: str
    reason: str
    severity: CaseSeverity
    bucket: CaseBucket
    due_date: date | None = None
    due_at: datetime | None = None
    days_to_due: int | None = None
    root_entity: WorkspaceRootEntity
    secondary_entity: WorkspaceRootEntity | None = None
    signal_count: int = 0
    preview_signals: list[WorkspaceSignal] = Field(default_factory=list)
    finance_context: WorkspaceFinanceContext | None = None
    suggested_actions: list[WorkspaceAction] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)


class WorkspaceAgendaItem(BaseModel):
    event_id: int
    client_id: int | None = None
    client_label: str | None = None
    title: str
    category: str
    status: AgendaStatus
    starts_at: datetime
    ends_at: datetime | None = None
    href: str
    has_case_warning: bool = False


class WorkspaceSummary(BaseModel):
    workspace: WorkspaceId
    generated_at: datetime
    critical_count: int = 0
    now_count: int = 0
    today_count: int = 0
    upcoming_7d_count: int = 0
    waiting_count: int = 0


class WorkspaceTodaySection(BaseModel):
    bucket: CaseBucket
    label: str
    total: int = 0
    items: list[OperationalCase] = Field(default_factory=list)


class WorkspaceTodayAgenda(BaseModel):
    date: date
    current_time: datetime
    next_event_id: int | None = None
    items: list[WorkspaceAgendaItem] = Field(default_factory=list)


class WorkspaceTodayResponse(BaseModel):
    summary: WorkspaceSummary
    focus_case: OperationalCase | None = None
    agenda: WorkspaceTodayAgenda
    sections: list[WorkspaceTodaySection] = Field(default_factory=list)
    completed_today_count: int = 0
    snoozed_count: int = 0


class WorkspaceCaseListFilters(BaseModel):
    workspace: WorkspaceId
    bucket: CaseBucket | None = None
    severity: CaseSeverity | None = None
    case_kind: CaseKind | None = None
    search: str | None = None
    sort_by: CaseSortBy = "priority"


class WorkspaceCaseListResponse(BaseModel):
    summary: WorkspaceSummary
    items: list[OperationalCase] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 25
    filters_applied: WorkspaceCaseListFilters


class WorkspaceCaseActivityItem(BaseModel):
    at: datetime
    label: str
    href: str | None = None


class WorkspaceCaseDetailResponse(BaseModel):
    case: OperationalCase
    signals: list[WorkspaceSignal] = Field(default_factory=list)
    related_entities: list[WorkspaceRootEntity] = Field(default_factory=list)
    activity_preview: list[WorkspaceCaseActivityItem] = Field(default_factory=list)


# ── Session Prep (cockpit chinesiologo) ──


HealthCheckStatus = Literal["ok", "warning", "critical", "missing"]


class SessionPrepHealthCheck(BaseModel):
    """Singola spunta salute (anamnesi/misurazioni/scheda/programma)."""

    domain: str
    label: str
    status: HealthCheckStatus
    detail: str | None = None
    days_since_last: int | None = None
    cta_href: str | None = None


class SessionPrepAlert(BaseModel):
    """Alert clinico sintetico (condizione medica attiva)."""

    condition_name: str
    category: str | None = None


class SessionPrepHint(BaseModel):
    """Spunto qualita' servizio."""

    code: str
    text: str
    severity: CaseSeverity = "medium"
    cta_href: str | None = None


class SessionPrepItem(BaseModel):
    """Profilo operativo completo per una sessione della giornata."""

    event_id: int
    starts_at: datetime
    ends_at: datetime | None = None
    category: str
    event_title: str | None = None
    event_notes: str | None = None
    client_id: int | None = None
    client_name: str | None = None
    client_age: int | None = None
    client_sex: str | None = None
    client_since: date | None = None
    is_new_client: bool = False
    total_sessions: int = 0
    completed_sessions: int = 0
    last_session_date: date | None = None
    days_since_last_session: int | None = None
    health_checks: list[SessionPrepHealthCheck] = Field(default_factory=list)
    clinical_alerts: list[SessionPrepAlert] = Field(default_factory=list)
    quality_hints: list[SessionPrepHint] = Field(default_factory=list)
    active_plan_name: str | None = None
    contract_credits_remaining: int | None = None
    contract_credits_total: int | None = None
    readiness_score: int | None = None


class SessionPrepResponse(BaseModel):
    """Risposta completa session prep per la giornata."""

    date: date
    current_time: datetime
    sessions: list[SessionPrepItem] = Field(default_factory=list)
    non_client_events: list[SessionPrepItem] = Field(default_factory=list)
    total_sessions: int = 0
    clients_with_alerts: int = 0
