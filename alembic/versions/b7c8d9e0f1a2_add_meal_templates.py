"""add meal_templates and template_components tables

Revision ID: b7c8d9e0f1a2
Revises: a9f1e2b3c4d5
Create Date: 2026-03-12 12:00:00.000000

Aggiunge 2 tabelle per i template pasti riutilizzabili:
  - meal_templates: template pasto (trainer-owned, nome + tipo_pasto)
  - template_components: componenti del template (alimento_id × quantita_g)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'a9f1e2b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea le tabelle meal_templates e template_components."""
    op.create_table(
        "meal_templates",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("trainer_id", sa.Integer(), sa.ForeignKey("trainers.id"), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("tipo_pasto", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_meal_templates_trainer_id", "meal_templates", ["trainer_id"])

    op.create_table(
        "template_components",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("meal_templates.id"), nullable=False),
        sa.Column("alimento_id", sa.Integer(), nullable=False),
        sa.Column("quantita_g", sa.Float(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_template_components_template_id", "template_components", ["template_id"])
    op.create_index("ix_template_components_alimento_id", "template_components", ["alimento_id"])


def downgrade() -> None:
    """Elimina le tabelle meal_templates e template_components."""
    op.drop_index("ix_template_components_alimento_id", "template_components")
    op.drop_index("ix_template_components_template_id", "template_components")
    op.drop_table("template_components")
    op.drop_index("ix_meal_templates_trainer_id", "meal_templates")
    op.drop_table("meal_templates")
