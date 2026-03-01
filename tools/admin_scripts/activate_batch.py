"""
Orchestratore attivazione batch esercizi — Foto-First Strategy.

Fasi:
  0. AUDIT    — Report stato corrente, conteggi foto su disco
  1. DEACTIVATE — in_subset=0 per esercizi attivi senza foto
  2. SELECT   — Scegli N candidati dall'archivio (con foto) per copertura
  3. ENRICH   — Popola campi mancanti via Ollama (Mixtral + gemma2:9b)
  4. ACTIVATE — in_subset=1 per candidati arricchiti
  5. VERIFY   — Quality gate sui nuovi attivi

Dopo l'esecuzione, lanciare la pipeline deterministica esterna:
  python -m tools.admin_scripts.populate_taxonomy --db both
  python -m tools.admin_scripts.populate_conditions --db both
  python -m tools.admin_scripts.populate_exercise_relations --db both
  python -m tools.admin_scripts.fill_subset_gaps --db both
  python -m tools.admin_scripts.verify_exercise_quality --db both

Eseguire dalla root:
  python -m tools.admin_scripts.activate_batch [--db dev|prod|both] [--dry-run] [--batch-size 50]
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from collections import Counter

import requests

# ================================================================
# CONFIG
# ================================================================

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
MEDIA_DIR = os.path.join(BASE_DIR, "media", "exercises")

OLLAMA_URL = "http://localhost:11434/api/generate"
ENRICH_MODEL = "gemma2:9b"
SAFETY_MODEL = "gemma2:9b"
OLLAMA_TIMEOUT = 300

# Campi obbligatori per attivazione
REQUIRED_TEXT_FIELDS = [
    "muscoli_primari", "setup", "esecuzione",
    "descrizione_anatomica", "descrizione_biomeccanica",
    "coaching_cues", "errori_comuni", "controindicazioni",
    "note_sicurezza", "respirazione", "tempo_consigliato",
]

# Dimensioni copertura
COVERAGE_DIMS = ["categoria", "pattern_movimento", "attrezzatura", "difficolta"]

# Constraint selezione
MAX_PER_CATEGORY = 15
MAX_PER_PATTERN = 8
MIN_COMPLEMENTARY = {"stretching": 3, "avviamento": 10, "mobilita": 5}

# Categorie che possono essere attivate senza foto (bodyweight semplice)
# Richiedono comunque il campo 'esecuzione' compilato
PHOTO_OPTIONAL_CATEGORIES = {"avviamento", "mobilita"}


# ================================================================
# HELPERS
# ================================================================

def get_db_paths(db_arg: str) -> list[str]:
    """Resolve DB paths from CLI argument."""
    paths = []
    if db_arg in ("dev", "both"):
        paths.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if db_arg in ("prod", "both"):
        paths.append(os.path.join(BASE_DIR, "crm.db"))
    return paths


def has_photos(exercise_id: int) -> bool:
    """Check if exercise has both exec_start.jpg and exec_end.jpg on disk."""
    d = os.path.join(MEDIA_DIR, str(exercise_id))
    return (
        os.path.isfile(os.path.join(d, "exec_start.jpg"))
        and os.path.isfile(os.path.join(d, "exec_end.jpg"))
    )


def field_filled(val) -> bool:
    """Check if a field value is non-empty."""
    if val is None:
        return False
    s = str(val).strip()
    return len(s) > 0 and s != "[]" and s != "{}"


# ================================================================
# FASE 0: AUDIT
# ================================================================

def phase_audit(db_path: str) -> dict:
    """Audit current state: counts, photos, distributions."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 60}")
    print(f"  FASE 0 — AUDIT: {db_name}")
    print(f"{'=' * 60}")

    all_ex = conn.execute(
        "SELECT * FROM esercizi WHERE deleted_at IS NULL ORDER BY id"
    ).fetchall()

    active = [e for e in all_ex if e["in_subset"] == 1]
    archived = [e for e in all_ex if e["in_subset"] == 0]

    active_with_photos = [e for e in active if has_photos(e["id"])]
    active_no_photos = [
        e for e in active
        if not has_photos(e["id"]) and e["categoria"] not in PHOTO_OPTIONAL_CATEGORIES
    ]
    archived_with_photos = [e for e in archived if has_photos(e["id"])]
    archived_no_photos = [e for e in archived if not has_photos(e["id"])]

    # Candidati photo-optional: no foto ma hanno esecuzione compilata
    archived_photo_optional = [
        e for e in archived_no_photos
        if e["categoria"] in PHOTO_OPTIONAL_CATEGORIES and field_filled(e["esecuzione"])
    ]

    print(f"\n  Totale esercizi: {len(all_ex)}")
    print(f"  Attivi (in_subset=1): {len(active)}")
    print(f"    Con foto:  {len(active_with_photos)}")
    print(f"    Senza foto (da disattivare): {len(active_no_photos)}")
    print(f"  Archiviati (in_subset=0): {len(archived)}")
    print(f"    Con foto:  {len(archived_with_photos)}")
    print(f"    Senza foto: {len(archived_no_photos)}")
    print(f"    Photo-optional (avviamento/mobilita con esecuzione): {len(archived_photo_optional)}")

    # Distribuzione attivi CON foto
    print(f"\n  Distribuzione attivi CON foto ({len(active_with_photos)}):")
    for dim in COVERAGE_DIMS:
        counts = Counter(e[dim] for e in active_with_photos if e[dim])
        items = sorted(counts.items(), key=lambda x: -x[1])
        print(f"    {dim}: {dict(items)}")

    # IDs da disattivare
    if active_no_photos:
        ids_str = ", ".join(str(e["id"]) for e in active_no_photos)
        print(f"\n  Da disattivare ({len(active_no_photos)} IDs): {ids_str}")

    conn.close()

    return {
        "db_path": db_path,
        "active_with_photos": [dict(e) for e in active_with_photos],
        "active_no_photos_ids": [e["id"] for e in active_no_photos],
        "archived_with_photos": [dict(e) for e in archived_with_photos],
        "archived_no_photos_ids": [e["id"] for e in archived_no_photos],
        "archived_photo_optional": [dict(e) for e in archived_photo_optional],
    }


