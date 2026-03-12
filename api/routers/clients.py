# api/routers/clients.py
"""
Endpoint Clienti — il primo router dell'API.

Ogni query filtra per trainer_id: un trainer vede SOLO i propri clienti.
Questo e' il pattern multi-tenancy che si ripete su TUTTI i router futuri.

Sicurezza (Design by Contract):
- trainer_id NON appare mai negli schemas di input (ClientCreate, ClientUpdate)
- trainer_id viene iniettato server-side dal JWT token (get_current_trainer)
- Ogni query filtra SEMPRE per trainer_id = trainer autenticato (IDOR prevention)
"""

import json
import re
from datetime import date, datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, or_, select, func
from pydantic import BaseModel, Field, field_validator

from api.database import catalog_engine, get_session
from api.models.goal import ClientGoal
from api.models.medical_condition import MedicalCondition
from api.models.workout import WorkoutPlan
from api.models.workout_log import WorkoutLog
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.contract import Contract
from api.models.event import Event
from api.models.rate import Rate
from api.routers._audit import log_audit
from api.schemas.clinical import ClinicalReadinessClientItem
from api.services.clinical_readiness import compute_clinical_readiness_data
from api.services.safety_engine import extract_client_conditions

router = APIRouter(prefix="/clients", tags=["clients"])


# --- Input schemas (cosa l'API accetta) ---
# SICUREZZA: nessun campo trainer_id. Il trainer viene dal JWT token.

