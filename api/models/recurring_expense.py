# api/models/recurring_expense.py
"""
Modello RecurringExpense — mappa la tabella 'spese_ricorrenti'.

Rappresenta le spese fisse (affitto, assicurazione, utenze, ecc.)
che generano promemoria periodici. L'utente conferma esplicitamente
ogni occorrenza per creare il CashMovement nel ledger.

Campi chiave:
- data_inizio: data scelta dall'utente per l'inizio del ciclo (ancoraggio frequenze)
- data_creazione: timestamp di creazione del record (audit trail, non usato per ancoraggio)
"""

from datetime import date, datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class RecurringExpense(SQLModel, table=True):
    """
    ORM model per la tabella 'spese_ricorrenti'.

    Ogni record definisce una spesa ricorrente con frequenza e giorno di scadenza.
    Il campo 'attiva' permette di disabilitare senza eliminare.
    Il campo 'data_inizio' ancora le frequenze non-mensili (TRIM/SEM/ANN).
    """
    __tablename__ = "spese_ricorrenti"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: Optional[int] = Field(default=None, foreign_key="trainers.id", index=True)
    nome: str
    categoria: Optional[str] = None
    importo: float
    frequenza: Optional[str] = Field(default="MENSILE")
    giorno_scadenza: int = Field(default=1)
    data_inizio: Optional[date] = Field(default_factory=date.today)
    attiva: bool = Field(default=True)
    data_creazione: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    data_disattivazione: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = None
