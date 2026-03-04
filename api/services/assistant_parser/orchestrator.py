"""
Orchestrator — pipeline principale del parser NLP.

Pipeline:
  1. normalize(text)
  2. classify_intent(normalized)
  3. extract_entities(normalized, original)
  4. resolve_entities(entities, session, trainer)
  5. build_payload(intent, entities, resolved)
  6. compute_confidence + detect_ambiguities
  7. assemble ParseResponse
"""

import logging
from datetime import date, datetime, time, timedelta
from typing import Any, Optional

from sqlmodel import Session

from api.models.trainer import Trainer
from api.schemas.assistant import (
    AmbiguityItem,
    ParsedOperation,
    ParseResponse,
    ResolvedEntity,
)
from api.services.assistant_parser.confidence import compute_confidence, get_missing_fields
from api.services.assistant_parser.entity_extractor import (
    ExtractedEntity,
    extract_entities,
    get_entities_by_type,
    get_first_entity,
)
from api.services.assistant_parser.entity_resolver import (
    ClientMatch,
    is_ambiguous,
    is_auto_resolved,
    resolve_client,
)
from api.services.assistant_parser.intent_classifier import classify_intent
from api.services.assistant_parser.normalizer import normalize

logger = logging.getLogger(__name__)

# Soglia minima per mostrare un'operazione
MIN_CONFIDENCE = 0.40


def orchestrate(
    text: str,
    trainer: Trainer,
    session: Session,
    catalog_session: Session,
) -> ParseResponse:
    """Analizza testo in linguaggio naturale e restituisce operazioni strutturate."""
    # 1. Normalize
    normalized = normalize(text)
    if not normalized:
        return _empty_response(text, "Testo vuoto.")

    # 2. Classify intent
    candidates = classify_intent(normalized)
    if not candidates:
        return _empty_response(text, "Non ho capito il comando. Prova con qualcosa come: "
                               "'Marco domani alle 18 PT' o 'spesa affitto 800 euro'.")

    # 3. Extract entities
    entities = extract_entities(normalized, text)

    # 4. Resolve client names
    resolved_entities: list[ResolvedEntity] = []
    ambiguities: list[AmbiguityItem] = []
    client_id: Optional[int] = None
    client_name: Optional[str] = None

    name_entity = get_first_entity(entities, "person_name")
    if name_entity:
        matches = resolve_client(name_entity.value, session, trainer.id)
        if matches:
            if is_auto_resolved(matches):
                client_id = matches[0].client.id
                client_name = matches[0].full_name
                resolved_entities.append(ResolvedEntity(
                    type="client",
                    raw=name_entity.raw,
                    value=client_id,
                    label=client_name,
                    confidence=matches[0].score,
                ))
            elif is_ambiguous(matches):
                ambiguities.append(_build_client_ambiguity(name_entity.raw, matches[:3]))
            elif matches[0].score >= 0.70:
                # Singolo match ma non abbastanza forte per auto-resolve
                client_id = matches[0].client.id
                client_name = matches[0].full_name
                resolved_entities.append(ResolvedEntity(
                    type="client",
                    raw=name_entity.raw,
                    value=client_id,
                    label=client_name,
                    confidence=matches[0].score,
                ))

    # 5. Build operations for top intent
    top_intent = candidates[0]
    operations: list[ParsedOperation] = []

    payload = _build_payload(top_intent.intent, entities, client_id, client_name)
    if payload is not None:
        confidence = compute_confidence(top_intent.intent, top_intent.score, entities)

        if confidence >= MIN_CONFIDENCE:
            preview = _build_preview_label(top_intent.intent, payload, client_name)
            operations.append(ParsedOperation(
                intent=top_intent.intent,
                payload=payload,
                preview_label=preview,
                confidence=confidence,
            ))

    # 6. Build entity list for UI
    for e in entities:
        if e.type == "person_name":
            continue  # Gia' gestito sopra
        resolved_entities.append(_entity_to_resolved(e))

    # 7. Missing fields
    missing = get_missing_fields(top_intent.intent, entities)

    # 8. Assemble response
    if operations:
        n_ops = len(operations)
        message = f"{n_ops} operazione riconosciuta." if n_ops == 1 else f"{n_ops} operazioni riconosciute."
        if ambiguities:
            message += " Risolvi le ambiguita' prima di confermare."
    elif missing:
        labels = {"date": "data", "time": "orario", "amount": "importo",
                  "tipo_movement": "tipo (entrata/uscita)", "metric_value": "misurazione"}
        missing_labels = [labels.get(m, m) for m in missing]
        message = f"Mancano: {', '.join(missing_labels)}."
    else:
        message = "Non sono riuscito a interpretare il comando."

    return ParseResponse(
        success=bool(operations),
        operations=operations,
        ambiguities=ambiguities,
        entities=resolved_entities,
        message=message,
        raw_text=text,
    )


