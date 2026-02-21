# tools/admin_scripts/test_agenda_idor.py
"""Test end-to-end: Agenda CRUD + Relational IDOR + Anti-Overlapping + validazioni."""

import requests
import sys
import time

BASE = "http://127.0.0.1:8000/api"
passed = 0
failed = 0


def ok(msg):
    global passed
    passed += 1
    print(f"  PASS: {msg}")


def fail(msg):
    global failed
    failed += 1
    print(f"  FAIL: {msg}")


# === SETUP ===
print("=== SETUP ===")

# Login trainer A e B (registrati dai test clients)
r = requests.post(f"{BASE}/auth/login", json={"email": "trainerA@test.com", "password": "SecurePass1!"})
if r.status_code != 200:
    r = requests.post(f"{BASE}/auth/register", json={
        "email": "trainerA@test.com", "password": "SecurePass1!",
        "nome": "Alice", "cognome": "Rossi"
    })
token_a = r.json()["access_token"]
trainer_a_id = r.json()["trainer_id"]
print(f"  Trainer A: id={trainer_a_id}")

r = requests.post(f"{BASE}/auth/login", json={"email": "trainerB@test.com", "password": "SecurePass2!"})
if r.status_code != 200:
    r = requests.post(f"{BASE}/auth/register", json={
        "email": "trainerB@test.com", "password": "SecurePass2!",
        "nome": "Bob", "cognome": "Bianchi"
    })
token_b = r.json()["access_token"]
trainer_b_id = r.json()["trainer_id"]
print(f"  Trainer B: id={trainer_b_id}")

headers_a = {"Authorization": f"Bearer {token_a}"}
headers_b = {"Authorization": f"Bearer {token_b}"}

# Crea un cliente per ogni trainer
r = requests.post(f"{BASE}/clients", json={"nome": "ClienteA", "cognome": "DiAlice"}, headers=headers_a)
client_a = r.json()
print(f"  Cliente A: id={client_a['id']}")

r = requests.post(f"{BASE}/clients", json={"nome": "ClienteB", "cognome": "DiBob"}, headers=headers_b)
client_b = r.json()
print(f"  Cliente B: id={client_b['id']}")


# === TEST 1: POST - Evento PT con cliente ===
print("\n=== TEST 1: POST /events (PT con cliente) ===")
r = requests.post(f"{BASE}/events", json={
    "data_inizio": "2026-04-01T09:00:00",
    "data_fine": "2026-04-01T10:00:00",
    "categoria": "pt",
    "titolo": "Upper Body",
    "id_cliente": client_a["id"],
}, headers=headers_a)
if r.status_code == 201:
    event_a1 = r.json()
    ok(f"Creato id={event_a1['id']}, categoria={event_a1['categoria']}")
else:
    fail(f"atteso 201, ricevuto {r.status_code}: {r.text}")
    sys.exit(1)


# === TEST 2: POST - Evento generico (SALA) senza cliente ===
print("\n=== TEST 2: POST /events (SALA generico) ===")
r = requests.post(f"{BASE}/events", json={
    "data_inizio": "2026-04-01T14:00:00",
    "data_fine": "2026-04-01T15:00:00",
    "categoria": "SALA",
    "titolo": "Ingresso Sala",
}, headers=headers_a)
if r.status_code == 201:
    event_a2 = r.json()
    ok(f"Creato id={event_a2['id']}, id_cliente=None")
else:
    fail(f"atteso 201, ricevuto {r.status_code}: {r.text}")
    sys.exit(1)


# === TEST 3: POST - Evento per trainer B ===
print("\n=== TEST 3: POST /events (Trainer B) ===")
r = requests.post(f"{BASE}/events", json={
    "data_inizio": "2026-04-01T09:00:00",
    "data_fine": "2026-04-01T10:00:00",
    "categoria": "PT",
    "titolo": "Leg Day Bob",
    "id_cliente": client_b["id"],
}, headers=headers_b)
if r.status_code == 201:
    event_b1 = r.json()
    ok(f"Creato id={event_b1['id']} per trainer B (stesso orario di A -> OK, trainer diversi)")
