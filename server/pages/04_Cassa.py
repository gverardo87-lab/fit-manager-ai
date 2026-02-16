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
import plotly.graph_objects as go
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
spese_fisse_non_pagate = db.get_spese_fisse_non_pagate()  # Nuova metrica

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
    # Priorità 1: Spese fisse non pagate (più urgente)
    if spese_fisse_non_pagate:
        totale_non_pagato = sum(s['importo'] for s in spese_fisse_non_pagate)
        nomi_spese = ", ".join([f"{s['nome']} (€{s['importo']:.0f})" for s in spese_fisse_non_pagate[:2]])
        if len(spese_fisse_non_pagate) > 2:
            nomi_spese += f" +{len(spese_fisse_non_pagate)-2} altre"
        st.warning(f"⚠️ **{len(spese_fisse_non_pagate)} spese fisse non pagate** → €{totale_non_pagato:.0f}")
        st.caption(f"💳 {nomi_spese}")
    # Priorità 2: Cash flow basso
    elif previsione['saldo_previsto'] < 500:
        st.warning(f"⚠️ **Cash flow basso** → Saldo previsto 30gg: €{previsione['saldo_previsto']:.0f}")
        st.caption(f"📊 Oggi: €{saldo_totale:.0f} + Rate: €{previsione['rate_scadenti']:.0f} - Costi: €{previsione['costi_previsti']:.0f}")
    else:
        st.success(f"✅ Cash flow OK → Previsione 30gg: €{previsione['saldo_previsto']:.0f}")
        st.caption(f"📊 Oggi: €{saldo_totale:.0f} + Rate: €{previsione['rate_scadenti']:.0f} - Costi: €{previsione['costi_previsti']:.0f}")

st.divider()

# KPI PRINCIPALI (3 numeri chiave)
st.subheader("📊 Situazione Finanziaria")
st.caption("💰 FLUSSO DI CASSA = Movimenti reali già registrati | 📈 PREVISIONE = Stima incassi futuri da rate programmate")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-label'>💰 Saldo in Cassa (REALE)</div>
        <div class='kpi-value {"positive" if saldo_totale >= 0 else "negative"}'>€ {saldo_totale:,.0f}</div>
        <small>Capitale effettivo accumulato</small>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-label'>💰 Flusso Questo Mese (REALE)</div>
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
        <div class='kpi-label'>📈 Previsione 30gg (STIMA)</div>
        <div class='kpi-value {"positive" if previsione["saldo_previsto"] >= 0 else "negative"}'>€ {previsione['saldo_previsto']:,.0f}</div>
        <small>Saldo attuale + rate future - costi attesi</small>
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

# Prima riga: Form Spesa + Form Entrata Spot
col_spesa, col_entrata = st.columns(2)

