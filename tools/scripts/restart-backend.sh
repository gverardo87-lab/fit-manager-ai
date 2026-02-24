#!/usr/bin/env bash
# tools/scripts/restart-backend.sh
#
# Restart pulito di un backend uvicorn su Windows.
# Killa il vecchio (inclusi worker figli), poi rilancia.
#
# Uso:
#   bash tools/scripts/restart-backend.sh dev     → porta 8001, crm_dev.db
#   bash tools/scripts/restart-backend.sh prod    → porta 8000, crm.db

set -euo pipefail

cd "$(dirname "$0")/../.."

ENV="${1:?Uso: restart-backend.sh <dev|prod>}"

case "$ENV" in
    dev)
        PORT=8001
        DB_URL="sqlite:///data/crm_dev.db"
        ;;
    prod)
        PORT=8000
        DB_URL="sqlite:///data/crm.db"
        ;;
    *)
        echo "Errore: usa 'dev' o 'prod'"
        exit 1
        ;;
esac

echo "=== Restart backend $ENV (porta $PORT) ==="

# Step 1: Kill vecchio processo
bash tools/scripts/kill-port.sh "$PORT"

# Step 2: Avvia nuovo uvicorn
echo ""
echo "  Avvio uvicorn su porta $PORT..."
DATABASE_URL="$DB_URL" venv/Scripts/uvicorn api.main:app \
    --reload --host 0.0.0.0 --port "$PORT" &

# Step 3: Attendi e verifica
sleep 3
HEALTH=$(curl -s "http://localhost:${PORT}/health" 2>/dev/null || echo "FAIL")

if echo "$HEALTH" | grep -q '"ok"'; then
    echo "  Backend $ENV attivo su porta $PORT"
else
    echo "  ERRORE: backend non risponde su porta $PORT"
    echo "  Response: $HEALTH"
    exit 1
fi
