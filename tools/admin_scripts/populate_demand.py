"""Populate per-exercise demand vectors for all active exercises.

Deterministic rule-based assignment:
- Base vector from demand_registry (pattern x difficulty)
- Equipment modifiers (barbell > dumbbell > cable > machine > bodyweight)
- Category modifiers (compound vs isolation vs bodyweight vs cardio etc.)
- Name-based overrides for special exercises (Olympic lifts, plyometrics)

Idempotent: re-running overwrites previous values.
Usage:
    python -m tools.admin_scripts.populate_demand --db dev
    python -m tools.admin_scripts.populate_demand --db prod
    python -m tools.admin_scripts.populate_demand --db both
    python -m tools.admin_scripts.populate_demand --db both --dry-run
"""

import argparse
import re
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

DEMAND_DIMS = [
    "skill_demand",
    "coordination_demand",
    "stability_demand",
    "ballistic_demand",
    "impact_demand",
    "axial_load_demand",
    "shoulder_complex_demand",
    "lumbar_load_demand",
    "grip_demand",
    "metabolic_demand",
]

# ──────────────────────────────────────────────────────────────
# Base vectors: (pattern, difficulty) -> 10D vector
# Copied from demand_registry.py for standalone use (no API import)
# ──────────────────────────────────────────────────────────────

