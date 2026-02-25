# api/models/exercise.py
"""
Modello Exercise — mappa la tabella 'esercizi'.

Dual ownership:
- trainer_id = NULL → esercizio builtin (seed), visibile a tutti, non modificabile
- trainer_id = X → esercizio custom del trainer, CRUD completo

Campi JSON (muscoli, coaching_cues, errori_comuni, controindicazioni)
serializzati come TEXT e deserializzati nello schema Pydantic.

v2: campi ricchi per scheda professionale (anatomia, biomeccanica,
esecuzione, coaching, media).
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

    # Classificazione biomeccanica (v2)
    force_type: Optional[str] = None         # push, pull, static
    lateral_pattern: Optional[str] = None    # bilateral, unilateral, alternating

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

    # Contenuto ricco (v2)
    descrizione_anatomica: Optional[str] = None     # TEXT: strutture muscolo-articolari
    descrizione_biomeccanica: Optional[str] = None  # TEXT: leve, angoli, catene cinetiche
    setup: Optional[str] = None                     # TEXT: posizione iniziale dettagliata
    esecuzione: Optional[str] = None                # TEXT: movimento step-by-step
    respirazione: Optional[str] = None              # TEXT: pattern respiratorio
    tempo_consigliato: Optional[str] = None         # "3-1-2-0" (ecc-pausa-conc-pausa)
    coaching_cues: Optional[str] = None             # JSON: ["Petto in fuori", "Spingi col tallone"]
    errori_comuni: Optional[str] = None             # JSON: [{"errore":"...", "correzione":"..."}]
    note_sicurezza: Optional[str] = None            # TEXT: avvertenze

    # Istruzioni legacy (JSON: {setup, esecuzione, errori_comuni}) — deprecato v2
    istruzioni: Optional[str] = None

    # Sicurezza (JSON array: ["ginocchio", "schiena"])
    controindicazioni: Optional[str] = None

    # Media (v2)
    image_url: Optional[str] = None   # path relativo: /media/exercises/42/main.jpg
    video_url: Optional[str] = None   # path relativo o URL esterno

    # Metadata
    is_builtin: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None
