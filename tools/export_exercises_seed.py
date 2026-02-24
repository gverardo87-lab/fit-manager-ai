#!/usr/bin/env python3
"""
Script one-time: esporta i 174 esercizi builtin da core/exercise_archive.py
in un JSON compatibile con il seed dell'API (api/seed_exercises.py).

Uso:
    python tools/export_exercises_seed.py

Output:
    data/exercises/seed_exercises.json
"""

import json
import sys
from pathlib import Path

# Root del progetto nel path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.exercise_archive import _get_seed_exercises


def main():
    raw = _get_seed_exercises()
    exercises = []

    for ex in raw:
        exercises.append({
            "nome": ex.get("it") or ex["name"],
            "nome_en": ex["name"],
            "categoria": ex["cat"],
            "pattern_movimento": ex["pat"],
            "muscoli_primari": ex["pm"],
            "muscoli_secondari": ex.get("sm", []),
            "attrezzatura": ex["eq"],
            "difficolta": ex["diff"],
            "rep_range_forza": ex.get("str"),
            "rep_range_ipertrofia": ex.get("hyp"),
            "rep_range_resistenza": ex.get("end"),
            "ore_recupero": ex.get("rec", 48),
            "istruzioni": ex.get("instr"),
            "controindicazioni": ex.get("contra", []),
        })

    output_path = ROOT / "data" / "exercises" / "seed_exercises.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(exercises, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(exercises)} exercises to {output_path}")


if __name__ == "__main__":
    main()
