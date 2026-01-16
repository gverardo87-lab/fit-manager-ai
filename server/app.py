# file: server/app.py
import streamlit as st
import os
import sys

# Setup Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="ProFit AI", page_icon="🍎", layout="wide")

st.title("🍎 ProFit AI Studio")

with st.sidebar:
    st.header("Navigazione")
    
    # Link SOLO alle pagine esistenti
    st.page_link("pages/01_Agenda.py", label="Agenda Operativa", icon="📅")
    st.page_link("pages/02_Clienti.py", label="Gestione Clienti", icon="👥")
    
    st.markdown("---")
    st.subheader("Strumenti AI")
    # Verifica che questi file esistano prima di cliccare
    if os.path.exists(os.path.join(os.path.dirname(__file__), "pages/03_Esperto_Tecnico.py")):
        st.page_link("pages/03_Esperto_Tecnico.py", label="AI Coach", icon="🧠")
    
    if os.path.exists(os.path.join(os.path.dirname(__file__), "pages/06_Document_Explorer.py")):
        st.page_link("pages/06_Document_Explorer.py", label="Documenti", icon="📂")

st.info("👈 Seleziona un modulo dal menu laterale per iniziare.")