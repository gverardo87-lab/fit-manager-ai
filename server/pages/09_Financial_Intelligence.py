# file: server/pages/09_Financial_Intelligence.py
"""
🎯 FINANCIAL INTELLIGENCE - Advanced Analytics Dashboard

Metriche professionali per competere con Trainerize, TrueCoach, MarketLabs:
- LTV (Lifetime Value) Analysis
- CAC (Customer Acquisition Cost)
- Churn Rate & Prediction
- MRR/ARR Tracking
- Cohort Analysis
- Revenue per Trainer

Target: Business-minded PT che vogliono crescere professionalmente
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.crm_db import CrmDBManager
from core.financial_analytics import FinancialAnalytics
from core.ui_components import (
    render_metric_box, create_section_header,
    render_success_message, render_error_message, render_card
)

# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Financial Intelligence",
    page_icon="🎯",
    layout="wide"
)

db = CrmDBManager()
analytics = FinancialAnalytics(db)

# ════════════════════════════════════════════════════════════
# CUSTOM CSS
# ════════════════════════════════════════════════════════════

st.markdown("""
<style>
    .big-metric {
        font-size: 48px;
        font-weight: bold;
        color: #0066cc;
        margin: 0;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .insight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .risk-critical {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 15px;
        border-radius: 5px;
    }
    .risk-high {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 15px;
        border-radius: 5px;
    }
    .risk-medium {
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        padding: 15px;
        border-radius: 5px;
    }
    .risk-low {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        padding: 15px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════

st.markdown("# 🎯 Financial Intelligence")
st.markdown("""
Dashboard di analytics avanzate per PT professionisti. Monitora le metriche che usano
i leader del settore (Trainerize, TrueCoach, MarketLabs) per crescere il business.
""")

st.info("""
**📊 Metriche Professionali Implementate:**
- **LTV** (Lifetime Value): Quanto vale ogni cliente nel tempo
- **CAC** (Customer Acquisition Cost): Costo per acquisire un nuovo cliente
- **Churn Rate**: % di clienti che abbandonano
- **MRR/ARR**: Ricavi ricorrenti mensili/annuali
- **Cohort Analysis**: Analisi per gruppi di clienti
""")

st.divider()

# ════════════════════════════════════════════════════════════
# SIDEBAR - PERIODO ANALISI
# ════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 📅 Periodo Analisi")

    periodo_preset = st.selectbox(
        "Periodo",
        ["Ultimi 30 giorni", "Ultimi 90 giorni", "Ultimi 12 mesi", "Anno corrente", "Personalizzato"],
        key="periodo_analytics"
    )

    oggi = date.today()

    if periodo_preset == "Ultimi 30 giorni":
        data_inizio = oggi - timedelta(days=30)
        data_fine = oggi
    elif periodo_preset == "Ultimi 90 giorni":
        data_inizio = oggi - timedelta(days=90)
        data_fine = oggi
    elif periodo_preset == "Ultimi 12 mesi":
        data_inizio = oggi - relativedelta(months=12)
        data_fine = oggi
    elif periodo_preset == "Anno corrente":
        data_inizio = date(oggi.year, 1, 1)
        data_fine = oggi
    else:  # Personalizzato
        col1, col2 = st.columns(2)
        with col1:
            data_inizio = st.date_input(
                "Da",
                value=oggi - timedelta(days=90),
                key="data_inizio_analytics"
            )
        with col2:
            data_fine = st.date_input(
                "A",
                value=oggi,
                key="data_fine_analytics"
            )

    st.caption(f"📍 {data_inizio.strftime('%d %b %Y')} - {data_fine.strftime('%d %b %Y')}")

    st.divider()

    # Costi Marketing/Sales per CAC
    st.markdown("### 💰 Costi Acquisizione")
    st.caption("Per calcolare il CAC corretto")

    costi_marketing = st.number_input(
        "Costi Marketing (€)",
        min_value=0.0,
        value=0.0,
        step=50.0,
        help="Spese per pubblicità, social ads, flyer, ecc."
    )

    costi_sales = st.number_input(
        "Costi Vendita (€)",
        min_value=0.0,
        value=0.0,
        step=50.0,
        help="Commissioni venditori, se applicabile"
    )

# ════════════════════════════════════════════════════════════
# CALCOLO METRICHE
# ════════════════════════════════════════════════════════════

with st.spinner("📊 Calcolo analytics avanzate..."):
    # 1. Portfolio LTV
    portfolio_ltv = analytics.calculate_portfolio_ltv()

    # 2. CAC
    cac_data = analytics.calculate_cac(
        data_inizio,
        data_fine,
        costi_marketing,
        costi_sales
    )

    # 3. Churn Rate
    churn_data = analytics.calculate_churn_rate(data_inizio, data_fine)

    # 4. MRR/ARR
    mrr_data = analytics.calculate_mrr_arr()

# ════════════════════════════════════════════════════════════
# DASHBOARD PRINCIPALE - KPI CARDS
# ════════════════════════════════════════════════════════════

st.subheader("📊 Dashboard Metriche Chiave", divider=True)

col1, col2, col3, col4 = st.columns(4, gap="large")

with col1:
    render_metric_box(
        "LTV Medio/Cliente",
        f"€{portfolio_ltv['avg_ltv_per_customer']:.2f}",
        f"Mediana: €{portfolio_ltv['median_ltv']:.2f}",
        "💎",
        "success"
    )

with col2:
    render_metric_box(
        "CAC (Costo Acquisizione)",
        f"€{cac_data['cac']:.2f}",
        f"{cac_data['num_new_customers']} nuovi clienti",
        "🎯",
        "primary"
    )

with col3:
    # LTV/CAC Ratio (target: 3+)
    ltv_cac = cac_data['ltv_cac_ratio']
    color = "success" if ltv_cac >= 3 else "accent" if ltv_cac >= 2 else "primary"

    render_metric_box(
        "LTV/CAC Ratio",
        f"{ltv_cac:.1f}x",
        "Target: 3.0x+",
        "📈",
        color
    )

with col4:
    # Churn Rate
    churn = churn_data['churn_rate']
    color = "success" if churn < 5 else "accent" if churn < 7 else "primary"

    render_metric_box(
        "Churn Rate",
        f"{churn:.1f}%",
        f"Retention: {churn_data['retention_rate']:.1f}%",
        "⚠️",
        color
    )

# Insight sul LTV/CAC Ratio
st.markdown("---")
if ltv_cac >= 3:
    st.success("""
    ✅ **Eccellente! LTV/CAC Ratio >= 3.0**

    Il tuo business è sostenibile: ogni €1 speso in acquisizione genera €{:.2f} di valore cliente.
    Continua a monitorare e scala il marketing.
    """.format(ltv_cac))
elif ltv_cac >= 2:
    st.warning("""
    ⚠️ **Buono ma migliorabile (LTV/CAC = {:.1f})**

    Sei vicino al target. Considera:
    - Aumentare retention (ridurre churn)
    - Upselling ai clienti esistenti
    - Ottimizzare costi marketing
    """.format(ltv_cac))
else:
    st.error("""
    🔴 **Attenzione: LTV/CAC < 2.0**

    Il business non è sostenibile a lungo termine. Azioni urgenti:
    1. **Riduci CAC**: Ottimizza canali marketing più performanti
    2. **Aumenta LTV**: Fidelizzazione, upselling, retention programs
    3. **Analizza churn**: Perché i clienti abbandonano?
    """)

st.divider()

# ════════════════════════════════════════════════════════════
# TABS PRINCIPALI
# ════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💎 LTV Analysis",
    "🎯 CAC & Acquisition",
    "⚠️ Churn & Retention",
    "💰 MRR/ARR Tracking",
    "👥 Cohort Analysis"
])

