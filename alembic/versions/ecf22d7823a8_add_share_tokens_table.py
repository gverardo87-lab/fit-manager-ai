"""add share_tokens table

Revision ID: ecf22d7823a8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-07

Aggiunge share_tokens per il Portale Clienti self-service.
Link monouso 48h per compilazione anamnesi senza autenticazione CRM.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'ecf22d7823a8'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'share_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('trainer_id', sa.Integer(), sa.ForeignKey('trainers.id'), nullable=False),
        sa.Column('client_id', sa.Integer(), sa.ForeignKey('clienti.id'), nullable=False),
        sa.Column('scope', sa.String(), nullable=False, server_default='anamnesi'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_share_tokens_token', 'share_tokens', ['token'], unique=True)
    op.create_index('ix_share_tokens_trainer_id', 'share_tokens', ['trainer_id'])
    op.create_index('ix_share_tokens_client_id', 'share_tokens', ['client_id'])


def downgrade() -> None:
    op.drop_index('ix_share_tokens_client_id', 'share_tokens')
    op.drop_index('ix_share_tokens_trainer_id', 'share_tokens')
    op.drop_index('ix_share_tokens_token', 'share_tokens')
    op.drop_table('share_tokens')
