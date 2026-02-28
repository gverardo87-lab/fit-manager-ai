# api/schemas/goal.py
"""
Pydantic schemas per Obiettivi Cliente.

Input: GoalCreate, GoalUpdate (Mass Assignment Prevention: no trainer_id, no id).
Output: GoalResponse, GoalWithProgress (enriched con calcolo progresso).
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
# INPUT
# ═══════════════════════════════════════════════════════════════

class GoalCreate(BaseModel):
    """Crea obiettivo per un cliente. trainer_id da JWT."""
    model_config = {"extra": "forbid"}

    id_metrica: int = Field(gt=0)
    direzione: str = Field(pattern=r"^(aumentare|diminuire|mantenere)$")
    valore_target: Optional[float] = None
    data_inizio: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    data_scadenza: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    priorita: int = Field(default=3, ge=1, le=5)
    note: Optional[str] = Field(None, max_length=500)


class GoalUpdate(BaseModel):
    """Aggiorna obiettivo (partial update)."""
    model_config = {"extra": "forbid"}

    direzione: Optional[str] = Field(None, pattern=r"^(aumentare|diminuire|mantenere)$")
    valore_target: Optional[float] = None
    data_scadenza: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    priorita: Optional[int] = Field(None, ge=1, le=5)
    stato: Optional[str] = Field(None, pattern=r"^(attivo|raggiunto|abbandonato)$")
    note: Optional[str] = Field(None, max_length=500)


# ═══════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════

class GoalProgress(BaseModel):
    """Progresso computato — enrichment dalla misurazione piu' recente."""
    valore_corrente: Optional[float] = None
    data_corrente: Optional[str] = None
    delta_da_baseline: Optional[float] = None
    percentuale_progresso: Optional[float] = None
    tendenza_positiva: Optional[bool] = None


class GoalResponse(BaseModel):
    """Obiettivo con progresso inline."""
    id: int
    id_cliente: int
    id_metrica: int
    nome_metrica: str
    unita_misura: str
    categoria_metrica: str

    tipo_obiettivo: str
    direzione: str
    valore_target: Optional[float] = None
    valore_baseline: Optional[float] = None
    data_baseline: Optional[str] = None

    data_inizio: str
    data_scadenza: Optional[str] = None

    priorita: int
    stato: str
    completed_at: Optional[str] = None
    completato_automaticamente: bool = False
    note: Optional[str] = None

    progresso: GoalProgress


class GoalListResponse(BaseModel):
    """Lista obiettivi con KPI."""
    items: List[GoalResponse]
    total: int
    attivi: int
    raggiunti: int
