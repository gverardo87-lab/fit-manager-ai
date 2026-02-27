"""
Modello MedicalCondition + ExerciseCondition — controindicazioni strutturate.

MedicalCondition: catalogo ~30 condizioni mediche rilevanti per l'allenamento.
ExerciseCondition: relazione M:N esercizio-condizione con severita' e nota.

Sostituira' il campo JSON 'controindicazioni' con relazioni normalizzate.
Nessun trainer_id: catalogo globale condiviso.
"""

from typing import Optional

from sqlmodel import Field, SQLModel


class MedicalCondition(SQLModel, table=True):
    __tablename__ = "condizioni_mediche"

    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True)          # Italiano: "Ernia del disco lombare"
    nome_en: str                            # Inglese: "Lumbar disc herniation"
    categoria: str = Field(index=True)      # orthopedic, cardiovascular, metabolic, neurological
    body_tags: Optional[str] = None         # JSON: ["schiena", "lombare"] — match con anamnesi


class ExerciseCondition(SQLModel, table=True):
    __tablename__ = "esercizi_condizioni"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_esercizio: int = Field(foreign_key="esercizi.id", index=True)
    id_condizione: int = Field(foreign_key="condizioni_mediche.id", index=True)
    severita: str                           # avoid, caution, modify
    nota: Optional[str] = None              # nota specifica: perche'/come adattare
