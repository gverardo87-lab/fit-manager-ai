#!/usr/bin/env bash
# tools/build/build-frontend.sh
# Produce il bundle Next.js standalone pronto per distribuzione.
#
# Output: frontend/.next/standalone/  (con server.js, static, public)
# Requisiti: Node.js 18+, npm
#
# Uso:
#   bash tools/build/build-frontend.sh
#
# Test manuale:
#   PORT=3002 HOSTNAME=0.0.0.0 node frontend/.next/standalone/server.js

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FRONTEND="$ROOT/frontend"

echo "══════════════════════════════════════════"
echo "  FitManager — Frontend Standalone Build"
echo "══════════════════════════════════════════"

# ── 1. Build Next.js ──
echo ""
echo "→ npm run build..."
cd "$FRONTEND"
npm run build

# ── 2. Verifica server.js ──
if [ ! -f ".next/standalone/server.js" ]; then
  echo "ERRORE: .next/standalone/server.js non trovato!"
  echo "Verifica che next.config.ts abbia output: \"standalone\""
  exit 1
fi
echo "✓ server.js presente"

# ── 3. Copia static assets (non inclusi automaticamente) ──
echo "→ Copia .next/static → standalone/.next/static..."
cp -r .next/static .next/standalone/.next/static

echo "→ Copia public/ → standalone/public/..."
if [ -d "public" ]; then
  cp -r public .next/standalone/public
else
  mkdir -p .next/standalone/public
fi

# ── 4. Verifica finale ──
echo ""
echo "══════════════════════════════════════════"
echo "  Build completata!"
echo ""
echo "  Bundle: $FRONTEND/.next/standalone/"
echo "  Server: $FRONTEND/.next/standalone/server.js"
echo ""
echo "  Test:"
echo "    PORT=3002 HOSTNAME=0.0.0.0 node frontend/.next/standalone/server.js"
echo "══════════════════════════════════════════"
