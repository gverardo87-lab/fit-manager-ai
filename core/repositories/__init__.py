"""
Repository Package - Data Access Layer Pattern

FASE 2 REFACTORING: Separazione logica accesso dati dal business logic

Architecture:
- BaseRepository: shared connection logic, context manager, utilities
- ClientRepository: clienti + misurazioni CRUD ✅ COMPLETATO
- AgendaRepository: sessioni/eventi CRUD ✅ COMPLETATO
- ContractRepository: contratti + rate CRUD ✅ COMPLETATO
- FinancialRepository: movimenti cassa, spese, bilanci ✅ COMPLETATO

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

__all__ = [
    "BaseRepository",
    "ClientRepository",
    "AgendaRepository",
    "ContractRepository",
    "FinancialRepository",
]
