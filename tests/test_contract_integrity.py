"""Test integrità contratto — validazione residuo, chiuso guard, auto-close."""


# ── F1: Validazione residuo rate ──


def test_rate_exceeding_residual_rejected(client, auth_headers, sample_contract):
    """Rata con importo > residuo rateizzabile → 422."""
    # sample_contract: prezzo=1000, acconto=200 → residuo = 800
    r = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 801.0,
    }, headers=auth_headers)
    assert r.status_code == 422
    assert "residuo" in r.json()["detail"].lower()


def test_rate_exactly_at_residual_accepted(client, auth_headers, sample_contract):
    """Rata con importo = residuo rateizzabile → 201."""
    r = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 800.0,
    }, headers=auth_headers)
    assert r.status_code == 201


def test_second_rate_exceeds_residual(client, auth_headers, sample_contract):
    """Prima rata OK, seconda eccede il residuo → 422."""
    # Prima rata: 500 (residuo dopo = 300)
    r1 = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 500.0,
    }, headers=auth_headers)
    assert r1.status_code == 201

    # Seconda rata: 301 eccede il residuo di 300
    r2 = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-04-01",
        "importo_previsto": 301.0,
    }, headers=auth_headers)
    assert r2.status_code == 422


# ── F1+F2: Chiuso guard ──


def test_rate_on_closed_contract_rejected(client, auth_headers, sample_contract):
    """Rata su contratto chiuso → 400."""
    client.put(f"/api/contracts/{sample_contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)

    r = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 100.0,
    }, headers=auth_headers)
    assert r.status_code == 400
    assert "chiuso" in r.json()["detail"].lower()


