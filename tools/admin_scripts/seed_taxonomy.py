"""
Seed cataloghi tassonomia scientifica esercizi.

Popola le 3 tabelle catalogo:
  - muscoli (~52 muscoli anatomici, livello NSCA/ACSM)
  - articolazioni (~15 articolazioni principali)
  - condizioni_mediche (~30 condizioni rilevanti per l'allenamento)

Idempotente: controlla esistenza prima di inserire (match su nome_en).
Eseguire dalla root:
  python -m tools.admin_scripts.seed_taxonomy [--db dev|prod|both]
"""

import argparse
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# ================================================================
# MUSCOLI — 52 muscoli anatomici (NSCA/ACSM professional level)
# ================================================================
# Formato: (nome_it, nome_en, gruppo, regione)

MUSCLES = [
    # ── PETTO (chest) ──
    ("Grande pettorale (clavicolare)", "Pectoralis major (clavicular)", "chest", "upper_body"),
    ("Grande pettorale (sternale)", "Pectoralis major (sternal)", "chest", "upper_body"),
    ("Piccolo pettorale", "Pectoralis minor", "chest", "upper_body"),
    ("Dentato anteriore", "Serratus anterior", "chest", "upper_body"),

    # ── SCHIENA (back) ──
    ("Grande dorsale", "Latissimus dorsi", "lats", "upper_body"),
    ("Trapezio superiore", "Trapezius (upper)", "traps", "upper_body"),
    ("Trapezio medio", "Trapezius (middle)", "traps", "upper_body"),
    ("Trapezio inferiore", "Trapezius (lower)", "traps", "upper_body"),
    ("Romboidi", "Rhomboids", "back", "upper_body"),
    ("Grande rotondo", "Teres major", "back", "upper_body"),
    ("Piccolo rotondo", "Teres minor", "back", "upper_body"),
    ("Infraspinato", "Infraspinatus", "back", "upper_body"),
    ("Sopraspinato", "Supraspinatus", "shoulders", "upper_body"),
    ("Sottoscapolare", "Subscapularis", "back", "upper_body"),
    ("Erettori spinali", "Erector spinae", "back", "core"),

    # ── SPALLE (shoulders) ──
    ("Deltoide anteriore", "Anterior deltoid", "shoulders", "upper_body"),
    ("Deltoide laterale", "Lateral deltoid", "shoulders", "upper_body"),
    ("Deltoide posteriore", "Posterior deltoid", "shoulders", "upper_body"),

    # ── BRACCIA (arms) ──
    ("Bicipite brachiale", "Biceps brachii", "biceps", "upper_body"),
    ("Brachiale", "Brachialis", "biceps", "upper_body"),
    ("Brachioradiale", "Brachioradialis", "forearms", "upper_body"),
    ("Tricipite brachiale (capo lungo)", "Triceps brachii (long head)", "triceps", "upper_body"),
    ("Tricipite brachiale (capo laterale)", "Triceps brachii (lateral head)", "triceps", "upper_body"),
    ("Tricipite brachiale (capo mediale)", "Triceps brachii (medial head)", "triceps", "upper_body"),
    ("Flessori del polso", "Wrist flexors", "forearms", "upper_body"),
    ("Estensori del polso", "Wrist extensors", "forearms", "upper_body"),

    # ── CORE ──
    ("Retto dell'addome", "Rectus abdominis", "core", "core"),
    ("Obliquo esterno", "External oblique", "core", "core"),
    ("Obliquo interno", "Internal oblique", "core", "core"),
    ("Trasverso dell'addome", "Transversus abdominis", "core", "core"),
    ("Quadrato dei lombi", "Quadratus lumborum", "core", "core"),
    ("Multifido", "Multifidus", "core", "core"),

    # ── ANCHE E GLUTEI (hips & glutes) ──
    ("Grande gluteo", "Gluteus maximus", "glutes", "lower_body"),
    ("Medio gluteo", "Gluteus medius", "glutes", "lower_body"),
    ("Piccolo gluteo", "Gluteus minimus", "glutes", "lower_body"),
    ("Tensore della fascia lata", "Tensor fasciae latae", "glutes", "lower_body"),
    ("Ileopsoas", "Iliopsoas", "hip_flexors", "lower_body"),
    ("Piriforme", "Piriformis", "glutes", "lower_body"),

    # ── QUADRICIPITI (quadriceps) ──
    ("Retto femorale", "Rectus femoris", "quadriceps", "lower_body"),
    ("Vasto laterale", "Vastus lateralis", "quadriceps", "lower_body"),
    ("Vasto mediale", "Vastus medialis", "quadriceps", "lower_body"),
    ("Vasto intermedio", "Vastus intermedius", "quadriceps", "lower_body"),

    # ── POSTERIORI COSCIA (hamstrings) ──
    ("Bicipite femorale (capo lungo)", "Biceps femoris (long head)", "hamstrings", "lower_body"),
    ("Bicipite femorale (capo breve)", "Biceps femoris (short head)", "hamstrings", "lower_body"),
    ("Semitendinoso", "Semitendinosus", "hamstrings", "lower_body"),
    ("Semimembranoso", "Semimembranosus", "hamstrings", "lower_body"),

    # ── ADDUTTORI (adductors) ──
    ("Adduttore lungo", "Adductor longus", "adductors", "lower_body"),
    ("Adduttore grande", "Adductor magnus", "adductors", "lower_body"),
    ("Gracile", "Gracilis", "adductors", "lower_body"),

    # ── POLPACCI (calves) ──
    ("Gastrocnemio", "Gastrocnemius", "calves", "lower_body"),
    ("Soleo", "Soleus", "calves", "lower_body"),
    ("Tibiale anteriore", "Tibialis anterior", "calves", "lower_body"),
    ("Peronei", "Peroneus (fibularis)", "calves", "lower_body"),
]

