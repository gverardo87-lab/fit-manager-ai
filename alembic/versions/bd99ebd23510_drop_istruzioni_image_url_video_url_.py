"""drop istruzioni image_url video_url columns

Revision ID: bd99ebd23510
Revises: 949f3f3fd5ed
Create Date: 2026-02-27 15:14:26.203106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd99ebd23510'
down_revision: Union[str, Sequence[str], None] = '949f3f3fd5ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rimuovi colonne legacy: istruzioni (deprecata v2), image_url e video_url (media via junction table)."""
    with op.batch_alter_table("esercizi") as batch_op:
        batch_op.drop_column("istruzioni")
        batch_op.drop_column("image_url")
        batch_op.drop_column("video_url")


def downgrade() -> None:
    """Ripristina colonne legacy (tutte nullable, nessun dato da ripristinare)."""
    with op.batch_alter_table("esercizi") as batch_op:
        batch_op.add_column(sa.Column("istruzioni", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("image_url", sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column("video_url", sa.VARCHAR(), nullable=True))
