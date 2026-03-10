"""add rinnovo_di to contratti

Revision ID: 27b8b9852489
Revises: faf8d3917048
Create Date: 2026-03-10 05:26:01.518954

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27b8b9852489'
down_revision: Union[str, Sequence[str], None] = 'faf8d3917048'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add rinnovo_di FK column to contratti table."""
    op.add_column("contratti", sa.Column("rinnovo_di", sa.Integer(), nullable=True))
    op.create_index("ix_contratti_rinnovo_di", "contratti", ["rinnovo_di"])


def downgrade() -> None:
    """Remove rinnovo_di column from contratti table."""
    op.drop_index("ix_contratti_rinnovo_di", table_name="contratti")
    op.drop_column("contratti", "rinnovo_di")
