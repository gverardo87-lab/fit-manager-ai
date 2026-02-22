# api/models/recurring_expense.py
"""
Modello RecurringExpense — mappa la tabella 'spese_ricorrenti' esistente.

Rappresenta le spese fisse mensili (affitto, assicurazione, utenze, ecc.)
che contribuiscono al calcolo del Margine Netto Mensile.

La tabella esiste gia' nel DB legacy (creata da Streamlit).
La colonna trainer_id viene aggiunta dalla migrazione in api/main.py.
"""

from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class RecurringExpense(SQLModel, table=True):
    """
    ORM model per la tabella 'spese_ricorrenti'.

    Ogni record e' una spesa fissa mensile con un giorno di scadenza.
    Il campo 'attiva' permette di disabilitare senza eliminare.
    """
    __tablename__ = "spese_ricorrenti"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: Optional[int] = Field(default=None, foreign_key="trainers.id", index=True)
    nome: str
    categoria: Optional[str] = None
    importo: float
    frequenza: Optional[str] = Field(default="MENSILE")
    giorno_inizio: int = Field(default=1)
    giorno_scadenza: int = Field(default=1)
    data_prossima_scadenza: Optional[date] = None
    attiva: bool = Field(default=True)
    data_creazione: Optional[datetime] = Field(default_factory=datetime.utcnow)
    data_disattivazione: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = None
