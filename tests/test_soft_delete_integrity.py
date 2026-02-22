"""Test integrita' soft delete — nessuna corruzione contabile."""


def test_soft_deleted_movement_not_in_list(client, auth_headers):
    """Movimento soft-deleted non appare in GET /movements."""
    # Crea movimento manuale
    r = client.post("/api/movements", json={
        "importo": 100.0,
        "tipo": "USCITA",
        "categoria": "AFFITTO",
        "data_effettiva": "2026-03-15",
    }, headers=auth_headers)
    assert r.status_code == 201
    mov_id = r.json()["id"]

    # Elimina (soft delete)
    dr = client.delete(f"/api/movements/{mov_id}", headers=auth_headers)
    assert dr.status_code == 204

    # Non appare in lista
    mr = client.get("/api/movements?anno=2026&mese=3", headers=auth_headers)
    ids = [m["id"] for m in mr.json()["items"]]
    assert mov_id not in ids


def test_soft_deleted_movements_excluded_from_stats(client, auth_headers):
    """Stats mensili non contano movimenti soft-deleted."""
    # Crea 2 movimenti
    for _ in range(2):
        client.post("/api/movements", json={
            "importo": 100.0,
            "tipo": "USCITA",
            "categoria": "AFFITTO",
            "data_effettiva": "2026-04-10",
        }, headers=auth_headers)

    # Prendi stats baseline
    sr1 = client.get("/api/movements/stats?anno=2026&mese=4", headers=auth_headers)
    baseline = sr1.json()["totale_uscite_variabili"]

    # Elimina un movimento
    mr = client.get("/api/movements?anno=2026&mese=4", headers=auth_headers)
    first_id = mr.json()["items"][0]["id"]
    client.delete(f"/api/movements/{first_id}", headers=auth_headers)

    # Stats deve riflettere solo il superstite
    sr2 = client.get("/api/movements/stats?anno=2026&mese=4", headers=auth_headers)
    assert sr2.json()["totale_uscite_variabili"] == baseline - 100.0


def test_delete_contract_cascades_to_rates(client, auth_headers, sample_contract_with_plan):
    """Delete contratto -> soft-delete rate associate."""
    contract = sample_contract_with_plan["contract"]
    rates = sample_contract_with_plan["rates"]

    dr = client.delete(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert dr.status_code == 204

    # Rate non accessibili
    for rate in rates:
        rr = client.get(f"/api/rates/{rate['id']}", headers=auth_headers)
        assert rr.status_code == 404


def test_delete_client_blocked_if_active_contracts(client, auth_headers, sample_contract):
    """Delete cliente bloccato se ha contratti attivi (non eliminati)."""
    client_id = sample_contract["id_cliente"]

    r = client.delete(f"/api/clients/{client_id}", headers=auth_headers)
    # Deve essere bloccato (400 o 409)
    assert r.status_code in (400, 409)


def test_delete_client_ok_without_contracts(client, auth_headers):
    """Delete cliente senza contratti -> 204."""
    # Crea cliente senza contratti
    r = client.post("/api/clients", json={
        "nome": "Solo",
        "cognome": "Niente",
    }, headers=auth_headers)
    assert r.status_code == 201
    client_id = r.json()["id"]

    dr = client.delete(f"/api/clients/{client_id}", headers=auth_headers)
    assert dr.status_code == 204
