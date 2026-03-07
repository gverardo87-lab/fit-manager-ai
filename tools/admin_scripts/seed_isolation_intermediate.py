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
        "esecuzione": "Siediti sulla macchina adduttori con il sedile regolato in modo che le ginocchia siano allineate ai perni. Posiziona la gamba da allenare sulla leva esterna, con il cuscinetto a contatto con la coscia interna. Mantieni la schiena aderente allo schienale e il core contratto. Esegui l'adduzione portando la coscia verso il centro in modo controllato. Mantieni la contrazione al punto di massimo avvicinamento per 1-2 secondi. Ritorna lentamente alla posizione iniziale resistendo al carico.",
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
        "esecuzione": "Aggancia la caviglia appesantita al cavo basso e posizionati di fianco alla macchina con la gamba allenata lontana dalla puleggia. Stai in piedi con i piedi uniti e il peso corporeo sulla gamba d'appoggio. Abduce leggermente la gamba con il cavo, poi esegui l'adduzione portando la gamba verso e oltre la linea mediana del corpo. Mantieni il busto eretto e il core attivo per tutta l'esecuzione. Controlla il ritorno alla posizione di partenza.",
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
        "esecuzione": "Sdraiati prone su una panca piana con le gambe fuori dal bordo. Stringi il manubrio tra i piedi (dorso del piede inferiore, suola del piede superiore). Mantieni le cosce aderenti alla panca e il bacino neutro. Fletti le ginocchia portando i talloni verso i glutei in modo controllato. Mantieni la contrazione massima per 1 secondo. Abbassa lentamente il manubrio fino alla quasi estensione completa senza far toccare terra.",
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
        "esecuzione": "Inginocchiati su una superficie morbida con le caviglie bloccate sotto una sbarra bassa o tenute da un partner. Il corpo deve formare una linea retta da ginocchia a testa. Mantieni il core e i glutei contratti. Abbassa lentamente il busto verso il pavimento resistendo con i femorali (fase eccentrica di 3-5 secondi). Quando non riesci più a controllare il movimento, appoggiati con le mani e spingi per tornare alla posizione eretta. Ripeti focalizzandoti sulla fase di discesa.",
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
        "esecuzione": "Siediti sulla leg extension machine con la schiena aderente allo schienale. Posiziona un solo piede sotto il cuscinetto con il ginocchio flesso a 90°. Tieni l'altra gamba ferma o sollevata leggermente. Estendi il ginocchio fino alla quasi completa estensione contraendo il quadricipite. Mantieni la contrazione al top per 1-2 secondi con particolare focus sul vasto mediale. Abbassa il peso lentamente in 3 secondi. Completa tutte le ripetizioni su una gamba prima di passare all'altra.",
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
        "esecuzione": "Regola la puleggia del cavo ad altezza superiore alla testa e aggancia la corda doppia. Afferra i capi della corda con entrambe le mani in presa pronata, pollici rivolti verso di te. Fai un passo indietro per creare tensione con le braccia quasi tese. Tira la corda verso il viso portando le mani ai lati delle orecchie con i gomiti alti e aperti (90° rispetto al torso). Al punto finale, extraruota le spalle portando i pollici indietro. Ritorna lentamente alla posizione di partenza.",
    },
]

INSERT_SQL = """
INSERT INTO esercizi (
    id, nome, categoria, pattern_movimento, attrezzatura, difficolta,
    muscoli_primari, muscoli_secondari, in_subset,
    force_type, piano_movimento, catena_cinetica, tipo_contrazione,
    esecuzione, ore_recupero, is_builtin
) VALUES (
    :id, :nome, :categoria, :pattern_movimento, :attrezzatura, :difficolta,
    :muscoli_primari, :muscoli_secondari, :in_subset,
    :force_type, :piano_movimento, :catena_cinetica, :tipo_contrazione,
    :esecuzione, :ore_recupero, :is_builtin
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
