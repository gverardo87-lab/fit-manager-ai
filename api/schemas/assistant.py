"""
Schemas per l'Assistant CRM — parse + commit.

Flusso:
  1. POST /assistant/parse   -> ParseRequest -> ParseResponse (read-only)
  2. POST /assistant/commit   -> CommitRequest -> CommitResponse (write)
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════
# PARSE
# ════════════════════════════════════════════════════════════


class ResolvedEntity(BaseModel):
    """Entita' risolta: testo -> record DB."""

    type: str  # "client", "metric", "category", "date", "time", "amount", "method"
    raw: str  # testo originale estratto
    value: Any  # valore risolto (id, stringa, numero)
    label: str  # label leggibile ("Marco Rossi", "Peso Corporeo")
    confidence: float = Field(ge=0.0, le=1.0)


class AmbiguityItem(BaseModel):
    """Piu' candidati possibili per un campo."""

    field: str  # es. "id_cliente"
    candidates: list[ResolvedEntity]
    message: str  # messaggio italiano ("Quale cliente intendi?")


class ParsedOperation(BaseModel):
    """Singola operazione riconosciuta dal parser."""

    intent: str  # es. "agenda.create_event"
    payload: dict[str, Any]  # dati pronti per il commit
    preview_label: str  # es. "Sessione PT con Marco Rossi, domani 18:00-19:00"
    confidence: float = Field(ge=0.0, le=1.0)


class ParseRequest(BaseModel):
    """Input: testo in linguaggio naturale italiano."""

    model_config = {"extra": "forbid"}

    text: str = Field(min_length=2, max_length=500)


class ParseResponse(BaseModel):
    """Output del parsing: operazioni riconosciute + ambiguita'."""

    success: bool
    operations: list[ParsedOperation] = []
    ambiguities: list[AmbiguityItem] = []
    entities: list[ResolvedEntity] = []
    message: str  # feedback italiano ("Ho capito: ...")
    raw_text: str  # echo del testo originale


# ════════════════════════════════════════════════════════════
# COMMIT
# ════════════════════════════════════════════════════════════


class CommitRequest(BaseModel):
    """Conferma un'operazione parsed."""

    model_config = {"extra": "forbid"}

    intent: str
    payload: dict[str, Any]


class CommitResponse(BaseModel):
    """Risultato del commit — include le query key da invalidare."""

    success: bool
    message: str  # feedback italiano ("Evento creato!")
    created_id: Optional[int] = None
    entity_type: str  # "event" | "movement" | "measurement"
    invalidate: list[str] = []  # query key React Query
    navigate_to: Optional[str] = None  # URL opzionale post-commit
