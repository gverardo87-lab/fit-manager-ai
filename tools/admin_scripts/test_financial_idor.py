# tools/admin_scripts/test_financial_idor.py
"""
Test end-to-end: Contratti + Rate CRUD, Deep Relational IDOR,
Pagamento Atomico, Mass Assignment Prevention, Validazione.
"""

import requests
import sys

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
# SETUP: 2 trainer + 1 cliente ciascuno
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

# Cliente per A
r = requests.post(f"{BASE}/clients", json={"nome": "Mario", "cognome": "Finanza"}, headers=headers_a)
client_a = r.json()
print(f"  Cliente A: id={client_a['id']}")

# Cliente per B
r = requests.post(f"{BASE}/clients", json={"nome": "Laura", "cognome": "Conto"}, headers=headers_b)
client_b = r.json()
print(f"  Cliente B: id={client_b['id']}")


# ════════════════════════════════════════════════════════════
# TEST 1: POST contratto — Trainer A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 1: POST /contracts (Trainer A) ===")
r = requests.post(f"{BASE}/contracts", json={
    "id_cliente": client_a["id"],
    "tipo_pacchetto": "10 PT",
    "crediti_totali": 10,
    "prezzo_totale": 500,
    "data_inizio": "2026-03-01",
    "data_scadenza": "2026-06-01",
    "acconto": 100,
    "metodo_acconto": "POS",
    "note": "Test contratto"
}, headers=headers_a)
if r.status_code == 201:
    contract_a = r.json()
    ok(f"Creato id={contract_a['id']}, totale_versato={contract_a['totale_versato']}")
else:
    fail(f"atteso 201, ricevuto {r.status_code}: {r.text}")
    sys.exit(1)


# ════════════════════════════════════════════════════════════
# TEST 2: POST contratto — Trainer B
# ════════════════════════════════════════════════════════════
print("\n=== TEST 2: POST /contracts (Trainer B) ===")
r = requests.post(f"{BASE}/contracts", json={
    "id_cliente": client_b["id"],
    "tipo_pacchetto": "Mensile",
    "crediti_totali": 20,
    "prezzo_totale": 300,
    "data_inizio": "2026-03-01",
    "data_scadenza": "2026-09-01",
}, headers=headers_b)
if r.status_code == 201:
    contract_b = r.json()
    ok(f"Creato id={contract_b['id']}")
else:
    fail(f"atteso 201, ricevuto {r.status_code}: {r.text}")
    sys.exit(1)


# ════════════════════════════════════════════════════════════
# TEST 3: Relational IDOR — A crea contratto con cliente di B
# ════════════════════════════════════════════════════════════
print("\n=== TEST 3: Relational IDOR (cliente altrui) ===")
r = requests.post(f"{BASE}/contracts", json={
    "id_cliente": client_b["id"],
    "tipo_pacchetto": "Hack",
    "crediti_totali": 1,
    "prezzo_totale": 1,
    "data_inizio": "2026-03-01",
    "data_scadenza": "2026-04-01",
}, headers=headers_a)
if r.status_code == 404:
    ok("404 — non posso creare contratto con cliente altrui")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 4: IDOR GET — Trainer B legge contratto di A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 4: IDOR GET contratto ===")
r = requests.get(f"{BASE}/contracts/{contract_a['id']}", headers=headers_b)
if r.status_code == 404:
    ok("404 — B non vede contratto di A")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 5: IDOR PUT — Trainer B modifica contratto di A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 5: IDOR PUT contratto ===")
r = requests.put(f"{BASE}/contracts/{contract_a['id']}", json={"tipo_pacchetto": "HACKED"}, headers=headers_b)
if r.status_code == 404:
    ok("404 — modifica IDOR bloccata")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")

# Verifica intatto
r = requests.get(f"{BASE}/contracts/{contract_a['id']}", headers=headers_a)
if r.json()["tipo_pacchetto"] == "10 PT":
    ok("Dati originali intatti")
else:
    fail(f"Tipo cambiato a: {r.json()['tipo_pacchetto']}")


# ════════════════════════════════════════════════════════════
# TEST 6: IDOR DELETE — Trainer B cancella contratto di A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 6: IDOR DELETE contratto ===")
r = requests.delete(f"{BASE}/contracts/{contract_a['id']}", headers=headers_b)
if r.status_code == 404:
    ok("404 — cancellazione IDOR bloccata")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")

r = requests.get(f"{BASE}/contracts/{contract_a['id']}", headers=headers_a)
if r.status_code == 200:
    ok("Contratto ancora presente dopo tentativo IDOR")
