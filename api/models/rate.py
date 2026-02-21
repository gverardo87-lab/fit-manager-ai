# api/models/rate.py
"""
Modello Rate — mappa la tabella 'rate_programmate' esistente in SQLite.

IMPORTANTE: la tabella esiste gia' con 26 record (14 PENDENTE, 12 SALDATA).

Multi-tenancy:
- Nessun trainer_id diretto. La tenancy e' garantita dal Deep Relational IDOR:
    Rate.id_contratto -> Contract.trainer_id
  Il router verifica SEMPRE che il contratto appartenga al trainer autenticato
  prima di qualsiasi operazione sulla rata.

Questa scelta evita ridondanza e mantiene il single source of truth
per l'ownership sul contratto.
"""

from datetime import date
from typing import Optional
from sqlmodel import SQLModel, Field


class Rate(SQLModel, table=True):
    """
    ORM model per la tabella 'rate_programmate' esistente.

    Mappa 1:1 le colonne SQLite. L'ownership e' derivata:
    Rate -> Contract -> trainer_id (Deep Relational IDOR).
    """
    __tablename__ = "rate_programmate"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_contratto: int = Field(foreign_key="contratti.id")
    data_scadenza: date
    importo_previsto: float
    descrizione: Optional[str] = None
    stato: str = Field(default="PENDENTE")
    importo_saldato: float = Field(default=0)
