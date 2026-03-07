"""
Seed 12 nuovi esercizi cardio (7 beginner + 5 advanced).
IDs 1094-1105. Dual-DB (crm.db + crm_dev.db).
"""
import sqlite3
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

EXERCISES = [
    # ── BEGINNER (7) ──────────────────────────────────────────────
    {
        "id": 1094,
        "nome": "Jumping Jacks",
        "categoria": "cardio",
        "pattern_movimento": "squat",
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "muscoli_primari": '["quadriceps", "glutes"]',
        "muscoli_secondari": '["calves", "shoulders"]',
        "in_subset": 1,
        "force_type": "push",
        "piano_movimento": "frontal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "dynamic",
    },
    {
        "id": 1095,
        "nome": "Marcia ad Alta Ginocchia",
        "categoria": "cardio",
        "pattern_movimento": "core",
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "muscoli_primari": '["hip_flexors", "core"]',
        "muscoli_secondari": '["quadriceps", "glutes"]',
        "in_subset": 1,
        "force_type": "pull",
        "piano_movimento": "sagittal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "dynamic",
    },
    {
        "id": 1096,
        "nome": "Step Aerobics",
        "categoria": "cardio",
        "pattern_movimento": "squat",
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "muscoli_primari": '["quadriceps", "glutes"]',
        "muscoli_secondari": '["calves", "hamstrings"]',
        "in_subset": 1,
        "force_type": "push",
        "piano_movimento": "sagittal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "dynamic",
    },
    {
        "id": 1097,
        "nome": "Nordic Walking",
        "categoria": "cardio",
        "pattern_movimento": "core",
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "muscoli_primari": '["glutes", "hamstrings"]',
        "muscoli_secondari": '["core", "shoulders", "triceps"]',
        "in_subset": 1,
        "force_type": "push",
        "piano_movimento": "sagittal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "dynamic",
    },
    {
        "id": 1098,
        "nome": "Nuoto a Crawl Lento",
        "categoria": "cardio",
        "pattern_movimento": "pull_h",
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "muscoli_primari": '["lats", "shoulders"]',
        "muscoli_secondari": '["core", "glutes", "triceps"]',
        "in_subset": 1,
        "force_type": "pull",
        "piano_movimento": "multi",
        "catena_cinetica": "open",
        "tipo_contrazione": "dynamic",
    },
    {
        "id": 1099,
        "nome": "Camminata in Acqua",
        "categoria": "cardio",
        "pattern_movimento": "squat",
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "muscoli_primari": '["quadriceps", "glutes"]',
        "muscoli_secondari": '["hamstrings", "calves", "core"]',
        "in_subset": 1,
        "force_type": "push",
        "piano_movimento": "sagittal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "dynamic",
    },
    {
        "id": 1100,
        "nome": "Lateral Shuffle",
        "categoria": "cardio",
        "pattern_movimento": "squat",
        "attrezzatura": "bodyweight",
        "difficolta": "beginner",
        "muscoli_primari": '["glutes", "adductors"]',
        "muscoli_secondari": '["quadriceps", "hamstrings", "calves"]',
        "in_subset": 1,
        "force_type": "push",
        "piano_movimento": "frontal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "dynamic",
    },
    # ── ADVANCED (5) ──────────────────────────────────────────────
    {
        "id": 1101,
        "nome": "HIIT Sprint sul Tappeto",
        "categoria": "cardio",
        "pattern_movimento": "squat",
        "attrezzatura": "machine",
        "difficolta": "advanced",
        "muscoli_primari": '["quadriceps", "hamstrings", "glutes"]',
        "muscoli_secondari": '["calves", "core", "hip_flexors"]',
        "in_subset": 1,
        "force_type": "push",
        "piano_movimento": "sagittal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "dynamic",
    },
    {
        "id": 1102,
        "nome": "Vogatore Intervalli 500m",
        "categoria": "cardio",
        "pattern_movimento": "pull_h",
        "attrezzatura": "machine",
        "difficolta": "advanced",
        "muscoli_primari": '["lats", "glutes", "hamstrings"]',
        "muscoli_secondari": '["core", "biceps", "shoulders", "quadriceps"]',
        "in_subset": 1,
        "force_type": "pull",
        "piano_movimento": "sagittal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "dynamic",
    },
    {
        "id": 1103,
        "nome": "Tabata Assault Bike",
        "categoria": "cardio",
        "pattern_movimento": "squat",
        "attrezzatura": "machine",
        "difficolta": "advanced",
        "muscoli_primari": '["quadriceps", "glutes"]',
        "muscoli_secondari": '["hamstrings", "calves", "shoulders", "core"]',
        "in_subset": 1,
        "force_type": "push",
        "piano_movimento": "sagittal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "dynamic",
    },
    {
        "id": 1104,
        "nome": "Circuit Cardio AMRAP",
        "categoria": "cardio",
        "pattern_movimento": "core",
        "attrezzatura": "bodyweight",
        "difficolta": "advanced",
        "muscoli_primari": '["core", "glutes", "quadriceps"]',
        "muscoli_secondari": '["hamstrings", "shoulders", "calves"]',
        "in_subset": 1,
        "force_type": "push",
        "piano_movimento": "multi",
        "catena_cinetica": "closed",
        "tipo_contrazione": "dynamic",
    },
    {
        "id": 1105,
        "nome": "Fartlek (Corsa con Variazioni di Ritmo)",
        "categoria": "cardio",
        "pattern_movimento": "squat",
        "attrezzatura": "bodyweight",
        "difficolta": "advanced",
        "muscoli_primari": '["quadriceps", "hamstrings", "glutes"]',
        "muscoli_secondari": '["calves", "core", "hip_flexors"]',
        "in_subset": 1,
        "force_type": "push",
        "piano_movimento": "sagittal",
        "catena_cinetica": "closed",
        "tipo_contrazione": "dynamic",
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

# Aggiungi ore_recupero e is_builtin a tutti gli esercizi
_ORE_RECUPERO = {
    "beginner": 24,
    "intermediate": 36,
    "advanced": 48,
}
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
    print(f"Seed {len(EXERCISES)} esercizi cardio (IDs {EXERCISES[0]['id']}–{EXERCISES[-1]['id']})")
    for db in DBS:
        seed(db)
    print("Done.")
