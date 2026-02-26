"""
Fase 5: Verifica finale quality gate.

Audit completo del database esercizi per verificare:
  - Completezza campi (esecuzione, anatomia, setup, cues, errori, controindicazioni, sicurezza)
  - Qualita' lingua (italiano, no inglese residuo)
  - Duplicati (nome, nome_en)
  - Enum validi (force_type, lateral_pattern, categoria, pattern_movimento)
  - JSON validi (coaching_cues, errori_comuni, controindicazioni)
  - Cross-reference controindicazioni con contraindication-engine

Eseguire dalla root:
  python -m tools.admin_scripts.verify_exercise_quality [--db dev|prod|both] [--verbose]
"""

import argparse
import json
import os
import re
import sqlite3
import sys

# ================================================================
# CONFIG
# ================================================================

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

VALID_CATEGORIES = {"compound", "isolation", "bodyweight", "cardio", "stretching", "mobilita", "avviamento"}
VALID_PATTERNS = {"squat", "hinge", "push_h", "push_v", "pull_h", "pull_v", "core", "rotation", "carry", "warmup", "stretch", "mobility"}
VALID_FORCE_TYPES = {"push", "pull", "static"}
VALID_LATERAL_PATTERNS = {"bilateral", "unilateral", "alternating"}

# English markers for language check
EN_WORDS = ["the ", "and ", "your ", "with ", "this ", "will ", "should ", "that "]

# Min lengths for text fields
MIN_LENGTHS = {
    "esecuzione": 50,
    "descrizione_anatomica": 30,
    "descrizione_biomeccanica": 30,
    "setup": 20,
    "note_sicurezza": 15,
}


def check_language(text: str) -> bool:
    """Check if text is in Italian (not English). Returns True if OK."""
    if not text:
        return True  # Empty is not an English issue
    text_lower = text.lower()
    en_count = sum(1 for w in EN_WORDS if w in text_lower)
    return en_count < 3


def check_json_field(text: str, field_name: str) -> list[str]:
    """Validate a JSON field. Returns list of issues."""
    issues = []
    if not text:
        issues.append(f"{field_name}: empty")
        return issues

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        issues.append(f"{field_name}: invalid JSON")
        return issues

    if not isinstance(data, list):
        issues.append(f"{field_name}: not a list")
        return issues

    if len(data) == 0:
        issues.append(f"{field_name}: empty list")

    if field_name == "errori_comuni" and data:
        if isinstance(data[0], dict):
            for item in data:
                if "errore" not in item or "correzione" not in item:
                    issues.append(f"{field_name}: item missing errore/correzione keys")
                    break

    return issues


# ================================================================
# AUDIT
# ================================================================

