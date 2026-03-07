"""Feasibility Engine v2 — classificazione pre-ranking degli esercizi.

Separa la logica di ammissibilita' (puo'/non-puo' entrare nel draft)
dalla logica di ordinamento (quale esercizio e' migliore per lo slot).

Il ranker riceve solo esercizi gia' classificati e non fa piu' gate autonomi.
Ogni verdetto e' deterministico, spiegabile e testabile.

v2: demand ceiling gate — il vettore biomeccanico 10D di ogni esercizio
    viene confrontato con il ceiling del protocollo selezionato.
    Violations hard → infeasible, family discouraged → discouraged.
"""

from dataclasses import dataclass, field
from typing import Literal

from api.schemas.safety import ExerciseSafetyEntry
from api.schemas.training_science import TSScientificProfileResolved
from api.services.training_science.demand.demand_policy import (
    DemandPolicyResult,
    check_demand_ceiling,
)
from api.services.training_science.demand.demand_registry import (
    get_default_demand_vector,
    get_protocol_ceiling,
)
from api.services.training_science.types import PatternMovimento

from .exercise_catalog import RankableExercise

FEASIBILITY_ENGINE_VERSION = "smart-feasibility-v2"

FeasibilityVerdict = Literal["feasible", "discouraged", "infeasible_for_auto_draft"]

_BEGINNER_POWER_SKILL_TOKENS = (
    "jump",
    "salto",
    "muscle-up",
    "muscle up",
    "plyo",
)

_SAFETY_TO_VERDICT: dict[str | None, FeasibilityVerdict] = {
    None: "feasible",
    "caution": "feasible",
    "modify": "discouraged",
    "avoid": "infeasible_for_auto_draft",
}


@dataclass(frozen=True)
class ExerciseFeasibility:
    """Verdetto di ammissibilita' per un singolo esercizio."""

    exercise_id: int
    verdict: FeasibilityVerdict
    reason_codes: tuple[str, ...]
    safety_severity: str | None = None
    demand_policy_result: DemandPolicyResult | None = None


@dataclass(frozen=True)
class FeasibilityReport:
    """Report completo di ammissibilita' per l'intero catalogo pre-ranking."""

    entries: dict[int, ExerciseFeasibility] = field(default_factory=dict)
    feasible_count: int = 0
    discouraged_count: int = 0
    infeasible_count: int = 0
    demand_ceiling_violations: int = 0
    demand_family_exclusions: int = 0
    demand_family_discouraged: int = 0
    infeasible_by_beginner_gate: int = 0
    infeasible_by_safety: int = 0
    infeasible_by_demand: int = 0
    discouraged_by_safety: int = 0
    discouraged_by_demand: int = 0

    def is_feasible(self, exercise_id: int) -> bool:
        entry = self.entries.get(exercise_id)
        return entry is not None and entry.verdict == "feasible"

    def get_verdict(self, exercise_id: int) -> FeasibilityVerdict:
        entry = self.entries.get(exercise_id)
        if entry is None:
            return "feasible"
        return entry.verdict


def _classify_beginner_gates(
    profile: TSScientificProfileResolved,
    exercise: RankableExercise,
) -> list[str]:
    """Gate deterministici per profili beginner. Restituisce reason codes."""
    if profile.livello_workout != "beginner":
        return []

    reasons: list[str] = []
    if exercise.difficolta == "advanced":
        reasons.append("beginner_advanced_difficulty")

    lower_name = exercise.nome.lower()
    if any(token in lower_name for token in _BEGINNER_POWER_SKILL_TOKENS):
        reasons.append("beginner_power_skill_exercise")

    if (
        exercise.categoria == "cardio"
        and profile.obiettivo_scientifico.value != "resistenza"
    ):
        reasons.append("beginner_cardio_non_endurance")

    return reasons


def _resolve_pattern(exercise: RankableExercise) -> PatternMovimento | None:
    """Risolve il pattern_movimento stringa dell'esercizio al PatternMovimento enum."""
    try:
        return PatternMovimento(exercise.pattern_movimento)
    except ValueError:
        return None


def _classify_demand_ceiling(
    exercise: RankableExercise,
    protocol_id: str | None,
) -> tuple[FeasibilityVerdict, list[str], DemandPolicyResult | None]:
    """Verifica il demand vector dell'esercizio contro il ceiling del protocollo.

    Ritorna (verdict, reason_codes, policy_result).
    Se protocol_id e' None o non ha ceiling, ritorna feasible senza findings.
    """
    if protocol_id is None:
        return "feasible", [], None

    ceiling = get_protocol_ceiling(protocol_id)
    if ceiling is None:
        return "feasible", [], None

    pattern = _resolve_pattern(exercise)
    if pattern is None:
        return "feasible", [], None

    difficulty = exercise.difficolta or "intermediate"
    vector = get_default_demand_vector(pattern, difficulty)
    policy_result = check_demand_ceiling(vector, ceiling)

    reasons: list[str] = []
    if policy_result.violations_count > 0:
        reasons.append("demand_ceiling_exceeded")
    for ff in policy_result.family_findings:
        if ff.verdict == "family_excluded":
            reasons.append("demand_family_excluded")
        elif ff.verdict == "family_discouraged":
            reasons.append("demand_family_discouraged")

    if policy_result.is_hard_fail:
        return "infeasible_for_auto_draft", reasons, policy_result
    if policy_result.discouraged_count > 0:
        return "discouraged", reasons, policy_result
    return "feasible", reasons, policy_result


