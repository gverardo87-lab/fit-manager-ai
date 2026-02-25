"""add workout plan tables

Crea 3 tabelle gerarchiche per schede allenamento:
- schede_allenamento (parent, FK trainers + clienti)
- sessioni_scheda (child, FK schede_allenamento)
- esercizi_sessione (grandchild, FK sessioni_scheda + esercizi)

Idempotente: CREATE TABLE IF NOT EXISTS via check sqlite_master.

Revision ID: f3f3eedfebd0
Revises: 733a3d623ab0
Create Date: 2026-02-25 13:58:38.139959

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3f3eedfebd0'
down_revision: Union[str, Sequence[str], None] = '733a3d623ab0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, name: str) -> bool:
    """Check se tabella esiste in SQLite."""
    row = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": name},
    ).fetchone()
    return row is not None


def upgrade() -> None:
    """Crea 3 tabelle workout + indici."""
    conn = op.get_bind()

    # ── 1. schede_allenamento ──
    if not _table_exists(conn, "schede_allenamento"):
        op.create_table(
            "schede_allenamento",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("trainer_id", sa.Integer(), sa.ForeignKey("trainers.id"), nullable=False),
            sa.Column("id_cliente", sa.Integer(), sa.ForeignKey("clienti.id"), nullable=True),
            sa.Column("nome", sa.Text(), nullable=False),
            sa.Column("obiettivo", sa.Text(), nullable=False),
            sa.Column("livello", sa.Text(), nullable=False),
            sa.Column("durata_settimane", sa.Integer(), nullable=False, server_default=sa.text("4")),
            sa.Column("sessioni_per_settimana", sa.Integer(), nullable=False, server_default=sa.text("3")),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.Text(), nullable=True),
            sa.Column("updated_at", sa.Text(), nullable=True),
            sa.Column("deleted_at", sa.Text(), nullable=True),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_schede_allenamento_trainer_id ON schede_allenamento (trainer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_schede_allenamento_id_cliente ON schede_allenamento (id_cliente)")

    # ── 2. sessioni_scheda ──
    if not _table_exists(conn, "sessioni_scheda"):
        op.create_table(
            "sessioni_scheda",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_scheda", sa.Integer(), sa.ForeignKey("schede_allenamento.id"), nullable=False),
            sa.Column("numero_sessione", sa.Integer(), nullable=False),
            sa.Column("nome_sessione", sa.Text(), nullable=False),
            sa.Column("focus_muscolare", sa.Text(), nullable=True),
            sa.Column("durata_minuti", sa.Integer(), nullable=False, server_default=sa.text("60")),
            sa.Column("note", sa.Text(), nullable=True),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_sessioni_scheda_id_scheda ON sessioni_scheda (id_scheda)")

    # ── 3. esercizi_sessione ──
    if not _table_exists(conn, "esercizi_sessione"):
        op.create_table(
            "esercizi_sessione",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_sessione", sa.Integer(), sa.ForeignKey("sessioni_scheda.id"), nullable=False),
            sa.Column("id_esercizio", sa.Integer(), sa.ForeignKey("esercizi.id"), nullable=False),
            sa.Column("ordine", sa.Integer(), nullable=False),
            sa.Column("serie", sa.Integer(), nullable=False, server_default=sa.text("3")),
            sa.Column("ripetizioni", sa.Text(), nullable=False, server_default=sa.text("'8-12'")),
            sa.Column("tempo_riposo_sec", sa.Integer(), nullable=False, server_default=sa.text("90")),
            sa.Column("tempo_esecuzione", sa.Text(), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_esercizi_sessione_id_sessione ON esercizi_sessione (id_sessione)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_esercizi_sessione_id_esercizio ON esercizi_sessione (id_esercizio)")


def downgrade() -> None:
    """Rimuove tabelle workout in ordine inverso (FK)."""
    op.execute("DROP INDEX IF EXISTS ix_esercizi_sessione_id_esercizio")
    op.execute("DROP INDEX IF EXISTS ix_esercizi_sessione_id_sessione")
    op.drop_table("esercizi_sessione")

    op.execute("DROP INDEX IF EXISTS ix_sessioni_scheda_id_scheda")
    op.drop_table("sessioni_scheda")

    op.execute("DROP INDEX IF EXISTS ix_schede_allenamento_id_cliente")
    op.execute("DROP INDEX IF EXISTS ix_schede_allenamento_trainer_id")
    op.drop_table("schede_allenamento")
