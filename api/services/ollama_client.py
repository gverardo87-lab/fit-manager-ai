# api/services/ollama_client.py
"""
Client condiviso per Ollama — config, chiamata HTTP, utility prompt.

Usato da: workout_commentary, workout_copilot (futuro), altri servizi AI.
Privacy-first: nessun dato personale esce dalla macchina.
"""

import json
import logging
import os
from typing import Optional

import requests

from api.models.exercise import Exercise
from api.models.workout import WorkoutExercise

logger = logging.getLogger("fitmanager.services.ollama")

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:9b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))


# ═══════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════


def parse_json_field(value: Optional[str], fallback=None):
    """Parse un campo JSON (str in DB) in modo sicuro."""
    if not value:
        return fallback if fallback is not None else []
    try:
        return json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, TypeError):
        return fallback if fallback is not None else []


# ═══════════════════════════════════════════════════════════
# OLLAMA CALL
# ═══════════════════════════════════════════════════════════


def call_ollama(system: str, prompt: str, num_predict: int = 2048) -> str:
    """Chiama Ollama /api/generate e ritorna il testo generato."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": 0.4,
            "num_predict": num_predict,
        },
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
        return resp.json()["response"]
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama non raggiungibile. Verifica che sia avviato (ollama serve)"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Ollama timeout — la generazione ha superato il limite di tempo"
        )
    except Exception as e:
        raise RuntimeError(f"Errore Ollama: {e}")


# ═══════════════════════════════════════════════════════════
# PROMPT FORMATTING
# ═══════════════════════════════════════════════════════════


def format_exercise_for_prompt(we: WorkoutExercise, ex: Exercise) -> str:
    """Formatta un singolo esercizio per il prompt con dati enriched."""
    lines = [
        f"  - {ex.nome} ({ex.categoria}, {ex.attrezzatura})",
        f"    Serie: {we.serie} x {we.ripetizioni}, Riposo: {we.tempo_riposo_sec}s",
    ]
    if we.tempo_esecuzione:
        lines.append(f"    Tempo: {we.tempo_esecuzione}")
    if we.note:
        lines.append(f"    Note trainer: {we.note}")

    # Muscoli
    muscoli_p = parse_json_field(ex.muscoli_primari)
    if muscoli_p:
        lines.append(f"    Muscoli primari: {', '.join(muscoli_p)}")

    muscoli_s = parse_json_field(ex.muscoli_secondari)
    if muscoli_s:
        lines.append(f"    Muscoli secondari: {', '.join(muscoli_s)}")

    # Esecuzione (troncata per context window)
    if ex.esecuzione:
        lines.append(f"    Esecuzione: {ex.esecuzione[:200]}")

    # Coaching cues (max 3)
    cues = parse_json_field(ex.coaching_cues)
    if cues:
        lines.append(f"    Cues: {'; '.join(cues[:3])}")

    # Errori comuni (max 2)
    errori = parse_json_field(ex.errori_comuni)
    if errori:
        err_strs = []
        for e in errori[:2]:
            if isinstance(e, dict) and "errore" in e:
                err_strs.append(e["errore"])
            elif isinstance(e, str):
                err_strs.append(e)
        if err_strs:
            lines.append(f"    Errori comuni: {'; '.join(err_strs)}")

    # Sicurezza e controindicazioni
    if ex.note_sicurezza:
        lines.append(f"    Sicurezza: {ex.note_sicurezza[:150]}")

    contras = parse_json_field(ex.controindicazioni)
    if contras:
        lines.append(f"    Controindicazioni: {', '.join(contras[:3])}")

    return "\n".join(lines)


def format_anamnesi_for_prompt(anamnesi: dict) -> str:
    """Formatta l'anamnesi per il prompt SENZA PII (nome, email, telefono)."""
    lines: list[str] = []

    def add_question(key: str, label: str) -> None:
        q = anamnesi.get(key, {})
        if isinstance(q, dict) and q.get("presente"):
            detail = q.get("dettaglio", "")
            lines.append(f"- {label}: SI{f' ({detail})' if detail else ''}")

    add_question("infortuni_attuali", "Infortuni attuali")
    add_question("infortuni_pregressi", "Infortuni pregressi")
    add_question("interventi_chirurgici", "Interventi chirurgici")
    add_question("dolori_cronici", "Dolori cronici")
    add_question("patologie", "Patologie")
    add_question("farmaci", "Farmaci in uso")
    add_question("problemi_cardiovascolari", "Problemi cardiovascolari")
    add_question("problemi_respiratori", "Problemi respiratori")

    livello = anamnesi.get("livello_attivita", "")
    if livello:
        lines.append(f"- Livello attivita: {livello}")

    obiettivi = anamnesi.get("obiettivi_specifici", "")
    if obiettivi:
        lines.append(f"- Obiettivi specifici: {obiettivi}")

    limitazioni = anamnesi.get("limitazioni_funzionali", "")
    if limitazioni:
        lines.append(f"- Limitazioni funzionali: {limitazioni}")

    return "\n".join(lines) if lines else "Nessuna informazione anamnesi disponibile."
