# file: server/app.py
import streamlit as st
import os
import sys

# Setup Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="ProFit AI", page_icon="🍎", layout="wide")

st.title("🍎 ProFit AI Studio")

with st.sidebar:
    st.header("Navigazione Moduli")
    
    st.subheader("Gestione Base")
    st.page_link("pages/01_Agenda.py", label="Agenda", icon="📅")
    st.page_link("pages/03_Clienti.py", label="Clienti", icon="👥")
    st.page_link("pages/04_Cassa.py", label="Cassa", icon="💰")
    
    st.divider()
    
    st.subheader("AI & Allenamento")
    st.page_link("pages/02_Assistente_Esperto.py", label="Assistente Esperto", icon="🧠")
    st.page_link("pages/06_Programma_Allenamento.py", label="Generatore Programmi", icon="🏋️")
    st.page_link("pages/05_Assessment_Allenamenti.py", label="Assessment", icon="📊")
    
    st.divider()
    
    st.subheader("Risorse")
    st.page_link("pages/07_Document_Explorer.py", label="Documenti", icon="📚")
    st.page_link("pages/08_Meteo_Cantiere.py", label="Meteo", icon="🌤️")
    st.page_link("pages/09_Bollettino_Mare.py", label="Mare", icon="🌊")

st.info("""
👈 **Seleziona un modulo** dal menu laterale.

**Moduli principali:**
- 🧠 **Assistente Esperto**: Chat intelligente basata su vector store e metodologie di allenamento
- 🏋️ **Generatore Programmi**: Crea workout personalizzati con IA
- 👥 **Gestione Clienti**: Amministra i tuoi clienti
""")