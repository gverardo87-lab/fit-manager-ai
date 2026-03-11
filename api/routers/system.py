"""Endpoint protetti di diagnostica runtime."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.database import get_catalog_session, get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.schemas.system import (
    ConnectivityConfigRequest,
    ConnectivityConfigResponse,
    ConnectivityStatusResponse,
    ConnectivityVerifyResponse,
    SupportSnapshotResponse,
)
from api.services.connectivity_config import apply_connectivity_config
from api.services.connectivity_runtime import build_connectivity_status
from api.services.connectivity_verify import verify_connectivity_setup
from api.services.system_runtime import build_support_snapshot

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/connectivity-status", response_model=ConnectivityStatusResponse)
def get_connectivity_status(
    _trainer: Trainer = Depends(get_current_trainer),
):
    """Stato read-only della connettivita locale: Tailscale, Funnel e base URL."""
    return build_connectivity_status()


@router.post("/connectivity-config", response_model=ConnectivityConfigResponse)
def update_connectivity_config(
    payload: ConnectivityConfigRequest,
    _trainer: Trainer = Depends(get_current_trainer),
):
    """Applica solo la configurazione FitManager: profilo, flag portale e base URL."""
    return apply_connectivity_config(payload)


@router.post("/connectivity-verify", response_model=ConnectivityVerifyResponse)
def run_connectivity_verification(
    _trainer: Trainer = Depends(get_current_trainer),
):
    """Verifica on-demand che la configurazione salvata sia davvero pronta all'uso."""
    return verify_connectivity_setup()


@router.get("/support-snapshot", response_model=SupportSnapshotResponse)
def get_support_snapshot(
    _trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
):
    """Snapshot read-only per supporto: runtime, licenza e backup recenti."""
    return build_support_snapshot(session, catalog_session)
