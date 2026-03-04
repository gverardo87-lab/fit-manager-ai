"""
Endpoint Assistant CRM — NLP deterministico per comandi testuali italiani.

2 endpoint:
  POST /assistant/parse   -> analisi testo (read-only, zero side effects)
  POST /assistant/commit  -> esegue operazione confermata

Feature flag: ASSISTANT_V1_ENABLED (default true).
"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from api.database import get_catalog_session, get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.schemas.assistant import (
    CommitRequest,
    CommitResponse,
    ParseRequest,
    ParseResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assistant", tags=["assistant"])

ASSISTANT_ENABLED = os.getenv("ASSISTANT_V1_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
)


def _check_enabled() -> None:
    if not ASSISTANT_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant non abilitato",
        )


@router.post("/parse", response_model=ParseResponse)
def parse_text(
    data: ParseRequest,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
) -> ParseResponse:
    """
    Analizza testo in linguaggio naturale e restituisce operazioni strutturate.

    Read-only: legge solo la lista clienti per entity resolution.
    Zero side effects sul DB.
    """
    _check_enabled()

    from api.services.assistant_parser import orchestrate

    return orchestrate(data.text, trainer, session, catalog_session)


@router.post("/commit", response_model=CommitResponse)
def commit_operation(
    data: CommitRequest,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
) -> CommitResponse:
    """
    Esegue un'operazione confermata dall'utente.

    Dispatcha all'endpoint di dominio appropriato (create_event,
    create_manual_movement, create_measurement).
    """
    _check_enabled()

    from api.services.assistant_parser.commit_dispatcher import dispatch

    return dispatch(data.intent, data.payload, trainer, session, catalog_session)
