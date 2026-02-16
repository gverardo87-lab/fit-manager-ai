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
from core.ui_components import badge, status_badge, format_currency, loading_message, section_divider_component, empty_state_component

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
        <div class='kpi-value {"positive" if saldo_totale >= 0 else "negative"}'>{format_currency(saldo_totale, 0)}</div>
        <small>Capitale effettivo accumulato</small>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-label'>💰 Flusso Questo Mese (REALE)</div>
        <div class='kpi-value {"positive" if bilancio["saldo_cassa"] >= 0 else "negative"}'>{format_currency(bilancio['saldo_cassa'], 0)}</div>
        <small>{format_currency(bilancio['incassato'], 0)} entrate · {format_currency(bilancio['speso'], 0)} uscite</small>
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
        <div class='kpi-value {"positive" if previsione["saldo_previsto"] >= 0 else "negative"}'>{format_currency(previsione['saldo_previsto'], 0)}</div>
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
        st.error(f"**TOTALE DA RECUPERARE: {format_currency(totale_scadute, 0)}**")
        
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
        st.info(f"**TOTALE ATTESO: {format_currency(totale_pendenti, 0)}**")
        
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
            st.metric("Totale Mensile", format_currency(totale_fisso, 0))
            
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
        format_currency(saldo_totale),
        delta=f"{format_currency(bilancio['saldo_cassa'], 0)} questo mese",
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
# MOVIMENTI RECENTI (Storico) - ENHANCED
# ════════════════════════════════════════════════════════════

st.markdown("### 📋 Storico Movimenti")
st.caption("🔍 Filtra e analizza tutte le transazioni - Stile app bancaria moderna")

# ═══ RIGA 1 FILTRI: Date Range + Tipo + Cliente ═══
col_f1, col_f2, col_f3, col_f4 = st.columns([1.5, 1.5, 1.5, 1.5])

with col_f1:
    # Default: ultimi 30 giorni
    data_da = st.date_input(
        "📅 Da",
        value=oggi - timedelta(days=30),
        max_value=oggi,
        key="filtro_data_da"
    )

with col_f2:
    data_a = st.date_input(
        "📅 A",
        value=oggi,
        max_value=oggi,
        key="filtro_data_a"
    )

with col_f3:
    filtro_tipo = st.selectbox(
        "Tipo Movimento",
        ["Tutti", "💵 Solo Entrate", "💸 Solo Uscite"],
        key="filtro_tipo_mov"
    )

with col_f4:
    # Carica lista clienti per filtro
    clienti_attivi = db.get_clienti_attivi()
    opzioni_clienti = ["Tutti i clienti"] + [f"{c['nome']} {c['cognome']}" for c in clienti_attivi]
    filtro_cliente = st.selectbox(
        "Cliente",
        opzioni_clienti,
        key="filtro_cliente_mov"
    )

# ═══ RIGA 2 FILTRI: Categoria + Ricerca + Ordinamento + Limite ═══
col_f5, col_f6, col_f7, col_f8 = st.columns([1.5, 2, 1.5, 1])

with col_f5:
    # Recupera categorie esistenti dinamicamente
    with db._connect() as conn:
        categorie_esistenti = [r[0] for r in conn.execute(
            "SELECT DISTINCT categoria FROM movimenti_cassa ORDER BY categoria"
        ).fetchall()]
    
    opzioni_categorie = ["Tutte le categorie"] + categorie_esistenti
    filtro_categoria = st.selectbox(
        "Categoria",
        opzioni_categorie,
        key="filtro_categoria_mov"
    )

with col_f6:
    ricerca_testo = st.text_input(
        "🔍 Cerca in note",
        placeholder="es: stipendio, affitto, cliente...",
        key="ricerca_mov"
    )

with col_f7:
    ordinamento = st.selectbox(
        "Ordinamento",
        ["Più recenti", "Meno recenti", "Importo ↑", "Importo ↓"],
        key="ordinamento_mov"
    )

with col_f8:
    limite_mov = st.selectbox(
        "N°",
        [10, 20, 50, 100, 500],
        index=2,  # Default 50
        key="limite_mov"
    )

