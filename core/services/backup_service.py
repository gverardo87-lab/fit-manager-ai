# core/services/backup_service.py
"""
BackupService - Backup e ripristino database crittografato.

Crea archivi .fitbackup (ZIP crittografato con Fernet/AES-128-CBC).
Formato file: MAGIC_BYTES (8) + SALT (16) + Fernet token (variabile).

Privacy-first: tutto locale, password mai salvata su disco.
"""

import sqlite3
import zipfile
import hashlib
import os
import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from core.config import DB_CRM_PATH, DATA_DIR
from core.models import BackupManifest
from core.error_handler import logger, safe_operation, ErrorSeverity


# Identificatore file .fitbackup (ASCII: "FITMGRBK")
MAGIC_BYTES = b"FITMGRBK"
MAGIC_LEN = 8
SALT_LEN = 16
PBKDF2_ITERATIONS = 100_000
MAX_BACKUP_SIZE = 100 * 1024 * 1024  # 100 MB
MIN_PASSWORD_LEN = 4


class BackupService:
    """
    Gestisce backup e ripristino del database CRM.

    Formato .fitbackup:
        [8 bytes magic "FITMGRBK"] + [16 bytes salt] + [Fernet encrypted ZIP]

    Il ZIP interno contiene:
        - crm.db (copia del database)
        - manifest.json (metadati: data, checksum, tabelle)
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DB_CRM_PATH

    # ── PUBLIC METHODS ──────────────────────────────────────────

    @safe_operation(
        operation_name="Crea Backup",
        severity=ErrorSeverity.HIGH,
        fallback_return=None
    )
    def create_backup(self, password: str) -> Optional[Tuple[bytes, BackupManifest]]:
        """
        Crea un backup crittografato del database.

        Flusso:
        1. Copia sicura del DB con SQLite backup API
        2. Calcola checksum SHA-256
        3. Conta righe per tabella
        4. Crea manifest + ZIP in memoria
        5. Crittografa con Fernet (password -> PBKDF2 -> AES key)

        Returns:
            Tuple (encrypted_bytes, manifest) oppure None se errore
        """
        self._validate_password(password)

        # 1. Copia sicura del database
        db_bytes = self._safe_db_copy()

        # 2. Checksum
        checksum = self._compute_checksum(db_bytes)

        # 3. Statistiche tabelle
        tables = self._get_table_stats()
        total_records = sum(tables.values())

        # 4. Manifest
        manifest = BackupManifest(
            backup_date=datetime.now(),
            db_checksum=checksum,
            db_size_bytes=len(db_bytes),
            tables=tables,
            total_records=total_records
        )

        # 5. Crea ZIP in memoria
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("crm.db", db_bytes)
            zf.writestr("manifest.json", manifest.model_dump_json(indent=2))
        zip_data = zip_buffer.getvalue()

        # 6. Crittografa
        salt = os.urandom(SALT_LEN)
        key = self._derive_key(password, salt)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(zip_data)

        # Formato finale: MAGIC + SALT + ENCRYPTED
        result_bytes = MAGIC_BYTES + salt + encrypted

        logger.info(
            f"Backup creato: {self._format_size(len(result_bytes))}, "
            f"{total_records} record, {len(tables)} tabelle"
        )

        return result_bytes, manifest

    def validate_backup(self, data: bytes, password: str) -> Optional[BackupManifest]:
        """
        Valida un file .fitbackup e ritorna il manifest.

        NON decorato con @safe_operation: le ValueError vengono propagate
        alla UI per mostrare messaggi di errore specifici (password sbagliata,
        file corrotto, checksum non valido, ecc.)

        Returns:
            BackupManifest se valido

        Raises:
            ValueError: con messaggio specifico per ogni tipo di errore
        """
        # Dimensione
        if len(data) > MAX_BACKUP_SIZE:
            raise ValueError("Il file supera la dimensione massima (100 MB)")

        if len(data) < MAGIC_LEN + SALT_LEN + 1:
            raise ValueError("Il file e' troppo piccolo per essere un backup valido")

        # Magic bytes
        if data[:MAGIC_LEN] != MAGIC_BYTES:
            raise ValueError("Il file non e' un backup FitManager valido")

        # Estrai salt + dati crittografati
        salt = data[MAGIC_LEN:MAGIC_LEN + SALT_LEN]
        encrypted = data[MAGIC_LEN + SALT_LEN:]

        # Decrittografa
        key = self._derive_key(password, salt)
        fernet = Fernet(key)
        try:
            zip_data = fernet.decrypt(encrypted)
        except InvalidToken:
            raise ValueError("Password non corretta o file corrotto")

        # Estrai ZIP
        zip_buffer = BytesIO(zip_data)
        try:
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                names = zf.namelist()
                if 'crm.db' not in names or 'manifest.json' not in names:
                    raise ValueError("Archivio backup incompleto (mancano crm.db o manifest)")

                manifest_json = zf.read("manifest.json")
                db_data = zf.read("crm.db")
        except zipfile.BadZipFile:
            raise ValueError("Il file di backup e' danneggiato")

        # Parse manifest
        manifest = BackupManifest.model_validate_json(manifest_json)

        # Verifica checksum
        actual_checksum = self._compute_checksum(db_data)
        if actual_checksum != manifest.db_checksum:
            raise ValueError(
                "Checksum non corrisponde: il database nel backup potrebbe essere corrotto"
            )

        # Verifica SQLite valido
        self._validate_sqlite(db_data)

        logger.info(
            f"Backup validato: {manifest.backup_date.isoformat()}, "
            f"{manifest.total_records} record"
        )

        return manifest

    @safe_operation(
        operation_name="Ripristina Backup",
        severity=ErrorSeverity.CRITICAL,
        fallback_return=False
    )
    def restore_backup(self, data: bytes, password: str) -> bool:
        """
        Ripristina il database dal backup.

        Flusso:
        1. Valida il backup completo
        2. Crea copia di sicurezza (crm_pre_restore.db.bak)
        3. Decrittografa e sovrascrive crm.db

        Returns:
            True se ripristino riuscito
        """
        # 1. Validazione completa
        manifest = self.validate_backup(data, password)
        if manifest is None:
            raise ValueError("Validazione backup fallita")

        # 2. Copia di sicurezza del DB attuale
        safety_path = DATA_DIR / "crm_pre_restore.db.bak"
        if self.db_path.exists():
            shutil.copy2(str(self.db_path), str(safety_path))
            logger.info(f"Copia di sicurezza creata: {safety_path}")

        # 3. Decrittografa e estrai crm.db
        salt = data[MAGIC_LEN:MAGIC_LEN + SALT_LEN]
        encrypted = data[MAGIC_LEN + SALT_LEN:]
        key = self._derive_key(password, salt)
        fernet = Fernet(key)
        zip_data = fernet.decrypt(encrypted)

        zip_buffer = BytesIO(zip_data)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            db_data = zf.read("crm.db")

        # 4. Sovrascrive crm.db
        self.db_path.write_bytes(db_data)

        logger.info(
            f"Database ripristinato da backup del {manifest.backup_date.isoformat()}, "
            f"{manifest.total_records} record"
        )

        return True

    @safe_operation(
        operation_name="Statistiche DB",
        severity=ErrorSeverity.LOW,
        fallback_return={}
    )
    def get_current_db_stats(self) -> Dict[str, int]:
        """Ritorna conteggio righe per tabella del DB corrente."""
        return self._get_table_stats()

    def get_db_info(self) -> Dict:
        """Ritorna info sul file DB (path, dimensione, ultima modifica)."""
        if not self.db_path.exists():
            return {"exists": False}
        stat = self.db_path.stat()
        return {
            "exists": True,
            "path": str(self.db_path),
            "size_bytes": stat.st_size,
            "size_display": self._format_size(stat.st_size),
            "last_modified": datetime.fromtimestamp(stat.st_mtime),
        }

    # ── PRIVATE METHODS ─────────────────────────────────────────

    def _validate_password(self, password: str) -> None:
        """Verifica requisiti minimi password."""
        if not password or len(password) < MIN_PASSWORD_LEN:
            raise ValueError(
                f"La password deve avere almeno {MIN_PASSWORD_LEN} caratteri"
            )

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Deriva chiave crittografica da password con PBKDF2.

        100k iterazioni rendono il brute-force costoso.
        Il salt random previene attacchi rainbow table.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        key_bytes = kdf.derive(password.encode('utf-8'))
        return base64.urlsafe_b64encode(key_bytes)

    def _compute_checksum(self, data: bytes) -> str:
        """SHA-256 hex digest."""
        return hashlib.sha256(data).hexdigest()

    def _safe_db_copy(self) -> bytes:
        """
        Copia sicura del database con l'API backup di SQLite.

        L'API backup garantisce uno snapshot consistente anche se
        l'applicazione sta scrivendo nel DB contemporaneamente.
        Un semplice file read potrebbe copiare uno stato parziale.
        """
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            source = sqlite3.connect(str(self.db_path))
            dest = sqlite3.connect(tmp_path)
            source.backup(dest)
            dest.close()
            source.close()

            return Path(tmp_path).read_bytes()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _get_table_stats(self) -> Dict[str, int]:
        """Conta le righe per ogni tabella utente (escluse tabelle di sistema)."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = {}
        for (name,) in cursor.fetchall():
            try:
                cursor.execute(f'SELECT COUNT(*) FROM [{name}]')
                tables[name] = cursor.fetchone()[0]
            except sqlite3.Error:
                tables[name] = -1
        conn.close()
        return tables

    def _validate_sqlite(self, db_data: bytes) -> None:
        """Verifica che i bytes siano un database SQLite valido con le tabelle essenziali."""
        if not db_data[:16].startswith(b'SQLite format 3'):
            raise ValueError("Il file nel backup non e' un database SQLite valido")

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp.write(db_data)
            tmp_path = tmp.name

        try:
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [row[0] for row in cursor.fetchall()]
            conn.close()

            essential = ['clienti', 'contratti', 'agenda', 'movimenti_cassa']
            missing = [t for t in essential if t not in table_names]
            if missing:
                raise ValueError(
                    f"Database non valido: tabelle mancanti: {', '.join(missing)}"
                )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Formatta dimensione file in formato leggibile."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
