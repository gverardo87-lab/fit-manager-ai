# api/seed_exercises.py
"""
Seed 174 esercizi builtin nel database.

Chiamato al startup dell'API (lifespan). Se la tabella esercizi contiene
gia' record builtin, il seed viene skippato (idempotente).

Legge da data/exercises/seed_exercises.json (generato da tools/export_exercises_seed.py).
"""

import json
import logging
from pathlib import Path

from sqlmodel import Session, select, func

from api.models.exercise import Exercise

logger = logging.getLogger("fitmanager.api")

SEED_FILE = Path(__file__).resolve().parents[1] / "data" / "exercises" / "seed_exercises.json"


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
            istruzioni=json.dumps(ex["istruzioni"], ensure_ascii=False) if ex.get("istruzioni") else None,
            controindicazioni=json.dumps(ex.get("controindicazioni", []), ensure_ascii=False),
            is_builtin=True,
        )
        session.add(exercise)

    session.commit()
    inserted = len(exercises_data)
    logger.info(f"Seed esercizi: inseriti {inserted} esercizi builtin")
    return inserted
