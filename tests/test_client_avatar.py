# tests/test_client_avatar.py
"""
Test Client Avatar — 11 test cases per schema, service e endpoint.
"""

import json
from datetime import date, timedelta

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_client(client, auth_headers, **overrides):
    payload = {"nome": "Test", "cognome": "Avatar", **overrides}
    r = client.post("/api/clients", json=payload, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _create_contract(client, auth_headers, id_cliente, **overrides):
    today = date.today()
    payload = {
        "id_cliente": id_cliente,
        "tipo_pacchetto": "Gold 10",
        "crediti_totali": 10,
        "prezzo_totale": 1000.0,
        "data_inizio": (today - timedelta(days=30)).isoformat(),
        "data_scadenza": (today + timedelta(days=335)).isoformat(),
        "acconto": 0,
        **overrides,
    }
    r = client.post("/api/contracts", json=payload, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _set_anamnesi(client, auth_headers, client_id, structured=True):
    if structured:
        anamnesi = {
            "data_compilazione": date.today().isoformat(),
            "obiettivo_principale": "Dimagrimento",
            "livello_attivita": "Sedentario",
        }
    else:
        anamnesi = {"note": "vecchia anamnesi"}

    r = client.put(
        f"/api/clients/{client_id}",
        json={"anamnesi": anamnesi},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestClientAvatar:
    """Test suite per Client Avatar endpoint e service."""

    def test_avatar_missing_client_404(self, client, auth_headers):
        """GET avatar per client inesistente = 404."""
        r = client.get("/api/clients/99999/avatar", headers=auth_headers)
        assert r.status_code == 404

    def test_avatar_minimal_client(self, client, auth_headers):
        """Client appena creato: tutte le dimensioni critiche."""
        c = _create_client(client, auth_headers)
        r = client.get(f"/api/clients/{c['id']}/avatar", headers=auth_headers)
        assert r.status_code == 200

        avatar = r.json()
        assert avatar["client_id"] == c["id"]
        assert avatar["readiness_score"] == 0
        assert avatar["identity"]["full_name"] == "Test Avatar"
        assert avatar["identity"]["status"] == "green"  # Attivo
        assert avatar["clinical"]["status"] == "red"  # anamnesi missing
        assert avatar["clinical"]["anamnesi_state"] == "missing"
        assert avatar["contract"]["status"] == "red"  # no contract
        assert avatar["training"]["status"] == "red"  # no plan
        assert avatar["body_goals"]["status"] == "red"  # no measurements

    def test_avatar_with_structured_anamnesi(self, client, auth_headers):
        """Anamnesi strutturata = clinical green, readiness +40."""
        c = _create_client(client, auth_headers)
        _set_anamnesi(client, auth_headers, c["id"], structured=True)

        r = client.get(f"/api/clients/{c['id']}/avatar", headers=auth_headers)
        avatar = r.json()

        assert avatar["clinical"]["status"] == "green"
        assert avatar["clinical"]["anamnesi_state"] == "structured"
        assert avatar["clinical"]["anamnesi_version"] == 2
        assert avatar["readiness_score"] >= 40

    def test_avatar_with_contract_credits(self, client, auth_headers):
        """Contratto attivo con crediti = contract green."""
        c = _create_client(client, auth_headers)
        _create_contract(client, auth_headers, c["id"])

        r = client.get(f"/api/clients/{c['id']}/avatar", headers=auth_headers)
        avatar = r.json()

        assert avatar["contract"]["has_active_contract"] is True
        assert avatar["contract"]["credits_remaining"] == 10
        assert avatar["contract"]["credits_total"] == 10
        assert avatar["contract"]["status"] == "green"

    def test_avatar_overdue_rates(self, client, auth_headers):
        """Rate scadute = contract red + highlight critical."""
        c = _create_client(client, auth_headers)
        contract = _create_contract(client, auth_headers, c["id"])

        # Create overdue rate
        past = (date.today() - timedelta(days=10)).isoformat()
        r = client.post("/api/rates", json={
            "id_contratto": contract["id"],
            "data_scadenza": past,
            "importo_previsto": 200.0,
        }, headers=auth_headers)
        assert r.status_code == 201, r.text

        r = client.get(f"/api/clients/{c['id']}/avatar", headers=auth_headers)
        avatar = r.json()

        assert avatar["contract"]["overdue_rates_count"] >= 1
        assert avatar["contract"]["status"] == "red"

        # Check highlight
        codes = [h["code"] for h in avatar["highlights"]]
        assert "overdue_rates" in codes

    def test_avatar_compliance_calculation(self, client, auth_headers):
        """Compliance e' None senza piano attivo."""
        c = _create_client(client, auth_headers)

        r = client.get(f"/api/clients/{c['id']}/avatar", headers=auth_headers)
        avatar = r.json()

        # No plan = no compliance
        assert avatar["training"]["compliance_30d"] is None
        assert avatar["training"]["compliance_60d"] is None

    def test_avatar_session_gap_highlight(self, client, auth_headers):
        """Senza sessioni ma con piano = no_active_plan highlight."""
        c = _create_client(client, auth_headers)

        r = client.get(f"/api/clients/{c['id']}/avatar", headers=auth_headers)
        avatar = r.json()

        # No plan → should have no_active_plan highlight
        codes = [h["code"] for h in avatar["highlights"]]
        assert "no_active_plan" in codes

    def test_avatar_batch_multiple_clients(self, client, auth_headers):
        """Batch con 3 clienti restituisce 3 avatar."""
        ids = []
        for i in range(3):
            c = _create_client(client, auth_headers, nome=f"Batch{i}")
            ids.append(c["id"])

        r = client.post("/api/clients/avatars", json={
            "client_ids": ids,
        }, headers=auth_headers)
        assert r.status_code == 200

        data = r.json()
        assert len(data["avatars"]) == 3
        returned_ids = {a["client_id"] for a in data["avatars"]}
        assert returned_ids == set(ids)

    def test_avatar_batch_trainer_isolation(self, client, auth_headers):
        """Batch non restituisce clienti di altri trainer."""
        # Create client with first trainer
        c = _create_client(client, auth_headers)

        # Register second trainer
        r2 = client.post("/api/auth/register", json={
            "email": "other@test.com",
            "nome": "Other",
            "cognome": "Trainer",
            "password": "testpass123",
        })
        assert r2.status_code == 201
        other_headers = {"Authorization": f"Bearer {r2.json()['access_token']}"}

        # Second trainer should not see first trainer's client
        r = client.post("/api/clients/avatars", json={
            "client_ids": [c["id"]],
        }, headers=other_headers)
        assert r.status_code == 200
        assert len(r.json()["avatars"]) == 0

    def test_avatar_batch_ignores_deleted(self, client, auth_headers):
        """Batch ignora clienti soft-deleted."""
        c = _create_client(client, auth_headers)

        # Delete client
        r = client.delete(f"/api/clients/{c['id']}", headers=auth_headers)
        assert r.status_code in (200, 204), r.text

        # Should not appear in batch
        r = client.post("/api/clients/avatars", json={
            "client_ids": [c["id"]],
        }, headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()["avatars"]) == 0

    def test_avatar_semaphore_determinism(self, client, auth_headers):
        """Stessi dati = stessi semafori (tranne generated_at)."""
        c = _create_client(client, auth_headers)
        _set_anamnesi(client, auth_headers, c["id"], structured=True)
        _create_contract(client, auth_headers, c["id"])

        r1 = client.get(f"/api/clients/{c['id']}/avatar", headers=auth_headers)
        r2 = client.get(f"/api/clients/{c['id']}/avatar", headers=auth_headers)

        a1, a2 = r1.json(), r2.json()

        # Semaphores must be identical
        assert a1["clinical"]["status"] == a2["clinical"]["status"]
        assert a1["contract"]["status"] == a2["contract"]["status"]
        assert a1["training"]["status"] == a2["training"]["status"]
        assert a1["body_goals"]["status"] == a2["body_goals"]["status"]
        assert a1["readiness_score"] == a2["readiness_score"]

        # Highlights must be identical (same codes in same order)
        assert [h["code"] for h in a1["highlights"]] == [h["code"] for h in a2["highlights"]]
