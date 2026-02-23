"""Test rate guards — modifica flessibile rate pagate + validazione residuo."""


# ── Guard: rate pagate — modifica consentita con vincoli ──


def test_update_parziale_rate_safe_fields_ok(client, auth_headers, sample_contract):
    """Modifica data_scadenza e descrizione su rata PARZIALE → 200."""
    rr = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 200.0,
    }, headers=auth_headers)
    assert rr.status_code == 201
    rate = rr.json()

    # Paga parzialmente (50 su 200)
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 50.0,
        "metodo": "CONTANTI",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)

    # Modifica data e descrizione → OK
    r = client.put(f"/api/rates/{rate['id']}", json={
        "data_scadenza": "2026-06-01",
        "descrizione": "Rata corretta",
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data_scadenza"] == "2026-06-01"
    assert r.json()["descrizione"] == "Rata corretta"


def test_update_parziale_importo_below_saldato_blocked(client, auth_headers, sample_contract):
    """Ridurre importo sotto il versato → 422."""
    rr = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 200.0,
    }, headers=auth_headers)
    rate = rr.json()

    # Paga 50
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 50.0,
        "metodo": "CONTANTI",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)

    # Ridurre a 30 (< 50 versato) → bloccato
    r = client.put(f"/api/rates/{rate['id']}", json={
        "importo_previsto": 30.0,
    }, headers=auth_headers)
    assert r.status_code == 422
    assert "versato" in r.json()["detail"].lower()


def test_update_saldata_rate_date_ok(client, auth_headers, sample_contract):
    """Modifica data_scadenza su rata SALDATA → 200."""
    rr = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 100.0,
    }, headers=auth_headers)
    rate = rr.json()

    # Paga completamente
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 100.0,
        "metodo": "POS",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)

    # Modifica data → OK
    r = client.put(f"/api/rates/{rate['id']}", json={
        "data_scadenza": "2026-06-01",
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data_scadenza"] == "2026-06-01"


def test_update_saldata_increase_importo_becomes_parziale(client, auth_headers, sample_contract):
    """Aumentare importo su rata SALDATA → diventa PARZIALE."""
    rr = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 100.0,
    }, headers=auth_headers)
    rate = rr.json()

    # Paga completamente (100)
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 100.0,
        "metodo": "POS",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)

    # Aumenta previsto a 200 → stato diventa PARZIALE
    r = client.put(f"/api/rates/{rate['id']}", json={
        "importo_previsto": 200.0,
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["stato"] == "PARZIALE"
    assert r.json()["importo_previsto"] == 200.0


# ── Guard: rate con pagamenti non eliminabili ──


def test_delete_parziale_rate_blocked(client, auth_headers, sample_contract):
    """Delete rata PARZIALE (ha pagamenti) → 400."""
    rr = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-04-01",
        "importo_previsto": 200.0,
    }, headers=auth_headers)
    assert rr.status_code == 201
    rate = rr.json()

    # Paga parzialmente
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 50.0,
        "metodo": "CONTANTI",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)

    # Tentativo delete → bloccato
    r = client.delete(f"/api/rates/{rate['id']}", headers=auth_headers)
    assert r.status_code == 400
    assert "pagamenti" in r.json()["detail"].lower()


def test_delete_pendente_rate_ok(client, auth_headers, sample_contract):
    """Delete rata PENDENTE (zero pagamenti) → 204."""
    rr = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-05-01",
        "importo_previsto": 100.0,
    }, headers=auth_headers)
    assert rr.status_code == 201
    rate = rr.json()

    r = client.delete(f"/api/rates/{rate['id']}", headers=auth_headers)
    assert r.status_code == 204


# ── Flusso corretto: unpay → poi modifica/delete ──


def test_unpay_then_update_ok(client, auth_headers, sample_contract):
    """Revoca pagamento → rata torna PENDENTE → modifica OK."""
    rr = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-06-01",
        "importo_previsto": 200.0,
    }, headers=auth_headers)
    rate = rr.json()

    # Paga parzialmente
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 50.0,
        "metodo": "CONTANTI",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)

    # Revoca → torna PENDENTE
    ur = client.post(f"/api/rates/{rate['id']}/unpay", headers=auth_headers)
    assert ur.status_code == 200
    assert ur.json()["stato"] == "PENDENTE"

    # Ora modifica → OK
    r = client.put(f"/api/rates/{rate['id']}", json={
        "importo_previsto": 150.0,
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["importo_previsto"] == 150.0


def test_unpay_then_delete_ok(client, auth_headers, sample_contract):
    """Revoca pagamento → rata torna PENDENTE → delete OK."""
    rr = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-07-01",
        "importo_previsto": 100.0,
    }, headers=auth_headers)
    rate = rr.json()

    # Paga completamente
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 100.0,
        "metodo": "POS",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)

    # Revoca → torna PENDENTE
    client.post(f"/api/rates/{rate['id']}/unpay", headers=auth_headers)

    # Ora delete → OK
    r = client.delete(f"/api/rates/{rate['id']}", headers=auth_headers)
    assert r.status_code == 204


# ── Validazione residuo su update importo_previsto ──


def test_update_importo_exceeding_residual_rejected(client, auth_headers, sample_contract):
    """Modifica importo_previsto che eccede residuo rateizzabile → 422."""
    # sample_contract: prezzo=1000, acconto=200 → cap = 800
    # Crea rata da 500
    rr = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 500.0,
    }, headers=auth_headers)
    assert rr.status_code == 201
    rate = rr.json()

    # Modifica a 801 → eccede cap (800)
    r = client.put(f"/api/rates/{rate['id']}", json={
        "importo_previsto": 801.0,
    }, headers=auth_headers)
    assert r.status_code == 422
    assert "residuo" in r.json()["detail"].lower()


def test_update_importo_within_residual_ok(client, auth_headers, sample_contract):
    """Modifica importo_previsto entro il residuo → 200."""
    rr = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 200.0,
    }, headers=auth_headers)
    assert rr.status_code == 201
    rate = rr.json()

    # Modifica a 800 → esattamente il cap
    r = client.put(f"/api/rates/{rate['id']}", json={
        "importo_previsto": 800.0,
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["importo_previsto"] == 800.0


def test_update_importo_with_other_rates(client, auth_headers, sample_contract):
    """Modifica importo con altre rate presenti → controlla residuo globale."""
    # Crea 2 rate: 400 + 300 = 700 (cap = 800, spazio = 100)
    r1 = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 400.0,
    }, headers=auth_headers)
    rate1 = r1.json()

    client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-04-01",
        "importo_previsto": 300.0,
    }, headers=auth_headers)

    # Modifica rate1 da 400 a 501 → 501 + 300 = 801 > 800
    r = client.put(f"/api/rates/{rate1['id']}", json={
        "importo_previsto": 501.0,
    }, headers=auth_headers)
    assert r.status_code == 422

    # Modifica rate1 da 400 a 500 → 500 + 300 = 800 = cap → OK
    r = client.put(f"/api/rates/{rate1['id']}", json={
        "importo_previsto": 500.0,
    }, headers=auth_headers)
    assert r.status_code == 200
