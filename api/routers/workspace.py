"""Operational workspace endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.schemas.workspace import (
    WorkspaceCaseDetailResponse,
    WorkspaceCaseListResponse,
    WorkspaceTodayResponse,
)
from api.services.workspace_engine import (
    build_workspace_case_detail,
    build_workspace_case_list,
    build_workspace_today,
)

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("/today", response_model=WorkspaceTodayResponse)
def get_workspace_today(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Read-only operational home for the authenticated trainer."""
    return build_workspace_today(
        trainer_id=trainer.id,
        session=session,
    )


@router.get("/cases", response_model=WorkspaceCaseListResponse)
def get_workspace_cases(
    workspace: str = Query(default="today", pattern="^(today|onboarding|programmi|renewals_cash)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    bucket: str | None = Query(default=None, pattern="^(now|today|upcoming_3d|upcoming_7d|waiting)$"),
    severity: str | None = Query(default=None, pattern="^(critical|high|medium|low)$"),
    case_kind: str | None = Query(
        default=None,
        pattern="^(onboarding_readiness|session_imminent|followup_post_session|todo_manual|plan_activation|plan_review_due|plan_compliance_risk|plan_cycle_closing|payment_overdue|payment_due_soon|contract_renewal_due|recurring_expense_due|client_reactivation|ops_anomaly|portal_questionnaire_pending)$",
    ),
    search: str | None = Query(default=None, max_length=120),
    sort_by: str = Query(default="priority", pattern="^(priority|due_date)$"),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Paginated and filterable list of operational cases."""
    return build_workspace_case_list(
        trainer_id=trainer.id,
        session=session,
        workspace=workspace,
        page=page,
        page_size=page_size,
        bucket=bucket,
        severity=severity,
        case_kind=case_kind,
        search=search,
        sort_by=sort_by,
    )


@router.get("/cases/{case_id}", response_model=WorkspaceCaseDetailResponse)
def get_workspace_case_detail(
    case_id: str,
    workspace: str = Query(default="today", pattern="^(today|onboarding|programmi|renewals_cash)$"),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Read-only detail payload for a single operational case."""
    detail = build_workspace_case_detail(
        trainer_id=trainer.id,
        session=session,
        workspace=workspace,
        case_id=case_id,
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="Workspace case not found")
    return detail
