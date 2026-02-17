# file: server/pages/02_Clienti.py (Versione 8.0 - Stable NO-FORM)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import date, datetime, timedelta
from core.repositories import ClientRepository, ContractRepository, AgendaRepository
from core.models import ClienteCreate, ClienteUpdate, ContratoCreate
from core.ui_components import badge, status_badge, format_currency, empty_state_component, loading_message

client_repo = ClientRepository()
contract_repo = ContractRepository()
agenda_repo = AgendaRepository()

st.set_page_config(page_title="Elite Client Manager", page_icon="💎", layout="wide")

# --- CSS PRO ---
st.markdown("""
<style>
    .stMetric { background-color: #ffffff; padding: 15px 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #f0f0f0; transition: transform 0.2s; }
    .stMetric:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }
    h1, h2, h3, h4 { font-family: 'Helvetica Neue', sans-serif; letter-spacing: -0.5px; }
    img { border-radius: 50%; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; border-radius: 10px; padding: 0 20px; background-color: #f8f9fa; border: 1px solid #eee; }
    .stTabs [aria-selected="true"] { background-color: #e3f2fd; color: #0d47a1; font-weight: bold; border: 1px solid #bbdefb; }
</style>
""", unsafe_allow_html=True)

# --- DIALOGHI (NO FORMS per stabilità) ---

