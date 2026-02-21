# api/models/movement.py
"""
Modello CashMovement — mappa la tabella 'movimenti_cassa' esistente in SQLite.

IMPORTANTE: la tabella esiste gia' con 16 record.
La colonna trainer_id viene aggiunta dalla migrazione in api/main.py.

Multi-tenancy:
- trainer_id: FK diretta verso trainers (ogni movimento appartiene a un trainer)

Questo modello e' il libro mastro (ledger) dell'applicazione.
Ogni pagamento rata e ogni acconto DEVONO generare un CashMovement
per mantenere la coerenza contabile.
"""

from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from api.models.contract import Contract
    from api.models.rate import Rate


class CashMovement(SQLModel, table=True):
    """
    ORM model per la tabella 'movimenti_cassa' esistente.

    Mappa 1:1 le colonne SQLite. Il campo trainer_id e' la FK
    per la multi-tenancy.

    Relationships:
    - contract: Contract associato (N:1, opzionale)
    - rate: Rate associata (N:1, opzionale — solo per pagamenti rata)
    """
    __tablename__ = "movimenti_cassa"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: Optional[int] = Field(default=None, foreign_key="trainers.id", index=True)
    data_movimento: Optional[datetime] = Field(default_factory=datetime.utcnow)
    data_effettiva: date = Field(default_factory=date.today)
    tipo: str  # ENTRATA | USCITA
    categoria: Optional[str] = None
    importo: float
    metodo: Optional[str] = None
    id_cliente: Optional[int] = Field(default=None, foreign_key="clienti.id")
    id_contratto: Optional[int] = Field(default=None, foreign_key="contratti.id")
    id_rata: Optional[int] = Field(default=None, foreign_key="rate_programmate.id")
    note: Optional[str] = None
    operatore: str = Field(default="API")
    id_spesa_ricorrente: Optional[int] = None

    # Relationships
    contract: Optional["Contract"] = Relationship(back_populates="movements")
    rate: Optional["Rate"] = Relationship(back_populates="movements")
