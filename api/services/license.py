"""
License service (Phase 1) - verifica RSA offline del file licenza locale.

Questo modulo NON applica enforcement HTTP: espone utility pure per:
1) leggere token da data/license.key
2) validare firma + expiry (RS256)
3) restituire uno stato normalizzato per middleware/health endpoint
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel, Field, ValidationError

from api.config import DATA_DIR


LICENSE_FILE = DATA_DIR / "license.key"
LICENSE_ALGORITHM = "RS256"

# La chiave pubblica puo' essere:
# 1) passata via env LICENSE_PUBLIC_KEY (supporta '\n' escaped)
# 2) messa in data/license_public.pem
# 3) embedded qui (fallback, da sostituire con quella reale prima del lancio)
DEFAULT_PUBLIC_KEY_PEM = ""
PUBLIC_KEY_FILE = DATA_DIR / "license_public.pem"


LicenseStatus = Literal["valid", "missing", "invalid", "expired", "unconfigured"]


class LicenseClaims(BaseModel):
    """Claim minimi richiesti dal token licenza."""

    client_id: str = Field(min_length=1)
    tier: str = Field(min_length=1)
    max_clients: int | None = Field(default=None, ge=1)
    exp: int


class LicenseCheckResult(BaseModel):
    """Esito standardizzato per middleware/health/UI."""

    status: LicenseStatus
    message: str
    expires_at: datetime | None = None
    claims: LicenseClaims | None = None

    @property
    def is_valid(self) -> bool:
        return self.status == "valid"


def _load_public_key(public_key: str | None = None) -> str | None:
    """Risoluzione chiave pubblica (parametro > env > file > embedded)."""
    if public_key is not None:
        key = public_key.strip()
        return key or None

    env_key = os.getenv("LICENSE_PUBLIC_KEY", "").strip()
    if env_key:
        return env_key.replace("\\n", "\n")

    if PUBLIC_KEY_FILE.exists():
        file_key = PUBLIC_KEY_FILE.read_text(encoding="utf-8").strip()
        return file_key or None

    embedded = DEFAULT_PUBLIC_KEY_PEM.strip()
    return embedded or None


def _read_license_token(token_path: Path) -> str | None:
    """Legge token JWT da file (None se assente o vuoto)."""
    if not token_path.exists():
        return None

    token = token_path.read_text(encoding="utf-8").strip()
    return token or None


def _to_utc_datetime(exp: int | float) -> datetime:
    """Converte timestamp unix in datetime UTC aware."""
    return datetime.fromtimestamp(float(exp), tz=timezone.utc)


def _decode_claims(token: str, public_key: str) -> LicenseClaims:
    """Decode con verifica firma + expiry."""
    payload = jwt.decode(
        token,
        public_key,
        algorithms=[LICENSE_ALGORITHM],
        options={"verify_aud": False},
    )
    return LicenseClaims.model_validate(payload)


def _decode_claims_ignore_exp(token: str, public_key: str) -> LicenseClaims | None:
    """Best effort: utile per mostrare expiry anche quando la licenza e' scaduta."""
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[LICENSE_ALGORITHM],
            options={"verify_aud": False, "verify_exp": False},
        )
        return LicenseClaims.model_validate(payload)
    except (JWTError, ValidationError):
        return None


def check_license(
    token_path: Path = LICENSE_FILE,
    public_key: str | None = None,
) -> LicenseCheckResult:
    """
    Valida la licenza locale.

    Stati:
    - missing: file licenza assente/vuoto
    - unconfigured: chiave pubblica non configurata
    - invalid: firma/claims non validi
    - expired: token valido ma scaduto
    - valid: licenza valida
    """
    token = _read_license_token(token_path)
    if token is None:
        return LicenseCheckResult(
            status="missing",
            message="Licenza non trovata",
        )

    key = _load_public_key(public_key)
    if key is None:
        return LicenseCheckResult(
            status="unconfigured",
            message="Chiave pubblica licenza non configurata",
        )

    try:
        claims = _decode_claims(token, key)
        return LicenseCheckResult(
            status="valid",
            message="Licenza valida",
            expires_at=_to_utc_datetime(claims.exp),
            claims=claims,
        )
    except ExpiredSignatureError:
        claims = _decode_claims_ignore_exp(token, key)
        return LicenseCheckResult(
            status="expired",
            message="Licenza scaduta",
            expires_at=_to_utc_datetime(claims.exp) if claims else None,
            claims=claims,
        )
    except (JWTError, ValidationError):
        return LicenseCheckResult(
            status="invalid",
            message="Licenza non valida",
        )
