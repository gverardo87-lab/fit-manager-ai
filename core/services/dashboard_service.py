"""
Dashboard Service - Business Logic per la Dashboard

FASE 2 REFACTORING: Migrato a Repository Pattern

Disaccoppia la UI dalla logica dati, applica caching intelligente
"""

from typing import Dict, Any
from datetime import datetime, date
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.repositories import ClientRepository, FinancialRepository, ContractRepository
from core.error_handler import safe_operation, ErrorSeverity


class DashboardService:
    """
    Service layer per la dashboard principale
    
    FASE 2: Usa Repository Pattern invece di CrmDBManager monolitico
    
    Responsabilità:
    - Aggregazione dati da repository
    - Calcoli KPI
    - Cache delle query costose
    
    Pattern: Usa @safe_operation per error handling (no try/except manuali)
    """
    
    def __init__(self):
        # FASE 2: Dependency Injection dei repository
        self._client_repo = ClientRepository()
        self._financial_repo = FinancialRepository()
        self._contract_repo = ContractRepository()
    
    @st.cache_data(ttl=300)
    @safe_operation(
        operation_name="Conta Clienti Attivi",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=0
    )
    def get_active_clients_count(_self) -> int:
        """Conta clienti attivi (CACHED 5min)"""
        clients = _self._client_repo.get_all_active()
        return len(clients)
    
    @st.cache_data(ttl=300)
    @safe_operation(
        operation_name="Calcola Fatturato Mensile",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=0.0
    )
    def get_monthly_revenue(_self, anno: int, mese: int) -> float:
        """
        Calcola fatturato mensile (CACHED 5min)
        
        FASE 2: Usa FinancialRepository.get_cash_balance()
        """
        # Calculate period dates (first day to last day of month)
        from calendar import monthrange
        start_date = date(anno, mese, 1)
        last_day = monthrange(anno, mese)[1]
        end_date = date(anno, mese, last_day)
        
        # Get cash balance for period
        balance = _self._financial_repo.get_cash_balance(start_date, end_date)
        return balance['incassato']  # Return only entrate
    
    @st.cache_data(ttl=300)
    @safe_operation(
        operation_name="Conta Rate Pendenti",
        severity=ErrorSeverity.LOW,
        fallback_return=0
    )
    def get_pending_invoices_count(_self) -> int:
        """
        Conta rate pendenti (CACHED 5min)
        
        FASE 2: Usa ContractRepository.get_pending_rates()
        """
        pending_rates = _self._contract_repo.get_pending_rates(only_future=True)
        return len(pending_rates)
    
    @st.cache_data(ttl=300)
    @safe_operation(
        operation_name="Carica Dashboard Summary",
        severity=ErrorSeverity.HIGH,
        fallback_return={
            'active_clients': 0,
            'monthly_revenue': 0.0,
            'pending_invoices': 0
        }
    )
    def get_dashboard_summary(_self) -> Dict[str, Any]:
        """
        Ottiene tutti i dati della dashboard in una singola chiamata
        Ottimizza le query multiple (CACHED 5min)
        
        FASE 2: Tutti i dati vengono dai repository
        
        Returns:
            Dict con chiavi: active_clients, monthly_revenue, pending_invoices
        """
        now = datetime.now()
        
        return {
            'active_clients': _self.get_active_clients_count(),
            'monthly_revenue': _self.get_monthly_revenue(now.year, now.month),
            'pending_invoices': _self.get_pending_invoices_count()
        }
