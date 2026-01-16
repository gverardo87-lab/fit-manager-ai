# file: core/crm_db.py (Versione FitManager 3.0 - Definitive Core)
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime
from datetime import date
from contextlib import contextmanager

# Percorso DB
DB_FILE = Path(__file__).resolve().parents[1] / "data" / "crm.db"

class CrmDBManager:
    def __init__(self, db_path: str | Path = DB_FILE):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 1. CLIENTI (Ex Anagrafica)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS clienti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, cognome TEXT NOT NULL,
                telefono TEXT, email TEXT,
                data_nascita DATE, sesso TEXT,
                anamnesi_json TEXT,      -- Dati clinici (JSON)
                stato TEXT DEFAULT 'Attivo',
                data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

            # 2. CONTRATTI (Portafoglio)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS contratti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                tipo_pacchetto TEXT,     -- Es. '10 PT', 'Mensile'
                data_inizio DATE, data_scadenza DATE,
                crediti_totali INTEGER, prezzo_pattuito REAL,
                note TEXT, chiuso BOOLEAN DEFAULT 0
            )""")

            # 3. PAGAMENTI (Cassa)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagamenti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                id_contratto INTEGER,
                data DATE DEFAULT CURRENT_DATE,
                importo REAL NOT NULL, metodo TEXT, note TEXT
            )""")

            # 4. AGENDA (Operatività)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agenda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_inizio DATETIME NOT NULL,
                data_fine DATETIME NOT NULL,
                categoria TEXT NOT NULL, -- PT, SALA, CORSO, ecc.
                titolo TEXT,
                id_cliente INTEGER,
                id_contratto INTEGER,
                stato TEXT DEFAULT 'Programmato',
                note TEXT
            )""")
            conn.commit()

    @contextmanager
    def transaction(self):
        conn = self._connect(); cursor = conn.cursor(); cursor.execute("BEGIN TRANSACTION")
        try: yield cursor; conn.commit()
        except Exception as e: conn.rollback(); raise e
        finally: conn.close()

    # --- API AGENDA ---
    def add_evento(self, start, end, categoria, titolo, id_cliente=None):
        with self.transaction() as cur:
            id_contr = None
            if categoria == 'PT' and id_cliente:
                # Cerca contratto attivo
                cur.execute("SELECT id FROM contratti WHERE id_cliente=? AND chiuso=0 ORDER BY data_inizio DESC LIMIT 1", (id_cliente,))
                row = cur.fetchone()
                if row: id_contr = row['id']
            
            cur.execute("INSERT INTO agenda (data_inizio, data_fine, categoria, titolo, id_cliente, id_contratto) VALUES (?, ?, ?, ?, ?, ?)", 
                        (start, end, categoria, titolo, id_cliente, id_contr))

    def get_agenda_range(self, start_date: date, end_date: date) -> List[dict]:
        # Recupera eventi per il calendario
        q = """
            SELECT a.*, c.nome, c.cognome 
            FROM agenda a 
            LEFT JOIN clienti c ON a.id_cliente = c.id
            WHERE date(a.data_inizio) BETWEEN ? AND ?
        """
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(q, (start_date, end_date)).fetchall()]
    
    def confirm_evento(self, id_ev):
        with self._connect() as conn: conn.execute("UPDATE agenda SET stato='Fatto' WHERE id=?", (id_ev,)); conn.commit()

    def delete_evento(self, id_ev):
        with self._connect() as conn: conn.execute("DELETE FROM agenda WHERE id=?", (id_ev,)); conn.commit()

    # --- API CLIENTI RAPIDE ---
    def get_clienti_attivi(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT id, nome, cognome FROM clienti WHERE stato='Attivo' ORDER BY cognome").fetchall()]