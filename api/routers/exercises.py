# api/routers/exercises.py
"""
CRUD + filtri per archivio esercizi.
v2: contenuto ricco, media upload, relazioni progressione/regressione.

Dual ownership:
- Builtin (trainer_id=NULL): visibili a tutti, NON modificabili/eliminabili
- Custom (trainer_id=X): CRUD completo per il trainer proprietario

Bouncer adattato: WHERE (trainer_id = ? OR trainer_id IS NULL) AND deleted_at IS NULL
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlmodel import Session, select, func, or_

from api.dependencies import get_current_trainer
from api.database import get_session
from api.models.exercise import Exercise
from api.models.exercise_media import ExerciseMedia
from api.models.exercise_relation import ExerciseRelation
from api.models.trainer import Trainer
from api.routers._audit import log_audit
from api.schemas.exercise import (
    ExerciseCreate,
    ExerciseListResponse,
    ExerciseMediaResponse,
    ExerciseRelationCreate,
    ExerciseRelationResponse,
    ExerciseResponse,
    ExerciseUpdate,
)

logger = logging.getLogger("fitmanager.api")

router = APIRouter(prefix="/exercises", tags=["exercises"])

# Media storage root
MEDIA_ROOT = Path(os.path.dirname(__file__)).parent.parent / "data" / "media" / "exercises"
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/webp",
    "video/mp4", "video/quicktime",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


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


def _to_response(exercise: Exercise, media: list | None = None, relazioni: list | None = None) -> ExerciseResponse:
    resp = ExerciseResponse.model_validate(exercise)
    if media is not None:
        resp.media = [ExerciseMediaResponse.model_validate(m) for m in media]
    if relazioni is not None:
        resp.relazioni = relazioni
    return resp


def _get_media(session: Session, exercise_id: int) -> list[ExerciseMedia]:
    return list(session.exec(
        select(ExerciseMedia)
        .where(ExerciseMedia.exercise_id == exercise_id)
        .order_by(ExerciseMedia.ordine, ExerciseMedia.id)
    ).all())


def _get_relazioni(session: Session, exercise_id: int) -> list[ExerciseRelationResponse]:
    rows = session.exec(
        select(ExerciseRelation, Exercise)
        .join(Exercise, ExerciseRelation.related_exercise_id == Exercise.id)
        .where(
            ExerciseRelation.exercise_id == exercise_id,
            Exercise.deleted_at == None,  # noqa: E711
        )
    ).all()
    return [
        ExerciseRelationResponse(
            id=rel.id,
            related_exercise_id=rel.related_exercise_id,
            related_exercise_nome=ex.nome,
            tipo_relazione=rel.tipo_relazione,
        )
        for rel, ex in rows
    ]


# JSON serialization helpers per campi v2
JSON_LIST_FIELDS = {
    "muscoli_primari", "muscoli_secondari", "controindicazioni",
    "coaching_cues", "errori_comuni",
}
JSON_DICT_FIELDS = {"istruzioni"}


def _serialize_field(field: str, value):
    """Serializza campi JSON list/dict per storage TEXT."""
    if field in JSON_LIST_FIELDS:
        return json.dumps(value or [], ensure_ascii=False)
    if field in JSON_DICT_FIELDS:
        return json.dumps(value, ensure_ascii=False) if value else None
    return value


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
    page_size: int = Query(default=1200, ge=1, le=2000),
):
    """Lista esercizi con filtri. Include builtin + custom del trainer."""
    query = select(Exercise).where(
        Exercise.deleted_at == None,  # noqa: E711
        or_(Exercise.trainer_id == trainer.id, Exercise.trainer_id == None),  # noqa: E711
    )

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
        query = query.where(Exercise.muscoli_primari.ilike(f'%"{muscolo}"%'))

    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

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
# GET SINGLE (enriched: media + relazioni)
# ═══════════════════════════════════════════════════════════════

@router.get("/{exercise_id}", response_model=ExerciseResponse)
def get_exercise(
    exercise_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Singolo esercizio per ID — enriched con media e relazioni."""
    exercise = _bouncer_exercise(session, exercise_id, trainer.id)
    media = _get_media(session, exercise_id)
    relazioni = _get_relazioni(session, exercise_id)
    return _to_response(exercise, media=media, relazioni=relazioni)


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
        force_type=data.force_type,
        lateral_pattern=data.lateral_pattern,
        muscoli_primari=json.dumps(data.muscoli_primari, ensure_ascii=False),
        muscoli_secondari=json.dumps(data.muscoli_secondari or [], ensure_ascii=False),
        attrezzatura=data.attrezzatura,
        difficolta=data.difficolta,
        rep_range_forza=data.rep_range_forza,
        rep_range_ipertrofia=data.rep_range_ipertrofia,
        rep_range_resistenza=data.rep_range_resistenza,
        ore_recupero=data.ore_recupero,
        descrizione_anatomica=data.descrizione_anatomica,
        descrizione_biomeccanica=data.descrizione_biomeccanica,
        setup=data.setup,
        esecuzione=data.esecuzione,
        respirazione=data.respirazione,
        tempo_consigliato=data.tempo_consigliato,
        coaching_cues=json.dumps(data.coaching_cues or [], ensure_ascii=False),
        errori_comuni=json.dumps(data.errori_comuni or [], ensure_ascii=False),
        note_sicurezza=data.note_sicurezza,
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

    for field, value in update_data.items():
        old_val = getattr(exercise, field)
        new_val = _serialize_field(field, value)

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


