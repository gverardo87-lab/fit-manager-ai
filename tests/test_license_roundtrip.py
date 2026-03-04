"""Test round-trip: genera chiavi → firma licenza → verifica con check_license()."""

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from api.services.license import check_license


def _generate_keypair(tmp_path: Path) -> tuple[str, str]:
    """Genera keypair RSA in tmp_path, ritorna (private_pem, public_pem)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    return private_pem, public_pem


def test_roundtrip_valid_license(tmp_path):
    """Genera keypair → firma token → verifica → status valid."""
    from datetime import datetime, timezone, timedelta

    private_pem, public_pem = _generate_keypair(tmp_path)

    claims = {
        "client_id": "test-gym",
        "tier": "pro",
        "max_clients": 50,
        "exp": int((datetime.now(tz=timezone.utc) + timedelta(days=365)).timestamp()),
    }
    token = jwt.encode(claims, private_pem, algorithm="RS256")

    token_path = tmp_path / "license.key"
    token_path.write_text(token, encoding="utf-8")

    result = check_license(token_path=token_path, public_key=public_pem)

    assert result.status == "valid"
    assert result.is_valid
    assert result.claims is not None
    assert result.claims.client_id == "test-gym"
    assert result.claims.tier == "pro"
    assert result.claims.max_clients == 50


def test_roundtrip_expired_license(tmp_path):
    """Token scaduto → status expired con claims leggibili."""
    from datetime import datetime, timezone, timedelta

    private_pem, public_pem = _generate_keypair(tmp_path)

    claims = {
        "client_id": "expired-gym",
        "tier": "basic",
        "exp": int((datetime.now(tz=timezone.utc) - timedelta(days=1)).timestamp()),
    }
    token = jwt.encode(claims, private_pem, algorithm="RS256")

    token_path = tmp_path / "license.key"
    token_path.write_text(token, encoding="utf-8")

    result = check_license(token_path=token_path, public_key=public_pem)

    assert result.status == "expired"
    assert not result.is_valid
    assert result.claims is not None
    assert result.claims.client_id == "expired-gym"


def test_roundtrip_wrong_key_invalid(tmp_path):
    """Token firmato con chiave A, verificato con chiave B → invalid."""
    from datetime import datetime, timezone, timedelta

    private_a, _ = _generate_keypair(tmp_path)
    _, public_b = _generate_keypair(tmp_path)

    claims = {
        "client_id": "wrong-key",
        "tier": "pro",
        "exp": int((datetime.now(tz=timezone.utc) + timedelta(days=365)).timestamp()),
    }
    token = jwt.encode(claims, private_a, algorithm="RS256")

    token_path = tmp_path / "license.key"
    token_path.write_text(token, encoding="utf-8")

    result = check_license(token_path=token_path, public_key=public_b)

    assert result.status == "invalid"
    assert not result.is_valid
