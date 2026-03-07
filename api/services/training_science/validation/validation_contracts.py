"""Validation Contracts v1 — check functions per la Validation Matrix.

Verifica deterministica del plan-package output contro le aspettative
dei 6 benchmark cases (VM-001..VM-006).

3 livelli di check:
1. Invariant — hard gate, non possono fallire
2. Snapshot  — contratti comportamentali stabili
3. Tolerance — ammessi entro range dichiarato

Fonte spec: UPG-2026-03-07-60 (SMART Validation Matrix v1).
"""

from dataclasses import dataclass
from typing import Literal

from api.schemas.training_science import TSPlanPackage
from api.services.training_science.demand import (
    check_demand_ceiling,
    get_default_demand_vector,
    get_protocol_ceiling,
)

from .validation_catalog import ValidationCase

VALIDATION_CONTRACTS_VERSION = "smart-validation-contracts-v1"

CheckVerdict = Literal["pass", "fail", "skip"]


@dataclass(frozen=True)
class CheckResult:
    """Esito di un singolo check."""

    check_id: str
    verdict: CheckVerdict
    message: str = ""
    failure_class: str = ""


@dataclass(frozen=True)
class ValidationReport:
    """Report completo per un singolo benchmark case."""

    case_id: str
    protocol_id: str
    invariant_results: tuple[CheckResult, ...]
    snapshot_results: tuple[CheckResult, ...]
    tolerance_results: tuple[CheckResult, ...]
    warning_policy_results: tuple[CheckResult, ...]
    overall_pass: bool
    hard_fail_count: int = 0
    soft_fail_count: int = 0


# ──────────────────────────────────────────────────────────────────────
# 1. Invariant Checks
# ──────────────────────────────────────────────────────────────────────


