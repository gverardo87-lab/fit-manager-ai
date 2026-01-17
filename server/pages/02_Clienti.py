# file: server/pages/02_Clienti.py (Versione FitManager 4.1 - Fix Layout & Nesting)
import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import date, datetime, timedelta
from core.crm_db import CrmDBManager

db = CrmDBManager()

st.set_page_config(page_title="Gestione Clienti", page_icon="👥", layout="wide")

# --- CSS CUSTOM PER UI ---
st.markdown("""
<style>
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #ddd; }
    div[data-testid="stExpander"] { border: none; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    /* Fix per header stretti */
    [data-testid="column"] { min-width: 100px; } 
</style>
""", unsafe_allow_html=True)

# --- DIALOGHI MODALI ---
@st.experimental_dialog("Registra Pagamento")
def dialog_pagamento(id_contratto, importo_residuo):
    st.info(f"Saldo residuo su questo pacchetto: **€ {importo_residuo:.2f}**")
    with st.form("form_rata"):
        imp = st.number_input("Importo Rata (€)", value=float(importo_residuo), max_value=float(importo_residuo), step=10.0)
        met = st.selectbox("Metodo", ["CONTANTI", "POS", "BONIFICO"])
        dt_pay = st.date_input("Data Pagamento", value=date.today())
        note = st.text_input("Note opzionali")
        
        if st.form_submit_button("💰 Registra Incasso"):
            db.registra_rata(id_contratto, imp, met, dt_pay, note)
            st.success("Pagamento registrato!")
            st.rerun()

@st.experimental_dialog("Nuova Vendita Pacchetto")
def dialog_vendita(id_cliente):
    st.write("Configura il nuovo contratto per il cliente.")
    with st.form("form_vendita"):
        tipo = st.selectbox("Tipologia", ["10 PT", "20 PT", "Mensile Sala", "Trimestrale", "Annuale", "Consulenza"])
        
        # Prezzi smart
        p_def = 350.0 if "10 PT" in tipo else 600.0 if "20 PT" in tipo else 50.0
        c_def = 10 if "10 PT" in tipo else 20 if "20 PT" in tipo else 0
        
        c1, c2 = st.columns(2)
        prezzo = c1.number_input("Prezzo Pattuito (€)", value=p_def, step=10.0)
        crediti = c2.number_input("Crediti Inclusi", value=c_def)
        
        d1, d2 = st.columns(2)
        start = d1.date_input("Inizio Validità", value=date.today())
        end = d2.date_input("Scadenza", value=date.today() + timedelta(days=365))
        
        st.markdown("---")
        st.write("Acconto Iniziale")
        acconto = st.number_input("Versato Oggi (€)", value=0.0, step=10.0)
        metodo = st.selectbox("Metodo Acconto", ["CONTANTI", "POS", "BONIFICO"])
        
        if st.form_submit_button("📝 Conferma Vendita"):
            db.crea_contratto_vendita(id_cliente, tipo, prezzo, crediti, start, end, acconto, metodo)
            st.success("Contratto creato con successo!")
            st.rerun()

@st.experimental_dialog("Check-up Fisico")
def dialog_misurazione(id_cliente):
    st.write("Inserisci i dati del check-up odierno.")
    with st.form("form_misure"):
        c1, c2 = st.columns(2)
        peso = c1.number_input("Peso (kg)", 40.0, 150.0, 70.0, step=0.1)
        vita = c2.number_input("Circonferenza Vita (cm)", 50.0, 150.0, 80.0, step=0.5)
        grasso = st.slider("Massa Grassa (%)", 5.0, 50.0, 15.0, step=0.5)
        note = st.text_area("Note Check-up")
        
        if st.form_submit_button("💾 Salva Dati"):
            db.add_misurazione(id_cliente, peso, grasso, vita, note)
            st.success("Check-up salvato!")
            st.rerun()

# --- LAYOUT PRINCIPALE ---
col_list, col_detail = st.columns([1, 3]) # LIV. 1: Master / Detail

# 1. LISTA CLIENTI (Sidebar)
with col_list:
    st.subheader("👥 Clienti")
    df_cli = db.get_clienti_df()
    
    selected_id = None
    if not df_cli.empty:
        search = st.text_input("🔍 Cerca...", placeholder="Nome...")
        if search:
            mask = df_cli['cognome'].str.contains(search, case=False) | df_cli['nome'].str.contains(search, case=False)
            df_cli = df_cli[mask]
        
        # Radio button come lista
        opts = {row['id']: f"{row['cognome']} {row['nome']}" for _, row in df_cli.iterrows()}
        if opts:
            selected_id = st.radio("Seleziona:", list(opts.keys()), format_func=lambda x: opts[x], label_visibility="collapsed")
    
    st.markdown("---")
    if st.button("➕ Nuovo Cliente", use_container_width=True):
        st.session_state['new_client_mode'] = True
        selected_id = None