class ClientCreate(BaseModel):
    """
    Schema per creazione cliente via API.

    trainer_id e' ASSENTE by design: viene iniettato dall'endpoint
    usando il trainer autenticato dal JWT. Questo impedisce a un trainer
    di creare clienti nel namespace di un altro trainer.
    """
    model_config = {"extra": "forbid"}

    nome: str = Field(min_length=1, max_length=100)
    cognome: str = Field(min_length=1, max_length=100)
    telefono: Optional[str] = None
    email: Optional[str] = None
    data_nascita: Optional[date] = None
    sesso: Optional[str] = Field(None, pattern=r"^(Uomo|Donna|Altro)$")
    anamnesi: Optional[dict] = Field(default_factory=dict)
    stato: str = Field(default="Attivo", pattern=r"^(Attivo|Inattivo)$")
    note_interne: Optional[str] = None

    @field_validator("telefono")
    @classmethod
    def validate_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not re.match(r"^[+]?[0-9\s\-()]{6,20}$", v):
            raise ValueError("Telefono non valido")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if "@" not in v or "." not in v:
            raise ValueError("Email non valida")
        return v.lower()

    @field_validator("data_nascita")
    @classmethod
    def validate_data_nascita(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("Data di nascita non puo' essere nel futuro")
        return v


class ClientUpdate(BaseModel):
    """
    Schema per update cliente via API (partial update).

    Tutti i campi sono opzionali: il frontend invia SOLO i campi da modificare.
    trainer_id e' ASSENTE: non si puo' "trasferire" un cliente via API.
    """
    model_config = {"extra": "forbid"}

    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    cognome: Optional[str] = Field(None, min_length=1, max_length=100)
    telefono: Optional[str] = None
    email: Optional[str] = None
    data_nascita: Optional[date] = None
    sesso: Optional[str] = Field(None, pattern=r"^(Uomo|Donna|Altro)$")
    anamnesi: Optional[dict] = None
    stato: Optional[str] = Field(None, pattern=r"^(Attivo|Inattivo)$")
    note_interne: Optional[str] = None

    @field_validator("telefono")
    @classmethod
    def validate_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not re.match(r"^[+]?[0-9\s\-()]{6,20}$", v):
            raise ValueError("Telefono non valido")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if "@" not in v or "." not in v:
            raise ValueError("Email non valida")
        return v.lower()

    @field_validator("data_nascita")
    @classmethod
    def validate_data_nascita(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("Data di nascita non puo' essere nel futuro")
        return v


# --- Response schemas (cosa l'API restituisce) ---

class ClientResponse(BaseModel):
    """Dati cliente restituiti dall'API. anamnesi_json raw viene parsato in dict."""
    id: int
    nome: str
    cognome: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    data_nascita: Optional[str] = None
    sesso: Optional[str] = None
    stato: str
    note_interne: Optional[str] = None
    crediti_residui: int = 0
    anamnesi: Optional[dict] = None


class ClientEnrichedResponse(ClientResponse):
    """Client con dati aggregati da contratti + eventi (batch-computed)."""
    contratti_attivi: int = 0
    totale_versato: float = 0.0
    prezzo_totale_attivo: float = 0.0
    ha_rate_scadute: bool = False
    ultimo_evento_data: Optional[str] = None


class ClientListResponse(BaseModel):
    """Risposta paginata enriched per lista clienti + KPI aggregati."""
    items: List[ClientEnrichedResponse]
    total: int
    page: int
    page_size: int
    # KPI aggregati (calcolati pre-filtro: quadro generale)
    kpi_attivi: int = 0
    kpi_inattivi: int = 0
    kpi_con_crediti: int = 0
    kpi_rate_scadute: int = 0


class ClientDossierIdentity(BaseModel):
    """Identita' cliente per il dossier read-only."""

    id: int
    nome: str
    cognome: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    data_nascita: Optional[str] = None
    sesso: Optional[str] = None
    stato: str
    note_interne: Optional[str] = None
    client_since: Optional[str] = None


class ClientDossierClinicalAlert(BaseModel):
    condition_name: str
    category: Optional[str] = None


class ClientDossierSessionSummary(BaseModel):
    total_pt_sessions: int = 0
    completed_pt_sessions: int = 0
    last_completed_session_at: Optional[str] = None
    next_scheduled_session_at: Optional[str] = None


class ClientDossierPlanSummary(BaseModel):
    total_plans: int = 0
    latest_plan_name: Optional[str] = None
    latest_plan_updated_at: Optional[str] = None
    active_plan_name: Optional[str] = None
    active_plan_start_date: Optional[str] = None
    active_plan_end_date: Optional[str] = None


class ClientDossierContractSummary(BaseModel):
    active_contracts: int = 0
    credits_residui: int = 0
    has_overdue_rates: bool = False
    next_contract_expiry_date: Optional[str] = None


class ClientDossierGoalSummary(BaseModel):
    active_goals: int = 0
    reached_goals: int = 0
    abandoned_goals: int = 0


class ClientDossierActivityItem(BaseModel):
    at: str
    kind: str
    label: str
    status: Optional[str] = None
    href: Optional[str] = None


class ClientDossierResponse(BaseModel):
    """Dossier cliente read-only per uso operativo on-demand."""

    generated_at: str
    client: ClientDossierIdentity
    readiness: Optional[ClinicalReadinessClientItem] = None
    clinical_alerts: List[ClientDossierClinicalAlert] = Field(default_factory=list)
    session_summary: ClientDossierSessionSummary
    plan_summary: ClientDossierPlanSummary
    contract_summary: ClientDossierContractSummary
    goal_summary: ClientDossierGoalSummary
    recent_activity: List[ClientDossierActivityItem] = Field(default_factory=list)


# --- Credit Engine helpers ---

def _calc_credits_batch(
    session: Session, client_ids: List[int], trainer_id: int
) -> Dict[int, int]:
    """
    Calcola crediti_residui per un batch di clienti in 2 query SQL.

    crediti_residui = crediti_acquistati - sedute_PT_usate

    - crediti_acquistati: SUM(crediti_totali) da TUTTI i contratti non eliminati
      (chiuso NON filtrato — chiuso blocca nuove operazioni, non invalida crediti)
    - sedute_PT_usate: COUNT(eventi) con categoria='PT' e stato!='Cancellato'
    """
    if not client_ids:
        return {}

    # Query 1: crediti acquistati per cliente (tutti i contratti non eliminati)
    # NOTA: chiuso NON filtrato — chiuso blocca nuove operazioni, non invalida i crediti
    credit_rows = session.exec(
        select(Contract.id_cliente, func.coalesce(func.sum(Contract.crediti_totali), 0))
        .where(
            Contract.id_cliente.in_(client_ids),
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
        )
        .group_by(Contract.id_cliente)
    ).all()
    credits_map: Dict[int, int] = {row[0]: int(row[1]) for row in credit_rows}

    # Query 2: sedute PT usate per cliente (non cancellate, non eliminate)
    usage_rows = session.exec(
        select(Event.id_cliente, func.count(Event.id))
        .where(
            Event.id_cliente.in_(client_ids),
            Event.categoria == "PT",
            Event.stato != "Cancellato",
            Event.trainer_id == trainer_id,
            Event.deleted_at == None,
        )
        .group_by(Event.id_cliente)
    ).all()
    usage_map: Dict[int, int] = {row[0]: int(row[1]) for row in usage_rows}

    return {
        cid: credits_map.get(cid, 0) - usage_map.get(cid, 0)
        for cid in client_ids
    }


def _stringify_date(value: Optional[date | datetime | str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _coerce_date(value: Optional[date | datetime | str]) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _is_plan_active(plan: WorkoutPlan, reference_date: date) -> bool:
    start_date = _coerce_date(plan.data_inizio)
    end_date = _coerce_date(plan.data_fine)
    if start_date is None or end_date is None:
        return False
    return end_date >= reference_date


def _build_client_enriched_response(
    session: Session,
    trainer_id: int,
    client: Client,
) -> ClientEnrichedResponse:
    if client.id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    credits = _calc_credits_batch(session, [client.id], trainer_id)

    contract_row = session.exec(
        select(
            func.count(Contract.id),
            func.coalesce(func.sum(Contract.totale_versato), 0),
            func.coalesce(func.sum(Contract.prezzo_totale), 0),
        )
        .where(
            Contract.id_cliente == client.id,
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
            Contract.chiuso == False,
        )
    ).one()

    today = date.today()
    overdue_count = session.exec(
        select(func.count(Rate.id))
        .join(Contract, Rate.id_contratto == Contract.id)
        .where(
            Contract.id_cliente == client.id,
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
            Contract.chiuso == False,
            Rate.deleted_at == None,
            Rate.stato != "SALDATA",
            or_(Rate.data_scadenza < today, Contract.data_scadenza < today),
        )
    ).one()

    last_event_row = session.exec(
        select(func.max(Event.data_inizio))
        .where(
            Event.id_cliente == client.id,
            Event.trainer_id == trainer_id,
            Event.deleted_at == None,
            Event.stato != "Cancellato",
        )
    ).one()

    return ClientEnrichedResponse(
        id=client.id,
        nome=client.nome,
        cognome=client.cognome,
        telefono=client.telefono,
        email=client.email,
        data_nascita=str(client.data_nascita) if client.data_nascita else None,
        sesso=client.sesso,
        stato=client.stato,
        note_interne=client.note_interne,
        crediti_residui=credits.get(client.id, 0),
        anamnesi=json.loads(client.anamnesi_json) if client.anamnesi_json else None,
        contratti_attivi=int(contract_row[0]),
        totale_versato=float(contract_row[1]),
        prezzo_totale_attivo=float(contract_row[2]),
        ha_rate_scadute=overdue_count > 0,
        ultimo_evento_data=str(last_event_row)[:10] if last_event_row else None,
    )


def _build_client_dossier_response(
    session: Session,
    trainer_id: int,
    client: Client,
) -> ClientDossierResponse:
    if client.id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    now_dt = datetime.now(timezone.utc)
    today = now_dt.date()
    enriched = _build_client_enriched_response(session, trainer_id, client)

    _summary, readiness_items = compute_clinical_readiness_data(
        trainer_id=trainer_id,
        session=session,
        reference_date=today,
    )
    readiness = next((item for item in readiness_items if item.client_id == client.id), None)

    condition_ids = extract_client_conditions(client.anamnesi_json)
    clinical_alerts: List[ClientDossierClinicalAlert] = []
    if condition_ids:
        with Session(catalog_engine) as catalog:
            rows = catalog.exec(
                select(MedicalCondition.id, MedicalCondition.nome, MedicalCondition.categoria)
                .where(MedicalCondition.id.in_(list(condition_ids)))
                .order_by(MedicalCondition.categoria, MedicalCondition.nome)
            ).all()
        clinical_alerts = [
            ClientDossierClinicalAlert(condition_name=row[1], category=row[2])
            for row in rows
        ]

    total_pt_sessions = int(session.exec(
        select(func.count(Event.id))
        .where(
            Event.trainer_id == trainer_id,
            Event.id_cliente == client.id,
            Event.deleted_at == None,
            Event.categoria == "PT",
            Event.stato != "Cancellato",
        )
    ).one())

    completed_pt_sessions = int(session.exec(
        select(func.count(Event.id))
        .where(
            Event.trainer_id == trainer_id,
            Event.id_cliente == client.id,
            Event.deleted_at == None,
            Event.categoria == "PT",
            Event.stato == "Completato",
        )
    ).one())

    last_completed_session = session.exec(
        select(func.max(Event.data_inizio))
        .where(
            Event.trainer_id == trainer_id,
            Event.id_cliente == client.id,
            Event.deleted_at == None,
            Event.categoria == "PT",
            Event.stato == "Completato",
        )
    ).one()

    next_scheduled_session = session.exec(
        select(Event.data_inizio)
        .where(
            Event.trainer_id == trainer_id,
            Event.id_cliente == client.id,
            Event.deleted_at == None,
            Event.categoria == "PT",
            Event.stato != "Cancellato",
            Event.data_inizio >= now_dt,
        )
        .order_by(Event.data_inizio.asc())
    ).first()

    plan_rows = session.exec(
        select(WorkoutPlan)
        .where(
            WorkoutPlan.trainer_id == trainer_id,
            WorkoutPlan.id_cliente == client.id,
            WorkoutPlan.deleted_at == None,
        )
        .order_by(func.coalesce(WorkoutPlan.updated_at, WorkoutPlan.created_at).desc())
    ).all()
    latest_plan = plan_rows[0] if plan_rows else None
    active_plan = next(
        (plan for plan in plan_rows if _is_plan_active(plan, today)),
        None,
    )

    next_contract_expiry = session.exec(
        select(func.min(Contract.data_scadenza))
        .where(
            Contract.id_cliente == client.id,
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
            Contract.chiuso == False,
        )
    ).one()

    goal_rows = session.exec(
        select(ClientGoal.stato, func.count(ClientGoal.id))
        .where(
            ClientGoal.id_cliente == client.id,
            ClientGoal.trainer_id == trainer_id,
            ClientGoal.deleted_at == None,
        )
        .group_by(ClientGoal.stato)
    ).all()
    goal_counts = {row[0]: int(row[1]) for row in goal_rows}

    recent_events = session.exec(
        select(Event)
        .where(
            Event.trainer_id == trainer_id,
            Event.id_cliente == client.id,
            Event.deleted_at == None,
            Event.stato != "Cancellato",
        )
        .order_by(Event.data_inizio.desc())
        .limit(5)
    ).all()

    recent_logs = session.exec(
        select(WorkoutLog)
        .where(
            WorkoutLog.trainer_id == trainer_id,
            WorkoutLog.id_cliente == client.id,
            WorkoutLog.deleted_at == None,
        )
        .order_by(WorkoutLog.data_esecuzione.desc())
        .limit(5)
    ).all()

    activity_items: List[tuple[datetime, ClientDossierActivityItem]] = []
    for event in recent_events:
        activity_items.append((
            event.data_inizio,
            ClientDossierActivityItem(
                at=event.data_inizio.isoformat(),
                kind="event",
                label=event.titolo or event.categoria,
                status=event.stato,
                href="/agenda",
            ),
        ))

    for log in recent_logs:
        activity_at = datetime.combine(log.data_esecuzione, datetime.min.time(), tzinfo=timezone.utc)
        activity_items.append((
            activity_at,
            ClientDossierActivityItem(
                at=activity_at.isoformat(),
                kind="workout_log",
                label="Allenamento registrato",
                href=f"/clienti/{client.id}?tab=schede",
            ),
        ))

    activity_items.sort(key=lambda item: item[0], reverse=True)

    return ClientDossierResponse(
        generated_at=now_dt.isoformat(),
        client=ClientDossierIdentity(
            id=client.id,
            nome=client.nome,
            cognome=client.cognome,
            telefono=client.telefono,
            email=client.email,
            data_nascita=_stringify_date(client.data_nascita),
            sesso=client.sesso,
            stato=client.stato,
            note_interne=client.note_interne,
            client_since=_stringify_date(client.data_creazione),
        ),
        readiness=readiness,
        clinical_alerts=clinical_alerts,
        session_summary=ClientDossierSessionSummary(
            total_pt_sessions=total_pt_sessions,
            completed_pt_sessions=completed_pt_sessions,
            last_completed_session_at=_stringify_date(last_completed_session),
            next_scheduled_session_at=_stringify_date(next_scheduled_session),
        ),
        plan_summary=ClientDossierPlanSummary(
            total_plans=len(plan_rows),
            latest_plan_name=latest_plan.nome if latest_plan else None,
            latest_plan_updated_at=(
                _stringify_date(latest_plan.updated_at or latest_plan.created_at)
                if latest_plan
                else None
            ),
            active_plan_name=active_plan.nome if active_plan else None,
            active_plan_start_date=_stringify_date(active_plan.data_inizio) if active_plan else None,
            active_plan_end_date=_stringify_date(active_plan.data_fine) if active_plan else None,
        ),
        contract_summary=ClientDossierContractSummary(
            active_contracts=enriched.contratti_attivi,
            credits_residui=enriched.crediti_residui,
            has_overdue_rates=enriched.ha_rate_scadute,
            next_contract_expiry_date=_stringify_date(next_contract_expiry),
        ),
        goal_summary=ClientDossierGoalSummary(
            active_goals=goal_counts.get("attivo", 0),
            reached_goals=goal_counts.get("raggiunto", 0),
            abandoned_goals=goal_counts.get("abbandonato", 0),
        ),
        recent_activity=[item[1] for item in activity_items[:5]],
    )


# --- Endpoints ---

@router.get("", response_model=ClientListResponse)
def list_clients(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1, description="Numero pagina"),
    page_size: int = Query(default=50, ge=1, le=200, description="Risultati per pagina"),
    stato: Optional[str] = Query(default=None, description="Filtra per stato (Attivo, Inattivo)"),
    search: Optional[str] = Query(default=None, description="Cerca per nome/cognome"),
):
    """
    Lista clienti del trainer autenticato.

    Filtro multi-tenancy: WHERE trainer_id = <trainer_corrente>.
    Supporta paginazione, filtro per stato, ricerca per nome.
    Include crediti_residui calcolati in batch (3 query totali, zero N+1).
    """
    # Query base: solo clienti di QUESTO trainer, non eliminati
    query = select(Client).where(Client.trainer_id == trainer.id, Client.deleted_at == None)

    # Filtro opzionale per stato
    if stato:
        query = query.where(Client.stato == stato)

    # Ricerca per nome/cognome (case insensitive con LIKE)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            (Client.nome.ilike(pattern)) | (Client.cognome.ilike(pattern))
        )

    # Count dalla stessa query base (zero duplicazione filtri)
    total = session.exec(
        select(func.count()).select_from(query.subquery())
    ).one()

    # Paginazione
    offset = (page - 1) * page_size
    query = query.order_by(Client.cognome, Client.nome).offset(offset).limit(page_size)

    clients = session.exec(query).all()
    client_ids = [c.id for c in clients]

    # ── Batch enrichment (5 query totali, zero N+1) ──

    # Q1-Q2: crediti residui (gia' esistente)
    credits = _calc_credits_batch(session, client_ids, trainer.id)

    # Q3: contratti attivi + totale versato + prezzo totale per cliente
    contract_map: Dict[int, Dict] = {}
    if client_ids:
        contract_rows = session.exec(
            select(
                Contract.id_cliente,
                func.count(Contract.id),
                func.coalesce(func.sum(Contract.totale_versato), 0),
                func.coalesce(func.sum(Contract.prezzo_totale), 0),
            )
            .where(
                Contract.id_cliente.in_(client_ids),
                Contract.trainer_id == trainer.id,
                Contract.deleted_at == None,
                Contract.chiuso == False,
            )
            .group_by(Contract.id_cliente)
        ).all()
        contract_map = {
            row[0]: {"count": int(row[1]), "versato": float(row[2]), "prezzo": float(row[3])}
            for row in contract_rows
        }

    # Q4: clienti con rate scadute (non saldate, data < oggi O contratto scaduto)
    today = date.today()
    overdue_set: set = set()
    if client_ids:
        overdue_rows = session.exec(
            select(Contract.id_cliente)
            .join(Rate, Rate.id_contratto == Contract.id)
            .where(
                Contract.id_cliente.in_(client_ids),
                Contract.trainer_id == trainer.id,
                Contract.deleted_at == None,
                Contract.chiuso == False,
                Rate.deleted_at == None,
                Rate.stato != "SALDATA",
                or_(Rate.data_scadenza < today, Contract.data_scadenza < today),
            )
            .group_by(Contract.id_cliente)
        ).all()
        overdue_set = set(overdue_rows)

    # Q5: ultimo evento per cliente (non cancellato)
    last_event_map: Dict[int, str] = {}
    if client_ids:
        last_event_rows = session.exec(
            select(
                Event.id_cliente,
                func.max(Event.data_inizio),
            )
            .where(
                Event.id_cliente.in_(client_ids),
                Event.trainer_id == trainer.id,
                Event.deleted_at == None,
                Event.stato != "Cancellato",
            )
            .group_by(Event.id_cliente)
        ).all()
        last_event_map = {
            row[0]: str(row[1])[:10] for row in last_event_rows if row[1]
        }

    # ── KPI aggregati (pre-filtro: intero dataset del trainer) ──
    all_query = select(Client).where(
        Client.trainer_id == trainer.id, Client.deleted_at == None
    )
    all_clients = session.exec(all_query).all()
    all_ids = [c.id for c in all_clients]
    all_credits = _calc_credits_batch(session, all_ids, trainer.id) if all_ids else {}

    # Clienti con rate scadute — tutti (non solo la pagina corrente)
    all_overdue_set: set = set()
    if all_ids:
        all_overdue_rows = session.exec(
            select(Contract.id_cliente)
            .join(Rate, Rate.id_contratto == Contract.id)
            .where(
                Contract.id_cliente.in_(all_ids),
                Contract.trainer_id == trainer.id,
                Contract.deleted_at == None,
                Contract.chiuso == False,
                Rate.deleted_at == None,
                Rate.stato != "SALDATA",
                or_(Rate.data_scadenza < today, Contract.data_scadenza < today),
            )
            .group_by(Contract.id_cliente)
        ).all()
        all_overdue_set = set(all_overdue_rows)

    kpi_attivi = sum(1 for c in all_clients if c.stato == "Attivo")
    kpi_inattivi = sum(1 for c in all_clients if c.stato == "Inattivo")
    kpi_con_crediti = sum(1 for cid in all_ids if all_credits.get(cid, 0) > 0)
    kpi_rate_scadute = len(all_overdue_set)

    # ── Build enriched response ──
    items = []
    for c in clients:
        cdata = contract_map.get(c.id, {"count": 0, "versato": 0.0, "prezzo": 0.0})
        items.append(ClientEnrichedResponse(
            id=c.id,
            nome=c.nome,
            cognome=c.cognome,
            telefono=c.telefono,
            email=c.email,
            data_nascita=str(c.data_nascita) if c.data_nascita else None,
            sesso=c.sesso,
            stato=c.stato,
            note_interne=c.note_interne,
            crediti_residui=credits.get(c.id, 0),
            anamnesi=json.loads(c.anamnesi_json) if c.anamnesi_json else None,
            contratti_attivi=cdata["count"],
            totale_versato=cdata["versato"],
            prezzo_totale_attivo=cdata["prezzo"],
            ha_rate_scadute=c.id in overdue_set,
            ultimo_evento_data=last_event_map.get(c.id),
        ))

    return ClientListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        kpi_attivi=kpi_attivi,
        kpi_inattivi=kpi_inattivi,
        kpi_con_crediti=kpi_con_crediti,
        kpi_rate_scadute=kpi_rate_scadute,
    )


@router.get("/{client_id}", response_model=ClientEnrichedResponse)
def get_client(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Dettaglio singolo cliente enriched.

    Bouncer: query filtra per trainer_id.
    Enrichment: stesse 5 query di list_clients, semplificate per 1 client.
    """
    client = session.exec(
        select(Client).where(
            Client.id == client_id, Client.trainer_id == trainer.id, Client.deleted_at == None
        )
    ).first()

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")
    return _build_client_enriched_response(session, trainer.id, client)


@router.get("/{client_id}/dossier", response_model=ClientDossierResponse)
def get_client_dossier(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Dossier cliente read-only per uso operativo on-demand."""
    client = session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.trainer_id == trainer.id,
            Client.deleted_at == None,
        )
    ).first()

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    return _build_client_dossier_response(session, trainer.id, client)


