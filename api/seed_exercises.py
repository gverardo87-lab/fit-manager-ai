# api/seed_exercises.py
"""
Seed esercizi builtin + relazioni nel database.

Chiamato al startup dell'API (lifespan). Se la tabella esercizi contiene
gia' record builtin, il seed viene skippato (idempotente).

Legge da data/exercises/:
- seed_exercises.json — 311 esercizi attivi (in_subset=1) con ID preservati
- seed_exercise_relations.json — 426 relazioni (progressioni/regressioni/varianti)

Gli esercizi archiviati (~750) verranno reinseriti gradualmente via activate_batch.py.
"""

import json
import logging

from sqlmodel import Session, select, func

from api.config import DATA_DIR
from api.models.exercise import Exercise

logger = logging.getLogger("fitmanager.api")

SEED_FILE = DATA_DIR / "exercises" / "seed_exercises.json"


def seed_builtin_exercises(session: Session) -> int:
    """Inserisce esercizi builtin se la tabella e' vuota.

    Returns:
        Numero di esercizi inseriti (0 se gia' seedato).
    """
    count = session.exec(
        select(func.count(Exercise.id)).where(Exercise.is_builtin == True)  # noqa: E712
    ).one()

    if count > 0:
        logger.info(f"Seed esercizi: gia' presenti {count} builtin, skip")
        return 0

    if not SEED_FILE.exists():
        logger.warning(f"Seed esercizi: file non trovato {SEED_FILE}")
        return 0

    with open(SEED_FILE, "r", encoding="utf-8") as f:
        exercises_data = json.load(f)

    for ex in exercises_data:
        exercise = Exercise(
            id=ex.get("id"),  # preserva ID originali per FK relazioni
            trainer_id=None,
            nome=ex["nome"],
            nome_en=ex.get("nome_en"),
            categoria=ex["categoria"],
            pattern_movimento=ex["pattern_movimento"],
            muscoli_primari=json.dumps(ex["muscoli_primari"], ensure_ascii=False),
            muscoli_secondari=json.dumps(ex.get("muscoli_secondari", []), ensure_ascii=False),
            attrezzatura=ex["attrezzatura"],
            difficolta=ex["difficolta"],
            rep_range_forza=ex.get("rep_range_forza"),
            rep_range_ipertrofia=ex.get("rep_range_ipertrofia"),
            rep_range_resistenza=ex.get("rep_range_resistenza"),
            ore_recupero=ex.get("ore_recupero", 48),
            controindicazioni=json.dumps(ex.get("controindicazioni", []), ensure_ascii=False),
            is_builtin=True,
            # Campi v2: tassonomia e biomeccanica
            in_subset=ex.get("in_subset", False),
            catena_cinetica=ex.get("catena_cinetica"),
            piano_movimento=ex.get("piano_movimento"),
            tipo_contrazione=ex.get("tipo_contrazione"),
            note_sicurezza=ex.get("note_sicurezza"),
            tempo_consigliato=ex.get("tempo_consigliato"),
            force_type=ex.get("force_type"),
            lateral_pattern=ex.get("lateral_pattern"),
            descrizione_anatomica=ex.get("descrizione_anatomica"),
            descrizione_biomeccanica=ex.get("descrizione_biomeccanica"),
            setup=ex.get("setup"),
            esecuzione=ex.get("esecuzione"),
            respirazione=ex.get("respirazione"),
            coaching_cues=json.dumps(ex["coaching_cues"], ensure_ascii=False) if ex.get("coaching_cues") else None,
            errori_comuni=json.dumps(ex["errori_comuni"], ensure_ascii=False) if ex.get("errori_comuni") else None,
        )
        session.add(exercise)

    session.commit()
    inserted = len(exercises_data)
    logger.info(f"Seed esercizi: inseriti {inserted} builtin")
    return inserted


RELATIONS_SEED_FILE = DATA_DIR / "exercises" / "seed_exercise_relations.json"


def seed_exercise_relations(session: Session) -> int:
    """Inserisce relazioni (progressioni/regressioni/varianti) se la tabella e' vuota.

    Returns:
        Numero di relazioni inserite (0 se gia' seedate).
    """
    from api.models.exercise_relation import ExerciseRelation

    count = session.exec(
        select(func.count(ExerciseRelation.id))
    ).one()

    if count > 0:
        logger.info(f"Seed relazioni: gia' presenti {count}, skip")
        return 0

    if not RELATIONS_SEED_FILE.exists():
        logger.warning(f"Seed relazioni: file non trovato {RELATIONS_SEED_FILE}")
        return 0

    with open(RELATIONS_SEED_FILE, "r", encoding="utf-8") as f:
        relations_data = json.load(f)

    for rel in relations_data:
        relation = ExerciseRelation(
            exercise_id=rel["exercise_id"],
            related_exercise_id=rel["related_exercise_id"],
            tipo_relazione=rel["tipo_relazione"],
        )
        session.add(relation)

    session.commit()
    logger.info(f"Seed relazioni: inserite {len(relations_data)} relazioni")
    return len(relations_data)