# ================================================================
# FASE 1: DEACTIVATE
# ================================================================

def phase_deactivate(db_path: str, ids_to_deactivate: list[int], dry_run: bool) -> int:
    """Set in_subset=0 for exercises without photos."""
    if not ids_to_deactivate:
        print("  Nessun esercizio da disattivare.")
        return 0

    db_name = os.path.basename(db_path)
    print(f"\n{'=' * 60}")
    print(f"  FASE 1 — DEACTIVATE: {db_name}")
    print(f"{'=' * 60}")
    print(f"  Esercizi da disattivare: {len(ids_to_deactivate)}")

    if dry_run:
        print("  [DRY-RUN] Nessuna modifica.")
        return len(ids_to_deactivate)

    conn = sqlite3.connect(db_path)
    placeholders = ",".join("?" * len(ids_to_deactivate))
    conn.execute(
        f"UPDATE esercizi SET in_subset = 0 WHERE id IN ({placeholders})",
        ids_to_deactivate,
    )
    conn.commit()
    conn.close()

    print(f"  Disattivati: {len(ids_to_deactivate)}")
    return len(ids_to_deactivate)


# ================================================================
# FASE 2: SELECT
# ================================================================

def phase_select(
    active_with_photos: list[dict],
    candidates: list[dict],
    batch_size: int,
    prefer_category: str | None = None,
) -> list[dict]:
    """Select best candidates from archive based on coverage gaps."""

    print(f"\n{'=' * 60}")
    print(f"  FASE 2 — SELECT (top {batch_size} da {len(candidates)} candidati)")
    if prefer_category:
        print(f"  Preferenza categoria: {prefer_category}")
    print(f"{'=' * 60}")

    # Distribuzione corrente degli attivi
    current_dist: dict[str, Counter] = {}
    for dim in COVERAGE_DIMS:
        current_dist[dim] = Counter(e[dim] for e in active_with_photos if e.get(dim))

    print(f"\n  Distribuzione corrente ({len(active_with_photos)} attivi):")
    for dim, counts in current_dist.items():
        print(f"    {dim}: {dict(sorted(counts.items(), key=lambda x: -x[1]))}")

    # Trova gap: valori con 0 presenze tra gli attivi
    all_values: dict[str, set[str]] = {}
    for dim in COVERAGE_DIMS:
        all_values[dim] = set(e[dim] for e in candidates if e.get(dim))

    gaps: dict[str, set[str]] = {}
    for dim in COVERAGE_DIMS:
        gaps[dim] = all_values[dim] - set(current_dist[dim].keys())
        if gaps[dim]:
            print(f"\n  Gap {dim}: {gaps[dim]}")

    # Pre-filtro: escludi candidati senza esecuzione (campo critico, non generabile)
    pre_count = len(candidates)
    candidates = [e for e in candidates if field_filled(e.get("esecuzione"))]
    if pre_count != len(candidates):
        print(f"\n  Pre-filtro: {pre_count - len(candidates)} esclusi (esecuzione vuota)")
        print(f"  Candidati validi: {len(candidates)}")

    # Scoring candidati
    scored: list[tuple[float, dict]] = []
    for ex in candidates:
        score = 0.0

        # +3 per categoria vuota tra gli attivi
        cat = ex.get("categoria", "")
        if cat and cat in gaps.get("categoria", set()):
            score += 3.0

        # +2 per pattern scoperto
        pat = ex.get("pattern_movimento", "")
        if pat and pat in gaps.get("pattern_movimento", set()):
            score += 2.0

        # +1.5 per attrezzatura scoperta
        attr = ex.get("attrezzatura", "")
        if attr and attr in gaps.get("attrezzatura", set()):
            score += 1.5

        # +1 per difficolta' scoperta
        diff = ex.get("difficolta", "")
        if diff and diff in gaps.get("difficolta", set()):
            score += 1.0

        # +0.5 per attrezzatura sotto-rappresentata (< 3)
        if attr and current_dist["attrezzatura"].get(attr, 0) < 3:
            score += 0.5

        # +0.5 per pattern sotto-rappresentato (< 3)
        if pat and current_dist["pattern_movimento"].get(pat, 0) < 3:
            score += 0.5

        # +2.5 per categoria preferita (--prefer flag)
        if prefer_category and cat == prefer_category:
            score += 2.5

        # +1 se ha gia' campi ricchi compilati (meno lavoro Ollama)
        rich_count = sum(1 for f in REQUIRED_TEXT_FIELDS if field_filled(ex.get(f)))
        score += rich_count * 0.1  # max +1.1 per 11 campi

        scored.append((score, ex))

    # Ordina per score decrescente
    scored.sort(key=lambda x: -x[0])

    # Seleziona rispettando constraint
    selected: list[dict] = []
    cat_counts: Counter = Counter()

    # Prima pass: assicura minimo complementari
    for min_cat, min_count in MIN_COMPLEMENTARY.items():
        cat_pool = [(s, e) for s, e in scored if e.get("categoria") == min_cat]
        for _, ex in cat_pool[:min_count]:
            if ex["id"] not in {s["id"] for s in selected}:
                selected.append(ex)
                cat_counts[ex["categoria"]] += 1

    # Seconda pass: riempi fino a batch_size
    pat_counts: Counter = Counter()
    for ex in selected:
        pat_counts[ex.get("pattern_movimento", "")] += 1

    for score, ex in scored:
        if len(selected) >= batch_size:
            break
        if ex["id"] in {s["id"] for s in selected}:
            continue

        cat = ex.get("categoria", "")
        pat = ex.get("pattern_movimento", "")
        if cat_counts[cat] >= MAX_PER_CATEGORY:
            continue
        if pat and pat_counts[pat] >= MAX_PER_PATTERN:
            continue

        selected.append(ex)
        cat_counts[cat] += 1
        pat_counts[pat] += 1

    # Report selezione
    print(f"\n  Selezionati: {len(selected)}")
    sel_dist: dict[str, Counter] = {}
    for dim in COVERAGE_DIMS:
        sel_dist[dim] = Counter(e[dim] for e in selected if e.get(dim))
        print(f"    {dim}: {dict(sorted(sel_dist[dim].items(), key=lambda x: -x[1]))}")

    # Completezza campi
    rich_stats = Counter()
    for ex in selected:
        for f in REQUIRED_TEXT_FIELDS:
            if field_filled(ex.get(f)):
                rich_stats[f] += 1
    print(f"\n  Campi gia' compilati sui {len(selected)} selezionati:")
    for f in REQUIRED_TEXT_FIELDS:
        pct = rich_stats[f] * 100 // len(selected) if selected else 0
        status = "OK" if pct >= 90 else ("PARTIAL" if pct >= 50 else "EMPTY")
        print(f"    {f:30s}: {rich_stats[f]:3d}/{len(selected)} ({pct}%) {status}")

    return selected


