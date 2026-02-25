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
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from sqlmodel import Session, text

from api.database import get_session

from api.config import API_PREFIX
from api.database import create_db_and_tables, engine
from api.seed_exercises import seed_builtin_exercises
from api.auth.router import router as auth_router
from api.routers.clients import router as clients_router
from api.routers.agenda import router as agenda_router
from api.routers.contracts import router as contracts_router
from api.routers.rates import router as rates_router
from api.routers.movements import router as movements_router
from api.routers.recurring_expenses import router as recurring_expenses_router
from api.routers.dashboard import router as dashboard_router
from api.routers.backup import router as backup_router
from api.routers.todos import router as todos_router
from api.routers.exercises import router as exercises_router
from api.routers.workouts import router as workouts_router

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

    # Seed esercizi builtin (idempotente)
    from sqlmodel import Session as SyncSession
    with SyncSession(engine) as session:
        seed_builtin_exercises(session)

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

# CORS: regex per accettare localhost, LAN (192.168.x.x), Tailscale (100.x.x.x)
# Nessun IP hardcodato — funziona da qualsiasi rete automaticamente.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|100\.\d+\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files: serve media (immagini/video esercizi)
_media_dir = Path(os.path.dirname(__file__)).parent / "data" / "media"
_media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(_media_dir)), name="media")

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
app.include_router(todos_router, prefix=API_PREFIX)
app.include_router(exercises_router, prefix=API_PREFIX)
app.include_router(workouts_router, prefix=API_PREFIX)


@app.get("/health")
def health_check(session: Session = Depends(get_session)):
    """Endpoint di salute — verifica connettivita' DB."""
    try:
        session.exec(text("SELECT 1")).one()
        return {"status": "ok", "version": "1.0.0", "db": "connected"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database non raggiungibile",
        )