with col_spesa:
    st.markdown("**💸 Registra Spesa Veloce**")
    
    with st.form("quick_spesa", clear_on_submit=True):
        # Costruisci dropdown dinamico con spese fisse NON PAGATE + categorie standard
        # IMPORTANTE: Mostra solo spese fisse NON ancora pagate questo mese per prevenire doppioni
        categorie_standard = ["──── ALTRE CATEGORIE ────", "Marketing", "Formazione", "Attrezzature", "Trasporti", "Altro"]
        
        if spese_fisse_non_pagate:
            categorie_spese_fisse = [f"📌 {s['nome']} (€{s['importo']:.0f} - {s['giorno_scadenza']}°)" for s in spese_fisse_non_pagate]
            opzioni_categoria = ["──── SPESE FISSE DA PAGARE ────"] + categorie_spese_fisse + categorie_standard
        else:
            opzioni_categoria = categorie_standard[1:]  # Salta header se no spese fisse da pagare
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            categoria_sel = st.selectbox(
                "Categoria",
                opzioni_categoria,
                key="cat_spesa"
            )
            
            # Se seleziona spesa fissa, pre-compila importo
            importo_default = 0.0
            id_spesa_ricorrente = None
            categoria_finale = categoria_sel
            
            if categoria_sel.startswith("📌 "):
                # Estrai nome spesa fissa (rimuovi emoji e parentesi)
                nome_spesa = categoria_sel.split(" (")[0].replace("📌 ", "")
                # Trova spesa corrispondente tra quelle NON pagate
                for sf in spese_fisse_non_pagate:
                    if sf['nome'] == nome_spesa:
                        importo_default = float(sf['importo'])
                        id_spesa_ricorrente = sf['id']
                        categoria_finale = sf['categoria']  # Usa categoria della spesa fissa
                        break
            
            importo_spesa = st.number_input("Importo €", min_value=0.0, step=10.0, value=importo_default, key="imp_spesa")
        with col_f2:
            data_spesa = st.date_input("Data", value=oggi, key="data_spesa_input")
            note_spesa = st.text_input("Note", placeholder="es: Bolletta luce", key="note_spesa")
        
        if st.form_submit_button("💾 Salva Spesa", type="primary", use_container_width=True):
            if importo_spesa > 0 and not categoria_sel.startswith("────"):
                try:
                    db.registra_spesa(
                        categoria=categoria_finale,
                        importo=importo_spesa,
                        metodo="Bonifico",
                        data_pagamento=data_spesa,
                        note=note_spesa,
                        id_spesa_ricorrente=id_spesa_ricorrente  # Collegamento diretto
                    )
                    st.success(f"✅ Spesa €{importo_spesa:.0f} registrata! Controlla lo storico movimenti sotto.")
                    st.balloons()
                    st.rerun()
                except ValueError as e:
                    # Protezione doppi pagamenti spese ricorrenti
                    st.error(f"🚫 **Pagamento duplicato bloccato!**\n\n{str(e)}\n\nRicarica la pagina per vedere lo status aggiornato.")
            elif categoria_sel.startswith("────"):
                st.error("⚠️ Seleziona una categoria valida")

with col_entrata:
    st.markdown("**💵 Registra Entrata Spot**")
    
    with st.form("quick_entrata", clear_on_submit=True):
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            categoria_entrata = st.selectbox(
                "Tipo",
                ["Lezione Singola", "Consulenza Spot", "Vendita Prodotto", "Altro"],
                key="cat_entrata"
            )
            importo_entrata = st.number_input("Importo €", min_value=0.0, step=10.0, key="imp_entrata")
        with col_e2:
            data_entrata = st.date_input("Data", value=oggi, key="data_entrata")
            
            # Cliente opzionale
            clienti_attivi = db.get_clienti_attivi()
            opzioni_clienti = ["--Nessun cliente--"] + [f"{c['nome']} {c['cognome']}" for c in clienti_attivi]
            cliente_sel = st.selectbox("Cliente (opz.)", opzioni_clienti, key="cli_entrata")
            
        note_entrata = st.text_input("Note", placeholder="es: Lezione prova", key="note_entrata")
        
        if st.form_submit_button("💾 Salva Entrata", type="primary", use_container_width=True):
            if importo_entrata > 0:
                # Trova id_cliente se selezionato
                id_cliente_entrata = None
                if cliente_sel != "--Nessun cliente--":
                    idx_sel = opzioni_clienti.index(cliente_sel) - 1
                    id_cliente_entrata = clienti_attivi[idx_sel]['id']
                
                db.registra_entrata_spot(
                    categoria=categoria_entrata,
                    importo=importo_entrata,
                    metodo="Contanti",
                    data_pagamento=data_entrata,
                    id_cliente=id_cliente_entrata,
                    note=note_entrata
                )
                st.success(f"✅ Entrata €{importo_entrata:.0f} registrata! Controlla lo storico movimenti sotto.")
                st.balloons()
                st.rerun()

st.divider()

