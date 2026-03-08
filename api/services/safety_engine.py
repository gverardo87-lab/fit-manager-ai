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
    MedicationFlag,
    SafetyConditionDetail,
    SafetyMapResponse,
)
from api.services.condition_rules import (
    ANAMNESI_KEYWORD_RULES,
    MEDICATION_RULES,
    STRUCTURAL_FLAGS,
    match_keywords,
)

logger = logging.getLogger(__name__)

# Gerarchia severity: avoid > modify > caution
# "modify" prevale su "caution" perche' richiede azione specifica
# (adattare ROM, grip, carico), mentre "caution" e' solo consapevolezza.
_SEVERITY_ORDER = {"caution": 0, "modify": 1, "avoid": 2}

# Campi AnamnesiData con struttura {presente: bool, dettaglio: str|null}
# Include sia v2 (questionario Chiara) che v1 (backward compat).
# Se un campo non esiste nel JSON, .get() ritorna None → skippato.
_QUESTION_FIELDS = [
    # v2 (questionario Chiara)
    "infortuni_importanti",
    "patologie",
    "limitazioni_mediche",
    # v1 (backward compat — dati esistenti)
    "infortuni_attuali",
    "infortuni_pregressi",
    "interventi_chirurgici",
    "dolori_cronici",
    "farmaci",
    "problemi_cardiovascolari",
    "problemi_respiratori",
    "dieta_particolare",
]

# Campi AnamnesiData con testo libero (str|null)
# NOTA: obiettivi/goal ESCLUSI — contengono goal ("migliorare spalle"),
# non condizioni mediche. Includerli causa falsi positivi.
_FREE_TEXT_FIELDS = [
    # v2
    "dolori_attuali_altro",
    "patologie_altro",
    "farmaci_dettaglio",
    "note_finali",
    # v1 (backward compat)
    "limitazioni_funzionali",
    "note",
]

# Campi v2 che contengono liste di stringhe (es. ["schiena", "cervicale"]).
# Vengono uniti in testo per keyword matching.
_ARRAY_TEXT_FIELDS = [
    "dolori_attuali",
    "patologie_lista",
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

    # Testi dai campi array (v2: dolori_attuali, patologie_lista)
    for field_name in _ARRAY_TEXT_FIELDS:
        arr = anamnesi.get(field_name)
        if isinstance(arr, list):
            for item in arr:
                if isinstance(item, str) and item.strip():
                    all_texts.append(item)

    # Matching
    full_text = " ".join(all_texts)
    if full_text.strip():
        for keywords, cond_id in ANAMNESI_KEYWORD_RULES:
            if match_keywords(full_text, keywords):
                condition_ids.add(cond_id)

    return condition_ids


def extract_medication_flags(anamnesi_json: Optional[str]) -> list[MedicationFlag]:
    """
    Estrae flag farmacologici dall'anamnesi per informare il trainer.

    Scansiona il campo `farmaci.dettaglio` con keyword matching.
    Returns: lista di MedicationFlag (flag_name + nota clinica).
    """
    if not anamnesi_json:
        return []

    try:
        anamnesi = json.loads(anamnesi_json)
    except (json.JSONDecodeError, TypeError):
        return []

    if not isinstance(anamnesi, dict):
        return []

    # Estrai testo farmaci — v1: farmaci.dettaglio, v2: farmaci_dettaglio
    dettaglio = None

    # v1: campo farmaci con struttura {presente, dettaglio}
    farmaci_data = anamnesi.get("farmaci")
    if isinstance(farmaci_data, dict):
        d = farmaci_data.get("dettaglio")
        if d and isinstance(d, str):
            dettaglio = d

    # v2: campo farmaci_dettaglio (testo libero)
    if not dettaglio:
        d2 = anamnesi.get("farmaci_dettaglio")
        if d2 and isinstance(d2, str):
            dettaglio = d2

    if not dettaglio:
        return []

    flags: list[MedicationFlag] = []
    for keywords, flag_name, clinical_note in MEDICATION_RULES:
        if match_keywords(dettaglio, keywords):
            flags.append(MedicationFlag(flag=flag_name, nota=clinical_note))

    return flags


def build_safety_map(
    session: Session,
    catalog_session: Session,
    client_id: int,
    trainer_id: int,
) -> SafetyMapResponse:
    """
    Costruisce la safety map per un cliente specifico.

    Dual session: business (Client, Exercise) + catalog (MedicalCondition, ExerciseCondition).
    Bouncer: client.trainer_id == trainer_id → 404.
    Anti-N+1: 4 query (client, active_ids, conditions, exercise-conditions).
    """
    # ── Bouncer (business session) ──
    client = session.get(Client, client_id)
    if not client or client.trainer_id != trainer_id or client.deleted_at is not None:
        raise HTTPException(404, "Cliente non trovato")

    client_nome = f"{client.nome} {client.cognome}"

    # ── Estrai condizioni dal JSON anamnesi ──
    condition_ids = extract_client_conditions(client.anamnesi_json)

    # ── Estrai flag farmacologici ──
    medication_flags = extract_medication_flags(client.anamnesi_json)

    if not condition_ids:
        return SafetyMapResponse(
            client_id=client_id,
            client_nome=client_nome,
            has_anamnesi=client.anamnesi_json is not None,
            condition_count=0,
            condition_names=[],
            entries={},
            medication_flags=medication_flags,
        )

    # ── Query: nomi condizioni per overview panel (catalog) ──
    cond_stmt = select(MedicalCondition).where(MedicalCondition.id.in_(condition_ids))
    conditions_list = catalog_session.exec(cond_stmt).all()
    condition_names = sorted([c.nome for c in conditions_list])

    # ── Query: ID esercizi attivi (business — cross-DB split) ──
    active_ids = session.exec(
        select(Exercise.id).where(
            Exercise.in_subset == True,  # noqa: E712
            Exercise.deleted_at == None,  # noqa: E711
        )
    ).all()

    # ── Query: exercise-condition mappings (catalog) ──
    stmt = (
        select(ExerciseCondition, MedicalCondition)
        .join(MedicalCondition, ExerciseCondition.id_condizione == MedicalCondition.id)
        .where(
            ExerciseCondition.id_condizione.in_(condition_ids),
            ExerciseCondition.id_esercizio.in_(active_ids),
        )
    )
    rows = catalog_session.exec(stmt).all()

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
            # Worst-case severity: avoid > modify > caution
            if _SEVERITY_ORDER.get(ec.severita, 0) > _SEVERITY_ORDER.get(entry.severity, 0):
                entry.severity = ec.severita

    return SafetyMapResponse(
        client_id=client_id,
        client_nome=client_nome,
        has_anamnesi=client.anamnesi_json is not None,
        condition_count=len(condition_ids),
        condition_names=condition_names,
        entries=entries,
        medication_flags=medication_flags,
    )
