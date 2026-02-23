#!/usr/bin/env python3
"""
Reset Production — DB vuoto con solo Chiara Bassani come trainer.

Operazioni:
1. Backup automatico del DB corrente
2. Drop + recreate schema (Windows-safe, no file delete)
3. Crea Chiara Bassani come unico trainer (bcrypt hash)
4. Stampa versione Alembic
5. Zero dati: nessun cliente, contratto, evento, movimento

Uso: python -m tools.admin_scripts.reset_production
IMPORTANTE: ferma il server API prima di eseguire!
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Setup path ──
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import SQLModel, Session, create_engine, text  # noqa: E402

# Importa TUTTI i modelli (necessario per SQLModel.metadata)
from api.models.trainer import Trainer  # noqa: E402, F401
from api.models.client import Client  # noqa: E402, F401
from api.models.contract import Contract  # noqa: E402, F401
from api.models.rate import Rate  # noqa: E402, F401
from api.models.event import Event  # noqa: E402, F401
from api.models.movement import CashMovement  # noqa: E402, F401
from api.models.recurring_expense import RecurringExpense  # noqa: E402, F401
from api.auth.service import hash_password  # noqa: E402

# ── Config ──
CHIARA = {
    "email": "chiarabassani96@gmail.com",
    "nome": "Chiara",
    "cognome": "Bassani",
    "password": "chiarabassani",
}

LATEST_ALEMBIC_VERSION = "be919715d0b5"


def run() -> None:
    from api.config import DATABASE_URL, DATA_DIR
    import shutil

    db_path = DATA_DIR / "crm.db"

    print("\n=== RESET PRODUCTION ===\n")

    # ── 1. Backup automatico ──
    if db_path.exists():
        backup_name = f"crm_pre_production_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = DATA_DIR / backup_name
        shutil.copy2(db_path, backup_path)
        print(f"[1/4] Backup salvato: {backup_name}")
    else:
        print("[1/4] Nessun database esistente")

    # ── 2. Drop + recreate schema ──
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    print(f"[2/4] Schema ricreato: {len(SQLModel.metadata.tables)} tabelle")

    # ── 3. Crea Chiara Bassani ──
    with Session(engine) as session:
        trainer = Trainer(
            email=CHIARA["email"],
            nome=CHIARA["nome"],
            cognome=CHIARA["cognome"],
            hashed_password=hash_password(CHIARA["password"]),
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        session.add(trainer)
        session.commit()
        session.refresh(trainer)
        print(f"[3/4] Trainer creato: {trainer.nome} {trainer.cognome} (id={trainer.id})")

    # ── 4. Alembic version stamp ──
    with Session(engine) as session:
        session.exec(text(
            "CREATE TABLE IF NOT EXISTS alembic_version "
            "(version_num VARCHAR(32) NOT NULL, "
            "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
        ))
        session.exec(text("DELETE FROM alembic_version"))
        session.exec(text(
            f"INSERT INTO alembic_version (version_num) "
            f"VALUES ('{LATEST_ALEMBIC_VERSION}')"
        ))
        session.commit()
        print(f"[4/4] Alembic version: {LATEST_ALEMBIC_VERSION}")

    print(f"\n=== PRODUZIONE PRONTA ===")
    print(f"Login: {CHIARA['email']} / {CHIARA['password']}")
    print(f"Database vuoto, zero dati di test.\n")


if __name__ == "__main__":
    run()
