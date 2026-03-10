from datetime import datetime, timezone

from sqlmodel import Session

from api.database import get_catalog_session
from api.main import app
from api.services.license import LicenseCheckResult


def test_health_returns_enriched_runtime_metadata(client, test_engine, monkeypatch):
    def override_catalog():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_catalog_session] = override_catalog

    monkeypatch.setattr(
        "api.main.APP_STARTED_AT",
        datetime(2026, 3, 10, 6, 0, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr("api.main.DATABASE_URL", "sqlite:///data/crm_dev.db")
    monkeypatch.setattr(
        "api.main.check_license",
        lambda: LicenseCheckResult(status="valid", message="Licenza valida"),
    )
    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "true")
    monkeypatch.setenv("PUBLIC_PORTAL_ENABLED", "true")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://fitmanager.example.ts.net")

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"]
    assert data["db"] == "connected"
    assert data["catalog"] == "connected"
    assert data["license_status"] == "valid"
    assert data["license_enforcement_enabled"] is True
    assert data["app_mode"] == "development"
    assert data["distribution_mode"] == "source"
    assert data["public_portal_enabled"] is True
    assert data["public_base_url_configured"] is True
    assert data["started_at"].startswith("2026-03-10T06:00:00")
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0
