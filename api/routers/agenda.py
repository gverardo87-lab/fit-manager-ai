# api/routers/agenda.py
"""
Endpoint Agenda — gestione eventi e sessioni.

Sicurezza multi-tenant a 2 livelli:
1. trainer_id diretto: ogni evento ha trainer_id = trainer autenticato
2. Relational IDOR: se l'evento ha id_cliente, verifica che il cliente
   appartenga al trainer (clienti.trainer_id == trainer.id)

Regola 404: se l'evento non esiste O non appartiene al trainer -> 404.
Mai 403, mai rivelare l'esistenza di dati altrui.

Validazioni:
- data_fine > data_inizio (model_validator)
- durata massima 4 ore
- categoria in SessionCategory enum
- Conflict Prevention: no sovrapposizioni temporali per lo stesso trainer
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func
from pydantic import BaseModel, Field, field_validator, model_validator

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.event import Event
from api.models.client import Client
from api.models.contract import Contract
from api.routers._audit import log_audit

router = APIRouter(prefix="/events", tags=["events"])

# Categorie valide (mirror di core/constants.py SessionCategory)
VALID_CATEGORIES = {"PT", "SALA", "CORSO", "COLLOQUIO"}

# Stati validi (mirror di core/constants.py EventStatus)
VALID_STATUSES = {"Programmato", "Completato", "Cancellato", "Rinviato"}


# --- Input schemas ---
# SICUREZZA: nessun campo trainer_id. Il trainer viene dal JWT token.

class EventCreate(BaseModel):
    """
    Schema per creazione evento via API.

    trainer_id e' ASSENTE: viene iniettato dall'endpoint.
    id_cliente e' opzionale: eventi generici (SALA, CORSO) non hanno cliente.
    id_contratto e' opzionale: gestito server-side con logica FIFO crediti.

    Validazioni temporali:
    - data_fine deve essere strettamente maggiore di data_inizio
    - durata massima 4 ore (coerente con core/models.py)
    """
    model_config = {"extra": "forbid"}

    data_inizio: datetime
    data_fine: datetime
    categoria: str
    titolo: str = Field(min_length=1, max_length=200)
    id_cliente: Optional[int] = Field(None, gt=0)
    id_contratto: Optional[int] = Field(None, gt=0)
    stato: str = Field(default="Programmato")
    note: Optional[str] = Field(None, max_length=500)

    @field_validator("categoria")
    @classmethod
    def validate_categoria(cls, v: str) -> str:
        normalized = v.upper()
        if normalized not in VALID_CATEGORIES:
            raise ValueError(f"Categoria non valida. Ammesse: {', '.join(sorted(VALID_CATEGORIES))}")
        return normalized

    @field_validator("stato")
    @classmethod
    def validate_stato(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"Stato non valido. Ammessi: {', '.join(sorted(VALID_STATUSES))}")
        return v

    @model_validator(mode="after")
    def validate_temporal(self):
        """data_fine deve essere strettamente dopo data_inizio, max 4 ore."""
        if self.data_fine <= self.data_inizio:
            raise ValueError("data_fine deve essere dopo data_inizio")
        duration_hours = (self.data_fine - self.data_inizio).total_seconds() / 3600
        if duration_hours > 4:
            raise ValueError("La durata massima di un evento e' 4 ore")
        return self


class EventUpdate(BaseModel):
    """
    Schema per update evento via API (partial update).

    Campi modificabili: data_inizio, data_fine, titolo, note, stato.
    NON modificabili via update: categoria, id_cliente, id_contratto, trainer_id.
    Coerente con AgendaRepository.update_event() che aggiorna solo scheduling.
    """
    model_config = {"extra": "forbid"}

    data_inizio: Optional[datetime] = None
    data_fine: Optional[datetime] = None
    titolo: Optional[str] = Field(None, min_length=1, max_length=200)
    note: Optional[str] = Field(None, max_length=500)
    stato: Optional[str] = None

    @field_validator("stato")
    @classmethod
    def validate_stato(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"Stato non valido. Ammessi: {', '.join(sorted(VALID_STATUSES))}")
        return v

    @model_validator(mode="after")
    def validate_temporal(self):
        """Se entrambe le date sono fornite, verifica coerenza temporale."""
        if self.data_inizio is not None and self.data_fine is not None:
            if self.data_fine <= self.data_inizio:
                raise ValueError("data_fine deve essere dopo data_inizio")
            duration_hours = (self.data_fine - self.data_inizio).total_seconds() / 3600
            if duration_hours > 4:
                raise ValueError("La durata massima di un evento e' 4 ore")
        return self


# --- Response schemas ---

class EventResponse(BaseModel):
    """Dati evento restituiti dall'API. Include nome cliente per eventi PT."""
    id: int
    data_inizio: str
    data_fine: str
    categoria: str
    titolo: Optional[str] = None
    id_cliente: Optional[int] = None
    id_contratto: Optional[int] = None
    stato: str
    note: Optional[str] = None
    cliente_nome: Optional[str] = None
    cliente_cognome: Optional[str] = None


