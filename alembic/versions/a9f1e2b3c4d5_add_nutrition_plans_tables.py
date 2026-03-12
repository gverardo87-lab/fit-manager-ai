"""add nutrition plans tables

Revision ID: a9f1e2b3c4d5
Revises: 27b8b9852489
Create Date: 2026-03-12 10:00:00.000000

Aggiunge 3 tabelle al DB business (crm.db) per i piani alimentari:
  - piani_alimentari: piano assegnato dal trainer al cliente
  - pasti_piano: pasto nel piano (colazione, pranzo, ecc.)
  - componenti_pasto: alimento × grammi nel pasto (cross-DB ref → nutrition.db)

Le tabelle del catalogo alimenti (categorie_alimenti, alimenti, porzioni_standard)
vivono in nutrition.db separato e non sono gestite da Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a9f1e2b3c4d5"
down_revision: Union[str, None] = "27b8b9852489"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:name"
        ),
        {"name": table_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    # ── piani_alimentari ──────────────────────────────────────────────────
    if not _table_exists("piani_alimentari"):
        op.create_table(
            "piani_alimentari",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("trainer_id", sa.Integer, sa.ForeignKey("trainers.id"), nullable=False, index=True),
            sa.Column("id_cliente", sa.Integer, sa.ForeignKey("clienti.id"), nullable=False, index=True),
            sa.Column("nome", sa.String, nullable=False),
            sa.Column("obiettivo_calorico", sa.Integer, nullable=True),
            sa.Column("proteine_g_target", sa.Integer, nullable=True),
            sa.Column("carboidrati_g_target", sa.Integer, nullable=True),
            sa.Column("grassi_g_target", sa.Integer, nullable=True),
            sa.Column("note_cliniche", sa.Text, nullable=True),
            sa.Column("data_inizio", sa.Date, nullable=True),
            sa.Column("data_fine", sa.Date, nullable=True),
            sa.Column("attivo", sa.Boolean, nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("deleted_at", sa.DateTime, nullable=True),
        )

    # ── pasti_piano ───────────────────────────────────────────────────────
    if not _table_exists("pasti_piano"):
        op.create_table(
            "pasti_piano",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("piano_id", sa.Integer, sa.ForeignKey("piani_alimentari.id"), nullable=False, index=True),
            sa.Column("giorno_settimana", sa.Integer, nullable=False, server_default="0"),
            sa.Column("tipo_pasto", sa.String, nullable=False),
            sa.Column("ordine", sa.Integer, nullable=False, server_default="0"),
            sa.Column("nome", sa.String, nullable=True),
            sa.Column("note", sa.Text, nullable=True),
            sa.Column("deleted_at", sa.DateTime, nullable=True),
        )

    # ── componenti_pasto ─────────────────────────────────────────────────
    if not _table_exists("componenti_pasto"):
        op.create_table(
            "componenti_pasto",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("pasto_id", sa.Integer, sa.ForeignKey("pasti_piano.id"), nullable=False, index=True),
            # Cross-DB reference: alimento_id → nutrition.db alimenti.id
            # Nessun FK constraint (stessa tecnica di esercizi_muscoli.id_esercizio)
            sa.Column("alimento_id", sa.Integer, nullable=False, index=True),
            sa.Column("quantita_g", sa.Float, nullable=False),
            sa.Column("note", sa.Text, nullable=True),
            sa.Column("deleted_at", sa.DateTime, nullable=True),
        )


def downgrade() -> None:
    # Ordine inverso per rispettare FK constraints
    if _table_exists("componenti_pasto"):
        op.drop_table("componenti_pasto")
    if _table_exists("pasti_piano"):
        op.drop_table("pasti_piano")
    if _table_exists("piani_alimentari"):
        op.drop_table("piani_alimentari")
