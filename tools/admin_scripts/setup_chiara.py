# tools/admin_scripts/setup_chiara.py
"""
Setup one-time: crea Chiara Bassani come unico trainer e assegna tutti i record.

Operazioni (idempotenti — sicuro rieseguire):
1. Elimina movimenti orfani di test (operatore='API', id_cliente inesistente)
2. Rimuove trainer di test (Alice, Bob)
3. Crea Chiara Bassani con password bcrypt
4. Assegna tutti i record esistenti a Chiara (trainer_id backfill)

Uso: python -m tools.admin_scripts.setup_chiara
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import bcrypt

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "crm.db"

CHIARA = {
    "email": "chiarabassani96@gmail.com",
    "nome": "Chiara",
    "cognome": "Bassani",
    "password": "chiarabassani",
}

TABLES_WITH_TRAINER_ID = ["clienti", "contratti", "agenda", "movimenti_cassa"]


def run() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = OFF")
    cursor = conn.cursor()

    # ── 1. Elimina movimenti orfani di test ──
    cursor.execute("""
        DELETE FROM movimenti_cassa
        WHERE operatore = 'API'
          AND id_cliente IS NOT NULL
          AND id_cliente NOT IN (SELECT id FROM clienti)
    """)
    deleted_movements = cursor.rowcount
    print(f"[1/4] Movimenti orfani eliminati: {deleted_movements}")

    # ── 2. Rimuove trainer di test ──
    # Prima svuota i riferimenti FK
    for table in TABLES_WITH_TRAINER_ID:
        cursor.execute(f"UPDATE {table} SET trainer_id = NULL WHERE trainer_id IS NOT NULL")

    cursor.execute("DELETE FROM trainers")
    deleted_trainers = cursor.rowcount
    cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'trainers'")
    print(f"[2/4] Trainer di test eliminati: {deleted_trainers}")

    # ── 3. Crea Chiara Bassani ──
    hashed = bcrypt.hashpw(
        CHIARA["password"].encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    cursor.execute(
        """
        INSERT INTO trainers (email, nome, cognome, hashed_password, is_active, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
        """,
        (CHIARA["email"], CHIARA["nome"], CHIARA["cognome"], hashed, datetime.utcnow().isoformat()),
    )
    chiara_id = cursor.lastrowid
    print(f"[3/4] Trainer creato: {CHIARA['nome']} {CHIARA['cognome']} (id={chiara_id})")

    # ── 4. Backfill trainer_id su tutti i record ──
    for table in TABLES_WITH_TRAINER_ID:
        cursor.execute(f"UPDATE {table} SET trainer_id = ? WHERE trainer_id IS NULL", (chiara_id,))
        updated = cursor.rowcount
        if updated > 0:
            print(f"     {table}: {updated} record assegnati a Chiara")

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    print(f"\nSetup completato. Login: {CHIARA['email']} / {CHIARA['password']}")


if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"ERRORE: database non trovato in {DB_PATH}")
        sys.exit(1)
    run()
