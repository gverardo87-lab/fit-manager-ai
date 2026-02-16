# file: server/pages/04_Cassa.py
"""
💰 Cassa & Bilancio - Versione DASHBOARD

Target: Libera professionista P.IVA forfettaria
Design: Executive Summary + Tabelle chiare + Visual hierarchy

Ispirato a: Stripe Dashboard, QuickBooks, Wave Accounting
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
# CSS OTTIMIZZATO
# ════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* Executive Summary Box */
    .summary-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 12px;
        margin-bottom: 30px;
    }
    
    /* KPI Cards */
    .kpi-card {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
    
    .kpi-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .kpi-label {
        font-size: 14px;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Colors */
    .positive { color: #10b981; }
    .negative { color: #ef4444; }
    .warning { color: #f59e0b; }
    .neutral { color: #6b7280; }
    
    /* Tables */
    .dataframe {
        font-size: 14px;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 20px;
        font-weight: 600;
        color: #111827;
        margin: 20px 0 10px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# DATI BASE
# ════════════════════════════════════════════════════════════

oggi = date.today()
primo_mese = date(oggi.year, oggi.month, 1)
ultimo_giorno = monthrange(oggi.year, oggi.month)[1]
ultimo_mese = date(oggi.year, oggi.month, ultimo_giorno)

# Calcola metriche
bilancio = db.get_bilancio_cassa(primo_mese, ultimo_mese)
saldo_totale = db.get_bilancio_cassa()['saldo_cassa']
previsione = db.get_previsione_cash(30)
rate_pendenti = db.get_rate_pendenti(oggi + timedelta(days=30), solo_future=True)
rate_scadute = db.get_rate_scadute()
spese_fisse = db.get_spese_ricorrenti()

# ════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY (Top Priority)
# ════════════════════════════════════════════════════════════

st.title("💰 Quadro Cassa")

# RIEPILOGO CRITICITÀ
col_alert1, col_alert2 = st.columns(2)

with col_alert1:
    if rate_scadute:
        totale_scaduto = sum(r['importo_previsto'] - r.get('importo_saldato', 0) for r in rate_scadute)
        clienti_scaduti = ", ".join([f"{r['nome']} (€{r['importo_previsto'] - r.get('importo_saldato', 0):.0f})" for r in rate_scadute[:3]])
        if len(rate_scadute) > 3:
            clienti_scaduti += f" +{len(rate_scadute)-3} altri"
        st.error(f"⚠️ **{len(rate_scadute)} rate in ritardo** → €{totale_scaduto:.0f} da recuperare")
        st.caption(f"👥 {clienti_scaduti}")
    else:
        st.success("✅ Nessuna rata in ritardo")

with col_alert2:
    if previsione['saldo_previsto'] < 500:
        st.warning(f"⚠️ **Cash flow basso** → Saldo previsto 30gg: €{previsione['saldo_previsto']:.0f}")
        st.caption(f"📊 Oggi: €{saldo_totale:.0f} + Rate: €{previsione['rate_scadenti']:.0f} - Costi: €{previsione['costi_previsti']:.0f}")
    else:
        st.success(f"✅ Cash flow OK → Previsione 30gg: €{previsione['saldo_previsto']:.0f}")
        st.caption(f"📊 Oggi: €{saldo_totale:.0f} + Rate: €{previsione['rate_scadenti']:.0f} - Costi: €{previsione['costi_previsti']:.0f}")

st.divider()

# KPI PRINCIPALI (3 numeri chiave)
st.subheader("📊 Situazione Finanziaria")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-label'>Saldo in Cassa</div>
        <div class='kpi-value {"positive" if saldo_totale >= 0 else "negative"}'>€ {saldo_totale:,.0f}</div>
        <small>Totale storico</small>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-label'>Questo Mese</div>
        <div class='kpi-value {"positive" if bilancio["saldo_cassa"] >= 0 else "negative"}'>€ {bilancio['saldo_cassa']:,.0f}</div>
        <small>€{bilancio['incassato']:,.0f} entrate · €{bilancio['speso']:,.0f} uscite</small>
    </div>
    """, unsafe_allow_html=True)    
    # Breakdown entrate/uscite questo mese
    with st.expander("📊 Breakdown Mensile"):
        with db._connect() as conn:
            # Entrate per categoria
            entrate_mese = conn.execute("""
                SELECT categoria, SUM(importo) as totale
                FROM movimenti_cassa
                WHERE tipo='ENTRATA' AND data_effettiva BETWEEN ? AND ?
                GROUP BY categoria
                ORDER BY totale DESC
            """, (primo_mese, ultimo_mese)).fetchall()
            
            if entrate_mese:
                st.markdown("**💵 Entrate:**")
                for cat, tot in entrate_mese:
                    st.caption(f"{cat}: €{tot:.0f}")
            
            st.divider()
            
            # Uscite per categoria
            uscite_mese = conn.execute("""
                SELECT categoria, SUM(importo) as totale
                FROM movimenti_cassa
                WHERE tipo='USCITA' AND data_effettiva BETWEEN ? AND ?
                GROUP BY categoria
                ORDER BY totale DESC
            """, (primo_mese, ultimo_mese)).fetchall()
            
            if uscite_mese:
                st.markdown("**💸 Uscite:**")
                for cat, tot in uscite_mese:
                    st.caption(f"{cat}: €{tot:.0f}")
