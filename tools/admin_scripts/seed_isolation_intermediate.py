"""
Seed 6 nuovi esercizi isolation/intermediate per colmare i pattern mancanti:
adductor (2), leg_curl (2), leg_extension (1), face_pull (1).
IDs 1106-1111. Dual-DB (crm.db + crm_dev.db).
"""
import sqlite3
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

EXERCISES = [
    # ── ADDUCTOR intermediate (2) ──────────────────────────────────
    {
        "id": 1106,
        "nome": "Adduzione alla Macchina Unilaterale",
        "categoria": "isolation",
        "pattern_movimento": "adductor",
        "attrezzatura": "machine",
        "difficolta": "intermediate",
        "muscoli_primari": '["adductors"]',
        "muscoli_secondari": '["glutes", "hip_flexors"]',
        "in_subset": 1,
        "force_type": "pull",
        "piano_movimento": "frontal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "concentric",
    },
    {
        "id": 1107,
        "nome": "Adduzione al Cavo con Caviglia Appesantita",
        "categoria": "isolation",
        "pattern_movimento": "adductor",
        "attrezzatura": "cable",
        "difficolta": "intermediate",
        "muscoli_primari": '["adductors"]',
        "muscoli_secondari": '["glutes", "core"]',
        "in_subset": 1,
        "force_type": "pull",
        "piano_movimento": "frontal",
        "catena_cinetica": "open",
        "tipo_contrazione": "concentric",
    },
    # ── LEG CURL intermediate (2) ───────────────────────────────────
    {
        "id": 1108,
        "nome": "Leg Curl con Manubrio Prono",
        "categoria": "isolation",
        "pattern_movimento": "leg_curl",
        "attrezzatura": "dumbbell",
        "difficolta": "intermediate",
        "muscoli_primari": '["hamstrings"]',
        "muscoli_secondari": '["glutes", "calves"]',
        "in_subset": 1,
        "force_type": "pull",
        "piano_movimento": "sagittal",
        "catena_cinetica": "open",
        "tipo_contrazione": "concentric",
    },
    {
        "id": 1109,
        "nome": "Nordic Curl Assistito",
        "categoria": "isolation",
        "pattern_movimento": "leg_curl",
        "attrezzatura": "bodyweight",
        "difficolta": "intermediate",
        "muscoli_primari": '["hamstrings"]',
        "muscoli_secondari": '["glutes", "calves", "core"]',
        "in_subset": 1,
        "force_type": "pull",
        "piano_movimento": "sagittal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "eccentric",
    },
    # ── LEG EXTENSION intermediate (1) ─────────────────────────────
    {
        "id": 1110,
        "nome": "Leg Extension Unilaterale",
        "categoria": "isolation",
        "pattern_movimento": "leg_extension",
        "attrezzatura": "machine",
        "difficolta": "intermediate",
        "muscoli_primari": '["quadriceps"]',
        "muscoli_secondari": '["hip_flexors"]',
        "in_subset": 1,
        "force_type": "push",
        "piano_movimento": "sagittal",
        "catena_cinetica": "open",
        "tipo_contrazione": "concentric",
    },
    # ── FACE PULL intermediate (1) ──────────────────────────────────
    {
        "id": 1111,
        "nome": "Face Pull con Corda ad Alta Puleggia",
        "categoria": "isolation",
        "pattern_movimento": "face_pull",
        "attrezzatura": "cable",
        "difficolta": "intermediate",
        "muscoli_primari": '["shoulders", "traps"]',
        "muscoli_secondari": '["back", "biceps"]',
        "in_subset": 1,
        "force_type": "pull",
        "piano_movimento": "transverse",
        "catena_cinetica": "open",
        "tipo_contrazione": "concentric",
    },
]

INSERT_SQL = """
INSERT INTO esercizi (
    id, nome, categoria, pattern_movimento, attrezzatura, difficolta,
    muscoli_primari, muscoli_secondari, in_subset,
    force_type, piano_movimento, catena_cinetica, tipo_contrazione,
    ore_recupero, is_builtin
) VALUES (
    :id, :nome, :categoria, :pattern_movimento, :attrezzatura, :difficolta,
    :muscoli_primari, :muscoli_secondari, :in_subset,
    :force_type, :piano_movimento, :catena_cinetica, :tipo_contrazione,
    :ore_recupero, :is_builtin
)
"""

_ORE_RECUPERO = {"beginner": 24, "intermediate": 36, "advanced": 48}
for ex in EXERCISES:
    ex.setdefault("ore_recupero", _ORE_RECUPERO[ex["difficolta"]])
    ex.setdefault("is_builtin", 1)

DBS = ["crm.db", "crm_dev.db"]


def seed(db_name: str) -> None:
    path = os.path.join(BASE_DIR, db_name)
    conn = sqlite3.connect(path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    inserted = 0
    skipped = 0
    for ex in EXERCISES:
        existing = conn.execute("SELECT id FROM esercizi WHERE id=?", (ex["id"],)).fetchone()
        if existing:
            skipped += 1
            continue
        conn.execute(INSERT_SQL, ex)
        inserted += 1

    conn.commit()
    conn.close()
    print(f"  {db_name}: {inserted} inseriti, {skipped} già presenti")


if __name__ == "__main__":
    print(f"Seed {len(EXERCISES)} esercizi isolation/intermediate (IDs {EXERCISES[0]['id']}–{EXERCISES[-1]['id']})")
    for db in DBS:
        seed(db)
    print("Done.")
