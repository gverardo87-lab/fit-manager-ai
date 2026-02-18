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

from core.repositories import ClientRepository, ContractRepository, FinancialRepository
from core.models import MovimentoCassaCreate, SpesaRicorrenteCreate
from core.ui_components import badge, status_badge, format_currency, loading_message, section_divider_component, empty_state_component, load_custom_css

# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Cassa & Bilancio",
    page_icon=":material/account_balance_wallet:",
    layout="wide"
)

load_custom_css()

client_repo = ClientRepository()
contract_repo = ContractRepository()
financial_repo = FinancialRepository()

# ════════════════════════════════════════════════════════════
# DATI BASE
# ════════════════════════════════════════════════════════════

oggi = date.today()
primo_mese = date(oggi.year, oggi.month, 1)
ultimo_giorno = monthrange(oggi.year, oggi.month)[1]
ultimo_mese = date(oggi.year, oggi.month, ultimo_giorno)

# Calcola metriche
bilancio = financial_repo.get_cash_balance(primo_mese, ultimo_mese)
saldo_totale = financial_repo.get_cash_balance()['saldo_cassa']
previsione = financial_repo.get_cash_forecast(30)
rate_pendenti = contract_repo.get_pending_rates(oggi + timedelta(days=30), solo_future=True)
rate_scadute = contract_repo.get_overdue_rates()
spese_fisse_raw = financial_repo.get_recurring_expenses()
# Convert Pydantic models to dicts for compatibility
spese_fisse = [{'id': s.id, 'nome': s.nome, 'importo': s.importo, 'categoria': s.categoria, 'giorno_scadenza': s.giorno_scadenza, 'frequenza': s.frequenza, 'attiva': s.attiva} for s in spese_fisse_raw]
spese_fisse_non_pagate = financial_repo.get_unpaid_fixed_expenses()

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
    # Priorità 1: Spese fisse non pagate o pagate con importo sbagliato
    if spese_fisse_non_pagate:
        # Distingui tra non pagate e pagate con importo sbagliato
        non_pagate = [s for s in spese_fisse_non_pagate if s.get('movimento_id') is None]
        pagate_male = [s for s in spese_fisse_non_pagate if s.get('movimento_id') is not None]
        
        totale_non_pagato = sum(s['importo'] for s in non_pagate)
        totale_discrepanza = sum(abs(s['importo'] - s.get('importo_pagato', 0)) for s in pagate_male)
        
        # Messaggio principale
        if pagate_male:
            st.error(f"⚠️ **{len(non_pagate)} spese NON pagate + {len(pagate_male)} con importo ERRATO** → €{totale_non_pagato + totale_discrepanza:.0f}")
        else:
            st.warning(f"⚠️ **{len(spese_fisse_non_pagate)} spese fisse non pagate** → €{totale_non_pagato:.0f}")
        
        # Dettaglio nomi
        nomi_problemi = []
        for s in spese_fisse_non_pagate[:2]:
            if s.get('movimento_id') is None:
                nomi_problemi.append(f"{s['nome']} (€{s['importo']:.0f} NON pagato)")
            else:
                nomi_problemi.append(f"{s['nome']} (€{s['importo']:.0f} previsto vs €{s.get('importo_pagato', 0):.0f} pagato)")
        
        nomi_spese = ", ".join(nomi_problemi)
        if len(spese_fisse_non_pagate) > 2:
            nomi_spese += f" +{len(spese_fisse_non_pagate)-2} altri"
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
        # Entrate per categoria
        entrate_mese = financial_repo.get_cash_breakdown_by_category(primo_mese, ultimo_mese, "ENTRATA")
        
        if entrate_mese:
            st.markdown("**💵 Entrate:**")
            for item in entrate_mese:
                st.caption(f"{item['categoria']}: €{item['totale']:.0f}")
        
        st.divider()
        
        # Uscite per categoria
        uscite_mese = financial_repo.get_cash_breakdown_by_category(primo_mese, ultimo_mese, "USCITA")
        
        if uscite_mese:
            st.markdown("**💸 Uscite:**")
            for item in uscite_mese:
                st.caption(f"{item['categoria']}: €{item['totale']:.0f}")
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
                    contract_repo.pay_rate(
                        rate_id=rata['id'],
                        amount_paid=importo_da_pagare,
                        payment_method="CONTANTI",
                        payment_date=oggi,
                        notes="Pagamento sollecitato"
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
                    contract_repo.pay_rate(
                        rate_id=rata['id'],
                        amount_paid=importo_da_pagare,
                        payment_method="CONTANTI",
                        payment_date=oggi,
                        notes="Pagamento anticipato"
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
                    movimento = MovimentoCassaCreate(
                        data_effettiva=data_spesa,
                        tipo="USCITA",
                        categoria=categoria_finale,
                        importo=importo_spesa,
                        metodo="BONIFICO",
                        id_spesa_ricorrente=id_spesa_ricorrente,
                        note=note_spesa
                    )
                    financial_repo.register_cash_movement(movimento)
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
            clienti_attivi_raw = client_repo.get_all_active()
            clienti_attivi = [{'id': c.id, 'nome': c.nome, 'cognome': c.cognome} for c in clienti_attivi_raw]
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
                
                movimento = MovimentoCassaCreate(
                    data_effettiva=data_entrata,
                    tipo="ENTRATA",
                    categoria=categoria_entrata,
                    importo=importo_entrata,
                    metodo="CONTANTI",
                    id_cliente=id_cliente_entrata,
                    note=note_entrata
                )
                financial_repo.register_cash_movement(movimento)
                st.success(f"✅ Entrata €{importo_entrata:.0f} registrata! Controlla lo storico movimenti sotto.")
                st.balloons()
                st.rerun()

st.divider()

# Seconda sezione: Spese Fisse (full width)
with st.expander("📊 Spese Fisse Mensili", expanded=False):
    # Quick Actions per spese non pagate
    if spese_fisse_non_pagate:
        # Distingui tra completamente non pagate e pagate male
        non_pagate = [s for s in spese_fisse_non_pagate if s.get('movimento_id') is None]
        pagate_male = [s for s in spese_fisse_non_pagate if s.get('movimento_id') is not None]
        
        if non_pagate:
            st.warning(f"⚠️ **{len(non_pagate)} spese non pagate questo mese**")
            
            cols_quick = st.columns(min(len(non_pagate), 3))
            for idx, (col, spesa) in enumerate(zip(cols_quick, non_pagate[:3])):
                with col:
                    st.markdown(f"**{spesa['nome']}**")
                    st.caption(f"Scadenza: {spesa['giorno_scadenza']} {oggi.strftime('%B')}")
                    st.caption(f"💶 {format_currency(spesa['importo'], 0)}")
                    
                    if st.button(f"💳 Paga Ora", key=f"quick_paga_{spesa['id']}", use_container_width=True, type="primary"):
                        try:
                            movimento = MovimentoCassaCreate(
                                data_effettiva=oggi,
                                tipo="USCITA",
                                categoria=spesa['categoria'],
                                importo=spesa['importo'],
                                metodo="BONIFICO",
                                id_spesa_ricorrente=spesa['id'],
                                note=f"Pagamento {spesa['nome']} - {oggi.strftime('%B %Y')}"
                            )
                            financial_repo.register_cash_movement(movimento)
                            st.success(f"✅ {spesa['nome']} pagata!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore: {str(e)}")
            
            if len(non_pagate) > 3:
                st.info(f"➕ {len(non_pagate)-3} altre spese da pagare (vedi dropdown sopra)")
        
        # Avviso per spese pagate con importo sbagliato
        if pagate_male:
            st.error(f"⚠️ **{len(pagate_male)} spese pagate con IMPORTO ERRATO**")
            st.info("📝 **Azione richiesta:** Vai a 'Storico Movimenti' sotto per correggere gli importi usando il bottone ✏️ Modifica")
            
            for spesa in pagate_male[:3]:
                st.caption(f"• {spesa['nome']}: previsto {format_currency(spesa['importo'], 0)}, pagato {format_currency(spesa.get('importo_pagato', 0), 0)}")
            
            if len(pagate_male) > 3:
                st.caption(f"➕ {len(pagate_male)-3} altri errori da correggere")
        
        st.divider()
    
    # Tabella completa spese fisse
    if spese_fisse:
        st.markdown("**📋 Tutte le Spese Fisse Configurate**")
        totale_fisso = sum(s['importo'] for s in spese_fisse)
        
        col_sf_left, col_sf_right = st.columns([2, 1])
        
        with col_sf_left:
            # Tabella spese fisse con status dettagliato
            dati_fisse = []
            
            # Crea dizionari per lookup veloce
            non_pagate_dict = {s['id']: s for s in spese_fisse_non_pagate if s.get('movimento_id') is None}
            pagate_male_dict = {s['id']: s for s in spese_fisse_non_pagate if s.get('movimento_id') is not None}
            
            for s in spese_fisse:
                # Determina status preciso
                if s['id'] in pagate_male_dict:
                    pm = pagate_male_dict[s['id']]
                    status = f"⚠️ Importo errato ({format_currency(pm.get('importo_pagato', 0), 0)} vs {format_currency(s['importo'], 0)})"
                elif s['id'] in non_pagate_dict:
                    if s['giorno_scadenza'] > oggi.day:
                        status = "⏳ Futura"
                    else:
                        status = "❌ Non Pagata"
                else:
                    status = "✅ Pagata"
                
                dati_fisse.append({
                    'Nome': s['nome'],
                    'Categoria': s['categoria'],
                    'Importo': format_currency(s['importo'], 0),
                    'Scadenza': f"{s['giorno_scadenza']}° del mese",
                    'Status': status
                })
            
            df_fisse = pd.DataFrame(dati_fisse)
            st.dataframe(df_fisse, use_container_width=True, hide_index=True)
        
        with col_sf_right:
            st.metric("Totale Mensile", format_currency(totale_fisso, 0))
            
            # Breakdown preciso: pagate correttamente / pagate male / non pagate
            spese_pagate_male = [s for s in spese_fisse_non_pagate if s.get('movimento_id') is not None]
            spese_non_pagate = [s for s in spese_fisse_non_pagate if s.get('movimento_id') is None]
            spese_pagate_ok = [s for s in spese_fisse if s['id'] not in [sp['id'] for sp in spese_fisse_non_pagate]]
            
            totale_pagato_ok = sum(s['importo'] for s in spese_pagate_ok)
            totale_non_pagato = sum(s['importo'] for s in spese_non_pagate)
            totale_pagato_male = sum(s['importo'] for s in spese_pagate_male)
            
            st.caption(f"✅ Pagate correttamente: {format_currency(totale_pagato_ok, 0)}")
            if totale_pagato_male > 0:
                st.caption(f"⚠️ Pagate con errore: {format_currency(totale_pagato_male, 0)}")
            st.caption(f"❌ Da pagare: {format_currency(totale_non_pagato, 0)}")
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
                    new_expense = SpesaRicorrenteCreate(
                        nome=nome_sf,
                        categoria=categoria_sf,
                        importo=importo_sf,
                        frequenza="MENSILE",
                        giorno_scadenza=giorno_sf
                    )
                    financial_repo.add_recurring_expense(new_expense)
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
    bil_mese = financial_repo.get_cash_balance(primo, ultimo)
    
    # SALDO TOTALE ALLA FINE DEL MESE (tutto dall'inizio dei tempi fino a ultimo giorno del mese)
    saldo_cumulativo = financial_repo.get_cash_balance(end_date=ultimo)
    
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
    clienti_attivi_raw = client_repo.get_all_active()
    clienti_attivi = [{'id': c.id, 'nome': c.nome, 'cognome': c.cognome} for c in clienti_attivi_raw]
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
    categorie_esistenti = financial_repo.get_movement_categories()
    
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

# ═══ RECUPERO MOVIMENTI FILTRATI ═══
_tipo_filtro = None
if filtro_tipo == "💵 Solo Entrate":
    _tipo_filtro = "ENTRATA"
elif filtro_tipo == "💸 Solo Uscite":
    _tipo_filtro = "USCITA"

_cliente_id_filtro = None
if filtro_cliente != "Tutti i clienti":
    idx_cliente = opzioni_clienti.index(filtro_cliente) - 1
    _cliente_id_filtro = clienti_attivi[idx_cliente]['id']

_categoria_filtro = filtro_categoria if filtro_categoria != "Tutte le categorie" else None

_sort_map = {
    "Più recenti": "recent",
    "Meno recenti": "oldest",
    "Importo ↑": "amount_asc",
    "Importo ↓": "amount_desc",
}

movimenti = financial_repo.get_cash_movements_filtered(
    date_from=data_da if data_da else None,
    date_to=data_a if data_a else None,
    tipo=_tipo_filtro,
    cliente_id=_cliente_id_filtro,
    categoria=_categoria_filtro,
    search_text=ricerca_testo if ricerca_testo else None,
    sort_by=_sort_map.get(ordinamento, "recent"),
    limit=limite_mov,
)

# ═══ VISUALIZZAZIONE RISULTATI ═══
if movimenti:
    from datetime import datetime
    
    dati_mov = []
    for idx, m in enumerate(movimenti):
        # Cliente info
        cliente_info = "-"
        if m.get('id_cliente'):
            cliente_obj = client_repo.get_by_id(m['id_cliente'])
            if cliente_obj:
                cliente_info = f"{cliente_obj.nome} {cliente_obj.cognome}"
        
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
            cliente_obj = client_repo.get_by_id(movimento_dettaglio['id_cliente'])
            if cliente_obj:
                cliente_nome = f"{cliente_obj.nome} {cliente_obj.cognome}"
        
        # Box dettagli con stile
        tipo_icon = "💵" if movimento_dettaglio['tipo'] == 'ENTRATA' else "💸"
        tipo_color = "green" if movimento_dettaglio['tipo'] == 'ENTRATA' else "red"
        
        st.markdown(f"""
        <div style="background: var(--bg-elevated); padding: 20px; border-radius: 10px; border-left: 5px solid {tipo_color};">
            <h4 style="margin-top: 0; color: var(--text-primary);">{tipo_icon} Dettagli Movimento #{movimento_dettaglio['id']}</h4>
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
                    categorie_esistenti = financial_repo.get_movement_categories()
                    
                    categoria_attuale = movimento_dettaglio.get('categoria', '')
                    cat_idx = categorie_esistenti.index(categoria_attuale) if categoria_attuale in categorie_esistenti else 0
                    nuova_categoria = st.selectbox(
                        "Categoria",
                        categorie_esistenti,
                        index=cat_idx
                    )
                    
                    # Metodo pagamento
                    metodi = ["CONTANTI", "POS", "BONIFICO", "ASSEGNO", "ALTRO"]
                    metodo_attuale = (movimento_dettaglio.get('metodo') or 'CONTANTI').upper()
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
                    success = financial_repo.update_cash_movement(
                        movimento_id=movimento_dettaglio['id'],
                        data_effettiva=nuovo_data,
                        tipo=nuovo_tipo,
                        importo=nuovo_importo,
                        categoria=nuova_categoria,
                        metodo=nuovo_metodo,
                        note=nuove_note
                    )
                    if success:
                        st.success(f"✅ Movimento #{movimento_dettaglio['id']} modificato con successo!")
                    else:
                        st.error("❌ Errore durante la modifica del movimento.")
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
                    success = financial_repo.delete_cash_movement(movimento_dettaglio['id'])
                    if success:
                        st.success(f"✅ Movimento #{movimento_dettaglio['id']} eliminato correttamente!")
                    else:
                        st.error("❌ Errore durante l'eliminazione del movimento.")
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
