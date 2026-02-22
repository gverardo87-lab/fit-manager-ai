# api/models/audit_log.py
"""
Modello AuditLog — registra ogni mutazione (CREATE, UPDATE, DELETE, RESTORE).

Ogni riga rappresenta un'azione su un'entita' del CRM.
Il campo 'changes' contiene un JSON con i valori prima/dopo per gli UPDATE.

Multi-tenancy: trainer_id diretto (chi ha fatto l'azione).
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class AuditLog(SQLModel, table=True):
    """
    ORM model per la tabella 'audit_log'.

    entity_type: 'client', 'contract', 'rate', 'event', 'movement', 'recurring_expense'
    action: 'CREATE', 'UPDATE', 'DELETE', 'RESTORE'
    changes: JSON string con diff campo-per-campo (solo per UPDATE)
    """
    __tablename__ = "audit_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str
    entity_id: int
    action: str
    changes: Optional[str] = None
    trainer_id: int = Field(foreign_key="trainers.id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
