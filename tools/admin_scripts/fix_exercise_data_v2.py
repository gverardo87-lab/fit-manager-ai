"""
Fix exercise data quality v2 — pulizia strutturale post-import FDB.

Correzioni:
  0A. Trailing punctuation nei nomi (~69 esercizi)
  0B. Duplicati nome_en (21 gruppi → soft-delete/merge)
  0C. Duplicati nome IT (6 gruppi → soft-delete/rinomina)
  0D. Misclassificazioni compound+core (33 esercizi)
  0E. Sync enrichment prod → dev (136 esercizi)

Idempotente: sicuro da rieseguire.
Eseguire dalla root:
  python -m tools.admin_scripts.fix_exercise_data_v2
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

# ================================================================
# CONFIG
# ================================================================

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DBS = [
    os.path.join(BASE_DIR, "crm.db"),
    os.path.join(BASE_DIR, "crm_dev.db"),
]
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

# ================================================================
# 0B. DUPLICATI nome_en — MERGE & SOFT-DELETE
# ================================================================

# keep_id: esercizio da mantenere (enriched, nome IT corretto)
# delete_id: esercizio da soft-delete (duplicato)
# Se delete_id e' usato in schede, prima merge esercizi_sessione
NOME_EN_DUPLICATES = [
    # (keep_id, delete_id, reason)
    (119, 258, "Ab Wheel Rollout: keep enriched Ruota Addominale"),
    (152, 303, "Band Pull Apart: keep enriched Aperture Elastico (merge 2 sessioni)"),
    # SKIP: (5, 184) Bodyweight Squat — categorie diverse (bodyweight vs avviamento), teniamo entrambi
    (178, 308, "Butt Kicks: keep enriched+used(17) Calci Indietro"),
    (26, 268, "Cable Pull Through: keep enriched+used(18)"),
    (101, 271, "Concentration Curl: keep enriched Curl Concentrato"),
    (189, 328, "Doorway Chest Stretch: keep enriched (merge 1 sessione)"),
    (121, 261, "Hanging Leg Raise: keep enriched (merge 1 sessione)"),
    (131, 259, "Hollow Body Hold: keep enriched (merge 1 sessione)"),
    # SKIP: (162, 183) Jump Rope — categorie diverse (cardio vs avviamento), teniamo entrambi
    (142, 296, "Kettlebell Clean: keep enriched+used(4)"),
    (31, 269, "Kettlebell Swing: keep enriched"),
    (145, 298, "Kettlebell Windmill: keep enriched"),
    (133, 240, "Landmine Rotation: keep enriched"),
    (11, 288, "Pistol Squat: keep enriched+used(1)"),
    (98, 272, "Preacher Curl: keep enriched"),
    (115, 279, "Reverse Wrist Curl: keep enriched"),
    (161, 284, "Rowing Machine: keep enriched Vogatore"),
    (105, 276, "Skull Crusher: keep enriched French Press"),
    (166, 282, "Sled Push: keep enriched+used(1) Spinta Slitta"),
    (19, 270, "Sumo Deadlift: keep enriched Stacco Sumo"),
]

# ================================================================
# 0C. DUPLICATI nome IT — RINOMINA o SOFT-DELETE
# ================================================================

# Soft-delete: concetto duplicato
NOME_IT_DELETE = [
    # (id_to_delete, reason)
    (412, "Ciclismo duplicato: id=160 Cycling e' il principale"),
    (1012, "Scalatore duplicato: id=168 Stair Climber e' il principale"),
]

# Rinomina: esercizi diversi con traduzione sbagliata
NOME_IT_RENAME = [
    # (id, new_nome, reason)
    (366, "Circonduzioni della Caviglia", "Ankle Circles tradotto erroneamente come 'polso'"),
    (566, "Floor Press con Catene", "Floor Press != Bench Press, entrambi tradotti 'Panca piana'"),
    (793, "Pin Press al Bilanciere", "Pin Presses, diverso da Tate Press"),
    (1033, "Tate Press con Manubri", "Tate Press, diverso da Pin Press"),
    (474, "Stacco per Clean", "Clean Deadlift tradotto erroneamente come 'Stacco Rumeno'"),
]

# ================================================================
# 0D. MISCLASSIFICAZIONI compound+core → correzione
# ================================================================

# Quasi tutti sono esercizi core che dovrebbero essere bodyweight/isolation
# (id, new_categoria, new_pattern, reason)
CATEGORY_FIXES = [
    # Core isolation/bodyweight → bodyweight + core
    (346, "bodyweight", "core", "3/4 Sit-Up: core isolation"),
    (349, "bodyweight", "core", "Ab Roller: core exercise"),
    (353, "bodyweight", "core", "Air Bike: core crunch variant"),
    (383, "bodyweight", "core", "Barbell Ab Rollout: core primary"),
    (389, "bodyweight", "core", "Barbell Rollout from Bench: core"),
    (404, "bodyweight", "core", "Bent-Knee Hip Raise: core isolation"),
    (422, "bodyweight", "core", "Bottoms Up: core exercise"),
    (429, "bodyweight", "core", "Butt-Ups: core exercise"),
    (485, "bodyweight", "core", "Cocoons: core crunch variant"),
    (504, "bodyweight", "core", "Decline Oblique Crunch: core"),
    (506, "bodyweight", "core", "Decline Reverse Crunch: core"),
    (548, "bodyweight", "core", "Elbow to Knee: core"),
    (554, "bodyweight", "core", "Exercise Ball Pull-In: core"),
    (562, "bodyweight", "core", "Flat Bench Leg Pull-In: core"),
    (600, "bodyweight", "core", "Hanging Pike: core advanced"),
    (638, "bodyweight", "core", "Jackknife Sit-Up: core"),
    (680, "bodyweight", "core", "Leg Pull-In: core"),
    (778, "bodyweight", "core", "Otis-Up: core"),
    (809, "bodyweight", "core", "Press Sit-Up: core"),
    (874, "bodyweight", "core", "Seated Flat Bench Leg Pull-In: core"),
    (899, "bodyweight", "core", "Side Jackknife: core"),
    (956, "bodyweight", "core", "Spider Crawl: core"),
    (1076, "bodyweight", "core", "Wind Sprints: core"),
    # Rotation exercises → compound + rotation (mantieni compound per movimento multi-articolare)
    (437, "compound", "rotation", "Cable Judo Flip: rotation movement"),
    (670, "compound", "rotation", "Landmine 180s: rotation"),
    (977, "compound", "rotation", "Standing Cable Lift: rotation/anti-rot"),
    (978, "compound", "rotation", "Standing Cable Wood Chop: rotation"),
    (955, "compound", "rotation", "Spell Caster: rotation"),
    # Compound with kettlebell: mantieni compound ma correggi pattern
    (411, "compound", "push_v", "Bent Press: overhead press variant"),
    (647, "compound", "core", "Kettlebell Figure 8: keep as compound core"),
    (650, "compound", "core", "Kettlebell Pass Between Legs: keep as compound core"),
    # Complex movements
    (590, "compound", "pull_v", "Gorilla Chin/Crunch: chin-up variant"),
    (760, "compound", "hinge", "One-Arm Medicine Ball Slam: explosive hinge"),
]

# ================================================================
# ENRICHMENT FIELDS (for sync prod → dev)
# ================================================================

ENRICHMENT_FIELDS = [
    "force_type", "lateral_pattern",
    "descrizione_anatomica", "descrizione_biomeccanica",
    "setup", "esecuzione", "respirazione", "tempo_consigliato",
    "coaching_cues", "errori_comuni", "note_sicurezza", "controindicazioni",
]


# ================================================================
# EXECUTION
# ================================================================

def fix_database(db_path: str) -> None:
    """Apply all fixes to a single database."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return

    conn = sqlite3.connect(db_path)
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 60}")
    print(f"  Fixing: {db_name}")
    print(f"{'=' * 60}")

    # ── 0A: Trailing punctuation ──
    print("\n  [0A] Trailing punctuation:")
    conn.execute("""
        UPDATE esercizi SET nome = RTRIM(RTRIM(RTRIM(nome, '.'), ','), ';')
        WHERE deleted_at IS NULL AND (nome LIKE '%.' OR nome LIKE '%,' OR nome LIKE '%;')
    """)
    print(f"    Fixed: {conn.total_changes} nomi")

    # ── 0B: Duplicati nome_en ──
    print("\n  [0B] Duplicati nome_en:")
    merged = 0
    deleted = 0
    for keep_id, delete_id, reason in NOME_EN_DUPLICATES:
        # Check if delete_id exists and is active
        exists = conn.execute(
            "SELECT id FROM esercizi WHERE id = ? AND deleted_at IS NULL", (delete_id,)
        ).fetchone()
        if not exists:
            continue

        # Merge: reassign workout sessions
        reassigned = conn.execute(
            "UPDATE esercizi_sessione SET id_esercizio = ? WHERE id_esercizio = ?",
            (keep_id, delete_id)
        ).rowcount
        if reassigned:
            merged += reassigned
            print(f"    Merged {reassigned} session(s): {delete_id} -> {keep_id}")

        # Soft-delete
        conn.execute(
            "UPDATE esercizi SET deleted_at = ? WHERE id = ? AND deleted_at IS NULL",
            (NOW, delete_id)
        )
        deleted += 1
        print(f"    Soft-deleted id={delete_id} ({reason})")

    print(f"    Total: {deleted} deleted, {merged} sessions merged")

    # ── 0C: Duplicati nome IT ──
    print("\n  [0C] Duplicati nome IT:")

    # Soft-delete
    for eid, reason in NOME_IT_DELETE:
        exists = conn.execute(
            "SELECT id FROM esercizi WHERE id = ? AND deleted_at IS NULL", (eid,)
        ).fetchone()
        if exists:
            conn.execute(
                "UPDATE esercizi SET deleted_at = ? WHERE id = ? AND deleted_at IS NULL",
                (NOW, eid)
            )
            print(f"    Soft-deleted id={eid} ({reason})")

    # Rename
    for eid, new_nome, reason in NOME_IT_RENAME:
        affected = conn.execute(
            "UPDATE esercizi SET nome = ? WHERE id = ? AND deleted_at IS NULL",
            (new_nome, eid)
        ).rowcount
        if affected:
            print(f"    Renamed id={eid} -> '{new_nome}' ({reason})")

    # ── 0D: Misclassificazioni ──
    print("\n  [0D] Category/pattern fixes:")
    fixed = 0
    for eid, new_cat, new_pat, reason in CATEGORY_FIXES:
        affected = conn.execute(
            "UPDATE esercizi SET categoria = ?, pattern_movimento = ? WHERE id = ? AND deleted_at IS NULL",
            (new_cat, new_pat, eid)
        ).rowcount
        if affected:
            fixed += 1
    print(f"    Fixed: {fixed}/{len(CATEGORY_FIXES)}")

    conn.commit()
    conn.close()
    print(f"\n  Done: {db_name}")


