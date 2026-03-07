"""Validation Matrix v1 — pytest harness per i 6 benchmark VM-001..VM-006.

Esegue la pipeline pura (zero DB) per ogni caso benchmark:
  fixture → profile → protocol selection → plan build → constraint eval → validation checks

Ogni test verifica che il plan-package generato passi tutti gli invariant,
snapshot e tolerance checks definiti nel catalogo.
"""

import pytest

from api.schemas.training_science import (
    TSCanonicalPlan,
    TSCanonicalSession,
    TSCanonicalSlot,
    TSFeasibilitySummary,
    TSPlanPackage,
    TSPlanPackageEngineInfo,
    TSPlanPackageProtocolInfo,
    TSScientificProfileResolved,
    TSValidationMetadata,
    TSWorkoutProjection,
)
from api.schemas.workout import WorkoutPlanCreate, WorkoutSessionInput
from api.services.training_science import TemplatePiano, analyze_plan, build_plan
from api.services.training_science.constraints import evaluate_protocol_constraints
from api.services.training_science.registry import select_protocol
from api.services.training_science.runtime.validation_metadata import ValidationMetadata
from api.services.training_science.validation.validation_catalog import (
    CLIENT_FIXTURES,
    REQUEST_FIXTURES,
    VALIDATION_MATRIX,
    ValidationCase,
)
from api.services.training_science.validation.validation_contracts import (
    ValidationReport,
    run_validation_case,
)

_LIVELLO_MAP = {
    "principiante": "beginner",
    "intermedio": "intermedio",
    "avanzato": "avanzato",
}

_OBIETTIVO_BUILDER_MAP = {
    "ipertrofia": "ipertrofia",
    "tonificazione": "generale",
    "forza": "forza",
    "dimagrimento": "dimagrimento",
    "resistenza": "resistenza",
}


def _build_profile(case: ValidationCase) -> TSScientificProfileResolved:
    """Risolve profilo scientifico dai fixture del caso benchmark."""
    client = CLIENT_FIXTURES[case.client_fixture_id]
    request = REQUEST_FIXTURES[case.request_fixture_id]
    return TSScientificProfileResolved(
        obiettivo_builder=_OBIETTIVO_BUILDER_MAP[request.obiettivo.value],
        obiettivo_scientifico=request.obiettivo,
        livello_scientifico=request.livello,
        livello_workout=_LIVELLO_MAP[request.livello.value],
        mode=request.mode,
        anamnesi_state="structured" if client.has_structured_anamnesis else "legacy",
        safety_condition_count=len(client.clinical_flags),
        profile_warnings=[],
    )


