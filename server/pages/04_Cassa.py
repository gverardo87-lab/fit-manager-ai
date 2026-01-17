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
    
    # Usa il metodo unificato per il mese
    metriche_mese = db.calculate_unified_metrics(primo_mese, ultimo_mese)
    
    # Bilancio effettivo (legacy, per compatibilità)
    bilancio_eff = db.get_bilancio_effettivo()
    bilancio_mese = db.get_bilancio_effettivo(primo_mese, None)
    
    # Previsione 30 giorni
    previsione = db.get_cashflow_previsione(30)
    
    # Bilancio completo per tabelle (legacy, per compatibilità)
    bilancio_full = db.get_bilancio_completo()

# ════════════════════════════════════════════════════════════
# DASHBOARD PRINCIPALE - KPI IN CARDS
# ════════════════════════════════════════════════════════════

st.subheader("📊 Dashboard Finanziaria", divider=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💼 Entrate Totali",
        f"€ {bilancio_eff['entrate']:.2f}",
        f"€ {bilancio_mese['entrate']:.2f} questo mese",
        delta_color="normal"
    )

with col2:
    st.metric(
        "💸 Uscite Totali",
        f"€ {bilancio_eff['uscite']:.2f}",
        f"€ {bilancio_mese['uscite']:.2f} questo mese",
        delta_color="inverse"
    )

with col3:
    st.metric(
        "📈 Saldo Effettivo",
        f"€ {bilancio_eff['saldo']:.2f}",
        delta_color="normal" if bilancio_eff['saldo'] >= 0 else "inverse"
    )

with col4:
    # Incassi completati vs non completati
    with db._connect() as conn:
        clienti = conn.execute("SELECT COUNT(DISTINCT id_cliente) FROM contratti").fetchone()[0]
    st.metric(
        "👥 Clienti Attivi",
        clienti,
        "nuovi questo mese" if True else "stabili",
        delta_color="normal"
    )

# ════════════════════════════════════════════════════════════
# ANALISI MARGINE - LOGICA UNIFICATA
# ════════════════════════════════════════════════════════════

st.subheader("📊 Analisi Margine (Logica Unificata)", divider=True)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.metric(
        "⏱️ Ore Fatturate",
        f"{metriche_mese['ore_fatturate']:.1f}h",
        f"Eseguite: {metriche_mese['ore_eseguite']:.1f}h",
        delta_color="normal"
    )

with col_m2:
    st.metric(
        "💰 Entrate Mese",
        f"€{metriche_mese['entrate_totali']:.2f}",
        f"da {metriche_mese['giorni']} giorni",
        delta_color="normal"
    )

with col_m3:
    st.metric(
        "💸 Costi Totali",
        f"€{metriche_mese['costi_totali']:.2f}",
        f"Fissi: €{metriche_mese['costi_fissi_periodo']:.2f}",
        delta_color="inverse"
    )

with col_m4:
    st.metric(
        "🎯 Margine/Ora",
        f"€{metriche_mese['margine_orario']:.2f}",
        f"Lordo: €{metriche_mese['margine_lordo']:.2f}",
        delta_color="normal" if metriche_mese['margine_orario'] > 0 else "inverse"
    )

st.info(f"""
📌 **Analisi Margine Mese {primo_mese.strftime('%B %Y')}**
- **Formula**: Margine/Ora = (Entrate - Costi Fissi - Costi Variabili) / Ore Pagate
- **Ore Non Pagate**: {metriche_mese['ore_non_pagate']:.1f}h (Admin, Formazione, ecc.)
- **Costi Fissi Mensili**: €{metriche_mese['costi_fissi_mensili']:.2f}
""")

# ════════════════════════════════════════════════════════════
# CASHFLOW MESE CORRENTE
# ════════════════════════════════════════════════════════════

st.subheader("💵 Cashflow Mese Corrente", divider=True)

