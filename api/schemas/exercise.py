# api/schemas/exercise.py
"""
Pydantic schemas per gli esercizi.

v2: campi ricchi (anatomia, biomeccanica, esecuzione, coaching, media, relazioni).

ExerciseCreate / ExerciseUpdate: input validation + Mass Assignment Prevention.
ExerciseResponse / ExerciseListResponse: output serialization con JSON→List parsing.
ExerciseMediaResponse / ExerciseRelationResponse: sub-entity response.
"""

import json
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════════
# ENUMS VALIDI
# ═══════════════════════════════════════════════════════════════

VALID_CATEGORIES = {"compound", "isolation", "bodyweight", "cardio", "stretching", "mobilita", "avviamento"}
VALID_PATTERNS = {"squat", "hinge", "push_h", "push_v", "pull_h", "pull_v", "core", "rotation", "carry", "stretch", "mobility", "warmup"}
VALID_EQUIPMENT = {"barbell", "dumbbell", "cable", "machine", "bodyweight", "kettlebell", "band", "trx"}
VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced"}
VALID_MUSCLES = {
    "quadriceps", "hamstrings", "glutes", "calves", "adductors",
    "chest", "back", "lats", "shoulders", "traps",
    "biceps", "triceps", "forearms", "core",
}
VALID_FORCE_TYPES = {"push", "pull", "static"}
VALID_LATERAL_PATTERNS = {"bilateral", "unilateral", "alternating"}
VALID_RELATION_TYPES = {"progression", "regression", "variation"}
VALID_MEDIA_TYPES = {"image", "video"}


# ═══════════════════════════════════════════════════════════════
# CREATE
# ═══════════════════════════════════════════════════════════════