def _build_canonical_plan(template: TemplatePiano) -> TSCanonicalPlan:
    """Converte TemplatePiano in TSCanonicalPlan (replica di plan_package_service)."""
    sessions: list[TSCanonicalSession] = []
    for s_idx, session in enumerate(template.sessioni, start=1):
        session_id = f"s{s_idx}"
        slots = [
            TSCanonicalSlot(
                slot_id=f"{session_id}_sl{sl_idx}",
                pattern=slot.pattern,
                priorita=slot.priorita,
                serie=slot.serie,
                rep_min=slot.rep_min,
                rep_max=slot.rep_max,
                riposo_sec=slot.riposo_sec,
                muscolo_target=slot.muscolo_target,
                note=slot.note,
            )
            for sl_idx, slot in enumerate(session.slots, start=1)
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
    plan_id = f"plan_f{template.frequenza}_{template.obiettivo.value}_{template.livello.value}"
    return TSCanonicalPlan(
        plan_id=plan_id,
        frequenza=template.frequenza,
        obiettivo=template.obiettivo,
        livello=template.livello,
        tipo_split=template.tipo_split,
        sessioni=sessions,
        note_generazione=template.note_generazione,
    )


def _build_package_for_case(case: ValidationCase) -> TSPlanPackage:
    """Costruisce un TSPlanPackage completo via pipeline pura (zero DB)."""
    profile = _build_profile(case)
    request_fixture = REQUEST_FIXTURES[case.request_fixture_id]

    protocol_selection = select_protocol(
        profile=profile,
        frequenza=request_fixture.frequenza,
    )
    template_plan = build_plan(
        request_fixture.frequenza,
        profile.obiettivo_scientifico,
        profile.livello_scientifico,
    )
    canonical_plan = _build_canonical_plan(template_plan)
    analyzer = analyze_plan(template_plan)
    constraint_eval = evaluate_protocol_constraints(
        protocol_selection=protocol_selection,
        canonical_plan=canonical_plan,
        analyzer=analyzer,
        requested_frequenza=request_fixture.frequenza,
    )

    validation_meta = ValidationMetadata.build(
        protocol_id=protocol_selection.protocol.protocol_id,
        constraint_profile_id=protocol_selection.protocol.constraint_profile_id,
        validation_case_ids=protocol_selection.protocol.validation_case_ids,
    )

    # Draft sintetico (rankings vuoti — i check non ispezionano exercise bindings)
    workout_sessions = [
        WorkoutSessionInput(
            nome_sessione=session.nome,
            focus_muscolare=session.focus,
            durata_minuti=60,
            esercizi=[],
            blocchi=[],
        )
        for session in canonical_plan.sessioni
    ]
    draft = WorkoutPlanCreate(
        nome=f"Validation {case.case_id}",
        obiettivo=profile.obiettivo_builder,
        livello=profile.livello_workout,
        durata_settimane=4,
        sessioni_per_settimana=canonical_plan.frequenza,
        note=f"Generated for benchmark {case.case_id}",
        sessioni=workout_sessions,
    )

    return TSPlanPackage(
        scientific_profile=profile,
        canonical_plan=canonical_plan,
        rankings={},
        workout_projection=TSWorkoutProjection(draft=draft, slot_bindings=[]),
        warnings=list(dict.fromkeys([
            *profile.profile_warnings,
            *canonical_plan.note_generazione,
            *(["clinical_mode_active"] if profile.mode == "clinical" else []),
        ])),
        protocol=TSPlanPackageProtocolInfo(
            protocol_id=protocol_selection.protocol.protocol_id,
            label=protocol_selection.protocol.label,
            status=protocol_selection.protocol.status,
            exact_match=protocol_selection.exact_match,
            registry_version=protocol_selection.registry_version,
            validation_case_ids=list(protocol_selection.protocol.validation_case_ids),
            selection_rationale=list(protocol_selection.selection_rationale),
        ),
        constraint_evaluation=constraint_eval,
        feasibility_summary=TSFeasibilitySummary(
            feasible_count=0,
            discouraged_count=0,
            infeasible_count=0,
        ),
        validation=TSValidationMetadata(**validation_meta.__dict__),
        engine=TSPlanPackageEngineInfo(
            planner_version="ts-plan-v1",
            ranking_version="ts-rank-v2-feasibility-demand",
            profile_version="ts-profile-v1",
        ),
    )


def _format_failures(report: ValidationReport) -> str:
    """Formatta i check falliti per messaggio di errore leggibile."""
    lines: list[str] = []
    for result in (
        *report.invariant_results,
        *report.snapshot_results,
        *report.tolerance_results,
        *report.warning_policy_results,
    ):
        if result.verdict == "fail":
            lines.append(f"  FAIL [{result.check_id}]: {result.message}")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
# Parametrized test per tutti i 6 benchmark cases
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(params=list(VALIDATION_MATRIX.keys()), ids=list(VALIDATION_MATRIX.keys()))
def benchmark_case(request: pytest.FixtureRequest) -> tuple[ValidationCase, TSPlanPackage, ValidationReport]:
    """Genera package e report per ogni caso benchmark."""
    case = VALIDATION_MATRIX[request.param]
    package = _build_package_for_case(case)
    report = run_validation_case(case, package)
    return case, package, report


class TestValidationMatrixInvariants:
    """Invariant checks — hard gates, non possono fallire."""

    def test_no_invariant_failures(
        self,
        benchmark_case: tuple[ValidationCase, TSPlanPackage, ValidationReport],
    ) -> None:
        case, _, report = benchmark_case
        failures = [r for r in report.invariant_results if r.verdict == "fail"]
        assert not failures, (
            f"{case.case_id}: {len(failures)} invariant failure(s):\n"
            + "\n".join(f"  [{r.check_id}] {r.message}" for r in failures)
        )

    def test_no_skipped_invariants(
        self,
        benchmark_case: tuple[ValidationCase, TSPlanPackage, ValidationReport],
    ) -> None:
        case, _, report = benchmark_case
        skipped = [r for r in report.invariant_results if r.verdict == "skip"]
        assert not skipped, (
            f"{case.case_id}: {len(skipped)} invariant check(s) skipped:\n"
            + "\n".join(f"  [{r.check_id}] {r.message}" for r in skipped)
        )


class TestValidationMatrixSnapshots:
    """Snapshot checks — contratti comportamentali stabili."""

    def test_no_snapshot_failures(
        self,
        benchmark_case: tuple[ValidationCase, TSPlanPackage, ValidationReport],
    ) -> None:
        case, _, report = benchmark_case
        failures = [r for r in report.snapshot_results if r.verdict == "fail"]
        assert not failures, (
            f"{case.case_id}: {len(failures)} snapshot failure(s):\n"
            + "\n".join(f"  [{r.check_id}] {r.message}" for r in failures)
        )


class TestValidationMatrixTolerance:
    """Tolerance checks — ammessi entro range dichiarato."""

    def test_no_tolerance_failures(
        self,
        benchmark_case: tuple[ValidationCase, TSPlanPackage, ValidationReport],
    ) -> None:
        case, _, report = benchmark_case
        failures = [r for r in report.tolerance_results if r.verdict == "fail"]
        assert not failures, (
            f"{case.case_id}: {len(failures)} tolerance failure(s):\n"
            + "\n".join(f"  [{r.check_id}] {r.message}" for r in failures)
        )


class TestValidationMatrixWarningPolicy:
    """Warning policy — required/forbidden warnings."""

    def test_no_warning_policy_violations(
        self,
        benchmark_case: tuple[ValidationCase, TSPlanPackage, ValidationReport],
    ) -> None:
        case, _, report = benchmark_case
        failures = [r for r in report.warning_policy_results if r.verdict == "fail"]
        assert not failures, (
            f"{case.case_id}: {len(failures)} warning policy violation(s):\n"
            + "\n".join(f"  [{r.check_id}] {r.message}" for r in failures)
        )


class TestValidationMatrixOverall:
    """Overall pass/fail e conteggi aggregati."""

    def test_zero_hard_fails(
        self,
        benchmark_case: tuple[ValidationCase, TSPlanPackage, ValidationReport],
    ) -> None:
        case, _, report = benchmark_case
        assert report.hard_fail_count == 0, (
            f"{case.case_id}: {report.hard_fail_count} hard fail(s)\n"
            + _format_failures(report)
        )

    def test_protocol_matches_expected(
        self,
        benchmark_case: tuple[ValidationCase, TSPlanPackage, ValidationReport],
    ) -> None:
        case, package, _ = benchmark_case
        assert package.protocol.protocol_id == case.protocol_id, (
            f"{case.case_id}: expected protocol {case.protocol_id}, "
            f"got {package.protocol.protocol_id}"
        )

    def test_engine_versions_populated(
        self,
        benchmark_case: tuple[ValidationCase, TSPlanPackage, ValidationReport],
    ) -> None:
        _, package, _ = benchmark_case
        assert package.engine.planner_version
        assert package.engine.ranking_version
        assert package.engine.profile_version

    def test_validation_metadata_populated(
        self,
        benchmark_case: tuple[ValidationCase, TSPlanPackage, ValidationReport],
    ) -> None:
        _, package, _ = benchmark_case
        assert package.validation.protocol_id
        assert package.validation.protocol_registry_version
        assert package.validation.constraint_engine_version
        assert package.validation.evidence_registry_version
        assert package.validation.feasibility_engine_version
        assert package.validation.generated_at
