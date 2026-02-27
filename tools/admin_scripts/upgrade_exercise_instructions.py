"""
Fase 2B: Upgrade esecuzione originali in formato step-by-step.

Per i 345 esercizi originali:
  - 291 con esecuzione breve (3 frasi vaghe) → rigenera in formato step-by-step dettagliato
  - 54 senza esecuzione → genera ex novo in formato step-by-step

Formato target: stile FDB — step-by-step, cumulativo, 5-8 frasi dettagliate,
include posizione iniziale, fase concentrica, eccentrica, respirazione, tip.

Idempotente: salta esercizi gia' in formato step-by-step (>400 chars).
Eseguire dalla root:
  python -m tools.admin_scripts.upgrade_exercise_instructions [--db dev|prod|both] [--batch N] [--model gemma2:9b|Mixtral:latest]
"""

import argparse
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
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma2:9b"
OLLAMA_TIMEOUT = 180  # Longer for generation
MIN_QUALITY_LENGTH = 400  # Exercises with esecuzione >= this are already good

# ================================================================
# PROMPTS — Category-aware
# ================================================================

SYSTEM_PROMPT_STRENGTH = """Sei un preparatore atletico NSCA-CSCS. Genera istruzioni di esecuzione DETTAGLIATE per esercizi di forza.

FORMATO OBBLIGATORIO (step-by-step, 5-8 paragrafi):
1. POSIZIONE INIZIALE: posizionamento corpo, presa, piedi, schiena. Dettagli specifici.
2. FASE CONCENTRICA: movimento principale, quali muscoli lavorano, direzione del movimento.
3. PUNTO DI MASSIMA CONTRAZIONE: cosa fare al top del movimento (pausa, squeeze, ecc.)
4. FASE ECCENTRICA: ritorno controllato, tempo di discesa, cosa controllare.
5. RESPIRAZIONE: quando inspirare/espirare rispetto al movimento.
6. TIP PRATICO: un consiglio specifico per l'esecuzione corretta.

REGOLE:
- Scrivi in ITALIANO, imperativo (es. "Afferra", "Posiziona", "Spingi")
- Ogni paragrafo = un passo distinto dell'esecuzione
- Sii SPECIFICO per l'esercizio (no frasi generiche riutilizzabili)
- Include angoli, posizioni, prese specifiche
- Minimo 5 paragrafi, massimo 8
- NO introduzioni ("Questo esercizio..."), NO conclusioni ("Ripeti per...")
- Rispondi SOLO con le istruzioni, nessun titolo o numerazione"""

SYSTEM_PROMPT_STRETCH = """Sei un preparatore atletico specializzato in flessibilita' e mobilita'. Genera istruzioni di esecuzione DETTAGLIATE per esercizi di stretching e mobilita'.

FORMATO OBBLIGATORIO (step-by-step, 4-6 paragrafi):
1. POSIZIONE INIZIALE: posizionamento corpo, appoggi, allineamento.
2. ENTRATA NELLA POSIZIONE: come raggiungere la posizione di allungamento progressivamente.
3. MANTENIMENTO: cosa sentire, dove sentire la tensione, durata consigliata.
4. RESPIRAZIONE: respirazione lenta e profonda, come usarla per approfondire lo stretch.
5. USCITA: come tornare alla posizione iniziale in sicurezza.

REGOLE:
- Scrivi in ITALIANO, imperativo
- Sii SPECIFICO per l'esercizio
- Indica quali strutture si allungano
- MAI forzare oltre il dolore
- Rispondi SOLO con le istruzioni"""

SYSTEM_PROMPT_WARMUP = """Sei un preparatore atletico. Genera istruzioni di esecuzione DETTAGLIATE per esercizi di avviamento/riscaldamento.

FORMATO OBBLIGATORIO (step-by-step, 4-6 paragrafi):
1. POSIZIONE INIZIALE: posizionamento corpo, piedi, braccia.
2. MOVIMENTO: descrizione chiara del pattern di movimento.
3. RITMO E INTENSITA': velocita' consigliata, ampiezza del movimento.
4. DURATA/RIPETIZIONI: indicazioni temporali o di volume.
5. PROGRESSIONE: come aumentare gradualmente l'intensita'.

REGOLE:
- Scrivi in ITALIANO, imperativo
- Movimenti fluidi e controllati
- Focus sulla qualita' del movimento, non sull'intensita'
- Rispondi SOLO con le istruzioni"""


def get_system_prompt(categoria: str) -> str:
    """Select system prompt based on exercise category."""
    if categoria in ("stretching", "mobilita"):
        return SYSTEM_PROMPT_STRETCH
    elif categoria == "avviamento":
        return SYSTEM_PROMPT_WARMUP
    else:
        return SYSTEM_PROMPT_STRENGTH


