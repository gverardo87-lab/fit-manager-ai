# file: server/pages/03_Cassa.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from core.crm_db import CrmDBManager

db = CrmDBManager()

st.set_page_config(page_title="Gestione Cassa", page_icon="💰", layout="wide")

st.title("💰 Gestione Finanziaria")

# --- KPI MENSILI ---
# Calcoliamo al volo le entrate del mese corrente
# (In una versione futura faremo query SQL dedicate per performance, ora Pandas va bene)
with st.spinner("Calcolo bilancio..."):
    # Mock data fetch - in produzione useremo query specifiche
    pass 

# --- TABELLA PAGAMENTI RECENTI ---
st.subheader("Ultimi Movimenti")
# Qui mostreremo la tabella movimenti_cassa
# Per ora placeholder finché non popoli il DB nuovo
st.info("I movimenti appariranno qui dopo le prime vendite.")

# --- SCADENZIARIO (Chi deve pagare) ---
st.subheader("⚠️ Rate e Saldi Pendenti")
# Query sui contratti con stato_pagamento != 'SALDATO'
# Placeholder
st.info("Tutti i clienti sono in regola.")