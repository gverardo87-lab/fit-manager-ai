from datetime import date, datetime, timedelta, timezone

from sqlmodel import select

from api.models.goal import ClientGoal
from api.models.measurement import Metric
from api.models.trainer import Trainer
from api.models.workout import WorkoutPlan, WorkoutSession
from api.models.workout_log import WorkoutLog


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


def _create_contract(client, headers, client_id):
    response = client.post(
        "/api/contracts",
        json={
            "id_cliente": client_id,
            "tipo_pacchetto": "Gold 10",
            "crediti_totali": 10,
            "prezzo_totale": 1000.0,
            "data_inizio": "2026-01-01",
            "data_scadenza": "2026-12-31",
            "acconto": 200.0,
            "metodo_acconto": "CONTANTI",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_event(
    client,
    headers,
    *,
    client_id,
    title,
    start_at,
    category="PT",
    contract_id=None,
    status="Programmato",
):
    payload = {
        "data_inizio": start_at.isoformat(),
        "data_fine": (start_at + timedelta(hours=1)).isoformat(),
        "categoria": category,
        "titolo": title,
        "id_cliente": client_id,
        "stato": status,
    }
    if contract_id is not None:
        payload["id_contratto"] = contract_id
    response = client.post("/api/events", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def _trainer_id(session) -> int:
    session.expire_all()
    trainer = session.exec(select(Trainer).where(Trainer.email == "test@test.com")).one()
    assert trainer.id is not None
    return trainer.id


def _seed_workout_bundle(session, *, trainer_id: int, client_id: int) -> None:
    today = date.today()
    active_plan = WorkoutPlan(
        trainer_id=trainer_id,
        id_cliente=client_id,
        nome="Forza Primavera",
        obiettivo="forza",
        livello="intermedio",
        durata_settimane=8,
        sessioni_per_settimana=3,
        data_inizio=today - timedelta(days=7),
        data_fine=today + timedelta(days=21),
        created_at=(datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        updated_at=(datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
    )
    completed_plan = WorkoutPlan(
        trainer_id=trainer_id,
        id_cliente=client_id,
        nome="Cut Invernale",
        obiettivo="dimagrimento",
        livello="intermedio",
        durata_settimane=6,
        sessioni_per_settimana=3,
        data_inizio=today - timedelta(days=90),
        data_fine=today - timedelta(days=30),
        created_at=(datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        updated_at=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    )
    session.add(active_plan)
    session.add(completed_plan)
    session.commit()
    session.refresh(active_plan)
    session.refresh(completed_plan)

    workout_session = WorkoutSession(
        id_scheda=active_plan.id,
        numero_sessione=1,
        nome_sessione="Giorno A",
        durata_minuti=60,
    )
    session.add(workout_session)
    session.commit()
    session.refresh(workout_session)

    workout_log = WorkoutLog(
        id_scheda=active_plan.id,
        id_sessione=workout_session.id,
        id_cliente=client_id,
        trainer_id=trainer_id,
        data_esecuzione=today - timedelta(days=2),
        created_at=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
    )
    session.add(workout_log)
    session.commit()


def _seed_goals(session, *, trainer_id: int, client_id: int) -> None:
    metric = Metric(
        nome="Peso corporeo",
        nome_en="Body Weight",
        unita_misura="kg",
        categoria="corporeo",
        ordinamento=1,
    )
    session.add(metric)
    session.commit()
    session.refresh(metric)
    assert metric.id is not None

    today = date.today()
    session.add(
        ClientGoal(
            id_cliente=client_id,
            trainer_id=trainer_id,
            id_metrica=metric.id,
            direzione="diminuire",
            valore_target=75.0,
            valore_baseline=80.0,
            data_baseline=today - timedelta(days=30),
            data_inizio=today - timedelta(days=20),
            data_scadenza=today + timedelta(days=40),
            stato="attivo",
        )
    )
    session.add(
        ClientGoal(
            id_cliente=client_id,
            trainer_id=trainer_id,
            id_metrica=metric.id,
            direzione="aumentare",
            valore_target=100.0,
            valore_baseline=90.0,
            data_baseline=today - timedelta(days=120),
            data_inizio=today - timedelta(days=100),
            data_scadenza=today - timedelta(days=10),
            stato="raggiunto",
        )
    )
    session.commit()


def test_client_dossier_returns_operational_summary(client, auth_headers, session):
    dossier_client = _create_client(
        client,
        auth_headers,
        "Giulia",
        "Bianchi",
        anamnesi=_structured_anamnesi(),
    )
    contract = _create_contract(client, auth_headers, dossier_client["id"])

    now = datetime.now(timezone.utc)
    _create_event(
        client,
        auth_headers,
        client_id=dossier_client["id"],
        contract_id=contract["id"],
        title="PT completata",
        start_at=now - timedelta(days=3),
        status="Completato",
    )
    next_session = _create_event(
        client,
        auth_headers,
        client_id=dossier_client["id"],
        contract_id=contract["id"],
        title="PT domani",
        start_at=now + timedelta(days=1),
    )
    _create_event(
        client,
        auth_headers,
        client_id=dossier_client["id"],
        title="Colloquio tecnico",
        start_at=now + timedelta(hours=4),
        category="COLLOQUIO",
    )

    trainer_id = _trainer_id(session)
    _seed_workout_bundle(session, trainer_id=trainer_id, client_id=dossier_client["id"])
    _seed_goals(session, trainer_id=trainer_id, client_id=dossier_client["id"])

    response = client.get(f"/api/clients/{dossier_client['id']}/dossier", headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["client"]["id"] == dossier_client["id"]
    assert data["client"]["nome"] == "Giulia"
    assert data["readiness"] is not None
    assert data["readiness"]["next_action_code"] == "collect_baseline"
    assert data["clinical_alerts"] == []

    assert data["session_summary"]["total_pt_sessions"] == 2
    assert data["session_summary"]["completed_pt_sessions"] == 1
    assert data["session_summary"]["next_scheduled_session_at"] == next_session["data_inizio"]
    assert data["session_summary"]["last_completed_session_at"] is not None

    assert data["plan_summary"]["total_plans"] == 2
    assert data["plan_summary"]["latest_plan_name"] == "Cut Invernale"
    assert data["plan_summary"]["active_plan_name"] == "Forza Primavera"
    assert data["plan_summary"]["active_plan_start_date"] == (
        date.today() - timedelta(days=7)
    ).isoformat()

    assert data["contract_summary"] == {
        "active_contracts": 1,
        "credits_residui": 8,
        "has_overdue_rates": False,
        "next_contract_expiry_date": "2026-12-31",
    }
    assert data["goal_summary"] == {
        "active_goals": 1,
        "reached_goals": 1,
        "abandoned_goals": 0,
    }

    assert len(data["recent_activity"]) <= 5
    assert {item["kind"] for item in data["recent_activity"]} >= {"event", "workout_log"}


def test_client_dossier_enforces_trainer_isolation(client, auth_headers):
    own_client = _create_client(client, auth_headers, "Mario", "Owner")

    register_other = client.post(
        "/api/auth/register",
        json={
            "email": "other-dossier@test.com",
            "nome": "Other",
            "cognome": "Trainer",
            "password": "testpass123",
        },
    )
    assert register_other.status_code == 201, register_other.text
    other_headers = {"Authorization": f"Bearer {register_other.json()['access_token']}"}

    response = client.get(f"/api/clients/{own_client['id']}/dossier", headers=other_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Cliente non trovato"
