"""
Import nuovi esercizi da free-exercise-db non matchati con i nostri 345.

Per ogni esercizio FDB senza match:
- Traduce nome via Ollama (gemma2:9b)
- Mappa muscoli, categoria, attrezzatura, difficolta, pattern_movimento
- Inserisce esercizio + copia immagini + ExerciseMedia records

Eseguire dalla root:
  python -m tools.admin_scripts.import_fdb_new_exercises
  DATABASE_URL=sqlite:///data/crm.db python -m tools.admin_scripts.import_fdb_new_exercises
"""

import json
import os
import shutil
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from tools.admin_scripts.fdb_mapping import (
    FDB_NAME_ALIASES,
    infer_pattern,
    map_category,
    map_difficulty,
    map_equipment,
    map_muscles,
    normalize_name,
)

# ================================================================
# CONFIG
# ================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FDB_JSON = BASE_DIR / "tools" / "external" / "free-exercise-db" / "dist" / "exercises.json"
FDB_EXERCISES_DIR = BASE_DIR / "tools" / "external" / "free-exercise-db" / "exercises"
MEDIA_DIR = BASE_DIR / "data" / "media" / "exercises"

DB_URL = os.environ.get("DATABASE_URL", "")
DB_PATH = DB_URL.replace("sqlite:///", "") if DB_URL else str(BASE_DIR / "data" / "crm_dev.db")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma2:9b"
OLLAMA_TIMEOUT = 30

# Force type mapping
FDB_FORCE_MAP = {
    "push": "push",
    "pull": "pull",
    "static": "static",
}

# Mechanic -> lateral_pattern hint
FDB_MECHANIC_MAP = {
    "compound": "bilateral",
    "isolation": "bilateral",
}


def translate_name(name_en: str) -> str:
    """Traduci nome esercizio via Ollama. Fallback: nome originale."""
    prompt = (
        f"Traduci il nome di questo esercizio fitness in italiano. "
        f"Rispondi SOLO con il nome tradotto, senza spiegazioni.\n\n"
        f"Esercizio: {name_en}"
    )
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=OLLAMA_TIMEOUT,
        )
        if resp.status_code == 200:
            result = resp.json().get("response", "").strip()
            # Pulisci risposte troppo lunghe o con spiegazioni
            lines = result.split("\n")
            first_line = lines[0].strip().strip('"').strip("'").strip("*").strip()
            if first_line and len(first_line) < 100:
                return first_line
    except Exception:
        pass
    return name_en  # fallback


def infer_lateral_pattern(fdb_exercise: dict) -> str:
    """Inferisci lateral_pattern dal nome esercizio."""
    name_lower = fdb_exercise.get("name", "").lower()
    unilateral_keywords = [
        "one-arm", "one arm", "single-arm", "single arm",
        "one-leg", "one leg", "single-leg", "single leg",
        "unilateral", "pistol",
    ]
    alternating_keywords = [
        "alternating", "alternate",
    ]
    if any(kw in name_lower for kw in alternating_keywords):
        return "alternating"
    if any(kw in name_lower for kw in unilateral_keywords):
        return "unilateral"
    return "bilateral"


def get_fdb_image_dir(fdb_exercise: dict) -> Path:
    """Trova la directory immagini FDB per un esercizio."""
    fdb_id = fdb_exercise.get("id", "")
    img_dir = FDB_EXERCISES_DIR / fdb_id
    if img_dir.is_dir():
        return img_dir

    images = fdb_exercise.get("images", [])
    if images:
        folder = images[0].split("/")[0]
        alt_dir = FDB_EXERCISES_DIR / folder
        if alt_dir.is_dir():
            return alt_dir

    return img_dir