# ════════════════════════════════════════════════════════════
# TAB 1: LTV ANALYSIS
# ════════════════════════════════════════════════════════════

with tab1:
    create_section_header(
        "Lifetime Value Analysis",
        "Analisi del valore totale generato da ogni cliente",
        "💎"
    )

    # Overview Portfolio
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "LTV Totale Portfolio",
            f"€{portfolio_ltv['total_ltv_portfolio']:.2f}",
            f"{portfolio_ltv['num_customers']} clienti attivi"
        )

    with col2:
        st.metric(
            "LTV Medio",
            f"€{portfolio_ltv['avg_ltv_per_customer']:.2f}",
            "Per cliente"
        )

    with col3:
        st.metric(
            "LTV Mediano",
            f"€{portfolio_ltv['median_ltv']:.2f}",
            "Valore centrale"
        )

    st.divider()

    # Distribuzione LTV
    if portfolio_ltv['ltv_distribution']:
        df_ltv = pd.DataFrame(portfolio_ltv['ltv_distribution'])

        # Grafico distribuzione (Top 20)
        top_20 = df_ltv.head(20)

        fig = px.bar(
            top_20,
            x='cliente_nome',
            y='ltv',
            color='ltv',
            title="Top 20 Clienti per LTV (Lifetime Value)",
            labels={'ltv': 'LTV (€)', 'cliente_nome': 'Cliente'},
            color_continuous_scale='Blues',
            height=400
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # Tabella completa LTV
        st.subheader("📋 LTV Dettagliato per Cliente")

        # Aggiungi dettagli per ogni cliente
        ltv_details = []
        for item in df_ltv.itertuples():
            cliente_ltv = analytics.calculate_customer_ltv(item.id_cliente)
            if cliente_ltv:
                ltv_details.append({
                    'Cliente': cliente_ltv['cliente_nome'],
                    'LTV Totale': f"€{cliente_ltv['ltv_total']:.2f}",
                    'LTV Mensile': f"€{cliente_ltv['ltv_monthly']:.2f}",
                    'Contratti': cliente_ltv['num_contracts'],
                    'Mesi Attivi': cliente_ltv['active_months'],
                    'Retention': f"{cliente_ltv['retention_rate']:.1f}%",
                    'Status': cliente_ltv['status'],
                    'LTV Previsto 12m': f"€{cliente_ltv['predicted_ltv_12m']:.2f}"
                })

        if ltv_details:
            df_ltv_details = pd.DataFrame(ltv_details)
            st.dataframe(
                df_ltv_details,
                use_container_width=True,
                hide_index=True,
                height=400
            )

            # Download CSV
            csv = df_ltv_details.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Scarica Report LTV (CSV)",
                csv,
                "ltv_analysis.csv",
                "text/csv",
                key='download_ltv'
            )
    else:
        st.info("Nessun dato LTV disponibile. Aggiungi clienti e contratti per vedere l'analisi.")

