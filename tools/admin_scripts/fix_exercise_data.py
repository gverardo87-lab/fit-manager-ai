"""
Fix exercise data quality issues — data corrections for Quality Engine accuracy.

Fixes:
  1. Pattern misattributions (3 exercises: Alzate Posteriori, Pec Machine Inversa, Rematore Alto)
  2. Calf raise pattern inconsistency (2 exercises: hinge → squat)
  3. Duplicate exercises soft-deleted (5 pairs)
  4. Missing muscoli_secondari populated (57 exercises)

Safe: uses UPDATE with WHERE id = ? — surgical fixes, no bulk operations.
Runs on BOTH databases (crm.db + crm_dev.db).
"""

import sqlite3
import json
import os
from datetime import datetime

# ════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DBS = [
    os.path.join(BASE_DIR, "crm.db"),
    os.path.join(BASE_DIR, "crm_dev.db"),
]

NOW = datetime.now().isoformat()

# ════════════════════════════════════════════════════════════
# FIX 1: PATTERN MISATTRIBUTIONS
# ════════════════════════════════════════════════════════════

PATTERN_FIXES = [
    # (nome, old_pattern, new_pattern, reason)
    ("Alzate Posteriori", "push_v", "pull_h", "Rear delt fly is horizontal abduction = pull"),
    ("Pectoral Machine Inversa", "push_v", "pull_h", "Reverse pec deck = horizontal pull"),
    ("Rematore Alto", "push_v", "pull_v", "Upright row = vertical pull"),
]

# ════════════════════════════════════════════════════════════
# FIX 2: CALF RAISE PATTERN STANDARDIZATION
# ════════════════════════════════════════════════════════════

CALF_PATTERN_FIXES = [
    # (nome, old_pattern, new_pattern)
    ("Calf Raise Seduto", "hinge", "squat"),
    ("Rialzi Sulle Punte", "hinge", "squat"),
]

# ════════════════════════════════════════════════════════════
# FIX 3: DUPLICATES TO SOFT-DELETE
# ════════════════════════════════════════════════════════════

# (nome_to_delete, reason)
DUPLICATES_TO_DELETE = [
    ("L-sit", "Duplicate of L-Sit (id=260) — case difference only"),
    ("Nordic Curl", "Duplicate of Nordic Hamstring Curl (id=266)"),
    ("Clean Kettlebell", "Duplicate of Kettlebell Clean (id=296) — richer data"),
    ("Snatch Kettlebell", "Duplicate of Kettlebell Snatch (id=297) — richer data"),
    ("Pulldown Braccia Tese", "Duplicate of Pulldown a Braccia Tese (id=247) — intermediate version"),
]

# ════════════════════════════════════════════════════════════
# FIX 4: MISSING MUSCOLI_SECONDARI
# ════════════════════════════════════════════════════════════