# Seconda sezione: Spese Fisse (full width)
with st.expander("📊 Spese Fisse Mensili", expanded=False):
    # Quick Actions per spese non pagate
    if spese_fisse_non_pagate:
        st.warning(f"⚠️ **{len(spese_fisse_non_pagate)} spese non pagate questo mese**")
        
        cols_quick = st.columns(min(len(spese_fisse_non_pagate), 3))
        for idx, (col, spesa) in enumerate(zip(cols_quick, spese_fisse_non_pagate[:3])):
            with col:
                st.markdown(f"**{spesa['nome']}**")
                st.caption(f"Scadenza: {spesa['giorno_scadenza']} {oggi.strftime('%B')}")
                st.caption(f"💶 €{spesa['importo']:.0f}")
                
                if st.button(f"💳 Paga Ora", key=f"quick_paga_{spesa['id']}", use_container_width=True, type="primary"):
                    try:
                        db.registra_spesa(
                            categoria=spesa['categoria'],
                            importo=spesa['importo'],
                            metodo="Bonifico",
                            data_pagamento=oggi,
                            note=f"Pagamento {spesa['nome']} - {oggi.strftime('%B %Y')}",
                            id_spesa_ricorrente=spesa['id']
                        )
                        st.success(f"✅ {spesa['nome']} pagata!")
                        st.balloons()
                        st.rerun()
                    except ValueError as e:
                        st.error(f"🚫 Pagamento già registrato! Ricarica la pagina.")
        
        if len(spese_fisse_non_pagate) > 3:
            st.info(f"➕ {len(spese_fisse_non_pagate)-3} altre spese da pagare (vedi dropdown sopra)")
        
        st.divider()
    
    # Tabella completa spese fisse
    if spese_fisse:
        st.markdown("**📋 Tutte le Spese Fisse Configurate**")
        totale_fisso = sum(s['importo'] for s in spese_fisse)
        
        col_sf_left, col_sf_right = st.columns([2, 1])
        
        with col_sf_left:
            # Tabella spese fisse con status
            dati_fisse = []
            for s in spese_fisse:
                # Verifica se pagata questo mese
                pagata_questo_mese = s['id'] not in [sp['id'] for sp in spese_fisse_non_pagate]
                status = "✅ Pagata" if pagata_questo_mese else ("⏳ Futura" if s['giorno_scadenza'] > oggi.day else "❌ Non Pagata")
                
                dati_fisse.append({
                    'Nome': s['nome'],
                    'Categoria': s['categoria'],
                    'Importo': f"€{s['importo']:.0f}",
                    'Scadenza': f"{s['giorno_scadenza']}° del mese",
                    'Status': status
                })
            
            df_fisse = pd.DataFrame(dati_fisse)
            st.dataframe(df_fisse, use_container_width=True, hide_index=True)
        
        with col_sf_right:
            st.metric("Totale Mensile", f"€{totale_fisso:,.0f}")
            
            # Breakdown pagato/non pagato
            totale_non_pagato = sum(s['importo'] for s in spese_fisse_non_pagate)
            totale_pagato = totale_fisso - totale_non_pagato
            st.caption(f"✅ Pagato: €{totale_pagato:.0f}")
            st.caption(f"❌ Da pagare: €{totale_non_pagato:.0f}")
    else:
        st.info("Nessuna spesa fissa configurata")
    
    # Form per aggiungere spesa fissa (usa checkbox per mostrare/nascondere)
    st.divider()
    mostra_form = st.checkbox("➕ Aggiungi Spesa Fissa", key="mostra_form_spesa_fissa")
    
    if mostra_form:
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

st.markdown("### 📈 Analisi Trend Flusso di Cassa")
st.caption("""
💰 **FLUSSO DI CASSA** = Movimenti effettivi registrati (quanto è entrato/uscito in quel mese)  
💎 **SALDO TOTALE** = Capitale cumulativo alla fine del mese (tutti i movimenti dall'inizio fino a quella data)
""")

# Metrica prominente: SALDO ATTUALE
col_saldo_attuale, col_variazione = st.columns([2, 1])
with col_saldo_attuale:
    st.metric(
        "💰 Saldo Totale Attuale",
        f"€ {saldo_totale:.2f}",
        delta=f"€ {bilancio['saldo_cassa']:.2f} questo mese",
        delta_color="normal" if bilancio['saldo_cassa'] >= 0 else "inverse"
    )
with col_variazione:
    perc_var = (bilancio['saldo_cassa'] / saldo_totale * 100) if saldo_totale != 0 else 0
    st.metric(
        "Variazione Mensile",
        f"{perc_var:.1f}%",
        delta="positivo" if bilancio['saldo_cassa'] >= 0 else "negativo",
        delta_color="off"
    )

