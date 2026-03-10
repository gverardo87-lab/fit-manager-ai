"""Helper runtime condivisi per surface salute e snapshot di supporto."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, text

from api import __version__
from api.config import DATA_DIR, DATABASE_URL
from api.schemas.system import (
    HealthResponse,
    SupportSnapshotBackupItem,
    SupportSnapshotResponse,
)
from api.services.license import check_license

BACKUP_DIR = DATA_DIR / "backups"
APP_STARTED_AT = datetime.now(timezone.utc)


def is_license_enforcement_enabled() -> bool:
    value = os.getenv("LICENSE_ENFORCEMENT_ENABLED", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def is_public_portal_enabled() -> bool:
    value = os.getenv("PUBLIC_PORTAL_ENABLED", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def get_public_base_url() -> str | None:
    value = os.getenv("PUBLIC_BASE_URL", "").strip()
    return value or None


def is_public_base_url_configured() -> bool:
    return get_public_base_url() is not None


def get_app_mode() -> str:
    return "development" if "crm_dev" in DATABASE_URL else "production"


def get_distribution_mode() -> str:
    return "installer" if getattr(sys, "frozen", False) else "source"


def _ping(session: Session) -> bool:
    try:
        session.exec(text("SELECT 1")).one()
        return True
    except Exception:
        return False


def _read_checksum_sidecar(backup_path: Path) -> str | None:
    sidecar = backup_path.with_suffix(".sha256")
    if not sidecar.exists():
        return None
    content = sidecar.read_text(encoding="utf-8").strip()
    return content.split()[0] if content else None


def list_recent_backups(limit: int = 5) -> list[SupportSnapshotBackupItem]:
    if not BACKUP_DIR.exists():
        return []

    backups: list[SupportSnapshotBackupItem] = []
    files = sorted(
        BACKUP_DIR.glob("*.sqlite"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for backup_path in files[:limit]:
        stat = backup_path.stat()
        backups.append(
            SupportSnapshotBackupItem(
                filename=backup_path.name,
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(
                    stat.st_mtime,
                    tz=timezone.utc,
                ).isoformat(),
                checksum=_read_checksum_sidecar(backup_path),
            )
        )
    return backups


def build_health_response(
    session: Session,
    catalog_session: Session,
) -> HealthResponse:
    db_ok = _ping(session)
    catalog_ok = _ping(catalog_session)
    license_result = check_license()
    healthy = db_ok and catalog_ok

    return HealthResponse(
        status="ok" if healthy else "degraded",
        version=__version__,
        db="connected" if db_ok else "disconnected",
        catalog="connected" if catalog_ok else "disconnected",
        license_status=license_result.status,
        license_enforcement_enabled=is_license_enforcement_enabled(),
        app_mode=get_app_mode(),
        distribution_mode=get_distribution_mode(),
        public_portal_enabled=is_public_portal_enabled(),
        public_base_url_configured=is_public_base_url_configured(),
        started_at=APP_STARTED_AT,
        uptime_seconds=int((datetime.now(timezone.utc) - APP_STARTED_AT).total_seconds()),
    )


def build_support_snapshot(
    session: Session,
    catalog_session: Session,
) -> SupportSnapshotResponse:
    return SupportSnapshotResponse(
        generated_at=datetime.now(timezone.utc),
        public_base_url=get_public_base_url(),
        health=build_health_response(session, catalog_session),
        recent_backups=list_recent_backups(),
    )
