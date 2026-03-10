# api/routers/workouts.py
"""
Endpoint Schede Allenamento — CRUD con Bouncer Pattern + Deep Relational IDOR.

Gerarchia: WorkoutPlan → WorkoutSession → SessionBlock / WorkoutExercise
IDOR chain: WorkoutExercise → WorkoutSession → WorkoutPlan.trainer_id

Operazioni atomiche: plan + sessioni + blocchi + esercizi in una transazione.
Full-replace sessions: DELETE old → INSERT new (semplice e sicuro).
"""

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.exercise import Exercise
from api.models.workout import WorkoutPlan, WorkoutSession, SessionBlock, WorkoutExercise
from api.models.workout_log import WorkoutLog
from api.schemas.workout import (
    WorkoutPlanCreate, WorkoutPlanUpdate, WorkoutSessionInput,
    WorkoutPlanResponse, WorkoutPlanListResponse,
    WorkoutSessionResponse, WorkoutExerciseResponse,
    SessionBlockResponse,
)
from api.routers._audit import log_audit

router = APIRouter(prefix="/workouts", tags=["workouts"])


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _bouncer_workout(session: Session, workout_id: int, trainer_id: int) -> WorkoutPlan:
    """Bouncer: verifica ownership scheda. 404 se non trovata o non propria."""
    plan = session.exec(
        select(WorkoutPlan).where(
            WorkoutPlan.id == workout_id,
            WorkoutPlan.trainer_id == trainer_id,
            WorkoutPlan.deleted_at == None,  # noqa: E711
        )
    ).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheda non trovata",
        )
    return plan


def _check_client_ownership(session: Session, client_id: int, trainer_id: int) -> None:
    """Relational IDOR: verifica che il cliente appartenga al trainer."""
    client = session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.trainer_id == trainer_id,
            Client.deleted_at == None,  # noqa: E711
        )
    ).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente non trovato",
        )


def _validate_exercise_ids(session: Session, exercise_ids: set[int], trainer_id: int) -> None:
    """Verifica che tutti gli id_esercizio esistano e siano accessibili."""
    if not exercise_ids:
        return
    existing = session.exec(
        select(Exercise.id).where(
            Exercise.id.in_(exercise_ids),
            Exercise.deleted_at == None,  # noqa: E711
            (Exercise.trainer_id == None) | (Exercise.trainer_id == trainer_id),  # noqa: E711
        )
    ).all()
    found = set(existing)
    missing = exercise_ids - found
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Esercizi non trovati: {sorted(missing)}",
        )


def _build_exercise_response(
    e: WorkoutExercise,
    exercise_map: dict[int, Exercise],
) -> WorkoutExerciseResponse:
    """Costruisce WorkoutExerciseResponse da un WorkoutExercise DB row."""
    ref = exercise_map.get(e.id_esercizio)
    return WorkoutExerciseResponse(
        id=e.id,
        id_esercizio=e.id_esercizio,
        esercizio_nome=ref.nome if ref else f"Esercizio #{e.id_esercizio}",
        esercizio_categoria=ref.categoria if ref else "",
        esercizio_attrezzatura=ref.attrezzatura if ref else "",
        ordine=e.ordine,
        serie=e.serie,
        ripetizioni=e.ripetizioni,
        tempo_riposo_sec=e.tempo_riposo_sec,
        tempo_esecuzione=e.tempo_esecuzione,
        carico_kg=e.carico_kg,
        note=e.note,
    )


