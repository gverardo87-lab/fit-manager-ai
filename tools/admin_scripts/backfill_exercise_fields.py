"""
Fase 4: Backfill note_sicurezza + force_type/lateral_pattern.

4A. note_sicurezza — genera per TUTTI gli esercizi (0% attuale)
    Campo critico per responsabilita' professionale.
    Ollama gemma2:9b, prompt focalizzato.

4B. force_type + lateral_pattern — inferenza deterministica per ~30 mancanti
    Zero Ollama, da pattern_movimento + nome.

Idempotente: salta campi gia' compilati.
Eseguire dalla root:
  python -m tools.admin_scripts.backfill_exercise_fields [--db dev|prod|both] [--batch N] [--only safety|force]
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time

import requests

# ================================================================
# CONFIG
# ================================================================

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma2:9b"
OLLAMA_TIMEOUT = 90

# ================================================================
# 4A. NOTE_SICUREZZA — Ollama generation
# ================================================================

SAFETY_SYSTEM = """Sei un preparatore atletico e fisioterapista con esperienza in prevenzione infortuni.
Genera note di sicurezza CONCISE per un esercizio fitness.

REGOLE:
- 1-3 frasi in ITALIANO
- Indica precauzioni SPECIFICHE per l'esercizio (non generiche)
- Menziona articolazioni a rischio, posture da mantenere, carichi
- Se l'esercizio coinvolge la schiena: menziona la posizione neutra
- Se coinvolge le ginocchia: menziona l'allineamento
- Se e' ad alta intensita': menziona il riscaldamento
- Rispondi SOLO con le note, nessun titolo o prefisso"""


def generate_safety_notes(
    nome: str,
    nome_en: str,
    categoria: str,
    muscoli_primari: str,
    attrezzatura: str,
) -> str | None:
    """Generate safety notes via Ollama."""
    prompt = (
        f"Genera note di sicurezza per questo esercizio:\n"
        f"Nome: {nome} ({nome_en})\n"
        f"Categoria: {categoria}\n"
        f"Muscoli: {muscoli_primari}\n"
        f"Attrezzatura: {attrezzatura}\n\n"
        f"Rispondi con 1-3 frasi di precauzioni specifiche."
    )
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "system": SAFETY_SYSTEM,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 200},
            },
            timeout=OLLAMA_TIMEOUT,
        )
        if resp.status_code == 200:
            result = resp.json().get("response", "").strip()
            result = result.strip('"').strip("'").strip("*")
            # Remove markdown headers
            result = re.sub(r"^#+\s*", "", result, flags=re.MULTILINE)
            result = re.sub(r"^\*\*[^*]+\*\*:?\s*", "", result, flags=re.MULTILINE)
            result = result.strip()
            if result and len(result) > 20:
                return result
    except Exception as e:
        print(f"      Ollama error: {e}")
    return None


def backfill_safety(db_path: str, batch_size: int = 0, subset_only: bool = False) -> tuple[int, int]:
    """Backfill note_sicurezza for exercises missing them."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return (0, 0)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n  [4A] Safety notes: {db_name}")

    query = """
        SELECT id, nome, nome_en, categoria, muscoli_primari, attrezzatura
        FROM esercizi
        WHERE deleted_at IS NULL
          AND (note_sicurezza IS NULL OR note_sicurezza = '')
    """
    if subset_only:
        query += "  AND in_subset = 1\n"
    query += "        ORDER BY id"
    exercises = conn.execute(query).fetchall()

    print(f"    To process: {len(exercises)}")

    filled = 0
    errors = 0

    for i, ex in enumerate(exercises):
        result = generate_safety_notes(
            ex["nome"], ex["nome_en"] or "",
            ex["categoria"], ex["muscoli_primari"] or "",
            ex["attrezzatura"] or "",
        )
        if result:
            conn.execute(
                "UPDATE esercizi SET note_sicurezza = ? WHERE id = ?",
                (result, ex["id"])
            )
            filled += 1
            if filled % 10 == 0:
                conn.commit()
        else:
            errors += 1

        if (i + 1) % 50 == 0:
            print(f"    Progress: {i + 1}/{len(exercises)} (filled={filled}, errors={errors})")

        if batch_size > 0 and filled >= batch_size:
            print(f"    Batch limit reached ({batch_size})")
            break

    conn.commit()
    conn.close()
    print(f"    Result: {filled} filled, {errors} errors")
    return (filled, errors)


# ================================================================
# 4B. FORCE_TYPE + LATERAL_PATTERN — Deterministic inference
# ================================================================

