"""
Fix classificazione esercizi nel subset curato (in_subset=1).

3 operazioni:
  1. Fix misclassificazioni CERTE (pattern_movimento errato)
  2. Fill force_type NULL (deterministico da pattern)
  3. Fix piano_movimento: aggiungere "frontal" dove appropriato

Idempotente, dual-DB, eseguibile dalla root:
  python -m tools.admin_scripts.fix_subset_classification [--db dev|prod|both] [--dry-run]
"""

import argparse
import json
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# ================================================================
# FIX 1: MISCLASSIFICAZIONI CERTE
# ================================================================
# (id, {campi da aggiornare})
# Ogni fix e' documentato con il motivo.

PATTERN_FIXES: list[tuple[int, dict[str, str], str]] = [
    (
        945,
        {"pattern_movimento": "pull_v"},
        "Rematore alla Smith Machine = Smith Machine Upright Row: "
        "e' un pull verticale (tira bilanciere verso mento), non push_v",
    ),
    (
        1024,
        {"pattern_movimento": "push_h"},
        "Lancio Pettorale Sdraiato = Chest Throw: "
        "e' un push orizzontale (lancia palla dal petto), non pull_h",
    ),
]

# ================================================================
# FIX 2: FORCE_TYPE NULL — mapping deterministico
# ================================================================

