"""Test spese ricorrenti — paradigma Conferma & Registra.

Il vecchio sync automatico e' stato rimosso. Ora le spese ricorrenti
generano occorrenze "pending" e l'utente le conferma esplicitamente.

10 test coprono:
- Pending endpoint (visibilita', filtraggio)
- Confirm endpoint (creazione CashMovement, idempotenza)
- Ancoraggio frequenze (data_inizio, cross-year)
- Soft delete e re-apparizione
- Stats read-only (zero auto-sync)
"""


def _create_expense(client, auth_headers, **overrides):
    """Helper: crea spesa ricorrente con defaults sensati."""
    payload = {
        "nome": "Test Spesa",
        "importo": 100.0,
        "giorno_scadenza": 1,
        "frequenza": "MENSILE",
    }
    payload.update(overrides)
    r = client.post("/api/recurring-expenses", json=payload, headers=auth_headers)
    assert r.status_code == 201, f"Create expense failed: {r.text}"
    return r.json()


def _get_pending(client, auth_headers, anno, mese):
    """Helper: GET pending expenses for a month."""
    r = client.get(
        f"/api/movements/pending-expenses?anno={anno}&mese={mese}",
        headers=auth_headers,
    )
    assert r.status_code == 200
    return r.json()


def _confirm(client, auth_headers, items):
    """Helper: POST confirm expenses."""
    r = client.post(
        "/api/movements/confirm-expenses",
        json={"items": items},
        headers=auth_headers,
    )
    assert r.status_code == 200
    return r.json()


# ════════════════════════════════════════════════════════════
# Pending endpoint
# ════════════════════════════════════════════════════════════


def test_pending_returns_unconfirmed(client, auth_headers):
    """Spesa creata con data_inizio nel mese target -> 1 pending."""
    _create_expense(client, auth_headers,
                    nome="Affitto", importo=800.0, data_inizio="2026-01-01")

    pending = _get_pending(client, auth_headers, 2026, 1)
    assert len(pending["items"]) == 1
    assert pending["items"][0]["nome"] == "Affitto"
    assert pending["items"][0]["importo"] == 800.0
    assert pending["totale_pending"] == 800.0


def test_pending_empty_after_confirm(client, auth_headers):
    """Dopo conferma, pending per lo stesso mese e' vuoto."""
    _create_expense(client, auth_headers,
                    nome="Assicurazione", importo=150.0, data_inizio="2026-03-01")

    pending = _get_pending(client, auth_headers, 2026, 3)
    assert len(pending["items"]) == 1

    # Conferma
    _confirm(client, auth_headers, [
        {"id_spesa": pending["items"][0]["id_spesa"],
         "mese_anno_key": pending["items"][0]["mese_anno_key"]},
    ])

    # Pending ora vuoto
    pending2 = _get_pending(client, auth_headers, 2026, 3)
    assert len(pending2["items"]) == 0
    assert pending2["totale_pending"] == 0


# ════════════════════════════════════════════════════════════
# Confirm endpoint
# ════════════════════════════════════════════════════════════


def test_confirm_creates_movement(client, auth_headers):
    """POST confirm crea CashMovement con dati corretti."""
    _create_expense(client, auth_headers,
                    nome="Internet", importo=50.0, data_inizio="2026-04-01")

    pending = _get_pending(client, auth_headers, 2026, 4)
    result = _confirm(client, auth_headers, [
        {"id_spesa": pending["items"][0]["id_spesa"],
         "mese_anno_key": pending["items"][0]["mese_anno_key"]},
    ])
    assert result["created"] == 1
    assert result["totale"] == 50.0

    # Verifica CashMovement nel ledger
    mr = client.get("/api/movements?anno=2026&mese=4", headers=auth_headers)
    movements = [
        m for m in mr.json()["items"]
        if m.get("id_spesa_ricorrente") is not None
    ]
    assert len(movements) == 1
    assert movements[0]["tipo"] == "USCITA"
    assert movements[0]["importo"] == 50.0
    assert movements[0]["operatore"] == "CONFERMA_UTENTE"


def test_confirm_idempotent(client, auth_headers):
    """Doppio POST confirm non duplica movimenti."""
    expense = _create_expense(client, auth_headers,
                              nome="Doppia Conferma", importo=200.0,
                              data_inizio="2026-05-01")

    pending = _get_pending(client, auth_headers, 2026, 5)
    item = {"id_spesa": expense["id"], "mese_anno_key": pending["items"][0]["mese_anno_key"]}

    # Prima conferma
    r1 = _confirm(client, auth_headers, [item])
    assert r1["created"] == 1

    # Seconda conferma — stessi dati, zero creati
    r2 = _confirm(client, auth_headers, [item])
    assert r2["created"] == 0

    # Solo 1 movimento nel ledger
    mr = client.get("/api/movements?anno=2026&mese=5", headers=auth_headers)
    spesa_movements = [
        m for m in mr.json()["items"]
        if m.get("id_spesa_ricorrente") is not None
    ]
    assert len(spesa_movements) == 1


