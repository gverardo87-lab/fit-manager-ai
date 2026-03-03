"""Test spese ricorrenti — paradigma Conferma & Registra.

Il vecchio sync automatico e' stato rimosso. Ora le spese ricorrenti
generano occorrenze "pending" e l'utente le conferma esplicitamente.

15 test coprono:
- Pending endpoint (visibilita', filtraggio)
- Confirm endpoint (creazione CashMovement, idempotenza)
- Ancoraggio frequenze (data_inizio, cross-year)
- Soft delete e re-apparizione
- Stats read-only (zero auto-sync)
"""

from datetime import date


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


def _preview_confirm(client, auth_headers, items):
    """Helper: POST preview conferma spese."""
    r = client.post(
        "/api/movements/impact-preview/confirm-expenses",
        json={"items": items},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


def _close_expense(client, auth_headers, expense_id, *, key, last_occurrence_due):
    """Helper: chiude spesa ricorrente con strategia cutoff."""
    r = client.post(
        f"/api/recurring-expenses/{expense_id}/close",
        json={
            "effective_mese_anno_key": key,
            "last_occurrence_due": last_occurrence_due,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


def _preview_close_expense(client, auth_headers, expense_id, *, key, last_occurrence_due):
    """Helper: anteprima chiusura spesa ricorrente."""
    r = client.post(
        f"/api/recurring-expenses/{expense_id}/close-preview",
        json={
            "effective_mese_anno_key": key,
            "last_occurrence_due": last_occurrence_due,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
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


def test_balance_separates_real_and_projected(client, auth_headers):
    """Saldo reale non include movimenti futuri gia' confermati."""
    today = date.today()
    next_month = today.month + 1
    next_year = today.year
    if next_month > 12:
        next_month = 1
        next_year += 1

    _create_expense(
        client,
        auth_headers,
        nome="Spesa Futura",
        importo=120.0,
        giorno_scadenza=5,
        data_inizio=f"{next_year:04d}-{next_month:02d}-01",
    )

    pending = _get_pending(client, auth_headers, next_year, next_month)
    assert len(pending["items"]) == 1

    _confirm(client, auth_headers, [
        {
            "id_spesa": pending["items"][0]["id_spesa"],
            "mese_anno_key": pending["items"][0]["mese_anno_key"],
        },
    ])

    br = client.get("/api/movements/balance", headers=auth_headers)
    assert br.status_code == 200
    data = br.json()

    assert data["saldo_attuale"] == 0.0
    assert data["saldo_previsto"] == -120.0
    assert data["delta_movimenti_futuri"] == -120.0
    assert data["totale_uscite_future_confermate"] == 120.0


def test_delete_recurring_with_cleanup_removes_linked_movements(client, auth_headers):
    """Delete spesa ricorrente con cleanup elimina anche movimenti ledger collegati."""
    expense = _create_expense(
        client,
        auth_headers,
        nome="Errore Inserimento",
        importo=90.0,
        giorno_scadenza=10,
        data_inizio="2026-09-01",
    )

    pending = _get_pending(client, auth_headers, 2026, 9)
    assert len(pending["items"]) == 1

    _confirm(client, auth_headers, [
        {
            "id_spesa": pending["items"][0]["id_spesa"],
            "mese_anno_key": pending["items"][0]["mese_anno_key"],
        },
    ])

    before = client.get("/api/movements?anno=2026&mese=9", headers=auth_headers).json()
    assert len([m for m in before["items"] if m.get("id_spesa_ricorrente") == expense["id"]]) == 1

    dr = client.delete(
        f"/api/recurring-expenses/{expense['id']}?delete_movements=true",
        headers=auth_headers,
    )
    assert dr.status_code == 200
    assert dr.json()["deleted_movements"] == 1

    after = client.get("/api/movements?anno=2026&mese=9", headers=auth_headers).json()
    assert len([m for m in after["items"] if m.get("id_spesa_ricorrente") == expense["id"]]) == 0


def test_confirm_rejects_off_cycle_key(client, auth_headers):
    """Conferma off-cycle su TRIMESTRALE viene ignorata (hardening key validation)."""
    expense = _create_expense(
        client,
        auth_headers,
        nome="Trimestre Guard",
        importo=200.0,
        frequenza="TRIMESTRALE",
        data_inizio="2026-01-01",
    )

    result = _confirm(client, auth_headers, [
        {"id_spesa": expense["id"], "mese_anno_key": "2026-02"},
    ])
    assert result["created"] == 0


def test_close_recurring_keeps_last_due_and_preserves_history(client, auth_headers):
    """Chiusura con ultima occorrenza dovuta: mantiene storico e registra cutoff."""
    expense = _create_expense(
        client,
        auth_headers,
        nome="Affitto Studio",
        importo=500.0,
        giorno_scadenza=8,
        data_inizio="2026-01-01",
    )

    jan = _get_pending(client, auth_headers, 2026, 1)
    feb = _get_pending(client, auth_headers, 2026, 2)
    _confirm(client, auth_headers, [{
        "id_spesa": jan["items"][0]["id_spesa"],
        "mese_anno_key": jan["items"][0]["mese_anno_key"],
    }])
    _confirm(client, auth_headers, [{
        "id_spesa": feb["items"][0]["id_spesa"],
        "mese_anno_key": feb["items"][0]["mese_anno_key"],
    }])

    close = _close_expense(
        client,
        auth_headers,
        expense["id"],
        key="2026-03",
        last_occurrence_due=True,
    )
    assert close["created_last_due_movement"] is True
    assert close["storni_creati"] == 0
    assert close["storni_rimossi"] == 0

    rec = client.get("/api/recurring-expenses", headers=auth_headers).json()["items"]
    target = next(e for e in rec if e["id"] == expense["id"])
    assert target["attiva"] is False

    march_mov = client.get("/api/movements?anno=2026&mese=3", headers=auth_headers).json()["items"]
    march_cutoff = [
        m for m in march_mov
        if m.get("id_spesa_ricorrente") == expense["id"]
        and m.get("data_effettiva") == "2026-03-08"
    ]
    assert len(march_cutoff) == 1
    assert march_cutoff[0]["tipo"] == "USCITA"

    april_pending = _get_pending(client, auth_headers, 2026, 4)
    assert len(april_pending["items"]) == 0


def test_close_recurring_non_due_creates_storno_for_cutoff(client, auth_headers):
    """Chiusura con ultima occorrenza NON dovuta: crea storno sul cutoff gia' registrato."""
    expense = _create_expense(
        client,
        auth_headers,
        nome="Piattaforma Gestionale",
        importo=120.0,
        giorno_scadenza=8,
        data_inizio="2026-01-01",
    )

    for month in (1, 2, 3):
        pending = _get_pending(client, auth_headers, 2026, month)
        _confirm(client, auth_headers, [{
            "id_spesa": pending["items"][0]["id_spesa"],
            "mese_anno_key": pending["items"][0]["mese_anno_key"],
        }])

    close = _close_expense(
        client,
        auth_headers,
        expense["id"],
        key="2026-03",
        last_occurrence_due=False,
    )
    assert close["created_last_due_movement"] is False
    assert close["storni_creati"] == 1
    assert close["storni_rimossi"] == 0

    march_mov = client.get("/api/movements?anno=2026&mese=3", headers=auth_headers).json()["items"]
    expense_rows = [m for m in march_mov if m.get("id_spesa_ricorrente") == expense["id"]]
    assert len([m for m in expense_rows if m["tipo"] == "USCITA"]) == 1
    assert len([m for m in expense_rows if m["tipo"] == "ENTRATA"]) == 1


def test_close_non_due_updates_stats_chart_and_reinsert_is_consistent(client, auth_headers):
    """
    Regressione cashflow:
    - Chiusura NON dovuta a marzo deve azzerare l'uscita fissa netta del mese
    - Il grafico giornaliero deve riflettere lo storno (nessuna uscita residua sul giorno cutoff)
    - Reinserendo la spesa nel mese, stats/grafico devono mostrare solo la nuova uscita netta
    """
    expense = _create_expense(
        client,
        auth_headers,
        nome="Affitto Sala",
        importo=120.0,
        giorno_scadenza=8,
        data_inizio="2026-01-01",
    )

    # Conferma gennaio, febbraio, marzo
    for month in (1, 2, 3):
        pending = _get_pending(client, auth_headers, 2026, month)
        _confirm(client, auth_headers, [{
            "id_spesa": pending["items"][0]["id_spesa"],
            "mese_anno_key": pending["items"][0]["mese_anno_key"],
        }])

    _close_expense(
        client,
        auth_headers,
        expense["id"],
        key="2026-03",
        last_occurrence_due=False,
    )

    stats_after_close = client.get(
        "/api/movements/stats?anno=2026&mese=3",
        headers=auth_headers,
    ).json()
    assert stats_after_close["totale_entrate"] == 0.0
    assert stats_after_close["totale_uscite_fisse"] == 0.0
    assert stats_after_close["saldo_fine_mese"] == stats_after_close["saldo_inizio_mese"]
    day8_after_close = next(d for d in stats_after_close["chart_data"] if d["giorno"] == 8)
    assert day8_after_close["entrate"] == 0.0
    assert day8_after_close["uscite"] == 0.0

    reinserted = _create_expense(
        client,
        auth_headers,
        nome="Affitto Sala",
        importo=120.0,
        giorno_scadenza=8,
        data_inizio="2026-03-01",
    )
    pending_march = _get_pending(client, auth_headers, 2026, 3)
    march_item = next(i for i in pending_march["items"] if i["id_spesa"] == reinserted["id"])
    _confirm(client, auth_headers, [{
        "id_spesa": march_item["id_spesa"],
        "mese_anno_key": march_item["mese_anno_key"],
    }])

    stats_after_reinsert = client.get(
        "/api/movements/stats?anno=2026&mese=3",
        headers=auth_headers,
    ).json()
    assert stats_after_reinsert["totale_entrate"] == 0.0
    assert stats_after_reinsert["totale_uscite_fisse"] == 120.0
    assert round(
        stats_after_reinsert["saldo_inizio_mese"] - stats_after_reinsert["saldo_fine_mese"],
        2,
    ) == 120.0
    day8_after_reinsert = next(d for d in stats_after_reinsert["chart_data"] if d["giorno"] == 8)
    assert day8_after_reinsert["entrate"] == 0.0
    assert day8_after_reinsert["uscite"] == 120.0


def test_close_allows_rectify_on_inactive_and_storno_older_cutoff(client, auth_headers):
    """
    Chiusura ripetuta su spesa gia' disattivata:
    - primo passaggio: cutoff marzo non dovuto -> storna marzo
    - rettifica successiva: cutoff febbraio non dovuto -> aggiunge storno febbraio
    """
    expense = _create_expense(
        client,
        auth_headers,
        nome="Affitto Sala Rettifica",
        importo=130.0,
        giorno_scadenza=5,
        data_inizio="2026-02-01",
    )

    for month in (2, 3):
        pending = _get_pending(client, auth_headers, 2026, month)
        _confirm(client, auth_headers, [{
            "id_spesa": pending["items"][0]["id_spesa"],
            "mese_anno_key": pending["items"][0]["mese_anno_key"],
        }])

    close_march = _close_expense(
        client,
        auth_headers,
        expense["id"],
        key="2026-03",
        last_occurrence_due=False,
    )
    assert close_march["storni_creati"] == 1
    assert close_march["storni_rimossi"] == 0

    rectify_feb = _close_expense(
        client,
        auth_headers,
        expense["id"],
        key="2026-02",
        last_occurrence_due=False,
    )
    assert rectify_feb["storni_creati"] == 1
    assert rectify_feb["storni_rimossi"] == 0

    feb_stats = client.get("/api/movements/stats?anno=2026&mese=2", headers=auth_headers).json()
    mar_stats = client.get("/api/movements/stats?anno=2026&mese=3", headers=auth_headers).json()
    assert feb_stats["totale_uscite_fisse"] == 0.0
    assert mar_stats["totale_uscite_fisse"] == 0.0

    feb_day5 = next(d for d in feb_stats["chart_data"] if d["giorno"] == 5)
    mar_day5 = next(d for d in mar_stats["chart_data"] if d["giorno"] == 5)
    assert feb_day5["uscite"] == 0.0
    assert mar_day5["uscite"] == 0.0


def test_close_rectify_can_restore_due_cutoff_by_removing_storno(client, auth_headers):
    """
    Rettifica inversa:
    - prima cutoff non dovuto (crea storno)
    - poi stesso cutoff dovuto (rimuove storno) senza riaprire la spesa
    """
    expense = _create_expense(
        client,
        auth_headers,
        nome="Ripristino Dovuta",
        importo=95.0,
        giorno_scadenza=7,
        data_inizio="2026-01-01",
    )

    for month in (1, 2):
        pending = _get_pending(client, auth_headers, 2026, month)
        _confirm(client, auth_headers, [{
            "id_spesa": pending["items"][0]["id_spesa"],
            "mese_anno_key": pending["items"][0]["mese_anno_key"],
        }])

    non_due = _close_expense(
        client,
        auth_headers,
        expense["id"],
        key="2026-02",
        last_occurrence_due=False,
    )
    assert non_due["storni_creati"] == 1
    assert non_due["storni_rimossi"] == 0

    due_again = _close_expense(
        client,
        auth_headers,
        expense["id"],
        key="2026-02",
        last_occurrence_due=True,
    )
    assert due_again["storni_creati"] == 0
    assert due_again["storni_rimossi"] == 1

    feb_stats = client.get("/api/movements/stats?anno=2026&mese=2", headers=auth_headers).json()
    assert feb_stats["totale_uscite_fisse"] == 95.0
    feb_day7 = next(d for d in feb_stats["chart_data"] if d["giorno"] == 7)
    assert feb_day7["entrate"] == 0.0
    assert feb_day7["uscite"] == 95.0


def test_close_rectify_is_idempotent_on_same_cutoff_strategy(client, auth_headers):
    """Ripetere la stessa strategia di cutoff non deve produrre ulteriori movimenti."""
    expense = _create_expense(
        client,
        auth_headers,
        nome="Idempotenza Rettifica",
        importo=80.0,
        giorno_scadenza=4,
        data_inizio="2026-02-01",
    )

    for month in (2, 3):
        pending = _get_pending(client, auth_headers, 2026, month)
        _confirm(client, auth_headers, [{
            "id_spesa": pending["items"][0]["id_spesa"],
            "mese_anno_key": pending["items"][0]["mese_anno_key"],
        }])

    first = _close_expense(
        client,
        auth_headers,
        expense["id"],
        key="2026-03",
        last_occurrence_due=False,
    )
    assert first["storni_creati"] == 1
    assert first["storni_rimossi"] == 0

    second = _close_expense(
        client,
        auth_headers,
        expense["id"],
        key="2026-03",
        last_occurrence_due=False,
    )
    assert second["storni_creati"] == 0
    assert second["storni_rimossi"] == 0


def test_preview_confirm_expenses_future_matches_balance_after_apply(client, auth_headers):
    """Anteprima conferma spese future: delta solo sul previsto e coerenza post-apply."""
    today = date.today()
    next_month = today.month + 1
    next_year = today.year
    if next_month > 12:
        next_month = 1
        next_year += 1

    _create_expense(
        client,
        auth_headers,
        nome="Preview Conferma",
        importo=110.0,
        giorno_scadenza=5,
        data_inizio=f"{next_year:04d}-{next_month:02d}-01",
    )
    pending = _get_pending(client, auth_headers, next_year, next_month)
    item = {
        "id_spesa": pending["items"][0]["id_spesa"],
        "mese_anno_key": pending["items"][0]["mese_anno_key"],
    }

    preview = _preview_confirm(client, auth_headers, [item])
    assert preview["operation"] == "CONFIRM_EXPENSES"
    assert preview["delta_saldo_attuale"] == 0.0
    assert preview["delta_saldo_previsto"] == -110.0
    assert preview["delta_netto"] == -110.0

    _confirm(client, auth_headers, [item])
    balance = client.get("/api/movements/balance", headers=auth_headers).json()
    assert balance["saldo_attuale"] == preview["saldo_attuale_after"]
    assert balance["saldo_previsto"] == preview["saldo_previsto_after"]


def test_preview_close_non_due_matches_effective_balance_after_apply(client, auth_headers):
    """Anteprima chiusura non dovuta: storni previsti e saldi after devono combaciare con apply."""
    expense = _create_expense(
        client,
        auth_headers,
        nome="Preview Chiusura",
        importo=140.0,
        giorno_scadenza=8,
        data_inizio="2026-01-01",
    )

    for month in (1, 2, 3):
        pending = _get_pending(client, auth_headers, 2026, month)
        _confirm(client, auth_headers, [{
            "id_spesa": pending["items"][0]["id_spesa"],
            "mese_anno_key": pending["items"][0]["mese_anno_key"],
        }])

    preview = _preview_close_expense(
        client,
        auth_headers,
        expense["id"],
        key="2026-03",
        last_occurrence_due=False,
    )
    assert preview["storni_creati_previsti"] == 1
    assert preview["storni_rimossi_previsti"] == 0
    assert preview["delta_saldo_previsto"] == 140.0
    assert preview["delta_netto"] == 140.0

    applied = _close_expense(
        client,
        auth_headers,
        expense["id"],
        key="2026-03",
        last_occurrence_due=False,
    )
    assert applied["storni_creati"] == preview["storni_creati_previsti"]
    assert applied["storni_rimossi"] == preview["storni_rimossi_previsti"]

    balance = client.get("/api/movements/balance", headers=auth_headers).json()
    assert balance["saldo_attuale"] == preview["saldo_attuale_after"]
    assert balance["saldo_previsto"] == preview["saldo_previsto_after"]
