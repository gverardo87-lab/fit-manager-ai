"""
Fase 1: Correzione nomi italiani esercizi FDB.

Strategia a 3 livelli:
  1A. Dizionario manuale (~100 nomi critici) — zero Ollama, garantiti corretti
  1B. Ri-traduzione Ollama (~640 nomi) con prompt fitness-aware rigoroso
  1C. Post-processing: term substitutions di sicurezza + report CSV

Idempotente: sicuro da rieseguire.
Eseguire dalla root:
  python -m tools.admin_scripts.fix_exercise_names [--dry-run] [--db dev|prod|both]
"""

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone

import requests

# ================================================================
# CONFIG
# ================================================================

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma2:9b"
OLLAMA_TIMEOUT = 60
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

# ================================================================
# 1A. DIZIONARIO MANUALE — Correzioni garantite (ID → nome corretto)
# ================================================================
# Esercizi con traduzioni completamente sbagliate.
# Queste sovrascrivono QUALSIASI traduzione Ollama.

MANUAL_OVERRIDES = {
    # ── Kettlebell exercises (Manico da Cucina / manubrio → Kettlebell) ──
    352: "Mulino Avanzato con Kettlebell",                          # Advanced Kettlebell Windmill
    645: "Arnold Press con Kettlebell",                             # Kettlebell Arnold Press
    646: "Dead Clean con Kettlebell",                               # Kettlebell Dead Clean
    648: "Hang Clean con Kettlebell",                               # Kettlebell Hang Clean
    649: "Stacco Rumeno Monopodalico con Kettlebell",               # Kettlebell One-Legged Deadlift
    654: "Sumo High Pull con Kettlebell",                           # Kettlebell Sumo High Pull
    749: "Clean and Jerk con Kettlebell a Un Braccio",              # One-Arm Kettlebell Clean and Jerk
    750: "Floor Press con Kettlebell a Un Braccio",                 # One-Arm Kettlebell Floor Press
    751: "Jerk con Kettlebell a Un Braccio",                        # One-Arm Kettlebell Jerk
    752: "Military Press Laterale con Kettlebell a Un Braccio",     # One-Arm Kettlebell Military Press To The Side
    753: "Para Press con Kettlebell a Un Braccio",                  # One-Arm Kettlebell Para Press
    755: "Push Press con Kettlebell a Un Braccio",                  # One-Arm Kettlebell Push Press
    756: "Split Jerk con Kettlebell a Un Braccio",                  # One-Arm Kettlebell Split Jerk
    757: "Split Snatch con Kettlebell a Un Braccio",                # One-Arm Kettlebell Split Snatch
    777: "Clean a Palmo Aperto con Kettlebell",                     # Open Palm Kettlebell Clean
    761: "Clean a Palmo Aperto con Kettlebell a Un Braccio",        # One-Arm Open Palm Kettlebell Clean
    748: "Clean con Kettlebell a Un Braccio",                       # One-Arm Kettlebell Clean
    1047: "Clean con Due Kettlebell",                               # Two-Arm Kettlebell Clean
    1048: "Jerk con Due Kettlebell",                                # Two-Arm Kettlebell Jerk
    1049: "Military Press con Due Kettlebell",                      # Two-Arm Kettlebell Military Press
    1050: "Rematore con Due Kettlebell",                            # Two-Arm Kettlebell Row
    511: "Hang Clean Alternato con Due Kettlebell",                 # Double Kettlebell Alternating Hang Clean
    512: "Jerk con Due Kettlebell",                                 # Double Kettlebell Jerk
    514: "Snatch con Due Kettlebell",                               # Double Kettlebell Snatch
    555: "Floor Press a Braccio Singolo con Kettlebell (ROM Esteso)", # Extended Range One-Arm Kettlebell Floor Press
    652: "Press da Seduto con Kettlebell",                          # Kettlebell Seated Press
    653: "Seesaw Press con Kettlebell",                             # Kettlebell Seesaw Press
    363: "Press Alternato con Kettlebell",                          # Alternating Kettlebell Press
    364: "Rematore Alternato con Kettlebell",                       # Alternating Kettlebell Row

    # ── Clean exercises (Pulizia/Slegamento/Sfilata → Girata/Clean) ──
    473: "Girata",                                                  # Clean
    474: "Stacco per Girata",                                       # Clean Deadlift (already renamed in Phase 0)
    475: "Tirata per Girata",                                       # Clean Pull
    476: "Scrollate per Girata",                                    # Clean Shrug
    477: "Girata dai Blocchi",                                      # Clean from Blocks
    421: "Girata Invertita dalla Sospensione",                      # Bottoms-Up Clean From The Hang Position
    522: "Girata con Manubrio",                                     # Dumbbell Clean
    596: "Hang Clean sotto le Ginocchia",                           # Hang Clean - Below the Knees
    802: "Power Clean dai Blocchi",                                 # Power Clean from Blocks
    936: "Hang Power Clean alla Smith Machine",                     # Smith Machine Hang Power Clean
    958: "Split Clean",                                             # Split Clean
    362: "Hang Clean Alternato",                                    # Alternating Hang Clean

    # ── Snatch exercises (Strappato/Stracco → Strappo/Snatch) ──
    597: "Hang Snatch",                                             # Hang Snatch
    598: "Hang Snatch sotto le Ginocchia",                          # Hang Snatch - Below Knees
    601: "Heaving Snatch Balance",                                  # Heaving Snatch Balance
    733: "Muscle Snatch",                                           # Muscle Snatch
    805: "Power Snatch",                                            # Power Snatch
    806: "Power Snatch dai Blocchi",                                # Power Snatch from Blocks
    947: "Snatch Balance",                                          # Snatch Balance
    948: "Stacco per Strappo",                                      # Snatch Deadlift
    949: "Tirata per Strappo",                                      # Snatch Pull
    950: "Scrollate per Strappo",                                   # Snatch Shrug
    951: "Strappo dai Blocchi",                                     # Snatch from Blocks
    961: "Split Snatch",                                            # Split Snatch

    # ── Jerk exercises (Stacco/gettaggio → Slancio/Jerk) ──
    641: "Jerk Balance",                                            # Jerk Balance
    642: "Jerk Dip Squat",                                          # Jerk Dip Squat
    803: "Power Jerk",                                              # Power Jerk
    959: "Split Jerk",                                              # Split Jerk
    963: "Squat Jerk",                                              # Squat Jerk

    # ── Press exercises (Stacco/Panca piana → Press corretto) ──
    359: "Shoulder Press Alternato ai Cavi",                        # Alternating Cable Shoulder Press
    369: "Pressa Anti-Gravità",                                     # Anti-Gravity Press
    390: "Shoulder Press con Bilanciere",                           # Barbell Shoulder Press
    399: "Panca Piana - Powerlifting",                              # Bench Press - Powerlifting
    411: "Bent Press",                                              # Bent Press
    414: "Board Press",                                             # Board Press
    428: "Bradford Press",                                          # Bradford/Rocky Presses
    431: "Chest Press ai Cavi",                                     # Cable Chest Press
    479: "Floor Press con Manubri Presa Stretta",                   # Close-Grip Dumbbell Press
    481: "Press con EZ-Bar Presa Stretta",                          # Close-Grip EZ-Bar Press
    507: "Distensioni Declinata alla Smith Machine",                # Decline Smith Press
    530: "Shoulder Press con Manubrio a Un Braccio",                # Dumbbell One-Arm Shoulder Press
    770: "Floor Press a Un Braccio",                                # One Arm Floor Press
    891: "See-Saw Press (Press Alternato Laterale)",                # See-Saw Press
    935: "Distensioni Declinata alla Smith Machine",                # Smith Machine Decline Press
    941: "Shoulder Press alla Smith Machine",                       # Smith Machine Overhead Shoulder Press
    970: "Press con Bilanciere Dietro il Collo",                    # Standing Barbell Press Behind Neck
    976: "Chest Press ai Cavi in Piedi",                            # Standing Cable Chest Press
    980: "Press con Manubri in Piedi",                              # Standing Dumbbell Press
    1001: "Press con Manubrio a Un Braccio in Piedi (Palmo Interno)", # Standing Palm-In One-Arm Dumbbell Press
    1002: "Press con Manubri in Piedi (Palmi Interni)",             # Standing Palms-In Dumbbell Press
    707: "Triceps Press Presa Stretta al Mento",                    # Lying Close-Grip Barbell Triceps Press To Chin

    # ── Shrug exercises (Strappo → Scrollate) ──
    391: "Scrollate con Bilanciere Dietro la Schiena",              # Barbell Shrug Behind The Back
    439: "Scrollate ai Cavi",                                       # Cable Shrug
    534: "Scrollate con Manubri",                                   # Dumbbell Shrug
    395: "Scrollate con Bilanciere",                                # Barbell Squat → actually no this is "Squat alla barra"

    # ── Duplicate nome IT fixes ──
    # crm.db duplicates
    440: "Curl al Cavo su Panca Scott",                             # Cable Preacher Curl (was "Curl al bilanciere")
    518: "Drag Curl",                                               # Drag Curl (was "Curl al bilanciere")
    531: "Estensione Tricipiti con Manubrio a Un Braccio",          # Dumbbell One-Arm Triceps Extension
    999: "Estensione Tricipiti con Manubrio a Un Braccio in Piedi", # Standing One-Arm Dumbbell Triceps Extension
    425: "Box Squat con Bande Elastiche",                           # Box Squat with Bands
    964: "Squat con Bande Elastiche",                               # Squat with Bands
    540: "Squat con Manubri",                                       # Dumbbell Squat
    798: "Plié Squat con Manubrio",                                 # Plie Dumbbell Squat

    # crm_dev.db duplicates
    595: "Allungamento degli Ischiocrurale",                        # Hamstring Stretch (was "quadricipiti")
    819: "Allungamento dei Quadricipiti",                           # Quad Stretch
    1064: "Jump Squat con Peso",                                    # Weighted Jump Squat
    1067: "Squat con Peso",                                         # Weighted Squat

    # ── Other specific fixes ──
    353: "Air Bike (Crunch Bicicletta)",                            # Air Bike
    354: "Allungamento Quadricipiti a Quattro Zampe",               # All Fours Quad Stretch
    367: "Caviglia sul Ginocchio",                                  # Ankle On The Knee
    370: "Giro del Mondo",                                          # Around The Worlds
    375: "Trascinamento all'Indietro",                              # Backward Drag
    378: "Leg Curl con Palla Svizzera",                             # Ball Leg Curl
    386: "Hack Squat con Bilanciere",                               # Barbell Hack Squat
    394: "Squat con Bilanciere",                                    # Barbell Squat
    395: "Squat con Bilanciere sulla Panca",                        # Barbell Squat To A Bench
    527: "Pronazione con Manubrio da Sdraiato",                     # Dumbbell Lying Pronation
    564: "Curl Inclinato con Manubri su Panca",                     # Flexor Incline Dumbbell Curls
    614: "Estensione Tricipiti con Bilanciere su Panca Inclinata",  # Incline Barbell Triceps Extension
    716: "Squat alla Macchina da Sdraiato",                         # Lying Machine Squat
    808: "Preacher Curl a Martello con Manubri",                    # Preacher Hammer Dumbbell Curl
    1034: "Spaccata Laterale (Straddle)",                           # The Straddle
    1070: "Pullover Declinato con Bilanciere Presa Larga",          # Wide-Grip Decline Barbell Pullover
}