# ================================================================
# FASE 3: ENRICH
# ================================================================

# Import funzioni dal pipeline esistente
from tools.admin_scripts.enrich_exercise_fields import (
    build_prompt,
    parse_json_response,
    validate_response,
    ENRICHMENT_FIELDS,
    VALID_FORCE_TYPES,
    VALID_LATERAL_PATTERNS,
)
from tools.admin_scripts.backfill_exercise_fields import generate_safety_notes


def enrich_single(conn: sqlite3.Connection, ex: dict, model: str) -> tuple[bool, list[str]]:
    """Enrich a single exercise via Ollama. Returns (success, issues)."""
    eid = ex["id"]
    nome = ex["nome"]

    # Check quali campi servono
    needs_enrich = not field_filled(ex.get("descrizione_anatomica"))
    needs_safety = not field_filled(ex.get("note_sicurezza"))

    if not needs_enrich and not needs_safety:
        return True, []

    issues: list[str] = []

    # 3a. Enrichment campi descrittivi (Mixtral)
    if needs_enrich:
        try:
            system, prompt = build_prompt(ex)
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

            validation = validate_response(data, ex.get("categoria", ""))
            if validation:
                issues.extend(validation)

            # Update solo campi vuoti
            fields = {}
            ft = data.get("force_type")
            if ft in VALID_FORCE_TYPES and not field_filled(ex.get("force_type")):
                fields["force_type"] = ft
            lp = data.get("lateral_pattern")
            if lp in VALID_LATERAL_PATTERNS and not field_filled(ex.get("lateral_pattern")):
                fields["lateral_pattern"] = lp

            for text_field in ["descrizione_anatomica", "descrizione_biomeccanica",
                               "setup", "respirazione", "tempo_consigliato"]:
                val = data.get(text_field)
                if val and isinstance(val, str) and len(val) > 10 and not field_filled(ex.get(text_field)):
                    fields[text_field] = val

            for json_field in ["coaching_cues", "errori_comuni", "controindicazioni"]:
                val = data.get(json_field)
                if val and isinstance(val, list) and not field_filled(ex.get(json_field)):
                    fields[json_field] = json.dumps(val, ensure_ascii=False)

            if fields:
                set_clause = ", ".join(f"{k} = ?" for k in fields)
                values = list(fields.values()) + [eid]
                conn.execute(f"UPDATE esercizi SET {set_clause} WHERE id = ?", values)

        except Exception as e:
            issues.append(f"enrich error: {e}")

    # 3b. Note sicurezza (gemma2:9b)
    if needs_safety:
        result = generate_safety_notes(
            nome, ex.get("nome_en") or "",
            ex.get("categoria") or "", ex.get("muscoli_primari") or "",
            ex.get("attrezzatura") or "",
        )
        if result:
            conn.execute(
                "UPDATE esercizi SET note_sicurezza = ? WHERE id = ?",
                (result, eid),
            )
        else:
            issues.append("note_sicurezza: generation failed")

    return len(issues) == 0, issues


