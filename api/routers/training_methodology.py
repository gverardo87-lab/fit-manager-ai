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

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.client import Client
from api.models.exercise import Exercise
from api.models.trainer import Trainer
from api.models.workout import WorkoutExercise, WorkoutPlan, WorkoutSession
from api.models.workout_log import WorkoutLog
from api.schemas.training_methodology import (
    SessionComplianceItem,
    TrainingMethodologyPlanItem,
    TrainingMethodologySummary,
    TrainingMethodologyWorklistResponse,
)
from api.services.training_science.plan_analyzer import analyze_plan
from api.services.training_science.plan_converter import convert_plan_to_template

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
            f"/schede/{item.plan_id}",
        )

    if item.sotto_mev_count >= 3:
        return (
            "fix_volume",
            "Correggi volume",
            f"/schede/{item.plan_id}",
        )

    if item.squilibri_count >= 2:
        return (
            "fix_balance",
            "Correggi equilibrio",
            f"/schede/{item.plan_id}",
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
            f"/schede/{item.plan_id}",
        )

    return (
        "review",
        "Rivedi piano",
        f"/schede/{item.plan_id}",
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
