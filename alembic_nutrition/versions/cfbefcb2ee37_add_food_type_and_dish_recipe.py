"""add_food_type_and_dish_recipe

Revision ID: cfbefcb2ee37
Revises: d276284e36d9
Create Date: 2026-03-13 14:51:40.082233

Aggiunge:
  - Colonna food_type su alimenti (ingrediente/pietanza/bevanda)
  - Tabella ricette_pietanze (composizione pietanze)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'cfbefcb2ee37'
down_revision: Union[str, Sequence[str], None] = 'd276284e36d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # food_type su alimenti — default 'ingrediente' per tutti gli esistenti
    with op.batch_alter_table('alimenti', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('food_type', sqlmodel.sql.sqltypes.AutoString(),
                      nullable=False, server_default='ingrediente')
        )

    # Tabella ricette_pietanze
    op.create_table(
        'ricette_pietanze',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pietanza_id', sa.Integer(), nullable=False),
        sa.Column('ingrediente_id', sa.Integer(), nullable=False),
        sa.Column('quantita_g', sa.Float(), nullable=False),
        sa.Column('note', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(['ingrediente_id'], ['alimenti.id']),
        sa.ForeignKeyConstraint(['pietanza_id'], ['alimenti.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('ricette_pietanze', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_ricette_pietanze_pietanza_id'),
            ['pietanza_id'], unique=False
        )
        batch_op.create_index(
            batch_op.f('ix_ricette_pietanze_ingrediente_id'),
            ['ingrediente_id'], unique=False
        )


def downgrade() -> None:
    op.drop_table('ricette_pietanze')
    with op.batch_alter_table('alimenti', schema=None) as batch_op:
        batch_op.drop_column('food_type')
