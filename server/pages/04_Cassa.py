# file: server/pages/04_Cassa_Simple.py
"""
💰 Cassa & Bilancio - Versione SEMPLIFICATA

Target: Libera professionista P.IVA forfettaria
- No concetti di "competenza" 
- No metriche aziendali (LTV, CAC, ecc.)
- Focus: Cash In, Cash Out, Saldo, Prossime Entrate

UI ispirata a: Trainerize, FitSW, MyPTHub (CRM semplici)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from calendar import monthrange
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from core.crm_db import CrmDBManager

# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Cassa & Bilancio",
    page_icon="💰",
    layout="wide"
)

db = CrmDBManager()

# ════════════════════════════════════════════════════════════
# CSS MINIMALISTA
# ════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* Card semplici */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Numeri grandi e leggibili */
    .big-number {
        font-size: 36px;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .positive { color: #10b981; }
    .negative { color: #ef4444; }
    .neutral { color: #6b7280; }
    
    /* Lista semplice */
    .simple-list {
        background: #f9fafb;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════

st.title("💰 Cassa & Bilancio")

st.markdown("""
<div style="background: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid #0ea5e9;">
<b>📋 Vista Semplice</b><br>
Quanto hai incassato, quanto hai speso, quanto ti aspetti nei prossimi giorni.
</div>
""", unsafe_allow_html=True)

st.divider()

# ════════════════════════════════════════════════════════════
# PERIODO: Mese Corrente (sempre)
# ════════════════════════════════════════════════════════════

oggi = date.today()
primo_mese = date(oggi.year, oggi.month, 1)
ultimo_giorno = monthrange(oggi.year, oggi.month)[1]
ultimo_mese = date(oggi.year, oggi.month, ultimo_giorno)

# Calcola bilancio mese corrente
bilancio = db.get_bilancio_cassa(primo_mese, ultimo_mese)
previsione = db.get_previsione_cash(30)

# ════════════════════════════════════════════════════════════
# DASHBOARD PRINCIPALE - 4 NUMERI CHIAVE
# ════════════════════════════════════════════════════════════

st.subheader(f"📊 Questo Mese ({oggi.strftime('%B %Y')})")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 💵 Incassato")
    st.markdown(f"<div class='big-number positive'>€ {bilancio['incassato']:.0f}</div>", unsafe_allow_html=True)
    st.caption("Soldi entrati questo mese")

with col2:
    st.markdown("### 💸 Speso")
    st.markdown(f"<div class='big-number negative'>€ {bilancio['speso']:.0f}</div>", unsafe_allow_html=True)
    st.caption("Soldi usciti questo mese")

with col3:
    st.markdown("### 🏦 Saldo Mese")
    saldo_colore = "positive" if bilancio['saldo_cassa'] >= 0 else "negative"
    st.markdown(f"<div class='big-number {saldo_colore}'>€ {bilancio['saldo_cassa']:.0f}</div>", unsafe_allow_html=True)
    st.caption("Differenza entrate - uscite")

with col4:
    st.markdown("### 📈 Previsione")
    prev_colore = "positive" if previsione['saldo_previsto'] >= 0 else "negative"
    st.markdown(f"<div class='big-number {prev_colore}'>€ {previsione['saldo_previsto']:.0f}</div>", unsafe_allow_html=True)
    st.caption("Saldo tra 30 giorni")

st.divider()

# ════════════════════════════════════════════════════════════
# GRAFICO SEMPLICE: Entrate vs Uscite Mensili
# ════════════════════════════════════════════════════════════

st.subheader("📊 Andamento Mese")

# Dati ultimi 6 mesi
mesi_dati = []
for i in range(5, -1, -1):
    mese_calc = oggi - timedelta(days=30*i)
    primo = date(mese_calc.year, mese_calc.month, 1)
    ultimo_g = monthrange(mese_calc.year, mese_calc.month)[1]
    ultimo = date(mese_calc.year, mese_calc.month, ultimo_g)
    
    bil = db.get_bilancio_cassa(primo, ultimo)
    mesi_dati.append({
        'Mese': primo.strftime('%b %Y'),
        'Entrate': bil['incassato'],
        'Uscite': bil['speso']
    })

df_mesi = pd.DataFrame(mesi_dati)

# Grafico a barre semplice
fig = px.bar(
    df_mesi,
    x='Mese',
    y=['Entrate', 'Uscite'],
    barmode='group',
    color_discrete_map={'Entrate': '#10b981', 'Uscite': '#ef4444'},
    height=350
)
fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=30, b=0),
    yaxis_title="Euro (€)"
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ════════════════════════════════════════════════════════════
# PROSSIME ENTRATE (Rate in Scadenza)
# ════════════════════════════════════════════════════════════

st.subheader("📅 Prossimi Incassi Attesi (30 giorni)")

rate_pendenti = db.get_rate_pendenti(oggi + timedelta(days=30))

if rate_pendenti:
    st.success(f"✅ {len(rate_pendenti)} rate in scadenza - Totale: **€ {sum(r['importo_previsto'] for r in rate_pendenti):.0f}**")
    
    # Lista semplice (come Trainerize, FitSW)
    for rata in rate_pendenti[:10]:  # Max 10 più vicine
        col_a, col_b, col_c = st.columns([3, 2, 1])
        
        with col_a:
            st.markdown(f"**{rata['nome']} {rata['cognome']}**")
            st.caption(f"{rata['tipo_pacchetto']}")
        
        with col_b:
            # Converti stringa ISO da SQLite (YYYY-MM-DD) in date object
            data_scadenza = date.fromisoformat(rata['data_scadenza']) if isinstance(rata['data_scadenza'], str) else rata['data_scadenza']
            giorni_mancanti = (data_scadenza - oggi).days
            if giorni_mancanti <= 7:
                st.markdown(f"🔴 Scadenza: {data_scadenza.strftime('%d/%m/%Y')}")
            else:
                st.markdown(f"Scadenza: {data_scadenza.strftime('%d/%m/%Y')}")
            st.caption(f"Tra {giorni_mancanti} giorni")
        
        with col_c:
            st.markdown(f"### € {rata['importo_previsto']:.0f}")
        
        st.divider()
    
    if len(rate_pendenti) > 10:
        st.info(f"... e altre {len(rate_pendenti) - 10} rate")
else:
    st.info("✅ Nessuna rata in scadenza nei prossimi 30 giorni")

st.divider()

# ════════════════════════════════════════════════════════════
# SPESE FISSE MENSILI (Configurazione)
# ════════════════════════════════════════════════════════════

st.subheader("💰 Spese Fisse Mensili")

col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    affitto = st.number_input(
        "🏠 Affitto Studio",
        min_value=0,
        step=50,
        value=1000,
        help="Affitto mensile dello studio"
    )

with col_s2:
    utenze = st.number_input(
        "⚡ Luce/Gas/Acqua",
        min_value=0,
        step=20,
        value=150,
        help="Utenze mensili medie"
    )

with col_s3:
    assicurazioni = st.number_input(
        "🛡️ Assicurazioni",
        min_value=0,
        step=50,
        value=200,
        help="Assicurazione professionale, RC, ecc."
    )

col_s4, col_s5 = st.columns(2)

with col_s4:
    altro = st.number_input(
        "🔧 Altro (materiali, manutenzione)",
        min_value=0,
        step=50,
        value=300,
        help="Spese varie mensili"
    )

with col_s5:
    st.markdown("### Totale Spese Fisse")
    totale_fisso = affitto + utenze + assicurazioni + altro
    st.markdown(f"<div class='big-number negative'>€ {totale_fisso:.0f}/mese</div>", unsafe_allow_html=True)

st.divider()

# ════════════════════════════════════════════════════════════
# PREVISIONE SEMPLICE (Saldo tra 30 giorni)
# ════════════════════════════════════════════════════════════

st.subheader("🔮 Previsione Semplice (30 giorni)")

col_p1, col_p2, col_p3, col_p4 = st.columns(4)

saldo_oggi = bilancio['saldo_cassa']  # Saldo mese corrente
rate_attese = previsione['rate_scadenti']  # Rate in arrivo
spese_previste = totale_fisso  # Spese fisse configurate
saldo_30gg = saldo_oggi + rate_attese - spese_previste

with col_p1:
    st.metric("💰 Saldo Oggi", f"€ {saldo_oggi:.0f}")

with col_p2:
    st.metric("➕ Rate Attese", f"€ {rate_attese:.0f}", delta="In arrivo")

with col_p3:
    st.metric("➖ Spese Previste", f"€ {spese_previste:.0f}", delta="Da pagare", delta_color="inverse")

with col_p4:
    delta_msg = "ATTENZIONE!" if saldo_30gg < 500 else "OK"
    delta_color = "inverse" if saldo_30gg < 500 else "normal"
    st.metric("🎯 Saldo tra 30gg", f"€ {saldo_30gg:.0f}", delta=delta_msg, delta_color=delta_color)

# Alert se saldo previsto basso
if saldo_30gg < 500:
    st.warning("""
    ⚠️ **Attenzione Cash Flow**
    
    Il saldo previsto tra 30 giorni è basso (< €500).
    Considera di:
    - Sollecitare rate in ritardo
    - Ridurre spese non essenziali
    - Programmare nuove vendite
    """)

st.divider()

# ════════════════════════════════════════════════════════════
# MOVIMENTI RECENTI (Ultimi 10)
# ════════════════════════════════════════════════════════════

st.subheader("📋 Ultimi Movimenti")

with db._connect() as conn:
    movimenti = [dict(r) for r in conn.execute("""
        SELECT data_effettiva, tipo, categoria, importo, note
        FROM movimenti_cassa
        WHERE data_effettiva >= ?
        ORDER BY data_effettiva DESC
        LIMIT 10
    """, (primo_mese,)).fetchall()]

if movimenti:
    for mov in movimenti:
        col_m1, col_m2, col_m3 = st.columns([2, 3, 1])
        
        with col_m1:
            st.markdown(f"**{mov['data_effettiva']}**")
        
        with col_m2:
            tipo_icon = "💵" if mov['tipo'] == 'ENTRATA' else "💸"
            st.markdown(f"{tipo_icon} {mov['categoria']}")
            if mov['note']:
                st.caption(mov['note'])
        
        with col_m3:
            colore = "positive" if mov['tipo'] == 'ENTRATA' else "negative"
            segno = "+" if mov['tipo'] == 'ENTRATA' else "-"
            st.markdown(f"<span class='{colore}'><b>{segno}€ {mov['importo']:.0f}</b></span>", unsafe_allow_html=True)
        
        st.divider()
else:
    st.info("Nessun movimento registrato ancora")

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════

st.divider()
st.caption("💡 Versione Semplificata - Ideale per P.IVA forfettaria e gestione libero professionista")
