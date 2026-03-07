"""Orchestratore runtime per il primo `plan-package` SMART backend-first."""

from api.models.trainer import Trainer
from api.schemas.training_science import (
    TSCanonicalPlan,
    TSCanonicalSession,
    TSCanonicalSlot,
    TSConstraintEvaluationReport,
    TSFeasibilitySummary,
    TSPlanPackage,
    TSPlanPackageEngineInfo,
    TSPlanPackageProtocolInfo,
    TSPlanPackageRequest,
    TSSlotBinding,
    TSWorkoutProjection,
)
from api.schemas.workout import WorkoutExerciseInput, WorkoutPlanCreate, WorkoutSessionInput
from api.services.training_science.constraints import evaluate_protocol_constraints
from api.services.training_science.registry import select_protocol
from api.services.training_science import TemplatePiano, analyze_plan, build_plan
from sqlmodel import Session

from .exercise_catalog import load_rankable_exercises
from .exercise_ranker import RankerSelectionState, rank_slot_candidates
from .feasibility_engine import compute_feasibility
from .profile_resolver import resolve_plan_context


def _build_canonical_plan(template_plan: TemplatePiano) -> TSCanonicalPlan:
    sessions: list[TSCanonicalSession] = []
    for session_index, session in enumerate(template_plan.sessioni, start=1):
        session_id = f"s{session_index}"
        slots = [
            TSCanonicalSlot(
                slot_id=f"{session_id}_sl{slot_index}",
                pattern=slot.pattern,
                priorita=slot.priorita,
                serie=slot.serie,
                rep_min=slot.rep_min,
                rep_max=slot.rep_max,
                riposo_sec=slot.riposo_sec,
                muscolo_target=slot.muscolo_target,
                note=slot.note,
            )
            for slot_index, slot in enumerate(session.slots, start=1)
        ]
        sessions.append(
            TSCanonicalSession(
                session_id=session_id,
                nome=session.nome,
                ruolo=session.ruolo,
                focus=session.focus,
                slots=slots,
            )
        )

    plan_id = f"plan_f{template_plan.frequenza}_{template_plan.obiettivo.value}_{template_plan.livello.value}"
    return TSCanonicalPlan(
        plan_id=plan_id,
        frequenza=template_plan.frequenza,
        obiettivo=template_plan.obiettivo,
        livello=template_plan.livello,
        tipo_split=template_plan.tipo_split,
        sessioni=sessions,
        note_generazione=template_plan.note_generazione,
    )


def _format_ripetizioni(slot: TSCanonicalSlot) -> str:
    if slot.rep_min == slot.rep_max:
        return str(slot.rep_min)
    return f"{slot.rep_min}-{slot.rep_max}"


def _build_workout_name(request: TSPlanPackageRequest, client_name: str | None) -> str:
    mode_labels = {
        "general": "Smart",
        "performance": "Smart Performance",
        "clinical": "Smart Clinical",
    }
    base_name = mode_labels[request.preset.mode]
    if not client_name:
        return f"Scheda {base_name}"
    return f"Scheda {base_name} - {client_name}"


