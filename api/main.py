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
        logger.info("Migration 6: aggiunta colonna acconto a contratti")
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
        logger.info("Migration 6: backfill acconto su %d contratti", backfilled)

    # --- Migrazione 7: backfill trainer_id orfani ---
    # Record creati da Streamlit senza trainer_id → assegna al primo trainer.
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
                logger.info("Migration 7: %d record orfani in %s assegnati a trainer %d",
                            cursor.rowcount, table, first_trainer)
        conn.commit()

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

    # --- Migrazione 9: riconciliazione pagamenti legacy Streamlit ---
    # Streamlit aggiornava totale_versato direttamente senza creare CashMovement.
    # Per ogni contratto con delta > 0.01, crea un movimento ENTRATA di riconciliazione.
    cursor.execute("""
        SELECT c.id, c.id_cliente, c.trainer_id, c.totale_versato, c.data_inizio,
               COALESCE(SUM(CASE WHEN m.tipo = 'ENTRATA' THEN m.importo ELSE 0 END), 0) as ledger
        FROM contratti c
        LEFT JOIN movimenti_cassa m ON m.id_contratto = c.id
        GROUP BY c.id
        HAVING ROUND(c.totale_versato - ledger, 2) > 0.01
    """)
    legacy_gaps = cursor.fetchall()
    for gap in legacy_gaps:
        cid, cliente_id, tid, versato, data_inizio, ledger = gap
        delta = round(versato - ledger, 2)
        # Controlla se esiste gia' un movimento di riconciliazione per questo contratto
        cursor.execute("""
            SELECT 1 FROM movimenti_cassa
            WHERE id_contratto = ? AND categoria = 'RICONCILIAZIONE_LEGACY'
        """, (cid,))
        if cursor.fetchone():
            continue
        cursor.execute("""
            INSERT INTO movimenti_cassa
                (trainer_id, data_effettiva, tipo, categoria, importo, note,
                 operatore, id_contratto, id_cliente)
            VALUES (?, ?, 'ENTRATA', 'RICONCILIAZIONE_LEGACY', ?, ?, 'MIGRAZIONE', ?, ?)
        """, (tid, data_inizio, delta,
              f"Riconciliazione pagamento legacy Streamlit ({delta:.2f} EUR)",
              cid, cliente_id))
        logger.info("Migration 9: riconciliazione +%.2f EUR per contratto %d", delta, cid)
    if legacy_gaps:
        conn.commit()

    # --- Migrazione 10: data_disattivazione su spese_ricorrenti ---
    cursor.execute("PRAGMA table_info(spese_ricorrenti)")
    spese_cols_v2 = [col[1] for col in cursor.fetchall()]
    if "data_disattivazione" not in spese_cols_v2:
        logger.info("Migration 10: aggiunta colonna data_disattivazione a spese_ricorrenti")
        cursor.execute("ALTER TABLE spese_ricorrenti ADD COLUMN data_disattivazione TIMESTAMP")
        conn.commit()

    # --- Migrazione 11: data_creazione su agenda ---
    cursor.execute("PRAGMA table_info(agenda)")
    agenda_cols = [col[1] for col in cursor.fetchall()]
    if "data_creazione" not in agenda_cols:
        logger.info("Migration 11: aggiunta colonna data_creazione a agenda")
        cursor.execute("ALTER TABLE agenda ADD COLUMN data_creazione TIMESTAMP")
        conn.commit()

    # --- Migrazione 12: FK Integrity Enforcement ---
    # SQLite non supporta ALTER TABLE ADD CONSTRAINT. Per aggiungere FK
    # a tabelle esistenti serve il "table rebuild": creare una nuova tabella
    # con i constraint, copiare i dati, eliminare la vecchia, rinominare.
    #
    # Ordine critico (le FK creano dipendenze tra tabelle):
    # 1. contratti      (riferisce clienti)
    # 2. rate_programmate (riferisce contratti)
    # 3. agenda          (riferisce clienti + contratti)
    # 4. movimenti_cassa (riferisce clienti + contratti + rate + spese)
    cursor.execute("PRAGMA foreign_key_list(rate_programmate)")
    rate_fks = {row[2] for row in cursor.fetchall()}
    if "contratti" not in rate_fks:
        logger.info("Migration 12: FK Integrity Enforcement — inizio rebuild tabelle")

        # FK OFF durante il rebuild per evitare violation temporanee
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Step 0: cleanup 3 record orfani in movimenti_cassa
        cursor.execute("""
            UPDATE movimenti_cassa SET id_spesa_ricorrente = NULL
            WHERE id_spesa_ricorrente IS NOT NULL
              AND id_spesa_ricorrente NOT IN (SELECT id FROM spese_ricorrenti)
        """)
        orphans_cleaned = cursor.rowcount
        if orphans_cleaned > 0:
            logger.info("Migration 12: puliti %d record orfani (id_spesa_ricorrente → NULL)",
                        orphans_cleaned)

        # Step 1: rebuild contratti (aggiunge FK id_cliente → clienti ON DELETE RESTRICT)
        cursor.execute("""
            CREATE TABLE contratti_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL REFERENCES clienti(id) ON DELETE RESTRICT,
                tipo_pacchetto TEXT,
                data_vendita DATE DEFAULT CURRENT_DATE,
                data_inizio DATE,
                data_scadenza DATE,
                crediti_totali INTEGER,
                crediti_usati INTEGER DEFAULT 0,
                prezzo_totale REAL,
                totale_versato REAL DEFAULT 0,
                stato_pagamento TEXT DEFAULT 'PENDENTE',
                note TEXT,
                chiuso BOOLEAN DEFAULT 0,
                trainer_id INTEGER REFERENCES trainers(id),
                acconto REAL DEFAULT 0
            )
        """)
        cursor.execute("""
            INSERT INTO contratti_new
                (id, id_cliente, tipo_pacchetto, data_vendita, data_inizio,
                 data_scadenza, crediti_totali, crediti_usati, prezzo_totale,
                 totale_versato, stato_pagamento, note, chiuso, trainer_id, acconto)
            SELECT id, id_cliente, tipo_pacchetto, data_vendita, data_inizio,
                   data_scadenza, crediti_totali, crediti_usati, prezzo_totale,
                   totale_versato, stato_pagamento, note, chiuso, trainer_id, acconto
            FROM contratti
        """)
        cursor.execute("DROP TABLE contratti")
        cursor.execute("ALTER TABLE contratti_new RENAME TO contratti")
        logger.info("Migration 12: rebuild contratti — FK id_cliente RESTRICT")

        # Step 2: rebuild rate_programmate (aggiunge FK id_contratto → contratti ON DELETE CASCADE)
        cursor.execute("""
            CREATE TABLE rate_programmate_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_contratto INTEGER NOT NULL REFERENCES contratti(id) ON DELETE CASCADE,
                data_scadenza DATE NOT NULL,
                importo_previsto REAL NOT NULL,
                descrizione TEXT,
                stato TEXT DEFAULT 'PENDENTE',
                importo_saldato REAL DEFAULT 0
            )
        """)
        cursor.execute("""
            INSERT INTO rate_programmate_new
                (id, id_contratto, data_scadenza, importo_previsto, descrizione,
                 stato, importo_saldato)
            SELECT id, id_contratto, data_scadenza, importo_previsto, descrizione,
                   stato, importo_saldato
            FROM rate_programmate
        """)
        cursor.execute("DROP TABLE rate_programmate")
        cursor.execute("ALTER TABLE rate_programmate_new RENAME TO rate_programmate")
        logger.info("Migration 12: rebuild rate_programmate — FK id_contratto CASCADE")

        # Step 3: rebuild agenda (aggiunge FK id_cliente + id_contratto ON DELETE SET NULL)
        cursor.execute("""
            CREATE TABLE agenda_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_inizio DATETIME NOT NULL,
                data_fine DATETIME NOT NULL,
                categoria TEXT NOT NULL,
                titolo TEXT,
                id_cliente INTEGER REFERENCES clienti(id) ON DELETE SET NULL,
                id_contratto INTEGER REFERENCES contratti(id) ON DELETE SET NULL,
                stato TEXT DEFAULT 'Programmato',
                note TEXT,
                trainer_id INTEGER REFERENCES trainers(id),
                data_creazione TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT INTO agenda_new
                (id, data_inizio, data_fine, categoria, titolo, id_cliente,
                 id_contratto, stato, note, trainer_id, data_creazione)
            SELECT id, data_inizio, data_fine, categoria, titolo, id_cliente,
                   id_contratto, stato, note, trainer_id, data_creazione
            FROM agenda
        """)
        cursor.execute("DROP TABLE agenda")
        cursor.execute("ALTER TABLE agenda_new RENAME TO agenda")
        logger.info("Migration 12: rebuild agenda — FK id_cliente/id_contratto SET NULL")

        # Step 4: rebuild movimenti_cassa (aggiunge tutte le FK mancanti ON DELETE SET NULL)
        cursor.execute("""
            CREATE TABLE movimenti_cassa_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_movimento DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_effettiva DATE NOT NULL DEFAULT CURRENT_DATE,
                tipo TEXT NOT NULL,
                categoria TEXT,
                importo REAL NOT NULL,
                metodo TEXT,
                id_cliente INTEGER REFERENCES clienti(id) ON DELETE SET NULL,
                id_contratto INTEGER REFERENCES contratti(id) ON DELETE SET NULL,
                id_rata INTEGER REFERENCES rate_programmate(id) ON DELETE SET NULL,
                note TEXT,
                operatore TEXT DEFAULT 'Admin',
                id_spesa_ricorrente INTEGER REFERENCES spese_ricorrenti(id) ON DELETE SET NULL,
                trainer_id INTEGER REFERENCES trainers(id),
                mese_anno TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO movimenti_cassa_new
                (id, data_movimento, data_effettiva, tipo, categoria, importo,
                 metodo, id_cliente, id_contratto, id_rata, note, operatore,
                 id_spesa_ricorrente, trainer_id, mese_anno)
            SELECT id, data_movimento, data_effettiva, tipo, categoria, importo,
                   metodo, id_cliente, id_contratto, id_rata, note, operatore,
                   id_spesa_ricorrente, trainer_id, mese_anno
            FROM movimenti_cassa
        """)
        cursor.execute("DROP TABLE movimenti_cassa")
        cursor.execute("ALTER TABLE movimenti_cassa_new RENAME TO movimenti_cassa")
        # Ricrea indice UNIQUE parziale per dedup spese ricorrenti
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_recurring_per_month
            ON movimenti_cassa (trainer_id, id_spesa_ricorrente, mese_anno)
            WHERE id_spesa_ricorrente IS NOT NULL
        """)
        logger.info("Migration 12: rebuild movimenti_cassa — 4 FK SET NULL + indice ricreato")

        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON")
        logger.info("Migration 12: FK Integrity Enforcement — completata")

    # --- Migrazione 13: Soft Delete — deleted_at su tutte le tabelle business ---
    for table in ["clienti", "contratti", "rate_programmate",
                  "agenda", "movimenti_cassa", "spese_ricorrenti"]:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [col[1] for col in cursor.fetchall()]
        if "deleted_at" not in cols:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN deleted_at TIMESTAMP")
            logger.info("Migration 13: aggiunta colonna deleted_at a %s", table)
    conn.commit()

    # --- Migrazione 14: Audit Trail — tabella audit_log ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            changes TEXT,
            trainer_id INTEGER NOT NULL REFERENCES trainers(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    logger.info("Migration 14: tabella audit_log pronta")

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


@app.get("/health")
def health_check():
    """Endpoint di salute — usato per monitoring e load balancer."""
    return {"status": "ok", "version": "1.0.0"}
