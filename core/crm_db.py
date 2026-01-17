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
            # Tabella per i piani di allenamento generati
            cursor.execute("""CREATE TABLE IF NOT EXISTS workout_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_inizio DATE NOT NULL,
                goal TEXT,
                level TEXT,
                duration_weeks INTEGER,
                sessions_per_week INTEGER,
                methodology TEXT,
                weekly_schedule TEXT,
                exercises_details TEXT,
                progressive_overload_strategy TEXT,
                recovery_recommendations TEXT,
                sources TEXT,
                attivo BOOLEAN DEFAULT 1,
                completato BOOLEAN DEFAULT 0,
                NOTE TEXT
            )""")
            
            # Tabella per il tracking del progresso durante il programma
            cursor.execute("""CREATE TABLE IF NOT EXISTS progress_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                data DATE NOT NULL DEFAULT CURRENT_DATE,
                pushup_reps INTEGER,
                vo2_estimate REAL,
                note TEXT,
                data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

            # Tabella per il tracking del margine orario giornaliero
            cursor.execute("""CREATE TABLE IF NOT EXISTS hourly_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data DATE NOT NULL,
                ore_totali_mese REAL DEFAULT 0,
                ore_pagate REAL DEFAULT 0,
                ore_non_pagate REAL DEFAULT 0,
                slot_disponibili INTEGER DEFAULT 0,
                slot_occupati INTEGER DEFAULT 0,
                fatturato_totale REAL DEFAULT 0,
                costi_fissi_giornalieri REAL DEFAULT 0,
                costi_variabili REAL DEFAULT 0,
                margine_lordo REAL DEFAULT 0,
                margine_netto REAL DEFAULT 0,
                margine_orario REAL DEFAULT 0,
                margine_orario_target REAL DEFAULT 0,
                note TEXT,
                data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(data)
            )""")
            
            # Tabella per gli slot disponibili (giorni/ore)
            cursor.execute("""CREATE TABLE IF NOT EXISTS slot_disponibili (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_slot DATE NOT NULL,
                ora_inizio TEXT NOT NULL,
                ora_fine TEXT NOT NULL,
                capacita INTEGER DEFAULT 1,
                occupati INTEGER DEFAULT 0,
                tipo_servizio TEXT,
                note TEXT,
                data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(data_slot, ora_inizio)
            )""")

            cursor.execute("""CREATE TABLE IF NOT EXISTS client_assessment_initial (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL UNIQUE,
                data_assessment DATE DEFAULT CURRENT_DATE,
                
                altezza_cm REAL,
                peso_kg REAL,
                massa_grassa_pct REAL,
                
                circonferenza_petto_cm REAL,
                circonferenza_vita_cm REAL,
                circonferenza_bicipite_sx_cm REAL,
                circonferenza_bicipite_dx_cm REAL,
                circonferenza_fianchi_cm REAL,
                circonferenza_quadricipite_sx_cm REAL,
                circonferenza_quadricipite_dx_cm REAL,
                circonferenza_coscia_sx_cm REAL,
                circonferenza_coscia_dx_cm REAL,
                
                pushups_reps INTEGER,
                pushups_note TEXT,
                
                panca_peso_kg REAL,
                panca_reps INTEGER,
                panca_note TEXT,
                
                rematore_peso_kg REAL,
                rematore_reps INTEGER,
                rematore_note TEXT,
                
                lat_machine_peso_kg REAL,
                lat_machine_reps INTEGER,
                lat_machine_note TEXT,
                
                squat_bastone_note TEXT,
                squat_macchina_peso_kg REAL,
                squat_macchina_reps INTEGER,
                squat_macchina_note TEXT,
                
                mobilita_spalle_note TEXT,
                mobilita_gomiti_note TEXT,
                mobilita_polsi_note TEXT,
                mobilita_anche_note TEXT,
                mobilita_schiena_note TEXT,
                
                infortuni_pregessi TEXT,
                infortuni_attuali TEXT,
                limitazioni TEXT,
                storia_medica TEXT,
                
                goals_quantificabili TEXT,
                goals_benessere TEXT,
                
                foto_fronte_path VARCHAR,
                foto_lato_path VARCHAR,
                foto_dietro_path VARCHAR,
                
                note_colloquio TEXT,
                
                data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS client_assessment_followup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                data_followup DATE DEFAULT CURRENT_DATE,
                
                peso_kg REAL,
                massa_grassa_pct REAL,
                
                circonferenza_petto_cm REAL,
                circonferenza_vita_cm REAL,
                circonferenza_bicipite_sx_cm REAL,
                circonferenza_bicipite_dx_cm REAL,
                circonferenza_fianchi_cm REAL,
                circonferenza_quadricipite_sx_cm REAL,
                circonferenza_quadricipite_dx_cm REAL,
                circonferenza_coscia_sx_cm REAL,
                circonferenza_coscia_dx_cm REAL,
                
                pushups_reps INTEGER,
                panca_peso_kg REAL,
                panca_reps INTEGER,
                rematore_peso_kg REAL,
                rematore_reps INTEGER,
                squat_peso_kg REAL,
                squat_reps INTEGER,
                
                goals_progress TEXT,
                
                foto_fronte_path VARCHAR,
                foto_lato_path VARCHAR,
                foto_dietro_path VARCHAR,
                
                note_followup TEXT,
                
                data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP
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

    # ═══════════════════════════════════════════════════════════════
    # SISTEMA FINANZIARIO UNIFICATO
    # Logica coerente per Cassa + Margine Orario
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_unified_metrics(self, data_inizio: date, data_fine: date) -> Dict[str, Any]:
        """
        Calcola metriche finanziarie unificate per un periodo.
        
        FORMULE USATE (da sincronizzare tra Cassa e Margine):
        ─────────────────────────────────────────────────────
        1. ENTRATE = SUM(importo) movimenti_cassa WHERE tipo='ENTRATA' AND data_effettiva IN [inizio, fine]
        
        2. ORE FATTURATE = SUM(crediti_totali) contratti WHERE sono COMPLETAMENTE PAGATI
                          durante il periodo (date_vendita IN [inizio, fine])
        
        3. ORE ESEGUITE = SUM(durata) agenda WHERE categoria IN ['Lezione', 'Allenamento'] 
                         (per tracking, non per calcolo margine)
        
        4. COSTI FISSI MENSILI = SUM(importo) FROM spese_ricorrenti WHERE frequenza='MENSILE'
        
        5. COSTI FISSI PERIODO = (Costi Fissi Mensili / 30) * giorni_nel_periodo
        
        6. COSTI VARIABILI = SUM(importo) WHERE tipo='USCITA' AND categoria IN ['SPESE_ATTREZZATURE', 'ALTRO']
        
        7. MARGINE LORDO = Entrate - Costi Fissi Periodo - Costi Variabili
        
        8. MARGINE/ORA = Margine Lordo / ORE FATTURATE (ciò che effettivamente è stato pagato!)
        
        Returns:
            Dict con metriche unificate
        """
        with self._connect() as conn:
            # 1. ENTRATE (soldi reali da movimenti_cassa)
            entrate = conn.execute("""
                SELECT COALESCE(SUM(importo), 0)
                FROM movimenti_cassa
                WHERE tipo='ENTRATA' AND data_effettiva BETWEEN ? AND ?
            """, (data_inizio, data_fine)).fetchone()[0]
            
            # 2. ORE FATTURATE (da contratti PAGATI - crediti totali del contratto)
            # Un contratto "pagato" è quando totale_versato >= prezzo_totale
            ore_fatturate = conn.execute("""
                SELECT COALESCE(SUM(crediti_totali), 0)
                FROM contratti
                WHERE data_vendita BETWEEN ? AND ?
                AND totale_versato > 0
            """, (data_inizio, data_fine)).fetchone()[0]
            
            # 3. ORE ESEGUITE (da agenda - solo per tracking)
            ore_eseguite = conn.execute("""
                SELECT COALESCE(SUM(
                    (CAST(substr(data_fine, 12, 2) AS REAL) + 
                     CAST(substr(data_fine, 15, 2) AS REAL)/60) -
                    (CAST(substr(data_inizio, 12, 2) AS REAL) + 
                     CAST(substr(data_inizio, 15, 2) AS REAL)/60)
                ), 0)
                FROM agenda
                WHERE categoria IN ('Lezione', 'Allenamento', 'Sessione')
                AND DATE(data_inizio) BETWEEN ? AND ?
            """, (data_inizio, data_fine)).fetchone()[0]
            
            # 4. ORE NON PAGATE (admin, formazione, marketing)
            ore_non_pagate = conn.execute("""
                SELECT COALESCE(SUM(
                    (CAST(substr(data_fine, 12, 2) AS REAL) + 
                     CAST(substr(data_fine, 15, 2) AS REAL)/60) -
                    (CAST(substr(data_inizio, 12, 2) AS REAL) + 
                     CAST(substr(data_inizio, 15, 2) AS REAL)/60)
                ), 0)
                FROM agenda
                WHERE categoria IN ('Admin', 'Formazione', 'Marketing', 'Riunione')
                AND DATE(data_inizio) BETWEEN ? AND ?
            """, (data_inizio, data_fine)).fetchone()[0]
            
            # 5. COSTI FISSI MENSILI
            costi_fissi_mensili = conn.execute("""
                SELECT COALESCE(SUM(importo), 0)
                FROM spese_ricorrenti
                WHERE attiva=1 AND frequenza='MENSILE'
            """).fetchone()[0]
            
            # Calcola costi fissi proporzionali al periodo
            giorni_periodo = (data_fine - data_inizio).days + 1
            costi_fissi_periodo = (costi_fissi_mensili / 30) * giorni_periodo
            
            # 6. COSTI VARIABILI (da movimenti_cassa)
            costi_variabili = conn.execute("""
                SELECT COALESCE(SUM(importo), 0)
                FROM movimenti_cassa
                WHERE tipo='USCITA' 
                AND categoria IN ('SPESE_ATTREZZATURE', 'ALTRO')
                AND data_effettiva BETWEEN ? AND ?
            """, (data_inizio, data_fine)).fetchone()[0]
            
            # 7. TOTALE COSTI
            costi_totali = costi_fissi_periodo + costi_variabili
            
            # 8. MARGINE (basato su ORE FATTURATE - ciò che il cliente ha EFFETTIVAMENTE PAGATO)
            margine_lordo = entrate - costi_totali
            margine_orario = (margine_lordo / ore_fatturate) if ore_fatturate > 0 else 0
            
            # 9. FATTURATO/ORA (per comparazione con ore eseguite)
            fatturato_per_ora = (entrate / ore_fatturate) if ore_fatturate > 0 else 0
            
            return {
                'periodo_inizio': str(data_inizio),
                'periodo_fine': str(data_fine),
                'giorni': giorni_periodo,
                
                # ORE
                'ore_fatturate': round(ore_fatturate, 2),  # ORE PAGATE DAL CLIENTE (da contratti)
                'ore_eseguite': round(ore_eseguite, 2),    # Ore fisicamente eseguite (da agenda)
                'ore_non_pagate': round(ore_non_pagate, 2),  # Ore admin/formazione
                'ore_totali': round(ore_eseguite + ore_non_pagate, 2),
                
                # ENTRATE
                'entrate_totali': round(entrate, 2),
                'fatturato_per_ora': round(fatturato_per_ora, 2),
                
                # COSTI
                'costi_fissi_mensili': round(costi_fissi_mensili, 2),
                'costi_fissi_periodo': round(costi_fissi_periodo, 2),
                'costi_variabili': round(costi_variabili, 2),
                'costi_totali': round(costi_totali, 2),
                
                # MARGINE
                'margine_lordo': round(margine_lordo, 2),
                'margine_netto': round(margine_lordo, 2),  # Netto = Lordo in questo caso
                'margine_orario': round(margine_orario, 2),
                'margine_per_ora_costi_variabili': round((entrate - costi_variabili) / ore_fatturate, 2) if ore_fatturate > 0 else 0,
                
                # METADATA
                'formula': 'Margine/Ora = (Entrate - Costi_Fissi_Periodo - Costi_Variabili) / Ore_Fatturate',
                'note': 'Ore Fatturate = crediti totali da contratti PAGATI (ciò che il cliente ha effettivamente pagato)'
            }
    
    def get_daily_metrics_range(self, data_inizio: date, data_fine: date) -> list:
        """
        Calcola metriche giornaliere per un range di date.
        Ritorna una lista di dict, uno per ogni giorno del range.
        """
        metriche_giornaliere = []
        data_corrente = data_inizio
        
        while data_corrente <= data_fine:
            metriche = self.calculate_unified_metrics(data_corrente, data_corrente)
            metriche['data'] = str(data_corrente)
            metriche_giornaliere.append(metriche)
            data_corrente += timedelta(days=1)
        
        return metriche_giornaliere
    
    def get_weekly_metrics_range(self, data_inizio: date, data_fine: date) -> list:
        """
        Calcola metriche settimanali (lunedì-domenica) per un range di date.
        Ritorna una lista di dict, uno per ogni settimana.
        """
        metriche_settimanali = []
        
        # Trova il primo lunedì
        lunedi_corrente = data_inizio - timedelta(days=data_inizio.weekday())
        
        while lunedi_corrente <= data_fine:
            domenica = lunedi_corrente + timedelta(days=6)
            
            # Non superare data_fine
            if domenica > data_fine:
                domenica = data_fine
            
            metriche = self.calculate_unified_metrics(lunedi_corrente, domenica)
            metriche['settimana'] = f"{lunedi_corrente.strftime('%d/%m')} - {domenica.strftime('%d/%m')}"
            metriche_settimanali.append(metriche)
            
            lunedi_corrente += timedelta(days=7)
        
        return metriche_settimanali

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
    
    def sincronizza_stato_contratti_da_movimenti(self):
        """
        Sincronizza lo stato dei contratti (totale_versato, stato_pagamento) 
        basandosi sui movimenti di RATA_CONTRATTO già registrati.
        Utile quando i pagamenti sono stati registrati direttamente come movimenti.
        """
        with self.transaction() as cur:
            # Per ogni contratto, calcola il totale versato dai movimenti RATA_CONTRATTO
            cur.execute("""
                SELECT DISTINCT c.id, c.prezzo_totale
                FROM contratti c
                WHERE EXISTS (
                    SELECT 1 FROM movimenti_cassa m 
                    WHERE m.id_contratto = c.id 
                    AND m.categoria = 'RATA_CONTRATTO'
                )
            """)
            contratti = cur.fetchall()
            
            for contratto in contratti:
                id_contr = contratto['id']
                prezzo_tot = contratto['prezzo_totale']
                
                # Somma i movimenti di RATA_CONTRATTO per questo contratto
                cur.execute("""
                    SELECT COALESCE(SUM(importo), 0) as totale
                    FROM movimenti_cassa
                    WHERE id_contratto = ? AND categoria = 'RATA_CONTRATTO'
                """, (id_contr,))
                
                result = cur.fetchone()
                totale_versato = result['totale'] if result else 0
                
                # Determina lo stato
                if totale_versato >= prezzo_tot:
                    nuovo_stato = 'SALDATO'
                elif totale_versato > 0:
                    nuovo_stato = 'PARZIALE'
                else:
                    nuovo_stato = 'PENDENTE'
                
                # Aggiorna il contratto
                cur.execute("""
                    UPDATE contratti 
                    SET totale_versato = ?, stato_pagamento = ?
                    WHERE id = ?
                """, (totale_versato, nuovo_stato, id_contr))

    # --- MISURAZIONI ---
    def add_misurazione_completa(self, id_cliente, dati):
        with self.transaction() as cur: cur.execute("INSERT INTO misurazioni (id_cliente, data_misurazione, peso, massa_grassa, massa_magra, acqua, collo, spalle, torace, braccio, vita, fianchi, coscia, polpaccio, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (id_cliente, dati.get('data'), dati.get('peso'), dati.get('grasso'), dati.get('muscolo'), dati.get('acqua'), dati.get('collo'), dati.get('spalle'), dati.get('torace'), dati.get('braccio'), dati.get('vita'), dati.get('fianchi'), dati.get('coscia'), dati.get('polpaccio'), dati.get('note')))
    def update_misurazione(self, id_misura, dati):
        with self.transaction() as cur: cur.execute("UPDATE misurazioni SET data_misurazione=?, peso=?, massa_grassa=?, massa_magra=?, acqua=?, collo=?, spalle=?, torace=?, braccio=?, vita=?, fianchi=?, coscia=?, polpaccio=?, note=? WHERE id=?", (dati.get('data'), dati.get('peso'), dati.get('grasso'), dati.get('muscolo'), dati.get('acqua'), dati.get('collo'), dati.get('spalle'), dati.get('torace'), dati.get('braccio'), dati.get('vita'), dati.get('fianchi'), dati.get('coscia'), dati.get('polpaccio'), dati.get('note'), id_misura))
    def get_progressi_cliente(self, id_cliente):
        with self._connect() as conn: return pd.read_sql("SELECT * FROM misurazioni WHERE id_cliente=? ORDER BY data_misurazione DESC", conn, params=(id_cliente,))

    # --- ASSESSMENTS ---
    def save_assessment_initial(self, id_cliente, dati):
        """Salva assessment iniziale completo per un cliente"""
        with self.transaction() as cur:
            cur.execute("""
                INSERT OR REPLACE INTO client_assessment_initial 
                (id_cliente, data_assessment, altezza_cm, peso_kg, massa_grassa_pct,
                 circonferenza_petto_cm, circonferenza_vita_cm, circonferenza_bicipite_sx_cm, 
                 circonferenza_bicipite_dx_cm, circonferenza_fianchi_cm, circonferenza_quadricipite_sx_cm,
                 circonferenza_quadricipite_dx_cm, circonferenza_coscia_sx_cm, circonferenza_coscia_dx_cm,
                 pushups_reps, pushups_note, panca_peso_kg, panca_reps, panca_note,
                 rematore_peso_kg, rematore_reps, rematore_note, lat_machine_peso_kg, lat_machine_reps,
                 lat_machine_note, squat_bastone_note, squat_macchina_peso_kg, squat_macchina_reps,
                 squat_macchina_note, mobilita_spalle_note, mobilita_gomiti_note, mobilita_polsi_note,
                 mobilita_anche_note, mobilita_schiena_note, infortuni_pregessi, infortuni_attuali,
                 limitazioni, storia_medica, goals_quantificabili, goals_benessere,
                 foto_fronte_path, foto_lato_path, foto_dietro_path, note_colloquio)
                VALUES (?, date(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_cliente, dati.get('altezza_cm'), dati.get('peso_kg'), dati.get('massa_grassa_pct'),
                  dati.get('circonferenza_petto_cm'), dati.get('circonferenza_vita_cm'),
                  dati.get('circonferenza_bicipite_sx_cm'), dati.get('circonferenza_bicipite_dx_cm'),
                  dati.get('circonferenza_fianchi_cm'), dati.get('circonferenza_quadricipite_sx_cm'),
                  dati.get('circonferenza_quadricipite_dx_cm'), dati.get('circonferenza_coscia_sx_cm'),
                  dati.get('circonferenza_coscia_dx_cm'), dati.get('pushups_reps'), dati.get('pushups_note'),
                  dati.get('panca_peso_kg'), dati.get('panca_reps'), dati.get('panca_note'),
                  dati.get('rematore_peso_kg'), dati.get('rematore_reps'), dati.get('rematore_note'),
                  dati.get('lat_machine_peso_kg'), dati.get('lat_machine_reps'), dati.get('lat_machine_note'),
                  dati.get('squat_bastone_note'), dati.get('squat_macchina_peso_kg'),
                  dati.get('squat_macchina_reps'), dati.get('squat_macchina_note'),
                  dati.get('mobilita_spalle_note'), dati.get('mobilita_gomiti_note'),
                  dati.get('mobilita_polsi_note'), dati.get('mobilita_anche_note'),
                  dati.get('mobilita_schiena_note'), dati.get('infortuni_pregessi'),
                  dati.get('infortuni_attuali'), dati.get('limitazioni'), dati.get('storia_medica'),
                  dati.get('goals_quantificabili'), dati.get('goals_benessere'),
                  dati.get('foto_fronte_path'), dati.get('foto_lato_path'), dati.get('foto_dietro_path'),
                  dati.get('note_colloquio')))

    def get_assessment_initial(self, id_cliente):
        """Recupera assessment iniziale di un cliente"""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM client_assessment_initial WHERE id_cliente=?", (id_cliente,)).fetchone()
            return dict(row) if row else None

    def save_assessment_followup(self, id_cliente, dati):
        """Salva followup assessment"""
        with self.transaction() as cur:
            cur.execute("""
                INSERT INTO client_assessment_followup
                (id_cliente, data_followup, peso_kg, massa_grassa_pct,
                 circonferenza_petto_cm, circonferenza_vita_cm, circonferenza_bicipite_sx_cm,
                 circonferenza_bicipite_dx_cm, circonferenza_fianchi_cm, circonferenza_quadricipite_sx_cm,
                 circonferenza_quadricipite_dx_cm, circonferenza_coscia_sx_cm, circonferenza_coscia_dx_cm,
                 pushups_reps, panca_peso_kg, panca_reps, rematore_peso_kg, rematore_reps,
                 squat_peso_kg, squat_reps, goals_progress,
                 foto_fronte_path, foto_lato_path, foto_dietro_path, note_followup)
                VALUES (?, date(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_cliente, dati.get('peso_kg'), dati.get('massa_grassa_pct'),
                  dati.get('circonferenza_petto_cm'), dati.get('circonferenza_vita_cm'),
                  dati.get('circonferenza_bicipite_sx_cm'), dati.get('circonferenza_bicipite_dx_cm'),
                  dati.get('circonferenza_fianchi_cm'), dati.get('circonferenza_quadricipite_sx_cm'),
                  dati.get('circonferenza_quadricipite_dx_cm'), dati.get('circonferenza_coscia_sx_cm'),
                  dati.get('circonferenza_coscia_dx_cm'), dati.get('pushups_reps'),
                  dati.get('panca_peso_kg'), dati.get('panca_reps'), dati.get('rematore_peso_kg'),
                  dati.get('rematore_reps'), dati.get('squat_peso_kg'), dati.get('squat_reps'),
                  dati.get('goals_progress'), dati.get('foto_fronte_path'), dati.get('foto_lato_path'),
                  dati.get('foto_dietro_path'), dati.get('note_followup')))

    def get_assessment_followups(self, id_cliente):
        """Recupera tutti i followup assessments di un cliente"""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM client_assessment_followup 
                WHERE id_cliente=? 
                ORDER BY data_followup DESC
            """, (id_cliente,)).fetchall()
            return [dict(r) for r in rows]

    def get_assessment_followup_latest(self, id_cliente):
        """Recupera il followup assessment più recente"""
        with self._connect() as conn:
            row = conn.execute("""
                SELECT * FROM client_assessment_followup 
                WHERE id_cliente=? 
                ORDER BY data_followup DESC 
                LIMIT 1
            """, (id_cliente,)).fetchone()
            return dict(row) if row else None

    def get_assessment_timeline(self, id_cliente):
        """Recupera timeline completa di assessments (initial + followups)"""
        with self._connect() as conn:
            initial = conn.execute("SELECT * FROM client_assessment_initial WHERE id_cliente=?", (id_cliente,)).fetchone()
            followups = conn.execute("SELECT * FROM client_assessment_followup WHERE id_cliente=? ORDER BY data_followup ASC", (id_cliente,)).fetchall()
            
            timeline = []
            if initial:
                timeline.append({"type": "initial", "data": dict(initial)})
            for fu in followups:
                timeline.append({"type": "followup", "data": dict(fu)})
            
            return timeline

    # ═══════════════════════════════════════════════════════════════
    # METODI PER WORKOUT PLANS (PROGRAMMI DI ALLENAMENTO)
    # ═══════════════════════════════════════════════════════════════
    
    def save_workout_plan(self, id_cliente: int, plan_data: Dict[str, Any], data_inizio: date) -> int:
        """
        Salva un programma di allenamento generato nel database.
        
        Args:
            id_cliente: ID del cliente
            plan_data: Dizionario con i dati del programma (da WorkoutGenerator)
            data_inizio: Data di inizio del programma
        
        Returns:
            ID del programma salvato
        """
        import json
        
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # Converti liste in JSON per storage
            weekly_schedule_json = json.dumps(plan_data.get('weekly_schedule', []))
            sources_json = json.dumps(plan_data.get('sources', []))
            
            cursor.execute("""
                INSERT INTO workout_plans (
                    id_cliente, data_inizio, goal, level, duration_weeks, 
                    sessions_per_week, methodology, weekly_schedule, 
                    exercises_details, progressive_overload_strategy, 
                    recovery_recommendations, sources, attivo, completato
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_cliente,
                data_inizio,
                plan_data.get('goal'),
                plan_data.get('level'),
                plan_data.get('duration_weeks'),
                plan_data.get('sessions_per_week'),
                plan_data.get('methodology', ''),
                weekly_schedule_json,
                plan_data.get('exercises_details', ''),
                plan_data.get('progressive_overload_strategy', ''),
                plan_data.get('recovery_recommendations', ''),
                sources_json,
                1,  # attivo
                0   # non completato
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_workout_plans_for_cliente(self, id_cliente: int) -> List[Dict[str, Any]]:
        """
        Recupera tutti i piani di allenamento per un cliente.
        
        Args:
            id_cliente: ID del cliente
        
        Returns:
            Lista di dizionari con i dati dei programmi
        """
        import json
        
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM workout_plans 
                WHERE id_cliente=? 
                ORDER BY data_creazione DESC
            """, (id_cliente,)).fetchall()
            
            plans = []
            for row in rows:
                plan_dict = dict(row)
                # Converte JSON back to Python objects
                plan_dict['weekly_schedule'] = json.loads(plan_dict.get('weekly_schedule', '[]'))
                plan_dict['sources'] = json.loads(plan_dict.get('sources', '[]'))
                plans.append(plan_dict)
            
            return plans
    
    def get_workout_plan_by_id(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """Recupera un programma specifico per ID."""
        import json
        
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM workout_plans WHERE id=?", (plan_id,)).fetchone()
            
            if not row:
                return None
            
            plan_dict = dict(row)
            plan_dict['weekly_schedule'] = json.loads(plan_dict.get('weekly_schedule', '[]'))
            plan_dict['sources'] = json.loads(plan_dict.get('sources', '[]'))
            
            return plan_dict
    
    def delete_workout_plan(self, plan_id: int) -> bool:
        """Elimina un programma di allenamento."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM workout_plans WHERE id=?", (plan_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def mark_workout_plan_completed(self, plan_id: int) -> bool:
        """Marca un programma come completato."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE workout_plans SET completato=1 WHERE id=?", (plan_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_progress_record(
        self,
        id_cliente: int,
        data: date,
        pushup_reps: int = 0,
        vo2_estimate: float = 0.0,
        note: str = ""
    ) -> int:
        """
        Aggiungi un record di progresso per il tracking.
        
        Args:
            id_cliente: ID cliente
            data: Data del record
            pushup_reps: Numero di pushup consecutivi
            vo2_estimate: Stima VO2 max
            note: Note sul progresso
        
        Returns:
            ID del record creato
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO progress_records (
                    id_cliente, data, pushup_reps, vo2_estimate, note
                ) VALUES (?, ?, ?, ?, ?)
            """, (id_cliente, data, pushup_reps, vo2_estimate, note))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_progress_records(self, id_cliente: int) -> List[Dict[str, Any]]:
        """Recupera tutti i record di progresso per un cliente."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM progress_records 
                WHERE id_cliente=? 
                ORDER BY data DESC
            """, (id_cliente,)).fetchall()
            
            return [dict(r) for r in rows]
    
    # ═══════════════════════════════════════════════════════════════
    # SISTEMA DI TRACKING MARGINE ORARIO
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_hourly_metrics(self, data: date) -> Dict[str, Any]:
        """
        Calcola metriche orarie per un giorno specifico.
        
        Args:
            data: Data per cui calcolare le metriche
        
        Returns:
            Dict con ore pagate, non pagate, slot, fatturato, costi, margine
        """
        with self._connect() as conn:
            # 1. Ore pagate (lezioni registrate in agenda)
            ore_pagate = conn.execute("""
                SELECT COALESCE(SUM(
                    (CAST(substr(data_fine, 12, 2) AS REAL) + 
                     CAST(substr(data_fine, 15, 2) AS REAL)/60) -
                    (CAST(substr(data_inizio, 12, 2) AS REAL) + 
                     CAST(substr(data_inizio, 15, 2) AS REAL)/60)
                ), 0) as ore
                FROM agenda
                WHERE DATE(data_inizio) = ? AND categoria IN ('Lezione', 'Allenamento', 'Sessione')
            """, (data,)).fetchone()[0]
            
            # 2. Ore non pagate (admin, formazione, marketing)
            ore_non_pagate = conn.execute("""
                SELECT COALESCE(SUM(
                    (CAST(substr(data_fine, 12, 2) AS REAL) + 
                     CAST(substr(data_fine, 15, 2) AS REAL)/60) -
                    (CAST(substr(data_inizio, 12, 2) AS REAL) + 
                     CAST(substr(data_inizio, 15, 2) AS REAL)/60)
                ), 0) as ore
                FROM agenda
                WHERE DATE(data_inizio) = ? AND categoria IN ('Admin', 'Formazione', 'Marketing')
            """, (data,)).fetchone()[0]
            
            # 3. Slot disponibili e occupati
            slot_info = conn.execute("""
                SELECT 
                    COALESCE(SUM(capacita), 0) as slot_tot,
                    COALESCE(SUM(occupati), 0) as slot_occ
                FROM slot_disponibili
                WHERE data_slot = ?
            """, (data,)).fetchone()
            slot_disponibili = slot_info[0] - slot_info[1] if slot_info else (0, 0)
            slot_occupati = slot_info[1] if slot_info else 0
            
            # 4. Fatturato del giorno
            fatturato = conn.execute("""
                SELECT COALESCE(SUM(importo), 0)
                FROM movimenti_cassa
                WHERE DATE(data_effettiva) = ? AND tipo = 'ENTRATA'
            """, (data,)).fetchone()[0]
            
            # 5. Costi fissi (spalmati su ore del mese)
            inizio_mese = date(data.year, data.month, 1)
            fine_mese = date(data.year, data.month + 1, 1) - timedelta(days=1) if data.month < 12 else date(data.year, 12, 31)
            
            ore_totali_mese = conn.execute("""
                SELECT COALESCE(SUM(
                    (CAST(substr(data_fine, 12, 2) AS REAL) + 
                     CAST(substr(data_fine, 15, 2) AS REAL)/60) -
                    (CAST(substr(data_inizio, 12, 2) AS REAL) + 
                     CAST(substr(data_inizio, 15, 2) AS REAL)/60)
                ), 0) as ore
                FROM agenda
                WHERE DATE(data_inizio) BETWEEN ? AND ? AND categoria IN ('Lezione', 'Allenamento', 'Sessione')
            """, (inizio_mese, fine_mese)).fetchone()[0]
            
            costi_fissi_mese = conn.execute("""
                SELECT COALESCE(SUM(importo), 0)
                FROM spese_ricorrenti
                WHERE attiva = 1 AND frequenza = 'MENSILE'
            """).fetchone()[0]
            
            costi_fissi_giornalieri = costi_fissi_mese / 30 if ore_totali_mese > 0 else 0
            
            # 6. Costi variabili (del giorno)
            costi_variabili = conn.execute("""
                SELECT COALESCE(SUM(importo), 0)
                FROM movimenti_cassa
                WHERE DATE(data_effettiva) = ? AND tipo = 'USCITA' AND categoria IN ('SPESE_ATTREZZATURE', 'ALTRO')
            """, (data,)).fetchone()[0]
            
            # 7. Calcolo margine
            ore_totali_giorno = ore_pagate + ore_non_pagate
            margine_lordo = fatturato - costi_fissi_giornalieri - costi_variabili
            margine_netto = margine_lordo
            margine_orario = (margine_netto / ore_pagate) if ore_pagate > 0 else 0
            
            return {
                'data': str(data),
                'ore_pagate': round(ore_pagate, 2),
                'ore_non_pagate': round(ore_non_pagate, 2),
                'ore_totali': round(ore_totali_giorno, 2),
                'slot_disponibili': int(slot_disponibili),
                'slot_occupati': int(slot_occupati),
                'fatturato_totale': round(fatturato, 2),
                'costi_fissi_giornalieri': round(costi_fissi_giornalieri, 2),
                'costi_variabili': round(costi_variabili, 2),
                'costi_totali': round(costi_fissi_giornalieri + costi_variabili, 2),
                'margine_lordo': round(margine_lordo, 2),
                'margine_netto': round(margine_netto, 2),
                'margine_orario': round(margine_orario, 2),
                'ore_totali_mese': round(ore_totali_mese, 2)
            }
    
    def get_hourly_metrics_period(self, data_inizio: date, data_fine: date) -> List[Dict[str, Any]]:
        """Recupera metriche orarie per un periodo."""
        metrics = []
        current = data_inizio
        while current <= data_fine:
            metrics.append(self.calculate_hourly_metrics(current))
            current += timedelta(days=1)
        return metrics
    
    def get_hourly_metrics_week(self, data: date) -> Dict[str, Any]:
        """Calcola metriche per la settimana contenente la data."""
        # Lunedì della settimana
        lunedi = data - timedelta(days=data.weekday())
        domenica = lunedi + timedelta(days=6)
        
        daily_metrics = self.get_hourly_metrics_period(lunedi, domenica)
        
        # Aggrega
        return {
            'settimana': f"{lunedi} - {domenica}",
            'ore_pagate': round(sum(m['ore_pagate'] for m in daily_metrics), 2),
            'ore_non_pagate': round(sum(m['ore_non_pagate'] for m in daily_metrics), 2),
            'ore_totali': round(sum(m['ore_totali'] for m in daily_metrics), 2),
            'slot_disponibili': sum(m['slot_disponibili'] for m in daily_metrics),
            'slot_occupati': sum(m['slot_occupati'] for m in daily_metrics),
            'fatturato_totale': round(sum(m['fatturato_totale'] for m in daily_metrics), 2),
            'costi_totali': round(sum(m['costi_totali'] for m in daily_metrics), 2),
            'margine_lordo': round(sum(m['margine_lordo'] for m in daily_metrics), 2),
            'margine_orario': round(sum(m['margine_orario'] for m in daily_metrics) / 7, 2),
            'giornalieri': daily_metrics
        }
    
    def get_hourly_metrics_month(self, anno: int, mese: int) -> Dict[str, Any]:
        """Calcola metriche per il mese."""
        from calendar import monthrange
        
        ultimo_giorno = monthrange(anno, mese)[1]
        data_inizio = date(anno, mese, 1)
        data_fine = date(anno, mese, ultimo_giorno)
        
        daily_metrics = self.get_hourly_metrics_period(data_inizio, data_fine)
        
        return {
            'mese': f"{anno}-{mese:02d}",
            'ore_pagate': round(sum(m['ore_pagate'] for m in daily_metrics), 2),
            'ore_non_pagate': round(sum(m['ore_non_pagate'] for m in daily_metrics), 2),
            'ore_totali': round(sum(m['ore_totali'] for m in daily_metrics), 2),
            'slot_disponibili': sum(m['slot_disponibili'] for m in daily_metrics),
            'slot_occupati': sum(m['slot_occupati'] for m in daily_metrics),
            'fatturato_totale': round(sum(m['fatturato_totale'] for m in daily_metrics), 2),
            'costi_totali': round(sum(m['costi_totali'] for m in daily_metrics), 2),
            'margine_lordo': round(sum(m['margine_lordo'] for m in daily_metrics), 2),
            'margine_orario': round(sum(m['margine_orario'] for m in daily_metrics) / len(daily_metrics), 2) if daily_metrics else 0,
            'giorni_totali': len(daily_metrics)
        }
    
    def get_margine_per_cliente(self, data_inizio: date, data_fine: date) -> List[Dict[str, Any]]:
        """Calcola margine per ogni cliente nel periodo."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT 
                    c.id,
                    c.nome || ' ' || c.cognome as cliente,
                    COUNT(DISTINCT a.id) as sessioni,
                    COALESCE(SUM(
                        (CAST(substr(a.data_fine, 12, 2) AS REAL) + 
                         CAST(substr(a.data_fine, 15, 2) AS REAL)/60) -
                        (CAST(substr(a.data_inizio, 12, 2) AS REAL) + 
                         CAST(substr(a.data_inizio, 15, 2) AS REAL)/60)
                    ), 0) as ore,
                    COALESCE(SUM(CASE WHEN m.tipo='ENTRATA' THEN m.importo ELSE 0 END), 0) as fatturato,
                    COALESCE(SUM(CASE WHEN m.tipo='USCITA' THEN m.importo ELSE 0 END), 0) as costi
                FROM clienti c
                LEFT JOIN agenda a ON c.id = a.id_cliente AND DATE(a.data_inizio) BETWEEN ? AND ?
                LEFT JOIN movimenti_cassa m ON c.id = m.id_cliente AND DATE(m.data_effettiva) BETWEEN ? AND ?
                GROUP BY c.id
                ORDER BY fatturato DESC
            """, (data_inizio, data_fine, data_inizio, data_fine)).fetchall()
            
            return [
                {
                    'cliente_id': r[0],
                    'cliente': r[1],
                    'sessioni': r[2],
                    'ore': round(r[3], 2),
                    'fatturato': round(r[4], 2),
                    'costi': round(r[5], 2),
                    'margine': round(r[4] - r[5], 2),
                    'margine_orario': round((r[4] - r[5]) / r[3], 2) if r[3] > 0 else 0
                }
                for r in rows if r[3] > 0  # Solo clienti con ore
            ]
    
    def add_slot_disponibile(self, data_slot: date, ora_inizio: str, ora_fine: str, 
                            capacita: int = 1, tipo_servizio: str = "Lezione") -> int:
        """Aggiungi uno slot disponibile."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO slot_disponibili 
                (data_slot, ora_inizio, ora_fine, capacita, tipo_servizio)
                VALUES (?, ?, ?, ?, ?)
            """, (data_slot, ora_inizio, ora_fine, capacita, tipo_servizio))
            conn.commit()
            return cursor.lastrowid
    
    def get_slot_disponibili(self, data: date) -> List[Dict[str, Any]]:
        """Recupera slot disponibili per una data."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM slot_disponibili
                WHERE data_slot = ?
                ORDER BY ora_inizio
            """, (data,)).fetchall()
            return [dict(r) for r in rows]