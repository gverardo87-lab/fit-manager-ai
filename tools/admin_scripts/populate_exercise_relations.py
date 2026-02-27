"""
Popola progressioni, regressioni e varianti per i 118 esercizi curati.

Catene propedeutiche definite manualmente da preparatore atletico.
Ogni catena e' ordinata dal piu' facile al piu' difficile:
  [beginner_id, intermediate_id, ..., advanced_id]

Lo script genera automaticamente relazioni bidirezionali:
  A -> B = progression  (B e' piu' difficile)
  B -> A = regression   (A e' piu' facile)

Idempotente (cancella e rigenera), dual-DB, dry-run obbligatorio prima dell'applicazione.
Eseguire dalla root:
  python -m tools.admin_scripts.populate_exercise_relations [--db dev|prod|both] [--dry-run]
"""

import argparse
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# ================================================================
# CATENE DI PROGRESSIONE
# ================================================================
# Ogni lista e' ordinata dal piu' facile al piu' difficile.
# Coppie adiacenti = progressione/regressione.
# Commenti: id -> nome esercizio per leggibilita'.

PROGRESSION_CHAINS: list[tuple[str, list[int]]] = [
    # ── PUSH ORIZZONTALE ──
    (
        "Push orizzontale — petto",
        # Pectoral Machine -> Croci Elastici -> Floor Press Alt
        # -> Floor Press DB -> Floor Press BB -> Croci Cavi -> Dip Anelli
        [45, 374, 361, 251, 252, 273, 290],
    ),
    (
        "Push orizzontale — planche",
        # Dip Anelli -> Planche Lean
        [290, 291],
    ),

    # ── PUSH VERTICALE ──
    (
        "Push verticale — spalle",
        # Shoulder Press Macchina -> Press Overhead Elastico
        # -> Clean & Press KB -> Spinta in Alto BB -> HSPU
        [62, 156, 144, 54, 289],
    ),
    (
        "Push verticale — tricipiti",
        # French Press Cavo -> Estensione Tricipiti OH
        [275, 106],
    ),
    (
        "Push verticale — potenza",
        # Thruster KB -> Battle Rope (entrambi intermediate, diverso focus)
        [147, 281],
    ),

    # ── PULL ORIZZONTALE ──
    (
        "Pull orizzontale — schiena",
        # Aperture Elastico -> Remata TRX -> Remata KB
        # -> Rematore Cavo -> Vogatore -> Front Lever
        [152, 148, 146, 1054, 161, 292],
    ),
    (
        "Pull orizzontale — avambracci",
        # Wrist Curl DB -> Curl Inverso BB
        [278, 277],
    ),
    # Pull orizzontale — bicipiti: Spider Curl Cavo standalone (unico curl nel subset)

    # ── PULL VERTICALE ──
    (
        "Pull verticale — dorsali",
        # Lat Pulldown Stretta -> Trazioni Anelli -> Muscle-Up
        [246, 250, 244],
    ),
    (
        "Pull verticale — trapezi (scrollate)",
        # Scrollate DB -> Face Pull Elastico -> Scrollate Trap Bar
        # -> Scrollate Multipower -> Sumo High Pull KB
        [158, 153, 229, 230, 654],
    ),
    (
        "Pull verticale — avanzati",
        # Rematore Smith Machine -> Skin the Cat
        [945, 294],
    ),

    # ── SQUAT ──
    (
        "Squat — quadricipiti",
        # Squat TRX -> Sumo Squat DB -> Front Squat 2KB -> Squat Anteriore BB
        [150, 223, 299, 2],
    ),
    (
        "Squat — polpacci",
        # Calf Raise BB -> Calf Raise Macchina
        [210, 212],
    ),
    (
        "Squat — adduttori",
        # Adduzione Elastico -> Adduzione Cavo Basso
        [222, 225],
    ),
    (
        "Squat — esplosivita'",
        # Burpee con Salto -> Shuttle Run (entrambi intermediate, intensita' crescente)
        [285, 287],
    ),
    # Squat — Alzata Turca KB con Affondo: standalone (complesso intermedio)

    # ── HINGE ──
    (
        "Hinge — catena posteriore",
        # Good Morning Banda -> Cable Pull Through -> Reverse Hyper
        # -> Stacco Trap Bar -> Stacco Classico
        [379, 26, 267, 30, 18],
    ),
    (
        "Hinge — hamstring avanzati",
        # Jefferson Curl -> Nordic Hamstring Curl
        [265, 266],
    ),
    (
        "Hinge — kettlebell",
        # Schiacciamento Palla -> KB Snatch
        [760, 297],
    ),

    # ── CORE ──
    (
        "Core — anti-estensione",
        # Crunch Cavi -> Dead Bug Peso -> Rollout BB -> Pike TRX -> Copenhagen Plank
        [120, 263, 383, 151, 221],
    ),
    (
        "Core — stabilita'",
        # Stir the Pot -> KB Figura Otto
        [264, 647],
    ),

    # ── ROTATION ──
    (
        "Rotation — anti-rotazione e rotazione",
        # Pallof Press -> Woodchop Cavo -> Russian Twist
        # -> Rotazione Landmine -> Turkish Get-Up
        [237, 238, 241, 133, 135],
    ),
    (
        "Rotation — polsi e halo",
        # Rotazione Polsi BB -> KB Halo
        [1080, 300],
    ),
    # Rotation — Med Ball Rotational Throw: collegato via cross-pattern a Russian Twist

    # ── CARRY ──
    (
        "Carry — presa e trasporto",
        # Dead Hang -> Farmer Walk DB -> Farmer Walk KB
        # -> Suitcase Carry -> Overhead Carry -> Bear Hug Carry
        [233, 232, 234, 137, 138, 235],
    ),
    (
        "Carry — polsi",
        # Curl Polsi Cavo -> Curl Pollici
        [447, 560],
    ),

    # ── WARMUP ──
    (
        "Warmup — attivazione",
        # Scapular Push-Up -> Crab Walk -> Clamshell -> Inchworm
        [314, 306, 302, 182],
    ),

    # ── MOBILITY ──
    (
        "Mobility — anca",
        # Squat Mobility Flow -> Rocking Hip Flexor -> CARs Anca -> Bretzel
        [338, 340, 332, 334],
    ),
    (
        "Mobility — spalle",
        # Mobilita Polsi -> Mobilita Overhead Bastone -> Shoulder Dislocates
        [205, 337, 200],
    ),
    (
        "Mobility — colonna",
        # Downward Dog to Cobra -> Jefferson Curl Mobilita
        [345, 335],
    ),
    # Mobility — CARs Cervicale: standalone

    # ── STRETCH ──
    (
        "Stretch — pettorali",
        # Stretching Pettorali Porta -> Allungamento Pettorali Dietro Testa
        [189, 397],
    ),
    (
        "Stretch — adduttori",
        # Stretching Adduttori in Piedi -> Adduttori (advanced)
        [325, 350],
    ),
    (
        "Stretch — spalle/braccia",
        # Stretching Spalle Cross-Body -> Stretching Tricipiti -> Stretching Bicipite Muro
        [191, 192, 322],
    ),
    # Stretch — Stretching Femorali Fascia: standalone (con attrezzo)
]

