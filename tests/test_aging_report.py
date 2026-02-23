"""Test aging report — bucket assignment e totali."""

from datetime import date, timedelta


def _create_rate(client, auth_headers, contract_id, days_offset, importo):
    """Helper: crea rata con scadenza a today + days_offset."""
    scadenza = (date.today() + timedelta(days=days_offset)).isoformat()
    r = client.post("/api/rates", json={
        "id_contratto": contract_id,
        "data_scadenza": scadenza,
        "importo_previsto": importo,
    }, headers=auth_headers)
    assert r.status_code == 201, f"Rate creation failed: {r.text}"
    return r.json()


def test_aging_bucket_assignment(client, auth_headers, sample_contract):
    """2 rate scadute (5gg e 45gg) + 1 futura (20gg) → bucket corretti."""
    cid = sample_contract["id"]

    # Rata scaduta da 5 giorni → bucket overdue "0-30"
    _create_rate(client, auth_headers, cid, days_offset=-5, importo=100.0)

    # Rata scaduta da 45 giorni → bucket overdue "31-60"
    _create_rate(client, auth_headers, cid, days_offset=-45, importo=200.0)

    # Rata futura tra 20 giorni → bucket upcoming "8-30"
    _create_rate(client, auth_headers, cid, days_offset=20, importo=150.0)

    r = client.get("/api/rates/aging", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()

    # Summary
    assert data["rate_scadute"] == 2
    assert data["rate_in_arrivo"] == 1
    assert data["totale_scaduto"] == 300.0      # 100 + 200
    assert data["totale_in_arrivo"] == 150.0
    assert data["clienti_con_scaduto"] == 1

    # Overdue bucket 0-30: 1 rata da 100
    bucket_0_30 = data["overdue_buckets"][0]
    assert bucket_0_30["label"] == "0-30"
    assert bucket_0_30["count"] == 1
    assert bucket_0_30["totale"] == 100.0
    assert bucket_0_30["items"][0]["giorni"] == 5

    # Overdue bucket 31-60: 1 rata da 200
    bucket_31_60 = data["overdue_buckets"][1]
    assert bucket_31_60["label"] == "31-60"
    assert bucket_31_60["count"] == 1
    assert bucket_31_60["totale"] == 200.0
    assert bucket_31_60["items"][0]["giorni"] == 45

    # Overdue bucket 61-90 e 90+: vuoti
    assert data["overdue_buckets"][2]["count"] == 0
    assert data["overdue_buckets"][3]["count"] == 0

    # Upcoming bucket 8-30: 1 rata da 150
    bucket_8_30 = data["upcoming_buckets"][1]
    assert bucket_8_30["label"] == "8-30"
    assert bucket_8_30["count"] == 1
    assert bucket_8_30["totale"] == 150.0


def test_aging_excludes_saldate(client, auth_headers, sample_contract):
    """Rate SALDATE non appaiono nell'aging report."""
    cid = sample_contract["id"]

    # Crea e paga una rata scaduta
    rate = _create_rate(client, auth_headers, cid, days_offset=-10, importo=100.0)
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 100.0,
        "metodo": "CONTANTI",
        "data_pagamento": date.today().isoformat(),
    }, headers=auth_headers)

    r = client.get("/api/rates/aging", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["rate_scadute"] == 0
    assert r.json()["rate_in_arrivo"] == 0


def test_aging_excludes_closed_contracts(client, auth_headers, sample_contract):
    """Rate di contratti chiusi non appaiono."""
    cid = sample_contract["id"]
    _create_rate(client, auth_headers, cid, days_offset=-10, importo=100.0)

    # Chiudi il contratto manualmente
    client.put(f"/api/contracts/{cid}", json={"chiuso": True}, headers=auth_headers)

    r = client.get("/api/rates/aging", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["rate_scadute"] == 0


def test_aging_empty_returns_zeroes(client, auth_headers):
    """Nessuna rata → risposta con zero e bucket vuoti."""
    r = client.get("/api/rates/aging", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()

    assert data["totale_scaduto"] == 0
    assert data["totale_in_arrivo"] == 0
    assert data["rate_scadute"] == 0
    assert data["rate_in_arrivo"] == 0
    assert data["clienti_con_scaduto"] == 0
    assert len(data["overdue_buckets"]) == 4
    assert len(data["upcoming_buckets"]) == 4