def sync_enrichment_prod_to_dev() -> None:
    """Copy enrichment data from crm.db to crm_dev.db for exercises missing in dev."""
    prod_path = os.path.join(BASE_DIR, "crm.db")
    dev_path = os.path.join(BASE_DIR, "crm_dev.db")

    if not os.path.exists(prod_path) or not os.path.exists(dev_path):
        print("\n  [0E] SKIP: both DBs needed for sync")
        return

    print(f"\n{'=' * 60}")
    print("  [0E] Sync enrichment prod -> dev")
    print(f"{'=' * 60}")

    prod_conn = sqlite3.connect(prod_path)
    prod_conn.row_factory = sqlite3.Row
    dev_conn = sqlite3.connect(dev_path)

    # Find exercises enriched in prod but not in dev (by nome_en match)
    prod_enriched = prod_conn.execute("""
        SELECT * FROM esercizi
        WHERE deleted_at IS NULL AND descrizione_anatomica IS NOT NULL AND descrizione_anatomica != ''
    """).fetchall()

    synced = 0
    for row in prod_enriched:
        nome_en = row["nome_en"]
        if not nome_en:
            continue

        # Check if dev has this exercise but unenriched
        dev_row = dev_conn.execute(
            "SELECT id, descrizione_anatomica FROM esercizi WHERE nome_en = ? AND deleted_at IS NULL",
            (nome_en,)
        ).fetchone()

        if not dev_row:
            continue
        if dev_row[1]:  # already enriched
            continue

        # Copy enrichment fields
        set_parts = []
        values = []
        for field in ENRICHMENT_FIELDS:
            set_parts.append(f"{field} = ?")
            values.append(row[field])
        values.append(dev_row[0])

        dev_conn.execute(
            f"UPDATE esercizi SET {', '.join(set_parts)} WHERE id = ?",
            values
        )
        synced += 1

    dev_conn.commit()
    prod_conn.close()
    dev_conn.close()
    print(f"  Synced: {synced} exercises from prod to dev")


