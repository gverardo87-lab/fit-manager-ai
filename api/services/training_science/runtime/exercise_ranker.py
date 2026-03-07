"""Ranker puro e deterministico per candidati esercizio slot-by-slot."""

from collections import Counter
from dataclasses import dataclass, field

from api.schemas.safety import ExerciseSafetyEntry
from api.schemas.training_science import (
    TSScientificProfileResolved,
    TSCanonicalSlot,
    TSSlotCandidate,
)
from api.services.training_science.demand.demand_registry import (
    get_protocol_ceiling,
)

from .exercise_catalog import RankableExercise, resolve_demand_vector
from .feasibility_engine import (
    FeasibilityReport,
    _BEGINNER_POWER_SKILL_TOKENS,
)
from .mappings import MUSCLE_GROUP_TO_CATALOG, PATTERN_TO_CATALOG_PATTERNS

_SEVERITY_BUCKET = {
    None: "recommended",
    "caution": "allowed",
    "modify": "allowed",
    "avoid": "discouraged",
}
_SEVERITY_PENALTY = {None: 0, "caution": 20, "modify": 40, "avoid": 80}
_BUCKET_ORDER = {"recommended": 0, "allowed": 1, "discouraged": 2}
_FREQUENCY_BONUS_CAP = 12
_RECOVERY_PENALTY_CAP = 12
_LEVEL_DIFFICULTY_SCORE: dict[str, dict[str, int]] = {
    "beginner": {"beginner": 12, "intermediate": 2, "advanced": -24},
    "intermedio": {"beginner": 6, "intermediate": 12, "advanced": 5},
    "avanzato": {"beginner": 2, "intermediate": 8, "advanced": 12},
}
_QUAD_MUSCLES = {"quadriceps", "quads", "quadricipiti"}
_HAMSTRINGS_MUSCLES = {"hamstrings", "femorali"}
_PATTERN_BALANCE_PAIRS = (
    ("push_h", "push_v"),
    ("pull_h", "pull_v"),
)
_RECOVERY_SENSITIVE_MUSCLES = {
    "back",
    "lats",
    "dorsali",
    "traps",
    "trapezius",
    "trapezio",
    "core",
    "abs",
    "abdominals",
}
_OBJECTIVE_REP_RANGE_ATTR = {
    "forza": "rep_range_forza",
    "ipertrofia": "rep_range_ipertrofia",
    "tonificazione": "rep_range_ipertrofia",
    "dimagrimento": "rep_range_ipertrofia",
    "resistenza": "rep_range_resistenza",
}
@dataclass
class RankerSelectionState:
    """Stato incrementale del ranking per introdurre feedback settimanale."""

    selected_pattern_counts: Counter[str] = field(default_factory=Counter)
    selected_muscle_counts: Counter[str] = field(default_factory=Counter)
    selected_exercise_ids: set[int] = field(default_factory=set)
    previous_session_muscles: set[str] = field(default_factory=set)
    current_session_muscles: set[str] = field(default_factory=set)

    def start_session(self) -> None:
        self.current_session_muscles = set()

    def finish_session(self) -> None:
        self.previous_session_muscles = set(self.current_session_muscles)
        self.current_session_muscles = set()

    def register_selected_exercise(self, exercise: RankableExercise) -> None:
        self.selected_pattern_counts[exercise.pattern_movimento] += 1
        for muscle in _candidate_muscles(exercise):
            self.selected_muscle_counts[muscle] += 1
        self.selected_exercise_ids.add(exercise.id)
        self.current_session_muscles.update(
            _candidate_muscles(exercise) & _RECOVERY_SENSITIVE_MUSCLES
        )


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


def _candidate_muscles(exercise: RankableExercise) -> set[str]:
    return set(exercise.muscoli_primari) | set(exercise.muscoli_secondari)


def _objective_alignment_adjustment(
    profile: TSScientificProfileResolved,
    exercise: RankableExercise,
) -> tuple[int, list[str]]:
    objective_key = profile.obiettivo_scientifico.value
    rep_range_attr = _OBJECTIVE_REP_RANGE_ATTR.get(objective_key)
    rationale: list[str] = []

    if rep_range_attr and getattr(exercise, rep_range_attr):
        rationale.append("objective_rep_range_alignment")
        return 8, rationale

    penalty = 0
    if rep_range_attr is not None:
        penalty += 12
        rationale.append("objective_rep_range_missing")

    if profile.livello_workout == "beginner" and exercise.categoria == "cardio":
        penalty += 12
        rationale.append("beginner_cardio_slot_penalty")

    lower_name = exercise.nome.lower()
    if profile.livello_workout == "beginner" and any(
        token in lower_name for token in _BEGINNER_POWER_SKILL_TOKENS
    ):
        penalty += 18
        rationale.append("beginner_power_skill_penalty")

    return -penalty, rationale


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


