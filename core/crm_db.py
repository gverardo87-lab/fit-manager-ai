# file: core/crm_db.py (Versione 7.0 - Financial Editing Core)
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
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
                data_vendita DATE DEFAULT CURRENT_DATE,
                data_inizio DATE, data_scadenza DATE,
                crediti_totali INTEGER, crediti_usati INTEGER DEFAULT 0,
                prezzo_totale REAL, totale_versato REAL DEFAULT 0,
                stato_pagamento TEXT DEFAULT 'PENDENTE',
                note TEXT, chiuso BOOLEAN DEFAULT 0
            )""")

            # 3. MOVIMENTI CASSA (Reale)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimenti_cassa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_movimento DATETIME DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT NOT NULL,
                categoria TEXT,          
                importo REAL NOT NULL,
                metodo TEXT,
                id_cliente INTEGER,
                id_contratto INTEGER,
                id_rata INTEGER,
                note TEXT,
                operatore TEXT DEFAULT 'Admin'
            )""")

            # 4. RATE PROGRAMMATE (Previsionale Entrate)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_programmate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_contratto INTEGER NOT NULL,
                data_scadenza DATE NOT NULL,
                importo_previsto REAL NOT NULL,
                descrizione TEXT,
                stato TEXT DEFAULT 'PENDENTE',
                importo_saldato REAL DEFAULT 0
            )""")

            # 5. SPESE RICORRENTI
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS spese_ricorrenti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                categoria TEXT,
                importo REAL NOT NULL,
                frequenza TEXT,
                giorno_scadenza INTEGER,
                attiva BOOLEAN DEFAULT 1
            )""")

            # 6. AGENDA
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agenda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_inizio DATETIME NOT NULL, data_fine DATETIME NOT NULL,
                categoria TEXT NOT NULL, titolo TEXT,
                id_cliente INTEGER, id_contratto INTEGER,
                stato TEXT DEFAULT 'Programmato', note TEXT
            )""")

            # 7. MISURAZIONI
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS misurazioni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                data_misurazione DATE DEFAULT CURRENT_DATE,
                peso REAL, massa_grassa REAL, massa_magra REAL, acqua REAL,
                collo REAL, spalle REAL, torace REAL, braccio REAL,
                vita REAL, fianchi REAL, coscia REAL, polpaccio REAL,
                note TEXT
            )""")
            
            conn.commit()

    @contextmanager
    def transaction(self):
        conn = self._connect(); cursor = conn.cursor(); cursor.execute("BEGIN TRANSACTION")
        try: yield cursor; conn.commit()
        except Exception as e: conn.rollback(); raise e
        finally: conn.close()

    # --- API FINANZIARIE CORE ---

    def genera_piano_rate(self, id_contratto, importo_totale, n_rate, data_inizio, periodicita="MENSILE"):
        if n_rate < 1: return
        importo_rata = importo_totale / n_rate
        if isinstance(data_inizio, str):
            data_inizio = datetime.datetime.strptime(data_inizio, "%Y-%m-%d").date()

        with self.transaction() as cur:
            for i in range(n_rate):
                if periodicita == "MENSILE":
                    scadenza = data_inizio + relativedelta(months=i)
                elif periodicita == "SETTIMANALE":
                    scadenza = data_inizio + relativedelta(weeks=i)
                else:
                    scadenza = data_inizio
                
                desc = f"Rata {i+1}/{n_rate}"
                cur.execute("""
                    INSERT INTO rate_programmate (id_contratto, data_scadenza, importo_previsto, descrizione)
                    VALUES (?, ?, ?, ?)
                """, (id_contratto, scadenza, importo_rata, desc))

    def get_rate_contratto(self, id_contratto):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM rate_programmate WHERE id_contratto=? ORDER BY data_scadenza", (id_contratto,)).fetchall()]

    # --- NUOVE FUNZIONI PER ELASTICITÀ TOTALE ---
    
    def update_contratto_dettagli(self, id_contratto, nuovo_prezzo, nuovi_crediti, nuova_scadenza):
        """Modifica i parametri vitali di un contratto esistente."""
        with self.transaction() as cur:
            cur.execute("""
                UPDATE contratti 
                SET prezzo_totale=?, crediti_totali=?, data_scadenza=?
                WHERE id=?
            """, (nuovo_prezzo, nuovi_crediti, nuova_scadenza, id_contratto))

    def update_rata_programmata(self, id_rata, data_scadenza, importo, descrizione):
        """Modifica una singola rata del piano."""
        with self.transaction() as cur:
            cur.execute("""
                UPDATE rate_programmate
                SET data_scadenza=?, importo_previsto=?, descrizione=?
                WHERE id=?
            """, (data_scadenza, importo, descrizione, id_rata))

    def aggiungi_rata_manuale(self, id_contratto, data_scadenza, importo, descrizione):
        """Aggiunge una rata extra al piano."""
        with self.transaction() as cur:
            cur.execute("""
                INSERT INTO rate_programmate (id_contratto, data_scadenza, importo_previsto, descrizione)
                VALUES (?, ?, ?, ?)
            """, (id_contratto, data_scadenza, importo, descrizione))

    def elimina_rata(self, id_rata):
        """Elimina una rata pianificata (se non saldata)."""
        with self.transaction() as cur:
            cur.execute("DELETE FROM rate_programmate WHERE id=?", (id_rata,))

    # ----------------------------------------------

    def paga_rata_specifica(self, id_rata, importo_versato, metodo, data_pagamento, note=""):
        with self.transaction() as cur:
            cur.execute("SELECT * FROM rate_programmate WHERE id=?", (id_rata,))
            rata = cur.fetchone()
            if not rata: return
            
            cur.execute("SELECT id_cliente FROM contratti WHERE id=?", (rata['id_contratto'],))
            contratto = cur.fetchone()
            
            cur.execute("""
                INSERT INTO movimenti_cassa (data_movimento, tipo, categoria, importo, metodo, id_cliente, id_contratto, id_rata, note)
                VALUES (?, 'ENTRATA', 'RATA_PIANIFICATA', ?, ?, ?, ?, ?, ?)
            """, (data_pagamento, importo_versato, metodo, contratto['id_cliente'], rata['id_contratto'], id_rata, note))
            
            nuovo_saldato = rata['importo_saldato'] + importo_versato
            stato = 'PENDENTE'
            if nuovo_saldato >= rata['importo_previsto'] - 0.1:
                stato = 'SALDATA'
            elif nuovo_saldato > 0:
                stato = 'PARZIALE'
            
            cur.execute("UPDATE rate_programmate SET importo_saldato=?, stato=? WHERE id=?", (nuovo_saldato, stato, id_rata))
            cur.execute("UPDATE contratti SET totale_versato = totale_versato + ? WHERE id=?", (importo_versato, rata['id_contratto']))

    def add_spesa_ricorrente(self, nome, categoria, importo, frequenza, giorno):
        with self.transaction() as cur:
            cur.execute("INSERT INTO spese_ricorrenti (nome, categoria, importo, frequenza, giorno_scadenza) VALUES (?,?,?,?,?)", 
                       (nome, categoria, importo, frequenza, giorno))

    def get_spese_ricorrenti(self):
        with self._connect() as conn: return [dict(r) for r in conn.execute("SELECT * FROM spese_ricorrenti WHERE attiva=1").fetchall()]

    # --- API STANDARD ---
    def get_clienti_df(self):
        with self._connect() as conn: return pd.read_sql("SELECT id, nome, cognome, telefono, email, stato FROM clienti ORDER BY cognome", conn)

    def get_clienti_attivi(self):
        with self._connect() as conn: return [dict(r) for r in conn.execute("SELECT id, nome, cognome FROM clienti WHERE stato='Attivo' ORDER BY cognome").fetchall()]

    def save_cliente(self, dati: Dict[str, Any], id_cliente: Optional[int] = None):
        anamnesi = json.dumps(dati.get('anamnesi', {}))
        p = (dati.get('nome'), dati.get('cognome'), dati.get('telefono',''), dati.get('email',''), 
             dati.get('data_nascita'), dati.get('sesso','Uomo'), anamnesi, dati.get('stato','Attivo'))
        with self.transaction() as cur:
            if id_cliente:
                cur.execute("UPDATE clienti SET nome=?, cognome=?, telefono=?, email=?, data_nascita=?, sesso=?, anamnesi_json=?, stato=? WHERE id=?", (*p, id_cliente))
            else:
                cur.execute("INSERT INTO clienti (nome, cognome, telefono, email, data_nascita, sesso, anamnesi_json, stato) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", p)

    def get_cliente_full(self, id_cliente: int) -> Dict[str, Any]:
        with self._connect() as conn:
            cli = conn.execute("SELECT * FROM clienti WHERE id=?", (id_cliente,)).fetchone()
            if not cli: return None
            res = dict(cli)
            contratto = conn.execute("SELECT * FROM contratti WHERE id_cliente=? AND chiuso=0 ORDER BY data_inizio DESC LIMIT 1", (id_cliente,)).fetchone()
            res['lezioni_residue'] = (contratto['crediti_totali'] - contratto['crediti_usati']) if contratto else 0
            return res

    def get_cliente_financial_history(self, id_cliente):
        with self._connect() as conn:
            contratti = conn.execute("SELECT * FROM contratti WHERE id_cliente=? ORDER BY data_vendita DESC", (id_cliente,)).fetchall()
            movimenti = conn.execute("SELECT * FROM movimenti_cassa WHERE id_cliente=? ORDER BY data_movimento DESC", (id_cliente,)).fetchall()
            dovuto = sum(c['prezzo_totale'] for c in contratti)
            versato = sum(c['totale_versato'] for c in contratti)
            return {"contratti": [dict(c) for c in contratti], "movimenti": [dict(m) for m in movimenti], "saldo_globale": dovuto - versato}

    def get_bilancio_completo(self):
        with self._connect() as conn:
            return pd.read_sql("SELECT * FROM movimenti_cassa ORDER BY data_movimento DESC", conn)

    def crea_contratto_vendita(self, id_cliente, pacchetto, prezzo, crediti, start, end, acconto=0, metodo_acconto=None):
        with self.transaction() as cur:
            stato_pag = 'SALDATO' if acconto >= prezzo else 'PARZIALE' if acconto > 0 else 'PENDENTE'
            cur.execute("INSERT INTO contratti (id_cliente, tipo_pacchetto, data_inizio, data_scadenza, crediti_totali, prezzo_totale, totale_versato, stato_pagamento) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                       (id_cliente, pacchetto, start, end, crediti, prezzo, acconto, stato_pag))
            id_contr = cur.lastrowid
            if acconto > 0:
                cur.execute("INSERT INTO movimenti_cassa (tipo, categoria, importo, metodo, id_cliente, id_contratto, note) VALUES ('ENTRATA', 'ACCONTO_CONTRATTO', ?, ?, ?, ?, 'Acconto contestuale')", 
                           (acconto, metodo_acconto, id_cliente, id_contr))
            return id_contr

    def registra_rata(self, id_contratto, importo, metodo, data_pagamento=None, note=""):
        if data_pagamento is None: data_pagamento = date.today()
        with self.transaction() as cur:
            cur.execute("SELECT id_cliente, prezzo_totale, totale_versato FROM contratti WHERE id=?", (id_contratto,))
            c = cur.fetchone()
            if not c: return
            nuovo_tot = c['totale_versato'] + importo
            stato = 'SALDATO' if nuovo_tot >= c['prezzo_totale'] else 'PARZIALE'
            cur.execute("INSERT INTO movimenti_cassa (data_movimento, tipo, categoria, importo, metodo, id_cliente, id_contratto, note) VALUES (?, 'ENTRATA', 'RATA_EXTRA', ?, ?, ?, ?, ?)", 
                       (data_pagamento, importo, metodo, c['id_cliente'], id_contratto, note))
            cur.execute("UPDATE contratti SET totale_versato=?, stato_pagamento=? WHERE id=?", (nuovo_tot, stato, id_contratto))

    def registra_spesa(self, categoria, importo, metodo, data_pagamento=None, note=""):
        if data_pagamento is None: data_pagamento = date.today()
        with self.transaction() as cur:
            cur.execute("INSERT INTO movimenti_cassa (data_movimento, tipo, categoria, importo, metodo, note) VALUES (?, 'USCITA', ?, ?, ?, ?)", 
                       (data_pagamento, categoria, importo, metodo, note))

    def add_evento(self, start, end, categoria, titolo, id_cliente=None, note=""):
        with self.transaction() as cur:
            id_contr = None
            if categoria == 'PT' and id_cliente:
                cur.execute("SELECT id FROM contratti WHERE id_cliente=? AND chiuso=0 AND crediti_usati < crediti_totali ORDER BY data_inizio ASC LIMIT 1", (id_cliente,))
                res = cur.fetchone()
                if res: 
                    id_contr = res['id']
                    cur.execute("UPDATE contratti SET crediti_usati = crediti_usati + 1 WHERE id=?", (id_contr,))
                else: note += " [⚠️ NO CREDITO]"
            cur.execute("INSERT INTO agenda (data_inizio, data_fine, categoria, titolo, id_cliente, id_contratto, note) VALUES (?, ?, ?, ?, ?, ?, ?)", (start, end, categoria, titolo, id_cliente, id_contr, note))

    def update_evento(self, id_ev, start, end, titolo, note=""):
        with self.transaction() as cur: cur.execute("UPDATE agenda SET data_inizio=?, data_fine=?, titolo=?, note=? WHERE id=?", (start, end, titolo, note, id_ev))

    def get_agenda_range(self, start, end):
        with self._connect() as conn: return [dict(r) for r in conn.execute("SELECT a.*, c.nome, c.cognome FROM agenda a LEFT JOIN clienti c ON a.id_cliente=c.id WHERE date(a.data_inizio) BETWEEN ? AND ?", (start, end)).fetchall()]

    def confirm_evento(self, id_ev):
        with self._connect() as conn: conn.execute("UPDATE agenda SET stato='Fatto' WHERE id=?", (id_ev,)); conn.commit()

    def delete_evento(self, id_ev):
        with self.transaction() as cur:
            cur.execute("SELECT id_contratto FROM agenda WHERE id=?", (id_ev,))
            row = cur.fetchone()
            if row and row['id_contratto']: cur.execute("UPDATE contratti SET crediti_usati = crediti_usati - 1 WHERE id=?", (row['id_contratto'],))
            cur.execute("DELETE FROM agenda WHERE id=?", (id_ev,))

    def get_storico_lezioni_cliente(self, id_cliente):
        q = "SELECT a.*, c.tipo_pacchetto FROM agenda a LEFT JOIN contratti c ON a.id_contratto=c.id WHERE a.id_cliente=? ORDER BY a.data_inizio DESC"
        with self._connect() as conn: return [dict(r) for r in conn.execute(q, (id_cliente,)).fetchall()]

    def add_misurazione_completa(self, id_cliente, dati: Dict[str, Any]):
        with self.transaction() as cur:
            cur.execute("""INSERT INTO misurazioni (id_cliente, data_misurazione, peso, massa_grassa, massa_magra, acqua, collo, spalle, torace, braccio, vita, fianchi, coscia, polpaccio, note) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                           (id_cliente, dati.get('data'), dati.get('peso'), dati.get('grasso'), dati.get('muscolo'), dati.get('acqua'),
                            dati.get('collo'), dati.get('spalle'), dati.get('torace'), dati.get('braccio'), dati.get('vita'), dati.get('fianchi'), dati.get('coscia'), dati.get('polpaccio'),
                            dati.get('note')))

    def update_misurazione(self, id_misura, dati: Dict[str, Any]):
        with self.transaction() as cur:
            cur.execute("""UPDATE misurazioni SET data_misurazione=?, peso=?, massa_grassa=?, massa_magra=?, acqua=?, collo=?, spalle=?, torace=?, braccio=?, vita=?, fianchi=?, coscia=?, polpaccio=?, note=? WHERE id=?""", 
                        (dati.get('data'), dati.get('peso'), dati.get('grasso'), dati.get('muscolo'), dati.get('acqua'), dati.get('collo'), dati.get('spalle'), dati.get('torace'), dati.get('braccio'), dati.get('vita'), dati.get('fianchi'), dati.get('coscia'), dati.get('polpaccio'), dati.get('note'), id_misura))

    def get_progressi_cliente(self, id_cliente):
        with self._connect() as conn: return pd.read_sql("SELECT * FROM misurazioni WHERE id_cliente=? ORDER BY data_misurazione DESC", conn, params=(id_cliente,))