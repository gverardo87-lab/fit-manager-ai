# file: server/app.py
"""
ProFit AI Studio - Dashboard Principale
Dark theme professionale con dati live.
"""

import streamlit as st
import sys
import os
from datetime import datetime, date, timedelta
from calendar import monthrange

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.repositories import ClientRepository, AgendaRepository, FinancialRepository, ContractRepository
from core.ui_components import load_custom_css, format_currency

# ════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="ProFit AI Studio",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "ProFit AI v2.0 - Piattaforma AI per Personal Trainer",
    }
)

load_custom_css()

# ════════════════════════════════════════════════════════════
# DATA - Load once, use everywhere
# ════════════════════════════════════════════════════════════

client_repo = ClientRepository()
agenda_repo = AgendaRepository()
financial_repo = FinancialRepository()
contract_repo = ContractRepository()

oggi = date.today()
primo_mese = date(oggi.year, oggi.month, 1)
ultimo_giorno = monthrange(oggi.year, oggi.month)[1]
ultimo_mese = date(oggi.year, oggi.month, ultimo_giorno)

# Safe data fetching
try:
    clienti_attivi = client_repo.get_all_active()
    n_clienti = len(clienti_attivi)
except Exception:
    clienti_attivi = []
    n_clienti = 0

try:
    eventi_oggi = agenda_repo.get_events_by_range(oggi, oggi)
    n_eventi_oggi = len(eventi_oggi)
except Exception:
    eventi_oggi = []
    n_eventi_oggi = 0

try:
    bilancio = financial_repo.get_cash_balance(primo_mese, ultimo_mese)
    entrate_mese = bilancio.get('incassato', 0) or 0
except Exception:
    entrate_mese = 0

try:
    prossimi_eventi = agenda_repo.get_events_by_range(oggi, oggi + timedelta(days=7))
except Exception:
    prossimi_eventi = []

try:
    sessioni_stale = agenda_repo.get_stale_sessions()
except Exception:
    sessioni_stale = []

# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 1rem 0;">
        <h2 style="margin: 0; font-size: 1.4rem; background: linear-gradient(135deg, #3b82f6, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">ProFit AI</h2>
        <p style="margin: 0.25rem 0 0 0; color: var(--text-muted); font-size: 0.75rem; letter-spacing: 1px; text-transform: uppercase;">Studio Personal Training</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown('<p style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.5rem; font-weight: 700;">Gestione</p>', unsafe_allow_html=True)
    st.page_link("pages/01_Agenda.py", label="Agenda", icon=":material/calendar_month:")
    st.page_link("pages/03_Clienti.py", label="Clienti", icon=":material/group:")
    st.page_link("pages/04_Cassa.py", label="Cassa & Bilancio", icon=":material/account_balance_wallet:")

    st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.5rem; font-weight: 700;">Strumenti AI</p>', unsafe_allow_html=True)
    st.page_link("pages/02_Assistente_Esperto.py", label="Assistente Esperto", icon=":material/psychology:")
    st.page_link("pages/07_Programma_Allenamento.py", label="Programmi", icon=":material/fitness_center:")
    st.page_link("pages/06_Assessment_Allenamenti.py", label="Assessment", icon=":material/monitoring:")
    st.page_link("pages/05_Analisi_Margine_Orario.py", label="Margine Orario", icon=":material/analytics:")

    st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.5rem; font-weight: 700;">Risorse</p>', unsafe_allow_html=True)
    st.page_link("pages/08_Document_Explorer.py", label="Documenti", icon=":material/description:")

    st.divider()

    # Footer
    st.markdown(f"""
    <div style="padding: 0.5rem 0; text-align: center;">
        <p style="color: var(--text-muted); font-size: 0.7rem; margin: 0;">v2.0 &middot; {oggi.strftime('%d %b %Y')}</p>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════

hour = datetime.now().hour
if hour < 12:
    greeting = "Buongiorno"
elif hour < 18:
    greeting = "Buon pomeriggio"
else:
    greeting = "Buonasera"

st.markdown(f"""
<div style="margin-bottom: 1.5rem;">
    <h1 style="margin-bottom: 0.25rem;">{greeting}, Coach</h1>
    <p style="color: var(--text-secondary); margin: 0; font-size: 1rem;">
        Ecco la tua situazione di oggi, {oggi.strftime('%A %d %B %Y').capitalize()}
    </p>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# KPI ROW - Dati reali
# ════════════════════════════════════════════════════════════

col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Clienti Attivi</div>
        <div class="kpi-value" style="color: var(--primary);">{n_clienti}</div>
        <div class="kpi-trend neutral">portfolio attuale</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    trend_class = "positive" if n_eventi_oggi > 0 else "neutral"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Sessioni Oggi</div>
        <div class="kpi-value" style="color: var(--secondary);">{n_eventi_oggi}</div>
        <div class="kpi-trend {trend_class}">{'in programma' if n_eventi_oggi > 0 else 'nessuna sessione'}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    entrate_formatted = format_currency(entrate_mese, decimals=0)
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Entrate Mese</div>
        <div class="kpi-value" style="color: var(--accent);">{entrate_formatted}</div>
        <div class="kpi-trend neutral">{oggi.strftime('%B %Y').capitalize()}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    n_stale = len(sessioni_stale)
    stale_color = "var(--danger)" if n_stale > 0 else "var(--secondary)"
    stale_trend_class = "negative" if n_stale > 0 else "positive"
    stale_trend_text = "da gestire!" if n_stale > 0 else "tutto in ordine"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Sessioni Scadute</div>
        <div class="kpi-value" style="color: {stale_color};">{n_stale}</div>
        <div class="kpi-trend {stale_trend_class}">{stale_trend_text}</div>
    </div>
    """, unsafe_allow_html=True)

# ─── Warning sessioni stale ───
if sessioni_stale:
    st.divider()
    st.warning(f"**{len(sessioni_stale)} sessioni passate mai confermate** - Appuntamenti con stato 'Programmato' e data gia' trascorsa.")
    with st.expander(f"Vedi {len(sessioni_stale)} sessioni da gestire"):
        for s in sessioni_stale:
            col_s1, col_s2, col_s3 = st.columns([3, 1, 2])
            with col_s1:
                nome = s['cliente_nome'] or s['titolo'] or 'Evento'
                data_str = str(s['data_inizio'])[:16] if s['data_inizio'] else '?'
                st.markdown(f"**{nome}** - {data_str}")
            with col_s2:
                st.caption(f"{s['days_overdue']}g fa")
            with col_s3:
                c_a, c_b = st.columns(2)
                if c_a.button("Conferma", key=f"stale_ok_{s['id']}", use_container_width=True):
                    agenda_repo.confirm_event(s['id'])
                    st.rerun()
                if c_b.button("Cancella", key=f"stale_no_{s['id']}", use_container_width=True):
                    agenda_repo.cancel_event(s['id'])
                    st.rerun()

# ════════════════════════════════════════════════════════════
# CONTENT ROW
# ════════════════════════════════════════════════════════════

st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

col_left, col_right = st.columns([3, 2], gap="large")

# ─── Prossime sessioni ───
with col_left:
    st.markdown("### Prossime sessioni")

    if prossimi_eventi:
        # Show next 6 events max
        for evento in prossimi_eventi[:6]:
            ev_date = str(evento.data_inizio)[:10] if evento.data_inizio else "?"
            ev_time = str(evento.data_inizio)[11:16] if evento.data_inizio and len(str(evento.data_inizio)) > 10 else ""
            ev_tipo = getattr(evento, 'tipo', 'PT') or 'PT'
            ev_stato = getattr(evento, 'stato', '') or ''
            ev_cliente_id = getattr(evento, 'id_cliente', None)

            # Get client name
            client_name = "Evento"
            if ev_cliente_id:
                try:
                    cliente = client_repo.get_by_id(ev_cliente_id)
                    if cliente:
                        client_name = f"{cliente.nome} {cliente.cognome}"
                except Exception:
                    pass

            # Determine badge
            is_today = ev_date == str(oggi)
            date_label = "OGGI" if is_today else ev_date[5:]  # MM-DD
            date_color = "var(--secondary)" if is_today else "var(--text-muted)"

            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 1rem; padding: 0.6rem 0; border-bottom: 1px solid var(--border-subtle);">
                <div style="min-width: 60px; text-align: center;">
                    <div style="color: {date_color}; font-weight: 700; font-size: 0.8rem;">{date_label}</div>
                    <div style="color: var(--text-muted); font-size: 0.75rem;">{ev_time}</div>
                </div>
                <div style="flex: 1;">
                    <div style="color: var(--text-primary); font-weight: 600; font-size: 0.9rem;">{client_name}</div>
                    <div style="color: var(--text-muted); font-size: 0.75rem;">{ev_tipo}</div>
                </div>
                <div>
                    <span class="badge badge-{'success' if ev_stato in ('CONFERMATO', 'COMPLETATO') else 'primary'}" style="font-size: 0.7rem;">{ev_stato or ev_tipo}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
            <p style="font-size: 2rem; margin-bottom: 0.5rem;">0</p>
            <p style="font-size: 0.9rem;">Nessuna sessione in programma</p>
        </div>
        """, unsafe_allow_html=True)