class EventListResponse(BaseModel):
    """Risposta paginata per lista eventi."""
    items: List[EventResponse]
    total: int


# --- Bouncer helpers (early return functions) ---

def _check_client_ownership(
    session: Session, client_id: int, trainer_id: int
) -> None:
    """
    Relational IDOR: verifica che il cliente appartenga al trainer.

    Se il cliente non esiste O appartiene a un altro trainer -> 404.
    Mai rivelare l'esistenza di clienti altrui.
    """
    client = session.exec(
        select(Client).where(
            Client.id == client_id, Client.trainer_id == trainer_id, Client.deleted_at == None
        )
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente non trovato",
        )


def _check_overlap(
    session: Session,
    trainer_id: int,
    data_inizio: datetime,
    data_fine: datetime,
    exclude_event_id: int | None = None,
) -> None:
    """
    Anti-Overlapping: verifica che il trainer non abbia eventi sovrapposti.

    Condizione di sovrapposizione:
        existing.data_inizio < new.data_fine AND existing.data_fine > new.data_inizio

    Per PUT: exclude_event_id esclude l'evento corrente dal check.
    Se c'e' sovrapposizione -> 409 Conflict.
    """
    query = select(Event).where(
        Event.trainer_id == trainer_id,
        Event.data_inizio < data_fine,
        Event.data_fine > data_inizio,
        Event.stato != "Cancellato",  # eventi cancellati non contano
        Event.deleted_at == None,
    )

    if exclude_event_id is not None:
        query = query.where(Event.id != exclude_event_id)

    conflict = session.exec(query).first()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sovrapposizione con evento id={conflict.id} "
                   f"({conflict.data_inizio} - {conflict.data_fine}, {conflict.categoria})",
        )


def _load_client_names_batch(
    session: Session, client_ids: set[int]
) -> Dict[int, Tuple[str, str]]:
    """Batch load client names. Returns {id: (nome, cognome)}. Zero N+1."""
    if not client_ids:
        return {}
    rows = session.exec(
        select(Client.id, Client.nome, Client.cognome)
        .where(Client.id.in_(list(client_ids)))
    ).all()
    return {r[0]: (r[1], r[2]) for r in rows}


def _to_response(
    event: Event,
    cliente_nome: Optional[str] = None,
    cliente_cognome: Optional[str] = None,
) -> EventResponse:
    """Converte un Event ORM in EventResponse con nome cliente opzionale."""
    return EventResponse(
        id=event.id,
        data_inizio=str(event.data_inizio),
        data_fine=str(event.data_fine),
        categoria=event.categoria,
        titolo=event.titolo,
        id_cliente=event.id_cliente,
        id_contratto=event.id_contratto,
        stato=event.stato,
        note=event.note,
        cliente_nome=cliente_nome,
        cliente_cognome=cliente_cognome,
    )


def _auto_assign_contract(
    session: Session, client_id: int, trainer_id: int
) -> Optional[int]:
    """
    Auto-FIFO: assegna l'evento PT al contratto attivo piu' vecchio
    con crediti residui > 0.

    2 query batch:
    1. Contratti attivi del cliente, ordinati per data_inizio ASC (FIFO)
    2. Conteggio PT events (non cancellati) per contratto

    Returns: contract.id oppure None se nessun contratto ha crediti.
    """
    contracts = session.exec(
        select(Contract).where(
            Contract.id_cliente == client_id,
            Contract.trainer_id == trainer_id,
            Contract.chiuso == False,
            Contract.deleted_at == None,
        ).order_by(Contract.data_inizio.asc())
    ).all()

    if not contracts:
        return None

    # Batch count PT events per contratto (zero N+1)
    contract_ids = [c.id for c in contracts]
    usage_rows = session.exec(
        select(Event.id_contratto, func.count(Event.id))
        .where(
            Event.id_contratto.in_(contract_ids),
            Event.categoria == "PT",
            Event.stato != "Cancellato",
            Event.deleted_at == None,
        )
        .group_by(Event.id_contratto)
    ).all()
    usage_map: Dict[int, int] = {row[0]: int(row[1]) for row in usage_rows}

    # FIFO: primo contratto con crediti residui
    for contract in contracts:
        totali = contract.crediti_totali or 0
        usati = usage_map.get(contract.id, 0)
        if totali - usati > 0:
            return contract.id

    return None


