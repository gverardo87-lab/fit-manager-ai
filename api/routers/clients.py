# api/routers/clients.py
"""
Endpoint Clienti — il primo router dell'API.

Ogni query filtra per trainer_id: un trainer vede SOLO i propri clienti.
Questo e' il pattern multi-tenancy che si ripete su TUTTI i router futuri.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from pydantic import BaseModel

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client

router = APIRouter(prefix="/clients", tags=["clients"])


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
        items=[
            ClientResponse(
                id=c.id,
                nome=c.nome,
                cognome=c.cognome,
                telefono=c.telefono,
                email=c.email,
                data_nascita=str(c.data_nascita) if c.data_nascita else None,
                sesso=c.sesso,
                stato=c.stato,
            )
            for c in clients
        ],
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
    """
    Dettaglio singolo cliente. Verifica che appartenga al trainer autenticato.
    """
    from fastapi import HTTPException, status

    client = session.exec(
        select(Client).where(Client.id == client_id, Client.trainer_id == trainer.id)
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente non trovato",
        )

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
