# tools/admin_scripts/test_crud_idor.py
"""Test end-to-end: CRUD completo + IDOR prevention + Mass Assignment + validazione."""

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


# === SETUP: Registra 2 trainer ===
print("=== SETUP: Registrazione trainer ===")

r = requests.post(f"{BASE}/auth/register", json={
    "email": "trainerA@test.com", "password": "SecurePass1!",
    "nome": "Alice", "cognome": "Rossi"
})
if r.status_code == 201:
    token_a = r.json()["access_token"]
    trainer_a_id = r.json()["trainer_id"]
    print(f"  Trainer A registrato: id={trainer_a_id}")
elif r.status_code == 409:
    r = requests.post(f"{BASE}/auth/login", json={"email": "trainerA@test.com", "password": "SecurePass1!"})
    token_a = r.json()["access_token"]
    trainer_a_id = r.json()["trainer_id"]
    print(f"  Trainer A login: id={trainer_a_id}")

r = requests.post(f"{BASE}/auth/register", json={
    "email": "trainerB@test.com", "password": "SecurePass2!",
    "nome": "Bob", "cognome": "Bianchi"
})
if r.status_code == 201:
    token_b = r.json()["access_token"]
    trainer_b_id = r.json()["trainer_id"]
    print(f"  Trainer B registrato: id={trainer_b_id}")
elif r.status_code == 409:
    r = requests.post(f"{BASE}/auth/login", json={"email": "trainerB@test.com", "password": "SecurePass2!"})
    token_b = r.json()["access_token"]
    trainer_b_id = r.json()["trainer_id"]
    print(f"  Trainer B login: id={trainer_b_id}")

headers_a = {"Authorization": f"Bearer {token_a}"}
headers_b = {"Authorization": f"Bearer {token_b}"}


# === TEST 1: POST - Crea cliente per Trainer A ===
print("\n=== TEST 1: POST /clients (Trainer A) ===")
r = requests.post(f"{BASE}/clients", json={
    "nome": "Mario", "cognome": "Verdi",
    "email": "Mario@Test.com", "telefono": "+39 333 1234567",
    "sesso": "Uomo"
}, headers=headers_a)
if r.status_code == 201:
    client_a = r.json()
    ok(f"Creato id={client_a['id']}, email={client_a['email']} (lowercase)")
else:
    fail(f"atteso 201, ricevuto {r.status_code}")
    sys.exit(1)


# === TEST 2: POST - Crea cliente per Trainer B ===
print("\n=== TEST 2: POST /clients (Trainer B) ===")
r = requests.post(f"{BASE}/clients", json={
    "nome": "Laura", "cognome": "Neri"
}, headers=headers_b)
if r.status_code == 201:
    client_b = r.json()
    ok(f"Creato id={client_b['id']}, stato={client_b['stato']}")
else:
    fail(f"atteso 201, ricevuto {r.status_code}")
    sys.exit(1)


# === TEST 3: GET - Isolamento multi-tenant ===
print("\n=== TEST 3: GET /clients (isolamento multi-tenant) ===")
items_a = requests.get(f"{BASE}/clients", headers=headers_a).json()["items"]
items_b = requests.get(f"{BASE}/clients", headers=headers_b).json()["items"]
ids_a = [c["id"] for c in items_a]
ids_b = [c["id"] for c in items_b]
if client_b["id"] not in ids_a and client_a["id"] not in ids_b:
    ok(f"A vede {len(items_a)} clienti, B vede {len(items_b)} - nessun leak")
else:
    fail("Cross-tenant data leak!")


# === TEST 4: IDOR GET - Trainer B legge cliente di A ===
print("\n=== TEST 4: IDOR GET ===")
r = requests.get(f"{BASE}/clients/{client_a['id']}", headers=headers_b)
if r.status_code == 404:
    ok("404 (non 403) - info leakage prevenuto")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")


# === TEST 5: IDOR PUT - Trainer B modifica cliente di A ===
print("\n=== TEST 5: IDOR PUT ===")
r = requests.put(f"{BASE}/clients/{client_a['id']}", json={"nome": "HACKED"}, headers=headers_b)
if r.status_code == 404:
    ok("404 - modifica IDOR bloccata")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")

# Verifica dati intatti
r = requests.get(f"{BASE}/clients/{client_a['id']}", headers=headers_a)
if r.json()["nome"] == "Mario":
    ok(f"Dati originali intatti (nome={r.json()['nome']})")
