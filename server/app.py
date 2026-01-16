# server/app.py (Versione FitManager 1.1 - Fix Import)

from __future__ import annotations
import os
import sys
import streamlit as st
import pandas as pd

# ----------------------------------------------------------------
# FIX CRUCIALE: Aggiungiamo la cartella padre al path PRIMA di importare core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# ----------------------------------------------------------------

# ORA possiamo importare i moduli interni senza errori
import core.config 
from core.schedule_db import schedule_db_manager

st.set_page_config(
    page_title="ProFit AI Studio",     
    page_icon="🍎",                    
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNZIONE DI CARICAMENTO DATI ---
def initialize_data():
    if 'data_loaded' not in st.session_state:
        # Carichiamo eventuali dati di base
        try:
            schedule_data = schedule_db_manager.get_schedule_data()
            st.session_state.df_schedule = pd.DataFrame(schedule_data) if schedule_data else pd.DataFrame()
        except Exception:
            st.session_state.df_schedule = pd.DataFrame()
            
        st.session_state.data_loaded = True

initialize_data()

# Refresh forzato
if st.session_state.pop('force_rerun', False):
    st.session_state.pop('data_loaded', None)
    initialize_data()
    st.rerun()

# --- SIDEBAR (Menu Navigazione) ---
with st.sidebar:
    st.title("🍎 ProFit AI") 
    st.caption("Studio Management System")
    st.markdown("---")
    
    st.markdown("### 📅 Operatività")
    st.page_link("pages/10_Pianificazione_Turni.py", label="Agenda Appuntamenti", icon="📆") 
    st.page_link("pages/14_Riepilogo_Calendario.py", label="Calendario Settimanale", icon="🗓️")
    
    st.markdown("### 👥 Clienti & Progressi")
    st.page_link("pages/11_Anagrafica.py", label="I Miei Atleti", icon="🧘")       
    st.page_link("pages/13_Control_Room_Ore.py", label="Diario Misure & Peso", icon="⚖️")       
    st.page_link("pages/12_Gestione_Squadre.py", label="Classi / Gruppi", icon="👯") 

    st.markdown("---")
    st.header("🧠 Intelligenza Artificiale")
    st.page_link("pages/03_Esperto_Tecnico.py", label="AI Nutrizionista", icon="🥗")
    st.page_link("pages/06_Document_Explorer.py", label="Studi & Ricette", icon="📚")


# --- DASHBOARD PRINCIPALE ---
st.title("🍎 Benvenuta in ProFit AI") 
st.markdown("La piattaforma per gestire il tuo **Studio di Personal Training** e i progressi dei tuoi atleti.")
st.divider()

# --- KPI RAPIDI ---
st.subheader("Panoramica Studio")
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4) 

with col_kpi1:
    with st.container(border=True):
        st.subheader("📅 Agenda")
        st.markdown("Gestisci i tuoi **Appuntamenti**.")
        st.page_link("pages/10_Pianificazione_Turni.py", label="Vai all'Agenda", icon="📅")

with col_kpi2:
    with st.container(border=True):
        st.subheader("⚖️ Tracking")
        st.markdown("Aggiorna **Peso e Misure**.")
        st.page_link("pages/13_Control_Room_Ore.py", label="Inserisci Misure", icon="⚖️")

with col_kpi3:
    with st.container(border=True):
        st.subheader("🥗 AI Coach")
        st.markdown("Crea spunti per **Diete**.")
        st.page_link("pages/03_Esperto_Tecnico.py", label="Chiedi all'AI", icon="🥗")

with col_kpi4:
    with st.container(border=True):
        st.subheader("🧘 Clienti")
        st.markdown("Anagrafica completa.")
        st.page_link("pages/11_Anagrafica.py", label="Gestisci Clienti", icon="🧘")

st.divider()
st.caption("FitManager AI v1.0 - Powered by CapoCantiere Core")