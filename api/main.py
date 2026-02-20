# api/main.py
"""
FastAPI application — entry point dell'API REST.

Avvia con: uvicorn api.main:app --reload --port 8000
Poi apri: http://localhost:8000/docs (Swagger UI interattiva)

Cosa succede al startup:
1. Crea tabella 'trainers' se non esiste
2. Aggiunge colonna 'trainer_id' a 'clienti' se non esiste
3. Registra tutti i router (auth, clients, ...)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import API_PREFIX
from api.database import create_db_and_tables, engine
from api.auth.router import router as auth_router
from api.routers.clients import router as clients_router

logger = logging.getLogger("fitmanager.api")


def _run_migrations() -> None:
    """
    Migrazioni al startup — idempotenti, sicure da rieseguire.

    Fase 1: Aggiunge trainer_id a clienti (nullable, per convivenza con Streamlit).
    Le tabelle nuove (trainers) vengono create da SQLModel.metadata.create_all().
    """
    import sqlite3
    from api.config import DATABASE_URL

    if not DATABASE_URL.startswith("sqlite"):
        return  # Solo per SQLite — PostgreSQL usera' Alembic

    # Estrai path dal URL sqlite:///path/to/db
    db_path = DATABASE_URL.replace("sqlite:///", "")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Controlla se trainer_id esiste gia' in clienti
    cursor.execute("PRAGMA table_info(clienti)")
    columns = [col[1] for col in cursor.fetchall()]

    if "trainer_id" not in columns:
        logger.info("Migration: aggiunta colonna trainer_id a clienti")
        cursor.execute("ALTER TABLE clienti ADD COLUMN trainer_id INTEGER REFERENCES trainers(id)")
        conn.commit()
    else:
        logger.debug("Migration: trainer_id gia' presente in clienti")

    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle dell'app: cose da fare prima di accettare richieste.

    1. Crea tabelle SQLModel (trainers, etc.) — CREATE IF NOT EXISTS
    2. Migrazioni manuali (ALTER TABLE per colonne nuove su tabelle esistenti)
    """
    logger.info("API startup: creazione tabelle e migrazioni...")
    create_db_and_tables()
    _run_migrations()
    logger.info("API pronta")
    yield
    logger.info("API shutdown")


# --- App FastAPI ---

app = FastAPI(
    title="ProFit AI Studio API",
    version="1.0.0",
    description="REST API per il CRM fitness. Multi-tenant, JWT auth, database-agnostic.",
    lifespan=lifespan,
)

# CORS: permetti al frontend React (porta 3000) di chiamare l'API (porta 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React dev server
        "http://localhost:8501",    # Streamlit (se servira')
        "http://localhost:5173",    # Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra router
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(clients_router, prefix=API_PREFIX)


@app.get("/health")
def health_check():
    """Endpoint di salute — usato per monitoring e load balancer."""
    return {"status": "ok", "version": "1.0.0"}
