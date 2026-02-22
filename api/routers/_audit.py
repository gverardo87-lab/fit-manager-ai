# api/routers/_audit.py
"""
Utility condivisa per l'audit trail.

log_audit() registra un'azione nella tabella audit_log.
NON fa session.commit() — il chiamante committa atomicamente.
"""

import json
from sqlmodel import Session
from api.models.audit_log import AuditLog


def log_audit(
    session: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    trainer_id: int,
    changes: dict | None = None,
) -> None:
    """
    Registra un'azione nel log di audit.

    Args:
        entity_type: 'client', 'contract', 'rate', 'event', 'movement', 'recurring_expense'
        entity_id: ID del record modificato
        action: 'CREATE', 'UPDATE', 'DELETE', 'RESTORE'
        trainer_id: chi ha eseguito l'azione
        changes: dict con diff campo-per-campo (solo UPDATE)
                 es. {"prezzo_totale": {"old": 100, "new": 150}}
    """
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changes=json.dumps(changes, default=str) if changes else None,
        trainer_id=trainer_id,
    )
    session.add(entry)