def _pattern_balance_adjustment(
    exercise: RankableExercise,
    state: RankerSelectionState | None,
) -> tuple[int, list[str]]:
    if state is None:
        return 0, []

    rationale: list[str] = []
    bonus = 0
    penalty = 0
    for primary_pattern, alternate_pattern in _PATTERN_BALANCE_PAIRS:
        if exercise.pattern_movimento not in {primary_pattern, alternate_pattern}:
            continue

        primary_count = state.selected_pattern_counts[primary_pattern]
        alternate_count = state.selected_pattern_counts[alternate_pattern]
        delta = primary_count - alternate_count

        if exercise.pattern_movimento == alternate_pattern and delta > 0:
            bonus += min(10, delta * 4)
            rationale.append("weekly_pattern_rebalance")
        elif exercise.pattern_movimento == primary_pattern and delta >= 1:
            penalty += min(10, delta * 4)
            rationale.append("weekly_pattern_penalty")

    return bonus - penalty, rationale


def _quad_ham_adjustment(
    exercise: RankableExercise,
    state: RankerSelectionState | None,
) -> tuple[int, list[str]]:
    if state is None:
        return 0, []

    muscles = _candidate_muscles(exercise)
    quad_count = sum(state.selected_muscle_counts[muscle] for muscle in _QUAD_MUSCLES)
    ham_count = sum(state.selected_muscle_counts[muscle] for muscle in _HAMSTRINGS_MUSCLES)

    is_quad = exercise.pattern_movimento == "squat" or bool(muscles & _QUAD_MUSCLES)
    is_ham = exercise.pattern_movimento == "hinge" or bool(muscles & _HAMSTRINGS_MUSCLES)

    rationale: list[str] = []
    if is_ham and quad_count > ham_count:
        rationale.append("posterior_chain_rebalance")
        return min(10, (quad_count - ham_count) * 3), rationale
    if is_quad and ham_count + 1 < quad_count:
        rationale.append("quad_dominance_penalty")
        return -min(8, (quad_count - ham_count) * 2), rationale
    return 0, rationale


def _frequency_adjustment(
    exercise: RankableExercise,
    state: RankerSelectionState | None,
) -> tuple[int, list[str]]:
    if state is None:
        return 0, []

    muscles = _candidate_muscles(exercise)
    bonus = 0
    rationale: list[str] = []

    if muscles & _HAMSTRINGS_MUSCLES:
        ham_count = sum(state.selected_muscle_counts[muscle] for muscle in _HAMSTRINGS_MUSCLES)
        if ham_count < 2:
            bonus += min(_FREQUENCY_BONUS_CAP, (2 - ham_count) * 6)
            rationale.append("frequency_boost_hamstrings")

    if "bicipiti" in muscles or "biceps" in muscles:
        biceps_count = state.selected_muscle_counts["bicipiti"] + state.selected_muscle_counts["biceps"]
        if biceps_count < 2:
            bonus += min(_FREQUENCY_BONUS_CAP, (2 - biceps_count) * 5)
            rationale.append("frequency_boost_biceps")

    return bonus, rationale


def _recovery_adjustment(
    exercise: RankableExercise,
    state: RankerSelectionState | None,
) -> tuple[int, list[str]]:
    if state is None or not state.previous_session_muscles:
        return 0, []

    overlap = _candidate_muscles(exercise) & state.previous_session_muscles & _RECOVERY_SENSITIVE_MUSCLES
    if not overlap:
        return 0, []
    return -min(_RECOVERY_PENALTY_CAP, len(overlap) * 4), ["recovery_overlap_penalty"]


def _uniqueness_adjustment(
    exercise: RankableExercise,
    state: RankerSelectionState | None,
) -> tuple[int, list[str]]:
    if state is None or exercise.id not in state.selected_exercise_ids:
        return 0, []
    return -25, ["weekly_uniqueness_penalty"]


_DEMAND_DIMENSIONS = (
    "skill_demand", "coordination_demand", "stability_demand",
    "ballistic_demand", "impact_demand", "axial_load_demand",
    "shoulder_complex_demand", "lumbar_load_demand", "grip_demand",
    "metabolic_demand",
)
_DEMAND_PROXIMITY_MAX = 15


def _demand_proximity_score(
    exercise: RankableExercise,
    protocol_id: str | None,
) -> tuple[int, list[str]]:
    """Bonus proporzionale alla distanza dal ceiling (headroom).

    Esercizi con piu' margine rispetto ai limiti del protocollo ricevono un
    bonus fino a _DEMAND_PROXIMITY_MAX punti. Puro e deterministico.
    """
    if protocol_id is None:
        return 0, []
    ceiling = get_protocol_ceiling(protocol_id)
    if ceiling is None:
        return 0, []
    vector = resolve_demand_vector(exercise)
    total_headroom = 0
    constrained_dims = 0
    for dim in _DEMAND_DIMENSIONS:
        max_val = getattr(ceiling, f"max_{dim}", None)
        if max_val is None:
            continue
        constrained_dims += 1
        headroom = max_val - getattr(vector, dim)
        total_headroom += max(0, headroom)

    if constrained_dims == 0:
        return 0, []

    normalized = total_headroom / (constrained_dims * 4)
    bonus = round(normalized * _DEMAND_PROXIMITY_MAX)
    if bonus > 0:
        return bonus, ["demand_headroom_bonus"]
    return 0, []


