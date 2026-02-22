"""Test revoca pagamento — revert atomico su 3 tabelle."""


def _pay_first_rate(client, auth_headers, plan):
    """Helper: paga la prima rata e ritorna la risposta."""
    rate = plan["rates"][0]
    r = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": rate["importo_previsto"],
        "metodo": "POS",
    }, headers=auth_headers)
    assert r.status_code == 200
    return rate


def test_unpay_reverts_to_pendente(client, auth_headers, sample_contract_with_plan):
    """Revoca: rata torna PENDENTE."""
    rate = _pay_first_rate(client, auth_headers, sample_contract_with_plan)

    r = client.post(f"/api/rates/{rate['id']}/unpay", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["stato"] == "PENDENTE"
    assert r.json()["importo_saldato"] == 0


def test_unpay_decrements_contract_totale(client, auth_headers, sample_contract_with_plan):
    """totale_versato del contratto decrementa dopo revoca."""
    rate = _pay_first_rate(client, auth_headers, sample_contract_with_plan)
    contract = sample_contract_with_plan["contract"]

    client.post(f"/api/rates/{rate['id']}/unpay", headers=auth_headers)

    cr = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    # Torna all'acconto originale (200)
    assert cr.json()["totale_versato"] == 200.0


def test_unpay_soft_deletes_cash_movement(client, auth_headers, sample_contract_with_plan):
    """Revoca: il CashMovement viene soft-deleted (non sparisce dal DB)."""
    rate = _pay_first_rate(client, auth_headers, sample_contract_with_plan)

    client.post(f"/api/rates/{rate['id']}/unpay", headers=auth_headers)

    # Il movimento non appare piu' nella lista (filtrata per deleted_at)
    mr = client.get("/api/movements?anno=2026&mese=2", headers=auth_headers)
    payment_movs = [
        m for m in mr.json()["items"]
        if m.get("id_rata") == rate["id"]
    ]
    assert len(payment_movs) == 0


def test_unpay_pendente_returns_400(client, auth_headers, sample_contract_with_plan):
    """Revoca su rata PENDENTE -> 400."""
    rate = sample_contract_with_plan["rates"][0]

    r = client.post(f"/api/rates/{rate['id']}/unpay", headers=auth_headers)
    assert r.status_code == 400