def _build_plan_response(
    session: Session,
    plan: WorkoutPlan,
    client_map: dict[int, Client] | None = None,
) -> WorkoutPlanResponse:
    """
    Costruisce WorkoutPlanResponse con sessioni + esercizi + blocchi enriched.
    Query batch: plan → sessioni → blocchi → esercizi → JOIN esercizi catalogo.
    """
    # 1. Sessioni della scheda
    sessions = session.exec(
        select(WorkoutSession)
        .where(WorkoutSession.id_scheda == plan.id)
        .order_by(WorkoutSession.numero_sessione)
    ).all()

    client = _get_client(session, plan, client_map)

    if not sessions:
        return WorkoutPlanResponse(
            **_plan_base(plan, client),
            sessioni=[],
        )

    session_ids = [s.id for s in sessions]

    # 2. Blocchi di tutte le sessioni (batch IN)
    blocks = session.exec(
        select(SessionBlock)
        .where(SessionBlock.id_sessione.in_(session_ids))
        .order_by(SessionBlock.ordine)
    ).all()

    # 3. Esercizi di tutte le sessioni (batch IN — straight: id_blocco IS NULL)
    all_exercises = session.exec(
        select(WorkoutExercise)
        .where(WorkoutExercise.id_sessione.in_(session_ids))
        .order_by(WorkoutExercise.ordine)
    ).all()

    # 4. JOIN esercizi catalogo (batch IN per tutti gli id_esercizio usati)
    exercise_ref_ids = list({e.id_esercizio for e in all_exercises})
    exercise_map: dict[int, Exercise] = {}
    if exercise_ref_ids:
        refs = session.exec(
            select(Exercise).where(Exercise.id.in_(exercise_ref_ids))
        ).all()
        exercise_map = {r.id: r for r in refs}

    # Raggruppa esercizi per sessione (straight: id_blocco None)
    straight_by_session: dict[int, list[WorkoutExercise]] = {}
    # Raggruppa esercizi per blocco
    exercises_by_block: dict[int, list[WorkoutExercise]] = {}

    for e in all_exercises:
        if e.id_blocco is None:
            straight_by_session.setdefault(e.id_sessione, []).append(e)
        else:
            exercises_by_block.setdefault(e.id_blocco, []).append(e)

    # Raggruppa blocchi per sessione
    blocks_by_session: dict[int, list[SessionBlock]] = {}
    for b in blocks:
        blocks_by_session.setdefault(b.id_sessione, []).append(b)

    # Build response
    session_responses = []
    for s in sessions:
        # Straight exercises
        straight_exs = straight_by_session.get(s.id, [])
        ex_responses = [_build_exercise_response(e, exercise_map) for e in straight_exs]

        # Blocks con loro esercizi
        block_responses = []
        for b in blocks_by_session.get(s.id, []):
            block_exs = exercises_by_block.get(b.id, [])
            # Ordina per posizione_nel_blocco se disponibile, altrimenti ordine
            block_exs.sort(key=lambda e: (e.posizione_nel_blocco or e.ordine))
            block_responses.append(SessionBlockResponse(
                id=b.id,
                tipo_blocco=b.tipo_blocco,
                ordine=b.ordine,
                nome=b.nome,
                giri=b.giri,
                durata_lavoro_sec=b.durata_lavoro_sec,
                durata_riposo_sec=b.durata_riposo_sec,
                durata_blocco_sec=b.durata_blocco_sec,
                note=b.note,
                esercizi=[_build_exercise_response(e, exercise_map) for e in block_exs],
            ))

        session_responses.append(WorkoutSessionResponse(
            id=s.id,
            numero_sessione=s.numero_sessione,
            nome_sessione=s.nome_sessione,
            focus_muscolare=s.focus_muscolare,
            durata_minuti=s.durata_minuti,
            note=s.note,
            esercizi=ex_responses,
            blocchi=block_responses,
        ))

    return WorkoutPlanResponse(
        **_plan_base(plan, client),
        sessioni=session_responses,
    )


def _plan_base(plan: WorkoutPlan, client: Client | None) -> dict:
    """Campi base della response (senza sessioni)."""
    return {
        "id": plan.id,
        "id_cliente": plan.id_cliente,
        "client_nome": client.nome if client else None,
        "client_cognome": client.cognome if client else None,
        "nome": plan.nome,
        "obiettivo": plan.obiettivo,
        "livello": plan.livello,
        "durata_settimane": plan.durata_settimane,
        "sessioni_per_settimana": plan.sessioni_per_settimana,
        "note": plan.note,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
        "data_inizio": str(plan.data_inizio) if plan.data_inizio else None,
        "data_fine": str(plan.data_fine) if plan.data_fine else None,
    }


