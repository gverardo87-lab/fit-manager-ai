"""add_esercizi_table

Revision ID: 9714db4efc6f
Revises: 1d644d81a733
Create Date: 2026-02-25 00:08:00.695648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9714db4efc6f'
down_revision: Union[str, Sequence[str], None] = '1d644d81a733'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea tabella esercizi (se non esiste) + indici."""
    # La tabella potrebbe gia' esistere via SQLModel auto-create.
    # Usiamo IF NOT EXISTS per idempotenza.
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='esercizi'")
    ).fetchone()

    if not result:
        op.create_table(
            "esercizi",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("trainer_id", sa.Integer(), sa.ForeignKey("trainers.id"), nullable=True),
            sa.Column("nome", sa.Text(), nullable=False),
            sa.Column("nome_en", sa.Text(), nullable=True),
            sa.Column("categoria", sa.Text(), nullable=False),
            sa.Column("pattern_movimento", sa.Text(), nullable=False),
            sa.Column("muscoli_primari", sa.Text(), nullable=False),
            sa.Column("muscoli_secondari", sa.Text(), nullable=True),
            sa.Column("attrezzatura", sa.Text(), nullable=False),
            sa.Column("difficolta", sa.Text(), nullable=False),
            sa.Column("rep_range_forza", sa.Text(), nullable=True),
            sa.Column("rep_range_ipertrofia", sa.Text(), nullable=True),
            sa.Column("rep_range_resistenza", sa.Text(), nullable=True),
            sa.Column("ore_recupero", sa.Integer(), nullable=False, server_default=sa.text("48")),
            sa.Column("istruzioni", sa.Text(), nullable=True),
            sa.Column("controindicazioni", sa.Text(), nullable=True),
            sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
        )

    # Indici — CREATE IF NOT EXISTS per idempotenza su SQLite
    op.execute("CREATE INDEX IF NOT EXISTS ix_esercizi_trainer_id ON esercizi (trainer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_esercizi_nome ON esercizi (nome)")


def downgrade() -> None:
    """Rimuovi tabella esercizi."""
    op.execute("DROP INDEX IF EXISTS ix_esercizi_nome")
    op.execute("DROP INDEX IF EXISTS ix_esercizi_trainer_id")
    op.drop_table("esercizi")
