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

# ================================================================
# MUSCLE ACTIVATION — EMG-based approximate percentages
# ================================================================
# Fonti: Contreras 2010, Schoenfeld 2010, NSCA CSCS guidelines.
# Valori = % di MVC (massima contrazione volontaria) approssimati.
# Usati per pesare il contributo di ogni muscolo nel volume counting.

ACTIVATION_LEVELS: dict[str, dict[str, int]] = {
    "squat": {
        "quadriceps": 95, "glutes": 85, "hamstrings": 40,
        "calves": 30, "core": 50, "adductors": 35,
    },
    "hinge": {
        "hamstrings": 90, "glutes": 95, "back": 60,
        "core": 50, "forearms": 35, "lats": 30,
    },
    "push_h": {
        "chest": 90, "triceps": 70, "shoulders": 60,
    },
    "push_v": {
        "shoulders": 90, "triceps": 70, "traps": 40, "chest": 30,
    },
    "pull_h": {
        "back": 85, "lats": 75, "biceps": 60,
        "traps": 45, "forearms": 35,
    },
    "pull_v": {
        "lats": 90, "biceps": 65, "back": 50,
        "forearms": 35, "traps": 30,
    },
    "core": {
        "core": 90,
    },
    "rotation": {
        "core": 85, "shoulders": 35,
    },
    "carry": {
        "core": 85, "forearms": 75, "traps": 65,
        "shoulders": 30, "calves": 30,
    },
}

# Default per ruolo se non in lookup specifico
DEFAULT_ACTIVATION: dict[str, int] = {
    "primary": 80,
    "secondary": 40,
    "stabilizer": 25,
}

# ================================================================
# STABILIZER MUSCLES — gruppi che stabilizzano per pattern
# ================================================================
# Inseriti come ruolo "stabilizer" con attivazione bassa.
# Skip se il gruppo e' gia' primary o secondary per l'esercizio.

PATTERN_STABILIZERS: dict[str, list[str]] = {
    "squat":    ["core", "calves"],          # trunk + ankle stability
    "hinge":    ["core", "forearms"],         # trunk + grip
    "push_h":   ["core", "back"],            # trunk + rotator cuff
    "push_v":   ["core", "traps"],           # trunk + scapular upward rotation
    "pull_h":   ["core", "forearms"],         # anti-rotation + grip
    "pull_v":   ["core", "forearms"],         # anti-extension + grip
    "rotation": ["back"],                     # spinal stabilization
    "carry":    ["shoulders", "calves"],      # glenohumeral + gait
}

# ================================================================
# ROM TIPICO — gradi di Range of Motion per pattern x articolazione
# ================================================================
# Fonte: ACSM Guidelines for Exercise Testing and Prescription.
# Valori = ROM tipico in gradi durante esecuzione standard.