st.caption("---")

# Calcola ultimi 6 mesi con saldo progressivo
mesi_dati = []

for i in range(5, -1, -1):
    mese_calc = oggi - timedelta(days=30*i)
    primo = date(mese_calc.year, mese_calc.month, 1)
    ultimo_g = monthrange(mese_calc.year, mese_calc.month)[1]
    ultimo = date(mese_calc.year, mese_calc.month, ultimo_g)
    
    # FLUSSO DI CASSA DEL MESE (quanto è entrato/uscito in quel mese)
    bil_mese = db.get_bilancio_cassa(primo, ultimo)
    
    # SALDO TOTALE ALLA FINE DEL MESE (tutto dall'inizio dei tempi fino a ultimo giorno del mese)
    saldo_cumulativo = db.get_bilancio_cassa(data_fine=ultimo)
    
    mesi_dati.append({
        'Mese': primo.strftime('%b %Y'),
        'Entrate': bil_mese['incassato'],
        'Uscite': bil_mese['speso'],
        'Saldo Mese': bil_mese['saldo_cassa'],
        'Saldo Totale': saldo_cumulativo['saldo_cassa']
    })

df_mesi = pd.DataFrame(mesi_dati)

# Grafico combinato con linea saldo totale
import plotly.graph_objects as go

fig = go.Figure()

# Barre per Entrate e Uscite
fig.add_trace(go.Bar(
    name='Entrate',
    x=df_mesi['Mese'],
    y=df_mesi['Entrate'],
    marker_color='#10b981'
))
fig.add_trace(go.Bar(
    name='Uscite',
    x=df_mesi['Mese'],
    y=df_mesi['Uscite'],
    marker_color='#ef4444'
))
fig.add_trace(go.Bar(
    name='Saldo Mese',
    x=df_mesi['Mese'],
    y=df_mesi['Saldo Mese'],
    marker_color='#3b82f6'
))

# LINEA SALDO TOTALE PROGRESSIVO (l'elemento chiave!)
fig.add_trace(go.Scatter(
    name='💰 Saldo Totale',
    x=df_mesi['Mese'],
    y=df_mesi['Saldo Totale'],
    mode='lines+markers+text',
    line=dict(color='#8b5cf6', width=3),
    marker=dict(size=10, symbol='diamond'),
    text=[f"€{val:.0f}" for val in df_mesi['Saldo Totale']],
    textposition='top center',
    textfont=dict(size=11, color='#8b5cf6', family='Arial Black'),
    yaxis='y2'  # Asse secondario
))

fig.update_layout(
    barmode='group',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=30, b=0),
    yaxis=dict(title="Flusso Mensile (€)"),
    yaxis2=dict(
        title="Saldo Totale (€)",
        overlaying='y',
        side='right',
        showgrid=False
    ),
    height=450,
    hovermode='x unified'
)
st.plotly_chart(fig, use_container_width=True)

# Tabella riassuntiva
st.dataframe(df_mesi, use_container_width=True, hide_index=True)

st.divider()

# ════════════════════════════════════════════════════════════
# MOVIMENTI RECENTI (Storico)
# ════════════════════════════════════════════════════════════

st.markdown("### 📋 Storico Movimenti")

col_filter1, col_filter2, col_filter3 = st.columns(3)
with col_filter1:
    filtro_tipo = st.selectbox(
        "Filtra per tipo",
        ["Tutti", "Solo Entrate", "Solo Uscite"],
        key="filtro_tipo_mov"
    )
with col_filter2:
    # Carica lista clienti per filtro
    clienti_attivi = db.get_clienti_attivi()
    opzioni_clienti = ["Tutti i clienti"] + [f"{c['nome']} {c['cognome']}" for c in clienti_attivi]
    filtro_cliente = st.selectbox(
        "Filtra per cliente",
        opzioni_clienti,
        key="filtro_cliente_mov"
    )
