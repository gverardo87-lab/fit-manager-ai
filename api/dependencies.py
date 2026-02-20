# api/dependencies.py
"""
Dependency injection per FastAPI.

get_current_trainer() e' il cuore della multi-tenancy:
ogni endpoint protetto riceve automaticamente il trainer autenticato.
Se il token e' assente/invalido/scaduto, l'endpoint ritorna 401.

Come funziona:
1. Il client invia: Authorization: Bearer <jwt_token>
2. FastAPI estrae il token dall'header
3. decode_access_token() verifica firma e scadenza
4. Cerchiamo il trainer nel DB
5. L'endpoint riceve l'oggetto Trainer pronto all'uso
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from api.database import get_session
from api.models.trainer import Trainer
from api.auth.service import decode_access_token

# Schema di sicurezza: estrae "Bearer <token>" dall'header Authorization
_security = HTTPBearer()


def get_current_trainer(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    session: Session = Depends(get_session),
) -> Trainer:
    """
    Dependency che ritorna il Trainer autenticato.

    Usala in qualsiasi endpoint che deve essere protetto:

        @router.get("/clients")
        def list_clients(trainer: Trainer = Depends(get_current_trainer)):
            # trainer.id e' il filtro multi-tenancy
            ...

    Se il token e' invalido, FastAPI ritorna automaticamente 401.
    """
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido o scaduto",
        )

    trainer_id = int(payload["sub"])
    trainer = session.get(Trainer, trainer_id)
    if not trainer or not trainer.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Trainer non trovato o disattivato",
        )

    return trainer