def _check_protocol_selection_correct(
    case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    if package.protocol.protocol_id == case.protocol_id:
        return CheckResult(
            check_id="protocol_selection_correct",
            verdict="pass",
            message=f"Protocollo selezionato {case.protocol_id} corretto.",
        )
    return CheckResult(
        check_id="protocol_selection_correct",
        verdict="fail",
        message=(
            f"Atteso {case.protocol_id}, ottenuto {package.protocol.protocol_id}."
        ),
        failure_class="protocol_selection_regression",
    )


def _check_split_family_correct(
    case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    actual_split = package.canonical_plan.tipo_split.value
    expected_families = {
        "full_body": "full_body",
        "upper_lower": "upper_lower",
        "push_pull_legs": "push_pull_legs",
    }
    expected = expected_families.get(case.expected_split_family, case.expected_split_family)
    if actual_split == expected:
        return CheckResult(
            check_id="split_family_correct",
            verdict="pass",
            message=f"Split family {expected} corretto.",
        )
    return CheckResult(
        check_id="split_family_correct",
        verdict="fail",
        message=f"Atteso split '{expected}', ottenuto '{actual_split}'.",
        failure_class="constraint_violation",
    )


def _check_no_advanced_draft_exercise(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    profile_level = package.scientific_profile.livello_scientifico
    if profile_level.value in ("principiante",):
        for warning in package.warnings:
            if "advanced_draft" in warning.lower():
                return CheckResult(
                    check_id="no_advanced_draft_exercise",
                    verdict="fail",
                    message="Esercizio advanced nel draft di un profilo beginner.",
                    failure_class="draft_suitability_regression",
                )
    return CheckResult(
        check_id="no_advanced_draft_exercise",
        verdict="pass",
        message="Nessun esercizio advanced inappropriato nel draft.",
    )


def _check_no_ceiling_exceeded(
    case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    ceiling = get_protocol_ceiling(case.protocol_id)
    if ceiling is None:
        return CheckResult(
            check_id="no_ceiling_exceeded",
            verdict="skip",
            message=f"Nessun ceiling definito per {case.protocol_id}.",
        )
    violations = []
    for slot_id, candidates in package.rankings.items():
        if not candidates:
            continue
        top = candidates[0]
        for session in package.canonical_plan.sessioni:
            for slot in session.slots:
                if slot.slot_id == slot_id:
                    vector = get_default_demand_vector(slot.pattern, "beginner")
                    result = check_demand_ceiling(vector, ceiling)
                    if result.is_hard_fail:
                        violations.append(
                            f"Slot {slot_id} (ex {top.exercise_id}): "
                            f"{result.violations_count} dimension violations"
                        )
    if violations:
        return CheckResult(
            check_id="no_ceiling_exceeded",
            verdict="fail",
            message=f"Ceiling exceeded: {'; '.join(violations[:3])}.",
            failure_class="draft_suitability_regression",
        )
    return CheckResult(
        check_id="no_ceiling_exceeded",
        verdict="pass",
        message="Nessun esercizio supera il ceiling del protocollo.",
    )


def _check_no_hard_constraint_fail(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    if package.constraint_evaluation.summary.hard_fail_count > 0:
        return CheckResult(
            check_id="no_hard_constraint_fail",
            verdict="fail",
            message=(
                f"{package.constraint_evaluation.summary.hard_fail_count} "
                f"hard constraint fail nel report."
            ),
            failure_class="constraint_violation",
        )
    return CheckResult(
        check_id="no_hard_constraint_fail",
        verdict="pass",
        message="Nessun hard constraint fail.",
    )


def _check_no_ballistic_impact_draft(
    case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    ceiling = get_protocol_ceiling(case.protocol_id)
    if ceiling is None:
        return CheckResult(
            check_id="no_ballistic_impact_draft",
            verdict="skip",
            message="Nessun ceiling definito.",
        )
    max_ballistic = getattr(ceiling, "max_ballistic_demand", None)
    max_impact = getattr(ceiling, "max_impact_demand", None)
    if max_ballistic == 0 and max_impact == 0:
        for session in package.canonical_plan.sessioni:
            for slot in session.slots:
                vector = get_default_demand_vector(slot.pattern, "beginner")
                if vector.ballistic_demand > 0 or vector.impact_demand > 0:
                    return CheckResult(
                        check_id="no_ballistic_impact_draft",
                        verdict="fail",
                        message=(
                            f"Slot {slot.slot_id}: ballistic={vector.ballistic_demand}, "
                            f"impact={vector.impact_demand} in protocollo zero-ballistic."
                        ),
                        failure_class="clinical_overlay_regression",
                    )
    return CheckResult(
        check_id="no_ballistic_impact_draft",
        verdict="pass",
        message="Nessun esercizio balistico/impact nel draft clinical.",
    )


def _check_demand_shoulder_lumbar_contained(
    case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    ceiling = get_protocol_ceiling(case.protocol_id)
    if ceiling is None:
        return CheckResult(
            check_id="demand_shoulder_lumbar_contained",
            verdict="skip",
            message="Nessun ceiling definito.",
        )
    max_shoulder = getattr(ceiling, "max_shoulder_complex_demand", None)
    max_lumbar = getattr(ceiling, "max_lumbar_load_demand", None)
    violations = []
    for session in package.canonical_plan.sessioni:
        for slot in session.slots:
            vector = get_default_demand_vector(slot.pattern, "beginner")
            if max_shoulder is not None and vector.shoulder_complex_demand > max_shoulder:
                violations.append(f"{slot.slot_id}: shoulder={vector.shoulder_complex_demand}")
            if max_lumbar is not None and vector.lumbar_load_demand > max_lumbar:
                violations.append(f"{slot.slot_id}: lumbar={vector.lumbar_load_demand}")
    if violations:
        return CheckResult(
            check_id="demand_shoulder_lumbar_contained",
            verdict="fail",
            message=f"Shoulder/lumbar fuori ceiling: {'; '.join(violations[:3])}.",
            failure_class="clinical_overlay_regression",
        )
    return CheckResult(
        check_id="demand_shoulder_lumbar_contained",
        verdict="pass",
        message="Costo spalla/lombare contenuto nel ceiling.",
    )


_INVARIANT_CHECKS = {
    "protocol_selection_correct": _check_protocol_selection_correct,
    "split_family_correct": _check_split_family_correct,
    "no_advanced_draft_exercise": _check_no_advanced_draft_exercise,
    "no_ceiling_exceeded": _check_no_ceiling_exceeded,
    "no_hard_constraint_fail": _check_no_hard_constraint_fail,
    "no_ballistic_impact_draft": _check_no_ballistic_impact_draft,
    "demand_shoulder_lumbar_contained": _check_demand_shoulder_lumbar_contained,
}


# ──────────────────────────────────────────────────────────────────────
# 2. Snapshot Checks
# ──────────────────────────────────────────────────────────────────────


def _check_session_count_matches_frequenza(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    actual = len(package.canonical_plan.sessioni)
    expected = package.canonical_plan.frequenza
    if actual == expected:
        return CheckResult(
            check_id="session_count_matches_frequenza",
            verdict="pass",
            message=f"Sessioni {actual} = frequenza {expected}.",
        )
    return CheckResult(
        check_id="session_count_matches_frequenza",
        verdict="fail",
        message=f"Sessioni {actual} != frequenza {expected}.",
        failure_class="constraint_violation",
    )


def _check_session_roles_full_body(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    for session in package.canonical_plan.sessioni:
        if "full" not in session.ruolo.value.lower():
            return CheckResult(
                check_id="session_roles_full_body",
                verdict="fail",
                message=f"Sessione {session.session_id} ruolo '{session.ruolo.value}' non full body.",
                failure_class="constraint_violation",
            )
    return CheckResult(
        check_id="session_roles_full_body",
        verdict="pass",
        message="Tutte le sessioni sono full body.",
    )


def _check_session_roles_upper_lower(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    roles = {s.ruolo.value for s in package.canonical_plan.sessioni}
    has_upper = any("upper" in r.lower() for r in roles)
    has_lower = any("lower" in r.lower() for r in roles)
    if has_upper and has_lower:
        return CheckResult(
            check_id="session_roles_upper_lower",
            verdict="pass",
            message="Split upper/lower con ruoli corretti.",
        )
    return CheckResult(
        check_id="session_roles_upper_lower",
        verdict="fail",
        message=f"Ruoli sessione non upper/lower: {roles}.",
        failure_class="constraint_violation",
    )


def _check_pattern_exposure_balanced(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    """Verifica che i pattern principali siano rappresentati."""
    patterns_seen: set[str] = set()
    for session in package.canonical_plan.sessioni:
        for slot in session.slots:
            patterns_seen.add(slot.pattern.value)
    core_patterns = {"squat", "hinge", "push_h", "push_v", "pull_h", "pull_v"}
    missing = core_patterns - patterns_seen
    if len(missing) <= 1:
        return CheckResult(
            check_id="pattern_exposure_balanced",
            verdict="pass",
            message=f"Pattern coverage: {len(patterns_seen)} pattern, max 1 mancante.",
        )
    return CheckResult(
        check_id="pattern_exposure_balanced",
        verdict="fail",
        message=f"Pattern mancanti: {missing}.",
        failure_class="analysis_regression",
    )


def _check_compound_priority_high(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    """Verifica che i compound siano prioritari (forza)."""
    compound_patterns = {"squat", "hinge", "push_h", "push_v", "pull_h", "pull_v"}
    for session in package.canonical_plan.sessioni:
        if session.slots:
            first_pattern = session.slots[0].pattern.value
            if first_pattern in compound_patterns:
                continue
            return CheckResult(
                check_id="compound_priority_high",
                verdict="fail",
                message=f"Sessione {session.session_id}: primo slot non compound ({first_pattern}).",
                failure_class="analysis_regression",
            )
    return CheckResult(
        check_id="compound_priority_high",
        verdict="pass",
        message="Compound priority rispettata in tutte le sessioni.",
    )


def _check_advanced_suitability_allowed(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    """Verifica che il profilo advanced non sia gate-bloccato."""
    if package.scientific_profile.livello_scientifico.value == "avanzato":
        return CheckResult(
            check_id="advanced_suitability_allowed",
            verdict="pass",
            message="Profilo avanzato correttamente abilitato.",
        )
    return CheckResult(
        check_id="advanced_suitability_allowed",
        verdict="fail",
        message=f"Livello {package.scientific_profile.livello_scientifico.value} != avanzato.",
        failure_class="draft_suitability_regression",
    )


def _check_clinical_overlay_dominant(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    """Verifica che il mode clinical sia attivo."""
    if package.scientific_profile.mode == "clinical":
        return CheckResult(
            check_id="clinical_overlay_dominant",
            verdict="pass",
            message="Clinical overlay dominante.",
        )
    return CheckResult(
        check_id="clinical_overlay_dominant",
        verdict="fail",
        message=f"Mode '{package.scientific_profile.mode}' != clinical.",
        failure_class="clinical_overlay_regression",
    )


_SNAPSHOT_CHECKS = {
    "session_count_matches_frequenza": _check_session_count_matches_frequenza,
    "session_roles_full_body": _check_session_roles_full_body,
    "session_roles_upper_lower": _check_session_roles_upper_lower,
    "pattern_exposure_balanced": _check_pattern_exposure_balanced,
    "compound_priority_high": _check_compound_priority_high,
    "advanced_suitability_allowed": _check_advanced_suitability_allowed,
    "clinical_overlay_dominant": _check_clinical_overlay_dominant,
}


# ──────────────────────────────────────────────────────────────────────
# 3. Tolerance Checks
# ──────────────────────────────────────────────────────────────────────


def _check_score_above_band(
    case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    score = package.constraint_evaluation.analyzer_score
    minimum = case.score_band.minimum
    if score >= minimum:
        return CheckResult(
            check_id="score_above_band",
            verdict="pass",
            message=f"Score {score:.0f} >= {minimum} ({case.score_band.description}).",
        )
    return CheckResult(
        check_id="score_above_band",
        verdict="fail",
        message=f"Score {score:.0f} < {minimum} ({case.score_band.description}).",
        failure_class="score_regression",
    )


def _check_push_pull_ratio_in_band(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    """Verifica che il push:pull non sia estremo (0.6..1.5)."""
    push_count = 0
    pull_count = 0
    for session in package.canonical_plan.sessioni:
        for slot in session.slots:
            if slot.pattern.value in ("push_h", "push_v"):
                push_count += slot.serie
            elif slot.pattern.value in ("pull_h", "pull_v"):
                pull_count += slot.serie
    if pull_count == 0:
        return CheckResult(
            check_id="push_pull_ratio_in_band",
            verdict="fail",
            message="Zero serie pull nel piano.",
            failure_class="analysis_regression",
        )
    ratio = push_count / pull_count
    if 0.6 <= ratio <= 1.5:
        return CheckResult(
            check_id="push_pull_ratio_in_band",
            verdict="pass",
            message=f"Push:pull ratio {ratio:.2f} in banda (0.6-1.5).",
        )
    return CheckResult(
        check_id="push_pull_ratio_in_band",
        verdict="fail",
        message=f"Push:pull ratio {ratio:.2f} fuori banda (0.6-1.5).",
        failure_class="analysis_regression",
    )


def _check_volume_in_low_mav(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    total_sets = sum(
        slot.serie
        for session in package.canonical_plan.sessioni
        for slot in session.slots
    )
    if total_sets <= 60:
        return CheckResult(
            check_id="volume_in_low_mav",
            verdict="pass",
            message=f"Volume totale {total_sets} serie/sett in low_mav.",
        )
    return CheckResult(
        check_id="volume_in_low_mav",
        verdict="fail",
        message=f"Volume totale {total_sets} serie/sett troppo alto per low_mav.",
        failure_class="analysis_regression",
    )


def _check_volume_in_mid_high_mav(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    total_sets = sum(
        slot.serie
        for session in package.canonical_plan.sessioni
        for slot in session.slots
    )
    if 40 <= total_sets <= 100:
        return CheckResult(
            check_id="volume_in_mid_high_mav",
            verdict="pass",
            message=f"Volume totale {total_sets} serie/sett in mid/high_mav.",
        )
    return CheckResult(
        check_id="volume_in_mid_high_mav",
        verdict="fail",
        message=f"Volume totale {total_sets} fuori range mid/high_mav (40-100).",
        failure_class="analysis_regression",
    )


def _check_recovery_overlap_below_threshold(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    recovery_warnings = [w for w in package.warnings if "recupero" in w.lower()]
    if len(recovery_warnings) <= 2:
        return CheckResult(
            check_id="recovery_overlap_below_threshold",
            verdict="pass",
            message=f"Recovery warnings: {len(recovery_warnings)} (soglia 2).",
        )
    return CheckResult(
        check_id="recovery_overlap_below_threshold",
        verdict="fail",
        message=f"Recovery warnings: {len(recovery_warnings)} > soglia 2.",
        failure_class="analysis_regression",
    )


def _check_strength_bias_present(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    """Verifica che esista un bias forza (serie basse, rep basse)."""
    low_rep_slots = 0
    total_slots = 0
    for session in package.canonical_plan.sessioni:
        for slot in session.slots:
            total_slots += 1
            if slot.rep_max <= 6:
                low_rep_slots += 1
    if total_slots == 0:
        return CheckResult(
            check_id="strength_bias_present",
            verdict="skip",
            message="Nessuno slot nel piano.",
        )
    ratio = low_rep_slots / total_slots
    if ratio >= 0.3:
        return CheckResult(
            check_id="strength_bias_present",
            verdict="pass",
            message=f"Strength bias: {ratio:.0%} slot con rep<=6.",
        )
    return CheckResult(
        check_id="strength_bias_present",
        verdict="fail",
        message=f"Strength bias assente: solo {ratio:.0%} slot con rep<=6.",
        failure_class="analysis_regression",
    )


def _check_volume_high_controlled(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    total_sets = sum(
        slot.serie
        for session in package.canonical_plan.sessioni
        for slot in session.slots
    )
    if 60 <= total_sets <= 140:
        return CheckResult(
            check_id="volume_high_controlled",
            verdict="pass",
            message=f"Volume alto controllato: {total_sets} serie/sett.",
        )
    return CheckResult(
        check_id="volume_high_controlled",
        verdict="fail",
        message=f"Volume {total_sets} fuori range alto controllato (60-140).",
        failure_class="analysis_regression",
    )


def _check_volume_conservative(
    _case: ValidationCase, package: TSPlanPackage
) -> CheckResult:
    total_sets = sum(
        slot.serie
        for session in package.canonical_plan.sessioni
        for slot in session.slots
    )
    if total_sets <= 50:
        return CheckResult(
            check_id="volume_conservative",
            verdict="pass",
            message=f"Volume conservativo: {total_sets} serie/sett.",
        )
    return CheckResult(
        check_id="volume_conservative",
        verdict="fail",
        message=f"Volume {total_sets} troppo alto per clinical (soglia 50).",
        failure_class="clinical_overlay_regression",
    )


_TOLERANCE_CHECKS = {
    "score_above_band": _check_score_above_band,
    "push_pull_ratio_in_band": _check_push_pull_ratio_in_band,
    "volume_in_low_mav": _check_volume_in_low_mav,
    "volume_in_mid_high_mav": _check_volume_in_mid_high_mav,
    "recovery_overlap_below_threshold": _check_recovery_overlap_below_threshold,
    "strength_bias_present": _check_strength_bias_present,
    "volume_high_controlled": _check_volume_high_controlled,
    "volume_conservative": _check_volume_conservative,
}


# ──────────────────────────────────────────────────────────────────────
# 4. Warning Policy Checks
# ──────────────────────────────────────────────────────────────────────


def _check_warning_policy(
    case: ValidationCase, package: TSPlanPackage
) -> list[CheckResult]:
    """Verifica required/forbidden warnings."""
    results: list[CheckResult] = []
    warnings_lower = {w.lower() for w in package.warnings}

    for required in case.warning_policy.required:
        found = any(required.lower() in w for w in warnings_lower)
        if found:
            results.append(CheckResult(
                check_id=f"warning_required:{required}",
                verdict="pass",
                message=f"Warning obbligatorio '{required}' presente.",
            ))
        else:
            results.append(CheckResult(
                check_id=f"warning_required:{required}",
                verdict="fail",
                message=f"Warning obbligatorio '{required}' mancante.",
                failure_class="analysis_regression",
            ))

    for forbidden in case.warning_policy.forbidden:
        found = any(forbidden.lower() in w for w in warnings_lower)
        if found:
            results.append(CheckResult(
                check_id=f"warning_forbidden:{forbidden}",
                verdict="fail",
                message=f"Warning vietato '{forbidden}' presente.",
                failure_class="analysis_regression",
            ))
        else:
            results.append(CheckResult(
                check_id=f"warning_forbidden:{forbidden}",
                verdict="pass",
                message=f"Warning vietato '{forbidden}' assente.",
            ))

    return results


# ──────────────────────────────────────────────────────────────────────
# 5. Runner — esegue tutti i check per un caso benchmark
# ──────────────────────────────────────────────────────────────────────


def run_validation_case(
    case: ValidationCase,
    package: TSPlanPackage,
) -> ValidationReport:
    """Esegue tutti i check dichiarati per un caso benchmark.

    Puro e deterministico. Nessun side-effect.
    """
    invariant_results: list[CheckResult] = []
    for check_id in case.invariant_checks:
        fn = _INVARIANT_CHECKS.get(check_id)
        if fn:
            invariant_results.append(fn(case, package))
        else:
            invariant_results.append(CheckResult(
                check_id=check_id,
                verdict="skip",
                message=f"Check '{check_id}' non implementato.",
            ))

    snapshot_results: list[CheckResult] = []
    for check_id in case.snapshot_checks:
        fn = _SNAPSHOT_CHECKS.get(check_id)
        if fn:
            snapshot_results.append(fn(case, package))
        else:
            snapshot_results.append(CheckResult(
                check_id=check_id,
                verdict="skip",
                message=f"Check '{check_id}' non implementato.",
            ))

    tolerance_results: list[CheckResult] = []
    for check_id in case.tolerance_checks:
        fn = _TOLERANCE_CHECKS.get(check_id)
        if fn:
            tolerance_results.append(fn(case, package))
        else:
            tolerance_results.append(CheckResult(
                check_id=check_id,
                verdict="skip",
                message=f"Check '{check_id}' non implementato.",
            ))

    warning_results = _check_warning_policy(case, package)

    hard_fail_count = sum(
        1 for r in invariant_results if r.verdict == "fail"
    )
    soft_fail_count = sum(
        1 for r in (snapshot_results + tolerance_results + warning_results)
        if r.verdict == "fail"
    )
    overall_pass = hard_fail_count == 0 and soft_fail_count == 0

    return ValidationReport(
        case_id=case.case_id,
        protocol_id=case.protocol_id,
        invariant_results=tuple(invariant_results),
        snapshot_results=tuple(snapshot_results),
        tolerance_results=tuple(tolerance_results),
        warning_policy_results=tuple(warning_results),
        overall_pass=overall_pass,
        hard_fail_count=hard_fail_count,
        soft_fail_count=soft_fail_count,
    )


def run_full_matrix(
    packages: dict[str, TSPlanPackage],
) -> dict[str, ValidationReport]:
    """Esegue tutti i 6 benchmark della matrice.

    Args:
        packages: dict case_id → TSPlanPackage generato per quel caso.

    Returns:
        dict case_id → ValidationReport.
    """
    from .validation_catalog import VALIDATION_MATRIX

    reports: dict[str, ValidationReport] = {}
    for case_id, case in VALIDATION_MATRIX.items():
        package = packages.get(case_id)
        if package is None:
            reports[case_id] = ValidationReport(
                case_id=case_id,
                protocol_id=case.protocol_id,
                invariant_results=(),
                snapshot_results=(),
                tolerance_results=(),
                warning_policy_results=(),
                overall_pass=False,
                hard_fail_count=1,
            )
            continue
        reports[case_id] = run_validation_case(case, package)
    return reports
