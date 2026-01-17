# file: server/pages/02_Clienti.py
import streamlit as st
import pandas as pd
import json
from datetime import date, datetime, timedelta
from core.crm_db import CrmDBManager

db = CrmDBManager()

st.set_page_config(page_title="Gestione Clienti", page_icon="👥", layout="wide")

st.title("👥 Gestione Clienti & Contratti Pro")

# --- 1. SELETTORE / LISTA ---
col_search, col_add = st.columns([3, 1])

# Carichiamo la lista base
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
    st.subheader("📝 Nuova Anagrafica Rapida")
    with st.form("new_client"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome*")
        cognome = c2.text_input("Cognome*")
        tel = c1.text_input("Telefono")
        email = c2.text_input("Email")
        
        if st.form_submit_button("Salva e Vai ai Dettagli"):
            if nome and cognome:
                # Creazione con dati minimi, poi si arricchisce nella scheda
                db.save_cliente({
                    "nome": nome, "cognome": cognome, "telefono": tel, "email": email,
                    "nascita": date(1990,1,1), "sesso": "Uomo", "stato": "Attivo", "anamnesi": {}
                })
                st.success("Cliente creato! Selezionalo dalla lista per completare la scheda.")
                st.session_state['new_client_mode'] = False
                st.rerun()
            else:
                st.error("Nome e Cognome obbligatori")
    
    if st.button("Annulla creazione"):
        st.session_state['new_client_mode'] = False
        st.rerun()

elif cliente_sel_id:
    # --- 3. SCHEDA DETTAGLIO CLIENTE ---
    # Recuperiamo TUTTI i dati (Anagrafica + Finanza)
    # Assicurati che core/crm_db.py abbia il metodo 'get_cliente_financial_history' aggiornato
    fin_data = db.get_cliente_financial_history(cliente_sel_id)
    # Recuperiamo anche i dati anagrafici grezzi
    cli_data = db.get_cliente_full(cliente_sel_id)
    
    if not cli_data:
        st.error("Errore caricamento dati cliente.")
        st.stop()

    # HEADER KPI
    k1, k2, k3 = st.columns(3)
    saldo = fin_data['saldo_globale']
    k1.metric("Saldo da Pagare", f"€ {saldo:.2f}", delta="-Da Saldare" if saldo > 0 else "In Regola", delta_color="inverse")
    k2.metric("Lezioni Residue", cli_data.get('lezioni_residue', 0))
    k3.info(f"Stato: **{cli_data['stato']}**")
    
    st.divider()
    
    # TABS COMPLETE
    tab_ana, tab_amm, tab_storico = st.tabs(["👤 Anagrafica & Salute", "💳 Amministrazione", "📅 Storico Lezioni"])
    
    # --- TAB 1: ANAGRAFICA & SALUTE (RIPRISTINATA) ---
    with tab_ana:
        with st.form("edit_ana"):
            st.subheader("✏️ Modifica Dati Personali")
            ac1, ac2 = st.columns(2)
            
            new_nome = ac1.text_input("Nome", cli_data['nome'])
            new_cogn = ac2.text_input("Cognome", cli_data['cognome'])
            new_tel = ac1.text_input("Telefono", cli_data['telefono'])
            new_mail = ac2.text_input("Email", cli_data['email'])
            
            # Gestione data di nascita (conversione sicura)
            try: d_nascita = pd.to_datetime(cli_data['data_nascita']).date()
            except: d_nascita = date(1990, 1, 1)
            new_nascita = ac1.date_input("Data di Nascita", value=d_nascita)
            
            new_sesso = ac2.radio("Sesso", ["Uomo", "Donna"], index=0 if cli_data['sesso'] == 'Uomo' else 1, horizontal=True)

            st.markdown("---")
            st.subheader("🧬 Profilo Clinico")
            
            # JSON Parsing Anamnesi
            anamnesi = {}
            if cli_data['anamnesi_json']:
                try: anamnesi = json.loads(cli_data['anamnesi_json'])
                except: pass
            
            tc1, tc2 = st.columns(2)
            prof = tc1.text_input("Professione", value=anamnesi.get('professione', ''))
            sport = tc2.text_input("Sport Precedenti", value=anamnesi.get('sport', ''))
            
            idx_fumo = 0
            if anamnesi.get('fumo') == "Occasionale": idx_fumo = 1
            elif anamnesi.get('fumo') == "Abituale": idx_fumo = 2
            fumo = tc1.selectbox("Fumatore", ["No", "Occasionale", "Abituale"], index=idx_fumo)
            
            note_med = st.text_area("Note Mediche / Infortuni", value=anamnesi.get('infortuni', ''))
            
            # Tasto Aggiorna
            if st.form_submit_button("💾 Aggiorna Anagrafica"):
                payload = {
                    "nome": new_nome, "cognome": new_cogn, "telefono": new_tel, "email": new_mail,
                    "nascita": new_nascita, "sesso": new_sesso, "stato": cli_data['stato'],
                    "anamnesi": {
                        "professione": prof, "sport": sport, "fumo": fumo, "infortuni": note_med
                    }
                }
                db.save_cliente(payload, cliente_sel_id)
                st.toast("Dati anagrafici salvati!", icon="✅")
                st.rerun()

    # --- TAB 2: AMMINISTRAZIONE (NUOVA LOGICA) ---
    with tab_amm:
        c_sx, c_dx = st.columns([2, 1])
        
        with c_sx:
            st.subheader("📜 Contratti Attivi & Storico")
            if not fin_data['contratti']:
                st.caption("Nessun contratto registrato.")
            else:
                for c in fin_data['contratti']:
                    # Logica colori stato
                    color_st = "green" if c['stato_pagamento'] == 'SALDATO' else "orange" if c['stato_pagamento'] == 'PARZIALE' else "red"
                    icon_cls = "🔒" if c['chiuso'] else "🔓"
                    
                    with st.container(border=True):
                        col_a, col_b = st.columns([3, 1])
                        col_a.markdown(f"**{c['tipo_pacchetto']}** (dal {c['data_inizio']}) {icon_cls}")
                        col_a.caption(f"Prezzo: €{c['prezzo_totale']} | Versato: €{c['totale_versato']} | Crediti: {c['crediti_usati']}/{c['crediti_totali']}")
                        col_b.markdown(f":{color_st}[**{c['stato_pagamento']}**]")
                        
                        # Se c'è un debito, mostra form per pagare
                        da_pagare = c['prezzo_totale'] - c['totale_versato']
                        if da_pagare > 0.01:
                            with st.expander(f"💸 Registra Rata (€ {da_pagare:.2f})"):
                                with st.form(f"pay_form_{c['id']}"):
                                    col_p1, col_p2 = st.columns(2)
                                    imp_rata = col_p1.number_input("Importo Rata (€)", value=float(da_pagare), max_value=float(da_pagare), step=10.0, key=f"ir_{c['id']}")
                                    met_rata = col_p2.selectbox("Metodo", ["CONTANTI", "POS", "BONIFICO"], key=f"mr_{c['id']}")
                                    
                                    # --- NUOVO CAMPO DATA ---
                                    data_rata = st.date_input("Data Pagamento", value=date.today(), key=f"dr_{c['id']}")
                                    note_rata = st.text_input("Note opzionali", key=f"nr_{c['id']}")
                                    
                                    if st.form_submit_button("Registra Incasso"):
                                        # Passiamo la data selezionata al DB
                                        db.registra_rata(c['id'], imp_rata, met_rata, data_rata, note_rata)
                                        st.success(f"Pagamento di €{imp_rata} registrato al {data_rata}!")
                                        st.rerun()

            st.divider()
            st.subheader("🧾 Storico Movimenti Cassa")
            if fin_data['movimenti']:
                st.dataframe(
                    pd.DataFrame(fin_data['movimenti'])[['data_movimento', 'categoria', 'importo', 'metodo', 'note']], 
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.caption("Nessun movimento.")

        with c_dx:
            st.markdown("### ⚡ Nuova Vendita")
            with st.container(border=True):
                with st.form("new_sale_form"):
                    st.write("**Vendi Pacchetto / Abbonamento**")
                    tipo = st.selectbox("Tipologia", ["10 PT", "20 PT", "Mensile Sala", "Trimestrale Sala", "Annuale Sala", "Consulenza Singola"])
                    
                    # Prezzi default intelligenti
                    prezzo_def = 350.0 if "10 PT" in tipo else 50.0
                    crediti_def = 10 if "10 PT" in tipo else 0
                    
                    prezzo = st.number_input("Prezzo Pattuito (€)", value=prezzo_def, step=10.0)
                    crediti = st.number_input("Crediti Inclusi", value=crediti_def)
                    
                    start_d = st.date_input("Data Inizio", date.today())
                    end_d = st.date_input("Scadenza", date.today() + timedelta(days=365))
                    
                    st.divider()
                    st.write("**Acconto Iniziale**")
                    acconto = st.number_input("Versato Oggi (€)", value=0.0, step=10.0)
                    metodo_acc = st.selectbox("Metodo Acconto", ["CONTANTI", "POS", "BONIFICO"])
                    
                    if st.form_submit_button("Conferma Vendita", type="primary"):
                        db.crea_contratto_vendita(
                            cliente_sel_id, tipo, prezzo, crediti, 
                            start_d, end_d, acconto, metodo_acc
                        )
                        st.success("Vendita registrata correttamente!")
                        st.balloons()
                        st.rerun()

    # --- TAB 3: STORICO LEZIONI (ORA ATTIVO) ---
    with tab_storico:
        st.subheader("📅 Registro Allenamenti")
        
        # Recupera storico dal DB
        storico = db.get_storico_lezioni_cliente(cliente_sel_id)
        
        if not storico:
            st.info("Nessuna lezione registrata in agenda.")
        else:
            # Creiamo una tabella leggibile
            data_list = []
            for ev in storico:
                # Icona stato
                stato_icon = "✅" if ev['stato'] == 'Fatto' else "📅"
                # Pacchetto di origine
                pack_name = ev['tipo_pacchetto'] if ev['tipo_pacchetto'] else "-(Extra)-"
                
                data_list.append({
                    "Data": pd.to_datetime(ev['data_inizio']).strftime("%d/%m/%Y %H:%M"),
                    "Attività": ev['titolo'],
                    "Categoria": ev['categoria'],
                    "Pacchetto Usato": pack_name,
                    "Stato": f"{stato_icon} {ev['stato']}",
                    "Note": ev['note']
                })
            
            st.dataframe(
                pd.DataFrame(data_list), 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Note": st.column_config.TextColumn("Note", width="medium")
                }
            )