else:
    fail(f"atteso 201, ricevuto {r.status_code}: {r.text}")
    sys.exit(1)


# === TEST 4: ANTI-OVERLAPPING (409 Conflict) ===
print("\n=== TEST 4: Anti-Overlapping ===")
# Trainer A prova a creare un evento che si sovrappone al suo 09:00-10:00
r = requests.post(f"{BASE}/events", json={
    "data_inizio": "2026-04-01T09:30:00",
    "data_fine": "2026-04-01T10:30:00",
    "categoria": "CONSULENZA",
    "titolo": "Overlap Test",
}, headers=headers_a)
if r.status_code == 409:
    ok(f"409 Conflict - sovrapposizione bloccata")
else:
    fail(f"atteso 409, ricevuto {r.status_code}: {r.text}")

# Evento adiacente (10:00-11:00) -> OK, nessuna sovrapposizione
r = requests.post(f"{BASE}/events", json={
    "data_inizio": "2026-04-01T10:00:00",
    "data_fine": "2026-04-01T11:00:00",
    "categoria": "CONSULENZA",
    "titolo": "Adiacente OK",
}, headers=headers_a)
if r.status_code == 201:
    event_a3 = r.json()
    ok(f"Adiacente (10:00-11:00) accettato, nessun overlap")
else:
    fail(f"evento adiacente rifiutato: {r.status_code}: {r.text}")


# === TEST 5: RELATIONAL IDOR - Trainer A crea evento con cliente di B ===
print("\n=== TEST 5: Relational IDOR (cliente altrui) ===")
r = requests.post(f"{BASE}/events", json={
    "data_inizio": "2026-04-02T09:00:00",
    "data_fine": "2026-04-02T10:00:00",
    "categoria": "PT",
    "titolo": "IDOR Attempt",
    "id_cliente": client_b["id"],
}, headers=headers_a)
if r.status_code == 404:
    ok("404 - non posso creare evento con cliente altrui")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")


# === TEST 6: IDOR GET - Trainer B legge evento di A ===
print("\n=== TEST 6: IDOR GET ===")
r = requests.get(f"{BASE}/events/{event_a1['id']}", headers=headers_b)
if r.status_code == 404:
    ok("404 - trainer B non vede evento di A")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")


# === TEST 7: IDOR PUT - Trainer B modifica evento di A ===
print("\n=== TEST 7: IDOR PUT ===")
r = requests.put(f"{BASE}/events/{event_a1['id']}", json={"titolo": "HACKED"}, headers=headers_b)
if r.status_code == 404:
    ok("404 - modifica IDOR bloccata")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")

# Verifica originale intatto
r = requests.get(f"{BASE}/events/{event_a1['id']}", headers=headers_a)
if r.json()["titolo"] == "Upper Body":
    ok("Dati originali intatti")
else:
    fail(f"Titolo cambiato a: {r.json()['titolo']}")


# === TEST 8: IDOR DELETE - Trainer B cancella evento di A ===
print("\n=== TEST 8: IDOR DELETE ===")
r = requests.delete(f"{BASE}/events/{event_a1['id']}", headers=headers_b)
if r.status_code == 404:
    ok("404 - cancellazione IDOR bloccata")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")

r = requests.get(f"{BASE}/events/{event_a1['id']}", headers=headers_a)
if r.status_code == 200:
    ok("Evento ancora presente dopo tentativo IDOR")
else:
    fail("Evento cancellato da trainer non autorizzato!")


# === TEST 9: PUT legittimo + Anti-Overlapping su PUT ===
print("\n=== TEST 9: PUT legittimo + overlap check ===")
# Sposta evento_a1 (09:00-10:00) a 10:00-11:00 -> CONFLICT con event_a3
r = requests.put(f"{BASE}/events/{event_a1['id']}", json={
    "data_inizio": "2026-04-01T10:00:00",
    "data_fine": "2026-04-01T11:00:00",
}, headers=headers_a)
if r.status_code == 409:
    ok("409 - overlap su PUT bloccato")
else:
    fail(f"atteso 409, ricevuto {r.status_code}: {r.text}")

