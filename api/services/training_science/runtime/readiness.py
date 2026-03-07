"""Helper condivisi per readiness clinica e stato anamnesi."""

from datetime import date
import json

from api.schemas.training_science import TSAnamnesiState


def parse_iso_date(value: object) -> date | None:
    """Parse ISO date sicuro; ritorna None su input non valido."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def extract_anamnesi_reference_date(anamnesi_json: str | None) -> date | None:
    """Estrae la data di riferimento piu' utile dall'anamnesi serializzata."""
    if not anamnesi_json:
        return None
    try:
        payload = json.loads(anamnesi_json)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    candidates = [
        payload.get("updated_at"),
        payload.get("last_review_at"),
        payload.get("data_ultima_revisione"),
        payload.get("compiled_at"),
        payload.get("created_at"),
        payload.get("data_compilazione"),
    ]
    for candidate in candidates:
        parsed = parse_iso_date(candidate)
        if parsed is not None:
            return parsed
    return None


def get_anamnesi_state(anamnesi_json: str | None) -> TSAnamnesiState:
    """Classifica l'anamnesi in missing/legacy/structured."""
    if not anamnesi_json:
        return "missing"
    try:
        payload = json.loads(anamnesi_json)
    except (TypeError, ValueError, json.JSONDecodeError):
        return "legacy"

    if not isinstance(payload, dict):
        return "legacy"
    if payload.get("schema_version") or payload.get("sezioni") or payload.get("anagrafica"):
        return "structured"
    return "legacy"
