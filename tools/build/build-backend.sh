#!/usr/bin/env bash
# tools/build/build-backend.sh
# Produce il bundle PyInstaller del backend API.
#
# Output: dist/fitmanager/ (directory con fitmanager.exe)
# Requisiti: PyInstaller (pip install pyinstaller)
#
# Uso:
#   bash tools/build/build-backend.sh
#
# Test manuale:
#   dist/fitmanager/fitmanager.exe --port 8002

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "══════════════════════════════════════════"
echo "  FitManager — Backend PyInstaller Build"
echo "══════════════════════════════════════════"

# ── 1. Verifica PyInstaller ──
if ! python -m PyInstaller --version > /dev/null 2>&1; then
  echo "ERRORE: PyInstaller non installato."
  echo "  pip install pyinstaller"
  exit 1
fi

echo "→ PyInstaller $(python -m PyInstaller --version)"

# ── 2. Build ──
echo "→ Avvio build..."
cd "$ROOT"
python -m PyInstaller tools/build/fitmanager.spec --noconfirm

# ── 3. Verifica output ──
EXE_PATH="$ROOT/dist/fitmanager/fitmanager.exe"
if [ ! -f "$EXE_PATH" ]; then
  echo "ERRORE: fitmanager.exe non trovato!"
  exit 1
fi

SIZE=$(du -sh "$ROOT/dist/fitmanager/" | cut -f1)
echo ""
echo "══════════════════════════════════════════"
echo "  Build completata!"
echo ""
echo "  Bundle: $ROOT/dist/fitmanager/ ($SIZE)"
echo "  Exe:    $EXE_PATH"
echo ""
echo "  Test:"
echo "    dist/fitmanager/fitmanager.exe --port 8002"
echo "    curl http://localhost:8002/health"
echo "══════════════════════════════════════════"
