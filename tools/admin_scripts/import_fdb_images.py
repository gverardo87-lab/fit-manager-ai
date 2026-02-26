"""
Import immagini esecuzione da free-exercise-db per esercizi matchati.

Per ogni esercizio nostro matchato con FDB:
- Copia 0.jpg -> exec_start.jpg
- Copia 1.jpg -> exec_end.jpg
- Crea ExerciseMedia records con tag "fdb:exec_start" / "fdb:exec_end"

Eseguire dalla root:
  python -m tools.admin_scripts.import_fdb_images
  DATABASE_URL=sqlite:///data/crm_dev.db python -m tools.admin_scripts.import_fdb_images
"""

import json
import os
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from tools.admin_scripts.fdb_mapping import normalize_name, FDB_NAME_ALIASES

# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FDB_JSON = BASE_DIR / "tools" / "external" / "free-exercise-db" / "dist" / "exercises.json"
FDB_EXERCISES_DIR = BASE_DIR / "tools" / "external" / "free-exercise-db" / "exercises"
MEDIA_DIR = BASE_DIR / "data" / "media" / "exercises"

DB_URL = os.environ.get("DATABASE_URL", "")
DB_PATH = DB_URL.replace("sqlite:///", "") if DB_URL else str(BASE_DIR / "data" / "crm_dev.db")


def get_fdb_image_dir(fdb_exercise: dict) -> Path:
    """Trova la directory immagini FDB per un esercizio."""
    # Le immagini sono in exercises/{id}/ dove id e' il campo id del JSON
    fdb_id = fdb_exercise.get("id", "")
    img_dir = FDB_EXERCISES_DIR / fdb_id
    if img_dir.is_dir():
        return img_dir

    # Fallback: prova dal percorso immagini nel JSON
    images = fdb_exercise.get("images", [])
    if images:
        # images[0] = "ExerciseName/0.jpg"
        folder = images[0].split("/")[0]
        alt_dir = FDB_EXERCISES_DIR / folder
        if alt_dir.is_dir():
            return alt_dir

    return img_dir  # ritorna comunque, verra' gestito come missing


def main():
    print("=" * 60)
    print("FDB Image Import - Matched Exercises")
    print(f"DB: {DB_PATH}")
    print("=" * 60)

    # Carica FDB
    with open(FDB_JSON) as f:
        fdb_exercises = json.load(f)
    print(f"FDB: {len(fdb_exercises)} esercizi")

    # Costruisci FDB lookup
    fdb_by_norm: dict[str, dict] = {}
    fdb_by_name: dict[str, dict] = {}
    for fdb in fdb_exercises:
        fdb_by_norm[normalize_name(fdb["name"])] = fdb
        fdb_by_name[fdb["name"]] = fdb

    # Carica nostri esercizi
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, nome, nome_en FROM esercizi WHERE is_builtin = 1 AND deleted_at IS NULL"
    ).fetchall()
    print(f"DB:  {len(rows)} esercizi builtin\n")

    # Match e import
    imported = 0
    skipped = 0
    errors = 0
    no_images = 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    for our_id, our_nome, our_nome_en in rows:
        if not our_nome_en:
            continue

        # Trova match FDB
        fdb = None
        norm = normalize_name(our_nome_en)
        if norm in fdb_by_norm:
            fdb = fdb_by_norm[norm]
        else:
            # Prova alias inverso: cerchiamo in FDB_NAME_ALIASES quale FDB name punta al nostro nome_en
            for fdb_name, our_target in FDB_NAME_ALIASES.items():
                if our_target == our_nome_en:
                    fdb = fdb_by_name.get(fdb_name)
                    break

        if not fdb:
            continue  # non matchato

        # Controlla se gia' importato (idempotenza)
        existing = conn.execute(
            "SELECT id FROM esercizi_media WHERE exercise_id = ? AND descrizione = 'fdb:exec_start'",
            (our_id,)
        ).fetchone()
        if existing:
            skipped += 1
            continue

        # Trova directory immagini
        img_dir = get_fdb_image_dir(fdb)
        start_src = img_dir / "0.jpg"
        end_src = img_dir / "1.jpg"

        if not start_src.exists():
            no_images += 1
            continue

        # Crea directory destinazione
        dest_dir = MEDIA_DIR / str(our_id)
        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Copia immagini
            start_dest = dest_dir / "exec_start.jpg"
            shutil.copy2(start_src, start_dest)

            has_end = end_src.exists()
            if has_end:
                end_dest = dest_dir / "exec_end.jpg"
                shutil.copy2(end_src, end_dest)

            # Inserisci ExerciseMedia records
            conn.execute(
                """INSERT INTO esercizi_media (exercise_id, trainer_id, tipo, url, ordine, descrizione, created_at)
                   VALUES (?, NULL, 'image', ?, 0, 'fdb:exec_start', ?)""",
                (our_id, f"/media/exercises/{our_id}/exec_start.jpg", now)
            )

            if has_end:
                conn.execute(
                    """INSERT INTO esercizi_media (exercise_id, trainer_id, tipo, url, ordine, descrizione, created_at)
                       VALUES (?, NULL, 'image', ?, 1, 'fdb:exec_end', ?)""",
                    (our_id, f"/media/exercises/{our_id}/exec_end.jpg", now)
                )

            imported += 1
        except Exception as e:
            errors += 1
            print(f"  ERROR [{our_id}] {our_nome_en}: {e}")

    conn.commit()
    conn.close()

    print(f"Imported:   {imported}")
    print(f"Skipped:    {skipped} (gia' presenti)")
    print(f"No images:  {no_images}")
    print(f"Errors:     {errors}")
    print("Done.")


if __name__ == "__main__":
    main()