# ════════════════════════════════════════════════════════════
# Filtraggio
# ════════════════════════════════════════════════════════════


def test_disabled_expense_no_pending(client, auth_headers):
    """Spesa disattivata non appare in pending."""
    expense = _create_expense(client, auth_headers,
                              nome="Vecchia Spesa", importo=300.0,
                              data_inizio="2026-06-01")

    # Disattiva
    client.put(f"/api/recurring-expenses/{expense['id']}", json={
        "attiva": False,
    }, headers=auth_headers)

    pending = _get_pending(client, auth_headers, 2026, 6)
    assert len(pending["items"]) == 0


def test_data_inizio_future_no_pending(client, auth_headers):
    """data_inizio nel futuro -> nessun pending per mesi precedenti."""
    _create_expense(client, auth_headers,
                    nome="Futura", importo=500.0,
                    data_inizio="2026-06-01")

    # Maggio (prima di data_inizio) -> nessun pending
    pending = _get_pending(client, auth_headers, 2026, 5)
    assert len(pending["items"]) == 0

    # Giugno (da data_inizio) -> pending presente
    pending2 = _get_pending(client, auth_headers, 2026, 6)
    assert len(pending2["items"]) == 1


# ════════════════════════════════════════════════════════════
# Ancoraggio frequenze
# ════════════════════════════════════════════════════════════


def test_data_inizio_anchoring_trimestrale(client, auth_headers):
    """TRIMESTRALE ancorata a data_inizio: solo ogni 3 mesi."""
    _create_expense(client, auth_headers,
                    nome="Trimestrale Test", importo=900.0,
                    frequenza="TRIMESTRALE", data_inizio="2026-01-01")

    # Gennaio (start) -> pending
    assert len(_get_pending(client, auth_headers, 2026, 1)["items"]) == 1
    # Febbraio -> nessun pending
    assert len(_get_pending(client, auth_headers, 2026, 2)["items"]) == 0
    # Marzo -> nessun pending
    assert len(_get_pending(client, auth_headers, 2026, 3)["items"]) == 0
    # Aprile (3 mesi dopo) -> pending
    assert len(_get_pending(client, auth_headers, 2026, 4)["items"]) == 1


def test_semestrale_cross_year(client, auth_headers):
    """SEMESTRALE cross-year: creata nov 2025, attesa mag 2026."""
    _create_expense(client, auth_headers,
                    nome="Semestrale Cross", importo=600.0,
                    frequenza="SEMESTRALE", data_inizio="2025-11-01")

    # Febbraio 2026 -> nessun pending (3 mesi, non 6)
    assert len(_get_pending(client, auth_headers, 2026, 2)["items"]) == 0
    # Maggio 2026 (6 mesi dopo nov 2025) -> pending
    assert len(_get_pending(client, auth_headers, 2026, 5)["items"]) == 1
    # Novembre 2026 (12 mesi dopo) -> pending
    assert len(_get_pending(client, auth_headers, 2026, 11)["items"]) == 1


# ════════════════════════════════════════════════════════════
# Soft delete e stats
# ════════════════════════════════════════════════════════════


def test_soft_deleted_movement_reappears_pending(client, auth_headers):
    """CashMovement confermato poi eliminato -> riappare come pending."""
    _create_expense(client, auth_headers,
                    nome="Eliminabile", importo=75.0,
                    data_inizio="2026-07-01")

    # Conferma
    pending = _get_pending(client, auth_headers, 2026, 7)
    _confirm(client, auth_headers, [
        {"id_spesa": pending["items"][0]["id_spesa"],
         "mese_anno_key": pending["items"][0]["mese_anno_key"]},
    ])

    # Pending vuoto
    assert len(_get_pending(client, auth_headers, 2026, 7)["items"]) == 0

    # Elimina il movimento
    mr = client.get("/api/movements?anno=2026&mese=7", headers=auth_headers)
    spesa_mov = [m for m in mr.json()["items"] if m.get("id_spesa_ricorrente")]
    assert len(spesa_mov) == 1
    dr = client.delete(f"/api/movements/{spesa_mov[0]['id']}", headers=auth_headers)
    assert dr.status_code == 204

    # Riappare in pending
    pending2 = _get_pending(client, auth_headers, 2026, 7)
    assert len(pending2["items"]) == 1


def test_stats_no_auto_sync(client, auth_headers):
    """GET /stats non crea movimenti automaticamente."""
    _create_expense(client, auth_headers,
                    nome="No Auto", importo=400.0,
                    data_inizio="2026-08-01")

    # GET stats — deve essere read-only
    sr = client.get("/api/movements/stats?anno=2026&mese=8", headers=auth_headers)
    assert sr.status_code == 200
    # Nessun uscita fissa (niente auto-sync)
    assert sr.json()["totale_uscite_fisse"] == 0

    # Nessun movimento creato
    mr = client.get("/api/movements?anno=2026&mese=8", headers=auth_headers)
    spesa_movements = [
        m for m in mr.json()["items"]
        if m.get("id_spesa_ricorrente") is not None
    ]
    assert len(spesa_movements) == 0
