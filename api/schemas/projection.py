# api/schemas/projection.py
"""
Pydantic schemas per la proiezione cliente.

3 layer indipendenti: volume accumulation, metric trends, goal projections.
Ogni layer puo' essere presente o assente a seconda dei dati disponibili.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class MetricTrendResponse(BaseModel):
    """Trend OLS per una singola metrica."""

    metric_id: int
    metric_name: str
    unit: str
    weekly_rate: float = Field(description="Variazione settimanale (slope × 7)")
    r_squared: float = Field(ge=0, le=1, description="R² della regressione (0-1)")
    n_points: int = Field(description="Numero di misurazioni usate")
    span_days: int = Field(description="Giorni tra prima e ultima misurazione")
    current_value: float
    current_date: str  # ISO date
    confidence: str = Field(description="insufficient | unstable | moderate | good")


class GoalProjectionResponse(BaseModel):
    """Proiezione per un singolo goal."""

    goal_id: int
    metric_name: str
    unit: str
    status: str = Field(
        description=(
            "projected | insufficient_data | wrong_direction | "
            "plateau | unreachable"
        ),
    )
    message: Optional[str] = None
    weekly_rate: Optional[float] = None
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    eta: Optional[str] = None  # ISO date
    eta_perfect: Optional[str] = None  # ISO date (scenario 100% compliance)
    days_saved: Optional[int] = Field(
        default=None,
        description="Giorni risparmiati con compliance perfetta",
    )
    days_per_missed_session: Optional[float] = Field(
        default=None,
        description="Giorni di ritardo per ogni sessione saltata",
    )
    r_squared: Optional[float] = None
    confidence: Optional[str] = None
    on_track: Optional[bool] = Field(
        default=None,
        description="True se ETA <= deadline del goal",
    )
    goal_deadline: Optional[str] = None  # ISO date


class VolumeAccumulationResponse(BaseModel):
    """Stimolo cumulativo nel periodo attivo del piano."""

    weekly_volume_planned: float
    weekly_volume_effective: float
    weeks_active: int
    total_volume_planned: float
    total_volume_effective: float
    total_volume_missed: float


class ProjectionPointResponse(BaseModel):
    """Punto per il chart predittivo."""

    date: str  # ISO date
    value: float
    is_projection: bool


class ProjectionChartResponse(BaseModel):
    """Dati per un singolo chart predittivo (una metrica)."""

    metric_id: int
    metric_name: str
    unit: str
    historical: List[ProjectionPointResponse] = Field(
        default_factory=list,
        description="Punti storici (misurazioni reali)",
    )
    projected: List[ProjectionPointResponse] = Field(
        default_factory=list,
        description="Punti proiettati (dalla regressione)",
    )
    target_value: Optional[float] = None
    eta: Optional[str] = None


class RiskFlagResponse(BaseModel):
    """Flag di rischio per il cliente."""

    severity: str = Field(description="alert | warning")
    code: str
    message: str
    metric_id: Optional[int] = None


class ClientProjectionResponse(BaseModel):
    """
    Risposta completa proiezione per un cliente.

    3 layer indipendenti — ciascuno puo' essere vuoto se mancano i dati.
    """

    client_id: int
    client_nome: str
    client_cognome: str

    # Layer 1: Accumulo stimolo (sempre se piano attivo)
    volume: Optional[VolumeAccumulationResponse] = None

    # Layer 2: Trend metriche (se misurazioni presenti)
    trends: List[MetricTrendResponse] = Field(default_factory=list)

    # Layer 3: Proiezioni goal (se goal + trend)
    projections: List[GoalProjectionResponse] = Field(default_factory=list)

    # Chart data (per metriche con goal attivi)
    charts: List[ProjectionChartResponse] = Field(default_factory=list)

    # Risk flags
    risk_flags: List[RiskFlagResponse] = Field(default_factory=list)

    # Meta
    compliance_pct: int = Field(default=0, description="Compliance piano attivo")
    plan_name: Optional[str] = None
    has_active_plan: bool = False
    has_measurements: bool = False
    has_goals: bool = False
