"""initial_schema_stamp

Revision ID: 2e74a22514ea
Revises:
Create Date: 2026-02-22 18:37:33.454929

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '2e74a22514ea'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Schema gia' esistente — stamp iniziale."""
    pass


def downgrade() -> None:
    """Non tornare indietro dalla versione iniziale."""
    pass
