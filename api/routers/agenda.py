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

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from pydantic import BaseModel, Field, field_validator, model_validator

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.event import Event
from api.models.client import Client

router = APIRouter(prefix="/events", tags=["events"])

# Categorie valide (mirror di core/constants.py SessionCategory)
VALID_CATEGORIES = {"PT", "SALA", "NUOTO", "YOGA", "CONSULENZA", "CORSO"}

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
    """Dati evento restituiti dall'API."""
    id: int
    data_inizio: str
    data_fine: str
    categoria: str
    titolo: Optional[str] = None
    id_cliente: Optional[int] = None
    id_contratto: Optional[int] = None
    stato: str
    note: Optional[str] = None


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
        select(Client).where(Client.id == client_id, Client.trainer_id == trainer_id)
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


def _to_response(event: Event) -> EventResponse:
    """Converte un Event ORM in EventResponse."""
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
    )


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
    query = select(Event).where(Event.trainer_id == trainer.id)

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

    return EventListResponse(
        items=[_to_response(e) for e in events],
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
        select(Event).where(Event.id == event_id, Event.trainer_id == trainer.id)
    ).first()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento non trovato")

    return _to_response(event)


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

    # Bouncer 2: Anti-Overlapping — ho gia' un evento in questo slot?
    _check_overlap(session, trainer.id, data.data_inizio, data.data_fine)

    # Tutto ok: salva
    event = Event(
        trainer_id=trainer.id,
        data_inizio=data.data_inizio,
        data_fine=data.data_fine,
        categoria=data.categoria,
        titolo=data.titolo,
        id_cliente=data.id_cliente,
        id_contratto=data.id_contratto,
        stato=data.stato,
        note=data.note,
    )
    session.add(event)
    session.commit()
    session.refresh(event)

    return _to_response(event)


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
    # Bouncer 1: l'evento e' mio?
    event = session.exec(
        select(Event).where(Event.id == event_id, Event.trainer_id == trainer.id)
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
    for field, value in update_data.items():
        setattr(event, field, value)

    session.add(event)
    session.commit()
    session.refresh(event)

    return _to_response(event)


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
        select(Event).where(Event.id == event_id, Event.trainer_id == trainer.id)
    ).first()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento non trovato")

    session.delete(event)
    session.commit()
