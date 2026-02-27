"""
Popola la tassonomia scientifica per il subset di esercizi.

Per i ~118 esercizi con in_subset=1:
  1. esercizi_muscoli: da muscoli_primari/secondari JSON → muscoli normalizzati
  2. esercizi_articolazioni: da pattern_movimento → articolazioni coinvolte
  3. colonne biomeccanica: catena_cinetica, piano_movimento, tipo_contrazione

Idempotente: pulisce e rigenera i mapping ad ogni esecuzione.
Eseguire dalla root:
  python -m tools.admin_scripts.populate_taxonomy [--db dev|prod|both]
"""

import argparse
import json
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# ================================================================
# JOINT MAPPING — pattern_movimento → articolazioni coinvolte
# ================================================================
# nome_en della tabella articolazioni → ruolo (agonist, stabilizer)

PATTERN_JOINTS: dict[str, list[tuple[str, str]]] = {
    "squat": [
        ("Hip", "agonist"),
        ("Knee", "agonist"),
        ("Ankle (talocrural)", "agonist"),
        ("Lumbar spine", "stabilizer"),
    ],
    "hinge": [
        ("Hip", "agonist"),
        ("Knee", "stabilizer"),
        ("Lumbar spine", "stabilizer"),
    ],
    "push_h": [
        ("Shoulder (glenohumeral)", "agonist"),
        ("Elbow", "agonist"),
        ("Scapulothoracic", "stabilizer"),
    ],
    "push_v": [
        ("Shoulder (glenohumeral)", "agonist"),
        ("Elbow", "agonist"),
        ("Scapulothoracic", "agonist"),
    ],
    "pull_h": [
        ("Shoulder (glenohumeral)", "agonist"),
        ("Elbow", "agonist"),
        ("Scapulothoracic", "agonist"),
    ],
    "pull_v": [
        ("Shoulder (glenohumeral)", "agonist"),
        ("Elbow", "agonist"),
        ("Scapulothoracic", "agonist"),
    ],
    "core": [
        ("Lumbar spine", "agonist"),
        ("Thoracic spine", "stabilizer"),
        ("Hip", "stabilizer"),
    ],
    "rotation": [
        ("Thoracic spine", "agonist"),
        ("Lumbar spine", "stabilizer"),
        ("Hip", "stabilizer"),
    ],
    "carry": [
        ("Shoulder (glenohumeral)", "stabilizer"),
        ("Lumbar spine", "stabilizer"),
        ("Hip", "stabilizer"),
        ("Knee", "stabilizer"),
    ],
}

# Warmup/Stretch/Mobility: infer joints from muscle groups
MUSCLE_GROUP_JOINTS: dict[str, list[tuple[str, str]]] = {
    "quadriceps": [("Knee", "agonist"), ("Hip", "agonist")],
    "hamstrings": [("Knee", "agonist"), ("Hip", "agonist")],
    "glutes": [("Hip", "agonist")],
    "calves": [("Ankle (talocrural)", "agonist")],
    "adductors": [("Hip", "agonist")],
    "hip_flexors": [("Hip", "agonist")],
    "chest": [("Shoulder (glenohumeral)", "agonist"), ("Scapulothoracic", "stabilizer")],
    "back": [("Shoulder (glenohumeral)", "agonist"), ("Scapulothoracic", "agonist")],
    "lats": [("Shoulder (glenohumeral)", "agonist"), ("Scapulothoracic", "agonist")],
    "shoulders": [("Shoulder (glenohumeral)", "agonist"), ("Scapulothoracic", "stabilizer")],
    "traps": [("Scapulothoracic", "agonist"), ("Cervical spine", "stabilizer")],
    "biceps": [("Elbow", "agonist")],
    "triceps": [("Elbow", "agonist")],
    "forearms": [("Wrist", "agonist"), ("Elbow", "stabilizer")],
    "core": [("Lumbar spine", "agonist"), ("Thoracic spine", "stabilizer")],
}

