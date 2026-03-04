#!/usr/bin/env python3
"""
build_catalog.py — Costruisce catalog.db dalle tabelle tassonomiche del DB sorgente.

Estrae le 7 tabelle catalog dal DB monolitico (crm.db o crm_dev.db)
e le copia in un catalog.db pulito e autonomo.

Tabelle catalog (4 cataloghi + 3 junction):
  - muscoli (53 record)
  - articolazioni (15 record)
  - condizioni_mediche (47 record)
  - metriche (~22 record)
  - esercizi_muscoli (~1271 junction)
  - esercizi_articolazioni (~299 junction)
  - esercizi_condizioni (~3600 junction)

Le junction hanno id_esercizio SENZA FK (riferimento cross-DB al business DB).
FK intra-catalog (id_muscolo, id_articolazione, id_condizione) enforced.

Usage:
  python -m tools.admin_scripts.build_catalog                    # default: crm.db → catalog.db
  python -m tools.admin_scripts.build_catalog --source crm_dev   # da crm_dev.db
  python -m tools.admin_scripts.build_catalog --dry-run           # solo conteggi, zero scrittura
"""

import argparse
import hashlib
import logging
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("build_catalog")


# ── Tabelle in ordine di creazione (cataloghi prima, junction dopo — FK safe) ──

CATALOG_TABLES = [
    "muscoli",
    "articolazioni",
    "condizioni_mediche",
    "metriche",
    "esercizi_muscoli",
    "esercizi_articolazioni",
    "esercizi_condizioni",
]

# ── DDL — FK intra-catalog enforced, id_esercizio senza FK (cross-DB) ──

CATALOG_DDL = {
    "muscoli": """
        CREATE TABLE IF NOT EXISTS muscoli (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR NOT NULL,
            nome_en VARCHAR NOT NULL,
            gruppo VARCHAR NOT NULL,
            regione VARCHAR NOT NULL
        )
    """,
    "articolazioni": """
        CREATE TABLE IF NOT EXISTS articolazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR NOT NULL,
            nome_en VARCHAR NOT NULL,
            tipo VARCHAR NOT NULL,
            regione VARCHAR NOT NULL
        )
    """,
    "condizioni_mediche": """
        CREATE TABLE IF NOT EXISTS condizioni_mediche (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR NOT NULL,
            nome_en VARCHAR NOT NULL,
            categoria VARCHAR NOT NULL,
            body_tags VARCHAR
        )
    """,
    "metriche": """
        CREATE TABLE IF NOT EXISTS metriche (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR NOT NULL,
            nome_en VARCHAR,
            unita_misura VARCHAR NOT NULL,
            categoria VARCHAR NOT NULL,
            ordinamento INTEGER DEFAULT 0
        )
    """,
    "esercizi_muscoli": """
        CREATE TABLE IF NOT EXISTS esercizi_muscoli (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_esercizio INTEGER NOT NULL,
            id_muscolo INTEGER NOT NULL REFERENCES muscoli(id),
            ruolo VARCHAR NOT NULL,
            attivazione INTEGER
        )
    """,
    "esercizi_articolazioni": """
        CREATE TABLE IF NOT EXISTS esercizi_articolazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_esercizio INTEGER NOT NULL,
            id_articolazione INTEGER NOT NULL REFERENCES articolazioni(id),
            ruolo VARCHAR NOT NULL,
            rom_gradi INTEGER
        )
    """,
    "esercizi_condizioni": """
        CREATE TABLE IF NOT EXISTS esercizi_condizioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_esercizio INTEGER NOT NULL,
            id_condizione INTEGER NOT NULL REFERENCES condizioni_mediche(id),
            severita VARCHAR NOT NULL,
            nota VARCHAR
        )
    """,
}

# ── Indici per performance query ──

CATALOG_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_muscoli_nome ON muscoli(nome)",
    "CREATE INDEX IF NOT EXISTS ix_muscoli_gruppo ON muscoli(gruppo)",
    "CREATE INDEX IF NOT EXISTS ix_articolazioni_nome ON articolazioni(nome)",
    "CREATE INDEX IF NOT EXISTS ix_condizioni_nome ON condizioni_mediche(nome)",
    "CREATE INDEX IF NOT EXISTS ix_condizioni_categoria ON condizioni_mediche(categoria)",
    "CREATE INDEX IF NOT EXISTS ix_metriche_categoria ON metriche(categoria)",
    "CREATE INDEX IF NOT EXISTS ix_em_esercizio ON esercizi_muscoli(id_esercizio)",
    "CREATE INDEX IF NOT EXISTS ix_em_muscolo ON esercizi_muscoli(id_muscolo)",
    "CREATE INDEX IF NOT EXISTS ix_ea_esercizio ON esercizi_articolazioni(id_esercizio)",
    "CREATE INDEX IF NOT EXISTS ix_ea_articolazione ON esercizi_articolazioni(id_articolazione)",
    "CREATE INDEX IF NOT EXISTS ix_ec_esercizio ON esercizi_condizioni(id_esercizio)",
    "CREATE INDEX IF NOT EXISTS ix_ec_condizione ON esercizi_condizioni(id_condizione)",
]


