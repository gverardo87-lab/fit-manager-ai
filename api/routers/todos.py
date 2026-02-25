# api/routers/todos.py
"""
Endpoint Todo — CRUD promemoria trainer.

Bouncer diretto: Todo.trainer_id == trainer.id (entita' diretta, no FK chain).
Soft delete con deleted_at.
"""

from datetime import date, datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from pydantic import BaseModel, Field

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.todo import Todo
from api.routers._audit import log_audit

router = APIRouter(prefix="/todos", tags=["todos"])


# ── Schemas ──

class TodoCreate(BaseModel):
    """Creazione todo. Solo titolo obbligatorio."""
    model_config = {"extra": "forbid"}

    titolo: str = Field(min_length=1, max_length=200)
    descrizione: Optional[str] = None
    data_scadenza: Optional[date] = None


class TodoUpdate(BaseModel):
    """Update parziale todo."""
    model_config = {"extra": "forbid"}

    titolo: Optional[str] = Field(None, min_length=1, max_length=200)
    descrizione: Optional[str] = None
    data_scadenza: Optional[date] = None


class TodoResponse(BaseModel):
    """Risposta todo."""
    id: int
    titolo: str
    descrizione: Optional[str] = None
    data_scadenza: Optional[str] = None
    completato: bool
    completed_at: Optional[str] = None
    created_at: str


class TodoListResponse(BaseModel):
    """Lista todo."""
    items: List[TodoResponse]
    total: int


# ── Bouncer ──

def _bouncer_todo(session: Session, todo_id: int, trainer_id: int) -> Todo:
    """Trova todo per id + trainer_id. 404 se non trovato."""
    todo = session.exec(
        select(Todo).where(
            Todo.id == todo_id,
            Todo.trainer_id == trainer_id,
            Todo.deleted_at == None,
        )
    ).first()
    if not todo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Todo non trovato")
    return todo


# ── Endpoints ──

@router.get("", response_model=TodoListResponse)
def list_todos(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    completato: Optional[bool] = Query(None, description="Filtra per stato completamento"),
):
    """Lista todo del trainer. Default: tutti. Filtrabile per completato."""
    query = select(Todo).where(
        Todo.trainer_id == trainer.id,
        Todo.deleted_at == None,
    )
    if completato is not None:
        query = query.where(Todo.completato == completato)

    # Ordinamento: non completati prima, poi per scadenza (null in fondo), poi per creazione
    query = query.order_by(
        Todo.completato.asc(),
        Todo.data_scadenza.asc().nulls_last(),
        Todo.created_at.desc(),
    )

    todos = session.exec(query).all()

    return TodoListResponse(
        items=[_to_response(t) for t in todos],
        total=len(todos),
    )


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    data: TodoCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Crea un nuovo todo. trainer_id iniettato dal JWT."""
    todo = Todo(
        trainer_id=trainer.id,
        titolo=data.titolo,
        descrizione=data.descrizione,
        data_scadenza=data.data_scadenza,
    )
    session.add(todo)
    session.flush()
    log_audit(session, "todo", todo.id, "CREATE", trainer.id)
    session.commit()
    session.refresh(todo)
    return _to_response(todo)


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int,
    data: TodoUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Aggiorna titolo/descrizione/scadenza di un todo."""
    todo = _bouncer_todo(session, todo_id, trainer.id)

    update_data = data.model_dump(exclude_unset=True)
    changes = {}
    for field, value in update_data.items():
        old_val = getattr(todo, field)
        setattr(todo, field, value)
        if value != old_val:
            changes[field] = {"old": str(old_val), "new": str(value)}

    log_audit(session, "todo", todo.id, "UPDATE", trainer.id, changes or None)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return _to_response(todo)


@router.patch("/{todo_id}/toggle", response_model=TodoResponse)
def toggle_todo(
    todo_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Toggle completato/non completato. Aggiorna completed_at."""
    todo = _bouncer_todo(session, todo_id, trainer.id)

    todo.completato = not todo.completato
    todo.completed_at = datetime.now(timezone.utc) if todo.completato else None

    log_audit(session, "todo", todo.id, "UPDATE", trainer.id, {
        "completato": {"old": not todo.completato, "new": todo.completato},
    })
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return _to_response(todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Soft-delete un todo."""
    todo = _bouncer_todo(session, todo_id, trainer.id)

    todo.deleted_at = datetime.now(timezone.utc)
    session.add(todo)
    log_audit(session, "todo", todo.id, "DELETE", trainer.id)
    session.commit()


# ── Helper ──

def _to_response(todo: Todo) -> TodoResponse:
    return TodoResponse(
        id=todo.id,
        titolo=todo.titolo,
        descrizione=todo.descrizione,
        data_scadenza=str(todo.data_scadenza) if todo.data_scadenza else None,
        completato=todo.completato,
        completed_at=str(todo.completed_at) if todo.completed_at else None,
        created_at=str(todo.created_at),
    )