# ================================================================
# ARTICOLAZIONI — 15 articolazioni principali
# ================================================================
# Formato: (nome_it, nome_en, tipo, regione)

JOINTS = [
    # ── Arto superiore ──
    ("Spalla (gleno-omerale)", "Shoulder (glenohumeral)", "ball_and_socket", "upper_body"),
    ("Acromion-clavicolare", "Acromioclavicular", "gliding", "upper_body"),
    ("Gomito", "Elbow", "hinge", "upper_body"),
    ("Polso", "Wrist", "condyloid", "upper_body"),

    # ── Colonna vertebrale ──
    ("Rachide cervicale", "Cervical spine", "pivot", "spine"),
    ("Rachide toracica", "Thoracic spine", "gliding", "spine"),
    ("Rachide lombare", "Lumbar spine", "gliding", "spine"),
    ("Sacro-iliaca", "Sacroiliac", "gliding", "spine"),

    # ── Arto inferiore ──
    ("Anca", "Hip", "ball_and_socket", "lower_body"),
    ("Ginocchio", "Knee", "hinge", "lower_body"),
    ("Caviglia (tibio-tarsica)", "Ankle (talocrural)", "hinge", "lower_body"),
    ("Sotto-astragalica", "Subtalar", "gliding", "lower_body"),

    # ── Scapola ──
    ("Scapolo-toracica", "Scapulothoracic", "gliding", "upper_body"),

    # ── Mano/Piede (aggregate) ──
    ("Metacarpo-falangee", "Metacarpophalangeal", "condyloid", "upper_body"),
    ("Metatarso-falangee", "Metatarsophalangeal", "condyloid", "lower_body"),
]

# ================================================================
# CONDIZIONI MEDICHE — 30 condizioni rilevanti per allenamento
# ================================================================
# Formato: (nome_it, nome_en, categoria, body_tags_json)

