# api/models/workout_log.py
"""
Modello WorkoutLog — log di esecuzione sessione di allenamento.

Registra QUANDO una sessione template e' stata effettivamente eseguita.
Fase 1: session-level only. Volume calcolato dal template (serie x rip x carico_kg).
Fase 2 (futuro): child table per override esercizio-level di pesi/rip effettivi.

Multi-tenancy: trainer_id FK diretta (stessa strategia di ClientMeasurement).
Deep IDOR: id_scheda -> WorkoutPlan.trainer_id | id_cliente -> Client.trainer_id
"""

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class WorkoutLog(SQLModel, table=True):
    """Log di esecuzione sessione allenamento."""

    __tablename__ = "allenamenti_eseguiti"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_scheda: int = Field(foreign_key="schede_allenamento.id", index=True)
    id_sessione: int = Field(foreign_key="sessioni_scheda.id", index=True)
    id_cliente: int = Field(foreign_key="clienti.id", index=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    data_esecuzione: date
    id_evento: Optional[int] = Field(default=None, foreign_key="agenda.id")
    note: Optional[str] = None
    created_at: Optional[str] = None
    deleted_at: Optional[datetime] = None
