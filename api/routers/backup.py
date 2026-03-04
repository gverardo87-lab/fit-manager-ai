# api/routers/backup.py
"""
Endpoint Backup e Restore — gestione sicura del database.

7 endpoint:
- POST /backup/create      — backup atomico SQLite via sqlite3.backup() + SHA-256
- GET  /backup/list         — lista backup esistenti con checksum
- GET  /backup/download/{f} — scarica file backup (con protezione path traversal)
- POST /backup/restore      — restore da file upload (con safety backup + verifica)
- GET  /backup/export       — export JSON completo dati trainer (GDPR-ready, v2.0)
- POST /backup/verify/{f}   — verifica integrita' backup (SHA-256 + PRAGMA integrity_check)
- POST /backup/pre-update   — backup pre-aggiornamento app

Sicurezza:
- Tutti gli endpoint richiedono autenticazione JWT
- Path traversal prevention su download (resolve + is_relative_to)
- Restore crea safety backup + verifica SHA-256 e integrity prima di sovrascrivere
- Export filtra per trainer_id + esclude soft-deleted
- SHA-256 checksum su ogni backup (sidecar .sha256)
- PRAGMA integrity_check post-backup
"""

import hashlib
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from api.config import DATA_DIR, DATABASE_URL
from api.database import engine, get_session
from api.dependencies import get_current_trainer
from api.models.audit_log import AuditLog
from api.models.client import Client
from api.models.contract import Contract
from api.models.event import Event
from api.models.exercise import Exercise
from api.models.exercise_media import ExerciseMedia
from api.models.goal import ClientGoal
from api.models.measurement import ClientMeasurement, MeasurementValue
from api.models.movement import CashMovement
from api.models.rate import Rate
from api.models.recurring_expense import RecurringExpense
from api.models.todo import Todo
from api.models.trainer import Trainer
from api.models.workout import (
    SessionBlock,
    WorkoutExercise,
    WorkoutPlan,
    WorkoutSession,
)
from api.models.workout_log import WorkoutLog

logger = logging.getLogger("fitmanager.backup")

router = APIRouter(prefix="/backup", tags=["backup"])

BACKUP_DIR = DATA_DIR / "backups"

# Estrai path DB da DATABASE_URL (sqlite:///data/crm.db → data/crm.db)
_db_relative = DATABASE_URL.replace("sqlite:///", "")
DB_PATH = Path(_db_relative) if Path(_db_relative).is_absolute() else DATA_DIR.parent / _db_relative


# --- Response schemas ---

class BackupInfo(BaseModel):
    filename: str
    size_bytes: int
    created_at: str
    checksum: Optional[str] = None


class BackupCreateResponse(BaseModel):
    filename: str
    size_bytes: int
    checksum: str
    message: str


class BackupRestoreResponse(BaseModel):
    message: str
    safety_backup: str


class BackupVerifyResponse(BaseModel):
    filename: str
    valid: bool
    checksum_match: bool
    integrity_ok: bool
    detail: str


# --- Helpers ---

def _ensure_backup_dir() -> Path:
    """Crea la directory backups se non esiste."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR


def _safe_resolve(filename: str) -> Path:
    """
    Risolve il path del file backup con protezione path traversal.

    Bouncer: se il path risolto esce da BACKUP_DIR, solleva 400.
    """
    resolved = (BACKUP_DIR / filename).resolve()
    if not resolved.is_relative_to(BACKUP_DIR.resolve()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome file non valido",
        )
    return resolved


def _compute_sha256(file_path: Path) -> str:
    """Calcola SHA-256 di un file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_checksum_sidecar(backup_path: Path, checksum: str) -> None:
    """Scrive il checksum SHA-256 in un file sidecar .sha256."""
    sidecar = backup_path.with_suffix(".sha256")
    sidecar.write_text(f"{checksum}  {backup_path.name}\n")


