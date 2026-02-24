# api/schemas/exercise.py
"""
Pydantic schemas per gli esercizi.

ExerciseCreate / ExerciseUpdate: input validation + Mass Assignment Prevention.
ExerciseResponse / ExerciseListResponse: output serialization con JSON→List parsing.
"""

import json
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ═══════════════════════════════════════════════════════════════
# ENUMS VALIDI
# ═══════════════════════════════════════════════════════════════

VALID_CATEGORIES = {"compound", "isolation", "bodyweight", "cardio"}
VALID_PATTERNS = {"squat", "hinge", "push_h", "push_v", "pull_h", "pull_v", "core", "rotation", "carry"}
VALID_EQUIPMENT = {"barbell", "dumbbell", "cable", "machine", "bodyweight", "kettlebell", "band", "trx"}
VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced"}
VALID_MUSCLES = {
    "quadriceps", "hamstrings", "glutes", "calves", "adductors",
    "chest", "back", "lats", "shoulders", "traps",
    "biceps", "triceps", "forearms", "core",
}


# ═══════════════════════════════════════════════════════════════
# CREATE
# ═══════════════════════════════════════════════════════════════

class ExerciseCreate(BaseModel):
    """Crea esercizio custom. trainer_id iniettato da JWT."""
    model_config = {"extra": "forbid"}

    nome: str = Field(min_length=1, max_length=200)
    nome_en: Optional[str] = Field(None, max_length=200)
    categoria: str
    pattern_movimento: str
    muscoli_primari: List[str] = Field(min_length=1)
    muscoli_secondari: Optional[List[str]] = None
    attrezzatura: str
    difficolta: str
    rep_range_forza: Optional[str] = Field(None, max_length=20)
    rep_range_ipertrofia: Optional[str] = Field(None, max_length=20)
    rep_range_resistenza: Optional[str] = Field(None, max_length=20)
    ore_recupero: int = Field(default=48, ge=1, le=96)
    istruzioni: Optional[dict[str, Any]] = None
    controindicazioni: Optional[List[str]] = None

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
    muscoli_primari: Optional[List[str]] = None
    muscoli_secondari: Optional[List[str]] = None
    attrezzatura: Optional[str] = None
    difficolta: Optional[str] = None
    rep_range_forza: Optional[str] = Field(None, max_length=20)
    rep_range_ipertrofia: Optional[str] = Field(None, max_length=20)
    rep_range_resistenza: Optional[str] = Field(None, max_length=20)
    ore_recupero: Optional[int] = Field(None, ge=1, le=96)
    istruzioni: Optional[dict[str, Any]] = None
    controindicazioni: Optional[List[str]] = None

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
# RESPONSE
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


class ExerciseResponse(BaseModel):
    """Risposta API — deserializza JSON fields in arrays/dicts."""
    model_config = {"from_attributes": True}

    id: int
    nome: str
    nome_en: Optional[str] = None
    categoria: str
    pattern_movimento: str
    muscoli_primari: List[str] = []
    muscoli_secondari: List[str] = []
    attrezzatura: str
    difficolta: str
    rep_range_forza: Optional[str] = None
    rep_range_ipertrofia: Optional[str] = None
    rep_range_resistenza: Optional[str] = None
    ore_recupero: int = 48
    istruzioni: Optional[dict[str, Any]] = None
    controindicazioni: List[str] = []
    is_builtin: bool = False
    created_at: Optional[datetime] = None

    @field_validator("muscoli_primari", "muscoli_secondari", "controindicazioni", mode="before")
    @classmethod
    def parse_json_lists(cls, v: Any) -> list:
        return _parse_json_list(v)

    @field_validator("istruzioni", mode="before")
    @classmethod
    def parse_json_dict(cls, v: Any) -> Optional[dict]:
        return _parse_json_dict(v)


class ExerciseListResponse(BaseModel):
    items: List[ExerciseResponse]
    total: int
    page: int
    page_size: int