# Remove duplicate: 395 was accidentally listed twice
# Barbell Shrug → keep in shrug section with correct name
MANUAL_OVERRIDES[395] = "Squat con Bilanciere sulla Panca"

# ================================================================
# 1B. PROMPT OLLAMA — Regole rigorose per traduzione fitness
# ================================================================

OLLAMA_SYSTEM = """Sei un traduttore specializzato in terminologia fitness e weightlifting.
Traduci i nomi degli esercizi dall'inglese all'italiano come vengono usati nelle palestre italiane.

REGOLE TASSATIVE:
- Kettlebell resta "Kettlebell" (MAI "manico", "manico da cucina", "manubrio pesante")
- Dumbbell = "Manubrio"
- Barbell = "Bilanciere"
- EZ-Bar = "EZ-Bar" o "Barra EZ"
- Clean = "Girata" (sollevamento olimpico, MAI "pulizia" o "slegamento")
- Snatch = "Strappo" (sollevamento olimpico, MAI "stracco" o "strappato")
- Jerk = "Jerk" o "Slancio" (MAI "stacco" o "gettaggio")
- Press (overhead/shoulder) = "Press" o "Distensioni" (MAI "stacco")
- Bench Press = "Panca Piana" (SOLO per bench press, non per altri press)
- Floor Press = "Floor Press" (a terra)
- Deadlift = "Stacco da Terra" o "Stacco"
- Squat = "Squat" (universale in Italia)
- Shrug = "Scrollate"
- Row = "Rematore"
- Pull-Up = "Trazioni alla Sbarra"
- Push-Up = "Flessioni"
- Plank = "Plank"
- Lunge = "Affondo"
- Curl = "Curl"
- Fly/Flye = "Croci"
- Raise (lateral/front) = "Alzate" o "Elevazioni"
- Pullover = "Pullover"
- Triceps Extension = "Estensione Tricipiti"
- Skull Crusher = "French Press"
- Cable = "Cavo" o "Cavi"
- Machine = "Macchina"
- Smith Machine = "Smith Machine" o "Multipower"
- Preacher = "Panca Scott"
- Incline = "Inclinato/a"
- Decline = "Declinato/a"
- Seated = "da Seduto"
- Standing = "in Piedi"
- Lying = "da Sdraiato"
- One-Arm/Single-Arm = "a Un Braccio"
- Alternate/Alternating = "Alternato"
- Stretch = "Allungamento"
- SMR/Self-Myofascial Release = "Auto-Massaggio"
- Foam Roller = "Foam Roller"

Rispondi SOLO con il nome tradotto. Max 80 caratteri. Nessuna spiegazione."""


