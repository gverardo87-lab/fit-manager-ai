"""
Fixtures pytest per test API — DB SQLite in-memory, isolamento totale.

Ogni test ottiene un database pulito, un TestClient FastAPI, e un trainer
autenticato con headers JWT pronti all'uso.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine, Session

# Importa TUTTI i modelli per registrarli in SQLModel.metadata
from api.models import *  # noqa: F401, F403
from api.main import app
from api.database import get_session


@pytest.fixture
def test_engine():
    """Engine SQLite in-memory — isolamento totale tra test.

    StaticPool forza una singola connessione condivisa: necessario perche'
    SQLite in-memory crea un DB separato per ogni connessione.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(test_engine):
    """Session di test per operazioni dirette sul DB."""
    with Session(test_engine) as s:
        yield s


@pytest.fixture
def client(test_engine):
    """TestClient FastAPI con session override."""
    def override():
        with Session(test_engine) as s:
            yield s
    app.dependency_overrides[get_session] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Registra trainer di test, ritorna headers JWT."""
    r = client.post("/api/auth/register", json={
        "email": "test@test.com",
        "nome": "Test",
        "cognome": "Trainer",
        "password": "testpass123",
    })
    assert r.status_code == 201, f"Register failed: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def sample_client(client, auth_headers):
    """Crea un cliente di test."""
    r = client.post("/api/clients", json={
        "nome": "Mario",
        "cognome": "Rossi",
    }, headers=auth_headers)
    assert r.status_code == 201, f"Client creation failed: {r.text}"
    return r.json()


@pytest.fixture
def sample_contract(client, auth_headers, sample_client):
    """Crea contratto: prezzo=1000, acconto=200, 10 crediti."""
    r = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Gold 10",
        "crediti_totali": 10,
        "prezzo_totale": 1000.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
        "acconto": 200.0,
        "metodo_acconto": "CONTANTI",
    }, headers=auth_headers)
    assert r.status_code == 201, f"Contract creation failed: {r.text}"
    return r.json()


@pytest.fixture
def sample_contract_with_plan(client, auth_headers, sample_contract):
    """Contratto con piano rate generato (4 rate da 200 euro)."""
    r = client.post(
        f"/api/rates/generate-plan/{sample_contract['id']}",
        json={
            "importo_da_rateizzare": 800.0,
            "numero_rate": 4,
            "data_prima_rata": "2026-02-01",
            "frequenza": "MENSILE",
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, f"Plan generation failed: {r.text}"
    plan = r.json()
    return {
        "contract": sample_contract,
        "rates": plan["items"],
    }
