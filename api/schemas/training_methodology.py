# api/schemas/training_methodology.py
"""
Pydantic schemas per il dominio MyTrainer — qualita' metodologica allenamento.

Parallelo a clinical.py (MyPortal): clinical tracka readiness salute,
training_methodology tracka qualita' scientifica dei programmi.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class TrainingMethodologyPlanItem(BaseModel):
    """Singolo piano nella worklist MyTrainer."""

    # ── Identita' piano ──
    plan_id: int
    plan_nome: str
    client_id: int
    client_nome: str
    client_cognome: str
    obiettivo: str
    livello: str
    status: str  # da_attivare | attivo | completato
    sessioni_count: int = 0
    data_inizio: Optional[str] = None
    data_fine: Optional[str] = None

    # ── Analisi scientifica (da analyze_plan) ──
    science_score: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Score scientifico 0-100 da analyze_plan()",
    )
    sotto_mev_count: int = Field(default=0, description="Muscoli sotto MEV")
    sopra_mrv_count: int = Field(default=0, description="Muscoli sopra MRV")
    ottimali_count: int = Field(default=0, description="Muscoli in range ottimale")
    squilibri_count: int = Field(default=0, description="Rapporti biomeccanici fuori tolleranza")
    warning_count: int = Field(default=0, description="Warning scientifici")
    volume_totale: float = Field(default=0.0, description="Serie totali/settimana")

    # ── Compliance (da workout_logs) ──
    compliance_pct: int = Field(default=0, ge=0, le=100, description="Aderenza 0-100%")
    sessions_expected: int = Field(default=0, description="Sessioni attese nel periodo")
    sessions_completed: int = Field(default=0, description="Sessioni completate")

    # ── Score combinato ──
    training_score: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Score combinato: science 60% + compliance 40%",
    )

    # ── Priorita' e CTA ──
    priority: str = "low"  # high | medium | low
    priority_score: int = 0  # deterministico per ordinamento
    next_action_code: str = "review"
    next_action_label: str = "Rivedi piano"
    next_action_href: str = ""
    analyzable: bool = Field(
        default=True,
        description="False se il piano non ha esercizi con pattern validi",
    )


class TrainingMethodologySummary(BaseModel):
    """KPI aggregati per MyTrainer hero card."""

    total_plans: int = 0
    active_plans: int = 0
    avg_science_score: float = 0.0
    avg_compliance: float = 0.0
    avg_training_score: float = 0.0
    plans_with_issues: int = 0  # science_score < 60
    plans_excellent: int = 0  # training_score >= 80
    high_priority: int = 0
    medium_priority: int = 0
    low_priority: int = 0


class TrainingMethodologyWorklistResponse(BaseModel):
    """Risposta paginata worklist per MyTrainer."""

    summary: TrainingMethodologySummary
    items: List[TrainingMethodologyPlanItem] = []
    total: int = 0
    page: int = 1
    page_size: int = 24