def rank_slot_candidates(
    *,
    slot: TSCanonicalSlot,
    profile: TSScientificProfileResolved,
    exercises: list[RankableExercise],
    safety_entries: dict[int, ExerciseSafetyEntry],
    excluded_exercise_ids: set[int],
    preferred_exercise_ids: set[int],
    pinned_exercise_id: int | None,
    feasibility: FeasibilityReport | None = None,
    selection_state: RankerSelectionState | None = None,
    protocol_id: str | None = None,
    limit: int = 8,
) -> list[TSSlotCandidate]:
    """Ordina i candidati per slot con tie-break stabile e zero random.

    Se ``feasibility`` e' fornito, gli esercizi ``infeasible_for_auto_draft``
    vengono esclusi dal draft automatico (a meno che non siano pinned/preferred).
    Il ranker non fa piu' gate autonomi sulla suitability.

    v2: ``protocol_id`` abilita il demand proximity bonus — esercizi con
    piu' headroom rispetto al ceiling del protocollo ricevono un bonus.
    """
    has_feasible_pattern_options = feasibility is not None and any(
        exercise.id not in excluded_exercise_ids
        and _pattern_score(slot, exercise) > 0
        and feasibility.is_feasible(exercise.id)
        for exercise in exercises
    )

    scored_payloads: list[dict[str, object]] = []
    for exercise in exercises:
        if exercise.id in excluded_exercise_ids:
            continue

        pattern_score = _pattern_score(slot, exercise)
        if pattern_score <= 0:
            continue

        if (
            feasibility is not None
            and has_feasible_pattern_options
            and feasibility.get_verdict(exercise.id) == "infeasible_for_auto_draft"
            and pinned_exercise_id != exercise.id
            and exercise.id not in preferred_exercise_ids
        ):
            continue

        muscle_score = _muscle_score(slot, exercise)
        difficulty_score = _difficulty_score(profile, exercise)
        objective_score, objective_rationale = _objective_alignment_adjustment(profile, exercise)
        preference_bonus = 6 if exercise.id in preferred_exercise_ids else 0
        pin_bonus = 100 if pinned_exercise_id == exercise.id else 0

        safety_entry = safety_entries.get(exercise.id)
        severity, safety_penalty, safety_rationale, adaptation_hint = _safety_adjustment(safety_entry)
        pattern_balance_score, pattern_balance_rationale = _pattern_balance_adjustment(
            exercise, selection_state
        )
        quad_ham_score, quad_ham_rationale = _quad_ham_adjustment(exercise, selection_state)
        frequency_score, frequency_rationale = _frequency_adjustment(exercise, selection_state)
        recovery_score, recovery_rationale = _recovery_adjustment(exercise, selection_state)
        uniqueness_score, uniqueness_rationale = _uniqueness_adjustment(exercise, selection_state)
        demand_score, demand_rationale = _demand_proximity_score(exercise, protocol_id)

        total_score = max(
            0,
            pattern_score
            + muscle_score
            + difficulty_score
            + objective_score
            + preference_bonus
            + pin_bonus
            + pattern_balance_score
            + quad_ham_score
            + frequency_score
            + recovery_score
            + uniqueness_score
            + demand_score
            - safety_penalty,
        )
        bucket = _SEVERITY_BUCKET[severity]
        rationale = ["pattern_match"]
        if muscle_score > 0:
            rationale.append("muscle_target_match")
        if difficulty_score > 0:
            rationale.append("difficulty_alignment")
        rationale.extend(objective_rationale)
        if preference_bonus > 0:
            rationale.append("trainer_preference")
        rationale.extend(safety_rationale)
        rationale.extend(pattern_balance_rationale)
        rationale.extend(quad_ham_rationale)
        rationale.extend(frequency_rationale)
        rationale.extend(recovery_rationale)
        rationale.extend(uniqueness_rationale)
        rationale.extend(demand_rationale)

        scored_payloads.append(
            {
                "slot_id": slot.slot_id,
                "exercise_id": exercise.id,
                "total_score": total_score,
                "safety_severity": severity,
                "bucket": bucket,
                "rationale": rationale,
                "adaptation_hint": adaptation_hint,
            }
        )

    scored_payloads.sort(
        key=lambda item: (
            _BUCKET_ORDER[str(item["bucket"])],
            -float(item["total_score"]),
            int(item["exercise_id"]),
        )
    )
    return [
        TSSlotCandidate(rank=index, **payload)
        for index, payload in enumerate(scored_payloads[:limit], start=1)
    ]
