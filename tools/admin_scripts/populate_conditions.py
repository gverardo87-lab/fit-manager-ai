"""
Popola esercizi_condizioni — mapping deterministico esercizio → condizioni mediche.

Per i 118 esercizi con in_subset=1:
  1. Scansiona campo 'controindicazioni' (JSON array di frasi testuali IT)
  2. Keyword matching → condizioni mediche dal catalogo (30 condizioni)
  3. Pattern-based rules → condizioni aggiuntive (cardiaco, metabolico)
  4. Severita': avoid (controindicazione diretta), caution (rischio, adattare)

Zero Ollama. 100% deterministico e replicabile.

Idempotente: pulisce e rigenera ad ogni esecuzione.
Eseguire dalla root:
  python -m tools.admin_scripts.populate_conditions [--db dev|prod|both] [--dry-run]
"""

import argparse
import json
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# ================================================================
# KEYWORD → CONDITION MAPPING
# ================================================================
# Ogni entry: (keyword_list, condition_id, severita, nota)
# keyword_list: basta che UNA keyword sia presente nella stringa
# Le keyword sono lowercase, il matching e' case-insensitive

KEYWORD_RULES: list[tuple[list[str], int, str, str]] = [
    # ── SCHIENA / LOMBARE ──
    (["ernia", "hernia discale"], 1, "avoid",
     "Carico assiale e flessione lombare controindicati con ernia discale."),
    (["lombalgia", "mal di schiena", "lombare"], 1, "caution",
     "Monitorare carico assiale. Evitare flessione lombare sotto carico."),
    (["scoliosi"], 3, "caution",
     "Adattare carichi. Evitare sovraccarico asimmetrico."),
    (["stenosi spinale"], 4, "avoid",
     "Compressione spinale: evitare estensione e carico assiale pesante."),
    (["spondilolistesi"], 5, "avoid",
     "Instabilita' vertebrale: evitare iperestensione e carico assiale."),

    # ── CERVICALE / COLLO ──
    (["cervicale", "collo", "cervicobrachialgia"], 2, "caution",
     "Proteggere il rachide cervicale. Evitare compressione assiale."),

    # ── SPALLA ──
    (["subacromiale", "impingement"], 6, "avoid",
     "Conflitto sub-acromiale: evitare elevazione sopra la testa sotto carico."),
    (["cuffia dei rotatori", "cuffia rotatori"], 7, "avoid",
     "Lesione cuffia: evitare rotazione esterna sotto carico."),
    (["instabilit" + chr(224) + " scapolare", "instabilit" + chr(224) + " gleno"], 8, "caution",
     "Instabilita' gleno-omerale: ridurre ROM e carico."),
    (["spalla congelata", "capsulite"], 9, "avoid",
     "Capsulite adesiva: evitare forzare ROM."),
    (["spalla", "spalle"], 6, "caution",
     "Attenzione alla spalla: verificare ROM e dolore."),

    # ── GINOCCHIO ──
    (["crociato", "lca"], 10, "avoid",
     "Lesione LCA: evitare taglio, rotazione e carico in valgismo."),
    (["menisco"], 11, "avoid",
     "Lesione menisco: evitare flessione profonda sotto carico."),
    (["femoro-rotulea", "rotula", "sindrome femoro"], 12, "caution",
     "Sindrome femoro-rotulea: limitare flessione oltre 90 gradi."),
    (["artrosi ginocchio", "artrosi grave del ginocchio",
      "artrosi grave delle ginocchia", "gonartrosi"], 13, "caution",
     "Artrosi ginocchio: ridurre carico e impatto."),
    (["ginocchio", "ginocchia"], 10, "caution",
     "Attenzione al ginocchio: monitorare allineamento e carico."),

    # ── ANCA ──
    (["artrosi anca", "coxartrosi", "artrosi severa dell'anca",
      "artrosi dell'anca"], 14, "caution",
     "Coxartrosi: ridurre ROM e impatto."),
    (["conflitto femoro-acetabolare", "impingement anca"], 15, "caution",
     "FAI: evitare flessione anca profonda."),
    (["anca"], 14, "caution",
     "Attenzione all'anca: monitorare ROM e dolore."),

    # ── GOMITO ──
    (["epicondilite", "gomito del tennista"], 16, "avoid",
     "Epicondilite: evitare presa stretta e movimenti di polso."),
    (["gomito"], 16, "caution",
     "Attenzione al gomito: monitorare carico in presa e flessione."),

    # ── POLSO ──
    (["tunnel carpale"], 17, "caution",
     "Sindrome tunnel carpale: evitare flessione/estensione polso sotto carico."),
    (["polso", "avambraccio", "frattura al polso", "frattura al radio"], 17, "caution",
     "Attenzione al polso: adattare presa e ROM."),

    # ── CAVIGLIA / PIEDE ──
    (["fascite plantare", "plantare"], 18, "caution",
     "Fascite plantare: evitare impatto ripetuto."),
    (["caviglia", "achille"], 19, "caution",
     "Instabilita' caviglia: attenzione a equilibrio e impatto."),

    # ── CARDIOVASCOLARE ──
    (["ipertensione", "pressione sanguigna"], 20, "caution",
     "Ipertensione: evitare Valsalva e carichi massimali."),
    (["cardiopatia", "cardiaci gravi", "cardiovascol"], 21, "caution",
     "Patologia cardiovascolare: monitorare FC e intensita'."),
    (["problemi cardiaci"], 20, "caution",
     "Problemi cardiaci: evitare sforzi massimali e apnea prolungata."),

    # ── METABOLICO ──
    (["osteoporosi"], 24, "caution",
     "Osteoporosi: evitare impatto e flessione vertebrale sotto carico."),

    # ── NEUROLOGICO ──
    (["sciatica", "radicolopatia", "nervo sciatico"], 26, "caution",
     "Sciatica: evitare flessione lombare sotto carico."),
    (["piriforme"], 27, "caution",
     "Sindrome piriforme: evitare flessione + rotazione anca."),

    # ── SPECIAL ──
    (["gravidanza"], 29, "caution",
     "Gravidanza: evitare posizioni supine e carichi addominali diretti."),
    (["diastasi"], 30, "avoid",
     "Diastasi retti: evitare crunch, sit-up e pressione intra-addominale."),
]