def _get_client(
    session: Session,
    plan: WorkoutPlan,
    client_map: dict[int, Client] | None = None,
) -> Client | None:
    if not plan.id_cliente:
        return None
    if client_map and plan.id_cliente in client_map:
        return client_map[plan.id_cliente]
    return session.get(Client, plan.id_cliente)


def _insert_sessions(
    session: Session,
    plan_id: int,
    sessions_input: list[WorkoutSessionInput],
) -> None:
    """Inserisce sessioni + blocchi + esercizi per un plan. Usata da create e full-replace."""
    for idx, sess_in in enumerate(sessions_input, start=1):
        ws = WorkoutSession(
            id_scheda=plan_id,
            numero_sessione=idx,
            nome_sessione=sess_in.nome_sessione,
            focus_muscolare=sess_in.focus_muscolare,
            durata_minuti=sess_in.durata_minuti,
            note=sess_in.note,
        )
        session.add(ws)
        session.flush()  # ottieni ws.id

        # Esercizi straight (non in blocco)
        for ex_in in sess_in.esercizi:
            we = WorkoutExercise(
                id_sessione=ws.id,
                id_blocco=None,
                id_esercizio=ex_in.id_esercizio,
                ordine=ex_in.ordine,
                posizione_nel_blocco=None,
                serie=ex_in.serie,
                ripetizioni=ex_in.ripetizioni,
                tempo_riposo_sec=ex_in.tempo_riposo_sec,
                tempo_esecuzione=ex_in.tempo_esecuzione,
                carico_kg=ex_in.carico_kg,
                note=ex_in.note,
            )
            session.add(we)

        # Blocchi strutturati (circuit, tabata, AMRAP, EMOM, superset)
        for block_in in sess_in.blocchi:
            sb = SessionBlock(
                id_sessione=ws.id,
                tipo_blocco=block_in.tipo_blocco,
                ordine=block_in.ordine,
                nome=block_in.nome,
                giri=block_in.giri,
                durata_lavoro_sec=block_in.durata_lavoro_sec,
                durata_riposo_sec=block_in.durata_riposo_sec,
                durata_blocco_sec=block_in.durata_blocco_sec,
                note=block_in.note,
            )
            session.add(sb)
            session.flush()  # ottieni sb.id

            for pos, ex_in in enumerate(block_in.esercizi, start=1):
                we = WorkoutExercise(
                    id_sessione=ws.id,
                    id_blocco=sb.id,
                    id_esercizio=ex_in.id_esercizio,
                    ordine=block_in.ordine,  # stessa posizione del blocco nella sessione
                    posizione_nel_blocco=pos,
                    serie=ex_in.serie,
                    ripetizioni=ex_in.ripetizioni,
                    tempo_riposo_sec=ex_in.tempo_riposo_sec,
                    tempo_esecuzione=ex_in.tempo_esecuzione,
                    carico_kg=ex_in.carico_kg,
                    note=ex_in.note,
                )
                session.add(we)


def _collect_exercise_ids(sessions: list[WorkoutSessionInput]) -> set[int]:
    """Raccoglie tutti gli id_esercizio da sessioni input (straight + in blocco)."""
    ids: set[int] = set()
    for s in sessions:
        for e in s.esercizi:
            ids.add(e.id_esercizio)
        for b in s.blocchi:
            for e in b.esercizi:
                ids.add(e.id_esercizio)
    return ids


def _delete_sessions_cascade(session: Session, session_ids: list[int]) -> None:
    """Elimina log → esercizi → blocchi → sessioni in ordine corretto (FK)."""
    if not session_ids:
        return
    # 0. Elimina workout logs che referenziano queste sessioni
    old_logs = session.exec(
        select(WorkoutLog).where(WorkoutLog.id_sessione.in_(session_ids))
    ).all()
    for log in old_logs:
        session.delete(log)
    if old_logs:
        session.flush()

    # 1. Elimina tutti gli esercizi delle sessioni
    old_exercises = session.exec(
        select(WorkoutExercise).where(WorkoutExercise.id_sessione.in_(session_ids))
    ).all()
    for e in old_exercises:
        session.delete(e)
    session.flush()

    # 2. Elimina blocchi
    old_blocks = session.exec(
        select(SessionBlock).where(SessionBlock.id_sessione.in_(session_ids))
    ).all()
    for b in old_blocks:
        session.delete(b)
    session.flush()

    # 3. Elimina sessioni
    old_sessions = session.exec(
        select(WorkoutSession).where(WorkoutSession.id.in_(session_ids))
    ).all()
    for s in old_sessions:
        session.delete(s)


