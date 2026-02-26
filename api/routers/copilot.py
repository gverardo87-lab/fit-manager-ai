# api/routers/copilot.py
"""
Endpoint Copilot AI — assistente integrato nel workout builder.

Due endpoint:
- POST /suggest-exercise — suggerimento rapido 3 esercizi (button click)
- POST /chat — agente conversazionale con intent routing

Bouncer Pattern: verifica ownership scheda via Deep IDOR chain.
Ollama locale (gemma2:9b), zero dati verso cloud.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.workout import WorkoutPlan
from api.schemas.copilot import (
    SuggestExerciseRequest,
    SuggestExerciseResponse,
    ExerciseSuggestion,
    CopilotChatRequest,
    CopilotChatResponse,
)
from api.services.workout_copilot import suggest_next_exercise, handle_chat

logger = logging.getLogger("fitmanager.routers.copilot")

router = APIRouter(prefix="/copilot", tags=["copilot"])


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════


def _bouncer_workout(session: Session, workout_id: int, trainer_id: int) -> WorkoutPlan:
    """Bouncer: verifica ownership scheda. 404 se non trovata o non propria."""
    plan = session.exec(
        select(WorkoutPlan).where(
            WorkoutPlan.id == workout_id,
            WorkoutPlan.trainer_id == trainer_id,
            WorkoutPlan.deleted_at == None,
        )
    ).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheda non trovata",
        )
    return plan


# ════════════════════════════════════════════════════════════
# POST: Suggerisci prossimo esercizio (button click)
# ════════════════════════════════════════════════════════════


@router.post("/suggest-exercise", response_model=SuggestExerciseResponse)
def suggest_exercise(
    data: SuggestExerciseRequest,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Suggerisce 3 esercizi per la sessione corrente del workout builder.

    Pipeline: Bouncer → analisi pattern → query candidati SQL → Ollama → validazione.
    Tempo risposta: ~5-15s (dipende da Ollama).
    """
    # Bouncer: verifica ownership scheda
    plan = _bouncer_workout(session, data.id_scheda, trainer.id)

    try:
        suggestions = suggest_next_exercise(
            session=session,
            plan=plan,
            sezione=data.sezione,
            current_exercise_ids=data.exercise_ids,
            trainer_id=trainer.id,
            focus_muscolare=data.focus_muscolare,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    return SuggestExerciseResponse(
        suggestions=[ExerciseSuggestion(**s) for s in suggestions],
    )


# ════════════════════════════════════════════════════════════
# POST: Chat conversazionale
# ════════════════════════════════════════════════════════════


@router.post("/chat", response_model=CopilotChatResponse)
def chat(
    data: CopilotChatRequest,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Agente conversazionale per il workout builder.

    Pipeline: Bouncer → intent routing → capability dispatch → Ollama → response.
    Tempo risposta: ~5-20s (dipende da intent e Ollama).

    Non ritorna mai 500 — errori Ollama gestiti con graceful fallback.
    """
    # Bouncer: verifica ownership scheda
    plan = _bouncer_workout(session, data.plan_id, trainer.id)

    return handle_chat(
        db=session,
        plan=plan,
        request=data,
        trainer_id=trainer.id,
    )
