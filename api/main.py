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
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from sqlmodel import Session, text

from api.database import get_catalog_session, get_session

from api.config import API_PREFIX, CATALOG_DATABASE_URL, DATA_DIR
from api.database import create_catalog_tables, create_db_and_tables, engine
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
from api.routers.measurements import router as measurements_router
from api.routers.goals import router as goals_router
from api.routers.workout_logs import router as workout_logs_router
from api.routers.assistant import router as assistant_router

logger = logging.getLogger("fitmanager.api")

BACKUP_DIR = DATA_DIR / "backups"
MAX_AUTO_BACKUPS = 5  # solo gli ultimi 5 backup automatici


def _auto_backup_on_startup(database_url: str) -> None:
    """
    Backup automatico del DB business al startup (solo prod).

    Usa sqlite3.backup() per copia atomica. Mantiene max 5 backup auto.
    Non blocca se fallisce (best-effort, log error).
    """
    db_path = database_url.replace("sqlite:///", "")
    if not Path(db_path).exists():
        return

    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = BACKUP_DIR / f"auto_{timestamp}.sqlite"

        source = sqlite3.connect(db_path)
        backup = sqlite3.connect(str(dest))
        try:
            source.backup(backup)
        finally:
            backup.close()
            source.close()

        size = dest.stat().st_size
        logger.info(f"Auto-backup: {dest.name} ({size:,} bytes)")

        # Retention: solo ultimi MAX_AUTO_BACKUPS
        auto_files = sorted(
            BACKUP_DIR.glob("auto_*.sqlite"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in auto_files[MAX_AUTO_BACKUPS:]:
            old.unlink(missing_ok=True)
            old.with_suffix(".sha256").unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"Auto-backup fallito (non bloccante): {e}")


def _integrity_check_on_startup(business_url: str, catalog_url: str) -> None:
    """
    PRAGMA integrity_check su entrambi i DB al startup.

    Se fallisce, log CRITICAL ma NON blocca (l'app parte comunque).
    L'operatore deve intervenire con restore.
    """
    for label, url in [("business", business_url), ("catalog", catalog_url)]:
        if not url.startswith("sqlite"):
            continue
        db_path = url.replace("sqlite:///", "")
        if not Path(db_path).exists():
            continue
        try:
            conn = sqlite3.connect(db_path)
            result = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if result and result[0] == "ok":
                logger.info(f"  {label} DB integrity: OK")
            else:
                logger.critical(f"  {label} DB integrity: FALLITO — {result}")
        except Exception as e:
            logger.critical(f"  {label} DB integrity check error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle dell'app.

    Startup sequence:
    1. Auto-backup (solo prod, non dev — protegge dati reali)
    2. Crea tabelle business (CREATE IF NOT EXISTS)
    3. Inizializza catalog DB
    4. Seed esercizi builtin
    5. Integrity check
    """
    from api.config import DATABASE_URL
    db_label = "DEV (crm_dev.db)" if "crm_dev" in DATABASE_URL else "PROD (crm.db)"
    is_dev = "crm_dev" in DATABASE_URL
    logger.info(f"API startup: database {db_label}")
    # Maschera credenziali per PostgreSQL (user:pass@host)
    safe_url = DATABASE_URL
    if "@" in DATABASE_URL:
        safe_url = DATABASE_URL.split("@", 1)[0].rsplit(":", 1)[0] + ":***@" + DATABASE_URL.split("@", 1)[1]
    logger.info(f"  DATABASE_URL = {safe_url}")

    # ── 1. Auto-backup (solo prod) ──
    if not is_dev and DATABASE_URL.startswith("sqlite"):
        _auto_backup_on_startup(DATABASE_URL)

    # ── 2. Business tables ──
    create_db_and_tables()

    # ── 3. Catalog DB ──
    catalog_path = CATALOG_DATABASE_URL.replace("sqlite:///", "")
    if not Path(catalog_path).exists():
        logger.warning("catalog.db non trovato — creo tabelle vuote. "
                       "Eseguire: python -m tools.admin_scripts.build_catalog")
    create_catalog_tables()
    logger.info(f"  CATALOG_DB = {catalog_path}")

    # ── 4. Seed esercizi builtin (idempotente) ──
    from sqlmodel import Session as SyncSession
    with SyncSession(engine) as session:
        seed_builtin_exercises(session)

    # ── 5. Integrity check ──
    _integrity_check_on_startup(DATABASE_URL, CATALOG_DATABASE_URL)

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
app.include_router(measurements_router, prefix=API_PREFIX)
app.include_router(goals_router, prefix=API_PREFIX)
app.include_router(workout_logs_router, prefix=API_PREFIX)
app.include_router(assistant_router, prefix=API_PREFIX)


@app.get("/health")
def health_check(
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
):
    """Endpoint di salute — verifica connettivita' business DB + catalog DB."""
    try:
        session.exec(text("SELECT 1")).one()
        catalog_session.exec(text("SELECT 1")).one()
        return {"status": "ok", "version": "1.0.0", "db": "connected", "catalog": "connected"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database non raggiungibile",
        )
