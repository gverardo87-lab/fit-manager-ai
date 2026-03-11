def test_connectivity_portal_validation_endpoint_requires_authentication(client):
    response = client.post(
        "/api/system/connectivity-portal-validation",
        json={
            "token": "12345678-1234-1234-1234-123456789012",
            "public_url": "https://chiara.tail8a3bc3.ts.net/public/anamnesi/12345678-1234-1234-1234-123456789012",
        },
    )

    assert response.status_code == 401


def test_connectivity_portal_validation_endpoint_returns_portal_verdict(
    client,
    auth_headers,
    monkeypatch,
):
    monkeypatch.setattr(
        "api.routers.system.validate_public_portal_link",
        lambda payload: {
            "validated_at": "2026-03-11T13:10:00Z",
            "status": "ready",
            "summary": "Link anamnesi pubblico verificato: pagina e token rispondono correttamente.",
            "public_url": payload.public_url,
            "validate_url": "https://chiara.tail8a3bc3.ts.net/api/public/anamnesi/validate?token=12345678-1234-1234-1234-123456789012",
            "masked_client_name": "Marco R.",
            "masked_trainer_name": "Chiara B.",
            "checks": [
                {
                    "code": "public_page",
                    "label": "Pagina pubblica",
                    "status": "ok",
                    "detail": "Pagina pubblica raggiungibile.",
                }
            ],
        },
    )

    response = client.post(
        "/api/system/connectivity-portal-validation",
        json={
            "token": "12345678-1234-1234-1234-123456789012",
            "public_url": "https://chiara.tail8a3bc3.ts.net/public/anamnesi/12345678-1234-1234-1234-123456789012",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["masked_client_name"] == "Marco R."
    assert data["checks"][0]["code"] == "public_page"