def _read_checksum_sidecar(backup_path: Path) -> Optional[str]:
    """Legge il checksum dal sidecar. None se non esiste."""
    sidecar = backup_path.with_suffix(".sha256")
    if not sidecar.exists():
        return None
    content = sidecar.read_text().strip()
    return content.split()[0] if content else None


def _check_sqlite_integrity(db_path: Path) -> bool:
    """Esegue PRAGMA integrity_check su un file SQLite. True se ok."""
    try:
        conn = sqlite3.connect(str(db_path))
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()
        return result is not None and result[0] == "ok"
    except Exception:
        return False


def _create_backup_file(dest_path: Path, label: str = "backup") -> tuple[int, str]:
    """
    Crea backup atomico via sqlite3.backup() + SHA-256 + integrity check.

    Returns: (size_bytes, checksum)
    Raises HTTPException se integrity check fallisce.
    """
    source = sqlite3.connect(str(DB_PATH))
    dest = sqlite3.connect(str(dest_path))
    try:
        source.backup(dest)
    finally:
        dest.close()
        source.close()

    # Verifica integrita' del file appena creato
    if not _check_sqlite_integrity(dest_path):
        dest_path.unlink(missing_ok=True)
        logger.error("Backup %s corrotto dopo creazione — eliminato", label)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backup corrotto dopo creazione. Riprovare.",
        )

    size = dest_path.stat().st_size
    checksum = _compute_sha256(dest_path)
    _write_checksum_sidecar(dest_path, checksum)
    return size, checksum


