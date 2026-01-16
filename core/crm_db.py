# file: core/crm_db.py (Versione FitManager 3.0 - Agenda Engine)
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime
from datetime import date
import json
from contextlib import contextmanager
import pandas as pd

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
            
            # --- 1. CLIENTI & LEAD ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS clienti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, cognome TEXT NOT NULL,
                telefono TEXT, email TEXT,
                data_nascita DATE, sesso TEXT,
                anamnesi_json TEXT, -- Dati clinici
                stato TEXT DEFAULT 'Attivo',
                data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

            # --- 2. CONTRATTI (Portafoglio) ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS contratti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                tipo_pacchetto TEXT,
                data_inizio DATE, data_scadenza DATE,
                crediti_totali INTEGER, prezzo_pattuito REAL,
                note TEXT, chiuso BOOLEAN DEFAULT 0
            )""")

            # --- 3. PAGAMENTI (Cassa) ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagamenti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                id_contratto INTEGER,
                data DATE DEFAULT CURRENT_DATE,
                importo REAL NOT NULL, metodo TEXT, note TEXT
            )""")

            # --- 4. AGENDA IBRIDA (Il centro operativo) ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agenda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_inizio DATETIME NOT NULL,
                data_fine DATETIME NOT NULL,
                categoria TEXT NOT NULL, -- PT, SALA, CORSO, CONSULENZA
                titolo TEXT,
                id_cliente INTEGER,
                id_contratto INTEGER,
                stato TEXT DEFAULT 'Programmato', -- Programmato, Fatto, Cancellato
                note TEXT
            )""")
            
            conn.commit()

    @contextmanager
    def transaction(self):
        conn = self._connect(); cursor = conn.cursor(); cursor.execute("BEGIN TRANSACTION")
        try: yield cursor; conn.commit()
        except Exception as e: conn.rollback(); raise e
        finally: conn.close()

    # --- API AGENDA INTERATTIVA ---
    def add_evento(self, start, end, categoria, titolo, id_cliente=None, note=""):
        with self.transaction() as cur:
            # Se è PT, aggancia contratto attivo
            id_contr = None
            if categoria == 'PT' and id_cliente:
                cur.execute("SELECT id FROM contratti WHERE id_cliente=? AND chiuso=0 ORDER BY data_inizio DESC LIMIT 1", (id_cliente,))
                row = cur.fetchone()
                if row: id_contr = row['id']
            
            cur.execute("""
                INSERT INTO agenda (data_inizio, data_fine, categoria, titolo, id_cliente, id_contratto, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (start, end, categoria, titolo, id_cliente, id_contr, note))

    def get_agenda_settimana(self, start_date: date, end_date: date) -> List[dict]:
        q = """
            SELECT a.*, c.nome, c.cognome, c.telefono 
            FROM agenda a 
            LEFT JOIN clienti c ON a.id_cliente = c.id
            WHERE date(a.data_inizio) BETWEEN ? AND ? AND a.stato != 'Cancellato'
            ORDER BY a.data_inizio
        """
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(q, (start_date, end_date)).fetchall()]

    def delete_evento(self, id_evento):
        with self._connect() as conn:
            conn.execute("UPDATE agenda SET stato = 'Cancellato' WHERE id = ?", (id_evento,))
            conn.commit()

    def confirm_evento(self, id_evento):
        with self._connect() as conn:
            conn.execute("UPDATE agenda SET stato = 'Fatto' WHERE id = ?", (id_evento,))
            conn.commit()

    # --- API CLIENTI & CONTRATTI BASE ---
    def get_clienti_attivi(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT id, nome, cognome FROM clienti WHERE stato='Attivo' ORDER BY cognome").fetchall()]

    def get_cliente_balance(self, id_cliente):
        # Calcolo rapido per la sidebar
        with self._connect() as conn:
            crediti = conn.execute("SELECT SUM(crediti_totali) FROM contratti WHERE id_cliente=?", (id_cliente,)).fetchone()[0] or 0
            usati = conn.execute("SELECT COUNT(*) FROM agenda WHERE id_cliente=? AND categoria='PT' AND stato != 'Cancellato'", (id_cliente,)).fetchone()[0] or 0
            
            dovuto = conn.execute("SELECT SUM(prezzo_pattuito) FROM contratti WHERE id_cliente=?", (id_cliente,)).fetchone()[0] or 0
            pagato = conn.execute("SELECT SUM(importo) FROM pagamenti WHERE id_cliente=?", (id_cliente,)).fetchone()[0] or 0
            
            return {"lezioni_residue": crediti - usati, "da_saldare": dovuto - pagato}
    
    # Placeholder per compatibilità con altre pagine se non ancora aggiornate
    def get_dipendenti_df(self, solo_attivi=False): return pd.DataFrame()
    def get_squadre(self): return []
    def get_turni_standard(self): return []