# Anatomically accurate secondary muscles for each exercise
SECONDARY_MUSCLES_FIXES = {
    # === BODYWEIGHT / CORE ===
    "Crunch Bicicletta": ["shoulders"],       # rotation = obliques (core primary) + hip flexors
    "Dead Bug": ["shoulders", "glutes"],      # anti-extension + hip stabilization
    "Hollow Body": ["quadriceps"],            # hip flexors assist
    "Plank Laterale": ["shoulders", "glutes"],  # shoulder stabilization + hip abduction
    "Russian Twist": ["shoulders"],           # arms hold weight
    "V-ups": ["quadriceps", "shoulders"],     # hip flexors + shoulder stabilization

    # === CARDIO ===
    "Ciclismo": ["hamstrings", "glutes", "calves"],
    "Corsa": ["hamstrings", "glutes", "calves", "core"],
    "Ellittica": ["hamstrings", "glutes", "chest", "back"],

    # === SHOULDER ISOLATION (push_v) ===
    "Alzate Frontali": ["chest", "core"],            # anterior deltoid + stabilization
    "Alzate Laterali": ["traps", "core"],            # upper traps assist
    "Alzate Laterali Cavi": ["traps", "core"],
    "Alzate Laterali Landmine": ["traps", "core"],

    # === PULL_H ISOLATION (biceps/forearms) ===
    "Aperture Elastico": ["traps", "shoulders"],     # rear delt + scapular retraction
    "Bayesian Curl": ["forearms"],
    "Curl Cavi": ["forearms"],
    "Curl Concentrato": ["forearms"],
    "Curl Inverso Bilanciere": ["biceps"],           # forearms primary, biceps assist
    "Curl Manubri Panca Inclinata": ["forearms"],
    "Curl Panca Scott": ["forearms"],
    "Curl Polso": ["biceps"],                        # wrist flexors primary, biceps stabilize
    "Curl Polso Inverso": ["biceps"],
    "Reverse Wrist Curl": ["biceps"],
    "Spider Curl": ["forearms"],
    "Wrist Curl con Manubrio": ["biceps"],

    # === SQUAT-PATTERN ISOLATION ===
    "Ball Squeeze Isometrico": ["core"],              # adductors primary, core stabilization
    "Calf Press alla Leg Press": ["quadriceps"],      # minimal quad involvement
    "Calf Raise Seduto alla Macchina": ["core"],      # minimal, stability only
    "Calf Raise alla Macchina in Piedi": ["core"],
    "Estensione Gambe": ["core"],                     # quad isolation

    # === HINGE-PATTERN ISOLATION ===
    "Calf Raise Seduto": ["core"],
    "Curl Gambe": ["glutes"],                         # hamstring curl = minor glute assist
    "Leg Curl Seduto": ["glutes"],
    "Rialzi Sulle Punte": ["core"],

    # === CORE ISOLATION ===
    "Crunch Cavi": ["shoulders"],                     # pulling cable down
    "Pallof Press": ["shoulders", "chest"],           # anti-rotation + arm extension

    # === PUSH_V ISOLATION (triceps) ===
    "Estensione Overhead Cavi": ["shoulders"],
    "Estensione Tricipiti Sopra Testa": ["shoulders"],
    "Pushdown Cavi": ["chest"],                       # minor pec assist at bottom
    "Spinta Tricipiti Corda": ["chest"],

    # === PULL_V ISOLATION ===
    "Face Pull Elastico": ["back"],                   # rear delts + scapular retractors
    "Scrollate Bilanciere": ["forearms"],             # grip demand
    "Scrollate Manubri": ["forearms"],

    # === PUSH_H ISOLATION (triceps/chest) ===
    "French Press": ["shoulders"],                    # long head stretches at shoulder
    "French Press Manubri": ["shoulders"],
    "Pectoral Machine": ["shoulders"],                # chest isolation, front delt assist
    "Svend Press": ["triceps", "shoulders"],          # isometric chest squeeze
    "Tricep Kickback": ["shoulders"],

    # === OTHER ===
    "Tibialis Raise": ["core"],                       # tibialis anterior primary, stability

    # === MOBILITA ===
    "Mobilita Caviglie": [],                          # mobility, no secondary load
    "Mobilita Polsi": [],

    # === STRETCHING ===
    "Stretching Avambracci Estensori": [],
    "Stretching Collo Laterale": [],
    "Stretching Polpacci": [],
    "Stretching Quadricipiti": [],
    "Stretching Soleo Seduto": [],
}

# ════════════════════════════════════════════════════════════
# EXECUTION
# ════════════════════════════════════════════════════════════