with col3:
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-label'>Previsione 30gg</div>
        <div class='kpi-value {"positive" if previsione["saldo_previsto"] >= 0 else "negative"}'>€ {previsione['saldo_previsto']:,.0f}</div>
        <small>€{previsione['rate_scadenti']:,.0f} attesi · €{previsione['costi_previsti']:,.0f} costi</small>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ════════════════════════════════════════════════════════════
# RATE DA INCASSARE (Tabella Prioritaria)
# ════════════════════════════════════════════════════════════

st.markdown("### 📋 Rate da Incassare")

# TABS: Scadute vs Prossime
tab1, tab2 = st.tabs(["⚠️ In Ritardo" + (f" ({len(rate_scadute)})" if rate_scadute else ""), 
                       "📅 Prossime 30gg" + (f" ({len(rate_pendenti)})" if rate_pendenti else "")])

with tab1:
    if rate_scadute:
        # Prepara dati per tabella
        dati_scadute = []
        for r in rate_scadute:
            data_sc = date.fromisoformat(r['data_scadenza']) if isinstance(r['data_scadenza'], str) else r['data_scadenza']
            giorni_ritardo = (oggi - data_sc).days
            importo_rimanente = r['importo_previsto'] - r.get('importo_saldato', 0)
            
            dati_scadute.append({
                'Cliente': f"{r['nome']} {r['cognome']}",
                'Pacchetto': r['tipo_pacchetto'],
                'Scadenza': data_sc.strftime('%d/%m/%Y'),
                'Giorni Ritardo': giorni_ritardo,
                'Importo': f"€{importo_rimanente:.0f}",
                'Parziale': "Sì" if r.get('importo_saldato', 0) > 0 else "No",
                '_id': r['id'],
                '_importo_num': importo_rimanente
            })
        
        df_scadute = pd.DataFrame(dati_scadute)
        
        # Mostra tabella
        st.dataframe(
            df_scadute[['Cliente', 'Pacchetto', 'Scadenza', 'Giorni Ritardo', 'Importo', 'Parziale']],
            use_container_width=True,
            hide_index=True
        )
        
        # Totale con breakdown dettagliato
        totale_scadute = df_scadute['_importo_num'].sum()
        st.error(f"**TOTALE DA RECUPERARE: €{totale_scadute:,.0f}**")
        
        # Breakdown per cliente (expander)
        with st.expander("🔍 Dettaglio per Cliente"):
            for _, row in df_scadute.iterrows():
                col_d1, col_d2 = st.columns([3, 1])
                with col_d1:
                    st.markdown(f"**{row['Cliente']}** · {row['Pacchetto']}")
                    st.caption(f"Scadenza: {row['Scadenza']} ({row['Giorni Ritardo']} giorni fa)")
                with col_d2:
                    st.markdown(f"**{row['Importo']}**")
                    if row['Parziale'] == "Sì":
                        st.caption("🟡 Parziale")
                st.divider()
        
        # Buttons per pagamento veloce
        st.markdown("**Azioni Rapide:**")
        cols = st.columns(min(len(rate_scadute), 5))
        for idx, (col, rata) in enumerate(zip(cols, rate_scadute[:5])):
            with col:
                importo_da_pagare = rata['importo_previsto'] - rata.get('importo_saldato', 0)
                if st.button(f"✅ {rata['nome']}", key=f"paga_scad_{rata['id']}", use_container_width=True):
                    db.paga_rata_specifica(
                        id_rata=rata['id'],
                        importo_versato=importo_da_pagare,
                        metodo="Contanti",
                        data_pagamento=oggi,
                        note="Pagamento sollecitato"
                    )
                    st.success(f"✅ €{importo_da_pagare:.0f} registrato! Movimento inserito in fondo alla pagina.")
                    st.balloons()
                    st.rerun()
    else:
        st.success("✅ Nessuna rata in ritardo - ottimo lavoro!")

