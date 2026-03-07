# api/models/share_token.py
"""
Modello ShareToken — link monouso per portale clienti self-service.

Un trainer genera un token UUID4 per permettere al proprio cliente
di compilare l'anamnesi senza autenticazione. Il token e':
- monouso (used_at traccia il consumo)
- temporaneo (expires_at = created_at + 48h)
- revocabile (il trainer puo' eliminarlo)
- scope-based (estendibile: "anamnesi", in futuro "misurazioni", ecc.)
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ShareToken(SQLModel, table=True):
    """ORM model per la tabella 'share_tokens'."""

    __tablename__ = "share_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True)               # UUID4 opaco
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    client_id: int = Field(foreign_key="clienti.id", index=True)
    scope: str = Field(default="anamnesi")                    # estendibile
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    expires_at: datetime                                       # created_at + 48h
    used_at: Optional[datetime] = None                        # None = non usato
