# api/schemas/workout.py
"""
Pydantic schemas per le schede allenamento (workout plans).

Gerarchia nested:
  WorkoutPlanCreate → WorkoutSessionInput → SessionBlockInput / WorkoutExerciseInput

Output enriched con JOIN (nome esercizio, categoria, nome cliente).
Mass Assignment Prevention: trainer_id da JWT, mai dal body.

Formati blocco supportati:
  circuit   — N esercizi in circuito, X giri, riposo tra stazioni
  superset  — 2 esercizi abbinati, X serie, mini-riposo tra esercizi
  tabata    — 8 round 20s lavoro / 10s riposo
  amrap     — As Many Rounds As Possible in N minuti
  emom      — Every Minute On the Minute, N minuti
  for_time  — Completare X giri il prima possibile
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════════
# COSTANTI VALIDE
# ═══════════════════════════════════════════════════════════════

VALID_OBIETTIVI = {"forza", "ipertrofia", "resistenza", "dimagrimento", "generale"}
VALID_LIVELLI = {"beginner", "intermedio", "avanzato"}
VALID_BLOCK_TYPES = {"circuit", "superset", "tabata", "amrap", "emom", "for_time"}


# ═══════════════════════════════════════════════════════════════
# INPUT
# ═══════════════════════════════════════════════════════════════

class WorkoutExerciseInput(BaseModel):
    """Esercizio dentro una sessione (straight) o dentro un blocco — input."""
    model_config = {"extra": "forbid"}

    id_esercizio: int = Field(gt=0)
    ordine: int = Field(ge=1, le=50)
    serie: int = Field(ge=1, le=10, default=3)
    ripetizioni: str = Field(min_length=1, max_length=20, default="8-12")
    tempo_riposo_sec: int = Field(ge=0, le=300, default=90)
    tempo_esecuzione: Optional[str] = Field(None, max_length=20)
    carico_kg: Optional[float] = Field(None, ge=0, le=500)
    note: Optional[str] = Field(None, max_length=500)


class SessionBlockInput(BaseModel):
    """Blocco strutturato di esercizi (circuit, tabata, AMRAP, EMOM, superset) — input."""
    model_config = {"extra": "forbid"}

    tipo_blocco: str = Field(default="circuit")
    ordine: int = Field(ge=1, le=50)
    nome: Optional[str] = Field(None, max_length=100)
    giri: int = Field(ge=1, le=20, default=3)
    durata_lavoro_sec: Optional[int] = Field(None, ge=5, le=600)
    durata_riposo_sec: Optional[int] = Field(None, ge=0, le=300)
    durata_blocco_sec: Optional[int] = Field(None, ge=60, le=7200)
    note: Optional[str] = Field(None, max_length=500)
    esercizi: List[WorkoutExerciseInput] = Field(min_length=1)

    @field_validator("tipo_blocco")
    @classmethod
    def validate_tipo_blocco(cls, v: str) -> str:
        if v not in VALID_BLOCK_TYPES:
            raise ValueError(f"Tipo blocco invalido. Validi: {sorted(VALID_BLOCK_TYPES)}")
        return v


class WorkoutSessionInput(BaseModel):
    """Sessione di allenamento — input."""
    model_config = {"extra": "forbid"}

    nome_sessione: str = Field(min_length=1, max_length=100)
    focus_muscolare: Optional[str] = Field(None, max_length=200)
    durata_minuti: int = Field(ge=15, le=180, default=60)
    note: Optional[str] = Field(None, max_length=500)
    # Esercizi "straight" (non in blocco)
    esercizi: List[WorkoutExerciseInput] = Field(default_factory=list)
    # Blocchi strutturati (circuit, tabata, AMRAP, EMOM, superset)
    blocchi: List[SessionBlockInput] = Field(default_factory=list)


class WorkoutPlanCreate(BaseModel):
    """Crea scheda allenamento. trainer_id iniettato da JWT."""
    model_config = {"extra": "forbid"}

    id_cliente: Optional[int] = None
    nome: str = Field(min_length=1, max_length=200)
    obiettivo: str
    livello: str
    durata_settimane: int = Field(ge=1, le=52, default=4)
    sessioni_per_settimana: int = Field(ge=1, le=7, default=3)
    note: Optional[str] = Field(None, max_length=1000)
    sessioni: List[WorkoutSessionInput] = Field(min_length=1)

    @field_validator("obiettivo")
    @classmethod
    def validate_obiettivo(cls, v: str) -> str:
        if v not in VALID_OBIETTIVI:
            raise ValueError(f"Obiettivo invalido. Validi: {sorted(VALID_OBIETTIVI)}")
        return v

    @field_validator("livello")
    @classmethod
    def validate_livello(cls, v: str) -> str:
        if v not in VALID_LIVELLI:
            raise ValueError(f"Livello invalido. Validi: {sorted(VALID_LIVELLI)}")
        return v


class WorkoutPlanUpdate(BaseModel):
    """Aggiornamento parziale metadati scheda."""
    model_config = {"extra": "forbid"}

    id_cliente: Optional[int] = None
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    obiettivo: Optional[str] = None
    livello: Optional[str] = None
    durata_settimane: Optional[int] = Field(None, ge=1, le=52)
    sessioni_per_settimana: Optional[int] = Field(None, ge=1, le=7)
    note: Optional[str] = Field(None, max_length=1000)
    data_inizio: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    data_fine: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")

    @field_validator("obiettivo")
    @classmethod
    def validate_obiettivo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_OBIETTIVI:
            raise ValueError(f"Obiettivo invalido. Validi: {sorted(VALID_OBIETTIVI)}")
        return v

    @field_validator("livello")
    @classmethod
    def validate_livello(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_LIVELLI:
            raise ValueError(f"Livello invalido. Validi: {sorted(VALID_LIVELLI)}")
        return v


# ═══════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════

class WorkoutExerciseResponse(BaseModel):
    """Esercizio in sessione o in blocco — output enriched con JOIN."""
    model_config = {"from_attributes": True}

    id: int
    id_esercizio: int
    esercizio_nome: str
    esercizio_categoria: str
    esercizio_attrezzatura: str
    ordine: int
    serie: int
    ripetizioni: str
    tempo_riposo_sec: int
    tempo_esecuzione: Optional[str] = None
    carico_kg: Optional[float] = None
    note: Optional[str] = None


class SessionBlockResponse(BaseModel):
    """Blocco strutturato — output con esercizi nested."""
    model_config = {"from_attributes": True}

    id: int
    tipo_blocco: str
    ordine: int
    nome: Optional[str] = None
    giri: int
    durata_lavoro_sec: Optional[int] = None
    durata_riposo_sec: Optional[int] = None
    durata_blocco_sec: Optional[int] = None
    note: Optional[str] = None
    esercizi: List[WorkoutExerciseResponse] = []


class WorkoutSessionResponse(BaseModel):
    """Sessione — output con esercizi straight + blocchi nested."""
    model_config = {"from_attributes": True}

    id: int
    numero_sessione: int
    nome_sessione: str
    focus_muscolare: Optional[str] = None
    durata_minuti: int
    note: Optional[str] = None
    # Esercizi "straight" (id_blocco = NULL)
    esercizi: List[WorkoutExerciseResponse] = []
    # Blocchi strutturati (circuit, tabata, ecc.)
    blocchi: List[SessionBlockResponse] = []


class WorkoutPlanResponse(BaseModel):
    """Scheda allenamento — output completo con sessioni + esercizi + blocchi."""
    model_config = {"from_attributes": True}

    id: int
    id_cliente: Optional[int] = None
    client_nome: Optional[str] = None
    client_cognome: Optional[str] = None
    nome: str
    obiettivo: str
    livello: str
    durata_settimane: int
    sessioni_per_settimana: int
    note: Optional[str] = None
    ai_commentary: Optional[str] = None
    sessioni: List[WorkoutSessionResponse] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    data_inizio: Optional[str] = None
    data_fine: Optional[str] = None


class WorkoutPlanListResponse(BaseModel):
    """Risposta lista paginata."""
    items: List[WorkoutPlanResponse]
    total: int
    page: int
    page_size: int
