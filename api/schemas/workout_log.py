# api/schemas/workout_log.py
"""
Pydantic schemas per workout execution logs.

Input: WorkoutLogCreate (body per POST).
Output: WorkoutLogResponse con nomi enriched da JOINs.
Mass Assignment Prevention: trainer_id e id_cliente da JWT + path param.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════
# INPUT
# ════════════════════════════════════════════════════════════

class WorkoutLogCreate(BaseModel):
    """Crea log esecuzione sessione. trainer_id + id_cliente da JWT/path."""

    model_config = {"extra": "forbid"}

    id_scheda: int = Field(gt=0)
    id_sessione: int = Field(gt=0)
    data_esecuzione: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    id_evento: Optional[int] = Field(None, gt=0)
    note: Optional[str] = Field(None, max_length=500)


# ════════════════════════════════════════════════════════════
# OUTPUT
# ════════════════════════════════════════════════════════════

class WorkoutLogResponse(BaseModel):
    """Log esecuzione — output enriched con nomi scheda e sessione."""

    id: int
    id_scheda: int
    id_sessione: int
    id_cliente: int
    data_esecuzione: str
    id_evento: Optional[int] = None
    note: Optional[str] = None
    created_at: Optional[str] = None
    scheda_nome: str
    sessione_nome: str


class WorkoutLogListResponse(BaseModel):
    """Lista log esecuzione."""

    items: List[WorkoutLogResponse]
    total: int
