# api/models/workout.py
"""
Modelli Workout Plan — gerarchia per schede allenamento.

Gerarchia:
  WorkoutPlan (schede_allenamento) — scheda madre
    └── WorkoutSession (sessioni_scheda) — sessioni / "giorni"
          ├── SessionBlock (blocchi_sessione) — blocchi esercizi (circuit, tabata, AMRAP…)
          │     └── WorkoutExercise (esercizi_sessione, id_blocco set)
          └── WorkoutExercise (esercizi_sessione, id_blocco NULL) — esercizi "straight"

Multi-tenancy:
- WorkoutPlan.trainer_id: FK diretta verso trainers
- WorkoutSession, SessionBlock, WorkoutExercise: nessun trainer_id diretto
  Deep IDOR: WorkoutExercise → WorkoutSession → WorkoutPlan.trainer_id

Soft delete: solo WorkoutPlan ha deleted_at (a cascata logica).
"""

from datetime import date as date_type
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
    data_inizio: Optional[date_type] = Field(default=None)
    data_fine: Optional[date_type] = Field(default=None)
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


class SessionBlock(SQLModel, table=True):
    """Blocco esercizi strutturato — circuit, superset, tabata, AMRAP, EMOM."""
    __tablename__ = "blocchi_sessione"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_sessione: int = Field(foreign_key="sessioni_scheda.id", index=True)
    # Tipo: circuit | superset | tabata | amrap | emom | for_time
    tipo_blocco: str = Field(default="circuit")
    # Ordine del blocco nella sessione (relativo agli esercizi straight e agli altri blocchi)
    ordine: int
    # Nome descrittivo opzionale (es. "Finisher HIIT")
    nome: Optional[str] = None
    # Giri/round (circuit: 3, tabata: 8)
    giri: int = Field(default=3)
    # Durata lavoro per stazione in secondi (Tabata: 20, EMOM: 60)
    durata_lavoro_sec: Optional[int] = None
    # Durata riposo tra stazioni in secondi (Tabata: 10, Circuit: 15)
    durata_riposo_sec: Optional[int] = None
    # Durata totale blocco in secondi (AMRAP: 720=12min, EMOM: 1200=20min)
    durata_blocco_sec: Optional[int] = None
    note: Optional[str] = None


class WorkoutExercise(SQLModel, table=True):
    """Esercizio dentro una sessione o dentro un blocco."""
    __tablename__ = "esercizi_sessione"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_sessione: int = Field(foreign_key="sessioni_scheda.id", index=True)
    # Se NULL → esercizio "straight" nella sessione
    # Se set → esercizio dentro un blocco (blocchi_sessione)
    id_blocco: Optional[int] = Field(default=None, foreign_key="blocchi_sessione.id")
    id_esercizio: int = Field(foreign_key="esercizi.id")
    # ordine: posizione nella sessione (esercizi straight) o nel blocco (esercizi in blocco)
    ordine: int
    # posizione_nel_blocco: ordine dentro il blocco (None per esercizi straight)
    posizione_nel_blocco: Optional[int] = None
    serie: int = Field(default=3)
    ripetizioni: str = Field(default="8-12")
    tempo_riposo_sec: int = Field(default=90)
    tempo_esecuzione: Optional[str] = None
    carico_kg: Optional[float] = None
    note: Optional[str] = None
