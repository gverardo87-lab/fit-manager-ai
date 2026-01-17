# file: server/pages/02_Clienti.py
import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import date, datetime, timedelta
from core.crm_db import CrmDBManager

db = CrmDBManager()

st.set_page_config(page_title="Gestione Clienti", page_icon="👥", layout="wide")

# --- CSS CUSTOM ---
st.markdown("""
<style>
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #ddd; }
    div[data-testid="stExpander"] { border: none; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    [data-testid="column"] { min-width: 100px; }
</style>
""", unsafe_allow_html=True)

# --- DIALOGHI ---
@st.experimental_dialog("Laboratorio Biometrico")
def dialog_misurazione(id_cliente):
    st.info("Inserisci i dati del check-up periodico.")
    with st.form("form_misure_pro"):
        dt = st.date_input("Data Rilevazione", value=date.today())
        
        t1, t2 = st.tabs(["⚖️ Composizione Corporea", "📏 Circonferenze (cm)"])
        
        with t1:
            c1, c2 = st.columns(2)
            peso = c1.number_input("Peso (kg)", 40.0, 200.0, 70.0, step=0.1)
            grasso = c2.number_input("Massa Grassa (%)", 3.0, 60.0, 15.0, step=0.1)
            muscolo = c1.number_input("Massa Magra (kg/%)", 0.0, 100.0, 0.0, step=0.1)
            acqua = c2.number_input("Acqua Corporea (%)", 0.0, 100.0, 0.0, step=0.1)
            
        with t2:
            cc1, cc2 = st.columns(2)
            collo = cc1.number_input("Collo", 0.0, step=0.5)
            spalle = cc2.number_input("Spalle", 0.0, step=0.5)
            torace = cc1.number_input("Torace", 0.0, step=0.5)
            braccio = cc2.number_input("Braccio (Bicipite)", 0.0, step=0.5)
            vita = cc1.number_input("Vita (Ombelico)", 0.0, step=0.5)
            fianchi = cc2.number_input("Fianchi", 0.0, step=0.5)
            coscia = cc1.number_input("Coscia prox", 0.0, step=0.5)
            polpaccio = cc2.number_input("Polpaccio", 0.0, step=0.5)
            
        note = st.text_area("Note Tecniche (es. pliche, sensazioni)")
        
        if st.form_submit_button("💾 Archivia Check-up", type="primary"):
            dati = {
                "data": dt, "peso": peso, "grasso": grasso, "muscolo": muscolo, "acqua": acqua,
                "collo": collo, "spalle": spalle, "torace": torace, "braccio": braccio,
                "vita": vita, "fianchi": fianchi, "coscia": coscia, "polpaccio": polpaccio,
                "note": note
            }
            db.add_misurazione_completa(id_cliente, dati)
            st.success("Dati biometrici salvati!")
            st.rerun()

@st.experimental_dialog("Registra Pagamento")
def dialog_pagamento(id_contratto, residuo):
    st.write(f"Residuo: **€ {residuo:.2f}**")
    with st.form("pay"):
        imp = st.number_input("Importo", value=float(residuo), max_value=float(residuo), step=10.0)
        met = st.selectbox("Metodo", ["CONTANTI", "POS", "BONIFICO"])
        dt = st.date_input("Data", value=date.today())
        if st.form_submit_button("Incassa"):
            db.registra_rata(id_contratto, imp, met, dt)
            st.success("OK!"); st.rerun()

@st.experimental_dialog("Nuovo Pacchetto")
def dialog_vendita(id_cl):
    with st.form("sell"):
        pk = st.selectbox("Pacchetto", ["10 PT", "20 PT", "Mensile", "Trimestrale", "Annuale"])
        pz = st.number_input("Prezzo", value=350.0 if "10" in pk else 600.0)
        cr = st.number_input("Crediti", value=10 if "10" in pk else 20)
        if st.form_submit_button("Vendi"):
            db.crea_contratto_vendita(id_cl, pk, pz, cr, date.today(), date.today()+timedelta(365))
            st.success("Fatto!"); st.rerun()

# --- MAIN PAGE ---
c_list, c_det = st.columns([1, 3]) # LIV. 1: Master | Detail

