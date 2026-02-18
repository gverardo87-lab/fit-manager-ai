# file: server/pages/05_Analisi_Margine_Orario.py
"""
Analisi Premium del Margine Orario per PT
Dashboard completa con 4 output: Tendenza Temporale, Per Cliente, Ore vs Fatturato, Target
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta, datetime
from calendar import monthrange
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.repositories import FinancialRepository
from core.ui_components import (
    load_custom_css,
    render_card, render_metric_box, create_section_header,
    render_success_message, render_error_message
)

# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Analisi Margine Orario",
    page_icon=":material/analytics:",
    layout="wide"
)
load_custom_css()

financial_repo = FinancialRepository()

# ════════════════════════════════════════════════════════════
# SIDEBAR - CONTROLLI TEMPORALI
# ════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 📊 Analisi Margine")
    
    # Selezione granularità
    granularita = st.radio(
        "Granularità",
        ["Giornaliera", "Settimanale", "Mensile"],
        key="gran_margine"
    )
    
    st.divider()
    
    if granularita == "Giornaliera":
        data_sel = st.date_input("Data", value=date.today(), key="date_margine_gg")
    elif granularita == "Settimanale":
        data_sel = st.date_input("Settimana (seleziona lunedì)", value=date.today(), key="date_margine_sett")
    else:  # Mensile
        col1, col2 = st.columns(2)
        with col1:
            anno = st.number_input("Anno", value=date.today().year, min_value=2020, max_value=2030)
        with col2:
            mese = st.selectbox("Mese", range(1, 13), index=date.today().month - 1)
        data_sel = (anno, mese)
    
    st.divider()
    
    # Target margine orario
    target_margine = st.number_input(
        "Target Margine/Ora (€)",
        value=50.0,
        min_value=10.0,
        max_value=500.0,
        step=5.0,
        help="Margine orario target che vuoi raggiungere"
    )
    
    # Mostra target come badge
    st.metric("🎯 Target", f"€{target_margine:.2f}/h")

# ════════════════════════════════════════════════════════════
# TITLE & HEADER
# ════════════════════════════════════════════════════════════

st.markdown("# 📊 Analisi Margine Orario")
st.markdown("""
Tracciamento completo della redditività oraria: costi fissi distribuiti + costi variabili, 
slot disponibili, fatturato reale vs previsione.
""")

st.divider()

# ════════════════════════════════════════════════════════════
# CALCOLO METRICHE - NUOVA LOGICA SEPARATA (CASSA vs COMPETENZA)
# ════════════════════════════════════════════════════════════

with st.spinner("📊 Calcolo metriche separate (Cassa + Competenza)..."):
    if granularita == "Giornaliera":
        # Logica separata per un giorno
        bilancio_cassa = financial_repo.get_cash_balance(data_sel, data_sel)
        bilancio_competenza = financial_repo.get_bilancio_competenza(data_sel, data_sel)
        periodo_label = f"Giorno {data_sel}"
    elif granularita == "Settimanale":
        # Logica separata: da lunedì a domenica della settimana
        lunedi = data_sel - timedelta(days=data_sel.weekday())
        domenica = lunedi + timedelta(days=6)
        bilancio_cassa = financial_repo.get_cash_balance(lunedi, domenica)
        bilancio_competenza = financial_repo.get_bilancio_competenza(lunedi, domenica)
        periodo_label = f"Settimana {lunedi.strftime('%d/%m')} - {domenica.strftime('%d/%m/%Y')}"
    else:  # Mensile
        # Logica separata: dall'1 all'ultimo giorno del mese
        anno, mese = data_sel
        primo_giorno = date(anno, mese, 1)
        ultimo_giorno = date(anno, mese, monthrange(anno, mese)[1])
        bilancio_cassa = financial_repo.get_cash_balance(primo_giorno, ultimo_giorno)
        bilancio_competenza = financial_repo.get_bilancio_competenza(primo_giorno, ultimo_giorno)
        periodo_label = f"Mese {primo_giorno.strftime('%B %Y')}"

# ════════════════════════════════════════════════════════════
# DASHBOARD KPI - 4 COLONNE
# ════════════════════════════════════════════════════════════

st.subheader(f"💼 KPI Principali - {periodo_label}", divider=True)

col1, col2, col3, col4 = st.columns(4, gap="large")

with col1:
    render_metric_box(
        "Ore Vendute",
        f"{bilancio_competenza['ore_vendute']:.1f}h",
        f"Eseguite: {bilancio_competenza['ore_eseguite']:.1f}h",
        "⏱️",
        "primary"
    )

with col2:
    render_metric_box(
        "Incassato",
        f"€{bilancio_cassa['incassato']:.2f}",
        f"Soldi VERI nel periodo",
        "💰",
        "success"
    )

with col3:
    # Margine/Ora calcolato CORRETTAMENTE:
    # = Incassato / Ore Vendute (non mischiare periodi)
    margine_orario = bilancio_cassa['incassato'] / max(bilancio_competenza['ore_vendute'], 1)
    delta_perc = ((margine_orario - target_margine) / target_margine * 100) if target_margine > 0 else 0
    
    render_metric_box(
        "Margine/Ora",
        f"€{margine_orario:.2f}",
        f"Target: €{target_margine:.2f}",
        "🎯",
        "accent" if margine_orario >= target_margine else "primary"
    )

with col4:
    # Rate in pendenza (non ancora incassate)
    render_metric_box(
        "Rate Mancanti",
        f"€{bilancio_competenza['rate_mancanti']:.2f}",
        f"Da riscuotere",
        "⏳",
        "primary"
    )

st.divider()

# ════════════════════════════════════════════════════════════
# TAB 1: TENDENZA TEMPORALE
# ════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Tendenza Temporale",
    "👥 Per Cliente",
    "⚙️ Ore vs Fatturato",
    "🎯 Target & Analisi"
])

with tab1:
    create_section_header("Andamento nel Tempo", "Evoluzione del margine orario", "📈")
    
    if granularita == "Giornaliera":
        # Mostra ultimi 30 giorni
        data_inizio = data_sel - timedelta(days=29)  # 30 giorni incluso oggi
        data_fine = data_sel
        
        daily_data = financial_repo.get_daily_metrics_range(data_inizio, data_fine)
        
        # Prepara DataFrame
        df_trend = pd.DataFrame([
            {
                'Data': m['data'],
                'Margine/Ora': m['margine_orario'],
                'Entrate': m['entrate_totali'],
                'Ore Fatturate': m['ore_fatturate']
            }
            for m in daily_data
        ])
        
        # Grafico tendenza
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_trend['Data'],
            y=df_trend['Margine/Ora'],
            mode='lines+markers',
            name='Margine/Ora',
            line=dict(color='#0066cc', width=3),
            marker=dict(size=6)
        ))
        
        # Aggiungi linea target
        fig.add_hline(
            y=target_margine,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Target: €{target_margine:.2f}/h",
            annotation_position="right"
        )
        
        fig.update_layout(
            title="Margine Orario - Ultimi 30 Giorni",
            xaxis_title="Data",
            yaxis_title="Margine/Ora (€)",
            hovermode="x unified",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # KPI nel grafico
        col1, col2, col3 = st.columns(3)

        with col1:
            max_margine = df_trend['Margine/Ora'].max()
            st.metric("Massimo Margine", f"€{max_margine:.2f}")
        
        with col2:
            media_margine = df_trend['Margine/Ora'].mean()
            st.metric("Media Margine", f"€{media_margine:.2f}")
        
        with col3:
            min_margine = df_trend['Margine/Ora'].min()
            st.metric("Minimo Margine", f"€{min_margine:.2f}")
    
    elif granularita == "Settimanale":
        fig = px.line(
            df_trend,
            x='Settimana',
            y='Margine/Ora',
            title="Margine Orario - Ultimi 12 Settimane",
            markers=True,
            line_shape='linear'
        )
        
        fig.add_hline(
            y=target_margine,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Target: €{target_margine:.2f}/h"
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # KPI settimane
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_w = df_trend['Margine/Ora'].max()
            st.metric("Max Settimana", f"€{max_w:.2f}")
        
        with col2:
            media_w = df_trend['Margine/Ora'].mean()
            st.metric("Media Settimane", f"€{media_w:.2f}")
        
        with col3:
            min_w = df_trend['Margine/Ora'].min()
            st.metric("Min Settimana", f"€{min_w:.2f}")
    
    else:  # Mensile
        st.info("📊 Analisi mensile - Ultimi 12 mesi in sviluppo")

with tab2:
    create_section_header("Redditività per Cliente", "Analisi margine diviso per cliente", "👥")
    
    # Calcola periodo per margine per cliente
    if granularita == "Giornaliera":
        data_inizio = data_sel
        data_fine = data_sel
    elif granularita == "Settimanale":
        lunedi = data_sel - timedelta(days=data_sel.weekday())
        data_inizio = lunedi
        data_fine = lunedi + timedelta(days=6)
    else:  # Mensile
        data_inizio = date(data_sel[0], data_sel[1], 1)
        ultimo_gg = monthrange(data_sel[0], data_sel[1])[1]
        data_fine = date(data_sel[0], data_sel[1], ultimo_gg)
    
    clienti_margine = financial_repo.get_margine_per_cliente(data_inizio, data_fine)
    
    if clienti_margine:
        df_clienti = pd.DataFrame(clienti_margine)
        
        # Filtro clienti
        col_filter1, col_filter2 = st.columns([3, 1])
        with col_filter1:
            clienti_lista = ['TUTTI'] + sorted(df_clienti['cliente'].unique().tolist())
            cliente_sel = st.selectbox(
                "Seleziona Cliente",
                clienti_lista,
                key="cliente_margine"
            )
        
        # Filtra dati
        if cliente_sel != 'TUTTI':
            df_clienti_filtered = df_clienti[df_clienti['cliente'] == cliente_sel]
        else:
            df_clienti_filtered = df_clienti
        
        # Tabella
        st.dataframe(
            df_clienti_filtered[['cliente', 'sessioni', 'ore', 'fatturato', 'margine', 'margine_orario']],
            use_container_width=True,
            column_config={
                'cliente': 'Cliente',
                'sessioni': '# Sessioni',
                'ore': 'Ore',
                'fatturato': 'Fatturato (€)',
                'margine': 'Margine (€)',
                'margine_orario': 'Margine/Ora (€)'
            }
        )
        
        # Grafico: Top clienti per margine (o cliente selezionato)
        if cliente_sel == 'TUTTI':
            dati_grafico = df_clienti.nlargest(10, 'fatturato')
            titolo = "Top 10 Clienti - Margine Orario"
        else:
            dati_grafico = df_clienti_filtered
            titolo = f"Margine Orario - {cliente_sel}"
        
        fig = px.bar(
            dati_grafico,
            x='cliente',
            y='margine_orario',
            color='margine_orario',
            title=titolo,
            labels={'margine_orario': 'Margine/Ora (€)', 'cliente': 'Cliente'},
            color_continuous_scale='RdYlGn'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("❌ Nessun dato disponibile per il periodo selezionato")

# ════════════════════════════════════════════════════════════
# TAB 3: ORE vs FATTURATO
# ════════════════════════════════════════════════════════════

with tab3:
    create_section_header("Correlazione Ore vs Fatturato", "Analisi della relazione", "⚙️")
    
    if granularita == "Giornaliera":
        data_inizio = data_sel - timedelta(days=30)
        data_fine = data_sel
        daily_data = financial_repo.get_hourly_metrics_period(data_inizio, data_fine)
        
        df_ore_fat = pd.DataFrame([
            {
                'Data': m['data'],
                'Ore Pagate': m['ore_fatturate'],
                'Fatturato': m['entrate_totali'],
                'Fatturato/Ora': m['entrate_totali'] / m['ore_fatturate'] if m['ore_fatturate'] > 0 else 0
            }
            for m in daily_data if m['ore_fatturate'] > 0
        ])
        
        if len(df_ore_fat) == 0:
            st.info("📊 Nessun dato disponibile per il periodo selezionato")
        else:
            # Scatter plot
            fig = px.scatter(
                df_ore_fat,
                x='Ore Pagate',
                y='Fatturato',
                size='Fatturato/Ora',
                hover_data=['Data'],
                title="Relazione Ore Eseguite vs Fatturato (da agenda)",
                labels={'Ore Pagate': 'Ore Pagate', 'Fatturato': 'Fatturato (€)'}
            )
            
            st.plotly_chart(fig, use_container_width=True)

            # Statistiche
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_fat_ora = df_ore_fat['Fatturato/Ora'].mean()
                st.metric("Fatturato Medio/Ora", f"€{avg_fat_ora:.2f}")
            with col2:
                total_ore = df_ore_fat['Ore Pagate'].sum()
                st.metric("Ore Totali", f"{total_ore:.1f}h")
            with col3:
                total_fat = df_ore_fat['Fatturato'].sum()
                st.metric("Fatturato Totale", f"€{total_fat:.2f}")

# ════════════════════════════════════════════════════════════
# TAB 4: TARGET & ANALISI
# ════════════════════════════════════════════════════════════

with tab4:
    create_section_header("Analisi vs Target", "Raggiungimento obiettivi", "🎯")
    
    # Margine/Ora calcolato CORRETTAMENTE
    margine_attuale = bilancio_cassa['incassato'] / max(bilancio_competenza['ore_vendute'], 1)
    differenza = margine_attuale - target_margine
    perc_target = (margine_attuale / target_margine * 100) if target_margine > 0 else 0
    
    # KPI principali
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if differenza >= 0:
            render_success_message(f"✅ Target Raggiunto: +€{differenza:.2f}")
        else:
            render_error_message(f"❌ Target Mancato: -€{abs(differenza):.2f}")
    
    with col2:
        st.metric("% del Target", f"{perc_target:.0f}%")
    
    with col3:
        if perc_target >= 100:
            st.success(f"🏆 Superato di {perc_target - 100:.0f}%")
        else:
            st.warning(f"⚠️ Manca {100 - perc_target:.0f}%")
    
    st.divider()
    
    # Raccomandazioni
    st.markdown("### 💡 Raccomandazioni")
    
    if margine_attuale < target_margine:
        gap_totale = (target_margine - margine_attuale) * bilancio_competenza['ore_vendute']
        tariffe_attuali = bilancio_cassa['incassato'] / max(bilancio_competenza['ore_vendute'], 1)
        aumento_tariffe_perc = ((target_margine - margine_attuale) / max(tariffe_attuali, 0.1) * 100) if bilancio_competenza['ore_vendute'] > 0 else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Gap da Colmare**: €{gap_totale:.2f}
            
            **Opzioni:**
            1. **Aumenta Tariffe**: +{aumento_tariffe_perc:.1f}% per raggiungere il target
            2. **Riduci Costi**: Identifica spese variabili da ottimizzare
            3. **Aumenta Volume**: Vendi più ore per distribuire i costi fissi
            """)
        
        with col2:
            st.markdown(f"""
            **Analisi Oraria:**
            - Ore Vendute: {bilancio_competenza['ore_vendute']:.1f}h
            - Ore Eseguite: {bilancio_competenza['ore_eseguite']:.1f}h
            - Ore Rimanenti: {bilancio_competenza['ore_rimanenti']:.1f}h
            - Tariffe Attuali: €{tariffe_attuali:.2f}/h
            - **Incassato**: €{bilancio_cassa['incassato']:.2f}
            - **Rate Mancanti**: €{bilancio_competenza['rate_mancanti']:.2f}
            """)
    else:
        st.success(f"""
        ✅ **Target Raggiunto!** (€{margine_attuale:.2f}/h)
        
        Mantieni questo livello di redditività e continua a monitorare:
        - **Ore Vendute**: {bilancio_competenza['ore_vendute']:.1f}h (di cui {bilancio_competenza['ore_eseguite']:.1f}h eseguite)
        - **Incassato**: €{bilancio_cassa['incassato']:.2f}
        - **Rate in Sospeso**: €{bilancio_competenza['rate_mancanti']:.2f}
        """)

st.divider()
st.caption("💪 ProFit AI - Analisi Margine Orario | Dati in tempo reale dal database")
