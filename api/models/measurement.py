"""
Modelli Measurement — tracking misurazioni corporee e prestazionali.

Metric: catalogo 22 metriche standard (peso, composizione, circonferenze, forza, cardio).
ClientMeasurement: sessione di misurazione per un cliente (data + note).
MeasurementValue: singolo valore misurato per sessione.

Metric: catalogo globale, nessun trainer_id.
ClientMeasurement: trainer_id per bouncer + id_cliente per ownership chain.
MeasurementValue: segue lifecycle della sessione padre (no deleted_at).
"""

from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Metric(SQLModel, table=True):
    """Catalogo metriche — pre-seeded, condiviso tra tutti i trainer."""
    __tablename__ = "metriche"

    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str                               # "Peso Corporeo"
    nome_en: str                            # "Body Weight"
    unita_misura: str                       # "kg", "%", "cm", "bpm", "mmHg"
    categoria: str = Field(index=True)      # MetricCategory enum value
    ordinamento: int = Field(default=0)     # display order within category


class ClientMeasurement(SQLModel, table=True):
    """Sessione di misurazione per un cliente."""
    __tablename__ = "misurazioni_cliente"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_cliente: int = Field(foreign_key="clienti.id", index=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    data_misurazione: date
    note: Optional[str] = None
    deleted_at: Optional[datetime] = None


class MeasurementValue(SQLModel, table=True):
    """Singolo valore misurato in una sessione."""
    __tablename__ = "valori_misurazione"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_misurazione: int = Field(foreign_key="misurazioni_cliente.id", index=True)
    id_metrica: int = Field(foreign_key="metriche.id", index=True)
    valore: float
