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

from core.crm_db import CrmDBManager
from core.ui_components import (
    render_card, render_metric_box, create_section_header,
    render_success_message, render_error_message
)

# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Analisi Margine Orario",
    page_icon="📊",
    layout="wide"
)

db = CrmDBManager()

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
# CALCOLO METRICHE
# ════════════════════════════════════════════════════════════

with st.spinner("📊 Calcolo metriche..."):
    if granularita == "Giornaliera":
        metrics_data = db.calculate_hourly_metrics(data_sel)
        periodo_label = f"Giorno {data_sel}"
    elif granularita == "Settimanale":
        metrics_data = db.get_hourly_metrics_week(data_sel)
        periodo_label = metrics_data['settimana']
    else:  # Mensile
        metrics_data = db.get_hourly_metrics_month(data_sel[0], data_sel[1])
        periodo_label = metrics_data['mese']

# ════════════════════════════════════════════════════════════
# DASHBOARD KPI - 4 COLONNE
# ════════════════════════════════════════════════════════════

st.subheader(f"💼 KPI Principali - {periodo_label}", divider=True)

col1, col2, col3, col4 = st.columns(4, gap="large")

with col1:
    render_metric_box(
        "Ore Pagate",
        f"{metrics_data['ore_pagate']}h",
        f"+ {metrics_data['ore_non_pagate']}h admin",
        "⏱️",
        "primary"
    )

with col2:
    render_metric_box(
        "Fatturato",
        f"€{metrics_data['fatturato_totale']:.2f}",
        f"Costi: €{metrics_data['costi_totali']:.2f}",
        "💰",
        "success"
    )

with col3:
    margine_orario = metrics_data['margine_orario']
    delta_perc = ((margine_orario - target_margine) / target_margine * 100) if target_margine > 0 else 0
    
    render_metric_box(
        "Margine/Ora",
        f"€{margine_orario:.2f}",
        f"Target: €{target_margine:.2f}",
        "🎯",
        "accent" if margine_orario >= target_margine else "primary"
    )

