"""
Modello Muscle + ExerciseMuscle — tassonomia muscolare scientifica.

Muscle: catalogo ~52 muscoli anatomici (livello NSCA/ACSM professionale).
ExerciseMuscle: relazione M:N esercizio-muscolo con ruolo e attivazione.

Nessun trainer_id: catalogo globale condiviso.
"""

from typing import Optional

from sqlmodel import Field, SQLModel


class Muscle(SQLModel, table=True):
    __tablename__ = "muscoli"

    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True)          # Italiano: "Grande pettorale"
    nome_en: str                            # Inglese NSCA: "Pectoralis major"
    gruppo: str = Field(index=True)         # quadriceps, hamstrings, glutes, chest, back, ...
    regione: str                            # upper_body, lower_body, core


class ExerciseMuscle(SQLModel, table=True):
    __tablename__ = "esercizi_muscoli"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_esercizio: int = Field(foreign_key="esercizi.id", index=True)
    id_muscolo: int = Field(foreign_key="muscoli.id", index=True)
    ruolo: str                              # primary, secondary, stabilizer
    attivazione: Optional[int] = None       # 0-100 percentuale attivazione (opzionale)