if len(bilancio_mese['movimenti']) > 0:
    # Preparare dati giornalieri usando data_effettiva
    cf_mese = pd.DataFrame(bilancio_mese['movimenti'])
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
    cf_stat_col1.metric("Entrate Mese", f"€ {bilancio_mese['entrate']:.2f}")
    cf_stat_col2.metric("Uscite Mese", f"€ {bilancio_mese['uscite']:.2f}")
    cf_stat_col3.metric("Saldo Netto Mese", f"€ {bilancio_mese['saldo']:.2f}")
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

# Calcolare entrate non ancora incassate (rate pendenti)
# Usare la nuova logica pulita da previsione
saldo_attuale = bilancio_eff['saldo']

# Calcoli previsione (usando nuova logica)
costi_fissi_totali = costo_affitto + costo_utilities + costo_assicurazioni + costo_altro

# La previsione è già calcolata dall'API, qui aggiorniamo con i costi fissi
previsione_giorni = 30  # Previsione a 30 giorni
costi_previsti_custom = costi_fissi_totali  # Costi configurati nel form
saldo_previsto = previsione['saldo_previsto'] - costi_previsti_custom  # Aggiusta per costi fissi custom

# Display previsione
prev_col1, prev_col2, prev_col3, prev_col4 = st.columns(4)

prev_col1.metric(
    "💰 Saldo Effettivo",
    f"€ {previsione['saldo_effettivo']:.2f}",
    delta_color="normal" if previsione['saldo_effettivo'] >= 0 else "inverse"
)

prev_col2.metric(
    "📈 Entrate Programmate (30gg)",
    f"€ {previsione['entrate_programmate']:.2f}",
    "(rate pendenti)",
    delta_color="normal"
)

prev_col3.metric(
    "📉 Uscite Programmate (30gg)",
    f"€ {previsione['uscite_programmate']:.2f}",
    "(spese ricorrenti)",
    delta_color="inverse"
)

prev_col4.metric(
    "🎯 Saldo Previsto (30gg)",
    f"€ {previsione['saldo_previsto']:.2f}",
    delta="CRITICO" if previsione['saldo_previsto'] < 500 else "BUONO",
    delta_color="inverse" if previsione['saldo_previsto'] < 500 else "normal"
)

st.divider()

# Grafico previsione
previsione_data = {
    'Categoria': ['Saldo Attuale', 'Entrate Programmate', 'Uscite Programmate', 'Saldo Previsto'],
    'Valore': [previsione['saldo_effettivo'], previsione['entrate_programmate'], -previsione['uscite_programmate'], previsione['saldo_previsto']],
    'Colore': ['#667eea', '#10b981', '#ef4444', '#f59e0b']
}

fig_prev = px.bar(
    x=previsione_data['Categoria'],
    y=previsione_data['Valore'],
    title="Waterfall Previsione Bilancio (30 giorni)",
    labels={'x': '', 'y': '€'},
    color=previsione_data['Categoria'],
    color_discrete_map={
        'Saldo Attuale': '#667eea',
        'Entrate Programmate': '#10b981',
        'Uscite Programmate': '#ef4444',
        'Saldo Previsto': '#f59e0b'
    },
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

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Movimenti Giornalieri",
    "📅 Scadenziario Pagamenti",
    "📊 Analisi Entrate/Uscite",
    "🔧 Registrazione Manuale",
    "⚙️ Spese Ricorrenti"
])

with tab1:
    st.subheader("🔄 Ultimi Movimenti")
    
    if len(bilancio_full) > 0:
        # Filtri
        col_filt1, col_filt2, col_filt3 = st.columns(3)
        
        with col_filt1:
            tipo_filt = st.selectbox("Tipo", ["Tutti", "ENTRATA", "USCITA"], key="tipo_filt_tab1")
        
        with col_filt2:
            categoria_filt = st.selectbox(
                "Categoria",
                ["Tutte"] + bilancio_full['categoria'].unique().tolist(),
                key="cat_filt_tab1"
            )
        
        with col_filt3:
            giorni_indietro = st.slider("Ultimi N giorni", 7, 365, 30, key="giorni_tab1")
        
        # Applicare filtri
        df_filt = bilancio_full.copy()
        if tipo_filt != "Tutti":
            df_filt = df_filt[df_filt['tipo'] == tipo_filt]
        if categoria_filt != "Tutte":
            df_filt = df_filt[df_filt['categoria'] == categoria_filt]
        
        data_limite = pd.Timestamp(datetime.now()) - timedelta(days=giorni_indietro)
        
        # Usare data_effettiva se disponibile, altrimenti data_movimento
        if 'data_effettiva' in df_filt.columns:
            df_filt['data_effettiva'] = pd.to_datetime(df_filt['data_effettiva'], format='mixed')
            df_filt = df_filt[df_filt['data_effettiva'] >= data_limite]
            date_column = 'data_effettiva'
        else:
            df_filt['data_movimento'] = pd.to_datetime(df_filt['data_movimento'], format='mixed')
            df_filt = df_filt[df_filt['data_movimento'] >= data_limite]
            date_column = 'data_movimento'
        
        # Tabella
        if len(df_filt) > 0:
            display_df = df_filt[['data_movimento', 'tipo', 'categoria', 'importo', 'metodo', 'note']].copy()
            display_df['data_movimento'] = pd.to_datetime(display_df['data_movimento']).dt.strftime('%d/%m/%Y %H:%M')
            display_df = display_df.sort_values('data_movimento', ascending=False)
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # Statistiche filtrate
            st.divider()
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            stat_col1.metric("Movimenti", len(df_filt))
            stat_col2.metric("Entrate", f"€ {df_filt[df_filt['tipo']=='ENTRATA']['importo'].sum():.2f}")
            stat_col3.metric("Uscite", f"€ {df_filt[df_filt['tipo']=='USCITA']['importo'].sum():.2f}")
        else:
            st.info("Nessun movimento nel periodo selezionato.")
    else:
        st.info("Nessun movimento registrato ancora.")

with tab2:
    st.subheader("⏰ Scadenziario Pagamenti Clienti")
    
    # Query su TUTTI i contratti per mostrare lo stato completo
    with db._connect() as conn:
        contratti = conn.execute("""
            SELECT c.id, c.id_cliente, c.tipo_pacchetto, c.prezzo_totale, c.totale_versato, 
                   cli.nome, cli.cognome, c.stato_pagamento, c.data_vendita
            FROM contratti c
            JOIN clienti cli ON c.id_cliente = cli.id
            ORDER BY c.data_vendita DESC
        """).fetchall()
    
    if len(contratti) > 0:
        # Filtri
        col_tab2_filt1, col_tab2_filt2 = st.columns(2)
        with col_tab2_filt1:
            stato_filt = st.multiselect(
                "Filtra per stato pagamento",
                ["SALDATO", "PARZIALE", "PENDENTE"],
                default=["PARZIALE", "PENDENTE"],
                key="stato_filt_tab2"
            )
        
        # Mostra contratti filtrati
        for contr in contratti:
            if contr['stato_pagamento'] not in stato_filt:
                continue
            
            rate = db.get_rate_contratto(contr['id'])
            
            with st.container(border=True):
                # Header
                h1, h2, h3, h4 = st.columns([2, 2, 1.2, 1])
                h1.markdown(f"**{contr['nome']} {contr['cognome']}** - {contr['tipo_pacchetto']}")
                h2.caption(f"Saldo: € {contr['totale_versato']:.2f} / € {contr['prezzo_totale']:.2f}")
                
                status_icon = "✅" if contr['stato_pagamento'] == 'SALDATO' else "⏳" if contr['stato_pagamento'] == 'PARZIALE' else "❌"
                percentuale_pagato = (contr['totale_versato'] / contr['prezzo_totale'] * 100) if contr['prezzo_totale'] > 0 else 0
                h3.write(f"{status_icon} {percentuale_pagato:.0f}%")
                h4.caption(f"Vendita: {contr['data_vendita']}")
                
                # Barra di progresso
                st.progress(min(percentuale_pagato / 100, 1.0), text=f"{percentuale_pagato:.1f}% pagato")
                
                # Rate
                if rate:
                    rate_df = pd.DataFrame(rate)
                    rate_df['data_scadenza'] = pd.to_datetime(rate_df['data_scadenza'])
                    rate_df = rate_df.sort_values('data_scadenza')
                    
                    # Intestazione tabella rate
                    rate_h1, rate_h2, rate_h3, rate_h4 = st.columns([1.5, 1.5, 1, 1])
                    rate_h1.caption("**Scadenza**")
                    rate_h2.caption("**Importo**")
                    rate_h3.caption("**Stato**")
                    rate_h4.caption("**Azioni**")
                    
                    for r in rate_df.to_dict('records'):
                        r_col1, r_col2, r_col3, r_col4 = st.columns([1.5, 1.5, 1, 1])
                        
                        scad_date = pd.to_datetime(r['data_scadenza']).date()
                        is_overdue = scad_date < date.today() and r['stato'] != 'SALDATA'
                        
                        if r['stato'] == 'SALDATA':
                            color_tag = "✅"
                            color = "green"
                        elif is_overdue:
                            color_tag = "⚠️ SCADUTA"
                            color = "red"
                        else:
                            color_tag = "⏳ IN SCADENZA"
                            color = "gray"
                        
                        r_col1.write(f"📅 {scad_date.strftime('%d/%m/%Y')}")
                        r_col2.write(f"€ {r['importo_previsto']:.2f}")
                        r_col3.markdown(f":{color}[{color_tag}]") if color != "green" else r_col3.markdown(f":{color}[{color_tag}]")
                        r_col4.caption(f"ID: {r['id']}")
                else:
                    st.caption("Nessuna rata associata")
    else:
        st.success("✅ Nessun contratto registrato!")

