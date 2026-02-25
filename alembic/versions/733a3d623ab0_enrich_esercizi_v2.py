"""enrich_esercizi_v2

Aggiunge 15 colonne a esercizi (contenuto ricco + biomeccanica + media).
Crea tabelle esercizi_media e esercizi_relazioni.

Revision ID: 733a3d623ab0
Revises: 9714db4efc6f
Create Date: 2026-02-25 01:01:20.428018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '733a3d623ab0'
down_revision: Union[str, Sequence[str], None] = '9714db4efc6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Colonne da aggiungere a esercizi (tutte nullable TEXT tranne dove specificato)
NEW_COLUMNS = [
    ("force_type", sa.Text()),
    ("lateral_pattern", sa.Text()),
    ("descrizione_anatomica", sa.Text()),
    ("descrizione_biomeccanica", sa.Text()),
    ("setup", sa.Text()),
    ("esecuzione", sa.Text()),
    ("respirazione", sa.Text()),
    ("tempo_consigliato", sa.Text()),
    ("coaching_cues", sa.Text()),
    ("errori_comuni", sa.Text()),
    ("note_sicurezza", sa.Text()),
    ("image_url", sa.Text()),
    ("video_url", sa.Text()),
]


def upgrade() -> None:
    """Aggiunge campi v2 a esercizi + crea tabelle media e relazioni."""
    conn = op.get_bind()

    # ── 1. Nuove colonne su esercizi (idempotente) ──
    result = conn.execute(sa.text("PRAGMA table_info(esercizi)")).fetchall()
    existing_cols = {row[1] for row in result}

    for col_name, col_type in NEW_COLUMNS:
        if col_name not in existing_cols:
            op.add_column("esercizi", sa.Column(col_name, col_type, nullable=True))

    # ── 2. Tabella esercizi_media (idempotente) ──
    media_exists = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='esercizi_media'")
    ).fetchone()

    if not media_exists:
        op.create_table(
            "esercizi_media",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("esercizi.id"), nullable=False),
            sa.Column("trainer_id", sa.Integer(), sa.ForeignKey("trainers.id"), nullable=True),
            sa.Column("tipo", sa.Text(), nullable=False),
            sa.Column("url", sa.Text(), nullable=False),
            sa.Column("ordine", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("descrizione", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_esercizi_media_exercise_id ON esercizi_media (exercise_id)")

    # ── 3. Tabella esercizi_relazioni (idempotente) ──
    rel_exists = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='esercizi_relazioni'")
    ).fetchone()

    if not rel_exists:
        op.create_table(
            "esercizi_relazioni",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("esercizi.id"), nullable=False),
            sa.Column("related_exercise_id", sa.Integer(), sa.ForeignKey("esercizi.id"), nullable=False),
            sa.Column("tipo_relazione", sa.Text(), nullable=False),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_esercizi_relazioni_exercise_id ON esercizi_relazioni (exercise_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_esercizi_relazioni_related_id ON esercizi_relazioni (related_exercise_id)")


def downgrade() -> None:
    """Rimuove tabelle media/relazioni e colonne v2."""
    # Indici
    op.execute("DROP INDEX IF EXISTS ix_esercizi_relazioni_related_id")
    op.execute("DROP INDEX IF EXISTS ix_esercizi_relazioni_exercise_id")
    op.execute("DROP INDEX IF EXISTS ix_esercizi_media_exercise_id")

    # Tabelle
    op.drop_table("esercizi_relazioni")
    op.drop_table("esercizi_media")

    # Colonne (ordine inverso)
    for col_name, _ in reversed(NEW_COLUMNS):
        op.drop_column("esercizi", col_name)
