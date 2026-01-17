# file: server/pages/02_Clienti.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import date, datetime, timedelta
from core.crm_db import CrmDBManager

db = CrmDBManager()

st.set_page_config(page_title="Elite Client Manager", page_icon="💎", layout="wide")

# --- CSS PRO & WOW EFFECT ---
st.markdown("""
<style>
    /* Card Stile Apple */
    .stMetric {
        background-color: #ffffff;
        padding: 15px 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
        transition: transform 0.2s;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    h1, h2, h3, h4 { font-family: 'Helvetica Neue', sans-serif; letter-spacing: -0.5px; }
    img { border-radius: 50%; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 10px;
        padding: 0 20px;
        background-color: #f8f9fa;
        border: 1px solid #eee;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e3f2fd;
        color: #0d47a1;
        font-weight: bold;
        border: 1px solid #bbdefb;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI GRAFICHE ---
def plot_radar_chart(df):
    if len(df) < 1: return None
    last = df.iloc[0]
    first = df.iloc[-1]
    categories = ['Spalle', 'Torace', 'Braccio', 'Vita', 'Fianchi', 'Coscia', 'Polpaccio']
    db_keys = [c.lower() for c in categories]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[last.get(k, 0) for k in db_keys], theta=categories, fill='toself', name='Oggi', line_color='#0068c9', opacity=0.8))
    if len(df) > 1:
        fig.add_trace(go.Scatterpolar(r=[first.get(k, 0) for k in db_keys], theta=categories, fill='toself', name='Inizio', line_color='#bdc3c7', opacity=0.4, line=dict(dash='dot')))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(last.get('fianchi', 100), 120)])), showlegend=True, title="🕸️ Analisi Simmetria Corporea", margin=dict(t=40, b=20, l=40, r=40), height=350)
    return fig

# --- DIALOGHI ---

@st.experimental_dialog("Laboratorio Biometrico")
def dialog_misurazione(id_cliente, dati_pre=None, id_misura=None):
    mode = "Modifica" if dati_pre else "Nuovo"
    st.markdown(f"### {mode} Check-up")
    def v(key, default): return float(dati_pre[key]) if dati_pre and key in dati_pre and dati_pre[key] else default
    with st.form("form_misure_pro"):
        d_def = date.today()
        if dati_pre: 
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
        note = st.text_area("📝 Note Tecniche", value=dati_pre['note'] if dati_pre else "")
        if st.form_submit_button("💾 Salva Check-up", type="primary"):
            dati = {"data": dt, "peso": peso, "grasso": grasso, "muscolo": muscolo, "acqua": 0, "collo": collo, "spalle": spalle, "torace": torace, "braccio": braccio, "vita": vita, "fianchi": fianchi, "coscia": coscia, "polpaccio": polpaccio, "note": note}
            if id_misura: db.update_misurazione(id_misura, dati)
            else: db.add_misurazione_completa(id_cliente, dati)
            st.rerun()

@st.experimental_dialog("Nuovo Contratto")
def dialog_vendita(id_cl):
    st.markdown("### 📝 Configurazione Accordo")
    with st.form("sell_wizard"):
        c_p1, c_p2 = st.columns(2)
        pk = c_p1.selectbox("Pacchetto", ["10 PT", "20 PT", "Mensile", "Trimestrale", "Annuale", "Consulenza"])
        cr = c_p2.number_input("Crediti", value=10 if "10" in pk else 20)
        st.markdown("---")
        c_f1, c_f2 = st.columns(2)
        prezzo_tot = c_f1.number_input("Prezzo Totale (€)", value=350.0, step=10.0)
        modo_pag = c_f2.radio("Modalità", ["Unica Soluzione", "Rateale 📅"], horizontal=True)
        n_rate = 1
        freq = "MENSILE"
        if modo_pag == "Rateale 📅":
            c_r1, c_r2 = st.columns(2)
            n_rate = c_r1.number_input("Numero Rate", 2, 12, 3)
            freq = c_r2.selectbox("Cadenza", ["MENSILE", "SETTIMANALE"])
        start = st.date_input("Inizio", value=date.today())
        if st.form_submit_button("✅ Crea Contratto", type="primary"):
            id_contr = db.crea_contratto_vendita(id_cl, pk, prezzo_tot, cr, start, start+timedelta(365), acconto=0)
            db.genera_piano_rate(id_contr, prezzo_tot, n_rate, start, freq)
            st.success("Fatto!"); st.rerun()

@st.experimental_dialog("Modifica Contratto")
def dialog_edit_contratto(c):
    st.markdown("### ✏️ Modifica Condizioni")
    with st.form("edit_c"):
        c1, c2 = st.columns(2)
        new_price = c1.number_input("Prezzo Totale (€)", value=float(c['prezzo_totale']))
        new_cred = c2.number_input("Crediti Totali", value=int(c['crediti_totali']))
        new_date = st.date_input("Data Scadenza", value=pd.to_datetime(c['data_scadenza']).date())
        if st.form_submit_button("💾 Salva Modifiche"):
            db.update_contratto_dettagli(c['id'], new_price, new_cred, new_date)
            st.success("Contratto aggiornato"); st.rerun()

@st.experimental_dialog("Gestione Rata")
def dialog_edit_rata(rata):
    st.markdown(f"### Gestione: {rata['descrizione']}")
    if rata['stato'] == 'SALDATA':
        st.success("✅ Rata già saldata. Impossibile modificare.")
        return

    tab_pay, tab_edit = st.tabs(["💳 Paga", "✏️ Modifica"])
    
    with tab_pay:
        with st.form("pay_rata"):
            imp = st.number_input("Importo Versato", value=float(rata['importo_previsto']), step=10.0)
            met = st.selectbox("Metodo", ["CONTANTI", "POS", "BONIFICO"])
            dt = st.date_input("Data Incasso", value=date.today())
            if st.form_submit_button("💰 Registra Incasso", type="primary"):
                db.paga_rata_specifica(rata['id'], imp, met, dt)
                st.success("Saldata!"); st.rerun()

    with tab_edit:
        with st.form("edit_rata"):
            n_date = st.date_input("Nuova Scadenza", value=pd.to_datetime(rata['data_scadenza']).date())
            n_imp = st.number_input("Nuovo Importo", value=float(rata['importo_previsto']))
            n_desc = st.text_input("Descrizione", value=rata['descrizione'])
            
            c_e1, c_e2 = st.columns(2)
            if c_e1.form_submit_button("💾 Salva"):
                db.update_rata_programmata(rata['id'], n_date, n_imp, n_desc)
                st.rerun()
            if c_e2.form_submit_button("🗑️ Elimina", type="primary"):
                db.elimina_rata(rata['id'])
                st.rerun()

@st.experimental_dialog("Aggiungi Rata Manuale")
def dialog_add_rata(id_contratto):
    st.markdown("### ➕ Nuova Rata")
    with st.form("add_r"):
        dt = st.date_input("Scadenza", value=date.today() + timedelta(days=30))
        imp = st.number_input("Importo (€)", value=100.0)
        desc = st.text_input("Descrizione", value="Rata Extra")
        if st.form_submit_button("Aggiungi"):
            db.aggiungi_rata_manuale(id_contratto, dt, imp, desc)
            st.rerun()

# --- MAIN LAYOUT ---
with st.sidebar:
    st.header("🗂️ Studio Manager")
    df = db.get_clienti_df()
    sel_id = None
    if not df.empty:
        search = st.text_input("🔍 Cerca Atleta", placeholder="Nome...")
        if search: df = df[df['cognome'].str.contains(search, case=False)]
        opts = {r['id']: f"{r['cognome']} {r['nome']}" for _, r in df.iterrows()}
        sel_id = st.radio("hidden", list(opts.keys()), format_func=lambda x: opts[x], label_visibility="collapsed")
    st.divider()
    if st.button("➕ Nuovo Atleta", use_container_width=True): st.session_state['new_c'] = True

if st.session_state.get('new_c'):
    st.markdown("## ✨ Inizia un nuovo percorso")
    with st.container(border=True):
        with st.form("new"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nome*"); c = c2.text_input("Cognome*")
            t = c1.text_input("Telefono"); e = c2.text_input("Email")
            if st.form_submit_button("Crea Profilo", type="primary"):
                if n and c:
                    db.save_cliente({"nome":n, "cognome":c, "telefono":t, "email":e, "data_nascita":date(1990,1,1), "sesso":"Uomo"})
                    st.session_state['new_c'] = False; st.rerun()
                else: st.error("Dati mancanti")
    if st.button("Annulla"): st.session_state['new_c'] = False; st.rerun()

elif sel_id:
    cli = db.get_cliente_full(sel_id)
    fin = db.get_cliente_financial_history(sel_id)
    prog = db.get_progressi_cliente(sel_id)
    
    with st.container():
        c_avatar, c_info, c_kpi1, c_kpi2 = st.columns([1, 3, 1.5, 1.5])
        with c_avatar: st.image(f"https://api.dicebear.com/9.x/initials/svg?seed={cli['cognome']}", width=100)
        with c_info:
            st.markdown(f"# {cli['nome']} {cli['cognome']}")
            st.markdown(f"**Status:** `{cli['stato']}` • 📞 {cli['telefono']}")
        with c_kpi1: st.metric("Crediti Residui", cli.get('lezioni_residue', 0), delta="Lezioni Dispo")
        with c_kpi2:
            saldo = fin['saldo_globale']
            st.metric("Saldo Contabile", f"€ {saldo:.0f}", delta="In Regola" if saldo <= 0 else "DA SALDARE", delta_color="inverse" if saldo > 0 else "normal")

    st.markdown("---")
    tabs = st.tabs(["🚀 Performance", "📂 Cartella", "💳 Contratti & Rate", "📅 Diario"])

    with tabs[0]: # Performance
        if prog.empty:
            st.info("👋 Benvenuto! Registra il primo Check-up."); 
            if st.button("➕ Primo Check-up"): dialog_misurazione(sel_id)
        else:
            col_tools, _ = st.columns([1, 4])
            if col_tools.button("➕ Nuovo Check-up", type="primary"): dialog_misurazione(sel_id)
            
            last = prog.iloc[0]; prev = prog.iloc[1] if len(prog) > 1 else last
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Peso", f"{last['peso']} kg", delta=f"{last['peso']-prev['peso']:.1f}")
            k2.metric("BF %", f"{last['massa_grassa']}%", delta=f"{last['massa_grassa']-prev['massa_grassa']:.1f}")
            k3.metric("Vita", f"{last.get('vita',0)} cm", delta=f"{last.get('vita',0)-prev.get('vita',0):.1f}")
            k4.metric("Torace", f"{last.get('torace',0)} cm", delta=f"{last.get('torace',0)-prev.get('torace',0):.1f}")
            
            g1, g2 = st.columns([2, 1])
            with g1:
                met = st.selectbox("Grafico", ["Peso", "Massa Grassa", "Vita", "Torace"], label_visibility="collapsed")
                map_m = {"Peso":"peso", "Massa Grassa":"massa_grassa", "Vita":"vita", "Torace":"torace"}
                st.plotly_chart(px.area(prog.sort_values('data_misurazione'), x='data_misurazione', y=map_m[met]), use_container_width=True)
            with g2:
                fig_radar = plot_radar_chart(prog)
                if fig_radar: st.plotly_chart(fig_radar, use_container_width=True)

            with st.expander("📜 Storico Dettagliato"):
                for _, row in prog.iterrows():
                    c1, c2, c3 = st.columns([1, 4, 1])
                    c1.write(f"**{pd.to_datetime(row['data_misurazione']).strftime('%d/%m')}**")
                    c2.caption(f"Peso: {row['peso']} | BF: {row['massa_grassa']}%")
                    if c3.button("✏️", key=f"ed_{row['id']}"): dialog_misurazione(sel_id, row.to_dict(), row['id'])

    with tabs[1]: # Cartella
        ana = json.loads(cli['anamnesi_json']) if cli['anamnesi_json'] else {}
        with st.form("ana"):
            c1, c2 = st.columns(2)
            nm = c1.text_input("Nome", cli['nome']); cg = c2.text_input("Cognome", cli['cognome'])
            tl = c1.text_input("Tel", cli['telefono']); em = c2.text_input("Email", cli['email'])
            inf = st.text_area("Note Mediche", ana.get('infortuni','')); obi = st.text_area("Obiettivi", ana.get('obiettivi',''))
            if st.form_submit_button("Salva"):
                db.save_cliente({"nome":nm,"cognome":cg,"telefono":tl,"email":em,"anamnesi":{**ana,"infortuni":inf,"obiettivi":obi}}, sel_id)
                st.rerun()

    with tabs[2]: # Contratti & Rate (Elasticità Totale)
        c_head, c_body = st.columns([1, 3])
        if c_head.button("💰 Nuovo Contratto", type="primary", use_container_width=True): dialog_vendita(sel_id)
        
        with c_body:
            for c in fin['contratti']:
                with st.container(border=True):
                    cl1, cl2, cl3 = st.columns([3, 1, 0.5])
                    cl1.markdown(f"**{c['tipo_pacchetto']}** ({c['data_vendita']}) - Tot: €{c['prezzo_totale']}")
                    cl2.caption(f"Versato: €{c['totale_versato']}")
                    if cl3.button("✏️", key=f"ec_{c['id']}", help="Modifica Contratto"): dialog_edit_contratto(c)
                    
                    rate = db.get_rate_contratto(c['id'])
                    if rate:
                        st.markdown("---")
                        for r in rate:
                            r1, r2, r3, r4 = st.columns([2, 2, 2, 1])
                            is_late = pd.to_datetime(r['data_scadenza']).date() < date.today() and r['stato'] != 'SALDATA'
                            col = "red" if is_late else "gray"
                            r1.markdown(f":{col}[{pd.to_datetime(r['data_scadenza']).strftime('%d/%m/%Y')}]")
                            r2.caption(r['descrizione'])
                            r3.write(f"€ {r['importo_previsto']:.0f}")
                            
                            if r['stato'] == 'SALDATA': r4.success("✅")
                            else:
                                if r4.button("⚙️", key=f"manage_{r['id']}"): dialog_edit_rata(r)
                        
                        if st.button("➕ Aggiungi Rata", key=f"add_r_{c['id']}"): dialog_add_rata(c['id'])
                    else:
                        st.warning("Nessun piano rate.")
                        if st.button("Crea Rata Manuale", key=f"first_r_{c['id']}"): dialog_add_rata(c['id'])

    with tabs[3]: # Diario
        hist = db.get_storico_lezioni_cliente(sel_id)
        if hist:
            df_h = pd.DataFrame(hist)
            df_h['Data'] = pd.to_datetime(df_h['data_inizio']).dt.strftime('%d/%m %H:%M')
            st.dataframe(df_h[['Data', 'titolo', 'stato']], use_container_width=True, hide_index=True)
        else: st.caption("Nessuna lezione.")