"""Test endpoint audit log cassa consultabile."""

from datetime import date, timedelta


def _create_manual_movement(client, auth_headers, *, tipo: str, importo: float, note: str):
    response = client.post(
        "/api/movements",
        json={
            "tipo": tipo,
            "importo": importo,
            "categoria": "TEST",
            "metodo": "CONTANTI",
            "data_effettiva": "2026-03-10",
            "note": note,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_cash_audit_log_tracks_movement_create_and_delete(client, auth_headers):
    movement = _create_manual_movement(
        client,
        auth_headers,
        tipo="ENTRATA",
        importo=120.0,
        note="Incasso test audit",
    )

    list_response = client.get("/api/movements/audit-log", headers=auth_headers)
    assert list_response.status_code == 200, list_response.text
    payload = list_response.json()
    assert payload["total"] >= 1

    created = next(
        (
            item
            for item in payload["items"]
            if item["entity_type"] == "movement"
            and item["entity_id"] == movement["id"]
            and item["action"] == "CREATE"
        ),
        None,
    )
    assert created is not None
    assert created["flow_hint"] == "ENTRATA"
    assert created["reason"] == "Incasso test audit"
    assert created["link_href"] == "/cassa?tab=ledger"

    delete_response = client.delete(f"/api/movements/{movement['id']}", headers=auth_headers)
    assert delete_response.status_code == 204

    deleted_list = client.get(
        "/api/movements/audit-log?entity_type=movement&action=DELETE",
        headers=auth_headers,
    )
    assert deleted_list.status_code == 200, deleted_list.text
    deleted_items = deleted_list.json()["items"]
    assert any(i["entity_id"] == movement["id"] and i["action"] == "DELETE" for i in deleted_items)


def test_cash_audit_log_filters_by_flow_and_date(client, auth_headers):
    _create_manual_movement(
        client,
        auth_headers,
        tipo="ENTRATA",
        importo=90.0,
        note="Entrata filtro",
    )
    _create_manual_movement(
        client,
        auth_headers,
        tipo="USCITA",
        importo=30.0,
        note="Uscita filtro",
    )

    entrate = client.get("/api/movements/audit-log?flow=ENTRATA", headers=auth_headers)
    assert entrate.status_code == 200, entrate.text
    entrate_items = entrate.json()["items"]
    assert len(entrate_items) > 0
    assert all(item["flow_hint"] == "ENTRATA" for item in entrate_items)

    uscite = client.get("/api/movements/audit-log?flow=USCITA", headers=auth_headers)
    assert uscite.status_code == 200, uscite.text
    uscite_items = uscite.json()["items"]
    assert len(uscite_items) > 0
    assert all(item["flow_hint"] == "USCITA" for item in uscite_items)

    tomorrow = date.today() + timedelta(days=1)
    empty_future = client.get(
        f"/api/movements/audit-log?data_da={tomorrow.isoformat()}",
        headers=auth_headers,
    )
    assert empty_future.status_code == 200
    assert empty_future.json()["total"] == 0
    assert empty_future.json()["items"] == []

