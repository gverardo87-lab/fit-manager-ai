# api/auth/schemas.py
"""
Schemi Pydantic per le richieste/risposte di autenticazione.

Questi NON sono modelli ORM (no table=True) — sono solo contratti API.
Separano cio' che il client invia da cio' che il DB salva.
"""

from pydantic import BaseModel, Field, field_validator


class TrainerRegister(BaseModel):
    """Payload per registrazione nuovo trainer."""
    email: str = Field(max_length=255)
    nome: str = Field(min_length=1, max_length=100)
    cognome: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v:
            raise ValueError("Email non valida")
        return v


class TrainerLogin(BaseModel):
    """Payload per login."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Risposta dopo login/register con successo."""
    access_token: str
    token_type: str = "bearer"
    trainer_id: int
    nome: str
    cognome: str


class TrainerPublic(BaseModel):
    """Dati pubblici del trainer (senza password)."""
    id: int
    email: str
    nome: str
    cognome: str
    is_active: bool
