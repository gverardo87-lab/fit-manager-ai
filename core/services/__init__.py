"""
Core Services Package

Service layer che disaccoppia UI da DB e business logic.
Tutti i service usano @safe_operation per error handling.
"""

from .dashboard_service import DashboardService

__all__ = [
    'DashboardService',
]
