from datetime import datetime, timezone

import pytest
from sqlmodel import Session

from api.database import get_catalog_session
from api.main import app
from api.services.license import LicenseCheckResult


def _register_and_token(client, email: str) -> str:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "nome": "License",
            "cognome": "Tester",
            "password": "testpass123",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def test_license_middleware_disabled_allows_protected_route(client, monkeypatch):
    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "false")
    monkeypatch.setattr(
        "api.main.check_license",
        lambda: (_ for _ in ()).throw(AssertionError("check_license should not be called")),
    )
    token = _register_and_token(client, "license-off@test.com")

    response = client.get(
        "/api/clients",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("status_name", "message"),
    [
        ("missing", "Licenza non trovata"),
        ("invalid", "Licenza non valida"),
        ("expired", "Licenza scaduta"),
        ("unconfigured", "Chiave pubblica licenza non configurata"),
    ],
)
def test_license_middleware_blocks_protected_route_for_negative_statuses(
    client,
    monkeypatch,
    status_name,
    message,
):
    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "true")
    token = _register_and_token(client, f"license-{status_name}@test.com")

    monkeypatch.setattr(
        "api.main.check_license",
        lambda: LicenseCheckResult(status=status_name, message=message),
    )

    response = client.get(
        "/api/clients",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["license_status"] == status_name
    assert response.json()["detail"] == message


def test_license_middleware_allows_exempt_auth_route(client, monkeypatch):
    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "true")
    monkeypatch.setattr(
        "api.main.check_license",
        lambda: (_ for _ in ()).throw(AssertionError("check_license should not be called")),
    )

    response = client.post(
        "/api/auth/register",
        json={
            "email": "license-exempt@test.com",
            "nome": "Exempt",
            "cognome": "Route",
            "password": "testpass123",
        },
    )

    assert response.status_code == 201


def test_health_route_stays_exempt_and_reports_negative_license_status(
    client,
    test_engine,
    monkeypatch,
):
    def override_catalog():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_catalog_session] = override_catalog

    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "true")
    monkeypatch.setattr(
        "api.services.system_runtime.check_license",
        lambda: LicenseCheckResult(
            status="invalid",
            message="Licenza non valida",
            expires_at=datetime(2026, 3, 10, 10, 0, 0, tzinfo=timezone.utc),
        ),
    )

    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides.pop(get_catalog_session, None)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["license_status"] == "invalid"
    assert data["license_enforcement_enabled"] is True


def test_license_middleware_allows_protected_route_with_valid_license(client, monkeypatch):
    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "true")
    token = _register_and_token(client, "license-valid@test.com")

    monkeypatch.setattr(
        "api.main.check_license",
        lambda: LicenseCheckResult(status="valid", message="Licenza valida"),
    )

    response = client.get(
        "/api/clients",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