# --- POST: Crea cliente ---

@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    data: ClientCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Crea un nuovo cliente per il trainer autenticato.

    trainer_id viene INIETTATO dal JWT — mai dal body della richiesta.
    Anche se il body contenesse trainer_id, lo schema ClientCreate lo ignora.
    """
    client = Client(
        trainer_id=trainer.id,  # <-- Iniezione sicura dal JWT
        nome=data.nome,
        cognome=data.cognome,
        telefono=data.telefono,
        email=data.email,
        data_nascita=data.data_nascita,
        sesso=data.sesso,
        anamnesi_json=json.dumps(data.anamnesi) if data.anamnesi else None,
        stato=data.stato,
        note_interne=data.note_interne,
    )
    session.add(client)
    session.flush()
    log_audit(session, "client", client.id, "CREATE", trainer.id)
    session.commit()
    session.refresh(client)

    return _to_response(client, 0)


# --- PUT: Aggiorna cliente (partial update) ---

@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    data: ClientUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Aggiorna un cliente esistente.

    Bouncer Pattern: query singola con id + trainer_id.
    Se il cliente non esiste O appartiene a un altro trainer -> 404.
    Mai 403: non riveliamo l'esistenza di risorse altrui.
    """
    # Bouncer: una sola query, filtro combinato id + trainer_id + non eliminato
    client = session.exec(
        select(Client).where(
            Client.id == client_id, Client.trainer_id == trainer.id, Client.deleted_at == None
        )
    ).first()

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    # Partial update: applica solo i campi effettivamente inviati
    update_data = data.model_dump(exclude_unset=True)
    changes = {}
    for field, value in update_data.items():
        if field == "anamnesi":
            old_val = client.anamnesi_json
            client.anamnesi_json = json.dumps(value) if value else None
            if client.anamnesi_json != old_val:
                changes[field] = {"old": old_val, "new": client.anamnesi_json}
        else:
            old_val = getattr(client, field)
            setattr(client, field, value)
            if value != old_val:
                changes[field] = {"old": old_val, "new": value}

    log_audit(session, "client", client.id, "UPDATE", trainer.id, changes or None)
    session.add(client)
    session.commit()
    session.refresh(client)

    credits = _calc_credits_batch(session, [client.id], trainer.id)

    return _to_response(client, credits.get(client.id, 0))