PATTERN_ROM: dict[str, dict[str, int]] = {
    "squat": {
        "Hip": 110, "Knee": 120, "Ankle (talocrural)": 30,
        "Lumbar spine": 5,
    },
    "hinge": {
        "Hip": 90, "Knee": 20, "Lumbar spine": 5,
    },
    "push_h": {
        "Shoulder (glenohumeral)": 90, "Elbow": 120,
        "Scapulothoracic": 15,
    },
    "push_v": {
        "Shoulder (glenohumeral)": 160, "Elbow": 140,
        "Scapulothoracic": 25,
    },
    "pull_h": {
        "Shoulder (glenohumeral)": 50, "Elbow": 130,
        "Scapulothoracic": 20,
    },
    "pull_v": {
        "Shoulder (glenohumeral)": 170, "Elbow": 140,
        "Scapulothoracic": 20,
    },
    "core": {
        "Lumbar spine": 10, "Thoracic spine": 5, "Hip": 10,
    },
    "rotation": {
        "Thoracic spine": 40, "Lumbar spine": 5, "Hip": 20,
    },
    "carry": {
        "Shoulder (glenohumeral)": 5, "Lumbar spine": 5,
        "Hip": 10, "Knee": 10,
    },
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

    # Reverse lookup: muscle_id → group name (for activation lookup)
    muscle_id_to_group: dict[int, str] = {}
    for m in muscle_rows:
        muscle_id_to_group[m["id"]] = m["gruppo"]

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
    stabilizer_inserts = 0
    joint_inserts = 0
    biomech_updates = 0

    for ex in exercises:
        eid = ex["id"]
        pattern = ex["pattern_movimento"]
        equip = ex["attrezzatura"]

        # --- 1. MUSCLE MAPPING (with activation % and stabilizers) ---
        assigned_groups: set[str] = set()

        # Primary muscles
        try:
            primary_groups = json.loads(ex["muscoli_primari"]) if ex["muscoli_primari"] else []
        except (json.JSONDecodeError, TypeError):
            primary_groups = []

        for group in primary_groups:
            assigned_groups.add(group)
            act = ACTIVATION_LEVELS.get(pattern, {}).get(group, DEFAULT_ACTIVATION["primary"])
            for muscle_id in muscles_by_group.get(group, []):
                conn.execute(
                    "INSERT INTO esercizi_muscoli (id_esercizio, id_muscolo, ruolo, attivazione) "
                    "VALUES (?, ?, ?, ?)",
                    (eid, muscle_id, "primary", act),
                )
                muscle_inserts += 1

        # Secondary muscles
        try:
            secondary_groups = json.loads(ex["muscoli_secondari"]) if ex["muscoli_secondari"] else []
        except (json.JSONDecodeError, TypeError):
            secondary_groups = []

        for group in secondary_groups:
            if group in primary_groups:
                continue
            assigned_groups.add(group)
            act = ACTIVATION_LEVELS.get(pattern, {}).get(group, DEFAULT_ACTIVATION["secondary"])
            for muscle_id in muscles_by_group.get(group, []):
                conn.execute(
                    "INSERT INTO esercizi_muscoli (id_esercizio, id_muscolo, ruolo, attivazione) "
                    "VALUES (?, ?, ?, ?)",
                    (eid, muscle_id, "secondary", act),
                )
                muscle_inserts += 1

        # Stabilizer muscles (skip groups already primary or secondary)
        for group in PATTERN_STABILIZERS.get(pattern, []):
            if group in assigned_groups:
                continue
            act = ACTIVATION_LEVELS.get(pattern, {}).get(group, DEFAULT_ACTIVATION["stabilizer"])
            for muscle_id in muscles_by_group.get(group, []):
                conn.execute(
                    "INSERT INTO esercizi_muscoli (id_esercizio, id_muscolo, ruolo, attivazione) "
                    "VALUES (?, ?, ?, ?)",
                    (eid, muscle_id, "stabilizer", act),
                )
                muscle_inserts += 1
                stabilizer_inserts += 1

        # --- 2. JOINT MAPPING (with ROM degrees) ---
        seen_joints: set[int] = set()

        if pattern in PATTERN_JOINTS:
            rom_map = PATTERN_ROM.get(pattern, {})
            for joint_name, ruolo in PATTERN_JOINTS[pattern]:
                jid = joint_id_map.get(joint_name)
                if jid and jid not in seen_joints:
                    rom = rom_map.get(joint_name)
                    conn.execute(
                        "INSERT INTO esercizi_articolazioni "
                        "(id_esercizio, id_articolazione, ruolo, rom_gradi) "
                        "VALUES (?, ?, ?, ?)",
                        (eid, jid, ruolo, rom),
                    )
                    seen_joints.add(jid)
                    joint_inserts += 1
        else:
            # Warmup/stretch/mobility: infer from muscle groups (no ROM data)
            all_groups = set(primary_groups + secondary_groups)
            for group in all_groups:
                for joint_name, ruolo in MUSCLE_GROUP_JOINTS.get(group, []):
                    jid = joint_id_map.get(joint_name)
                    if jid and jid not in seen_joints:
                        conn.execute(
                            "INSERT INTO esercizi_articolazioni "
                            "(id_esercizio, id_articolazione, ruolo, rom_gradi) "
                            "VALUES (?, ?, ?, ?)",
                            (eid, jid, ruolo, None),
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

        # Preserva piano_movimento se gia' impostato a un valore diverso
        # dal default pattern-based (es. fix manuali per "frontal")
        current_piano = conn.execute(
            "SELECT piano_movimento FROM esercizi WHERE id = ?", (eid,)
        ).fetchone()["piano_movimento"]
        if current_piano and current_piano != piano:
            piano = current_piano  # preserva il valore manuale

        conn.execute(
            "UPDATE esercizi SET catena_cinetica = ?, piano_movimento = ?, tipo_contrazione = ? WHERE id = ?",
            (catena, piano, contrazione, eid),
        )
        biomech_updates += 1

    conn.commit()
    conn.close()

    print(f"\n  Results ({db_name}):")
    print(f"    Muscle mappings inserted: {muscle_inserts} (incl. {stabilizer_inserts} stabilizers)")
    print(f"    Joint mappings inserted: {joint_inserts}")
    print(f"    Biomechanics updated: {biomech_updates}")


def verify(db_path: str) -> None:
    """Post-populate verification."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
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

    # Activation coverage
    act_stats = conn.execute("""
        SELECT ruolo, ROUND(AVG(attivazione), 1) as avg_act,
               MIN(attivazione) as min_act, MAX(attivazione) as max_act,
               COUNT(*) as total,
               SUM(CASE WHEN attivazione IS NOT NULL THEN 1 ELSE 0 END) as filled
        FROM esercizi_muscoli
        WHERE id_esercizio IN (SELECT id FROM esercizi WHERE in_subset = 1)
        GROUP BY ruolo
    """).fetchall()
    print("    Activation coverage:")
    for row in act_stats:
        print(f"      {row['ruolo']:12s} avg={row['avg_act']}% "
              f"range=[{row['min_act']}-{row['max_act']}] "
              f"filled={row['filled']}/{row['total']}")

    # Joint role distribution
    roles = conn.execute("""
        SELECT ruolo, COUNT(*) FROM esercizi_articolazioni
        WHERE id_esercizio IN (SELECT id FROM esercizi WHERE in_subset = 1)
        GROUP BY ruolo
    """).fetchall()
    print(f"    Joint roles: {dict(roles)}")

    # ROM coverage
    rom_stats = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN rom_gradi IS NOT NULL THEN 1 ELSE 0 END) as filled,
               ROUND(AVG(rom_gradi), 1) as avg_rom
        FROM esercizi_articolazioni
        WHERE id_esercizio IN (SELECT id FROM esercizi WHERE in_subset = 1)
    """).fetchone()
    print(f"    ROM coverage: {rom_stats['filled']}/{rom_stats['total']} "
          f"(avg={rom_stats['avg_rom']} deg)")

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
