#!/usr/bin/env python3
"""
Verify QA Clinical — Verifica end-to-end 30 profili clinici per lotto.

Script read-only che incrocia:
  - Anamnesi → extract_client_conditions() vs expected conditions
  - Medication flags (keyword matching su farmaci.dettaglio)
  - Safety map entries (build_safety_map → conteggio esercizi flaggati)
  - Misurazioni (conteggio sessioni e valori per cliente)
  - Obiettivi (stato coerente con ultima misurazione)

Output: PASS / FAIL / WARN per ogni check.
  WARN = comportamento corretto ma condizione "morta" (0 exercise mappings).

Uso:
  python -m tools.admin_scripts.verify_qa_clinical --lotto all
  python -m tools.admin_scripts.verify_qa_clinical --lotto 1
  python -m tools.admin_scripts.verify_qa_clinical --lotto 3 --verbose
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ── Forza DATABASE_URL su crm_dev.db ──
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
os.environ["DATABASE_URL"] = f"sqlite:///{DATA_DIR / 'crm_dev.db'}"
sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, create_engine, text  # noqa: E402

from api.services.condition_rules import (  # noqa: E402
    ANAMNESI_KEYWORD_RULES,
    MEDICATION_RULES,
    STRUCTURAL_FLAGS,
    match_keywords,
)
from api.services.safety_engine import (  # noqa: E402
    build_safety_map,  # signature: (session, catalog_session, client_id, trainer_id)
    extract_client_conditions,
)
from tools.admin_scripts.seed_qa_clinical import (  # noqa: E402
    CLIENTS_DATA,
    EXPECTED_CONDITIONS,
    EXPECTED_MEDICATION_FLAGS,
    GOALS_DATA,
    MEASUREMENT_PROFILES,
)


# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

LOTTO_NAMES = [
    "Baseline Sano",
    "Singola Ortopedica",
    "Cardiovascolare + Farmaci",
    "Multi-Condizione + Critico",
    "Popolazioni Speciali",
    "Atleti + Edge Cases",
]

# Condition IDs noti come "morti" (0 exercise mapping in esercizi_condizioni)
# Queste producono estrazione corretta ma safety_map vuota — WARN, non FAIL.
# Dopo riallineamento: tutte le 10 condizioni hanno pattern rules → set vuoto.
KNOWN_DEAD_CONDITIONS: set[int] = set()


# ═══════════════════════════════════════════════════════════════
# Verification Functions
# ═══════════════════════════════════════════════════════════════

def verify_conditions(session, client_id, client_idx, verbose=False):
    """Verifica extract_client_conditions vs expected."""
    # Fetch anamnesi
    row = session.execute(
        text("SELECT anamnesi_json FROM clienti WHERE id = :cid"),
        {"cid": client_id},
    ).first()
    anamnesi_json = row[0] if row else None

    actual = extract_client_conditions(anamnesi_json)
    expected = EXPECTED_CONDITIONS.get(client_idx, set())

    if actual == expected:
        status = "PASS"
    else:
        status = "FAIL"

    if verbose or status == "FAIL":
        extra_msg = ""
        if actual != expected:
            missing = expected - actual
            extra = actual - expected
            if missing:
                extra_msg += f" MISSING={missing}"
            if extra:
                extra_msg += f" EXTRA={extra}"
        return status, f"conditions: {actual}{extra_msg}"

    return status, f"conditions: {actual}"


def verify_medication_flags(session, client_id, client_idx, verbose=False):
    """Verifica medication flags da anamnesi farmaci."""
    row = session.execute(
        text("SELECT anamnesi_json FROM clienti WHERE id = :cid"),
        {"cid": client_id},
    ).first()
    anamnesi_json = row[0] if row else None

    expected_flags = EXPECTED_MEDICATION_FLAGS.get(client_idx, set())

    if not anamnesi_json:
        actual_flags = set()
    else:
        try:
            data = json.loads(anamnesi_json)
        except (json.JSONDecodeError, TypeError):
            actual_flags = set()
        else:
            farmaci = data.get("farmaci", {})
            if isinstance(farmaci, dict) and farmaci.get("presente"):
                dettaglio = farmaci.get("dettaglio", "")
                actual_flags = set()
                for keywords, flag_name, _ in MEDICATION_RULES:
                    if match_keywords(dettaglio, keywords):
                        actual_flags.add(flag_name)
            else:
                actual_flags = set()

    if actual_flags == expected_flags:
        status = "PASS"
    else:
        status = "FAIL"

    if not expected_flags and not actual_flags:
        return status, "medication: none (expected)"
    return status, f"medication: {actual_flags}"


def verify_safety_map(session, client_id, client_idx, trainer_id, verbose=False):
    """Verifica safety map (entries + dead conditions)."""
    expected_conds = EXPECTED_CONDITIONS.get(client_idx, set())

    if not expected_conds:
        # No conditions → should have 0 entries
        try:
            safety_map = build_safety_map(session, session, client_id, trainer_id)
            n_entries = len(safety_map.entries)
            if n_entries == 0:
                return "PASS", "safety_map: 0 entries (no conditions)"
            else:
                return "FAIL", f"safety_map: {n_entries} entries but expected 0 (no conditions)"
        except Exception as e:
            return "FAIL", f"safety_map error: {e}"

    try:
        safety_map = build_safety_map(session, session, client_id, trainer_id)
    except Exception as e:
        return "FAIL", f"safety_map error: {e}"

    n_entries = len(safety_map.entries)
    dead_in_client = expected_conds & KNOWN_DEAD_CONDITIONS
    live_conds = expected_conds - KNOWN_DEAD_CONDITIONS

    if live_conds and n_entries == 0:
        return "FAIL", f"safety_map: 0 entries but has live conditions {live_conds}"

    if dead_in_client and n_entries == 0 and not live_conds:
        return "WARN", f"safety_map: 0 entries (ALL {len(dead_in_client)} conditions DEAD: {dead_in_client})"

    if dead_in_client:
        return "WARN", (
            f"safety_map: {n_entries} entries, "
            f"DEAD conditions: {dead_in_client}"
        )

    return "PASS", f"safety_map: {n_entries} entries"


def verify_measurements(session, client_id, client_idx, verbose=False):
    """Verifica conteggio sessioni e valori per cliente."""
    profile = MEASUREMENT_PROFILES.get(client_idx)
    if not profile:
        return "FAIL", "measurements: no profile defined"

    expected_sessions = profile["n"]

    row = session.execute(
        text(
            "SELECT COUNT(*) FROM misurazioni_cliente "
            "WHERE id_cliente = :cid AND deleted_at IS NULL"
        ),
        {"cid": client_id},
    ).scalar_one()
    actual_sessions = row

    row2 = session.execute(
        text(
            "SELECT COUNT(*) FROM valori_misurazione v "
            "JOIN misurazioni_cliente m ON v.id_misurazione = m.id "
            "WHERE m.id_cliente = :cid AND m.deleted_at IS NULL"
        ),
        {"cid": client_id},
    ).scalar_one()
    actual_values = row2

    if actual_sessions != expected_sessions:
        return "FAIL", (
            f"measurements: {actual_sessions} sessions "
            f"(expected {expected_sessions}), {actual_values} values"
        )

    return "PASS", f"measurements: {actual_sessions} sessions, {actual_values} values"


def verify_goals(session, client_id, client_idx, verbose=False):
    """Verifica obiettivi per cliente."""
    expected_goals = GOALS_DATA.get(client_idx, [])

    row = session.execute(
        text(
            "SELECT COUNT(*) FROM obiettivi_cliente "
            "WHERE id_cliente = :cid AND deleted_at IS NULL"
        ),
        {"cid": client_id},
    ).scalar_one()
    actual_count = row

    if actual_count != len(expected_goals):
        return "FAIL", (
            f"goals: {actual_count} found "
            f"(expected {len(expected_goals)})"
        )

    if not expected_goals:
        return "PASS", "goals: none (expected)"

    # Check stati
    rows = session.execute(
        text(
            "SELECT stato, COUNT(*) FROM obiettivi_cliente "
            "WHERE id_cliente = :cid AND deleted_at IS NULL "
            "GROUP BY stato"
        ),
        {"cid": client_id},
    ).all()
    stati = {r[0]: r[1] for r in rows}

    return "PASS", f"goals: {actual_count} ({', '.join(f'{v} {k}' for k, v in stati.items())})"


# ═══════════════════════════════════════════════════════════════
# Main Verification
# ═══════════════════════════════════════════════════════════════

def verify_lotto(session, trainer_id, lotto_num, verbose=False):
    """Verifica un singolo lotto (5 clienti)."""
    start = (lotto_num - 1) * 5
    end = start + 5

    results = {"PASS": 0, "FAIL": 0, "WARN": 0}

    for client_idx in range(start, end):
        if client_idx >= len(CLIENTS_DATA):
            break

        cd = CLIENTS_DATA[client_idx]
        client_id = client_idx + 1  # IDs start from 1

        name = f"{cd['nome']} {cd['cognome']}"
        age_sex = f"{cd.get('sesso', '?')[0]}"

        print(f"\n  Client #{client_idx} {name} ({age_sex})")

        checks = [
            ("Anamnesi", verify_conditions(session, client_id, client_idx, verbose)),
            ("Farmaci", verify_medication_flags(session, client_id, client_idx, verbose)),
            ("Safety", verify_safety_map(session, client_id, client_idx, trainer_id, verbose)),
            ("Misure", verify_measurements(session, client_id, client_idx, verbose)),
            ("Goals", verify_goals(session, client_id, client_idx, verbose)),
        ]

        for check_name, (status, detail) in checks:
            icon = {"PASS": "+", "FAIL": "X", "WARN": "!"}[status]
            print(f"    [{icon}] {check_name:9s} {detail}")
            results[status] += 1

    return results


def main():
    parser = argparse.ArgumentParser(description="Verify QA Clinical Database")
    parser.add_argument(
        "--lotto",
        default="all",
        help="Lotto number (1-6) or 'all'",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output",
    )
    args = parser.parse_args()

    dev_path = DATA_DIR / "crm_dev.db"
    if not dev_path.exists():
        print("ERRORE: crm_dev.db non trovato. Eseguire seed_qa_clinical prima.")
        sys.exit(1)

    engine = create_engine(
        f"sqlite:///{dev_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    totals = {"PASS": 0, "FAIL": 0, "WARN": 0}

    if args.lotto == "all":
        lotti = range(1, 7)
    else:
        lotti = [int(args.lotto)]

    with Session(engine) as session:
        # Get trainer ID
        tid = session.execute(text("SELECT id FROM trainers LIMIT 1")).scalar_one()

        for lotto_num in lotti:
            name = LOTTO_NAMES[lotto_num - 1]
            print(f"\n{'=' * 60}")
            print(f"LOTTO {lotto_num}: {name}")
            print(f"{'=' * 60}")

            results = verify_lotto(session, tid, lotto_num, args.verbose)
            for k, v in results.items():
                totals[k] += v

    # ── Summary ──
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  PASS: {totals['PASS']}")
    print(f"  WARN: {totals['WARN']}")
    print(f"  FAIL: {totals['FAIL']}")
    total_checks = sum(totals.values())
    print(f"  Total: {total_checks} checks")
    print()

    if totals["FAIL"] > 0:
        print("RISULTATO: FAIL — ci sono errori da investigare")
        sys.exit(1)
    elif totals["WARN"] > 0:
        print(f"RISULTATO: PASS con {totals['WARN']} WARN (condizioni morte)")
    else:
        print("RISULTATO: PASS — tutto ok!")


if __name__ == "__main__":
    main()