MEDICAL_CONDITIONS = [
    # ── Ortopediche — Colonna ──
    ("Ernia del disco lombare", "Lumbar disc herniation", "orthopedic",
     '["schiena", "lombare"]'),
    ("Ernia del disco cervicale", "Cervical disc herniation", "orthopedic",
     '["collo", "cervicale"]'),
    ("Scoliosi", "Scoliosis", "orthopedic",
     '["schiena"]'),
    ("Stenosi spinale", "Spinal stenosis", "orthopedic",
     '["schiena", "lombare"]'),
    ("Spondilolistesi", "Spondylolisthesis", "orthopedic",
     '["schiena", "lombare"]'),

    # ── Ortopediche — Spalla ──
    ("Conflitto sub-acromiale", "Shoulder impingement", "orthopedic",
     '["spalla"]'),
    ("Lesione cuffia dei rotatori", "Rotator cuff tear", "orthopedic",
     '["spalla"]'),
    ("Instabilita' gleno-omerale", "Glenohumeral instability", "orthopedic",
     '["spalla"]'),
    ("Capsulite adesiva (spalla congelata)", "Adhesive capsulitis (frozen shoulder)", "orthopedic",
     '["spalla"]'),

    # ── Ortopediche — Ginocchio ──
    ("Lesione LCA (crociato anteriore)", "ACL tear", "orthopedic",
     '["ginocchio"]'),
    ("Lesione menisco", "Meniscus tear", "orthopedic",
     '["ginocchio"]'),
    ("Sindrome femoro-rotulea", "Patellofemoral syndrome", "orthopedic",
     '["ginocchio"]'),
    ("Gonartrosi (artrosi ginocchio)", "Knee osteoarthritis", "orthopedic",
     '["ginocchio"]'),

    # ── Ortopediche — Anca ──
    ("Coxartrosi (artrosi anca)", "Hip osteoarthritis", "orthopedic",
     '["anca"]'),
    ("Conflitto femoro-acetabolare", "Femoroacetabular impingement", "orthopedic",
     '["anca"]'),

    # ── Ortopediche — Altre ──
    ("Epicondilite (gomito del tennista)", "Lateral epicondylitis (tennis elbow)", "orthopedic",
     '["gomito"]'),
    ("Sindrome del tunnel carpale", "Carpal tunnel syndrome", "orthopedic",
     '["polso"]'),
    ("Fascite plantare", "Plantar fasciitis", "orthopedic",
     '["caviglia", "piede"]'),
    ("Instabilita' di caviglia", "Ankle instability", "orthopedic",
     '["caviglia"]'),

    # ── Cardiovascolari ──
    ("Ipertensione arteriosa", "Hypertension", "cardiovascular",
     '["cardiovascolare"]'),
    ("Cardiopatia ischemica", "Coronary artery disease", "cardiovascular",
     '["cardiovascolare"]'),
    ("Insufficienza cardiaca compensata", "Compensated heart failure", "cardiovascular",
     '["cardiovascolare"]'),

    # ── Metaboliche ──
    ("Diabete tipo 2", "Type 2 diabetes", "metabolic",
     '["metabolico"]'),
    ("Osteoporosi", "Osteoporosis", "metabolic",
     '["schiena", "anca"]'),
    ("Obesita' (BMI > 35)", "Obesity (BMI > 35)", "metabolic",
     '["metabolico"]'),

    # ── Neurologiche ──
    ("Sciatica (radicolopatia lombare)", "Sciatica (lumbar radiculopathy)", "neurological",
     '["schiena", "lombare", "gamba"]'),
    ("Sindrome del piriforme", "Piriformis syndrome", "neurological",
     '["anca", "gamba"]'),

    # ── Respiratorie ──
    ("Asma da sforzo", "Exercise-induced asthma", "respiratory",
     '["respiratorio"]'),

    # ── Gravidanza / Speciali ──
    ("Gravidanza (2-3 trimestre)", "Pregnancy (2nd-3rd trimester)", "special",
     '["addome", "schiena"]'),
    ("Diastasi dei retti", "Diastasis recti", "special",
     '["addome"]'),
]


