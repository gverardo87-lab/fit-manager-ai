"""add session blocks (blocchi_sessione)

Aggiunge supporto per formati di allenamento ibridi (circuit, tabata, AMRAP, EMOM, superset):
- Nuova tabella blocchi_sessione: blocchi esercizi con tipo e parametri specifici per formato
- esercizi_sessione: aggiunge id_blocco (FK nullable) e posizione_nel_blocco

Zero breaking change: id_blocco nullable → record esistenti non toccati.

Revision ID: a1b2c3d4e5f6
Revises: 50645c9f3052
Create Date: 2026-03-02 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "50645c9f3052"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, name: str) -> bool:
    row = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": name},
    ).fetchone()
    return row is not None


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(sa.text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. blocchi_sessione ──
    if not _table_exists(conn, "blocchi_sessione"):
        op.create_table(
            "blocchi_sessione",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_sessione", sa.Integer(), sa.ForeignKey("sessioni_scheda.id"), nullable=False),
            # Tipo blocco: circuit, superset, tabata, amrap, emom, for_time
            sa.Column("tipo_blocco", sa.Text(), nullable=False, server_default=sa.text("'circuit'")),
            # Ordine del blocco nella sessione (vs esercizi straight)
            sa.Column("ordine", sa.Integer(), nullable=False, server_default=sa.text("1")),
            # Nome descrittivo opzionale (es. "Finisher HIIT")
            sa.Column("nome", sa.Text(), nullable=True),
            # Giri/round del blocco (circuit: 3 giri, tabata: 8 round)
            sa.Column("giri", sa.Integer(), nullable=False, server_default=sa.text("3")),
            # Durata lavoro per stazione (Tabata: 20s, EMOM: 60s)
            sa.Column("durata_lavoro_sec", sa.Integer(), nullable=True),
            # Durata riposo tra stazioni (Tabata: 10s, Circuit: 15s)
            sa.Column("durata_riposo_sec", sa.Integer(), nullable=True),
            # Durata totale blocco (AMRAP: 12min, EMOM: 20min)
            sa.Column("durata_blocco_sec", sa.Integer(), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_blocchi_sessione_id_sessione ON blocchi_sessione (id_sessione)")

    # ── 2. esercizi_sessione: aggiungi id_blocco + posizione_nel_blocco ──
    # Nota: SQLite non supporta ADD COLUMN con FK constraint via op.add_column.
    # Usiamo raw SQL: la FK è dichiarativa in SQLite (non viene enforced in DDL).
    if not _column_exists(conn, "esercizi_sessione", "id_blocco"):
        op.execute(
            "ALTER TABLE esercizi_sessione ADD COLUMN id_blocco INTEGER REFERENCES blocchi_sessione(id)"
        )
    if not _column_exists(conn, "esercizi_sessione", "posizione_nel_blocco"):
        op.execute(
            "ALTER TABLE esercizi_sessione ADD COLUMN posizione_nel_blocco INTEGER"
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_esercizi_sessione_id_blocco ON esercizi_sessione (id_blocco)")


def downgrade() -> None:
    # SQLite non supporta DROP COLUMN nativamente fino a 3.35 — ricrea tabella
    conn = op.get_bind()

    # Rimuovi indice su id_blocco
    op.execute("DROP INDEX IF EXISTS ix_esercizi_sessione_id_blocco")

    # Ricrea esercizi_sessione senza le nuove colonne
    op.execute("""
        CREATE TABLE esercizi_sessione_backup AS
        SELECT id, id_sessione, id_esercizio, ordine, serie, ripetizioni,
               tempo_riposo_sec, tempo_esecuzione, carico_kg, note
        FROM esercizi_sessione
    """)
    op.execute("DROP TABLE esercizi_sessione")
    op.execute("ALTER TABLE esercizi_sessione_backup RENAME TO esercizi_sessione")
    op.execute("CREATE INDEX IF NOT EXISTS ix_esercizi_sessione_id_sessione ON esercizi_sessione (id_sessione)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_esercizi_sessione_id_esercizio ON esercizi_sessione (id_esercizio)")

    # Rimuovi tabella blocchi
    op.execute("DROP INDEX IF EXISTS ix_blocchi_sessione_id_sessione")
    op.drop_table("blocchi_sessione")
