"""Workspace today endpoint tests."""

from datetime import date, datetime, timedelta

from sqlmodel import select

from api.models.client import Client
from api.models.contract import Contract
from api.models.measurement import ClientMeasurement
from api.models.trainer import Trainer
from api.models.workout import WorkoutPlan
from api.services.workspace_engine import build_workspace_case_list, build_workspace_today


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


def _create_contract_with_rate_plan(
    client,
    headers,
    client_id,
    *,
    first_due: date,
    numero_rate: int = 2,
    frequenza: str = "SETTIMANALE",
):
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
            "numero_rate": numero_rate,
            "data_prima_rata": first_due.isoformat(),
            "frequenza": frequenza,
        },
        headers=headers,
    )
    assert rate_response.status_code == 201, rate_response.text
    return contract, rate_response.json()["items"]


def _create_contract_with_overdue_plan(client, headers, client_id):
    return _create_contract_with_rate_plan(
        client,
        headers,
        client_id,
        first_due=date.today() - timedelta(days=20),
    )


def _create_event(client, headers, *, client_id, contract_id=None, title, start_at=None):
    start_at = start_at or (datetime.now() + timedelta(minutes=30))
    end_at = start_at + timedelta(hours=1)
    payload = {
        "data_inizio": start_at.isoformat(),
        "data_fine": end_at.isoformat(),
        "categoria": "PT",
        "titolo": title,
        "id_cliente": client_id,
        "stato": "Programmato",
    }
    if contract_id is not None:
        payload["id_contratto"] = contract_id
    response = client.post(
        "/api/events",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_recurring_expense(
    client,
    headers,
    *,
    nome="Affitto Studio",
    categoria="Affitto",
    importo=650.0,
    giorno_scadenza=None,
    frequenza="MENSILE",
    data_inizio=None,
):
    today = date.today()
    payload = {
        "nome": nome,
        "categoria": categoria,
        "importo": importo,
        "giorno_scadenza": giorno_scadenza or today.day,
        "frequenza": frequenza,
        "data_inizio": data_inizio or today.replace(day=1).isoformat(),
    }
    response = client.post("/api/recurring-expenses", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def _trainer_id(session) -> int:
    trainer = session.exec(select(Trainer).where(Trainer.email == "test@test.com")).one()
    assert trainer.id is not None
    return trainer.id


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
    assert "client_reactivation" in case_kinds

    todo_case = next(case for case in all_cases if case["case_kind"] == "todo_manual")
    assert todo_case["root_entity"]["id"] == open_todo["id"]

    overdue_case = next(case for case in all_cases if case["case_kind"] == "payment_overdue")
    assert overdue_case["root_entity"]["id"] == contract["id"]
    assert overdue_case["finance_context"]["visibility"] == "redacted"
    assert overdue_case["finance_context"]["total_due_amount"] is None
    assert overdue_case["signal_count"] == len(rates)

    onboarding_case = next(case for case in all_cases if case["case_kind"] == "onboarding_readiness")
    assert onboarding_case["root_entity"]["id"] == onboarding_client["id"]
    assert onboarding_case["signal_count"] >= 2

    reactivation_case = next(case for case in all_cases if case["case_kind"] == "client_reactivation")
    assert reactivation_case["root_entity"]["id"] == inactive_client["id"]

    agenda_titles = [item["title"] for item in data["agenda"]["items"]]
    assert "Sessione premium" in agenda_titles

    renewals_response = client.get(
        "/api/workspace/cases",
        params={"workspace": "renewals_cash", "case_kind": "contract_renewal_due", "page_size": 20},
        headers=auth_headers,
    )
    assert renewals_response.status_code == 200, renewals_response.text
    renewal_items = renewals_response.json()["items"]
    assert renewal_items
    renewal_case = next(item for item in renewal_items if item["root_entity"]["id"] == contract["id"])
    assert renewal_case["finance_context"]["visibility"] == "full"


def test_workspace_renewals_cash_includes_payment_due_soon_but_keeps_it_out_of_today(client, auth_headers):
    due_client = _create_client(
        client,
        auth_headers,
        "Sara",
        "Scadenza",
        anamnesi=_structured_anamnesi(),
    )
    contract, _rates = _create_contract_with_rate_plan(
        client,
        auth_headers,
        due_client["id"],
        first_due=date.today() + timedelta(days=2),
        numero_rate=1,
    )

    due_soon_response = client.get(
        "/api/workspace/cases",
        params={"workspace": "renewals_cash", "case_kind": "payment_due_soon", "page_size": 20},
        headers=auth_headers,
    )
    assert due_soon_response.status_code == 200, due_soon_response.text
    due_soon_items = due_soon_response.json()["items"]
    due_soon_case = next(item for item in due_soon_items if item["root_entity"]["id"] == contract["id"])
    assert due_soon_case["bucket"] == "upcoming_3d"
    assert due_soon_case["finance_context"]["visibility"] == "full"
    assert due_soon_case["finance_context"]["total_due_amount"] == 600.0
    assert "scadenza" in due_soon_case["reason"].lower()

    detail_response = client.get(
        f"/api/workspace/cases/{due_soon_case['case_id']}",
        params={"workspace": "renewals_cash"},
        headers=auth_headers,
    )
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["case"]["case_kind"] == "payment_due_soon"
    assert detail["signals"]

    today_response = client.get("/api/workspace/today", headers=auth_headers)
    assert today_response.status_code == 200, today_response.text
    today_case_kinds = {
        case["case_kind"]
        for section in today_response.json()["sections"]
        for case in section["items"]
    }
    assert "payment_due_soon" not in today_case_kinds

    today_list_response = client.get(
        "/api/workspace/cases",
        params={"workspace": "today", "case_kind": "payment_due_soon", "page_size": 20},
        headers=auth_headers,
    )
    assert today_list_response.status_code == 200, today_list_response.text
    assert today_list_response.json()["total"] == 0


def test_workspace_renewals_cash_suppresses_payment_due_soon_when_contract_has_overdue(client, auth_headers):
    mixed_client = _create_client(
        client,
        auth_headers,
        "Marco",
        "Misto",
        anamnesi=_structured_anamnesi(),
    )
    contract, _rates = _create_contract_with_rate_plan(
        client,
        auth_headers,
        mixed_client["id"],
        first_due=date.today() - timedelta(days=1),
        numero_rate=2,
    )

    overdue_response = client.get(
        "/api/workspace/cases",
        params={"workspace": "renewals_cash", "case_kind": "payment_overdue", "page_size": 20},
        headers=auth_headers,
    )
    assert overdue_response.status_code == 200, overdue_response.text
    overdue_items = overdue_response.json()["items"]
    assert any(item["root_entity"]["id"] == contract["id"] for item in overdue_items)

    due_soon_response = client.get(
        "/api/workspace/cases",
        params={"workspace": "renewals_cash", "case_kind": "payment_due_soon", "page_size": 20},
        headers=auth_headers,
    )
    assert due_soon_response.status_code == 200, due_soon_response.text
    due_soon_items = due_soon_response.json()["items"]
    assert not any(item["root_entity"]["id"] == contract["id"] for item in due_soon_items)


def test_workspace_renewals_cash_includes_recurring_expense_due_and_removes_it_after_confirm(
    client,
    auth_headers,
):
    expense = _create_recurring_expense(
        client,
        auth_headers,
        nome="Affitto Sala PT",
        importo=720.0,
    )
    today = date.today()

    pending_response = client.get(
        "/api/movements/pending-expenses",
        params={"anno": today.year, "mese": today.month},
        headers=auth_headers,
    )
    assert pending_response.status_code == 200, pending_response.text
    pending_items = pending_response.json()["items"]
    pending_item = next(item for item in pending_items if item["id_spesa"] == expense["id"])

    finance_response = client.get(
        "/api/workspace/cases",
        params={"workspace": "renewals_cash", "case_kind": "recurring_expense_due", "page_size": 20},
        headers=auth_headers,
    )
    assert finance_response.status_code == 200, finance_response.text
    finance_items = finance_response.json()["items"]
    finance_case = next(item for item in finance_items if item["root_entity"]["id"] == expense["id"])
    assert finance_case["bucket"] == "today"
    assert finance_case["finance_context"]["visibility"] == "full"
    assert finance_case["finance_context"]["total_due_amount"] == 720.0
    assert pending_item["mese_anno_key"] in finance_case["case_id"]

    detail_response = client.get(
        f"/api/workspace/cases/{finance_case['case_id']}",
        params={"workspace": "renewals_cash"},
        headers=auth_headers,
    )
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["case"]["case_kind"] == "recurring_expense_due"
    assert detail["signals"]
    assert any(signal["signal_code"] == "recurring_expense_due" for signal in detail["signals"])

    today_response = client.get(
        "/api/workspace/cases",
        params={"workspace": "today", "case_kind": "recurring_expense_due", "page_size": 20},
        headers=auth_headers,
    )
    assert today_response.status_code == 200, today_response.text
    assert today_response.json()["total"] == 0

    confirm_response = client.post(
        "/api/movements/confirm-expenses",
        json={
            "items": [
                {
                    "id_spesa": pending_item["id_spesa"],
                    "mese_anno_key": pending_item["mese_anno_key"],
                }
            ]
        },
        headers=auth_headers,
    )
    assert confirm_response.status_code == 200, confirm_response.text
    assert confirm_response.json()["created"] == 1

    pending_after_response = client.get(
        "/api/movements/pending-expenses",
        params={"anno": today.year, "mese": today.month},
        headers=auth_headers,
    )
    assert pending_after_response.status_code == 200, pending_after_response.text
    pending_after_items = pending_after_response.json()["items"]
    assert not any(item["id_spesa"] == expense["id"] for item in pending_after_items)

    finance_after_response = client.get(
        "/api/workspace/cases",
        params={"workspace": "renewals_cash", "case_kind": "recurring_expense_due", "page_size": 20},
        headers=auth_headers,
    )
    assert finance_after_response.status_code == 200, finance_after_response.text
    finance_after_items = finance_after_response.json()["items"]
    assert not any(item["root_entity"]["id"] == expense["id"] for item in finance_after_items)


def test_workspace_today_session_absorbs_onboarding_blockers(client, auth_headers):
    blocked_client = _create_client(
        client,
        auth_headers,
        "Teresa",
        "Bloccata",
        anamnesi=_structured_anamnesi(),
    )
    event = _create_event(
        client,
        auth_headers,
        client_id=blocked_client["id"],
        title="Sessione con blocker",
    )

    today_response = client.get("/api/workspace/today", headers=auth_headers)
    assert today_response.status_code == 200, today_response.text
    sections = today_response.json()["sections"]
    all_cases = [case for section in sections for case in section["items"]]

    session_case = next(case for case in all_cases if case["case_kind"] == "session_imminent")
    assert session_case["root_entity"]["id"] == event["id"]
    assert session_case["secondary_entity"]["id"] == blocked_client["id"]
    assert session_case["signal_count"] >= 3
    assert "cliente da preparare" in session_case["reason"].lower()

    assert not any(
        case["case_kind"] == "onboarding_readiness" and case["root_entity"]["id"] == blocked_client["id"]
        for case in all_cases
    )

    detail_response = client.get(
        f"/api/workspace/cases/{session_case['case_id']}",
        params={"workspace": "today"},
        headers=auth_headers,
    )
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    signal_codes = {signal["signal_code"] for signal in detail["signals"]}
    assert {"baseline", "workout"}.issubset(signal_codes)


def test_workspace_today_degrades_complete_legacy_anamnesi_out_of_today(
    client,
    auth_headers,
    session,
):
    trainer_id = _trainer_id(session)
    legacy_client = _create_client(
        client,
        auth_headers,
        "Anamnesi",
        "Legacy",
        anamnesi={"note": "legacy"},
    )

    session.add(
        ClientMeasurement(
            id_cliente=legacy_client["id"],
            trainer_id=trainer_id,
            data_misurazione=date(2026, 3, 2),
        )
    )
    session.add(
        WorkoutPlan(
            trainer_id=trainer_id,
            id_cliente=legacy_client["id"],
            nome="Scheda attiva",
            obiettivo="generale",
            livello="beginner",
            created_at="2026-03-01",
            updated_at="2026-03-01",
        )
    )
    session.commit()

    reference_dt = datetime(2026, 3, 9, 9, 0)
    today_workspace = build_workspace_today(
        trainer_id=trainer_id,
        session=session,
        reference_dt=reference_dt,
    )
    visible_today_ids = {
        int(case.root_entity.id)
        for section in today_workspace.sections
        if section.bucket in {"now", "today", "upcoming_3d", "upcoming_7d"}
        for case in section.items
        if case.case_kind == "onboarding_readiness"
    }
    assert legacy_client["id"] not in visible_today_ids

    waiting_section = next(section for section in today_workspace.sections if section.bucket == "waiting")
    waiting_case = next(
        case
        for case in waiting_section.items
        if case.case_kind == "onboarding_readiness" and int(case.root_entity.id) == legacy_client["id"]
    )
    assert waiting_case.title == "Anamnesi da rivedere: Anamnesi Legacy"
    assert waiting_case.severity == "low"

    today_case_list = build_workspace_case_list(
        trainer_id=trainer_id,
        session=session,
        workspace="today",
        case_kind="onboarding_readiness",
        page_size=20,
        reference_dt=reference_dt,
    )
    today_ids = [int(item.root_entity.id) for item in today_case_list.items]
    assert legacy_client["id"] not in today_ids

    onboarding_case_list = build_workspace_case_list(
        trainer_id=trainer_id,
        session=session,
        workspace="onboarding",
        case_kind="onboarding_readiness",
        page_size=20,
        reference_dt=reference_dt,
    )
    onboarding_case = next(item for item in onboarding_case_list.items if int(item.root_entity.id) == legacy_client["id"])
    assert onboarding_case.bucket == "waiting"
    assert onboarding_case.title == "Anamnesi da rivedere: Anamnesi Legacy"


def test_workspace_today_degrades_stale_incomplete_onboarding_without_operational_pressure(
    client,
    auth_headers,
    session,
):
    trainer_id = _trainer_id(session)
    stale_client = _create_client(
        client,
        auth_headers,
        "Stale",
        "Onboarding",
        anamnesi={"note": "legacy"},
    )
    client_row = session.get(Client, stale_client["id"])
    assert client_row is not None
    client_row.data_creazione = datetime(2025, 12, 1, 9, 0)
    session.add(client_row)
    session.commit()

    reference_dt = datetime(2026, 3, 9, 9, 0)
    today_case_list = build_workspace_case_list(
        trainer_id=trainer_id,
        session=session,
        workspace="today",
        case_kind="onboarding_readiness",
        page_size=20,
        reference_dt=reference_dt,
    )
    today_ids = [int(item.root_entity.id) for item in today_case_list.items]
    assert stale_client["id"] not in today_ids

    onboarding_case_list = build_workspace_case_list(
        trainer_id=trainer_id,
        session=session,
        workspace="onboarding",
        case_kind="onboarding_readiness",
        page_size=20,
        reference_dt=reference_dt,
    )
    onboarding_case = next(item for item in onboarding_case_list.items if int(item.root_entity.id) == stale_client["id"])
    assert onboarding_case.bucket == "waiting"
    assert onboarding_case.severity == "high"


def test_workspace_today_keeps_incomplete_onboarding_visible_with_recent_contract(
    client,
    auth_headers,
    session,
):
    trainer_id = _trainer_id(session)
    recent_client = _create_client(
        client,
        auth_headers,
        "Recent",
        "Onboarding",
        anamnesi={"note": "legacy"},
    )
    session.add(
        Contract(
            trainer_id=trainer_id,
            id_cliente=recent_client["id"],
            tipo_pacchetto="Starter",
            data_vendita=date(2026, 3, 8),
            data_inizio=date(2026, 3, 9),
            data_scadenza=date(2026, 4, 9),
            crediti_totali=8,
            totale_versato=0.0,
            chiuso=False,
        )
    )
    session.commit()

    reference_dt = datetime(2026, 3, 9, 9, 0)
    today_case_list = build_workspace_case_list(
        trainer_id=trainer_id,
        session=session,
        workspace="today",
        case_kind="onboarding_readiness",
        page_size=20,
        reference_dt=reference_dt,
    )
    recent_case = next(item for item in today_case_list.items if int(item.root_entity.id) == recent_client["id"])
    assert recent_case.bucket == "today"
    assert recent_case.severity == "high"


def test_workspace_today_orders_sessions_by_actual_start_time(client, auth_headers, session):
    first_client = _create_client(
        client,
        auth_headers,
        "Riccardo",
        "De Luca",
        anamnesi=_structured_anamnesi(),
    )
    second_client = _create_client(
        client,
        auth_headers,
        "Stefano",
        "Leone",
        anamnesi=_structured_anamnesi(),
    )
    third_client = _create_client(
        client,
        auth_headers,
        "Matteo",
        "Barbieri",
        anamnesi=_structured_anamnesi(),
    )

    reference_dt = datetime(2026, 3, 9, 9, 0)
    _create_event(
        client,
        auth_headers,
        client_id=third_client["id"],
        title="PT Matteo Barbieri",
        start_at=datetime(2026, 3, 9, 16, 0),
    )
    _create_event(
        client,
        auth_headers,
        client_id=first_client["id"],
        title="PT Riccardo De Luca",
        start_at=datetime(2026, 3, 9, 10, 0),
    )
    _create_event(
        client,
        auth_headers,
        client_id=second_client["id"],
        title="PT Stefano Leone",
        start_at=datetime(2026, 3, 9, 11, 0),
    )

    workspace = build_workspace_today(
        trainer_id=_trainer_id(session),
        session=session,
        reference_dt=reference_dt,
    )

    session_titles = [
        case.title
        for section in workspace.sections
        for case in section.items
        if case.case_kind == "session_imminent"
    ]
    assert session_titles[:3] == [
        "PT Riccardo De Luca",
        "PT Stefano Leone",
        "PT Matteo Barbieri",
    ]


def test_workspace_today_applies_backend_viewport_budget_without_truncating_case_list(
    client,
    auth_headers,
    session,
):
    for index in range(5):
        _create_todo(
            client,
            auth_headers,
            f"Todo operativo {index + 1}",
            date(2026, 3, 9),
        )

    reference_dt = datetime(2026, 3, 9, 9, 0)
    today_workspace = build_workspace_today(
        trainer_id=_trainer_id(session),
        session=session,
        reference_dt=reference_dt,
    )
    today_section = next(section for section in today_workspace.sections if section.bucket == "today")
    assert today_section.total == 5
    assert len(today_section.items) == 2
    assert today_workspace.focus_case is not None
    assert today_workspace.focus_case.case_id == today_section.items[0].case_id

    case_list = build_workspace_case_list(
        trainer_id=_trainer_id(session),
        session=session,
        workspace="today",
        bucket="today",
        case_kind="todo_manual",
        page_size=20,
        reference_dt=reference_dt,
    )
    assert case_list.total == 5
    assert len(case_list.items) == 5


def test_workspace_today_hides_due_today_manual_todos_when_now_has_structural_cases(
    client,
    auth_headers,
    session,
):
    due_today_todo = _create_todo(client, auth_headers, "Richiama lead", date(2026, 3, 9))
    session_client = _create_client(
        client,
        auth_headers,
        "Now",
        "Client",
        anamnesi=_structured_anamnesi(),
    )
    _create_event(
        client,
        auth_headers,
        client_id=session_client["id"],
        title="PT adesso",
        start_at=datetime(2026, 3, 9, 9, 30),
    )

    reference_dt = datetime(2026, 3, 9, 9, 45)
    today_workspace = build_workspace_today(
        trainer_id=_trainer_id(session),
        session=session,
        reference_dt=reference_dt,
    )

    now_section = next(section for section in today_workspace.sections if section.bucket == "now")
    assert any(case.case_kind == "session_imminent" for case in now_section.items)

    today_section = next(section for section in today_workspace.sections if section.bucket == "today")
    assert today_section.total == 1
    assert all(case.case_kind != "todo_manual" for case in today_section.items)

    case_list = build_workspace_case_list(
        trainer_id=_trainer_id(session),
        session=session,
        workspace="today",
        bucket="today",
        case_kind="todo_manual",
        page_size=20,
        reference_dt=reference_dt,
    )
    assert case_list.total == 1
    assert case_list.items[0].root_entity.id == due_today_todo["id"]


def test_workspace_today_pushes_reactivation_to_later_and_caps_visible_backlog(
    client,
    auth_headers,
    session,
):
    for index in range(4):
        _create_client(
            client,
            auth_headers,
            f"Reactivation{index + 1}",
            "Client",
            anamnesi=_structured_anamnesi(),
        )

    session_client = _create_client(
        client,
        auth_headers,
        "Session",
        "Client",
        anamnesi=_structured_anamnesi(),
    )
    _create_event(
        client,
        auth_headers,
        client_id=session_client["id"],
        title="PT adesso",
        start_at=datetime(2026, 3, 9, 9, 30),
    )

    reference_dt = datetime(2026, 3, 9, 9, 45)
    today_workspace = build_workspace_today(
        trainer_id=_trainer_id(session),
        session=session,
        reference_dt=reference_dt,
    )

    today_section = next(section for section in today_workspace.sections if section.bucket == "today")
    assert all(case.case_kind != "client_reactivation" for case in today_section.items)

    upcoming_section = next(section for section in today_workspace.sections if section.bucket == "upcoming_7d")
    assert upcoming_section.total == 4
    assert len(upcoming_section.items) == 1
    assert all(case.case_kind == "client_reactivation" for case in upcoming_section.items)

    case_list = build_workspace_case_list(
        trainer_id=_trainer_id(session),
        session=session,
        workspace="today",
        case_kind="client_reactivation",
        page_size=20,
        reference_dt=reference_dt,
    )
    assert case_list.total == 4
    assert len(case_list.items) == 4


def test_workspace_today_undated_manual_todos_do_not_enter_today_case_list(
    client,
    auth_headers,
    session,
):
    undated_todo = _create_todo(client, auth_headers, "Promemoria senza data")
    due_today_todo = _create_todo(client, auth_headers, "Promemoria con data", date(2026, 3, 9))

    reference_dt = datetime(2026, 3, 9, 9, 0)
    case_list = build_workspace_case_list(
        trainer_id=_trainer_id(session),
        session=session,
        workspace="today",
        case_kind="todo_manual",
        page_size=20,
        reference_dt=reference_dt,
    )

    returned_ids = [int(item.root_entity.id) for item in case_list.items]
    assert due_today_todo["id"] in returned_ids
    assert undated_todo["id"] not in returned_ids


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
