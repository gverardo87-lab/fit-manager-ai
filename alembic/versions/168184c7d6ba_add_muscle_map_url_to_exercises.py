"""add_muscle_map_url_to_exercises

Revision ID: 168184c7d6ba
Revises: be401d80750d
Create Date: 2026-02-26 01:58:43.948784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '168184c7d6ba'
down_revision: Union[str, Sequence[str], None] = 'be401d80750d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("esercizi", sa.Column("muscle_map_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("esercizi", "muscle_map_url")