with c_list:
    st.subheader("Atleti")
    df = db.get_clienti_df()
    sel_id = None
    if not df.empty:
        search = st.text_input("🔍", placeholder="Cerca...")
        if search: df = df[df['cognome'].str.contains(search, case=False)]
        opts = {r['id']: f"{r['cognome']} {r['nome']}" for _, r in df.iterrows()}
        if opts:
            sel_id = st.radio("Lista", list(opts.keys()), format_func=lambda x: opts[x], label_visibility="collapsed")
    
    st.divider()
    if st.button("➕ Nuovo Atleta", use_container_width=True): st.session_state['new_c'] = True

with c_det:
    if st.session_state.get('new_c'):
        st.subheader("Nuovo Profilo")
        with st.form("new"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nome*"); c = c2.text_input("Cognome*")
            t = c1.text_input("Telefono"); e = c2.text_input("Email")
            if st.form_submit_button("Crea Profilo", type="primary"): 
                if n and c:
                    db.save_cliente({
                        "nome":n, "cognome":c, "telefono":t, "email":e, 
                        "data_nascita":date(1990,1,1), "sesso":"Uomo", "stato":"Attivo"
                    })
                    st.session_state['new_c']=False; st.rerun()
                else:
                    st.error("Nome e Cognome obbligatori")
    
    elif sel_id:
        cli = db.get_cliente_full(sel_id)
        fin = db.get_cliente_financial_history(sel_id)
        
        # HEADER PRO
        with st.container(border=True):
            h1, h2, h3, h4 = st.columns([0.5, 2, 1, 1])
            h1.image(f"https://api.dicebear.com/9.x/initials/svg?seed={cli['cognome']}", width=70)
            h2.title(f"{cli['nome']} {cli['cognome']}")
            h2.caption(f"Stato: {cli['stato']} | 📞 {cli['telefono']}")
            
            # KPI Rapidi
            h3.metric("Crediti", cli.get('lezioni_residue', 0), delta="Lezioni", delta_color="off")
            saldo = fin['saldo_globale']
            h4.metric("Saldo", f"€ {saldo:.0f}", delta="Da Saldare" if saldo > 0 else "OK", delta_color="inverse")

        # TABS
        tabs = st.tabs(["📊 Analisi & Risultati", "📋 Cartella Clinica", "💳 Amministrazione", "📅 Diario"])

        # TAB 1: ANALISI 360
        with tabs[0]:
            col_act, col_data = st.columns([1, 3])
            with col_act:
                if st.button("➕ Check-up Completo", type="primary", use_container_width=True):
                    dialog_misurazione(sel_id)
                st.info("Monitora qui l'evoluzione fisica.")
            
            with col_data:
                df_prog = db.get_progressi_cliente(sel_id)
                if not df_prog.empty:
                    # Selettore Metrica
                    metrica = st.selectbox("Analizza andamento di:", 
                                         ["Peso", "Massa Grassa", "Vita", "Fianchi", "Torace", "Braccio"], 
                                         index=0)
                    mapping = {"Peso":"peso", "Massa Grassa":"massa_grassa", "Vita":"vita", 
                               "Fianchi":"fianchi", "Torace":"torace", "Braccio":"braccio"}
                    col_db = mapping[metrica]
                    
                    # Grafico
                    if col_db in df_prog.columns:
                        fig = px.line(df_prog, x='data_misurazione', y=col_db, markers=True, 
                                      title=f"Trend {metrica}", line_shape="spline")
                        fig.update_traces(line_color='#FF4B4B', line_width=3)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Confronto Start vs Now
                        if len(df_prog) > 1:
                            first = df_prog.iloc[0]
                            last = df_prog.iloc[-1]
                            
                            st.markdown("#### 🏆 Risultati Ottenuti")
                            k1, k2, k3 = st.columns(3)
                            
                            val1 = first[col_db] or 0
                            val2 = last[col_db] or 0
                            diff = val2 - val1
                            
                            k1.metric(f"{metrica} Iniziale", f"{val1}")
                            k2.metric(f"{metrica} Attuale", f"{val2}")
                            color_d = "normal" if diff < 0 else "inverse" # Verde se scende
                            k3.metric("Variazione", f"{diff:.1f}", delta_color=color_d)
                    else:
                        st.warning("Dato non disponibile per i check-up salvati.")
                            
                else:
                    st.warning("Nessuna misurazione. Fai il primo check-up!")

        # TAB 2: CARTELLA CLINICA
        with tabs[1]:
            ana = json.loads(cli['anamnesi_json']) if cli['anamnesi_json'] else {}
            with st.form("anamnesi_form"):
                st.subheader("🗂️ Anagrafica Completa")
                a1, a2 = st.columns(2)
                nm = a1.text_input("Nome", cli['nome']); cg = a2.text_input("Cognome", cli['cognome'])
                tl = a1.text_input("Tel", cli['telefono']); em = a2.text_input("Email", cli['email'])
                dn = a1.date_input("Nascita", pd.to_datetime(cli['data_nascita']).date() if cli['data_nascita'] else date(1990,1,1))
                
                st.divider()
                st.subheader("🏥 Area Medica & Stile di Vita")
                
                mc1, mc2 = st.columns(2)
                with mc1:
                    st.markdown("**Stile di Vita**")
                    lav = st.text_input("Professione", ana.get('lavoro', ''))
                    sonno = st.slider("Qualità Sonno (1-10)", 1, 10, ana.get('sonno', 7))
                    stress = st.select_slider("Livello Stress", ["Basso", "Medio", "Alto", "Estremo"], value=ana.get('stress', "Medio"))
                
                with mc2:
                    st.markdown("**Clinica**")
                    fumo = st.checkbox("Fumatore", value=ana.get('fumo', False))
                    farmaci = st.text_area("Farmaci / Integratori", ana.get('farmaci', ''))
                    infortuni = st.text_area("Infortuni / Dolori", ana.get('infortuni', ''))
                
                st.markdown("**Obiettivi & Note**")
                obiettivi = st.text_area("Obiettivo del cliente", ana.get('obiettivi', ''), height=100)
                
                if st.form_submit_button("💾 Aggiorna Cartella"):
                    new_ana = {
                        "lavoro": lav, "sonno": sonno, "stress": stress,
                        "fumo": fumo, "farmaci": farmaci, "infortuni": infortuni,
                        "obiettivi": obiettivi
                    }
                    db.save_cliente({
                        "nome": nm, "cognome": cg, "telefono": tl, "email": em,
                        "data_nascita": dn, "sesso": cli['sesso'], "stato": cli['stato'],
                        "anamnesi": new_ana
                    }, sel_id)
                    st.success("Salvato!"); st.rerun()

        # TAB 3: AMMINISTRAZIONE (LAYOUT FIX)
        with tabs[2]:
            # FIX: Layout verticale piatto per evitare nesting level 3
            if st.button("💰 Nuovo Contratto", use_container_width=True): 
                dialog_vendita(sel_id)
            
            st.divider()
            st.caption("Contratti Attivi & Storico")
            
            for c in fin['contratti']:
                col_st = "green" if c['stato_pagamento']=='SALDATO' else "red"
                with st.expander(f"{c['tipo_pacchetto']} | {c['data_inizio']} | :{col_st}[{c['stato_pagamento']}]"):
                    # Ora c1, c2 sono Livello 2 (perché sono dentro Expander -> Tabs -> MainColumn). OK!
                    c1, c2 = st.columns(2)
                    c1.write(f"Prezzo: €{c['prezzo_totale']} (Versato: {c['totale_versato']})")
                    res = c['prezzo_totale'] - c['totale_versato']
                    if res > 0.1:
                        if c2.button("Paga Rata", key=f"pay_{c['id']}"): dialog_pagamento(c['id'], res)

        # TAB 4: DIARIO
        with tabs[3]:
            hist = db.get_storico_lezioni_cliente(sel_id)
            if hist: st.dataframe(pd.DataFrame(hist)[['data_inizio','titolo','stato']], use_container_width=True)
            else: st.caption("Nessuna lezione.")
    
    else:
        st.info("Seleziona un atleta.")