# ════════════════════════════════════════════════════════════
# TAB 2: CAC & ACQUISITION
# ════════════════════════════════════════════════════════════

with tab2:
    create_section_header(
        "Customer Acquisition Cost Analysis",
        f"Analisi costi acquisizione clienti ({data_inizio.strftime('%d %b')} - {data_fine.strftime('%d %b %Y')})",
        "🎯"
    )

    # KPI CAC
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "CAC Medio",
            f"€{cac_data['cac']:.2f}",
            "Per nuovo cliente"
        )

    with col2:
        st.metric(
            "Nuovi Clienti",
            cac_data['num_new_customers'],
            f"nel periodo"
        )

    with col3:
        st.metric(
            "Costi Totali",
            f"€{cac_data['total_acquisition_cost']:.2f}",
            "Marketing + Sales"
        )

    with col4:
        st.metric(
            "Payback Period",
            f"{cac_data['payback_months']:.1f} mesi",
            "Recupero CAC"
        )

    st.divider()

    # Breakdown costi
    st.subheader("💸 Breakdown Costi Acquisizione")

    breakdown_data = {
        'Categoria': ['Marketing', 'Sales', 'Altro'],
        'Importo': [
            costi_marketing,
            costi_sales,
            max(0, cac_data['total_acquisition_cost'] - costi_marketing - costi_sales)
        ]
    }
    df_breakdown = pd.DataFrame(breakdown_data)
    df_breakdown = df_breakdown[df_breakdown['Importo'] > 0]  # Solo voci non zero

    if not df_breakdown.empty:
        fig = px.pie(
            df_breakdown,
            values='Importo',
            names='Categoria',
            title="Distribuzione Costi Acquisizione",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nessun costo di acquisizione registrato per il periodo. Imposta i costi nella sidebar per vedere l'analisi.")

    # Raccomandazioni CAC
    st.divider()
    st.subheader("💡 Raccomandazioni")

    if cac_data['payback_months'] > 12:
        st.warning(f"""
        ⚠️ **Payback Period Alto ({cac_data['payback_months']:.1f} mesi)**

        Stai impiegando oltre 1 anno per recuperare il costo di acquisizione.

        **Azioni consigliate:**
        1. Rivedi i canali marketing più costosi
        2. Aumenta il valore medio del primo acquisto
        3. Implementa upselling immediato post-vendita
        """)
    elif cac_data['payback_months'] <= 6:
        st.success(f"""
        ✅ **Eccellente Payback Period ({cac_data['payback_months']:.1f} mesi)**

        Recuperi il CAC rapidamente. Questo è un indicatore di business sano.
        Considera di aumentare il budget marketing per scalare.
        """)
    else:
        st.info(f"""
        📊 **Payback Period Nella Norma ({cac_data['payback_months']:.1f} mesi)**

        Il tempo di recupero è accettabile. Monitora e ottimizza continuamente.
        """)

# ════════════════════════════════════════════════════════════
# TAB 3: CHURN & RETENTION
# ════════════════════════════════════════════════════════════

with tab3:
    create_section_header(
        "Churn Rate & Customer Retention",
        f"Analisi abbandoni e retention ({data_inizio.strftime('%d %b')} - {data_fine.strftime('%d %b %Y')})",
        "⚠️"
    )

    # KPI Churn
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        churn_color = "🟢" if churn_data['churn_rate'] < 5 else "🟡" if churn_data['churn_rate'] < 10 else "🔴"
        st.metric(
            f"{churn_color} Churn Rate",
            f"{churn_data['churn_rate']:.1f}%",
            "Clienti persi"
        )

    with col2:
        st.metric(
            "Retention Rate",
            f"{churn_data['retention_rate']:.1f}%",
            "Clienti mantenuti"
        )

    with col3:
        st.metric(
            "Clienti Persi",
            churn_data['customers_lost'],
            f"su {churn_data['customers_start']} iniziali"
        )

    with col4:
        st.metric(
            "Revenue Churn",
            f"€{churn_data['revenue_churn']:.2f}/mese",
            "Fatturato perso"
        )

    st.divider()

    # Benchmark Industry
    st.subheader("📊 Benchmark Industry Fitness")

    benchmark_data = pd.DataFrame({
        'Categoria': ['Eccellente', 'Buono', 'Medio', 'Tuo Churn'],
        'Churn Rate': [5, 7, 10, churn_data['churn_rate']],
        'Colore': ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']
    })

    fig = go.Figure()

    # Barre benchmark
    fig.add_trace(go.Bar(
        x=benchmark_data['Categoria'][:3],
        y=benchmark_data['Churn Rate'][:3],
        marker_color=benchmark_data['Colore'][:3],
        name='Benchmark',
        text=benchmark_data['Churn Rate'][:3],
        textposition='auto'
    ))

    # Tuo churn
    fig.add_trace(go.Bar(
        x=[benchmark_data['Categoria'][3]],
        y=[benchmark_data['Churn Rate'][3]],
        marker_color=benchmark_data['Colore'][3],
        name='Il Tuo Churn',
        text=[f"{churn_data['churn_rate']:.1f}%"],
        textposition='auto'
    ))

    fig.update_layout(
        title="Churn Rate vs Benchmark Industry",
        yaxis_title="Churn Rate (%)",
        showlegend=False,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # Churn Prediction per Clienti
    st.divider()
    st.subheader("🔮 Churn Risk Prediction")
    st.caption("Identifica clienti a rischio abbandono usando AI")

    # Calcola rischio per tutti i clienti attivi
    with st.spinner("Analisi rischio churn in corso..."):
        with db._connect() as conn:
            clienti_attivi = conn.execute("""
                SELECT id, nome, cognome
                FROM clienti
                WHERE stato = 'Attivo'
                ORDER BY cognome, nome
            """).fetchall()

        if clienti_attivi:
            churn_risks = []
            for cliente in clienti_attivi:
                risk = analytics.predict_churn_risk(cliente['id'])
                churn_risks.append({
                    'Cliente': f"{cliente['nome']} {cliente['cognome']}",
                    'Risk Score': risk['risk_score'],
                    'Risk Level': risk['risk_level'],
                    'Fattori': ', '.join(risk['factors']),
                    'Azioni': ', '.join(risk['recommendations'])
                })

            df_risk = pd.DataFrame(churn_risks)
            df_risk = df_risk.sort_values('Risk Score', ascending=False)

            # Filtra per livello rischio
            risk_filter = st.multiselect(
                "Filtra per livello rischio",
                ['Critico', 'Alto', 'Medio', 'Basso'],
                default=['Critico', 'Alto'],
                key='risk_filter'
            )

            df_risk_filtered = df_risk[df_risk['Risk Level'].isin(risk_filter)]

            if not df_risk_filtered.empty:
                # Mostra clienti a rischio con colori
                for _, row in df_risk_filtered.iterrows():
                    risk_class = f"risk-{row['Risk Level'].lower()}"

                    st.markdown(f"""
                    <div class="{risk_class}">
                        <h4>{row['Cliente']} - Rischio: {row['Risk Level']} ({row['Risk Score']:.0f}/100)</h4>
                        <p><strong>Fattori di rischio:</strong> {row['Fattori']}</p>
                        <p><strong>Azioni consigliate:</strong> {row['Azioni']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                # Download report rischio
                csv_risk = df_risk.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Scarica Report Rischio Churn (CSV)",
                    csv_risk,
                    "churn_risk_report.csv",
                    "text/csv",
                    key='download_churn'
                )
            else:
                st.success("✅ Nessun cliente nei livelli di rischio selezionati!")
        else:
            st.info("Nessun cliente attivo per l'analisi churn.")

# ════════════════════════════════════════════════════════════
# TAB 4: MRR/ARR TRACKING
# ════════════════════════════════════════════════════════════

with tab4:
    create_section_header(
        "Monthly & Annual Recurring Revenue",
        "Tracking ricavi ricorrenti (essenziale per SaaS business)",
        "💰"
    )

    # KPI MRR/ARR
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "MRR (Monthly)",
            f"€{mrr_data['mrr']:.2f}",
            "Ricavi mensili ricorrenti"
        )

    with col2:
        st.metric(
            "ARR (Annual)",
            f"€{mrr_data['arr']:.2f}",
            "MRR × 12"
        )

    with col3:
        st.metric(
            "Subscriptions Attive",
            mrr_data['active_subscriptions'],
            "Contratti attivi"
        )

    with col4:
        st.metric(
            "ARPU (Avg Revenue)",
            f"€{mrr_data['avg_revenue_per_customer']:.2f}",
            "Per cliente/mese"
        )

    st.divider()

    # Proiezioni
    st.subheader("📈 Proiezioni Revenue")

    col1, col2 = st.columns(2)

    with col1:
        # Proiezione 6 mesi
        projection_6m = mrr_data['mrr'] * 6
        st.metric(
            "Proiezione 6 Mesi",
            f"€{projection_6m:.2f}",
            f"Assumendo MRR costante di €{mrr_data['mrr']:.2f}"
        )

    with col2:
        # Proiezione 12 mesi
        projection_12m = mrr_data['arr']
        st.metric(
            "Proiezione 12 Mesi",
            f"€{projection_12m:.2f}",
            "ARR attuale"
        )

    st.info("""
    **💡 Nota sul MRR/ARR:**

    Queste metriche sono calcolate dai contratti attivi e rappresentano i ricavi ricorrenti.
    Per un business fitness sostenibile:
    - **MRR Growth** dovrebbe essere positivo mese su mese
    - **ARPU** (Average Revenue Per User) dovrebbe aumentare con upselling
    - **Churn** dovrebbe essere < 5% per mantenere MRR growth
    """)

# ════════════════════════════════════════════════════════════
# TAB 5: COHORT ANALYSIS
# ════════════════════════════════════════════════════════════

with tab5:
    create_section_header(
        "Cohort Analysis",
        "Analisi per coorti di clienti (acquisiti nello stesso periodo)",
        "👥"
    )

    # Opzioni cohort
    col1, col2 = st.columns(2)

    with col1:
        cohort_by = st.selectbox(
            "Raggruppa per",
            ["month", "quarter", "year"],
            format_func=lambda x: {
                "month": "Mese",
                "quarter": "Trimestre",
                "year": "Anno"
            }[x],
            key="cohort_by"
        )

    with col2:
        lookback_months = st.number_input(
            "Mesi indietro",
            min_value=3,
            max_value=24,
            value=12,
            step=3,
            key="cohort_lookback"
        )

    # Calcola coorti
    start_cohort = date.today() - relativedelta(months=lookback_months)
    end_cohort = date.today()

    with st.spinner("Analisi coorti in corso..."):
        df_cohorts = analytics.analyze_cohorts(
            cohort_by=cohort_by,
            start_date=start_cohort,
            end_date=end_cohort
        )

    if not df_cohorts.empty:
        st.subheader("📊 Metriche per Coorte")

        # Tabella coorti
        st.dataframe(
            df_cohorts,
            use_container_width=True,
            hide_index=True,
            column_config={
                'cohort': 'Coorte',
                'num_customers': 'Clienti',
                'avg_ltv': 'LTV Medio (€)',
                'avg_retention': 'Retention (%)',
                'total_revenue': 'Revenue Totale (€)'
            }
        )

        # Grafici coorti
        col1, col2 = st.columns(2)

        with col1:
            # LTV per coorte
            fig_ltv = px.bar(
                df_cohorts,
                x='cohort',
                y='avg_ltv',
                title="LTV Medio per Coorte",
                labels={'avg_ltv': 'LTV Medio (€)', 'cohort': 'Coorte'},
                color='avg_ltv',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_ltv, use_container_width=True)

        with col2:
            # Retention per coorte
            fig_ret = px.line(
                df_cohorts,
                x='cohort',
                y='avg_retention',
                title="Retention Rate per Coorte",
                labels={'avg_retention': 'Retention (%)', 'cohort': 'Coorte'},
                markers=True
            )
            fig_ret.add_hline(
                y=80,
                line_dash="dash",
                line_color="green",
                annotation_text="Target: 80%"
            )
            st.plotly_chart(fig_ret, use_container_width=True)

        # Insights
        st.divider()
        st.subheader("💡 Insights")

        # Coorte migliore
        best_cohort = df_cohorts.loc[df_cohorts['avg_ltv'].idxmax()]
        worst_cohort = df_cohorts.loc[df_cohorts['avg_ltv'].idxmin()]

        col1, col2 = st.columns(2)

        with col1:
            st.success(f"""
            **🏆 Coorte Migliore: {best_cohort['cohort']}**

            - LTV Medio: €{best_cohort['avg_ltv']:.2f}
            - Retention: {best_cohort['avg_retention']:.1f}%
            - Clienti: {best_cohort['num_customers']}

            Studia cosa ha funzionato in questo periodo!
            """)

        with col2:
            st.warning(f"""
            **⚠️ Coorte da Migliorare: {worst_cohort['cohort']}**

            - LTV Medio: €{worst_cohort['avg_ltv']:.2f}
            - Retention: {worst_cohort['avg_retention']:.1f}%
            - Clienti: {worst_cohort['num_customers']}

            Identifica problemi di quel periodo e correggi.
            """)
    else:
        st.info("Nessun dato per coorti nel periodo selezionato. Aggiungi più clienti per vedere l'analisi.")

st.divider()
st.caption("🎯 FitManager AI - Financial Intelligence | Metriche professionali per PT business-minded")
