#!/usr/bin/env python3
"""
Popola gli esercizi con contenuto professionale via Ollama.

Usa il modello locale per generare:
- force_type, lateral_pattern (classificazione biomeccanica)
- descrizione_anatomica, descrizione_biomeccanica
- setup, esecuzione, respirazione, tempo_consigliato
- coaching_cues, errori_comuni, note_sicurezza, controindicazioni

Uso:
    python tools/populate_exercises.py                    # tutti (skip gia' compilati)
    python tools/populate_exercises.py --ids 1 2 3        # solo specifici
    python tools/populate_exercises.py --limit 5          # primi 5 vuoti
    python tools/populate_exercises.py --force             # rigenera anche compilati
    python tools/populate_exercises.py --model gemma2:9b   # modello specifico
    python tools/populate_exercises.py --dry-run           # genera ma non salva
"""

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERRORE: pip install requests")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════

DB_PATH = Path(__file__).parent.parent / "data" / "crm.db"
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "Mixtral:latest"

# Campi che indicano se un esercizio e' gia' stato popolato
POPULATED_CHECK_FIELD = "descrizione_anatomica"

# Validazione enum
VALID_FORCE_TYPES = {"push", "pull", "static"}
VALID_LATERAL_PATTERNS = {"bilateral", "unilateral", "alternating"}

# ═══════════════════════════════════════════════════════════
# PROMPT
# ═══════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Sei un preparatore atletico professionista e fisiologo dell'esercizio con 20 anni di esperienza.
Genera contenuto tecnico accurato in ITALIANO per schede esercizi di un software CRM fitness.
Il tuo output DEVE essere ESCLUSIVAMENTE un oggetto JSON valido, senza testo prima o dopo.
Rispondi SOLO con il JSON richiesto."""

def build_user_prompt(exercise: dict) -> str:
    muscles_pri = exercise["muscoli_primari"]
    muscles_sec = exercise["muscoli_secondari"] or "nessuno"

    return f"""Genera la scheda professionale completa per questo esercizio:

ESERCIZIO: {exercise["nome"]} ({exercise["nome_en"]})
CATEGORIA: {exercise["categoria"]}
PATTERN MOVIMENTO: {exercise["pattern_movimento"]}
ATTREZZATURA: {exercise["attrezzatura"]}
DIFFICOLTA: {exercise["difficolta"]}
MUSCOLI PRIMARI: {muscles_pri}
MUSCOLI SECONDARI: {muscles_sec}

Rispondi con un JSON con ESATTAMENTE questa struttura:

{{
  "force_type": "push|pull|static",
  "lateral_pattern": "bilateral|unilateral|alternating",
  "descrizione_anatomica": "2-3 frasi sui muscoli coinvolti e il loro ruolo nel movimento",
  "descrizione_biomeccanica": "2-3 frasi sulle leve articolari, curva di resistenza e angoli di lavoro",
  "setup": "posizione iniziale dettagliata in 2-3 frasi",
  "esecuzione": "descrizione del movimento step-by-step in 3-4 frasi",
  "respirazione": "pattern respiratorio in 1 frase (es. 'Inspira in fase eccentrica, espira in fase concentrica')",
  "tempo_consigliato": "formato X-X-X-X (eccentrica-pausa bassa-concentrica-pausa alta, es. 3-1-2-0)",
  "coaching_cues": ["3-5 indicazioni brevi e pratiche per l'esecuzione corretta"],
  "errori_comuni": [
    {{"errore": "descrizione errore", "correzione": "come correggerlo"}},
    {{"errore": "descrizione errore", "correzione": "come correggerlo"}}
  ],
  "note_sicurezza": "1-2 frasi su precauzioni importanti",
  "controindicazioni": ["2-3 condizioni in cui evitare questo esercizio"]
}}

