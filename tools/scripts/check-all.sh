#!/usr/bin/env bash
# tools/scripts/check-all.sh
#
# Quality gate: backend lint + frontend production build.
# Run before each release-oriented commit.

set -euo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

resolve_ruff() {
    if [ -x "venv/Scripts/ruff.exe" ]; then
        printf '%s\n' "venv/Scripts/ruff.exe"
        return 0
    fi

    if command -v ruff >/dev/null 2>&1; then
        command -v ruff
        return 0
    fi

    echo "ERRORE: ruff non trovato. Attiva la venv o installa ruff." >&2
    exit 1
}

RUFF_BIN="$(resolve_ruff)"

echo "=== Backend: ruff check ==="
if "$RUFF_BIN" check api/; then
    echo "  OK"
else
    echo "  FAIL - correggi gli errori ruff prima di committare."
    FAIL=1
fi

echo ""

echo "=== Frontend: next build ==="
if (cd frontend && npx next build); then
    echo "  OK"
else
    echo "  FAIL - correggi gli errori TypeScript/build prima di committare."
    FAIL=1
fi

echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "=== TUTTO OK - pronto per il commit. ==="
else
    echo "=== ERRORI TROVATI - correggi prima di committare. ==="
    exit 1
fi
