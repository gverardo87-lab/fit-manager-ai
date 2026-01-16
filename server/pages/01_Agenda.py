# file: server/pages/01_Agenda.py
import streamlit as st
from streamlit_calendar import calendar # Plugin Google-style
from datetime import datetime, date, timedelta
from core.crm_db import CrmDBManager

db = CrmDBManager()

st.set_page_config(page_title="Agenda", page_icon="📅", layout="wide")

# --- CSS PERSONALIZZATO (Per renderla professionale) ---
st.markdown("""
    <style>
    .fc-event { cursor: pointer; border: none !important; }
    .fc-timegrid-slot { height: 40px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📅 Agenda Operativa")

# --- 1. SIDEBAR: INSERIMENTO RAPIDO ---
with st.sidebar:
    st.header("➕ Nuovo Evento")
    with st.form("quick_add", clear_on_submit=True):
        tipo = st.selectbox("Attività", ["PT 🏋️", "Sala Pesi 🏢", "Corso 🧘", "Consulenza 🤝"])
        
        # Selettore Cliente (solo se serve)
        id_cliente = None
        if "PT" in tipo or "Consulenza" in tipo:
            clienti = db.get_clienti_attivi()
            map_c = {c['id']: f"{c['cognome']} {c['nome']}" for c in clienti}
            sel = st.selectbox("Cliente", [None]+list(map_c.keys()), format_func=lambda x: map_c.get(x, "Seleziona..."))
            id_cliente = sel
        
        titolo = st.text_input("Note / Titolo", value="Turno Sala" if "Sala" in tipo else "Allenamento")
        d_inp = st.date_input("Giorno", date.today())
        t_inp = st.time_input("Ora Inizio", datetime.now().time())
        durata = st.select_slider("Durata (min)", [30, 45, 60, 90, 120, 240], value=60)
        
        if st.form_submit_button("💾 Salva", type="primary"):
            start_dt = datetime.combine(d_inp, t_inp)
            end_dt = start_dt + timedelta(minutes=durata)
            cat = tipo.split(" ")[0] # Prende solo 'PT', 'Sala' etc.
            
            try:
                db.add_evento(start_dt, end_dt, cat, titolo, id_cliente)
                st.toast("Evento salvato!", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"Errore: {e}")

# --- 2. CONFIGURAZIONE CALENDARIO ---
cal_options = {
    "editable": True, # Permette drag & drop (futuro)
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "timeGridWeek,timeGridDay,listWeek"
    },
    "initialView": "timeGridWeek",
    "slotMinTime": "06:00:00",
    "slotMaxTime": "22:00:00",
    "allDaySlot": False,
    "locale": "it",
}

# --- 3. DATI DAL DB ---
today = date.today()
events_data = db.get_agenda_range(today - timedelta(days=30), today + timedelta(days=60))

calendar_events = []
for ev in events_data:
    # Color Coding
    color = "#3788d8" # Blu (Default)
    if ev['categoria'] == 'SALA': color = "#f6bf26" # Giallo
    elif ev['categoria'] == 'CONSULENZA': color = "#d50000" # Rosso
    elif ev['stato'] == 'Fatto': color = "#33b679" # Verde
    
    title = f"{ev['titolo']}"
    if ev['nome']: title += f" ({ev['cognome']})"

    calendar_events.append({
        "id": str(ev['id']),
        "title": title,
        "start": ev['data_inizio'].replace(" ", "T"),
        "end": ev['data_fine'].replace(" ", "T"),
        "backgroundColor": color,
        "borderColor": color,
        "extendedProps": {"stato": ev['stato']}
    })

# --- 4. RENDER E INTERAZIONI ---
col_main, col_detail = st.columns([3, 1])

with col_main:
    cal = calendar(events=calendar_events, options=cal_options, key="my_cal")

# Gestione Click su Evento
if cal.get("eventClick"):
    ev_data = cal["eventClick"]["event"]
    ev_id = int(ev_data["id"])
    
    with col_detail:
        st.info(f"**{ev_data['title']}**")
        st.caption(f"Stato: {ev_data['extendedProps']['stato']}")
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Fatto", key=f"ok_{ev_id}"):
            db.confirm_evento(ev_id)
            st.rerun()
        
        if c2.button("🗑️ Elimina", key=f"del_{ev_id}", type="primary"):
            db.delete_evento(ev_id)
            st.rerun()