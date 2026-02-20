"""
Core Services Package

Service layer che disaccoppia UI da DB e business logic.
Tutti i service usano @safe_operation per error handling.
"""

from .backup_service import BackupService

__all__ = [
    'BackupService',
]
