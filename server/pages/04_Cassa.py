# file: server/pages/03_Cassa.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta, datetime
from core.crm_db import CrmDBManager

db = CrmDBManager()

st.set_page_config(page_title="Gestione Cassa", page_icon="💰", layout="wide")

# CSS Styling
st.markdown("""
<style>
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: bold;
        margin: 10px 0;
    }
    .kpi-label {
        font-size: 12px;
        opacity: 0.9;
    }
    .status-positive { color: #10b981; }
    .status-warning { color: #f59e0b; }
    .status-negative { color: #ef4444; }
</style>
""", unsafe_allow_html=True)

st.title("💰 Gestione Cassa & Contabilità")

st.info("""
📋 **Sistema Finanziario Professionale**
- **Bilancio Effettivo**: Solo movimenti confermati (data_effettiva)
- **Previsione**: Rate pendenti + spese ricorrenti
- **Fonte Unica**: movimenti_cassa è la verità assoluta
""")

# Fetch dati usando la NUOVA logica pulita
with st.spinner("Caricamento dati finanziari..."):
    # IMPORTANTE: Sincronizza lo stato dei contratti da movimenti RATA_CONTRATTO
    # (utile quando i pagamenti sono stati registrati direttamente come movimenti)
    db.sincronizza_stato_contratti_da_movimenti()
    
    # Metriche unificate per il mese corrente
    oggi = date.today()
    primo_mese = date(oggi.year, oggi.month, 1)
    from calendar import monthrange
    ultimo_giorno_mese = monthrange(oggi.year, oggi.month)[1]
    ultimo_mese = date(oggi.year, oggi.month, ultimo_giorno_mese)

# ════════════════════════════════════════════════════════════
# FILTRI PERIODO ANALISI
# ════════════════════════════════════════════════════════════

col_filter1, col_filter2, col_filter3 = st.columns(3)

with col_filter1:
    tipo_periodo = st.radio(
        "📅 Periodo Analisi",
        ["Mese Solare", "Ultimi 30 giorni", "Ultimi 7 giorni", "Personalizzato"],
        horizontal=True
    )

# Calcola il periodo in base alla selezione
if tipo_periodo == "Mese Solare":
    data_inizio = primo_mese
    data_fine = ultimo_mese
    label_periodo = f"{primo_mese.strftime('%d %b')} - {ultimo_mese.strftime('%d %b %Y')}"
elif tipo_periodo == "Ultimi 30 giorni":
    data_fine = oggi
    data_inizio = oggi - timedelta(days=29)
    label_periodo = f"{data_inizio.strftime('%d %b')} - {data_fine.strftime('%d %b %Y')} (ultimi 30gg)"
elif tipo_periodo == "Ultimi 7 giorni":
    data_fine = oggi
    data_inizio = oggi - timedelta(days=6)
    label_periodo = f"{data_inizio.strftime('%d %b')} - {data_fine.strftime('%d %b %Y')} (ultimi 7gg)"
else:  # Personalizzato
    with col_filter2:
        data_inizio = st.date_input("Data Inizio", value=primo_mese, key="custom_start")
    with col_filter3:
        data_fine = st.date_input("Data Fine", value=ultimo_mese, key="custom_end")
    label_periodo = f"{data_inizio.strftime('%d %b')} - {data_fine.strftime('%d %b %Y')} (custom)"

st.caption(f"📍 Periodo selezionato: {label_periodo}")

# Calcola metriche per il periodo selezionato
with st.spinner("Ricalcolo metriche per periodo selezionato..."):
    # NUOVA LOGICA: Tre fonti separate e coerenti
    bilancio_cassa = db.get_bilancio_cassa(data_inizio, data_fine)
    bilancio_competenza = db.get_bilancio_competenza(data_inizio, data_fine)
    previsione = db.get_previsione_cash(30)
    
    # Carica movimenti per il periodo (per i grafici cashflow)
    with db._connect() as conn:
        movimenti_periodo = [dict(r) for r in conn.execute("""
            SELECT * FROM movimenti_cassa
            WHERE data_effettiva BETWEEN ? AND ?
            ORDER BY data_effettiva
        """, (data_inizio, data_fine)).fetchall()]

# ════════════════════════════════════════════════════════════
# DASHBOARD PRINCIPALE - KPI IN CARDS
# ════════════════════════════════════════════════════════════

