"""
Schema transport per il runtime SMART `plan-package`.

Questi DTO vivono fuori dal core `api/services/training_science/types.py`
per mantenere separati:
- dominio scientifico puro e computazionale
- orchestrazione DB-aware e contratti API applicativi
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from api.schemas.workout import WorkoutPlanCreate
from api.services.training_science.types import (
    GruppoMuscolare,
    Livello,
    Obiettivo,
    OrdinePriorita,
    PatternMovimento,
    RuoloSessione,
    TipoSplit,
)

TSBuilderObjective = Literal[
    "generale",
    "forza",
    "ipertrofia",
    "resistenza",
    "dimagrimento",
]
TSBuilderLevelChoice = Literal["auto", "beginner", "intermedio", "avanzato"]
TSBuilderMode = Literal["general", "performance", "clinical"]
TSSafetySeverity = Literal["avoid", "modify", "caution"] | None
TSCandidateBucket = Literal["recommended", "allowed", "discouraged"]
TSAnamnesiState = Literal["missing", "legacy", "structured"]


class TSPlanPresetInput(BaseModel):
    """Preset intenzionale del builder SMART."""

    model_config = {"extra": "forbid"}

    frequenza: int = Field(ge=2, le=6)
    obiettivo_builder: TSBuilderObjective
    livello_choice: TSBuilderLevelChoice = "auto"
    livello_override: Optional[Literal["beginner", "intermedio", "avanzato"]] = None
    mode: TSBuilderMode = "general"
    durata_target_min: Optional[int] = Field(default=None, ge=30, le=120)


class TSTrainerOverridesInput(BaseModel):
    """Override operativi del professionista sul ranking."""

    model_config = {"extra": "forbid"}

    excluded_exercise_ids: list[int] = Field(default_factory=list)
    preferred_exercise_ids: list[int] = Field(default_factory=list)
    pinned_exercise_ids_by_slot: dict[str, int] = Field(default_factory=dict)
    notes: Optional[str] = Field(default=None, max_length=1000)


class TSPlanPackageRequest(BaseModel):
    """Request additiva per l'orchestrazione runtime SMART."""

    model_config = {"extra": "forbid"}

    client_id: Optional[int] = Field(default=None, gt=0)
    preset: TSPlanPresetInput
    trainer_overrides: TSTrainerOverridesInput = Field(default_factory=TSTrainerOverridesInput)


class TSScientificProfileResolved(BaseModel):
    """Profilo scientifico risolto lato backend prima della generazione."""

    obiettivo_builder: TSBuilderObjective
    obiettivo_scientifico: Obiettivo
    livello_scientifico: Livello
    livello_workout: Literal["beginner", "intermedio", "avanzato"]
    mode: TSBuilderMode
    anamnesi_state: TSAnamnesiState
    safety_condition_count: int = Field(ge=0)
    profile_warnings: list[str] = Field(default_factory=list)


class TSCanonicalSlot(BaseModel):
    """Slot canonico backend-owned con identita' stabile."""

    slot_id: str = Field(min_length=1, max_length=80)
    pattern: PatternMovimento
    priorita: OrdinePriorita
    serie: int = Field(ge=1, le=10)
    rep_min: int = Field(ge=1, le=50)
    rep_max: int = Field(ge=1, le=50)
    riposo_sec: int = Field(ge=0, le=300)
    muscolo_target: Optional[GruppoMuscolare] = None
    note: str = Field(default="", max_length=500)


class TSCanonicalSession(BaseModel):
    """Sessione canonica backend-owned con slot lineari."""

    session_id: str = Field(min_length=1, max_length=80)
    nome: str = Field(min_length=1, max_length=100)
    ruolo: RuoloSessione
    focus: str = Field(min_length=1, max_length=200)
    slots: list[TSCanonicalSlot] = Field(min_length=1)


class TSCanonicalPlan(BaseModel):
    """Prescrizione scientifica canonica generata dal backend."""

    plan_id: str = Field(min_length=1, max_length=120)
    frequenza: int = Field(ge=2, le=6)
    obiettivo: Obiettivo
    livello: Livello
    tipo_split: TipoSplit
    sessioni: list[TSCanonicalSession] = Field(min_length=1)
    note_generazione: list[str] = Field(default_factory=list)


class TSSlotCandidate(BaseModel):
    """Candidato rankato per uno slot canonico."""

    slot_id: str = Field(min_length=1, max_length=80)
    exercise_id: int = Field(gt=0)
    rank: int = Field(ge=1)
    total_score: float = Field(ge=0)
    safety_severity: TSSafetySeverity = None
    bucket: TSCandidateBucket
    rationale: list[str] = Field(default_factory=list)
    adaptation_hint: Optional[str] = Field(default=None, max_length=500)


class TSSlotBinding(BaseModel):
    """Legame tra slot canonico ed esercizio proiettato nel workout draft."""

    session_id: str = Field(min_length=1, max_length=80)
    slot_id: str = Field(min_length=1, max_length=80)
    exercise_id: int = Field(gt=0)
    candidate_rank: int = Field(ge=1)


class TSWorkoutProjection(BaseModel):
    """Draft save-compatible derivato dal canonico e dal ranking."""

    draft: WorkoutPlanCreate
    slot_bindings: list[TSSlotBinding] = Field(default_factory=list)


class TSPlanPackageEngineInfo(BaseModel):
    """Versioni dei sottosistemi che hanno costruito il package."""

    planner_version: str = Field(min_length=1, max_length=50)
    ranking_version: str = Field(min_length=1, max_length=50)
    profile_version: str = Field(min_length=1, max_length=50)


class TSPlanPackage(BaseModel):
    """Envelope completo per il primo cutover SMART backend-first."""

    scientific_profile: TSScientificProfileResolved
    canonical_plan: TSCanonicalPlan
    rankings: dict[str, list[TSSlotCandidate]] = Field(default_factory=dict)
    workout_projection: TSWorkoutProjection
    warnings: list[str] = Field(default_factory=list)
    engine: TSPlanPackageEngineInfo