def main():
    print("=" * 60)
    print("FDB New Exercise Import")
    print(f"DB: {DB_PATH}")
    print("=" * 60)

    # Carica FDB
    with open(FDB_JSON) as f:
        fdb_exercises = json.load(f)
    print(f"FDB: {len(fdb_exercises)} esercizi")

    # Costruisci lookup per match
    fdb_by_norm: dict[str, dict] = {}
    fdb_by_name: dict[str, dict] = {}
    for fdb in fdb_exercises:
        fdb_by_norm[normalize_name(fdb["name"])] = fdb
        fdb_by_name[fdb["name"]] = fdb

    # Carica nostri esercizi per match check
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, nome, nome_en FROM esercizi WHERE is_builtin = 1 AND deleted_at IS NULL"
    ).fetchall()
    print(f"DB:  {len(rows)} esercizi builtin")

    our_by_norm: dict[str, int] = {}
    our_by_nome_en: dict[str, int] = {}
    for row_id, nome, nome_en in rows:
        if nome_en:
            our_by_norm[normalize_name(nome_en)] = row_id
            our_by_nome_en[nome_en.lower()] = row_id

    # Filtra solo non-matchati
    unmatched: list[dict] = []
    for fdb in fdb_exercises:
        norm = normalize_name(fdb["name"])
        if norm in our_by_norm:
            continue
        alias_target = FDB_NAME_ALIASES.get(fdb["name"])
        if alias_target and alias_target.lower() in our_by_nome_en:
            continue
        # Check idempotenza: se nome_en esiste gia' (da precedente import)
        if fdb["name"].lower() in our_by_nome_en:
            continue
        unmatched.append(fdb)

    print(f"Nuovi da importare: {len(unmatched)}\n")

    if not unmatched:
        print("Nessun nuovo esercizio da importare.")
        return

    # Test connessione Ollama
    ollama_ok = False
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        ollama_ok = resp.status_code == 200
    except Exception:
        pass

    if ollama_ok:
        print("Ollama: ATTIVO (traduzione nomi IT)")
    else:
        print("Ollama: NON DISPONIBILE (nomi inglesi come fallback)")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    imported = 0
    errors = 0
    translate_count = 0

    for i, fdb in enumerate(unmatched):
        nome_en = fdb["name"]

        # Traduci nome
        if ollama_ok:
            nome_it = translate_name(nome_en)
            if nome_it != nome_en:
                translate_count += 1
        else:
            nome_it = nome_en

        # Mappa campi
        muscoli_primari = map_muscles(fdb.get("primaryMuscles", []))
        muscoli_secondari = map_muscles(fdb.get("secondaryMuscles", []))
        categoria = map_category(fdb)
        attrezzatura = map_equipment(fdb)
        difficolta = map_difficulty(fdb)
        pattern = infer_pattern(fdb)
        force_type = FDB_FORCE_MAP.get(fdb.get("force"), None)
        lateral = infer_lateral_pattern(fdb)

        # Istruzioni -> esecuzione
        instructions = fdb.get("instructions", [])
        esecuzione = "\n".join(instructions) if instructions else None

        # Fallback muscoli vuoti
        if not muscoli_primari:
            muscoli_primari = ["core"]

        try:
            # INSERT esercizio
            cursor = conn.execute(
                """INSERT INTO esercizi (
                    trainer_id, nome, nome_en, categoria, pattern_movimento,
                    force_type, lateral_pattern,
                    muscoli_primari, muscoli_secondari,
                    attrezzatura, difficolta, ore_recupero,
                    esecuzione,
                    is_builtin, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (
                    None,  # trainer_id
                    nome_it,
                    nome_en,
                    categoria,
                    pattern,
                    force_type,
                    lateral,
                    json.dumps(muscoli_primari, ensure_ascii=False),
                    json.dumps(muscoli_secondari, ensure_ascii=False),
                    attrezzatura,
                    difficolta,
                    48,  # ore_recupero default
                    esecuzione,
                    now,
                ),
            )
            new_id = cursor.lastrowid

            # Copia immagini
            img_dir = get_fdb_image_dir(fdb)
            start_src = img_dir / "0.jpg"
            end_src = img_dir / "1.jpg"

            if start_src.exists():
                dest_dir = MEDIA_DIR / str(new_id)
                dest_dir.mkdir(parents=True, exist_ok=True)

                start_dest = dest_dir / "exec_start.jpg"
                shutil.copy2(start_src, start_dest)

                conn.execute(
                    """INSERT INTO esercizi_media (exercise_id, trainer_id, tipo, url, ordine, descrizione, created_at)
                       VALUES (?, NULL, 'image', ?, 0, 'fdb:exec_start', ?)""",
                    (new_id, f"/media/exercises/{new_id}/exec_start.jpg", now),
                )

                if end_src.exists():
                    end_dest = dest_dir / "exec_end.jpg"
                    shutil.copy2(end_src, end_dest)

                    conn.execute(
                        """INSERT INTO esercizi_media (exercise_id, trainer_id, tipo, url, ordine, descrizione, created_at)
                           VALUES (?, NULL, 'image', ?, 1, 'fdb:exec_end', ?)""",
                        (new_id, f"/media/exercises/{new_id}/exec_end.jpg", now),
                    )

            imported += 1

            # Progress ogni 50
            if (i + 1) % 50 == 0:
                conn.commit()
                print(f"  Progress: {i + 1}/{len(unmatched)} ({imported} importati)")

        except Exception as e:
            errors += 1
            print(f"  ERROR [{nome_en}]: {e}")

    conn.commit()
    conn.close()

    print(f"\n{'=' * 60}")
    print(f"Imported:    {imported}")
    print(f"Translated:  {translate_count} nomi")
    print(f"Errors:      {errors}")
    print(f"{'=' * 60}")
    print("Done.")


if __name__ == "__main__":
    main()
