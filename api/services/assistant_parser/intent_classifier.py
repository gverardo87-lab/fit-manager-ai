"""
Intent Classifier — classificazione intent via regex.

3 intent pilota V0.5:
  agenda.create_event     — sessione, appuntamento, pt, sala, corso, colloquio
  movement.create_manual  — spesa, uscita, incasso, entrata, euro
  measurement.create      — peso, massa grassa, vita, fianchi, pressione
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class IntentCandidate:
    """Candidato intent con score."""

    intent: str
    score: float  # 0.0 - 1.0
    matched_triggers: list[str]


# ── Trigger patterns per intent ──────────────────────────────

_AGENDA_TRIGGERS = [
    (r"\b(sessione|sessioni)\b", 0.30),
    (r"\b(appuntamento|appuntamenti)\b", 0.30),
    (r"\b(lezione|lezioni)\b", 0.25),
    (r"\bpt\b", 0.35),
    (r"\b(personal\s*training)\b", 0.35),
    (r"\b(colloquio|consulenza)\b", 0.30),
    (r"\b(sala|corso)\b", 0.25),
    (r"\b(prenota|prenotare|fissa|fissare)\b", 0.20),
]

_MOVEMENT_TRIGGERS = [
    (r"\b(spesa|spese)\b", 0.35),
    (r"\b(uscita|uscite)\b", 0.30),
    (r"\b(pago|pagamento|pagare|pagato)\b", 0.25),
    (r"\b(incasso|incassi|incassato)\b", 0.35),
    (r"\b(entrata|entrate)\b", 0.30),
    (r"\b(ricevo|ricevuto)\b", 0.25),
    (r"\b(affitto|bolletta|utenza|attrezzatura|commercialista)\b", 0.20),
    (r"\b(euro|€)\b", 0.15),
]

_MEASUREMENT_TRIGGERS = [
    (r"\b(peso|pesare)\b", 0.30),
    (r"\b(massa\s*grassa|grasso)\b", 0.35),
    (r"\b(girovita|vita)\b", 0.25),
    (r"\b(fianchi)\b", 0.25),
    (r"\b(misura|misurazione|rilevazione)\b", 0.30),
    (r"\b(pressione|sistolica|diastolica)\b", 0.30),
    (r"\b(frequenza\s*cardiaca|battiti|fc)\b", 0.30),
    (r"\b(braccio|coscia|polpaccio|circonferenza)\b", 0.25),
]

_INTENT_CONFIG: dict[str, list[tuple[str, float]]] = {
    "agenda.create_event": _AGENDA_TRIGGERS,
    "movement.create_manual": _MOVEMENT_TRIGGERS,
    "measurement.create": _MEASUREMENT_TRIGGERS,
}


def classify_intent(normalized_text: str) -> list[IntentCandidate]:
    """
    Classifica intent dal testo normalizzato.

    Ritorna lista di IntentCandidate ordinata per score DESC.
    Solo candidati con almeno 1 trigger matchato.
    """
    candidates: list[IntentCandidate] = []

    for intent, triggers in _INTENT_CONFIG.items():
        total_score = 0.0
        matched: list[str] = []

        for pattern, weight in triggers:
            if re.search(pattern, normalized_text):
                total_score += weight
                matched.append(pattern)

        if matched:
            # Normalizza score a 0-1 (cap a 1.0)
            score = min(total_score, 1.0)
            candidates.append(IntentCandidate(
                intent=intent,
                score=score,
                matched_triggers=matched,
            ))

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates
