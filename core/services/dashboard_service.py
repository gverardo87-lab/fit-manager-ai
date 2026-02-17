"""
Dashboard Service - Business Logic per la Dashboard

Disaccoppia la UI dalla logica dati, applica caching intelligente
"""

from typing import Dict, Any
from datetime import datetime
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.crm_db import CrmDBManager
from core.error_handler import safe_operation, ErrorSeverity


class DashboardService:
    """
    Service layer per la dashboard principale
    
    Responsabilità:
    - Aggregazione dati da DB
    - Calcoli KPI
    - Cache delle query costose
    
    Pattern: Usa @safe_operation per error handling (no try/except manuali)
    """
    
    def __init__(self):
        self._crm_db = CrmDBManager()
    
    @st.cache_data(ttl=300)
    @safe_operation(
        operation_name="Conta Clienti Attivi",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=0
    )
    def get_active_clients_count(_self) -> int:
        """Conta clienti attivi (CACHED 5min)"""
        return len(_self._crm_db.get_clienti_attivi())
    
    @st.cache_data(ttl=300)
    @safe_operation(
        operation_name="Calcola Fatturato Mensile",
        severity=ErrorSeverity.MEDIUM,
        fallback_return=0.0
    )
    def get_monthly_revenue(_self, anno: int, mese: int) -> float:
        """Calcola fatturato mensile (CACHED 5min)"""
        movimenti = _self._crm_db.get_movimenti_cassa(anno=anno, mese=mese)
        if not movimenti:
            return 0.0
        
        entrate = sum(m['importo'] for m in movimenti if m['tipo'] == 'ENTRATA')
        return entrate
    
    @st.cache_data(ttl=300)
    @safe_operation(
        operation_name="Conta Fatture Pending",
        severity=ErrorSeverity.LOW,
        fallback_return=0
    )
    def get_pending_invoices_count(_self) -> int:
        """Conta contratti con pagamenti parziali (CACHED 5min)"""
        contratti = _self._crm_db.get_contratti()
        pending = [c for c in contratti if c.get('stato_pagamento') == 'PARZIALE']
        return len(pending)
    
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
        
        Returns:
            Dict con chiavi: active_clients, monthly_revenue, pending_invoices
        """
        now = datetime.now()
        
        return {
            'active_clients': _self.get_active_clients_count(),
            'monthly_revenue': _self.get_monthly_revenue(now.year, now.month),
            'pending_invoices': _self.get_pending_invoices_count()
        }