def _classify_safety(
    exercise: RankableExercise,
    safety_entries: dict[int, ExerciseSafetyEntry],
) -> tuple[FeasibilityVerdict, str | None, list[str]]:
    """Classifica ammissibilita' clinica via safety map."""
    entry = safety_entries.get(exercise.id)
    severity = entry.severity if entry is not None else None
    verdict = _SAFETY_TO_VERDICT[severity]
    reasons: list[str] = []
    if severity == "avoid":
        reasons.append("clinical_avoid")
    elif severity == "modify":
        reasons.append("clinical_modify_required")
    return verdict, severity, reasons


def _merge_verdicts(
    verdicts: list[FeasibilityVerdict],
) -> FeasibilityVerdict:
    """Worst-case merge: infeasible > discouraged > feasible."""
    if "infeasible_for_auto_draft" in verdicts:
        return "infeasible_for_auto_draft"
    if "discouraged" in verdicts:
        return "discouraged"
    return "feasible"


def compute_feasibility(
    *,
    exercises: list[RankableExercise],
    profile: TSScientificProfileResolved,
    safety_entries: dict[int, ExerciseSafetyEntry],
    protocol_id: str | None = None,
) -> FeasibilityReport:
    """Classifica ogni esercizio prima del ranking. Puro e deterministico.

    v2: protocol_id abilita il demand ceiling gate — ogni esercizio viene
    confrontato con il vettore biomeccanico 10D e il ceiling del protocollo.
    """
    entries: dict[int, ExerciseFeasibility] = {}
    feasible_count = 0
    discouraged_count = 0
    infeasible_count = 0
    demand_ceiling_violations = 0
    demand_family_exclusions = 0
    demand_family_discouraged = 0
    infeasible_by_beginner_gate = 0
    infeasible_by_safety = 0
    infeasible_by_demand = 0
    discouraged_by_safety = 0
    discouraged_by_demand = 0

    for exercise in exercises:
        reasons: list[str] = []
        partial_verdicts: list[FeasibilityVerdict] = []

        # Gate 1: beginner-specific constraints
        beginner_reasons = _classify_beginner_gates(profile, exercise)
        if beginner_reasons:
            reasons.extend(beginner_reasons)
            partial_verdicts.append("infeasible_for_auto_draft")

        # Gate 2: clinical safety
        safety_verdict, severity, safety_reasons = _classify_safety(exercise, safety_entries)
        reasons.extend(safety_reasons)
        partial_verdicts.append(safety_verdict)

        # Gate 3: demand ceiling (v2)
        demand_verdict, demand_reasons, demand_result = _classify_demand_ceiling(
            exercise, protocol_id,
        )
        reasons.extend(demand_reasons)
        partial_verdicts.append(demand_verdict)

        if demand_result is not None:
            demand_ceiling_violations += demand_result.violations_count
            for ff in demand_result.family_findings:
                if ff.verdict == "family_excluded":
                    demand_family_exclusions += 1
                elif ff.verdict == "family_discouraged":
                    demand_family_discouraged += 1

        final_verdict = _merge_verdicts(partial_verdicts) if partial_verdicts else "feasible"

        entries[exercise.id] = ExerciseFeasibility(
            exercise_id=exercise.id,
            verdict=final_verdict,
            reason_codes=tuple(reasons),
            safety_severity=severity,
            demand_policy_result=demand_result,
        )

        if final_verdict == "feasible":
            feasible_count += 1
        elif final_verdict == "discouraged":
            discouraged_count += 1
            if safety_verdict == "discouraged":
                discouraged_by_safety += 1
            if demand_verdict == "discouraged":
                discouraged_by_demand += 1
        else:
            infeasible_count += 1
            if beginner_reasons:
                infeasible_by_beginner_gate += 1
            if safety_verdict == "infeasible_for_auto_draft":
                infeasible_by_safety += 1
            if demand_verdict == "infeasible_for_auto_draft":
                infeasible_by_demand += 1

    return FeasibilityReport(
        entries=entries,
        feasible_count=feasible_count,
        discouraged_count=discouraged_count,
        infeasible_count=infeasible_count,
        demand_ceiling_violations=demand_ceiling_violations,
        demand_family_exclusions=demand_family_exclusions,
        demand_family_discouraged=demand_family_discouraged,
        infeasible_by_beginner_gate=infeasible_by_beginner_gate,
        infeasible_by_safety=infeasible_by_safety,
        infeasible_by_demand=infeasible_by_demand,
        discouraged_by_safety=discouraged_by_safety,
        discouraged_by_demand=discouraged_by_demand,
    )
