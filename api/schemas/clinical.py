# api/schemas/clinical.py
"""
Pydantic schemas per il dominio clinico-operativo dashboard/MyPortal.

Nota: questo modulo resta non-medico e orientato a workflow tecnico
del chinesiologo (anamnesi, misurazioni, schede, monitoraggio).
"""

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel


class ClinicalFreshnessSignal(BaseModel):
    """Stato unificato di freshness per misurazioni e schede."""

    domain: Literal["measurements", "workout"]
    status: Literal["missing", "ok", "warning", "critical"] = "missing"
    label: str
    cta_label: str
    cta_href: str
    timeline_status: str = "none"        # overdue | today | upcoming_7d | upcoming_14d | future | none
    reason_code: Optional[str] = None
    due_date: Optional[date] = None
    last_recorded_date: Optional[date] = None
    days_to_due: Optional[int] = None
    days_since_last: Optional[int] = None


class ClinicalReadinessClientItem(BaseModel):
    """Singolo cliente nella coda readiness clinica."""

    client_id: int
    client_nome: str
    client_cognome: str
    anamnesi_state: str                  # missing | legacy | structured
    has_measurements: bool = False
    has_workout_plan: bool = False
    workout_activated: bool = False
    workout_plan_name: Optional[str] = None
    missing_steps: List[str] = []        # anamnesi_missing | anamnesi_legacy | baseline | workout | workout_not_activated
    readiness_score: int = 0             # 0..100
    priority: str = "low"                # high | medium | low
    priority_score: int = 0              # deterministico per ordinamento
    next_action_code: str                # collect_anamnesi | migrate_anamnesi | collect_baseline | assign_workout | activate_workout | ready
    next_action_label: str
    next_action_href: str
    next_due_date: Optional[date] = None
    days_to_due: Optional[int] = None
    timeline_status: str = "none"        # overdue | today | upcoming_7d | upcoming_14d | future | none
    timeline_reason: Optional[str] = None
    timeline_label: Optional[str] = None
    measurement_freshness: ClinicalFreshnessSignal
    workout_freshness: ClinicalFreshnessSignal


class ClinicalReadinessSummary(BaseModel):
    """Contatori aggregati della coda readiness."""
    total_clients: int = 0
    ready_clients: int = 0
    missing_anamnesi: int = 0
    legacy_anamnesi: int = 0
    missing_measurements: int = 0
    missing_workout_plan: int = 0
    high_priority: int = 0
    medium_priority: int = 0
    low_priority: int = 0


class ClinicalReadinessResponse(BaseModel):
    """Risposta completa readiness clinica."""
    summary: ClinicalReadinessSummary
    items: List[ClinicalReadinessClientItem] = []


class ClinicalReadinessWorklistResponse(BaseModel):
    """Risposta paginata readiness per MyPortal worklist."""
    summary: ClinicalReadinessSummary
    items: List[ClinicalReadinessClientItem] = []
    total: int = 0
    page: int = 1
    page_size: int = 25