with tab2:
    if rate_pendenti:
        # Prepara dati per tabella
        dati_pendenti = []
        for r in rate_pendenti:
            data_sc = date.fromisoformat(r['data_scadenza']) if isinstance(r['data_scadenza'], str) else r['data_scadenza']
            giorni_mancanti = (data_sc - oggi).days
            importo_rimanente = r['importo_previsto'] - r.get('importo_saldato', 0)
            
            dati_pendenti.append({
                'Cliente': f"{r['nome']} {r['cognome']}",
                'Pacchetto': r['tipo_pacchetto'],
                'Scadenza': data_sc.strftime('%d/%m/%Y'),
                'Tra Giorni': giorni_mancanti,
                'Importo': f"€{importo_rimanente:.0f}",
                'Urgente': "🔴" if giorni_mancanti <= 7 else "",
                '_id': r['id'],
                '_importo_num': importo_rimanente
            })
        
        df_pendenti = pd.DataFrame(dati_pendenti)
        
        # Mostra tabella
        st.dataframe(
            df_pendenti[['Urgente', 'Cliente', 'Pacchetto', 'Scadenza', 'Tra Giorni', 'Importo']],
            use_container_width=True,
            hide_index=True
        )
        
        # Totale con breakdown dettagliato
        totale_pendenti = df_pendenti['_importo_num'].sum()
        st.info(f"**TOTALE ATTESO: €{totale_pendenti:,.0f}**")
        
        # Breakdown per cliente (expander)
        with st.expander("🔍 Dettaglio per Cliente"):
            for _, row in df_pendenti.iterrows():
                col_d1, col_d2 = st.columns([3, 1])
                with col_d1:
                    st.markdown(f"{row['Urgente']} **{row['Cliente']}** · {row['Pacchetto']}")
                    st.caption(f"Scadenza: {row['Scadenza']} (tra {row['Tra Giorni']} giorni)")
                with col_d2:
                    st.markdown(f"**{row['Importo']}**")
                st.divider()
        
        # Buttons per pagamento veloce
        st.markdown("**Azioni Rapide:**")
        cols = st.columns(min(len(rate_pendenti), 5))
        for idx, (col, rata) in enumerate(zip(cols, rate_pendenti[:5])):
            with col:
                importo_da_pagare = rata['importo_previsto'] - rata.get('importo_saldato', 0)
                if st.button(f"✅ {rata['nome']}", key=f"paga_pend_{rata['id']}", use_container_width=True):
                    db.paga_rata_specifica(
                        id_rata=rata['id'],
                        importo_versato=importo_da_pagare,
                        metodo="Contanti",
                        data_pagamento=oggi,
                        note="Pagamento anticipato"
                    )
                    st.success(f"✅ €{importo_da_pagare:.0f} registrato! Movimento inserito in fondo alla pagina.")
                    st.balloons()
                    st.rerun()
    else:
        st.info("Nessuna rata in scadenza nei prossimi 30 giorni")

st.divider()

