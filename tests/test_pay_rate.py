"""Test pagamento rata — transazione atomica su 3 tabelle."""


def test_pay_full_rate(client, auth_headers, sample_contract_with_plan):
    """Pagamento totale: rata diventa SALDATA, contratto aggiornato."""
    rate = sample_contract_with_plan["rates"][0]

    r = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": rate["importo_previsto"],
        "metodo": "POS",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)
    assert r.status_code == 200

    paid = r.json()
    assert paid["stato"] == "SALDATA"
    assert paid["importo_saldato"] == rate["importo_previsto"]


def test_pay_partial_rate(client, auth_headers, sample_contract_with_plan):
    """Pagamento parziale: rata diventa PARZIALE."""
    rate = sample_contract_with_plan["rates"][0]

    r = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 50.0,
        "metodo": "CONTANTI",
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["stato"] == "PARZIALE"
    assert r.json()["importo_saldato"] == 50.0


def test_pay_rate_updates_contract_totale_versato(client, auth_headers, sample_contract_with_plan):
    """totale_versato del contratto incrementa dopo pagamento."""
    rate = sample_contract_with_plan["rates"][0]
    contract = sample_contract_with_plan["contract"]

    # totale_versato parte da 200 (acconto)
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": rate["importo_previsto"],
        "metodo": "POS",
    }, headers=auth_headers)

    # Rileggi contratto
    cr = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert cr.json()["totale_versato"] == 200.0 + rate["importo_previsto"]


def test_pay_rate_creates_cash_movement(client, auth_headers, sample_contract_with_plan):
    """Pagamento crea un CashMovement ENTRATA."""
    rate = sample_contract_with_plan["rates"][0]

    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 200.0,
        "metodo": "BONIFICO",
    }, headers=auth_headers)

    # Verifica movimenti
    mr = client.get("/api/movements?anno=2026&mese=2", headers=auth_headers)
    payments = [
        m for m in mr.json()["items"]
        if m.get("id_rata") == rate["id"]
    ]
    assert len(payments) == 1
    assert payments[0]["tipo"] == "ENTRATA"
    assert payments[0]["importo"] == 200.0
    assert payments[0]["metodo"] == "BONIFICO"


def test_pay_already_paid_returns_400(client, auth_headers, sample_contract_with_plan):
    """Doppio pagamento su rata SALDATA -> 400."""
    rate = sample_contract_with_plan["rates"][0]

    # Primo pagamento
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": rate["importo_previsto"],
        "metodo": "POS",
    }, headers=auth_headers)

    # Secondo pagamento -> 400
    r = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 1.0,
        "metodo": "CONTANTI",
    }, headers=auth_headers)
    assert r.status_code == 400


def test_pay_all_rates_completes_contract(client, auth_headers, sample_contract_with_plan):
    """Tutte le rate pagate -> contratto SALDATO."""
    contract = sample_contract_with_plan["contract"]
    rates = sample_contract_with_plan["rates"]

    for rate in rates:
        r = client.post(f"/api/rates/{rate['id']}/pay", json={
            "importo": rate["importo_previsto"],
            "metodo": "POS",
        }, headers=auth_headers)
        assert r.status_code == 200

    cr = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert cr.json()["stato_pagamento"] == "SALDATO"


def test_pay_rate_deep_idor(client, auth_headers, sample_contract_with_plan):
    """Trainer non autorizzato non puo' pagare rata altrui -> 404."""
    rate = sample_contract_with_plan["rates"][0]

    # Registra secondo trainer
    r = client.post("/api/auth/register", json={
        "email": "evil@test.com",
        "nome": "Evil",
        "cognome": "Trainer",
        "password": "evilpass123",
    })
    evil_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 100.0,
        "metodo": "CONTANTI",
    }, headers=evil_headers)
    assert r.status_code == 404


def test_overpayment_rejected(client, auth_headers, sample_contract_with_plan):
    """Pagamento superiore al residuo della rata -> 422."""
    rate = sample_contract_with_plan["rates"][0]

    r = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": rate["importo_previsto"] + 100,
        "metodo": "CONTANTI",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)
    assert r.status_code == 422


def test_overpayment_after_partial_rejected(client, auth_headers, sample_contract_with_plan):
    """Pagamento parziale + secondo che supera residuo -> 422."""
    rate = sample_contract_with_plan["rates"][0]
    previsto = rate["importo_previsto"]

    r1 = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": previsto / 2,
        "metodo": "CONTANTI",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)
    assert r1.status_code == 200
    assert r1.json()["stato"] == "PARZIALE"

    r2 = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": previsto,
        "metodo": "CONTANTI",
        "data_pagamento": "2026-02-02",
    }, headers=auth_headers)
    assert r2.status_code == 422


def test_exact_residual_payment_accepted(client, auth_headers, sample_contract_with_plan):
    """Pagamento esatto del residuo dopo parziale -> SALDATA."""
    rate = sample_contract_with_plan["rates"][0]
    previsto = rate["importo_previsto"]

    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": previsto / 2,
        "metodo": "CONTANTI",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)

    r = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": previsto / 2,
        "metodo": "CONTANTI",
        "data_pagamento": "2026-02-02",
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["stato"] == "SALDATA"