#                                    sk co st ba im ax sh lu gr me
_BASE: dict[tuple[str, str], list[int]] = {
    # Squat
    ("squat", "beginner"):           [1, 1, 1, 0, 0, 1, 0, 1, 0, 1],
    ("squat", "intermediate"):       [2, 2, 2, 0, 0, 2, 0, 2, 1, 2],
    ("squat", "advanced"):           [2, 2, 2, 0, 0, 3, 1, 3, 1, 2],
    # Hinge
    ("hinge", "beginner"):           [1, 1, 1, 0, 0, 1, 0, 2, 1, 1],
    ("hinge", "intermediate"):       [2, 2, 2, 0, 0, 2, 0, 3, 2, 2],
    ("hinge", "advanced"):           [2, 2, 2, 0, 0, 3, 0, 3, 2, 2],
    # Push H
    ("push_h", "beginner"):          [1, 1, 1, 0, 0, 0, 2, 0, 0, 1],
    ("push_h", "intermediate"):      [1, 1, 2, 0, 0, 0, 2, 1, 1, 1],
    ("push_h", "advanced"):          [2, 2, 2, 0, 0, 0, 3, 1, 1, 1],
    # Push V
    ("push_v", "beginner"):          [1, 1, 1, 0, 0, 1, 2, 1, 0, 1],
    ("push_v", "intermediate"):      [2, 2, 2, 0, 0, 1, 3, 1, 1, 1],
    ("push_v", "advanced"):          [2, 2, 2, 0, 0, 2, 3, 1, 1, 1],
    # Pull H
    ("pull_h", "beginner"):          [1, 1, 1, 0, 0, 0, 1, 1, 1, 1],
    ("pull_h", "intermediate"):      [1, 1, 1, 0, 0, 0, 1, 1, 2, 1],
    ("pull_h", "advanced"):          [2, 2, 2, 0, 0, 0, 2, 1, 2, 1],
    # Pull V
    ("pull_v", "beginner"):          [1, 1, 1, 0, 0, 0, 2, 0, 2, 1],
    ("pull_v", "intermediate"):      [2, 2, 2, 0, 0, 0, 2, 0, 2, 1],
    ("pull_v", "advanced"):          [3, 3, 2, 0, 0, 0, 3, 0, 3, 2],
    # Core
    ("core", "beginner"):            [1, 1, 2, 0, 0, 0, 0, 1, 0, 1],
    ("core", "intermediate"):        [1, 1, 2, 0, 0, 0, 0, 2, 0, 1],
    ("core", "advanced"):            [2, 2, 3, 0, 0, 1, 0, 2, 0, 1],
    # Rotation
    ("rotation", "beginner"):        [1, 2, 2, 0, 0, 0, 1, 1, 0, 1],
    ("rotation", "intermediate"):    [2, 2, 2, 0, 0, 0, 1, 2, 1, 1],
    ("rotation", "advanced"):        [2, 3, 3, 0, 0, 1, 1, 2, 1, 1],
    # Carry
    ("carry", "beginner"):           [1, 1, 2, 0, 0, 2, 1, 2, 3, 2],
    ("carry", "intermediate"):       [1, 1, 2, 0, 0, 3, 1, 2, 3, 2],
    ("carry", "advanced"):           [1, 1, 2, 0, 0, 4, 1, 3, 4, 3],
    # Isolation patterns
    ("hip_thrust", "beginner"):      [1, 1, 1, 0, 0, 0, 0, 1, 0, 1],
    ("hip_thrust", "intermediate"):  [1, 1, 1, 0, 0, 0, 0, 1, 0, 1],
    ("hip_thrust", "advanced"):      [1, 1, 1, 0, 0, 1, 0, 1, 0, 1],
    ("curl", "beginner"):            [0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    ("curl", "intermediate"):        [0, 0, 1, 0, 0, 0, 0, 0, 1, 0],
    ("curl", "advanced"):            [1, 1, 1, 0, 0, 0, 0, 0, 2, 0],
    ("extension_tri", "beginner"):   [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    ("extension_tri", "intermediate"): [0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    ("extension_tri", "advanced"):   [1, 1, 1, 0, 0, 0, 1, 0, 1, 0],
    ("lateral_raise", "beginner"):   [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    ("lateral_raise", "intermediate"): [0, 1, 1, 0, 0, 0, 2, 0, 0, 0],
    ("lateral_raise", "advanced"):   [1, 1, 1, 0, 0, 0, 2, 0, 0, 0],
    ("face_pull", "beginner"):       [0, 1, 1, 0, 0, 0, 1, 0, 1, 0],
    ("face_pull", "intermediate"):   [0, 1, 1, 0, 0, 0, 1, 0, 1, 0],
    ("face_pull", "advanced"):       [1, 1, 1, 0, 0, 0, 2, 0, 1, 0],
    ("calf_raise", "beginner"):      [0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    ("calf_raise", "intermediate"):  [0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    ("calf_raise", "advanced"):      [0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
    ("leg_curl", "beginner"):        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ("leg_curl", "intermediate"):    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    ("leg_curl", "advanced"):        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    ("leg_extension", "beginner"):   [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ("leg_extension", "intermediate"): [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    ("leg_extension", "advanced"):   [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    ("adductor", "beginner"):        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ("adductor", "intermediate"):    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    ("adductor", "advanced"):        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
}

# Fallback for unmapped combinations
_FALLBACK = [1, 1, 1, 0, 0, 1, 1, 1, 1, 1]

# Zero vector for non-training categories (stretching, mobilita, avviamento)
_ZERO = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# ──────────────────────────────────────────────────────────────
# Equipment modifiers — delta applied to base vector
# Rationale: free weights demand more stability, skill, grip
# than guided machines. Barbell > dumbbell > kettlebell > cable > band > machine > bodyweight
# ──────────────────────────────────────────────────────────────

#                              sk  co  st  ba  im  ax  sh  lu  gr  me
_EQUIP_MOD: dict[str, list[int]] = {
    "barbell":    [+1, +1, +1,  0,  0, +1,  0, +1, +1,  0],
    "dumbbell":   [ 0,  0, +1,  0,  0,  0,  0,  0, +1,  0],
    "kettlebell": [+1, +1, +1,  0,  0,  0,  0,  0, +1,  0],
    "cable":      [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    "band":       [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    "machine":    [-1, -1, -1,  0,  0,  0,  0, -1,  0,  0],
    "bodyweight": [ 0,  0,  0,  0,  0,  0,  0,  0, -1,  0],
    "trx":        [+1, +1, +1,  0,  0,  0,  0,  0,  0,  0],
}

# ──────────────────────────────────────────────────────────────
# Name-based overrides for special exercises
# Pattern: (regex_pattern, dimension_deltas)
# Applied AFTER base + equipment modifiers
# ──────────────────────────────────────────────────────────────

_NAME_OVERRIDES: list[tuple[re.Pattern[str], list[int]]] = [
    # Olympic lifts: high skill, coordination, ballistic, axial load
    #                                        sk  co  st  ba  im  ax  sh  lu  gr  me
    (re.compile(r"(?i)(girata|clean|slancio|strappo|snatch)", re.IGNORECASE),
                                             [+2, +2,  0, +2,  0, +1, +1, +1, +1, +1]),

    # Plyometrics / box jumps: ballistic + impact
    (re.compile(r"(?i)(salt[oi]|jump|box jump|plyometric|burpee)", re.IGNORECASE),
                                             [+1, +1,  0, +2, +2,  0,  0,  0,  0, +1]),

    # Unilateral compound (Bulgarian, single leg): stability + coordination
    (re.compile(r"(?i)(bulgaro|unilateral|single.?leg|un.?braccio|monolateral)", re.IGNORECASE),
                                             [+1, +1, +1,  0,  0,  0,  0,  0,  0,  0]),

    # Deficit / from blocks: more ROM = more skill + lumbar
    (re.compile(r"(?i)(deficit|dal.?blocco|from.?block)", re.IGNORECASE),
                                             [+1,  0,  0,  0,  0,  0,  0, +1,  0,  0]),

    # Overhead movements: shoulder complex
    (re.compile(r"(?i)(overhead|sopra.?la.?testa|military|lento.?avanti)", re.IGNORECASE),
                                             [ 0,  0,  0,  0,  0,  0, +1,  0,  0,  0]),

    # Atlas stones / unconventional: high everything
    (re.compile(r"(?i)(atlas|pietra.?atlante|sassi)", re.IGNORECASE),
                                             [+1, +1, +1,  0,  0, +1,  0, +1, +1, +1]),

    # Farmer walk / loaded carries: grip + axial
    (re.compile(r"(?i)(farmer|trascinamento|walk|loaded.?carry|valigia)", re.IGNORECASE),
                                             [ 0,  0,  0,  0,  0, +1,  0,  0, +1, +1]),

    # TRX / suspension: stability boost
    (re.compile(r"(?i)(trx|suspension|anelli)", re.IGNORECASE),
                                             [+1, +1, +1,  0,  0,  0,  0,  0,  0,  0]),

    # Rope exercises: grip
    (re.compile(r"(?i)(corda|rope|battle.?rope)", re.IGNORECASE),
                                             [ 0,  0,  0,  0,  0,  0,  0,  0, +1,  0]),
]


def _clamp(val: int) -> int:
    """Clamp demand value to 0-4 range."""
    return max(0, min(4, val))


def compute_demand_vector(
    nome: str,
    pattern: str,
    difficulty: str,
    equipment: str,
    category: str,
) -> list[int]:
    """Compute the 10D demand vector for an exercise.

    Logic:
    1. Non-training categories (stretching/mobilita/avviamento) → zero vector
    2. Cardio → base from pattern with reduced strength demands
    3. Start from base vector (pattern × difficulty)
    4. Apply equipment modifier
    5. Apply name-based overrides
    6. Clamp all values to 0-4
    """
    # Non-training categories: zero demand
    if category in ("stretching", "mobilita", "avviamento"):
        return list(_ZERO)

    # Base vector
    base = list(_BASE.get((pattern, difficulty), _FALLBACK))

    # Cardio: use base but boost metabolic, reduce grip
    if category == "cardio":
        base[9] = max(base[9], 2)  # metabolic >= 2
        base[8] = 0  # grip = 0 (cardio machines / bodyweight)
        # Machine cardio = low everything except metabolic
        if equipment == "machine":
            for i in range(8):
                base[i] = min(base[i], 1)
            base[9] = 2  # metabolic
            return base

    # Equipment modifier
    equip_mod = _EQUIP_MOD.get(equipment, [0] * 10)
    for i in range(10):
        base[i] += equip_mod[i]

    # Isolation category: reduce metabolic and axial load (already low in base,
    # but equipment mods might have pushed them up)
    if category == "isolation":
        base[5] = min(base[5], 1)  # axial_load capped at 1
        base[9] = min(base[9], 1)  # metabolic capped at 1

    # Name-based overrides
    for regex, deltas in _NAME_OVERRIDES:
        if regex.search(nome):
            for i in range(10):
                base[i] += deltas[i]

    # Clamp
    return [_clamp(v) for v in base]


def populate_demand(db_path: str, dry_run: bool = False) -> dict[str, int]:
    """Populate demand vectors for all active exercises in the given DB.

    Returns stats dict with counts.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch all active exercises
    rows = cur.execute(
        "SELECT id, nome, pattern_movimento, difficolta, attrezzatura, categoria "
        "FROM esercizi WHERE in_subset = 1 AND deleted_at IS NULL"
    ).fetchall()

    stats = {"total": len(rows), "updated": 0, "zero": 0, "skipped": 0}
    updates: list[tuple] = []

    for row in rows:
        vec = compute_demand_vector(
            nome=row["nome"],
            pattern=row["pattern_movimento"],
            difficulty=row["difficolta"],
            equipment=row["attrezzatura"],
            category=row["categoria"],
        )

        if all(v == 0 for v in vec):
            stats["zero"] += 1
        else:
            stats["updated"] += 1

        updates.append((*vec, row["id"]))

    if dry_run:
        # Print sample of non-zero vectors
        print(f"\n{'='*80}")
        print(f"DRY RUN — {db_path}")
        print(f"{'='*80}")
        print(f"Total exercises: {stats['total']}")
        print(f"Non-zero vectors: {stats['updated']}")
        print(f"Zero vectors (stretch/mob/avv): {stats['zero']}")

        # Show distribution
        sample_rows = cur.execute(
            "SELECT id, nome, pattern_movimento, difficolta, attrezzatura, categoria "
            "FROM esercizi WHERE in_subset = 1 AND deleted_at IS NULL "
            "AND categoria IN ('compound', 'isolation') "
            "ORDER BY categoria, pattern_movimento, attrezzatura "
            "LIMIT 30"
        ).fetchall()
        print(f"\n--- Sample vectors (first 30 compound/isolation) ---")
        print(f"{'Nome':<40s} {'cat':<10s} {'pat':<10s} {'eq':<10s} {'dif':<12s}  sk co st ba im ax sh lu gr me")
        for r in sample_rows:
            vec = compute_demand_vector(r["nome"], r["pattern_movimento"], r["difficolta"], r["attrezzatura"], r["categoria"])
            dims = " ".join(f"{v:2d}" for v in vec)
            print(f"{r['nome'][:39]:<40s} {r['categoria']:<10s} {r['pattern_movimento']:<10s} "
                  f"{r['attrezzatura']:<10s} {r['difficolta']:<12s}  {dims}")
    else:
        set_clause = ", ".join(f"{dim} = ?" for dim in DEMAND_DIMS)
        sql = f"UPDATE esercizi SET {set_clause} WHERE id = ?"
        cur.executemany(sql, updates)
        conn.commit()
        print(f"[{db_path}] Updated {stats['updated']} exercises, "
              f"{stats['zero']} zero vectors, total {stats['total']}")

    conn.close()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate exercise demand vectors")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    targets: list[str] = []
    if args.db in ("prod", "both"):
        targets.append(str(DATA_DIR / "crm.db"))
    if args.db in ("dev", "both"):
        targets.append(str(DATA_DIR / "crm_dev.db"))

    for db_path in targets:
        populate_demand(db_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
