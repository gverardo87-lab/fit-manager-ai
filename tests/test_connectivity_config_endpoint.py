def test_connectivity_config_endpoint_requires_authentication(client):
    response = client.post(
        "/api/system/connectivity-config",
        json={"profile": "trusted_devices"},
    )

    assert response.status_code == 401


def test_connectivity_config_endpoint_applies_fitmanager_runtime_settings(
    client,
    auth_headers,
    monkeypatch,
):
    monkeypatch.setattr(
        "api.routers.system.apply_connectivity_config",
        lambda payload: {
            "applied_at": "2026-03-11T08:45:00Z",
            "profile": payload.profile,
            "public_portal_enabled": True,
            "public_base_url": payload.public_base_url,
            "written_keys": ["PUBLIC_PORTAL_ENABLED", "PUBLIC_BASE_URL"],
            "restart_required": False,
            "message": "Portale pubblico configurato e base URL salvata.",
        },
    )

    response = client.post(
        "/api/system/connectivity-config",
        json={
            "profile": "public_portal",
            "public_base_url": "https://chiara.tail8a3bc3.ts.net",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["profile"] == "public_portal"
    assert data["public_portal_enabled"] is True
    assert data["public_base_url"] == "https://chiara.tail8a3bc3.ts.net"
    assert data["written_keys"] == ["PUBLIC_PORTAL_ENABLED", "PUBLIC_BASE_URL"]
    assert data["restart_required"] is False


def test_connectivity_config_endpoint_rejects_public_portal_without_https_base_url(
    client,
    auth_headers,
):
    response = client.post(
        "/api/system/connectivity-config",
        json={"profile": "public_portal", "public_base_url": "http://localhost:3000"},
        headers=auth_headers,
    )

    assert response.status_code == 422