# 2. DETTAGLIO CLIENTE
with col_detail:
    # MODALITÀ CREAZIONE
    if st.session_state.get('new_client_mode'):
        st.header("📝 Nuova Scheda Anagrafica")
        with st.form("new_c"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nome*"); c = c2.text_input("Cognome*")
            t = c1.text_input("Telefono"); e = c2.text_input("Email")
            if st.form_submit_button("Salva Cliente", type="primary"):
                if n and c:
                    db.save_cliente({"nome": n, "cognome": c, "telefono": t, "email": e, "nascita": date(1990,1,1), "sesso": "Uomo", "stato": "Attivo", "anamnesi": {}})
                    st.session_state['new_client_mode'] = False
                    st.rerun()
                else: st.error("Nome/Cognome obbligatori")
        if st.button("Annulla"): st.session_state['new_client_mode'] = False; st.rerun()

    # MODALITÀ VISUALIZZAZIONE
    elif selected_id:
        cli = db.get_cliente_full(selected_id)
        fin = db.get_cliente_financial_history(selected_id)
        
        # --- HEADER CARD OTTIMIZZATO ---
        with st.container(border=True):
            # Layout modificato: Meno spazio all'avatar (0.5), più al nome (1.5)
            c1, c2, c3, c4 = st.columns([0.5, 1.5, 1, 1]) 
            c1.image(f"https://api.dicebear.com/9.x/initials/svg?seed={cli['cognome']}", width=60)
            c2.title(f"{cli['nome']} {cli['cognome']}")
            c2.caption(f"📞 {cli['telefono']} | 📧 {cli['email']}")
            
            c3.metric("Crediti Residui", cli.get('lezioni_residue', 0))
            
            saldo = fin['saldo_globale']
            lbl = "DA SALDARE" if saldo > 0 else "OK"
            clr = "inverse" if saldo > 0 else "normal"
            c4.metric("Saldo", f"€ {saldo:.2f}", delta=lbl, delta_color=clr)

        # --- TABBED VIEW ---
        t_prog, t_amm, t_hist, t_ana = st.tabs(["📈 Progressi", "💳 Amministrazione", "📅 Diario", "👤 Anagrafica"])

        # TAB 1: PROGRESSI
        with t_prog:
            col_act, col_chart = st.columns([1, 3])
            with col_act:
                st.info("Registra le misurazioni periodiche.")
                if st.button("➕ Nuovo Check-up", use_container_width=True):
                    dialog_misurazione(selected_id)
            with col_chart:
                df_prog = db.get_progressi_cliente(selected_id)
                if not df_prog.empty:
                    fig = px.line(df_prog, x='data_misurazione', y='peso', markers=True, title="Andamento Peso Corporeo")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Nessun dato. Inizia a monitorare i progressi!")

        # TAB 2: AMMINISTRAZIONE (FIX NESTING)
        with t_amm:
            # FIX: Abbiamo rimosso la colonna wrapper 'col_con' che causava il livello 3 di annidamento.
            # Ora abbiamo layout piatto: Toolbar in alto, Lista sotto.
            
            # Toolbar azioni
            c_tools1, c_tools2 = st.columns([3, 1])
            with c_tools1:
                st.caption("Gestione Contratti e Pagamenti")
            with c_tools2:
                if st.button("💰 Vendi Pacchetto", type="primary", use_container_width=True):
                    dialog_vendita(selected_id)
            
            st.divider()
            
            # Lista Contratti
            st.subheader("Contratti Attivi & Storico")
            if not fin['contratti']: 
                st.info("Nessun contratto attivo.")
            
            for c in fin['contratti']:
                color = "red" if c['stato_pagamento'] != 'SALDATO' else "green"
                # Card Contratto
                with st.container(border=True):
                    # Questo st.columns è ora Livello 2 (dentro Master->Detail), quindi è OK!
                    l1, l2, l3 = st.columns([3, 2, 1])
                    
                    l1.markdown(f"**{c['tipo_pacchetto']}**")
                    l1.caption(f"Data: {c['data_vendita']} | Scadenza: {c['data_scadenza']}")
                    
                    l2.markdown(f"Stato: :{color}[**{c['stato_pagamento']}**]")
                    residuo = c['prezzo_totale'] - c['totale_versato']
                    l2.caption(f"Versato: €{c['totale_versato']} / €{c['prezzo_totale']}")
                    
                    if residuo > 0.1:
                        if l3.button("Paga Rata", key=f"p_{c['id']}", use_container_width=True):
                            dialog_pagamento(c['id'], residuo)
                    else:
                        l3.success("Saldato")

            st.markdown("### 🧾 Ultimi Movimenti Cassa")
            if fin['movimenti']:
                st.dataframe(pd.DataFrame(fin['movimenti'])[['data_movimento', 'importo', 'metodo', 'note']], hide_index=True, use_container_width=True)

        # TAB 3: DIARIO (STORICO LEZIONI)
        with t_hist:
            storico = db.get_storico_lezioni_cliente(selected_id)
            if storico:
                st.dataframe(pd.DataFrame(storico)[['data_inizio', 'titolo', 'stato', 'tipo_pacchetto']], use_container_width=True)
            else:
                st.info("Nessuna lezione registrata.")

        # TAB 4: ANAGRAFICA (EDITABILE)
        with t_ana:
            with st.form("edit_ana"):
                nc1, nc2 = st.columns(2)
                nn = nc1.text_input("Nome", cli['nome']); nc = nc2.text_input("Cognome", cli['cognome'])
                nt = nc1.text_input("Tel", cli['telefono']); ne = nc2.text_input("Email", cli['email'])
                
                # Anamnesi
                anamnesi = json.loads(cli['anamnesi_json']) if cli['anamnesi_json'] else {}
                note = st.text_area("Note Mediche", anamnesi.get('infortuni', ''))
                
                if st.form_submit_button("Salva Modifiche"):
                    db.save_cliente({"nome": nn, "cognome": nc, "telefono": nt, "email": ne, "nascita": cli['data_nascita'], "sesso": cli['sesso'], "stato": cli['stato'], "anamnesi": {**anamnesi, "infortuni": note}}, selected_id)
                    st.success("Aggiornato!")
                    st.rerun()
    else:
        st.info("👈 Seleziona un cliente dalla lista.")