#!/usr/bin/env bash
# tools/build/build-backend.sh
# Produce the PyInstaller bundle for the backend API.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

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

echo "=========================================="
echo "  FitManager - Backend PyInstaller Build"
echo "=========================================="

if ! "$PYTHON_BIN" -m PyInstaller --version > /dev/null 2>&1; then
  echo "ERRORE: PyInstaller non installato."
  echo "  pip install pyinstaller"
  exit 1
fi

echo "-> PyInstaller $("$PYTHON_BIN" -m PyInstaller --version)"

echo "-> Avvio build..."
cd "$ROOT"
"$PYTHON_BIN" -m PyInstaller tools/build/fitmanager.spec --noconfirm

EXE_PATH="$ROOT/dist/fitmanager/fitmanager.exe"
if [ ! -f "$EXE_PATH" ]; then
  echo "ERRORE: fitmanager.exe non trovato!"
  exit 1
fi

SIZE=$(du -sh "$ROOT/dist/fitmanager/" | cut -f1)
echo ""
echo "=========================================="
echo "  Build completata!"
echo ""
echo "  Bundle: $ROOT/dist/fitmanager/ ($SIZE)"
echo "  Exe:    $EXE_PATH"
echo ""
echo "  Test:"
echo "    dist/fitmanager/fitmanager.exe --port 8002"
echo "    curl http://localhost:8002/health"
echo "=========================================="