# --- Endpoints ---

@router.get("", response_model=EventListResponse)
def list_events(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    start: Optional[str] = Query(None, description="Inizio range ISO (YYYY-MM-DD o datetime)"),
    end: Optional[str] = Query(None, description="Fine range ISO (YYYY-MM-DD o datetime)"),
    categoria: Optional[str] = Query(None, description="Filtra per categoria (PT, SALA, ...)"),
    stato: Optional[str] = Query(None, description="Filtra per stato (Programmato, Completato, ...)"),
    id_cliente: Optional[int] = Query(None, description="Filtra per cliente"),
):
    """
    Lista eventi del trainer autenticato.

    Supporta filtri per range temporale, categoria, stato, cliente.
    Nessuna paginazione: il calendario ha bisogno di tutti gli eventi nel range.
    """
    query = select(Event).where(Event.trainer_id == trainer.id, Event.deleted_at == None)

    if start:
        query = query.where(Event.data_inizio >= start)
    if end:
        query = query.where(Event.data_fine <= end)
    if categoria:
        query = query.where(Event.categoria == categoria.upper())
    if stato:
        query = query.where(Event.stato == stato)
    if id_cliente:
        _check_client_ownership(session, id_cliente, trainer.id)
        query = query.where(Event.id_cliente == id_cliente)

    query = query.order_by(Event.data_inizio)
    events = session.exec(query).all()

    # Batch load client names (1 query aggiuntiva, zero N+1)
    client_ids = {e.id_cliente for e in events if e.id_cliente}
    client_names = _load_client_names_batch(session, client_ids)

    def _names(cid: Optional[int]) -> Tuple[Optional[str], Optional[str]]:
        if not cid:
            return (None, None)
        return client_names.get(cid, (None, None))

    return EventListResponse(
        items=[
            _to_response(e, *_names(e.id_cliente))
            for e in events
        ],
        total=len(events),
    )


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Dettaglio evento. Bouncer: trainer_id filter."""
    event = session.exec(
        select(Event).where(Event.id == event_id, Event.trainer_id == trainer.id, Event.deleted_at == None)
    ).first()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento non trovato")

    names = _load_client_names_batch(session, {event.id_cliente} if event.id_cliente else set())
    nome, cognome = names.get(event.id_cliente, (None, None)) if event.id_cliente else (None, None)

    return _to_response(event, nome, cognome)


# --- POST: Crea evento ---

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    data: EventCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Crea un nuovo evento per il trainer autenticato.

    Bouncer chain (early returns):
    1. Se id_cliente fornito -> verifica ownership (Relational IDOR)
    2. Check sovrapposizione temporale -> 409 se conflitto
    3. Salva con trainer_id iniettato dal JWT
    """
    # Bouncer 1: Relational IDOR — il cliente e' mio?
    if data.id_cliente:
        _check_client_ownership(session, data.id_cliente, trainer.id)

    # Bouncer 2: Validazione id_contratto esplicito (ownership + chiuso)
    if data.id_contratto:
        contract = session.exec(
            select(Contract).where(
                Contract.id == data.id_contratto,
                Contract.trainer_id == trainer.id,
                Contract.deleted_at == None,
            )
        ).first()
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contratto non trovato",
            )
        if contract.chiuso:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossibile assegnare eventi a un contratto chiuso",
            )

    # Bouncer 3: Anti-Overlapping — ho gia' un evento in questo slot?
    _check_overlap(session, trainer.id, data.data_inizio, data.data_fine)

    # Auto-FIFO: assegna contratto per eventi PT senza contratto esplicito
    assigned_contract_id = data.id_contratto
    if data.categoria == "PT" and data.id_cliente and not data.id_contratto:
        assigned_contract_id = _auto_assign_contract(
            session, data.id_cliente, trainer.id
        )

    # Tutto ok: salva
    event = Event(
        trainer_id=trainer.id,
        data_inizio=data.data_inizio,
        data_fine=data.data_fine,
        categoria=data.categoria,
        titolo=data.titolo,
        id_cliente=data.id_cliente,
        id_contratto=assigned_contract_id,
        stato=data.stato,
        note=data.note,
    )
    session.add(event)
    session.flush()
    log_audit(session, "event", event.id, "CREATE", trainer.id)

    # Auto-close: se evento PT con contratto, verifica crediti esauriti + saldato
    if event.categoria == "PT" and event.id_contratto:
        ev_contract = session.get(Contract, event.id_contratto)
        if ev_contract and not ev_contract.chiuso and ev_contract.crediti_totali:
            crediti_usati = session.exec(
                select(func.count(Event.id)).where(
                    Event.id_contratto == ev_contract.id,
                    Event.categoria == "PT",
                    Event.stato != "Cancellato",
                    Event.deleted_at == None,
                )
            ).one()
            if (crediti_usati >= ev_contract.crediti_totali
                    and ev_contract.stato_pagamento == "SALDATO"):
                ev_contract.chiuso = True
                session.add(ev_contract)

    session.commit()
    session.refresh(event)

    names = _load_client_names_batch(session, {event.id_cliente} if event.id_cliente else set())
    nome, cognome = names.get(event.id_cliente, (None, None)) if event.id_cliente else (None, None)

    return _to_response(event, nome, cognome)


