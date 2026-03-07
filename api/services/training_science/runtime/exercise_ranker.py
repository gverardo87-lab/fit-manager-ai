"""Ranker puro e deterministico per candidati esercizio slot-by-slot."""

from api.schemas.safety import ExerciseSafetyEntry
from api.schemas.training_science import (
    TSScientificProfileResolved,
    TSCanonicalSlot,
    TSSlotCandidate,
)
from .exercise_catalog import RankableExercise
from .mappings import MUSCLE_GROUP_TO_CATALOG, PATTERN_TO_CATALOG_PATTERNS

_SEVERITY_BUCKET = {
    None: "recommended",
    "caution": "allowed",
    "modify": "allowed",
    "avoid": "discouraged",
}
_SEVERITY_PENALTY = {None: 0, "caution": 20, "modify": 40, "avoid": 80}
_BUCKET_ORDER = {"recommended": 0, "allowed": 1, "discouraged": 2}
_LEVEL_DIFFICULTY_SCORE: dict[str, dict[str, int]] = {
    "beginner": {"beginner": 12, "intermediate": 4, "advanced": -8},
    "intermedio": {"beginner": 6, "intermediate": 12, "advanced": 5},
    "avanzato": {"beginner": 2, "intermediate": 8, "advanced": 12},
}


def _resolve_target_muscles(slot: TSCanonicalSlot) -> set[str]:
    if slot.muscolo_target is None:
        return set()
    return MUSCLE_GROUP_TO_CATALOG.get(slot.muscolo_target, set())


def _pattern_score(slot: TSCanonicalSlot, exercise: RankableExercise) -> int:
    allowed_patterns = PATTERN_TO_CATALOG_PATTERNS.get(slot.pattern, set())
    if exercise.pattern_movimento == slot.pattern.value:
        return 50
    if exercise.pattern_movimento in allowed_patterns:
        return 36
    return 0


def _muscle_score(slot: TSCanonicalSlot, exercise: RankableExercise) -> int:
    target_muscles = _resolve_target_muscles(slot)
    if not target_muscles:
        return 0
    primaries = set(exercise.muscoli_primari)
    secondaries = set(exercise.muscoli_secondari)
    if primaries & target_muscles:
        return 25
    if secondaries & target_muscles:
        return 12
    return 0


def _difficulty_score(profile: TSScientificProfileResolved, exercise: RankableExercise) -> int:
    return _LEVEL_DIFFICULTY_SCORE.get(profile.livello_workout, {}).get(exercise.difficolta, 0)


def _safety_adjustment(entry: ExerciseSafetyEntry | None) -> tuple[str | None, int, list[str], str | None]:
    severity = entry.severity if entry is not None else None
    rationale: list[str] = []
    adaptation_hint = None
    if severity == "avoid":
        rationale.append("clinical_risk_penalty")
        adaptation_hint = "Esercizio sconsigliato per il profilo clinico corrente."
    elif severity == "modify":
        rationale.append("clinical_modify_required")
        adaptation_hint = "Richiede adattamento tecnico o di ROM prima dell'uso."
    elif severity == "caution":
        rationale.append("clinical_caution")
        adaptation_hint = "Richiede monitoraggio tecnico-clinico ravvicinato."
    return severity, _SEVERITY_PENALTY[severity], rationale, adaptation_hint


def rank_slot_candidates(
    *,
    slot: TSCanonicalSlot,
    profile: TSScientificProfileResolved,
    exercises: list[RankableExercise],
    safety_entries: dict[int, ExerciseSafetyEntry],
    excluded_exercise_ids: set[int],
    preferred_exercise_ids: set[int],
    pinned_exercise_id: int | None,
    limit: int = 8,
) -> list[TSSlotCandidate]:
    """Ordina i candidati per slot con tie-break stabile e zero random."""
    scored: list[TSSlotCandidate] = []
    for exercise in exercises:
        if exercise.id in excluded_exercise_ids:
            continue

        pattern_score = _pattern_score(slot, exercise)
        if pattern_score <= 0:
            continue

        muscle_score = _muscle_score(slot, exercise)
        difficulty_score = _difficulty_score(profile, exercise)
        preference_bonus = 6 if exercise.id in preferred_exercise_ids else 0
        pin_bonus = 100 if pinned_exercise_id == exercise.id else 0

        safety_entry = safety_entries.get(exercise.id)
        severity, safety_penalty, safety_rationale, adaptation_hint = _safety_adjustment(safety_entry)

        total_score = max(
            0,
            pattern_score + muscle_score + difficulty_score + preference_bonus + pin_bonus - safety_penalty,
        )
        bucket = _SEVERITY_BUCKET[severity]
        rationale = ["pattern_match"]
        if muscle_score > 0:
            rationale.append("muscle_target_match")
        if difficulty_score > 0:
            rationale.append("difficulty_alignment")
        if preference_bonus > 0:
            rationale.append("trainer_preference")
        rationale.extend(safety_rationale)

        scored.append(
            TSSlotCandidate(
                slot_id=slot.slot_id,
                exercise_id=exercise.id,
                rank=0,
                total_score=total_score,
                safety_severity=severity,
                bucket=bucket,
                rationale=rationale,
                adaptation_hint=adaptation_hint,
            )
        )

    scored.sort(
        key=lambda item: (
            _BUCKET_ORDER[item.bucket],
            -item.total_score,
            item.exercise_id,
        )
    )
    for index, candidate in enumerate(scored, start=1):
        candidate.rank = index
    return scored[:limit]
