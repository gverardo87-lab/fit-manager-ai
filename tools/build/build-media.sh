#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
# build-media.sh — Copia foto esercizi attivi (in_subset=1) in staging dir
# ══════════════════════════════════════════════════════════════
#
# Output: dist/media/exercises/{id}/ (solo esercizi attivi)
# Uso:    bash tools/build/build-media.sh
#
# Requisiti: Python 3 con sqlite3 (stdlib)

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== build-media.sh ==="

# Pulisci staging dir
rm -rf "$ROOT/dist/media"
mkdir -p "$ROOT/dist/media/exercises"

# Usa Python per tutto (evita problemi path Windows/bash)
python3 << 'PYEOF'
import sqlite3, shutil, os, sys
from pathlib import Path

root = Path(__file__).resolve().parent if '__file__' in dir() else Path.cwd()
# Fallback: trova il root dal working directory
for candidate in [Path.cwd(), Path.cwd().parent]:
    if (candidate / "data" / "crm.db").exists():
        root = candidate
        break

db_path = root / "data" / "crm.db"
src = root / "data" / "media" / "exercises"
dst = root / "dist" / "media" / "exercises"

if not db_path.exists():
    print(f"ERRORE: Database non trovato: {db_path}")
    sys.exit(1)

if not src.exists():
    print(f"ERRORE: Cartella media non trovata: {src}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
ids = [r[0] for r in conn.execute("SELECT id FROM esercizi WHERE in_subset = 1").fetchall()]
conn.close()

copied = 0
skipped = 0
total_size = 0

for eid in sorted(ids):
    src_dir = src / str(eid)
    dst_dir = dst / str(eid)
    if src_dir.is_dir():
        shutil.copytree(str(src_dir), str(dst_dir))
        for f in dst_dir.iterdir():
            if f.is_file():
                total_size += f.stat().st_size
        copied += 1
    else:
        skipped += 1

print(f"Esercizi attivi: {len(ids)}")
print(f"Con foto copiate: {copied}")
print(f"Senza foto: {skipped}")
print(f"Dimensione totale: {total_size / 1024 / 1024:.1f} MB")
print(f"Output: {dst}")
PYEOF

echo "=== build-media.sh completato ==="
