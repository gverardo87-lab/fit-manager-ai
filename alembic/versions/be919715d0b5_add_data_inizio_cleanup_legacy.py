"""add_data_inizio_cleanup_legacy

Revision ID: be919715d0b5
Revises: b4e89834fbef
Create Date: 2026-02-23 07:08:15.727233

Aggiunge campo data_inizio a spese_ricorrenti (data scelta dall'utente
per l'inizio della spesa, disaccoppiata da data_creazione).
Rimuove campi legacy mai usati dal sync engine (giorno_inizio,
data_prossima_scadenza).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be919715d0b5'
down_revision: Union[str, Sequence[str], None] = 'b4e89834fbef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add data_inizio, drop legacy columns."""
    # 1. Aggiungi data_inizio (date, nullable per backward compat)
    op.execute("ALTER TABLE spese_ricorrenti ADD COLUMN data_inizio DATE")

    # 2. Popola da data_creazione per record esistenti
    op.execute("UPDATE spese_ricorrenti SET data_inizio = DATE(data_creazione)")

    # 3. Drop colonne legacy (SQLite richiede batch_op)
    with op.batch_alter_table("spese_ricorrenti") as batch_op:
        batch_op.drop_column("giorno_inizio")
        batch_op.drop_column("data_prossima_scadenza")


def downgrade() -> None:
    """Restore legacy columns, drop data_inizio."""
    with op.batch_alter_table("spese_ricorrenti") as batch_op:
        batch_op.add_column(sa.Column("giorno_inizio", sa.Integer(), server_default="1"))
        batch_op.add_column(sa.Column("data_prossima_scadenza", sa.Date(), nullable=True))
        batch_op.drop_column("data_inizio")
