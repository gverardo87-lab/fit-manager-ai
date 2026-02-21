# tools/admin_scripts/test_ledger_dashboard.py
"""
Test end-to-end: Movimenti Cassa (Ledger Integrity) + Dashboard KPI.

Verifica:
- POST /movements crea solo movimenti manuali
- Mass Assignment: id_contratto/id_rata/id_cliente nel body -> 422
- DELETE /movements solo su manuali, sistema -> 400
- IDOR: trainer B non vede/cancella movimenti di trainer A
- GET /movements con filtri (anno, mese, tipo)
- GET /dashboard/summary restituisce KPI aggregati
"""

import requests
from datetime import date, timedelta

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


# ════════════════════════════════════════════════════════════
# SETUP: 2 trainer + 1 cliente + 1 contratto con acconto (per movimento di sistema)
# ════════════════════════════════════════════════════════════
print("=== SETUP ===")

# Trainer A
r = requests.post(f"{BASE}/auth/login", json={"email": "trainerA@test.com", "password": "SecurePass1!"})
if r.status_code != 200:
    r = requests.post(f"{BASE}/auth/register", json={
        "email": "trainerA@test.com", "password": "SecurePass1!",
        "nome": "Alice", "cognome": "Rossi"
    })
token_a = r.json()["access_token"]
trainer_a_id = r.json()["trainer_id"]
print(f"  Trainer A: id={trainer_a_id}")

# Trainer B
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

# Cliente per Trainer A
r = requests.post(f"{BASE}/clients", json={"nome": "Carla", "cognome": "Ledger"}, headers=headers_a)
client_a = r.json()
print(f"  Cliente A: id={client_a['id']}")

# Contratto con acconto (genera CashMovement di sistema)
today = date.today().isoformat()
next_year = (date.today().replace(year=date.today().year + 1)).isoformat()
r = requests.post(f"{BASE}/contracts", json={
    "id_cliente": client_a["id"],
    "tipo_pacchetto": "10 PT Ledger",
    "crediti_totali": 10,
    "prezzo_totale": 500,
    "data_inizio": today,
    "data_scadenza": next_year,
    "acconto": 100,
    "metodo_acconto": "CONTANTI",
}, headers=headers_a)
contract_a = r.json()
print(f"  Contratto A: id={contract_a['id']} (acconto 100)")


# ════════════════════════════════════════════════════════════
# TEST 1: POST /movements — crea movimento manuale
# ════════════════════════════════════════════════════════════
print("\n=== TEST 1: POST /movements (manuale) ===")
r = requests.post(f"{BASE}/movements", json={
    "importo": 150.0,
    "tipo": "USCITA",
    "categoria": "AFFITTO",
    "metodo": "BONIFICO",
    "data_effettiva": today,
    "note": "Affitto palestra gennaio",
}, headers=headers_a)
if r.status_code == 201:
    manual_mov = r.json()
    ok(f"Movimento manuale creato: id={manual_mov['id']}, {manual_mov['importo']}€ {manual_mov['tipo']}")
    if manual_mov["operatore"] == "MANUALE":
        ok("Operatore = MANUALE (corretto)")
    else:
        fail(f"Operatore atteso MANUALE, ottenuto {manual_mov['operatore']}")
    if manual_mov["id_contratto"] is None and manual_mov["id_rata"] is None:
        ok("Nessun link a contratto/rata (corretto per manuale)")
    else:
        fail("Movimento manuale ha link a contratto/rata!")
else:
    fail(f"POST /movements -> {r.status_code}: {r.text}")
    manual_mov = {"id": -1}


# ════════════════════════════════════════════════════════════
# TEST 2: Mass Assignment — id_contratto nel body -> 422
# ════════════════════════════════════════════════════════════
print("\n=== TEST 2: Mass Assignment (id_contratto nel body) ===")
r = requests.post(f"{BASE}/movements", json={
    "importo": 50.0,
    "tipo": "ENTRATA",
    "data_effettiva": today,
    "id_contratto": contract_a["id"],  # VIETATO
}, headers=headers_a)
if r.status_code == 422:
    ok("422 — id_contratto nel body rifiutato (extra: forbid)")