# --- DELETE: Elimina cliente ---

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Soft-delete un cliente.

    Bouncer Pattern: query singola con id + trainer_id + non eliminato.
    RESTRICT: se il cliente ha contratti attivi (non eliminati) → 400.
    Nessun response body (204 No Content).
    """
    # Bouncer: filtro combinato id + trainer_id + non eliminato
    client = session.exec(
        select(Client).where(
            Client.id == client_id, Client.trainer_id == trainer.id, Client.deleted_at == None
        )
    ).first()

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    # RESTRICT: verifica nessun contratto attivo (non eliminato)
    active_contracts = session.exec(
        select(func.count(Contract.id)).where(
            Contract.id_cliente == client_id,
            Contract.trainer_id == trainer.id,
            Contract.deleted_at == None,
            Contract.chiuso == False,
        )
    ).one()
    if active_contracts > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile eliminare: il cliente ha contratti attivi",
        )

    client.deleted_at = datetime.now(timezone.utc)
    session.add(client)
    log_audit(session, "client", client.id, "DELETE", trainer.id)
    session.commit()


# --- Helper ---

def _to_response(client: Client, crediti_residui: int = 0) -> ClientResponse:
    """Converte un Client ORM in ClientResponse. Centralizza la conversione."""
    return ClientResponse(
        id=client.id,
        nome=client.nome,
        cognome=client.cognome,
        telefono=client.telefono,
        email=client.email,
        data_nascita=str(client.data_nascita) if client.data_nascita else None,
        sesso=client.sesso,
        stato=client.stato,
        note_interne=client.note_interne,
        crediti_residui=crediti_residui,
        anamnesi=json.loads(client.anamnesi_json) if client.anamnesi_json else None,
    )