else:
    fail("Contratto cancellato da trainer non autorizzato!")


# ════════════════════════════════════════════════════════════
# TEST 7: Mass Assignment — trainer_id nel body
# ════════════════════════════════════════════════════════════
print("\n=== TEST 7: Mass Assignment prevention ===")
r = requests.post(f"{BASE}/contracts", json={
    "id_cliente": client_b["id"],
    "tipo_pacchetto": "Hack",
    "crediti_totali": 1,
    "prezzo_totale": 1,
    "data_inizio": "2026-03-01",
    "data_scadenza": "2026-04-01",
    "trainer_id": trainer_a_id
}, headers=headers_b)
if r.status_code == 422:
    ok("422 — trainer_id nel body rifiutato (extra=forbid)")
else:
    fail(f"atteso 422, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 8: Validazione — date invertite
# ════════════════════════════════════════════════════════════
print("\n=== TEST 8: Validazione contratto ===")
r = requests.post(f"{BASE}/contracts", json={
    "id_cliente": client_a["id"],
    "tipo_pacchetto": "Test",
    "crediti_totali": 1,
    "prezzo_totale": 100,
    "data_inizio": "2026-06-01",
    "data_scadenza": "2026-03-01",
}, headers=headers_a)
ok("date invertite -> 422") if r.status_code == 422 else fail(f"date: {r.status_code}")

# acconto > prezzo
r = requests.post(f"{BASE}/contracts", json={
    "id_cliente": client_a["id"],
    "tipo_pacchetto": "Test",
    "crediti_totali": 1,
    "prezzo_totale": 100,
    "data_inizio": "2026-03-01",
    "data_scadenza": "2026-06-01",
    "acconto": 200,
}, headers=headers_a)
ok("acconto > prezzo -> 422") if r.status_code == 422 else fail(f"acconto: {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 9: Genera piano rate per contratto A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 9: POST /rates/generate-plan ===")
r = requests.post(f"{BASE}/rates/generate-plan/{contract_a['id']}", json={
    "importo_da_rateizzare": 400,
    "numero_rate": 4,
    "data_prima_rata": "2026-04-01",
    "frequenza": "MENSILE"
}, headers=headers_a)
if r.status_code == 201:
    plan = r.json()
    ok(f"Piano generato: {plan['total']} rate per contratto {plan['contract_id']}")
    rate_ids_a = [rt["id"] for rt in plan["items"]]
else:
    fail(f"atteso 201, ricevuto {r.status_code}: {r.text}")
    sys.exit(1)


# ════════════════════════════════════════════════════════════
# TEST 10: IDOR generate-plan — B genera piano su contratto di A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 10: IDOR generate-plan ===")
r = requests.post(f"{BASE}/rates/generate-plan/{contract_a['id']}", json={
    "importo_da_rateizzare": 100,
    "numero_rate": 1,
    "data_prima_rata": "2026-04-01",
}, headers=headers_b)
if r.status_code == 404:
    ok("404 — B non puo' generare piano per contratto di A")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 11: Deep IDOR GET — B legge rata di A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 11: Deep IDOR GET rata ===")
r = requests.get(f"{BASE}/rates/{rate_ids_a[0]}", headers=headers_b)
if r.status_code == 404:
    ok("404 — B non vede rata di contratto di A (Deep IDOR)")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 12: Deep IDOR PUT — B modifica rata di A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 12: Deep IDOR PUT rata ===")
r = requests.put(f"{BASE}/rates/{rate_ids_a[0]}", json={"importo_previsto": 0.01}, headers=headers_b)
if r.status_code == 404:
    ok("404 — modifica Deep IDOR bloccata")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 13: Deep IDOR DELETE — B cancella rata di A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 13: Deep IDOR DELETE rata ===")
r = requests.delete(f"{BASE}/rates/{rate_ids_a[0]}", headers=headers_b)
if r.status_code == 404:
    ok("404 — cancellazione Deep IDOR bloccata")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 14: Deep IDOR PAY — B paga rata di A
# ════════════════════════════════════════════════════════════
print("\n=== TEST 14: Deep IDOR PAY rata ===")
r = requests.post(f"{BASE}/rates/{rate_ids_a[0]}/pay", json={
    "importo": 100, "metodo": "CONTANTI"
}, headers=headers_b)
if r.status_code == 404:
    ok("404 — pagamento Deep IDOR bloccato")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 15: Pagamento atomico — paga rata 1
# ════════════════════════════════════════════════════════════
print("\n=== TEST 15: POST /rates/{id}/pay (atomico) ===")
r = requests.post(f"{BASE}/rates/{rate_ids_a[0]}/pay", json={
    "importo": 100, "metodo": "POS", "note": "Pagamento rata 1"
}, headers=headers_a)
if r.status_code == 200:
    paid = r.json()
    ok(f"Rata pagata: stato={paid['stato']}, saldato={paid['importo_saldato']}")
else:
    fail(f"atteso 200, ricevuto {r.status_code}: {r.text}")

# Verifica contratto aggiornato
r = requests.get(f"{BASE}/contracts/{contract_a['id']}", headers=headers_a)
c = r.json()
# totale_versato = 200 (100 acconto iniziale + 100 rata pagata)
ok(f"Contratto: totale_versato={c['totale_versato']}, stato={c['stato_pagamento']}") if c["totale_versato"] == 200 else fail(f"totale_versato={c['totale_versato']}")


# ════════════════════════════════════════════════════════════
# TEST 16: Pagamento parziale — importo < previsto
# ════════════════════════════════════════════════════════════
print("\n=== TEST 16: Pagamento parziale rata 2 ===")
r = requests.post(f"{BASE}/rates/{rate_ids_a[1]}/pay", json={
    "importo": 50, "metodo": "CONTANTI"
}, headers=headers_a)
if r.status_code == 200:
    paid = r.json()
    if paid["stato"] == "PARZIALE":
        ok(f"Stato PARZIALE: saldato={paid['importo_saldato']} su previsto={paid['importo_previsto']}")
    else:
        fail(f"atteso PARZIALE, ricevuto {paid['stato']}")
else:
    fail(f"atteso 200, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 17: Rata gia' SALDATA — 400
# ════════════════════════════════════════════════════════════
print("\n=== TEST 17: Rata gia' saldata -> 400 ===")
r = requests.post(f"{BASE}/rates/{rate_ids_a[0]}/pay", json={
    "importo": 1, "metodo": "CONTANTI"
}, headers=headers_a)
if r.status_code == 400:
    ok("400 — rata gia' saldata")
else:
    fail(f"atteso 400, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 18: Pagamento tutte le rate -> contratto SALDATO
# ════════════════════════════════════════════════════════════
print("\n=== TEST 18: Paga tutto -> contratto SALDATO ===")
# Rata 2: completa (mancano 50)
r = requests.post(f"{BASE}/rates/{rate_ids_a[1]}/pay", json={
    "importo": 50, "metodo": "POS"
}, headers=headers_a)
ok(f"Rata 2 completata: stato={r.json()['stato']}") if r.status_code == 200 else fail(f"rata 2: {r.status_code}")

# Rata 3
r = requests.post(f"{BASE}/rates/{rate_ids_a[2]}/pay", json={
    "importo": 100, "metodo": "BONIFICO"
}, headers=headers_a)
ok(f"Rata 3: stato={r.json()['stato']}") if r.status_code == 200 else fail(f"rata 3: {r.status_code}")

# Rata 4 (ultima)
r = requests.post(f"{BASE}/rates/{rate_ids_a[3]}/pay", json={
    "importo": 100, "metodo": "CONTANTI"
}, headers=headers_a)
ok(f"Rata 4: stato={r.json()['stato']}") if r.status_code == 200 else fail(f"rata 4: {r.status_code}")

# Verifica contratto SALDATO
r = requests.get(f"{BASE}/contracts/{contract_a['id']}", headers=headers_a)
c = r.json()
if c["stato_pagamento"] == "SALDATO":
    ok(f"Contratto SALDATO! totale_versato={c['totale_versato']} (prezzo={c['prezzo_totale']})")
else:
    fail(f"atteso SALDATO, ricevuto stato={c['stato_pagamento']}, versato={c['totale_versato']}")


# ════════════════════════════════════════════════════════════
# TEST 19: PUT rate SALDATE -> 400
# ════════════════════════════════════════════════════════════
print("\n=== TEST 19: PUT rata SALDATA -> 400 ===")
r = requests.put(f"{BASE}/rates/{rate_ids_a[0]}", json={"importo_previsto": 999}, headers=headers_a)
if r.status_code == 400:
    ok("400 — rata saldata immutabile")
else:
    fail(f"atteso 400, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 20: DELETE rata SALDATA -> 400
# ════════════════════════════════════════════════════════════
print("\n=== TEST 20: DELETE rata SALDATA -> 400 ===")
r = requests.delete(f"{BASE}/rates/{rate_ids_a[0]}", headers=headers_a)
if r.status_code == 400:
    ok("400 — rata saldata non eliminabile")
else:
    fail(f"atteso 400, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 21: PUT contratto legittimo (partial update)
# ════════════════════════════════════════════════════════════
print("\n=== TEST 21: PUT contratto legittimo ===")
r = requests.put(f"{BASE}/contracts/{contract_a['id']}", json={
    "tipo_pacchetto": "10 PT Premium",
    "note": "Aggiornato"
}, headers=headers_a)
if r.status_code == 200:
    u = r.json()
    if u["tipo_pacchetto"] == "10 PT Premium" and u["crediti_totali"] == 10:
        ok(f"tipo={u['tipo_pacchetto']}, crediti={u['crediti_totali']} (invariato)")
    else:
        fail(f"Dati inattesi: {u}")
else:
    fail(f"atteso 200, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 22: GET lista con filtri
# ════════════════════════════════════════════════════════════
print("\n=== TEST 22: GET /contracts con filtri ===")
r = requests.get(f"{BASE}/contracts", headers=headers_a)
total_a = r.json()["total"]
ok(f"Trainer A vede {total_a} contratti") if total_a >= 1 else fail(f"A vede {total_a}")

r = requests.get(f"{BASE}/contracts", headers=headers_b)
total_b = r.json()["total"]
ok(f"Trainer B vede {total_b} contratti") if total_b >= 1 else fail(f"B vede {total_b}")

# Isolamento: A non vede quelli di B
ids_a = [c["id"] for c in requests.get(f"{BASE}/contracts", headers=headers_a).json()["items"]]
ids_b = [c["id"] for c in requests.get(f"{BASE}/contracts", headers=headers_b).json()["items"]]
if contract_b["id"] not in ids_a and contract_a["id"] not in ids_b:
    ok("Isolamento multi-tenant verificato")
else:
    fail("Cross-tenant data leak!")


# ════════════════════════════════════════════════════════════
# TEST 23: GET rate con filtro stato
# ════════════════════════════════════════════════════════════
print("\n=== TEST 23: GET /rates con filtri ===")
r = requests.get(f"{BASE}/rates?id_contratto={contract_a['id']}&stato=SALDATA", headers=headers_a)
if r.status_code == 200:
    saldate = r.json()["total"]
    ok(f"{saldate} rate SALDATE per contratto A") if saldate == 4 else fail(f"saldate={saldate}")
else:
    fail(f"atteso 200, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 24: No auth -> 401/403
# ════════════════════════════════════════════════════════════
print("\n=== TEST 24: No auth ===")
r = requests.get(f"{BASE}/contracts")
ok("no auth -> 401/403") if r.status_code in (401, 403) else fail(f"no auth: {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 25: DELETE contratto legittimo (CASCADE rate)
# ════════════════════════════════════════════════════════════
print("\n=== TEST 25: DELETE contratto legittimo (CASCADE) ===")
r = requests.delete(f"{BASE}/contracts/{contract_b['id']}", headers=headers_b)
if r.status_code == 204:
    ok(f"Contratto {contract_b['id']} eliminato")
else:
    fail(f"atteso 204, ricevuto {r.status_code}")

r = requests.get(f"{BASE}/contracts/{contract_b['id']}", headers=headers_b)
ok("GET dopo DELETE -> 404") if r.status_code == 404 else fail(f"ancora presente: {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 26: Verifica CashMovement acconto creato
# ════════════════════════════════════════════════════════════
print("\n=== TEST 26: CashMovement acconto ===")
# Creo un contratto fresco con acconto per testare il ledger
r = requests.post(f"{BASE}/contracts", json={
    "id_cliente": client_a["id"],
    "tipo_pacchetto": "Ledger Test",
    "crediti_totali": 5,
    "prezzo_totale": 300,
    "data_inizio": "2026-03-01",
    "data_scadenza": "2026-06-01",
    "acconto": 50,
    "metodo_acconto": "CONTANTI",
}, headers=headers_a)
if r.status_code == 201:
    ledger_contract = r.json()
    # Verifico che esiste un movimento cassa per l'acconto
    import sqlite3
    conn = sqlite3.connect("data/crm.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM movimenti_cassa WHERE id_contratto = ? AND categoria = 'ACCONTO_CONTRATTO'",
        (ledger_contract["id"],)
    )
    mov = cur.fetchone()
    if mov and mov["importo"] == 50 and mov["tipo"] == "ENTRATA" and mov["metodo"] == "CONTANTI":
        ok(f"CashMovement acconto creato: {mov['importo']}€ {mov['metodo']} ({mov['categoria']})")
    else:
        fail(f"CashMovement acconto non trovato o errato: {dict(mov) if mov else 'None'}")
    conn.close()
else:
    fail(f"atteso 201, ricevuto {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 27: Verifica CashMovement pagamento rata
# ════════════════════════════════════════════════════════════
print("\n=== TEST 27: CashMovement pagamento rata ===")
# Genero una rata e la pago
r = requests.post(f"{BASE}/rates/generate-plan/{ledger_contract['id']}", json={
    "importo_da_rateizzare": 250,
    "numero_rate": 2,
    "data_prima_rata": "2026-04-01",
}, headers=headers_a)
if r.status_code == 201:
    ledger_rates = r.json()["items"]
    # Pago la prima rata
    r = requests.post(f"{BASE}/rates/{ledger_rates[0]['id']}/pay", json={
        "importo": 125, "metodo": "BONIFICO", "note": "Test ledger"
    }, headers=headers_a)
    if r.status_code == 200:
        conn = sqlite3.connect("data/crm.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM movimenti_cassa WHERE id_rata = ? AND categoria = 'PAGAMENTO_RATA'",
            (ledger_rates[0]["id"],)
        )
        mov = cur.fetchone()
        if mov and mov["importo"] == 125 and mov["tipo"] == "ENTRATA" and mov["metodo"] == "BONIFICO":
            ok(f"CashMovement rata creato: {mov['importo']}€ {mov['metodo']} (rata #{mov['id_rata']})")
        else:
            fail(f"CashMovement rata non trovato: {dict(mov) if mov else 'None'}")

        # Verifico che id_contratto e id_cliente sono collegati
        if mov and mov["id_contratto"] == ledger_contract["id"] and mov["id_cliente"] == client_a["id"]:
            ok(f"CashMovement linkato: contratto={mov['id_contratto']}, cliente={mov['id_cliente']}")
        else:
            fail("CashMovement non linkato correttamente")
        conn.close()
    else:
        fail(f"pagamento fallito: {r.status_code}")
else:
    fail(f"piano rate fallito: {r.status_code}")


# ════════════════════════════════════════════════════════════
# TEST 28: Rounding — il centesimo non si perde
# ════════════════════════════════════════════════════════════
print("\n=== TEST 28: Rounding corretto (centesimo perduto) ===")
# 100€ / 3 rate -> 33.34 + 33.33 + 33.33 = 100.00
r = requests.post(f"{BASE}/rates/generate-plan/{ledger_contract['id']}", json={
    "importo_da_rateizzare": 100,
    "numero_rate": 3,
    "data_prima_rata": "2026-05-01",
}, headers=headers_a)
if r.status_code == 201:
    rounding_rates = r.json()["items"]
    amounts = [rt["importo_previsto"] for rt in rounding_rates]
    total_sum = sum(amounts)
    if abs(total_sum - 100.0) < 0.001:
        ok(f"Somma rate = {total_sum} (rate: {amounts})")
    else:
        fail(f"Somma rate = {total_sum} != 100.00 (rate: {amounts})")
    # La prima rata deve avere il resto
    if amounts[0] > amounts[1]:
        ok(f"Resto sulla prima rata: {amounts[0]} > {amounts[1]}")
    else:
        fail(f"Resto non sulla prima rata: {amounts}")
else:
    fail(f"piano rate fallito: {r.status_code}")


# ════════════════════════════════════════════════════════════
# CLEANUP
# ════════════════════════════════════════════════════════════
# Pulisci movimenti cassa creati dal test
import sqlite3
conn = sqlite3.connect("data/crm.db")
cur = conn.cursor()
if 'ledger_contract' in dir():
    cur.execute("DELETE FROM movimenti_cassa WHERE id_contratto = ?", (ledger_contract["id"],))
    conn.commit()
conn.close()

requests.delete(f"{BASE}/contracts/{contract_a['id']}", headers=headers_a)
if 'ledger_contract' in dir():
    requests.delete(f"{BASE}/contracts/{ledger_contract['id']}", headers=headers_a)
requests.delete(f"{BASE}/clients/{client_a['id']}", headers=headers_a)
requests.delete(f"{BASE}/clients/{client_b['id']}", headers=headers_b)


# ════════════════════════════════════════════════════════════
# RISULTATO
# ════════════════════════════════════════════════════════════
print(f"\n{'='*50}")
print(f"  RISULTATO: {passed} passati, {failed} falliti")
print(f"{'='*50}")
sys.exit(0 if failed == 0 else 1)
