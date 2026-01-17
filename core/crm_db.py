# file: core/crm_db.py (Versione FitManager 3.4 - Golden Master)
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
                tipo_pacchetto TEXT,     -- '10 PT', 'Mensile'
                data_vendita DATE DEFAULT CURRENT_DATE,
                data_inizio DATE, 
                data_scadenza DATE,
                
                crediti_totali INTEGER, 
                crediti_usati INTEGER DEFAULT 0,
                
                prezzo_totale REAL,      -- Prezzo pattuito
                totale_versato REAL DEFAULT 0, -- Somma dei pagamenti ricevuti
                stato_pagamento TEXT DEFAULT 'PENDENTE', -- PENDENTE, PARZIALE, SALDATO
                
                note TEXT, 
                chiuso BOOLEAN DEFAULT 0
            )""")

            # 3. MOVIMENTI CASSA (Nuova Tabella Finanziaria)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimenti_cassa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_movimento DATETIME DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT NOT NULL,      -- 'ENTRATA', 'USCITA'
                categoria TEXT,          -- 'VENDITA', 'RATA', 'SERVIZIO'
                importo REAL NOT NULL,
                metodo TEXT,             -- 'CONTANTI', 'BONIFICO', 'POS'
                
                id_cliente INTEGER,
                id_contratto INTEGER,
                
                note TEXT,
                operatore TEXT DEFAULT 'Admin'
            )""")

            # 4. PAGAMENTI (Legacy/Semplificata - Mantenuta per compatibilità o migrazione)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagamenti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                id_contratto INTEGER,
                data DATE DEFAULT CURRENT_DATE,
                importo REAL NOT NULL, metodo TEXT, note TEXT
            )""")

            # 5. AGENDA
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

    # --- API CLIENTI (CRUD) ---
    def get_clienti_df(self):
        with self._connect() as conn:
            return pd.read_sql("SELECT id, nome, cognome, telefono, email, stato FROM clienti ORDER BY cognome", conn)

    def get_clienti_attivi(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT id, nome, cognome FROM clienti WHERE stato='Attivo' ORDER BY cognome").fetchall()]

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

    def get_cliente_full(self, id_cliente: int) -> Dict[str, Any]:
        """Restituisce anagrafica completa e sintesi contrattuale per la scheda cliente."""
        with self._connect() as conn:
            cli = conn.execute("SELECT * FROM clienti WHERE id=?", (id_cliente,)).fetchone()
            if not cli: return None
            res = dict(cli)
            
            # Calcolo rapido lezioni residue
            res['lezioni_residue'] = 0
            # Prende l'ultimo contratto attivo
            contratto = conn.execute("SELECT * FROM contratti WHERE id_cliente=? AND chiuso=0 ORDER BY data_inizio DESC LIMIT 1", (id_cliente,)).fetchone()
            if contratto:
                res['lezioni_residue'] = contratto['crediti_totali'] - contratto['crediti_usati']
                
            return res

    # --- API AMMINISTRAZIONE & CASSA ---
    def get_cliente_financial_history(self, id_cliente):
        """Recupera storico contratti e movimenti per il TAB Amministrazione."""
        with self._connect() as conn:
            contratti = conn.execute("SELECT * FROM contratti WHERE id_cliente=? ORDER BY data_vendita DESC", (id_cliente,)).fetchall()
            movimenti = conn.execute("SELECT * FROM movimenti_cassa WHERE id_cliente=? ORDER BY data_movimento DESC", (id_cliente,)).fetchall()
            
            dovuto = sum(c['prezzo_totale'] for c in contratti)
            versato = sum(c['totale_versato'] for c in contratti)
            
            return {
                "contratti": [dict(c) for c in contratti],
                "movimenti": [dict(m) for m in movimenti],
                "saldo_globale": dovuto - versato
            }

    def crea_contratto_vendita(self, id_cliente, pacchetto, prezzo, crediti, start, end, acconto=0, metodo_acconto=None):
        with self.transaction() as cur:
            stato_pag = 'PENDENTE'
            if acconto >= prezzo: stato_pag = 'SALDATO'
            elif acconto > 0: stato_pag = 'PARZIALE'
            
            # Crea Contratto
            cur.execute("""
                INSERT INTO contratti (id_cliente, tipo_pacchetto, data_inizio, data_scadenza, crediti_totali, prezzo_totale, totale_versato, stato_pagamento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_cliente, pacchetto, start, end, crediti, prezzo, acconto, stato_pag))
            id_contratto = cur.lastrowid
            
            # Registra Acconto
            if acconto > 0:
                cur.execute("""
                    INSERT INTO movimenti_cassa (tipo, categoria, importo, metodo, id_cliente, id_contratto, note)
                    VALUES ('ENTRATA', 'ACCONTO_CONTRATTO', ?, ?, ?, ?, 'Acconto contestuale')
                """, (acconto, metodo_acconto, id_cliente, id_contratto))

    def registra_rata(self, id_contratto, importo, metodo, data_pagamento=None, note=""):
        if data_pagamento is None: 
            data_pagamento = date.today()
            
        with self.transaction() as cur:
            cur.execute("SELECT id_cliente, prezzo_totale, totale_versato FROM contratti WHERE id=?", (id_contratto,))
            contratto = cur.fetchone()
            
            nuovo_totale = contratto['totale_versato'] + importo
            stato_pag = 'SALDATO' if nuovo_totale >= contratto['prezzo_totale'] else 'PARZIALE'
            
            # Ora inseriamo anche la data personalizzata
            cur.execute("""
                INSERT INTO movimenti_cassa (data_movimento, tipo, categoria, importo, metodo, id_cliente, id_contratto, note)
                VALUES (?, 'ENTRATA', 'RATA_CONTRATTO', ?, ?, ?, ?, ?)
            """, (data_pagamento, importo, metodo, contratto['id_cliente'], id_contratto, note))
            
            cur.execute("UPDATE contratti SET totale_versato = ?, stato_pagamento = ? WHERE id = ?", (nuovo_totale, stato_pag, id_contratto)) (nuovo_totale, stato_pag, id_contratto),

    # --- API AGENDA ---
    def add_evento(self, start, end, categoria, titolo, id_cliente=None, note=""):
        with self.transaction() as cur:
            id_contr = None
            if categoria == 'PT' and id_cliente:
                # Cerca contratto per scalare credito
                cur.execute("""
                    SELECT id FROM contratti 
                    WHERE id_cliente=? AND chiuso=0 AND crediti_usati < crediti_totali
                    ORDER BY data_inizio ASC LIMIT 1
                """, (id_cliente,))
                contratto = cur.fetchone()
                
                if contratto:
                    id_contr = contratto['id']
                    cur.execute("UPDATE contratti SET crediti_usati = crediti_usati + 1 WHERE id=?", (id_contr,))
                else:
                    note += " [⚠️ NO CREDITO]"

            cur.execute("""
                INSERT INTO agenda (data_inizio, data_fine, categoria, titolo, id_cliente, id_contratto, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (start, end, categoria, titolo, id_cliente, id_contr, note))

    def get_agenda_range(self, start_date: date, end_date: date) -> List[dict]:
        q = "SELECT a.*, c.nome, c.cognome FROM agenda a LEFT JOIN clienti c ON a.id_cliente = c.id WHERE date(a.data_inizio) BETWEEN ? AND ?"
        with self._connect() as conn: return [dict(r) for r in conn.execute(q, (start_date, end_date)).fetchall()]
    
    def confirm_evento(self, id_ev):
        with self._connect() as conn: conn.execute("UPDATE agenda SET stato='Fatto' WHERE id=?", (id_ev,)); conn.commit()

    def delete_evento(self, id_ev):
        # Nota: Qui potremmo implementare la restituzione del credito se cancellato prima di X ore.
        # Per ora semplice cancellazione.
        with self._connect() as conn: conn.execute("DELETE FROM agenda WHERE id=?", (id_ev,)); conn.commit()