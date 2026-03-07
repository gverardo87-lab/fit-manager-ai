# api/schemas/public.py
"""
Schema Pydantic per il Portale Clienti pubblico (self-service anamnesi).

Endpoint pubblici (no JWT trainer):
  GET  /api/public/anamnesi/validate?token=X  → AnamnesiValidateResponse
  POST /api/public/anamnesi/submit             → AnamnesiSubmitResponse

Endpoint protetto (JWT trainer):
  POST /api/clients/{id}/share-anamnesi        → ShareTokenResponse
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ── Generazione token (trainer → POST /api/clients/{id}/share-anamnesi) ──

class ShareTokenResponse(BaseModel):
    """Risposta alla generazione del link monouso per l'anamnesi."""
    token: str
    url: str          # path relativo: /public/anamnesi/{token}
    expires_at: datetime
    client_name: str  # feedback visivo per il trainer


# ── Validazione token (pubblico → GET /api/public/anamnesi/validate) ──

class AnamnesiValidateResponse(BaseModel):
    """Info per pre-popolare la pagina pubblica. Nome mascherato: 'Marco R.'"""
    client_name: str    # "Marco R." — cognome troncato per privacy
    trainer_name: str   # "Chiara B." — nome del professionista
    has_existing: bool  # se esiste gia' un'anamnesi (per messaggio contestuale)
    scope: str          # "anamnesi"


# ── Submit anamnesi (pubblico → POST /api/public/anamnesi/submit) ──

class AnamnesiSubmitRequest(BaseModel):
    """Payload invio anamnesi compilata dal cliente."""
    token: str
    anamnesi: dict[str, Any]  # AnamnesiData strutturata (validata lato frontend)


class AnamnesiSubmitResponse(BaseModel):
    """Conferma invio anamnesi."""
    success: bool
    message: str
