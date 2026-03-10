"""
E2E Business Rehearsal — Step 4 Launch Hardening
Validates the 3 critical revenue & trust flows against a live dev backend.

Flow 1: Client -> Contract -> Rate -> Pay/Unpay -> Ledger
Flow 2: Agenda -> Credit consumption -> Contract state
Flow 3: Backup -> Mutate -> Restore

Usage: python -m tools.admin_scripts.e2e_business_rehearsal [--base-url URL]
"""

import argparse
import sys
import time
from datetime import date, timedelta

import requests

_BASE_URL = "http://localhost:8001"
PASS = 0
FAIL = 0


def _set_base_url(url: str):
    global _BASE_URL
    _BASE_URL = url


def _url(path: str) -> str:
    return f"{_BASE_URL}{path}"


def _log(ok: bool, label: str, detail: str = ""):
    global PASS, FAIL
    tag = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    suffix = f" — {detail}" if detail else ""
    print(f"  [{tag}] {label}{suffix}")


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Setup: register a fresh trainer ──────────────────────────────────────────

def setup_trainer() -> str:
    """Register a test trainer and return JWT token."""
    email = f"e2e-rehearsal-{int(time.time())}@test.com"
    r = requests.post(f"{_BASE_URL}/api/auth/register", json={
        "email": email,
        "nome": "E2E",
        "cognome": "Rehearsal",
        "password": "TestPass123!",
    })
    if r.status_code != 201:
        print(f"  [FAIL] Register trainer — {r.status_code}: {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    print(f"  [PASS] Trainer registered: {email}")
    return token


# ── Flow 1: Client -> Contract -> Rate -> Pay/Unpay -> Ledger ──────────────────

def flow_1_revenue(token: str):
    print("\n=== Flow 1: Client -> Contract -> Rate -> Pay/Unpay -> Ledger ===")
    h = _auth_headers(token)
    today = date.today()

    # 1. Create client
    r = requests.post(f"{_BASE_URL}/api/clients", json={
        "nome": "Marco", "cognome": "Rossi",
    }, headers=h)
    _log(r.status_code == 201, "Create client", f"status={r.status_code}")
    client_id = r.json()["id"]

    # 2. Create contract
    r = requests.post(f"{_BASE_URL}/api/contracts", json={
        "id_cliente": client_id,
        "tipo_pacchetto": "Gold 10",
        "crediti_totali": 10,
        "prezzo_totale": 500.0,
        "data_inizio": today.isoformat(),
        "data_scadenza": (today + timedelta(days=90)).isoformat(),
        "acconto": 0.0,
    }, headers=h)
    _log(r.status_code == 201, "Create contract", f"status={r.status_code}")
    contract_id = r.json()["id"]

    # 3. Generate payment plan (2 rates)
    r = requests.post(f"{_BASE_URL}/api/rates/generate-plan/{contract_id}", json={
        "importo_da_rateizzare": 500.0,
        "numero_rate": 2,
        "data_prima_rata": (today + timedelta(days=7)).isoformat(),
        "frequenza": "MENSILE",
    }, headers=h)
    _log(r.status_code == 201, "Generate payment plan", f"status={r.status_code}")
    rates = r.json()["items"]
    rate_1_id = rates[0]["id"]
    rate_2_id = rates[1]["id"]

    # 4. Pay first rate
    r = requests.post(f"{_BASE_URL}/api/rates/{rate_1_id}/pay", json={
        "importo": 250.0,
        "metodo": "BONIFICO",
    }, headers=h)
    _log(r.status_code == 200, "Pay rate 1", f"status={r.status_code}")

    # 5. Verify ledger has the movement
    r = requests.get(f"{_BASE_URL}/api/movements", headers=h)
    movements = r.json()["items"]
    paid_movements = [m for m in movements if m.get("id_rata") == rate_1_id]
    _log(len(paid_movements) >= 1, "Ledger has payment movement", f"found={len(paid_movements)}")

    # 6. Verify cash balance
    r = requests.get(f"{_BASE_URL}/api/movements/balance", headers=h)
    _log(r.status_code == 200, "Cash balance endpoint", f"status={r.status_code}")
    balance = r.json()
    _log(balance["saldo_attuale"] >= 250.0, "Balance reflects payment", f"saldo={balance['saldo_attuale']}")

    # 7. Unpay the rate
    r = requests.post(f"{_BASE_URL}/api/rates/{rate_1_id}/unpay", headers=h)
    _log(r.status_code == 200, "Unpay rate 1", f"status={r.status_code}")

    # 8. Verify ledger movement soft-deleted
    r = requests.get(f"{_BASE_URL}/api/movements", headers=h)
    movements_after = r.json()["items"]
    paid_after = [m for m in movements_after if m.get("id_rata") == rate_1_id]
    _log(len(paid_after) == 0, "Ledger movement removed after unpay", f"found={len(paid_after)}")

    # 9. Verify balance reverted
    r = requests.get(f"{_BASE_URL}/api/movements/balance", headers=h)
    balance_after = r.json()
    _log(balance_after["saldo_attuale"] < balance["saldo_attuale"], "Balance reverted after unpay",
         f"before={balance['saldo_attuale']}, after={balance_after['saldo_attuale']}")

    # 10. Re-pay for flow 2
    r = requests.post(f"{_BASE_URL}/api/rates/{rate_1_id}/pay", json={
        "importo": 250.0,
        "metodo": "CONTANTI",
    }, headers=h)
    _log(r.status_code == 200, "Re-pay rate 1 for flow 2", f"status={r.status_code}")

    return client_id, contract_id, rate_2_id


# ── Flow 2: Agenda -> Credit consumption -> Contract state ────────────────────

def flow_2_agenda(token: str, client_id: int, contract_id: int, rate_2_id: int):
    print("\n=== Flow 2: Agenda -> Credit Consumption -> Contract State ===")
    h = _auth_headers(token)
    today = date.today()

    # 1. Create PT event consuming a credit
    start = f"{today.isoformat()}T10:00:00"
    end = f"{today.isoformat()}T11:00:00"
    r = requests.post(f"{_BASE_URL}/api/events", json={
        "titolo": "PT Marco Rossi",
        "data_inizio": start,
        "data_fine": end,
        "categoria": "PT",
        "id_cliente": client_id,
        "id_contratto": contract_id,
    }, headers=h)
    _log(r.status_code == 201, "Create PT event", f"status={r.status_code}")
    event_id = r.json()["id"]

    # 2. Verify credit consumed
    r = requests.get(f"{_BASE_URL}/api/contracts/{contract_id}", headers=h)
    contract = r.json()
    _log(contract["crediti_usati"] == 1, "Credit consumed", f"crediti_usati={contract['crediti_usati']}")
    _log(contract["chiuso"] is False, "Contract still open", f"chiuso={contract['chiuso']}")

    # 3. Create more events to consume all credits
    event_ids = [event_id]
    for i in range(9):  # 9 more = 10 total
        day = today + timedelta(days=i + 1)
        s = f"{day.isoformat()}T10:00:00"
        e = f"{day.isoformat()}T11:00:00"
        r = requests.post(f"{_BASE_URL}/api/events", json={
            "titolo": f"PT #{i+2}",
            "data_inizio": s,
            "data_fine": e,
            "categoria": "PT",
            "id_cliente": client_id,
            "id_contratto": contract_id,
        }, headers=h)
        if r.status_code == 201:
            event_ids.append(r.json()["id"])
        else:
            _log(False, f"Create PT event #{i+2}", f"status={r.status_code}: {r.text[:100]}")
            break

    # 4. Verify all credits consumed
    r = requests.get(f"{_BASE_URL}/api/contracts/{contract_id}", headers=h)
    contract = r.json()
    _log(contract["crediti_usati"] == 10, "All 10 credits consumed", f"crediti_usati={contract['crediti_usati']}")

    # 5. Try to create event beyond credits — should fail
    day = today + timedelta(days=20)
    r = requests.post(f"{_BASE_URL}/api/events", json={
        "titolo": "PT extra",
        "data_inizio": f"{day.isoformat()}T10:00:00",
        "data_fine": f"{day.isoformat()}T11:00:00",
        "categoria": "PT",
        "id_cliente": client_id,
        "id_contratto": contract_id,
    }, headers=h)
    _log(r.status_code == 400, "Credit exhaustion guard", f"status={r.status_code}")

    # 6. Pay second rate to make contract SALDATO
    r = requests.post(f"{_BASE_URL}/api/rates/{rate_2_id}/pay", json={
        "importo": 250.0,
        "metodo": "BONIFICO",
    }, headers=h)
    _log(r.status_code == 200, "Pay rate 2", f"status={r.status_code}")

    # 7. Verify auto-close: SALDATO + all credits used -> chiuso=True
    r = requests.get(f"{_BASE_URL}/api/contracts/{contract_id}", headers=h)
    contract = r.json()
    _log(contract["stato_pagamento"] == "SALDATO", "Contract SALDATO",
         f"stato={contract['stato_pagamento']}")
    _log(contract["chiuso"] is True, "Contract auto-closed",
         f"chiuso={contract['chiuso']}")

    # 8. Delete an event -> auto-reopen (crediti_usati drops below total)
    r = requests.delete(f"{_BASE_URL}/api/events/{event_ids[-1]}", headers=h)
    _log(r.status_code == 200 or r.status_code == 204, "Delete last event", f"status={r.status_code}")

    r = requests.get(f"{_BASE_URL}/api/contracts/{contract_id}", headers=h)
    contract = r.json()
    _log(contract["chiuso"] is False, "Contract auto-reopened after event delete",
         f"chiuso={contract['chiuso']}, crediti_usati={contract['crediti_usati']}")

    return event_ids


# ── Flow 3: Backup -> Mutate -> Restore ───────────────────────────────────────

def flow_3_backup(token: str, client_id: int):
    print("\n=== Flow 3: Backup -> Mutate -> Restore ===")
    h = _auth_headers(token)

    # 1. Create backup
    r = requests.post(f"{_BASE_URL}/api/backup/create", headers=h)
    _log(r.status_code == 200, "Create backup", f"status={r.status_code}")
    backup_filename = r.json().get("filename", "")
    _log(len(backup_filename) > 0, "Backup filename returned", f"file={backup_filename}")

    # 2. Verify backup in list
    r = requests.get(f"{_BASE_URL}/api/backup/list", headers=h)
    _log(r.status_code == 200, "List backups", f"status={r.status_code}")
    backups = r.json() if isinstance(r.json(), list) else r.json().get("backups", [])
    found = any((b.get("filename") if isinstance(b, dict) else b) == backup_filename for b in backups)
    _log(found, "Backup appears in list")

    # 3. Verify backup integrity
    r = requests.post(f"{_BASE_URL}/api/backup/verify/{backup_filename}", headers=h)
    _log(r.status_code == 200, "Verify backup integrity", f"status={r.status_code}")
    verification = r.json()
    _log(verification.get("integrity_ok") is True, "Integrity check passed")
    _log(verification.get("checksum_match") is True, "Checksum check passed")

    # 4. Mutate: update client name
    r = requests.put(f"{_BASE_URL}/api/clients/{client_id}", json={
        "nome": "MUTATED",
        "cognome": "CLIENT",
    }, headers=h)
    _log(r.status_code == 200, "Mutate client name", f"status={r.status_code}")

    # 5. Verify mutation
    r = requests.get(f"{_BASE_URL}/api/clients/{client_id}", headers=h)
    _log(r.json()["nome"] == "MUTATED", "Mutation verified")

    # 6. Download backup for restore
    r = requests.get(f"{_BASE_URL}/api/backup/download/{backup_filename}", headers=h)
    _log(r.status_code == 200, "Download backup", f"size={len(r.content)} bytes")
    backup_data = r.content

    # 7. Restore from backup
    r = requests.post(
        f"{_BASE_URL}/api/backup/restore",
        files={"file": (backup_filename, backup_data, "application/octet-stream")},
        headers=h,
    )
    _log(r.status_code == 200, "Restore from backup", f"status={r.status_code}")

    # 8. Re-authenticate (restore may change DB state)
    email = f"e2e-rehearsal-{int(time.time())}@test.com"
    # Use the original trainer — need to re-login since restore resets the DB
    # The original trainer was registered before backup, so it should exist
    # But JWT is still valid if secret hasn't changed
    r = requests.get(f"{_BASE_URL}/api/clients/{client_id}", headers=h)
    if r.status_code == 200:
        restored_name = r.json()["nome"]
        _log(restored_name == "Marco", "Client name restored to pre-mutation state",
             f"nome={restored_name}")
    else:
        _log(False, "Access client after restore", f"status={r.status_code}")

    # 9. Export JSON
    r = requests.get(f"{_BASE_URL}/api/backup/export", headers=h)
    _log(r.status_code == 200, "JSON export", f"status={r.status_code}")
    if r.status_code == 200:
        export = r.json()
        export_data = export.get("data", export)
        _log("clienti" in export_data, "Export contains clienti entity")
        _log("contratti" in export_data, "Export contains contratti entity")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="E2E Business Rehearsal")
    parser.add_argument("--base-url", default=_BASE_URL)
    args = parser.parse_args()

    _set_base_url(args.base_url)

    print(f"\n{'='*60}")
    print(f"  E2E Business Rehearsal — Step 4 Launch Hardening")
    print(f"  Target: {_BASE_URL}")
    print(f"{'='*60}")

    # Health check
    try:
        r = requests.get(f"{_BASE_URL}/health", timeout=5)
        if r.status_code != 200:
            print(f"\n  [FAIL] Backend not healthy: {r.status_code}")
            sys.exit(1)
        print(f"\n  [PASS] Backend healthy: {r.json()}")
    except requests.ConnectionError:
        print(f"\n  [FAIL] Cannot connect to {BASE_URL}")
        sys.exit(1)

    token = setup_trainer()
    client_id, contract_id, rate_2_id = flow_1_revenue(token)
    flow_2_agenda(token, client_id, contract_id, rate_2_id)
    flow_3_backup(token, client_id)

    print(f"\n{'='*60}")
    print(f"  Results: {PASS} PASS, {FAIL} FAIL")
    print(f"{'='*60}\n")

    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()
