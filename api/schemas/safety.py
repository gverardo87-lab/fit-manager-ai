# api/schemas/safety.py
"""
Pydantic schemas per l'Exercise Safety Engine.

SafetyMapResponse: output dell'endpoint /exercises/safety-map.
Mappa exercise_id → safety entry con severita' e condizioni dettagliate.
"""

from typing import Optional

from pydantic import BaseModel


class SafetyConditionDetail(BaseModel):
    """Singola condizione medica rilevante per un esercizio."""
    id: int
    nome: str
    severita: str           # avoid, caution, modify
    nota: Optional[str] = None
    categoria: str          # orthopedic, cardiovascular, metabolic, neurological, respiratory, special
    body_tags: list[str] = []  # zone anatomiche (schiena, spalla, ginocchio...) per Risk Body Map


class ExerciseSafetyEntry(BaseModel):
    """Safety entry per un singolo esercizio."""
    exercise_id: int
    severity: str           # avoid, caution, modify (worst-case del cluster)
    conditions: list[SafetyConditionDetail]


class MedicationFlag(BaseModel):
    """Flag farmacologico rilevante per la programmazione dell'allenamento."""
    flag: str               # beta_blocker, anticoagulant, corticosteroid, insulin, statin
    nota: str               # nota clinica per il trainer


class SafetyMapResponse(BaseModel):
    """Risposta completa safety map per un cliente."""
    client_id: int
    client_nome: str
    has_anamnesi: bool
    condition_count: int    # quante condizioni rilevate nell'anamnesi
    condition_names: list[str]  # nomi condizioni rilevate (per overview panel)
    entries: dict[int, ExerciseSafetyEntry]   # exercise_id → safety entry
    medication_flags: list[MedicationFlag] = []  # flag farmacologici rilevati