class ExerciseCreate(BaseModel):
    """Crea esercizio custom. trainer_id iniettato da JWT."""
    model_config = {"extra": "forbid"}

    # Identita'
    nome: str = Field(min_length=1, max_length=200)
    nome_en: Optional[str] = Field(None, max_length=200)

    # Classificazione
    categoria: str
    pattern_movimento: str
    force_type: Optional[str] = None
    lateral_pattern: Optional[str] = None

    # Muscoli
    muscoli_primari: List[str] = Field(min_length=1)
    muscoli_secondari: Optional[List[str]] = None

    # Setup
    attrezzatura: str
    difficolta: str
    rep_range_forza: Optional[str] = Field(None, max_length=20)
    rep_range_ipertrofia: Optional[str] = Field(None, max_length=20)
    rep_range_resistenza: Optional[str] = Field(None, max_length=20)
    ore_recupero: int = Field(default=48, ge=1, le=96)

    # Contenuto ricco (v2)
    descrizione_anatomica: Optional[str] = None
    descrizione_biomeccanica: Optional[str] = None
    setup: Optional[str] = None
    esecuzione: Optional[str] = None
    respirazione: Optional[str] = None
    tempo_consigliato: Optional[str] = Field(None, max_length=20)
    coaching_cues: Optional[List[str]] = None
    errori_comuni: Optional[List[dict[str, str]]] = None
    note_sicurezza: Optional[str] = None
    controindicazioni: Optional[List[str]] = None

    # Legacy (deprecato v2, accettato per backward compat)
    istruzioni: Optional[dict[str, Any]] = None

    @field_validator("categoria")
    @classmethod
    def validate_categoria(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Categoria invalida. Valide: {sorted(VALID_CATEGORIES)}")
        return v

    @field_validator("pattern_movimento")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        if v not in VALID_PATTERNS:
            raise ValueError(f"Pattern invalido. Validi: {sorted(VALID_PATTERNS)}")
        return v

    @field_validator("attrezzatura")
    @classmethod
    def validate_attrezzatura(cls, v: str) -> str:
        if v not in VALID_EQUIPMENT:
            raise ValueError(f"Attrezzatura invalida. Valide: {sorted(VALID_EQUIPMENT)}")
        return v

    @field_validator("difficolta")
    @classmethod
    def validate_difficolta(cls, v: str) -> str:
        if v not in VALID_DIFFICULTIES:
            raise ValueError(f"Difficolta' invalida. Valide: {sorted(VALID_DIFFICULTIES)}")
        return v

    @field_validator("force_type")
    @classmethod
    def validate_force_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_FORCE_TYPES:
            raise ValueError(f"Tipo forza invalido. Validi: {sorted(VALID_FORCE_TYPES)}")
        return v

    @field_validator("lateral_pattern")
    @classmethod
    def validate_lateral_pattern(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_LATERAL_PATTERNS:
            raise ValueError(f"Pattern laterale invalido. Validi: {sorted(VALID_LATERAL_PATTERNS)}")
        return v

    @field_validator("muscoli_primari", "muscoli_secondari")
    @classmethod
    def validate_muscles(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        for m in v:
            if m not in VALID_MUSCLES:
                raise ValueError(f"Muscolo '{m}' invalido. Validi: {sorted(VALID_MUSCLES)}")
        return v


# ═══════════════════════════════════════════════════════════════
# UPDATE
# ═══════════════════════════════════════════════════════════════

class ExerciseUpdate(BaseModel):
    """Aggiornamento parziale — solo su esercizi custom."""
    model_config = {"extra": "forbid"}

    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    nome_en: Optional[str] = Field(None, max_length=200)
    categoria: Optional[str] = None
    pattern_movimento: Optional[str] = None
    force_type: Optional[str] = None
    lateral_pattern: Optional[str] = None
    muscoli_primari: Optional[List[str]] = None
    muscoli_secondari: Optional[List[str]] = None
    attrezzatura: Optional[str] = None
    difficolta: Optional[str] = None
    rep_range_forza: Optional[str] = Field(None, max_length=20)
    rep_range_ipertrofia: Optional[str] = Field(None, max_length=20)
    rep_range_resistenza: Optional[str] = Field(None, max_length=20)
    ore_recupero: Optional[int] = Field(None, ge=1, le=96)
    descrizione_anatomica: Optional[str] = None
    descrizione_biomeccanica: Optional[str] = None
    setup: Optional[str] = None
    esecuzione: Optional[str] = None
    respirazione: Optional[str] = None
    tempo_consigliato: Optional[str] = Field(None, max_length=20)
    coaching_cues: Optional[List[str]] = None
    errori_comuni: Optional[List[dict[str, str]]] = None
    note_sicurezza: Optional[str] = None
    controindicazioni: Optional[List[str]] = None
    istruzioni: Optional[dict[str, Any]] = None

    @field_validator("categoria")
    @classmethod
    def validate_categoria(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_CATEGORIES:
            raise ValueError(f"Categoria invalida. Valide: {sorted(VALID_CATEGORIES)}")
        return v

    @field_validator("pattern_movimento")
    @classmethod
    def validate_pattern(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PATTERNS:
            raise ValueError(f"Pattern invalido. Validi: {sorted(VALID_PATTERNS)}")
        return v

    @field_validator("attrezzatura")
    @classmethod
    def validate_attrezzatura(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_EQUIPMENT:
            raise ValueError(f"Attrezzatura invalida. Valide: {sorted(VALID_EQUIPMENT)}")
        return v

    @field_validator("difficolta")
    @classmethod
    def validate_difficolta(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_DIFFICULTIES:
            raise ValueError(f"Difficolta' invalida. Valide: {sorted(VALID_DIFFICULTIES)}")
        return v

    @field_validator("force_type")
    @classmethod
    def validate_force_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_FORCE_TYPES:
            raise ValueError(f"Tipo forza invalido. Validi: {sorted(VALID_FORCE_TYPES)}")
        return v

    @field_validator("lateral_pattern")
    @classmethod
    def validate_lateral_pattern(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_LATERAL_PATTERNS:
            raise ValueError(f"Pattern laterale invalido. Validi: {sorted(VALID_LATERAL_PATTERNS)}")
        return v

    @field_validator("muscoli_primari", "muscoli_secondari")
    @classmethod
    def validate_muscles(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        for m in v:
            if m not in VALID_MUSCLES:
                raise ValueError(f"Muscolo '{m}' invalido. Validi: {sorted(VALID_MUSCLES)}")
        return v


# ═══════════════════════════════════════════════════════════════
# RESPONSE HELPERS
# ═══════════════════════════════════════════════════════════════

def _parse_json_list(v: Any) -> list:
    """Parse JSON string → list, passthrough if already list."""
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def _parse_json_dict(v: Any) -> Optional[dict]:
    """Parse JSON string → dict, passthrough if already dict."""
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, dict) else None
        except (json.JSONDecodeError, TypeError):
            return None
    return None


# ═══════════════════════════════════════════════════════════════
# RESPONSE: Media + Relazioni
# ═══════════════════════════════════════════════════════════════

class ExerciseMediaResponse(BaseModel):
    """Risposta per singolo media dell'esercizio."""
    model_config = {"from_attributes": True}

    id: int
    tipo: str
    url: str
    ordine: int
    descrizione: Optional[str] = None


class ExerciseRelationResponse(BaseModel):
    """Risposta per relazione tra esercizi (joined con nome)."""
    id: int
    related_exercise_id: int
    related_exercise_nome: str
    tipo_relazione: str


# ═══════════════════════════════════════════════════════════════
# RESPONSE: Exercise
# ═══════════════════════════════════════════════════════════════

class ExerciseResponse(BaseModel):
    """Risposta API — deserializza JSON fields in arrays/dicts."""
    model_config = {"from_attributes": True}

    id: int
    nome: str
    nome_en: Optional[str] = None
    categoria: str
    pattern_movimento: str
    force_type: Optional[str] = None
    lateral_pattern: Optional[str] = None
    muscoli_primari: List[str] = []
    muscoli_secondari: List[str] = []
    attrezzatura: str
    difficolta: str
    rep_range_forza: Optional[str] = None
    rep_range_ipertrofia: Optional[str] = None
    rep_range_resistenza: Optional[str] = None
    ore_recupero: int = 48
    descrizione_anatomica: Optional[str] = None
    descrizione_biomeccanica: Optional[str] = None
    setup: Optional[str] = None
    esecuzione: Optional[str] = None
    respirazione: Optional[str] = None
    tempo_consigliato: Optional[str] = None
    coaching_cues: List[str] = []
    errori_comuni: List[dict[str, str]] = []
    note_sicurezza: Optional[str] = None
    istruzioni: Optional[dict[str, Any]] = None
    controindicazioni: List[str] = []
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    is_builtin: bool = False
    created_at: Optional[datetime] = None

    # Populated by GET /{id} (enriched)
    media: List[ExerciseMediaResponse] = []
    relazioni: List[ExerciseRelationResponse] = []

    @field_validator(
        "muscoli_primari", "muscoli_secondari", "controindicazioni",
        "coaching_cues", mode="before",
    )
    @classmethod
    def parse_json_lists(cls, v: Any) -> list:
        return _parse_json_list(v)

    @field_validator("errori_comuni", mode="before")
    @classmethod
    def parse_errori_comuni(cls, v: Any) -> list:
        parsed = _parse_json_list(v)
        return [item for item in parsed if isinstance(item, dict)]

    @field_validator("istruzioni", mode="before")
    @classmethod
    def parse_json_dict(cls, v: Any) -> Optional[dict]:
        return _parse_json_dict(v)


class ExerciseListResponse(BaseModel):
    items: List[ExerciseResponse]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════
# INPUT: Media + Relazioni
# ═══════════════════════════════════════════════════════════════

class ExerciseRelationCreate(BaseModel):
    """Crea relazione tra esercizi."""
    model_config = {"extra": "forbid"}

    related_exercise_id: int
    tipo_relazione: str

    @field_validator("tipo_relazione")
    @classmethod
    def validate_tipo(cls, v: str) -> str:
        if v not in VALID_RELATION_TYPES:
            raise ValueError(f"Tipo relazione invalido. Validi: {sorted(VALID_RELATION_TYPES)}")
        return v
