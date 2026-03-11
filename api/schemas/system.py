"""Schemas per stato runtime e support snapshot dell'installazione."""

from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, model_validator


HealthStatus = Literal["ok", "degraded"]
ConnectionStatus = Literal["connected", "disconnected"]
LicenseStatus = Literal["valid", "missing", "invalid", "expired", "unconfigured"]
AppMode = Literal["development", "production"]
DistributionMode = Literal["source", "installer"]
ConnectivityProfile = Literal["local_only", "trusted_devices", "public_portal"]
ConnectivityProbeStatus = Literal[
    "ok",
    "not_installed",
    "not_connected",
    "permission_denied",
    "not_enabled",
    "error",
]
ConnectivityCheckStatus = Literal["ok", "warning", "critical", "neutral"]
ConnectivityVerifyStatus = Literal["ready", "partial", "blocked"]
ConnectivityActionCode = Literal[
    "install_tailscale",
    "connect_tailscale",
    "grant_tailscale_access",
    "configure_public_base_url",
    "review_public_base_url",
    "enable_funnel",
    "verify_public_origin",
    "ready",
]


class HealthResponse(BaseModel):
    status: HealthStatus
    version: str
    db: ConnectionStatus
    catalog: ConnectionStatus
    license_status: LicenseStatus
    license_enforcement_enabled: bool
    app_mode: AppMode
    distribution_mode: DistributionMode
    public_portal_enabled: bool
    public_base_url_configured: bool
    started_at: datetime
    uptime_seconds: int


class SupportSnapshotBackupItem(BaseModel):
    filename: str
    size_bytes: int
    created_at: str
    checksum: str | None = None


class SupportSnapshotResponse(BaseModel):
    generated_at: datetime
    public_base_url: str | None = None
    health: HealthResponse
    recent_backups: list[SupportSnapshotBackupItem]


class ConnectivityCheck(BaseModel):
    code: str
    label: str
    status: ConnectivityCheckStatus
    detail: str


class ConnectivityStatusResponse(BaseModel):
    generated_at: datetime
    profile: ConnectivityProfile
    tailscale_cli_installed: bool
    tailscale_version: str | None = None
    tailscale_status: ConnectivityProbeStatus
    tailscale_connected: bool
    tailscale_ip: str | None = None
    tailscale_dns_name: str | None = None
    funnel_status: ConnectivityProbeStatus
    funnel_enabled: bool
    public_portal_enabled: bool
    public_base_url: str | None = None
    public_base_url_matches_dns: bool | None = None
    next_recommended_action_code: ConnectivityActionCode
    next_recommended_action_label: str
    checks: list[ConnectivityCheck]
    missing_requirements: list[str]


class ConnectivityConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: ConnectivityProfile
    public_base_url: str | None = None

    @model_validator(mode="after")
    def validate_public_base_url(self):
        if self.profile != "public_portal":
            return self

        value = (self.public_base_url or "").strip()
        if not value:
            raise ValueError("La base URL pubblica e obbligatoria per il profilo portale pubblico")

        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("La base URL pubblica deve essere un URL HTTPS assoluto")

        return self


class ConnectivityConfigResponse(BaseModel):
    applied_at: datetime
    profile: ConnectivityProfile
    public_portal_enabled: bool
    public_base_url: str | None = None
    written_keys: list[str]
    restart_required: bool
    message: str


class ConnectivityVerifyResponse(BaseModel):
    verified_at: datetime
    target_profile: ConnectivityProfile
    effective_profile: ConnectivityProfile
    status: ConnectivityVerifyStatus
    summary: str
    verified_public_origin: str | None = None
    checks: list[ConnectivityCheck]
    next_recommended_action_code: ConnectivityActionCode
    next_recommended_action_label: str