# ════════════════════════════════════════════════════════════
# SPESE E ENTRATE (Gestione Operativa)
# ════════════════════════════════════════════════════════════

st.markdown("### 💼 Gestione Operativa")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**➕ Registra Spesa Veloce**")
    
    with st.form("quick_spesa", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            categoria_spesa = st.selectbox(
                "Categoria",
                ["Affitto", "Utenze", "Attrezzature", "Marketing", "Formazione", "Altro"]
            )
            importo_spesa = st.number_input("Importo €", min_value=0.0, step=10.0)
        with col_f2:
            data_spesa = st.date_input("Data", value=oggi)
            note_spesa = st.text_input("Note", placeholder="es: Bolletta luce")
        
        if st.form_submit_button("💾 Salva Spesa", type="primary", use_container_width=True):
            if importo_spesa > 0:
                db.registra_spesa(
                    categoria=categoria_spesa,
                    importo=importo_spesa,
                    metodo="Contanti",
                    data_pagamento=data_spesa,
                    note=note_spesa
                )
                st.success(f"✅ Spesa €{importo_spesa:.0f} registrata! Controlla lo storico movimenti sotto.")
                st.balloons()  # Feedback visivo
                st.rerun()

with col_right:
    st.markdown("**📊 Spese Fisse Mensili**")
    
    if spese_fisse:
        totale_fisso = sum(s['importo'] for s in spese_fisse)
        
        # Tabella spese fisse
        dati_fisse = []
        for s in spese_fisse:
            dati_fisse.append({
                'Nome': s['nome'],
                'Categoria': s['categoria'],
                'Importo': f"€{s['importo']:.0f}",
                'Scadenza': f"{s['giorno_scadenza']} del mese"
            })
        
        df_fisse = pd.DataFrame(dati_fisse)
        st.dataframe(df_fisse, use_container_width=True, hide_index=True)
        st.info(f"**Totale mensile: €{totale_fisso:,.0f}**")
    else:
        st.info("Nessuna spesa fissa configurata")
    
    with st.expander("➕ Aggiungi Spesa Fissa"):
        with st.form("add_spesa_fissa"):
            nome_sf = st.text_input("Nome", placeholder="es: Affitto Studio")
            col_sf1, col_sf2 = st.columns(2)
            with col_sf1:
                categoria_sf = st.selectbox("Categoria", ["Affitto", "Utenze", "Assicurazioni", "Altro"])
                importo_sf = st.number_input("Importo mensile €", min_value=0.0, step=50.0)
            with col_sf2:
                giorno_sf = st.number_input("Giorno scadenza", min_value=1, max_value=28, value=1)
            
            if st.form_submit_button("💾 Salva", type="primary"):
                if nome_sf and importo_sf > 0:
                    db.add_spesa_ricorrente(nome_sf, categoria_sf, importo_sf, "MENSILE", giorno_sf)
                    st.success(f"✅ {nome_sf} aggiunto!")
                    st.rerun()

st.divider()

# ════════════════════════════════════════════════════════════
# ANALISI TREND (Grafico)
# ════════════════════════════════════════════════════════════

st.markdown("### 📈 Trend Ultimi 6 Mesi")

# Calcola ultimi 6 mesi
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
        'Uscite': bil['speso'],
        'Saldo': bil['saldo_cassa']
    })

df_mesi = pd.DataFrame(mesi_dati)

# Grafico combinato
fig = px.bar(
    df_mesi,
    x='Mese',
    y=['Entrate', 'Uscite', 'Saldo'],
    barmode='group',
    color_discrete_map={'Entrate': '#10b981', 'Uscite': '#ef4444', 'Saldo': '#3b82f6'},
    height=400
)
fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=30, b=0),
    yaxis_title="Euro (€)"
)
st.plotly_chart(fig, use_container_width=True)

# Tabella riassuntiva
st.dataframe(df_mesi, use_container_width=True, hide_index=True)

st.divider()

# ════════════════════════════════════════════════════════════
# MOVIMENTI RECENTI (Storico)
# ════════════════════════════════════════════════════════════

st.markdown("### 📋 Storico Movimenti")

