"""Dashboard clinical readiness queue tests."""

from datetime import date

from sqlmodel import select

from api.models.measurement import ClientMeasurement
from api.models.trainer import Trainer
from api.models.workout import WorkoutPlan


def _create_client(client, headers, nome, cognome, anamnesi=None):
    payload = {
        "nome": nome,
        "cognome": cognome,
    }
    if anamnesi is not None:
        payload["anamnesi"] = anamnesi

    response = client.post("/api/clients", json=payload, headers=headers)
    assert response.status_code == 201, f"Client creation failed: {response.text}"
    return response.json()


def _structured_anamnesi():
    return {
        "infortuni_attuali": {"presente": False, "dettaglio": None},
        "data_compilazione": "2026-03-01",
    }


def test_clinical_readiness_prioritizes_missing_and_legacy(client, auth_headers, session):
    """Queue ordering and counters must be deterministic across readiness states."""
    trainer = session.exec(
        select(Trainer).where(Trainer.email == "test@test.com")
    ).first()
    assert trainer is not None
    assert trainer.id is not None

    c_missing = _create_client(client, auth_headers, "Alpha", "Missing")
    c_legacy = _create_client(client, auth_headers, "Beta", "Legacy", anamnesi={"note": "old"})
    c_workout_missing = _create_client(
        client,
        auth_headers,
        "Gamma",
        "Workout",
        anamnesi=_structured_anamnesi(),
    )
    c_ready = _create_client(
        client,
        auth_headers,
        "Delta",
        "Ready",
        anamnesi=_structured_anamnesi(),
    )

    # c_workout_missing: has baseline, no workout
    session.add(
        ClientMeasurement(
            id_cliente=c_workout_missing["id"],
            trainer_id=trainer.id,
            data_misurazione=date(2026, 3, 1),
        )
    )

    # c_ready: baseline + workout assigned
    session.add(
        ClientMeasurement(
            id_cliente=c_ready["id"],
            trainer_id=trainer.id,
            data_misurazione=date(2026, 3, 2),
        )
    )
    session.add(
        WorkoutPlan(
            trainer_id=trainer.id,
            id_cliente=c_ready["id"],
            nome="Ready plan",
            obiettivo="generale",
            livello="beginner",
        )
    )
    session.commit()

    response = client.get("/api/dashboard/clinical-readiness", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    summary = data["summary"]
    items = data["items"]

    assert summary["total_clients"] == 4
    assert summary["ready_clients"] == 1
    assert summary["missing_anamnesi"] == 1
    assert summary["legacy_anamnesi"] == 1
    assert summary["missing_measurements"] == 2
    assert summary["missing_workout_plan"] == 3
    assert summary["high_priority"] == 2
    assert summary["medium_priority"] == 1
    assert summary["low_priority"] == 1

    # Priority order: missing anamnesi -> legacy anamnesi -> missing workout -> ready
    assert items[0]["client_id"] == c_missing["id"]
    assert items[0]["next_action_code"] == "collect_anamnesi"
    assert items[0]["next_action_href"] == f"/clienti/{c_missing['id']}/anamnesi?startWizard=1"
    assert items[0]["priority"] == "high"
    assert items[0]["timeline_reason"] == "anamnesi_missing"
    assert items[0]["timeline_label"] == "Anamnesi mancante"
    assert items[0]["timeline_status"] == "today"
    assert items[0]["next_due_date"] == date.today().isoformat()
    assert items[0]["days_to_due"] == 0
    assert items[0]["measurement_freshness"]["status"] == "missing"
    assert items[0]["workout_freshness"]["status"] == "missing"

    assert items[1]["client_id"] == c_legacy["id"]
    assert items[1]["next_action_code"] == "migrate_anamnesi"
    assert items[1]["next_action_href"] == f"/clienti/{c_legacy['id']}/anamnesi?startWizard=1"
    assert items[1]["priority"] == "high"
    assert items[1]["timeline_reason"] == "anamnesi_legacy"
    assert items[1]["timeline_label"] == "Anamnesi legacy da rivedere"
    assert items[1]["timeline_status"] == "today"
    assert items[1]["next_due_date"] == date.today().isoformat()
    assert items[1]["days_to_due"] == 0

    assert items[2]["client_id"] == c_workout_missing["id"]
    assert items[2]["next_action_code"] == "assign_workout"
    assert items[2]["next_action_href"] == f"/clienti/{c_workout_missing['id']}?tab=schede&startScheda=1"
    assert items[2]["priority"] == "medium"
    assert items[2]["timeline_reason"] == "workout_missing"
    assert items[2]["timeline_label"] == "Nessuna scheda assegnata"
    assert items[2]["timeline_status"] == "today"
    assert items[2]["next_due_date"] == date.today().isoformat()
    assert items[2]["days_to_due"] == 0
    assert items[2]["measurement_freshness"]["status"] == "ok"
    assert items[2]["measurement_freshness"]["reason_code"] == "measurement_review"
    assert items[2]["workout_freshness"]["status"] == "missing"

    expected_ready_due = date(2026, 3, 2) + date.resolution * 25
    expected_ready_days = (expected_ready_due - date.today()).days
    assert items[3]["client_id"] == c_ready["id"]
    assert items[3]["next_action_code"] == "ready"
    assert items[3]["readiness_score"] == 100
    assert items[3]["priority"] == "low"
    assert items[3]["timeline_reason"] == "measurement_review"
    assert items[3]["timeline_label"] == f"Review misurazioni tra {expected_ready_days} giorni"
    assert items[3]["next_due_date"] == expected_ready_due.isoformat()
    assert items[3]["measurement_freshness"]["status"] == "ok"
    assert items[3]["measurement_freshness"]["due_date"] == expected_ready_due.isoformat()
    assert items[3]["workout_freshness"]["status"] == "ok"


def test_clinical_readiness_enforces_trainer_isolation(client, auth_headers):
    """Endpoint must only expose active clients belonging to the authenticated trainer."""
    own_client = _create_client(client, auth_headers, "Mario", "Owner")

    register_other = client.post(
        "/api/auth/register",
        json={
            "email": "other@test.com",
            "nome": "Other",
            "cognome": "Trainer",
            "password": "testpass123",
        },
    )
    assert register_other.status_code == 201
    other_headers = {"Authorization": f"Bearer {register_other.json()['access_token']}"}

    other_client = _create_client(client, other_headers, "Luigi", "Other")

    response = client.get("/api/dashboard/clinical-readiness", headers=auth_headers)
    assert response.status_code == 200
    ids = [item["client_id"] for item in response.json()["items"]]

    assert own_client["id"] in ids
    assert other_client["id"] not in ids


def test_clinical_readiness_exposes_shared_measurement_and_workout_freshness(client, auth_headers, session):
    """Readiness payload must expose the same freshness policy for measurements and workout reviews."""
    trainer = session.exec(
        select(Trainer).where(Trainer.email == "test@test.com")
    ).first()
    assert trainer is not None
    assert trainer.id is not None

    today = date.today()
    stale_client = _create_client(
        client,
        auth_headers,
        "Freshness",
        "Policy",
        anamnesi=_structured_anamnesi(),
    )

    session.add(
        ClientMeasurement(
            id_cliente=stale_client["id"],
            trainer_id=trainer.id,
            data_misurazione=today - date.resolution * 28,
        )
    )
    session.add(
        WorkoutPlan(
            trainer_id=trainer.id,
            id_cliente=stale_client["id"],
            nome="Policy plan",
            obiettivo="generale",
            livello="beginner",
            created_at=(today - date.resolution * 36).isoformat(),
            updated_at=(today - date.resolution * 36).isoformat(),
        )
    )
    session.commit()

    response = client.get("/api/dashboard/clinical-readiness", headers=auth_headers)
    assert response.status_code == 200
    item = next(entry for entry in response.json()["items"] if entry["client_id"] == stale_client["id"])

    assert item["next_action_code"] == "ready"
    assert item["measurement_freshness"]["status"] == "warning"
    assert item["measurement_freshness"]["timeline_status"] == "overdue"
    assert item["measurement_freshness"]["days_since_last"] == 28
    assert item["measurement_freshness"]["reason_code"] == "measurement_review"

    assert item["workout_freshness"]["status"] == "critical"
    assert item["workout_freshness"]["timeline_status"] == "overdue"
    assert item["workout_freshness"]["days_since_last"] == 36
    assert item["workout_freshness"]["reason_code"] == "workout_stale"

    expected_workout_due = today - date.resolution * 15
    assert item["next_due_date"] == expected_workout_due.isoformat()
    assert item["timeline_reason"] == "workout_stale"
    assert item["timeline_label"].startswith("Scheda da aggiornare")


def test_clinical_readiness_worklist_supports_pagination_and_filters(client, auth_headers, session):
    """Worklist endpoint must support server-side pagination and deterministic filters."""
    trainer = session.exec(
        select(Trainer).where(Trainer.email == "test@test.com")
    ).first()
    assert trainer is not None
    assert trainer.id is not None

    c_missing = _create_client(client, auth_headers, "Arianna", "Rossi")
    c_legacy = _create_client(client, auth_headers, "Bruno", "Bianchi", anamnesi={"note": "legacy"})
    c_workout_missing = _create_client(
        client,
        auth_headers,
        "Chiara",
        "Verdi",
        anamnesi=_structured_anamnesi(),
    )
    c_ready = _create_client(
        client,
        auth_headers,
        "Diego",
        "Neri",
        anamnesi=_structured_anamnesi(),
    )
    c_ready_two = _create_client(
        client,
        auth_headers,
        "Elena",
        "Marini",
        anamnesi=_structured_anamnesi(),
    )

    session.add(
        ClientMeasurement(
            id_cliente=c_workout_missing["id"],
            trainer_id=trainer.id,
            data_misurazione=date(2026, 3, 1),
        )
    )
    session.add(
        ClientMeasurement(
            id_cliente=c_ready["id"],
            trainer_id=trainer.id,
            data_misurazione=date(2026, 3, 2),
        )
    )
    session.add(
        ClientMeasurement(
            id_cliente=c_ready_two["id"],
            trainer_id=trainer.id,
            data_misurazione=date(2026, 3, 3),
        )
    )
    session.add(
        WorkoutPlan(
            trainer_id=trainer.id,
            id_cliente=c_ready["id"],
            nome="Ready plan 1",
            obiettivo="generale",
            livello="beginner",
        )
    )
    session.add(
        WorkoutPlan(
            trainer_id=trainer.id,
            id_cliente=c_ready_two["id"],
            nome="Ready plan 2",
            obiettivo="generale",
            livello="beginner",
        )
    )
    session.commit()

    page_one = client.get(
        "/api/dashboard/clinical-readiness/worklist",
        params={"view": "todo", "page": 1, "page_size": 2},
        headers=auth_headers,
    )
    assert page_one.status_code == 200
    page_one_data = page_one.json()

    assert page_one_data["summary"]["total_clients"] == 5
    assert page_one_data["total"] == 3
    assert page_one_data["page"] == 1
    assert page_one_data["page_size"] == 2
    assert [item["client_id"] for item in page_one_data["items"]] == [
        c_missing["id"],
        c_legacy["id"],
    ]

    page_two = client.get(
        "/api/dashboard/clinical-readiness/worklist",
        params={"view": "todo", "page": 2, "page_size": 2},
        headers=auth_headers,
    )
    assert page_two.status_code == 200
    page_two_data = page_two.json()
    assert page_two_data["total"] == 3
    assert len(page_two_data["items"]) == 1
    assert page_two_data["items"][0]["client_id"] == c_workout_missing["id"]

    high_priority = client.get(
        "/api/dashboard/clinical-readiness/worklist",
        params={"view": "all", "priority": "high", "page_size": 20},
        headers=auth_headers,
    )
    assert high_priority.status_code == 200
    high_priority_ids = [item["client_id"] for item in high_priority.json()["items"]]
    assert high_priority.json()["total"] == 2
    assert c_missing["id"] in high_priority_ids
    assert c_legacy["id"] in high_priority_ids

    timeline_today = client.get(
        "/api/dashboard/clinical-readiness/worklist",
        params={"view": "todo", "timeline_status": "today", "page_size": 20},
        headers=auth_headers,
    )
    assert timeline_today.status_code == 200
    assert timeline_today.json()["total"] == 3

    due_date_sorted = client.get(
        "/api/dashboard/clinical-readiness/worklist",
        params={"view": "all", "sort_by": "due_date", "page_size": 20},
        headers=auth_headers,
    )
    assert due_date_sorted.status_code == 200
    sorted_ids = [item["client_id"] for item in due_date_sorted.json()["items"]]
    assert sorted_ids[:3] == [c_missing["id"], c_legacy["id"], c_workout_missing["id"]]
    assert sorted_ids[3:] == [c_ready["id"], c_ready_two["id"]]

    search_by_name = client.get(
        "/api/dashboard/clinical-readiness/worklist",
        params={"view": "all", "search": "rossi", "page_size": 20},
        headers=auth_headers,
    )
    assert search_by_name.status_code == 200
    assert search_by_name.json()["total"] == 1
    assert search_by_name.json()["items"][0]["client_id"] == c_missing["id"]


def test_clinical_readiness_worklist_enforces_trainer_isolation(client, auth_headers):
    """Worklist endpoint must only return clients owned by authenticated trainer."""
    own_client = _create_client(client, auth_headers, "Mario", "Owner")

    register_other = client.post(
        "/api/auth/register",
        json={
            "email": "worklist_other@test.com",
            "nome": "Other",
            "cognome": "Trainer",
            "password": "testpass123",
        },
    )
    assert register_other.status_code == 201
    other_headers = {"Authorization": f"Bearer {register_other.json()['access_token']}"}

    other_client = _create_client(client, other_headers, "Luigi", "Other")

    response = client.get(
        "/api/dashboard/clinical-readiness/worklist",
        params={"view": "all", "page_size": 50},
        headers=auth_headers,
    )
    assert response.status_code == 200
    ids = [item["client_id"] for item in response.json()["items"]]

    assert own_client["id"] in ids
    assert other_client["id"] not in ids
