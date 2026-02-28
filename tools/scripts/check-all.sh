#!/usr/bin/env bash
# tools/scripts/check-all.sh
#
# Gate di qualita': linter backend + build frontend.
# Uso: bash tools/scripts/check-all.sh
#
# Esegui PRIMA di ogni commit. Se fallisce, non committare.

set -euo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

# ── Backend: ruff linter ──
echo "=== Backend: ruff check ==="
if ruff check api/; then
    echo "  OK"
else
    echo "  FAIL — correggi gli errori ruff prima di committare."
    FAIL=1
fi

echo ""

# ── Frontend: TypeScript + Next.js build ──
echo "=== Frontend: next build ==="
if (cd frontend && npx next build); then
    echo "  OK"
else
    echo "  FAIL — correggi gli errori TypeScript/build prima di committare."
    FAIL=1
fi

echo ""

# ── Risultato ──
if [ "$FAIL" -eq 0 ]; then
    echo "=== TUTTO OK — pronto per il commit. ==="
else
    echo "=== ERRORI TROVATI — correggi prima di committare. ==="
    exit 1
fi