REGOLE:
- force_type: "push" se il movimento allontana il carico, "pull" se lo avvicina, "static" se isometrico
- lateral_pattern: "bilateral" se entrambi i lati lavorano insieme, "unilateral" se un lato alla volta, "alternating" se alternato
- Contenuto in ITALIANO, tecnico ma comprensibile
- Coaching cues: brevi, azionabili (es. "Spingi col tallone", "Scapole addotte")
- Errori comuni: 2-3 errori con correzione pratica
- Controindicazioni: condizioni mediche specifiche
- SOLO JSON valido, nessun testo aggiuntivo"""


# ═══════════════════════════════════════════════════════════
# OLLAMA CLIENT
# ═══════════════════════════════════════════════════════════

def call_ollama(prompt: str, model: str) -> str:
    """Chiama Ollama e ritorna il testo generato."""
    payload = {
        "model": model,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 2048,
        },
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()["response"]
    except requests.exceptions.ConnectionError:
        print("ERRORE: Ollama non raggiungibile. Avvia con: ollama serve")
        sys.exit(1)
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}") from e


def parse_json_response(raw: str) -> dict:
    """Estrae il JSON dalla risposta Ollama (gestisce markdown fences)."""
    text = raw.strip()

    # Rimuovi markdown code fences se presenti
    if text.startswith("```"):
        lines = text.split("\n")
        # Rimuovi prima e ultima riga (``` ... ```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Trova il primo { e l'ultimo }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Nessun JSON trovato nella risposta:\n{raw[:200]}")

    json_str = text[start:end + 1]
    return json.loads(json_str)


# ═══════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════

def get_exercises(db: sqlite3.Connection, ids: list[int] | None, limit: int | None, force: bool) -> list[dict]:
    """Recupera esercizi da popolare."""
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    query = "SELECT * FROM esercizi WHERE deleted_at IS NULL"
    params: list = []

    if ids:
        placeholders = ",".join("?" * len(ids))
        query += f" AND id IN ({placeholders})"
        params.extend(ids)

    if not force:
        query += f" AND ({POPULATED_CHECK_FIELD} IS NULL OR {POPULATED_CHECK_FIELD} = '')"

    query += " ORDER BY id"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    rows = cur.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def update_exercise(db: sqlite3.Connection, exercise_id: int, data: dict) -> None:
    """Aggiorna un esercizio con i dati generati."""
    fields = {
        "force_type": data.get("force_type"),
        "lateral_pattern": data.get("lateral_pattern"),
        "descrizione_anatomica": data.get("descrizione_anatomica"),
        "descrizione_biomeccanica": data.get("descrizione_biomeccanica"),
        "setup": data.get("setup"),
        "esecuzione": data.get("esecuzione"),
        "respirazione": data.get("respirazione"),
        "tempo_consigliato": data.get("tempo_consigliato"),
        "coaching_cues": json.dumps(data.get("coaching_cues", []), ensure_ascii=False),
        "errori_comuni": json.dumps(data.get("errori_comuni", []), ensure_ascii=False),
        "note_sicurezza": data.get("note_sicurezza"),
        "controindicazioni": json.dumps(data.get("controindicazioni", []), ensure_ascii=False),
    }

    # Validazione enum
    if fields["force_type"] not in VALID_FORCE_TYPES:
        fields["force_type"] = None
    if fields["lateral_pattern"] not in VALID_LATERAL_PATTERNS:
        fields["lateral_pattern"] = None

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [exercise_id]

    db.execute(f"UPDATE esercizi SET {set_clause} WHERE id = ?", values)
    db.commit()


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Popola esercizi con contenuto via Ollama")
    parser.add_argument("--ids", nargs="+", type=int, help="ID esercizi specifici")
    parser.add_argument("--limit", type=int, help="Limita a N esercizi")
    parser.add_argument("--force", action="store_true", help="Rigenera anche se gia' compilato")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Modello Ollama (default: {DEFAULT_MODEL})")
    parser.add_argument("--dry-run", action="store_true", help="Genera ma non salva nel DB")
    parser.add_argument("--output", type=str, help="Salva output JSON in file")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"ERRORE: Database non trovato: {DB_PATH}")
        sys.exit(1)

    db = sqlite3.connect(str(DB_PATH))
    db.execute("PRAGMA foreign_keys = ON")

    exercises = get_exercises(db, args.ids, args.limit, args.force)
    total = len(exercises)

    if total == 0:
        print("Nessun esercizio da popolare (tutti gia' compilati o filtro vuoto).")
        print("Usa --force per rigenerare, o --ids per specificare ID.")
        return

    print(f"\n{'='*60}")
    print(f"  Popolamento esercizi — {total} da elaborare")
    print(f"  Modello: {args.model}")
    print(f"  Dry-run: {'SI' if args.dry_run else 'NO'}")
    print(f"{'='*60}\n")

    results = []
    success = 0
    errors = 0

    for i, ex in enumerate(exercises, 1):
        name = ex["nome"]
        ex_id = ex["id"]

        print(f"[{i}/{total}] {name} (id={ex_id})...", end=" ", flush=True)

        try:
            t0 = time.time()
            prompt = build_user_prompt(ex)
            raw_response = call_ollama(prompt, args.model)
            data = parse_json_response(raw_response)
            elapsed = time.time() - t0

            # Salva nel DB (se non dry-run)
            if not args.dry_run:
                update_exercise(db, ex_id, data)

            results.append({"id": ex_id, "nome": name, "data": data})
            success += 1
            print(f"OK ({elapsed:.1f}s)")

        except (json.JSONDecodeError, ValueError) as e:
            errors += 1
            print(f"ERRORE JSON: {e}")
            results.append({"id": ex_id, "nome": name, "error": str(e)})
        except Exception as e:
            errors += 1
            print(f"ERRORE: {e}")
            results.append({"id": ex_id, "nome": name, "error": str(e)})

    # Salva output se richiesto
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nOutput salvato in: {output_path}")

    # Riepilogo
    print(f"\n{'='*60}")
    print(f"  Completato: {success}/{total} successi, {errors} errori")
    if args.dry_run:
        print("  (dry-run — nessuna modifica al DB)")
    print(f"{'='*60}\n")

    db.close()


if __name__ == "__main__":
    main()
