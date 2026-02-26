"""
Fase 2A: Traduzione istruzioni FDB EN→IT.

Traduce le istruzioni step-by-step degli esercizi FDB dall'inglese all'italiano,
preservando la struttura dettagliata e cumulativa del formato originale.

NON riassume, NON abbrevia, NON rigenera. Solo traduzione fedele.

Idempotente: salta esercizi gia' tradotti (check lingua).
Eseguire dalla root:
  python -m tools.admin_scripts.translate_fdb_instructions [--db dev|prod|both] [--resume] [--batch N]
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone

import requests

# ================================================================
# CONFIG
# ================================================================

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma2:9b"
OLLAMA_TIMEOUT = 120  # Longer timeout for instruction translation
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

# English words that indicate untranslated content
EN_MARKERS = [
    "your", "the", "and", "with", "this", "will", "should",
    "begin", "repeat", "position", "slowly", "back",
    "starting position", "return to",
]

# ================================================================
# TRANSLATION PROMPT
# ================================================================

SYSTEM_PROMPT = """Sei un traduttore esperto di istruzioni per esercizi fitness.
Traduci dall'inglese all'italiano MANTENENDO ESATTAMENTE la struttura step-by-step.

REGOLE TASSATIVE:
1. Traduci OGNI frase preservando TUTTI i dettagli tecnici
2. NON riassumere, NON abbreviare, NON omettere passi
3. Mantieni la stessa quantita' di passi/paragrafi dell'originale
4. Usa l'imperativo (es. "Afferra", "Posiziona", "Spingi")
5. Terminologia fitness italiana:
   - Barbell = bilanciere
   - Dumbbell = manubrio
   - Kettlebell = kettlebell (invariato)
   - Rep/Repetition = ripetizione
   - Set = serie
   - Starting position = posizione iniziale
   - Range of motion = escursione articolare
   - Grip = presa/impugnatura
   - Supinated grip = presa supina
   - Pronated grip = presa prona
   - Overhand grip = presa prona
   - Underhand grip = presa supina
   - Core = core (invariato)
   - Squeeze = contrai/spremi
   - Lock out = estendi completamente
   - Exhale = espira
   - Inhale = inspira
6. Rispondi SOLO con la traduzione, nessun commento o nota aggiuntiva"""


def is_already_italian(text: str) -> bool:
    """Check if text is already in Italian (heuristic)."""
    if not text:
        return False
    # Count English markers vs Italian markers
    text_lower = text.lower()
    en_count = sum(1 for marker in EN_MARKERS if marker in text_lower)
    # If more than 3 English markers, it's still English
    return en_count < 3


def translate_instructions(esecuzione_en: str) -> str | None:
    """Translate exercise instructions from EN to IT via Ollama."""
    prompt = (
        "Traduci queste istruzioni di esercizio fitness dall'inglese all'italiano.\n"
        "Mantieni ESATTAMENTE la stessa struttura (ogni paragrafo = un passo).\n\n"
        f"{esecuzione_en}"
    )
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "system": SYSTEM_PROMPT,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 1024},
            },
            timeout=OLLAMA_TIMEOUT,
        )
        if resp.status_code == 200:
            result = resp.json().get("response", "").strip()
            # Remove any leading/trailing quotes or markdown
            result = result.strip('"').strip("'")
            if result.startswith("```"):
                result = re.sub(r"^```\w*\n?", "", result)
                result = re.sub(r"\n?```$", "", result)
            # Validate: should be at least 50% of original length
            if len(result) >= len(esecuzione_en) * 0.4:
                return result
    except Exception as e:
        print(f"      Ollama error: {e}")
    return None


# ================================================================
# EXECUTION
# ================================================================

def translate_db(db_path: str, batch_size: int = 0) -> tuple[int, int, int]:
    """Translate FDB instructions in a single database.
    Returns (translated, skipped_already_it, errors)."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return (0, 0, 0)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 60}")
    print(f"  Translating instructions: {db_name}")
    print(f"{'=' * 60}")

    # Load FDB exercises with English instructions
    exercises = conn.execute("""
        SELECT id, nome, nome_en, esecuzione FROM esercizi
        WHERE deleted_at IS NULL
          AND id > 345
          AND esecuzione IS NOT NULL
          AND esecuzione != ''
        ORDER BY id
    """).fetchall()

    print(f"  Total FDB with instructions: {len(exercises)}")

    translated = 0
    skipped = 0
    errors = 0

    for i, ex in enumerate(exercises):
        eid = ex["id"]
        esecuzione = ex["esecuzione"]

        # Skip if already Italian
        if is_already_italian(esecuzione):
            skipped += 1
            continue

        # Translate
        result = translate_instructions(esecuzione)
        if result:
            conn.execute(
                "UPDATE esercizi SET esecuzione = ? WHERE id = ?",
                (result, eid)
            )
            translated += 1

            # Commit every 10 exercises (atomic per small batch)
            if translated % 10 == 0:
                conn.commit()
        else:
            errors += 1
            print(f"    ERROR: id={eid} ({ex['nome_en']})")

        # Progress
        if (i + 1) % 25 == 0:
            print(f"    Progress: {i + 1}/{len(exercises)} "
                  f"(translated={translated}, skipped={skipped}, errors={errors})")

        # Batch limit
        if batch_size > 0 and translated >= batch_size:
            print(f"    Batch limit reached ({batch_size})")
            break

    conn.commit()
    conn.close()

    print(f"\n  Results ({db_name}):")
    print(f"    Translated: {translated}")
    print(f"    Already Italian: {skipped}")
    print(f"    Errors: {errors}")

    return (translated, skipped, errors)


