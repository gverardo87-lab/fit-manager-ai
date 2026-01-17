# file: server/pages/02_Clienti.py (Versione 7.9 - Stable Form Logic)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import date, datetime, timedelta
from core.crm_db import CrmDBManager

db = CrmDBManager()

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

# --- GRAPH ---
def plot_radar_chart(df):
    if len(df) < 1: return None
    last = df.iloc[0]; first = df.iloc[-1]
    keys = ['Spalle', 'Torace', 'Braccio', 'Vita', 'Fianchi', 'Coscia', 'Polpaccio']
    db_keys = [c.lower() for c in keys]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[last.get(k, 0) for k in db_keys], theta=keys, fill='toself', name='Oggi', line_color='#0068c9', opacity=0.8))
    if len(df) > 1: fig.add_trace(go.Scatterpolar(r=[first.get(k, 0) for k in db_keys], theta=keys, fill='toself', name='Inizio', line_color='#bdc3c7', opacity=0.4, line=dict(dash='dot')))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(last.get('fianchi', 100), 120)])), showlegend=True, title="🕸️ Analisi Simmetria", margin=dict(t=40, b=20, l=40, r=40), height=350)
    return fig

# --- DIALOGHI ---

@st.experimental_dialog("Laboratorio Biometrico")
def dialog_misurazione(id_cliente, dati_pre=None, id_misura=None):
    mode = "Modifica" if dati_pre else "Nuovo"
    st.markdown(f"### {mode} Check-up")
    
    # Helper sicuro
    def v(key, default): 
        if dati_pre and isinstance(dati_pre, dict):
            val = dati_pre.get(key, default)
            return float(val) if val is not None else default
        return default

    # FORM DATA
    dati_salvataggio = {}
    submitted = False

    with st.form("form_misure_pro"):
        d_def = date.today()
        if dati_pre and 'data_misurazione' in dati_pre: 
            try: d_def = pd.to_datetime(dati_pre['data_misurazione']).date()
            except: pass
            
        dt = st.date_input("Data Rilevazione", value=d_def)
        
        t1, t2 = st.tabs(["⚖️ Composizione", "📏 Circonferenze"])
        
        with t1:
            c1, c2, c3 = st.columns(3)
            peso = c1.number_input("Peso (kg)", 40.0, 200.0, v('peso', 70.0), step=0.1)
            grasso = c2.number_input("Fat Mass (%)", 0.0, 60.0, v('massa_grassa', 15.0), step=0.1)
            muscolo = c3.number_input("Muscle Mass (kg)", 0.0, 100.0, v('massa_magra', 0.0), step=0.1)
            
        with t2:
            cc1, cc2 = st.columns(2)
            collo = cc1.number_input("Collo", 0.0, 100.0, v('collo', 0.0), step=0.5)
            spalle = cc2.number_input("Spalle", 0.0, 200.0, v('spalle', 0.0), step=0.5)
            torace = cc1.number_input("Torace", 0.0, 200.0, v('torace', 0.0), step=0.5)
            braccio = cc2.number_input("Braccio", 0.0, 100.0, v('braccio', 0.0), step=0.5)
            
            r2c1, r2c2, r2c3, r2c4 = st.columns(4)
            vita = r2c1.number_input("Vita", 0.0, 200.0, v('vita', 0.0), step=0.5)
            fianchi = r2c2.number_input("Fianchi", 0.0, 200.0, v('fianchi', 0.0), step=0.5)
            coscia = r2c3.number_input("Coscia", 0.0, 100.0, v('coscia', 0.0), step=0.5)
            polpaccio = r2c4.number_input("Polpaccio", 0.0, 100.0, v('polpaccio', 0.0), step=0.5)
            
        note_val = dati_pre.get('note', "") if dati_pre else ""
        note = st.text_area("📝 Note Tecniche", value=note_val)
        
        # IL BOTTONE DEVE ESSERE L'ULTIMA COSA NEL FORM
        submitted = st.form_submit_button("💾 Salva Check-up", type="primary")
        
        if submitted:
            dati_salvataggio = {
                "data": dt, "peso": peso, "grasso": grasso, "muscolo": muscolo, "acqua": 0,
                "collo": collo, "spalle": spalle, "torace": torace, "braccio": braccio,
                "vita": vita, "fianchi": fianchi, "coscia": coscia, "polpaccio": polpaccio,
                "note": note
            }

    # LOGICA ESEGUITA FUORI DAL FORM PER EVITARE CRASH
    if submitted:
        if id_misura: db.update_misurazione(id_misura, dati_salvataggio)
        else: db.add_misurazione_completa(id_cliente, dati_salvataggio)
        st.success("Salvato!")
        st.rerun()