# --- PUT: Aggiorna evento (partial update) ---

@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    data: EventUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Aggiorna un evento esistente (scheduling only).

    Bouncer chain (early returns):
    1. Verifica ownership trainer_id -> 404 se non mio
    2. Se date cambiate -> verifica coerenza temporale con date esistenti
    3. Check sovrapposizione (escludendo se' stesso) -> 409 se conflitto
    4. Applica partial update
    """
    # Bouncer 1: l'evento e' mio? (non eliminato)
    event = session.exec(
        select(Event).where(Event.id == event_id, Event.trainer_id == trainer.id, Event.deleted_at == None)
    ).first()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento non trovato")

    # Calcola date effettive (merge tra esistenti e nuove)
    new_inizio = data.data_inizio if data.data_inizio is not None else event.data_inizio
    new_fine = data.data_fine if data.data_fine is not None else event.data_fine

    # Bouncer 2: validazione temporale cross-field (una sola data fornita)
    if new_fine <= new_inizio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="data_fine deve essere dopo data_inizio",
        )
    duration_hours = (new_fine - new_inizio).total_seconds() / 3600
    if duration_hours > 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La durata massima di un evento e' 4 ore",
        )

    # Bouncer 3: Anti-Overlapping (se le date sono cambiate)
    dates_changed = data.data_inizio is not None or data.data_fine is not None
    if dates_changed:
        _check_overlap(session, trainer.id, new_inizio, new_fine, exclude_event_id=event_id)

    # Tutto ok: applica partial update
    update_data = data.model_dump(exclude_unset=True)
    changes = {}
    for field, value in update_data.items():
        old_val = getattr(event, field)
        setattr(event, field, value)
        if value != old_val:
            changes[field] = {"old": old_val, "new": value}

    log_audit(session, "event", event.id, "UPDATE", trainer.id, changes or None)
    session.add(event)
    session.commit()
    session.refresh(event)

    names = _load_client_names_batch(session, {event.id_cliente} if event.id_cliente else set())
    nome, cognome = names.get(event.id_cliente, (None, None)) if event.id_cliente else (None, None)

    return _to_response(event, nome, cognome)


# --- DELETE: Elimina evento ---

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Elimina un evento.

    Bouncer: trainer_id filter. 404 se non mio o non esiste.
    """
    event = session.exec(
        select(Event).where(Event.id == event_id, Event.trainer_id == trainer.id, Event.deleted_at == None)
    ).first()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento non trovato")

    event.deleted_at = datetime.now(timezone.utc)
    session.add(event)
    log_audit(session, "event", event.id, "DELETE", trainer.id)
    session.commit()
