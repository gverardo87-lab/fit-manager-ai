# api/models/exercise_relation.py
"""
Modello ExerciseRelation — catena progressioni/regressioni tra esercizi.

tipo_relazione:
- "progression" → esercizio piu' difficile
- "regression"  → esercizio piu' facile
- "variation"   → variante equivalente
"""

from typing import Optional
from sqlmodel import SQLModel, Field


class ExerciseRelation(SQLModel, table=True):
    __tablename__ = "esercizi_relazioni"

    id: Optional[int] = Field(default=None, primary_key=True)
    exercise_id: int = Field(foreign_key="esercizi.id", index=True)
    related_exercise_id: int = Field(foreign_key="esercizi.id", index=True)
    tipo_relazione: str  # "progression" | "regression" | "variation"
