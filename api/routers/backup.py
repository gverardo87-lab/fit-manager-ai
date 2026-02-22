# api/routers/backup.py
"""
Endpoint Backup e Restore — gestione sicura del database.

5 endpoint:
- POST /backup/create      — backup atomico SQLite via sqlite3.backup()
- GET  /backup/list         — lista backup esistenti
- GET  /backup/download/{f} — scarica file backup (con protezione path traversal)
- POST /backup/restore      — restore da file upload (con safety backup)
- GET  /backup/export       — export JSON dati trainer (GDPR-ready)

Sicurezza:
- Tutti gli endpoint richiedono autenticazione JWT
- Path traversal prevention su download (resolve + is_relative_to)
- Restore crea safety backup prima di sovrascrivere
- Export filtra per trainer_id + esclude soft-deleted
"""

import json
import logging
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from api.config import DATA_DIR
from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.client import Client
from api.models.contract import Contract
from api.models.event import Event
from api.models.movement import CashMovement
from api.models.rate import Rate
from api.models.recurring_expense import RecurringExpense
from api.models.trainer import Trainer

logger = logging.getLogger("fitmanager.backup")

router = APIRouter(prefix="/backup", tags=["backup"])

BACKUP_DIR = DATA_DIR / "backups"
DB_PATH = DATA_DIR / "crm.db"


# --- Response schemas ---

class BackupInfo(BaseModel):
    filename: str
    size_bytes: int
    created_at: str


class BackupCreateResponse(BaseModel):
    filename: str
    size_bytes: int
    message: str


class BackupRestoreResponse(BaseModel):
    message: str
    safety_backup: str


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


# --- Endpoints ---

@router.post("/create", response_model=BackupCreateResponse)
def create_backup(
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Backup atomico del database SQLite.

    Usa sqlite3.backup() — copia consistente anche con connessioni aperte.
    Il file viene salvato in data/backups/backup_{timestamp}.sqlite.
    """
    _ensure_backup_dir()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sqlite"
    dest_path = BACKUP_DIR / filename

    # sqlite3.backup() e' atomico — il file risultante e' sempre consistente
    source = sqlite3.connect(str(DB_PATH))
    dest = sqlite3.connect(str(dest_path))
    try:
        source.backup(dest)
    finally:
        dest.close()
        source.close()

    size = dest_path.stat().st_size
    logger.info("Backup creato: %s (%d bytes) da trainer %d", filename, size, trainer.id)

    return BackupCreateResponse(
        filename=filename,
        size_bytes=size,
        message=f"Backup creato: {filename}",
    )


@router.get("/list", response_model=List[BackupInfo])
def list_backups(
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Lista dei backup disponibili, ordinati dal piu' recente.

    Scansiona data/backups/ per file .sqlite.
    """
    _ensure_backup_dir()

    backups = []
    for f in sorted(BACKUP_DIR.glob("*.sqlite"), reverse=True):
        stat = f.stat()
        backups.append(BackupInfo(
            filename=f.name,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
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
    1. Valida che il file sia un database SQLite (magic bytes)
    2. Crea un safety backup prima di sovrascrivere
    3. Copia il file upload come nuovo crm.db

    NOTA: dopo il restore, il server va riavviato per ricaricare le connessioni.
    """
    # Bouncer: valida content type (best-effort, il vero check e' sui magic bytes)
    content = file.file.read()

    # Check magic bytes SQLite: "SQLite format 3\000"
    if not content[:16].startswith(b"SQLite format 3\x00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Il file non e' un database SQLite valido",
        )

    # Safety backup prima di sovrascrivere
    _ensure_backup_dir()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safety_filename = f"pre_restore_{timestamp}.sqlite"
    safety_path = BACKUP_DIR / safety_filename

    shutil.copy2(str(DB_PATH), str(safety_path))
    logger.info("Safety backup creato: %s", safety_filename)

    # Sovrascrivi il database
    DB_PATH.write_bytes(content)
    logger.warning(
        "Database ripristinato da upload (%d bytes) da trainer %d. "
        "Safety backup: %s. Riavviare il server.",
        len(content), trainer.id, safety_filename,
    )

    return BackupRestoreResponse(
        message="Database ripristinato. Riavviare il server per applicare.",
        safety_backup=safety_filename,
    )


@router.get("/export")
def export_trainer_data(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Export JSON di tutti i dati del trainer (GDPR data portability).

    Esporta: clienti, contratti, rate, eventi, movimenti, spese ricorrenti.
    Esclude record soft-deleted (deleted_at IS NOT NULL).
    Filtra per trainer_id (multi-tenancy).
    """
    tid = trainer.id

    # Clienti
    clients = session.exec(
        select(Client).where(Client.trainer_id == tid, Client.deleted_at == None)  # noqa: E711
    ).all()

    # Contratti
    contracts = session.exec(
        select(Contract).where(Contract.trainer_id == tid, Contract.deleted_at == None)  # noqa: E711
    ).all()

    # Rate — IDOR via contratti del trainer
    contract_ids = [c.id for c in contracts]
    rates = []
    if contract_ids:
        rates = session.exec(
            select(Rate).where(
                Rate.id_contratto.in_(contract_ids),  # type: ignore[union-attr]
                Rate.deleted_at == None,  # noqa: E711
            )
        ).all()

    # Eventi
    events = session.exec(
        select(Event).where(Event.trainer_id == tid, Event.deleted_at == None)  # noqa: E711
    ).all()

    # Movimenti cassa
    movements = session.exec(
        select(CashMovement).where(CashMovement.trainer_id == tid, CashMovement.deleted_at == None)  # noqa: E711
    ).all()

    # Spese ricorrenti
    expenses = session.exec(
        select(RecurringExpense).where(
            RecurringExpense.trainer_id == tid,
            RecurringExpense.deleted_at == None,  # noqa: E711
        )
    ).all()

    def _serialize(records: list) -> list:
        """Converte SQLModel records in dicts serializzabili JSON."""
        result = []
        for r in records:
            d = r.model_dump()
            # Converti date/datetime in ISO string
            for k, v in d.items():
                if isinstance(v, (datetime,)):
                    d[k] = v.isoformat()
                elif hasattr(v, "isoformat"):
                    d[k] = v.isoformat()
            result.append(d)
        return result

    export = {
        "trainer": {
            "id": trainer.id,
            "email": trainer.email,
            "nome": trainer.nome,
            "cognome": trainer.cognome,
        },
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "data": {
            "clienti": _serialize(clients),
            "contratti": _serialize(contracts),
            "rate": _serialize(rates),
            "eventi": _serialize(events),
            "movimenti_cassa": _serialize(movements),
            "spese_ricorrenti": _serialize(expenses),
        },
    }

    return export
