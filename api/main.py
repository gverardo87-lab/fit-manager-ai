# api/main.py
"""
FastAPI application — entry point dell'API REST.

Avvia con: uvicorn api.main:app --reload --port 8000
Poi apri: http://localhost:8000/docs (Swagger UI interattiva)

Cosa succede al startup:
1. Crea tabelle SQLModel (trainers, audit_log) — CREATE IF NOT EXISTS
2. Registra tutti i router (auth, clients, agenda, contracts, rates, movements, dashboard, backup)

Migrazioni schema gestite da Alembic: `alembic upgrade head`
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import API_PREFIX
from api.database import create_db_and_tables
from api.auth.router import router as auth_router
from api.routers.clients import router as clients_router
from api.routers.agenda import router as agenda_router
from api.routers.contracts import router as contracts_router
from api.routers.rates import router as rates_router
from api.routers.movements import router as movements_router
from api.routers.recurring_expenses import router as recurring_expenses_router
from api.routers.dashboard import router as dashboard_router
from api.routers.backup import router as backup_router

logger = logging.getLogger("fitmanager.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle dell'app.

    - Crea tabelle SQLModel (CREATE IF NOT EXISTS) — primo avvio
    - Migrazioni gestite da Alembic: `alembic upgrade head`
    """
    logger.info("API startup: inizializzazione database...")
    create_db_and_tables()
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
        "http://localhost:3000",    # Next.js dev server
        "http://localhost:5173",    # Vite dev server (fallback)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra router
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(clients_router, prefix=API_PREFIX)
app.include_router(agenda_router, prefix=API_PREFIX)
app.include_router(contracts_router, prefix=API_PREFIX)
app.include_router(rates_router, prefix=API_PREFIX)
app.include_router(movements_router, prefix=API_PREFIX)
app.include_router(recurring_expenses_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(backup_router, prefix=API_PREFIX)


@app.get("/health")
def health_check():
    """Endpoint di salute — usato per monitoring e load balancer."""
    return {"status": "ok", "version": "1.0.0"}