def phase_enrich(db_path: str, selected_ids: list[int], model: str, dry_run: bool) -> dict[int, list[str]]:
    """Enrich selected exercises. Returns {id: issues} for exercises with problems."""
    db_name = os.path.basename(db_path)
    print(f"\n{'=' * 60}")
    print(f"  FASE 3 — ENRICH: {db_name} ({len(selected_ids)} esercizi)")
    print(f"{'=' * 60}")

    if dry_run:
        print("  [DRY-RUN] Nessun enrichment.")
        return {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Load selected exercises
    placeholders = ",".join("?" * len(selected_ids))
    exercises = conn.execute(
        f"SELECT * FROM esercizi WHERE id IN ({placeholders}) ORDER BY id",
        selected_ids,
    ).fetchall()

    all_issues: dict[int, list[str]] = {}
    enriched = 0
    skipped = 0
    errors = 0

    for i, ex in enumerate(exercises):
        ex_dict = dict(ex)
        eid = ex["id"]
        nome = ex["nome"]

        # Skip se gia' completo
        needs_work = (
            not field_filled(ex["descrizione_anatomica"])
            or not field_filled(ex["note_sicurezza"])
        )
        if not needs_work:
            skipped += 1
            continue

        t0 = time.time()
        ok, issues = enrich_single(conn, ex_dict, model)
        elapsed = time.time() - t0

        if ok:
            enriched += 1
            print(f"    [{i+1}/{len(exercises)}] {nome} OK ({elapsed:.1f}s)")
        else:
            errors += 1
            all_issues[eid] = issues
            print(f"    [{i+1}/{len(exercises)}] {nome} ISSUES: {'; '.join(issues)}")

        # Commit ogni 5
        if (enriched + errors) % 5 == 0:
            conn.commit()

    conn.commit()
    conn.close()

    print(f"\n  Risultato: {enriched} arricchiti, {skipped} gia' completi, {errors} con problemi")
    return all_issues


# ================================================================
# FASE 4: ACTIVATE
# ================================================================

def phase_activate(db_path: str, selected_ids: list[int], dry_run: bool) -> int:
    """Set in_subset=1 for selected exercises."""
    db_name = os.path.basename(db_path)
    print(f"\n{'=' * 60}")
    print(f"  FASE 4 — ACTIVATE: {db_name}")
    print(f"{'=' * 60}")
    print(f"  Esercizi da attivare: {len(selected_ids)}")

    if dry_run:
        print("  [DRY-RUN] Nessuna modifica.")
        return 0

    conn = sqlite3.connect(db_path)
    placeholders = ",".join("?" * len(selected_ids))
    conn.execute(
        f"UPDATE esercizi SET in_subset = 1 WHERE id IN ({placeholders})",
        selected_ids,
    )
    conn.commit()

    # Verifica
    count = conn.execute(
        "SELECT COUNT(*) FROM esercizi WHERE in_subset = 1"
    ).fetchone()[0]
    conn.close()

    print(f"  Attivati: {len(selected_ids)}")
    print(f"  Totale attivi ora: {count}")
    return len(selected_ids)


# ================================================================
# FASE 5: VERIFY
# ================================================================

def phase_verify(db_path: str, selected_ids: list[int]) -> list[int]:
    """Quick quality check on newly activated exercises.
    Returns list of IDs that FAILED and should be deactivated."""

    db_name = os.path.basename(db_path)
    print(f"\n{'=' * 60}")
    print(f"  FASE 5 — VERIFY: {db_name}")
    print(f"{'=' * 60}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    placeholders = ",".join("?" * len(selected_ids))
    exercises = conn.execute(
        f"SELECT * FROM esercizi WHERE id IN ({placeholders}) ORDER BY id",
        selected_ids,
    ).fetchall()

    failed_ids: list[int] = []
    passed = 0

    for ex in exercises:
        eid = ex["id"]
        nome = ex["nome"]
        issues: list[str] = []

        # Campi obbligatori
        for f in REQUIRED_TEXT_FIELDS:
            if not field_filled(ex[f]):
                issues.append(f"{f}: vuoto")

        # Foto (double-check — skip per categorie photo-optional)
        cat = ex["categoria"] or ""
        if not has_photos(eid) and cat not in PHOTO_OPTIONAL_CATEGORIES:
            issues.append("foto: mancanti")

        # Esecuzione (campo critico)
        if not field_filled(ex["esecuzione"]):
            issues.append("esecuzione: vuota (campo critico)")

        if issues:
            failed_ids.append(eid)
            print(f"    FAIL [{eid}] {nome}: {'; '.join(issues)}")
        else:
            passed += 1

    conn.close()

    print(f"\n  Passed: {passed}/{len(exercises)}")
    if failed_ids:
        print(f"  Failed: {len(failed_ids)} — verranno disattivati")

    return failed_ids


def rollback_failed(db_path: str, failed_ids: list[int]) -> None:
    """Deactivate exercises that failed verification."""
    if not failed_ids:
        return

    conn = sqlite3.connect(db_path)
    placeholders = ",".join("?" * len(failed_ids))
    conn.execute(
        f"UPDATE esercizi SET in_subset = 0 WHERE id IN ({placeholders})",
        failed_ids,
    )
    conn.commit()
    conn.close()
    print(f"  Rollback: {len(failed_ids)} esercizi disattivati")


# ================================================================
# REPORT FINALE
# ================================================================

def final_report(db_path: str) -> None:
    """Print final state after all phases."""
    conn = sqlite3.connect(db_path)
    db_name = os.path.basename(db_path)

    total = conn.execute(
        "SELECT COUNT(*) FROM esercizi WHERE deleted_at IS NULL"
    ).fetchone()[0]
    active = conn.execute(
        "SELECT COUNT(*) FROM esercizi WHERE deleted_at IS NULL AND in_subset = 1"
    ).fetchone()[0]

    # Tutti gli attivi hanno foto?
    active_rows = conn.execute(
        "SELECT id FROM esercizi WHERE deleted_at IS NULL AND in_subset = 1"
    ).fetchall()
    all_have_photos = all(has_photos(r[0]) for r in active_rows)

    print(f"\n{'=' * 60}")
    print(f"  REPORT FINALE: {db_name}")
    print(f"{'=' * 60}")
    print(f"  Totale esercizi: {total}")
    print(f"  Attivi (in_subset=1): {active}")
    print(f"  Archiviati (in_subset=0): {total - active}")
    print(f"  Tutti attivi con foto: {'SI' if all_have_photos else 'NO !!!'}")

    # Distribuzione attivi
    for dim in COVERAGE_DIMS:
        rows = conn.execute(
            f"SELECT {dim}, COUNT(*) as cnt FROM esercizi "
            f"WHERE deleted_at IS NULL AND in_subset = 1 AND {dim} IS NOT NULL "
            f"GROUP BY {dim} ORDER BY cnt DESC"
        ).fetchall()
        dist = {r[0]: r[1] for r in rows}
        print(f"  {dim}: {dist}")

    conn.close()


# ================================================================
# MAIN
# ================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Orchestratore attivazione batch esercizi (Foto-First)"
    )
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both")
    parser.add_argument("--dry-run", action="store_true",
                        help="Audit + select senza modifiche")
    parser.add_argument("--batch-size", type=int, default=50,
                        help="Numero esercizi da attivare (default: 50)")
    parser.add_argument("--skip-enrich", action="store_true",
                        help="Salta Fase 3 (per ri-esecuzione dopo fix manuale)")
    parser.add_argument("--model", default=ENRICH_MODEL,
                        help=f"Modello Ollama per enrichment (default: {ENRICH_MODEL})")
    parser.add_argument("--prefer", default=None,
                        help="Categoria da preferire nella selezione (es. bodyweight, stretching)")
    args = parser.parse_args()

    print("=" * 60)
    print("  ACTIVATE BATCH — Foto-First Strategy")
    print("=" * 60)
    print(f"  DB: {args.db} | Batch: {args.batch_size} | Dry-run: {args.dry_run}")
    print(f"  Model: {args.model} | Skip enrich: {args.skip_enrich}")
    if args.prefer:
        print(f"  Preferenza categoria: {args.prefer}")

    db_paths = get_db_paths(args.db)
    if not db_paths:
        print("ERROR: nessun database trovato.")
        sys.exit(1)

    # ── Fase 0: Audit (primo DB come riferimento per selezione) ──
    audit_data = phase_audit(db_paths[0])

    # ── Fase 1: Deactivate ──
    ids_to_deactivate = audit_data["active_no_photos_ids"]
    for db_path in db_paths:
        phase_deactivate(db_path, ids_to_deactivate, args.dry_run)

    # ── Fase 2: Select ──
    # Merge photo candidates + photo-optional (avviamento/mobilita con esecuzione)
    all_candidates = audit_data["archived_with_photos"] + audit_data["archived_photo_optional"]
    # Deduplica per id (photo-optional non dovrebbe sovrapporre, ma safety check)
    seen_ids = set()
    unique_candidates = []
    for c in all_candidates:
        if c["id"] not in seen_ids:
            unique_candidates.append(c)
            seen_ids.add(c["id"])

    selected = phase_select(
        audit_data["active_with_photos"],
        unique_candidates,
        args.batch_size,
        prefer_category=args.prefer,
    )
    selected_ids = [e["id"] for e in selected]

    if not selected_ids:
        print("\nNessun candidato selezionato. Fine.")
        return

    print(f"\n  IDs selezionati ({len(selected_ids)}): {selected_ids}")

    if args.dry_run:
        print("\n  [DRY-RUN] Fine preview. Rimuovi --dry-run per eseguire.")
        return

    # ── Fase 3: Enrich ──
    if not args.skip_enrich:
        for db_path in db_paths:
            phase_enrich(db_path, selected_ids, args.model, dry_run=False)
    else:
        print("\n  [SKIP] Fase 3 saltata (--skip-enrich)")

    # ── Fase 4: Activate ──
    for db_path in db_paths:
        phase_activate(db_path, selected_ids, dry_run=False)

    # ── Fase 5: Verify ──
    for db_path in db_paths:
        failed = phase_verify(db_path, selected_ids)
        if failed:
            rollback_failed(db_path, failed)

    # ── Report finale ──
    for db_path in db_paths:
        final_report(db_path)

    print(f"\n{'=' * 60}")
    print("  PROSSIMI PASSI:")
    print("  Eseguire la pipeline deterministica:")
    print("    python -m tools.admin_scripts.populate_taxonomy --db both")
    print("    python -m tools.admin_scripts.populate_conditions --db both")
    print("    python -m tools.admin_scripts.populate_exercise_relations --db both")
    print("    python -m tools.admin_scripts.fill_subset_gaps --db both")
    print("    python -m tools.admin_scripts.verify_exercise_quality --db both")
    print("=" * 60)


if __name__ == "__main__":
    main()
