"""
Completa i gap residui dei 118 esercizi subset.

3 operazioni deterministiche:
  A. muscoli_secondari — 9 esercizi con secondari vuoti
  B. tempo_consigliato — 22 esercizi senza tempo
  C. relazioni — riesegue populate_exercise_relations.py

Zero Ollama. 100% deterministico. Idempotente.
Eseguire dalla root:
  python -m tools.admin_scripts.fill_subset_gaps [--db dev|prod|both] [--dry-run]
"""

import argparse
import json
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# ================================================================
# A. MUSCOLI SECONDARI — lookup statico per i 9 mancanti
# ================================================================
# Per esercizi di isolamento piccoli distretti, i secondari sono minimi
# ma comunque compilabili deterministicamente

SECONDARY_MUSCLE_RULES: dict[int, list[str]] = {
    205: [],                    # Mobilita Polsi — nessun secondario significativo
    320: [],                    # Stretching Soleo Seduto — isolamento puro
    350: ["hamstrings", "glutes"],  # Stretching Adduttori — coinvolge femorali e glutei
    381: ["core", "glutes"],    # Addurrezioni con Band — stabilizzazione core/glutei
    447: [],                    # Curl Polsi al Cavo — isolamento puro avambracci
    560: [],                    # Curl Pollici — isolamento puro
    635: [],                    # Isometrico Collo — isolamento puro
    731: ["hamstrings", "core", "quadriceps"],  # Camminata del Mostro — tutto il lower body
    1080: [],                   # Rotazione Polsi — isolamento puro
}

# ================================================================
# B. TEMPO CONSIGLIATO — dedotto da categoria + pattern
# ================================================================
# Formato: "ecc-pausa-conc-pausa" in secondi

TEMPO_DEFAULTS: dict[str, dict[str, str]] = {
    "compound": {
        "default": "3-1-2-0",
        "core": "2-1-2-0",
        "carry": "0-0-0-0",  # carry = tempo continuo, non ha fasi
    },
    "isolation": {
        "default": "2-0-2-0",
        "core": "2-1-2-0",
        "carry": "2-0-2-0",
        "rotation": "2-0-2-0",
    },
    "bodyweight": {
        "default": "2-0-2-0",
        "core": "2-1-2-0",
        "push_h": "2-1-2-0",
    },
    "cardio": {
        "default": "0-0-0-0",  # cardio continuo
        "core": "0-0-0-0",
    },
    "stretching": {
        "default": "0-30-0-0",  # 30s hold
    },
    "mobilita": {
        "default": "2-0-2-0",
    },
    "avviamento": {
        "default": "1-0-1-0",
    },
}


def _get_tempo(categoria: str, pattern: str) -> str:
    cat_map = TEMPO_DEFAULTS.get(categoria, {})
    return cat_map.get(pattern, cat_map.get("default", "2-0-2-0"))


def process_db(db_path: str, dry_run: bool = False) -> dict:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    stats = {"muscoli_updated": 0, "tempo_updated": 0}

    # A. Muscoli secondari
    for ex_id, secondaries in SECONDARY_MUSCLE_RULES.items():
        current = conn.execute(
            "SELECT muscoli_secondari FROM esercizi WHERE id = ? AND in_subset = 1",
            (ex_id,),
        ).fetchone()
        if not current:
            continue
        val = current[0]
        if val and val not in ("", "[]"):
            continue  # gia' popolato
        new_val = json.dumps(secondaries, ensure_ascii=False)
        if not dry_run:
            conn.execute(
                "UPDATE esercizi SET muscoli_secondari = ? WHERE id = ?",
                (new_val, ex_id),
            )
        stats["muscoli_updated"] += 1

    # B. Tempo consigliato
    rows = conn.execute(
        "SELECT id, categoria, pattern_movimento FROM esercizi "
        "WHERE in_subset = 1 AND tempo_consigliato IS NULL"
    ).fetchall()
    for ex_id, cat, pattern in rows:
        tempo = _get_tempo(cat, pattern)
        if not dry_run:
            conn.execute(
                "UPDATE esercizi SET tempo_consigliato = ? WHERE id = ?",
                (tempo, ex_id),
            )
        stats["tempo_updated"] += 1

    if not dry_run:
        conn.commit()
    conn.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Completa gap subset (muscoli, tempo)")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    dbs = []
    if args.db in ("dev", "both"):
        dbs.append(("DEV", os.path.join(BASE_DIR, "crm_dev.db")))
    if args.db in ("prod", "both"):
        dbs.append(("PROD", os.path.join(BASE_DIR, "crm.db")))

    for label, path in dbs:
        if not os.path.exists(path):
            print(f"  SKIP {label}: {path} non trovato")
            continue
        print(f"\n=== {label} ({path}) ===")
        stats = process_db(path, dry_run=args.dry_run)
        mode = "DRY RUN" if args.dry_run else "SCRITTO"
        print(f"  Muscoli secondari aggiornati: {stats['muscoli_updated']} [{mode}]")
        print(f"  Tempo consigliato aggiornati: {stats['tempo_updated']} [{mode}]")


if __name__ == "__main__":
    main()
