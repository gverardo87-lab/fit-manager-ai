# api/models/client.py
"""
Modello Client — mappa la tabella 'clienti' esistente in SQLite.

IMPORTANTE: questa tabella esiste gia'. SQLModel non la ricrea,
ma la usa per le query ORM. La colonna trainer_id viene aggiunta
dalla migrazione in api/main.py al primo avvio.
"""

from datetime import date, datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class Client(SQLModel, table=True):
    """
    ORM model per la tabella 'clienti' esistente.

    Mappa 1:1 le colonne SQLite. Il campo trainer_id e' la FK
    per la multi-tenancy: ogni client appartiene a un trainer.
    """
    __tablename__ = "clienti"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: Optional[int] = Field(default=None, foreign_key="trainers.id", index=True)
    nome: str
    cognome: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    data_nascita: Optional[date] = None
    sesso: Optional[str] = None
    anamnesi_json: Optional[str] = None
    stato: str = Field(default="Attivo")
    note_interne: Optional[str] = None
    data_creazione: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None
