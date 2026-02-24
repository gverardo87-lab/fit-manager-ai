"""add_note_interne_to_clienti

Revision ID: 1d644d81a733
Revises: a4142c29f0bc
Create Date: 2026-02-24 03:32:57.377382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d644d81a733'
down_revision: Union[str, Sequence[str], None] = 'a4142c29f0bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aggiunge colonna note_interne alla tabella clienti."""
    with op.batch_alter_table("clienti") as batch_op:
        batch_op.add_column(sa.Column("note_interne", sa.Text(), nullable=True))


def downgrade() -> None:
    """Rimuove colonna note_interne dalla tabella clienti."""
    with op.batch_alter_table("clienti") as batch_op:
        batch_op.drop_column("note_interne")