def translate_name_ollama(name_en: str) -> str | None:
    """Traduci nome esercizio via Ollama con prompt migliorato."""
    prompt = f"Traduci il nome di questo esercizio fitness in italiano:\n{name_en}"
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "system": OLLAMA_SYSTEM,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 60},
            },
            timeout=OLLAMA_TIMEOUT,
        )
        if resp.status_code == 200:
            result = resp.json().get("response", "").strip()
            lines = result.split("\n")
            first_line = lines[0].strip().strip('"').strip("'").strip("*").strip()
            # Remove trailing punctuation
            first_line = first_line.rstrip(".,;")
            if first_line and len(first_line) < 100:
                return first_line
    except Exception:
        pass
    return None


# ================================================================
# 1C. POST-PROCESSING — Sostituzione termini di sicurezza
# ================================================================
# Cattura errori residui anche dopo Ollama

TERM_SUBS = [
    # Kettlebell variants
    (re.compile(r"\bManico da Cucina\b", re.I), "Kettlebell"),
    (re.compile(r"\bManico Pesante\b", re.I), "Kettlebell"),
    (re.compile(r"\bManico\b(?!\s+(di|della|del))", re.I), "Kettlebell"),
    # Clean mistranslations
    (re.compile(r"\bPulizia\b", re.I), "Girata"),
    (re.compile(r"\bSlegamento\b", re.I), "Girata"),
    (re.compile(r"\bSfilata\b", re.I), "Girata"),
    # Snatch mistranslations
    (re.compile(r"\bStracco\b", re.I), "Strappo"),
    (re.compile(r"\bStrappato\b", re.I), "Strappo"),
    (re.compile(r"\bStrappata\b", re.I), "Strappo"),
]