def _apply_retention(max_backups: int = 30) -> int:
    """
    Applica retention policy: cancella backup oltre il limite.
    Non cancella safety backup (pre_restore_*, pre_update_*, pre_split_*).
    Returns: numero di backup eliminati.
    """
    regular = sorted(
        [f for f in BACKUP_DIR.glob("backup_*.sqlite")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for old in regular[max_backups:]:
        old.unlink(missing_ok=True)
        old.with_suffix(".sha256").unlink(missing_ok=True)
        removed += 1
    if removed:
        logger.info("Retention: eliminati %d backup oltre il limite di %d", removed, max_backups)
    return removed


# --- Endpoints ---

@router.post("/create", response_model=BackupCreateResponse)
def create_backup(
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Backup atomico del database SQLite.

    Usa sqlite3.backup() — copia consistente anche con connessioni aperte.
    Post-backup: PRAGMA integrity_check + SHA-256 checksum + sidecar.
    Applica retention policy (max 30 backup regolari).
    """
    _ensure_backup_dir()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sqlite"
    dest_path = BACKUP_DIR / filename

    size, checksum = _create_backup_file(dest_path)
    _apply_retention()

    logger.info(
        "Backup creato: %s (%d bytes, sha256=%s) da trainer %d",
        filename, size, checksum[:12], trainer.id,
    )

    return BackupCreateResponse(
        filename=filename,
        size_bytes=size,
        checksum=checksum,
        message=f"Backup creato e verificato: {filename}",
    )


@router.get("/list", response_model=List[BackupInfo])
def list_backups(
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Lista dei backup disponibili, ordinati dal piu' recente.

    Scansiona data/backups/ per file .sqlite. Include checksum dal sidecar.
    """
    _ensure_backup_dir()

    backups = []
    for f in sorted(BACKUP_DIR.glob("*.sqlite"), reverse=True):
        stat = f.stat()
        backups.append(BackupInfo(
            filename=f.name,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            checksum=_read_checksum_sidecar(f),
        ))

    return backups


@router.get("/download/{filename}")
def download_backup(
    filename: str,
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Scarica un file backup.

    Protezione path traversal: il filename viene risolto e verificato
    che resti dentro BACKUP_DIR.
    """
    file_path = _safe_resolve(filename)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup non trovato",
        )

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/x-sqlite3",
    )


@router.post("/restore", response_model=BackupRestoreResponse)
def restore_backup(
    file: UploadFile,
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Restore del database da file upload.

    Sicurezza:
    1. Valida magic bytes SQLite
    2. Scrive in file temporaneo e verifica integrita' (PRAGMA integrity_check)
    3. Crea safety backup del DB corrente (sqlite3.backup — include WAL data)
    4. Restore via sqlite3.backup() nel DB live (non sovrascrittura file)

    Perche' sqlite3.backup() e non file.write_bytes():
    - Su Windows il file .db e' lockato da SQLite (open connections)
    - WAL mode crea file -wal/-shm che contengono le scritture recenti
    - sqlite3.backup() copia pagina per pagina DENTRO il DB live,
      funziona anche con connessioni aperte, nessun lock file-level.
    - Dopo backup + engine.dispose(), le nuove connessioni vedono i dati ripristinati.
    """
    content = file.file.read()

    # Check magic bytes SQLite
    if not content[:16].startswith(b"SQLite format 3\x00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Il file non e' un database SQLite valido",
        )

    # Scrivi in temp e verifica integrita' PRIMA di sovrascrivere
    _ensure_backup_dir()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    temp_path = BACKUP_DIR / f"_restore_temp_{timestamp}.sqlite"
    try:
        temp_path.write_bytes(content)
        if not _check_sqlite_integrity(temp_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Il file di backup non supera il controllo di integrita'",
            )
    except HTTPException:
        temp_path.unlink(missing_ok=True)
        raise
    # temp_path NON viene eliminato — serve come sorgente per il restore

    # Safety backup del DB corrente (con checksum)
    # Usa sqlite3.backup() per catturare ANCHE i dati nel WAL (shutil.copy2 li perderebbe)
    safety_filename = f"pre_restore_{timestamp}.sqlite"
    safety_path = BACKUP_DIR / safety_filename
    source_conn = sqlite3.connect(str(DB_PATH))
    safety_conn = sqlite3.connect(str(safety_path))
    try:
        source_conn.backup(safety_conn)
    finally:
        safety_conn.close()
        source_conn.close()
    safety_checksum = _compute_sha256(safety_path)
    _write_checksum_sidecar(safety_path, safety_checksum)
    logger.info("Safety backup creato: %s (sha256=%s)", safety_filename, safety_checksum[:12])

    # ── Restore via sqlite3.backup() — sovrascrive il DB live pagina per pagina ──
    # Funziona anche con connessioni SQLAlchemy aperte (nessun lock file-level).
    try:
        restore_source = sqlite3.connect(str(temp_path))
        restore_target = sqlite3.connect(str(DB_PATH))
        try:
            restore_source.backup(restore_target)
        finally:
            restore_target.close()
            restore_source.close()
    finally:
        temp_path.unlink(missing_ok=True)

    # Chiudi il pool connessioni — le prossime request creano connessioni fresche
    # che vedranno i dati ripristinati.
    engine.dispose()

    logger.warning(
        "Database ripristinato via sqlite3.backup(): %d bytes, trainer %d. Safety: %s",
        len(content), trainer.id, safety_filename,
    )

    return BackupRestoreResponse(
        message="Database ripristinato con successo. Ricaricare la pagina per vedere i dati aggiornati.",
        safety_backup=safety_filename,
    )


@router.post("/verify/{filename}", response_model=BackupVerifyResponse)
def verify_backup(
    filename: str,
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Verifica integrita' di un backup esistente.

    1. Ricalcola SHA-256 e confronta con sidecar
    2. Esegue PRAGMA integrity_check sul file
    """
    file_path = _safe_resolve(filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Backup non trovato")

    # SHA-256
    actual_checksum = _compute_sha256(file_path)
    expected_checksum = _read_checksum_sidecar(file_path)
    checksum_match = expected_checksum is not None and actual_checksum == expected_checksum

    # Integrity
    integrity_ok = _check_sqlite_integrity(file_path)

    valid = checksum_match and integrity_ok
    details = []
    if not checksum_match:
        if expected_checksum is None:
            details.append("nessun checksum sidecar trovato")
        else:
            details.append(f"checksum mismatch: atteso {expected_checksum[:12]}..., trovato {actual_checksum[:12]}...")
    if not integrity_ok:
        details.append("PRAGMA integrity_check fallito")
    if valid:
        details.append("backup integro e verificato")

    return BackupVerifyResponse(
        filename=filename,
        valid=valid,
        checksum_match=checksum_match,
        integrity_ok=integrity_ok,
        detail="; ".join(details),
    )


@router.post("/pre-update", response_model=BackupCreateResponse)
def create_pre_update_backup(
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Backup pre-aggiornamento app.

    Chiamato dall'updater prima di applicare aggiornamenti.
    Salvato come pre_update_{version}_{timestamp}.sqlite.
    """
    _ensure_backup_dir()

    from api.main import app
    version = getattr(app, "version", "unknown").replace(".", "_")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"pre_update_{version}_{timestamp}.sqlite"
    dest_path = BACKUP_DIR / filename

    size, checksum = _create_backup_file(dest_path, label="pre-update")

    logger.info(
        "Pre-update backup: %s (%d bytes, sha256=%s) da trainer %d",
        filename, size, checksum[:12], trainer.id,
    )

    return BackupCreateResponse(
        filename=filename,
        size_bytes=size,
        checksum=checksum,
        message=f"Backup pre-aggiornamento creato: {filename}",
    )


@router.get("/export")
def export_trainer_data(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Export JSON completo di TUTTI i dati del trainer (GDPR data portability).

    v2.0: 17 entita' business in ordine FK-safe per restore.
    Esclude: record soft-deleted, esercizi builtin, tassonomia (catalog data).
    Filtra per trainer_id (multi-tenancy).
    """
    tid = trainer.id

    def _serialize(records: list) -> list:
        """Converte SQLModel records in dicts serializzabili JSON."""
        result = []
        for r in records:
            d = r.model_dump()
            for k, v in d.items():
                if isinstance(v, (datetime,)):
                    d[k] = v.isoformat()
                elif hasattr(v, "isoformat"):
                    d[k] = v.isoformat()
            result.append(d)
        return result

    # ── 1. Clienti ──
    clients = session.exec(
        select(Client).where(Client.trainer_id == tid, Client.deleted_at == None)  # noqa: E711
    ).all()

    # ── 2. Contratti ──
    contracts = session.exec(
        select(Contract).where(Contract.trainer_id == tid, Contract.deleted_at == None)  # noqa: E711
    ).all()
    contract_ids = [c.id for c in contracts]

    # ── 3. Rate (Deep IDOR via contratto) ──
    rates: list = []
    if contract_ids:
        rates = session.exec(
            select(Rate).where(
                Rate.id_contratto.in_(contract_ids),  # type: ignore[union-attr]
                Rate.deleted_at == None,  # noqa: E711
            )
        ).all()

    # ── 4. Eventi ──
    events = session.exec(
        select(Event).where(Event.trainer_id == tid, Event.deleted_at == None)  # noqa: E711
    ).all()

    # ── 5. Movimenti cassa ──
    movements = session.exec(
        select(CashMovement).where(CashMovement.trainer_id == tid, CashMovement.deleted_at == None)  # noqa: E711
    ).all()

    # ── 6. Spese ricorrenti ──
    expenses = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.trainer_id == tid,
            RecurringExpense.deleted_at == None,  # noqa: E711
        )
    ).all()

    # ── 7. Schede allenamento ──
    plans = session.exec(
        select(WorkoutPlan).where(WorkoutPlan.trainer_id == tid, WorkoutPlan.deleted_at == None)  # noqa: E711
    ).all()
    plan_ids = [p.id for p in plans]

    # ── 8. Sessioni scheda (Deep IDOR via plan) ──
    sessions_list: list = []
    if plan_ids:
        sessions_list = session.exec(
            select(WorkoutSession).where(
                WorkoutSession.id_scheda.in_(plan_ids),  # type: ignore[union-attr]
            )
        ).all()
    session_ids = [s.id for s in sessions_list]

    # ── 9. Blocchi sessione (Deep IDOR via session) ──
    blocks: list = []
    if session_ids:
        blocks = session.exec(
            select(SessionBlock).where(
                SessionBlock.id_sessione.in_(session_ids),  # type: ignore[union-attr]
            )
        ).all()

    # ── 10. Esercizi sessione (Deep IDOR via session) ──
    workout_exercises: list = []
    if session_ids:
        workout_exercises = session.exec(
            select(WorkoutExercise).where(
                WorkoutExercise.id_sessione.in_(session_ids),  # type: ignore[union-attr]
            )
        ).all()

    # ── 11. Log allenamenti ──
    workout_logs = session.exec(
        select(WorkoutLog).where(WorkoutLog.trainer_id == tid, WorkoutLog.deleted_at == None)  # noqa: E711
    ).all()

    # ── 12. Misurazioni cliente ──
    measurements = session.exec(
        select(ClientMeasurement).where(
            ClientMeasurement.trainer_id == tid,
            ClientMeasurement.deleted_at == None,  # noqa: E711
        )
    ).all()
    measurement_ids = [m.id for m in measurements]

    # ── 13. Valori misurazione (Deep IDOR via measurement) ──
    values: list = []
    if measurement_ids:
        values = session.exec(
            select(MeasurementValue).where(
                MeasurementValue.id_misurazione.in_(measurement_ids),  # type: ignore[union-attr]
            )
        ).all()

    # ── 14. Obiettivi cliente ──
    goals = session.exec(
        select(ClientGoal).where(
            ClientGoal.trainer_id == tid,
            ClientGoal.deleted_at == None,  # noqa: E711
        )
    ).all()

    # ── 15. Todos ──
    todos = session.exec(
        select(Todo).where(Todo.trainer_id == tid, Todo.deleted_at == None)  # noqa: E711
    ).all()

    # ── 16. Esercizi custom (solo trainer, no builtin) ──
    custom_exercises = session.exec(
        select(Exercise).where(
            Exercise.trainer_id == tid,
            Exercise.deleted_at == None,  # noqa: E711
        )
    ).all()
    custom_exercise_ids = [e.id for e in custom_exercises]

    # ── 16b. Media esercizi custom ──
    custom_media: list = []
    if custom_exercise_ids:
        custom_media = session.exec(
            select(ExerciseMedia).where(
                ExerciseMedia.exercise_id.in_(custom_exercise_ids),  # type: ignore[union-attr]
            )
        ).all()

    # ── 17. Audit log (immutabile, completo) ──
    audit = session.exec(
        select(AuditLog).where(AuditLog.trainer_id == tid)
    ).all()

    # ── Costruisci export ──
    data = {
        "clienti": _serialize(clients),
        "contratti": _serialize(contracts),
        "rate": _serialize(rates),
        "eventi": _serialize(events),
        "movimenti_cassa": _serialize(movements),
        "spese_ricorrenti": _serialize(expenses),
        "schede_allenamento": _serialize(plans),
        "sessioni_scheda": _serialize(sessions_list),
        "blocchi_sessione": _serialize(blocks),
        "esercizi_sessione": _serialize(workout_exercises),
        "allenamenti_eseguiti": _serialize(workout_logs),
        "misurazioni_cliente": _serialize(measurements),
        "valori_misurazione": _serialize(values),
        "obiettivi_cliente": _serialize(goals),
        "todos": _serialize(todos),
        "esercizi_custom": _serialize(custom_exercises),
        "esercizi_custom_media": _serialize(custom_media),
        "audit_log": _serialize(audit),
    }

    counts = {k: len(v) for k, v in data.items()}

    return {
        "version": "2.0",
        "trainer": {
            "id": trainer.id,
            "email": trainer.email,
            "nome": trainer.nome,
            "cognome": trainer.cognome,
        },
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "data": data,
    }
