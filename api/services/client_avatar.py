# api/services/client_avatar.py
"""
Client Avatar Service — oggetto composito dello stato completo di un cliente.

Entry point:
  build_avatar(session, trainer_id, client_id) -> ClientAvatar
  build_avatars_batch(session, trainer_id, client_ids) -> list[ClientAvatar]

Anti-N+1: ~12 query per qualsiasi batch size.
Riusa compute_clinical_readiness_data, extract_client_conditions,
build_measurement_freshness per evitare drift.
"""

import logging
from datetime import date, datetime, timezone

from sqlmodel import Session, select, func

from api.models.client import Client
from api.models.contract import Contract
from api.models.goal import ClientGoal
from api.models.measurement import ClientMeasurement
from api.models.rate import Rate
from api.models.workout import WorkoutPlan
from api.models.workout_log import WorkoutLog
from api.schemas.client_avatar import (
    AvatarBodyGoals,
    AvatarClinicalProfile,
    AvatarContractStatus,
    AvatarIdentity,
    AvatarTrainingPath,
    ClientAvatar,
    Momentum,
    SemaphoreStatus,
    TrendDirection,
)
from api.services.client_avatar_highlights import AvatarContext, compute_highlights
from api.services.client_freshness import build_measurement_freshness
from api.services.clinical_readiness import _get_anamnesi_state
from api.services.safety_engine import extract_client_conditions

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client_age(data_nascita: date | None, reference: date) -> int | None:
    if not data_nascita:
        return None
    age = reference.year - data_nascita.year
    if (reference.month, reference.day) < (data_nascita.month, data_nascita.day):
        age -= 1
    return age


def _parse_date(value) -> date | None:
    """Parse date from string or date object (SQLite returns strings)."""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except (ValueError, TypeError):
            return None
    return None