with col4:
    if 'slot_disponibili' in metrics_data:
        slot_occupati = metrics_data.get('slot_occupati', 0)
        slot_tot = metrics_data['slot_disponibili'] + slot_occupati
        tasso_occupazione = (slot_occupati / slot_tot * 100) if slot_tot > 0 else 0
        
        render_metric_box(
            "Slot Occupati",
            f"{slot_occupati}/{slot_tot}",
            f"Tasso: {tasso_occupazione:.0f}%",
            "📍",
            "success" if tasso_occupazione > 75 else "primary"
        )
    else:
        render_metric_box(
            "Margine Lordo",
            f"€{metrics_data['margine_lordo']:.2f}",
            f"vs Netto: €{metrics_data['margine_netto']:.2f}",
            "📊",
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
    
    if granularita in ["Giornaliera", "Settimanale"]:
        # Mostra ultimi 30 giorni
        if granularita == "Giornaliera":
            data_inizio = data_sel - timedelta(days=30)
            data_fine = data_sel
            daily_data = db.get_hourly_metrics_period(data_inizio, data_fine)
            
            # Prepara DataFrame
            df_trend = pd.DataFrame([
                {
                    'Data': m['data'],
                    'Margine/Ora': m['margine_orario'],
                    'Fatturato': m['fatturato_totale'],
                    'Ore Pagate': m['ore_pagate']
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
                height=400,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiche
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_margine = df_trend['Margine/Ora'].mean()
                st.metric("Media Margine/Ora", f"€{avg_margine:.2f}")
            with col2:
                max_margine = df_trend['Margine/Ora'].max()
                st.metric("Picco Margine", f"€{max_margine:.2f}")
            with col3:
                min_margine = df_trend['Margine/Ora'].min()
                st.metric("Minimo Margine", f"€{min_margine:.2f}")
        
        else:  # Settimanale
            # Ultimi 12 settimane
            settimane_data = []
            data_corrente = date_sel
            for _ in range(12):
                settimana = db.get_hourly_metrics_week(data_corrente)
                settimane_data.append(settimana)
                data_corrente -= timedelta(weeks=1)
            
            settimane_data.reverse()
            
            df_trend = pd.DataFrame([
                {
                    'Settimana': s['settimana'],
                    'Margine/Ora': s['margine_orario'],
                    'Fatturato': s['fatturato_totale']
                }
                for s in settimane_data
            ])
            
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
    
    else:  # Mensile
        st.info("📊 Visualizza gli ultimi 12 mesi per analizzare la tendenza")
        # TODO: Implementare visualizzazione annuale

# ════════════════════════════════════════════════════════════
# TAB 2: MARGINE PER CLIENTE
# ════════════════════════════════════════════════════════════

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
    
    clienti_margine = db.get_margine_per_cliente(data_inizio, data_fine)
    
    if clienti_margine:
        df_clienti = pd.DataFrame(clienti_margine)
        
        # Tabella
        st.dataframe(
            df_clienti[['cliente', 'sessioni', 'ore', 'fatturato', 'margine', 'margine_orario']],
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
        
        # Grafico: Top clienti per margine
        fig = px.bar(
            df_clienti.nlargest(10, 'fatturato'),
            x='cliente',
            y='margine_orario',
            color='margine_orario',
            title="Top 10 Clienti - Margine Orario",
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
        daily_data = db.get_hourly_metrics_period(data_inizio, data_fine)
        
        df_ore_fat = pd.DataFrame([
            {
                'Data': m['data'],
                'Ore Pagate': m['ore_pagate'],
                'Fatturato': m['fatturato_totale'],
                'Fatturato/Ora': m['fatturato_totale'] / m['ore_pagate'] if m['ore_pagate'] > 0 else 0
            }
            for m in daily_data if m['ore_pagate'] > 0
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
                title="Relazione Ore Pagate vs Fatturato",
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
    
    margine_attuale = metrics_data['margine_orario']
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
        gap_totale = (target_margine - margine_attuale) * metrics_data['ore_pagate']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Calcola percentuale occupazione slot
            slot_tot = metrics_data.get('slot_disponibili', 0) + metrics_data.get('slot_occupati', 0)
            occupazione_slot = (metrics_data.get('slot_occupati', 0) / slot_tot * 100) if slot_tot > 0 else 0
            
            st.markdown(f"""
            **Gap da Colmare**: €{gap_totale:.2f}
            
            **Opzioni:**
            1. **Aumenta Tariffe**: +{((target_margine - margine_attuale) / (metrics_data['fatturato_totale'] / metrics_data['ore_pagate']) * 100) if metrics_data['ore_pagate'] > 0 else 0:.1f}% per raggiungere il target
            2. **Riduci Costi**: Identifica spese variabili da ottimizzare
            3. **Migliora Slot**: Occupazione slot al {occupazione_slot:.0f}%
            """)
        
        with col2:
            st.markdown(f"""
            **Analisi Oraria:**
            - Ore Pagate: {metrics_data['ore_pagate']}h
            - Ore Non Pagate: {metrics_data['ore_non_pagate']}h
            - Fatturato/Ora: €{(metrics_data['fatturato_totale'] / metrics_data['ore_pagate']) if metrics_data['ore_pagate'] > 0 else 0:.2f}
            - Costi/Ora: €{(metrics_data['costi_totali'] / metrics_data['ore_pagate']) if metrics_data['ore_pagate'] > 0 else 0:.2f}
            """)
    else:
        st.success("""
        ✅ **Target Raggiunto!**
        
        Mantieni questo livello di redditività e continua a monitorare:
        - Equilibrio ore pagate/non pagate
        - Tasso di occupazione slot
        - Margine per cliente
        """)

st.divider()
st.caption("💪 ProFit AI - Analisi Margine Orario | Dati in tempo reale dal database")
