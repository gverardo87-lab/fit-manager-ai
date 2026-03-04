"""
Confidence Scorer — calcola confidenza e rileva ambiguita'.

Score composto:
  intent_match   0.35 — quanti trigger pattern hanno matchato
  entities_found 0.30 — entita' obbligatorie presenti
  slots_filled   0.20 — campi opzionali compilati
  validation     0.15 — payload valido per lo schema target

Soglie:
  >= 0.70   ready (pronto per commit)
  0.40-0.69 needs_confirmation (mostrare con warning)
  < 0.40    non mostrare
"""

from api.services.assistant_parser.entity_extractor import ExtractedEntity, get_first_entity


# ── Required entities per intent ──────────────────────────────

_REQUIRED_ENTITIES: dict[str, list[str]] = {
    "agenda.create_event": ["date", "time"],
    "movement.create_manual": ["amount", "tipo_movement"],
    "measurement.create": ["metric_value"],
}

_OPTIONAL_ENTITIES: dict[str, list[str]] = {
    "agenda.create_event": ["person_name", "category_event"],
    "movement.create_manual": ["method_payment", "category_text", "date"],
    "measurement.create": ["person_name", "date"],
}


def compute_confidence(
    intent: str,
    intent_score: float,
    entities: list[ExtractedEntity],
) -> float:
    """
    Calcola confidenza composta per un'operazione parsed.

    Returns: float 0.0 - 1.0
    """
    # 1. Intent match (0.35)
    w_intent = min(intent_score, 1.0) * 0.35

    # 2. Required entities (0.30)
    required = _REQUIRED_ENTITIES.get(intent, [])
    if required:
        found = sum(1 for r in required if get_first_entity(entities, r))
        w_required = (found / len(required)) * 0.30
    else:
        w_required = 0.30

    # 3. Optional slots (0.20)
    optional = _OPTIONAL_ENTITIES.get(intent, [])
    if optional:
        found = sum(1 for o in optional if get_first_entity(entities, o))
        w_optional = (found / len(optional)) * 0.20
    else:
        w_optional = 0.10

    # 4. Validation (0.15) — base, raffinabile
    w_validation = 0.15

    # Penalty: entita' obbligatorie mancanti
    missing_required = [r for r in required if not get_first_entity(entities, r)]
    penalty = len(missing_required) * 0.15

    score = w_intent + w_required + w_optional + w_validation - penalty
    return round(max(0.0, min(1.0, score)), 2)


def get_missing_fields(
    intent: str,
    entities: list[ExtractedEntity],
) -> list[str]:
    """Ritorna lista di campi obbligatori mancanti."""
    required = _REQUIRED_ENTITIES.get(intent, [])
    return [r for r in required if not get_first_entity(entities, r)]
