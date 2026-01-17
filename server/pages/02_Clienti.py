# file: server/pages/02_Clienti.py (Versione FitManager 5.0 - Elite UI)
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
    /* Headers più eleganti */
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; letter-spacing: -0.5px; }
    
    /* Avatar circolare */
    img { border-radius: 50%; }
    
    /* Tabs pulite */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 10px;
        padding: 0 20px;
        background-color: #f8f9fa;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e3f2fd;
        color: #0d47a1;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI GRAFICHE AVANZATE ---
def plot_radar_chart(df):
    """Crea il grafico a ragnatela per le circonferenze."""
    if len(df) < 1: return None
    
    # Prendiamo l'ultimo check-up e il primo
    last = df.iloc[0] # Ordine decrescente nel DB -> 0 è il più recente
    first = df.iloc[-1]
    
    categories = ['Spalle', 'Torace', 'Braccio', 'Vita', 'Fianchi', 'Coscia', 'Polpaccio']
    # Normalizziamo le chiavi per il DB (minuscolo)
    db_keys = [c.lower() for c in categories]
    
    fig = go.Figure()

    # Dati Attuali
    fig.add_trace(go.Scatterpolar(
        r=[last.get(k, 0) for k in db_keys],
        theta=categories,
        fill='toself',
        name='Oggi',
        line_color='#0068c9',
        opacity=0.8
    ))

    # Dati Iniziali (Confronto)
    if len(df) > 1:
        fig.add_trace(go.Scatterpolar(
            r=[first.get(k, 0) for k in db_keys],
            theta=categories,
            fill='toself',
            name='Inizio',
            line_color='#bdc3c7',
            opacity=0.4,
            line=dict(dash='dot')
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(last.get('fianchi', 100), 120)])),
        showlegend=True,
        title="🕸️ Analisi Simmetria Corporea",
        margin=dict(t=40, b=20, l=40, r=40),
        height=350
    )
    return fig

# --- DIALOGHI ---
@st.experimental_dialog("Laboratorio Biometrico")
def dialog_misurazione(id_cliente, dati_pre=None, id_misura=None):
    mode = "Modifica" if dati_pre else "Nuovo"
    st.markdown(f"### {mode} Check-up")
    
    def v(key, default):
        return float(dati_pre[key]) if dati_pre and key in dati_pre and dati_pre[key] else default

    with st.form("form_misure_pro"):
        d_def = date.today()
        if dati_pre and 'data_misurazione' in dati_pre:
            try: d_def = pd.to_datetime(dati_pre['data_misurazione']).date()
            except: pass
        
        dt = st.date_input("Data Rilevazione", value=d_def)
        
        st.markdown("#### 🧬 Composizione & Misure")
        c1, c2, c3 = st.columns(3)
        peso = c1.number_input("Peso (kg)", 40.0, 200.0, v('peso', 70.0), step=0.1)
        grasso = c2.number_input("Fat Mass (%)", 0.0, 60.0, v('massa_grassa', 15.0), step=0.1)
        muscolo = c3.number_input("Muscle Mass (kg)", 0.0, 100.0, v('massa_magra', 0.0), step=0.1)
        
        with st.expander("📏 Circonferenze (cm)", expanded=True):
            r1c1, r1c2, r1c3, r1c4 = st.columns(4)
            collo = r1c1.number_input("Collo", 0.0, 100.0, v('collo', 0.0), step=0.5)
            spalle = r1c2.number_input("Spalle", 0.0, 200.0, v('spalle', 0.0), step=0.5)
            torace = r1c3.number_input("Torace", 0.0, 200.0, v('torace', 0.0), step=0.5)
            braccio = r1c4.number_input("Braccio", 0.0, 100.0, v('braccio', 0.0), step=0.5)
            
            r2c1, r2c2, r2c3, r2c4 = st.columns(4)
            vita = r2c1.number_input("Vita", 0.0, 200.0, v('vita', 0.0), step=0.5)
            fianchi = r2c2.number_input("Fianchi", 0.0, 200.0, v('fianchi', 0.0), step=0.5)
            coscia = r2c3.number_input("Coscia", 0.0, 100.0, v('coscia', 0.0), step=0.5)
            polpaccio = r2c4.number_input("Polpaccio", 0.0, 100.0, v('polpaccio', 0.0), step=0.5)
            
        note = st.text_area("📝 Note Tecniche", value=dati_pre['note'] if dati_pre else "")
        
        btn_txt = "🔄 Aggiorna Dati" if id_misura else "💾 Salva Check-up"
        if st.form_submit_button(btn_txt, type="primary"):
            dati = {
                "data": dt, "peso": peso, "grasso": grasso, "muscolo": muscolo, "acqua": 0,
                "collo": collo, "spalle": spalle, "torace": torace, "braccio": braccio,
                "vita": vita, "fianchi": fianchi, "coscia": coscia, "polpaccio": polpaccio,
                "note": note
            }
            if id_misura: db.update_misurazione(id_misura, dati)
            else: db.add_misurazione_completa(id_cliente, dati)
            st.rerun()

@st.experimental_dialog("Nuovo Pacchetto")
def dialog_vendita(id_cl):
    st.markdown("### 💰 Configura Vendita")
    with st.form("sell"):
        pk = st.selectbox("Pacchetto", ["10 PT", "20 PT", "Mensile", "Trimestrale", "Annuale", "Consulenza"])
        c1, c2 = st.columns(2)
        pz = c1.number_input("Prezzo (€)", value=350.0)
        cr = c2.number_input("Crediti", value=10)
        start = st.date_input("Inizio", value=date.today())
        if st.form_submit_button("Conferma Vendita", type="primary"):
            db.crea_contratto_vendita(id_cl, pk, pz, cr, start, start+timedelta(365))
            st.rerun()

@st.experimental_dialog("Pagamento Rapido")
def dialog_pagamento(id_contratto, residuo):
    st.markdown(f"### Saldare: € {residuo:.2f}")
    with st.form("pay"):
        imp = st.number_input("Importo", value=float(residuo), max_value=float(residuo))
        met = st.selectbox("Metodo", ["CONTANTI", "POS", "BONIFICO"])
        dt = st.date_input("Data", value=date.today())
        nt = st.text_input("Note")
        if st.form_submit_button("Registra Incasso"):
            db.registra_rata(id_contratto, imp, met, dt, nt)
            st.rerun()

# --- MAIN LAYOUT ---
# Sidebar più pulita
with st.sidebar:
    st.header("🗂️ Studio Manager")
    df = db.get_clienti_df()
    sel_id = None
    if not df.empty:
        search = st.text_input("🔍 Cerca Atleta", placeholder="Nome...")
        if search: df = df[df['cognome'].str.contains(search, case=False)]
        
        # Lista stilizzata
        st.markdown("### Elenco Atleti")
        opts = {r['id']: f"{r['cognome']} {r['nome']}" for _, r in df.iterrows()}
        sel_id = st.radio("hidden_label", list(opts.keys()), format_func=lambda x: opts[x], label_visibility="collapsed")
        
        st.markdown("---")
    
    if st.button("➕ Nuovo Atleta", type="secondary", use_container_width=True):
        st.session_state['new_c'] = True