def test_plan_on_closed_contract_rejected(client, auth_headers, sample_contract):
    """Piano rate su contratto chiuso → 400."""
    client.put(f"/api/contracts/{sample_contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)

    r = client.post(f"/api/rates/generate-plan/{sample_contract['id']}", json={
        "importo_da_rateizzare": 800.0,
        "numero_rate": 4,
        "data_prima_rata": "2026-02-01",
        "frequenza": "MENSILE",
    }, headers=auth_headers)
    assert r.status_code == 400
    assert "chiuso" in r.json()["detail"].lower()


def test_event_on_closed_contract_rejected(client, auth_headers, sample_client, sample_contract):
    """Evento PT con id_contratto su contratto chiuso → 400."""
    client.put(f"/api/contracts/{sample_contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)

    r = client.post("/api/events", json={
        "data_inizio": "2026-03-01T09:00:00",
        "data_fine": "2026-03-01T10:00:00",
        "categoria": "PT",
        "titolo": "Sessione bloccata",
        "id_cliente": sample_client["id"],
        "id_contratto": sample_contract["id"],
    }, headers=auth_headers)
    assert r.status_code == 400
    assert "chiuso" in r.json()["detail"].lower()


# ── F2: Close/Reopen via update ──


def test_close_contract_via_update(client, auth_headers, sample_contract):
    """Chiudere un contratto via PUT → chiuso = True."""
    r = client.put(f"/api/contracts/{sample_contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)
    assert r.status_code == 200

    cr = client.get(f"/api/contracts/{sample_contract['id']}", headers=auth_headers)
    assert cr.json()["chiuso"] is True


def test_delete_client_with_closed_contract(client, auth_headers, sample_client, sample_contract):
    """Cancellazione cliente con contratto chiuso → OK (non blocca)."""
    client.put(f"/api/contracts/{sample_contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)

    r = client.delete(f"/api/clients/{sample_client['id']}", headers=auth_headers)
    assert r.status_code == 204


# ── F5: Auto-close + auto-reopen ──


def _create_mini_contract(client, auth_headers, client_id):
    """Helper: contratto 1 credito, 100€, acconto 0."""
    r = client.post("/api/contracts", json={
        "id_cliente": client_id,
        "tipo_pacchetto": "Mini 1",
        "crediti_totali": 1,
        "prezzo_totale": 100.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
    }, headers=auth_headers)
    assert r.status_code == 201
    return r.json()


def test_auto_close_after_full_payment_and_credits(client, auth_headers, sample_client):
    """Auto-close: contratto saldato + crediti esauriti → chiuso automatico."""
    contract = _create_mini_contract(client, auth_headers, sample_client["id"])

    # Crea 1 rata da 100
    rr = client.post("/api/rates", json={
        "id_contratto": contract["id"],
        "data_scadenza": "2026-02-01",
        "importo_previsto": 100.0,
    }, headers=auth_headers)
    assert rr.status_code == 201
    rate = rr.json()

    # Crea 1 evento PT (consuma il credito)
    er = client.post("/api/events", json={
        "data_inizio": "2026-02-01T09:00:00",
        "data_fine": "2026-02-01T10:00:00",
        "categoria": "PT",
        "titolo": "Sessione test",
        "id_cliente": sample_client["id"],
        "id_contratto": contract["id"],
    }, headers=auth_headers)
    assert er.status_code == 201

    # Paga la rata → saldato + crediti esauriti → auto-close
    pr = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 100.0,
        "metodo": "POS",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)
    assert pr.status_code == 200

    # Verifica contratto chiuso
    check = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    data = check.json()
    assert data["stato_pagamento"] == "SALDATO"
    assert data["chiuso"] is True


def test_unpay_reopens_closed_contract(client, auth_headers, sample_client):
    """Revoca pagamento su contratto auto-chiuso → riapre (chiuso = False)."""
    contract = _create_mini_contract(client, auth_headers, sample_client["id"])

    rr = client.post("/api/rates", json={
        "id_contratto": contract["id"],
        "data_scadenza": "2026-02-01",
        "importo_previsto": 100.0,
    }, headers=auth_headers)
    rate = rr.json()

    # Evento PT per consumare il credito
    client.post("/api/events", json={
        "data_inizio": "2026-02-01T11:00:00",
        "data_fine": "2026-02-01T12:00:00",
        "categoria": "PT",
        "titolo": "Sessione test 2",
        "id_cliente": sample_client["id"],
        "id_contratto": contract["id"],
    }, headers=auth_headers)

    # Paga → auto-close
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 100.0,
        "metodo": "POS",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)

    check = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert check.json()["chiuso"] is True

    # Revoca pagamento → riapre
    ur = client.post(f"/api/rates/{rate['id']}/unpay", headers=auth_headers)
    assert ur.status_code == 200

    check2 = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert check2.json()["chiuso"] is False
    assert check2.json()["stato_pagamento"] != "SALDATO"


# ── Delete contract guards ──


def test_delete_contract_blocked_if_pending_rates(client, auth_headers, sample_contract_with_plan):
    """Delete contratto con rate PENDENTI (non pagate) → 409."""
    contract = sample_contract_with_plan["contract"]

    r = client.delete(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert r.status_code == 409
    assert "rate" in r.json()["detail"].lower()


def test_delete_contract_blocked_if_events(client, auth_headers, sample_client):
    """Delete contratto con sedute collegate → 409."""
    # Crea contratto pulito (senza acconto, senza rate)
    cr = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Test eventi",
        "crediti_totali": 5,
        "prezzo_totale": 500.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
    }, headers=auth_headers)
    assert cr.status_code == 201
    contract = cr.json()

    # Crea evento PT collegato al contratto
    client.post("/api/events", json={
        "data_inizio": "2026-03-01T09:00:00",
        "data_fine": "2026-03-01T10:00:00",
        "categoria": "PT",
        "titolo": "Sessione test",
        "id_cliente": sample_client["id"],
        "id_contratto": contract["id"],
    }, headers=auth_headers)

    # Delete → bloccato per eventi
    r = client.delete(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert r.status_code == 409
    assert "sedute" in r.json()["detail"].lower()


def test_delete_clean_contract_ok(client, auth_headers, sample_client):
    """Delete contratto pulito (zero rate, zero eventi) → 204."""
    cr = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Errore",
        "crediti_totali": 1,
        "prezzo_totale": 50.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
    }, headers=auth_headers)
    assert cr.status_code == 201
    contract = cr.json()

    r = client.delete(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert r.status_code == 204

    # Contratto non piu' accessibile
    check = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert check.status_code == 404


def test_delete_contract_cascades_acconto_movement(client, auth_headers, sample_client):
    """Delete contratto pulito con acconto → CashMovement acconto soft-deleted."""
    # Crea contratto con acconto (genera CashMovement automaticamente)
    cr = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Errore con acconto",
        "crediti_totali": 1,
        "prezzo_totale": 100.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
        "acconto": 50.0,
        "metodo_acconto": "CONTANTI",
    }, headers=auth_headers)
    assert cr.status_code == 201
    contract = cr.json()

    # Verifica che il movimento acconto esista (mese gennaio 2026)
    mr = client.get("/api/movements?anno=2026&mese=1", headers=auth_headers)
    acconto_before = [m for m in mr.json()["items"] if m.get("id_contratto") == contract["id"]]
    assert len(acconto_before) >= 1

    # Delete contratto → cascade acconto
    r = client.delete(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert r.status_code == 204

    # Movimento acconto non piu' visibile
    mr2 = client.get("/api/movements?anno=2026&mese=1", headers=auth_headers)
    acconto_after = [m for m in mr2.json()["items"] if m.get("id_contratto") == contract["id"]]
    assert len(acconto_after) == 0


# ── Credit engine: contratti chiusi ──


def test_credits_include_closed_contracts(client, auth_headers, sample_client):
    """Crediti residui includono contratti chiusi (chiuso non invalida crediti)."""
    # Crea contratto con 5 crediti
    cr = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Test 5",
        "crediti_totali": 5,
        "prezzo_totale": 500.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
    }, headers=auth_headers)
    assert cr.status_code == 201
    contract = cr.json()

    # Chiudi il contratto
    client.put(f"/api/contracts/{contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)

    # Crediti del cliente devono includere i 5 del contratto chiuso
    cl = client.get(f"/api/clients/{sample_client['id']}", headers=auth_headers)
    assert cl.json()["crediti_residui"] == 5
