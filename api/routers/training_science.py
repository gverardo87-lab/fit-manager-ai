"""
Endpoint Training Science Engine — Generazione e analisi piani scientifici.

Endpoint:
  POST   /training-science/plan          -> genera piano settimanale volume-driven
  POST   /training-science/plan-package  -> orchestration runtime SMART DB-aware
  POST   /training-science/analyze       -> analisi 4D di un piano esistente
  POST   /training-science/mesocycle     -> genera mesociclo da piano base
  GET    /training-science/volume-targets -> target volume per livello x obiettivo
  GET    /training-science/parameters     -> parametri di carico per obiettivo

`/plan`, `/analyze` e `/mesocycle` restano computazionali puri (zero DB).
`/plan-package` e' additivo e orchestration-aware per il cutover SMART backend-first.
Autenticazione JWT obbligatoria (il motore e' una feature del prodotto).
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session

from api.database import get_catalog_session, get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.schemas.training_science import TSPlanPackage, TSPlanPackageRequest
from api.services.training_science import (
    Obiettivo,
    Livello,
    TemplatePiano,
    AnalisiPiano,
    ParametriCarico,
    VolumeTarget,
    Mesociclo,
    build_plan,
    analyze_plan,
    build_mesocycle,
    get_parametri,
    get_all_volume_targets,
)
from api.services.training_science.runtime import build_plan_package

router = APIRouter(prefix="/training-science", tags=["training-science"])


# ════════════════════════════════════════════════════════════
# SCHEMA INPUT — Pydantic v2
# ════════════════════════════════════════════════════════════


class PlanRequest(BaseModel):
    """Richiesta generazione piano settimanale."""

    model_config = {"extra": "forbid"}

    frequenza: int = Field(ge=2, le=6, description="Sessioni per settimana (2-6)")
    obiettivo: Obiettivo
    livello: Livello


class AnalyzeRequest(BaseModel):
    """Richiesta analisi di un piano esistente."""

    model_config = {"extra": "forbid"}

    piano: TemplatePiano


class MesocycleRequest(BaseModel):
    """Richiesta generazione mesociclo da piano base."""

    model_config = {"extra": "forbid"}

    piano_base: TemplatePiano


# ════════════════════════════════════════════════════════════
# ENDPOINT — Generazione e analisi
# ════════════════════════════════════════════════════════════


@router.post("/plan", response_model=TemplatePiano)
def generate_plan(
    data: PlanRequest,
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Genera un piano di allenamento settimanale volume-driven.

    Algoritmo deterministico a 4 fasi:
    1. Struttura compound base (split_logic + session_order)
    2. Boost serie compound per muscoli carenti
    3. Compensazione con isolamento (matrice EMG + MEV/MAV)
    4. Feedback loop se deficit persistono

    Il piano e' un template: definisce pattern, serie, rep range, riposo.
    Il trainer associa poi gli esercizi concreti del catalogo.
    """
    return build_plan(data.frequenza, data.obiettivo, data.livello)


@router.post("/plan-package", response_model=TSPlanPackage)
def generate_plan_package(
    data: TSPlanPackageRequest,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
):
    """
    Costruisce il package SMART per il primo cutover backend-first.

    Include:
    - profilo scientifico risolto dal cliente reale
    - piano scientifico canonico
    - ranking deterministico per slot
    - workout projection compatibile col salvataggio attuale

    Questo endpoint e' DB-aware perche' integra cliente, anamnesi,
    safety map e catalogo esercizi nel runtime orchestration layer.
    """
    return build_plan_package(
        session=session,
        catalog_session=catalog_session,
        trainer=trainer,
        request=data,
    )


@router.post("/analyze", response_model=AnalisiPiano)
def analyze_existing_plan(
    data: AnalyzeRequest,
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Analisi scientifica completa di un piano su 4 dimensioni:
    1. Volume — serie effettive per muscolo vs MEV/MAV/MRV
    2. Bilanciamento — rapporti biomeccanici push:pull, quad:ham
    3. Frequenza — stimoli settimanali per muscolo
    4. Recupero — overlap muscolare tra sessioni consecutive

    Score composito 0-100 con pesi trasparenti:
    volume 40, balance 25, frequenza 20, recupero 15.
    """
    return analyze_plan(data.piano)


@router.post("/mesocycle", response_model=Mesociclo)
def generate_mesocycle(
    data: MesocycleRequest,
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Genera un mesociclo completo da un piano settimanale base.

    Periodizzazione ondulata a blocchi (Israetel RP 2020, Bompa 2019):
    - Progressione volume lineare (base -> picco)
    - Deload finale a ~50% (Helms 2019)
    - Durata per livello: principiante 4, intermedio 5, avanzato 6 settimane

    Il piano base viene scalato nelle serie (non nell'intensita').
    """
    return build_mesocycle(data.piano_base)


# ════════════════════════════════════════════════════════════
# ENDPOINT — Dati di riferimento (read-only)
# ════════════════════════════════════════════════════════════


@router.get("/parameters/{obiettivo}", response_model=ParametriCarico)
def get_load_parameters(
    obiettivo: Obiettivo,
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Parametri di carico per un obiettivo (NSCA/ACSM/Schoenfeld).

    Ritorna: intensita, rep range, serie, riposo, frequenza, fonte.
    """
    return get_parametri(obiettivo)


@router.get("/volume-targets", response_model=list[VolumeTarget])
def get_volume_targets(
    livello: Livello,
    obiettivo: Obiettivo,
    trainer: Trainer = Depends(get_current_trainer),
):
    """
    Target di volume (MEV/MAV/MRV) per tutti i 15 gruppi muscolari.

    I target sono scalati per obiettivo (fattore_volume da principles.py).
    Fonte: Israetel RP 2020, Schoenfeld 2017, Krieger 2010.
    """
    targets = get_all_volume_targets(livello, obiettivo)
    return list(targets.values())