# ─── Azioni rapide + info ───
with col_right:
    st.markdown("### Azioni rapide")

    c1, c2 = st.columns(2, gap="small")
    with c1:
        if st.button("Nuovo Cliente", use_container_width=True, key="btn_new_client"):
            st.switch_page("pages/03_Clienti.py")
    with c2:
        if st.button("Genera Programma", use_container_width=True, key="btn_new_program"):
            st.switch_page("pages/07_Programma_Allenamento.py")

    c3, c4 = st.columns(2, gap="small")
    with c3:
        if st.button("Chat Esperto", use_container_width=True, key="btn_expert"):
            st.switch_page("pages/02_Assistente_Esperto.py")
    with c4:
        if st.button("Apri Agenda", use_container_width=True, key="btn_calendar"):
            st.switch_page("pages/01_Agenda.py")

    # AI Status
    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
    st.markdown("### Status AI")

    try:
        from core.workout_ai_pipeline import WorkoutAIPipeline
        from unittest.mock import patch
        with patch.object(WorkoutAIPipeline, '_init_llm'):
            pipeline = WorkoutAIPipeline()
            pipeline.llm = None
            status = pipeline.get_pipeline_status()

        dna_cards = status.get('dna_cards', 0)
        dna_level = status.get('dna_level', 'none')
        meth_docs = status.get('methodology_docs', 0)

        level_colors = {'none': 'neutral', 'learning': 'accent', 'intermediate': 'primary', 'advanced': 'success'}
        level_color = level_colors.get(dna_level, 'neutral')

        st.markdown(f"""
        <div class="card" style="padding: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="color: var(--text-secondary); font-size: 0.85rem;">Trainer DNA</span>
                <span class="badge badge-{level_color}" style="font-size: 0.7rem;">{dna_level.upper()}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="color: var(--text-secondary); font-size: 0.85rem;">Schede importate</span>
                <span style="color: var(--text-primary); font-weight: 600;">{dna_cards}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: var(--text-secondary); font-size: 0.85rem;">Knowledge Base</span>
                <span style="color: var(--text-primary); font-weight: 600;">{meth_docs} docs</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        st.markdown("""
        <div class="card" style="padding: 1rem;">
            <span style="color: var(--text-muted); font-size: 0.85rem;">AI non disponibile</span>
        </div>
        """, unsafe_allow_html=True)