# ── Pattern-based rules (NO keyword match needed) ──
# Queste regole si applicano in base a categoria/pattern, non al testo controindicazioni

PATTERN_CONDITION_RULES: list[tuple[dict, int, str, str]] = [
    # Compound pesanti + condizione cardiaca → caution
    ({"categoria": "compound"}, 20, "caution",
     "Esercizio compound: monitorare FC e pressione in soggetti ipertesi."),
    ({"categoria": "compound"}, 21, "caution",
     "Esercizio compound ad alto carico: attenzione con cardiopatia."),
    # Cardio + condizione cardiaca
    ({"categoria": "cardio"}, 20, "caution",
     "Attivita' cardio: monitorare FC in soggetti ipertesi."),
    ({"categoria": "cardio"}, 28, "caution",
     "Cardio: attenzione con asma da sforzo, preriscaldamento adeguato."),
    # Squat/hinge pesanti + osteoporosi
    ({"pattern_movimento": "squat"}, 24, "caution",
     "Squat: carico assiale benefico ma moderare intensita' con osteoporosi."),
    ({"pattern_movimento": "hinge"}, 24, "caution",
     "Hinge: carico assiale benefico ma moderare con osteoporosi."),
    # Core + diastasi
    ({"pattern_movimento": "core"}, 30, "caution",
     "Core: evitare crunch e aumento pressione intra-addominale con diastasi."),
    # Core + gravidanza
    ({"pattern_movimento": "core"}, 29, "caution",
     "Core: adattare in gravidanza, evitare posizione supina prolungata."),
]


def _normalize(text: str) -> str:
    """Normalizza testo per matching: lowercase, strip."""
    return text.lower().strip()


def _match_keywords(text: str, keywords: list[str]) -> bool:
    """Ritorna True se almeno una keyword e' presente nel testo."""
    text_lower = _normalize(text)
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False


