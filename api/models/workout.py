# api/models/workout.py
"""
Modelli Workout Plan — 3 tabelle gerarchiche per schede allenamento.

Gerarchia:
  WorkoutPlan (schede_allenamento) — scheda madre
    └── WorkoutSession (sessioni_scheda) — sessioni / "giorni"
          └── WorkoutExercise (esercizi_sessione) — esercizi dentro una sessione

Multi-tenancy:
- WorkoutPlan.trainer_id: FK diretta verso trainers
- WorkoutSession, WorkoutExercise: nessun trainer_id diretto
  Deep IDOR: WorkoutExercise → WorkoutSession → WorkoutPlan.trainer_id
  Stessa strategia di Rate → Contract.trainer_id.

Soft delete: solo WorkoutPlan ha deleted_at (a cascata logica).
"""

from typing import Optional
from sqlmodel import SQLModel, Field


class WorkoutPlan(SQLModel, table=True):
    """Scheda allenamento — entita' padre."""
    __tablename__ = "schede_allenamento"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    id_cliente: Optional[int] = Field(default=None, foreign_key="clienti.id")
    nome: str
    obiettivo: str       # forza, ipertrofia, resistenza, dimagrimento, generale
    livello: str         # beginner, intermedio, avanzato
    durata_settimane: int = Field(default=4)
    sessioni_per_settimana: int = Field(default=3)
    note: Optional[str] = None
    ai_commentary: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    deleted_at: Optional[str] = None


class WorkoutSession(SQLModel, table=True):
    """Sessione di allenamento — figlio di WorkoutPlan."""
    __tablename__ = "sessioni_scheda"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_scheda: int = Field(foreign_key="schede_allenamento.id", index=True)
    numero_sessione: int
    nome_sessione: str
    focus_muscolare: Optional[str] = None
    durata_minuti: int = Field(default=60)
    note: Optional[str] = None


class WorkoutExercise(SQLModel, table=True):
    """Esercizio dentro una sessione — nipote di WorkoutPlan."""
    __tablename__ = "esercizi_sessione"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_sessione: int = Field(foreign_key="sessioni_scheda.id", index=True)
    id_esercizio: int = Field(foreign_key="esercizi.id")
    ordine: int
    serie: int = Field(default=3)
    ripetizioni: str = Field(default="8-12")
    tempo_riposo_sec: int = Field(default=90)
    tempo_esecuzione: Optional[str] = None
    carico_kg: Optional[float] = None
    note: Optional[str] = None