# ═══════════════════════════════════════════════════════════════
# MEDIA UPLOAD
# ═══════════════════════════════════════════════════════════════

@router.post("/{exercise_id}/media", response_model=ExerciseMediaResponse, status_code=status.HTTP_201_CREATED)
def upload_exercise_media(
    exercise_id: int,
    file: UploadFile,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Upload immagine/video per esercizio custom."""
    exercise = _bouncer_exercise(session, exercise_id, trainer.id)
    _guard_custom(exercise)

    # Validazione content-type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Tipo file non consentito. Accettati: JPEG, PNG, WebP, MP4",
        )

    # Leggi contenuto e verifica dimensione
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File troppo grande (max 50 MB)")

    # Determina tipo e estensione
    tipo = "video" if file.content_type.startswith("video/") else "image"
    ext_map = {
        "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp",
        "video/mp4": "mp4", "video/quicktime": "mov",
    }
    ext = ext_map.get(file.content_type, "bin")

    # Salva su disco
    media_dir = MEDIA_ROOT / str(exercise_id)
    media_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex[:12]}.{ext}"
    filepath = media_dir / filename
    filepath.write_bytes(content)

    # Conta media esistenti per ordine
    existing_count = session.exec(
        select(func.count(ExerciseMedia.id))
        .where(ExerciseMedia.exercise_id == exercise_id)
    ).one()

    # Crea record DB
    media = ExerciseMedia(
        exercise_id=exercise_id,
        trainer_id=trainer.id,
        tipo=tipo,
        url=f"/media/exercises/{exercise_id}/{filename}",
        ordine=existing_count,
        descrizione=file.filename,
    )
    session.add(media)
    log_audit(session, "exercise_media", exercise_id, "UPLOAD", trainer.id, {"file": filename})
    session.commit()
    session.refresh(media)
    return ExerciseMediaResponse.model_validate(media)


@router.delete("/{exercise_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise_media(
    exercise_id: int,
    media_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Elimina media di un esercizio custom."""
    exercise = _bouncer_exercise(session, exercise_id, trainer.id)
    _guard_custom(exercise)

    media = session.exec(
        select(ExerciseMedia).where(
            ExerciseMedia.id == media_id,
            ExerciseMedia.exercise_id == exercise_id,
        )
    ).first()
    if not media:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media non trovato")

    # Rimuovi file da disco (best-effort)
    file_path = MEDIA_ROOT.parent.parent.parent / media.url.lstrip("/")
    if file_path.exists():
        file_path.unlink()

    session.delete(media)
    log_audit(session, "exercise_media", exercise_id, "DELETE_MEDIA", trainer.id, {"media_id": media_id})
    session.commit()


# ═══════════════════════════════════════════════════════════════
# RELAZIONI (progressioni/regressioni)
# ═══════════════════════════════════════════════════════════════

@router.post("/{exercise_id}/relations", response_model=ExerciseRelationResponse, status_code=status.HTTP_201_CREATED)
def create_exercise_relation(
    exercise_id: int,
    data: ExerciseRelationCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Crea relazione tra esercizi (progressione/regressione/variante)."""
    exercise = _bouncer_exercise(session, exercise_id, trainer.id)
    _guard_custom(exercise)

    # Verifica che l'esercizio correlato esista
    related = _bouncer_exercise(session, data.related_exercise_id, trainer.id)

    # Verifica duplicato
    existing = session.exec(
        select(ExerciseRelation).where(
            ExerciseRelation.exercise_id == exercise_id,
            ExerciseRelation.related_exercise_id == data.related_exercise_id,
            ExerciseRelation.tipo_relazione == data.tipo_relazione,
        )
    ).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Relazione gia' esistente")

    relation = ExerciseRelation(
        exercise_id=exercise_id,
        related_exercise_id=data.related_exercise_id,
        tipo_relazione=data.tipo_relazione,
    )
    session.add(relation)
    log_audit(session, "exercise_relation", exercise_id, "CREATE_RELATION", trainer.id, {
        "related_id": data.related_exercise_id, "tipo": data.tipo_relazione,
    })
    session.commit()
    session.refresh(relation)

    return ExerciseRelationResponse(
        id=relation.id,
        related_exercise_id=relation.related_exercise_id,
        related_exercise_nome=related.nome,
        tipo_relazione=relation.tipo_relazione,
    )


@router.delete("/{exercise_id}/relations/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise_relation(
    exercise_id: int,
    relation_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Elimina relazione tra esercizi."""
    exercise = _bouncer_exercise(session, exercise_id, trainer.id)
    _guard_custom(exercise)

    relation = session.exec(
        select(ExerciseRelation).where(
            ExerciseRelation.id == relation_id,
            ExerciseRelation.exercise_id == exercise_id,
        )
    ).first()
    if not relation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Relazione non trovata")

    session.delete(relation)
    log_audit(session, "exercise_relation", exercise_id, "DELETE_RELATION", trainer.id, {
        "relation_id": relation_id,
    })
    session.commit()