def _parse_datetime(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
    return None


def _anamnesi_version(state: str) -> int:
    return {"missing": 0, "legacy": 1, "structured": 2}.get(state, 0)


def _compute_trend(
    recent: float | None, older: float | None, threshold: float = 0.10
) -> TrendDirection:
    """Compare 30d window vs prior 30d. ±threshold = significant change."""
    if recent is None or older is None:
        return "unknown"
    delta = recent - older
    if delta >= threshold:
        return "up"
    if delta <= -threshold:
        return "down"
    return "stable"


def _compute_momentum(
    compliance_trend: TrendDirection,
    pt_attendance_trend: TrendDirection,
    has_active_plan: bool,
    days_since_last: int | None,
) -> Momentum:
    """Composite of compliance + PT attendance trends."""
    if not has_active_plan and (days_since_last is None or days_since_last >= 30):
        return "inactive"
    trend_scores = {"up": 1, "stable": 0, "down": -1, "unknown": 0}
    score = trend_scores[compliance_trend] + trend_scores[pt_attendance_trend]
    if score >= 1:
        return "accelerating"
    if score <= -1:
        return "decelerating"
    return "steady"


# ---------------------------------------------------------------------------
# Dimension builders
# ---------------------------------------------------------------------------

def _build_identity(
    client: Client,
    reference: date,
) -> AvatarIdentity:
    age = _client_age(client.data_nascita, reference)
    created = _parse_datetime(client.data_creazione) or _parse_datetime(
        getattr(client, "created_at", None)
    )
    seniority = (reference - created.date()).days if created else 0
    status: SemaphoreStatus = "green" if client.stato == "Attivo" else "red"

    return AvatarIdentity(
        id=client.id or 0,
        nome=client.nome,
        cognome=client.cognome,
        full_name=f"{client.nome} {client.cognome}",
        age=age,
        sesso=client.sesso,
        telefono=client.telefono,
        email=client.email,
        client_since=created.date().isoformat() if created else None,
        seniority_days=max(seniority, 0),
        stato=client.stato or "Attivo",
        status=status,
    )


def _build_clinical(
    client: Client,
    condition_ids: set[int],
    condition_names_map: dict[int, str],
) -> AvatarClinicalProfile:
    state = _get_anamnesi_state(client.anamnesi_json)
    names = sorted(condition_names_map[cid] for cid in condition_ids if cid in condition_names_map)
    count = len(condition_ids)

    if count == 0:
        risk = "low"
    elif count <= 2:
        risk = "medium"
    else:
        risk = "high"

    if state == "missing":
        status: SemaphoreStatus = "red"
    elif state == "legacy":
        status = "amber"
    else:
        status = "green"

    return AvatarClinicalProfile(
        anamnesi_state=state,
        anamnesi_version=_anamnesi_version(state),
        condition_count=count,
        condition_names=names,
        risk_level=risk,
        status=status,
    )


def _build_contract(
    *,
    active_contract: Contract | None,
    credits_used: int,
    overdue_count: int,
    renewal_count: int,
    reference: date,
) -> AvatarContractStatus:
    if not active_contract:
        return AvatarContractStatus(status="red")

    total = active_contract.crediti_totali or 0
    remaining = max(0, total - credits_used)
    used_pct = (credits_used / total * 100) if total > 0 else 0.0

    expiry = _parse_date(active_contract.data_scadenza)
    days_to_expiry = (expiry - reference).days if expiry else None

    payment_status = active_contract.stato_pagamento or "PENDENTE"

    # Semaphore
    if overdue_count > 0 or remaining <= 0:
        status: SemaphoreStatus = "red"
    elif remaining <= 2 or (days_to_expiry is not None and days_to_expiry <= 14):
        status = "amber"
    else:
        status = "green"

    return AvatarContractStatus(
        has_active_contract=True,
        active_contract_id=active_contract.id,
        credits_remaining=remaining,
        credits_total=total,
        credits_used_pct=round(used_pct, 1),
        days_to_expiry=days_to_expiry,
        payment_status=payment_status,
        overdue_rates_count=overdue_count,
        renewal_count=renewal_count,
        status=status,
    )


def _build_training(
    *,
    active_plan: WorkoutPlan | None,
    total_sessions: int,
    completed_sessions: int,
    days_since_last: int | None,
    compliance_30d: float | None,
    compliance_60d: float | None,
    compliance_trend: TrendDirection = "unknown",
    pt_sessions_completed_30d: int = 0,
    pt_sessions_scheduled_30d: int = 0,
    pt_attendance_30d: float | None = None,
    pt_attendance_60d: float | None = None,
    pt_attendance_trend: TrendDirection = "unknown",
    days_since_last_pt: int | None = None,
    days_until_next_pt: int | None = None,
    next_pt_date: str | None = None,
    pt_cancellation_rate_30d: float | None = None,
    momentum: Momentum = "inactive",
) -> AvatarTrainingPath:
    # Common PT fields
    pt_fields = dict(
        pt_sessions_completed_30d=pt_sessions_completed_30d,
        pt_sessions_scheduled_30d=pt_sessions_scheduled_30d,
        pt_attendance_30d=round(pt_attendance_30d, 2) if pt_attendance_30d is not None else None,
        pt_attendance_60d=round(pt_attendance_60d, 2) if pt_attendance_60d is not None else None,
        pt_attendance_trend=pt_attendance_trend,
        days_since_last_pt=days_since_last_pt,
        days_until_next_pt=days_until_next_pt,
        next_pt_date=next_pt_date,
        pt_cancellation_rate_30d=pt_cancellation_rate_30d,
        momentum=momentum,
    )

    has_active = active_plan is not None
    if not has_active:
        return AvatarTrainingPath(
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            days_since_last_session=days_since_last,
            status="red",
            **pt_fields,
        )

    # Semaphore
    if days_since_last is not None and days_since_last >= 14:
        status: SemaphoreStatus = "red"
    elif compliance_30d is not None and compliance_30d < 0.5:
        status = "amber"
    else:
        status = "green"

    return AvatarTrainingPath(
        has_active_plan=True,
        active_plan_name=active_plan.nome,
        active_plan_objective=active_plan.obiettivo,
        compliance_30d=round(compliance_30d, 2) if compliance_30d is not None else None,
        compliance_60d=round(compliance_60d, 2) if compliance_60d is not None else None,
        compliance_trend=compliance_trend,
        total_sessions=total_sessions,
        completed_sessions=completed_sessions,
        days_since_last_session=days_since_last,
        status=status,
        **pt_fields,
    )


def _build_body_goals(
    *,
    has_measurements: bool,
    last_measurement_date: date | None,
    measurement_freshness_status: str,
    active_goals_count: int,
    bmi: float | None,
    body_fat_pct: float | None,
) -> AvatarBodyGoals:
    if not has_measurements:
        status: SemaphoreStatus = "red"
    elif measurement_freshness_status in ("warning", "critical"):
        status = "amber"
    else:
        status = "green"

    return AvatarBodyGoals(
        has_measurements=has_measurements,
        last_measurement_date=last_measurement_date,
        measurement_freshness=measurement_freshness_status,
        active_goals=active_goals_count,
        bmi=round(bmi, 1) if bmi is not None else None,
        body_fat_pct=round(body_fat_pct, 1) if body_fat_pct is not None else None,
        status=status,
    )


# ---------------------------------------------------------------------------
# Readiness score
# ---------------------------------------------------------------------------

def _compute_readiness_score(
    clinical_state: str,
    has_measurements: bool,
    has_plan: bool,
    has_contract: bool,
    overdue_count: int,
) -> int:
    """
    Readiness score 0-100. Riusa pesi da clinical_readiness:
    anamnesi 40pt, misurazioni 30pt, scheda 20pt, contratto bonus max 10pt.
    """
    score = 0
    if clinical_state == "structured":
        score += 40
    elif clinical_state == "legacy":
        score += 15

    if has_measurements:
        score += 30

    if has_plan:
        score += 20

    # Contract bonus
    if has_contract and overdue_count == 0:
        score += 10

    return min(score, 100)


# ---------------------------------------------------------------------------
# Batch builder (core)
# ---------------------------------------------------------------------------

def build_avatars_batch(
    session: Session,
    trainer_id: int,
    client_ids: list[int],
    catalog_session: Session | None = None,
) -> list[ClientAvatar]:
    """
    Build avatars for a batch of client IDs. Anti-N+1: ~12 queries.
    """
    reference = date.today()
    now_str = datetime.now(timezone.utc).isoformat()

    if not client_ids:
        return []

    # ── Q1: Clients (bouncer: trainer_id + deleted_at) ──
    clients = session.exec(
        select(Client).where(
            Client.id.in_(client_ids),
            Client.trainer_id == trainer_id,
            Client.deleted_at == None,  # noqa: E711
        )
    ).all()
    clients_by_id: dict[int, Client] = {c.id: c for c in clients if c.id is not None}
    valid_ids = list(clients_by_id.keys())
    if not valid_ids:
        return []

    # ── Q2: Clinical conditions (pure, no DB) ──
    conditions_by_client: dict[int, set[int]] = {}
    all_condition_ids: set[int] = set()
    for cid, client in clients_by_id.items():
        conds = extract_client_conditions(client.anamnesi_json)
        conditions_by_client[cid] = conds
        all_condition_ids.update(conds)

    # ── Q3: Condition names from catalog ──
    condition_names_map: dict[int, str] = {}
    if all_condition_ids and catalog_session is not None:
        from api.models.medical_condition import MedicalCondition
        cond_rows = catalog_session.exec(
            select(MedicalCondition.id, MedicalCondition.nome).where(
                MedicalCondition.id.in_(list(all_condition_ids))
            )
        ).all()
        condition_names_map = {row[0]: row[1] for row in cond_rows if row[0] is not None}

    # ── Q4: Active contracts (latest non-closed per client) ──
    contract_rows = session.exec(
        select(Contract).where(
            Contract.trainer_id == trainer_id,
            Contract.id_cliente.in_(valid_ids),
            Contract.chiuso == False,  # noqa: E712
            Contract.deleted_at == None,  # noqa: E711
        ).order_by(Contract.data_scadenza.desc())
    ).all()
    # Keep latest per client
    active_contracts: dict[int, Contract] = {}
    for c in contract_rows:
        if c.id_cliente not in active_contracts:
            active_contracts[c.id_cliente] = c

    # ── Q5: Credits used (events count with categoria=PT) ──
    from api.models.event import Event
    credit_rows = session.exec(
        select(Event.id_contratto, func.count(Event.id)).where(
            Event.trainer_id == trainer_id,
            Event.id_contratto != None,  # noqa: E711
            Event.categoria == "PT",
            Event.stato != "Cancellato",
            Event.deleted_at == None,  # noqa: E711
        ).group_by(Event.id_contratto)
    ).all()
    credits_used_by_contract: dict[int, int] = {
        row[0]: row[1] for row in credit_rows if row[0] is not None
    }

    # ── Q6: Overdue rates count per client ──
    today_str = reference.isoformat()
    overdue_rows = session.exec(
        select(Contract.id_cliente, func.count(Rate.id)).where(
            Rate.id_contratto == Contract.id,
            Contract.trainer_id == trainer_id,
            Contract.id_cliente.in_(valid_ids),
            Contract.deleted_at == None,  # noqa: E711
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.data_scadenza < today_str,
            Rate.deleted_at == None,  # noqa: E711
        ).group_by(Contract.id_cliente)
    ).all()
    overdue_by_client: dict[int, int] = {
        row[0]: row[1] for row in overdue_rows if row[0] is not None
    }

    # ── Q7: Renewal count per client ──
    renewal_rows = session.exec(
        select(Contract.id_cliente, func.count(Contract.id)).where(
            Contract.trainer_id == trainer_id,
            Contract.id_cliente.in_(valid_ids),
            Contract.rinnovo_di != None,  # noqa: E711
            Contract.deleted_at == None,  # noqa: E711
        ).group_by(Contract.id_cliente)
    ).all()
    renewals_by_client: dict[int, int] = {
        row[0]: row[1] for row in renewal_rows if row[0] is not None
    }

    # ── Q8: Workout sessions (total + completed + last date) ──
    log_rows = session.exec(
        select(
            WorkoutLog.id_cliente,
            func.count(WorkoutLog.id),
            func.max(WorkoutLog.data_esecuzione),
        ).where(
            WorkoutLog.trainer_id == trainer_id,
            WorkoutLog.id_cliente.in_(valid_ids),
            WorkoutLog.deleted_at == None,  # noqa: E711
        ).group_by(WorkoutLog.id_cliente)
    ).all()
    sessions_by_client: dict[int, tuple[int, date | None]] = {}
    for row in log_rows:
        cid = row[0]
        if cid is not None:
            sessions_by_client[cid] = (row[1], _parse_date(row[2]))

    # ── Q9: Compliance 30d / 60d ──
    from datetime import timedelta
    d30 = reference - timedelta(days=30)
    d60 = reference - timedelta(days=60)

    compliance_30_rows = session.exec(
        select(WorkoutLog.id_cliente, func.count(WorkoutLog.id)).where(
            WorkoutLog.trainer_id == trainer_id,
            WorkoutLog.id_cliente.in_(valid_ids),
            WorkoutLog.data_esecuzione >= d30.isoformat(),
            WorkoutLog.deleted_at == None,  # noqa: E711
        ).group_by(WorkoutLog.id_cliente)
    ).all()
    logs_30d: dict[int, int] = {
        row[0]: row[1] for row in compliance_30_rows if row[0] is not None
    }

    compliance_60_rows = session.exec(
        select(WorkoutLog.id_cliente, func.count(WorkoutLog.id)).where(
            WorkoutLog.trainer_id == trainer_id,
            WorkoutLog.id_cliente.in_(valid_ids),
            WorkoutLog.data_esecuzione >= d60.isoformat(),
            WorkoutLog.deleted_at == None,  # noqa: E711
        ).group_by(WorkoutLog.id_cliente)
    ).all()
    logs_60d: dict[int, int] = {
        row[0]: row[1] for row in compliance_60_rows if row[0] is not None
    }

    # ── Q10: Active plans (latest non-expired per client) ──
    plan_rows = session.exec(
        select(WorkoutPlan).where(
            WorkoutPlan.trainer_id == trainer_id,
            WorkoutPlan.id_cliente.in_(valid_ids),
            WorkoutPlan.deleted_at == None,  # noqa: E711
        ).order_by(
            WorkoutPlan.id_cliente,
            func.coalesce(WorkoutPlan.updated_at, WorkoutPlan.created_at).desc(),
        )
    ).all()
    active_plans: dict[int, WorkoutPlan] = {}
    for p in plan_rows:
        if p.id_cliente is not None and p.id_cliente not in active_plans:
            # Consider active if data_inizio set (or latest plan)
            active_plans[p.id_cliente] = p

    # ── Q11: Active goals count ──
    goal_rows = session.exec(
        select(ClientGoal.id_cliente, func.count(ClientGoal.id)).where(
            ClientGoal.trainer_id == trainer_id,
            ClientGoal.id_cliente.in_(valid_ids),
            ClientGoal.stato == "attivo",
            ClientGoal.deleted_at == None,  # noqa: E711
        ).group_by(ClientGoal.id_cliente)
    ).all()
    goals_by_client: dict[int, int] = {
        row[0]: row[1] for row in goal_rows if row[0] is not None
    }

    # ── Q12: Latest measurement date + BMI/body fat ──
    measurement_rows = session.exec(
        select(
            ClientMeasurement.id_cliente,
            func.max(ClientMeasurement.data_misurazione),
        ).where(
            ClientMeasurement.trainer_id == trainer_id,
            ClientMeasurement.id_cliente.in_(valid_ids),
            ClientMeasurement.deleted_at == None,  # noqa: E711
        ).group_by(ClientMeasurement.id_cliente)
    ).all()
    measurements_by_client: dict[int, date | None] = {
        row[0]: _parse_date(row[1]) for row in measurement_rows if row[0] is not None
    }

    # ── Q13a: PT events completed in 30d (agenda, categoria=PT, stato=Completato) ──
    pt_completed_30d_rows = session.exec(
        select(Event.id_cliente, func.count(Event.id)).where(
            Event.trainer_id == trainer_id,
            Event.id_cliente.in_(valid_ids),
            Event.categoria == "PT",
            Event.stato == "Completato",
            Event.data_inizio >= d30.isoformat(),
            Event.deleted_at == None,  # noqa: E711
        ).group_by(Event.id_cliente)
    ).all()
    pt_completed_30d: dict[int, int] = {
        row[0]: row[1] for row in pt_completed_30d_rows if row[0] is not None
    }

    # ── Q13b: PT events scheduled in 30d (non-cancelled) ──
    pt_scheduled_30d_rows = session.exec(
        select(Event.id_cliente, func.count(Event.id)).where(
            Event.trainer_id == trainer_id,
            Event.id_cliente.in_(valid_ids),
            Event.categoria == "PT",
            Event.stato != "Cancellato",
            Event.data_inizio >= d30.isoformat(),
            Event.deleted_at == None,  # noqa: E711
        ).group_by(Event.id_cliente)
    ).all()
    pt_scheduled_30d: dict[int, int] = {
        row[0]: row[1] for row in pt_scheduled_30d_rows if row[0] is not None
    }

    # ── Q14a: PT events completed in 60d ──
    pt_completed_60d_rows = session.exec(
        select(Event.id_cliente, func.count(Event.id)).where(
            Event.trainer_id == trainer_id,
            Event.id_cliente.in_(valid_ids),
            Event.categoria == "PT",
            Event.stato == "Completato",
            Event.data_inizio >= d60.isoformat(),
            Event.deleted_at == None,  # noqa: E711
        ).group_by(Event.id_cliente)
    ).all()
    pt_completed_60d: dict[int, int] = {
        row[0]: row[1] for row in pt_completed_60d_rows if row[0] is not None
    }

    # ── Q14b: PT events scheduled in 60d (non-cancelled) ──
    pt_scheduled_60d_rows = session.exec(
        select(Event.id_cliente, func.count(Event.id)).where(
            Event.trainer_id == trainer_id,
            Event.id_cliente.in_(valid_ids),
            Event.categoria == "PT",
            Event.stato != "Cancellato",
            Event.data_inizio >= d60.isoformat(),
            Event.deleted_at == None,  # noqa: E711
        ).group_by(Event.id_cliente)
    ).all()
    pt_scheduled_60d: dict[int, int] = {
        row[0]: row[1] for row in pt_scheduled_60d_rows if row[0] is not None
    }

    # ── Q15: Last completed PT session date ──
    last_pt_rows = session.exec(
        select(Event.id_cliente, func.max(Event.data_inizio)).where(
            Event.trainer_id == trainer_id,
            Event.id_cliente.in_(valid_ids),
            Event.categoria == "PT",
            Event.stato == "Completato",
            Event.deleted_at == None,  # noqa: E711
        ).group_by(Event.id_cliente)
    ).all()
    last_pt_by_client: dict[int, date | None] = {
        row[0]: _parse_date(row[1]) for row in last_pt_rows if row[0] is not None
    }

    # ── Q16: Next scheduled PT session (first future Programmato) ──
    next_pt_rows = session.exec(
        select(Event.id_cliente, func.min(Event.data_inizio)).where(
            Event.trainer_id == trainer_id,
            Event.id_cliente.in_(valid_ids),
            Event.categoria == "PT",
            Event.stato == "Programmato",
            Event.data_inizio >= now_str,
            Event.deleted_at == None,  # noqa: E711
        ).group_by(Event.id_cliente)
    ).all()
    next_pt_by_client: dict[int, date | None] = {
        row[0]: _parse_date(row[1]) for row in next_pt_rows if row[0] is not None
    }

    # ── Q17: PT cancellations in 30d ──
    pt_cancelled_30d_rows = session.exec(
        select(Event.id_cliente, func.count(Event.id)).where(
            Event.trainer_id == trainer_id,
            Event.id_cliente.in_(valid_ids),
            Event.categoria == "PT",
            Event.stato == "Cancellato",
            Event.data_inizio >= d30.isoformat(),
            Event.deleted_at == None,  # noqa: E711
        ).group_by(Event.id_cliente)
    ).all()
    pt_cancelled_30d: dict[int, int] = {
        row[0]: row[1] for row in pt_cancelled_30d_rows if row[0] is not None
    }

    # ── Build avatars ──
    avatars: list[ClientAvatar] = []
    for cid in valid_ids:
        client = clients_by_id[cid]

        # Identity
        identity = _build_identity(client, reference)

        # Clinical
        clinical = _build_clinical(
            client,
            conditions_by_client.get(cid, set()),
            condition_names_map,
        )

        # Contract
        ac = active_contracts.get(cid)
        credits_used = credits_used_by_contract.get(ac.id, 0) if ac and ac.id else 0
        contract = _build_contract(
            active_contract=ac,
            credits_used=credits_used,
            overdue_count=overdue_by_client.get(cid, 0),
            renewal_count=renewals_by_client.get(cid, 0),
            reference=reference,
        )

        # Training
        plan = active_plans.get(cid)
        sess_data = sessions_by_client.get(cid, (0, None))
        total_sess, last_sess_date = sess_data
        days_since_last = (reference - last_sess_date).days if last_sess_date else None

        # Compliance: sessions in period / expected (based on plan's sessioni_per_settimana)
        spw = plan.sessioni_per_settimana if plan else 3
        expected_30 = max(1, 30 / 7 * spw)
        expected_60 = max(1, 60 / 7 * spw)
        c30 = min(1.0, logs_30d.get(cid, 0) / expected_30) if plan else None
        c60 = min(1.0, logs_60d.get(cid, 0) / expected_60) if plan else None

        # Compliance trend: compare 30d vs prior 30d (derived from 60d - 30d)
        if c30 is not None and c60 is not None:
            logs_prior_30 = logs_60d.get(cid, 0) - logs_30d.get(cid, 0)
            c_prior = min(1.0, logs_prior_30 / expected_30) if plan else None
            c_trend = _compute_trend(c30, c_prior)
        else:
            c_trend: TrendDirection = "unknown"

        # PT attendance (agenda events — independent axis)
        pt_comp_30 = pt_completed_30d.get(cid, 0)
        pt_sched_30 = pt_scheduled_30d.get(cid, 0)
        pt_comp_60 = pt_completed_60d.get(cid, 0)
        pt_sched_60 = pt_scheduled_60d.get(cid, 0)

        pt_att_30 = min(1.0, pt_comp_30 / pt_sched_30) if pt_sched_30 > 0 else None
        pt_att_60 = min(1.0, pt_comp_60 / pt_sched_60) if pt_sched_60 > 0 else None

        # PT attendance trend: compare 30d vs prior 30d
        if pt_att_30 is not None and pt_att_60 is not None:
            pt_comp_prior = pt_comp_60 - pt_comp_30
            pt_sched_prior = pt_sched_60 - pt_sched_30
            pt_att_prior = min(1.0, pt_comp_prior / pt_sched_prior) if pt_sched_prior > 0 else None
            pt_att_trend = _compute_trend(pt_att_30, pt_att_prior)
        else:
            pt_att_trend: TrendDirection = "unknown"

        # PT temporal anchors
        last_pt_date = last_pt_by_client.get(cid)
        days_since_last_pt = (reference - last_pt_date).days if last_pt_date else None
        next_pt_dt = next_pt_by_client.get(cid)
        days_until_next_pt = (next_pt_dt - reference).days if next_pt_dt else None
        next_pt_date_str = next_pt_dt.isoformat() if next_pt_dt else None

        # PT cancellation rate
        pt_canc_30 = pt_cancelled_30d.get(cid, 0)
        pt_total_30 = pt_sched_30 + pt_canc_30
        pt_cancel_rate = round(pt_canc_30 / pt_total_30, 2) if pt_total_30 > 0 else None

        has_active_plan = plan is not None and plan.data_inizio is not None
        momentum = _compute_momentum(c_trend, pt_att_trend, has_active_plan, days_since_last)

        training = _build_training(
            active_plan=plan if has_active_plan else None,
            total_sessions=total_sess,
            completed_sessions=logs_30d.get(cid, 0),
            days_since_last=days_since_last,
            compliance_30d=c30,
            compliance_60d=c60,
            compliance_trend=c_trend,
            pt_sessions_completed_30d=pt_comp_30,
            pt_sessions_scheduled_30d=pt_sched_30,
            pt_attendance_30d=pt_att_30,
            pt_attendance_60d=pt_att_60,
            pt_attendance_trend=pt_att_trend,
            days_since_last_pt=days_since_last_pt,
            days_until_next_pt=days_until_next_pt,
            next_pt_date=next_pt_date_str,
            pt_cancellation_rate_30d=pt_cancel_rate,
            momentum=momentum,
        )

        # Body goals
        last_meas = measurements_by_client.get(cid)
        meas_freshness = build_measurement_freshness(
            client_id=cid,
            latest_measurement_date=last_meas,
            reference_date=reference,
        )

        body_goals = _build_body_goals(
            has_measurements=last_meas is not None,
            last_measurement_date=last_meas,
            measurement_freshness_status=meas_freshness.status,
            active_goals_count=goals_by_client.get(cid, 0),
            bmi=None,  # Computed only when measurement values available
            body_fat_pct=None,
        )

        # Readiness score
        readiness = _compute_readiness_score(
            clinical.anamnesi_state,
            body_goals.has_measurements,
            has_active_plan,
            contract.has_active_contract,
            contract.overdue_rates_count,
        )

        # Highlights
        ctx = AvatarContext(
            client_id=cid,
            anamnesi_state=clinical.anamnesi_state,
            has_active_contract=contract.has_active_contract,
            credits_remaining=contract.credits_remaining,
            credits_total=contract.credits_total,
            overdue_rates_count=contract.overdue_rates_count,
            days_to_expiry=contract.days_to_expiry,
            renewal_count=contract.renewal_count,
            has_active_plan=has_active_plan,
            compliance_30d=c30,
            compliance_60d=c60,
            days_since_last_session=days_since_last,
            has_measurements=body_goals.has_measurements,
            measurement_freshness=meas_freshness.status,
            seniority_days=identity.seniority_days,
            pt_attendance_trend=pt_att_trend,
            momentum=momentum,
            days_since_last_pt=days_since_last_pt,
            days_until_next_pt=days_until_next_pt,
            pt_cancellation_rate_30d=pt_cancel_rate,
        )
        highlights = compute_highlights(ctx)

        avatars.append(ClientAvatar(
            client_id=cid,
            generated_at=now_str,
            readiness_score=readiness,
            identity=identity,
            clinical=clinical,
            contract=contract,
            training=training,
            body_goals=body_goals,
            highlights=highlights,
        ))

    return avatars


def build_avatar(
    session: Session,
    trainer_id: int,
    client_id: int,
    catalog_session: Session | None = None,
) -> ClientAvatar | None:
    """Build avatar for a single client. Returns None if not found."""
    result = build_avatars_batch(session, trainer_id, [client_id], catalog_session)
    return result[0] if result else None