st.subheader("📊 Dashboard Finanziaria (Bilancio per CASSA)", divider=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💵 Incassato",
        f"€ {bilancio_cassa['incassato']:.2f}",
        "Soldi VERI entrati",
        delta_color="normal"
    )

with col2:
    st.metric(
        "💸 Speso",
        f"€ {bilancio_cassa['speso']:.2f}",
        "Soldi VERI usciti",
        delta_color="inverse"
    )

with col3:
    st.metric(
        "🏦 Saldo Cassa",
        f"€ {bilancio_cassa['saldo_cassa']:.2f}",
        "Nel periodo",
        delta_color="normal" if bilancio_cassa['saldo_cassa'] >= 0 else "inverse"
    )

with col4:
    st.metric(
        "📈 Previsione Saldo",
        f"€ {previsione['saldo_previsto']:.2f}",
        f"tra {previsione.get('periodo', '30 giorni')}",
        delta_color="normal" if previsione['saldo_previsto'] >= 0 else "inverse"
    )

# ════════════════════════════════════════════════════════════
# ANALISI COMPETENZA - ORE VENDUTE NEL PERIODO
# ════════════════════════════════════════════════════════════

st.subheader("📊 Analisi Competenza (Ore VENDUTE nel periodo)", divider=True)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.metric(
        "⏱️ Ore Vendute",
        f"{bilancio_competenza['ore_vendute']:.1f}h",
        f"Eseguite: {bilancio_competenza['ore_eseguite']:.1f}h",
        delta_color="normal"
    )

with col_m2:
    st.metric(
        "💰 Fatturato Potenziale",
        f"€{bilancio_competenza['fatturato_potenziale']:.2f}",
        f"Vendite nel periodo",
        delta_color="normal"
    )

with col_m3:
    st.metric(
        "💳 Incassato su Contratti",
        f"€{bilancio_competenza['incassato_su_contratti']:.2f}",
        f"Pagato ({(bilancio_competenza['incassato_su_contratti']/max(bilancio_competenza['fatturato_potenziale'],1)*100):.1f}%)",
        delta_color="normal"
    )

with col_m4:
    st.metric(
        "⏳ Rate Mancanti",
        f"€{bilancio_competenza['rate_mancanti']:.2f}",
        f"Da riscuotere",
        delta_color="inverse" if bilancio_competenza['rate_mancanti'] > 0 else "normal"
    )

st.info(f"""
📌 **Analisi Competenza (Ore vendute {label_periodo})**
- **Ore Vendute**: Fatturato il {data_inizio.strftime('%d %b')} - {data_fine.strftime('%d %b %Y')}
- **Ore Eseguite**: Lezioni già completate su queste vendite
- **Fatturato Potenziale**: Quanto dovrebbe entrarmi se tutti pagano
- **Incassato**: Quanto REALMENTE ho ricevuto (può essere da altri periodi)
- **Rate Mancanti**: La differenza tra fatturato e incassato

**Nota**: Le ore sono LOGICAMENTE SEPARATE dal cash flow.
Una vendita oggi con pagamento tra 30 giorni genera:
- **Ore in questo mese** (competenza)
- **Cash in prossimo mese** (cassa)
""")

# ════════════════════════════════════════════════════════════
# CASHFLOW MESE CORRENTE
# ════════════════════════════════════════════════════════════

st.subheader("💵 Cashflow Periodo Selezionato", divider=True)

