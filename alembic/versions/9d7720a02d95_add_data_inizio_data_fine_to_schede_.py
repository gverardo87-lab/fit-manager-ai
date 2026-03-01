"""add data_inizio data_fine to schede_allenamento

Revision ID: 9d7720a02d95
Revises: d11f8852a4c7
Create Date: 2026-03-01 01:20:11.151123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d7720a02d95'
down_revision: Union[str, Sequence[str], None] = 'd11f8852a4c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("schede_allenamento", sa.Column("data_inizio", sa.Date(), nullable=True))
    op.add_column("schede_allenamento", sa.Column("data_fine", sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("schede_allenamento", schema=None) as batch_op:
        batch_op.drop_column("data_fine")
        batch_op.drop_column("data_inizio")
