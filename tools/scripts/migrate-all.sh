#!/usr/bin/env bash
# tools/scripts/migrate-all.sh
#
# Applica le migrazioni Alembic a ENTRAMBI i database.
# Uso: bash tools/scripts/migrate-all.sh
#
# REGOLA BLINDATA: ogni volta che crei una migrazione Alembic,
# esegui questo script. Mai alembic upgrade head da solo.

set -euo pipefail

cd "$(dirname "$0")/../.."

PROD_DB="sqlite:///data/crm.db"
DEV_DB="sqlite:///data/crm_dev.db"

echo "=== Migrazione PROD (crm.db) ==="
DATABASE_URL="$PROD_DB" alembic upgrade head
echo "  OK"

echo ""
echo "=== Migrazione DEV (crm_dev.db) ==="
DATABASE_URL="$DEV_DB" alembic upgrade head
echo "  OK"

echo ""
echo "=== Verifica versioni ==="
PROD_VER=$(DATABASE_URL="$PROD_DB" alembic current 2>/dev/null | grep -oE '[a-f0-9]+' | head -1)
DEV_VER=$(DATABASE_URL="$DEV_DB" alembic current 2>/dev/null | grep -oE '[a-f0-9]+' | head -1)

echo "  PROD: $PROD_VER"
echo "  DEV:  $DEV_VER"

if [ "$PROD_VER" = "$DEV_VER" ]; then
    echo ""
    echo "  ALLINEATI — entrambi i DB sulla stessa versione."
else
    echo ""
    echo "  ATTENZIONE: versioni diverse! Investigare."
    exit 1
fi