else:
    fail(f"Nome cambiato a {r.json()['nome']}!")


# === TEST 6: IDOR DELETE - Trainer B cancella cliente di A ===
print("\n=== TEST 6: IDOR DELETE ===")
r = requests.delete(f"{BASE}/clients/{client_a['id']}", headers=headers_b)
if r.status_code == 404:
    ok("404 - cancellazione IDOR bloccata")
else:
    fail(f"atteso 404, ricevuto {r.status_code}")

r = requests.get(f"{BASE}/clients/{client_a['id']}", headers=headers_a)
if r.status_code == 200:
    ok("Cliente ancora presente dopo tentativo IDOR")
else:
    fail("Il cliente e' stato cancellato!")


# === TEST 7: PUT legittimo (partial update) ===
print("\n=== TEST 7: PUT legittimo (partial update) ===")
r = requests.put(f"{BASE}/clients/{client_a['id']}", json={
    "nome": "Marco", "stato": "Inattivo"
}, headers=headers_a)
if r.status_code == 200:
    u = r.json()
    if u["nome"] == "Marco" and u["cognome"] == "Verdi" and u["stato"] == "Inattivo":
        ok(f"nome={u['nome']}, cognome={u['cognome']} (invariato), stato={u['stato']}")
    else:
        fail(f"Dati inattesi: {u}")
else:
    fail(f"atteso 200, ricevuto {r.status_code}")


# === TEST 8: DELETE legittimo ===
print("\n=== TEST 8: DELETE legittimo ===")
r = requests.delete(f"{BASE}/clients/{client_b['id']}", headers=headers_b)
if r.status_code == 204:
    ok(f"id={client_b['id']} eliminato (204 No Content)")
else:
    fail(f"atteso 204, ricevuto {r.status_code}")

r = requests.get(f"{BASE}/clients/{client_b['id']}", headers=headers_b)
if r.status_code == 404:
    ok("GET dopo DELETE -> 404")
else:
    fail(f"Cliente ancora presente dopo DELETE: {r.status_code}")


# === TEST 9: Mass Assignment - trainer_id nel body ===
print("\n=== TEST 9: Mass Assignment prevention ===")
r = requests.post(f"{BASE}/clients", json={
    "nome": "Hack", "cognome": "Attempt",
    "trainer_id": trainer_a_id
}, headers=headers_b)
if r.status_code == 201:
    hack_id = r.json()["id"]
    r_b = requests.get(f"{BASE}/clients/{hack_id}", headers=headers_b)
    r_a = requests.get(f"{BASE}/clients/{hack_id}", headers=headers_a)
    if r_b.status_code == 200 and r_a.status_code == 404:
        ok("trainer_id ignorato - cliente nel namespace di B, invisibile ad A")
    else:
        fail(f"Leak! B={r_b.status_code}, A={r_a.status_code}")
    requests.delete(f"{BASE}/clients/{hack_id}", headers=headers_b)
else:
    fail(f"atteso 201, ricevuto {r.status_code}")


# === TEST 10: Validazione input ===
print("\n=== TEST 10: Validazione input ===")

r = requests.post(f"{BASE}/clients", json={"nome": "", "cognome": "Test"}, headers=headers_a)
ok("nome vuoto -> 422") if r.status_code == 422 else fail(f"nome vuoto: {r.status_code}")

r = requests.post(f"{BASE}/clients", json={"nome": "A", "cognome": "B", "email": "nope"}, headers=headers_a)
ok("email invalida -> 422") if r.status_code == 422 else fail(f"email: {r.status_code}")

r = requests.post(f"{BASE}/clients", json={"nome": "A", "cognome": "B", "sesso": "Boh"}, headers=headers_a)
ok("sesso invalido -> 422") if r.status_code == 422 else fail(f"sesso: {r.status_code}")

r = requests.get(f"{BASE}/clients/999999", headers=headers_a)
ok("ID inesistente -> 404") if r.status_code == 404 else fail(f"ID 999999: {r.status_code}")

r = requests.get(f"{BASE}/clients")
ok("no auth -> 401/403") if r.status_code in (401, 403) else fail(f"no auth: {r.status_code}")


# === Cleanup ===
requests.delete(f"{BASE}/clients/{client_a['id']}", headers=headers_a)


# === RISULTATO ===
print(f"\n{'='*50}")
print(f"  RISULTATO: {passed} passati, {failed} falliti")
print(f"{'='*50}")
sys.exit(0 if failed == 0 else 1)
