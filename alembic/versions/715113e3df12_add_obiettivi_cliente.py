"""add_obiettivi_cliente

Tabella obiettivi strutturati per cliente.
Ogni obiettivo collega un cliente a una metrica con direzione, target e baseline.

Revision ID: 715113e3df12
Revises: fa1c0b21a18a
Create Date: 2026-02-28 18:12:21.346312

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '715113e3df12'
down_revision: Union[str, Sequence[str], None] = 'fa1c0b21a18a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, name: str) -> bool:
    """Check if table exists in SQLite."""
    row = conn.execute(
        sa.text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": name},
    ).fetchone()
    return row is not None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    if _table_exists(conn, "obiettivi_cliente"):
        return

    op.create_table(
        "obiettivi_cliente",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("id_cliente", sa.Integer, sa.ForeignKey("clienti.id"), nullable=False),
        sa.Column("trainer_id", sa.Integer, sa.ForeignKey("trainers.id"), nullable=False),
        sa.Column("id_metrica", sa.Integer, sa.ForeignKey("metriche.id"), nullable=False),
        sa.Column("direzione", sa.Text, nullable=False),
        sa.Column("valore_target", sa.Float, nullable=True),
        sa.Column("valore_baseline", sa.Float, nullable=True),
        sa.Column("data_baseline", sa.Date, nullable=True),
        sa.Column("data_inizio", sa.Date, nullable=False),
        sa.Column("data_scadenza", sa.Date, nullable=True),
        sa.Column("priorita", sa.Integer, nullable=False, server_default="3"),
        sa.Column("stato", sa.Text, nullable=False, server_default="attivo"),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )

    op.create_index("ix_obiettivi_cliente", "obiettivi_cliente", ["id_cliente"])
    op.create_index("ix_obiettivi_trainer", "obiettivi_cliente", ["trainer_id"])
    op.create_index("ix_obiettivi_stato", "obiettivi_cliente", ["stato"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_obiettivi_stato")
    op.drop_index("ix_obiettivi_trainer")
    op.drop_index("ix_obiettivi_cliente")
    op.drop_table("obiettivi_cliente")
