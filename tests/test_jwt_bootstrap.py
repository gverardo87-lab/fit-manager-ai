"""Test JWT_SECRET auto-bootstrap in api/config.py."""

import os
import importlib
from pathlib import Path


def test_jwt_bootstrap_generates_and_persists(tmp_path, monkeypatch):
    """Fresh env senza JWT_SECRET → genera, salva in data/.env, ritorna hex 64 chars."""
    # Simula DATA_DIR in tmp
    monkeypatch.setenv("JWT_SECRET", "")
    monkeypatch.setattr("api.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("api.config.os.getenv", lambda k, d="": "" if k == "JWT_SECRET" else os.getenv(k, d))

    from api.config import _resolve_jwt_secret

    # Forza riesecuzione con DATA_DIR patchato
    monkeypatch.setattr("api.config.DATA_DIR", tmp_path)
    secret = _resolve_jwt_secret()

    # Deve essere un hex di 64 chars (32 bytes)
    assert len(secret) == 64
    assert all(c in "0123456789abcdef" for c in secret)

    # Deve essere stato scritto in data/.env
    env_file = tmp_path / ".env"
    assert env_file.exists()
    content = env_file.read_text(encoding="utf-8")
    assert f"JWT_SECRET={secret}" in content


def test_jwt_bootstrap_respects_existing_env(monkeypatch):
    """Se JWT_SECRET e' gia' settato, non genera nulla."""
    monkeypatch.setenv("JWT_SECRET", "my-custom-secret-key")

    from api.config import _resolve_jwt_secret

    secret = _resolve_jwt_secret()
    assert secret == "my-custom-secret-key"


def test_jwt_bootstrap_appends_without_overwrite(tmp_path, monkeypatch):
    """Se data/.env esiste gia' con altre variabili, appende senza sovrascrivere."""
    env_file = tmp_path / ".env"
    env_file.write_text("OTHER_VAR=hello\n", encoding="utf-8")

    monkeypatch.setenv("JWT_SECRET", "")
    monkeypatch.setattr("api.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("api.config.os.getenv", lambda k, d="": "" if k == "JWT_SECRET" else os.getenv(k, d))

    from api.config import _resolve_jwt_secret

    monkeypatch.setattr("api.config.DATA_DIR", tmp_path)
    secret = _resolve_jwt_secret()

    content = env_file.read_text(encoding="utf-8")
    assert "OTHER_VAR=hello" in content
    assert f"JWT_SECRET={secret}" in content
