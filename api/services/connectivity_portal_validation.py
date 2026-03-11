"""Functional validation helpers for the public anamnesi portal."""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib import error, parse, request

from api.schemas.system import (
    ConnectivityCheck,
    ConnectivityPortalValidationRequest,
    ConnectivityPortalValidationResponse,
)
from api.services.connectivity_runtime import build_connectivity_status

PORTAL_VALIDATE_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class PublicPageProbe:
    status: str
    detail: str
    page_url: str


@dataclass(frozen=True)
class PublicValidateProbe:
    status: str
    detail: str
    validate_url: str
    client_name: str | None = None
    trainer_name: str | None = None


def _perform_request(target_url: str) -> tuple[int, str, str]:
    req = request.Request(
        target_url,
        headers={"User-Agent": "FitManagerPortalValidation/1.0"},
    )
    with request.urlopen(req, timeout=PORTAL_VALIDATE_TIMEOUT_SECONDS) as response:
        status_code = response.getcode()
        content_type = response.headers.get("Content-Type", "")
        body = response.read().decode("utf-8")
    return status_code, content_type, body


def _build_validate_url(public_url: str, token: str) -> str:
    parsed = parse.urlsplit(public_url)
    base = parse.urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    query = parse.urlencode({"token": token})
    return f"{base}/api/public/anamnesi/validate?{query}"


def _probe_public_page(public_url: str) -> PublicPageProbe:
    try:
        status_code, content_type, _body = _perform_request(public_url)
    except error.HTTPError as exc:
        return PublicPageProbe(
            status="critical",
            detail=f"La pagina pubblica anamnesi risponde con HTTP {exc.code}.",
            page_url=public_url,
        )
    except error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, socket.timeout):
            detail = "Timeout nel contatto con la pagina pubblica anamnesi."
        else:
            detail = f"Impossibile raggiungere la pagina pubblica anamnesi: {reason}."
        return PublicPageProbe(status="critical", detail=detail, page_url=public_url)
    except TimeoutError:
        return PublicPageProbe(
            status="critical",
            detail="Timeout nel contatto con la pagina pubblica anamnesi.",
            page_url=public_url,
        )

    if status_code != 200:
        return PublicPageProbe(
            status="critical",
            detail=f"La pagina pubblica anamnesi ha risposto con HTTP {status_code}.",
            page_url=public_url,
        )

    if "text/html" not in content_type.lower():
        return PublicPageProbe(
            status="warning",
            detail="La pagina pubblica risponde, ma il Content-Type non e `text/html`.",
            page_url=public_url,
        )

    return PublicPageProbe(
        status="ok",
        detail="La pagina pubblica anamnesi risponde correttamente.",
        page_url=public_url,
    )


def _probe_public_validate(validate_url: str) -> PublicValidateProbe:
    try:
        status_code, _content_type, body = _perform_request(validate_url)
    except error.HTTPError as exc:
        return PublicValidateProbe(
            status="critical",
            detail=f"L'endpoint pubblico di validazione risponde con HTTP {exc.code}.",
            validate_url=validate_url,
        )
    except error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, socket.timeout):
            detail = "Timeout nel contatto con l'endpoint pubblico di validazione."
        else:
            detail = f"Impossibile raggiungere l'endpoint pubblico di validazione: {reason}."
        return PublicValidateProbe(status="critical", detail=detail, validate_url=validate_url)
    except TimeoutError:
        return PublicValidateProbe(
            status="critical",
            detail="Timeout nel contatto con l'endpoint pubblico di validazione.",
            validate_url=validate_url,
        )

    if status_code != 200:
        return PublicValidateProbe(
            status="critical",
            detail=f"L'endpoint pubblico di validazione ha risposto con HTTP {status_code}.",
            validate_url=validate_url,
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return PublicValidateProbe(
            status="critical",
            detail="L'endpoint pubblico di validazione non restituisce JSON valido.",
            validate_url=validate_url,
        )

    client_name = str(payload.get("client_name") or "").strip()
    trainer_name = str(payload.get("trainer_name") or "").strip()
    scope = str(payload.get("scope") or "").strip().lower()

    if scope != "anamnesi" or not client_name or not trainer_name:
        return PublicValidateProbe(
            status="warning",
            detail="Il token risponde, ma il payload pubblico non e coerente con l'anamnesi.",
            validate_url=validate_url,
        )

    return PublicValidateProbe(
        status="ok",
        detail="Il token pubblico anamnesi e valido e restituisce i dati minimi attesi.",
        validate_url=validate_url,
        client_name=client_name,
        trainer_name=trainer_name,
    )


def _build_runtime_check() -> ConnectivityCheck:
    runtime_status = build_connectivity_status()
    if runtime_status.profile != "public_portal":
        return ConnectivityCheck(
            code="runtime_profile",
            label="Profilo runtime",
            status="critical",
            detail="Il portale pubblico non e ancora attivo nel runtime corrente.",
        )

    return ConnectivityCheck(
        code="runtime_profile",
        label="Profilo runtime",
        status="ok",
        detail="Il runtime risulta gia configurato sul profilo portale pubblico.",
    )


def validate_public_portal_link(
    payload: ConnectivityPortalValidationRequest,
) -> ConnectivityPortalValidationResponse:
    runtime_check = _build_runtime_check()
    validate_url = _build_validate_url(payload.public_url, payload.token)

    page_probe = _probe_public_page(payload.public_url)
    validate_probe = _probe_public_validate(validate_url)

    checks = [
        runtime_check,
        ConnectivityCheck(
            code="public_page",
            label="Pagina pubblica",
            status=page_probe.status,
            detail=page_probe.detail,
        ),
        ConnectivityCheck(
            code="public_validate",
            label="Token anamnesi",
            status=validate_probe.status,
            detail=validate_probe.detail,
        ),
    ]

    statuses = {check.status for check in checks}
    if "critical" in statuses:
        status = "blocked"
    elif "warning" in statuses:
        status = "partial"
    else:
        status = "ready"

    if status == "ready":
        summary = "Link anamnesi pubblico verificato: pagina e token rispondono correttamente."
    elif status == "partial":
        summary = "Link pubblico raggiungibile, ma la risposta del token non e ancora perfetta."
    else:
        summary = "Link anamnesi pubblico non pronto: completa prima il profilo portale pubblico."

    return ConnectivityPortalValidationResponse(
        validated_at=datetime.now(timezone.utc),
        status=status,
        summary=summary,
        public_url=payload.public_url,
        validate_url=validate_url,
        masked_client_name=validate_probe.client_name,
        masked_trainer_name=validate_probe.trainer_name,
        checks=checks,
    )
