# api/models/contract.py
"""
Modello Contract — mappa la tabella 'contratti' esistente in SQLite.

IMPORTANTE: la tabella esiste gia' con 7 record (tutti chiuso=0).
La colonna trainer_id viene aggiunta dalla migrazione in api/main.py.

Multi-tenancy:
- trainer_id: FK diretta verso trainers (aggiunta via migration)
- id_cliente: FK verso clienti (il cliente DEVE appartenere allo stesso trainer)

Deep Relational IDOR chain:
  Rate -> Contract.trainer_id (verifica diretta)
  Contract -> Client.trainer_id (verifica coerenza su POST)
"""

from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Contract(SQLModel, table=True):
    """
    ORM model per la tabella 'contratti' esistente.

    Mappa 1:1 le colonne SQLite. Il campo trainer_id e' la FK
    per la multi-tenancy: ogni contratto appartiene a un trainer.
    """
    __tablename__ = "contratti"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: Optional[int] = Field(default=None, foreign_key="trainers.id", index=True)
    id_cliente: int = Field(foreign_key="clienti.id")
    tipo_pacchetto: Optional[str] = None
    data_vendita: Optional[date] = Field(default_factory=date.today)
    data_inizio: Optional[date] = None
    data_scadenza: Optional[date] = None
    crediti_totali: Optional[int] = None
    crediti_usati: int = Field(default=0)
    prezzo_totale: Optional[float] = None
    totale_versato: float = Field(default=0)
    stato_pagamento: str = Field(default="PENDENTE")
    note: Optional[str] = None
    chiuso: bool = Field(default=False)
