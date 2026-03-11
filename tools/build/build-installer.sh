#!/usr/bin/env bash
# build-installer.sh -- Rebuild frontend, backend, media staging and Inno Setup installer.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INSTALLER_VERSION="1.0.2"
ISCC_PATH=""
SKIP_CHECKS=0

usage() {
  cat <<EOF
Usage: bash tools/build/build-installer.sh [--skip-checks] [--iscc /path/to/ISCC.exe]

Build order:
  1. check-all.sh (unless --skip-checks)
  2. build-frontend.sh
  3. build-backend.sh
  4. build-media.sh
  5. Inno Setup compilation
EOF
}

resolve_iscc() {
  if [ -n "$ISCC_PATH" ]; then
    printf '%s\n' "$ISCC_PATH"
    return 0
  fi

  local candidates=(
    "C:/Program Files (x86)/Inno Setup 6/ISCC.exe"
    "C:/Program Files/Inno Setup 6/ISCC.exe"
    "C:/Users/gvera/AppData/Local/Programs/Inno Setup 6/ISCC.exe"
  )

  local candidate
  for candidate in "${candidates[@]}"; do
    if [ -f "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  echo "ERRORE: ISCC.exe non trovato. Usa --iscc per indicare il path." >&2
  exit 1
}

while [ $# -gt 0 ]; do
  case "$1" in
    --skip-checks)
      SKIP_CHECKS=1
      shift
      ;;
    --iscc)
      [ $# -ge 2 ] || { echo "ERRORE: --iscc richiede un path." >&2; exit 1; }
      ISCC_PATH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERRORE: argomento sconosciuto: $1" >&2
      usage
      exit 1
      ;;
  esac
done

echo "=== build-installer.sh ==="
echo "Project root: $ROOT"
echo "Installer version: $INSTALLER_VERSION"

RELEASE_DATA_DIR="$ROOT/dist/release-data"

if [ "$SKIP_CHECKS" -eq 0 ]; then
  bash "$ROOT/tools/scripts/check-all.sh"
else
  echo "Skipping quality gate (--skip-checks)."
fi

bash "$ROOT/tools/build/build-frontend.sh"
bash "$ROOT/tools/build/build-backend.sh"
bash "$ROOT/tools/build/build-media.sh"

echo "Staging immutable release data..."
mkdir -p "$RELEASE_DATA_DIR"
cp "$ROOT/data/catalog.db" "$RELEASE_DATA_DIR/catalog.db"
cp "$ROOT/data/license_public.pem" "$RELEASE_DATA_DIR/license_public.pem"

ISCC_BIN="$(resolve_iscc)"
echo "Using ISCC: $ISCC_BIN"

"$ISCC_BIN" "$ROOT/installer/fitmanager.iss"

echo "Installer atteso: $ROOT/dist/FitManager_Setup_${INSTALLER_VERSION}.exe"
echo "=== build-installer.sh completato ==="
