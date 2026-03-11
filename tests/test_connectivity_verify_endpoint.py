def test_connectivity_verify_endpoint_requires_authentication(client):
    response = client.post("/api/system/connectivity-verify")

    assert response.status_code == 401


def test_connectivity_verify_endpoint_returns_verdict_payload(
    client,
    auth_headers,
    monkeypatch,
):
    monkeypatch.setattr(
        "api.routers.system.verify_connectivity_setup",
        lambda: {
            "verified_at": "2026-03-11T12:30:00Z",
            "target_profile": "public_portal",
            "effective_profile": "public_portal",
            "status": "ready",
            "summary": "Portale pubblico verificato: l'origine configurata risponde correttamente.",
            "verified_public_origin": "https://chiara.tail8a3bc3.ts.net/health",
            "checks": [
                {
                    "code": "public_origin",
                    "label": "Origine pubblica",
                    "status": "ok",
                    "detail": "Origine pubblica raggiungibile.",
                }
            ],
            "next_recommended_action_code": "ready",
            "next_recommended_action_label": "Portale pubblico verificato",
        },
    )

    response = client.post("/api/system/connectivity-verify", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["target_profile"] == "public_portal"
    assert data["verified_public_origin"] == "https://chiara.tail8a3bc3.ts.net/health"
    assert data["checks"][0]["code"] == "public_origin"