# ═══════════════════════════════════════════════════════════════
# Payload builders
# ═══════════════════════════════════════════════════════════════


def _build_payload(
    intent: str,
    entities: list[ExtractedEntity],
    client_id: Optional[int],
    client_name: Optional[str],
) -> Optional[dict[str, Any]]:
    """Costruisce il payload per il commit in base all'intent."""
    if intent == "agenda.create_event":
        return _build_event_payload(entities, client_id, client_name)
    if intent == "movement.create_manual":
        return _build_movement_payload(entities)
    if intent == "measurement.create":
        return _build_measurement_payload(entities, client_id)
    return None


def _build_event_payload(
    entities: list[ExtractedEntity],
    client_id: Optional[int],
    client_name: Optional[str],
) -> Optional[dict[str, Any]]:
    """Payload per agenda.create_event."""
    date_entity = get_first_entity(entities, "date")
    time_entity = get_first_entity(entities, "time")
    cat_entity = get_first_entity(entities, "category_event")

    # Data: obbligatoria
    event_date = date_entity.value if date_entity else date.today()
    event_time = time_entity.value if time_entity else None

    if event_time is None:
        return None  # Senza orario non possiamo creare un evento

    # Combina data + ora
    dt_start = datetime.combine(event_date, event_time)
    dt_end = dt_start + timedelta(hours=1)  # Default 1h

    # Categoria
    categoria = cat_entity.value if cat_entity else "PT"

    # Titolo auto-generato
    if client_name and categoria == "PT":
        titolo = f"PT {client_name}"
    else:
        titolo = categoria

    payload: dict[str, Any] = {
        "data_inizio": dt_start.isoformat(),
        "data_fine": dt_end.isoformat(),
        "categoria": categoria,
        "titolo": titolo,
        "stato": "Programmato",
    }

    if client_id:
        payload["id_cliente"] = client_id

    return payload


def _build_movement_payload(
    entities: list[ExtractedEntity],
) -> Optional[dict[str, Any]]:
    """Payload per movement.create_manual."""
    amount_entity = get_first_entity(entities, "amount")
    tipo_entity = get_first_entity(entities, "tipo_movement")
    method_entity = get_first_entity(entities, "method_payment")
    cat_entity = get_first_entity(entities, "category_text")
    date_entity = get_first_entity(entities, "date")

    if not amount_entity:
        return None

    # Tipo: inferito da trigger, default USCITA
    tipo = tipo_entity.value if tipo_entity else "USCITA"

    payload: dict[str, Any] = {
        "importo": amount_entity.value,
        "tipo": tipo,
        "data_effettiva": (date_entity.value if date_entity else date.today()).isoformat(),
    }

    if method_entity:
        payload["metodo"] = method_entity.value

    if cat_entity:
        payload["categoria"] = cat_entity.value

    return payload


def _build_measurement_payload(
    entities: list[ExtractedEntity],
    client_id: Optional[int],
) -> Optional[dict[str, Any]]:
    """Payload per measurement.create."""
    metric_entities = get_entities_by_type(entities, "metric_value")
    date_entity = get_first_entity(entities, "date")

    if not metric_entities or not client_id:
        return None

    valori = []
    for e in metric_entities:
        if isinstance(e.value, dict) and "id_metrica" in e.value:
            valori.append({
                "id_metrica": e.value["id_metrica"],
                "valore": e.value["valore"],
            })

    if not valori:
        return None

    return {
        "client_id": client_id,
        "data_misurazione": (
            date_entity.value if date_entity else date.today()
        ).isoformat(),
        "valori": valori,
    }


