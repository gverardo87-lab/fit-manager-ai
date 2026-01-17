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

# Fetch dati
with st.spinner("Caricamento dati finanziari..."):
    bilancio = db.get_bilancio_completo()
    
    # Calcoli globali
    tot_entrate = bilancio[bilancio['tipo'] == 'ENTRATA']['importo'].sum() if len(bilancio) > 0 else 0
    tot_uscite = bilancio[bilancio['tipo'] == 'USCITA']['importo'].sum() if len(bilancio) > 0 else 0
    saldo_netto = tot_entrate - tot_uscite
    
    # Dati mese corrente
    oggi = date.today()
    primo_mese = pd.Timestamp(date(oggi.year, oggi.month, 1))
    bilancio['data_movimento'] = pd.to_datetime(bilancio['data_movimento'], format='mixed')
    mov_mese = bilancio[(bilancio['data_movimento'] >= primo_mese)]
    entrate_mese = mov_mese[mov_mese['tipo'] == 'ENTRATA']['importo'].sum()
    uscite_mese = mov_mese[mov_mese['tipo'] == 'USCITA']['importo'].sum()

# ════════════════════════════════════════════════════════════
# DASHBOARD PRINCIPALE - KPI IN CARDS
# ════════════════════════════════════════════════════════════

st.subheader("📊 Dashboard Finanziaria", divider=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💼 Totale Entrate",
        f"€ {tot_entrate:.2f}",
        f"€ {entrate_mese:.2f} questo mese",
        delta_color="normal"
    )

with col2:
    st.metric(
        "💸 Totale Uscite",
        f"€ {tot_uscite:.2f}",
        f"€ {uscite_mese:.2f} questo mese",
        delta_color="inverse"
    )

with col3:
    delta_saldo = saldo_netto - (tot_entrate - tot_uscite)
    st.metric(
        "📈 Saldo Netto",
        f"€ {saldo_netto:.2f}",
        delta_color="normal" if saldo_netto >= 0 else "inverse"
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
# TABS PRINCIPALI
# ════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Movimenti Giornalieri",
    "📅 Scadenziario Pagamenti",
    "📊 Analisi Entrate/Uscite",
    "🔧 Registrazione Manuale"
])

with tab1:
    st.subheader("🔄 Ultimi Movimenti")
    
    if len(bilancio) > 0:
        # Filtri
        col_filt1, col_filt2, col_filt3 = st.columns(3)
        
        with col_filt1:
            tipo_filt = st.selectbox("Tipo", ["Tutti", "ENTRATA", "USCITA"], key="tipo_filt_tab1")
        
        with col_filt2:
            categoria_filt = st.selectbox(
                "Categoria",
                ["Tutte"] + bilancio['categoria'].unique().tolist(),
                key="cat_filt_tab1"
            )
        
        with col_filt3:
            giorni_indietro = st.slider("Ultimi N giorni", 7, 365, 30, key="giorni_tab1")
        
        # Applicare filtri
        df_filt = bilancio.copy()
        if tipo_filt != "Tutti":
            df_filt = df_filt[df_filt['tipo'] == tipo_filt]
        if categoria_filt != "Tutte":
            df_filt = df_filt[df_filt['categoria'] == categoria_filt]
        
        data_limite = pd.Timestamp(datetime.now()) - timedelta(days=giorni_indietro)
        df_filt['data_movimento'] = pd.to_datetime(df_filt['data_movimento'], format='mixed')
        df_filt = df_filt[df_filt['data_movimento'] >= data_limite]
        
        # Tabella
        if len(df_filt) > 0:
            display_df = df_filt[['data_movimento', 'tipo', 'categoria', 'importo', 'metodo', 'note']].copy()
            display_df['data_movimento'] = pd.to_datetime(display_df['data_movimento']).dt.strftime('%d/%m/%Y %H:%M')
            display_df = display_df.sort_values('data_movimento', ascending=False)
            
            # Colori per tipo
            def color_tipo(val):
                return 'color: #10b981' if val == 'ENTRATA' else 'color: #ef4444'
            
            st.dataframe(
                display_df.style.applymap(lambda x: '', subset=['tipo']),
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
    
    # Query su contratti con rate pendenti
    with db._connect() as conn:
        contratti = conn.execute("""
            SELECT c.id, c.id_cliente, c.tipo_pacchetto, c.prezzo_totale, c.totale_versato, 
                   cli.nome, cli.cognome, c.stato_pagamento
            FROM contratti c
            JOIN clienti cli ON c.id_cliente = cli.id
            WHERE c.stato_pagamento != 'SALDATO' 
            ORDER BY c.data_vendita DESC
        """).fetchall()
    
    if len(contratti) > 0:
        # Mostra contratti non saldati
        for contr in contratti:
            rate = db.get_rate_contratto(contr['id'])
            
            with st.container(border=True):
                # Header
                h1, h2, h3 = st.columns([2, 2, 1])
                h1.markdown(f"**{contr['nome']} {contr['cognome']}** - {contr['tipo_pacchetto']}")
                h2.caption(f"Saldo: € {contr['totale_versato']:.2f} / € {contr['prezzo_totale']:.2f}")
                
                status_icon = "🟢" if contr['stato_pagamento'] == 'SALDATO' else "🟡" if contr['stato_pagamento'] == 'PARZIALE' else "🔴"
                h3.write(f"{status_icon} {contr['stato_pagamento']}")
                
                # Rate
                if rate:
                    rate_df = pd.DataFrame(rate)
                    rate_df['data_scadenza'] = pd.to_datetime(rate_df['data_scadenza'])
                    rate_df = rate_df.sort_values('data_scadenza')
                    
                    for r in rate_df.to_dict('records'):
                        r_col1, r_col2, r_col3, r_col4 = st.columns([2, 2, 1.5, 1.5])
                        
                        scad_date = pd.to_datetime(r['data_scadenza']).date()
                        is_overdue = scad_date < date.today() and r['stato'] != 'SALDATA'
                        color = "red" if is_overdue else "gray"
                        
                        r_col1.markdown(f":{color}[📅 {scad_date.strftime('%d/%m/%Y')}]")
                        r_col2.write(f"€ {r['importo_previsto']:.2f}")
                        r_col3.write(r['stato'])
                        r_col4.write("⚠️ SCADUTA" if is_overdue else "")
    else:
        st.success("✅ Tutti i pagamenti sono in regola!")

with tab3:
    st.subheader("📈 Analisi Finanziaria")
    
    if len(bilancio) > 0:
        # Grafico trend mensile
        bilancio_mese = bilancio.copy()
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
            entrate_cat = bilancio[bilancio['tipo'] == 'ENTRATA'].groupby('categoria')['importo'].sum()
            if len(entrate_cat) > 0:
                fig_pie1 = px.pie(
                    values=entrate_cat.values,
                    names=entrate_cat.index,
                    title="Entrate per Categoria",
                    height=400
                )
                st.plotly_chart(fig_pie1, use_container_width=True)
        
        with col_pie2:
            uscite_cat = bilancio[bilancio['tipo'] == 'USCITA'].groupby('categoria')['importo'].sum()
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
                    (data_movimento, tipo, categoria, importo, metodo, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (data_mov, tipo_mov, categoria, importo, metodo, note))
            st.success(f"✅ Movimento registrato: € {importo:.2f}")
            st.rerun()
        else:
            st.error("Inserisci un importo maggiore di 0")