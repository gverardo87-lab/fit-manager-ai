"""Guided verification helpers for FitManager connectivity setup."""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib import error, request

from api.schemas.system import ConnectivityCheck, ConnectivityVerifyResponse
from api.services.connectivity_runtime import build_connectivity_status

VERIFY_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class PublicOriginProbe:
    status: str
    detail: str
    target_url: str | None


def _resolve_target_profile(status) -> str:
    if status.public_portal_enabled:
        return "public_portal"
    return status.profile


def _probe_public_origin(public_base_url: str | None) -> PublicOriginProbe:
    if not public_base_url:
        return PublicOriginProbe(
            status="neutral",
            detail="Base URL pubblica non configurata: verifica esterna non eseguibile.",
            target_url=None,
        )

    target_url = f"{public_base_url.rstrip('/')}/health"
    req = request.Request(
        target_url,
        headers={"User-Agent": "FitManagerConnectivityVerify/1.0"},
    )

    try:
        with request.urlopen(req, timeout=VERIFY_TIMEOUT_SECONDS) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        return PublicOriginProbe(
            status="warning",
            detail=f"L'origine pubblica risponde con HTTP {exc.code}.",
            target_url=target_url,
        )
    except error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, socket.timeout):
            detail = "Timeout nel contatto con l'origine pubblica configurata."
        else:
            detail = f"Impossibile raggiungere l'origine pubblica: {reason}."
        return PublicOriginProbe(status="warning", detail=detail, target_url=target_url)
    except TimeoutError:
        return PublicOriginProbe(
            status="warning",
            detail="Timeout nel contatto con l'origine pubblica configurata.",
            target_url=target_url,
        )

    if status_code != 200:
        return PublicOriginProbe(
            status="warning",
            detail=f"L'origine pubblica ha risposto con HTTP {status_code}.",
            target_url=target_url,
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return PublicOriginProbe(
            status="warning",
            detail="L'origine pubblica e raggiungibile ma /health non restituisce JSON valido.",
            target_url=target_url,
        )

    health_status = str(payload.get("status") or "").strip().lower()
    if health_status == "ok":
        return PublicOriginProbe(
            status="ok",
            detail="Origine pubblica raggiungibile: frontend e proxy /health rispondono correttamente.",
            target_url=target_url,
        )
    if health_status:
        return PublicOriginProbe(
            status="warning",
            detail=(
                "Origine pubblica raggiungibile, ma /health segnala stato "
                f"`{health_status}`."
            ),
            target_url=target_url,
        )

    return PublicOriginProbe(
        status="warning",
        detail="Origine pubblica raggiungibile, ma il payload /health non e atteso.",
        target_url=target_url,
    )


def _build_target_profile_check(status, target_profile: str) -> ConnectivityCheck:
    if target_profile == "local_only":
        return ConnectivityCheck(
            code="target_profile",
            label="Profilo richiesto",
            status="ok",
            detail="Modalita locale confermata: nessun requisito remoto richiesto.",
        )

    if target_profile == "trusted_devices":
        detail = (
            "Tailscale e connesso: FitManager puo essere raggiunto da dispositivi fidati."
            if status.tailscale_connected
            else "Tailscale non e ancora pronto: l'accesso da altri dispositivi resta bloccato."
        )
        return ConnectivityCheck(
            code="target_profile",
            label="Profilo richiesto",
            status="ok" if status.tailscale_connected else "critical",
            detail=detail,
        )

    missing = "; ".join(status.missing_requirements)
    return ConnectivityCheck(
        code="target_profile",
        label="Profilo richiesto",
        status="ok" if not missing else "critical",
        detail=(
            "Portale pubblico configurato: i prerequisiti di base risultano completi."
            if not missing
            else f"Il profilo pubblico non e ancora completo: {missing}"
        ),
    )


def _build_runtime_state_check(status, target_profile: str) -> ConnectivityCheck:
    if target_profile == "local_only":
        return ConnectivityCheck(
            code="runtime_state",
            label="Runtime attuale",
            status="ok",
            detail="Il CRM resta operativo in locale e non dipende da Tailscale.",
        )

    if target_profile == "trusted_devices":
        runtime_ready = status.profile in {"trusted_devices", "public_portal"}
        detail = (
            "Il runtime ha raggiunto il profilo multi-dispositivo."
            if runtime_ready
            else "Il runtime non e ancora pronto per l'accesso da altri dispositivi."
        )
        return ConnectivityCheck(
            code="runtime_state",
            label="Runtime attuale",
            status="ok" if runtime_ready else "critical",
            detail=detail,
        )

    if status.profile == "public_portal":
        detail = "Il runtime ha raggiunto il profilo pubblico completo."
        check_status = "ok"
    elif status.profile == "trusted_devices":
        detail = (
            "Il runtime e fermo a dispositivi fidati: manca ancora la piena esposizione "
            "pubblica del portale."
        )
        check_status = "warning"
    else:
        detail = "Il runtime e ancora locale: il profilo pubblico non e operativo."
        check_status = "critical"

    return ConnectivityCheck(
        code="runtime_state",
        label="Runtime attuale",
        status=check_status,
        detail=detail,
    )


def _build_public_origin_check(target_profile: str, probe: PublicOriginProbe) -> ConnectivityCheck:
    if target_profile != "public_portal":
        return ConnectivityCheck(
            code="public_origin",
            label="Origine pubblica",
            status="neutral",
            detail="Non richiesta finche il profilo pubblico resta disattivo.",
        )

    return ConnectivityCheck(
        code="public_origin",
        label="Origine pubblica",
        status=probe.status,
        detail=probe.detail,
    )


def _resolve_next_action(status, target_profile: str, probe: PublicOriginProbe) -> tuple[str, str]:
    if target_profile == "public_portal" and probe.status == "warning" and not status.missing_requirements:
        return (
            "verify_public_origin",
            "Controlla dal browser che il link pubblico risponda davvero",
        )

    if target_profile == "local_only":
        return ("ready", "Configurazione locale verificata")

    if target_profile == "trusted_devices" and status.tailscale_connected:
        return ("ready", "Accesso per dispositivi fidati verificato")

    if target_profile == "public_portal" and probe.status == "ok" and status.profile == "public_portal":
        return ("ready", "Portale pubblico verificato")

    return (status.next_recommended_action_code, status.next_recommended_action_label)


def _resolve_summary(target_profile: str, verification_status: str) -> str:
    summaries = {
        ("local_only", "ready"): "Configurazione locale verificata: il CRM e pronto su questo PC.",
        (
            "trusted_devices",
            "ready",
        ): "Configurazione multi-dispositivo verificata: Tailscale e pronto per i device fidati.",
        (
            "trusted_devices",
            "blocked",
        ): "Accesso da dispositivi fidati non verificato: Tailscale non e ancora pronto.",
        (
            "public_portal",
            "ready",
        ): "Portale pubblico verificato: l'origine configurata risponde correttamente.",
        (
            "public_portal",
            "partial",
        ): "Configurazione pubblica salvata, ma l'origine esterna non e ancora verificata.",
        (
            "public_portal",
            "blocked",
        ): "Portale pubblico non pronto: completa prima i prerequisiti di runtime.",
    }
    return summaries.get(
        (target_profile, verification_status),
        "Configurazione in verifica: controlla i check per il prossimo passo corretto.",
    )


def verify_connectivity_setup() -> ConnectivityVerifyResponse:
    runtime_status = build_connectivity_status()
    target_profile = _resolve_target_profile(runtime_status)
    public_origin_probe = _probe_public_origin(
        runtime_status.public_base_url if target_profile == "public_portal" else None,
    )

    checks = [
        _build_target_profile_check(runtime_status, target_profile),
        _build_runtime_state_check(runtime_status, target_profile),
        _build_public_origin_check(target_profile, public_origin_probe),
    ]

    check_statuses = {check.status for check in checks}
    if "critical" in check_statuses:
        verification_status = "blocked"
    elif "warning" in check_statuses:
        verification_status = "partial"
    else:
        verification_status = "ready"

    next_action_code, next_action_label = _resolve_next_action(
        runtime_status,
        target_profile,
        public_origin_probe,
    )

    return ConnectivityVerifyResponse(
        verified_at=datetime.now(timezone.utc),
        target_profile=target_profile,
        effective_profile=runtime_status.profile,
        status=verification_status,
        summary=_resolve_summary(target_profile, verification_status),
        verified_public_origin=public_origin_probe.target_url,
        checks=checks,
        next_recommended_action_code=next_action_code,
        next_recommended_action_label=next_action_label,
    )