def apply_term_subs(nome: str) -> str:
    """Apply safety-net term substitutions."""
    for pattern, replacement in TERM_SUBS:
        nome = pattern.sub(replacement, nome)
    return nome


# ================================================================
# EXECUTION
# ================================================================

def fix_names(db_path: str, dry_run: bool = False) -> list[dict]:
    """Fix exercise names in a single database. Returns change log."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 60}")
    print(f"  {'[DRY-RUN] ' if dry_run else ''}Fixing names: {db_name}")
    print(f"{'=' * 60}")

    # Load FDB exercises (id > 345)
    exercises = conn.execute("""
        SELECT id, nome, nome_en FROM esercizi
        WHERE deleted_at IS NULL AND id > 345
        ORDER BY id
    """).fetchall()

    changes = []
    manual_count = 0
    ollama_count = 0
    termsub_count = 0
    unchanged_count = 0

    for i, ex in enumerate(exercises):
        eid = ex["id"]
        old_nome = ex["nome"]
        nome_en = ex["nome_en"]
        new_nome = None
        source = ""

        # Priority 1: Manual override
        if eid in MANUAL_OVERRIDES:
            new_nome = MANUAL_OVERRIDES[eid]
            source = "manual"
            manual_count += 1
        else:
            # Priority 2: Ollama re-translation
            if not dry_run:
                translated = translate_name_ollama(nome_en)
                if translated and translated != old_nome:
                    new_nome = translated
                    source = "ollama"
                    ollama_count += 1

        # Priority 3: Term substitutions (applied to whatever we have)
        final_nome = new_nome or old_nome
        after_subs = apply_term_subs(final_nome)
        if after_subs != final_nome:
            new_nome = after_subs
            if source != "manual":
                source = f"{source}+termsub" if source else "termsub"
                termsub_count += 1

        if new_nome and new_nome != old_nome:
            changes.append({
                "id": eid,
                "nome_en": nome_en,
                "old_nome": old_nome,
                "new_nome": new_nome,
                "source": source,
            })
            if not dry_run:
                conn.execute(
                    "UPDATE esercizi SET nome = ? WHERE id = ?",
                    (new_nome, eid)
                )
        else:
            unchanged_count += 1

        # Progress
        if (i + 1) % 50 == 0:
            print(f"    Progress: {i + 1}/{len(exercises)}")

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"\n  Results ({db_name}):")
    print(f"    Manual overrides: {manual_count}")
    print(f"    Ollama re-translated: {ollama_count}")
    print(f"    Term substitutions: {termsub_count}")
    print(f"    Unchanged: {unchanged_count}")
    print(f"    Total changes: {len(changes)}")

    return changes


def save_report(changes: list[dict], db_name: str) -> str:
    """Save change report as CSV."""
    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"name_fixes_{db_name}_{timestamp}.csv"
    filepath = os.path.join(REPORT_DIR, filename)

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "nome_en", "old_nome", "new_nome", "source"])
        writer.writeheader()
        writer.writerows(changes)

    print(f"  Report: {filepath} ({len(changes)} rows)")
    return filepath


def verify_names(db_path: str) -> None:
    """Post-fix name verification."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    db_name = os.path.basename(db_path)

    print(f"\n  Verification: {db_name}")

    # Duplicate nome IT
    dupes = conn.execute("""
        SELECT nome, GROUP_CONCAT(id), COUNT(*) as cnt FROM esercizi
        WHERE deleted_at IS NULL GROUP BY nome HAVING cnt > 1 ORDER BY nome
    """).fetchall()
    print(f"    Duplicate nome IT: {len(dupes)} groups {'PASS' if len(dupes) == 0 else 'CHECK'}")
    for nome, ids, cnt in dupes:
        print(f"      \"{nome}\" (ids: {ids})")

    # Bad terms check
    bad_terms = [
        ("Manico da Cucina", "Manico da Cucina"),
        ("Pulizia (wrong Clean)", "Pulizia"),
        ("Stracco (wrong Snatch)", "Stracco"),
        ("Strappato (wrong)", "Strappato"),
        ("Slegamento (wrong Clean)", "Slegamento"),
    ]
    for label, term in bad_terms:
        cnt = conn.execute(
            "SELECT COUNT(*) FROM esercizi WHERE deleted_at IS NULL AND nome LIKE ?",
            (f"%{term}%",)
        ).fetchone()[0]
        if cnt > 0:
            print(f"    WARNING: {cnt} exercises still contain '{term}'")

    # Sample some translations for quality
    print(f"    Sample translations:")
    samples = conn.execute("""
        SELECT id, nome, nome_en FROM esercizi
        WHERE deleted_at IS NULL AND id > 345
        ORDER BY RANDOM() LIMIT 10
    """).fetchall()
    for s in samples:
        print(f"      [{s[0]}] \"{s[1]}\" <- \"{s[2]}\"")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix exercise names (Phase 1)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both",
                        help="Which database to fix")
    args = parser.parse_args()

    print("Exercise Name Fix — Phase 1")
    print("=" * 60)

    dbs = []
    if args.db in ("dev", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if args.db in ("prod", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm.db"))

    for db_path in dbs:
        db_name = os.path.basename(db_path).replace(".db", "")
        changes = fix_names(db_path, dry_run=args.dry_run)
        if changes:
            save_report(changes, db_name)

    print(f"\n{'=' * 60}")
    print("  POST-FIX VERIFICATION")
    print("=" * 60)

    for db_path in dbs:
        verify_names(db_path)

    print("\nDone.")