@st.experimental_dialog("Nuovo Contratto")
def dialog_vendita(id_cl):
    st.markdown("### 📝 Configurazione Accordo")
    # WIZARD SENZA FORM PER INTERATTIVITÀ TOTALE
    
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
        
        # Logica Bidirezionale
        tipo_calc = st.radio("Calcola in base a:", ["Numero Rate", "Importo Rata"], horizontal=True, label_visibility="collapsed")
        
        if tipo_calc == "Numero Rate":
            n_rate = cr1.number_input("Numero Rate", 2, 24, 3, step=1)
            rata_calc = residuo / n_rate
            cr2.metric("Importo Rata", f"€ {rata_calc:.2f}")
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
        st.info(f"Residuo di **€ {residuo:.2f}** da saldare in unica soluzione.")
    
    st.markdown("---")
    cd1, cd2 = st.columns(2)
    start = cd1.date_input("Inizio", value=date.today())
    end = cd2.date_input("Fine", value=date.today() + timedelta(days=365))
    
    if st.button("✅ Genera Contratto", type="primary", use_container_width=True):
        id_contr = db.crea_contratto_vendita(id_cl, pk, prezzo_tot, cr, start, end, acconto=acconto, metodo_acconto=metodo_acconto)
        
        if residuo > 0:
            if modo_pag == "Rateale 📅":
                db.genera_piano_rate(id_contr, residuo, n_rate, start, freq)
            else:
                db.genera_piano_rate(id_contr, residuo, 1, end, "MENSILE")
        
        st.success("Contratto creato!"); st.rerun()

@st.experimental_dialog("Gestione Rata")
def dialog_edit_rata(rata, totale_contratto):
    st.markdown(f"### Modifica: {rata['descrizione']}")
    tab_pay, tab_edit = st.tabs(["💳 Incassa", "✏️ Modifica"])
    
    with tab_pay:
        # Form pagamento semplice
        with st.form("pay_rata"):
            imp = st.number_input("Importo Versato", value=float(rata['importo_previsto']), step=10.0)
            met = st.selectbox("Metodo", ["CONTANTI", "POS", "BONIFICO"])
            dt = st.date_input("Data Incasso", value=date.today())
            submitted_pay = st.form_submit_button("Registra Incasso", type="primary")
            
        if submitted_pay:
            db.paga_rata_specifica(rata['id'], imp, met, dt)
            st.success("Saldata!"); st.rerun()

    with tab_edit:
        st.caption("Modifica piano")
        # NO FORM QUI per permettere interattività checkbox
        n_imp = st.number_input("Nuovo Importo", value=float(rata['importo_previsto']), step=5.0)
        n_date = st.date_input("Scadenza", value=pd.to_datetime(rata['data_scadenza']).date())
        smart = st.checkbox("Rimodula rate successive", value=True)
        
        c1, c2 = st.columns(2)
        if c1.button("💾 Salva", type="primary"):
            if smart: db.rimodula_piano_rate(rata['id_contratto'], rata['id'], n_imp, n_date)
            else: db.update_rata_programmata(rata['id'], n_date, n_imp, rata['descrizione'])
            st.rerun()
        if c2.button("🗑️ Elimina", type="secondary"):
            db.elimina_rata(rata['id']); st.rerun()

@st.experimental_dialog("Aggiungi Rata")
def dialog_add_rata(id_contratto):
    st.markdown("### ➕ Nuova Rata")
    with st.form("add_r"):
        dt = st.date_input("Scadenza", value=date.today() + timedelta(days=30))
        imp = st.number_input("Importo", value=100.0)
        desc = st.text_input("Descrizione", value="Rata Extra")
        sub = st.form_submit_button("Aggiungi")
        
    if sub:
        db.aggiungi_rata_manuale(id_contratto, dt, imp, desc); st.rerun()

@st.experimental_dialog("Modifica Contratto")
def dialog_edit_contratto(c):
    st.markdown("### Gestione Contratto")
    # NO FORM per avere bottoni distinti
    p = st.number_input("Totale (€)", value=float(c['prezzo_totale']))
    cr = st.number_input("Crediti", value=int(c['crediti_totali']))
    scad = st.date_input("Scadenza", value=pd.to_datetime(c['data_scadenza']).date())
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    if c1.button("💾 Salva Modifiche"):
        db.update_contratto_dettagli(c['id'], p, cr, scad); st.rerun()
    if c2.button("🗑️ ELIMINA", type="primary"):
        db.delete_contratto(c['id']); st.warning("Eliminato"); st.rerun()

