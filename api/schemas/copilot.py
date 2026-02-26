# api/schemas/copilot.py
"""
Pydantic schemas per il copilot AI del workout builder.

Due endpoint:
- POST /suggest-exercise — suggerimento rapido 3 esercizi (button click)
- POST /chat — agente conversazionale con intent routing

Mass Assignment Prevention: trainer_id da JWT, mai dal body.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

VALID_SEZIONI = {"avviamento", "principale", "stretching"}


# ════════════════════════════════════════════════════════════
# SUGGEST EXERCISE (endpoint originale, backward compatible)
# ════════════════════════════════════════════════════════════


class SuggestExerciseRequest(BaseModel):
    """Richiesta suggerimento esercizio per il workout builder."""
    model_config = {"extra": "forbid"}

    id_scheda: int = Field(gt=0)
    sezione: str
    exercise_ids: List[int] = Field(
        default=[],
        description="ID esercizi gia' presenti nella sessione corrente",
    )
    focus_muscolare: Optional[str] = Field(
        None,
        max_length=200,
        description="Focus muscolare della sessione (opzionale)",
    )

    @field_validator("sezione")
    @classmethod
    def validate_sezione(cls, v: str) -> str:
        if v not in VALID_SEZIONI:
            raise ValueError(
                f"Sezione non valida: '{v}'. Valide: {sorted(VALID_SEZIONI)}"
            )
        return v


class ExerciseSuggestion(BaseModel):
    """Singolo suggerimento esercizio dal copilot."""
    exercise_id: int
    nome: str
    categoria: str
    pattern_movimento: str
    attrezzatura: str
    muscoli_primari: List[str] = []
    reasoning: str


class SuggestExerciseResponse(BaseModel):
    """Risposta con 3 suggerimenti esercizio."""
    suggestions: List[ExerciseSuggestion]


# ════════════════════════════════════════════════════════════
# CHAT (agente conversazionale)
# ════════════════════════════════════════════════════════════


class ChatWorkoutExercise(BaseModel):
    """Esercizio nel workout state inviato dal frontend."""
    id: int
    nome: str
    pattern: str
    sezione: str
    serie: int = 3
    ripetizioni: str = "8-12"
    riposo: int = 90


class ChatWorkoutSession(BaseModel):
    """Sessione nel workout state."""
    nome: str
    focus: Optional[str] = None
    exercises: List[ChatWorkoutExercise] = []


class ChatWorkoutState(BaseModel):
    """Snapshot dello stato corrente della scheda dal frontend."""
    sessions: List[ChatWorkoutSession] = []


class ChatMessage(BaseModel):
    """Messaggio nella conversation history."""
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class CopilotChatRequest(BaseModel):
    """Richiesta chat al copilot conversazionale."""
    model_config = {"extra": "forbid"}

    plan_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=1000)
    workout_state: ChatWorkoutState = Field(default_factory=ChatWorkoutState)
    conversation_history: List[ChatMessage] = Field(
        default=[],
        max_length=10,
        description="Ultimi messaggi (max 10, verranno troncati a 6 nel prompt)",
    )
    context_notes: List[str] = Field(
        default=[],
        max_length=20,
        description="Note di contesto estratte da conversazioni precedenti",
    )


# ── Action types nella risposta ──

class CopilotActionAddExercise(BaseModel):
    """Azione: aggiungi esercizio alla sessione."""
    type: Literal["add_exercise"] = "add_exercise"
    label: str
    reasoning: str
    exercise_id: int
    nome: str
    categoria: str
    pattern_movimento: str
    attrezzatura: str
    muscoli_primari: List[str] = []
    sezione: str
    serie: int = 3
    ripetizioni: str = "8-12"
    riposo: int = 90


class CopilotActionSwapExercise(BaseModel):
    """Azione: sostituisci un esercizio con un altro."""
    type: Literal["swap_exercise"] = "swap_exercise"
    label: str
    reasoning: str
    old_exercise_id: int
    new_exercise_id: int
    new_nome: str
    new_categoria: str
    new_attrezzatura: str


class CopilotActionModifyParams(BaseModel):
    """Azione: modifica parametri (serie, rip, riposo) di un esercizio."""
    type: Literal["modify_params"] = "modify_params"
    label: str
    reasoning: str
    exercise_id: int
    serie: Optional[int] = None
    ripetizioni: Optional[str] = None
    riposo: Optional[int] = None


# Union type per le azioni
CopilotAction = CopilotActionAddExercise | CopilotActionSwapExercise | CopilotActionModifyParams


class CopilotChatResponse(BaseModel):
    """Risposta del copilot conversazionale."""
    message: str = Field(description="Risposta testuale in italiano")
    actions: List[CopilotAction] = Field(
        default=[],
        description="Azioni proposte (bottoni cliccabili nel frontend)",
    )
    context_notes_update: List[str] = Field(
        default=[],
        description="Note di contesto aggiornate/estratte dalla conversazione",
    )
    intent: str = Field(
        default="chat",
        description="Intent classificato (debug/logging)",
    )
