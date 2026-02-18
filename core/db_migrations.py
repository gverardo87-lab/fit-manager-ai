"""
DB Migrations - Schema extensions for Trainer DNA system

Idempotent migrations (CREATE TABLE IF NOT EXISTS).
Called at page startup - safe to run multiple times.
"""

import sqlite3
from pathlib import Path
from core.error_handler import logger


class DBMigrations:
    """Gestisce migrazioni DB idempotenti per nuove feature."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def run_all(self):
        """Esegue tutte le migrazioni. Sicuro da chiamare ogni volta."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")

            self._migration_imported_cards(conn)
            self._migration_trainer_dna(conn)
            self._migration_exercise_edits(conn)

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB Migration error: {e}")

    def _migration_imported_cards(self, conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS imported_workout_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_path TEXT,
                raw_content TEXT,
                parsed_exercises TEXT,
                parsed_metadata TEXT,
                extraction_status TEXT DEFAULT 'pending',
                extraction_error TEXT,
                pattern_extracted INTEGER DEFAULT 0,
                imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_cliente) REFERENCES clienti(id) ON DELETE SET NULL
            )
        """)

    def _migration_trainer_dna(self, conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trainer_dna_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_key TEXT NOT NULL,
                pattern_value TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.5,
                evidence_count INTEGER DEFAULT 1,
                source_card_ids TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _migration_exercise_edits(self, conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workout_exercise_edits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_workout_plan INTEGER NOT NULL,
                week_number INTEGER NOT NULL,
                day_key TEXT NOT NULL,
                exercise_index INTEGER NOT NULL,
                original_exercise TEXT NOT NULL,
                edited_exercise TEXT NOT NULL,
                edit_type TEXT NOT NULL,
                edit_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_workout_plan) REFERENCES workout_plans(id) ON DELETE CASCADE
            )
        """)