# ════════════════════════════════════════════════════════════
# POST: Crea scheda (atomico: plan + sessioni + blocchi + esercizi)
# ════════════════════════════════════════════════════════════

@router.post("", response_model=WorkoutPlanResponse, status_code=status.HTTP_201_CREATED)
def create_workout(
    data: WorkoutPlanCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Crea scheda allenamento completa in una transazione."""
    if data.id_cliente is not None:
        _check_client_ownership(session, data.id_cliente, trainer.id)

    _validate_exercise_ids(session, _collect_exercise_ids(data.sessioni), trainer.id)

    now = datetime.now(timezone.utc).isoformat()

    plan = WorkoutPlan(
        trainer_id=trainer.id,
        id_cliente=data.id_cliente,
        nome=data.nome,
        obiettivo=data.obiettivo,
        livello=data.livello,
        durata_settimane=data.durata_settimane,
        sessioni_per_settimana=data.sessioni_per_settimana,
        note=data.note,
        created_at=now,
        updated_at=now,
    )
    session.add(plan)
    session.flush()

    _insert_sessions(session, plan.id, data.sessioni)

    log_audit(session, "workout_plan", plan.id, "CREATE", trainer.id)
    session.commit()
    session.refresh(plan)

    return _build_plan_response(session, plan)


# ════════════════════════════════════════════════════════════
# GET: Lista schede (paginata + filtri)
# ════════════════════════════════════════════════════════════

@router.get("", response_model=WorkoutPlanListResponse)
def list_workouts(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    id_cliente: Optional[int] = Query(default=None),
    obiettivo: Optional[str] = Query(default=None),
    livello: Optional[str] = Query(default=None),
):
    """Lista schede con filtri e paginazione."""
    query = select(WorkoutPlan).where(
        WorkoutPlan.trainer_id == trainer.id,
        WorkoutPlan.deleted_at == None,  # noqa: E711
    )

    if id_cliente is not None:
        query = query.where(WorkoutPlan.id_cliente == id_cliente)
    if obiettivo is not None:
        query = query.where(WorkoutPlan.obiettivo == obiettivo)
    if livello is not None:
        query = query.where(WorkoutPlan.livello == livello)

    total = session.exec(
        select(func.count()).select_from(query.subquery())
    ).one()

    offset = (page - 1) * page_size
    plans = session.exec(
        query.order_by(WorkoutPlan.updated_at.desc()).offset(offset).limit(page_size)
    ).all()

    if not plans:
        return WorkoutPlanListResponse(items=[], total=total, page=page, page_size=page_size)

    client_ids = list({p.id_cliente for p in plans if p.id_cliente})
    client_map: dict[int, Client] = {}
    if client_ids:
        clients = session.exec(select(Client).where(Client.id.in_(client_ids))).all()
        client_map = {c.id: c for c in clients}

    items = [_build_plan_response(session, p, client_map) for p in plans]

    return WorkoutPlanListResponse(items=items, total=total, page=page, page_size=page_size)


# ════════════════════════════════════════════════════════════
# GET: Dettaglio scheda
# ════════════════════════════════════════════════════════════

@router.get("/{workout_id}", response_model=WorkoutPlanResponse)
def get_workout(
    workout_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Dettaglio scheda con sessioni + esercizi + blocchi enriched."""
    plan = _bouncer_workout(session, workout_id, trainer.id)
    return _build_plan_response(session, plan)


# ════════════════════════════════════════════════════════════
# PUT: Aggiorna metadati scheda
# ════════════════════════════════════════════════════════════

@router.put("/{workout_id}", response_model=WorkoutPlanResponse)
def update_workout(
    workout_id: int,
    data: WorkoutPlanUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Aggiorna metadati scheda (nome, obiettivo, livello, note, durata)."""
    plan = _bouncer_workout(session, workout_id, trainer.id)

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return _build_plan_response(session, plan)

    if "id_cliente" in update_data and update_data["id_cliente"] is not None:
        _check_client_ownership(session, update_data["id_cliente"], trainer.id)

    for key in ("data_inizio", "data_fine"):
        if key in update_data and update_data[key] is not None:
            try:
                update_data[key] = date.fromisoformat(update_data[key])
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Formato data non valido per {key}",
                )

    for field, value in update_data.items():
        setattr(plan, field, value)

    if plan.data_inizio and plan.data_fine:
        di = plan.data_inizio if isinstance(plan.data_inizio, date) else date.fromisoformat(str(plan.data_inizio))
        df = plan.data_fine if isinstance(plan.data_fine, date) else date.fromisoformat(str(plan.data_fine))
        if df <= di:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La data fine deve essere successiva alla data inizio",
            )

    plan.updated_at = datetime.now(timezone.utc).isoformat()
    session.add(plan)
    log_audit(session, "workout_plan", plan.id, "UPDATE", trainer.id)
    session.commit()
    session.refresh(plan)

    return _build_plan_response(session, plan)


# ════════════════════════════════════════════════════════════
# PUT: Full-replace sessioni + blocchi + esercizi
# ════════════════════════════════════════════════════════════

@router.put("/{workout_id}/sessions", response_model=WorkoutPlanResponse)
def replace_sessions(
    workout_id: int,
    sessions: list[WorkoutSessionInput],
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Full-replace sessioni + blocchi + esercizi.
    DELETE vecchie → INSERT nuove in unica transazione.
    """
    plan = _bouncer_workout(session, workout_id, trainer.id)

    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Almeno una sessione richiesta",
        )

    _validate_exercise_ids(session, _collect_exercise_ids(sessions), trainer.id)

    # DELETE: esercizi → blocchi → sessioni (ordine FK corretto)
    old_sessions = session.exec(
        select(WorkoutSession).where(WorkoutSession.id_scheda == plan.id)
    ).all()
    old_session_ids = [s.id for s in old_sessions]
    _delete_sessions_cascade(session, old_session_ids)

    # INSERT nuove sessioni + blocchi + esercizi
    _insert_sessions(session, plan.id, sessions)

    plan.updated_at = datetime.now(timezone.utc).isoformat()
    session.add(plan)
    log_audit(session, "workout_plan", plan.id, "UPDATE_SESSIONS", trainer.id)
    session.commit()
    session.refresh(plan)

    return _build_plan_response(session, plan)


# ════════════════════════════════════════════════════════════
# DELETE: Soft delete scheda
# ════════════════════════════════════════════════════════════

@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    workout_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Soft delete scheda. Le sessioni, blocchi e esercizi restano (cascata logica)."""
    plan = _bouncer_workout(session, workout_id, trainer.id)

    plan.deleted_at = datetime.now(timezone.utc).isoformat()
    session.add(plan)
    log_audit(session, "workout_plan", plan.id, "DELETE", trainer.id)
    session.commit()


# ════════════════════════════════════════════════════════════
# POST: Duplica scheda (copia plan + sessioni + blocchi + esercizi)
# ════════════════════════════════════════════════════════════

@router.post("/{workout_id}/duplicate", response_model=WorkoutPlanResponse, status_code=status.HTTP_201_CREATED)
def duplicate_workout(
    workout_id: int,
    id_cliente: Optional[int] = Query(default=None, description="Assegna copia a altro cliente"),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Duplica scheda (per nuovo cliente o nuova settimana). Copia plan + sessioni + blocchi + esercizi."""
    source = _bouncer_workout(session, workout_id, trainer.id)

    target_client = id_cliente if id_cliente is not None else source.id_cliente
    if target_client is not None:
        _check_client_ownership(session, target_client, trainer.id)

    now = datetime.now(timezone.utc).isoformat()

    new_plan = WorkoutPlan(
        trainer_id=trainer.id,
        id_cliente=target_client,
        nome=f"{source.nome} (copia)",
        obiettivo=source.obiettivo,
        livello=source.livello,
        durata_settimane=source.durata_settimane,
        sessioni_per_settimana=source.sessioni_per_settimana,
        note=source.note,
        created_at=now,
        updated_at=now,
    )
    session.add(new_plan)
    session.flush()

    # Fetch sessioni source
    source_sessions = session.exec(
        select(WorkoutSession)
        .where(WorkoutSession.id_scheda == source.id)
        .order_by(WorkoutSession.numero_sessione)
    ).all()

    source_session_ids = [s.id for s in source_sessions]

    # Fetch blocchi source
    source_blocks: list[SessionBlock] = []
    if source_session_ids:
        source_blocks = list(session.exec(
            select(SessionBlock)
            .where(SessionBlock.id_sessione.in_(source_session_ids))
            .order_by(SessionBlock.ordine)
        ).all())

    # Fetch esercizi source (sia straight che in blocco)
    source_exercises: list[WorkoutExercise] = []
    if source_session_ids:
        source_exercises = list(session.exec(
            select(WorkoutExercise)
            .where(WorkoutExercise.id_sessione.in_(source_session_ids))
            .order_by(WorkoutExercise.ordine)
        ).all())

    straight_by_session: dict[int, list[WorkoutExercise]] = {}
    exercises_by_block: dict[int, list[WorkoutExercise]] = {}
    blocks_by_session: dict[int, list[SessionBlock]] = {}

    for e in source_exercises:
        if e.id_blocco is None:
            straight_by_session.setdefault(e.id_sessione, []).append(e)
        else:
            exercises_by_block.setdefault(e.id_blocco, []).append(e)
    for b in source_blocks:
        blocks_by_session.setdefault(b.id_sessione, []).append(b)

    # Duplica sessioni + blocchi + esercizi
    for s in source_sessions:
        new_session = WorkoutSession(
            id_scheda=new_plan.id,
            numero_sessione=s.numero_sessione,
            nome_sessione=s.nome_sessione,
            focus_muscolare=s.focus_muscolare,
            durata_minuti=s.durata_minuti,
            note=s.note,
        )
        session.add(new_session)
        session.flush()

        # Esercizi straight
        for e in straight_by_session.get(s.id, []):
            session.add(WorkoutExercise(
                id_sessione=new_session.id,
                id_blocco=None,
                id_esercizio=e.id_esercizio,
                ordine=e.ordine,
                posizione_nel_blocco=None,
                serie=e.serie,
                ripetizioni=e.ripetizioni,
                tempo_riposo_sec=e.tempo_riposo_sec,
                tempo_esecuzione=e.tempo_esecuzione,
                carico_kg=e.carico_kg,
                note=e.note,
            ))

        # Blocchi
        for b in blocks_by_session.get(s.id, []):
            new_block = SessionBlock(
                id_sessione=new_session.id,
                tipo_blocco=b.tipo_blocco,
                ordine=b.ordine,
                nome=b.nome,
                giri=b.giri,
                durata_lavoro_sec=b.durata_lavoro_sec,
                durata_riposo_sec=b.durata_riposo_sec,
                durata_blocco_sec=b.durata_blocco_sec,
                note=b.note,
            )
            session.add(new_block)
            session.flush()

            for e in exercises_by_block.get(b.id, []):
                session.add(WorkoutExercise(
                    id_sessione=new_session.id,
                    id_blocco=new_block.id,
                    id_esercizio=e.id_esercizio,
                    ordine=e.ordine,
                    posizione_nel_blocco=e.posizione_nel_blocco,
                    serie=e.serie,
                    ripetizioni=e.ripetizioni,
                    tempo_riposo_sec=e.tempo_riposo_sec,
                    tempo_esecuzione=e.tempo_esecuzione,
                    carico_kg=e.carico_kg,
                    note=e.note,
                ))

    log_audit(session, "workout_plan", new_plan.id, "DUPLICATE", trainer.id,
              {"source_id": source.id})
    session.commit()
    session.refresh(new_plan)

    return _build_plan_response(session, new_plan)
