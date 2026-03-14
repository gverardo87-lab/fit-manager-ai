# api/routers/client_avatar.py
"""
Client Avatar endpoints — profilo composito per cliente.

GET  /clients/{client_id}/avatar  → singolo avatar
POST /clients/avatars             → batch (max 50)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.schemas.client_avatar import (
    ClientAvatar,
    ClientAvatarBatchRequest,
    ClientAvatarBatchResponse,
)
from api.services.client_avatar import build_avatar, build_avatars_batch

router = APIRouter(prefix="/clients", tags=["client-avatar"])


@router.get("/{client_id}/avatar", response_model=ClientAvatar)
def get_client_avatar(
    client_id: int,
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Avatar composito per un singolo cliente."""
    avatar = build_avatar(session, trainer.id, client_id)
    if not avatar:
        raise HTTPException(404, "Cliente non trovato")
    return avatar


@router.post("/avatars", response_model=ClientAvatarBatchResponse)
def get_client_avatars_batch(
    body: ClientAvatarBatchRequest,
    session: Session = Depends(get_session),
    trainer: Trainer = Depends(get_current_trainer),
):
    """Avatar compositi per un batch di clienti (max 50)."""
    avatars = build_avatars_batch(session, trainer.id, body.client_ids)
    return ClientAvatarBatchResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        avatars=avatars,
    )