def build_plan_package(
    *,
    session: Session,
    catalog_session: Session,
    trainer: Trainer,
    request: TSPlanPackageRequest,
) -> TSPlanPackage:
    """Costruisce canonico, ranking e workout projection save-compatible."""
    context = resolve_plan_context(
        session=session,
        catalog_session=catalog_session,
        trainer=trainer,
        request=request,
    )
    protocol_selection = select_protocol(
        profile=context.scientific_profile,
        frequenza=request.preset.frequenza,
    )
    template_plan = build_plan(
        request.preset.frequenza,
        context.scientific_profile.obiettivo_scientifico,
        context.scientific_profile.livello_scientifico,
    )
    canonical_plan = _build_canonical_plan(template_plan)
    constraint_evaluation: TSConstraintEvaluationReport = evaluate_protocol_constraints(
        protocol_selection=protocol_selection,
        canonical_plan=canonical_plan,
        analyzer=analyze_plan(template_plan),
        requested_frequenza=request.preset.frequenza,
    )
    exercises = load_rankable_exercises(session, trainer.id)
    exercise_lookup = {exercise.id: exercise for exercise in exercises}

    safety_entries = context.safety_map.entries if context.safety_map is not None else {}
    feasibility = compute_feasibility(
        exercises=exercises,
        profile=context.scientific_profile,
        safety_entries=safety_entries,
    )
    excluded_ids = set(request.trainer_overrides.excluded_exercise_ids)
    preferred_ids = set(request.trainer_overrides.preferred_exercise_ids)
    selection_state = RankerSelectionState()

    rankings: dict[str, list] = {}
    slot_bindings: list[TSSlotBinding] = []
    workout_sessions: list[WorkoutSessionInput] = []

    for session_item in canonical_plan.sessioni:
        selection_state.start_session()
        workout_exercises: list[WorkoutExerciseInput] = []
        for exercise_order, slot in enumerate(session_item.slots, start=1):
            ranked = rank_slot_candidates(
                slot=slot,
                profile=context.scientific_profile,
                exercises=exercises,
                safety_entries=safety_entries,
                excluded_exercise_ids=excluded_ids,
                preferred_exercise_ids=preferred_ids,
                pinned_exercise_id=request.trainer_overrides.pinned_exercise_ids_by_slot.get(slot.slot_id),
                feasibility=feasibility,
                selection_state=selection_state,
            )
            rankings[slot.slot_id] = ranked
            if not ranked:
                continue

            selected = ranked[0]
            selected_exercise = exercise_lookup.get(selected.exercise_id)
            workout_exercises.append(
                WorkoutExerciseInput(
                    id_esercizio=selected.exercise_id,
                    ordine=exercise_order,
                    serie=slot.serie,
                    ripetizioni=_format_ripetizioni(slot),
                    tempo_riposo_sec=slot.riposo_sec,
                )
            )
            slot_bindings.append(
                TSSlotBinding(
                    session_id=session_item.session_id,
                    slot_id=slot.slot_id,
                    exercise_id=selected.exercise_id,
                    candidate_rank=selected.rank,
                )
            )
            if selected_exercise is not None:
                selection_state.register_selected_exercise(selected_exercise)

        workout_sessions.append(
            WorkoutSessionInput(
                nome_sessione=session_item.nome,
                focus_muscolare=session_item.focus,
                durata_minuti=request.preset.durata_target_min or 60,
                esercizi=workout_exercises,
                blocchi=[],
            )
        )
        selection_state.finish_session()

    client_name = None
    if context.client is not None:
        client_name = f"{context.client.nome} {context.client.cognome}".strip()

    draft = WorkoutPlanCreate(
        id_cliente=context.client.id if context.client is not None else None,
        nome=_build_workout_name(request, client_name),
        obiettivo=request.preset.obiettivo_builder,
        livello=context.scientific_profile.livello_workout,
        durata_settimane=4,
        sessioni_per_settimana=canonical_plan.frequenza,
        note="Generata da training-science/plan-package v1",
        sessioni=workout_sessions,
    )
    warnings = list(dict.fromkeys([
        *context.scientific_profile.profile_warnings,
        *canonical_plan.note_generazione,
    ]))
    return TSPlanPackage(
        scientific_profile=context.scientific_profile,
        canonical_plan=canonical_plan,
        rankings=rankings,
        workout_projection=TSWorkoutProjection(draft=draft, slot_bindings=slot_bindings),
        warnings=warnings,
        protocol=TSPlanPackageProtocolInfo(
            protocol_id=protocol_selection.protocol.protocol_id,
            label=protocol_selection.protocol.label,
            status=protocol_selection.protocol.status,
            exact_match=protocol_selection.exact_match,
            registry_version=protocol_selection.registry_version,
            validation_case_ids=list(protocol_selection.protocol.validation_case_ids),
            selection_rationale=list(protocol_selection.selection_rationale),
        ),
        constraint_evaluation=constraint_evaluation,
        feasibility_summary=TSFeasibilitySummary(
            feasible_count=feasibility.feasible_count,
            discouraged_count=feasibility.discouraged_count,
            infeasible_count=feasibility.infeasible_count,
        ),
        engine=TSPlanPackageEngineInfo(
            planner_version="ts-plan-v1",
            ranking_version="ts-rank-v2-feasibility",
            profile_version="ts-profile-v1",
        ),
    )
