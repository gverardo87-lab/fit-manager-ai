"""add_taxonomy_schema

Tassonomia scientifica esercizi: 6 nuove tabelle + 4 colonne su esercizi.

Tabelle catalogo:
  - muscoli (~52 muscoli anatomici)
  - articolazioni (~15 articolazioni)
  - condizioni_mediche (~30 condizioni)

Tabelle junction M:N:
  - esercizi_muscoli (ruolo + attivazione)
  - esercizi_articolazioni (ruolo + ROM)
  - esercizi_condizioni (severita' + nota)

Colonne su esercizi:
  - in_subset (flag sviluppo tassonomia)
  - catena_cinetica (open/closed)
  - piano_movimento (sagittal/frontal/transverse/multi)
  - tipo_contrazione (concentric/eccentric/isometric/dynamic)

Idempotente: controlla esistenza prima di creare.

Revision ID: 949f3f3fd5ed
Revises: 168184c7d6ba
Create Date: 2026-02-27 02:16:56.892651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '949f3f3fd5ed'
down_revision: Union[str, Sequence[str], None] = '168184c7d6ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, name: str) -> bool:
    """Check if table exists in SQLite."""
    row = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": name},
    ).fetchone()
    return row is not None


def _column_exists(conn, table: str, column: str) -> bool:
    """Check if column exists in SQLite table."""
    result = conn.execute(sa.text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in result)


def upgrade() -> None:
    """Create taxonomy tables and add biomechanics columns."""
    conn = op.get_bind()

    # ── Catalog tables ──

    if not _table_exists(conn, "muscoli"):
        op.create_table(
            "muscoli",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("nome", sa.Text(), nullable=False),
            sa.Column("nome_en", sa.Text(), nullable=False),
            sa.Column("gruppo", sa.Text(), nullable=False),
            sa.Column("regione", sa.Text(), nullable=False),
        )
        op.create_index("ix_muscoli_nome", "muscoli", ["nome"])
        op.create_index("ix_muscoli_gruppo", "muscoli", ["gruppo"])

    if not _table_exists(conn, "articolazioni"):
        op.create_table(
            "articolazioni",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("nome", sa.Text(), nullable=False),
            sa.Column("nome_en", sa.Text(), nullable=False),
            sa.Column("tipo", sa.Text(), nullable=False),
            sa.Column("regione", sa.Text(), nullable=False),
        )
        op.create_index("ix_articolazioni_nome", "articolazioni", ["nome"])

    if not _table_exists(conn, "condizioni_mediche"):
        op.create_table(
            "condizioni_mediche",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("nome", sa.Text(), nullable=False),
            sa.Column("nome_en", sa.Text(), nullable=False),
            sa.Column("categoria", sa.Text(), nullable=False),
            sa.Column("body_tags", sa.Text(), nullable=True),
        )
        op.create_index("ix_condizioni_mediche_nome", "condizioni_mediche", ["nome"])
        op.create_index("ix_condizioni_mediche_categoria", "condizioni_mediche", ["categoria"])

    # ── Junction tables M:N ──

    if not _table_exists(conn, "esercizi_muscoli"):
        op.create_table(
            "esercizi_muscoli",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_esercizio", sa.Integer(), sa.ForeignKey("esercizi.id"), nullable=False),
            sa.Column("id_muscolo", sa.Integer(), sa.ForeignKey("muscoli.id"), nullable=False),
            sa.Column("ruolo", sa.Text(), nullable=False),
            sa.Column("attivazione", sa.Integer(), nullable=True),
        )
        op.create_index("ix_esercizi_muscoli_esercizio", "esercizi_muscoli", ["id_esercizio"])
        op.create_index("ix_esercizi_muscoli_muscolo", "esercizi_muscoli", ["id_muscolo"])

    if not _table_exists(conn, "esercizi_articolazioni"):
        op.create_table(
            "esercizi_articolazioni",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_esercizio", sa.Integer(), sa.ForeignKey("esercizi.id"), nullable=False),
            sa.Column("id_articolazione", sa.Integer(), sa.ForeignKey("articolazioni.id"), nullable=False),
            sa.Column("ruolo", sa.Text(), nullable=False),
            sa.Column("rom_gradi", sa.Integer(), nullable=True),
        )
        op.create_index("ix_esercizi_articolazioni_esercizio", "esercizi_articolazioni", ["id_esercizio"])
        op.create_index("ix_esercizi_articolazioni_articolazione", "esercizi_articolazioni", ["id_articolazione"])

    if not _table_exists(conn, "esercizi_condizioni"):
        op.create_table(
            "esercizi_condizioni",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_esercizio", sa.Integer(), sa.ForeignKey("esercizi.id"), nullable=False),
            sa.Column("id_condizione", sa.Integer(), sa.ForeignKey("condizioni_mediche.id"), nullable=False),
            sa.Column("severita", sa.Text(), nullable=False),
            sa.Column("nota", sa.Text(), nullable=True),
        )
        op.create_index("ix_esercizi_condizioni_esercizio", "esercizi_condizioni", ["id_esercizio"])
        op.create_index("ix_esercizi_condizioni_condizione", "esercizi_condizioni", ["id_condizione"])

    # ── New columns on esercizi (idempotent) ──

    new_columns = [
        ("in_subset", sa.Boolean()),
        ("catena_cinetica", sa.Text()),
        ("piano_movimento", sa.Text()),
        ("tipo_contrazione", sa.Text()),
    ]

    for col_name, col_type in new_columns:
        if not _column_exists(conn, "esercizi", col_name):
            with op.batch_alter_table("esercizi") as batch_op:
                batch_op.add_column(sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    """Remove taxonomy tables and biomechanics columns."""
    # Drop junction tables first (FK references)
    op.drop_table("esercizi_condizioni")
    op.drop_table("esercizi_articolazioni")
    op.drop_table("esercizi_muscoli")

    # Drop catalog tables
    op.drop_table("condizioni_mediche")
    op.drop_table("articolazioni")
    op.drop_table("muscoli")

    # Remove columns from esercizi
    with op.batch_alter_table("esercizi") as batch_op:
        batch_op.drop_column("tipo_contrazione")
        batch_op.drop_column("piano_movimento")
        batch_op.drop_column("catena_cinetica")
        batch_op.drop_column("in_subset")