def generate_instructions(
    nome: str,
    nome_en: str,
    categoria: str,
    pattern: str,
    muscoli_primari: str,
    attrezzatura: str,
    old_esecuzione: str | None,
    model: str,
) -> str | None:
    """Generate step-by-step instructions via Ollama."""
    system = get_system_prompt(categoria)

    # Build context for the prompt
    context_parts = [f"Esercizio: {nome}"]
    if nome_en and nome_en != nome:
        context_parts.append(f"Nome inglese: {nome_en}")
    context_parts.append(f"Categoria: {categoria}")
    if pattern:
        context_parts.append(f"Pattern di movimento: {pattern}")
    if muscoli_primari:
        try:
            muscles = json.loads(muscoli_primari)
            if muscles:
                context_parts.append(f"Muscoli primari: {', '.join(muscles)}")
        except (json.JSONDecodeError, TypeError):
            pass
    if attrezzatura:
        context_parts.append(f"Attrezzatura: {attrezzatura}")

    if old_esecuzione:
        context_parts.append(
            f"\nEsecuzione attuale (da migliorare e espandere):\n{old_esecuzione}"
        )

    prompt = (
        "Genera istruzioni di esecuzione DETTAGLIATE e step-by-step "
        "per questo esercizio.\n\n"
        + "\n".join(context_parts)
    )

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "system": system,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 512},
            },
            timeout=OLLAMA_TIMEOUT,
        )
        if resp.status_code == 200:
            result = resp.json().get("response", "").strip()
            # Clean up markdown artifacts
            result = result.strip('"').strip("'")
            if result.startswith("```"):
                result = re.sub(r"^```\w*\n?", "", result)
                result = re.sub(r"\n?```$", "", result)
            # Remove numbered list prefixes (1. 2. 3.) — keep as paragraphs
            result = re.sub(r"^\d+\.\s*", "", result, flags=re.MULTILINE)
            # Remove bold markdown
            result = result.replace("**", "")
            # Validate minimum quality
            if len(result) >= 200:
                return result.strip()
    except Exception as e:
        print(f"      Ollama error: {e}")
    return None


# ================================================================
# EXECUTION
# ================================================================

def upgrade_db(db_path: str, model: str, batch_size: int = 0) -> tuple[int, int, int]:
    """Upgrade exercise instructions in a single database.
    Returns (upgraded, skipped, errors)."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return (0, 0, 0)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 60}")
    print(f"  Upgrading instructions: {db_name} (model: {model})")
    print(f"{'=' * 60}")

    # Load exercises needing upgrade:
    # - Originals (id <= 345): short or missing esecuzione
    # - Any FDB with missing esecuzione
    exercises = conn.execute("""
        SELECT id, nome, nome_en, categoria, pattern_movimento,
               muscoli_primari, attrezzatura, esecuzione
        FROM esercizi
        WHERE deleted_at IS NULL
          AND (id <= 345 OR esecuzione IS NULL OR esecuzione = '')
        ORDER BY id
    """).fetchall()

    print(f"  Total exercises to check: {len(exercises)}")

    upgraded = 0
    skipped = 0
    errors = 0

    for i, ex in enumerate(exercises):
        eid = ex["id"]
        old_exec = ex["esecuzione"]

        # Skip if already high quality (long enough = already step-by-step)
        if old_exec and len(old_exec) >= MIN_QUALITY_LENGTH:
            skipped += 1
            continue

        # Generate new instructions
        result = generate_instructions(
            nome=ex["nome"],
            nome_en=ex["nome_en"],
            categoria=ex["categoria"],
            pattern=ex["pattern_movimento"],
            muscoli_primari=ex["muscoli_primari"],
            attrezzatura=ex["attrezzatura"],
            old_esecuzione=old_exec,
            model=model,
        )

        if result:
            conn.execute(
                "UPDATE esercizi SET esecuzione = ? WHERE id = ?",
                (result, eid)
            )
            upgraded += 1

            # Commit every 5 exercises
            if upgraded % 5 == 0:
                conn.commit()
        else:
            errors += 1
            print(f"    ERROR: id={eid} ({ex['nome']})")

        # Progress
        if (i + 1) % 25 == 0:
            print(f"    Progress: {i + 1}/{len(exercises)} "
                  f"(upgraded={upgraded}, skipped={skipped}, errors={errors})")

        # Batch limit
        if batch_size > 0 and upgraded >= batch_size:
            print(f"    Batch limit reached ({batch_size})")
            break

    conn.commit()
    conn.close()

    print(f"\n  Results ({db_name}):")
    print(f"    Upgraded: {upgraded}")
    print(f"    Already good (>={MIN_QUALITY_LENGTH} chars): {skipped}")
    print(f"    Errors: {errors}")

    return (upgraded, skipped, errors)


def verify(db_path: str) -> None:
    """Post-upgrade verification."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    db_name = os.path.basename(db_path)

    print(f"\n  Verification: {db_name}")

    # Coverage — all exercises
    total = conn.execute(
        "SELECT COUNT(*) FROM esercizi WHERE deleted_at IS NULL"
    ).fetchone()[0]
    with_exec = conn.execute(
        "SELECT COUNT(*) FROM esercizi WHERE deleted_at IS NULL AND esecuzione IS NOT NULL AND esecuzione != ''"
    ).fetchone()[0]
    missing = conn.execute(
        "SELECT COUNT(*) FROM esercizi WHERE deleted_at IS NULL AND (esecuzione IS NULL OR esecuzione = '')"
    ).fetchone()[0]

    print(f"    Total exercises: {total}")
    print(f"    With esecuzione: {with_exec}/{total} ({with_exec*100//total}%)")
    print(f"    Still missing: {missing}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upgrade original exercise instructions (Phase 2B)")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both",
                        help="Which database to process")
    parser.add_argument("--batch", type=int, default=0,
                        help="Limit number of upgrades per DB (0=unlimited)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help="Ollama model to use")
    args = parser.parse_args()

    print("Exercise Instruction Upgrade — Phase 2B")
    print("=" * 60)

    dbs = []
    if args.db in ("dev", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if args.db in ("prod", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm.db"))

    total_upgraded = 0
    total_errors = 0
    for db_path in dbs:
        u, s, e = upgrade_db(db_path, model=args.model, batch_size=args.batch)
        total_upgraded += u
        total_errors += e

    print(f"\n{'=' * 60}")
    print("  POST-UPGRADE VERIFICATION")
    print("=" * 60)

    for db_path in dbs:
        verify(db_path)

    print(f"\nTotal upgraded: {total_upgraded}, errors: {total_errors}")
    print("Done.")