# --- MAIN PAGE ---
with st.sidebar:
    st.header("🗂️ Studio Manager")
    df = db.get_clienti_df()
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
                    db.save_cliente({"nome":n, "cognome":c, "telefono":t, "email":e, "data_nascita":date(1990,1,1), "sesso":"Uomo"})
                    st.session_state['new_c'] = False; st.rerun()
    if st.button("Annulla"): st.session_state['new_c'] = False; st.rerun()

elif sel_id:
    cli = db.get_cliente_full(sel_id)
    fin = db.get_cliente_financial_history(sel_id)
    prog = db.get_progressi_cliente(sel_id)
    
    with st.container():
        c1, c2, c3, c4 = st.columns([1, 3, 1.5, 1.5])
        c1.image(f"https://api.dicebear.com/9.x/initials/svg?seed={cli['cognome']}", width=80)
        c2.markdown(f"## {cli['nome']} {cli['cognome']}\n📞 {cli['telefono']}")
        c3.metric("Lezioni", cli.get('lezioni_residue', 0))
        saldo = fin['saldo_globale']
        c4.metric("Saldo", f"€ {saldo:.0f}", delta="OK" if saldo <= 0 else "DA SALDARE", delta_color="inverse" if saldo > 0 else "normal")

    tabs = st.tabs(["🚀 Performance", "📂 Cartella", "💳 Contratti & Rate", "📅 Diario"])

    with tabs[0]: # Performance
        if prog.empty: st.info("Nessun dato."); st.button("➕ Primo Check-up", on_click=lambda: dialog_misurazione(sel_id))
        else:
            col_tools, _ = st.columns([1, 4])
            if col_tools.button("➕ Nuovo Check-up", type="primary"): dialog_misurazione(sel_id)
            
            last = prog.iloc[0]; prev = prog.iloc[1] if len(prog) > 1 else last
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Peso", f"{last['peso']} kg", delta=f"{last['peso']-prev['peso']:.1f}")
            k2.metric("BF", f"{last['massa_grassa']}%", delta=f"{last['massa_grassa']-prev['massa_grassa']:.1f}")
            k3.metric("Vita", f"{last.get('vita',0)}", delta=f"{last.get('vita',0)-prev.get('vita',0):.1f}")
            k4.metric("Torace", f"{last.get('torace',0)}", delta=f"{last.get('torace',0)-prev.get('torace',0):.1f}")
            
            g1, g2 = st.columns([2, 1])
            with g1: st.plotly_chart(px.area(prog.sort_values('data_misurazione'), x='data_misurazione', y='peso', title="Trend Peso"), use_container_width=True)
            with g2: st.plotly_chart(plot_radar_chart(prog), use_container_width=True)
            
            with st.expander("Storico"):
                for _, r in prog.iterrows():
                    if st.button(f"✏️ {pd.to_datetime(r['data_misurazione']).strftime('%d/%m')} - Peso: {r['peso']}", key=f"e_{r['id']}"):
                        dialog_misurazione(sel_id, r.to_dict(), r['id'])

    with tabs[1]: # Cartella Restaurata
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
                db.save_cliente({
                    "nome":nm, "cognome":cg, "telefono":tl, "email":em, 
                    "data_nascita":dn, "sesso":sx, "anamnesi":new_ana
                }, sel_id)
                st.success("Aggiornato!"); st.rerun()

    with tabs[2]: # Contratti
        if st.button("💰 Nuovo Contratto", type="primary"): dialog_vendita(sel_id)
        for c in fin['contratti']:
            with st.container(border=True):
                st.markdown(f"**{c['tipo_pacchetto']}** - Tot: €{c['prezzo_totale']:.2f} (Versato: €{c['totale_versato']:.2f})")
                if st.button("✏️", key=f"edc_{c['id']}", help="Modifica / Elimina"): dialog_edit_contratto(c)
                
                rate = db.get_rate_contratto(c['id'])
                if rate:
                    st.caption("Piano Rateale")
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
    
    with tabs[3]: # Diario
        hist = db.get_storico_lezioni_cliente(sel_id)
        if hist: st.dataframe(pd.DataFrame(hist)[['data_inizio','titolo','stato']], use_container_width=True)
        else: st.info("Nessuna lezione.")
else:
    st.info("👈 Seleziona un atleta.")