if len(movimenti_periodo) > 0:
    # Preparare dati giornalieri usando data_effettiva
    cf_mese = pd.DataFrame(movimenti_periodo)
    cf_mese['data_effettiva'] = pd.to_datetime(cf_mese['data_effettiva'], format='mixed')
    cf_mese['data_giorno'] = cf_mese['data_effettiva'].dt.date
    
    # Pivot per tipo giornaliero
    cf_giornaliero = cf_mese.groupby(['data_giorno', 'tipo'])['importo'].sum().unstack(fill_value=0)
    cf_giornaliero['SALDO_GIORNO'] = cf_giornaliero.get('ENTRATA', 0) - cf_giornaliero.get('USCITA', 0)
    cf_giornaliero['SALDO_CUMULATIVO'] = cf_giornaliero['SALDO_GIORNO'].cumsum()
    
    col_cf1, col_cf2 = st.columns(2)
    
    with col_cf1:
        # Grafico entrate vs uscite giornaliere
        cf_reset = cf_giornaliero.reset_index()
        
        # Assicurare che entrambe le colonne esistano
        if 'ENTRATA' not in cf_reset.columns:
            cf_reset['ENTRATA'] = 0
        if 'USCITA' not in cf_reset.columns:
            cf_reset['USCITA'] = 0
        
        cf_melted = cf_reset.melt(
            id_vars='data_giorno',
            value_vars=['ENTRATA', 'USCITA'],
            var_name='Tipo',
            value_name='Importo'
        )
        fig_cf = px.bar(
            cf_melted,
            x='data_giorno',
            y='Importo',
            color='Tipo',
            title="Entrate vs Uscite Giornaliere",
            barmode='group',
            labels={'data_giorno': 'Data', 'Importo': '€'},
            color_discrete_map={'ENTRATA': '#10b981', 'USCITA': '#ef4444'}
        )
        fig_cf.update_xaxes(tickformat="%d/%m")
        st.plotly_chart(fig_cf, use_container_width=True)
    
    with col_cf2:
        # Grafico saldo cumulativo
        fig_saldo = px.line(
            cf_giornaliero.reset_index(),
            x='data_giorno',
            y='SALDO_CUMULATIVO',
            title="Saldo Cumulativo Giornaliero",
            markers=True,
            labels={'data_giorno': 'Data', 'SALDO_CUMULATIVO': '€'}
        )
        fig_saldo.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        fig_saldo.update_traces(line_color='#667eea')
        st.plotly_chart(fig_saldo, use_container_width=True)
    
    # Statistiche cashflow
    st.divider()
    cf_stat_col1, cf_stat_col2, cf_stat_col3, cf_stat_col4 = st.columns(4)
    cf_stat_col1.metric("Entrate Periodo", f"€ {bilancio_cassa['incassato']:.2f}")
    cf_stat_col2.metric("Uscite Periodo", f"€ {bilancio_cassa['speso']:.2f}")
    cf_stat_col3.metric("Saldo Netto Periodo", f"€ {bilancio_cassa['saldo_cassa']:.2f}")
    if len(cf_giornaliero) > 0 and 'ENTRATA' in cf_giornaliero.columns:
        cf_stat_col4.metric("Giorno con + Entrate", f"€ {cf_giornaliero['ENTRATA'].max():.2f}")
else:
    st.info("Nessun movimento registrato nel mese corrente.")

# ════════════════════════════════════════════════════════════
# PREVISIONE BILANCIO CON COSTI FISSI
# ════════════════════════════════════════════════════════════

st.subheader("📊 Previsione Bilancio & Costi Fissi", divider=True)

# Impostazioni costi fissi
with st.expander("⚙️ Configura Costi Fissi Mensili"):
    col_cf_config1, col_cf_config2, col_cf_config3 = st.columns(3)
    with col_cf_config1:
        costo_affitto = st.number_input("Affitto", min_value=0.0, step=50.0, value=1000.0, key="affitto")
    with col_cf_config2:
        costo_utilities = st.number_input("Luce/Gas/Acqua", min_value=0.0, step=10.0, value=150.0, key="utilities")
    with col_cf_config3:
        costo_assicurazioni = st.number_input("Assicurazioni", min_value=0.0, step=50.0, value=200.0, key="assicurazioni")
    
    col_cf_config4, col_cf_config5 = st.columns(2)
    with col_cf_config4:
        costo_altro = st.number_input("Altro (manutenzione, attrezzi, ecc)", min_value=0.0, step=50.0, value=300.0, key="altro_costi")

# Calcoli previsione (usando nuova logica)
costi_fissi_totali = costo_affitto + costo_utilities + costo_assicurazioni + costo_altro

# La previsione è già calcolata dall'API, qui aggiorniamo con i costi fissi
previsione_giorni = 30  # Previsione a 30 giorni
costi_previsti_custom = costi_fissi_totali  # Costi configurati nel form
saldo_previsto_con_costi = previsione['saldo_previsto'] - costi_previsti_custom  # Aggiusta per costi fissi custom

# Display previsione
prev_col1, prev_col2, prev_col3, prev_col4 = st.columns(4)

prev_col1.metric(
    "Saldo Cassa Oggi",
    f"EUR {bilancio_cassa['saldo_cassa']:.2f}",
    delta_color="normal" if bilancio_cassa['saldo_cassa'] >= 0 else "inverse"
)

prev_col2.metric(
    "Rate in Scadenza (30gg)",
    f"EUR {previsione['rate_scadenti']:.2f}",
    "che arriveranno",
    delta_color="normal"
)

