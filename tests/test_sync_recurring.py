"""Test sync engine spese ricorrenti — idempotenza e soft delete."""


def test_first_sync_creates_movements(client, auth_headers):
    """Prima sync: crea CashMovement da spesa ricorrente."""
    # Crea spesa ricorrente
    client.post("/api/recurring-expenses", json={
        "nome": "Affitto palestra",
        "importo": 800.0,
        "giorno_scadenza": 5,
        "frequenza": "MENSILE",
    }, headers=auth_headers)

    # GET stats triggera il sync
    sr = client.get("/api/movements/stats?anno=2026&mese=2", headers=auth_headers)
    assert sr.status_code == 200
    stats = sr.json()
    assert stats["totale_uscite_fisse"] == 800.0


def test_sync_idempotent(client, auth_headers):
    """Seconda sync stesso mese: 0 nuovi movimenti."""
    client.post("/api/recurring-expenses", json={
        "nome": "Assicurazione",
        "importo": 150.0,
        "giorno_scadenza": 1,
        "frequenza": "MENSILE",
    }, headers=auth_headers)

    # Prima sync
    client.get("/api/movements/stats?anno=2026&mese=3", headers=auth_headers)

    # Seconda sync — stessi importi
    sr = client.get("/api/movements/stats?anno=2026&mese=3", headers=auth_headers)
    stats = sr.json()
    assert stats["totale_uscite_fisse"] == 150.0  # NON 300


def test_disabled_expense_no_sync(client, auth_headers):
    """Spesa disattivata: non genera movimenti."""
    r = client.post("/api/recurring-expenses", json={
        "nome": "Vecchia spesa",
        "importo": 200.0,
        "giorno_scadenza": 10,
        "frequenza": "MENSILE",
    }, headers=auth_headers)
    expense_id = r.json()["id"]

    # Disattiva
    client.put(f"/api/recurring-expenses/{expense_id}", json={
        "attiva": False,
    }, headers=auth_headers)

    # Sync non deve creare movimenti per questa spesa
    sr = client.get("/api/movements/stats?anno=2026&mese=5", headers=auth_headers)
    stats = sr.json()
    assert stats["totale_uscite_fisse"] == 0


def test_soft_deleted_movement_triggers_resync(client, auth_headers):
    """
    Fix 0A+0B verification:
    Movimento soft-deleted -> sync crea uno NUOVO per lo stesso mese.

    Questo e' il test piu' critico: verifica che:
    1. Il NOT EXISTS nel sync engine filtra deleted_at IS NULL (Fix 0A)
    2. L'UNIQUE index esclude deleted_at IS NOT NULL (Fix 0B)
    """
    # Crea spesa
    client.post("/api/recurring-expenses", json={
        "nome": "Internet",
        "importo": 50.0,
        "giorno_scadenza": 15,
        "frequenza": "MENSILE",
    }, headers=auth_headers)

    # Prima sync
    client.get("/api/movements/stats?anno=2026&mese=6", headers=auth_headers)

    # Trova il movimento creato
    mr = client.get("/api/movements?anno=2026&mese=6", headers=auth_headers)
    spesa_movements = [
        m for m in mr.json()["items"]
        if m.get("id_spesa_ricorrente") is not None
    ]
    assert len(spesa_movements) == 1

    # Soft-delete il movimento
    mid = spesa_movements[0]["id"]
    dr = client.delete(f"/api/movements/{mid}", headers=auth_headers)
    assert dr.status_code == 204

    # Re-sync: deve creare uno NUOVO (non fallire per UNIQUE constraint)
    client.get("/api/movements/stats?anno=2026&mese=6", headers=auth_headers)

    mr2 = client.get("/api/movements?anno=2026&mese=6", headers=auth_headers)
    spesa_movements_2 = [
        m for m in mr2.json()["items"]
        if m.get("id_spesa_ricorrente") is not None
    ]
    # Deve avere 1 movimento attivo (il nuovo), non 0
    assert len(spesa_movements_2) == 1
    # Stats deve riflettere il movimento
    sr = client.get("/api/movements/stats?anno=2026&mese=6", headers=auth_headers)
    assert sr.json()["totale_uscite_fisse"] == 50.0


# ════════════════════════════════════════════════════════════
# FREQUENZE ESTESE (S4 — SEMESTRALE + ANNUALE)
# ════════════════════════════════════════════════════════════


def test_semestrale_only_every_6_months(client, auth_headers):
    """Spesa SEMESTRALE: genera movimento solo ogni 6 mesi dal mese di creazione."""
    # Crea spesa SEMESTRALE (creata a febbraio 2026)
    client.post("/api/recurring-expenses", json={
        "nome": "Assicurazione Semestrale",
        "importo": 600.0,
        "giorno_scadenza": 10,
        "frequenza": "SEMESTRALE",
    }, headers=auth_headers)

    # Febbraio (mese creazione) → deve generare
    sr_feb = client.get("/api/movements/stats?anno=2026&mese=2", headers=auth_headers)
    assert sr_feb.json()["totale_uscite_fisse"] == 600.0

    # Marzo → non deve generare (non multiplo di 6 da febbraio)
    sr_mar = client.get("/api/movements/stats?anno=2026&mese=3", headers=auth_headers)
    assert sr_mar.json()["totale_uscite_fisse"] == 0

    # Agosto (6 mesi dopo febbraio) → deve generare
    sr_ago = client.get("/api/movements/stats?anno=2026&mese=8", headers=auth_headers)
    assert sr_ago.json()["totale_uscite_fisse"] == 600.0


def test_annuale_only_anniversary_month(client, auth_headers):
    """Spesa ANNUALE: genera movimento solo nel mese anniversario."""
    # Crea spesa ANNUALE (creata a marzo 2026)
    # Per forzare il mese di creazione a marzo, creiamo la spesa
    # e il sync engine usa data_creazione.month per l'ancoraggio
    client.post("/api/recurring-expenses", json={
        "nome": "Commercialista Annuale",
        "importo": 1200.0,
        "giorno_scadenza": 15,
        "frequenza": "ANNUALE",
    }, headers=auth_headers)

    # Il mese di creazione dipende da quando viene eseguito il test.
    # La spesa viene creata con data_creazione = now(), quindi il mese
    # di creazione e' il mese corrente. Verifichiamo:
    # - GET stats per mesi diversi dal mese di creazione → 0
    # - GET stats per il mese di creazione → 1200

    # Recupera la spesa per sapere il mese di creazione
    lr = client.get("/api/recurring-expenses", headers=auth_headers)
    expense = next(e for e in lr.json()["items"] if e["nome"] == "Commercialista Annuale")
    creation_month = int(expense["data_creazione"][:7].split("-")[1])

    # Mese anniversario → deve generare
    sr_hit = client.get(f"/api/movements/stats?anno=2026&mese={creation_month}", headers=auth_headers)
    assert sr_hit.json()["totale_uscite_fisse"] == 1200.0

    # Mese diverso → non deve generare
    other_month = (creation_month % 12) + 1  # mese successivo
    sr_miss = client.get(f"/api/movements/stats?anno=2026&mese={other_month}", headers=auth_headers)
    assert sr_miss.json()["totale_uscite_fisse"] == 0