# ═══ COSTRUZIONE QUERY DINAMICA ═══
with db._connect() as conn:
    query = """
        SELECT data_movimento, data_effettiva, tipo, categoria, importo, note, id_cliente, id
        FROM movimenti_cassa
    """
    
    conditions = []
    params = []
    
    # Filtro date range
    if data_da:
        conditions.append("data_effettiva >= ?")
        params.append(data_da)
    if data_a:
        conditions.append("data_effettiva <= ?")
        params.append(data_a)
    
    # Filtro tipo
    if filtro_tipo == "💵 Solo Entrate":
        conditions.append("tipo='ENTRATA'")
    elif filtro_tipo == "💸 Solo Uscite":
        conditions.append("tipo='USCITA'")
    
    # Filtro cliente
    if filtro_cliente != "Tutti i clienti":
        idx_cliente = opzioni_clienti.index(filtro_cliente) - 1
        id_cliente_selezionato = clienti_attivi[idx_cliente]['id']
        conditions.append("id_cliente=?")
        params.append(id_cliente_selezionato)
    
    # Filtro categoria
    if filtro_categoria != "Tutte le categorie":
        conditions.append("categoria=?")
        params.append(filtro_categoria)
    
    # Ricerca testuale in note
    if ricerca_testo and ricerca_testo.strip():
        conditions.append("(note LIKE ? OR categoria LIKE ?)")
        search_term = f"%{ricerca_testo.strip()}%"
        params.append(search_term)
        params.append(search_term)
    
    # Aggiungi WHERE se ci sono condizioni
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # Ordinamento
    if ordinamento == "Più recenti":
        query += " ORDER BY data_movimento DESC, id DESC"
    elif ordinamento == "Meno recenti":
        query += " ORDER BY data_movimento ASC, id ASC"
    elif ordinamento == "Importo ↑":
        query += " ORDER BY importo ASC"
    elif ordinamento == "Importo ↓":
        query += " ORDER BY importo DESC"
    
    query += f" LIMIT {limite_mov}"
    
    movimenti = [dict(r) for r in conn.execute(query, params).fetchall()]