with col_filter3:
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
    
    conditions = []
    params = []
    
    if filtro_tipo == "Solo Entrate":
        conditions.append("tipo='ENTRATA'")
    elif filtro_tipo == "Solo Uscite":
        conditions.append("tipo='USCITA'")
    
    if filtro_cliente != "Tutti i clienti":
        # Trova ID cliente selezionato
        idx_cliente = opzioni_clienti.index(filtro_cliente) - 1  # -1 perché "Tutti i clienti" è primo
        id_cliente_selezionato = clienti_attivi[idx_cliente]['id']
        conditions.append("id_cliente=?")
        params.append(id_cliente_selezionato)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # ORDINAMENTO CORRETTO: per timestamp (data + ora), non solo data
    query += f" ORDER BY data_movimento DESC, id DESC LIMIT {limite_mov}"
    
    movimenti = [dict(r) for r in conn.execute(query, params).fetchall()]

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
    
    # ═══════════════════════════════════════════════════════
    # POPUP DETTAGLI MOVIMENTO
    # ═══════════════════════════════════════════════════════
    st.divider()
    st.markdown("**🔍 Visualizza Dettagli Movimento**")
    
    # Crea lista opzioni per selectbox
    opzioni_movimenti = [f"#{m['id']} - {m['data_effettiva']} - {m['categoria']} (€{m['importo']:.2f})" for m in movimenti]
    
    movimento_selezionato = st.selectbox(
        "Seleziona un movimento per vedere i dettagli completi:",
        ["-- Seleziona movimento --"] + opzioni_movimenti,
        key="select_movimento"
    )
    
    if movimento_selezionato != "-- Seleziona movimento --":
        # Estrai ID dal testo selezionato
        idx_movimento = opzioni_movimenti.index(movimento_selezionato)
        movimento_dettaglio = movimenti[idx_movimento]
        
        # Recupera cliente se presente
        cliente_nome = "-"
        if movimento_dettaglio.get('id_cliente'):
            with db._connect() as conn:
                cliente = conn.execute(
                    "SELECT nome, cognome FROM clienti WHERE id=?",
                    (movimento_dettaglio['id_cliente'],)
                ).fetchone()
                if cliente:
                    cliente_nome = f"{cliente['nome']} {cliente['cognome']}"
        
        # Box dettagli con stile
        tipo_icon = "💵" if movimento_dettaglio['tipo'] == 'ENTRATA' else "💸"
        tipo_color = "green" if movimento_dettaglio['tipo'] == 'ENTRATA' else "red"
        
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {tipo_color};">
            <h4 style="margin-top: 0;">{tipo_icon} Dettagli Movimento #{movimento_dettaglio['id']}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col_det1, col_det2, col_det3 = st.columns(3)
        
        with col_det1:
            st.metric("Importo", f"€{movimento_dettaglio['importo']:.2f}")
            st.caption(f"**Tipo:** {movimento_dettaglio['tipo']}")
        
        with col_det2:
            st.metric("Categoria", movimento_dettaglio['categoria'])
            st.caption(f"**Metodo:** {movimento_dettaglio.get('metodo', 'N/D')}")
        
        with col_det3:
            st.metric("Cliente", cliente_nome)
            st.caption(f"**Data:** {movimento_dettaglio['data_effettiva']}")
        
        if movimento_dettaglio.get('note'):
            st.info(f"📝 **Note:** {movimento_dettaglio['note']}")
        
        # Timestamp registrazione
        st.caption(f"🕐 Registrato il: {movimento_dettaglio['data_movimento']}")
        
        # Future: pulsanti Modifica/Elimina
        # col_btn1, col_btn2 = st.columns(2)
        # with col_btn1:
        #     if st.button("✏️ Modifica", use_container_width=True):
        #         st.warning("Funzione in sviluppo")
        # with col_btn2:
        #     if st.button("🗑️ Elimina", use_container_width=True, type="secondary"):
        #         st.warning("Funzione in sviluppo")

else:
    st.info("Nessun movimento registrato")

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════

st.divider()
st.caption("💡 Dashboard ottimizzato per P.IVA forfettaria · Aggiornamento: " + oggi.strftime('%d/%m/%Y'))
