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
    assert items[0]["priority"] == "high"

    assert items[1]["client_id"] == c_legacy["id"]
    assert items[1]["next_action_code"] == "migrate_anamnesi"
    assert items[1]["priority"] == "high"

    assert items[2]["client_id"] == c_workout_missing["id"]
    assert items[2]["next_action_code"] == "assign_workout"
    assert items[2]["next_action_href"] == f"/clienti/{c_workout_missing['id']}?tab=schede"
    assert items[2]["priority"] == "medium"

    assert items[3]["client_id"] == c_ready["id"]
    assert items[3]["next_action_code"] == "ready"
    assert items[3]["readiness_score"] == 100
    assert items[3]["priority"] == "low"


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
