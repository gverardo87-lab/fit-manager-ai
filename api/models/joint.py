"""
Modello Joint + ExerciseJoint — tassonomia articolare scientifica.

Joint: catalogo ~15 articolazioni principali.
ExerciseJoint: relazione M:N esercizio-articolazione con ruolo e ROM.

Nessun trainer_id: catalogo globale condiviso.
"""

from typing import Optional

from sqlmodel import Field, SQLModel


class Joint(SQLModel, table=True):
    __tablename__ = "articolazioni"

    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True)          # Italiano: "Ginocchio"
    nome_en: str                            # Inglese: "Knee"
    tipo: str                               # hinge, ball_and_socket, pivot, condyloid, saddle, gliding
    regione: str                            # upper_body, lower_body, spine


class ExerciseJoint(SQLModel, table=True):
    __tablename__ = "esercizi_articolazioni"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_esercizio: int = Field(foreign_key="esercizi.id", index=True)
    id_articolazione: int = Field(foreign_key="articolazioni.id", index=True)
    ruolo: str                              # agonist, stabilizer
    rom_gradi: Optional[int] = None         # range of motion in gradi (opzionale)
