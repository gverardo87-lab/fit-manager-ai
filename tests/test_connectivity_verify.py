from datetime import datetime, timezone

from api.schemas.system import ConnectivityStatusResponse
from api.services import connectivity_verify as verify_service


def _make_status(**overrides) -> ConnectivityStatusResponse:
    payload = {
        "generated_at": datetime(2026, 3, 11, 12, 0, tzinfo=timezone.utc),
        "profile": "local_only",
        "tailscale_cli_installed": False,
        "tailscale_version": None,
        "tailscale_status": "not_installed",
        "tailscale_connected": False,
        "tailscale_ip": None,
        "tailscale_dns_name": None,
        "funnel_status": "not_enabled",
        "funnel_enabled": False,
        "public_portal_enabled": False,
        "public_base_url": None,
        "public_base_url_matches_dns": None,
        "next_recommended_action_code": "install_tailscale",
        "next_recommended_action_label": "Installa Tailscale sul PC",
        "checks": [],
        "missing_requirements": [],
    }
    payload.update(overrides)
    return ConnectivityStatusResponse(**payload)


def test_verify_connectivity_setup_marks_local_only_as_ready(monkeypatch):
    monkeypatch.setattr(verify_service, "build_connectivity_status", lambda: _make_status())

    response = verify_service.verify_connectivity_setup()

    assert response.target_profile == "local_only"
    assert response.effective_profile == "local_only"
    assert response.status == "ready"
    assert response.next_recommended_action_code == "ready"
    assert response.verified_public_origin is None


def test_verify_connectivity_setup_marks_public_portal_as_partial_when_origin_not_reachable(
    monkeypatch,
):
    monkeypatch.setattr(
        verify_service,
        "build_connectivity_status",
        lambda: _make_status(
            profile="public_portal",
            tailscale_cli_installed=True,
            tailscale_version="1.94.2",
            tailscale_status="ok",
            tailscale_connected=True,
            tailscale_ip="100.88.77.66",
            tailscale_dns_name="chiara.tail8a3bc3.ts.net",
            funnel_status="ok",
            funnel_enabled=True,
            public_portal_enabled=True,
            public_base_url="https://chiara.tail8a3bc3.ts.net",
            public_base_url_matches_dns=True,
            next_recommended_action_code="ready",
            next_recommended_action_label="Connettivita pronta",
        ),
    )
    monkeypatch.setattr(
        verify_service,
        "_probe_public_origin",
        lambda _url: verify_service.PublicOriginProbe(
            status="warning",
            detail="Timeout nel contatto con l'origine pubblica configurata.",
            target_url="https://chiara.tail8a3bc3.ts.net/health",
        ),
    )

    response = verify_service.verify_connectivity_setup()

    assert response.target_profile == "public_portal"
    assert response.effective_profile == "public_portal"
    assert response.status == "partial"
    assert response.next_recommended_action_code == "verify_public_origin"
    assert response.verified_public_origin == "https://chiara.tail8a3bc3.ts.net/health"


def test_verify_connectivity_setup_blocks_public_portal_when_runtime_prerequisites_are_missing(
    monkeypatch,
):
    monkeypatch.setattr(
        verify_service,
        "build_connectivity_status",
        lambda: _make_status(
            profile="trusted_devices",
            tailscale_cli_installed=True,
            tailscale_version="1.94.2",
            tailscale_status="ok",
            tailscale_connected=True,
            tailscale_ip="100.88.77.66",
            tailscale_dns_name="chiara.tail8a3bc3.ts.net",
            funnel_status="not_enabled",
            funnel_enabled=False,
            public_portal_enabled=True,
            public_base_url="https://chiara.tail8a3bc3.ts.net",
            public_base_url_matches_dns=True,
            next_recommended_action_code="enable_funnel",
            next_recommended_action_label="Attiva Tailscale Funnel per il portale clienti",
            missing_requirements=["Attiva `tailscale funnel --bg 3000` per il portale pubblico."],
        ),
    )
    monkeypatch.setattr(
        verify_service,
        "_probe_public_origin",
        lambda _url: verify_service.PublicOriginProbe(
            status="neutral",
            detail="Probe non eseguita.",
            target_url="https://chiara.tail8a3bc3.ts.net/health",
        ),
    )

    response = verify_service.verify_connectivity_setup()

    assert response.target_profile == "public_portal"
    assert response.effective_profile == "trusted_devices"
    assert response.status == "blocked"
    assert response.next_recommended_action_code == "enable_funnel"
    assert any(check.code == "target_profile" and check.status == "critical" for check in response.checks)
