from api.services import connectivity_runtime as runtime


def test_build_connectivity_status_reports_local_only_when_tailscale_is_missing(monkeypatch):
    monkeypatch.setattr(runtime, "_resolve_tailscale_binary", lambda: None)
    monkeypatch.setattr(
        runtime,
        "_probe_tailscale",
        lambda _binary: runtime.TailscaleProbe(
            cli_installed=False,
            version=None,
            status="not_installed",
            connected=False,
            ip=None,
            dns_name=None,
        ),
    )
    monkeypatch.setattr(
        runtime,
        "_probe_funnel",
        lambda _binary: runtime.FunnelProbe(status="not_installed", enabled=False),
    )
    monkeypatch.setattr(runtime, "is_public_portal_enabled", lambda: False)
    monkeypatch.setattr(runtime, "get_public_base_url", lambda: None)

    status = runtime.build_connectivity_status()

    assert status.profile == "local_only"
    assert status.tailscale_cli_installed is False
    assert status.tailscale_status == "not_installed"
    assert status.next_recommended_action_code == "install_tailscale"
    assert "Installa Tailscale sul PC del trainer." in status.missing_requirements


def test_build_connectivity_status_surfaces_permission_denied_for_local_tailscale(monkeypatch):
    monkeypatch.setattr(runtime, "_resolve_tailscale_binary", lambda: "tailscale.exe")
    monkeypatch.setattr(
        runtime,
        "_probe_tailscale",
        lambda _binary: runtime.TailscaleProbe(
            cli_installed=True,
            version="1.94.2",
            status="permission_denied",
            connected=False,
            ip=None,
            dns_name=None,
        ),
    )
    monkeypatch.setattr(
        runtime,
        "_probe_funnel",
        lambda _binary: runtime.FunnelProbe(status="permission_denied", enabled=False),
    )
    monkeypatch.setattr(runtime, "is_public_portal_enabled", lambda: False)
    monkeypatch.setattr(runtime, "get_public_base_url", lambda: None)

    status = runtime.build_connectivity_status()

    assert status.profile == "local_only"
    assert status.tailscale_status == "permission_denied"
    assert status.next_recommended_action_code == "grant_tailscale_access"
    assert any(check.code == "tailscale_session" and check.status == "critical" for check in status.checks)
    assert any("permessi locali" in item for item in status.missing_requirements)


def test_build_connectivity_status_reports_public_portal_ready_when_dns_base_url_and_funnel_match(
    monkeypatch,
):
    monkeypatch.setattr(runtime, "_resolve_tailscale_binary", lambda: "tailscale.exe")
    monkeypatch.setattr(
        runtime,
        "_probe_tailscale",
        lambda _binary: runtime.TailscaleProbe(
            cli_installed=True,
            version="1.94.2",
            status="ok",
            connected=True,
            ip="100.88.77.66",
            dns_name="chiara.tail8a3bc3.ts.net",
        ),
    )
    monkeypatch.setattr(
        runtime,
        "_probe_funnel",
        lambda _binary: runtime.FunnelProbe(status="ok", enabled=True),
    )
    monkeypatch.setattr(runtime, "is_public_portal_enabled", lambda: True)
    monkeypatch.setattr(
        runtime,
        "get_public_base_url",
        lambda: "https://chiara.tail8a3bc3.ts.net",
    )

    status = runtime.build_connectivity_status()

    assert status.profile == "public_portal"
    assert status.tailscale_connected is True
    assert status.funnel_enabled is True
    assert status.public_base_url_matches_dns is True
    assert status.next_recommended_action_code == "ready"
    assert status.missing_requirements == []
