# api/schemas/measurement.py
"""
Pydantic schemas per il tracking misurazioni corporee/prestazionali.

Input: MeasurementCreate, MeasurementUpdate (batch valori).
Output: MetricResponse, MeasurementResponse con valori nested enriched.
Mass Assignment Prevention: trainer_id da JWT, mai dal body.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
# INPUT
# ═══════════════════════════════════════════════════════════════

class MeasurementValueInput(BaseModel):
    """Singolo valore — input batch."""
    model_config = {"extra": "forbid"}

    id_metrica: int = Field(gt=0)
    valore: float = Field(gt=0)


class MeasurementCreate(BaseModel):
    """Crea sessione di misurazione + valori batch. trainer_id da JWT."""
    model_config = {"extra": "forbid"}

    data_misurazione: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    note: Optional[str] = Field(None, max_length=500)
    valori: List[MeasurementValueInput] = Field(min_length=1)


class MeasurementUpdate(BaseModel):
    """Aggiorna sessione di misurazione + full-replace valori."""
    model_config = {"extra": "forbid"}

    data_misurazione: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    note: Optional[str] = Field(None, max_length=500)
    valori: Optional[List[MeasurementValueInput]] = None


# ═══════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════

class MetricResponse(BaseModel):
    """Metrica dal catalogo."""
    model_config = {"from_attributes": True}

    id: int
    nome: str
    nome_en: str
    unita_misura: str
    categoria: str
    ordinamento: int


class MeasurementValueResponse(BaseModel):
    """Singolo valore misurato — output enriched con nome metrica."""
    id_metrica: int
    nome_metrica: str
    unita: str
    valore: float


class GoalCompletionInfo(BaseModel):
    """Info obiettivo auto-completato — per toast nel frontend."""
    id: int
    nome_metrica: str
    valore_target: float
    valore_raggiunto: float


class MeasurementResponse(BaseModel):
    """Sessione di misurazione — output con valori nested."""
    id: int
    id_cliente: int
    data_misurazione: str
    note: Optional[str] = None
    valori: List[MeasurementValueResponse] = []
    obiettivi_raggiunti: List[GoalCompletionInfo] = []


class MeasurementListResponse(BaseModel):
    """Lista sessioni di misurazione."""
    items: List[MeasurementResponse]
    total: int