# Area Principale
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
    # Caricamento Dati
    cli = db.get_cliente_full(sel_id)
    fin = db.get_cliente_financial_history(sel_id)
    prog = db.get_progressi_cliente(sel_id)
    
    # --- HEADER "HERO" ---
    with st.container():
        c_avatar, c_info, c_kpi1, c_kpi2 = st.columns([1, 3, 1.5, 1.5])
        
        with c_avatar:
            st.image(f"https://api.dicebear.com/9.x/initials/svg?seed={cli['cognome']}", width=100)
        
        with c_info:
            st.markdown(f"# {cli['nome']} {cli['cognome']}")
            st.markdown(f"**Status:** `{cli['stato']}` • 📞 {cli['telefono']} • 📧 {cli['email']}")
        
        with c_kpi1:
            st.metric("Crediti Residui", cli.get('lezioni_residue', 0), delta="Lezioni Dispo")
            
        with c_kpi2:
            saldo = fin['saldo_globale']
            lbl = "In Regola" if saldo <= 0 else "DA SALDARE"
            clr = "normal" if saldo <= 0 else "inverse"
            st.metric("Saldo Contabile", f"€ {saldo:.0f}", delta=lbl, delta_color=clr)

    st.markdown("---")

    # --- TABS "ELITE" ---
    tabs = st.tabs(["🚀 Performance & Biometria", "📂 Cartella Clinica", "💳 Gestione Commerciale", "📅 Diario Allenamenti"])

    # TAB 1: ANALISI WOW
    with tabs[0]:
        if prog.empty:
            st.info("👋 Benvenuto! Inizia registrando il primo Check-up biometrico.")
            if st.button("➕ Avvia Primo Check-up", type="primary"): dialog_misurazione(sel_id)
        else:
            # Toolbar
            col_tools, col_space = st.columns([1, 4])
            with col_tools:
                if st.button("➕ Nuovo Check-up", type="primary", use_container_width=True): dialog_misurazione(sel_id)
            
            # --- DASHBOARD KPI ---
            last = prog.iloc[0] # Più recente
            prev = prog.iloc[1] if len(prog) > 1 else last
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Peso", f"{last['peso']} kg", delta=f"{last['peso']-prev['peso']:.1f} kg", delta_color="inverse")
            k2.metric("Massa Grassa", f"{last['massa_grassa']}%", delta=f"{last['massa_grassa']-prev['massa_grassa']:.1f}%", delta_color="inverse")
            k3.metric("Vita", f"{last['vita']} cm", delta=f"{last.get('vita',0)-prev.get('vita',0):.1f} cm", delta_color="inverse")
            k4.metric("Torace", f"{last.get('torace',0)} cm", delta=f"{last.get('torace',0)-prev.get('torace',0):.1f} cm")
            
            st.markdown("") # Spacer
            
            # --- GRAFICI SPLIT (Line + Radar) ---
            g_left, g_right = st.columns([2, 1])
            
            with g_left:
                st.subheader("📉 Trend Storico")
                metrica = st.selectbox("Seleziona parametro:", ["Peso", "Massa Grassa", "Vita", "Fianchi", "Torace"], label_visibility="collapsed")
                map_m = {"Peso":"peso", "Massa Grassa":"massa_grassa", "Vita":"vita", "Fianchi":"fianchi", "Torace":"torace"}
                
                # Grafico Linea Elegante
                fig_line = px.area(prog.sort_values('data_misurazione'), x='data_misurazione', y=map_m[metrica], markers=True)
                fig_line.update_traces(line_color='#0068c9', fillcolor='rgba(0, 104, 201, 0.1)')
                fig_line.update_layout(xaxis_title="", yaxis_title=metrica, height=350, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_line, use_container_width=True)
                
            with g_right:
                # Grafico Radar WOW
                fig_radar = plot_radar_chart(prog)
                if fig_radar: st.plotly_chart(fig_radar, use_container_width=True)
            
            # --- STORICO TABELLARE CON EDIT ---
            with st.expander("📜 Storico Dettagliato (Clicca per modificare)"):
                for _, row in prog.iterrows():
                    c_date, c_data, c_act = st.columns([1, 4, 1])
                    d_str = pd.to_datetime(row['data_misurazione']).strftime("%d %B %Y")
                    c_date.write(f"**{d_str}**")
                    c_data.caption(f"Peso: {row['peso']}kg | BF: {row['massa_grassa']}% | Vita: {row.get('vita','-')}cm")
                    if c_act.button("✏️ Modifica", key=f"ed_{row['id']}"):
                        dialog_misurazione(sel_id, row.to_dict(), row['id'])

    # TAB 2: CARTELLA CLINICA
    with tabs[1]:
        ana = json.loads(cli['anamnesi_json']) if cli['anamnesi_json'] else {}
        with st.form("ana_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 👤 Info Personali")
                nm = st.text_input("Nome", cli['nome']); cg = st.text_input("Cognome", cli['cognome'])
                tl = st.text_input("Telefono", cli['telefono']); em = st.text_input("Email", cli['email'])
            with c2:
                st.markdown("#### 🩺 Quadro Medico")
                inf = st.text_area("Infortuni / Dolori", ana.get('infortuni',''))
                obi = st.text_area("Obiettivi Specifici", ana.get('obiettivi',''))
            
            if st.form_submit_button("💾 Salva Modifiche"):
                new_ana = {**ana, "infortuni":inf, "obiettivi":obi}
                db.save_cliente({"nome":nm, "cognome":cg, "telefono":tl, "email":em, "anamnesi":new_ana}, sel_id)
                st.success("Salvato!"); st.rerun()

    # TAB 3: AMMINISTRAZIONE
    with tabs[2]:
        c_head, c_body = st.columns([1, 2]) # Layout asimmetrico
        with c_head:
            st.info("💡 Usa questa sezione per vendere pacchetti e registrare pagamenti.")
            if st.button("💰 Vendi Nuovo Pacchetto", type="primary", use_container_width=True): dialog_vendita(sel_id)
        
        with c_body:
            st.markdown("#### 📂 Contratti Attivi")
            for c in fin['contratti']:
                with st.container(border=True):
                    cl1, cl2, cl3 = st.columns([2, 1, 1])
                    col_st = "green" if c['stato_pagamento']=='SALDATO' else "orange" if c['stato_pagamento']=='PARZIALE' else "red"
                    
                    cl1.markdown(f"**{c['tipo_pacchetto']}**")
                    cl1.caption(f"Data: {c['data_vendita']}")
                    
                    cl2.markdown(f":{col_st}[{c['stato_pagamento']}]")
                    res = c['prezzo_totale'] - c['totale_versato']
                    cl2.caption(f"Residuo: €{res:.2f}")
                    
                    if res > 0.1:
                        if cl3.button("💳 Paga", key=f"p_{c['id']}"): dialog_pagamento(c['id'], res)
                    else:
                        cl3.success("✅")

            st.markdown("#### 🧾 Storico Transazioni")
            if fin['movimenti']:
                df_mov = pd.DataFrame(fin['movimenti'])
                df_mov['Data'] = pd.to_datetime(df_mov['data_movimento']).dt.strftime('%d/%m/%Y')
                st.dataframe(
                    df_mov[['Data', 'categoria', 'importo', 'metodo', 'note']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={"importo": st.column_config.NumberColumn("€", format="%.2f")}
                )

    # TAB 4: DIARIO
    with tabs[3]:
        hist = db.get_storico_lezioni_cliente(sel_id)
        if hist:
            df_h = pd.DataFrame(hist)
            df_h['Data'] = pd.to_datetime(df_h['data_inizio']).dt.strftime('%d/%m %H:%M')
            st.dataframe(df_h[['Data', 'titolo', 'stato', 'tipo_pacchetto']], use_container_width=True, hide_index=True)
        else:
            st.warning("Nessuna lezione registrata in agenda.")

else:
    st.info("👈 Seleziona un atleta dal menu laterale per accedere alla sua cartella.")