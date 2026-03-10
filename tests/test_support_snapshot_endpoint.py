from datetime import datetime, timezone

from sqlmodel import Session

from api.database import get_catalog_session
from api.main import app
from api.services.license import LicenseCheckResult


def test_support_snapshot_returns_safe_runtime_diagnostic_payload(
    client,
    test_engine,
    auth_headers,
    monkeypatch,
    tmp_path,
):
    def override_catalog():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_catalog_session] = override_catalog

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    backup_path = backup_dir / "backup_20260310_060000.sqlite"
    backup_path.write_bytes(b"SQLite format 3\x00diagnostic-backup")
    backup_path.with_suffix(".sha256").write_text(
        "abc123  backup_20260310_060000.sqlite\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("api.services.system_runtime.BACKUP_DIR", backup_dir)
    monkeypatch.setattr(
        "api.services.system_runtime.APP_STARTED_AT",
        datetime(2026, 3, 10, 6, 0, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr("api.services.system_runtime.DATABASE_URL", "sqlite:///data/crm.db")
    monkeypatch.setattr(
        "api.services.system_runtime.check_license",
        lambda: LicenseCheckResult(status="valid", message="Licenza valida"),
    )
    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "true")
    monkeypatch.setenv("PUBLIC_PORTAL_ENABLED", "true")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://fitmanager.example.ts.net")

    response = client.get("/api/system/support-snapshot", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "trainer" not in data
    assert "data" not in data
    assert data["generated_at"].startswith("2026-03-10T")
    assert data["public_base_url"] == "https://fitmanager.example.ts.net"
    assert data["health"]["status"] == "ok"
    assert data["health"]["app_mode"] == "production"
    assert data["health"]["distribution_mode"] == "source"
    assert data["health"]["license_enforcement_enabled"] is True
    assert len(data["recent_backups"]) == 1
    assert data["recent_backups"][0]["filename"] == "backup_20260310_060000.sqlite"
    assert data["recent_backups"][0]["checksum"] == "abc123"
