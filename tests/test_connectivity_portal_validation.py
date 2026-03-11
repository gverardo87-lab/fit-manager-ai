from datetime import datetime, timezone

from api.schemas.system import ConnectivityPortalValidationRequest, ConnectivityStatusResponse
from api.services import connectivity_portal_validation as portal_service


def _make_status(**overrides) -> ConnectivityStatusResponse:
    payload = {
        "generated_at": datetime(2026, 3, 11, 12, 0, tzinfo=timezone.utc),
        "profile": "public_portal",
        "tailscale_cli_installed": True,
        "tailscale_version": "1.94.2",
        "tailscale_status": "ok",
        "tailscale_connected": True,
        "tailscale_ip": "100.88.77.66",
        "tailscale_dns_name": "chiara.tail8a3bc3.ts.net",
        "funnel_status": "ok",
        "funnel_enabled": True,
        "public_portal_enabled": True,
        "public_base_url": "https://chiara.tail8a3bc3.ts.net",
        "public_base_url_matches_dns": True,
        "next_recommended_action_code": "ready",
        "next_recommended_action_label": "Connettivita pronta",
        "checks": [],
        "missing_requirements": [],
    }
    payload.update(overrides)
    return ConnectivityStatusResponse(**payload)


def _make_payload() -> ConnectivityPortalValidationRequest:
    return ConnectivityPortalValidationRequest(
        token="12345678-1234-1234-1234-123456789012",
        public_url="https://chiara.tail8a3bc3.ts.net/public/anamnesi/12345678-1234-1234-1234-123456789012",
    )


def test_validate_public_portal_link_returns_ready_when_page_and_token_are_ok(monkeypatch):
    monkeypatch.setattr(portal_service, "build_connectivity_status", lambda: _make_status())
    monkeypatch.setattr(
        portal_service,
        "_probe_public_page",
        lambda _url: portal_service.PublicPageProbe(
            status="ok",
            detail="Pagina pubblica raggiungibile.",
            page_url="https://chiara.tail8a3bc3.ts.net/public/anamnesi/123",
        ),
    )
    monkeypatch.setattr(
        portal_service,
        "_probe_public_validate",
        lambda _url: portal_service.PublicValidateProbe(
            status="ok",
            detail="Token valido.",
            validate_url="https://chiara.tail8a3bc3.ts.net/api/public/anamnesi/validate?token=123",
            client_name="Marco R.",
            trainer_name="Chiara B.",
        ),
    )

    response = portal_service.validate_public_portal_link(_make_payload())

    assert response.status == "ready"
    assert response.masked_client_name == "Marco R."
    assert response.masked_trainer_name == "Chiara B."
    assert response.checks[0].code == "runtime_profile"
    assert all(check.status == "ok" for check in response.checks)


def test_validate_public_portal_link_blocks_when_runtime_is_not_public(monkeypatch):
    monkeypatch.setattr(
        portal_service,
        "build_connectivity_status",
        lambda: _make_status(profile="trusted_devices", public_portal_enabled=False),
    )
    monkeypatch.setattr(
        portal_service,
        "_probe_public_page",
        lambda _url: portal_service.PublicPageProbe(
            status="ok",
            detail="Pagina pubblica raggiungibile.",
            page_url="https://chiara.tail8a3bc3.ts.net/public/anamnesi/123",
        ),
    )
    monkeypatch.setattr(
        portal_service,
        "_probe_public_validate",
        lambda _url: portal_service.PublicValidateProbe(
            status="ok",
            detail="Token valido.",
            validate_url="https://chiara.tail8a3bc3.ts.net/api/public/anamnesi/validate?token=123",
            client_name="Marco R.",
            trainer_name="Chiara B.",
        ),
    )

    response = portal_service.validate_public_portal_link(_make_payload())

    assert response.status == "blocked"
    assert response.checks[0].status == "critical"


def test_validate_public_portal_link_blocks_when_validate_endpoint_fails(monkeypatch):
    monkeypatch.setattr(portal_service, "build_connectivity_status", lambda: _make_status())
    monkeypatch.setattr(
        portal_service,
        "_probe_public_page",
        lambda _url: portal_service.PublicPageProbe(
            status="ok",
            detail="Pagina pubblica raggiungibile.",
            page_url="https://chiara.tail8a3bc3.ts.net/public/anamnesi/123",
        ),
    )
    monkeypatch.setattr(
        portal_service,
        "_probe_public_validate",
        lambda _url: portal_service.PublicValidateProbe(
            status="critical",
            detail="HTTP 404.",
            validate_url="https://chiara.tail8a3bc3.ts.net/api/public/anamnesi/validate?token=123",
        ),
    )

    response = portal_service.validate_public_portal_link(_make_payload())

    assert response.status == "blocked"
    assert response.checks[-1].code == "public_validate"
    assert response.checks[-1].status == "critical"
