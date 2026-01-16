# file: core/crm_db.py (Versione FitManager 2.4 - Full Contract Edit)
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime
from datetime import date
import pandas as pd
import json
from contextlib import contextmanager

DB_FILE = Path(__file__).resolve().parents[1] / "data" / "crm.db"

class CrmDBManager:
    def __init__(self, db_path: str | Path = DB_FILE):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;") 
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Anagrafica (Base solida)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS anagrafica_dipendenti (
                id_dipendente INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, cognome TEXT NOT NULL, sesso TEXT, data_nascita TEXT,
                email TEXT, telefono TEXT, altezza INTEGER, peso_iniziale REAL,
                obiettivo TEXT, livello_attivita TEXT, 
                anamnesi_json TEXT, -- Qui salviamo: Lavoro, Stress, Fumo, Sport, Intolleranze
                attivo BOOLEAN DEFAULT 1 NOT NULL, 
                data_iscrizione DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

            # Abbonamenti (Contratti)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS abbonamenti (
                id_abbonamento INTEGER PRIMARY KEY AUTOINCREMENT,
                id_atleta INTEGER NOT NULL,
                tipo_pacchetto TEXT NOT NULL,
                data_inizio DATE NOT NULL,
                data_scadenza DATE,
                ingressi_totali INTEGER,
                ingressi_residui INTEGER,
                prezzo_pattuito REAL NOT NULL,
                stato TEXT DEFAULT 'Attivo',
                note_contratto TEXT,
                FOREIGN KEY (id_atleta) REFERENCES anagrafica_dipendenti(id_dipendente)
            )""")

            # Pagamenti (Cassa)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagamenti (
                id_pagamento INTEGER PRIMARY KEY AUTOINCREMENT,
                id_abbonamento INTEGER NOT NULL,
                data_pagamento DATE DEFAULT CURRENT_DATE,
                importo_versato REAL NOT NULL,
                metodo TEXT,
                note TEXT,
                FOREIGN KEY (id_abbonamento) REFERENCES abbonamenti(id_abbonamento)
            )""")
            
            # Tabelle tecniche (Legacy compatibili)
            self._init_technical_tables(cursor)
            conn.commit()

    def _init_technical_tables(self, cursor):
        cursor.execute("CREATE TABLE IF NOT EXISTS turni_standard (id_turno TEXT PRIMARY KEY, nome_turno TEXT, ora_inizio TIME, ora_fine TIME, scavalca_mezzanotte BOOLEAN)")
        cursor.execute("CREATE TABLE IF NOT EXISTS squadre (id_squadra INTEGER PRIMARY KEY, nome_squadra TEXT, id_caposquadra INTEGER)")
        cursor.execute("CREATE TABLE IF NOT EXISTS membri_squadra (id_squadra INTEGER, id_dipendente INTEGER, PRIMARY KEY (id_squadra, id_dipendente))")
        cursor.execute("CREATE TABLE IF NOT EXISTS turni_master (id_turno_master INTEGER PRIMARY KEY, id_dipendente INTEGER, id_squadra INTEGER, data_ora_inizio_effettiva DATETIME, data_ora_fine_effettiva DATETIME, note TEXT, id_attivita TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS registrazioni_ore (id_registrazione INTEGER PRIMARY KEY, id_turno_master INTEGER, id_dipendente INTEGER, id_attivita TEXT, data_ora_inizio DATETIME, data_ora_fine DATETIME, ore_presenza REAL, ore_lavoro REAL, tipo_ore TEXT, note TEXT)")

    @contextmanager
    def transaction(self):
        conn = self._connect(); cursor = conn.cursor(); cursor.execute("BEGIN TRANSACTION")
        try: yield cursor; conn.commit()
        except Exception as e: conn.rollback(); raise e
        finally: conn.close()

    # --- CRUD COMPLETO ---
    def add_atleta_completo(self, dati: Dict[str, Any]) -> int:
        with self.transaction() as cursor:
            # 1. Anagrafica
            anamnesi_str = json.dumps(dati.get('anamnesi_dettagli', {}))
            cursor.execute("""
                INSERT INTO anagrafica_dipendenti 
                (nome, cognome, sesso, data_nascita, email, telefono, altezza, peso_iniziale, obiettivo, livello_attivita, anamnesi_json) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dati['nome'], dati['cognome'], dati['sesso'], dati['data_nascita'], 
                dati['email'], dati['telefono'], dati['altezza'], dati['peso'], 
                dati['obiettivo'], dati['livello_attivita'], anamnesi_str
            ))
            id_atleta = cursor.lastrowid
            
            # 2. Abbonamento
            if 'abbonamento' in dati and dati['abbonamento']:
                abb = dati['abbonamento']
                cursor.execute("""
                    INSERT INTO abbonamenti (id_atleta, tipo_pacchetto, data_inizio, data_scadenza, ingressi_totali, ingressi_residui, prezzo_pattuito, note_contratto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (id_atleta, abb['tipo'], abb['start_date'], abb['end_date'], abb['ingressi'], abb['ingressi'], abb['prezzo'], abb['note']))
                id_abb = cursor.lastrowid
                
                # 3. Primo Pagamento
                if 'acconto' in dati and dati['acconto'] > 0:
                    cursor.execute("INSERT INTO pagamenti (id_abbonamento, data_pagamento, importo_versato, metodo, note) VALUES (?, ?, ?, ?, ?)", 
                                   (id_abb, date.today(), dati['acconto'], dati['metodo_pag'], "Acconto Iniziale"))
            return id_atleta

    def update_atleta_completo(self, id_atleta: int, dati: Dict[str, Any]):
        """Aggiorna TUTTO: Anagrafica, Anamnesi JSON e Abbonamento Attivo."""
        with self.transaction() as cursor:
            # 1. Update Anagrafica
            anamnesi_str = json.dumps(dati.get('anamnesi_dettagli', {}))
            cursor.execute("""
                UPDATE anagrafica_dipendenti 
                SET nome=?, cognome=?, sesso=?, data_nascita=?, email=?, telefono=?, 
                    altezza=?, peso_iniziale=?, obiettivo=?, livello_attivita=?, anamnesi_json=?
                WHERE id_dipendente=?
            """, (
                dati['nome'], dati['cognome'], dati['sesso'], dati['data_nascita'], 
                dati['email'], dati['telefono'], dati['altezza'], dati['peso'], 
                dati['obiettivo'], dati['livello_attivita'], anamnesi_str, id_atleta
            ))
            
            # 2. Update/Insert Abbonamento
            if 'abbonamento' in dati and dati['abbonamento']:
                abb = dati['abbonamento']
                
                # Cerchiamo se esiste un abbonamento attivo
                cursor.execute("SELECT id_abbonamento FROM abbonamenti WHERE id_atleta = ? AND stato = 'Attivo' ORDER BY id_abbonamento DESC LIMIT 1", (id_atleta,))
                row = cursor.fetchone()
                
                if row:
                    # AGGIORNA ESISTENTE
                    id_abb_esistente = row['id_abbonamento']
                    cursor.execute("""
                        UPDATE abbonamenti 
                        SET tipo_pacchetto=?, data_inizio=?, data_scadenza=?, ingressi_totali=?, prezzo_pattuito=?, note_contratto=?
                        WHERE id_abbonamento=?
                    """, (abb['tipo'], abb['start_date'], abb['end_date'], abb['ingressi'], abb['prezzo'], abb['note'], id_abb_esistente))
                else:
                    # CREA NUOVO (Se mancava o erano tutti chiusi)
                    cursor.execute("""
                        INSERT INTO abbonamenti (id_atleta, tipo_pacchetto, data_inizio, data_scadenza, ingressi_totali, ingressi_residui, prezzo_pattuito, note_contratto)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (id_atleta, abb['tipo'], abb['start_date'], abb['end_date'], abb['ingressi'], abb['ingressi'], abb['prezzo'], abb['note']))

    def get_atleta_detail(self, id_atleta: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            atleta = conn.execute("SELECT * FROM anagrafica_dipendenti WHERE id_dipendente = ?", (id_atleta,)).fetchone()
            if not atleta: return None
            res = dict(atleta)
            
            abb = conn.execute("SELECT * FROM abbonamenti WHERE id_atleta = ? AND stato = 'Attivo' ORDER BY data_inizio DESC LIMIT 1", (id_atleta,)).fetchone()
            res['abbonamento_attivo'] = dict(abb) if abb else None
            
            if abb:
                pagato = conn.execute("SELECT SUM(importo_versato) FROM pagamenti WHERE id_abbonamento = ?", (abb['id_abbonamento'],)).fetchone()[0] or 0.0
                res['billing'] = {"totale_dovuto": abb['prezzo_pattuito'], "pagato": pagato, "saldo": abb['prezzo_pattuito'] - pagato}
            return res

    def get_dipendenti_df(self, solo_attivi: bool = False) -> pd.DataFrame:
        # Query sicura che non rompe se mancano dati
        q = """
        SELECT a.id_dipendente, a.cognome, a.nome, a.obiettivo, a.telefono,
               sub.tipo_pacchetto as pacchetto, sub.data_scadenza as scadenza,
               (sub.prezzo_pattuito - IFNULL(p.pagato, 0)) as saldo_aperto
        FROM anagrafica_dipendenti a
        LEFT JOIN (SELECT * FROM abbonamenti WHERE stato = 'Attivo' GROUP BY id_atleta HAVING MAX(id_abbonamento)) sub ON a.id_dipendente = sub.id_atleta
        LEFT JOIN (SELECT id_abbonamento, SUM(importo_versato) as pagato FROM pagamenti GROUP BY id_abbonamento) p ON sub.id_abbonamento = p.id_abbonamento
        """
        if solo_attivi: q += " WHERE a.attivo = 1"
        q += " ORDER BY a.cognome, a.nome"
        with self._connect() as conn: return pd.read_sql_query(q, conn, index_col="id_dipendente")

    # Wrapper compatibilità
    def get_squadre(self): return [] 
    def get_turni_standard(self): return []