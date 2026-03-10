import os

from api.schemas.system import ConnectivityConfigRequest
from api.services import connectivity_config as config_service


def test_apply_connectivity_config_enables_public_portal_and_updates_runtime_env(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("JWT_SECRET=abc123\nPUBLIC_PORTAL_ENABLED=false\n", encoding="utf-8")
    monkeypatch.setattr(config_service, "ENV_FILE", env_file)
    monkeypatch.delenv("PUBLIC_PORTAL_ENABLED", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)

    response = config_service.apply_connectivity_config(
        ConnectivityConfigRequest(
            profile="public_portal",
            public_base_url="https://chiara.tail8a3bc3.ts.net",
        )
    )

    content = env_file.read_text(encoding="utf-8")
    assert "JWT_SECRET=abc123" in content
    assert "PUBLIC_PORTAL_ENABLED=true" in content
    assert "PUBLIC_BASE_URL=https://chiara.tail8a3bc3.ts.net" in content
    assert response.public_portal_enabled is True
    assert response.public_base_url == "https://chiara.tail8a3bc3.ts.net"
    assert response.restart_required is False
    assert os.environ["PUBLIC_PORTAL_ENABLED"] == "true"
    assert os.environ["PUBLIC_BASE_URL"] == "https://chiara.tail8a3bc3.ts.net"


def test_apply_connectivity_config_clears_public_portal_settings_for_trusted_devices(
    monkeypatch,
    tmp_path,
):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "JWT_SECRET=abc123\nPUBLIC_PORTAL_ENABLED=true\nPUBLIC_BASE_URL=https://old.ts.net\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config_service, "ENV_FILE", env_file)
    monkeypatch.setenv("PUBLIC_PORTAL_ENABLED", "true")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://old.ts.net")

    response = config_service.apply_connectivity_config(
        ConnectivityConfigRequest(profile="trusted_devices")
    )

    content = env_file.read_text(encoding="utf-8")
    assert "PUBLIC_PORTAL_ENABLED=false" in content
    assert "PUBLIC_BASE_URL=" not in content
    assert response.profile == "trusted_devices"
    assert response.public_portal_enabled is False
    assert response.public_base_url is None
    assert os.environ["PUBLIC_PORTAL_ENABLED"] == "false"
    assert "PUBLIC_BASE_URL" not in os.environ


def test_apply_connectivity_config_creates_env_file_when_missing(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    monkeypatch.setattr(config_service, "ENV_FILE", env_file)
    monkeypatch.delenv("PUBLIC_PORTAL_ENABLED", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)

    response = config_service.apply_connectivity_config(
        ConnectivityConfigRequest(profile="trusted_devices")
    )

    assert env_file.exists()
    content = env_file.read_text(encoding="utf-8")
    assert content == "PUBLIC_PORTAL_ENABLED=false\n"
    assert response.profile == "trusted_devices"
    assert response.restart_required is False
