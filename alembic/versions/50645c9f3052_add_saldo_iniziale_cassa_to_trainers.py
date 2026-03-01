"""add saldo_iniziale_cassa to trainers

Revision ID: 50645c9f3052
Revises: 9d7720a02d95
Create Date: 2026-03-01 15:13:39.212602

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50645c9f3052'
down_revision: Union[str, Sequence[str], None] = '9d7720a02d95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("trainers", sa.Column("saldo_iniziale_cassa", sa.Float(), nullable=False, server_default="0.0"))
    op.add_column("trainers", sa.Column("data_saldo_iniziale", sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("trainers", "data_saldo_iniziale")
    op.drop_column("trainers", "saldo_iniziale_cassa")