# Sposta a 11:00-12:00 -> OK
r = requests.put(f"{BASE}/events/{event_a1['id']}", json={
    "data_inizio": "2026-04-01T11:00:00",
    "data_fine": "2026-04-01T12:00:00",
}, headers=headers_a)
if r.status_code == 200:
    updated = r.json()
    ok(f"Spostato a {updated['data_inizio'][:16]} - titolo invariato: {updated['titolo']}")
else:
    fail(f"atteso 200, ricevuto {r.status_code}: {r.text}")

# Aggiorna solo titolo (nessun cambio date -> no overlap check)
r = requests.put(f"{BASE}/events/{event_a1['id']}", json={"titolo": "Upper Body V2"}, headers=headers_a)
if r.status_code == 200 and r.json()["titolo"] == "Upper Body V2":
    ok("Partial update titolo senza check overlap")
else:
    fail(f"atteso 200, ricevuto {r.status_code}")


# === TEST 10: GET lista con filtri ===
print("\n=== TEST 10: GET /events con filtri ===")
r = requests.get(f"{BASE}/events", headers=headers_a)
total_a = r.json()["total"]
ok(f"Trainer A vede {total_a} eventi") if total_a >= 3 else fail(f"A vede solo {total_a}")

r = requests.get(f"{BASE}/events", headers=headers_b)
total_b = r.json()["total"]
ok(f"Trainer B vede {total_b} evento(i)") if total_b >= 1 else fail(f"B vede {total_b}")

# Filtro per categoria
r = requests.get(f"{BASE}/events?categoria=SALA", headers=headers_a)
if r.json()["total"] >= 1:
    ok("Filtro per categoria SALA funziona")
else:
    fail("Filtro categoria non funziona")


# === TEST 11: Validazione temporale ===
print("\n=== TEST 11: Validazione temporale ===")
# data_fine < data_inizio
r = requests.post(f"{BASE}/events", json={
    "data_inizio": "2026-04-05T10:00:00",
    "data_fine": "2026-04-05T09:00:00",
    "categoria": "PT", "titolo": "Backwards"
}, headers=headers_a)
ok("date invertite -> 422") if r.status_code == 422 else fail(f"date: {r.status_code}")

# durata > 4h
r = requests.post(f"{BASE}/events", json={
    "data_inizio": "2026-04-05T08:00:00",
    "data_fine": "2026-04-05T12:01:00",
    "categoria": "PT", "titolo": "Troppo lungo"
}, headers=headers_a)
ok("durata >4h -> 422") if r.status_code == 422 else fail(f"durata: {r.status_code}")

# categoria invalida
r = requests.post(f"{BASE}/events", json={
    "data_inizio": "2026-04-05T09:00:00",
    "data_fine": "2026-04-05T10:00:00",
    "categoria": "BUNGEE", "titolo": "Nope"
}, headers=headers_a)
ok("categoria invalida -> 422") if r.status_code == 422 else fail(f"cat: {r.status_code}")


# === TEST 12: DELETE legittimo ===
print("\n=== TEST 12: DELETE legittimo ===")
r = requests.delete(f"{BASE}/events/{event_b1['id']}", headers=headers_b)
if r.status_code == 204:
    ok(f"Evento {event_b1['id']} eliminato")
else:
    fail(f"atteso 204, ricevuto {r.status_code}")

r = requests.get(f"{BASE}/events/{event_b1['id']}", headers=headers_b)
ok("GET dopo DELETE -> 404") if r.status_code == 404 else fail(f"ancora presente: {r.status_code}")


# === Cleanup ===
for eid in [event_a1["id"], event_a2["id"], event_a3["id"]]:
    requests.delete(f"{BASE}/events/{eid}", headers=headers_a)
requests.delete(f"{BASE}/clients/{client_a['id']}", headers=headers_a)
requests.delete(f"{BASE}/clients/{client_b['id']}", headers=headers_b)


# === RISULTATO ===
print(f"\n{'='*50}")
print(f"  RISULTATO: {passed} passati, {failed} falliti")
print(f"{'='*50}")
sys.exit(0 if failed == 0 else 1)
