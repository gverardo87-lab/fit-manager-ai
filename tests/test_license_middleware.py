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
    token = _register_and_token(client, "license-off@test.com")

    response = client.get(
        "/api/clients",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


def test_license_middleware_blocks_protected_route_without_license(client, monkeypatch):
    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "true")
    token = _register_and_token(client, "license-missing@test.com")

    monkeypatch.setattr(
        "api.main.check_license",
        lambda: LicenseCheckResult(status="missing", message="Licenza non trovata"),
    )

    response = client.get(
        "/api/clients",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["license_status"] == "missing"


def test_license_middleware_allows_exempt_auth_route(client, monkeypatch):
    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "true")

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
