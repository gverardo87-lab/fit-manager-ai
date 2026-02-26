"""
Diagnostica matching free-exercise-db -> nostri 345 esercizi.

Esegui dalla root:
  python -m tools.admin_scripts.fdb_diagnostic

Output: report match/unmatch + template alias dict.
"""

import json
import os
import sqlite3
from pathlib import Path

from tools.admin_scripts.fdb_mapping import normalize_name, FDB_NAME_ALIASES

# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FDB_JSON = BASE_DIR / "tools" / "external" / "free-exercise-db" / "dist" / "exercises.json"
DB_PATH = os.environ.get("DATABASE_URL", "").replace("sqlite:///", "") or str(BASE_DIR / "data" / "crm_dev.db")


def main():
    print("=" * 60)
    print("FDB Diagnostic — Match Analysis")
    print("=" * 60)

    # Carica FDB
    with open(FDB_JSON) as f:
        fdb_exercises = json.load(f)
    print(f"\nFDB: {len(fdb_exercises)} esercizi")

    # Carica nostri esercizi
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, nome, nome_en FROM esercizi WHERE is_builtin = 1 AND deleted_at IS NULL"
    ).fetchall()
    conn.close()
    print(f"DB:  {len(rows)} esercizi builtin")

    # Costruisci lookup: normalized_nome_en -> (id, nome, nome_en)
    our_by_norm: dict[str, tuple[int, str, str]] = {}
    our_by_nome_en: dict[str, tuple[int, str, str]] = {}
    for row_id, nome, nome_en in rows:
        if nome_en:
            norm = normalize_name(nome_en)
            our_by_norm[norm] = (row_id, nome, nome_en)
            our_by_nome_en[nome_en.lower()] = (row_id, nome, nome_en)

    # Match
    matched: list[tuple[dict, int, str, str]] = []  # (fdb, our_id, our_nome, our_nome_en)
    unmatched_fdb: list[dict] = []
    matched_our_ids: set[int] = set()

    for fdb in fdb_exercises:
        fdb_name = fdb["name"]
        fdb_norm = normalize_name(fdb_name)

        # 1. Exact match su normalized name
        if fdb_norm in our_by_norm:
            our = our_by_norm[fdb_norm]
            matched.append((fdb, our[0], our[1], our[2]))
            matched_our_ids.add(our[0])
            continue

        # 2. Alias match
        alias_target = FDB_NAME_ALIASES.get(fdb_name)
        if alias_target and alias_target.lower() in our_by_nome_en:
            our = our_by_nome_en[alias_target.lower()]
            matched.append((fdb, our[0], our[1], our[2]))
            matched_our_ids.add(our[0])
            continue

        # 3. Unmatched
        unmatched_fdb.append(fdb)

    unmatched_ours = [(row_id, nome, nome_en) for row_id, nome, nome_en in rows if row_id not in matched_our_ids]

    # Report
    print(f"\n{'-' * 60}")
    print(f"RISULTATI:")
    print(f"  Matchati:              {len(matched)}")
    print(f"  FDB senza match:       {len(unmatched_fdb)} (candidati import)")
    print(f"  Nostri senza match:    {len(unmatched_ours)} (niente immagine FDB)")
    print(f"{'-' * 60}")

    # Dettaglio matchati (primi 20)
    print(f"\nMATCHATI (primi 20):")
    for fdb, our_id, our_nome, our_nome_en in matched[:20]:
        images = len(fdb.get("images", []))
        print(f"  [{our_id:3d}] {our_nome_en:<40s} -> {fdb['name']:<40s} ({images} img)")

    # Dettaglio FDB non matchati (primi 30)
    print(f"\nFDB SENZA MATCH (primi 30 — candidati import):")
    for fdb in unmatched_fdb[:30]:
        images = len(fdb.get("images", []))
        print(f"  {fdb['name']:<50s} [{fdb['category']:<12s}] ({images} img)")

    # Dettaglio nostri senza match (primi 30)
    print(f"\nNOSTRI SENZA MATCH (primi 30 — niente immagine FDB):")
    for row_id, nome, nome_en in unmatched_ours[:30]:
        print(f"  [{row_id:3d}] {nome_en or '(no nome_en)':<40s} ({nome})")

    # Statistiche immagini
    total_images_matched = sum(len(fdb.get("images", [])) for fdb, _, _, _ in matched)
    total_images_unmatched = sum(len(fdb.get("images", [])) for fdb in unmatched_fdb)
    print(f"\nIMMAGINI:")
    print(f"  Matchati:    {total_images_matched} immagini")
    print(f"  Nuovi:       {total_images_unmatched} immagini")
    print(f"  Totale:      {total_images_matched + total_images_unmatched} immagini")

    # Genera template alias (per curare manualmente)
    if unmatched_fdb:
        print(f"\n{'-' * 60}")
        print("ALIAS TEMPLATE (copia in fdb_mapping.py -> FDB_NAME_ALIASES):")
        print("FDB_NAME_ALIASES = {")
        for fdb in sorted(unmatched_fdb, key=lambda x: x["name"])[:50]:
            print(f'    "{fdb["name"]}": "",  # {fdb["category"]}')
        print("    # ... (mostra solo primi 50)")
        print("}")


if __name__ == "__main__":
    main()
