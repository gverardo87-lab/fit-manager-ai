# api/routers/training_methodology.py
"""
Router MyTrainer — qualita' metodologica dei programmi di allenamento.

Parallelo a dashboard.py (clinical-readiness / MyPortal):
- clinical-readiness: il cliente e' clinicamente pronto?
- training-methodology: il programma di allenamento e' scientificamente solido?

Pattern: batch fetch anti-N+1, analyze_plan() per piano, compliance da logs.
"""

import logging
import unicodedata
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, func, select

from api.database import get_catalog_session, get_session
from api.dependencies import get_current_trainer
from api.models.client import Client
from api.models.exercise import Exercise
from api.models.goal import ClientGoal
from api.models.measurement import ClientMeasurement, MeasurementValue, Metric
from api.models.trainer import Trainer
from api.models.workout import WorkoutExercise, WorkoutPlan, WorkoutSession
from api.models.workout_log import WorkoutLog
from api.schemas.projection import (
    ClientProjectionResponse,
    GoalProjectionResponse,
    MetricTrendResponse,
    ProjectionChartResponse,
    ProjectionPointResponse,
    RiskFlagResponse,
    VolumeAccumulationResponse,
)
from api.schemas.training_methodology import (
    SessionComplianceItem,
    TrainingMethodologyPlanItem,
    TrainingMethodologySummary,
    TrainingMethodologyWorklistResponse,
)
from api.services.projection_engine import (
    compute_goal_projection,
    compute_metric_trend,
    compute_risk_flags,
    compute_volume_accumulation,
    generate_projection_points,
)
from api.services.training_science.plan_analyzer import analyze_plan
from api.services.training_science.plan_converter import (
    convert_plan_to_template,
    create_effective_template,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/training-methodology",
    tags=["training-methodology"],
)


# ════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════


def _get_plan_status(plan: WorkoutPlan) -> str:
    """Stato derivato da date (stessa logica di getProgramStatus frontend)."""
    today = date.today()
    if not plan.data_inizio:
        return "da_attivare"
    try:
        d_inizio = (
            date.fromisoformat(plan.data_inizio)
            if isinstance(plan.data_inizio, str)
            else plan.data_inizio
        )
    except (ValueError, TypeError):
        return "da_attivare"

    if plan.data_fine:
        try:
            d_fine = (
                date.fromisoformat(plan.data_fine)
                if isinstance(plan.data_fine, str)
                else plan.data_fine
            )
        except (ValueError, TypeError):
            d_fine = None
    else:
        d_fine = None

    if d_fine and today > d_fine:
        return "completato"
    if today >= d_inizio:
        return "attivo"
    return "da_attivare"


