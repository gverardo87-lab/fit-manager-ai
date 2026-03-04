# api/database.py
"""
Database layer con SQLModel (SQLAlchemy + Pydantic).

Architettura dual-database:
  - business engine (data.db / crm.db): dati trainer, clienti, contratti, workout
  - catalog engine (catalog.db): tassonomia scientifica (muscoli, articolazioni, condizioni, metriche)

Perche' SQLModel e non sqlite3 raw:
- Cambi DATABASE_URL e passi a PostgreSQL senza toccare una query
- I modelli ORM SONO modelli Pydantic (zero conversione)
- Session management con dependency injection
- Connection pooling automatico (importante per multi-utente)
"""

import logging
from typing import Generator

from sqlalchemy import event
from sqlmodel import SQLModel, Session, create_engine

from api.config import CATALOG_DATABASE_URL, DATABASE_URL

logger = logging.getLogger("fitmanager.database")

# --- SQLite PRAGMA setup ---


def _setup_sqlite_pragmas(dbapi_conn, connection_record):
    """
    Configura PRAGMA SQLite per sicurezza e performance.

    - WAL: crash resistance, letture concorrenti
    - foreign_keys: integrita' referenziale enforced
    - busy_timeout: evita "database is locked" su accessi concorrenti
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


# --- Business Engine (data.db / crm.db) ---

_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=_connect_args,
)

if DATABASE_URL.startswith("sqlite"):
    event.listen(engine, "connect", _setup_sqlite_pragmas)

# --- Catalog Engine (catalog.db) ---

_catalog_connect_args = {}
if CATALOG_DATABASE_URL.startswith("sqlite"):
    _catalog_connect_args = {"check_same_thread": False}

catalog_engine = create_engine(
    CATALOG_DATABASE_URL,
    echo=False,
    connect_args=_catalog_connect_args,
)

if CATALOG_DATABASE_URL.startswith("sqlite"):
    event.listen(catalog_engine, "connect", _setup_sqlite_pragmas)


# --- Table creation ---

# Tabelle catalog (tassonomia scientifica)
CATALOG_TABLE_NAMES = frozenset({
    "muscoli",
    "esercizi_muscoli",
    "articolazioni",
    "esercizi_articolazioni",
    "condizioni_mediche",
    "esercizi_condizioni",
    "metriche",
})


def create_db_and_tables() -> None:
    """
    Crea le tabelle BUSINESS nel database principale (data.db).

    Usa CREATE TABLE IF NOT EXISTS: sicuro da chiamare piu' volte.
    NON sovrascrive tabelle esistenti, NON aggiunge colonne mancanti
    (per quello servono migrazioni esplicite).
    """
    SQLModel.metadata.create_all(engine)


def create_catalog_tables() -> None:
    """
    Crea le tabelle CATALOG nel database tassonomico (catalog.db).

    Usato da build_catalog.py per creare catalog.db da zero.
    In produzione, catalog.db viene shippato pre-costruito.
    """
    tables = [
        t for t in SQLModel.metadata.sorted_tables
        if t.name in CATALOG_TABLE_NAMES
    ]
    SQLModel.metadata.create_all(catalog_engine, tables=tables)


# --- Session factories ---


def get_session() -> Generator[Session, None, None]:
    """
    Dependency injection per FastAPI: session BUSINESS (data.db).

    Usata dalla maggior parte degli endpoint (clienti, contratti, agenda, etc.).
    """
    with Session(engine) as session:
        yield session


def get_catalog_session() -> Generator[Session, None, None]:
    """
    Dependency injection per FastAPI: session CATALOG (catalog.db).

    Usata dagli endpoint che leggono tassonomia scientifica:
    - Dettaglio esercizio (muscoli, articolazioni)
    - Safety map (condizioni mediche)
    - Metriche (misurazioni, obiettivi)
    """
    with Session(catalog_engine) as session:
        yield session
