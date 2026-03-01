"""add allenamenti_eseguiti table

Revision ID: d11f8852a4c7
Revises: 2b6e73e8b1c7
Create Date: 2026-03-01 00:32:43.580621

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'd11f8852a4c7'
down_revision: Union[str, Sequence[str], None] = '2b6e73e8b1c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('allenamenti_eseguiti',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_scheda', sa.Integer(), nullable=False),
    sa.Column('id_sessione', sa.Integer(), nullable=False),
    sa.Column('id_cliente', sa.Integer(), nullable=False),
    sa.Column('trainer_id', sa.Integer(), nullable=False),
    sa.Column('data_esecuzione', sa.Date(), nullable=False),
    sa.Column('id_evento', sa.Integer(), nullable=True),
    sa.Column('note', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_cliente'], ['clienti.id'], ),
    sa.ForeignKeyConstraint(['id_evento'], ['agenda.id'], ),
    sa.ForeignKeyConstraint(['id_scheda'], ['schede_allenamento.id'], ),
    sa.ForeignKeyConstraint(['id_sessione'], ['sessioni_scheda.id'], ),
    sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('allenamenti_eseguiti', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_allenamenti_eseguiti_id_cliente'), ['id_cliente'], unique=False)
        batch_op.create_index(batch_op.f('ix_allenamenti_eseguiti_id_scheda'), ['id_scheda'], unique=False)
        batch_op.create_index(batch_op.f('ix_allenamenti_eseguiti_id_sessione'), ['id_sessione'], unique=False)
        batch_op.create_index(batch_op.f('ix_allenamenti_eseguiti_trainer_id'), ['trainer_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('allenamenti_eseguiti', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_allenamenti_eseguiti_trainer_id'))
        batch_op.drop_index(batch_op.f('ix_allenamenti_eseguiti_id_sessione'))
        batch_op.drop_index(batch_op.f('ix_allenamenti_eseguiti_id_scheda'))
        batch_op.drop_index(batch_op.f('ix_allenamenti_eseguiti_id_cliente'))

    op.drop_table('allenamenti_eseguiti')
