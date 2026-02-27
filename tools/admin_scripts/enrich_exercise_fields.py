"""
Fase 3: Enrichment campi descrittivi con Ollama.

Genera contenuto professionale per ~910 esercizi mancanti:
  - descrizione_anatomica, descrizione_biomeccanica
  - setup, respirazione, tempo_consigliato
  - coaching_cues, errori_comuni, controindicazioni

NON tocca il campo `esecuzione` (gia' perfezionato in Fase 2).
NON tocca `note_sicurezza` (gestito in Fase 4).

Prompt category-aware (strength / stretch / warmup).
Usa l'esecuzione esistente come CONTESTO per coerenza.

Idempotente: salta esercizi con descrizione_anatomica gia' compilata.
Eseguire dalla root:
  python -m tools.admin_scripts.enrich_exercise_fields [--db dev|prod|both] [--batch N] [--model Mixtral:latest] [--category compound]
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
DEFAULT_MODEL = "Mixtral:latest"
OLLAMA_TIMEOUT = 300

VALID_FORCE_TYPES = {"push", "pull", "static"}
VALID_LATERAL_PATTERNS = {"bilateral", "unilateral", "alternating"}

# Categories that use stretching prompt
STRETCH_CATS = {"stretching", "mobilita"}
WARMUP_CATS = {"avviamento"}

# Fields to update (NOT esecuzione, NOT note_sicurezza)
ENRICHMENT_FIELDS = [
    "force_type", "lateral_pattern",
    "descrizione_anatomica", "descrizione_biomeccanica",
    "setup", "respirazione", "tempo_consigliato",
    "coaching_cues", "errori_comuni", "controindicazioni",
]

# ================================================================
# PROMPTS — Category-aware
# ================================================================

SYSTEM_STRENGTH = """Sei un preparatore atletico NSCA-CSCS con 20 anni di esperienza.
Genera contenuto tecnico PROFESSIONALE in ITALIANO per una scheda esercizio.
Il contenuto e' destinato a laureati in scienze motorie che devono decidere
se prescrivere questo esercizio a clienti con patologie o limitazioni.

Il tuo output DEVE essere ESCLUSIVAMENTE un oggetto JSON valido.
Rispondi SOLO con il JSON, senza testo prima o dopo."""

SYSTEM_STRETCH = """Sei un fisioterapista e preparatore atletico specializzato in flessibilita' articolare.
Genera contenuto tecnico PROFESSIONALE in ITALIANO per una scheda di stretching/mobilita'.
Il contenuto e' destinato a professionisti del fitness e della riabilitazione.

Il tuo output DEVE essere ESCLUSIVAMENTE un oggetto JSON valido.
Rispondi SOLO con il JSON, senza testo prima o dopo."""

SYSTEM_WARMUP = """Sei un preparatore atletico specializzato in riscaldamento e attivazione neuromuscolare.
Genera contenuto tecnico in ITALIANO per una scheda di avviamento/riscaldamento.
Il contenuto e' destinato a professionisti del fitness.

Il tuo output DEVE essere ESCLUSIVAMENTE un oggetto JSON valido.
Rispondi SOLO con il JSON, senza testo prima o dopo."""


def build_prompt(exercise: dict) -> tuple[str, str]:
    """Build prompt and system prompt based on exercise category."""
    cat = exercise["categoria"]
    nome = exercise["nome"]
    nome_en = exercise["nome_en"] or ""
    muscles_pri = exercise["muscoli_primari"] or "[]"
    muscles_sec = exercise["muscoli_secondari"] or "[]"
    pattern = exercise["pattern_movimento"] or ""
    attrezzatura = exercise["attrezzatura"] or ""
    difficolta = exercise["difficolta"] or ""
    esecuzione = exercise["esecuzione"] or ""

    # Select system prompt
    if cat in STRETCH_CATS:
        system = SYSTEM_STRETCH
    elif cat in WARMUP_CATS:
        system = SYSTEM_WARMUP
    else:
        system = SYSTEM_STRENGTH

    # Build user prompt with context
    context = f"""ESERCIZIO: {nome} ({nome_en})
