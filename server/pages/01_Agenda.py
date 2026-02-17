# file: server/pages/01_Agenda.py (Versione 5.9 - FASE 2 Repository Pattern)
import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, date, timedelta
import pandas as pd
from core.repositories import ClientRepository, AgendaRepository
from core.models import SessioneCreate

# Setup
st.set_page_config(page_title="Agenda Elite", page_icon="📅", layout="wide")
client_repo = ClientRepository()
agenda_repo = AgendaRepository()

# --- GESTIONE STATO ---
if 'cal_view' not in st.session_state:
    st.session_state.cal_view = "timeGridWeek"
if 'cal_date' not in st.session_state:
    st.session_state.cal_date = date.today().isoformat()

# --- CSS CUSTOM "ELITE" ---
st.markdown("""
<style>
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
    }
    .fc-event { 
        border-radius: 6px !important; 
        border: none !important; 
        font-size: 0.9em !important; 
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        cursor: pointer; 
        transition: transform 0.1s; 
        padding: 2px 4px;
    }
    .fc-event:hover { transform: scale(1.02); z-index: 10; }
    .fc-timegrid-slot { height: 50px !important; } 
    .fc-toolbar-title { font-size: 1.5em !important; font-weight: 600; color: #2c3e50; }
    .fc-col-header-cell { background-color: #f8f9fa; padding: 10px 0; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- UTILS ROBUSTE ---
def parse_click_naive(date_str):
    try:
        if "T" in date_str:
            parts = date_str.split("T")
            d_str = parts[0]
            t_str = parts[1][:5]
            return datetime.strptime(d_str, "%Y-%m-%d").date(), datetime.strptime(t_str, "%H:%M").time()
        else:
            return datetime.strptime(date_str, "%Y-%m-%d").date(), datetime.strptime("09:00", "%H:%M").time()
    except:
        return date.today(), datetime.now().time()

# --- DIALOGHI ---

@st.experimental_dialog("📅 Nuovo Appuntamento")
def dialog_add_event(default_date, default_time):
    st.caption(f"Inserimento per il **{default_date.strftime('%d/%m/%Y')}** alle **{default_time.strftime('%H:%M')}**")
    
    with st.form("add_event_form"):
        # Mappa Attività
        ACTIVITY_MAP = {
            "PT 🏋️": {"code": "PT", "title": "Allenamento"},
            "Sala Pesi 🏢": {"code": "SALA", "title": "Ingresso Sala"},
            "Consulenza 🤝": {"code": "CONSULENZA", "title": "Consulenza Tecnica"},
            "Corso 🧘": {"code": "CORSO", "title": "Lezione Group"}
        }
        
        tipo_sel = st.selectbox("Tipo Attività", list(ACTIVITY_MAP.keys()))
        selected_info = ACTIVITY_MAP[tipo_sel]
        
        id_cliente = None
        if selected_info["code"] in ["PT", "CONSULENZA"]:
            clienti = client_repo.get_all_active()
            map_cli = {c.id: f"{c.cognome} {c.nome}" for c in clienti}
            id_cliente = st.selectbox("Seleziona Cliente", options=[None] + list(map_cli.keys()), format_func=lambda x: map_cli.get(x, "Scegli..."))
            
            if id_cliente and selected_info["code"] == "PT":
                info = client_repo.get_by_id(id_cliente)
                if info:
                    res = info.lezioni_residue
                    if res > 0: st.success(f"✅ Crediti Disponibili: {res}")
                    else: st.error(f"⚠️ Crediti Esauriti ({res}).")

        c1, c2 = st.columns(2)
        giorno = c1.date_input("Data", value=default_date)
        ora_ini = c2.time_input("Ora Inizio", value=default_time)
        durata = st.select_slider("Durata (min)", options=[30, 45, 60, 90, 120], value=60)
        
        # KEY Dinamica per aggiornamento
        titolo = st.text_input("Note / Titolo", value=selected_info["title"], key=f"title_{tipo_sel}")
        
        if st.form_submit_button("💾 Salva in Agenda", type="primary"):
            dt_start = datetime.combine(giorno, ora_ini)
            dt_end = dt_start + timedelta(minutes=durata)
            
            try:
                session = SessioneCreate(
                    id_cliente=id_cliente,
                    data_inizio=dt_start,
                    data_fine=dt_end,
                    categoria=selected_info["code"],
                    titolo=titolo,
                    stato="Programmato"
                )
                agenda_repo.create_event(session)
                st.success("Evento creato!")
                st.rerun()
            except Exception as e: st.error(f"Errore: {e}")

@st.experimental_dialog("Gestione Evento")
def dialog_view_event(event_id, event_props):
    st.subheader("Modifica Appuntamento")
    
    # 1. Recupero Dati Esistenti
    props = event_props['extendedProps']
    
    # Parsing Date/Time Start & End
    try:
        start_dt = datetime.strptime(event_props['start'].split("+")[0], "%Y-%m-%dT%H:%M:%S")
        end_dt = datetime.strptime(event_props['end'].split("+")[0], "%Y-%m-%dT%H:%M:%S")
    except:
        start_dt = datetime.now()
        end_dt = start_dt + timedelta(minutes=60)
    
    # Calcolo durata attuale
    durata_min = int((end_dt - start_dt).total_seconds() / 60)
    
    # Info Statiche (Cliente e Tipo)
    st.info(f"**{props.get('categoria', 'N/A')}**" + (f" - {props['cliente']}" if props.get('cliente') else ""))
    
    # 2. Form di Modifica
    with st.form("edit_event_form"):
        c1, c2, c3 = st.columns(3)
        new_date = c1.date_input("Data", value=start_dt.date())
        new_time = c2.time_input("Ora", value=start_dt.time())
        new_dur = c3.number_input("Durata (min)", value=durata_min, step=15, min_value=15)
        
        new_title = st.text_input("Titolo / Note", value=event_props['title'].replace("🏋️ ", "").replace("🏢 ", "").replace("🤝 ", "").replace("🧘 ", "").strip())
        
        col_act1, col_act2 = st.columns(2)
        
        # LOGICA UPDATE
        if col_act1.form_submit_button("💾 Salva Modifiche", type="primary"):
            new_start = datetime.combine(new_date, new_time)
            new_end = new_start + timedelta(minutes=new_dur)
            
            agenda_repo.update_event(event_id, new_start, new_end, new_title)
            st.success("Aggiornato!")
            st.rerun()
            
    # AZIONI RAPIDE FUORI FORM
    st.markdown("---")
    ca, cb = st.columns(2)
    
    status = props.get('stato', 'N/A')
    if status != 'Fatto':
        if ca.button("✅ Conferma Esecuzione", use_container_width=True):
            agenda_repo.confirm_event(event_id)
            st.rerun()
    else:
        ca.success("✅ Già Completato")

    if cb.button("🗑️ Elimina Evento", type="primary", use_container_width=True):
        agenda_repo.delete_event(event_id)
        st.rerun()

# --- CARICAMENTO DATI ---
today = date.today()
events_raw = agenda_repo.get_events_by_range(today - timedelta(days=60), today + timedelta(days=180))

# Convert Pydantic models to dicts for calendar
events_data = [{
    'id': e.id,
    'data_inizio': e.data_inizio,
    'data_fine': e.data_fine,
    'categoria': e.categoria,
    'titolo': e.titolo,
    'id_cliente': e.id_cliente,
    'stato': e.stato
} for e in events_raw]

calendar_events = []
todays_count = 0

for ev in events_data:
    try:
        raw_start = ev['data_inizio'].split(".")[0]
        raw_end = ev['data_fine'].split(".")[0]
        dt_obj = datetime.strptime(raw_start, '%Y-%m-%d %H:%M:%S')
        if dt_obj.date() == today: todays_count += 1
    except: continue

    cat = str(ev['categoria']).upper() if ev['categoria'] else "VARIE"
    status = ev['stato']
    
    bg = "#95a5a6"
    if status == 'Fatto': bg = "#2ecc71"
    elif 'PT' in cat: bg = "#3498db"
    elif 'SALA' in cat: bg = "#f1c40f"
    elif 'CONSULENZA' in cat: bg = "#9b59b6"
    elif 'CORSO' in cat: bg = "#e67e22"

    title_text = f"{ev['titolo']}"
    if ev['nome']: title_text = f"{ev['nome']} {ev['cognome']}"
    
    icon_map = {"PT": "🏋️", "SALA": "🏢", "CONSULENZA": "🤝", "CORSO": "🧘"}
    icon = ""
    for k, v in icon_map.items():
        if k in cat:
            icon = v
            break
            
    full_title = f"{icon} {title_text}"

    calendar_events.append({
        "id": ev['id'],
        "title": full_title,
        "start": raw_start.replace(" ", "T"),
        "end": raw_end.replace(" ", "T"),
        "backgroundColor": bg,
        "borderColor": bg,
        "textColor": "#ffffff" if 'SALA' not in cat else "#2c3e50",
        "extendedProps": {
            "stato": status, "categoria": cat,
            "cliente": f"{ev['nome']} {ev['cognome']}" if ev['nome'] else None
        }
    })

# --- LAYOUT DASHBOARD ---
c1, c2, c3 = st.columns(3)
c1.metric("Appuntamenti Oggi", todays_count, delta="Impegni")
c2.metric("Focus Data", pd.to_datetime(st.session_state.cal_date).strftime("%d %B %Y"))
c3.info("👆 Clicca su uno slot per aggiungere. Clicca su un evento per modificare.")

st.divider()

calendar_options = {
    "editable": True,
    "navLinks": False, 
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay,listWeek"
    },
    "initialView": st.session_state.cal_view,
    "initialDate": st.session_state.cal_date,
    "slotMinTime": "06:00:00",
    "slotMaxTime": "22:00:00",
    "allDaySlot": False,
    "locale": "it",
    "height": "800px",
    "selectable": True,
    "nowIndicator": True,
    "slotDuration": "00:30:00",
    "timeZone": "local", 
}

cal = calendar(
    events=calendar_events,
    options=calendar_options,
    custom_css=".fc-timegrid-slot { height: 50px !important; }",
    key="agenda_master"
)

# --- SMART INTERACTION ---
if cal.get("dateClick"):
    click_data = cal["dateClick"]
    view_type = click_data["view"]["type"]
    date_clicked = click_data.get("dateStr", click_data["date"])
    
    if view_type == "dayGridMonth":
        st.session_state.cal_view = "timeGridDay"
        st.session_state.cal_date = date_clicked 
        st.rerun()
    
    elif view_type in ["timeGridWeek", "timeGridDay"]:
        d_obj, t_obj = parse_click_naive(date_clicked)
        dialog_add_event(d_obj, t_obj)

if cal.get("eventClick"):
    ev = cal["eventClick"]["event"]
    dialog_view_event(int(ev["id"]), ev)