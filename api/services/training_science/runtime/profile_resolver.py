"""Resolver DB-aware del profilo scientifico richiesto dal plan-package."""

from dataclasses import dataclass

from fastapi import HTTPException
from sqlmodel import Session, func, select

from api.models.client import Client
from api.models.goal import ClientGoal
from api.models.measurement import ClientMeasurement
from api.models.trainer import Trainer
from api.schemas.safety import SafetyMapResponse
from api.schemas.training_science import TSPlanPackageRequest, TSScientificProfileResolved
from api.services.safety_engine import build_safety_map

from .mappings import (
    BUILDER_LEVEL_TO_SCIENTIFIC,
    BUILDER_OBJECTIVE_TO_SCIENTIFIC,
    SCIENTIFIC_LEVEL_TO_WORKOUT,
)
from .readiness import get_anamnesi_state


@dataclass(frozen=True)
class ResolvedPlanContext:
    """Output composito del resolver per la build del package."""

    client: Client | None
    scientific_profile: TSScientificProfileResolved
    safety_map: SafetyMapResponse | None


def _resolve_level(
    request: TSPlanPackageRequest,
    measurements_count: int,
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if request.preset.livello_override is not None:
        warnings.append("Livello override esplicito applicato dal trainer.")
        return request.preset.livello_override, warnings
    if request.preset.livello_choice != "auto":
        return request.preset.livello_choice, warnings
    if measurements_count < 1:
        warnings.append("Auto-level fallback: nessuna misurazione disponibile, uso beginner.")
        return "beginner", warnings
    if measurements_count < 3:
        warnings.append("Auto-level euristico: profilo dati parziale, uso beginner conservativo.")
        return "beginner", warnings
    warnings.append("Auto-level euristico: profilo dati minimo disponibile, uso intermedio.")
    return "intermedio", warnings


def resolve_plan_context(
    *,
    session: Session,
    catalog_session: Session,
    trainer: Trainer,
    request: TSPlanPackageRequest,
) -> ResolvedPlanContext:
    """Risolve ownership cliente, anamnesi, safety e mapping builder->scienza."""
    warnings: list[str] = []
    client: Client | None = None
    safety_map: SafetyMapResponse | None = None
    anamnesi_state = "missing"
    active_goals_count = 0
    measurements_count = 0

    if request.client_id is not None:
        client = session.get(Client, request.client_id)
        if client is None or client.deleted_at is not None or client.trainer_id != trainer.id:
            raise HTTPException(status_code=404, detail="Cliente non trovato")

        anamnesi_state = get_anamnesi_state(client.anamnesi_json)
        safety_map = build_safety_map(
            session=session,
            catalog_session=catalog_session,
            client_id=client.id,
            trainer_id=trainer.id,
        )
        measurements_count = int(
            session.exec(
                select(func.count())
                .select_from(ClientMeasurement)
                .where(ClientMeasurement.id_cliente == client.id)
                .where(ClientMeasurement.deleted_at.is_(None))
            ).one()
        )
        active_goals_count = int(
            session.exec(
                select(func.count())
                .select_from(ClientGoal)
                .where(ClientGoal.id_cliente == client.id)
                .where(ClientGoal.stato == "attivo")
                .where(ClientGoal.deleted_at.is_(None))
            ).one()
        )
    else:
        warnings.append("Nessun cliente associato: profilo scientifico generato senza anamnesi e safety map.")

    resolved_level_key, level_warnings = _resolve_level(request, measurements_count)
    warnings.extend(level_warnings)

    if request.preset.mode == "clinical" and anamnesi_state != "structured":
        warnings.append("Mode clinical con anamnesi non strutturata: ranking safety meno affidabile.")
    if active_goals_count == 0 and request.client_id is not None:
        warnings.append("Cliente senza obiettivi attivi: uso solo preset builder come intent di generazione.")
    if request.preset.obiettivo_builder == "generale":
        warnings.append("Builder 'generale' mappato a obiettivo scientifico 'tonificazione'.")

    livello_scientifico = BUILDER_LEVEL_TO_SCIENTIFIC[resolved_level_key]
    obiettivo_scientifico = BUILDER_OBJECTIVE_TO_SCIENTIFIC[request.preset.obiettivo_builder]

    profile = TSScientificProfileResolved(
        obiettivo_builder=request.preset.obiettivo_builder,
        obiettivo_scientifico=obiettivo_scientifico,
        livello_scientifico=livello_scientifico,
        livello_workout=SCIENTIFIC_LEVEL_TO_WORKOUT[livello_scientifico],
        mode=request.preset.mode,
        anamnesi_state=anamnesi_state,
        safety_condition_count=safety_map.condition_count if safety_map is not None else 0,
        profile_warnings=warnings,
    )
    return ResolvedPlanContext(
        client=client,
        scientific_profile=profile,
        safety_map=safety_map,
    )
