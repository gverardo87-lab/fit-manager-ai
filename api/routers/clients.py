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
from datetime import date, datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func
from pydantic import BaseModel, Field, field_validator

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.contract import Contract
from api.models.event import Event
from api.routers._audit import log_audit

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
    model_config = {"extra": "forbid"}

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
    model_config = {"extra": "forbid"}

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
    crediti_residui: int = 0


class ClientListResponse(BaseModel):
    """Risposta paginata per lista clienti."""
    items: List[ClientResponse]
    total: int
    page: int
    page_size: int


# --- Credit Engine helpers ---

def _calc_credits_batch(
    session: Session, client_ids: List[int], trainer_id: int
) -> Dict[int, int]:
    """
    Calcola crediti_residui per un batch di clienti in 2 query SQL.

    crediti_residui = crediti_acquistati - sedute_PT_usate

    - crediti_acquistati: SUM(crediti_totali) da TUTTI i contratti non eliminati
      (chiuso NON filtrato — chiuso blocca nuove operazioni, non invalida crediti)
    - sedute_PT_usate: COUNT(eventi) con categoria='PT' e stato!='Cancellato'
    """
    if not client_ids:
        return {}

    # Query 1: crediti acquistati per cliente (tutti i contratti non eliminati)
    # NOTA: chiuso NON filtrato — chiuso blocca nuove operazioni, non invalida i crediti
    credit_rows = session.exec(
        select(Contract.id_cliente, func.coalesce(func.sum(Contract.crediti_totali), 0))
        .where(
            Contract.id_cliente.in_(client_ids),
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
        )
        .group_by(Contract.id_cliente)
    ).all()
    credits_map: Dict[int, int] = {row[0]: int(row[1]) for row in credit_rows}

    # Query 2: sedute PT usate per cliente (non cancellate, non eliminate)
    usage_rows = session.exec(
        select(Event.id_cliente, func.count(Event.id))
        .where(
            Event.id_cliente.in_(client_ids),
            Event.categoria == "PT",
            Event.stato != "Cancellato",
            Event.trainer_id == trainer_id,
            Event.deleted_at == None,
        )
        .group_by(Event.id_cliente)
    ).all()
    usage_map: Dict[int, int] = {row[0]: int(row[1]) for row in usage_rows}

    return {
        cid: credits_map.get(cid, 0) - usage_map.get(cid, 0)
        for cid in client_ids
    }


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
    Include crediti_residui calcolati in batch (3 query totali, zero N+1).
    """
    # Query base: solo clienti di QUESTO trainer, non eliminati
    query = select(Client).where(Client.trainer_id == trainer.id, Client.deleted_at == None)

    # Filtro opzionale per stato
    if stato:
        query = query.where(Client.stato == stato)

    # Ricerca per nome/cognome (case insensitive con LIKE)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            (Client.nome.ilike(pattern)) | (Client.cognome.ilike(pattern))
        )

    # Count dalla stessa query base (zero duplicazione filtri)
    total = session.exec(
        select(func.count()).select_from(query.subquery())
    ).one()

    # Paginazione
    offset = (page - 1) * page_size
    query = query.order_by(Client.cognome, Client.nome).offset(offset).limit(page_size)

    clients = session.exec(query).all()

    # Batch credit calculation (2 query per tutti i clienti)
    client_ids = [c.id for c in clients]
    credits = _calc_credits_batch(session, client_ids, trainer.id)

    return ClientListResponse(
        items=[_to_response(c, credits.get(c.id, 0)) for c in clients],
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
    """Dettaglio singolo cliente con crediti. Bouncer: query filtra per trainer_id."""
    client = session.exec(
        select(Client).where(
            Client.id == client_id, Client.trainer_id == trainer.id, Client.deleted_at == None
        )
    ).first()

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    credits = _calc_credits_batch(session, [client.id], trainer.id)

    return _to_response(client, credits.get(client.id, 0))


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
    session.flush()
    log_audit(session, "client", client.id, "CREATE", trainer.id)
    session.commit()
    session.refresh(client)

    return _to_response(client, 0)


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
    # Bouncer: una sola query, filtro combinato id + trainer_id + non eliminato
    client = session.exec(
        select(Client).where(
            Client.id == client_id, Client.trainer_id == trainer.id, Client.deleted_at == None
        )
    ).first()

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    # Partial update: applica solo i campi effettivamente inviati
    update_data = data.model_dump(exclude_unset=True)
    changes = {}
    for field, value in update_data.items():
        if field == "anamnesi":
            old_val = client.anamnesi_json
            client.anamnesi_json = json.dumps(value) if value else None
            if client.anamnesi_json != old_val:
                changes[field] = {"old": old_val, "new": client.anamnesi_json}
        else:
            old_val = getattr(client, field)
            setattr(client, field, value)
            if value != old_val:
                changes[field] = {"old": old_val, "new": value}

    log_audit(session, "client", client.id, "UPDATE", trainer.id, changes or None)
    session.add(client)
    session.commit()
    session.refresh(client)

    credits = _calc_credits_batch(session, [client.id], trainer.id)

    return _to_response(client, credits.get(client.id, 0))


# --- DELETE: Elimina cliente ---

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Soft-delete un cliente.

    Bouncer Pattern: query singola con id + trainer_id + non eliminato.
    RESTRICT: se il cliente ha contratti attivi (non eliminati) → 400.
    Nessun response body (204 No Content).
    """
    # Bouncer: filtro combinato id + trainer_id + non eliminato
    client = session.exec(
        select(Client).where(
            Client.id == client_id, Client.trainer_id == trainer.id, Client.deleted_at == None
        )
    ).first()

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    # RESTRICT: verifica nessun contratto attivo (non eliminato)
    active_contracts = session.exec(
        select(func.count(Contract.id)).where(
            Contract.id_cliente == client_id,
            Contract.trainer_id == trainer.id,
            Contract.deleted_at == None,
            Contract.chiuso == False,
        )
    ).one()
    if active_contracts > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile eliminare: il cliente ha contratti attivi",
        )

    client.deleted_at = datetime.now(timezone.utc)
    session.add(client)
    log_audit(session, "client", client.id, "DELETE", trainer.id)
    session.commit()


# --- Helper ---

def _to_response(client: Client, crediti_residui: int = 0) -> ClientResponse:
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
        crediti_residui=crediti_residui,
    )
