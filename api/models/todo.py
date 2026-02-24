# api/models/todo.py
"""
Modello Todo — promemoria del trainer.

Entita' semplice: titolo, descrizione opzionale, data scadenza opzionale.
Nessun link a cliente/contratto — i todo sono operativi del trainer.
Multi-tenant via trainer_id (come tutte le entita' business).
"""

from datetime import date, datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class Todo(SQLModel, table=True):
    """ORM model per la tabella 'todos'."""
    __tablename__ = "todos"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    titolo: str = Field(max_length=200)
    descrizione: Optional[str] = None
    data_scadenza: Optional[date] = None
    completato: bool = Field(default=False)
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None