with tab3:
    st.subheader("📈 Analisi Finanziaria")
    
    if len(bilancio_full) > 0:
        # Grafico trend mensile
        bilancio_mese = bilancio_full.copy()
        bilancio_mese['data_movimento'] = pd.to_datetime(bilancio_mese['data_movimento'], format='mixed')
        bilancio_mese['anno_mese'] = bilancio_mese['data_movimento'].dt.to_period('M').astype(str)
        trend = bilancio_mese.groupby(['anno_mese', 'tipo'])['importo'].sum().unstack(fill_value=0)
        
        if len(trend) > 0:
            fig_trend = px.bar(
                trend,
                title="Trend Mensile Entrate vs Uscite",
                labels={"value": "€", "anno_mese": "Mese"},
                barmode='group',
                height=400
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        
        # Pie chart categorie
        col_pie1, col_pie2 = st.columns(2)
        
        with col_pie1:
            entrate_cat = bilancio_full[bilancio_full['tipo'] == 'ENTRATA'].groupby('categoria')['importo'].sum()
            if len(entrate_cat) > 0:
                fig_pie1 = px.pie(
                    values=entrate_cat.values,
                    names=entrate_cat.index,
                    title="Entrate per Categoria",
                    height=400
                )
                st.plotly_chart(fig_pie1, use_container_width=True)
        
        with col_pie2:
            uscite_cat = bilancio_full[bilancio_full['tipo'] == 'USCITA'].groupby('categoria')['importo'].sum()
            if len(uscite_cat) > 0:
                fig_pie2 = px.pie(
                    values=uscite_cat.values,
                    names=uscite_cat.index,
                    title="Uscite per Categoria",
                    height=400
                )
                st.plotly_chart(fig_pie2, use_container_width=True)
    else:
        st.info("Nessun dato per l'analisi.")

with tab4:
    st.subheader("➕ Registra Movimento Manuale")
    st.info("📌 Usa questa sezione per registrazioni straordinarie non legate a contratti")
    
    col_form1, col_form2 = st.columns(2)
    
    with col_form1:
        data_mov = st.date_input("Data Movimento", date.today())
        tipo_mov = st.radio("Tipo", ["ENTRATA", "USCITA"], horizontal=True)
    
    with col_form2:
        categoria = st.selectbox("Categoria", [
            "ACCONTO_CONTRATTO", "RATA_CONTRATTO",
            "SPESE_AFFITTO", "SPESE_UTILITIES", "SPESE_ATTREZZATURE",
            "RIMBORSI", "ALTRO"
        ])
        importo = st.number_input("Importo (€)", min_value=0.0, step=0.01)
    
    col_form3, col_form4 = st.columns(2)
    
    with col_form3:
        metodo = st.selectbox("Metodo Pagamento", [
            "CONTANTI", "CARTA_DEBITO", "CARTA_CREDITO", "BONIFICO", "ASSEGNO"
        ])
    
    with col_form4:
        note = st.text_input("Note (opzionale)")
    
    if st.button("💾 Registra Movimento", type="primary", use_container_width=True):
        if importo > 0:
            with db.transaction() as cur:
                cur.execute("""
                    INSERT INTO movimenti_cassa 
                    (data_effettiva, tipo, categoria, importo, metodo, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (data_mov, tipo_mov, categoria, importo, metodo, note))
            st.success(f"✅ Movimento registrato: € {importo:.2f}")
            st.rerun()
        else:
            st.error("Inserisci un importo maggiore di 0")

with tab5:
    st.subheader("⚙️ Gestione Spese Ricorrenti")
    st.info("📌 Spese mensili/ricorrenti (affitto, utilities, assicurazioni, ecc)")
    
    col_tabs5_1, col_tabs5_2 = st.columns([1, 1])
    
    with col_tabs5_1:
        st.subheader("➕ Aggiungi Spesa Ricorrente")
        
        nome_spesa = st.text_input("Nome Spesa", placeholder="es. Affitto Studio")
        categoria_spesa = st.selectbox("Categoria", [
            "SPESE_AFFITTO", "SPESE_UTILITIES", "SPESE_ATTREZZATURE",
            "SPESE_ASSICURAZIONI", "STIPENDI", "MARKETING", "SPESE_GENERALI"
        ])
        importo_spesa = st.number_input("Importo Mensile (€)", min_value=0.0, step=0.01)
        frequenza_spesa = st.selectbox("Frequenza", ["MENSILE", "SETTIMANALE", "ANNUALE", "SEMESTRALE"])
        giorno_scadenza_spesa = st.number_input("Giorno del Mese (1-28)", min_value=1, max_value=28, value=1)
        
        if st.button("💾 Aggiungi Spesa", type="primary", use_container_width=True):
            if nome_spesa and importo_spesa > 0:
                db.add_spesa_ricorrente(nome_spesa, categoria_spesa, importo_spesa, frequenza_spesa, giorno_scadenza_spesa)
                st.success(f"✅ Spesa ricorrente aggiunta: {nome_spesa}")
                st.rerun()
            else:
                st.error("Inserisci nome e importo")
    
    with col_tabs5_2:
        st.subheader("📋 Spese Ricorrenti Attive")
        
        spese_attive = db.get_spese_ricorrenti()
        if spese_attive:
            spese_df = pd.DataFrame(spese_attive)
            display_cols = ['nome', 'categoria', 'importo', 'frequenza', 'giorno_scadenza', 'data_prossima_scadenza']
            spese_df_display = spese_df[display_cols].copy()
            spese_df_display.columns = ['Nome', 'Categoria', 'Importo', 'Frequenza', 'Giorno', 'Prossima Scad.']
            
            st.dataframe(spese_df_display, use_container_width=True, hide_index=True, height=300)
            
            # Statistiche spese
            st.divider()
            spese_stat_col1, spese_stat_col2 = st.columns(2)
            spese_stat_col1.metric("Numero Spese", len(spese_attive))
            spese_stat_col2.metric("Totale Mensile", f"€ {sum(s['importo'] for s in spese_attive):.2f}")
        else:
            st.info("Nessuna spesa ricorrente configurata ancora.")