# ═══════════════════════════════════════════════════════════════
# Preview labels
# ═══════════════════════════════════════════════════════════════


def _build_preview_label(
    intent: str,
    payload: dict[str, Any],
    client_name: Optional[str],
) -> str:
    """Genera label leggibile per l'UI."""
    if intent == "agenda.create_event":
        cat = payload.get("categoria", "PT")
        dt = payload.get("data_inizio", "")
        try:
            dt_obj = datetime.fromisoformat(dt)
            dt_str = dt_obj.strftime("%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            dt_str = dt
        name_part = f" con {client_name}" if client_name else ""
        return f"{cat}{name_part} — {dt_str}"

    if intent == "movement.create_manual":
        tipo = payload.get("tipo", "USCITA")
        importo = payload.get("importo", 0)
        cat = payload.get("categoria", "")
        tipo_label = "Entrata" if tipo == "ENTRATA" else "Uscita"
        cat_part = f" — {cat}" if cat else ""
        return f"{tipo_label} €{importo:.2f}{cat_part}"

    if intent == "measurement.create":
        valori = payload.get("valori", [])
        parts = []
        from api.services.assistant_parser.entity_extractor import METRIC_SYNONYMS
        # Inverti mapping per ottenere nomi
        id_to_name: dict[int, str] = {}
        for name, mid in METRIC_SYNONYMS.items():
            if mid not in id_to_name or len(name) > len(id_to_name[mid]):
                id_to_name[mid] = name
        for v in valori:
            name = id_to_name.get(v["id_metrica"], f"metrica {v['id_metrica']}")
            parts.append(f"{name}: {v['valore']}")
        name_part = f"{client_name} — " if client_name else ""
        return f"Misurazione {name_part}{', '.join(parts)}"

    return f"Operazione {intent}"


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def _empty_response(text: str, message: str) -> ParseResponse:
    return ParseResponse(
        success=False,
        operations=[],
        ambiguities=[],
        entities=[],
        message=message,
        raw_text=text,
    )


def _build_client_ambiguity(raw: str, matches: list[ClientMatch]) -> AmbiguityItem:
    return AmbiguityItem(
        field="id_cliente",
        candidates=[
            ResolvedEntity(
                type="client",
                raw=raw,
                value=m.client.id,
                label=m.full_name,
                confidence=m.score,
            )
            for m in matches
        ],
        message="Quale cliente intendi?",
    )


def _entity_to_resolved(e: ExtractedEntity) -> ResolvedEntity:
    """Converte ExtractedEntity in ResolvedEntity per l'UI."""
    type_labels = {
        "date": "Data",
        "time": "Orario",
        "amount": "Importo",
        "category_event": "Categoria",
        "category_text": "Categoria",
        "method_payment": "Metodo",
        "tipo_movement": "Tipo",
        "metric_value": "Metrica",
    }
    label = type_labels.get(e.type, e.type)

    # Formatta il valore per display
    if e.type == "date" and isinstance(e.value, date):
        display = e.value.strftime("%d/%m/%Y")
    elif e.type == "time" and isinstance(e.value, time):
        display = e.value.strftime("%H:%M")
    elif e.type == "amount":
        display = f"€{e.value:.2f}"
    elif e.type == "metric_value" and isinstance(e.value, dict):
        display = f"{e.value.get('nome', '')}: {e.value.get('valore', '')}"
        label = str(e.value.get("nome", "Metrica")).capitalize()
    else:
        display = str(e.value)

    return ResolvedEntity(
        type=e.type,
        raw=e.raw,
        value=e.value if not isinstance(e.value, (date, time)) else str(e.value),
        label=f"{label}: {display}",
        confidence=1.0,
    )