def fix_database(db_path: str) -> None:
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    db_name = os.path.basename(db_path)

    print(f"\n{'='*60}")
    print(f"  Fixing: {db_name}")
    print(f"{'='*60}")

    # ── Fix 1: Pattern misattributions ──
    print("\n  [Fix 1] Pattern misattributions:")
    for nome, old_pat, new_pat, reason in PATTERN_FIXES:
        cur.execute(
            "UPDATE esercizi SET pattern_movimento = ? WHERE nome = ? AND pattern_movimento = ? AND deleted_at IS NULL",
            (new_pat, nome, old_pat),
        )
        affected = cur.rowcount
        status = "OK" if affected > 0 else "SKIP (not found or already fixed)"
        print(f"    {nome}: {old_pat} -> {new_pat} [{status}] ({reason})")

    # ── Fix 2: Calf raise standardization ──
    print("\n  [Fix 2] Calf raise pattern standardization:")
    for nome, old_pat, new_pat in CALF_PATTERN_FIXES:
        cur.execute(
            "UPDATE esercizi SET pattern_movimento = ? WHERE nome = ? AND pattern_movimento = ? AND deleted_at IS NULL",
            (new_pat, nome, old_pat),
        )
        affected = cur.rowcount
        status = "OK" if affected > 0 else "SKIP"
        print(f"    {nome}: {old_pat} -> {new_pat} [{status}]")

    # ── Fix 3: Soft-delete duplicates ──
    print("\n  [Fix 3] Soft-delete duplicates:")
    for nome, reason in DUPLICATES_TO_DELETE:
        # Check if used in any workout session first
        cur.execute(
            """SELECT COUNT(*) as cnt FROM esercizi_sessione es
               JOIN esercizi e ON es.id_esercizio = e.id
               WHERE e.nome = ? AND e.deleted_at IS NULL""",
            (nome,),
        )
        in_use = cur.fetchone()["cnt"]
        if in_use > 0:
            print(f"    {nome}: SKIP — in use by {in_use} workout session(s)")
            continue

        cur.execute(
            "UPDATE esercizi SET deleted_at = ? WHERE nome = ? AND deleted_at IS NULL",
            (NOW, nome),
        )
        affected = cur.rowcount
        status = "OK" if affected > 0 else "SKIP (not found or already deleted)"
        print(f"    {nome}: soft-deleted [{status}] ({reason})")

    # ── Fix 4: Missing muscoli_secondari ──
    print("\n  [Fix 4] Missing muscoli_secondari:")
    fixed = 0
    skipped = 0
    for nome, muscles in SECONDARY_MUSCLES_FIXES.items():
        muscles_json = json.dumps(muscles)
        cur.execute(
            """UPDATE esercizi SET muscoli_secondari = ?
               WHERE nome = ? AND deleted_at IS NULL
               AND (muscoli_secondari IS NULL OR muscoli_secondari = '' OR muscoli_secondari = '[]')""",
            (muscles_json, nome),
        )
        if cur.rowcount > 0:
            fixed += 1
        else:
            skipped += 1
    print(f"    Fixed: {fixed}, Skipped (already had data or not found): {skipped}")

    conn.commit()
    conn.close()
    print(f"\n  Done: {db_name}")


def verify_database(db_path: str) -> None:
    """Post-fix verification."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    db_name = os.path.basename(db_path)

    print(f"\n  Verification: {db_name}")

    # Check pattern fixes
    for nome, _, new_pat, _ in PATTERN_FIXES:
        cur.execute("SELECT pattern_movimento FROM esercizi WHERE nome = ? AND deleted_at IS NULL", (nome,))
        r = cur.fetchone()
        if r:
            ok = "PASS" if r["pattern_movimento"] == new_pat else f"FAIL (got {r['pattern_movimento']})"
            print(f"    {nome}: pattern = {r['pattern_movimento']} [{ok}]")

    # Check remaining null secondaries
    cur.execute(
        """SELECT COUNT(*) as cnt FROM esercizi
           WHERE deleted_at IS NULL AND (muscoli_secondari IS NULL OR muscoli_secondari = '' OR muscoli_secondari = '[]')"""
    )
    remaining = cur.fetchone()["cnt"]
    print(f"    Remaining exercises without muscoli_secondari: {remaining}")

    # Check total active exercises
    cur.execute("SELECT COUNT(*) as cnt FROM esercizi WHERE deleted_at IS NULL")
    total = cur.fetchone()["cnt"]
    print(f"    Total active exercises: {total}")

    # Pattern distribution after fix
    print(f"    Pattern distribution (push/pull balance):")
    cur.execute(
        """SELECT pattern_movimento, COUNT(*) as cnt FROM esercizi
           WHERE deleted_at IS NULL AND categoria NOT IN ('avviamento', 'stretching', 'mobilita')
           GROUP BY pattern_movimento ORDER BY cnt DESC"""
    )
    for r in cur.fetchall():
        print(f"      {r['pattern_movimento']:10s}: {r['cnt']}")

    conn.close()


if __name__ == "__main__":
    print("Exercise Data Quality Fix Script")
    print("=" * 60)

    for db_path in DBS:
        fix_database(db_path)

    print("\n" + "=" * 60)
    print("  POST-FIX VERIFICATION")
    print("=" * 60)

    for db_path in DBS:
        verify_database(db_path)

    print("\nAll done.")
