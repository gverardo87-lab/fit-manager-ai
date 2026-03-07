"""add 10 demand vector columns to exercises

Revision ID: faf8d3917048
Revises: ecf22d7823a8
Create Date: 2026-03-07 21:54:23.030928

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'faf8d3917048'
down_revision: Union[str, Sequence[str], None] = 'ecf22d7823a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 10 demand vector columns (scale 0-4, nullable) to esercizi."""
    columns = [
        "skill_demand",
        "coordination_demand",
        "stability_demand",
        "ballistic_demand",
        "impact_demand",
        "axial_load_demand",
        "shoulder_complex_demand",
        "lumbar_load_demand",
        "grip_demand",
        "metabolic_demand",
    ]
    for col in columns:
        op.add_column("esercizi", sa.Column(col, sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove 10 demand vector columns from esercizi."""
    columns = [
        "skill_demand",
        "coordination_demand",
        "stability_demand",
        "ballistic_demand",
        "impact_demand",
        "axial_load_demand",
        "shoulder_complex_demand",
        "lumbar_load_demand",
        "grip_demand",
        "metabolic_demand",
    ]
    for col in columns:
        op.drop_column("esercizi", col)
