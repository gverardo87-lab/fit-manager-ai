"""Write-safe helpers for FitManager connectivity configuration in data/.env."""

from __future__ import annotations

import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from api.config import DATA_DIR
from api.schemas.system import ConnectivityConfigRequest, ConnectivityConfigResponse

ENV_FILE = DATA_DIR / ".env"
_ENV_KEY_PATTERN = re.compile(r"^\s*([A-Z0-9_]+)\s*=")


def _normalize_updates(payload: ConnectivityConfigRequest) -> dict[str, str | None]:
    if payload.profile == "public_portal":
        return {
            "PUBLIC_PORTAL_ENABLED": "true",
            "PUBLIC_BASE_URL": (payload.public_base_url or "").strip(),
        }

    return {
        "PUBLIC_PORTAL_ENABLED": "false",
        "PUBLIC_BASE_URL": None,
    }


def _read_env_lines(env_file: Path) -> list[str]:
    if not env_file.exists():
        return []
    return env_file.read_text(encoding="utf-8").splitlines()


def _write_env_values(env_file: Path, updates: dict[str, str | None]) -> list[str]:
    env_file.parent.mkdir(parents=True, exist_ok=True)
    lines = _read_env_lines(env_file)
    updated_lines = list(lines)
    written_keys: list[str] = []

    for key, value in updates.items():
        matching_indexes = [
            index
            for index, line in enumerate(updated_lines)
            if (match := _ENV_KEY_PATTERN.match(line)) and match.group(1) == key
        ]

        if value is None:
            if matching_indexes:
                for index in reversed(matching_indexes):
                    updated_lines.pop(index)
                written_keys.append(key)
            continue

        new_line = f"{key}={value}"
        if matching_indexes:
            for index in reversed(matching_indexes[1:]):
                updated_lines.pop(index)
            updated_lines[matching_indexes[0]] = new_line
        else:
            updated_lines.append(new_line)
        written_keys.append(key)

    content = "\n".join(updated_lines).strip()
    temp_path: str | None = None
    try:
        fd, temp_path = tempfile.mkstemp(
            prefix=".env.",
            suffix=".tmp",
            dir=str(env_file.parent),
        )
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as temp_file:
            temp_file.write(f"{content}\n" if content else "")
        os.replace(temp_path, env_file)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
    return written_keys


def _apply_process_env(updates: dict[str, str | None]) -> None:
    for key, value in updates.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def apply_connectivity_config(payload: ConnectivityConfigRequest) -> ConnectivityConfigResponse:
    updates = _normalize_updates(payload)
    written_keys = _write_env_values(ENV_FILE, updates)
    _apply_process_env(updates)

    public_portal_enabled = updates["PUBLIC_PORTAL_ENABLED"] == "true"
    public_base_url = updates["PUBLIC_BASE_URL"]
    message = (
        "Portale pubblico configurato e base URL salvata."
        if payload.profile == "public_portal"
        else "Configurazione remota salvata: il portale pubblico e ora disattivo."
    )

    return ConnectivityConfigResponse(
        applied_at=datetime.now(timezone.utc),
        profile=payload.profile,
        public_portal_enabled=public_portal_enabled,
        public_base_url=public_base_url,
        written_keys=written_keys,
        restart_required=False,
        message=message,
    )