def _compute_compliance(
    plan: WorkoutPlan,
    plan_status: str,
    log_count: int,
) -> tuple[int, int, int]:
    """
    Calcola compliance (expected, completed, pct).

    Per piani attivi: settimane trascorse × sessioni_per_settimana.
    Per piani completati: durata_settimane × sessioni_per_settimana.
    Per piani da_attivare: 0/0/0.
    """
    if plan_status == "da_attivare" or not plan.data_inizio:
        return 0, log_count, 0

    today = date.today()
    try:
        d_inizio = (
            date.fromisoformat(plan.data_inizio)
            if isinstance(plan.data_inizio, str)
            else plan.data_inizio
        )
    except (ValueError, TypeError):
        return 0, log_count, 0

    if plan_status == "completato":
        weeks = plan.durata_settimane or 4
    else:
        days = (today - d_inizio).days
        weeks = max(1, (days // 7) + 1)

    expected = weeks * (plan.sessioni_per_settimana or 3)
    completed = log_count
    pct = min(100, round((completed / expected) * 100)) if expected > 0 else 0

    return expected, completed, pct


def _compute_priority(
    science_score: float,
    compliance_pct: int,
    plan_status: str,
    analyzable: bool,
    session_imbalance: bool = False,
) -> tuple[str, int]:
    """
    Calcola priorita' e priority_score deterministico.

    high: problemi gravi (score basso + compliance bassa)
    medium: un indicatore problematico
    low: tutto ok o non analizzabile
    """
    if not analyzable:
        return "low", 0

    if plan_status == "da_attivare":
        return "medium", 40

    score = 0

    if science_score < 40:
        score += 60
    elif science_score < 60:
        score += 30

    if compliance_pct < 50 and plan_status == "attivo":
        score += 40
    elif compliance_pct < 70 and plan_status == "attivo":
        score += 15

    # Sessioni saltate sistematicamente → segnale di squilibrio esecutivo
    if session_imbalance and plan_status == "attivo":
        score += 20

    if score >= 70:
        return "high", score
    if score >= 30:
        return "medium", score
    return "low", score


def _compute_cta(
    item: TrainingMethodologyPlanItem,
) -> tuple[str, str, str]:
    """Determina next action code, label, href."""
    if item.status == "da_attivare":
        return (
            "activate",
            "Attiva programma",
            f"/allenamenti?idCliente={item.client_id}",
        )

    if not item.analyzable:
        return (
            "add_exercises",
            "Aggiungi esercizi",
            f"/schede/{item.plan_id}?from=monitoraggio",
        )

    if item.sotto_mev_count >= 3:
        return (
            "fix_volume",
            "Correggi volume",
            f"/schede/{item.plan_id}?from=monitoraggio",
        )

    if item.squilibri_count >= 2:
        return (
            "fix_balance",
            "Correggi equilibrio",
            f"/schede/{item.plan_id}?from=monitoraggio",
        )

    if item.session_imbalance and item.status == "attivo":
        return (
            "fix_imbalance",
            "Sessioni sbilanciate",
            f"/allenamenti?idCliente={item.client_id}",
        )

    if item.compliance_pct < 50 and item.status == "attivo":
        return (
            "improve_compliance",
            "Migliora aderenza",
            f"/allenamenti?idCliente={item.client_id}",
        )

    if item.training_score >= 80:
        return (
            "excellent",
            "Eccellente",
            f"/schede/{item.plan_id}?from=monitoraggio",
        )

    return (
        "review",
        "Rivedi piano",
        f"/schede/{item.plan_id}?from=monitoraggio",
    )


def _normalize_search(text: str) -> str:
    """Normalizza per ricerca accent-insensitive."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ════════════════════════════════════════════════════════════
# Core computation
# ════════════════════════════════════════════════════════════


def _compute_training_methodology_data(
    trainer_id: int,
    session: Session,
) -> tuple[TrainingMethodologySummary, list[TrainingMethodologyPlanItem]]:
    """
    Calcola dati MyTrainer per tutti i piani con cliente assegnato.

    Pattern anti-N+1: 6 batch query + N pure computations.
    """
    # 1. Piani con cliente assegnato (non eliminati)
    plans = session.exec(
        select(WorkoutPlan).where(
            WorkoutPlan.trainer_id == trainer_id,
            WorkoutPlan.id_cliente.isnot(None),  # type: ignore[union-attr]
            WorkoutPlan.deleted_at.is_(None),  # type: ignore[union-attr]
        )
    ).all()

    if not plans:
        return TrainingMethodologySummary(), []

    plan_ids = [p.id for p in plans]
    client_ids = list({p.id_cliente for p in plans if p.id_cliente})

    # 2. Clienti (batch)
    clients = session.exec(
        select(Client).where(Client.id.in_(client_ids))
    ).all()
    client_map: dict[int, Client] = {c.id: c for c in clients}

    # 3. Sessioni (batch)
    all_sessions = session.exec(
        select(WorkoutSession)
        .where(WorkoutSession.id_scheda.in_(plan_ids))
        .order_by(WorkoutSession.numero_sessione)
    ).all()
    sessions_by_plan: dict[int, list[WorkoutSession]] = {}
    session_ids: list[int] = []
    for s in all_sessions:
        sessions_by_plan.setdefault(s.id_scheda, []).append(s)
        session_ids.append(s.id)

    # 4. Esercizi (batch)
    all_exercises: list[WorkoutExercise] = []
    if session_ids:
        all_exercises = list(
            session.exec(
                select(WorkoutExercise)
                .where(WorkoutExercise.id_sessione.in_(session_ids))
                .order_by(WorkoutExercise.ordine)
            ).all()
        )
    exercises_by_session: dict[int, list[WorkoutExercise]] = {}
    exercise_ref_ids: set[int] = set()
    for e in all_exercises:
        exercises_by_session.setdefault(e.id_sessione, []).append(e)
        exercise_ref_ids.add(e.id_esercizio)

    # 5. Catalogo esercizi (batch — per pattern_movimento)
    exercise_catalog: dict[int, Exercise] = {}
    if exercise_ref_ids:
        refs = session.exec(
            select(Exercise).where(Exercise.id.in_(list(exercise_ref_ids)))
        ).all()
        exercise_catalog = {r.id: r for r in refs}

    # 6. Log allenamenti raggruppati per (piano, sessione) (batch)
    # Struttura: {plan_id: {session_id: count}}
    log_by_plan_session: dict[int, dict[int, int]] = {}
    log_counts: dict[int, int] = {}
    if plan_ids:
        log_rows = session.exec(
            select(
                WorkoutLog.id_scheda,
                WorkoutLog.id_sessione,
                func.count(WorkoutLog.id),
            )
            .where(
                WorkoutLog.id_scheda.in_(plan_ids),
                WorkoutLog.deleted_at.is_(None),  # type: ignore[union-attr]
            )
            .group_by(WorkoutLog.id_scheda, WorkoutLog.id_sessione)
        ).all()
        for row in log_rows:
            pid, sid, cnt = row[0], row[1], row[2]
            log_by_plan_session.setdefault(pid, {})[sid] = cnt
            log_counts[pid] = log_counts.get(pid, 0) + cnt

    # ── Build items ──
    items: list[TrainingMethodologyPlanItem] = []

    for plan in plans:
        client = client_map.get(plan.id_cliente) if plan.id_cliente else None
        if not client:
            continue

        plan_status = _get_plan_status(plan)
        plan_sessions = sessions_by_plan.get(plan.id, [])

        # Raccogli esercizi per sessione di QUESTO piano
        plan_ex_by_session: dict[int, list[WorkoutExercise]] = {}
        for s in plan_sessions:
            plan_ex_by_session[s.id] = exercises_by_session.get(s.id, [])

        # Converti e analizza
        template = convert_plan_to_template(
            plan=plan,
            sessions=plan_sessions,
            exercises_by_session=plan_ex_by_session,
            exercise_catalog=exercise_catalog,
            client_sesso=client.sesso,
            client_data_nascita=(
                date.fromisoformat(client.data_nascita)
                if isinstance(client.data_nascita, str) and client.data_nascita
                else client.data_nascita if isinstance(client.data_nascita, date) else None
            ),
        )

        analyzable = template is not None
        science_score = 0.0
        sotto_mev = 0
        sopra_mrv = 0
        ottimali = 0
        squilibri = 0
        warnings = 0
        volume_tot = 0.0

        if template:
            try:
                analysis = analyze_plan(template)
                science_score = analysis.score
                sotto_mev = len(analysis.volume.muscoli_sotto_mev)
                sopra_mrv = len(analysis.volume.muscoli_sopra_mrv)
                ottimali = sum(
                    1
                    for v in analysis.volume.per_muscolo
                    if v.stato == "ottimale"
                )
                squilibri = len(analysis.balance.squilibri)
                warnings = len(analysis.warnings)
                volume_tot = analysis.volume.volume_totale_settimana
            except Exception:
                logger.warning(
                    "analyze_plan failed for plan %s", plan.id, exc_info=True
                )
                analyzable = False

        # Compliance aggregata
        lc = log_counts.get(plan.id, 0)
        expected, completed, compliance_pct = _compute_compliance(
            plan, plan_status, lc
        )

        # Compliance per sessione
        session_logs = log_by_plan_session.get(plan.id, {})
        sess_compliance_items: list[SessionComplianceItem] = []
        if plan_sessions and plan_status != "da_attivare":
            # expected_per_session: quante volte OGNI sessione avrebbe dovuto
            # essere eseguita (settimane trascorse o totali)
            weeks = expected // max(1, len(plan_sessions)) if expected > 0 else 0
            for ps in plan_sessions:
                sc = session_logs.get(ps.id, 0)
                sp = min(100, round((sc / weeks) * 100)) if weeks > 0 else 0
                sess_compliance_items.append(
                    SessionComplianceItem(
                        session_id=ps.id,
                        session_name=ps.nome_sessione,
                        expected=weeks,
                        completed=sc,
                        compliance_pct=sp,
                    )
                )

        # Sessione piu' saltata + imbalance
        worst_session_name = None
        session_imbalance = False
        if len(sess_compliance_items) >= 2:
            by_pct = sorted(sess_compliance_items, key=lambda s: s.compliance_pct)
            worst = by_pct[0]
            best = by_pct[-1]
            if worst.compliance_pct < best.compliance_pct:
                worst_session_name = worst.session_name
            # Gap > 30 punti percentuali = squilibrio aderenza tra sessioni
            if best.compliance_pct - worst.compliance_pct > 30:
                session_imbalance = True

        # ── Analisi effettiva (pesata per compliance sessione) ──
        effective_score_val: float | None = None
        effective_sotto_mev = 0
        effective_squilibri = 0
        score_delta: float | None = None

        if (
            template
            and analyzable
            and plan_status == "attivo"
            and sess_compliance_items
        ):
            # Costruisci pesi: {nome_sessione: compliance_ratio 0.0-1.0}
            session_weights = {
                sc.session_name: sc.compliance_pct / 100.0
                for sc in sess_compliance_items
            }
            eff_template = create_effective_template(template, session_weights)
            if eff_template:
                try:
                    eff_analysis = analyze_plan(eff_template)
                    effective_score_val = round(eff_analysis.score, 1)
                    effective_sotto_mev = len(
                        eff_analysis.volume.muscoli_sotto_mev
                    )
                    effective_squilibri = len(eff_analysis.balance.squilibri)
                    score_delta = round(science_score - eff_analysis.score, 1)
                except Exception:
                    logger.warning(
                        "effective analyze_plan failed for plan %s",
                        plan.id,
                        exc_info=True,
                    )

        # Training score combinato
        training_score = round(science_score * 0.6 + compliance_pct * 0.4)

        # Priorita'
        priority, priority_score = _compute_priority(
            science_score, compliance_pct, plan_status, analyzable,
            session_imbalance=session_imbalance,
        )

        item = TrainingMethodologyPlanItem(
            plan_id=plan.id,
            plan_nome=plan.nome,
            client_id=client.id,
            client_nome=client.nome,
            client_cognome=client.cognome,
            obiettivo=plan.obiettivo,
            livello=plan.livello,
            status=plan_status,
            sessioni_count=len(plan_sessions),
            data_inizio=str(plan.data_inizio) if plan.data_inizio else None,
            data_fine=str(plan.data_fine) if plan.data_fine else None,
            science_score=round(science_score, 1),
            sotto_mev_count=sotto_mev,
            sopra_mrv_count=sopra_mrv,
            ottimali_count=ottimali,
            squilibri_count=squilibri,
            warning_count=warnings,
            volume_totale=round(volume_tot, 1),
            compliance_pct=compliance_pct,
            sessions_expected=expected,
            sessions_completed=completed,
            training_score=training_score,
            priority=priority,
            priority_score=priority_score,
            analyzable=analyzable,
            session_compliance=sess_compliance_items,
            worst_session_name=worst_session_name,
            session_imbalance=session_imbalance,
            effective_score=effective_score_val,
            effective_sotto_mev=effective_sotto_mev,
            effective_squilibri=effective_squilibri,
            score_delta=score_delta,
        )

        # CTA
        code, label, href = _compute_cta(item)
        item.next_action_code = code
        item.next_action_label = label
        item.next_action_href = href

        items.append(item)

    # ── Summary ──
    active_items = [i for i in items if i.status == "attivo"]
    analyzable_items = [i for i in items if i.analyzable]

    summary = TrainingMethodologySummary(
        total_plans=len(items),
        active_plans=len(active_items),
        avg_science_score=(
            round(sum(i.science_score for i in analyzable_items) / len(analyzable_items), 1)
            if analyzable_items
            else 0.0
        ),
        avg_compliance=(
            round(sum(i.compliance_pct for i in active_items) / len(active_items), 1)
            if active_items
            else 0.0
        ),
        avg_training_score=(
            round(sum(i.training_score for i in analyzable_items) / len(analyzable_items), 1)
            if analyzable_items
            else 0.0
        ),
        avg_effective_score=(
            round(
                sum(i.effective_score for i in active_items if i.effective_score is not None)
                / max(1, sum(1 for i in active_items if i.effective_score is not None)),
                1,
            )
            if any(i.effective_score is not None for i in active_items)
            else 0.0
        ),
        plans_with_issues=sum(1 for i in analyzable_items if i.science_score < 60),
        plans_excellent=sum(1 for i in items if i.training_score >= 80),
        high_priority=sum(1 for i in items if i.priority == "high"),
        medium_priority=sum(1 for i in items if i.priority == "medium"),
        low_priority=sum(1 for i in items if i.priority == "low"),
    )

    return summary, items


def _filter_items(
    items: list[TrainingMethodologyPlanItem],
    view: str,
    status_filter: str | None,
    search: str | None,
) -> list[TrainingMethodologyPlanItem]:
    """Applica filtri server-side."""
    filtered = items

    # View filter
    if view == "issues":
        filtered = [i for i in filtered if i.analyzable and i.science_score < 60]
    elif view == "excellent":
        filtered = [i for i in filtered if i.training_score >= 80]

    # Status filter
    if status_filter:
        filtered = [i for i in filtered if i.status == status_filter]

    # Search (accent-insensitive su nome piano + nome cliente)
    if search:
        needle = _normalize_search(search)
        filtered = [
            i
            for i in filtered
            if needle in _normalize_search(f"{i.client_cognome} {i.client_nome} {i.plan_nome}")
        ]

    return filtered


def _sort_items(
    items: list[TrainingMethodologyPlanItem],
    sort_by: str,
) -> list[TrainingMethodologyPlanItem]:
    """Ordinamento deterministico."""
    if sort_by == "science_score":
        return sorted(items, key=lambda i: (i.science_score, -i.priority_score))
    if sort_by == "compliance":
        return sorted(items, key=lambda i: (i.compliance_pct, -i.priority_score))
    # Default: priority (high first)
    return sorted(
        items,
        key=lambda i: (-i.priority_score, i.science_score, i.client_cognome),
    )


# ════════════════════════════════════════════════════════════
# Endpoint
# ════════════════════════════════════════════════════════════


@router.get("/worklist", response_model=TrainingMethodologyWorklistResponse)
def get_training_methodology_worklist(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    view: str = Query(default="all", pattern="^(all|issues|excellent)$"),
    sort_by: str = Query(
        default="priority",
        pattern="^(priority|science_score|compliance)$",
    ),
    status: str | None = Query(
        default=None,
        alias="plan_status",
        pattern="^(attivo|da_attivare|completato)$",
    ),
    search: str | None = Query(default=None, max_length=120),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Worklist paginata qualita' metodologica per MyTrainer.

    Per ogni piano con cliente assegnato:
    - Converte in TemplatePiano e lancia analyze_plan() (pura computazione)
    - Calcola compliance da workout_logs
    - Combina in training_score (science 60% + compliance 40%)
    """
    summary, items = _compute_training_methodology_data(
        trainer_id=trainer.id,
        session=session,
    )

    filtered = _filter_items(items, view=view, status_filter=status, search=search)
    sorted_items = _sort_items(filtered, sort_by=sort_by)
    total = len(filtered)
    offset = (page - 1) * page_size
    paged = sorted_items[offset: offset + page_size]

    return TrainingMethodologyWorklistResponse(
        summary=summary,
        items=paged,
        total=total,
        page=page,
        page_size=page_size,
    )


# ════════════════════════════════════════════════════════════
# Projection endpoint
# ════════════════════════════════════════════════════════════


@router.get(
    "/projection/{client_id}",
    response_model=ClientProjectionResponse,
)
def get_client_projection(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    catalog: Session = Depends(get_catalog_session),
):
    """
    Proiezione 3-layer per un cliente.

    Layer 1: Accumulo stimolo (volume × compliance × tempo) — se piano attivo
    Layer 2: Trend metriche (OLS regression) — se misurazioni
    Layer 3: Proiezione goal (ETA + fear of loss) — se goal + trend
    """
    # ── Bouncer ──
    client = session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.trainer_id == trainer.id,
        )
    ).first()
    if not client:
        raise HTTPException(404, "Cliente non trovato")

    today = date.today()

    # ── 1. Piano attivo + compliance ──
    active_plan = session.exec(
        select(WorkoutPlan).where(
            WorkoutPlan.id_cliente == client_id,
            WorkoutPlan.trainer_id == trainer.id,
            WorkoutPlan.deleted_at.is_(None),  # type: ignore[union-attr]
        )
    ).all()

    # Trova piano attivo (da date)
    plan: WorkoutPlan | None = None
    for p in active_plan:
        if _get_plan_status(p) == "attivo":
            plan = p
            break

    plan_name: str | None = None
    compliance_pct = 0
    volume_resp: VolumeAccumulationResponse | None = None
    weeks_active = 0

    if plan:
        plan_name = plan.nome
        plan_status = "attivo"

        # Compliance
        log_count_row = session.exec(
            select(func.count(WorkoutLog.id)).where(
                WorkoutLog.id_scheda == plan.id,
                WorkoutLog.deleted_at.is_(None),  # type: ignore[union-attr]
            )
        ).one()
        log_count = log_count_row or 0

        expected, completed, compliance_pct = _compute_compliance(
            plan, plan_status, log_count
        )

        # Weeks active
        try:
            d_inizio = (
                date.fromisoformat(plan.data_inizio)
                if isinstance(plan.data_inizio, str)
                else plan.data_inizio
            )
        except (ValueError, TypeError):
            d_inizio = today
        weeks_active = max(1, ((today - d_inizio).days // 7) + 1)

        # Layer 1: Volume accumulation
        plan_sessions = session.exec(
            select(WorkoutSession).where(
                WorkoutSession.id_scheda == plan.id,
            )
        ).all()

        session_ids = [s.id for s in plan_sessions]
        plan_exercises: list[WorkoutExercise] = []
        if session_ids:
            plan_exercises = list(session.exec(
                select(WorkoutExercise).where(
                    WorkoutExercise.id_sessione.in_(session_ids),
                )
            ).all())

        ex_by_session: dict[int, list[WorkoutExercise]] = {}
        ref_ids: set[int] = set()
        for e in plan_exercises:
            ex_by_session.setdefault(e.id_sessione, []).append(e)
            ref_ids.add(e.id_esercizio)

        exercise_catalog: dict[int, Exercise] = {}
        if ref_ids:
            refs = session.exec(
                select(Exercise).where(Exercise.id.in_(list(ref_ids)))
            ).all()
            exercise_catalog = {r.id: r for r in refs}

        template = convert_plan_to_template(
            plan=plan,
            sessions=list(plan_sessions),
            exercises_by_session={
                s.id: ex_by_session.get(s.id, []) for s in plan_sessions
            },
            exercise_catalog=exercise_catalog,
            client_sesso=client.sesso,
            client_data_nascita=(
                date.fromisoformat(client.data_nascita)
                if isinstance(client.data_nascita, str) and client.data_nascita
                else client.data_nascita
                if isinstance(client.data_nascita, date)
                else None
            ),
        )

        weekly_volume = 0.0
        if template:
            try:
                analysis = analyze_plan(template)
                weekly_volume = analysis.volume.volume_totale_settimana
            except Exception:
                logger.warning(
                    "analyze_plan failed for projection plan %s", plan.id,
                    exc_info=True,
                )

        if weekly_volume > 0:
            vol = compute_volume_accumulation(
                weekly_volume, compliance_pct, weeks_active,
            )
            volume_resp = VolumeAccumulationResponse(
                weekly_volume_planned=vol.weekly_volume_planned,
                weekly_volume_effective=vol.weekly_volume_effective,
                weeks_active=vol.weeks_active,
                total_volume_planned=vol.total_volume_planned,
                total_volume_effective=vol.total_volume_effective,
                total_volume_missed=vol.total_volume_missed,
            )

    # ── 2. Misurazioni — fetch da business DB + metrica da catalog ──
    measurements = session.exec(
        select(ClientMeasurement).where(
            ClientMeasurement.id_cliente == client_id,
            ClientMeasurement.trainer_id == trainer.id,
            ClientMeasurement.deleted_at.is_(None),  # type: ignore[union-attr]
        )
    ).all()

    has_measurements = len(measurements) > 0
    measurement_ids = [m.id for m in measurements]

    # Raggruppa valori per metrica: {metric_id: [(date, value), ...]}
    metric_values: dict[int, list[tuple[date, float]]] = {}
    if measurement_ids:
        values = session.exec(
            select(MeasurementValue).where(
                MeasurementValue.id_misurazione.in_(measurement_ids),
            )
        ).all()

        # Build measurement date map
        meas_date_map: dict[int, date] = {}
        for m in measurements:
            d = m.data_misurazione
            if isinstance(d, str):
                try:
                    d = date.fromisoformat(d)
                except (ValueError, TypeError):
                    continue
            meas_date_map[m.id] = d

        for v in values:
            d = meas_date_map.get(v.id_misurazione)
            if d is not None:
                metric_values.setdefault(v.id_metrica, []).append((d, v.valore))

    # Fetch metric catalog info
    metric_ids_needed = list(metric_values.keys())
    metric_catalog: dict[int, Metric] = {}
    if metric_ids_needed:
        metrics = catalog.exec(
            select(Metric).where(Metric.id.in_(metric_ids_needed))
        ).all()
        metric_catalog = {m.id: m for m in metrics}

    # Layer 2: Compute trends
    trends_internal: dict[int, object] = {}  # metric_id -> MetricTrend
    trends_resp: list[MetricTrendResponse] = []

    for mid, vals in metric_values.items():
        if len(vals) < 2:
            continue
        trend = compute_metric_trend(vals)
        if trend is None:
            continue

        met = metric_catalog.get(mid)
        if not met:
            continue

        trends_internal[mid] = trend
        trends_resp.append(MetricTrendResponse(
            metric_id=mid,
            metric_name=met.nome,
            unit=met.unita_misura,
            weekly_rate=trend.weekly_rate,
            r_squared=trend.r_squared,
            n_points=trend.n_points,
            span_days=trend.span_days,
            current_value=trend.current_value,
            current_date=str(trend.current_date),
            confidence=trend.confidence,
        ))

    # ── 3. Goals — fetch attivi per questo cliente ──
    goals = session.exec(
        select(ClientGoal).where(
            ClientGoal.id_cliente == client_id,
            ClientGoal.trainer_id == trainer.id,
            ClientGoal.stato == "attivo",
            ClientGoal.deleted_at.is_(None),  # type: ignore[union-attr]
        )
    ).all()

    has_goals = len(goals) > 0

    # Layer 3: Proiezioni goal
    projections_resp: list[GoalProjectionResponse] = []
    charts_resp: list[ProjectionChartResponse] = []

    for goal in goals:
        met = metric_catalog.get(goal.id_metrica)
        if not met:
            # Fetch from catalog if not yet loaded
            m = catalog.exec(
                select(Metric).where(Metric.id == goal.id_metrica)
            ).first()
            if m:
                metric_catalog[m.id] = m
                met = m

        met_name = met.nome if met else f"Metrica {goal.id_metrica}"
        met_unit = met.unita_misura if met else ""

        trend = trends_internal.get(goal.id_metrica)
        if not trend:
            projections_resp.append(GoalProjectionResponse(
                goal_id=goal.id,
                metric_name=met_name,
                unit=met_unit,
                status="insufficient_data",
                message="Servono almeno 2 misurazioni per proiettare",
            ))
            continue

        deadline = None
        if goal.data_scadenza:
            try:
                deadline = (
                    date.fromisoformat(goal.data_scadenza)
                    if isinstance(goal.data_scadenza, str)
                    else goal.data_scadenza
                )
            except (ValueError, TypeError):
                pass

        proj = compute_goal_projection(
            trend=trend,
            target=goal.valore_target or 0,
            direction=goal.direzione,
            compliance_pct=compliance_pct or 50,
            goal_deadline=deadline,
        )

        if proj is None:
            continue

        projections_resp.append(GoalProjectionResponse(
            goal_id=goal.id,
            metric_name=met_name,
            unit=met_unit,
            status=proj.status,
            message=proj.message,
            weekly_rate=proj.weekly_rate,
            current_value=proj.current_value,
            target_value=proj.target_value,
            eta=str(proj.eta) if proj.eta else None,
            eta_perfect=str(proj.eta_perfect) if proj.eta_perfect else None,
            days_saved=proj.days_saved,
            days_per_missed_session=proj.days_per_missed_session,
            r_squared=proj.r_squared,
            confidence=proj.confidence,
            on_track=proj.on_track,
            goal_deadline=str(proj.goal_deadline) if proj.goal_deadline else None,
        ))

        # Chart data for goals with projections
        if proj.status == "projected" and trend and goal.valore_target:
            chart_points = generate_projection_points(
                trend=trend,
                target=goal.valore_target,
                eta=proj.eta,
            )

            # Historical points
            hist_vals = metric_values.get(goal.id_metrica, [])
            historical = [
                ProjectionPointResponse(
                    date=str(d), value=round(v, 2), is_projection=False,
                )
                for d, v in sorted(hist_vals, key=lambda x: x[0])
            ]

            projected = [
                ProjectionPointResponse(
                    date=str(p.date), value=p.value, is_projection=True,
                )
                for p in chart_points
                if p.is_projection
            ]

            charts_resp.append(ProjectionChartResponse(
                metric_id=goal.id_metrica,
                metric_name=met_name,
                unit=met_unit,
                historical=historical,
                projected=projected,
                target_value=goal.valore_target,
                eta=str(proj.eta) if proj.eta else None,
            ))

    # ── Risk flags ──
    goal_dicts = [
        {
            "id_metrica": g.id_metrica,
            "direzione": g.direzione,
            "valore_target": g.valore_target,
        }
        for g in goals
    ]
    risk_flags_internal = compute_risk_flags(trends_internal, goal_dicts)
    risk_flags_resp = [
        RiskFlagResponse(
            severity=f.severity,
            code=f.code,
            message=f.message,
            metric_id=f.metric_id,
        )
        for f in risk_flags_internal
    ]

    return ClientProjectionResponse(
        client_id=client.id,
        client_nome=client.nome,
        client_cognome=client.cognome,
        volume=volume_resp,
        trends=trends_resp,
        projections=projections_resp,
        charts=charts_resp,
        risk_flags=risk_flags_resp,
        compliance_pct=compliance_pct,
        plan_name=plan_name,
        has_active_plan=plan is not None,
        has_measurements=has_measurements,
        has_goals=has_goals,
    )
