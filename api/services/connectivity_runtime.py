"""Read-only runtime helpers for Tailscale/Funnel connectivity status."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from api.schemas.system import ConnectivityCheck, ConnectivityStatusResponse
from api.services.system_runtime import get_public_base_url, is_public_portal_enabled

TAILSCALE_BINARY_HINTS = (
    Path(r"C:\Program Files\Tailscale\tailscale.exe"),
    Path(r"C:\Program Files (x86)\Tailscale\tailscale.exe"),
)
COMMAND_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def combined_output(self) -> str:
        return "\n".join(part for part in (self.stdout, self.stderr) if part).strip()


@dataclass(frozen=True)
class TailscaleProbe:
    cli_installed: bool
    version: str | None
    status: str
    connected: bool
    ip: str | None
    dns_name: str | None


@dataclass(frozen=True)
class FunnelProbe:
    status: str
    enabled: bool


def _resolve_tailscale_binary() -> str | None:
    binary = shutil.which("tailscale")
    if binary:
        return binary

    for candidate in TAILSCALE_BINARY_HINTS:
        if candidate.exists():
            return str(candidate)

    return None


def _run_tailscale_command(binary: str, *args: str) -> CommandResult:
    completed = subprocess.run(
        [binary, *args],
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
        check=False,
    )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def _normalize_dns_name(value: str | None) -> str | None:
    if not value:
        return None
    return value.rstrip(".").strip() or None


def _classify_command_error(result: CommandResult, *, allow_not_enabled: bool = False) -> str:
    text = result.combined_output.lower()
    if "accesso negato" in text or "access is denied" in text or "permission denied" in text:
        return "permission_denied"
    if allow_not_enabled and ("no serve config" in text or "not enabled" in text):
        return "not_enabled"
    if "failed to connect to local tailscaled" in text:
        return "not_connected"
    if "not logged in" in text or "logged out" in text:
        return "not_connected"
    return "error"


def _extract_version(binary: str) -> str | None:
    result = _run_tailscale_command(binary, "version")
    if result.returncode != 0:
        return None
    first_line = result.stdout.splitlines()[0].strip() if result.stdout else ""
    return first_line or None


def _extract_primary_ip(status_payload: dict) -> str | None:
    self_data = status_payload.get("Self") or {}
    ips = self_data.get("TailscaleIPs") or []
    if not isinstance(ips, list):
        return None

    for value in ips:
        if isinstance(value, str) and "." in value:
            return value

    for value in ips:
        if isinstance(value, str) and value:
            return value
    return None


def _probe_tailscale(binary: str | None) -> TailscaleProbe:
    if binary is None:
        return TailscaleProbe(
            cli_installed=False,
            version=None,
            status="not_installed",
            connected=False,
            ip=None,
            dns_name=None,
        )

    version = _extract_version(binary)
    status_result = _run_tailscale_command(binary, "status", "--json")
    if status_result.returncode != 0:
        return TailscaleProbe(
            cli_installed=True,
            version=version,
            status=_classify_command_error(status_result),
            connected=False,
            ip=None,
            dns_name=None,
        )

    try:
        payload = json.loads(status_result.stdout)
    except json.JSONDecodeError:
        return TailscaleProbe(
            cli_installed=True,
            version=version,
            status="error",
            connected=False,
            ip=None,
            dns_name=None,
        )

    self_data = payload.get("Self") or {}
    dns_name = _normalize_dns_name(self_data.get("DNSName"))
    ip = _extract_primary_ip(payload)
    backend_state = str(payload.get("BackendState") or "").lower()
    connected = bool(self_data.get("Online")) or bool(ip) or backend_state == "running"

    return TailscaleProbe(
        cli_installed=True,
        version=version,
        status="ok" if connected else "not_connected",
        connected=connected,
        ip=ip,
        dns_name=dns_name,
    )


def _probe_funnel(binary: str | None) -> FunnelProbe:
    if binary is None:
        return FunnelProbe(status="not_installed", enabled=False)

    result = _run_tailscale_command(binary, "funnel", "status")
    if result.returncode != 0:
        return FunnelProbe(
            status=_classify_command_error(result, allow_not_enabled=True),
            enabled=False,
        )

    text = result.combined_output.lower()
    enabled = "https://" in text or "|-- proxy" in text or "available on the internet" in text
    if enabled:
        return FunnelProbe(status="ok", enabled=True)
    return FunnelProbe(status="not_enabled", enabled=False)


def _public_base_url_matches_dns(public_base_url: str | None, dns_name: str | None) -> bool | None:
    if not public_base_url or not dns_name:
        return None

    hostname = urlparse(public_base_url).hostname
    if hostname is None:
        return False
    return hostname.lower() == dns_name.lower()


def _resolve_profile(
    *,
    public_portal_enabled: bool,
    public_base_url_matches_dns: bool | None,
    funnel_enabled: bool,
    tailscale_connected: bool,
) -> str:
    if (
        public_portal_enabled
        and tailscale_connected
        and funnel_enabled
        and public_base_url_matches_dns is True
    ):
        return "public_portal"
    if tailscale_connected:
        return "trusted_devices"
    return "local_only"


def _resolve_next_action(
    *,
    tailscale_status: str,
    public_portal_enabled: bool,
    public_base_url: str | None,
    public_base_url_matches_dns: bool | None,
    funnel_status: str,
) -> tuple[str, str]:
    if tailscale_status == "not_installed":
        return ("install_tailscale", "Installa Tailscale sul PC")
    if tailscale_status == "permission_denied":
        return ("grant_tailscale_access", "Apri Tailscale con l'utente corretto")
    if tailscale_status != "ok":
        return ("connect_tailscale", "Accedi a Tailscale e verifica la connessione")
    if public_portal_enabled and not public_base_url:
        return ("configure_public_base_url", "Configura la base URL pubblica")
    if public_portal_enabled and public_base_url_matches_dns is False:
        return ("review_public_base_url", "Allinea la base URL al DNS Tailscale")
    if public_portal_enabled and funnel_status != "ok":
        return ("enable_funnel", "Attiva Tailscale Funnel per il portale clienti")
    return ("ready", "Connettivita pronta")


def build_connectivity_status() -> ConnectivityStatusResponse:
    binary = _resolve_tailscale_binary()
    tailscale = _probe_tailscale(binary)
    funnel = _probe_funnel(binary)
    public_portal_enabled = is_public_portal_enabled()
    public_base_url = get_public_base_url()
    public_base_url_matches_dns = _public_base_url_matches_dns(
        public_base_url,
        tailscale.dns_name,
    )
    profile = _resolve_profile(
        public_portal_enabled=public_portal_enabled,
        public_base_url_matches_dns=public_base_url_matches_dns,
        funnel_enabled=funnel.enabled,
        tailscale_connected=tailscale.connected,
    )
    next_action_code, next_action_label = _resolve_next_action(
        tailscale_status=tailscale.status,
        public_portal_enabled=public_portal_enabled,
        public_base_url=public_base_url,
        public_base_url_matches_dns=public_base_url_matches_dns,
        funnel_status=funnel.status,
    )

    checks = [
        ConnectivityCheck(
            code="tailscale_cli",
            label="Client Tailscale",
            status="ok" if tailscale.cli_installed else "neutral",
            detail=(
                f"Installato ({tailscale.version})"
                if tailscale.cli_installed and tailscale.version
                else "Non installato: accesso remoto non ancora configurato"
            ),
        ),
        ConnectivityCheck(
            code="tailscale_session",
            label="Sessione Tailscale",
            status=(
                "ok"
                if tailscale.status == "ok"
                else "critical" if tailscale.status == "permission_denied" else "warning"
            ),
            detail={
                "ok": "Nodo raggiungibile e pronto per accesso fidato.",
                "permission_denied": "Il demone Tailscale risponde con accesso negato per questo utente.",
                "not_connected": "Tailscale e' installato ma il nodo non e' pronto.",
                "not_installed": "Tailscale non e' installato su questo PC.",
            }.get(tailscale.status, "Impossibile leggere lo stato locale di Tailscale."),
        ),
        ConnectivityCheck(
            code="tailscale_dns",
            label="DNS Tailscale",
            status=(
                "ok"
                if tailscale.dns_name
                else "warning" if tailscale.connected else "neutral"
            ),
            detail=(
                f"DNS rilevato: {tailscale.dns_name}"
                if tailscale.dns_name
                else "DNS non disponibile: MagicDNS o sessione Tailscale da verificare."
            ),
        ),
        ConnectivityCheck(
            code="public_base_url",
            label="Base URL portale",
            status=(
                "neutral"
                if not public_portal_enabled
                else "ok"
                if public_base_url and public_base_url_matches_dns is not False
                else "warning"
            ),
            detail=(
                "Portale pubblico disattivo: base URL non richiesta."
                if not public_portal_enabled
                else f"Configurata: {public_base_url}"
                if public_base_url and public_base_url_matches_dns is not False
                else "Portale pubblico attivo ma base URL assente o non allineata."
            ),
        ),
        ConnectivityCheck(
            code="funnel",
            label="Tailscale Funnel",
            status=(
                "neutral"
                if not public_portal_enabled
                else "ok"
                if funnel.status == "ok"
                else "critical" if funnel.status == "permission_denied" else "warning"
            ),
            detail=(
                "Non richiesto finche il portale pubblico resta disattivo."
                if not public_portal_enabled
                else "Funnel attivo e pronto per i link pubblici."
                if funnel.status == "ok"
                else "Funnel non ancora pronto o non accessibile da questo utente."
            ),
        ),
    ]

    missing_requirements: list[str] = []
    if tailscale.status == "not_installed":
        missing_requirements.append("Installa Tailscale sul PC del trainer.")
    elif tailscale.status == "permission_denied":
        missing_requirements.append(
            "Apri Tailscale con l'utente corretto o verifica i permessi locali del demone.",
        )
    elif tailscale.status != "ok":
        missing_requirements.append("Accedi a Tailscale e verifica che il nodo sia online.")

    if public_portal_enabled and not public_base_url:
        missing_requirements.append("Configura `PUBLIC_BASE_URL` per il portale clienti.")
    elif public_portal_enabled and public_base_url_matches_dns is False:
        missing_requirements.append(
            "Allinea `PUBLIC_BASE_URL` al DNS Tailscale rilevato su questa macchina.",
        )

    if public_portal_enabled and funnel.status != "ok":
        missing_requirements.append("Attiva `tailscale funnel --bg 3000` per il portale pubblico.")

    return ConnectivityStatusResponse(
        generated_at=datetime.now(timezone.utc),
        profile=profile,
        tailscale_cli_installed=tailscale.cli_installed,
        tailscale_version=tailscale.version,
        tailscale_status=tailscale.status,
        tailscale_connected=tailscale.connected,
        tailscale_ip=tailscale.ip,
        tailscale_dns_name=tailscale.dns_name,
        funnel_status=funnel.status,
        funnel_enabled=funnel.enabled,
        public_portal_enabled=public_portal_enabled,
        public_base_url=public_base_url,
        public_base_url_matches_dns=public_base_url_matches_dns,
        next_recommended_action_code=next_action_code,
        next_recommended_action_label=next_action_label,
        checks=checks,
        missing_requirements=missing_requirements,
    )
