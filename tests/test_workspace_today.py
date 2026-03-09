"""Workspace today endpoint tests."""

from datetime import date, datetime, timedelta


def _structured_anamnesi():
    return {
        "data_compilazione": date.today().isoformat(),
        "obiettivo_principale": "massa_muscolare",
    }


def _create_client(client, headers, nome, cognome, anamnesi=None):
    payload = {"nome": nome, "cognome": cognome}
    if anamnesi is not None:
        payload["anamnesi"] = anamnesi
    response = client.post("/api/clients", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def _create_todo(client, headers, titolo, data_scadenza=None):
    payload = {"titolo": titolo}
    if data_scadenza is not None:
        payload["data_scadenza"] = data_scadenza.isoformat()
    response = client.post("/api/todos", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def _toggle_todo(client, headers, todo_id):
    response = client.patch(f"/api/todos/{todo_id}/toggle", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def _create_contract_with_overdue_plan(client, headers, client_id):
    today = date.today()
    contract_response = client.post(
        "/api/contracts",
        json={
            "id_cliente": client_id,
            "tipo_pacchetto": "Gold 10",
            "crediti_totali": 10,
            "prezzo_totale": 600.0,
            "data_inizio": (today - timedelta(days=30)).isoformat(),
            "data_scadenza": (today + timedelta(days=5)).isoformat(),
            "acconto": 0.0,
        },
        headers=headers,
    )
    assert contract_response.status_code == 201, contract_response.text
    contract = contract_response.json()

    rate_response = client.post(
        f"/api/rates/generate-plan/{contract['id']}",
        json={
            "importo_da_rateizzare": 600.0,
            "numero_rate": 2,
            "data_prima_rata": (today - timedelta(days=20)).isoformat(),
            "frequenza": "SETTIMANALE",
        },
        headers=headers,
    )
    assert rate_response.status_code == 201, rate_response.text
    return contract, rate_response.json()["items"]


def _create_event(client, headers, *, client_id, contract_id, title):
    start_at = datetime.utcnow() + timedelta(minutes=30)
    end_at = start_at + timedelta(hours=1)
    response = client.post(
        "/api/events",
        json={
            "data_inizio": start_at.isoformat(),
            "data_fine": end_at.isoformat(),
            "categoria": "PT",
            "titolo": title,
            "id_cliente": client_id,
            "id_contratto": contract_id,
            "stato": "Programmato",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_workspace_today_aggregates_real_sources(client, auth_headers):
    onboarding_client = _create_client(
        client,
        auth_headers,
        "Mario",
        "Onboarding",
        anamnesi=_structured_anamnesi(),
    )
    contract_client = _create_client(
        client,
        auth_headers,
        "Lucia",
        "Pagamenti",
        anamnesi=_structured_anamnesi(),
    )
    inactive_client = _create_client(
        client,
        auth_headers,
        "Gianni",
        "Fermo",
        anamnesi=_structured_anamnesi(),
    )

    open_todo = _create_todo(client, auth_headers, "Richiama fornitore", date.today())
    completed_todo = _create_todo(client, auth_headers, "Task completato", date.today())
    _toggle_todo(client, auth_headers, completed_todo["id"])

    contract, rates = _create_contract_with_overdue_plan(
        client,
        auth_headers,
        contract_client["id"],
    )
    event = _create_event(
        client,
        auth_headers,
        client_id=contract_client["id"],
        contract_id=contract["id"],
        title="Sessione premium",
    )

    response = client.get("/api/workspace/today", headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["summary"]["workspace"] == "today"
    assert data["focus_case"] is not None
    assert data["agenda"]["next_event_id"] == event["id"]
    assert data["completed_today_count"] == 1
    assert data["snoozed_count"] == 0

    all_cases = [case for section in data["sections"] for case in section["items"]]
    case_kinds = {case["case_kind"] for case in all_cases}

    assert "session_imminent" in case_kinds
    assert "onboarding_readiness" in case_kinds
    assert "todo_manual" in case_kinds
    assert "payment_overdue" in case_kinds
    assert "contract_renewal_due" in case_kinds
    assert "client_reactivation" in case_kinds

    todo_case = next(case for case in all_cases if case["case_kind"] == "todo_manual")
    assert todo_case["root_entity"]["id"] == open_todo["id"]

    overdue_case = next(case for case in all_cases if case["case_kind"] == "payment_overdue")
    assert overdue_case["root_entity"]["id"] == contract["id"]
    assert overdue_case["finance_context"]["visibility"] == "redacted"
    assert overdue_case["finance_context"]["total_due_amount"] is None
    assert overdue_case["signal_count"] == len(rates)

    renewal_case = next(case for case in all_cases if case["case_kind"] == "contract_renewal_due")
    assert renewal_case["root_entity"]["id"] == contract["id"]
    assert renewal_case["finance_context"]["visibility"] == "redacted"

    onboarding_case = next(case for case in all_cases if case["case_kind"] == "onboarding_readiness")
    assert onboarding_case["root_entity"]["id"] == onboarding_client["id"]
    assert onboarding_case["signal_count"] >= 2

    reactivation_case = next(case for case in all_cases if case["case_kind"] == "client_reactivation")
    assert reactivation_case["root_entity"]["id"] == inactive_client["id"]

    agenda_titles = [item["title"] for item in data["agenda"]["items"]]
    assert "Sessione premium" in agenda_titles


def test_workspace_today_enforces_trainer_isolation(client, auth_headers):
    own_client = _create_client(client, auth_headers, "Anna", "Owner", anamnesi=_structured_anamnesi())
    own_todo = _create_todo(client, auth_headers, "Todo owner", date.today())

    other_register = client.post(
        "/api/auth/register",
        json={
            "email": "workspace-other@test.com",
            "nome": "Other",
            "cognome": "Trainer",
            "password": "testpass123",
        },
    )
    assert other_register.status_code == 201
    other_headers = {"Authorization": f"Bearer {other_register.json()['access_token']}"}

    foreign_client = _create_client(
        client,
        other_headers,
        "Luca",
        "Foreign",
        anamnesi=_structured_anamnesi(),
    )
    _create_todo(client, other_headers, "Todo foreign", date.today())

    response = client.get("/api/workspace/today", headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()

    all_cases = [case for section in data["sections"] for case in section["items"]]
    titles = [case["title"] for case in all_cases]
    client_ids = [
        case["root_entity"]["id"]
        for case in all_cases
        if case["root_entity"]["type"] == "client"
    ]

    assert any(case["root_entity"]["id"] == own_todo["id"] for case in all_cases if case["case_kind"] == "todo_manual")
    assert own_client["id"] in client_ids
    assert foreign_client["id"] not in client_ids
    assert not any("foreign" in title.lower() for title in titles)


def test_workspace_cases_support_pagination_and_filters(client, auth_headers):
    onboarding_client = _create_client(
        client,
        auth_headers,
        "Paolo",
        "Onboarding",
        anamnesi=_structured_anamnesi(),
    )
    finance_client = _create_client(
        client,
        auth_headers,
        "Sara",
        "Cash",
        anamnesi=_structured_anamnesi(),
    )
    _create_todo(client, auth_headers, "Todo oggi", date.today())
    _create_todo(client, auth_headers, "Todo domani", date.today() + timedelta(days=1))
    contract, _rates = _create_contract_with_overdue_plan(client, auth_headers, finance_client["id"])
    _create_event(
        client,
        auth_headers,
        client_id=finance_client["id"],
        contract_id=contract["id"],
        title="Sessione filtrabile",
    )

    onboarding_page = client.get(
        "/api/workspace/cases",
        params={"workspace": "onboarding", "page": 1, "page_size": 20},
        headers=auth_headers,
    )
    assert onboarding_page.status_code == 200, onboarding_page.text
    onboarding_data = onboarding_page.json()
    assert onboarding_data["summary"]["workspace"] == "onboarding"
    assert onboarding_data["filters_applied"]["workspace"] == "onboarding"
    assert onboarding_data["total"] >= 1
    assert onboarding_data["items"][0]["case_kind"] == "onboarding_readiness"
    assert onboarding_data["items"][0]["root_entity"]["id"] == onboarding_client["id"]

    finance_page = client.get(
        "/api/workspace/cases",
        params={"workspace": "renewals_cash", "page": 1, "page_size": 20},
        headers=auth_headers,
    )
    assert finance_page.status_code == 200, finance_page.text
    finance_data = finance_page.json()
    finance_kinds = {item["case_kind"] for item in finance_data["items"]}
    assert "payment_overdue" in finance_kinds
    assert "contract_renewal_due" in finance_kinds

    overdue_only = client.get(
        "/api/workspace/cases",
        params={
            "workspace": "renewals_cash",
            "case_kind": "payment_overdue",
            "page": 1,
            "page_size": 20,
        },
        headers=auth_headers,
    )
    assert overdue_only.status_code == 200, overdue_only.text
    overdue_data = overdue_only.json()
    assert overdue_data["total"] >= 1
    assert all(item["case_kind"] == "payment_overdue" for item in overdue_data["items"])

    search_hit = client.get(
        "/api/workspace/cases",
        params={
            "workspace": "renewals_cash",
            "search": "sara cash",
            "page": 1,
            "page_size": 20,
        },
        headers=auth_headers,
    )
    assert search_hit.status_code == 200, search_hit.text
    assert search_hit.json()["total"] >= 1

    paged_today = client.get(
        "/api/workspace/cases",
        params={"workspace": "today", "page": 1, "page_size": 2},
        headers=auth_headers,
    )
    assert paged_today.status_code == 200, paged_today.text
    today_data = paged_today.json()
    assert today_data["page"] == 1
    assert today_data["page_size"] == 2
    assert today_data["total"] >= 3
    assert len(today_data["items"]) == 2


def test_workspace_cases_finance_visibility_depends_on_workspace(client, auth_headers):
    finance_client = _create_client(
        client,
        auth_headers,
        "Elisa",
        "Finance",
        anamnesi=_structured_anamnesi(),
    )
    contract, _rates = _create_contract_with_overdue_plan(client, auth_headers, finance_client["id"])

    today_response = client.get(
        "/api/workspace/cases",
        params={"workspace": "today", "case_kind": "payment_overdue", "page_size": 20},
        headers=auth_headers,
    )
    assert today_response.status_code == 200, today_response.text
    today_items = today_response.json()["items"]
    assert today_items
    today_case = next(item for item in today_items if item["root_entity"]["id"] == contract["id"])
    assert today_case["finance_context"]["visibility"] == "redacted"
    assert today_case["finance_context"]["total_due_amount"] is None
    assert today_case["finance_context"]["total_residual_amount"] is None

    finance_response = client.get(
        "/api/workspace/cases",
        params={"workspace": "renewals_cash", "case_kind": "payment_overdue", "page_size": 20},
        headers=auth_headers,
    )
    assert finance_response.status_code == 200, finance_response.text
    finance_items = finance_response.json()["items"]
    assert finance_items
    finance_case = next(item for item in finance_items if item["root_entity"]["id"] == contract["id"])
    assert finance_case["finance_context"]["visibility"] == "full"
    assert finance_case["finance_context"]["total_due_amount"] is not None
    assert finance_case["finance_context"]["total_residual_amount"] is not None


def test_workspace_case_detail_returns_onboarding_signals_and_activity(client, auth_headers):
    onboarding_client = _create_client(
        client,
        auth_headers,
        "Nadia",
        "Onboarding",
        anamnesi=_structured_anamnesi(),
    )
    case_id = f"case:onboarding_readiness:client:{onboarding_client['id']}"

    response = client.get(
        f"/api/workspace/cases/{case_id}",
        params={"workspace": "onboarding"},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["case"]["case_id"] == case_id
    assert data["case"]["workspace"] == "onboarding"
    assert data["case"]["root_entity"]["id"] == onboarding_client["id"]
    assert len(data["signals"]) >= 2
    assert {signal["signal_code"] for signal in data["signals"]}.issuperset({"baseline", "workout"})
    assert data["related_entities"] == [
        {
            "type": "client",
            "id": onboarding_client["id"],
            "label": "Nadia Onboarding",
            "href": f"/clienti/{onboarding_client['id']}",
        }
    ]
    assert len(data["activity_preview"]) >= 1


def test_workspace_case_detail_finance_visibility_depends_on_workspace(client, auth_headers):
    finance_client = _create_client(
        client,
        auth_headers,
        "Bianca",
        "Finance",
        anamnesi=_structured_anamnesi(),
    )
    contract, rates = _create_contract_with_overdue_plan(client, auth_headers, finance_client["id"])
    case_id = f"case:payment_overdue:contract:{contract['id']}"

    today_response = client.get(
        f"/api/workspace/cases/{case_id}",
        params={"workspace": "today"},
        headers=auth_headers,
    )
    assert today_response.status_code == 200, today_response.text
    today_data = today_response.json()
    assert today_data["case"]["finance_context"]["visibility"] == "redacted"
    assert today_data["case"]["finance_context"]["total_due_amount"] is None
    assert today_data["case"]["finance_context"]["total_residual_amount"] is None
    assert len(today_data["signals"]) == len(rates)
    assert {entity["type"] for entity in today_data["related_entities"]}.issuperset({"contract", "client"})
    assert len(today_data["activity_preview"]) >= 2

    finance_response = client.get(
        f"/api/workspace/cases/{case_id}",
        params={"workspace": "renewals_cash"},
        headers=auth_headers,
    )
    assert finance_response.status_code == 200, finance_response.text
    finance_data = finance_response.json()
    assert finance_data["case"]["finance_context"]["visibility"] == "full"
    assert finance_data["case"]["finance_context"]["total_due_amount"] is not None
    assert finance_data["case"]["finance_context"]["total_residual_amount"] is not None
    assert len(finance_data["signals"]) == len(rates)


def test_workspace_case_detail_enforces_scope_and_trainer_isolation(client, auth_headers):
    finance_client = _create_client(
        client,
        auth_headers,
        "Irene",
        "Scope",
        anamnesi=_structured_anamnesi(),
    )
    contract, _rates = _create_contract_with_overdue_plan(client, auth_headers, finance_client["id"])
    case_id = f"case:payment_overdue:contract:{contract['id']}"

    wrong_workspace = client.get(
        f"/api/workspace/cases/{case_id}",
        params={"workspace": "onboarding"},
        headers=auth_headers,
    )
    assert wrong_workspace.status_code == 404, wrong_workspace.text

    other_register = client.post(
        "/api/auth/register",
        json={
            "email": "workspace-detail-other@test.com",
            "nome": "Other",
            "cognome": "Trainer",
            "password": "testpass123",
        },
    )
    assert other_register.status_code == 201
    other_headers = {"Authorization": f"Bearer {other_register.json()['access_token']}"}
    foreign_client = _create_client(
        client,
        other_headers,
        "Giada",
        "Foreign",
        anamnesi=_structured_anamnesi(),
    )
    foreign_contract, _ = _create_contract_with_overdue_plan(client, other_headers, foreign_client["id"])
    foreign_case_id = f"case:payment_overdue:contract:{foreign_contract['id']}"

    foreign_detail = client.get(
        f"/api/workspace/cases/{foreign_case_id}",
        params={"workspace": "renewals_cash"},
        headers=auth_headers,
    )
    assert foreign_detail.status_code == 404, foreign_detail.text
