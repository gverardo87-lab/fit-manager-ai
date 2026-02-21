# api/main.py
"""
FastAPI application — entry point dell'API REST.

Avvia con: uvicorn api.main:app --reload --port 8000
Poi apri: http://localhost:8000/docs (Swagger UI interattiva)

Cosa succede al startup:
1. Crea tabella 'trainers' se non esiste
2. Aggiunge colonna 'trainer_id' a 'clienti' se non esiste
3. Aggiunge colonna 'trainer_id' a 'agenda' se non esiste
4. Aggiunge colonna 'trainer_id' a 'contratti' se non esiste
5. Aggiunge colonna 'trainer_id' a 'movimenti_cassa' se non esiste
6. Registra tutti i router (auth, clients, agenda, contracts, rates, movements, dashboard)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import API_PREFIX
from api.database import create_db_and_tables, engine
from api.auth.router import router as auth_router
from api.routers.clients import router as clients_router
from api.routers.agenda import router as agenda_router
from api.routers.contracts import router as contracts_router
from api.routers.rates import router as rates_router
from api.routers.movements import router as movements_router
from api.routers.recurring_expenses import router as recurring_expenses_router
from api.routers.dashboard import router as dashboard_router

logger = logging.getLogger("fitmanager.api")


def _run_migrations() -> None:
    """
    Migrazioni al startup — idempotenti, sicure da rieseguire.

    Aggiunge trainer_id (nullable) alle tabelle esistenti per multi-tenancy:
    - clienti: FK verso trainers per filtrare clienti per trainer
    - agenda: FK verso trainers per filtrare TUTTI gli eventi (anche quelli senza cliente)
    - contratti: FK verso trainers per filtrare contratti (Deep Relational IDOR base)
    - movimenti_cassa: FK verso trainers per filtrare il libro mastro

    Le tabelle nuove (trainers) vengono create da SQLModel.metadata.create_all().
    """
    import sqlite3
    from api.config import DATABASE_URL

    if not DATABASE_URL.startswith("sqlite"):
        return  # Solo per SQLite — PostgreSQL usera' Alembic

    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # --- Migrazione 1: trainer_id su clienti ---
    cursor.execute("PRAGMA table_info(clienti)")
    clienti_cols = [col[1] for col in cursor.fetchall()]
    if "trainer_id" not in clienti_cols:
        logger.info("Migration: aggiunta colonna trainer_id a clienti")
        cursor.execute("ALTER TABLE clienti ADD COLUMN trainer_id INTEGER REFERENCES trainers(id)")
        conn.commit()

    # --- Migrazione 2: trainer_id su agenda ---
    cursor.execute("PRAGMA table_info(agenda)")
    agenda_cols = [col[1] for col in cursor.fetchall()]
    if "trainer_id" not in agenda_cols:
        logger.info("Migration: aggiunta colonna trainer_id a agenda")
        cursor.execute("ALTER TABLE agenda ADD COLUMN trainer_id INTEGER REFERENCES trainers(id)")
        conn.commit()

    # --- Migrazione 3: trainer_id su contratti ---
    cursor.execute("PRAGMA table_info(contratti)")
    contratti_cols = [col[1] for col in cursor.fetchall()]
    if "trainer_id" not in contratti_cols:
        logger.info("Migration: aggiunta colonna trainer_id a contratti")
        cursor.execute("ALTER TABLE contratti ADD COLUMN trainer_id INTEGER REFERENCES trainers(id)")
        conn.commit()

    # --- Migrazione 4: trainer_id su movimenti_cassa ---
    cursor.execute("PRAGMA table_info(movimenti_cassa)")
    movimenti_cols = [col[1] for col in cursor.fetchall()]
    if "trainer_id" not in movimenti_cols:
        logger.info("Migration: aggiunta colonna trainer_id a movimenti_cassa")
        cursor.execute("ALTER TABLE movimenti_cassa ADD COLUMN trainer_id INTEGER REFERENCES trainers(id)")
        conn.commit()

    # --- Migrazione 5: trainer_id su spese_ricorrenti ---
    cursor.execute("PRAGMA table_info(spese_ricorrenti)")
    spese_cols = [col[1] for col in cursor.fetchall()]
    if "trainer_id" not in spese_cols:
        logger.info("Migration: aggiunta colonna trainer_id a spese_ricorrenti")
        cursor.execute("ALTER TABLE spese_ricorrenti ADD COLUMN trainer_id INTEGER REFERENCES trainers(id)")
        conn.commit()

    # --- Migrazione 6: acconto su contratti ---
    cursor.execute("PRAGMA table_info(contratti)")
    contratti_cols_v2 = [col[1] for col in cursor.fetchall()]
    if "acconto" not in contratti_cols_v2:
        logger.info("Migration: aggiunta colonna acconto a contratti")
        cursor.execute("ALTER TABLE contratti ADD COLUMN acconto REAL DEFAULT 0")
        # Backfill: recupera acconto da CashMovement ACCONTO_CONTRATTO
        cursor.execute("""
            UPDATE contratti SET acconto = COALESCE(
                (SELECT SUM(m.importo)
                 FROM movimenti_cassa m
                 WHERE m.id_contratto = contratti.id
                   AND m.categoria = 'ACCONTO_CONTRATTO'
                   AND m.tipo = 'ENTRATA'),
                0
            )
        """)
        backfilled = cursor.rowcount
        conn.commit()
        logger.info("Migration: backfill acconto su %d contratti", backfilled)

    # --- Migrazione 8: colonna mese_anno + dedup spese ricorrenti ---
    cursor.execute("PRAGMA table_info(movimenti_cassa)")
    mov_cols_v2 = [col[1] for col in cursor.fetchall()]
    if "mese_anno" not in mov_cols_v2:
        logger.info("Migration 8: aggiunta colonna mese_anno a movimenti_cassa")
        cursor.execute("ALTER TABLE movimenti_cassa ADD COLUMN mese_anno TEXT")

        # Backfill: popola mese_anno per movimenti di spese ricorrenti esistenti
        cursor.execute("""
            UPDATE movimenti_cassa
            SET mese_anno = strftime('%Y-%m', data_effettiva)
            WHERE id_spesa_ricorrente IS NOT NULL AND mese_anno IS NULL
        """)
        backfilled = cursor.rowcount
        logger.info("Migration 8: backfill mese_anno su %d movimenti", backfilled)

        # Cleanup duplicati: per ogni (trainer_id, id_spesa_ricorrente, mese_anno)
        # con piu' di un record, elimina tutti tranne il primo (MIN id)
        cursor.execute("""
            DELETE FROM movimenti_cassa
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM movimenti_cassa
                WHERE id_spesa_ricorrente IS NOT NULL
                GROUP BY trainer_id, id_spesa_ricorrente, mese_anno
            )
            AND id_spesa_ricorrente IS NOT NULL
        """)
        cleaned = cursor.rowcount
        if cleaned > 0:
            logger.info("Migration 8: rimossi %d movimenti duplicati spese fisse", cleaned)

        # UNIQUE parziale: impedisce futuri duplicati a livello DB
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_recurring_per_month
            ON movimenti_cassa (trainer_id, id_spesa_ricorrente, mese_anno)
            WHERE id_spesa_ricorrente IS NOT NULL
        """)
        conn.commit()
        logger.info("Migration 8: indice univoco uq_recurring_per_month creato")

    # --- Migrazione 7: backfill trainer_id orfani ---
    # Se Streamlit crea record senza trainer_id, li assegna al primo trainer.
    cursor.execute("SELECT MIN(id) FROM trainers")
    row = cursor.fetchone()
    first_trainer = row[0] if row else None
    if first_trainer:
        for table in ["clienti", "agenda", "contratti", "movimenti_cassa", "spese_ricorrenti"]:
            cursor.execute(
                f"UPDATE {table} SET trainer_id = ? WHERE trainer_id IS NULL",
                (first_trainer,),
            )
            if cursor.rowcount > 0:
                logger.info("Migration: %d record orfani in %s assegnati a trainer %d",
                            cursor.rowcount, table, first_trainer)
        conn.commit()

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
app.include_router(agenda_router, prefix=API_PREFIX)
app.include_router(contracts_router, prefix=API_PREFIX)
app.include_router(rates_router, prefix=API_PREFIX)
app.include_router(movements_router, prefix=API_PREFIX)
app.include_router(recurring_expenses_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)


@app.get("/health")
def health_check():
    """Endpoint di salute — usato per monitoring e load balancer."""
    return {"status": "ok", "version": "1.0.0"}
