# file: server/pages/02_Clienti.py (Versione FitManager 4.3 - Edit & Payment Fix)
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

# --- DIALOGHI (ORA SUPPORTANO EDIT) ---
@st.experimental_dialog("Scheda Biometrica")
def dialog_misurazione(id_cliente, dati_pre=None, id_misura=None):
    """
    Dialogo intelligente: se passo dati_pre, siamo in MODIFICA.
    Altrimenti siamo in NUOVO INSERIMENTO.
    """
    mode = "Modifica" if dati_pre else "Nuovo"
    st.info(f"Modalità: **{mode} Check-up**")
    
    # Valori di default (o presi dal DB se in edit)
    def v(key, default):
        return float(dati_pre[key]) if dati_pre and key in dati_pre and dati_pre[key] else default

    with st.form("form_misure_pro"):
        # Gestione data: stringa da DB -> date object
        d_def = date.today()
        if dati_pre and 'data_misurazione' in dati_pre:
            try: d_def = pd.to_datetime(dati_pre['data_misurazione']).date()
            except: pass
            
        dt = st.date_input("Data Rilevazione", value=d_def)
        
        t1, t2 = st.tabs(["⚖️ Composizione", "📏 Circonferenze"])
        
        with t1:
            c1, c2 = st.columns(2)
            peso = c1.number_input("Peso (kg)", 40.0, 200.0, v('peso', 70.0), step=0.1)
            grasso = c2.number_input("Massa Grassa (%)", 0.0, 60.0, v('massa_grassa', 15.0), step=0.1)
            muscolo = c1.number_input("Massa Magra (kg)", 0.0, 100.0, v('massa_magra', 0.0), step=0.1)
            acqua = c2.number_input("Acqua (%)", 0.0, 100.0, v('acqua', 0.0), step=0.1)
            
        with t2:
            cc1, cc2 = st.columns(2)
            collo = cc1.number_input("Collo", 0.0, 100.0, v('collo', 0.0), step=0.5)
            spalle = cc2.number_input("Spalle", 0.0, 200.0, v('spalle', 0.0), step=0.5)
            torace = cc1.number_input("Torace", 0.0, 200.0, v('torace', 0.0), step=0.5)
            braccio = cc2.number_input("Braccio", 0.0, 100.0, v('braccio', 0.0), step=0.5)
            vita = cc1.number_input("Vita", 0.0, 200.0, v('vita', 0.0), step=0.5)
            fianchi = cc2.number_input("Fianchi", 0.0, 200.0, v('fianchi', 0.0), step=0.5)
            coscia = cc1.number_input("Coscia", 0.0, 100.0, v('coscia', 0.0), step=0.5)
            polpaccio = cc2.number_input("Polpaccio", 0.0, 100.0, v('polpaccio', 0.0), step=0.5)
            
        note_txt = dati_pre['note'] if dati_pre and 'note' in dati_pre else ""
        note = st.text_area("Note Tecniche", value=note_txt)
        
        btn_label = "💾 Aggiorna Dati" if id_misura else "💾 Salva Nuovo"
        
        if st.form_submit_button(btn_label, type="primary"):
            dati = {
                "data": dt, "peso": peso, "grasso": grasso, "muscolo": muscolo, "acqua": acqua,
                "collo": collo, "spalle": spalle, "torace": torace, "braccio": braccio,
                "vita": vita, "fianchi": fianchi, "coscia": coscia, "polpaccio": polpaccio,
                "note": note
            }
            if id_misura:
                db.update_misurazione(id_misura, dati)
                st.success("Check-up aggiornato!")
            else:
                db.add_misurazione_completa(id_cliente, dati)
                st.success("Check-up salvato!")
            st.rerun()

@st.experimental_dialog("Registra Pagamento")
def dialog_pagamento(id_contratto, residuo):
    st.write(f"Residuo: **€ {residuo:.2f}**")
    with st.form("pay"):
        imp = st.number_input("Importo", value=float(residuo), max_value=float(residuo), step=10.0)
        met = st.selectbox("Metodo", ["CONTANTI", "POS", "BONIFICO"])
        dt = st.date_input("Data", value=date.today())
        nt = st.text_input("Note")
        if st.form_submit_button("Incassa"):
            db.registra_rata(id_contratto, imp, met, dt, nt)
            st.success("OK!"); st.rerun()

@st.experimental_dialog("Nuovo Pacchetto")
def dialog_vendita(id_cl):
    with st.form("sell"):
        pk = st.selectbox("Pacchetto", ["10 PT", "20 PT", "Mensile", "Trimestrale", "Annuale"])
        pz = st.number_input("Prezzo", value=350.0 if "10" in pk else 600.0)
        cr = st.number_input("Crediti", value=10 if "10" in pk else 20)
        start = st.date_input("Inizio", value=date.today())
        if st.form_submit_button("Vendi"):
            db.crea_contratto_vendita(id_cl, pk, pz, cr, start, start+timedelta(365))
            st.success("Fatto!"); st.rerun()