def process_db(db_path: str, dry_run: bool = False) -> dict:
    """Processa un singolo database."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Carica esercizi subset
    exercises = conn.execute(
        "SELECT id, nome, controindicazioni, categoria, pattern_movimento "
        "FROM esercizi WHERE in_subset = 1 AND deleted_at IS NULL"
    ).fetchall()

    # Carica condizioni per verifica
    conditions = {
        row[0]: row[1]
        for row in conn.execute("SELECT id, nome FROM condizioni_mediche").fetchall()
    }

    stats = {"exercises": len(exercises), "mappings": 0, "exercises_with_conditions": 0}

    if not dry_run:
        # Pulisci mapping esistenti per subset
        subset_ids = [e[0] for e in exercises]
        if subset_ids:
            placeholders = ",".join("?" * len(subset_ids))
            conn.execute(
                f"DELETE FROM esercizi_condizioni WHERE id_esercizio IN ({placeholders})",
                subset_ids,
            )

    all_mappings: list[tuple[int, int, str, str]] = []

    for ex_id, ex_nome, ex_controindicazioni, ex_cat, ex_pattern in exercises:
        exercise_conditions: dict[int, tuple[str, str]] = {}  # condition_id → (severita, nota)

        # 1. Parse controindicazioni JSON
        contra_texts: list[str] = []
        if ex_controindicazioni:
            try:
                parsed = json.loads(ex_controindicazioni)
                if isinstance(parsed, list):
                    contra_texts = [str(t) for t in parsed]
            except (json.JSONDecodeError, TypeError):
                pass

        # 2. Keyword matching su ogni testo controindicazione
        full_text = " ".join(contra_texts)
        for keywords, cond_id, severity, nota in KEYWORD_RULES:
            if cond_id not in conditions:
                continue
            if _match_keywords(full_text, keywords):
                # Prendi la severita' piu' alta (avoid > caution > modify)
                existing = exercise_conditions.get(cond_id)
                if existing is None or (severity == "avoid" and existing[0] != "avoid"):
                    exercise_conditions[cond_id] = (severity, nota)

        # 3. Pattern-based rules
        for rule_filter, cond_id, severity, nota in PATTERN_CONDITION_RULES:
            if cond_id not in conditions:
                continue
            match = True
            for key, val in rule_filter.items():
                actual = {"categoria": ex_cat, "pattern_movimento": ex_pattern}.get(key)
                if actual != val:
                    match = False
                    break
            if match:
                existing = exercise_conditions.get(cond_id)
                if existing is None:
                    exercise_conditions[cond_id] = (severity, nota)

        # Accumula mapping
        for cond_id, (sev, nota) in exercise_conditions.items():
            all_mappings.append((ex_id, cond_id, sev, nota))

        if exercise_conditions:
            stats["exercises_with_conditions"] += 1

    stats["mappings"] = len(all_mappings)

    if not dry_run and all_mappings:
        conn.executemany(
            "INSERT INTO esercizi_condizioni (id_esercizio, id_condizione, severita, nota) "
            "VALUES (?, ?, ?, ?)",
            all_mappings,
        )
        conn.commit()

    conn.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Popola esercizi_condizioni (deterministico)")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both")
    parser.add_argument("--dry-run", action="store_true", help="Simula senza scrivere")
    args = parser.parse_args()

    dbs = []
    if args.db in ("dev", "both"):
        dbs.append(("DEV", os.path.join(BASE_DIR, "crm_dev.db")))
    if args.db in ("prod", "both"):
        dbs.append(("PROD", os.path.join(BASE_DIR, "crm.db")))

    for label, path in dbs:
        if not os.path.exists(path):
            print(f"  SKIP {label}: {path} non trovato")
            continue
        print(f"\n=== {label} ({path}) ===")
        stats = process_db(path, dry_run=args.dry_run)
        mode = "DRY RUN" if args.dry_run else "SCRITTO"
        print(f"  Esercizi processati: {stats['exercises']}")
        print(f"  Esercizi con condizioni: {stats['exercises_with_conditions']}")
        print(f"  Mapping totali: {stats['mappings']} [{mode}]")


if __name__ == "__main__":
    main()
