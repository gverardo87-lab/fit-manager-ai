# file: server/pages/02_Clienti.py
import streamlit as st
import pandas as pd
import json
from datetime import date, datetime, timedelta
from core.crm_db import CrmDBManager

db = CrmDBManager()

st.set_page_config(page_title="Gestione Clienti", page_icon="👥", layout="wide")

st.title("👥 Gestione Clienti & Contratti")

# --- 1. SELETTORE / LISTA ---
col_search, col_add = st.columns([3, 1])

# Carica lista clienti
df_cli = db.get_clienti_df()
search_opts = {row['id']: f"{row['cognome']} {row['nome']}" for _, row in df_cli.iterrows()} if not df_cli.empty else {}

cliente_sel_id = None

with col_search:
    if not df_cli.empty:
        cliente_sel_id = st.selectbox("🔍 Cerca Cliente", options=[None] + list(search_opts.keys()), format_func=lambda x: search_opts.get(x, "Seleziona..."))

with col_add:
    st.write("") # Spacer
    if st.button("➕ Nuovo Cliente", type="primary", use_container_width=True):
        st.session_state['new_client_mode'] = True
        cliente_sel_id = None

# --- 2. LOGICA VISUALIZZAZIONE ---
if st.session_state.get('new_client_mode'):
    st.divider()
    st.subheader("Nuova Anagrafica")
    with st.form("new_client"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome")
        cognome = c2.text_input("Cognome")
        tel = c1.text_input("Telefono")
        email = c2.text_input("Email")
        
        if st.form_submit_button("Salva Anagrafica"):
            if nome and cognome:
                db.save_cliente({
                    "nome": nome, "cognome": cognome, "telefono": tel, "email": email,
                    "nascita": date(1990,1,1), "sesso": "Uomo", "stato": "Attivo", "anamnesi": {}
                })
                st.success("Cliente creato! Selezionalo dalla lista per i dettagli.")
                st.session_state['new_client_mode'] = False
                st.rerun()
            else:
                st.error("Nome e Cognome obbligatori")
    
    if st.button("Annulla"):
        st.session_state['new_client_mode'] = False
        st.rerun()

elif cliente_sel_id:
    # --- 3. SCHEDA DETTAGLIO CLIENTE ---
    cli_data = db.get_cliente_full(cliente_sel_id)
    
    # Header con KPI rapidi
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Saldo Contabile", f"€ {cli_data['saldo']:.2f}", delta_color="inverse")
    kpi2.metric("Lezioni Residue", cli_data['lezioni_residue'])
    kpi3.info(f"Stato: {cli_data['stato']}")
    
    # Tabs
    tab_ana, tab_amm, tab_storico = st.tabs(["👤 Anagrafica & Salute", "💳 Contratti & Pagamenti", "📅 Storico Lezioni"])
    
    # --- TAB 1: ANAGRAFICA & SALUTE ---
    with tab_ana:
        with st.form("edit_ana"):
            ac1, ac2 = st.columns(2)
            new_nome = ac1.text_input("Nome", cli_data['nome'])
            new_cogn = ac2.text_input("Cognome", cli_data['cognome'])
            new_tel = ac1.text_input("Telefono", cli_data['telefono'])
            new_mail = ac2.text_input("Email", cli_data['email'])
            
            # Anamnesi JSON Parsing
            anamnesi = {}
            if cli_data['anamnesi_json']:
                try: anamnesi = json.loads(cli_data['anamnesi_json'])
                except: pass
            
            st.markdown("##### 🧬 Profilo Tecnico")
            tc1, tc2 = st.columns(2)
            prof = tc1.text_input("Professione", value=anamnesi.get('professione', ''))
            sport = tc2.text_input("Sport Precedenti", value=anamnesi.get('sport', ''))
            note_med = st.text_area("Note Mediche / Infortuni", value=anamnesi.get('infortuni', ''))
            
            if st.form_submit_button("💾 Aggiorna Dati"):
                # Salva
                payload = {
                    "nome": new_nome, "cognome": new_cogn, "telefono": new_tel, "email": new_mail,
                    "nascita": cli_data['data_nascita'], "sesso": cli_data['sesso'], "stato": cli_data['stato'],
                    "anamnesi": {"professione": prof, "sport": sport, "infortuni": note_med}
                }
                db.save_cliente(payload, cliente_sel_id)
                st.success("Dati aggiornati!")
                st.rerun()

    # --- TAB 2: AMMINISTRAZIONE ---
    with tab_amm:
        c_sx, c_dx = st.columns([2, 1])
        
        with c_sx:
            st.subheader("Contratti")
            if not cli_data['contratti']:
                st.warning("Nessun contratto registrato.")
            else:
                for c in cli_data['contratti']:
                    icon = "🟢" if not c['chiuso'] else "🔴"
                    with st.expander(f"{icon} {c['tipo_pacchetto']} ({c['data_inizio']})"):
                        st.write(f"Prezzo: €{c['prezzo_pattuito']} | Crediti: {c['crediti_totali']}")
                        st.write(f"Note: {c['note']}")
            
            st.subheader("Storico Pagamenti")
            if cli_data['pagamenti']:
                df_pay = pd.DataFrame(cli_data['pagamenti'])
                st.dataframe(df_pay[['data', 'importo', 'metodo', 'note']], use_container_width=True)
        
        with c_dx:
            st.markdown("### ⚡ Operazioni")
            
            with st.expander("📝 Vendi Nuovo Pacchetto", expanded=True):
                with st.form("new_contract"):
                    pacc = st.selectbox("Pacchetto", ["10 PT", "20 PT", "Mensile", "Trimestrale", "Consulenza"])
                    prezzo = st.number_input("Prezzo (€)", value=350.0, step=10.0)
                    ingr = st.number_input("Crediti", value=10)
                    start = st.date_input("Inizio", date.today())
                    note_c = st.text_input("Note")
                    
                    if st.form_submit_button("Vendi Pacchetto"):
                        db.add_contratto(cliente_sel_id, pacc, prezzo, ingr, start, None, note_c)
                        st.success("Contratto Attivato!")
                        st.rerun()
            
            with st.expander("💰 Registra Incasso"):
                with st.form("new_pay"):
                    imp = st.number_input("Importo (€)", value=50.0)
                    met = st.selectbox("Metodo", ["Contanti", "Bonifico", "POS"])
                    
                    if st.form_submit_button("Registra Pagamento"):
                        db.add_pagamento(cliente_sel_id, imp, met, "Pagamento Manuale")
                        st.success("Incasso registrato!")
                        st.rerun()

    # --- TAB 3: STORICO ---
    with tab_storico:
        # Qui potremo vedere le lezioni fatte
        st.info("🚧 Qui apparirà la lista delle lezioni completate dall'agenda.")

else:
    st.info("👈 Seleziona un cliente o creane uno nuovo.")