# Pattern → force_type mapping
PATTERN_FORCE = {
    "push_h": "push",
    "push_v": "push",
    "pull_h": "pull",
    "pull_v": "pull",
    "squat": "push",
    "hinge": "pull",
    "core": "static",
    "rotation": "pull",
    "carry": "static",
    "warmup": "static",
    "stretch": "static",
    "mobility": "static",
}

# Keywords for lateral pattern inference
UNILATERAL_KEYWORDS = [
    "singol", "single", "one-arm", "one arm", "un braccio",
    "una mano", "one-leg", "one leg", "una gamba", "monopodalic",
    "unilateral",
]
ALTERNATING_KEYWORDS = [
    "alternat", "alternate", "see-saw", "seesaw",
]


def infer_force_type(pattern: str, nome: str, nome_en: str) -> str | None:
    """Infer force_type from pattern_movimento."""
    if pattern in PATTERN_FORCE:
        return PATTERN_FORCE[pattern]
    return None


def infer_lateral_pattern(nome: str, nome_en: str) -> str:
    """Infer lateral_pattern from exercise name."""
    combined = f"{nome} {nome_en}".lower()
    for kw in ALTERNATING_KEYWORDS:
        if kw in combined:
            return "alternating"
    for kw in UNILATERAL_KEYWORDS:
        if kw in combined:
            return "unilateral"
    return "bilateral"


def backfill_force(db_path: str) -> int:
    """Backfill force_type and lateral_pattern deterministically."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return 0

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n  [4B] Force/lateral inference: {db_name}")

    # Force type
    exercises_ft = conn.execute("""
        SELECT id, nome, nome_en, pattern_movimento FROM esercizi
        WHERE deleted_at IS NULL AND (force_type IS NULL OR force_type = '')
        ORDER BY id
    """).fetchall()

    ft_fixed = 0
    for ex in exercises_ft:
        ft = infer_force_type(ex["pattern_movimento"] or "", ex["nome"], ex["nome_en"] or "")
        if ft:
            conn.execute("UPDATE esercizi SET force_type = ? WHERE id = ?", (ft, ex["id"]))
            ft_fixed += 1

    # Lateral pattern
    exercises_lp = conn.execute("""
        SELECT id, nome, nome_en FROM esercizi
        WHERE deleted_at IS NULL AND (lateral_pattern IS NULL OR lateral_pattern = '')
        ORDER BY id
    """).fetchall()

    lp_fixed = 0
    for ex in exercises_lp:
        lp = infer_lateral_pattern(ex["nome"], ex["nome_en"] or "")
        conn.execute("UPDATE esercizi SET lateral_pattern = ? WHERE id = ?", (lp, ex["id"]))
        lp_fixed += 1

    conn.commit()
    conn.close()
    print(f"    force_type filled: {ft_fixed}")
    print(f"    lateral_pattern filled: {lp_fixed}")
    return ft_fixed + lp_fixed


# ================================================================
# EXECUTION
# ================================================================

def verify(db_path: str) -> None:
    """Post-backfill verification."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    db_name = os.path.basename(db_path)
    total = conn.execute("SELECT COUNT(*) FROM esercizi WHERE deleted_at IS NULL").fetchone()[0]

    print(f"\n  Verification: {db_name}")

    for field in ["note_sicurezza", "force_type", "lateral_pattern"]:
        filled = conn.execute(f"""
            SELECT COUNT(*) FROM esercizi WHERE deleted_at IS NULL
            AND {field} IS NOT NULL AND {field} != ''
        """).fetchone()[0]
        pct = filled * 100 // total if total > 0 else 0
        status = "PASS" if pct >= 95 else "CHECK"
        print(f"    {field}: {filled}/{total} ({pct}%) {status}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill safety notes + force/lateral (Phase 4)")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both")
    parser.add_argument("--batch", type=int, default=0, help="Limit safety notes per DB")
    parser.add_argument("--only", choices=["safety", "force"], help="Run only one sub-phase")
    parser.add_argument("--subset-only", action="store_true",
                        help="Process only curated subset (in_subset=1)")
    args = parser.parse_args()

    print("Exercise Backfill — Phase 4")
    print("=" * 60)

    dbs = []
    if args.db in ("dev", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if args.db in ("prod", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm.db"))

    for db_path in dbs:
        if args.only != "force":
            backfill_safety(db_path, batch_size=args.batch, subset_only=args.subset_only)
        if args.only != "safety":
            backfill_force(db_path)

    print(f"\n{'=' * 60}")
    print("  VERIFICATION")
    print("=" * 60)

    for db_path in dbs:
        verify(db_path)

    print("\nDone.")