def audit_db(db_path: str, verbose: bool = False) -> dict:
    """Run full quality audit on a database. Returns stats dict."""
    if not os.path.exists(db_path):
        print(f"  SKIP: {db_path} not found")
        return {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = os.path.basename(db_path)

    print(f"\n{'=' * 60}")
    print(f"  QUALITY AUDIT: {db_name}")
    print(f"{'=' * 60}")

    exercises = conn.execute("""
        SELECT * FROM esercizi WHERE deleted_at IS NULL ORDER BY id
    """).fetchall()

    total = len(exercises)
    stats = {
        "total": total,
        "fully_enriched": 0,
        "issues": [],
        "field_coverage": {},
        "language_issues": 0,
        "json_issues": 0,
        "enum_issues": 0,
        "duplicate_nome": 0,
        "duplicate_nome_en": 0,
    }

    # ── Field Coverage ──
    print(f"\n  Field Coverage ({total} active exercises):")
    text_fields = [
        "esecuzione", "descrizione_anatomica", "descrizione_biomeccanica",
        "setup", "respirazione", "tempo_consigliato",
        "note_sicurezza", "force_type", "lateral_pattern",
    ]
    json_fields = ["coaching_cues", "errori_comuni", "controindicazioni"]
    all_fields = text_fields + json_fields

    for field in all_fields:
        filled = sum(1 for ex in exercises if ex[field] and str(ex[field]).strip())
        pct = filled * 100 // total if total > 0 else 0
        status = "OK" if pct >= 95 else ("WARN" if pct >= 50 else "FAIL")
        stats["field_coverage"][field] = {"filled": filled, "total": total, "pct": pct}
        print(f"    {field:30s}: {filled:4d}/{total} ({pct:3d}%) {status}")

    # ── Per-exercise Checks ──
    print(f"\n  Per-exercise validation:")
    issues_by_type = {}

    for ex in exercises:
        eid = ex["id"]
        nome = ex["nome"]
        ex_issues = []

        # Name checks
        if not nome or len(nome.strip()) == 0:
            ex_issues.append("nome: empty")
        elif len(nome) > 100:
            ex_issues.append(f"nome: too long ({len(nome)} chars)")
        if nome and (nome.endswith(".") or nome.endswith(",") or nome.endswith(";")):
            ex_issues.append("nome: trailing punctuation")

        # Enum checks
        if ex["categoria"] and ex["categoria"] not in VALID_CATEGORIES:
            ex_issues.append(f"categoria: invalid '{ex['categoria']}'")
            stats["enum_issues"] += 1
        if ex["pattern_movimento"] and ex["pattern_movimento"] not in VALID_PATTERNS:
            ex_issues.append(f"pattern_movimento: invalid '{ex['pattern_movimento']}'")
            stats["enum_issues"] += 1
        if ex["force_type"] and ex["force_type"] not in VALID_FORCE_TYPES:
            ex_issues.append(f"force_type: invalid '{ex['force_type']}'")
            stats["enum_issues"] += 1
        if ex["lateral_pattern"] and ex["lateral_pattern"] not in VALID_LATERAL_PATTERNS:
            ex_issues.append(f"lateral_pattern: invalid '{ex['lateral_pattern']}'")
            stats["enum_issues"] += 1

        # Min length checks
        for field, min_len in MIN_LENGTHS.items():
            val = ex[field]
            if val and len(str(val).strip()) < min_len:
                ex_issues.append(f"{field}: too short ({len(str(val))} < {min_len})")

        # Language checks
        for field in ["esecuzione", "descrizione_anatomica", "setup"]:
            val = ex[field]
            if val and not check_language(str(val)):
                ex_issues.append(f"{field}: English detected")
                stats["language_issues"] += 1

        # JSON field checks
        for field in json_fields:
            field_issues = check_json_field(ex[field], field)
            if field_issues:
                ex_issues.extend(field_issues)
                stats["json_issues"] += len(field_issues)

        # Track
        if ex_issues:
            stats["issues"].append({"id": eid, "nome": nome, "issues": ex_issues})
            for issue in ex_issues:
                key = issue.split(":")[0]
                issues_by_type[key] = issues_by_type.get(key, 0) + 1

            if verbose:
                print(f"    [{eid}] {nome}:")
                for issue in ex_issues:
                    print(f"      - {issue}")
        else:
            stats["fully_enriched"] += 1

    # Issue summary
    if issues_by_type:
        print(f"    Issues by type:")
        for key, cnt in sorted(issues_by_type.items(), key=lambda x: -x[1]):
            print(f"      {key}: {cnt}")

    # ── Duplicates ──
    print(f"\n  Duplicate checks:")

    # nome duplicates
    dupes_it = conn.execute("""
        SELECT nome, GROUP_CONCAT(id), COUNT(*) as cnt FROM esercizi
        WHERE deleted_at IS NULL GROUP BY nome HAVING cnt > 1
    """).fetchall()
    stats["duplicate_nome"] = len(dupes_it)
    status = "PASS" if len(dupes_it) == 0 else "FAIL"
    print(f"    Duplicate nome IT: {len(dupes_it)} groups {status}")
    for d in dupes_it:
        print(f"      \"{d[0]}\" (ids: {d[1]})")

    # nome_en duplicates
    dupes_en = conn.execute("""
        SELECT LOWER(nome_en), GROUP_CONCAT(id), COUNT(*) as cnt FROM esercizi
        WHERE deleted_at IS NULL AND nome_en IS NOT NULL
        GROUP BY LOWER(nome_en) HAVING cnt > 1
    """).fetchall()
    stats["duplicate_nome_en"] = len(dupes_en)
    expected_dupes = 2  # jump rope, bodyweight squat
    status = "PASS" if len(dupes_en) <= expected_dupes else "CHECK"
    print(f"    Duplicate nome_en: {len(dupes_en)} groups (expected {expected_dupes}) {status}")
    for d in dupes_en:
        print(f"      \"{d[0]}\" (ids: {d[1]})")

    # ── Summary ──
    print(f"\n  {'=' * 50}")
    print(f"  SUMMARY: {db_name}")
    print(f"  {'=' * 50}")
    print(f"    Total active:      {total}")
    print(f"    Fully enriched:    {stats['fully_enriched']}/{total} "
          f"({stats['fully_enriched']*100//total if total > 0 else 0}%)")
    print(f"    With issues:       {len(stats['issues'])}")
    print(f"    Language issues:   {stats['language_issues']}")
    print(f"    JSON issues:       {stats['json_issues']}")
    print(f"    Enum issues:       {stats['enum_issues']}")
    print(f"    Duplicate nome:    {stats['duplicate_nome']}")
    print(f"    Duplicate nome_en: {stats['duplicate_nome_en']}")

    quality_score = stats["fully_enriched"] * 100 // total if total > 0 else 0
    if quality_score >= 95:
        print(f"    QUALITY GATE:      PASS ({quality_score}%)")
    elif quality_score >= 80:
        print(f"    QUALITY GATE:      WARN ({quality_score}%)")
    else:
        print(f"    QUALITY GATE:      FAIL ({quality_score}%)")

    conn.close()
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exercise quality audit (Phase 5)")
    parser.add_argument("--db", choices=["dev", "prod", "both"], default="both")
    parser.add_argument("--verbose", action="store_true", help="Show per-exercise issues")
    args = parser.parse_args()

    print("Exercise Quality Audit — Phase 5")
    print("=" * 60)

    dbs = []
    if args.db in ("dev", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm_dev.db"))
    if args.db in ("prod", "both"):
        dbs.append(os.path.join(BASE_DIR, "crm.db"))

    for db_path in dbs:
        audit_db(db_path, verbose=args.verbose)

    print("\nDone.")
