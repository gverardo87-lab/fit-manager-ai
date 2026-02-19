# file: server/app.py
"""
ProFit AI Studio - Entrypoint con st.navigation()

Router centrale: definisce le pagine e le sezioni della sidebar.
Il contenuto della dashboard e' in app_dashboard.py.
"""

import streamlit as st
from datetime import date

st.set_page_config(
    page_title="ProFit AI Studio",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "ProFit AI v2.0 - Piattaforma AI per Personal Trainer",
    }
)

# ════════════════════════════════════════════════════════════
# NAVIGAZIONE CON SEZIONI
# ════════════════════════════════════════════════════════════

nav = st.navigation({
    "": [
        st.Page("app_dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
    ],
    "Gestione": [
        st.Page("pages/01_Agenda.py", title="Agenda", icon=":material/calendar_month:"),
        st.Page("pages/03_Clienti.py", title="Clienti", icon=":material/group:"),
        st.Page("pages/04_Cassa.py", title="Cassa & Bilancio", icon=":material/account_balance_wallet:"),
    ],
    "Strumenti AI": [
        st.Page("pages/02_Assistente_Esperto.py", title="Assistente Esperto", icon=":material/psychology:"),
        st.Page("pages/07_Programma_Allenamento.py", title="Programmi", icon=":material/fitness_center:"),
        st.Page("pages/06_Assessment_Allenamenti.py", title="Assessment", icon=":material/monitoring:"),
        st.Page("pages/05_Analisi_Margine_Orario.py", title="Margine Orario", icon=":material/analytics:"),
    ],
    "Risorse": [
        st.Page("pages/08_Document_Explorer.py", title="Documenti", icon=":material/description:"),
        st.Page("pages/09_Impostazioni.py", title="Impostazioni", icon=":material/settings:"),
    ],
})

# Footer sidebar
with st.sidebar:
    st.divider()
    st.caption(f"ProFit AI Studio v2.0 · {date.today().strftime('%d %b %Y')}")

nav.run()
