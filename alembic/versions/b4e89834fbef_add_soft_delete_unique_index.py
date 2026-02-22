"""add_soft_delete_unique_index

Revision ID: b4e89834fbef
Revises: 2e74a22514ea
Create Date: 2026-02-22 19:43:48.078490

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4e89834fbef'
down_revision: Union[str, Sequence[str], None] = '2e74a22514ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """UNIQUE index soft-delete aware per deduplicazione spese ricorrenti."""
    op.execute("DROP INDEX IF EXISTS uq_recurring_per_month")
    op.execute("""
        CREATE UNIQUE INDEX uq_recurring_per_month
        ON movimenti_cassa (trainer_id, id_spesa_ricorrente, mese_anno)
        WHERE id_spesa_ricorrente IS NOT NULL AND deleted_at IS NULL
    """)


def downgrade() -> None:
    """Ripristina indice senza filtro soft-delete."""
    op.execute("DROP INDEX IF EXISTS uq_recurring_per_month")
    op.execute("""
        CREATE UNIQUE INDEX uq_recurring_per_month
        ON movimenti_cassa (trainer_id, id_spesa_ricorrente, mese_anno)
        WHERE id_spesa_ricorrente IS NOT NULL
    """)
