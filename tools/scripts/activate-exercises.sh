#!/usr/bin/env bash
# tools/scripts/activate-exercises.sh
#
# Ciclo completo attivazione esercizi: activate_batch + pipeline deterministica.
#
# Uso:
#   bash tools/scripts/activate-exercises.sh              # 50 esercizi, entrambi i DB
#   bash tools/scripts/activate-exercises.sh 30            # 30 esercizi
#   bash tools/scripts/activate-exercises.sh 50 dev        # solo DB dev
#   bash tools/scripts/activate-exercises.sh --dry-run     # solo audit, zero modifiche
#
# Richiede: Ollama in esecuzione con gemma2:9b

set -euo pipefail

cd "$(dirname "$0")/../.."

# ── Parse args ──
BATCH_SIZE=50
DB="both"
DRY_RUN=""

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN="--dry-run" ;;
    dev|prod|both) DB="$arg" ;;
    [0-9]*) BATCH_SIZE="$arg" ;;
  esac
done

echo "╔══════════════════════════════════════════════════════╗"
echo "║  Attivazione Esercizi — Batch $BATCH_SIZE ($DB)     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Fase 1: activate_batch (Ollama enrichment + activate) ──
echo "=== FASE 1/6: activate_batch (select + enrich + activate + verify) ==="
PYTHONUNBUFFERED=1 python -m tools.admin_scripts.activate_batch \
  --db "$DB" --batch-size "$BATCH_SIZE" $DRY_RUN
echo ""

if [ -n "$DRY_RUN" ]; then
  echo "=== DRY-RUN completato. Nessuna modifica. ==="
  exit 0
fi

# ── Fase 2-6: Pipeline deterministica (zero Ollama) ──
echo "=== FASE 2/6: populate_taxonomy ==="
python -m tools.admin_scripts.populate_taxonomy --db "$DB"
echo ""

echo "=== FASE 3/6: populate_conditions ==="
python -m tools.admin_scripts.populate_conditions --db "$DB"
echo ""

echo "=== FASE 4/6: populate_exercise_relations ==="
python -m tools.admin_scripts.populate_exercise_relations --db "$DB"
echo ""

echo "=== FASE 5/6: fill_subset_gaps ==="
python -m tools.admin_scripts.fill_subset_gaps --db "$DB"
echo ""

echo "=== FASE 6/6: verify_exercise_quality ==="
python -m tools.admin_scripts.verify_exercise_quality --db "$DB"
echo ""

echo "╔══════════════════════════════════════════════════════╗"
echo "║  COMPLETATO — Esercizi attivati e verificati.       ║"
echo "╚══════════════════════════════════════════════════════╝"