prev_col3.metric(
    "Costi Previsti (30gg)",
    f"EUR {previsione['costi_previsti']:.2f}",
    "fissi", 
    delta_color="inverse"
)

prev_col4.metric(
    "Saldo Previsto (30gg)",
    f"EUR {previsione['saldo_previsto']:.2f}",
    delta="CRITICO" if previsione['saldo_previsto'] < 500 else "BUONO",
    delta_color="inverse" if previsione['saldo_previsto'] < 500 else "normal"
)

st.divider()

# Grafico waterfall semplificato (solo previsione)
fig_prev = px.bar(
    x=['Saldo Oggi', 'Rate Attese', 'Costi Previsti', 'Saldo Previsto (30gg)'],
    y=[bilancio_cassa['saldo_cassa'], previsione['rate_scadenti'], -previsione['costi_previsti'], previsione['saldo_previsto']],
    title="Waterfall Previsione Bilancio (30 giorni)",
    labels={'x': '', 'y': 'EUR'},
    color=['#667eea', '#10b981', '#ef4444', '#f59e0b'],
    height=400
)
st.plotly_chart(fig_prev, use_container_width=True)

# Dettaglio entrate programmate
with st.expander("📋 Dettaglio Entrate Programmate (Rate Pendenti)"):
    rate_pendenti = db.get_rate_pendenti(date.today() + timedelta(days=30))
    if rate_pendenti:
        rate_df = pd.DataFrame(rate_pendenti)
        rate_df_display = rate_df[['nome', 'cognome', 'tipo_pacchetto', 'data_scadenza', 'importo_previsto']].copy()
        rate_df_display.columns = ['Cliente', 'Cognome', 'Pacchetto', 'Scadenza', 'Importo']
        st.dataframe(rate_df_display, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Nessuna rata pendente nei prossimi 30 giorni!")

# Dettaglio uscite programmate
with st.expander("📋 Dettaglio Uscite Programmate (Spese Ricorrenti)"):
    spese_prossime = db.get_spese_ricorrenti_prossime(30)
    if spese_prossime:
        spese_df = pd.DataFrame(spese_prossime)
        if len(spese_df) > 0:
            spese_df_display = spese_df[['nome', 'categoria', 'importo', 'data_prossima_scadenza']].copy()
            spese_df_display.columns = ['Nome', 'Categoria', 'Importo', 'Prossima Scadenza']
            st.dataframe(spese_df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Nessuna spesa ricorrente configurata.")

# ════════════════════════════════════════════════════════════
# TABS PRINCIPALI
# ════════════════════════════════════════════════════════════

tab1, tab2 = st.tabs([
    "📊 Movimenti del Periodo",
    "📅 Scadenziario Pagamenti"
])

with tab1:
    st.subheader("Movimenti nel Periodo")
    
    st.info(f"""
    Periodo: {data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}
    
    **Incassato (soldi VERI entrati)**
    - EUR {bilancio_cassa['incassato']:.2f}
    
    **Speso (soldi VERI usciti)**  
    - EUR {bilancio_cassa['speso']:.2f}
    
    **Saldo Netto nel Periodo**
    - EUR {bilancio_cassa['saldo_cassa']:.2f}
    """)
    
    # Tabella movimenti del periodo
    if len(movimenti_periodo) > 0:
        movimenti_df = pd.DataFrame(movimenti_periodo)
        cols_to_show = ['data_effettiva', 'tipo', 'categoria', 'importo']
        if all(col in movimenti_df.columns for col in cols_to_show):
            display_df = movimenti_df[cols_to_show].copy()
            display_df.columns = ['Data', 'Tipo', 'Categoria', 'Importo (EUR)']
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=300)
        else:
            st.info("Tabella movimenti non disponibile")
    else:
        st.info("Nessun movimento nel periodo selezionato")

with tab2:
    st.subheader("Scadenziario Pagamenti Clienti")
    
    st.info("""
    Questo tab mostra il calendario delle rate in scadenza nei prossimi giorni.
    
    **Rate da riscuotere** (dai dati di competenza):
    - EUR {:.2f} di rate mancanti
    - Prossimi 30 giorni: EUR {:.2f} in scadenza
    """.format(
        bilancio_competenza['rate_mancanti'],
        previsione['rate_scadenti']
    ))

st.divider()
st.caption("Sistema di gestione cassa - Versione aggiornata con logica separata Cassa vs Competenza")