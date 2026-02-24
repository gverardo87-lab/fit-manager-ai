# api/models/exercise.py
"""
Modello Exercise — mappa la tabella 'esercizi'.

Dual ownership:
- trainer_id = NULL → esercizio builtin (seed), visibile a tutti, non modificabile
- trainer_id = X → esercizio custom del trainer, CRUD completo

Campi JSON (muscoli, istruzioni, controindicazioni) serializzati come TEXT
e deserializzati nello schema Pydantic.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class Exercise(SQLModel, table=True):
    __tablename__ = "esercizi"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: Optional[int] = Field(default=None, foreign_key="trainers.id", index=True)

    # Identita'
    nome: str = Field(index=True)
    nome_en: Optional[str] = None

    # Classificazione
    categoria: str          # compound, isolation, bodyweight, cardio
    pattern_movimento: str  # squat, hinge, push_h, push_v, pull_h, pull_v, core, rotation, carry

    # Muscoli (JSON arrays stored as TEXT)
    muscoli_primari: str              # JSON: ["quadriceps", "glutes"]
    muscoli_secondari: Optional[str] = None  # JSON: ["hamstrings", "core"]

    # Setup
    attrezzatura: str  # barbell, dumbbell, cable, machine, bodyweight, kettlebell, band, trx
    difficolta: str    # beginner, intermediate, advanced

    # Parametri allenamento
    rep_range_forza: Optional[str] = None       # "3-6"
    rep_range_ipertrofia: Optional[str] = None  # "6-12"
    rep_range_resistenza: Optional[str] = None  # "15-20"
    ore_recupero: int = Field(default=48)

    # Istruzioni (JSON: {setup, esecuzione, errori_comuni})
    istruzioni: Optional[str] = None

    # Sicurezza (JSON array: ["ginocchio", "schiena"])
    controindicazioni: Optional[str] = None

    # Metadata
    is_builtin: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None
