# api/models/event.py
"""
Modello Event — mappa la tabella 'agenda' esistente in SQLite.

IMPORTANTE: la tabella esiste gia' con 19 record.
La colonna trainer_id viene aggiunta dalla migrazione in api/main.py.

Multi-tenancy:
- trainer_id: FK diretta per filtrare TUTTI gli eventi (con e senza cliente)
- id_cliente: FK verso clienti (solo per eventi PT, CONSULENZA con cliente)
- id_contratto: FK verso contratti (solo per eventi PT che consumano crediti)

Un evento puo' essere:
- Personale (PT): ha id_cliente + id_contratto, consuma crediti
- Generico (SALA, CORSO, YOGA): ha solo trainer_id, nessun cliente
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Event(SQLModel, table=True):
    """
    ORM model per la tabella 'agenda' esistente.

    Mappa 1:1 le colonne SQLite. Il campo trainer_id e' la FK
    per la multi-tenancy diretta: ogni evento appartiene a un trainer.
    """
    __tablename__ = "agenda"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: Optional[int] = Field(default=None, foreign_key="trainers.id", index=True)
    data_inizio: datetime
    data_fine: datetime
    categoria: str
    titolo: Optional[str] = None
    id_cliente: Optional[int] = Field(default=None, foreign_key="clienti.id")
    id_contratto: Optional[int] = None
    stato: str = Field(default="Programmato")
    note: Optional[str] = None
    data_creazione: Optional[datetime] = Field(default_factory=datetime.utcnow)
