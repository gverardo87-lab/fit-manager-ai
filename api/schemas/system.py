"""Schemas per stato runtime e salute installazione."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


HealthStatus = Literal["ok", "degraded"]
ConnectionStatus = Literal["connected", "disconnected"]
LicenseStatus = Literal["valid", "missing", "invalid", "expired", "unconfigured"]
AppMode = Literal["development", "production"]
DistributionMode = Literal["source", "installer"]


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