CATEGORIA: {cat}
PATTERN MOVIMENTO: {pattern}
ATTREZZATURA: {attrezzatura}
DIFFICOLTA: {difficolta}
MUSCOLI PRIMARI: {muscles_pri}
MUSCOLI SECONDARI: {muscles_sec}"""

    if esecuzione:
        context += f"""

ISTRUZIONI ESECUZIONE (gia' validate — usa come riferimento, NON rigenerarle):
{esecuzione[:800]}"""

    if cat in STRETCH_CATS:
        json_template = """{
  "force_type": "static",
  "lateral_pattern": "bilateral|unilateral",
  "descrizione_anatomica": "2-3 frasi: strutture allungate (muscoli, tendini, fasce), catena cinetica coinvolta",
  "descrizione_biomeccanica": "2-3 frasi: articolazioni mobilizzate, ROM target, leve anatomiche",
  "setup": "posizione iniziale dettagliata, appoggi, allineamento in 2-3 frasi",
  "respirazione": "pattern respiratorio (es. 'Inspira profondamente, espira approfondendo l'allungamento')",
  "tempo_consigliato": "durata hold (es. '30-45 secondi per lato')",
  "coaching_cues": ["3-4 indicazioni pratiche per la corretta esecuzione"],
  "errori_comuni": [
    {"errore": "descrizione errore", "correzione": "come correggerlo"}
  ],
  "controindicazioni": ["2-3 condizioni in cui evitare (es. 'Ernia discale in fase acuta')"]
}"""
    elif cat in WARMUP_CATS:
        json_template = """{
  "force_type": "static|push|pull",
  "lateral_pattern": "bilateral|unilateral|alternating",
  "descrizione_anatomica": "2 frasi: muscoli attivati, catena cinetica",
  "descrizione_biomeccanica": "2 frasi: articolazioni mobilizzate, pattern di movimento",
  "setup": "posizione iniziale in 1-2 frasi",
  "respirazione": "pattern respiratorio in 1 frase",
  "tempo_consigliato": "durata/ripetizioni (es. '30 secondi' o '10-15 ripetizioni')",
  "coaching_cues": ["3 indicazioni pratiche"],
  "errori_comuni": [
    {"errore": "descrizione errore", "correzione": "come correggerlo"}
  ],
  "controindicazioni": ["1-2 condizioni in cui evitare"]
}"""
    else:
        json_template = """{
  "force_type": "push|pull|static",
  "lateral_pattern": "bilateral|unilateral|alternating",
  "descrizione_anatomica": "2-3 frasi: muscoli primari e secondari, loro ruolo, catena cinetica",
  "descrizione_biomeccanica": "2-3 frasi: leve articolari, curva di resistenza, angoli di lavoro ottimali",
  "setup": "posizione iniziale dettagliata: presa, piedi, schiena, allineamento in 2-3 frasi",
  "respirazione": "pattern respiratorio in 1 frase (es. 'Inspira in eccentrica, espira in concentrica')",
  "tempo_consigliato": "formato X-X-X-X (eccentrica-pausa-concentrica-pausa, es. '3-1-2-0')",
  "coaching_cues": ["3-5 indicazioni brevi e pratiche per l'esecuzione corretta"],
  "errori_comuni": [
    {"errore": "descrizione errore", "correzione": "come correggerlo"},
    {"errore": "descrizione errore", "correzione": "come correggerlo"}
  ],
  "controindicazioni": ["2-3 condizioni mediche in cui evitare (specifiche, non generiche)"]
}"""

    prompt = f"""{context}

Genera la scheda descrittiva professionale. Rispondi con un JSON con QUESTA struttura:

{json_template}

REGOLE:
- force_type: "push" se allontana il carico, "pull" se avvicina, "static" se isometrico/stretch
- Contenuto in ITALIANO, tecnico ma comprensibile per un laureato in scienze motorie
- Coaching cues: brevi, azionabili (es. "Spingi col tallone", "Scapole addotte")
- Errori comuni: 2-3 errori con correzione pratica specifica per QUESTO esercizio
- Controindicazioni: condizioni mediche SPECIFICHE (es. "Sindrome del tunnel carpale", "Ernia inguinale")
- NON generare il campo esecuzione (gia' presente)
- SOLO JSON valido"""

    return system, prompt


def parse_json_response(raw: str) -> dict:
    """Extract JSON from Ollama response."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON in response: {raw[:200]}")

    return json.loads(text[start:end + 1])


def validate_response(data: dict, categoria: str) -> list[str]:
    """Validate generated data. Returns list of issues."""
    issues = []

    # Required text fields
    for field in ["descrizione_anatomica", "descrizione_biomeccanica", "setup"]:
        val = data.get(field, "")
        if not val or len(str(val)) < 30:
            issues.append(f"{field} too short or missing")

    # coaching_cues should be a list with 2+ items
    cues = data.get("coaching_cues", [])
    if not isinstance(cues, list) or len(cues) < 2:
        issues.append(f"coaching_cues: need 2+ items, got {len(cues) if isinstance(cues, list) else 'non-list'}")

    # errori_comuni should be a list of dicts
    errori = data.get("errori_comuni", [])
    if not isinstance(errori, list) or len(errori) < 1:
        issues.append(f"errori_comuni: need 1+ items")
    elif errori and not isinstance(errori[0], dict):
        issues.append("errori_comuni: items should be dicts with errore/correzione")

    # controindicazioni should be a list
    contra = data.get("controindicazioni", [])
    if not isinstance(contra, list) or len(contra) < 1:
        issues.append(f"controindicazioni: need 1+ items")

    # English language check (basic)
    for field in ["descrizione_anatomica", "setup"]:
        val = str(data.get(field, "")).lower()
        en_words = sum(1 for w in ["the ", "and ", "your ", "with "] if w in val)
        if en_words >= 2:
            issues.append(f"{field}: appears to be in English")

    return issues


# ================================================================
# EXECUTION
# ================================================================

def enrich_db(db_path: str, model: str, batch_size: int = 0, category: str | None = None, subset_only: bool = False) -> tuple[int, int, int]:
    """Enrich exercises in a single database.
    Returns (enriched, skipped, errors)."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return (0, 0, 0)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 60}")
    print(f"  Enriching: {db_name} (model: {model})")
    print(f"{'=' * 60}")

    # Load unenriched exercises (any enrichment field NULL)
    query = """
        SELECT * FROM esercizi
        WHERE deleted_at IS NULL
          AND (descrizione_anatomica IS NULL OR descrizione_anatomica = ''
               OR controindicazioni IS NULL OR controindicazioni = '')
    """
    params = []
    if subset_only:
        query += " AND in_subset = 1"
    if category:
        query += " AND categoria = ?"
        params.append(category)
    query += " ORDER BY id"

    exercises = conn.execute(query, params).fetchall()
    print(f"  To enrich: {len(exercises)}" + (f" (category: {category})" if category else ""))

    enriched = 0
    skipped = 0
    errors = 0

    for i, ex in enumerate(exercises):
        eid = ex["id"]
        nome = ex["nome"]

        try:
            t0 = time.time()
            system, prompt = build_prompt(dict(ex))

            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": model,
                    "system": system,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 2048},
                },
                timeout=OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()
            raw = resp.json()["response"]
            data = parse_json_response(raw)
            elapsed = time.time() - t0

            # Validate
            issues = validate_response(data, ex["categoria"])
            if issues:
                print(f"    WARN id={eid} ({nome}): {'; '.join(issues)}")

            # Update DB — only enrichment fields, NOT esecuzione
            # Field-level idempotent: skip fields already populated
            fields = {}
            ft = data.get("force_type")
            if ft in VALID_FORCE_TYPES and not ex["force_type"]:
                fields["force_type"] = ft
            lp = data.get("lateral_pattern")
            if lp in VALID_LATERAL_PATTERNS and not ex["lateral_pattern"]:
                fields["lateral_pattern"] = lp

            for text_field in ["descrizione_anatomica", "descrizione_biomeccanica",
                               "setup", "respirazione", "tempo_consigliato"]:
                val = data.get(text_field)
                if val and isinstance(val, str) and len(val) > 10 and not ex[text_field]:
                    fields[text_field] = val

            for json_field in ["coaching_cues", "errori_comuni", "controindicazioni"]:
                val = data.get(json_field)
                if val and isinstance(val, list) and not ex[json_field]:
                    fields[json_field] = json.dumps(val, ensure_ascii=False)

            if fields:
                set_clause = ", ".join(f"{k} = ?" for k in fields)
                values = list(fields.values()) + [eid]
                conn.execute(f"UPDATE esercizi SET {set_clause} WHERE id = ?", values)
                enriched += 1

                if enriched % 5 == 0:
                    conn.commit()

                print(f"    [{i+1}/{len(exercises)}] {nome} OK ({elapsed:.1f}s, {len(fields)} fields)")
            else:
                errors += 1
                print(f"    [{i+1}/{len(exercises)}] {nome} EMPTY RESPONSE")

        except (json.JSONDecodeError, ValueError) as e:
            errors += 1
            print(f"    [{i+1}/{len(exercises)}] {nome} JSON ERROR: {e}")
        except Exception as e:
            errors += 1
            print(f"    [{i+1}/{len(exercises)}] {nome} ERROR: {e}")

        # Batch limit
        if batch_size > 0 and enriched >= batch_size:
            print(f"    Batch limit reached ({batch_size})")
            break

    conn.commit()
    conn.close()

    print(f"\n  Results ({db_name}):")
    print(f"    Enriched: {enriched}")
    print(f"    Errors: {errors}")

    return (enriched, skipped, errors)


def verify(db_path: str) -> None:
    """Post-enrichment verification."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    db_name = os.path.basename(db_path)

    print(f"\n  Verification: {db_name}")

    total = conn.execute("SELECT COUNT(*) FROM esercizi WHERE deleted_at IS NULL").fetchone()[0]
    enriched = conn.execute("""
        SELECT COUNT(*) FROM esercizi WHERE deleted_at IS NULL
        AND descrizione_anatomica IS NOT NULL AND descrizione_anatomica != ''
    """).fetchone()[0]
    print(f"    Enriched: {enriched}/{total} ({enriched*100//total}%)")

    # By category
    cats = conn.execute("""
        SELECT categoria,
               COUNT(*) as total,
               SUM(CASE WHEN descrizione_anatomica IS NOT NULL AND descrizione_anatomica != '' THEN 1 ELSE 0 END) as enriched
        FROM esercizi WHERE deleted_at IS NULL
        GROUP BY categoria ORDER BY total DESC
    """).fetchall()
    for cat in cats:
        pct = cat[2]*100//cat[1] if cat[1] > 0 else 0
        print(f"    {cat[0]}: {cat[2]}/{cat[1]} ({pct}%)")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich exercise descriptive fields (Phase 3)")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both")
    parser.add_argument("--batch", type=int, default=0, help="Limit per DB (0=unlimited)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--category", type=str, help="Process only this category")
    parser.add_argument("--subset-only", action="store_true",
                        help="Process only exercises with in_subset = 1")
    args = parser.parse_args()

    print("Exercise Enrichment — Phase 3")
    print("=" * 60)

    dbs = []
    if args.db in ("dev", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if args.db in ("prod", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm.db"))

    for db_path in dbs:
        enrich_db(db_path, model=args.model, batch_size=args.batch,
                  category=args.category, subset_only=args.subset_only)

    print(f"\n{'=' * 60}")
    print("  VERIFICATION")
    print("=" * 60)

    for db_path in dbs:
        verify(db_path)

    print("\nDone.")
