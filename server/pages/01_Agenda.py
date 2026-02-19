# file: server/pages/01_Agenda.py (Versione 5.9 - FASE 2 Repository Pattern)
import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, date, timedelta
import pandas as pd
from core.repositories import ClientRepository, AgendaRepository
from core.models import SessioneCreate
from core.ui_components import load_custom_css

# Setup
st.set_page_config(page_title="Agenda", page_icon=":material/calendar_month:", layout="wide")
load_custom_css()
client_repo = ClientRepository()
agenda_repo = AgendaRepository()

# --- GESTIONE STATO ---
if 'cal_view' not in st.session_state:
    st.session_state.cal_view = "timeGridWeek"
if 'cal_date' not in st.session_state:
    st.session_state.cal_date = date.today().isoformat()

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

@st.dialog("📅 Nuovo Appuntamento")
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
                summary = agenda_repo.get_credit_summary(id_cliente)
                if summary and summary.contratti_attivi > 0:
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("Totali", summary.crediti_totali)
                    mc2.metric("Prenotati", summary.crediti_prenotati)
                    mc3.metric("Disponibili", summary.crediti_disponibili)
                    if summary.crediti_disponibili > 0:
                        st.success(f"Crediti disponibili: {summary.crediti_disponibili}")
                    elif summary.crediti_disponibili == 0:
                        st.warning("Tutti i crediti sono prenotati o completati.")
                    else:
                        st.error(f"OVERBOOKING: {abs(summary.crediti_disponibili)} crediti in eccesso!")
                else:
                    st.warning("Nessun contratto attivo per questo cliente.")

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

@st.dialog("Gestione Evento")
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
    status = props.get('stato', 'N/A')

    if status == 'Programmato':
        ca, cb, cc = st.columns(3)
        if ca.button("✅ Conferma", use_container_width=True):
            agenda_repo.confirm_event(event_id)
            st.rerun()
        if cb.button("❌ Cancella", use_container_width=True):
            st.session_state[f'confirming_cancel_{event_id}'] = True
            st.rerun()
        if cc.button("📅 Rinvia", use_container_width=True):
            st.session_state[f'reschedule_{event_id}'] = True
            st.rerun()

        # Pannello conferma cancellazione
        if st.session_state.get(f'confirming_cancel_{event_id}'):
            st.warning("Vuoi cancellare questa sessione? Il credito prenotato sarà liberato.")
            cc1, cc2 = st.columns(2)
            if cc1.button("✅ Sì, Cancella", use_container_width=True, type="primary", key=f"yes_cancel_{event_id}"):
                agenda_repo.cancel_event(event_id)
                st.session_state[f'confirming_cancel_{event_id}'] = False
                st.success("Sessione cancellata. Credito liberato.")
                st.rerun()
            if cc2.button("❌ Annulla", use_container_width=True, key=f"no_cancel_{event_id}"):
                st.session_state[f'confirming_cancel_{event_id}'] = False
                st.rerun()
    elif status == 'Completato':
        st.success("Sessione completata")
    elif status == 'Cancellato':
        st.info("Sessione cancellata")
    elif status == 'Rinviato':
        st.info("Sessione rinviata a nuova data")

    # Reschedule form (shown only when Rinvia clicked)
    if st.session_state.get(f'reschedule_{event_id}'):
        st.markdown("**Scegli nuova data e ora:**")
        rc1, rc2 = st.columns(2)
        new_resc_date = rc1.date_input("Nuova data", value=start_dt.date(), key=f"resc_date_{event_id}")
        new_resc_time = rc2.time_input("Nuova ora", value=start_dt.time(), key=f"resc_time_{event_id}")
        if st.button("Conferma Rinvio", type="primary", key=f"resc_btn_{event_id}"):
            new_start_dt = datetime.combine(new_resc_date, new_resc_time)
            new_end_dt = new_start_dt + timedelta(minutes=durata_min)
            agenda_repo.reschedule_event(event_id, new_start_dt, new_end_dt)
            del st.session_state[f'reschedule_{event_id}']
            st.success("Sessione rinviata!")
            st.rerun()

    # Delete always available
    st.markdown("---")
    if st.button("🗑️ Elimina Evento", use_container_width=True, key=f"del_{event_id}"):
        st.session_state[f'confirming_delete_{event_id}'] = True
        st.rerun()

    if st.session_state.get(f'confirming_delete_{event_id}'):
        st.error("### ⚠️ Conferma Eliminazione")
        st.warning("Stai per eliminare **definitivamente** questo evento.\n\n⚠️ **Questa azione NON può essere annullata!**")
        conferma = st.checkbox(
            "✓ Sono sicuro di voler eliminare questo evento",
            key=f"check_del_{event_id}"
        )
        cd1, cd2 = st.columns(2)
        if cd1.button("🗑️ Elimina Definitivamente", use_container_width=True, type="primary",
                       disabled=not conferma, key=f"yes_del_{event_id}"):
            agenda_repo.delete_event(event_id)
            st.session_state[f'confirming_delete_{event_id}'] = False
            st.rerun()
        if cd2.button("❌ Annulla", use_container_width=True, key=f"no_del_{event_id}"):
            st.session_state[f'confirming_delete_{event_id}'] = False
            st.rerun()

# --- CARICAMENTO DATI ---
today = date.today()
# Extended range to include past events (last 120 days + future 180 days)
events_raw = agenda_repo.get_events_by_range(today - timedelta(days=120), today + timedelta(days=180))

# Load all active clients for name lookups
all_clients = client_repo.get_all_active()
client_names = {c.id: f"{c.nome} {c.cognome}" for c in all_clients}

# Convert Pydantic models to dicts for calendar
events_data = [{
    'id': e.id,
    'data_inizio': e.data_inizio.strftime('%Y-%m-%d %H:%M:%S'),
    'data_fine': e.data_fine.strftime('%Y-%m-%d %H:%M:%S'),
    'categoria': e.categoria,
    'titolo': e.titolo,
    'id_cliente': e.id_cliente,
    'stato': e.stato,
    'cliente_nome': client_names.get(e.id_cliente) if e.id_cliente else None
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

    # Hide cancelled and rescheduled events from calendar view
    if status in ('Cancellato', 'Rinviato'):
        continue

    bg = "#95a5a6"
    if status == 'Completato': bg = "#2ecc71"
    elif 'PT' in cat: bg = "#3498db"
    elif 'SALA' in cat: bg = "#f1c40f"
    elif 'CONSULENZA' in cat: bg = "#9b59b6"
    elif 'CORSO' in cat: bg = "#e67e22"

    # Use cliente_nome if available, otherwise use titolo
    title_text = ev['cliente_nome'] if ev.get('cliente_nome') else ev['titolo']
    
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
            "stato": status, 
            "categoria": cat,
            "cliente": ev.get('cliente_nome')
        }
    })

# --- LAYOUT DASHBOARD ---
c1, c2, c3 = st.columns(3)
c1.metric("Appuntamenti Oggi", todays_count, delta="Impegni")
c2.metric("Focus Data", pd.to_datetime(st.session_state.cal_date).strftime("%d %B %Y"))
c3.info("👆 Clicca su uno slot per aggiungere. Clicca su un evento per modificare.")

# Warning sessioni stale
stale_sessions = agenda_repo.get_stale_sessions()
if stale_sessions:
    st.warning(f"**{len(stale_sessions)} sessioni passate mai confermate.** Apri ciascun evento per confermare o cancellare.")

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