# --- MAIN PAGE ---
c_list, c_det = st.columns([1, 3])

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
                else: st.error("Nome mancante")
    
    elif sel_id:
        cli = db.get_cliente_full(sel_id)
        fin = db.get_cliente_financial_history(sel_id)
        
        # HEADER
        with st.container(border=True):
            h1, h2, h3, h4 = st.columns([0.5, 2, 1, 1])
            h1.image(f"https://api.dicebear.com/9.x/initials/svg?seed={cli['cognome']}", width=70)
            h2.title(f"{cli['nome']} {cli['cognome']}")
            h2.caption(f"Stato: {cli['stato']} | 📞 {cli['telefono']}")
            h3.metric("Crediti", cli.get('lezioni_residue', 0))
            saldo = fin['saldo_globale']
            h4.metric("Saldo", f"€ {saldo:.0f}", delta="Da Saldare" if saldo > 0 else "OK", delta_color="inverse")

        # TABS
        tabs = st.tabs(["📊 Analisi & Risultati", "📋 Cartella Clinica", "💳 Amministrazione", "📅 Diario"])

        # TAB 1: ANALISI (CON EDITING)
        with tabs[0]:
            col_act, col_data = st.columns([1, 3])
            df_prog = db.get_progressi_cliente(sel_id)
            
            with col_act:
                if st.button("➕ Nuovo Check-up", type="primary", use_container_width=True):
                    dialog_misurazione(sel_id)
                
                st.markdown("---")
                st.caption("Storico (Clicca per Modificare)")
                if not df_prog.empty:
                    for _, row in df_prog.iterrows():
                        # Lista check-up come bottoni
                        d_str = pd.to_datetime(row['data_misurazione']).strftime("%d/%m/%Y")
                        if st.button(f"✏️ {d_str}", key=f"hist_{row['id']}", use_container_width=True):
                            dialog_misurazione(sel_id, row.to_dict(), row['id'])
                else:
                    st.caption("Nessun dato.")

            with col_data:
                if not df_prog.empty:
                    # Ordiniamo per data crescente per il grafico
                    df_chart = df_prog.sort_values('data_misurazione')
                    metrica = st.selectbox("Grafico:", ["Peso", "Massa Grassa", "Vita", "Fianchi", "Torace"], index=0)
                    mapping = {"Peso":"peso", "Massa Grassa":"massa_grassa", "Vita":"vita", "Fianchi":"fianchi", "Torace":"torace"}
                    col_db = mapping[metrica]
                    
                    fig = px.line(df_chart, x='data_misurazione', y=col_db, markers=True, title=f"Trend {metrica}")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("👈 Inizia inserendo il primo check-up!")

        # TAB 2: CARTELLA
        with tabs[1]:
            ana = json.loads(cli['anamnesi_json']) if cli['anamnesi_json'] else {}
            with st.form("anamnesi_form"):
                st.subheader("Anagrafica Completa")
                a1, a2 = st.columns(2)
                nm = a1.text_input("Nome", cli['nome']); cg = a2.text_input("Cognome", cli['cognome'])
                tl = a1.text_input("Tel", cli['telefono']); em = a2.text_input("Email", cli['email'])
                
                st.divider()
                st.subheader("Note Mediche & Stile Vita")
                mc1, mc2 = st.columns(2)
                lav = mc1.text_input("Lavoro", ana.get('lavoro', ''))
                infortuni = mc2.text_area("Infortuni", ana.get('infortuni', ''))
                obiettivi = st.text_area("Obiettivi", ana.get('obiettivi', ''))
                
                if st.form_submit_button("💾 Salva Cartella"):
                    new_ana = {**ana, "lavoro": lav, "infortuni": infortuni, "obiettivi": obiettivi}
                    db.save_cliente({
                        "nome": nm, "cognome": cg, "telefono": tl, "email": em,
                        "data_nascita": cli['data_nascita'], "sesso": cli['sesso'], "stato": cli['stato'],
                        "anamnesi": new_ana
                    }, sel_id)
                    st.success("Salvato!"); st.rerun()

        # TAB 3: AMMINISTRAZIONE (FIX TABELLA PAGAMENTI)
        with tabs[2]:
            if st.button("💰 Nuovo Contratto", use_container_width=True): dialog_vendita(sel_id)
            st.divider()
            
            # 1. Contratti
            st.markdown("#### 📜 Contratti")
            for c in fin['contratti']:
                col_st = "green" if c['stato_pagamento']=='SALDATO' else "red"
                with st.expander(f"{c['tipo_pacchetto']} ({c['data_inizio']}) - :{col_st}[{c['stato_pagamento']}]"):
                    c1, c2 = st.columns(2)
                    c1.write(f"Totale: €{c['prezzo_totale']} | Versato: €{c['totale_versato']}")
                    if c['prezzo_totale'] - c['totale_versato'] > 0.1:
                        if c2.button("Paga Rata", key=f"pay_{c['id']}"): 
                            dialog_pagamento(c['id'], c['prezzo_totale'] - c['totale_versato'])

            st.divider()
            
            # 2. Storico Pagamenti (LA TUA RICHIESTA)
            st.markdown("#### 🧾 Registro Pagamenti")
            if fin['movimenti']:
                # Creiamo un DF pulito per la visualizzazione
                df_mov = pd.DataFrame(fin['movimenti'])
                # Formattiamo la data
                df_mov['Data'] = pd.to_datetime(df_mov['data_movimento']).dt.strftime('%d/%m/%Y')
                # Rinominiamo colonne per l'utente
                df_view = df_mov[['Data', 'importo', 'metodo', 'note']].rename(columns={
                    'importo': 'Importo (€)', 'metodo': 'Metodo', 'note': 'Note'
                })
                st.dataframe(df_view, use_container_width=True, hide_index=True)
            else:
                st.caption("Nessun pagamento registrato.")

        # TAB 4: DIARIO
        with tabs[3]:
            hist = db.get_storico_lezioni_cliente(sel_id)
            if hist: st.dataframe(pd.DataFrame(hist)[['data_inizio','titolo','stato']], use_container_width=True)
            else: st.caption("Nessuna lezione.")
    
    else:
        st.info("Seleziona un atleta.")