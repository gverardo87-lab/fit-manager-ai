#!/usr/bin/env bash
# build-media.sh -- Stage exercise photos for the active catalog subset.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CATALOG_DB="${FITMANAGER_CATALOG_DB:-$ROOT/data/catalog.db}"
EXPECTED_ACTIVE_COUNT="${FITMANAGER_EXPECTED_ACTIVE_COUNT:-391}"
MEDIA_SRC="$ROOT/data/media/exercises"
MEDIA_DST="$ROOT/dist/media/exercises"

resolve_python() {
  if [ -x "$ROOT/venv/Scripts/python.exe" ]; then
    printf '%s\n' "$ROOT/venv/Scripts/python.exe"
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi

  echo "ERRORE: Python non trovato. Attiva la venv o installa Python." >&2
  exit 1
}

PYTHON_BIN="$(resolve_python)"

echo "=== build-media.sh ==="
echo "Catalog DB: $CATALOG_DB"
echo "Expected active exercises: $EXPECTED_ACTIVE_COUNT"

rm -rf "$ROOT/dist/media"
mkdir -p "$MEDIA_DST"

"$PYTHON_BIN" - "$ROOT" "$CATALOG_DB" "$MEDIA_SRC" "$MEDIA_DST" "$EXPECTED_ACTIVE_COUNT" <<'PYEOF'
import shutil
import sqlite3
import sys
from pathlib import Path

root = Path(sys.argv[1])
catalog_db = Path(sys.argv[2])
src = Path(sys.argv[3])
dst = Path(sys.argv[4])
expected_count = int(sys.argv[5])

if not catalog_db.exists():
    print(f"ERRORE: Catalog DB non trovato: {catalog_db}", file=sys.stderr)
    sys.exit(1)

if not src.exists():
    print(f"ERRORE: Cartella media non trovata: {src}", file=sys.stderr)
    sys.exit(1)

query = """
SELECT DISTINCT id_esercizio
FROM (
    SELECT id_esercizio FROM esercizi_muscoli
    UNION
    SELECT id_esercizio FROM esercizi_articolazioni
    UNION
    SELECT id_esercizio FROM esercizi_condizioni
)
ORDER BY id_esercizio
"""

with sqlite3.connect(str(catalog_db)) as conn:
    ids = [row[0] for row in conn.execute(query).fetchall()]

if not ids:
    print("ERRORE: catalog.db non ha restituito esercizi attivi.", file=sys.stderr)
    sys.exit(1)

if len(ids) != expected_count:
    print(
        f"ERRORE: attesi {expected_count} esercizi attivi, trovati {len(ids)} in catalog.db.",
        file=sys.stderr,
    )
    sys.exit(1)

copied = 0
skipped = 0
total_size = 0

for exercise_id in ids:
    src_dir = src / str(exercise_id)
    dst_dir = dst / str(exercise_id)
    if not src_dir.is_dir():
        skipped += 1
        continue

    shutil.copytree(src_dir, dst_dir)
    for file_path in dst_dir.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    copied += 1

print(f"Project root: {root}")
print(f"Esercizi attivi da catalog.db: {len(ids)}")
print(f"Cartelle foto copiate: {copied}")
print(f"Esercizi senza foto: {skipped}")
print(f"Dimensione totale staging: {total_size / 1024 / 1024:.1f} MB")
print(f"Output: {dst}")
PYEOF

echo "=== build-media.sh completato ==="
