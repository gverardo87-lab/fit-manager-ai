"""
Repository Package - Data Access Layer Pattern

FASE 2 REFACTORING: Separazione logica accesso dati dal business logic

Architecture:
- BaseRepository: shared connection logic, context manager, utilities
- ClientRepository: clienti + misurazioni CRUD
- AgendaRepository: sessioni/eventi CRUD
- ContractRepository: contratti + rate CRUD
- FinancialRepository: movimenti cassa, spese, bilanci
- AssessmentRepository: assessment iniziali + follow-up
- WorkoutRepository: piani allenamento + progress records

Tutti repository:
- Accettano SOLO Pydantic models in input
- Ritornano SOLO Pydantic models in output
- Usano @safe_operation per error handling
- Isolano SQL dentro repository (NO SQL in service layer)
"""

from .base_repository import BaseRepository
from .client_repository import ClientRepository
from .agenda_repository import AgendaRepository
from .contract_repository import ContractRepository
from .financial_repository import FinancialRepository
from .assessment_repository import AssessmentRepository
from .workout_repository import WorkoutRepository

__all__ = [
    "BaseRepository",
    "ClientRepository",
    "AgendaRepository",
    "ContractRepository",
    "FinancialRepository",
    "AssessmentRepository",
    "WorkoutRepository",
]
