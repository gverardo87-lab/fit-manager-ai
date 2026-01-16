# file: core/crm_db.py (Versione FitManager - Update Fix)
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime
import pandas as pd
import json
from contextlib import contextmanager

DB_FILE = Path(__file__).resolve().parents[1] / "data" / "crm.db"

class CrmDBManager:
    def __init__(self, db_path: str | Path = DB_FILE):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_schema()
        self._check_and_migrate()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;") 
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS anagrafica_dipendenti (
                id_dipendente INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cognome TEXT NOT NULL,
                sesso TEXT,
                data_nascita TEXT,
                email TEXT,
                telefono TEXT,
                altezza INTEGER,
                peso_iniziale REAL,
                ruolo TEXT,
                obiettivo TEXT,
                livello_attivita TEXT,
                anamnesi_json TEXT,
                attivo BOOLEAN DEFAULT 1 NOT NULL,
                data_iscrizione DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            # ... (Altre tabelle standard omesse per brevità, non servono per questa modifica) ...
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS turni_standard (id_turno TEXT PRIMARY KEY, nome_turno TEXT, ora_inizio TIME, ora_fine TIME, scavalca_mezzanotte BOOLEAN)
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS squadre (id_squadra INTEGER PRIMARY KEY, nome_squadra TEXT, id_caposquadra INTEGER)
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS membri_squadra (id_squadra INTEGER, id_dipendente INTEGER, PRIMARY KEY (id_squadra, id_dipendente))
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS turni_master (id_turno_master INTEGER PRIMARY KEY, id_dipendente INTEGER, id_squadra INTEGER, data_ora_inizio_effettiva DATETIME, data_ora_fine_effettiva DATETIME, note TEXT, id_attivita TEXT)
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrazioni_ore (id_registrazione INTEGER PRIMARY KEY, id_turno_master INTEGER, id_dipendente INTEGER, id_attivita TEXT, data_ora_inizio DATETIME, data_ora_fine DATETIME, ore_presenza REAL, ore_lavoro REAL, tipo_ore TEXT, note TEXT)
            """)
            conn.commit()

    def _check_and_migrate(self):
        # Migrazione silenziosa (già fatta col reset, la manteniamo per sicurezza)
        pass

    # --- CRUD ANAGRAFICA COMPLETA ---
    def add_atleta_completo(self, dati: Dict[str, Any]) -> int:
        with self._connect() as conn:
            anamnesi_str = json.dumps(dati.get('anamnesi_dettagli', {}))
            cursor = conn.execute("""
                INSERT INTO anagrafica_dipendenti 
                (nome, cognome, sesso, data_nascita, email, telefono, altezza, peso_iniziale, ruolo, obiettivo, livello_attivita, anamnesi_json) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dati['nome'], dati['cognome'], dati['sesso'], dati['data_nascita'], 
                dati['email'], dati['telefono'], dati['altezza'], dati['peso'], 
                dati['abbonamento'], dati['obiettivo'], dati['livello_attivita'], anamnesi_str
            ))
            conn.commit()
            return cursor.lastrowid

    def update_atleta_completo(self, id_atleta: int, dati: Dict[str, Any]):
        """Aggiorna TUTTI i dati dell'atleta (incluso JSON)."""
        with self._connect() as conn:
            anamnesi_str = json.dumps(dati.get('anamnesi_dettagli', {}))
            conn.execute("""
                UPDATE anagrafica_dipendenti 
                SET nome=?, cognome=?, sesso=?, data_nascita=?, email=?, telefono=?, 
                    altezza=?, peso_iniziale=?, ruolo=?, obiettivo=?, livello_attivita=?, anamnesi_json=?, attivo=?
                WHERE id_dipendente=?
            """, (
                dati['nome'], dati['cognome'], dati['sesso'], dati['data_nascita'], 
                dati['email'], dati['telefono'], dati['altezza'], dati['peso'], 
                dati['abbonamento'], dati['obiettivo'], dati['livello_attivita'], anamnesi_str, dati.get('attivo', 1),
                id_atleta
            ))
            conn.commit()

    def get_atleta_by_id(self, id_atleta: int) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM anagrafica_dipendenti WHERE id_dipendente = ?", (id_atleta,)).fetchone()

    def get_dipendenti_df(self, solo_attivi: bool = False) -> pd.DataFrame:
        q = "SELECT * FROM anagrafica_dipendenti"
        if solo_attivi: q += " WHERE attivo = 1"
        q += " ORDER BY cognome, nome"
        with self._connect() as conn: return pd.read_sql_query(q, conn, index_col="id_dipendente")

    # --- METODI READ STANDARD ---
    def get_squadre(self) -> List[Dict[str, Any]]:
        with self._connect() as conn: return [dict(r) for r in conn.execute("SELECT * FROM squadre").fetchall()]
    
    def get_turni_standard(self) -> List[Dict[str, Any]]:
         with self._connect() as conn: return [dict(r) for r in conn.execute("SELECT * FROM turni_standard").fetchall()]