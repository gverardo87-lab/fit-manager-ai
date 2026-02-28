"""
Modello ClientGoal — obiettivi strutturati per cliente.

Ogni obiettivo collega un cliente a una metrica specifica con direzione,
target opzionale, baseline congelata, timeframe e priorita'.

Multi-tenancy: trainer_id diretto (bouncer pattern senza join).
Deep IDOR: id_cliente -> Client.trainer_id per doppia verifica.
"""

from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ClientGoal(SQLModel, table=True):
    """Obiettivo strutturato per un cliente."""
    __tablename__ = "obiettivi_cliente"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_cliente: int = Field(foreign_key="clienti.id", index=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    id_metrica: int = Field(foreign_key="metriche.id")

    # Direzione e target
    direzione: str                          # aumentare | diminuire | mantenere
    valore_target: Optional[float] = None   # NULL = migliorare senza target numerico

    # Baseline congelata alla creazione
    valore_baseline: Optional[float] = None
    data_baseline: Optional[date] = None

    # Timeframe
    data_inizio: date
    data_scadenza: Optional[date] = None

    # Categoria e priorita'
    tipo_obiettivo: str = Field(default="corporeo", index=True)  # corporeo | atletico
    priorita: int = Field(default=3)        # 1 (max) → 5 (min)
    stato: str = Field(default="attivo", index=True)  # attivo | raggiunto | abbandonato
    completed_at: Optional[datetime] = None
    completato_automaticamente: bool = Field(default=False)

    # Meta
    note: Optional[str] = None
    deleted_at: Optional[datetime] = None
