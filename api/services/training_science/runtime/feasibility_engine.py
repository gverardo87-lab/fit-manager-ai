"""Feasibility Engine v1 — classificazione pre-ranking degli esercizi.

Separa la logica di ammissibilita' (puo'/non-puo' entrare nel draft)
dalla logica di ordinamento (quale esercizio e' migliore per lo slot).

Il ranker riceve solo esercizi gia' classificati e non fa piu' gate autonomi.
Ogni verdetto e' deterministico, spiegabile e testabile.
"""

from dataclasses import dataclass, field
from typing import Literal

from api.schemas.safety import ExerciseSafetyEntry
from api.schemas.training_science import TSScientificProfileResolved
from .exercise_catalog import RankableExercise

FEASIBILITY_ENGINE_VERSION = "smart-feasibility-v1"

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


@dataclass(frozen=True)
class FeasibilityReport:
    """Report completo di ammissibilita' per l'intero catalogo pre-ranking."""

    entries: dict[int, ExerciseFeasibility] = field(default_factory=dict)
    feasible_count: int = 0
    discouraged_count: int = 0
    infeasible_count: int = 0

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
) -> FeasibilityReport:
    """Classifica ogni esercizio prima del ranking. Puro e deterministico."""
    entries: dict[int, ExerciseFeasibility] = {}
    feasible_count = 0
    discouraged_count = 0
    infeasible_count = 0

    for exercise in exercises:
        reasons: list[str] = []
        partial_verdicts: list[FeasibilityVerdict] = []

        beginner_reasons = _classify_beginner_gates(profile, exercise)
        if beginner_reasons:
            reasons.extend(beginner_reasons)
            partial_verdicts.append("infeasible_for_auto_draft")

        safety_verdict, severity, safety_reasons = _classify_safety(exercise, safety_entries)
        reasons.extend(safety_reasons)
        partial_verdicts.append(safety_verdict)

        final_verdict = _merge_verdicts(partial_verdicts) if partial_verdicts else "feasible"

        entries[exercise.id] = ExerciseFeasibility(
            exercise_id=exercise.id,
            verdict=final_verdict,
            reason_codes=tuple(reasons),
            safety_severity=severity,
        )

        if final_verdict == "feasible":
            feasible_count += 1
        elif final_verdict == "discouraged":
            discouraged_count += 1
        else:
            infeasible_count += 1

    return FeasibilityReport(
        entries=entries,
        feasible_count=feasible_count,
        discouraged_count=discouraged_count,
        infeasible_count=infeasible_count,
    )