@st.experimental_dialog("Nuovo Contratto")
def dialog_vendita(id_cl):
    st.markdown("### 📝 Configurazione Accordo")
    
    st.caption("📦 Dettagli Pacchetto")
    c1, c2 = st.columns(2)
    pk = c1.selectbox("Pacchetto", ["10 PT", "20 PT", "Mensile", "Trimestrale", "Annuale", "Consulenza"])
    cr = c2.number_input("Crediti (Lezioni)", value=10 if "10" in pk else 20)
    
    st.markdown("---")
    st.caption("💰 Piano Finanziario")
    ce1, ce2 = st.columns(2)
    prezzo_tot = ce1.number_input("Prezzo Totale (€)", value=350.0, step=10.0)
    acconto = ce2.number_input("Acconto Iniziale (€)", value=0.0, step=10.0)
    
    metodo_acconto = None
    if acconto > 0:
        metodo_acconto = st.selectbox("Metodo Acconto", ["CONTANTI", "POS", "BONIFICO"])
    
    residuo = prezzo_tot - acconto
    
    modo_pag = st.radio("Metodo Saldo Residuo:", ["Unica Soluzione (Fine Contratto)", "Rateale 📅"], horizontal=True)
    
    n_rate = 1
    freq = "MENSILE"
    
    if modo_pag == "Rateale 📅" and residuo > 0:
        st.info("Configurazione Rate")
        cr1, cr2, cr3 = st.columns(3)
        
        tipo_calc = st.radio("Calcola in base a:", ["Numero Rate", "Importo Rata"], horizontal=True, label_visibility="collapsed")
        
        if tipo_calc == "Numero Rate":
            n_rate = cr1.number_input("Numero Rate", 2, 24, 3, step=1)
            rata_calc = residuo / n_rate
            cr2.metric("Importo Rata", format_currency(rata_calc))
        else:
            target_rata = cr1.number_input("Importo Desiderato (€)", value=100.0, step=10.0)
            if target_rata > 0:
                n_rate = int(residuo // target_rata)
                if n_rate < 1: n_rate = 1
                resto = residuo - (n_rate * target_rata)
                cr2.metric("Numero Rate", n_rate)
                if resto > 0: cr3.warning(f"+ Maxi-rata finale: € {resto:.2f}")
        
        freq = st.selectbox("Cadenza Rate", ["MENSILE", "SETTIMANALE"])
    
    elif residuo > 0:
        st.info(f"Residuo di **{format_currency(residuo)}** da saldare in unica soluzione.")
    
    st.markdown("---")
    cd1, cd2 = st.columns(2)
    start = cd1.date_input("Inizio", value=date.today())
    end = cd2.date_input("Fine", value=date.today() + timedelta(days=365))
    
    if st.button("✅ Genera Contratto", type="primary", use_container_width=True):
        contract = ContratoCreate(
            id_cliente=id_cl,
            tipo_pacchetto=pk,
            prezzo_totale=prezzo_tot,
            crediti_totali=cr,
            data_inizio=start,
            data_scadenza=end,
            acconto=acconto,
            metodo_acconto=metodo_acconto
        )
        created_contract = contract_repo.create_contract(contract)
        
        if created_contract and residuo > 0:
            id_contr = created_contract.id
            if modo_pag == "Rateale 📅":
                contract_repo.generate_payment_plan(id_contr, residuo, n_rate, start, freq)
            else:
                contract_repo.generate_payment_plan(id_contr, residuo, 1, end, "MENSILE")
        
        st.success("Contratto creato!"); st.rerun()

@st.experimental_dialog("Gestione Rata")
def dialog_edit_rata(rata, totale_contratto):
    st.markdown(f"### Modifica: {rata['descrizione']}")
    tab_pay, tab_edit = st.tabs(["💳 Incassa", "✏️ Modifica"])
    
    with tab_pay:
        imp = st.number_input("Importo Versato", value=float(rata['importo_previsto']), step=10.0)
        met = st.selectbox("Metodo", ["CONTANTI", "POS", "BONIFICO"])
        dt = st.date_input("Data Incasso", value=date.today())
        if st.button("Registra Incasso", type="primary"):
            contract_repo.pay_rate(rata['id'], imp, met, dt)
            st.success("Saldata!"); st.rerun()

    with tab_edit:
        st.caption("Modifica piano")
        n_imp = st.number_input("Nuovo Importo", value=float(rata['importo_previsto']), step=5.0)
        n_date = st.date_input("Scadenza", value=pd.to_datetime(rata['data_scadenza']).date())
        smart = st.checkbox("Rimodula rate successive", value=True)
        
        c1, c2 = st.columns(2)
        if c1.button("💾 Salva", type="primary"):
            if smart: contract_repo.remodulate_payment_plan(rata['id_contratto'], rata['id'], n_imp, n_date)
            else: contract_repo.update_rate(rata['id'], n_date, n_imp, rata['descrizione'])
            st.rerun()
        if c2.button("🗑️ Elimina", type="secondary"):
            contract_repo.delete_rate(rata['id']); st.rerun()

@st.experimental_dialog("Aggiungi Rata")
def dialog_add_rata(id_contratto):
    st.markdown("### ➕ Nuova Rata")
    dt = st.date_input("Scadenza", value=date.today() + timedelta(days=30))
    imp = st.number_input("Importo", value=100.0)
    desc = st.text_input("Descrizione", value="Rata Extra")
    if st.button("Aggiungi"):
        contract_repo.add_manual_rate(id_contratto, dt, imp, desc); st.rerun()

@st.experimental_dialog("Modifica Contratto")
def dialog_edit_contratto(c):
    st.markdown("### Gestione Contratto")
    p = st.number_input("Totale (€)", value=float(c['prezzo_totale']))
    cr = st.number_input("Crediti", value=int(c['crediti_totali']))
    scad = st.date_input("Scadenza", value=pd.to_datetime(c['data_scadenza']).date())
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    if c1.button("💾 Salva Modifiche"):
        contract_repo.update_contract_details(c['id'], p, cr, scad); st.rerun()
    if c2.button("🗑️ ELIMINA", type="primary"):
        contract_repo.delete_contract(c['id']); st.warning("Eliminato"); st.rerun()

# --- MAIN PAGE ---
with st.sidebar:
    st.header("🗂️ Studio Manager")
    clienti = client_repo.get_all_active()
    df = pd.DataFrame([{
        'id': c.id,
        'nome': c.nome,
        'cognome': c.cognome,
        'telefono': c.telefono,
        'email': c.email
    } for c in clienti])
    sel_id = None
    if not df.empty:
        search = st.text_input("🔍 Cerca...", placeholder="Nome...")
        if search: df = df[df['cognome'].str.contains(search, case=False)]
        opts = {r['id']: f"{r['cognome']} {r['nome']}" for _, r in df.iterrows()}
        sel_id = st.radio("hidden", list(opts.keys()), format_func=lambda x: opts[x], label_visibility="collapsed")
    st.divider()
    if st.button("➕ Nuovo Atleta", use_container_width=True): st.session_state['new_c'] = True

if st.session_state.get('new_c'):
    with st.container(border=True):
        st.subheader("Nuovo Profilo")
        with st.form("new"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nome*"); c = c2.text_input("Cognome*")
            t = c1.text_input("Telefono"); e = c2.text_input("Email")
            if st.form_submit_button("Crea", type="primary"):
                if n and c:
                    new_client = ClienteCreate(
                        nome=n,
                        cognome=c,
                        telefono=t or "",
                        email=e or "",
                        data_nascita=date(1990, 1, 1),
                        sesso="Uomo"
                    )
                    client_repo.create(new_client)
                    st.session_state['new_c'] = False; st.rerun()
    if st.button("Annulla"): st.session_state['new_c'] = False; st.rerun()

elif sel_id:
    cli_obj = client_repo.get_by_id(sel_id)
    if not cli_obj:
        st.error("Cliente non trovato")
        st.stop()
    
    # Convert to dict for compatibility with existing code
    cli = {
        'id': cli_obj.id,
        'nome': cli_obj.nome,
        'cognome': cli_obj.cognome,
        'telefono': cli_obj.telefono or '',
        'email': cli_obj.email or '',
        'data_nascita': cli_obj.data_nascita,
        'sesso': cli_obj.sesso or 'Uomo',
        'anamnesi_json': cli_obj.anamnesi_json,
        'lezioni_residue': cli_obj.crediti_residui or 0
    }
    fin = client_repo.get_financial_history(sel_id)
    
    with st.container():
        c1, c2, c3, c4 = st.columns([1, 3, 1.5, 1.5])
        c1.image(f"https://api.dicebear.com/9.x/initials/svg?seed={cli['cognome']}", width=80)
        c2.markdown(f"## {cli['nome']} {cli['cognome']}\n📞 {cli['telefono']}")
        c3.metric("Lezioni", cli.get('lezioni_residue', 0))
        saldo = fin['saldo_globale']
        c4.metric("Saldo", f"€ {saldo:.0f}", delta="OK" if saldo <= 0 else "DA SALDARE", delta_color="inverse" if saldo > 0 else "normal")

    tabs = st.tabs(["� Cartella", "💳 Contratti & Rate", "📅 Diario"])
    
    # Link a Assessment & Allenamenti
    st.info("""
    🏋️ **Per gestire Assessment, Test di Forza e Progressi Allenamento:**
    Vai alla pagina **🏋️ Assessment & Allenamenti**
    """)

    with tabs[0]: # Cartella Restaurata
        ana = json.loads(cli['anamnesi_json']) if cli['anamnesi_json'] else {}
        with st.form("ana_form"):
            st.subheader("👤 Anagrafica")
            c1, c2 = st.columns(2)
            nm = c1.text_input("Nome", cli['nome'])
            cg = c2.text_input("Cognome", cli['cognome'])
            tl = c1.text_input("Telefono", cli['telefono'])
            em = c2.text_input("Email", cli['email'])
            
            dn_val = pd.to_datetime(cli['data_nascita']).date() if cli['data_nascita'] else date(1990,1,1)
            dn = c1.date_input("Data Nascita", dn_val)
            sx = c2.selectbox("Sesso", ["Uomo", "Donna", "Altro"], index=0 if cli['sesso']=="Uomo" else 1)

            st.divider()
            cm1, cm2 = st.columns(2)
            job = cm1.text_input("Professione", ana.get('lavoro', ''))
            style = cm2.select_slider("Stile di Vita", ["Sedentario", "Attivo", "Sportivo", "Agonista"], value=ana.get('stile', "Attivo"))
            
            inf = st.text_area("Infortuni / Note Mediche", ana.get('infortuni',''))
            obi = st.text_area("Obiettivi", ana.get('obiettivi',''))
            
            if st.form_submit_button("💾 Salva Modifiche", type="primary"):
                new_ana = {**ana, "lavoro":job, "stile":style, "infortuni":inf, "obiettivi":obi}
                update_data = ClienteUpdate(
                    nome=nm,
                    cognome=cg,
                    telefono=tl,
                    email=em,
                    data_nascita=dn,
                    sesso=sx,
                    anamnesi_json=json.dumps(new_ana)
                )
                client_repo.update(sel_id, update_data)
                st.success("Aggiornato!"); st.rerun()

    with tabs[1]: # Contratti & Pagamenti
        # --- RIEPILOGO PAGAMENTI GLOBALE ---
        st.subheader("📊 Riepilogo Finanziario")
        fin_cols = st.columns(5)
        
        # Calcolare statistiche
        tot_contratti = sum(c['prezzo_totale'] for c in fin['contratti'])
        tot_versato = sum(c['totale_versato'] for c in fin['contratti'])
        tot_residuo = tot_contratti - tot_versato
        perc_pagato = (tot_versato / tot_contratti * 100) if tot_contratti > 0 else 0
        
        # Separare acconto e rate dai movimenti
        tot_acconto = sum(m['importo'] for m in fin['movimenti'] if m['categoria'] == 'ACCONTO_CONTRATTO')
        tot_rate = sum(m['importo'] for m in fin['movimenti'] if m['categoria'] == 'RATA_CONTRATTO')
        
        fin_cols[0].metric("Totale Contratti", format_currency(tot_contratti), f"{len(fin['contratti'])} contratti")
        fin_cols[1].metric("💰 Acconto", format_currency(tot_acconto), f"{(tot_acconto/tot_contratti*100):.0f}%" if tot_contratti > 0 else "0%")
        fin_cols[2].metric("📋 Rate", format_currency(tot_rate))
        fin_cols[3].metric("Residuo", format_currency(tot_residuo), delta="CRITICO" if tot_residuo > 500 else "OK", delta_color="inverse" if tot_residuo > 500 else "normal")
        
        # Status pagamenti
        rate_scadute = sum(1 for c in fin['contratti'] for r in db.get_rate_contratto(c['id']) if pd.to_datetime(r['data_scadenza']).date() < date.today() and r['stato'] != 'SALDATA')
        fin_cols[4].metric("Rate Scadute", rate_scadute, "⚠️" if rate_scadute > 0 else "✅")
        
        st.divider()
        
        # --- LISTA CONTRATTI DETTAGLIATA ---
        if st.button("💰 Nuovo Contratto", type="primary"): dialog_vendita(sel_id)
        
        for c in fin['contratti']:
            with st.container(border=True):
                # Header contratto con status
                h1, h2, h3 = st.columns([3, 1.5, 1.5])
                status_text = "SALDATO" if c['totale_versato'] >= c['prezzo_totale'] else "PARZIALE" if c['totale_versato'] > 0 else "PENDENTE"
                status_html = status_badge(status_text)
                h1.markdown(f"**{c['tipo_pacchetto']}** {status_html}", unsafe_allow_html=True)
                h2.write(f"Crediti: {c['crediti_usati']}/{c['crediti_totali']}")
                if h3.button("✏️", key=f"edc_{c['id']}", help="Modifica / Elimina"): dialog_edit_contratto(c)
                
                # Progress bar pagamento (clampato tra 0.0 e 1.0)
                progress_val = (c['totale_versato'] / c['prezzo_totale']) if c['prezzo_totale'] > 0 else 0
                st.progress(max(0.0, min(progress_val, 1.0)), text=f"{format_currency(c['totale_versato'])} / {format_currency(c['prezzo_totale'])}")
                
                # Rate
                rate_raw = contract_repo.get_rates_by_contract(c['id'])
                # Convert Pydantic models to dicts
                rate = [{
                    'id': r.id,
                    'id_contratto': r.id_contratto,
                    'data_scadenza': r.data_scadenza,
                    'importo_previsto': r.importo_previsto,
                    'importo_saldato': r.importo_saldato,
                    'stato': r.stato,
                    'descrizione': r.descrizione
                } for r in rate_raw]
                if rate:
                    st.caption("📅 Piano Rateale")
                    rate_paid = sum(1 for r in rate if r['stato'] == 'SALDATA')
                    st.text(f"{rate_paid}/{len(rate)} rate saldate")
                    
                    for r in rate:
                        c_d, c_desc, c_imp, c_btn = st.columns([2, 3, 2, 2])
                        is_late = pd.to_datetime(r['data_scadenza']).date() < date.today() and r['stato'] != 'SALDATA'
                        color = "red" if is_late else "gray"
                        c_d.markdown(f":{color}[{pd.to_datetime(r['data_scadenza']).strftime('%d/%m')}]")
                        c_desc.caption(r['descrizione'])
                        c_imp.write(f"€ {r['importo_previsto']:.0f}")
                        if r['stato'] == 'SALDATA': c_btn.success("✅")
                        else:
                            if c_btn.button("🔴 PAGA" if is_late else "⚙️", key=f"r_{r['id']}", type="primary" if is_late else "secondary"):
                                dialog_edit_rata(r, c['prezzo_totale'])
                    if st.button("➕ Rata", key=f"ar_{c['id']}"): dialog_add_rata(c['id'])
    
    with tabs[2]: # Storico Pagamenti + Lezioni
        st.subheader("📜 Storico Attività")
        
        sub_tab1, sub_tab2 = st.tabs(["💳 Movimenti Finanziari", "📅 Lezioni"])
        
        with sub_tab1:
            # Storico pagamenti
            movimenti = db.get_storico_pagamenti_cliente(sel_id) if hasattr(db, 'get_storico_pagamenti_cliente') else []
            if movimenti:
                mov_df = pd.DataFrame(movimenti)
                mov_df['data'] = pd.to_datetime(mov_df['data_movimento']).dt.strftime('%d/%m/%Y')
                mov_df = mov_df[['data', 'tipo', 'importo', 'metodo', 'note']]
                st.dataframe(mov_df, use_container_width=True, hide_index=True)
                
                # Statistiche movimenti
                st.divider()
                st.caption("📊 Statistiche Movimenti")
                stat_col1, stat_col2 = st.columns(2)
                total_movimenti = sum(m['importo'] for m in movimenti)
                num_movimenti = len(movimenti)
                stat_col1.metric("Totale Movimenti", f"€ {total_movimenti:.2f}")
                stat_col2.metric("Numero Operazioni", num_movimenti)
            else:
                st.info("Nessun movimento registrato per questo cliente.")
        
        with sub_tab2:
            # Storico lezioni
            hist_raw = agenda_repo.get_client_session_history(sel_id)
            # Convert Pydantic models to dicts
            hist = [{
                'data_inizio': h.data_inizio,
                'titolo': h.titolo or '',
                'stato': h.stato or 'Programmato'
            } for h in hist_raw]
            if hist:
                hist_df = pd.DataFrame(hist)
                # Ordinare per data decrescente
                hist_df['data_inizio'] = pd.to_datetime(hist_df['data_inizio'])
                hist_df = hist_df.sort_values('data_inizio', ascending=False)
                
                # Colonne principali
                display_df = hist_df[['data_inizio', 'titolo', 'stato']].copy()
                display_df['data_inizio'] = display_df['data_inizio'].dt.strftime('%d/%m/%Y %H:%M')
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Statistiche lezioni
                st.divider()
                st.caption("📊 Statistiche Lezioni")
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                num_lezioni = len(hist_df)
                completate = sum(1 for h in hist if h['stato'] == 'Completato')
                programmate = sum(1 for h in hist if h['stato'] == 'Programmato')
                
                stat_col1.metric("Totale Lezioni", num_lezioni)
                stat_col2.metric("Completate", completate, f"{(completate/num_lezioni*100):.0f}%" if num_lezioni > 0 else "0%")
                stat_col3.metric("Programmate", programmate)
            else:
                st.info("Nessuna lezione registrata per questo cliente.")
else:
    st.info("👈 Seleziona un atleta.")