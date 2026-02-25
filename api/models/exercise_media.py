# api/models/exercise_media.py
"""
Modello ExerciseMedia — galleria media per esercizi.

Ogni esercizio puo' avere N immagini/video, ordinati per 'ordine'.
trainer_id = NULL per media su esercizi builtin (seed futuro).
trainer_id = X per media caricati dal trainer su esercizi custom.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class ExerciseMedia(SQLModel, table=True):
    __tablename__ = "esercizi_media"

    id: Optional[int] = Field(default=None, primary_key=True)
    exercise_id: int = Field(foreign_key="esercizi.id", index=True)
    trainer_id: Optional[int] = Field(default=None, foreign_key="trainers.id")
    tipo: str                  # "image" | "video"
    url: str                   # path relativo: /media/exercises/42/img_001.jpg
    ordine: int = Field(default=0)
    descrizione: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