col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    filtro_tipo = st.selectbox(
        "Filtra per tipo",
        ["Tutti", "Solo Entrate", "Solo Uscite"],
        key="filtro_tipo_mov"
    )
with col_filter2:
    limite_mov = st.selectbox(
        "Mostra ultimi",
        [10, 20, 50, 100],
        index=1,
        key="limite_mov"
    )

with db._connect() as conn:
    query = """
        SELECT data_movimento, data_effettiva, tipo, categoria, importo, note, id_cliente, id
        FROM movimenti_cassa
    """
    
    if filtro_tipo == "Solo Entrate":
        query += " WHERE tipo='ENTRATA'"
    elif filtro_tipo == "Solo Uscite":
        query += " WHERE tipo='USCITA'"
    
    # ORDINAMENTO CORRETTO: per timestamp (data + ora), non solo data
    query += f" ORDER BY data_movimento DESC, id DESC LIMIT {limite_mov}"
    
    movimenti = [dict(r) for r in conn.execute(query).fetchall()]

if movimenti:
    from datetime import datetime
    
    dati_mov = []
    for idx, m in enumerate(movimenti):
        # Per entrate con id_cliente, mostra il nome cliente
        cliente_info = "-"
        if m.get('id_cliente'):
            with db._connect() as conn:
                cliente = conn.execute(
                    "SELECT nome, cognome FROM clienti WHERE id=?",
                    (m['id_cliente'],)
                ).fetchone()
                if cliente:
                    cliente_info = f"{cliente['nome']} {cliente['cognome']}"
        
        # Parsea data_movimento per estrarre ora
        data_mov_str = m['data_movimento']
        try:
            if isinstance(data_mov_str, str):
                data_mov = datetime.fromisoformat(data_mov_str.replace(' ', 'T'))
            else:
                data_mov = data_mov_str
            ora_str = data_mov.strftime('%H:%M')
        except:
            ora_str = ""
        
        # Formatta data in modo user-friendly (stile app bancarie)
        data_eff = m['data_effettiva']
        if isinstance(data_eff, str):
            data_eff = date.fromisoformat(data_eff)
        
        if data_eff == oggi:
            data_display = f"🆕 Oggi {ora_str}"
            badge = ""
        elif data_eff == oggi - timedelta(days=1):
            data_display = f"Ieri {ora_str}"
            badge = ""
        elif data_eff >= oggi - timedelta(days=7):
            # Ultimi 7 giorni: mostra giorno settimana
            giorni = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
            data_display = f"{giorni[data_eff.weekday()]} {data_eff.strftime('%d/%m')} {ora_str}"
            badge = ""
        else:
            data_display = f"{data_eff.strftime('%d/%m/%Y')} {ora_str}"
            badge = ""
        
        # Badge NUOVO per prime 3 entry di oggi
        if idx < 3 and data_eff == oggi:
            badge = "🆕"
        
        dati_mov.append({
            'Data': data_display,
            'Tipo': "💵 Entrata" if m['tipo'] == 'ENTRATA' else "💸 Uscita",
            'Categoria': f"{badge} {m['categoria']}" if badge else m['categoria'],
            'Cliente': cliente_info,
            'Importo': f"€{m['importo']:.2f}",
            'Note': m['note'] or "-"
        })
    
    df_mov = pd.DataFrame(dati_mov)
    st.dataframe(df_mov, use_container_width=True, hide_index=True)
    
    # Riepilogo filtrato
    totale_entrate_filt = sum(m['importo'] for m in movimenti if m['tipo'] == 'ENTRATA')
    totale_uscite_filt = sum(m['importo'] for m in movimenti if m['tipo'] == 'USCITA')
    st.info(f"📊 Periodo mostrato: €{totale_entrate_filt:.0f} entrate · €{totale_uscite_filt:.0f} uscite · Saldo: €{totale_entrate_filt - totale_uscite_filt:.0f}")
else:
    st.info("Nessun movimento registrato")

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════

st.divider()
st.caption("💡 Dashboard ottimizzato per P.IVA forfettaria · Aggiornamento: " + oggi.strftime('%d/%m/%Y'))
