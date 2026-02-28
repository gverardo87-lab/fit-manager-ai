"""add_goal_type_and_auto_complete

Revision ID: ef27c93ba498
Revises: 715113e3df12
Create Date: 2026-02-28 18:48:16.940952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef27c93ba498'
down_revision: Union[str, Sequence[str], None] = '715113e3df12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aggiunge tipo_obiettivo e completato_automaticamente a obiettivi_cliente."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("obiettivi_cliente")]

    if "tipo_obiettivo" not in columns:
        op.add_column(
            "obiettivi_cliente",
            sa.Column("tipo_obiettivo", sa.Text(), nullable=False, server_default="corporeo"),
        )
        op.create_index("ix_obiettivi_tipo", "obiettivi_cliente", ["tipo_obiettivo"])

    if "completato_automaticamente" not in columns:
        op.add_column(
            "obiettivi_cliente",
            sa.Column("completato_automaticamente", sa.Boolean(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    """Rimuove colonne tipo_obiettivo e completato_automaticamente."""
    op.drop_index("ix_obiettivi_tipo", table_name="obiettivi_cliente")
    op.drop_column("obiettivi_cliente", "completato_automaticamente")
    op.drop_column("obiettivi_cliente", "tipo_obiettivo")
