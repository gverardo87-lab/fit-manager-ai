"""Loader DB-aware del catalogo esercizi rankabile per SMART."""

from dataclasses import dataclass
import json

from sqlmodel import Session, select

from api.models.exercise import Exercise


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
        )
        for exercise in exercises
        if exercise.id is not None
    ]
