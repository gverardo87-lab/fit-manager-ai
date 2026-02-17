"""
BaseRepository - Shared database connection logic for all repositories

FASE 2 REFACTORING: Repository Pattern - Base Abstract Class

Responsabilità:
- Connection management (context manager con transazioni)
- Row to dict mapping
- Error handling centralizzato
- Foreign keys enforcement
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any
from datetime import date, datetime
import json

from core.error_handler import logger

# Database file path (default)
DB_FILE = Path(__file__).resolve().parents[2] / "data" / "crm.db"


class BaseRepository:
    """
    Abstract base class per tutti i repository.
    
    Fornisce:
    - _connect(): context manager per gestione connection + transazioni
    - _row_to_dict(): converte sqlite3.Row in dict
    - _serialize_json(): converte dict Python in JSON per colonne json
    - _deserialize_json(): converte JSON in dict Python
    
    Pattern:
        class MyRepository(BaseRepository):
            def get_by_id(self, id: int) -> Optional[MyModel]:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM table WHERE id = ?", (id,))
                    row = cursor.fetchone()
                    return MyModel(**self._row_to_dict(row)) if row else None
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Inizializza repository con path al database.
        
        Args:
            db_path: Path al file SQLite. Se None, usa DB_FILE default
        """
        self.db_path = db_path or DB_FILE
        self._ensure_db_exists()
    
    def _ensure_db_exists(self) -> None:
        """Crea directory data/ se non esiste"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def _connect(self):
        """
        Context manager per connessione SQLite con gestione transazioni.
        
        Features:
        - Row factory: accesso colonne per nome
        - Foreign keys enforced
        - Auto commit on success
        - Auto rollback on exception (con logging)
        - Auto close connection
        
        ROLLBACK AUTOMATICO: Su qualsiasi Exception durante yield, esegue rollback
        e propaga l'eccezione al decoratore @safe_operation del metodo chiamante.
        
        Usage:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO ...")
                # commit automatico se nessuna eccezione
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Accesso colonne per nome
        conn.execute("PRAGMA foreign_keys = ON")  # Enforce referential integrity
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"🔄 DB Transaction rollback: {type(e).__name__} - {str(e)[:100]}")
            raise  # Re-raise per @safe_operation decorator
        finally:
            conn.close()
    
    @contextmanager
    def get_connection(self):
        """
        Public method for accessing database connection (temporary workaround).
        
        WARNING:
            Use this only for complex dynamic queries that don't fit
            repository pattern. Prefer creating specific repository methods.
        
        Usage:
            with repo.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ...")
        """
        with self._connect() as conn:
            yield conn
    
    def _row_to_dict(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        """
        Converte sqlite3.Row in dict Python.
        
        Args:
            row: sqlite3.Row da convertire (o None)
        
        Returns:
            Dict con chiavi = nomi colonne, valori = valori colonne
            None se row è None
        
        Note:
            - Gestisce automaticamente valori NULL
            - Preserva tipi Python (int, float, str, bytes)
        """
        if row is None:
            return None
        return {key: row[key] for key in row.keys()}
    
    def _serialize_json(self, data: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Converte dict Python in JSON string per storage nel DB.
        
        Args:
            data: Dict da serializzare (o None)
        
        Returns:
            JSON string o None
        
        Note:
            - Gestisce date/datetime convertendoli in isoformat
            - Usa ensure_ascii=False per supporto unicode
        """
        if data is None:
            return None
        
        def json_default(obj):
            """Custom JSON encoder per date/datetime"""
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        return json.dumps(data, default=json_default, ensure_ascii=False)
    
    def _deserialize_json(self, json_str: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Converte JSON string in dict Python.
        
        Args:
            json_str: JSON string da deserializzare (o None)
        
        Returns:
            Dict Python o None
        
        Note:
            - Ritorna None se json_str è None o ''
            - Gestisce malformed JSON ritornando dict vuoto
        """
        if not json_str:
            return None
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {}
    
    def _execute_query(
        self,
        query: str,
        params: tuple = (),
        fetch: str = "all"
    ) -> Optional[list | dict]:
        """
        Utility per eseguire query SELECT con boilerplate ridotto.
        
        Args:
            query: SQL query da eseguire
            params: Parametri per query parametrizzata
            fetch: 'one' | 'all' | 'none'
        
        Returns:
            - fetch='one': dict (singola riga) o None
            - fetch='all': list di dict
            - fetch='none': None (per INSERT/UPDATE/DELETE)
        
        Usage:
            # Single row
            user = self._execute_query("SELECT * FROM users WHERE id = ?", (1,), fetch='one')
            
            # Multiple rows
            users = self._execute_query("SELECT * FROM users WHERE active = ?", (True,), fetch='all')
            
            # No result needed
            self._execute_query("DELETE FROM users WHERE id = ?", (1,), fetch='none')
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch == 'one':
                row = cursor.fetchone()
                return self._row_to_dict(row)
            elif fetch == 'all':
                rows = cursor.fetchall()
                return [self._row_to_dict(r) for r in rows]
            else:  # fetch == 'none'
                return None
    
    def _get_last_insert_id(self, cursor: sqlite3.Cursor) -> int:
        """
        Get ID dell'ultima riga inserita.
        
        Args:
            cursor: Cursor SQLite dopo INSERT
        
        Returns:
            Last inserted row ID
        """
        return cursor.lastrowid
