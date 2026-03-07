"""Loader DB-aware del catalogo esercizi rankabile per SMART."""

from dataclasses import dataclass
import json

from sqlmodel import Session, select

from api.models.exercise import Exercise
from api.services.training_science.demand.demand_registry import get_default_demand_vector
from api.services.training_science.demand.demand_types import ExerciseDemandVector
from api.services.training_science.types import PatternMovimento


@dataclass(frozen=True)
class RankableExercise:
    """Vista normalizzata minima per il ranker deterministico."""

    id: int
    nome: str
    pattern_movimento: str
    difficolta: str
    categoria: str
    attrezzatura: str
    rep_range_forza: str | None
    rep_range_ipertrofia: str | None
    rep_range_resistenza: str | None
    muscoli_primari: tuple[str, ...]
    muscoli_secondari: tuple[str, ...]

    # Demand Vector 10D — None = usa default da demand_registry
    skill_demand: int | None = None
    coordination_demand: int | None = None
    stability_demand: int | None = None
    ballistic_demand: int | None = None
    impact_demand: int | None = None
    axial_load_demand: int | None = None
    shoulder_complex_demand: int | None = None
    lumbar_load_demand: int | None = None
    grip_demand: int | None = None
    metabolic_demand: int | None = None


def _parse_muscles(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return ()
    try:
        payload = json.loads(raw_value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return ()
    if not isinstance(payload, list):
        return ()
    items = []
    for value in payload:
        if isinstance(value, str) and value:
            items.append(value.strip().lower())
    return tuple(items)


def load_rankable_exercises(session: Session, trainer_id: int) -> list[RankableExercise]:
    """Carica gli esercizi builtin + custom del trainer, senza leak multi-tenant."""
    statement = (
        select(Exercise)
        .where(Exercise.deleted_at.is_(None))
        .where(Exercise.in_subset.is_(True))
        .where((Exercise.is_builtin.is_(True)) | (Exercise.trainer_id == trainer_id))
        .order_by(Exercise.nome)
    )
    exercises = session.exec(statement).all()
    return [
        RankableExercise(
            id=exercise.id,
            nome=exercise.nome,
            pattern_movimento=exercise.pattern_movimento,
            difficolta=exercise.difficolta,
            categoria=exercise.categoria,
            attrezzatura=exercise.attrezzatura,
            rep_range_forza=exercise.rep_range_forza,
            rep_range_ipertrofia=exercise.rep_range_ipertrofia,
            rep_range_resistenza=exercise.rep_range_resistenza,
            muscoli_primari=_parse_muscles(exercise.muscoli_primari),
            muscoli_secondari=_parse_muscles(exercise.muscoli_secondari),
            skill_demand=exercise.skill_demand,
            coordination_demand=exercise.coordination_demand,
            stability_demand=exercise.stability_demand,
            ballistic_demand=exercise.ballistic_demand,
            impact_demand=exercise.impact_demand,
            axial_load_demand=exercise.axial_load_demand,
            shoulder_complex_demand=exercise.shoulder_complex_demand,
            lumbar_load_demand=exercise.lumbar_load_demand,
            grip_demand=exercise.grip_demand,
            metabolic_demand=exercise.metabolic_demand,
        )
        for exercise in exercises
        if exercise.id is not None
    ]


_DEMAND_FIELDS = (
    "skill_demand", "coordination_demand", "stability_demand",
    "ballistic_demand", "impact_demand", "axial_load_demand",
    "shoulder_complex_demand", "lumbar_load_demand",
    "grip_demand", "metabolic_demand",
)


def resolve_demand_vector(exercise: RankableExercise) -> ExerciseDemandVector:
    """Build ExerciseDemandVector from DB fields, fallback to registry default.

    If ALL 10 DB fields are None, uses the pattern×difficulty default.
    If any DB field is populated, uses DB values (None fields treated as 0).
    """
    has_db_data = any(
        getattr(exercise, f) is not None for f in _DEMAND_FIELDS
    )

    if has_db_data:
        return ExerciseDemandVector(
            **{f: getattr(exercise, f) or 0 for f in _DEMAND_FIELDS},
            evidence_class="B_biomechanical_inference",
            source_anchors=("DB-per-exercise",),
        )

    # Fallback to registry default
    try:
        pattern = PatternMovimento(exercise.pattern_movimento)
    except ValueError:
        pattern = None

    if pattern is not None:
        return get_default_demand_vector(pattern, exercise.difficolta or "intermediate")

    # Unknown pattern — conservative fallback
    return ExerciseDemandVector(
        skill_demand=1, coordination_demand=1, stability_demand=1,
        ballistic_demand=0, impact_demand=0, axial_load_demand=1,
        shoulder_complex_demand=1, lumbar_load_demand=1,
        grip_demand=1, metabolic_demand=1,
        evidence_class="C_provisional_expert_model",
    )
