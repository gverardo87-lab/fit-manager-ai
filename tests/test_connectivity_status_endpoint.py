from datetime import datetime, timezone

from api.schemas.system import ConnectivityCheck, ConnectivityStatusResponse


def test_connectivity_status_endpoint_requires_authentication(client):
    response = client.get("/api/system/connectivity-status")

    assert response.status_code == 401


def test_connectivity_status_endpoint_returns_read_only_runtime_contract(
    client,
    auth_headers,
    monkeypatch,
):
    monkeypatch.setattr(
        "api.routers.system.build_connectivity_status",
        lambda: ConnectivityStatusResponse(
            generated_at=datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc),
            profile="trusted_devices",
            tailscale_cli_installed=True,
            tailscale_version="1.94.2",
            tailscale_status="ok",
            tailscale_connected=True,
            tailscale_ip="100.88.77.66",
            tailscale_dns_name="chiara.tail8a3bc3.ts.net",
            funnel_status="not_enabled",
            funnel_enabled=False,
            public_portal_enabled=False,
            public_base_url=None,
            public_base_url_matches_dns=None,
            next_recommended_action_code="ready",
            next_recommended_action_label="Connettivita pronta",
            checks=[
                ConnectivityCheck(
                    code="tailscale_cli",
                    label="Client Tailscale",
                    status="ok",
                    detail="Installato (1.94.2)",
                )
            ],
            missing_requirements=[],
        ),
    )

    response = client.get("/api/system/connectivity-status", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["generated_at"].startswith("2026-03-10T12:00:00")
    assert data["profile"] == "trusted_devices"
    assert data["tailscale_cli_installed"] is True
    assert data["tailscale_status"] == "ok"
    assert data["tailscale_dns_name"] == "chiara.tail8a3bc3.ts.net"
    assert data["funnel_enabled"] is False
    assert data["next_recommended_action_code"] == "ready"
    assert data["checks"][0]["code"] == "tailscale_cli"