def seed_db(db_path: str) -> None:
    """Seed taxonomy catalogs into a single database."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return

    conn = sqlite3.connect(db_path)
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 60}")
    print(f"  Seeding taxonomy: {db_name}")
    print(f"{'=' * 60}")

    # Check tables exist
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]

    for t in ("muscoli", "articolazioni", "condizioni_mediche"):
        if t not in tables:
            print(f"  ERROR: table '{t}' missing — run migration first")
            conn.close()
            return

    # ── Muscoli ──
    existing = {r[0] for r in conn.execute("SELECT nome_en FROM muscoli").fetchall()}
    inserted = 0
    for nome, nome_en, gruppo, regione in MUSCLES:
        if nome_en not in existing:
            conn.execute(
                "INSERT INTO muscoli (nome, nome_en, gruppo, regione) VALUES (?, ?, ?, ?)",
                (nome, nome_en, gruppo, regione),
            )
            inserted += 1
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM muscoli").fetchone()[0]
    print(f"  Muscoli: {inserted} inserted, {total} total")

    # ── Articolazioni ──
    existing = {r[0] for r in conn.execute("SELECT nome_en FROM articolazioni").fetchall()}
    inserted = 0
    for nome, nome_en, tipo, regione in JOINTS:
        if nome_en not in existing:
            conn.execute(
                "INSERT INTO articolazioni (nome, nome_en, tipo, regione) VALUES (?, ?, ?, ?)",
                (nome, nome_en, tipo, regione),
            )
            inserted += 1
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM articolazioni").fetchone()[0]
    print(f"  Articolazioni: {inserted} inserted, {total} total")

    # ── Condizioni Mediche ──
    existing = {r[0] for r in conn.execute("SELECT nome_en FROM condizioni_mediche").fetchall()}
    inserted = 0
    for nome, nome_en, categoria, body_tags in MEDICAL_CONDITIONS:
        if nome_en not in existing:
            conn.execute(
                "INSERT INTO condizioni_mediche (nome, nome_en, categoria, body_tags) VALUES (?, ?, ?, ?)",
                (nome, nome_en, categoria, body_tags),
            )
            inserted += 1
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM condizioni_mediche").fetchone()[0]
    print(f"  Condizioni mediche: {inserted} inserted, {total} total")

    conn.close()


def verify(db_path: str) -> None:
    """Post-seed verification."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    db_name = os.path.basename(db_path)

    print(f"\n  Verification: {db_name}")

    # Muscoli by gruppo
    rows = conn.execute(
        "SELECT gruppo, COUNT(*) FROM muscoli GROUP BY gruppo ORDER BY gruppo"
    ).fetchall()
    print(f"    Muscoli per gruppo: {dict(rows)}")

    # Articolazioni by regione
    rows = conn.execute(
        "SELECT regione, COUNT(*) FROM articolazioni GROUP BY regione ORDER BY regione"
    ).fetchall()
    print(f"    Articolazioni per regione: {dict(rows)}")

    # Condizioni by categoria
    rows = conn.execute(
        "SELECT categoria, COUNT(*) FROM condizioni_mediche GROUP BY categoria ORDER BY categoria"
    ).fetchall()
    print(f"    Condizioni per categoria: {dict(rows)}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed taxonomy catalogs")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both",
                        help="Which database to seed")
    args = parser.parse_args()

    print("Taxonomy Catalog Seed")
    print("=" * 60)

    dbs = []
    if args.db in ("dev", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if args.db in ("prod", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm.db"))

    for db_path in dbs:
        seed_db(db_path)

    print(f"\n{'=' * 60}")
    print("  VERIFICATION")
    print("=" * 60)

    for db_path in dbs:
        verify(db_path)

    print("\nDone.")
