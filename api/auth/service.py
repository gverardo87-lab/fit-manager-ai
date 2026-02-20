# api/auth/service.py
"""
Servizio autenticazione: password hashing + JWT token.

Password: bcrypt (one-way hash, salt automatico, sicuro per produzione).
Token: JWT con expiry configurabile. Il token contiene solo il trainer_id
e l'email — mai dati sensibili.
"""

from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import jwt, JWTError

from api.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES


def hash_password(plain_password: str) -> str:
    """Genera hash bcrypt della password. Ogni chiamata produce un hash diverso (salt random)."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Confronta password in chiaro con hash. Ritorna True se corrispondono."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(trainer_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea JWT token con payload {sub: trainer_id, email, exp}.

    Il token e' firmato con JWT_SECRET (HS256). Chi possiede il token
    puo' chiamare le API come quel trainer. Per questo ha un'expiry.
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    payload = {
        "sub": str(trainer_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica e valida un JWT token. Ritorna il payload o None se invalido/scaduto.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
