"""add_todos_table

Revision ID: a4142c29f0bc
Revises: be919715d0b5
Create Date: 2026-02-24 03:29:20.924678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4142c29f0bc'
down_revision: Union[str, Sequence[str], None] = 'be919715d0b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea tabella todos."""
    op.create_table(
        "todos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trainer_id", sa.Integer(), sa.ForeignKey("trainers.id"), nullable=False),
        sa.Column("titolo", sa.String(200), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("data_scadenza", sa.Date(), nullable=True),
        sa.Column("completato", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_todos_trainer_id", "todos", ["trainer_id"])


def downgrade() -> None:
    """Rimuovi tabella todos."""
    op.drop_index("ix_todos_trainer_id", table_name="todos")
    op.drop_table("todos")
