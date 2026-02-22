# api/models/trainer.py
"""
Modello Trainer — l'utente autenticato del sistema.

Ogni trainer e' un personal trainer / coach che gestisce i propri clienti.
Il trainer_id e' la chiave di multi-tenancy: ogni dato nel DB
appartiene a UN trainer e solo lui puo' vederlo.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class Trainer(SQLModel, table=True):
    """
    ORM model per la tabella 'trainers'.

    Mappa direttamente al DB. I campi sono sia colonne SQLAlchemy
    che attributi Pydantic (grazie a SQLModel).
    """
    __tablename__ = "trainers"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    nome: str = Field(max_length=100)
    cognome: str = Field(max_length=100)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
