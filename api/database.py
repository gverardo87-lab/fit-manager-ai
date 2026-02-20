# api/database.py
"""
Database layer con SQLModel (SQLAlchemy + Pydantic).

Perche' SQLModel e non sqlite3 raw:
- Cambi DATABASE_URL e passi a PostgreSQL senza toccare una query
- I modelli ORM SONO modelli Pydantic (zero conversione)
- Session management con dependency injection
- Connection pooling automatico (importante per multi-utente)
"""

from typing import Generator
from sqlmodel import SQLModel, Session, create_engine
from api.config import DATABASE_URL

# Engine — il "pool" di connessioni al database.
# connect_args necessario solo per SQLite (thread safety).
_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    echo=False,  # True per debug SQL queries
    connect_args=_connect_args,
)


def create_db_and_tables() -> None:
    """
    Crea tutte le tabelle definite nei modelli SQLModel.

    Usa CREATE TABLE IF NOT EXISTS: sicuro da chiamare piu' volte.
    NON sovrascrive tabelle esistenti, NON aggiunge colonne mancanti
    (per quello servono migrazioni esplicite).
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency injection per FastAPI: fornisce una session DB per request.

    Ogni richiesta HTTP ottiene la propria session. Al termine (successo o errore)
    la session viene chiusa automaticamente. Questo e' il pattern standard
    per applicazioni web con SQLAlchemy/SQLModel.

    Usage negli endpoint:
        @router.get("/clients")
        def get_clients(session: Session = Depends(get_session)):
            clients = session.exec(select(Client)).all()
    """
    with Session(engine) as session:
        yield session