def _compute_sha256(file_path: Path) -> str:
    """Calcola SHA-256 di un file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_source(name: str) -> Path:
    """Risolve il path del DB sorgente da nome breve o path completo."""
    # Path completo
    p = Path(name)
    if p.suffix == ".db" and p.exists():
        return p
    # Nome breve: "crm" → data/crm.db, "crm_dev" → data/crm_dev.db
    candidate = DATA_DIR / f"{name}.db"
    if candidate.exists():
        return candidate
    # Fallback: prova come path relativo
    if p.exists():
        return p
    return candidate  # ritorna comunque (errore gestito dopo)


def build_catalog(
    source_path: Path,
    dest_path: Path,
    dry_run: bool = False,
) -> dict[str, int]:
    """
    Costruisce catalog.db dal DB sorgente via ATTACH DATABASE.

    Steps:
    1. Crea catalog.db con DDL pulito (no FK cross-DB su id_esercizio)
    2. ATTACH sorgente come 'src'
    3. Copia dati tabella per tabella con colonne esplicite
    4. Crea indici
    5. PRAGMA integrity_check
    6. SHA-256 checksum + sidecar

    Returns: dict con conteggio record per tabella.
    """
    if not source_path.exists():
        logger.error("DB sorgente non trovato: %s", source_path)
        sys.exit(1)

    # Verifica sorgente integro
    src_conn = sqlite3.connect(str(source_path))
    result = src_conn.execute("PRAGMA integrity_check").fetchone()
    if not result or result[0] != "ok":
        logger.error("DB sorgente non supera integrity_check: %s", result)
        src_conn.close()
        sys.exit(1)

    # Verifica tabelle presenti nel sorgente
    existing = {
        row[0]
        for row in src_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    src_conn.close()

    missing = [t for t in CATALOG_TABLES if t not in existing]
    if missing:
        logger.error("Tabelle mancanti nel DB sorgente: %s", missing)
        sys.exit(1)

    # Dry run: solo conteggi
    if dry_run:
        logger.info("=== DRY RUN — solo conteggi ===")
        conn = sqlite3.connect(str(source_path))
        counts = {}
        for table in CATALOG_TABLES:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            counts[table] = count
            logger.info("  %-25s %6d record", table, count)
        conn.close()
        return counts

    # Rimuovi catalog.db esistente (rebuild completo)
    if dest_path.exists():
        dest_path.unlink()
        sidecar = dest_path.with_suffix(".sha256")
        sidecar.unlink(missing_ok=True)
        logger.info("Rimosso catalog.db esistente")

    # Crea catalog.db e ATTACH sorgente
    catalog = sqlite3.connect(str(dest_path))
    catalog.execute("PRAGMA journal_mode=WAL")
    catalog.execute("PRAGMA foreign_keys=OFF")  # OFF durante population (id_esercizio cross-DB)

    # Crea tabelle con DDL pulito
    for table_name in CATALOG_TABLES:
        catalog.execute(CATALOG_DDL[table_name])
    logger.info("Tabelle create: %d", len(CATALOG_TABLES))

    # ATTACH sorgente
    catalog.execute("ATTACH DATABASE ? AS src", (str(source_path),))

    # Copia dati con colonne esplicite (ordine garantito dal DDL destinazione)
    counts = {}
    for table_name in CATALOG_TABLES:
        # Colonne dalla tabella destinazione (ordine DDL)
        cols_info = catalog.execute(f"PRAGMA table_info({table_name})").fetchall()
        col_names = [c[1] for c in cols_info]
        cols_str = ", ".join(col_names)

        catalog.execute(
            f"INSERT INTO main.{table_name} ({cols_str}) "
            f"SELECT {cols_str} FROM src.{table_name}"
        )
        count = catalog.execute(f"SELECT COUNT(*) FROM main.{table_name}").fetchone()[0]
        counts[table_name] = count
        logger.info("  %-25s %6d record copiati", table_name, count)

    # Commit PRIMA di DETACH (transazione implicita dagli INSERT)
    catalog.commit()
    catalog.execute("DETACH DATABASE src")

    # Crea indici
    for idx_sql in CATALOG_INDEXES:
        catalog.execute(idx_sql)
    logger.info("Indici creati: %d", len(CATALOG_INDEXES))

    # Abilita FK e commit finale
    catalog.execute("PRAGMA foreign_keys=ON")
    catalog.commit()

    # Integrity check finale
    result = catalog.execute("PRAGMA integrity_check").fetchone()
    if not result or result[0] != "ok":
        logger.error("PRAGMA integrity_check FALLITO su catalog.db: %s", result)
        catalog.close()
        dest_path.unlink(missing_ok=True)
        sys.exit(1)
    logger.info("PRAGMA integrity_check: OK")

    catalog.close()

    # SHA-256 checksum + sidecar
    checksum = _compute_sha256(dest_path)
    sidecar = dest_path.with_suffix(".sha256")
    sidecar.write_text(f"{checksum}  {dest_path.name}\n")
    size = dest_path.stat().st_size

    logger.info("SHA-256: %s", checksum[:16])
    logger.info("catalog.db: %d bytes", size)

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Costruisce catalog.db dalle tabelle tassonomiche del DB sorgente"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="crm",
        help="DB sorgente: 'crm', 'crm_dev', o path completo (default: crm)",
    )
    parser.add_argument(
        "--dest",
        type=str,
        default=str(DATA_DIR / "catalog.db"),
        help="Path catalog.db destinazione (default: data/catalog.db)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo conteggi, zero scrittura",
    )
    args = parser.parse_args()

    source_path = _resolve_source(args.source)
    dest_path = Path(args.dest)

    logger.info("=== Build Catalog DB ===")
    logger.info("Sorgente:     %s", source_path)
    logger.info("Destinazione: %s", dest_path)
    logger.info("")

    counts = build_catalog(source_path, dest_path, dry_run=args.dry_run)

    total = sum(counts.values())
    logger.info("")
    logger.info("=== Riepilogo ===")
    for table, count in counts.items():
        logger.info("  %-25s %6d", table, count)
    logger.info("  %-25s %6d", "TOTALE", total)
    logger.info("")

    if args.dry_run:
        logger.info("Dry run completato. Nessun file creato.")
    else:
        logger.info("Catalog DB pronto: %s", dest_path)


if __name__ == "__main__":
    main()
