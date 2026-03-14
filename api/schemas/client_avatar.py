# api/schemas/client_avatar.py
"""
Client Avatar — schema Pydantic v2 per il profilo composito cliente.

6 dimensioni + highlights + wrapper. Ogni dimensione ha un semaforo
(green/amber/red) che sintetizza lo stato in un colpo d'occhio.
"""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


SemaphoreStatus = Literal["green", "amber", "red"]


class AvatarIdentity(BaseModel):
    """Dimensione anagrafica del cliente."""
    id: int
    nome: str
    cognome: str
    full_name: str
    age: Optional[int] = None
    sesso: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    client_since: Optional[str] = None
    seniority_days: int = 0
    stato: str = "Attivo"
    status: SemaphoreStatus = "green"


class AvatarClinicalProfile(BaseModel):
    """Dimensione clinica: anamnesi + condizioni mediche."""
    anamnesi_state: str = "missing"  # missing | legacy | structured
    anamnesi_version: int = 0  # 0=missing, 1=legacy, 2=structured
    condition_count: int = 0
    condition_names: list[str] = Field(default_factory=list)
    risk_level: str = "unknown"  # low | medium | high | unknown
    status: SemaphoreStatus = "red"


class AvatarContractStatus(BaseModel):
    """Dimensione contrattuale: contratto attivo, crediti, rate."""
    has_active_contract: bool = False
    active_contract_id: Optional[int] = None
    credits_remaining: int = 0
    credits_total: int = 0
    credits_used_pct: float = 0.0
    days_to_expiry: Optional[int] = None
    payment_status: str = "none"  # none | PENDENTE | PARZIALE | SALDATA
    overdue_rates_count: int = 0
    renewal_count: int = 0
    status: SemaphoreStatus = "red"


class AvatarTrainingPath(BaseModel):
    """Dimensione allenamento: scheda, compliance, sessioni."""
    has_active_plan: bool = False
    active_plan_name: Optional[str] = None
    active_plan_objective: Optional[str] = None
    compliance_30d: Optional[float] = None
    compliance_60d: Optional[float] = None
    total_sessions: int = 0
    completed_sessions: int = 0
    days_since_last_session: Optional[int] = None
    status: SemaphoreStatus = "red"


class AvatarBodyGoals(BaseModel):
    """Dimensione corporea: misurazioni, obiettivi, composizione."""
    has_measurements: bool = False
    last_measurement_date: Optional[date] = None
    measurement_freshness: str = "missing"  # missing | ok | warning | critical
    active_goals: int = 0
    bmi: Optional[float] = None
    body_fat_pct: Optional[float] = None
    status: SemaphoreStatus = "red"


class AvatarHighlight(BaseModel):
    """Segnalazione puntuale che richiede attenzione."""
    code: str
    text: str  # Italiano
    severity: Literal["info", "warning", "critical"]
    dimension: str  # identity | clinical | contract | training | body_goals
    cta_href: Optional[str] = None


class ClientAvatar(BaseModel):
    """Proiezione composita dello stato completo di un cliente."""
    client_id: int
    generated_at: str
    readiness_score: int = 0  # 0-100
    identity: AvatarIdentity
    clinical: AvatarClinicalProfile = Field(default_factory=AvatarClinicalProfile)
    contract: AvatarContractStatus = Field(default_factory=AvatarContractStatus)
    training: AvatarTrainingPath = Field(default_factory=AvatarTrainingPath)
    body_goals: AvatarBodyGoals = Field(default_factory=AvatarBodyGoals)
    highlights: list[AvatarHighlight] = Field(default_factory=list)


class ClientAvatarBatchRequest(BaseModel):
    """Request body per batch avatar."""
    model_config = {"extra": "forbid"}

    client_ids: list[int] = Field(..., min_length=1, max_length=50)


class ClientAvatarBatchResponse(BaseModel):
    """Response wrapper per batch avatar."""
    generated_at: str
    avatars: list[ClientAvatar] = Field(default_factory=list)