def verify(db_path: str) -> None:
    """Post-translation verification."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    db_name = os.path.basename(db_path)

    print(f"\n  Verification: {db_name}")

    # Count FDB with Italian instructions
    total = conn.execute("""
        SELECT COUNT(*) FROM esercizi
        WHERE deleted_at IS NULL AND id > 345
          AND esecuzione IS NOT NULL AND esecuzione != ''
    """).fetchone()[0]

    still_en = 0
    rows = conn.execute("""
        SELECT id, esecuzione FROM esercizi
        WHERE deleted_at IS NULL AND id > 345
          AND esecuzione IS NOT NULL AND esecuzione != ''
    """).fetchall()

    for row in rows:
        if not is_already_italian(row[1]):
            still_en += 1

    print(f"    FDB with instructions: {total}")
    print(f"    Still in English: {still_en}")
    print(f"    In Italian: {total - still_en}")

    # Show a sample
    sample = conn.execute("""
        SELECT id, nome, SUBSTR(esecuzione, 1, 150) as preview FROM esercizi
        WHERE deleted_at IS NULL AND id > 345
          AND esecuzione IS NOT NULL AND esecuzione != ''
        ORDER BY RANDOM() LIMIT 3
    """).fetchall()
    print(f"    Sample translations:")
    for s in sample:
        print(f"      [{s[0]}] {s[1]}:")
        print(f"        {s[2]}...")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate FDB instructions EN→IT (Phase 2A)")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both",
                        help="Which database to process")
    parser.add_argument("--batch", type=int, default=0,
                        help="Limit number of translations per DB (0=unlimited)")
    args = parser.parse_args()

    print("FDB Instruction Translation — Phase 2A")
    print("=" * 60)

    dbs = []
    if args.db in ("dev", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if args.db in ("prod", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm.db"))

    total_translated = 0
    total_errors = 0
    for db_path in dbs:
        t, s, e = translate_db(db_path, batch_size=args.batch)
        total_translated += t
        total_errors += e

    print(f"\n{'=' * 60}")
    print("  POST-TRANSLATION VERIFICATION")
    print("=" * 60)

    for db_path in dbs:
        verify(db_path)

    print(f"\nTotal translated: {total_translated}, errors: {total_errors}")
    print("Done.")