# ═══ VISUALIZZAZIONE RISULTATI ═══
if movimenti:
    from datetime import datetime
    
    dati_mov = []
    for idx, m in enumerate(movimenti):
        # Cliente info
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
        
        # Formatta data in modo user-friendly
        data_eff = m['data_effettiva']
        if isinstance(data_eff, str):
            data_eff = date.fromisoformat(data_eff)
        
        if data_eff == oggi:
            data_display = f"🆕 Oggi {ora_str}"
        elif data_eff == oggi - timedelta(days=1):
            data_display = f"Ieri {ora_str}"
        elif data_eff >= oggi - timedelta(days=7):
            giorni = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
            data_display = f"{giorni[data_eff.weekday()]} {data_eff.strftime('%d/%m')} {ora_str}"
        else:
            data_display = f"{data_eff.strftime('%d/%m/%Y')} {ora_str}"
        
        # Badge tipo con colori
        if m['tipo'] == 'ENTRATA':
            tipo_badge = badge("ENTRATA", "success", "💵")
        else:
            tipo_badge = badge("USCITA", "danger", "💸")
        
        dati_mov.append({
            'ID': f"#{m['id']}",
            'Data': data_display,
            'Tipo': tipo_badge,
            'Categoria': m['categoria'],
            'Cliente': cliente_info,
            'Importo': format_currency(m['importo']),
            'Note': (m['note'] or "-")[:50] + "..." if m.get('note') and len(m['note']) > 50 else (m['note'] or "-")
        })
    
    df_mov = pd.DataFrame(dati_mov)
    
    # Render dataframe con HTML badges
    st.markdown(df_mov.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # ═══ STATISTICHE PERIODO FILTRATO ═══
    st.markdown("<br>", unsafe_allow_html=True)
    
    totale_entrate_filt = sum(m['importo'] for m in movimenti if m['tipo'] == 'ENTRATA')
    totale_uscite_filt = sum(m['importo'] for m in movimenti if m['tipo'] == 'USCITA')
    saldo_filt = totale_entrate_filt - totale_uscite_filt
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    stat_col1.metric("💵 Totale Entrate", format_currency(totale_entrate_filt, 0))
    stat_col2.metric("💸 Totale Uscite", format_currency(totale_uscite_filt, 0))
    stat_col3.metric("📊 Saldo Periodo", format_currency(saldo_filt, 0), delta="Positivo" if saldo_filt >= 0 else "Negativo")
    stat_col4.metric("📝 Movimenti", len(movimenti))
    
    # ═══ EXPORT CSV ═══
    if st.button("📥 Esporta in CSV", key="export_csv"):
        csv_data = df_mov.to_csv(index=False)
        st.download_button(
            label="⬇️ Scarica CSV",
            data=csv_data,
            file_name=f"movimenti_{data_da}_{data_a}.csv",
            mime="text/csv"
        )
    
    # ═══════════════════════════════════════════════════════
    # POPUP DETTAGLI MOVIMENTO
    # ═══════════════════════════════════════════════════════
    st.divider()
    st.markdown("**🔍 Visualizza Dettagli Movimento**")
    
    # Crea lista opzioni per selectbox
    opzioni_movimenti = [f"#{m['id']} - {m['data_effettiva']} - {m['categoria']} ({format_currency(m['importo'])})" for m in movimenti]
    
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
            st.metric("Importo", format_currency(movimento_dettaglio['importo']))
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
        
        # ═══ AZIONI: MODIFICA / ELIMINA ═══
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Inizializza session state per edit/delete
        if 'editing_movimento_id' not in st.session_state:
            st.session_state.editing_movimento_id = None
        if 'deleting_movimento_id' not in st.session_state:
            st.session_state.deleting_movimento_id = None
        
        # ═══ MODALITÀ EDIT ═══
        if st.session_state.editing_movimento_id == movimento_dettaglio['id']:
            st.markdown("---")
            st.markdown("### ✏️ Modifica Movimento")
            
            with st.form(key=f"form_edit_mov_{movimento_dettaglio['id']}"):
                edit_col1, edit_col2 = st.columns(2)
                
                with edit_col1:
                    # Data effettiva
                    data_eff_edit = movimento_dettaglio['data_effettiva']
                    if isinstance(data_eff_edit, str):
                        data_eff_edit = date.fromisoformat(data_eff_edit)
                    
                    nuovo_data = st.date_input(
                        "Data effettiva",
                        value=data_eff_edit,
                        max_value=oggi
                    )
                    
                    # Tipo
                    tipo_idx = 0 if movimento_dettaglio['tipo'] == 'ENTRATA' else 1
                    nuovo_tipo = st.selectbox(
                        "Tipo",
                        ["ENTRATA", "USCITA"],
                        index=tipo_idx
                    )
                    
                    # Importo
                    nuovo_importo = st.number_input(
                        "Importo (€)",
                        min_value=0.0,
                        value=float(movimento_dettaglio['importo']),
                        step=10.0,
                        format="%.2f"
                    )
                
                with edit_col2:
                    # Categoria
                    with db._connect() as conn:
                        categorie_esistenti = [r[0] for r in conn.execute(
                            "SELECT DISTINCT categoria FROM movimenti_cassa ORDER BY categoria"
                        ).fetchall()]
                    
                    cat_idx = categorie_esistenti.index(movimento_dettaglio['categoria']) if movimento_dettaglio['categoria'] in categorie_esistenti else 0
                    nuova_categoria = st.selectbox(
                        "Categoria",
                        categorie_esistenti,
                        index=cat_idx
                    )
                    
                    # Metodo pagamento
                    metodi = ["CONTANTI", "POS", "BONIFICO", "ASSEGNO", "ALTRO"]
                    metodo_attuale = movimento_dettaglio.get('metodo', 'CONTANTI')
                    metodo_idx = metodi.index(metodo_attuale) if metodo_attuale in metodi else 0
                    nuovo_metodo = st.selectbox(
                        "Metodo pagamento",
                        metodi,
                        index=metodo_idx
                    )
                    
                    # Note
                    nuove_note = st.text_area(
                        "Note",
                        value=movimento_dettaglio.get('note', ''),
                        height=100
                    )
                
                # Bottoni form
                form_col1, form_col2 = st.columns(2)
                with form_col1:
                    salva_btn = st.form_submit_button("💾 Salva Modifiche", use_container_width=True, type="primary")
                with form_col2:
                    annulla_btn = st.form_submit_button("❌ Annulla", use_container_width=True)
                
                if salva_btn:
                    # Esegui UPDATE
                    with db._connect() as conn:
                        conn.execute("""
                            UPDATE movimenti_cassa
                            SET data_effettiva = ?,
                                tipo = ?,
                                importo = ?,
                                categoria = ?,
                                metodo = ?,
                                note = ?
                            WHERE id = ?
                        """, (
                            nuovo_data,
                            nuovo_tipo,
                            nuovo_importo,
                            nuova_categoria,
                            nuovo_metodo,
                            nuove_note,
                            movimento_dettaglio['id']
                        ))
                        conn.commit()
                    
                    st.success(f"✅ Movimento #{movimento_dettaglio['id']} modificato con successo!")
                    st.session_state.editing_movimento_id = None
                    st.rerun()
                
                if annulla_btn:
                    st.session_state.editing_movimento_id = None
                    st.rerun()
        
        # ═══ MODALITÀ DELETE ═══
        elif st.session_state.deleting_movimento_id == movimento_dettaglio['id']:
            st.markdown("---")
            st.error("### ⚠️ Conferma Eliminazione")
            st.warning(f"""
            Stai per eliminare **definitivamente** il movimento:
            - **ID:** #{movimento_dettaglio['id']}
            - **Data:** {movimento_dettaglio['data_effettiva']}
            - **Tipo:** {movimento_dettaglio['tipo']}
            - **Importo:** {format_currency(movimento_dettaglio['importo'])}
            - **Categoria:** {movimento_dettaglio['categoria']}
            
            ⚠️ **Questa azione NON può essere annullata!**
            """)
            
            conferma_eliminazione = st.checkbox(
                "✓ Sono sicuro di voler eliminare questo movimento",
                key=f"confirm_delete_{movimento_dettaglio['id']}"
            )
            
            del_col1, del_col2 = st.columns(2)
            with del_col1:
                if st.button(
                    "🗑️ Elimina Definitivamente",
                    use_container_width=True,
                    type="primary",
                    disabled=not conferma_eliminazione
                ):
                    # Esegui DELETE
                    with db._connect() as conn:
                        conn.execute(
                            "DELETE FROM movimenti_cassa WHERE id = ?",
                            (movimento_dettaglio['id'],)
                        )
                        conn.commit()
                    
                    st.success(f"✅ Movimento #{movimento_dettaglio['id']} eliminato correttamente!")
                    st.session_state.deleting_movimento_id = None
                    st.balloons()
                    st.rerun()
            
            with del_col2:
                if st.button("❌ Annulla", use_container_width=True):
                    st.session_state.deleting_movimento_id = None
                    st.rerun()
        
        # ═══ MODALITÀ VISUALIZZAZIONE (DEFAULT) ═══
        else:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✏️ Modifica", use_container_width=True, key=f"edit_btn_{movimento_dettaglio['id']}"):
                    st.session_state.editing_movimento_id = movimento_dettaglio['id']
                    st.session_state.deleting_movimento_id = None
                    st.rerun()
            with col_btn2:
                if st.button("🗑️ Elimina", use_container_width=True, type="secondary", key=f"delete_btn_{movimento_dettaglio['id']}"):
                    st.session_state.deleting_movimento_id = movimento_dettaglio['id']
                    st.session_state.editing_movimento_id = None
                    st.rerun()

else:
    # Empty state quando nessun risultato
    st.markdown(
        empty_state_component(
            "Nessun movimento trovato",
            "Prova a modificare i filtri o ampliare il periodo di ricerca",
            "📭"
        ),
        unsafe_allow_html=True
    )

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════

st.divider()
st.caption("💡 Dashboard ottimizzato per P.IVA forfettaria · Aggiornamento: " + oggi.strftime('%d/%m/%Y'))
