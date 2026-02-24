# api/routers/exercises.py
"""
CRUD + filtri per archivio esercizi.

Dual ownership:
- Builtin (trainer_id=NULL): visibili a tutti, NON modificabili/eliminabili
- Custom (trainer_id=X): CRUD completo per il trainer proprietario

Bouncer adattato: WHERE (trainer_id = ? OR trainer_id IS NULL) AND deleted_at IS NULL
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func, or_

from api.dependencies import get_current_trainer
from api.database import get_session
from api.models.exercise import Exercise
from api.models.trainer import Trainer
from api.routers._audit import log_audit
from api.schemas.exercise import (
    ExerciseCreate,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseUpdate,
)

logger = logging.getLogger("fitmanager.api")

router = APIRouter(prefix="/exercises", tags=["exercises"])


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _bouncer_exercise(session: Session, exercise_id: int, trainer_id: int) -> Exercise:
    """Trova esercizio: (trainer_id match) OR (builtin). 404 se non trovato."""
    exercise = session.exec(
        select(Exercise).where(
            Exercise.id == exercise_id,
            Exercise.deleted_at == None,  # noqa: E711
            or_(Exercise.trainer_id == trainer_id, Exercise.trainer_id == None),  # noqa: E711
        )
    ).first()
    if not exercise:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Esercizio non trovato")
    return exercise


def _guard_custom(exercise: Exercise) -> None:
    """Blocca modifica/eliminazione su builtin."""
    if exercise.is_builtin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esercizio builtin non modificabile")


def _to_response(exercise: Exercise) -> ExerciseResponse:
    return ExerciseResponse.model_validate(exercise)


# ═══════════════════════════════════════════════════════════════
# LIST
# ═══════════════════════════════════════════════════════════════

@router.get("", response_model=ExerciseListResponse)
def list_exercises(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    search: Optional[str] = Query(None, description="Ricerca per nome"),
    categoria: Optional[str] = Query(None),
    attrezzatura: Optional[str] = Query(None),
    difficolta: Optional[str] = Query(None),
    pattern_movimento: Optional[str] = Query(None),
    muscolo: Optional[str] = Query(None, description="Filtra per muscolo primario"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=200, ge=1, le=500),
):
    """Lista esercizi con filtri. Include builtin + custom del trainer."""
    # Base: builtin + custom del trainer, non eliminati
    query = select(Exercise).where(
        Exercise.deleted_at == None,  # noqa: E711
        or_(Exercise.trainer_id == trainer.id, Exercise.trainer_id == None),  # noqa: E711
    )

    # Filtri
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(Exercise.nome.ilike(pattern), Exercise.nome_en.ilike(pattern))
        )
    if categoria:
        query = query.where(Exercise.categoria == categoria)
    if attrezzatura:
        query = query.where(Exercise.attrezzatura == attrezzatura)
    if difficolta:
        query = query.where(Exercise.difficolta == difficolta)
    if pattern_movimento:
        query = query.where(Exercise.pattern_movimento == pattern_movimento)
    if muscolo:
        # Cerca dentro il JSON array (e.g. muscoli_primari contiene "glutes")
        query = query.where(Exercise.muscoli_primari.ilike(f'%"{muscolo}"%'))

    # Count totale (per paginazione)
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    # Fetch paginato
    offset = (page - 1) * page_size
    exercises = session.exec(
        query.order_by(Exercise.nome).offset(offset).limit(page_size)
    ).all()

    return ExerciseListResponse(
        items=[_to_response(e) for e in exercises],
        total=total,
        page=page,
        page_size=page_size,
    )


# ═══════════════════════════════════════════════════════════════
# GET SINGLE
# ═══════════════════════════════════════════════════════════════

@router.get("/{exercise_id}", response_model=ExerciseResponse)
def get_exercise(
    exercise_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Singolo esercizio per ID."""
    exercise = _bouncer_exercise(session, exercise_id, trainer.id)
    return _to_response(exercise)


# ═══════════════════════════════════════════════════════════════
# CREATE
# ═══════════════════════════════════════════════════════════════

@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
def create_exercise(
    data: ExerciseCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Crea esercizio custom. trainer_id iniettato da JWT."""
    exercise = Exercise(
        trainer_id=trainer.id,
        nome=data.nome,
        nome_en=data.nome_en,
        categoria=data.categoria,
        pattern_movimento=data.pattern_movimento,
        muscoli_primari=json.dumps(data.muscoli_primari, ensure_ascii=False),
        muscoli_secondari=json.dumps(data.muscoli_secondari or [], ensure_ascii=False),
        attrezzatura=data.attrezzatura,
        difficolta=data.difficolta,
        rep_range_forza=data.rep_range_forza,
        rep_range_ipertrofia=data.rep_range_ipertrofia,
        rep_range_resistenza=data.rep_range_resistenza,
        ore_recupero=data.ore_recupero,
        istruzioni=json.dumps(data.istruzioni, ensure_ascii=False) if data.istruzioni else None,
        controindicazioni=json.dumps(data.controindicazioni or [], ensure_ascii=False),
        is_builtin=False,
    )
    session.add(exercise)
    session.flush()
    log_audit(session, "exercise", exercise.id, "CREATE", trainer.id)
    session.commit()
    session.refresh(exercise)
    return _to_response(exercise)


# ═══════════════════════════════════════════════════════════════
# UPDATE
# ═══════════════════════════════════════════════════════════════

@router.put("/{exercise_id}", response_model=ExerciseResponse)
def update_exercise(
    exercise_id: int,
    data: ExerciseUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Aggiorna esercizio custom. Blocca su builtin."""
    exercise = _bouncer_exercise(session, exercise_id, trainer.id)
    _guard_custom(exercise)

    update_data = data.model_dump(exclude_unset=True)
    changes: dict = {}

    # Campi JSON: converti List/Dict in JSON string
    json_list_fields = {"muscoli_primari", "muscoli_secondari", "controindicazioni"}
    json_dict_fields = {"istruzioni"}

    for field, value in update_data.items():
        old_val = getattr(exercise, field)

        if field in json_list_fields:
            new_val = json.dumps(value or [], ensure_ascii=False)
        elif field in json_dict_fields:
            new_val = json.dumps(value, ensure_ascii=False) if value else None
        else:
            new_val = value

        if new_val != old_val:
            changes[field] = {"old": old_val, "new": new_val}

        setattr(exercise, field, new_val)

    log_audit(session, "exercise", exercise.id, "UPDATE", trainer.id, changes or None)
    session.add(exercise)
    session.commit()
    session.refresh(exercise)
    return _to_response(exercise)


# ═══════════════════════════════════════════════════════════════
# DELETE
# ═══════════════════════════════════════════════════════════════

@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    exercise_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Soft-delete esercizio custom. Blocca su builtin."""
    exercise = _bouncer_exercise(session, exercise_id, trainer.id)
    _guard_custom(exercise)

    exercise.deleted_at = datetime.now(timezone.utc)
    session.add(exercise)
    log_audit(session, "exercise", exercise.id, "DELETE", trainer.id)
    session.commit()