# ================================================================
# BIOMECHANICS — pattern → catena_cinetica, piano, contrazione
# ================================================================

PATTERN_BIOMECHANICS: dict[str, dict[str, str]] = {
    "squat": {
        "catena_cinetica": "closed",
        "piano_movimento": "sagittal",
        "tipo_contrazione": "dynamic",
    },
    "hinge": {
        "catena_cinetica": "closed",
        "piano_movimento": "sagittal",
        "tipo_contrazione": "dynamic",
    },
    "push_h": {
        "catena_cinetica": "open",
        "piano_movimento": "sagittal",
        "tipo_contrazione": "dynamic",
    },
    "push_v": {
        "catena_cinetica": "open",
        "piano_movimento": "sagittal",
        "tipo_contrazione": "dynamic",
    },
    "pull_h": {
        "catena_cinetica": "open",
        "piano_movimento": "sagittal",
        "tipo_contrazione": "dynamic",
    },
    "pull_v": {
        "catena_cinetica": "open",
        "piano_movimento": "sagittal",
        "tipo_contrazione": "dynamic",
    },
    "core": {
        "catena_cinetica": "closed",
        "piano_movimento": "multi",
        "tipo_contrazione": "isometric",
    },
    "rotation": {
        "catena_cinetica": "open",
        "piano_movimento": "transverse",
        "tipo_contrazione": "dynamic",
    },
    "carry": {
        "catena_cinetica": "closed",
        "piano_movimento": "sagittal",
        "tipo_contrazione": "isometric",
    },
    "warmup": {
        "catena_cinetica": "closed",
        "piano_movimento": "multi",
        "tipo_contrazione": "dynamic",
    },
    "stretch": {
        "catena_cinetica": "open",
        "piano_movimento": "multi",
        "tipo_contrazione": "isometric",
    },
    "mobility": {
        "catena_cinetica": "open",
        "piano_movimento": "multi",
        "tipo_contrazione": "dynamic",
    },
}

# Equipment overrides for catena_cinetica
# bodyweight exercises in push patterns are usually closed chain (pushup)
CLOSED_CHAIN_OVERRIDES: dict[tuple[str, str], str] = {
    ("push_h", "bodyweight"): "closed",   # pushup
    ("push_v", "bodyweight"): "closed",   # handstand pushup, pike pushup
    ("pull_v", "bodyweight"): "closed",   # pullup, chinup
    ("core", "bodyweight"): "closed",     # plank, crunch
}