PATTERN_FORCE: dict[str, str] = {
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

# ================================================================
# FIX 3: PIANO_MOVIMENTO FRONTAL
# ================================================================
# Esercizi con movimento nel piano frontale (abduzione/adduzione,
# movimenti laterali) classificati erroneamente come sagittal/multi.

FRONTAL_FIXES: list[tuple[int, str]] = [
    (225, "Adduzione al Cavo Basso — Cable Hip Adduction: piano frontale"),
    (222, "Adduzione con Elastico — Band Hip Adduction: piano frontale"),
]


def fix_db(db_path: str, dry_run: bool) -> None:
    """Applica fix al DB specificato."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 60}")
    print(f"  Fix Subset Classification: {db_name}")
    if dry_run:
        print("  MODE: DRY RUN (nessuna modifica)")
    print(f"{'=' * 60}")

    # ── Fix 1: Pattern movimento ──
    print("\n  --- FIX 1: Misclassificazioni pattern_movimento ---")
    for eid, updates, reason in PATTERN_FIXES:
        row = conn.execute(
            "SELECT nome, pattern_movimento, force_type, muscoli_primari "
            "FROM esercizi WHERE id = ? AND in_subset = 1",
            (eid,),
        ).fetchone()
        if not row:
            print(f"  SKIP id={eid}: non trovato nel subset")
            continue

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [eid]

        print(f"  FIX id={eid} {row['nome']}")
        print(f"      {reason}")
        for k, v in updates.items():
            print(f"      {k}: {row[k]} -> {v}")

        if not dry_run:
            conn.execute(
                f"UPDATE esercizi SET {set_clause} WHERE id = ?", values
            )

    # ── Fix 2: Force type NULL ──
    print("\n  --- FIX 2: Fill force_type NULL ---")
    nulls = conn.execute(
        "SELECT id, nome, pattern_movimento FROM esercizi "
        "WHERE in_subset = 1 AND force_type IS NULL AND deleted_at IS NULL "
        "ORDER BY nome"
    ).fetchall()

    for row in nulls:
        expected = PATTERN_FORCE.get(row["pattern_movimento"])
        if not expected:
            print(f"  WARN id={row['id']} {row['nome']}: pattern {row['pattern_movimento']} non in mapping")
            continue
        print(f"  FILL id={row['id']:4d} {row['nome']:40s} pat={row['pattern_movimento']:10s} -> force={expected}")
        if not dry_run:
            conn.execute(
                "UPDATE esercizi SET force_type = ? WHERE id = ?",
                (expected, row["id"]),
            )

    if not nulls:
        print("  Nessun force_type NULL nel subset")

    # ── Fix 3: Piano movimento frontal ──
    print("\n  --- FIX 3: Piano movimento -> frontal ---")
    for eid, reason in FRONTAL_FIXES:
        row = conn.execute(
            "SELECT nome, piano_movimento FROM esercizi WHERE id = ? AND in_subset = 1",
            (eid,),
        ).fetchone()
        if not row:
            print(f"  SKIP id={eid}: non trovato nel subset")
            continue
        if row["piano_movimento"] == "frontal":
            print(f"  OK   id={eid} {row['nome']}: gia' frontal")
            continue
        print(f"  FIX  id={eid} {row['nome']}: {row['piano_movimento']} -> frontal")
        print(f"       {reason}")
        if not dry_run:
            conn.execute(
                "UPDATE esercizi SET piano_movimento = 'frontal' WHERE id = ?",
                (eid,),
            )

    if not dry_run:
        conn.commit()
        print(f"\n  Commit eseguito su {db_name}")
    else:
        print(f"\n  DRY RUN completato — nessuna modifica a {db_name}")

    conn.close()


def report_db(db_path: str) -> None:
    """Report di validazione post-fix."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 60}")
    print(f"  REPORT VALIDAZIONE: {db_name}")
    print(f"{'=' * 60}")

    # Subset size
    total = conn.execute(
        "SELECT COUNT(*) FROM esercizi WHERE in_subset = 1 AND deleted_at IS NULL"
    ).fetchone()[0]
    print(f"\n  Subset: {total} esercizi")

    # Force type coverage
    ft_null = conn.execute(
        "SELECT COUNT(*) FROM esercizi WHERE in_subset = 1 AND force_type IS NULL AND deleted_at IS NULL"
    ).fetchone()[0]
    print(f"  force_type NULL: {ft_null}")

    # Piano movimento distribution
    print("\n  Piano movimento distribuzione:")
    for row in conn.execute(
        "SELECT piano_movimento, COUNT(*) as cnt FROM esercizi "
        "WHERE in_subset = 1 AND deleted_at IS NULL GROUP BY piano_movimento ORDER BY cnt DESC"
    ).fetchall():
        print(f"    {row['piano_movimento']:12s} {row['cnt']}")

    # Cross-validation: muscle/pattern conflicts
    print("\n  Cross-validazione muscoli/pattern:")
    pull_muscles = {"back", "lats", "biceps"}
    push_muscles = {"chest", "triceps"}
    rows = conn.execute(
        "SELECT id, nome, pattern_movimento, muscoli_primari FROM esercizi "
        "WHERE in_subset = 1 AND deleted_at IS NULL ORDER BY id"
    ).fetchall()

    conflicts = 0
    for r in rows:
        try:
            muscles = set(json.loads(r["muscoli_primari"]))
        except (json.JSONDecodeError, TypeError):
            continue
        pat = r["pattern_movimento"]
        if pat in ("push_h", "push_v") and muscles & pull_muscles:
            print(f"    CONFLICT id={r['id']} {r['nome']}: pat={pat} muscles={muscles & pull_muscles}")
            conflicts += 1
        if pat in ("pull_h", "pull_v") and muscles & push_muscles:
            print(f"    CONFLICT id={r['id']} {r['nome']}: pat={pat} muscles={muscles & push_muscles}")
            conflicts += 1
    print(f"    Totale conflitti: {conflicts}")

    # Force_type vs pattern (INFORMATIVO, non errori)
    print("\n  Force_type vs pattern (info — molti sono legittimi):")
    mismatches = 0
    for r in conn.execute(
        "SELECT id, nome, pattern_movimento, force_type FROM esercizi "
        "WHERE in_subset = 1 AND force_type IS NOT NULL AND deleted_at IS NULL ORDER BY id"
    ).fetchall():
        expected = PATTERN_FORCE.get(r["pattern_movimento"])
        if expected and r["force_type"] != expected:
            mismatches += 1
    print(f"    Deviazioni dal mapping pattern->force: {mismatches}")
    print(f"    (Molte sono legittime: es. Croci=push_h/pull, Carry=carry/pull)")

    # Fields coverage
    print("\n  Copertura campi:")
    for field in ["esecuzione", "note_sicurezza", "controindicazioni",
                   "catena_cinetica", "piano_movimento", "tipo_contrazione"]:
        filled = conn.execute(
            f"SELECT COUNT(*) FROM esercizi WHERE in_subset = 1 "
            f"AND {field} IS NOT NULL AND {field} != '' AND deleted_at IS NULL"
        ).fetchone()[0]
        pct = round(filled / total * 100) if total > 0 else 0
        status = "OK" if pct == 100 else f"MANCA {total - filled}"
        print(f"    {field:25s} {filled:3d}/{total} ({pct}%) {status}")

    # Condition mappings
    cond_count = conn.execute(
        "SELECT COUNT(*) FROM esercizi_condizioni WHERE id_esercizio IN "
        "(SELECT id FROM esercizi WHERE in_subset = 1)"
    ).fetchone()[0]
    print(f"\n  esercizi_condizioni: {cond_count} righe")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fix classificazione esercizi subset (in_subset=1)"
    )
    parser.add_argument(
        "--db", choices=["dev", "prod", "both"], default="both",
        help="Quale database processare"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mostra cosa farebbe senza modificare"
    )
    args = parser.parse_args()

    print("Fix Subset Classification")
    print("=" * 60)

    dbs: list[str] = []
    if args.db in ("dev", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if args.db in ("prod", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm.db"))

    for db_path in dbs:
        fix_db(db_path, dry_run=args.dry_run)

    print(f"\n{'=' * 60}")
    print("  POST-FIX REPORT")
    print("=" * 60)

    for db_path in dbs:
        report_db(db_path)

    print("\nDone.")