# ================================================================
# VARIANTI (stessa difficolta'/pattern, diversa attrezzatura/angolo)
# ================================================================
# Bidirezionali: (A, B) genera A->B variation e B->A variation.

VARIATION_PAIRS: list[tuple[int, int, str]] = [
    (232, 234, "Farmer Walk Manubri <-> Farmer Walk Kettlebell"),
    (251, 252, "Floor Press Manubri <-> Floor Press Bilanciere"),
    (158, 945, "Scrollate Manubri <-> Rematore Smith Machine (entrambi trapezi)"),
    (120, 263, "Crunch Cavi <-> Dead Bug Peso (anti-estensione beginner/intermediate)"),
    (241, 243, "Russian Twist <-> Med Ball Rotational Throw (rotazione esplosiva)"),
]

# ================================================================
# EXTRA: progressioni cross-pattern (collegano pattern diversi)
# ================================================================
# Queste sono progressioni dove l'esercizio avanzato cambia pattern
# ma e' la progressione naturale dal punto di vista propedeutico.

CROSS_PATTERN_PROGRESSIONS: list[tuple[int, int, str]] = [
    (241, 243, "Russian Twist -> Med Ball Rotational Throw (rotazione -> potenza)"),
]


def populate_relations(db_path: str, dry_run: bool) -> dict:
    """Popola esercizi_relazioni per il subset curato."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 70}")
    print(f"  Progressioni/Regressioni: {db_name}")
    if dry_run:
        print("  MODE: DRY RUN (nessuna modifica)")
    print(f"{'=' * 70}")

    # Carica nomi esercizi subset per validazione e report
    subset = {}
    for row in conn.execute(
        "SELECT id, nome, difficolta, pattern_movimento, attrezzatura "
        "FROM esercizi WHERE in_subset = 1 AND deleted_at IS NULL"
    ).fetchall():
        subset[row["id"]] = dict(row)

    print(f"\n  Esercizi nel subset: {len(subset)}")

    # Validazione: tutti gli ID nelle catene esistono nel subset
    all_chain_ids = set()
    errors = []
    for label, chain in PROGRESSION_CHAINS:
        for eid in chain:
            all_chain_ids.add(eid)
            if eid not in subset:
                errors.append(f"  ERRORE: id={eid} in '{label}' non nel subset!")

    for a, b, label in VARIATION_PAIRS:
        for eid in (a, b):
            all_chain_ids.add(eid)
            if eid not in subset:
                errors.append(f"  ERRORE: id={eid} in variante '{label}' non nel subset!")

    for a, b, label in CROSS_PATTERN_PROGRESSIONS:
        for eid in (a, b):
            all_chain_ids.add(eid)
            if eid not in subset:
                errors.append(f"  ERRORE: id={eid} in cross '{label}' non nel subset!")

    if errors:
        for e in errors:
            print(e)
        print("\n  ABORT: errori di validazione. Correggi gli ID.")
        conn.close()
        return {}

    # Cancella relazioni esistenti per esercizi del subset (idempotente)
    if not dry_run:
        subset_ids = list(subset.keys())
        placeholders = ",".join("?" * len(subset_ids))
        conn.execute(
            f"DELETE FROM esercizi_relazioni WHERE exercise_id IN ({placeholders})",
            subset_ids,
        )

    # Genera relazioni
    relations = []

    # ── Catene di progressione ──
    print("\n  --- CATENE DI PROGRESSIONE ---")
    for label, chain in PROGRESSION_CHAINS:
        if len(chain) < 2:
            continue
        print(f"\n  {label}:")
        for i in range(len(chain) - 1):
            a_id = chain[i]
            b_id = chain[i + 1]
            a_name = subset[a_id]["nome"]
            b_name = subset[b_id]["nome"]
            a_diff = subset[a_id]["difficolta"]
            b_diff = subset[b_id]["difficolta"]

            # A -> B = progression
            relations.append((a_id, b_id, "progression"))
            # B -> A = regression
            relations.append((b_id, a_id, "regression"))

            print(f"    {a_name:45s} [{a_diff:12s}] -> {b_name} [{b_diff}]")

    # ── Cross-pattern progressions ──
    if CROSS_PATTERN_PROGRESSIONS:
        print("\n  --- PROGRESSIONI CROSS-PATTERN ---")
        for a_id, b_id, label in CROSS_PATTERN_PROGRESSIONS:
            a_name = subset[a_id]["nome"]
            b_name = subset[b_id]["nome"]
            relations.append((a_id, b_id, "progression"))
            relations.append((b_id, a_id, "regression"))
            print(f"    {a_name} -> {b_name}  ({label})")

    # ── Varianti ──
    print("\n  --- VARIANTI ---")
    for a_id, b_id, label in VARIATION_PAIRS:
        a_name = subset[a_id]["nome"]
        b_name = subset[b_id]["nome"]
        relations.append((a_id, b_id, "variation"))
        relations.append((b_id, a_id, "variation"))
        print(f"    {a_name} <-> {b_name}")

    # Deduplica (stessa coppia potrebbe apparire in catene + varianti)
    seen = set()
    unique_relations = []
    for a, b, tipo in relations:
        key = (a, b, tipo)
        if key not in seen:
            seen.add(key)
            unique_relations.append((a, b, tipo))

    # Inserisci
    if not dry_run:
        for a, b, tipo in unique_relations:
            conn.execute(
                "INSERT INTO esercizi_relazioni (exercise_id, related_exercise_id, tipo_relazione) "
                "VALUES (?, ?, ?)",
                (a, b, tipo),
            )
        conn.commit()

    # ── Report ──
    progressions = sum(1 for _, _, t in unique_relations if t == "progression")
    regressions = sum(1 for _, _, t in unique_relations if t == "regression")
    variations = sum(1 for _, _, t in unique_relations if t == "variation")

    print(f"\n  {'=' * 50}")
    print(f"  RIEPILOGO")
    print(f"  {'=' * 50}")
    print(f"    Progressioni:  {progressions}")
    print(f"    Regressioni:   {regressions}")
    print(f"    Varianti:      {variations}")
    print(f"    TOTALE righe:  {len(unique_relations)}")

    # Esercizi coperti vs non coperti
    covered_ids = set()
    for a, b, _ in unique_relations:
        covered_ids.add(a)
        covered_ids.add(b)

    uncovered = set(subset.keys()) - covered_ids
    print(f"\n    Esercizi con relazioni: {len(covered_ids)}/{len(subset)}")
    if uncovered:
        print(f"    Esercizi SENZA relazioni ({len(uncovered)}):")
        for eid in sorted(uncovered):
            ex = subset[eid]
            print(f"      id={eid:4d} [{ex['pattern_movimento']:12s}] {ex['nome']}")

    if dry_run:
        print(f"\n  DRY RUN completato — nessuna modifica a {db_name}")
    else:
        print(f"\n  Commit eseguito su {db_name}")

    conn.close()

    return {
        "progressions": progressions,
        "regressions": regressions,
        "variations": variations,
        "total": len(unique_relations),
        "covered": len(covered_ids),
        "uncovered": len(uncovered),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Popola progressioni/regressioni/varianti per subset curato"
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

    print("Populate Exercise Relations")
    print("=" * 70)

    dbs: list[str] = []
    if args.db in ("dev", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if args.db in ("prod", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm.db"))

    for db_path in dbs:
        populate_relations(db_path, dry_run=args.dry_run)

    print("\nDone.")
