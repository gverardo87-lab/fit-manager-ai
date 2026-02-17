"""Test AgendaRepository.get_events_by_range() method"""
from datetime import date, timedelta
from core.repositories import AgendaRepository, ClientRepository

# Initialize repositories
agenda_repo = AgendaRepository()
client_repo = ClientRepository()

# Calculate date range (same as in 01_Agenda.py)
today = date.today()
start_date = today - timedelta(days=120)
end_date = today + timedelta(days=180)

print(f"\n{'='*60}")
print(f"TEST AgendaRepository.get_events_by_range()")
print(f"{'='*60}")
print(f"TODAY: {today}")
print(f"RANGE: {start_date} → {end_date}")
print(f"{'='*60}")

# Call the repository method
events_raw = agenda_repo.get_events_by_range(start_date, end_date)

print(f"\n✅ Eventi ritornati dal repository: {len(events_raw)}")

if not events_raw:
    print("\n🚨 NESSUN EVENTO RITORNATO! C'è un problema nel repository!")
else:
    print(f"\n📋 Dettaglio eventi:\n")
    
    # Load all active clients for name lookups (same as in fix)
    all_clients = client_repo.get_all_active()
    client_names = {c.id: f"{c.nome} {c.cognome}" for c in all_clients}
    
    for i, e in enumerate(events_raw, 1):
        print(f"\n{i}. Evento #{e.id}")
        print(f"   📅 Data: {e.data_inizio}")
        print(f"   📝 Titolo: {e.titolo}")
        print(f"   🏷  Categoria: {e.categoria}")
        print(f"   ✅ Stato: {e.stato}")
        print(f"   👤 ID Cliente: {e.id_cliente}")
        
        # Test client name lookup
        if e.id_cliente:
            cliente_nome = client_names.get(e.id_cliente)
            print(f"   👤 Nome Cliente: {cliente_nome}")
        else:
            print(f"   👤 Nome Cliente: (nessuno)")
        
        # Check for potential issues with data format
        issues = []
        if not e.data_inizio:
            issues.append("⚠️ data_inizio è None")
        if not e.data_fine:
            issues.append("⚠️ data_fine è None")
        if not e.titolo:
            issues.append("⚠️ titolo è None")
        
        if issues:
            print("   🔴 PROBLEMI:")
            for issue in issues:
                print(f"      {issue}")

print(f"\n{'='*60}\n")

# Now simulate the conversion to dict (same as in 01_Agenda.py)
print("SIMULAZIONE CONVERSIONE A DICT (come in 01_Agenda.py):\n")

events_data = [{
    'id': e.id,
    'data_inizio': e.data_inizio,
    'data_fine': e.data_fine,
    'categoria': e.categoria,
    'titolo': e.titolo,
    'id_cliente': e.id_cliente,
    'stato': e.stato,
    'cliente_nome': client_names.get(e.id_cliente) if e.id_cliente else None
} for e in events_raw]

print(f"✅ Eventi convertiti in dict: {len(events_data)}")

# Test the calendar event creation logic
calendar_events = []
todays_count = 0

for ev in events_data:
    try:
        raw_start = ev['data_inizio'].split(".")[0]
        raw_end = ev['data_fine'].split(".")[0]
        dt_obj = datetime.strptime(raw_start, '%Y-%m-%d %H:%M:%S')
        if dt_obj.date() == today: 
            todays_count += 1
        
        # The rest of the logic from 01_Agenda.py
        cat = str(ev['categoria']).upper() if ev['categoria'] else "VARIE"
        status = ev['stato']
        
        bg = "#95a5a6"
        if status == 'Fatto': bg = "#2ecc71"
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
        
        print(f"✅ Evento #{ev['id']}: {full_title}")
        
    except Exception as e:
        print(f"❌ ERRORE processando evento #{ev.get('id', '?')}: {e}")
        import traceback
        traceback.print_exc()
        continue

print(f"\n{'='*60}")
print(f"RISULTATO FINALE:")
print(f"{'='*60}")
print(f"Eventi processati con successo: {len(calendar_events)}/{len(events_data)}")
print(f"Eventi oggi: {todays_count}")
print(f"{'='*60}\n")

# Import datetime for the test
from datetime import datetime
