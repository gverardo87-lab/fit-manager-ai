# file: server/app.py
"""
ProFit AI - Dashboard Principale
Esperienza Premium per PT e Clienti
"""

import streamlit as st
import os
import sys
from datetime import datetime

# Setup Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.crm_db import CrmDBManager

# ════════════════════════════════════════════════════════════
# PAGE CONFIG + CUSTOM THEME
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="ProFit AI Studio",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "ProFit AI v1.0 - Piattaforma AI per Personal Trainer",
        "Get Help": "https://github.com/tuoprofit",
        "Report a bug": "https://github.com/tuoprofit/issues"
    }
)

# ════════════════════════════════════════════════════════════
# CUSTOM CSS - TEMA PROFESSIONALE CON DARK MODE SUPPORT
# ════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* ═══════════════════════════════════════════════════════════════ */
    /* TEMA ADATTIVO LIGHT/DARK - Base su variabili CSS native */
    /* ═══════════════════════════════════════════════════════════════ */
    
    :root {
        /* Colori primari del brand */
        --primary: #0066cc;
        --primary-dark: #0052a3;
        --primary-light: #e6f0ff;
        
        --secondary: #00a86b;
        --secondary-dark: #008855;
        --secondary-light: #e6f9f0;
        
        --accent: #ff6b35;
        --accent-light: #fff5f0;
        --danger: #e74c3c;
        
        /* Colori in light mode (default) */
        --bg-main: #f8f9fa;
        --bg-card: #ffffff;
        --bg-sidebar: #f0f2f5;
        --text-primary: #1a1a2e;
        --text-secondary: #5a5a6e;
        --text-muted: #8f8f9e;
        --border-color: #e0e0e8;
        --shadow: 0 2px 8px rgba(0,0,0,0.08);
        --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
    }
    
    /* Dark mode overrides */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #0f1419;
            --bg-card: #1a1e2e;
            --bg-sidebar: #0a0d15;
            --text-primary: #f0f0f5;
            --text-secondary: #b8b8c8;
            --text-muted: #7a7a8a;
            --border-color: #2d3142;
            --shadow: 0 2px 8px rgba(0,0,0,0.3);
            --shadow-lg: 0 8px 24px rgba(0,0,0,0.4);
        }
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* MAIN LAYOUT */
    /* ═══════════════════════════════════════════════════════════════ */
    
    .main {
        background: var(--bg-main);
    }
    
    /* Root container */
    [data-testid="stAppViewContainer"] {
        background: var(--bg-main);
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* SIDEBAR - Alto contrasto indipendentemente dal tema */
    /* ═══════════════════════════════════════════════════════════════ */
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-sidebar) 0%, var(--bg-sidebar) 100%);
        border-right: 1px solid var(--border-color);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--text-primary) !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: var(--text-primary) !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stButton,
    [data-testid="stSidebar"] select,
    [data-testid="stSidebar"] input {
        color: var(--text-primary) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
    }
    
    /* Contrasto migliorato per testi sidebar */
    [data-testid="stSidebar"] label {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* TYPOGRAPHY */
    /* ═══════════════════════════════════════════════════════════════ */
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: none;
    }
    
    h2 {
        font-size: 1.75rem;
        color: var(--text-primary);
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    h3 {
        font-size: 1.25rem;
        color: var(--text-primary);
    }

    p {
        color: var(--text-primary);
        line-height: 1.6;
        font-size: 1rem;
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* CARD SYSTEM */
    /* ═══════════════════════════════════════════════════════════════ */
    
    .card {
        background: var(--bg-card);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
    }

    .card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-4px);
    }

    .card-primary {
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--bg-card) 100%);
        border-left: 4px solid var(--primary);
    }

    .card-success {
        background: linear-gradient(135deg, var(--secondary-light) 0%, var(--bg-card) 100%);
        border-left: 4px solid var(--secondary);
    }

    .card-accent {
        background: linear-gradient(135deg, var(--accent-light) 0%, var(--bg-card) 100%);
        border-left: 4px solid var(--accent);
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* METRIC BOX */
    /* ═══════════════════════════════════════════════════════════════ */
    
    .metric-box {
        background: var(--bg-card);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary);
        margin: 0.5rem 0;
    }

    .metric-label {
        font-size: 0.9rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* BUTTON STYLING */
    /* ═══════════════════════════════════════════════════════════════ */
    
    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(0, 102, 204, 0.2) !important;
    }

    .stButton > button:hover {
        box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3) !important;
        transform: translateY(-2px) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* BADGE STYLING */
    /* ═══════════════════════════════════════════════════════════════ */
    
    .badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }

    .badge-primary { 
        background: var(--primary-light); 
        color: var(--primary); 
        font-weight: 600;
    }
    
    .badge-success { 
        background: var(--secondary-light); 
        color: var(--secondary); 
        font-weight: 600;
    }
    
    .badge-accent { 
        background: var(--accent-light); 
        color: var(--accent); 
        font-weight: 600;
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* FORM ELEMENTS */
    /* ═══════════════════════════════════════════════════════════════ */
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox select,
    .stSlider,
    .stNumberInput {
        color: var(--text-primary) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: var(--text-muted) !important;
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* ALERTS E MESSAGES */
    /* ═══════════════════════════════════════════════════════════════ */
    
    [data-testid="stAlert"] {
        border-radius: 8px;
        border-left: 4px solid var(--primary);
        background: var(--bg-card);
        color: var(--text-primary);
        padding: 1rem;
    }
    
    .stSuccess {
        border-left-color: var(--secondary) !important;
    }
    
    .stError {
        border-left-color: var(--danger) !important;
    }
    
    .stWarning {
        border-left-color: var(--accent) !important;
    }
    
    .stInfo {
        border-left-color: var(--primary) !important;
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* EXPANDER */
    /* ═══════════════════════════════════════════════════════════════ */
    
    .streamlit-expanderHeader {
        background: var(--bg-card);
        border-radius: 8px;
        border: 1px solid var(--border-color);
        color: var(--text-primary) !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--primary-light);
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* DIVIDER */
    /* ═══════════════════════════════════════════════════════════════ */
    
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        margin: 1.5rem 0;
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* SCROLLBAR */
    /* ═══════════════════════════════════════════════════════════════ */
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-main);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-secondary);
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* RESPONSIVE DESIGN */
    /* ═══════════════════════════════════════════════════════════════ */
    
    @media (max-width: 768px) {
        h1 {
            font-size: 1.75rem;
        }
        
        h2 {
            font-size: 1.25rem;
        }
        
        .metric-box {
            padding: 0.75rem;
        }
        
        .card {
            padding: 1rem;
        }
    }
    
    @media (max-width: 480px) {
        h1 {
            font-size: 1.5rem;
        }
        
        p {
            font-size: 0.95rem;
        }
    }

    /* ═══════════════════════════════════════════════════════════════ */
    /* CUSTOM UTILITIES */
    /* ═══════════════════════════════════════════════════════════════ */
    
    .section-header {
        color: var(--text-primary);
        margin-bottom: 1rem;
    }
    
    .section-header h2 {
        color: var(--primary);
        margin: 0;
    }
    
    .section-header p {
        color: var(--text-secondary);
        margin: 0.25rem 0 0 0;
        font-size: 0.9rem;
    }
    
    /* Animazioni fluide */
    * {
        transition-property: background-color, color, border-color, box-shadow;
        transition-duration: 0.2s;
        transition-timing-function: ease;
    }
    
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 💪 ProFit AI")
    st.caption("Piattaforma Premium per Personal Trainer")
    
    st.divider()
    
    # User Profile Quick View
    db = CrmDBManager()
    
    st.markdown("#### 👤 Sezioni Principali")
    st.page_link("pages/01_Agenda.py", label="📅 Agenda", icon="📅")
    st.page_link("pages/03_Clienti.py", label="👥 Clienti", icon="👥")
    st.page_link("pages/04_Cassa.py", label="💰 Cassa", icon="💰")
    
    st.divider()
    
    st.markdown("#### 🤖 Strumenti AI")
    st.page_link("pages/02_Assistente_Esperto.py", label="🧠 Assistente Esperto", icon="🧠")
    st.page_link("pages/07_Programma_Allenamento.py", label="🏋️ Generatore Programmi", icon="🏋️")
    st.page_link("pages/06_Assessment_Allenamenti.py", label="📊 Assessment", icon="📊")
    st.page_link("pages/05_Analisi_Margine_Orario.py", label="📊 Margine Orario", icon="📊")
    
    st.divider()
    
    st.markdown("#### 📚 Risorse")
    st.page_link("pages/08_Document_Explorer.py", label="📚 Documenti", icon="📚")
    st.page_link("pages/09_Meteo_Cantiere.py", label="🌤️ Meteo", icon="🌤️")
    st.page_link("pages/10_Bollettino_Mare.py", label="🌊 Mare", icon="🌊")
    
    st.divider()
    
    # Stats Footer
    try:
        clienti_count = len(db.get_clienti_attivi())
        st.metric("Clienti Attivi", clienti_count)
    except:
        pass
    
    st.caption("🔐 v1.0 | © 2026 ProFit AI")

# ════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ════════════════════════════════════════════════════════════

# Header con Greeting
hour = datetime.now().hour
greeting = "Buongiorno" if hour < 12 else "Buonasera" if hour < 18 else "Buonasera"

st.markdown(f"""
<div style="margin-bottom: 2rem;">
    <h1>💪 {greeting}, Coach!</h1>
    <p style="font-size: 1.1rem; color: var(--text-secondary); margin: 0;">
        Bentornato in ProFit AI - La tua piattaforma intelligente per il personal training
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ════════════════════════════════════════════════════════════
# DASHBOARD CARDS - QUICK STATS
# ════════════════════════════════════════════════════════════

st.markdown("### 📊 Dashboard Veloce")

col1, col2, col3, col4 = st.columns(4, gap="medium")

db = CrmDBManager()

try:
    clienti_attivi = len(db.get_clienti_attivi())
    with col1:
        st.markdown("""
        <div class="card card-primary">
            <div class="metric-box">
                <div class="metric-label">👥 Clienti Attivi</div>
                <div class="metric-value">{}</div>
                <small style="color: var(--text-secondary);">In seguito attualmente</small>
            </div>
        </div>
        """.format(clienti_attivi), unsafe_allow_html=True)
except:
    with col1:
        st.markdown("""
        <div class="card card-primary">
            <div class="metric-box">
                <div class="metric-label">👥 Clienti Attivi</div>
                <div class="metric-value">-</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card card-success">
        <div class="metric-box">
            <div class="metric-label">🏋️ Programmi Creati</div>
            <div class="metric-value">0</div>
            <small style="color: var(--text-secondary);">Questa settimana</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card card-accent">
        <div class="metric-box">
            <div class="metric-label">📈 Progressi Tracciati</div>
            <div class="metric-value">0</div>
            <small style="color: var(--text-secondary);">Ultimi 7 giorni</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="card">
        <div class="metric-box">
            <div class="metric-label">🧠 Ricerche KB</div>
            <div class="metric-value">0</div>
            <small style="color: var(--text-secondary);">Assistente esperto</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# QUICK ACTIONS
# ════════════════════════════════════════════════════════════

st.divider()
st.markdown("### ⚡ Azioni Rapide")

col_action1, col_action2, col_action3, col_action4 = st.columns(4, gap="medium")

with col_action1:
    if st.button("➕ Nuovo Cliente", use_container_width=True, key="btn_new_client"):
        st.switch_page("pages/03_Clienti.py")

with col_action2:
    if st.button("📋 Genera Programma", use_container_width=True, key="btn_new_program"):
        st.switch_page("pages/07_Programma_Allenamento.py")

with col_action3:
    if st.button("💬 Chat Esperto", use_container_width=True, key="btn_expert"):
        st.switch_page("pages/02_Assistente_Esperto.py")

with col_action4:
    if st.button("📊 Visualizza Calendario", use_container_width=True, key="btn_calendar"):
        st.switch_page("pages/01_Agenda.py")

# ════════════════════════════════════════════════════════════
# FEATURED SECTIONS
# ════════════════════════════════════════════════════════════

st.divider()
st.markdown("### 🌟 Funzionalità Principali")

col_feat1, col_feat2 = st.columns(2, gap="large")

with col_feat1:
    st.markdown("""
    <div class="card card-primary">
        <h3 style="margin-top: 0; color: var(--primary);">🧠 Assistente Esperto</h3>
        <p>Chat intelligente basata su vector store e metodologie avanzate di allenamento. Accedi a una knowledge base di 400+ chunk di documentazione specializzata.</p>
        <span class="badge badge-primary">RAG Avanzato</span>
        <span class="badge badge-primary">AI-Powered</span>
    </div>
    """, unsafe_allow_html=True)

with col_feat2:
    st.markdown("""
    <div class="card card-success">
        <h3 style="margin-top: 0; color: var(--secondary);">🏋️ Generatore di Programmi</h3>
        <p>Crea workout personalizzati con IA che tiene conto di goal, livello, disponibilità e limitazioni. Supporta periodizzazione avanzata e strategie di progressione.</p>
        <span class="badge badge-success">Ipertrofia</span>
        <span class="badge badge-success">Forza</span>
        <span class="badge badge-success">Resistenza</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

col_feat3, col_feat4 = st.columns(2, gap="large")

with col_feat3:
    st.markdown("""
    <div class="card card-accent">
        <h3 style="margin-top: 0; color: var(--accent);">📊 Dashboard Analytics</h3>
        <p>Monitora i progressi dei tuoi clienti con visualizzazioni avanzate. Trackizza forza, volume, peso corporeo e performance nel tempo.</p>
        <span class="badge badge-accent">Real-time</span>
        <span class="badge badge-accent">Grafici Interattivi</span>
    </div>
    """, unsafe_allow_html=True)

with col_feat4:
    st.markdown("""
    <div class="card">
        <h3 style="margin-top: 0; color: var(--primary);">👥 Gestione Clienti</h3>
        <p>Interfaccia completa per gestire anagrafe, progressi, programmi assegnati e comunicazioni. Database centralizzato e sempre sincronizzato.</p>
        <span class="badge badge-primary">Database</span>
        <span class="badge badge-primary">CRM</span>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════

st.divider()

col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.caption("📧 Support: support@profit-ai.com")

with col_footer2:
    st.caption("🔐 Privacy & Security | GDPR Compliant")

with col_footer3:
    st.caption(f"⏰ {datetime.now().strftime('%d %b %Y - %H:%M')}")

st.markdown("""
---
<center>
<small>ProFit AI v1.0 | Developed with ❤️ | © 2026</small>
</center>
""", unsafe_allow_html=True)
