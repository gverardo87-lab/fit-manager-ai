# api/services/safety_engine.py
"""
Exercise Safety Engine — fonte di verita' unica.

Incrocia anamnesi cliente con esercizi_condizioni per produrre
una safety map per-esercizio. Deterministico, zero Ollama.

Flusso:
  1. extract_client_conditions(anamnesi_json) → set[condition_id]
  2. build_safety_map(session, client_id, trainer_id) → SafetyMapResponse
"""

import json
import logging
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from api.models.client import Client
from api.models.exercise import Exercise
from api.models.medical_condition import ExerciseCondition, MedicalCondition
from api.schemas.safety import (
    ExerciseSafetyEntry,
    SafetyConditionDetail,
    SafetyMapResponse,
)
from api.services.condition_rules import (
    ANAMNESI_KEYWORD_RULES,
    STRUCTURAL_FLAGS,
    match_keywords,
)

logger = logging.getLogger(__name__)

# Campi AnamnesiData con struttura {presente: bool, dettaglio: str|null}
_QUESTION_FIELDS = [
    "infortuni_attuali",
    "infortuni_pregressi",
    "interventi_chirurgici",
    "dolori_cronici",
    "patologie",
    "farmaci",
    "problemi_cardiovascolari",
    "problemi_respiratori",
    "dieta_particolare",
]

# Campi AnamnesiData con testo libero (str|null)
# NOTA: obiettivi_specifici ESCLUSO — contiene goal ("migliorare spalle"),
# non condizioni mediche. Includerlo causa falsi positivi.
_FREE_TEXT_FIELDS = [
    "limitazioni_funzionali",
    "note",
]


def extract_client_conditions(anamnesi_json: Optional[str]) -> set[int]:
    """
    Estrae condition_id rilevanti dall'anamnesi di un cliente.

    2 livelli:
      1. Flag strutturali (campo .presente == true → condition IDs diretti)
      2. Keyword matching su tutti i testi liberi (.dettaglio + limitazioni + note)

    Returns: set di condition_id dalla tabella condizioni_mediche.
    """
    if not anamnesi_json:
        return set()

    try:
        anamnesi = json.loads(anamnesi_json)
    except (json.JSONDecodeError, TypeError):
        return set()

    if not isinstance(anamnesi, dict):
        return set()

    condition_ids: set[int] = set()

    # ── Livello 1: Flag strutturali ──
    for field_name, cond_ids in STRUCTURAL_FLAGS.items():
        field_data = anamnesi.get(field_name)
        if isinstance(field_data, dict) and field_data.get("presente"):
            condition_ids.update(cond_ids)

    # ── Livello 2: Keyword matching su testi liberi ──
    all_texts: list[str] = []

    # Testi dai campi question (.dettaglio)
    for field_name in _QUESTION_FIELDS:
        field_data = anamnesi.get(field_name)
        if isinstance(field_data, dict):
            dettaglio = field_data.get("dettaglio")
            if dettaglio and isinstance(dettaglio, str):
                all_texts.append(dettaglio)

    # Testi dai campi liberi
    for field_name in _FREE_TEXT_FIELDS:
        value = anamnesi.get(field_name)
        if value and isinstance(value, str):
            all_texts.append(value)

    # Matching
    full_text = " ".join(all_texts)
    if full_text.strip():
        for keywords, cond_id in ANAMNESI_KEYWORD_RULES:
            if match_keywords(full_text, keywords):
                condition_ids.add(cond_id)

    return condition_ids


def build_safety_map(
    session: Session,
    client_id: int,
    trainer_id: int,
) -> SafetyMapResponse:
    """
    Costruisce la safety map per un cliente specifico.

    Bouncer: client.trainer_id == trainer_id → 404.
    Anti-N+1: 3 query (client, conditions, exercise-conditions).
    """
    # ── Bouncer ──
    client = session.get(Client, client_id)
    if not client or client.trainer_id != trainer_id or client.deleted_at is not None:
        raise HTTPException(404, "Cliente non trovato")

    client_nome = f"{client.nome} {client.cognome}"

    # ── Estrai condizioni dal JSON anamnesi ──
    condition_ids = extract_client_conditions(client.anamnesi_json)

    if not condition_ids:
        return SafetyMapResponse(
            client_id=client_id,
            client_nome=client_nome,
            has_anamnesi=client.anamnesi_json is not None,
            condition_count=0,
            condition_names=[],
            entries={},
        )

    # ── Query: nomi condizioni per overview panel ──
    cond_stmt = select(MedicalCondition).where(MedicalCondition.id.in_(condition_ids))
    conditions_list = session.exec(cond_stmt).all()
    condition_names = sorted([c.nome for c in conditions_list])

    # ── Query: exercise-condition mappings per condizioni rilevanti ──
    # Solo esercizi attivi (in_subset=True)
    active_ids_stmt = select(Exercise.id).where(
        Exercise.in_subset == True,
        Exercise.deleted_at == None,
    )

    stmt = (
        select(ExerciseCondition, MedicalCondition)
        .join(MedicalCondition, ExerciseCondition.id_condizione == MedicalCondition.id)
        .where(
            ExerciseCondition.id_condizione.in_(condition_ids),
            ExerciseCondition.id_esercizio.in_(active_ids_stmt),
        )
    )
    rows = session.exec(stmt).all()

    # ── Aggregazione per exercise_id ──
    entries: dict[int, ExerciseSafetyEntry] = {}

    for ec, mc in rows:
        ex_id = ec.id_esercizio
        # Parse body_tags JSON
        try:
            tags = json.loads(mc.body_tags) if mc.body_tags else []
        except (json.JSONDecodeError, TypeError):
            tags = []

        detail = SafetyConditionDetail(
            id=mc.id,
            nome=mc.nome,
            severita=ec.severita,
            nota=ec.nota,
            categoria=mc.categoria,
            body_tags=tags,
        )

        if ex_id not in entries:
            entries[ex_id] = ExerciseSafetyEntry(
                exercise_id=ex_id,
                severity=ec.severita,
                conditions=[detail],
            )
        else:
            entry = entries[ex_id]
            entry.conditions.append(detail)
            # Worst-case: avoid > caution > modify
            if ec.severita == "avoid":
                entry.severity = "avoid"

    return SafetyMapResponse(
        client_id=client_id,
        client_nome=client_nome,
        has_anamnesi=client.anamnesi_json is not None,
        condition_count=len(condition_ids),
        condition_names=condition_names,
        entries=entries,
    )
