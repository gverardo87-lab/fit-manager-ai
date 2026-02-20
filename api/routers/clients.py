# api/routers/clients.py
"""
Endpoint Clienti — il primo router dell'API.

Ogni query filtra per trainer_id: un trainer vede SOLO i propri clienti.
Questo e' il pattern multi-tenancy che si ripete su TUTTI i router futuri.

Sicurezza (Design by Contract):
- trainer_id NON appare mai negli schemas di input (ClientCreate, ClientUpdate)
- trainer_id viene iniettato server-side dal JWT token (get_current_trainer)
- Ogni query filtra SEMPRE per trainer_id = trainer autenticato (IDOR prevention)
"""

import json
import re
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from pydantic import BaseModel, Field, field_validator

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client

router = APIRouter(prefix="/clients", tags=["clients"])


# --- Input schemas (cosa l'API accetta) ---
# SICUREZZA: nessun campo trainer_id. Il trainer viene dal JWT token.

class ClientCreate(BaseModel):
    """
    Schema per creazione cliente via API.

    trainer_id e' ASSENTE by design: viene iniettato dall'endpoint
    usando il trainer autenticato dal JWT. Questo impedisce a un trainer
    di creare clienti nel namespace di un altro trainer.
    """
    nome: str = Field(min_length=1, max_length=100)
    cognome: str = Field(min_length=1, max_length=100)
    telefono: Optional[str] = None
    email: Optional[str] = None
    data_nascita: Optional[date] = None
    sesso: Optional[str] = Field(None, pattern=r"^(Uomo|Donna|Altro)$")
    anamnesi: Optional[dict] = Field(default_factory=dict)
    stato: str = Field(default="Attivo", pattern=r"^(Attivo|Inattivo)$")

    @field_validator("telefono")
    @classmethod
    def validate_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not re.match(r"^[+]?[0-9\s\-()]{6,20}$", v):
            raise ValueError("Telefono non valido")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if "@" not in v or "." not in v:
            raise ValueError("Email non valida")
        return v.lower()

    @field_validator("data_nascita")
    @classmethod
    def validate_data_nascita(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("Data di nascita non puo' essere nel futuro")
        return v


class ClientUpdate(BaseModel):
    """
    Schema per update cliente via API (partial update).

    Tutti i campi sono opzionali: il frontend invia SOLO i campi da modificare.
    trainer_id e' ASSENTE: non si puo' "trasferire" un cliente via API.
    """
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    cognome: Optional[str] = Field(None, min_length=1, max_length=100)
    telefono: Optional[str] = None
    email: Optional[str] = None
    data_nascita: Optional[date] = None
    sesso: Optional[str] = Field(None, pattern=r"^(Uomo|Donna|Altro)$")
    anamnesi: Optional[dict] = None
    stato: Optional[str] = Field(None, pattern=r"^(Attivo|Inattivo)$")

    @field_validator("telefono")
    @classmethod
    def validate_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not re.match(r"^[+]?[0-9\s\-()]{6,20}$", v):
            raise ValueError("Telefono non valido")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if "@" not in v or "." not in v:
            raise ValueError("Email non valida")
        return v.lower()

    @field_validator("data_nascita")
    @classmethod
    def validate_data_nascita(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("Data di nascita non puo' essere nel futuro")
        return v


# --- Response schemas (cosa l'API restituisce) ---

class ClientResponse(BaseModel):
    """Dati cliente restituiti dall'API. Mai esporre campi interni come anamnesi_json raw."""
    id: int
    nome: str
    cognome: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    data_nascita: Optional[str] = None
    sesso: Optional[str] = None
    stato: str


class ClientListResponse(BaseModel):
    """Risposta paginata per lista clienti."""
    items: List[ClientResponse]
    total: int
    page: int
    page_size: int


# --- Endpoints ---

@router.get("", response_model=ClientListResponse)
def list_clients(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1, description="Numero pagina"),
    page_size: int = Query(default=50, ge=1, le=200, description="Risultati per pagina"),
    stato: Optional[str] = Query(default=None, description="Filtra per stato (Attivo, Inattivo)"),
    search: Optional[str] = Query(default=None, description="Cerca per nome/cognome"),
):
    """
    Lista clienti del trainer autenticato.

    Filtro multi-tenancy: WHERE trainer_id = <trainer_corrente>.
    Supporta paginazione, filtro per stato, ricerca per nome.
    """
    # Query base: solo clienti di QUESTO trainer
    query = select(Client).where(Client.trainer_id == trainer.id)

    # Filtro opzionale per stato
    if stato:
        query = query.where(Client.stato == stato)

    # Ricerca per nome/cognome (case insensitive con LIKE)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            (Client.nome.ilike(pattern)) | (Client.cognome.ilike(pattern))
        )

    # Count totale (prima della paginazione)
    count_query = select(Client.id).where(Client.trainer_id == trainer.id)
    if stato:
        count_query = count_query.where(Client.stato == stato)
    if search:
        pattern = f"%{search}%"
        count_query = count_query.where(
            (Client.nome.ilike(pattern)) | (Client.cognome.ilike(pattern))
        )
    total = len(session.exec(count_query).all())

    # Paginazione
    offset = (page - 1) * page_size
    query = query.order_by(Client.cognome, Client.nome).offset(offset).limit(page_size)

    clients = session.exec(query).all()

    return ClientListResponse(
        items=[_to_response(c) for c in clients],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Dettaglio singolo cliente. Bouncer: query filtra per trainer_id."""
    client = session.exec(
        select(Client).where(Client.id == client_id, Client.trainer_id == trainer.id)
    ).first()

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    return _to_response(client)


# --- POST: Crea cliente ---

@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    data: ClientCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Crea un nuovo cliente per il trainer autenticato.

    trainer_id viene INIETTATO dal JWT — mai dal body della richiesta.
    Anche se il body contenesse trainer_id, lo schema ClientCreate lo ignora.
    """
    client = Client(
        trainer_id=trainer.id,  # <-- Iniezione sicura dal JWT
        nome=data.nome,
        cognome=data.cognome,
        telefono=data.telefono,
        email=data.email,
        data_nascita=data.data_nascita,
        sesso=data.sesso,
        anamnesi_json=json.dumps(data.anamnesi) if data.anamnesi else None,
        stato=data.stato,
    )
    session.add(client)
    session.commit()
    session.refresh(client)

    return _to_response(client)


# --- PUT: Aggiorna cliente (partial update) ---

@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    data: ClientUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Aggiorna un cliente esistente.

    Bouncer Pattern: query singola con id + trainer_id.
    Se il cliente non esiste O appartiene a un altro trainer -> 404.
    Mai 403: non riveliamo l'esistenza di risorse altrui.
    """
    # Bouncer: una sola query, filtro combinato id + trainer_id
    client = session.exec(
        select(Client).where(Client.id == client_id, Client.trainer_id == trainer.id)
    ).first()

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    # Partial update: applica solo i campi effettivamente inviati
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "anamnesi":
            client.anamnesi_json = json.dumps(value) if value else None
        else:
            setattr(client, field, value)

    session.add(client)
    session.commit()
    session.refresh(client)

    return _to_response(client)


# --- DELETE: Elimina cliente ---

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Elimina un cliente.

    Bouncer Pattern: query singola con id + trainer_id.
    Se il cliente non esiste O appartiene a un altro trainer -> 404.
    Nessun response body (204 No Content).
    """
    # Bouncer: una sola query, filtro combinato id + trainer_id
    client = session.exec(
        select(Client).where(Client.id == client_id, Client.trainer_id == trainer.id)
    ).first()

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    session.delete(client)
    session.commit()


# --- Helper ---

def _to_response(client: Client) -> ClientResponse:
    """Converte un Client ORM in ClientResponse. Centralizza la conversione."""
    return ClientResponse(
        id=client.id,
        nome=client.nome,
        cognome=client.cognome,
        telefono=client.telefono,
        email=client.email,
        data_nascita=str(client.data_nascita) if client.data_nascita else None,
        sesso=client.sesso,
        stato=client.stato,
    )
