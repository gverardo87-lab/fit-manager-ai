# api/routers/public_portal.py
"""
Portale Clienti Self-Service — Anamnesi.

3 endpoint:
  POST /api/clients/{client_id}/share-anamnesi  [JWT trainer]  — genera token monouso
  GET  /api/public/anamnesi/validate             [pubblico]     — valida token + info form
  POST /api/public/anamnesi/submit               [pubblico]     — salva anamnesi + invalida token

Architettura sicurezza:
  - Token UUID4 (122 bit entropia), monouso (used_at), 48h scadenza
  - Endpoint pubblici: rate limiting IP-based in-process (10 req/min, 30 req/h)
  - Nome cliente mascherato: "Marco R." — nessun dato sensibile senza token valido
  - Feature flag: PUBLIC_PORTAL_ENABLED=false → tutti gli endpoint 404
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session, select

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.client import Client
from api.models.share_token import ShareToken
from api.models.trainer import Trainer
from api.schemas.public import (
    AnamnesiSubmitRequest,
    AnamnesiSubmitResponse,
    AnamnesiValidateResponse,
    ShareTokenResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["public-portal"])

# ── Feature flag ────────────────────────────────────────────────────────────

def _is_enabled() -> bool:
    return os.getenv("PUBLIC_PORTAL_ENABLED", "false").strip().lower() in ("true", "1", "yes")


def _require_enabled() -> None:
    if not _is_enabled():
        raise HTTPException(status_code=404, detail="Not Found")


# ── Rate limiting in-process (zero dipendenze) ──────────────────────────────

_rate_log: dict[str, list[float]] = defaultdict(list)
_WINDOW_MIN = 60.0    # 1 minuto in secondi
_WINDOW_HOUR = 3600.0
_MAX_PER_MIN = 10
_MAX_PER_HOUR = 30


def _check_rate_limit(request: Request) -> None:
    """Rate limiting IP-based leggero per endpoint pubblici."""
    ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc).timestamp()

    timestamps = _rate_log[ip]

    # Pulizia: mantieni solo ultimi 60 minuti
    timestamps[:] = [t for t in timestamps if now - t < _WINDOW_HOUR]

    per_min = sum(1 for t in timestamps if now - t < _WINDOW_MIN)
    per_hour = len(timestamps)

    if per_min >= _MAX_PER_MIN or per_hour >= _MAX_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Troppe richieste. Riprova tra qualche minuto.",
        )

    timestamps.append(now)


# ── Helper: bouncer token pubblico ───────────────────────────────────────────

def _get_valid_token(session: Session, token: str) -> ShareToken:
    """
    Valida token: esiste, non scaduto, non usato, cliente attivo.
    404 in tutti i casi di errore (nessun info leaking).
    """
    share = session.exec(
        select(ShareToken).where(ShareToken.token == token)
    ).first()

    if not share:
        raise HTTPException(404, "Link non valido")

    now = datetime.now(timezone.utc)
    # expires_at potrebbe essere naive (SQLite) — normalizziamo
    expires = share.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now > expires:
        raise HTTPException(404, "Link scaduto")

    if share.used_at is not None:
        raise HTTPException(404, "Link gia' utilizzato")

    # Cliente ancora attivo e non cancellato
    client = session.get(Client, share.client_id)
    if not client or client.deleted_at is not None:
        raise HTTPException(404, "Link non valido")

    return share


# ── ENDPOINT 1: Generazione token (protetto, JWT trainer) ───────────────────

@router.post(
    "/clients/{client_id}/share-anamnesi",
    response_model=ShareTokenResponse,
    summary="Genera link monouso per anamnesi self-service",
)
def create_share_token(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
) -> ShareTokenResponse:
    _require_enabled()

    # Bouncer: il cliente deve appartenere al trainer (deep IDOR)
    client = session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.trainer_id == trainer.id,
            Client.deleted_at == None,  # noqa: E711
        )
    ).first()
    if not client:
        raise HTTPException(404, "Cliente non trovato")

    # Invalida eventuali token precedenti non usati per stesso client+scope
    old_tokens = session.exec(
        select(ShareToken).where(
            ShareToken.trainer_id == trainer.id,
            ShareToken.client_id == client_id,
            ShareToken.scope == "anamnesi",
            ShareToken.used_at == None,  # noqa: E711
        )
    ).all()
    for old in old_tokens:
        session.delete(old)

    now = datetime.now(timezone.utc)
    share = ShareToken(
        token=str(uuid4()),
        trainer_id=trainer.id,
        client_id=client_id,
        scope="anamnesi",
        created_at=now,
        expires_at=now + timedelta(hours=48),
    )
    session.add(share)
    session.commit()
    session.refresh(share)

    logger.info(
        "Share token generato: trainer=%d client=%d scope=anamnesi",
        trainer.id, client_id,
    )

    return ShareTokenResponse(
        token=share.token,
        url=f"/public/anamnesi/{share.token}",
        expires_at=share.expires_at,
        client_name=f"{client.nome} {client.cognome}",
    )


# ── ENDPOINT 2: Validazione token (pubblico) ────────────────────────────────

@router.get(
    "/public/anamnesi/validate",
    response_model=AnamnesiValidateResponse,
    summary="Valida token e ritorna info per il form pubblico",
)
def validate_anamnesi_token(
    token: str = Query(..., min_length=36, max_length=36),
    request: Request = None,
    session: Session = Depends(get_session),
) -> AnamnesiValidateResponse:
    _require_enabled()
    _check_rate_limit(request)

    share = _get_valid_token(session, token)

    client = session.get(Client, share.client_id)
    trainer = session.get(Trainer, share.trainer_id)

    # Mascheramento cognome: "Marco R."
    cognome_iniziale = (client.cognome[0] + ".") if client.cognome else ""
    client_name = f"{client.nome} {cognome_iniziale}".strip()

    trainer_cognome_iniziale = (trainer.cognome[0] + ".") if trainer.cognome else ""
    trainer_name = f"{trainer.nome} {trainer_cognome_iniziale}".strip()

    has_existing = bool(client.anamnesi_json)

    return AnamnesiValidateResponse(
        client_name=client_name,
        trainer_name=trainer_name,
        has_existing=has_existing,
        scope=share.scope,
    )


# ── ENDPOINT 3: Submit anamnesi (pubblico) ───────────────────────────────────

@router.post(
    "/public/anamnesi/submit",
    response_model=AnamnesiSubmitResponse,
    summary="Salva anamnesi compilata dal cliente e invalida il token",
)
def submit_anamnesi(
    body: AnamnesiSubmitRequest,
    request: Request = None,
    session: Session = Depends(get_session),
) -> AnamnesiSubmitResponse:
    _require_enabled()
    _check_rate_limit(request)

    share = _get_valid_token(session, body.token)
    client = session.get(Client, share.client_id)

    # Salva anamnesi sul cliente
    client.anamnesi_json = json.dumps(body.anamnesi, ensure_ascii=False)

    # Invalida token (monouso)
    share.used_at = datetime.now(timezone.utc)

    session.add(client)
    session.add(share)
    session.commit()

    logger.info(
        "Anamnesi self-service ricevuta: client=%d scope=%s",
        share.client_id, share.scope,
    )

    return AnamnesiSubmitResponse(
        success=True,
        message="Grazie! Il tuo questionario e' stato inviato al tuo trainer.",
    )