def verify(db_path: str) -> None:
    """Post-fix verification."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    db_name = os.path.basename(db_path)

    print(f"\n  Verification: {db_name}")

    # Active exercises
    total = conn.execute("SELECT COUNT(*) FROM esercizi WHERE deleted_at IS NULL").fetchone()[0]
    print(f"    Active exercises: {total}")

    # Trailing punctuation
    punct = conn.execute("""
        SELECT COUNT(*) FROM esercizi
        WHERE deleted_at IS NULL AND (nome LIKE '%.' OR nome LIKE '%,' OR nome LIKE '%;')
    """).fetchone()[0]
    print(f"    Trailing punctuation: {punct} {'PASS' if punct == 0 else 'FAIL'}")

    # Duplicate nome_en
    dupes_en = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT LOWER(nome_en), COUNT(*) as cnt FROM esercizi
            WHERE deleted_at IS NULL AND nome_en IS NOT NULL
            GROUP BY LOWER(nome_en) HAVING cnt > 1
        )
    """).fetchone()[0]
    # Expected: 2 intentional (jump rope, bodyweight squat)
    print(f"    Duplicate nome_en groups: {dupes_en} (expected 2: jump rope, bodyweight squat)")

    # Duplicate nome
    dupes_it = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT nome, COUNT(*) as cnt FROM esercizi
            WHERE deleted_at IS NULL
            GROUP BY nome HAVING cnt > 1
        )
    """).fetchone()[0]
    print(f"    Duplicate nome groups: {dupes_it} {'PASS' if dupes_it == 0 else 'FAIL'}")

    # Compound+core
    cc = conn.execute("""
        SELECT COUNT(*) FROM esercizi
        WHERE deleted_at IS NULL AND categoria = 'compound' AND pattern_movimento = 'core'
    """).fetchone()[0]
    print(f"    Compound+core: {cc} (expected 2: kettlebell figure 8, pass between legs)")

    # Category distribution
    print("    Category distribution:")
    rows = conn.execute("""
        SELECT categoria, COUNT(*) FROM esercizi
        WHERE deleted_at IS NULL GROUP BY categoria ORDER BY COUNT(*) DESC
    """).fetchall()
    for cat, cnt in rows:
        print(f"      {cat}: {cnt}")

    conn.close()


if __name__ == "__main__":
    print("Exercise Data Quality Fix v2")
    print("=" * 60)

    for db_path in DBS:
        fix_database(db_path)

    sync_enrichment_prod_to_dev()

    print(f"\n{'=' * 60}")
    print("  POST-FIX VERIFICATION")
    print("=" * 60)

    for db_path in DBS:
        verify(db_path)

    # Cleanup temp file
    temp = os.path.join(os.path.dirname(__file__), "_temp_analyze.py")
    if os.path.exists(temp):
        os.remove(temp)

    print("\nAll done.")
