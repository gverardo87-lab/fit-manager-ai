#!/usr/bin/env bash
# tools/scripts/kill-port.sh
#
# Killa TUTTI i processi su una porta (inclusi worker figli).
# Risolve il problema Windows dei zombie uvicorn worker.
#
# Uso:
#   bash tools/scripts/kill-port.sh 8000
#   bash tools/scripts/kill-port.sh 8001

set -euo pipefail

PORT="${1:?Uso: kill-port.sh <porta>}"

echo "=== Kill tutti i processi sulla porta $PORT ==="

# Trova tutti i PID che ascoltano sulla porta
PIDS=$(netstat -ano 2>/dev/null | grep ":${PORT}.*LISTEN" | awk '{print $5}' | sort -u)

if [ -z "$PIDS" ]; then
    echo "  Nessun processo trovato sulla porta $PORT."
    exit 0
fi

echo "  PID trovati: $PIDS"

for PID in $PIDS; do
    echo "  Killing PID $PID (con albero processi)..."
    # /T = kill tree (parent + figli), /F = force
    taskkill //T //F //PID "$PID" 2>/dev/null || true
done

# Attendi e verifica
sleep 2

REMAINING=$(netstat -ano 2>/dev/null | grep ":${PORT}.*LISTEN" | awk '{print $5}' | sort -u)
if [ -z "$REMAINING" ]; then
    echo ""
    echo "  Porta $PORT libera."
else
    echo ""
    echo "  ATTENZIONE: processi ancora attivi: $REMAINING"
    echo "  Tentativo fallback: kill figli orfani..."

    # Fallback: cerca processi Python il cui parent è nella lista
    for PID in $REMAINING; do
        powershell -Command "
            Get-CimInstance Win32_Process |
            Where-Object { \$_.ParentProcessId -eq $PID } |
            ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }
        " 2>/dev/null || true
    done

    sleep 1
    FINAL=$(netstat -ano 2>/dev/null | grep ":${PORT}.*LISTEN" | wc -l)
    if [ "$FINAL" -eq 0 ]; then
        echo "  Porta $PORT libera (dopo fallback)."
    else
        echo "  ERRORE: impossibile liberare porta $PORT. Riavvia il PC."
        exit 1
    fi
fi
