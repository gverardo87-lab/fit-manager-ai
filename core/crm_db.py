# file: core/crm_db.py (Versione 8.0 - Stable Core)
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import json
from contextlib import contextmanager

# Percorso DB
DB_FILE = Path(__file__).resolve().parents[1] / "data" / "crm.db"

# === CATEGORIE STANDARD ===
CATEGORIA_ACCONTO = "ACCONTO_CONTRATTO"
CATEGORIA_RATA = "RATA_CONTRATTO"
CATEGORIA_SPESA_AFFITTO = "SPESE_AFFITTO"
CATEGORIA_SPESA_UTILITIES = "SPESE_UTILITIES"
CATEGORIA_SPESA_ATTREZZATURE = "SPESE_ATTREZZATURE"
CATEGORIA_RIMBORSO = "RIMBORSI"
CATEGORIA_ALTRO = "ALTRO"

class CrmDBManager:
    def __init__(self, db_path: str | Path = DB_FILE):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _run_migrations(self, conn):
        """Esegui migrazioni per aggiungere colonne nuove a DB esistenti"""
        cursor = conn.cursor()
        
        # Migrazione 1: Aggiungi data_effettiva a movimenti_cassa se non esiste
        try:
            cursor.execute("ALTER TABLE movimenti_cassa ADD COLUMN data_effettiva DATE DEFAULT CURRENT_DATE")
            conn.commit()
        except sqlite3.OperationalError:
            # Colonna già esiste, ignora
            pass
        
        # Migrazione 2: Aggiungi colonne a spese_ricorrenti se non esistono
        try:
            cursor.execute("ALTER TABLE spese_ricorrenti ADD COLUMN giorno_inizio INTEGER DEFAULT 1")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE spese_ricorrenti ADD COLUMN data_prossima_scadenza DATE")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    def _init_schema(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS clienti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, cognome TEXT NOT NULL,
                telefono TEXT, email TEXT, data_nascita DATE, sesso TEXT,
                anamnesi_json TEXT, stato TEXT DEFAULT 'Attivo',
                data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS contratti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                tipo_pacchetto TEXT, data_vendita DATE DEFAULT CURRENT_DATE,
                data_inizio DATE, data_scadenza DATE,
                crediti_totali INTEGER, crediti_usati INTEGER DEFAULT 0,
                prezzo_totale REAL, totale_versato REAL DEFAULT 0,
                stato_pagamento TEXT DEFAULT 'PENDENTE',
                note TEXT, chiuso BOOLEAN DEFAULT 0
            )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS movimenti_cassa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_movimento DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_effettiva DATE NOT NULL DEFAULT CURRENT_DATE,
                tipo TEXT NOT NULL, categoria TEXT, importo REAL NOT NULL,
                metodo TEXT, id_cliente INTEGER, id_contratto INTEGER,
                id_rata INTEGER, note TEXT, operatore TEXT DEFAULT 'Admin'
            )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS rate_programmate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_contratto INTEGER NOT NULL,
                data_scadenza DATE NOT NULL,
                importo_previsto REAL NOT NULL,
                descrizione TEXT,
                stato TEXT DEFAULT 'PENDENTE',
                importo_saldato REAL DEFAULT 0
            )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS spese_ricorrenti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, categoria TEXT, importo REAL NOT NULL,
                frequenza TEXT, 
                giorno_inizio INTEGER DEFAULT 1,
                giorno_scadenza INTEGER DEFAULT 1,
                data_prossima_scadenza DATE,
                attiva BOOLEAN DEFAULT 1,
                data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS agenda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_inizio DATETIME NOT NULL, data_fine DATETIME NOT NULL,
                categoria TEXT NOT NULL, titolo TEXT,
                id_cliente INTEGER, id_contratto INTEGER,
                stato TEXT DEFAULT 'Programmato', note TEXT
            )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS misurazioni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL, data_misurazione DATE DEFAULT CURRENT_DATE,
                peso REAL, massa_grassa REAL, massa_magra REAL, acqua REAL,
                collo REAL, spalle REAL, torace REAL, braccio REAL,
                vita REAL, fianchi REAL, coscia REAL, polpaccio REAL, note TEXT
            )""")
            conn.commit()
        
        # === MIGRAZIONI (esegui DOPO che la connessione è stata chiusa e committata) ===
        # Migrazione 1: Aggiungi data_effettiva a movimenti_cassa se non esiste
        conn2 = self._connect()
        try:
            conn2.execute("ALTER TABLE movimenti_cassa ADD COLUMN data_effettiva DATE DEFAULT CURRENT_DATE")
            conn2.commit()
        except sqlite3.OperationalError:
            pass
        finally:
            conn2.close()
        
        # Migrazione 2: Aggiungi colonne a spese_ricorrenti se non esistono
        conn3 = self._connect()
        try:
            conn3.execute("ALTER TABLE spese_ricorrenti ADD COLUMN giorno_inizio INTEGER DEFAULT 1")
            conn3.commit()
        except sqlite3.OperationalError:
            pass
        finally:
            conn3.close()
        
        conn4 = self._connect()
        try:
            conn4.execute("ALTER TABLE spese_ricorrenti ADD COLUMN data_prossima_scadenza DATE")
            conn4.commit()
        except sqlite3.OperationalError:
            pass
        finally:
            conn4.close()

    @contextmanager
    def transaction(self):
        conn = self._connect(); cursor = conn.cursor(); cursor.execute("BEGIN TRANSACTION")
        try: yield cursor; conn.commit()
        except Exception as e: conn.rollback(); raise e
        finally: conn.close()

    # --- LOGICA RATE INTELLIGENTE ---
    def rimodula_piano_rate(self, id_contratto, id_rata_modificata, nuovo_importo_rata, nuova_data=None):
        with self.transaction() as cur:
            cur.execute("SELECT prezzo_totale FROM contratti WHERE id=?", (id_contratto,))
            res = cur.fetchone()
            if not res: return
            totale_contratto = res['prezzo_totale']

            # Acconto
            cur.execute("SELECT SUM(importo) as acconto FROM movimenti_cassa WHERE id_contratto=? AND categoria=?", (id_contratto, CATEGORIA_ACCONTO))
            res_acc = cur.fetchone()
            acconto = res_acc['acconto'] if res_acc and res_acc['acconto'] else 0.0

            # Aggiorna rata target
            if nuova_data:
                cur.execute("UPDATE rate_programmate SET importo_previsto=?, data_scadenza=? WHERE id=?", (nuovo_importo_rata, nuova_data, id_rata_modificata))
            else:
                cur.execute("UPDATE rate_programmate SET importo_previsto=? WHERE id=?", (nuovo_importo_rata, id_rata_modificata))

            # Ricalcola le altre
            cur.execute("SELECT * FROM rate_programmate WHERE id_contratto=? ORDER BY data_scadenza ASC, id ASC", (id_contratto,))
            tutte = [dict(r) for r in cur.fetchall()]

            bloccato = acconto
            da_spalmare = []
            
            for r in tutte:
                if r['id'] == id_rata_modificata: bloccato += nuovo_importo_rata
                elif r['stato'] == 'SALDATA': bloccato += r['importo_previsto']
                else: da_spalmare.append(r)

            residuo = totale_contratto - bloccato
            if residuo < 0: residuo = 0 

            if da_spalmare:
                val_singolo = residuo / len(da_spalmare)
                for r in da_spalmare:
                    cur.execute("UPDATE rate_programmate SET importo_previsto=? WHERE id=?", (val_singolo, r['id']))

    # --- API CONTRATTI ---
    def crea_contratto_vendita(self, id_cliente, pacchetto, prezzo, crediti, start, end, acconto=0, metodo_acconto=None, data_acconto=None):
        if data_acconto is None: 
            data_acconto = date.today()
        with self.transaction() as cur:
            cur.execute("INSERT INTO contratti (id_cliente, tipo_pacchetto, data_inizio, data_scadenza, crediti_totali, prezzo_totale, totale_versato, stato_pagamento) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                       (id_cliente, pacchetto, start, end, crediti, prezzo, acconto, 'PENDENTE'))
            id_contr = cur.lastrowid
            if acconto > 0:
                cur.execute("INSERT INTO movimenti_cassa (data_effettiva, tipo, categoria, importo, metodo, id_cliente, id_contratto, note) VALUES (?, 'ENTRATA', ?, ?, ?, ?, ?, 'Acconto contestuale')", 
                           (data_acconto, CATEGORIA_ACCONTO, acconto, metodo_acconto, id_cliente, id_contr))
            return id_contr

    def delete_contratto(self, id_contratto):
        with self.transaction() as cur:
            cur.execute("DELETE FROM movimenti_cassa WHERE id_contratto=?", (id_contratto,))
            cur.execute("DELETE FROM rate_programmate WHERE id_contratto=?", (id_contratto,))
            cur.execute("DELETE FROM contratti WHERE id=?", (id_contratto,))

    def update_contratto_dettagli(self, id_contratto, nuovo_prezzo, nuovi_crediti, nuova_scadenza):
        with self.transaction() as cur: cur.execute("UPDATE contratti SET prezzo_totale=?, crediti_totali=?, data_scadenza=? WHERE id=?", (nuovo_prezzo, nuovi_crediti, nuova_scadenza, id_contratto))

    # --- API RATE ---
    def genera_piano_rate(self, id_contratto, importo_da_rateizzare, n_rate, data_inizio, periodicita="MENSILE"):
        if n_rate < 1: return
        importo_rata = importo_da_rateizzare / n_rate
        if isinstance(data_inizio, str): data_inizio = datetime.datetime.strptime(data_inizio, "%Y-%m-%d").date()

        with self.transaction() as cur:
            cur.execute("DELETE FROM rate_programmate WHERE id_contratto=? AND stato='PENDENTE'", (id_contratto,))
            for i in range(n_rate):
                scadenza = data_inizio
                if periodicita == "MENSILE": scadenza += relativedelta(months=i)
                elif periodicita == "SETTIMANALE": scadenza += relativedelta(weeks=i)
                desc = f"Rata {i+1}/{n_rate}"
                cur.execute("INSERT INTO rate_programmate (id_contratto, data_scadenza, importo_previsto, descrizione) VALUES (?, ?, ?, ?)", (id_contratto, scadenza, importo_rata, desc))

    def get_rate_contratto(self, id_contratto):
        with self._connect() as conn: return [dict(r) for r in conn.execute("SELECT * FROM rate_programmate WHERE id_contratto=? ORDER BY data_scadenza", (id_contratto,)).fetchall()]

    def update_rata_programmata(self, id_rata, data_scadenza, importo, descrizione):
        with self.transaction() as cur: cur.execute("UPDATE rate_programmate SET data_scadenza=?, importo_previsto=?, descrizione=? WHERE id=?", (data_scadenza, importo, descrizione, id_rata))

    def aggiungi_rata_manuale(self, id_contratto, data_scadenza, importo, descrizione):
        with self.transaction() as cur: cur.execute("INSERT INTO rate_programmate (id_contratto, data_scadenza, importo_previsto, descrizione) VALUES (?, ?, ?, ?)", (id_contratto, data_scadenza, importo, descrizione))

    def elimina_rata(self, id_rata):
        with self.transaction() as cur: cur.execute("DELETE FROM rate_programmate WHERE id=?", (id_rata,))

    def paga_rata_specifica(self, id_rata, importo_versato, metodo, data_pagamento, note=""):
        with self.transaction() as cur:
            cur.execute("SELECT * FROM rate_programmate WHERE id=?", (id_rata,))
            rata = cur.fetchone()
            if not rata: return
            cur.execute("SELECT id_cliente FROM contratti WHERE id=?", (rata['id_contratto'],))
            contratto = cur.fetchone()
            cur.execute("INSERT INTO movimenti_cassa (data_effettiva, tipo, categoria, importo, metodo, id_cliente, id_contratto, id_rata, note) VALUES (?, 'ENTRATA', ?, ?, ?, ?, ?, ?, ?)", (data_pagamento, CATEGORIA_RATA, importo_versato, metodo, contratto['id_cliente'], rata['id_contratto'], id_rata, note))
            nuovo_saldato = rata['importo_saldato'] + importo_versato
            stato = 'SALDATA' if nuovo_saldato >= rata['importo_previsto'] - 0.1 else 'PARZIALE'
            cur.execute("UPDATE rate_programmate SET importo_saldato=?, stato=? WHERE id=?", (nuovo_saldato, stato, id_rata))
            cur.execute("UPDATE contratti SET totale_versato = totale_versato + ? WHERE id=?", (importo_versato, rata['id_contratto']))

    # --- FINANZE - NUOVA LOGICA PULITA (FONTE DI VERITÀ UNICA) ---
    def get_bilancio_effettivo(self, data_inizio=None, data_fine=None):
        """
        Calcola il bilancio EFFETTIVO basato su movimenti_cassa confermati (data_effettiva).
        Fonte di verità unica: solo soldi che sono effettivamente entrati/usciti.
        """
        with self._connect() as conn:
            query = "SELECT * FROM movimenti_cassa WHERE 1=1"
            params = []
            
            if data_inizio:
                query += " AND data_effettiva >= ?"
                params.append(data_inizio)
            if data_fine:
                query += " AND data_effettiva <= ?"
                params.append(data_fine)
            
            query += " ORDER BY data_effettiva"
            movimenti = [dict(r) for r in conn.execute(query, params).fetchall()]
            
            entrate = sum(m['importo'] for m in movimenti if m['tipo'] == 'ENTRATA')
            uscite = sum(m['importo'] for m in movimenti if m['tipo'] == 'USCITA')
            
            return {
                "entrate": entrate,
                "uscite": uscite,
                "saldo": entrate - uscite,
                "movimenti": movimenti
            }

    def get_rate_pendenti(self, data_entro=None):
        """
        Ritorna rate NON ancora pagate (stato != 'SALDATA'), opzionalmente entro una certa data.
        """
        with self._connect() as conn:
            query = """
                SELECT rp.*, c.id_cliente, c.tipo_pacchetto, cl.nome, cl.cognome
                FROM rate_programmate rp
                JOIN contratti c ON rp.id_contratto = c.id
                JOIN clienti cl ON c.id_cliente = cl.id
                WHERE rp.stato != 'SALDATA'
            """
            params = []
            
            if data_entro:
                query += " AND rp.data_scadenza <= ?"
                params.append(data_entro)
            
            query += " ORDER BY rp.data_scadenza ASC"
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def get_spese_ricorrenti_prossime(self, giorni_futuri=30):
        """
        Ritorna spese ricorrenti che scadono nei prossimi N giorni (basate su data_prossima_scadenza).
        """
        with self._connect() as conn:
            data_limite = date.today() + timedelta(days=giorni_futuri)
            spese = [dict(r) for r in conn.execute("""
                SELECT * FROM spese_ricorrenti 
                WHERE attiva=1 AND data_prossima_scadenza IS NOT NULL AND data_prossima_scadenza <= ?
                ORDER BY data_prossima_scadenza ASC
            """, (data_limite,)).fetchall()]
            
            return spese

    def get_cashflow_previsione(self, giorni_futuri=30):
        """
        Calcola cashflow previsto considerando rate pendenti e spese ricorrenti.
        Questo è PER LA PREVISIONE, non il valore effettivo.
        """
        entrate_programmate = sum(r['importo_previsto'] for r in self.get_rate_pendenti(date.today() + timedelta(days=giorni_futuri)))
        uscite_programmate = sum(s['importo'] for s in self.get_spese_ricorrenti_prossime(giorni_futuri))
        
        saldo_effettivo = self.get_bilancio_effettivo()['saldo']
        saldo_previsto = saldo_effettivo + entrate_programmate - uscite_programmate
        
        return {
            "saldo_effettivo": saldo_effettivo,
            "entrate_programmate": entrate_programmate,
            "uscite_programmate": uscite_programmate,
            "saldo_previsto": saldo_previsto
        }

    # --- SPESE ---
    def registra_spesa(self, categoria, importo, metodo, data_pagamento=None, note=""):
        if data_pagamento is None: 
            data_pagamento = date.today()
        with self.transaction() as cur: 
            cur.execute("INSERT INTO movimenti_cassa (data_effettiva, tipo, categoria, importo, metodo, note) VALUES (?, 'USCITA', ?, ?, ?, ?)", (data_pagamento, categoria, importo, metodo, note))
    def add_spesa_ricorrente(self, nome, categoria, importo, frequenza, giorno_scadenza, data_prossima=None):
        if data_prossima is None:
            data_prossima = date(date.today().year, date.today().month, min(giorno_scadenza, 28))
            if data_prossima < date.today():
                # Se la data è nel passato, passa al prossimo mese
                data_prossima += relativedelta(months=1)
        
        with self.transaction() as cur: 
            cur.execute("""
                INSERT INTO spese_ricorrenti 
                (nome, categoria, importo, frequenza, giorno_scadenza, data_prossima_scadenza) 
                VALUES (?,?,?,?,?,?)
            """, (nome, categoria, importo, frequenza, giorno_scadenza, data_prossima))
    def get_spese_ricorrenti(self):
        with self._connect() as conn: return [dict(r) for r in conn.execute("SELECT * FROM spese_ricorrenti WHERE attiva=1").fetchall()]

    # --- GETTERS ---
    def get_clienti_df(self):
        with self._connect() as conn: return pd.read_sql("SELECT id, nome, cognome, telefono, email, stato FROM clienti ORDER BY cognome", conn)
    def get_clienti_attivi(self):
        with self._connect() as conn: return [dict(r) for r in conn.execute("SELECT id, nome, cognome FROM clienti WHERE stato='Attivo' ORDER BY cognome").fetchall()]
    def get_cliente_full(self, id_cliente):
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
        with self._connect() as conn: return pd.read_sql("SELECT * FROM movimenti_cassa ORDER BY data_movimento DESC", conn)

    # --- SAVE ---
    def save_cliente(self, dati, id_cliente=None):
        anamnesi = json.dumps(dati.get('anamnesi', {}))
        p = (dati.get('nome'), dati.get('cognome'), dati.get('telefono',''), dati.get('email',''), dati.get('data_nascita'), dati.get('sesso','Uomo'), anamnesi, dati.get('stato','Attivo'))
        with self.transaction() as cur:
            if id_cliente: cur.execute("UPDATE clienti SET nome=?, cognome=?, telefono=?, email=?, data_nascita=?, sesso=?, anamnesi_json=?, stato=? WHERE id=?", (*p, id_cliente))
            else: cur.execute("INSERT INTO clienti (nome, cognome, telefono, email, data_nascita, sesso, anamnesi_json, stato) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", p)

    # --- AGENDA ---
    def add_evento(self, start, end, categoria, titolo, id_cliente=None, note=""):
        with self.transaction() as cur:
            id_contr = None
            if categoria == 'PT' and id_cliente:
                cur.execute("SELECT id FROM contratti WHERE id_cliente=? AND chiuso=0 AND crediti_usati < crediti_totali ORDER BY data_inizio ASC LIMIT 1", (id_cliente,))
                res = cur.fetchone(); id_contr = res['id'] if res else None
                if id_contr: cur.execute("UPDATE contratti SET crediti_usati = crediti_usati + 1 WHERE id=?", (id_contr,))
            cur.execute("INSERT INTO agenda (data_inizio, data_fine, categoria, titolo, id_cliente, id_contratto, note) VALUES (?, ?, ?, ?, ?, ?, ?)", (start, end, categoria, titolo, id_cliente, id_contr, note))
    def update_evento(self, id_ev, start, end, titolo, note=""):
        with self.transaction() as cur: cur.execute("UPDATE agenda SET data_inizio=?, data_fine=?, titolo=?, note=? WHERE id=?", (start, end, titolo, note, id_ev))
    def delete_evento(self, id_ev):
        with self.transaction() as cur:
            cur.execute("SELECT id_contratto FROM agenda WHERE id=?", (id_ev,))
            row = cur.fetchone()
            if row and row['id_contratto']: cur.execute("UPDATE contratti SET crediti_usati = crediti_usati - 1 WHERE id=?", (row['id_contratto'],))
            cur.execute("DELETE FROM agenda WHERE id=?", (id_ev,))
    def confirm_evento(self, id_ev):
        with self._connect() as conn: conn.execute("UPDATE agenda SET stato='Fatto' WHERE id=?", (id_ev,)); conn.commit()
    def get_agenda_range(self, start, end):
        with self._connect() as conn: return [dict(r) for r in conn.execute("SELECT a.*, c.nome, c.cognome FROM agenda a LEFT JOIN clienti c ON a.id_cliente=c.id WHERE date(a.data_inizio) BETWEEN ? AND ?", (start, end)).fetchall()]
    def get_storico_lezioni_cliente(self, id_cliente):
        with self._connect() as conn: return [dict(r) for r in conn.execute("SELECT a.*, c.tipo_pacchetto FROM agenda a LEFT JOIN contratti c ON a.id_contratto=c.id WHERE a.id_cliente=? ORDER BY a.data_inizio DESC", (id_cliente,)).fetchall()]
    def registra_rata(self, id_contratto, importo, metodo, data_pagamento=None, note=""):
        if data_pagamento is None: 
            data_pagamento = date.today()
        with self.transaction() as cur:
            cur.execute("SELECT id_cliente, prezzo_totale, totale_versato FROM contratti WHERE id=?", (id_contratto,))
            c = cur.fetchone()
            if not c: return
            nuovo_tot = c['totale_versato'] + importo
            stato = 'SALDATO' if nuovo_tot >= c['prezzo_totale'] else 'PARZIALE'
            cur.execute("INSERT INTO movimenti_cassa (data_effettiva, tipo, categoria, importo, metodo, id_cliente, id_contratto, note) VALUES (?, 'ENTRATA', ?, ?, ?, ?, ?, ?)", (data_pagamento, CATEGORIA_RATA, importo, metodo, c['id_cliente'], id_contratto, note))
            cur.execute("UPDATE contratti SET totale_versato=?, stato_pagamento=? WHERE id=?", (nuovo_tot, stato, id_contratto))

    # --- MISURAZIONI ---
    def add_misurazione_completa(self, id_cliente, dati):
        with self.transaction() as cur: cur.execute("INSERT INTO misurazioni (id_cliente, data_misurazione, peso, massa_grassa, massa_magra, acqua, collo, spalle, torace, braccio, vita, fianchi, coscia, polpaccio, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (id_cliente, dati.get('data'), dati.get('peso'), dati.get('grasso'), dati.get('muscolo'), dati.get('acqua'), dati.get('collo'), dati.get('spalle'), dati.get('torace'), dati.get('braccio'), dati.get('vita'), dati.get('fianchi'), dati.get('coscia'), dati.get('polpaccio'), dati.get('note')))
    def update_misurazione(self, id_misura, dati):
        with self.transaction() as cur: cur.execute("UPDATE misurazioni SET data_misurazione=?, peso=?, massa_grassa=?, massa_magra=?, acqua=?, collo=?, spalle=?, torace=?, braccio=?, vita=?, fianchi=?, coscia=?, polpaccio=?, note=? WHERE id=?", (dati.get('data'), dati.get('peso'), dati.get('grasso'), dati.get('muscolo'), dati.get('acqua'), dati.get('collo'), dati.get('spalle'), dati.get('torace'), dati.get('braccio'), dati.get('vita'), dati.get('fianchi'), dati.get('coscia'), dati.get('polpaccio'), dati.get('note'), id_misura))
    def get_progressi_cliente(self, id_cliente):
        with self._connect() as conn: return pd.read_sql("SELECT * FROM misurazioni WHERE id_cliente=? ORDER BY data_misurazione DESC", conn, params=(id_cliente,))