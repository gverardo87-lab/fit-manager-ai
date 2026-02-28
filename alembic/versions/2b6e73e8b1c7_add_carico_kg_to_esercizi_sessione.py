"""add_carico_kg_to_esercizi_sessione

Revision ID: 2b6e73e8b1c7
Revises: ef27c93ba498
Create Date: 2026-02-28 23:07:08.822744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b6e73e8b1c7'
down_revision: Union[str, Sequence[str], None] = 'ef27c93ba498'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("esercizi_sessione",
        sa.Column("carico_kg", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("esercizi_sessione", "carico_kg")
