# file: core/crm_db.py (Versione FitManager 3.2 - Fix All Methods)
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime
from datetime import date
import pandas as pd
import json
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
            
            # 1. CLIENTI
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS clienti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, cognome TEXT NOT NULL,
                telefono TEXT, email TEXT,
                data_nascita DATE, sesso TEXT,
                anamnesi_json TEXT,
                stato TEXT DEFAULT 'Attivo',
                data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

            # 2. CONTRATTI
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS contratti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                tipo_pacchetto TEXT,
                data_inizio DATE, data_scadenza DATE,
                crediti_totali INTEGER, prezzo_pattuito REAL,
                note TEXT, chiuso BOOLEAN DEFAULT 0
            )""")

            # 3. PAGAMENTI
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagamenti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                id_contratto INTEGER,
                data DATE DEFAULT CURRENT_DATE,
                importo REAL NOT NULL, metodo TEXT, note TEXT
            )""")

            # 4. AGENDA
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agenda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_inizio DATETIME NOT NULL, data_fine DATETIME NOT NULL,
                categoria TEXT NOT NULL, titolo TEXT,
                id_cliente INTEGER, id_contratto INTEGER,
                stato TEXT DEFAULT 'Programmato', note TEXT
            )""")
            conn.commit()

    @contextmanager
    def transaction(self):
        conn = self._connect(); cursor = conn.cursor(); cursor.execute("BEGIN TRANSACTION")
        try: yield cursor; conn.commit()
        except Exception as e: conn.rollback(); raise e
        finally: conn.close()

    # --- API AGENDA (Quelle che mancavano) ---
    def add_evento(self, start, end, categoria, titolo, id_cliente=None, note=""):
        with self.transaction() as cur:
            id_contr = None
            if categoria == 'PT' and id_cliente:
                cur.execute("SELECT id FROM contratti WHERE id_cliente=? AND chiuso=0 ORDER BY data_inizio DESC LIMIT 1", (id_cliente,))
                row = cur.fetchone()
                if row: id_contr = row['id']
            cur.execute("INSERT INTO agenda (data_inizio, data_fine, categoria, titolo, id_cliente, id_contratto, note) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                        (start, end, categoria, titolo, id_cliente, id_contr, note))

    def get_agenda_range(self, start_date: date, end_date: date) -> List[dict]:
        """Recupera eventi per il calendario."""
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

    # --- API CLIENTI (Quelle che mancavano) ---
    def get_clienti_df(self):
        """Per la lista clienti."""
        with self._connect() as conn:
            return pd.read_sql("SELECT id, nome, cognome, telefono, email, stato FROM clienti ORDER BY cognome", conn)

    def get_clienti_attivi(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT id, nome, cognome FROM clienti WHERE stato='Attivo' ORDER BY cognome").fetchall()]

    def get_cliente_full(self, id_cliente: int) -> Dict[str, Any]:
        with self._connect() as conn:
            cli = conn.execute("SELECT * FROM clienti WHERE id=?", (id_cliente,)).fetchone()
            if not cli: return None
            res = dict(cli)
            
            contratti = conn.execute("SELECT * FROM contratti WHERE id_cliente=? ORDER BY data_inizio DESC", (id_cliente,)).fetchall()
            res['contratti'] = [dict(c) for c in contratti]
            
            pagamenti = conn.execute("SELECT * FROM pagamenti WHERE id_cliente=? ORDER BY data DESC", (id_cliente,)).fetchall()
            res['pagamenti'] = [dict(p) for p in pagamenti]
            
            dovuto = sum(c['prezzo_pattuito'] for c in res['contratti'])
            pagato = sum(p['importo'] for p in res['pagamenti'])
            res['saldo'] = dovuto - pagato
            
            res['lezioni_residue'] = 0
            active_c = next((c for c in res['contratti'] if not c['chiuso']), None)
            if active_c:
                usate = conn.execute("SELECT COUNT(*) FROM agenda WHERE id_contratto=? AND stato!='Cancellato'", (active_c['id'],)).fetchone()[0]
                res['lezioni_residue'] = active_c['crediti_totali'] - usate

            return res

    def save_cliente(self, dati: Dict[str, Any], id_cliente: Optional[int] = None):
        anamnesi = json.dumps(dati.get('anamnesi', {}))
        with self.transaction() as cur:
            if id_cliente:
                cur.execute("""
                    UPDATE clienti SET nome=?, cognome=?, telefono=?, email=?, data_nascita=?, sesso=?, anamnesi_json=?, stato=?
                    WHERE id=?
                """, (dati['nome'], dati['cognome'], dati['telefono'], dati['email'], dati['nascita'], dati['sesso'], anamnesi, dati['stato'], id_cliente))
            else:
                cur.execute("""
                    INSERT INTO clienti (nome, cognome, telefono, email, data_nascita, sesso, anamnesi_json, stato)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (dati['nome'], dati['cognome'], dati['telefono'], dati['email'], dati['nascita'], dati['sesso'], anamnesi, dati['stato']))

    # --- API AMMINISTRAZIONE ---
    def add_contratto(self, id_cliente, pacchetto, prezzo, ingressi, start, end, note):
        with self.transaction() as cur:
            cur.execute("UPDATE contratti SET chiuso=1 WHERE id_cliente=? AND chiuso=0", (id_cliente,))
            cur.execute("""
                INSERT INTO contratti (id_cliente, tipo_pacchetto, prezzo_pattuito, crediti_totali, data_inizio, data_scadenza, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (id_cliente, pacchetto, prezzo, ingressi, start, end, note))

    def add_pagamento(self, id_cliente, importo, metodo, note):
        with self.transaction() as cur:
            cur.execute("INSERT INTO pagamenti (id_cliente, importo, metodo, note) VALUES (?, ?, ?, ?)",
                        (id_cliente, importo, metodo, note))