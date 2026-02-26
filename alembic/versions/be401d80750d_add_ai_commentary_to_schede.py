"""add_ai_commentary_to_schede

Revision ID: be401d80750d
Revises: f3f3eedfebd0
Create Date: 2026-02-26 00:11:38.030791

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be401d80750d'
down_revision: Union[str, Sequence[str], None] = 'f3f3eedfebd0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("schede_allenamento") as batch_op:
        batch_op.add_column(sa.Column("ai_commentary", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("schede_allenamento") as batch_op:
        batch_op.drop_column("ai_commentary")