else:
    fail(f"Atteso 422, ottenuto {r.status_code}: {r.text}")


# ════════════════════════════════════════════════════════════
# TEST 3: Mass Assignment — id_rata nel body -> 422
# ════════════════════════════════════════════════════════════
print("\n=== TEST 3: Mass Assignment (id_rata nel body) ===")
r = requests.post(f"{BASE}/movements", json={
    "importo": 50.0,
    "tipo": "ENTRATA",
    "data_effettiva": today,
    "id_rata": 1,  # VIETATO
}, headers=headers_a)
if r.status_code == 422:
    ok("422 — id_rata nel body rifiutato (extra: forbid)")
else:
    fail(f"Atteso 422, ottenuto {r.status_code}: {r.text}")


# ════════════════════════════════════════════════════════════
# TEST 4: Mass Assignment — id_cliente nel body -> 422
# ════════════════════════════════════════════════════════════
print("\n=== TEST 4: Mass Assignment (id_cliente nel body) ===")
r = requests.post(f"{BASE}/movements", json={
    "importo": 50.0,
    "tipo": "ENTRATA",
    "data_effettiva": today,
    "id_cliente": client_a["id"],  # VIETATO
}, headers=headers_a)
if r.status_code == 422:
    ok("422 — id_cliente nel body rifiutato (extra: forbid)")
else:
    fail(f"Atteso 422, ottenuto {r.status_code}: {r.text}")


# ════════════════════════════════════════════════════════════
# TEST 5: Mass Assignment — trainer_id nel body -> 422
# ════════════════════════════════════════════════════════════
print("\n=== TEST 5: Mass Assignment (trainer_id nel body) ===")
r = requests.post(f"{BASE}/movements", json={
    "importo": 50.0,
    "tipo": "ENTRATA",
    "data_effettiva": today,
    "trainer_id": trainer_b_id,  # VIETATO
}, headers=headers_a)
if r.status_code == 422:
    ok("422 — trainer_id nel body rifiutato (extra: forbid)")
else:
    fail(f"Atteso 422, ottenuto {r.status_code}: {r.text}")


# ════════════════════════════════════════════════════════════
# TEST 6: Validazione — tipo invalido -> 422
# ════════════════════════════════════════════════════════════
print("\n=== TEST 6: Validazione tipo invalido ===")
r = requests.post(f"{BASE}/movements", json={
    "importo": 50.0,
    "tipo": "REGALO",
    "data_effettiva": today,
}, headers=headers_a)
if r.status_code == 422:
    ok("422 — tipo 'REGALO' rifiutato")
else:
    fail(f"Atteso 422, ottenuto {r.status_code}: {r.text}")


# ════════════════════════════════════════════════════════════
# TEST 7: Crea secondo movimento manuale per trainer A (ENTRATA)
# ════════════════════════════════════════════════════════════
print("\n=== TEST 7: POST secondo movimento (ENTRATA) ===")
r = requests.post(f"{BASE}/movements", json={
    "importo": 200.0,
    "tipo": "ENTRATA",
    "categoria": "LEZIONE_GRUPPO",
    "metodo": "POS",
    "data_effettiva": today,
    "note": "Lezione di gruppo",
}, headers=headers_a)
if r.status_code == 201:
    manual_mov_2 = r.json()
    ok(f"Secondo manuale: id={manual_mov_2['id']}, {manual_mov_2['importo']}€ ENTRATA")
else:
    fail(f"POST -> {r.status_code}: {r.text}")
    manual_mov_2 = {"id": -1}