def populate_db(db_path: str) -> None:
    """Populate taxonomy mappings for subset exercises."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 60}")
    print(f"  Populating taxonomy: {db_name}")
    print(f"{'=' * 60}")

    # Load subset exercises
    exercises = conn.execute("""
        SELECT id, nome, muscoli_primari, muscoli_secondari,
               pattern_movimento, attrezzatura, categoria
        FROM esercizi
        WHERE in_subset = 1 AND deleted_at IS NULL
        ORDER BY id
    """).fetchall()

    if not exercises:
        print("  No subset exercises found (in_subset=1)")
        conn.close()
        return

    print(f"  Subset exercises: {len(exercises)}")

    # Load muscle catalog (gruppo → list of muscle IDs)
    muscle_rows = conn.execute("SELECT id, nome_en, gruppo FROM muscoli").fetchall()
    muscles_by_group: dict[str, list[int]] = {}
    for m in muscle_rows:
        muscles_by_group.setdefault(m["gruppo"], []).append(m["id"])
    print(f"  Muscle catalog: {len(muscle_rows)} muscles in {len(muscles_by_group)} groups")

    # Load joint catalog (nome_en → ID)
    joint_rows = conn.execute("SELECT id, nome_en FROM articolazioni").fetchall()
    joint_id_map: dict[str, int] = {j["nome_en"]: j["id"] for j in joint_rows}
    print(f"  Joint catalog: {len(joint_rows)} joints")

    # ── Clean existing mappings for subset ──
    subset_ids = [ex["id"] for ex in exercises]
    placeholders = ",".join("?" * len(subset_ids))

    for table in ("esercizi_muscoli", "esercizi_articolazioni"):
        conn.execute(
            f"DELETE FROM {table} WHERE id_esercizio IN ({placeholders})",
            subset_ids,
        )
    conn.commit()
    print("  Cleaned existing mappings")

    # ── Populate ──
    muscle_inserts = 0
    joint_inserts = 0
    biomech_updates = 0

    for ex in exercises:
        eid = ex["id"]
        pattern = ex["pattern_movimento"]
        equip = ex["attrezzatura"]

        # --- 1. MUSCLE MAPPING ---
        # Primary muscles
        try:
            primary_groups = json.loads(ex["muscoli_primari"]) if ex["muscoli_primari"] else []
        except (json.JSONDecodeError, TypeError):
            primary_groups = []

        for group in primary_groups:
            for muscle_id in muscles_by_group.get(group, []):
                conn.execute(
                    "INSERT INTO esercizi_muscoli (id_esercizio, id_muscolo, ruolo) VALUES (?, ?, ?)",
                    (eid, muscle_id, "primary"),
                )
                muscle_inserts += 1

        # Secondary muscles
        try:
            secondary_groups = json.loads(ex["muscoli_secondari"]) if ex["muscoli_secondari"] else []
        except (json.JSONDecodeError, TypeError):
            secondary_groups = []

        for group in secondary_groups:
            # Skip if already primary (avoid duplicates)
            if group in primary_groups:
                continue
            for muscle_id in muscles_by_group.get(group, []):
                conn.execute(
                    "INSERT INTO esercizi_muscoli (id_esercizio, id_muscolo, ruolo) VALUES (?, ?, ?)",
                    (eid, muscle_id, "secondary"),
                )
                muscle_inserts += 1

        # --- 2. JOINT MAPPING ---
        seen_joints: set[int] = set()

        if pattern in PATTERN_JOINTS:
            # Use pattern-based rules
            for joint_name, ruolo in PATTERN_JOINTS[pattern]:
                jid = joint_id_map.get(joint_name)
                if jid and jid not in seen_joints:
                    conn.execute(
                        "INSERT INTO esercizi_articolazioni (id_esercizio, id_articolazione, ruolo) VALUES (?, ?, ?)",
                        (eid, jid, ruolo),
                    )
                    seen_joints.add(jid)
                    joint_inserts += 1
        else:
            # Warmup/stretch/mobility: infer from muscle groups
            all_groups = set(primary_groups + secondary_groups)
            for group in all_groups:
                for joint_name, ruolo in MUSCLE_GROUP_JOINTS.get(group, []):
                    jid = joint_id_map.get(joint_name)
                    if jid and jid not in seen_joints:
                        conn.execute(
                            "INSERT INTO esercizi_articolazioni (id_esercizio, id_articolazione, ruolo) VALUES (?, ?, ?)",
                            (eid, jid, ruolo),
                        )
                        seen_joints.add(jid)
                        joint_inserts += 1

        # --- 3. BIOMECHANICS COLUMNS ---
        bio = PATTERN_BIOMECHANICS.get(pattern, {})
        catena = bio.get("catena_cinetica", "open")
        piano = bio.get("piano_movimento", "multi")
        contrazione = bio.get("tipo_contrazione", "dynamic")

        # Equipment override for catena_cinetica
        override_key = (pattern, equip)
        if override_key in CLOSED_CHAIN_OVERRIDES:
            catena = CLOSED_CHAIN_OVERRIDES[override_key]

        conn.execute(
            "UPDATE esercizi SET catena_cinetica = ?, piano_movimento = ?, tipo_contrazione = ? WHERE id = ?",
            (catena, piano, contrazione, eid),
        )
        biomech_updates += 1

    conn.commit()
    conn.close()

    print(f"\n  Results ({db_name}):")
    print(f"    Muscle mappings inserted: {muscle_inserts}")
    print(f"    Joint mappings inserted: {joint_inserts}")
    print(f"    Biomechanics updated: {biomech_updates}")


def verify(db_path: str) -> None:
    """Post-populate verification."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    db_name = os.path.basename(db_path)

    print(f"\n  Verification: {db_name}")

    # Exercises with muscles
    with_muscles = conn.execute("""
        SELECT COUNT(DISTINCT id_esercizio) FROM esercizi_muscoli
        WHERE id_esercizio IN (SELECT id FROM esercizi WHERE in_subset = 1)
    """).fetchone()[0]

    # Exercises with joints
    with_joints = conn.execute("""
        SELECT COUNT(DISTINCT id_esercizio) FROM esercizi_articolazioni
        WHERE id_esercizio IN (SELECT id FROM esercizi WHERE in_subset = 1)
    """).fetchone()[0]

    # Biomechanics coverage
    with_bio = conn.execute("""
        SELECT COUNT(*) FROM esercizi
        WHERE in_subset = 1 AND catena_cinetica IS NOT NULL
    """).fetchone()[0]

    subset_total = conn.execute(
        "SELECT COUNT(*) FROM esercizi WHERE in_subset = 1 AND deleted_at IS NULL"
    ).fetchone()[0]

    print(f"    Subset size: {subset_total}")
    print(f"    With muscles: {with_muscles}/{subset_total}")
    print(f"    With joints: {with_joints}/{subset_total}")
    print(f"    With biomechanics: {with_bio}/{subset_total}")

    # Avg muscles per exercise
    avg_muscles = conn.execute("""
        SELECT ROUND(AVG(cnt), 1) FROM (
            SELECT COUNT(*) as cnt FROM esercizi_muscoli
            WHERE id_esercizio IN (SELECT id FROM esercizi WHERE in_subset = 1)
            GROUP BY id_esercizio
        )
    """).fetchone()[0]
    print(f"    Avg muscles per exercise: {avg_muscles}")

    # Avg joints per exercise
    avg_joints = conn.execute("""
        SELECT ROUND(AVG(cnt), 1) FROM (
            SELECT COUNT(*) as cnt FROM esercizi_articolazioni
            WHERE id_esercizio IN (SELECT id FROM esercizi WHERE in_subset = 1)
            GROUP BY id_esercizio
        )
    """).fetchone()[0]
    print(f"    Avg joints per exercise: {avg_joints}")

    # Muscle role distribution
    roles = conn.execute("""
        SELECT ruolo, COUNT(*) FROM esercizi_muscoli
        WHERE id_esercizio IN (SELECT id FROM esercizi WHERE in_subset = 1)
        GROUP BY ruolo
    """).fetchall()
    print(f"    Muscle roles: {dict(roles)}")

    # Joint role distribution
    roles = conn.execute("""
        SELECT ruolo, COUNT(*) FROM esercizi_articolazioni
        WHERE id_esercizio IN (SELECT id FROM esercizi WHERE in_subset = 1)
        GROUP BY ruolo
    """).fetchall()
    print(f"    Joint roles: {dict(roles)}")

    # Biomechanics distribution
    for col in ("catena_cinetica", "piano_movimento", "tipo_contrazione"):
        dist = conn.execute(f"""
            SELECT {col}, COUNT(*) FROM esercizi
            WHERE in_subset = 1 AND {col} IS NOT NULL
            GROUP BY {col}
        """).fetchall()
        print(f"    {col}: {dict(dist)}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate taxonomy mappings for subset")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both",
                        help="Which database to process")
    args = parser.parse_args()

    print("Taxonomy Population — Subset Only")
    print("=" * 60)

    dbs = []
    if args.db in ("dev", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if args.db in ("prod", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm.db"))

    for db_path in dbs:
        populate_db(db_path)

    print(f"\n{'=' * 60}")
    print("  VERIFICATION")
    print("=" * 60)

    for db_path in dbs:
        verify(db_path)

    print("\nDone.")
