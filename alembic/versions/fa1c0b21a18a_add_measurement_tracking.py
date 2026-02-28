"""add_measurement_tracking

Tracking misurazioni corporee e prestazionali per il tab "Progressi".

3 tabelle:
  - metriche (catalogo 22 metriche standard — pre-seeded)
  - misurazioni_cliente (sessioni di misurazione per cliente)
  - valori_misurazione (valori individuali per sessione)

Idempotente: controlla esistenza prima di creare.

Revision ID: fa1c0b21a18a
Revises: bd99ebd23510
Create Date: 2026-02-28 15:51:18.419728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa1c0b21a18a'
down_revision: Union[str, Sequence[str], None] = 'bd99ebd23510'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── 22 metriche standard ──
METRICS_SEED = [
    # (nome, nome_en, unita_misura, categoria, ordinamento)
    ("Peso Corporeo", "Body Weight", "kg", "antropometrica", 1),
    ("Altezza", "Height", "cm", "antropometrica", 2),
    ("Massa Grassa", "Body Fat", "%", "composizione", 1),
    ("Massa Magra", "Lean Mass", "kg", "composizione", 2),
    ("BMI", "BMI", "kg/m\u00b2", "composizione", 3),
    ("Acqua Corporea", "Body Water", "%", "composizione", 4),
    ("Collo", "Neck", "cm", "circonferenza", 1),
    ("Petto", "Chest", "cm", "circonferenza", 2),
    ("Vita", "Waist", "cm", "circonferenza", 3),
    ("Fianchi", "Hips", "cm", "circonferenza", 4),
    ("Braccio Destro", "Right Arm", "cm", "circonferenza", 5),
    ("Braccio Sinistro", "Left Arm", "cm", "circonferenza", 6),
    ("Coscia Destra", "Right Thigh", "cm", "circonferenza", 7),
    ("Coscia Sinistra", "Left Thigh", "cm", "circonferenza", 8),
    ("Polpaccio Destro", "Right Calf", "cm", "circonferenza", 9),
    ("Polpaccio Sinistro", "Left Calf", "cm", "circonferenza", 10),
    ("FC Riposo", "Resting HR", "bpm", "cardiovascolare", 1),
    ("PA Sistolica", "Systolic BP", "mmHg", "cardiovascolare", 2),
    ("PA Diastolica", "Diastolic BP", "mmHg", "cardiovascolare", 3),
    ("Squat 1RM", "Squat 1RM", "kg", "forza", 1),
    ("Panca Piana 1RM", "Bench Press 1RM", "kg", "forza", 2),
    ("Stacco da Terra 1RM", "Deadlift 1RM", "kg", "forza", 3),
]


def _table_exists(conn, name: str) -> bool:
    """Check if table exists in SQLite."""
    row = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": name},
    ).fetchone()
    return row is not None


def upgrade() -> None:
    """Create measurement tracking tables and seed metrics catalog."""
    conn = op.get_bind()

    # ── Catalog: metriche ──
    if not _table_exists(conn, "metriche"):
        op.create_table(
            "metriche",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("nome", sa.Text(), nullable=False),
            sa.Column("nome_en", sa.Text(), nullable=False),
            sa.Column("unita_misura", sa.Text(), nullable=False),
            sa.Column("categoria", sa.Text(), nullable=False),
            sa.Column("ordinamento", sa.Integer(), nullable=False, server_default="0"),
        )
        op.create_index("ix_metriche_categoria", "metriche", ["categoria"])

    # Seed 22 metriche standard (idempotente — solo se tabella vuota)
    count = conn.execute(sa.text("SELECT COUNT(*) FROM metriche")).scalar()
    if count == 0:
        metriche_table = sa.table(
            "metriche",
            sa.column("nome", sa.Text),
            sa.column("nome_en", sa.Text),
            sa.column("unita_misura", sa.Text),
            sa.column("categoria", sa.Text),
            sa.column("ordinamento", sa.Integer),
        )
        op.bulk_insert(metriche_table, [
            {
                "nome": nome,
                "nome_en": nome_en,
                "unita_misura": unita,
                "categoria": cat,
                "ordinamento": ordine,
            }
            for nome, nome_en, unita, cat, ordine in METRICS_SEED
        ])

    # ── Sessioni di misurazione ──
    if not _table_exists(conn, "misurazioni_cliente"):
        op.create_table(
            "misurazioni_cliente",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_cliente", sa.Integer(), sa.ForeignKey("clienti.id"), nullable=False),
            sa.Column("trainer_id", sa.Integer(), sa.ForeignKey("trainers.id"), nullable=False),
            sa.Column("data_misurazione", sa.Date(), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_misurazioni_cliente_id_cliente", "misurazioni_cliente", ["id_cliente"])
        op.create_index("ix_misurazioni_cliente_trainer", "misurazioni_cliente", ["trainer_id"])

    # ── Valori individuali ──
    if not _table_exists(conn, "valori_misurazione"):
        op.create_table(
            "valori_misurazione",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_misurazione", sa.Integer(), sa.ForeignKey("misurazioni_cliente.id"), nullable=False),
            sa.Column("id_metrica", sa.Integer(), sa.ForeignKey("metriche.id"), nullable=False),
            sa.Column("valore", sa.Float(), nullable=False),
        )
        op.create_index("ix_valori_misurazione_sessione", "valori_misurazione", ["id_misurazione"])
        op.create_index("ix_valori_misurazione_metrica", "valori_misurazione", ["id_metrica"])


def downgrade() -> None:
    """Remove measurement tracking tables."""
    op.drop_table("valori_misurazione")
    op.drop_table("misurazioni_cliente")
    op.drop_table("metriche")