# ════════════════════════════════════════════════════════════
# TEST 8: GET /movements — lista con filtro tipo
# ════════════════════════════════════════════════════════════
print("\n=== TEST 8: GET /movements filtro tipo=USCITA ===")
r = requests.get(f"{BASE}/movements?tipo=USCITA", headers=headers_a)
if r.status_code == 200:
    data = r.json()
    uscite = data["items"]
    if all(m["tipo"] == "USCITA" for m in uscite):
        ok(f"Filtro tipo funziona: {data['total']} USCITE")
    else:
        fail("Filtro tipo non funziona — trovate ENTRATE tra le USCITE")
else:
    fail(f"GET /movements?tipo=USCITA -> {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 9: GET /movements — filtro anno + mese
# ════════════════════════════════════════════════════════════
print("\n=== TEST 9: GET /movements filtro anno+mese ===")
now = date.today()
r = requests.get(f"{BASE}/movements?anno={now.year}&mese={now.month}", headers=headers_a)
if r.status_code == 200:
    data = r.json()
    ok(f"Filtro anno/mese: {data['total']} movimenti nel {now.month}/{now.year}")
else:
    fail(f"GET /movements?anno&mese -> {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 10: IDOR — Trainer B non vede movimenti di A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 10: IDOR — isolamento movimenti ===")
r = requests.get(f"{BASE}/movements", headers=headers_b)
if r.status_code == 200:
    data = r.json()
    if data["total"] == 0:
        ok("Trainer B vede 0 movimenti (isolamento multi-tenant)")
    else:
        fail(f"Trainer B vede {data['total']} movimenti — IDOR leak!")
else:
    fail(f"GET /movements B -> {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 11: IDOR DELETE — Trainer B non cancella movimento di A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 11: IDOR DELETE ===")
r = requests.delete(f"{BASE}/movements/{manual_mov['id']}", headers=headers_b)
if r.status_code == 404:
    ok("404 — B non puo' cancellare movimento di A")
else:
    fail(f"Atteso 404, ottenuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 12: DELETE movimento di sistema -> 400
# ════════════════════════════════════════════════════════════
print("\n=== TEST 12: DELETE movimento di sistema -> 400 ===")

# Trova il movimento di sistema (ACCONTO_CONTRATTO) creato dal contratto
r = requests.get(f"{BASE}/movements", headers=headers_a)
system_mov_id = None
if r.status_code == 200:
    for m in r.json()["items"]:
        if m["id_contratto"] is not None:
            system_mov_id = m["id"]
            break

if system_mov_id:
    r = requests.delete(f"{BASE}/movements/{system_mov_id}", headers=headers_a)
    if r.status_code == 400:
        ok(f"400 — movimento di sistema (id={system_mov_id}) protetto")
    else:
        fail(f"Atteso 400, ottenuto {r.status_code}: {r.text}")
else:
    fail("Nessun movimento di sistema trovato (acconto non generato?)")


# ════════════════════════════════════════════════════════════
# TEST 13: DELETE movimento manuale legittimo -> 204
# ════════════════════════════════════════════════════════════
print("\n=== TEST 13: DELETE movimento manuale -> 204 ===")
r = requests.delete(f"{BASE}/movements/{manual_mov['id']}", headers=headers_a)
if r.status_code == 204:
    ok(f"Movimento manuale id={manual_mov['id']} eliminato")
    # Verifica che sia effettivamente sparito
    r2 = requests.get(f"{BASE}/movements", headers=headers_a)
    ids = [m["id"] for m in r2.json()["items"]]
    if manual_mov["id"] not in ids:
        ok("Conferma: movimento non piu' in lista")
    else:
        fail("Movimento ancora presente dopo DELETE!")
else:
    fail(f"Atteso 204, ottenuto {r.status_code}: {r.text}")


# ════════════════════════════════════════════════════════════
# TEST 14: No auth -> 401/403
# ════════════════════════════════════════════════════════════
print("\n=== TEST 14: No auth ===")
r = requests.get(f"{BASE}/movements")
if r.status_code in (401, 403):
    ok(f"no auth -> {r.status_code}")
else:
    fail(f"Atteso 401/403, ottenuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 15: GET /dashboard/summary
# ════════════════════════════════════════════════════════════
print("\n=== TEST 15: GET /dashboard/summary ===")
r = requests.get(f"{BASE}/dashboard/summary", headers=headers_a)
if r.status_code == 200:
    summary = r.json()
    ok(f"Dashboard: clients={summary['active_clients']}, revenue={summary['monthly_revenue']}, "
       f"rates={summary['pending_rates']}, appointments={summary['todays_appointments']}")

    # Verifica che active_clients >= 1 (abbiamo creato Carla)
    if summary["active_clients"] >= 1:
        ok(f"active_clients >= 1 ({summary['active_clients']})")
    else:
        fail(f"active_clients = {summary['active_clients']}, atteso >= 1")

    # Verifica che monthly_revenue include l'acconto (100€) + lezione gruppo (200€)
    if summary["monthly_revenue"] >= 100:
        ok(f"monthly_revenue >= 100 ({summary['monthly_revenue']})")
    else:
        fail(f"monthly_revenue = {summary['monthly_revenue']}, atteso >= 100")

    # Verifica che i valori sono numeri (non None)
    if all(isinstance(summary[k], (int, float)) for k in summary):
        ok("Tutti i KPI sono numerici (nessun None)")
    else:
        fail(f"KPI con None: {summary}")
else:
    fail(f"GET /dashboard/summary -> {r.status_code}: {r.text}")


# ════════════════════════════════════════════════════════════
# TEST 16: Dashboard IDOR — Trainer B vede solo i suoi dati
# ════════════════════════════════════════════════════════════
print("\n=== TEST 16: Dashboard IDOR ===")
r = requests.get(f"{BASE}/dashboard/summary", headers=headers_b)
if r.status_code == 200:
    summary_b = r.json()
    if summary_b["monthly_revenue"] == 0:
        ok("Trainer B: revenue = 0 (nessun dato suo)")
    else:
        fail(f"Trainer B vede revenue {summary_b['monthly_revenue']} — IDOR leak!")
    if summary_b["active_clients"] == 0:
        ok("Trainer B: clients = 0 (isolamento multi-tenant)")
    else:
        fail(f"Trainer B vede {summary_b['active_clients']} clienti — IDOR leak!")
else:
    fail(f"GET /dashboard/summary B -> {r.status_code}: {r.text}")


# ════════════════════════════════════════════════════════════
# TEST 17: Dashboard no auth -> 401/403
# ════════════════════════════════════════════════════════════
print("\n=== TEST 17: Dashboard no auth ===")
r = requests.get(f"{BASE}/dashboard/summary")
if r.status_code in (401, 403):
    ok(f"no auth -> {r.status_code}")
else:
    fail(f"Atteso 401/403, ottenuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# CLEANUP
# ════════════════════════════════════════════════════════════
print("\n=== CLEANUP ===")
import sqlite3
conn = sqlite3.connect("data/crm.db")
cursor = conn.cursor()

# Elimina movimenti di test
cursor.execute("DELETE FROM movimenti_cassa WHERE note LIKE '%Ledger%' OR note LIKE '%Affitto%' OR note LIKE '%Lezione di gruppo%' OR categoria = 'ACCONTO_CONTRATTO'")
# Elimina rate di test
cursor.execute("DELETE FROM rate_programmate WHERE id_contratto IN (SELECT id FROM contratti WHERE tipo_pacchetto LIKE '%Ledger%')")
# Elimina contratti di test
cursor.execute("DELETE FROM contratti WHERE tipo_pacchetto LIKE '%Ledger%'")
# Elimina clienti di test
cursor.execute("DELETE FROM clienti WHERE cognome = 'Ledger'")
conn.commit()
conn.close()
print("  Cleanup completato")


# ════════════════════════════════════════════════════════════
# RISULTATO
# ════════════════════════════════════════════════════════════
print(f"\n{'='*50}")
print(f"  RISULTATO: {passed} passati, {failed} falliti")
print(f"{'='*50}")

if failed > 0:
    exit(1)
