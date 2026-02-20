# api/auth/router.py
"""
Endpoint di autenticazione: registrazione e login.

POST /auth/register  -> crea nuovo trainer, ritorna JWT
POST /auth/login     -> verifica credenziali, ritorna JWT
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from api.database import get_session
from api.models.trainer import Trainer
from api.auth.schemas import TrainerRegister, TrainerLogin, TokenResponse
from api.auth.service import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: TrainerRegister, session: Session = Depends(get_session)):
    """
    Registra un nuovo trainer.

    1. Verifica che l'email non sia gia' in uso
    2. Hash della password con bcrypt
    3. Salva nel DB
    4. Ritorna JWT token (il trainer e' gia' loggato)
    """
    existing = session.exec(select(Trainer).where(Trainer.email == data.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email gia' registrata",
        )

    trainer = Trainer(
        email=data.email,
        nome=data.nome,
        cognome=data.cognome,
        hashed_password=hash_password(data.password),
    )
    session.add(trainer)
    session.commit()
    session.refresh(trainer)

    token = create_access_token(trainer.id, trainer.email)
    return TokenResponse(
        access_token=token,
        trainer_id=trainer.id,
        nome=trainer.nome,
        cognome=trainer.cognome,
    )


@router.post("/login", response_model=TokenResponse)
def login(data: TrainerLogin, session: Session = Depends(get_session)):
    """
    Login trainer esistente.

    1. Cerca trainer per email
    2. Verifica password con bcrypt
    3. Ritorna JWT token
    """
    trainer = session.exec(
        select(Trainer).where(Trainer.email == data.email.strip().lower())
    ).first()

    if not trainer or not verify_password(data.password, trainer.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corretti",
        )

    if not trainer.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disattivato",
        )

    token = create_access_token(trainer.id, trainer.email)
    return TokenResponse(
        access_token=token,
        trainer_id=trainer.id,
        nome=trainer.nome,
        cognome=trainer.cognome,
    )
