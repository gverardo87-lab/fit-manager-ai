# tools/admin_scripts/patch_ledger_names.py
"""
Patch one-time: aggiorna le note dei CashMovement di sistema
con il nome del cliente associato.

Target: movimenti con id_cliente e categoria di sistema
(PAGAMENTO_RATA, ACCONTO_CONTRATTO) le cui note non contengono
ancora il nome corretto del cliente.

Idempotente: rieseguire e' sicuro — salta i record gia' corretti.

Uso: python -m tools.admin_scripts.patch_ledger_names
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "crm.db"

# Mappa categoria -> prefisso nota
NOTE_PREFIXES = {
    "PAGAMENTO_RATA": "Pagamento Rata",
    "ACCONTO_CONTRATTO": "Acconto Contratto",
}


def run() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.id, m.categoria, m.note, c.nome, c.cognome
        FROM movimenti_cassa m
        JOIN clienti c ON c.id = m.id_cliente
        WHERE m.id_cliente IS NOT NULL
          AND m.categoria IN ('PAGAMENTO_RATA', 'ACCONTO_CONTRATTO')
    """)

    rows = cursor.fetchall()
    updated = 0

    for row in rows:
        prefix = NOTE_PREFIXES.get(row["categoria"])
        if not prefix:
            continue

        client_label = f"{row['nome']} {row['cognome']}"
        new_note = f"{prefix} - {client_label}"

        if row["note"] == new_note:
            continue

        cursor.execute(
            "UPDATE movimenti_cassa SET note = ? WHERE id = ?",
            (new_note, row["id"]),
        )
        updated += 1
        print(f"  #{row['id']}: {row['note']!r} -> {new_note!r}")

    conn.commit()
    conn.close()

    print(f"\nPatch completata: {updated}/{len(rows)} movimenti aggiornati")


if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"ERRORE: database non trovato in {DB_PATH}")
        sys.exit(1)
    run()
