"""
Session Prep engine — cockpit data per la pagina Oggi.

Aggrega in una sola query batch:
- Eventi del giorno con client join
- Conteggio sessioni storiche per cliente
- Clinical readiness (anamnesi, misurazioni, scheda, programma)
- Condizioni mediche dall'anamnesi (safety engine)
- Contratto attivo con crediti

Read-only, zero side effects.
"""

from datetime import date, datetime

from sqlalchemy import case
from sqlmodel import Session, func, select

from api.database import catalog_engine
from api.models.client import Client
from api.models.contract import Contract
from api.models.event import Event
from api.models.medical_condition import MedicalCondition
from api.schemas.workspace import (
    SessionPrepAlert,
    SessionPrepHealthCheck,
    SessionPrepHint,
    SessionPrepItem,
    SessionPrepResponse,
)
from api.services.clinical_readiness import compute_clinical_readiness_data
from api.services.safety_engine import extract_client_conditions


def _client_age(data_nascita: date | None, reference: date) -> int | None:
    if not data_nascita:
        return None
    age = reference.year - data_nascita.year
    if (reference.month, reference.day) < (data_nascita.month, data_nascita.day):
        age -= 1
    return age


def _is_new_client(data_creazione: datetime | None, reference: date) -> bool:
    if not data_creazione:
        return False
    return (reference - data_creazione.date()).days <= 30


def _build_health_checks(readiness_item) -> list[SessionPrepHealthCheck]:
    checks: list[SessionPrepHealthCheck] = []

    # 1. Anamnesi
    anamnesi_status = "ok"
    anamnesi_detail = "Compilata"
    if readiness_item.anamnesi_state == "missing":
        anamnesi_status = "critical"
        anamnesi_detail = "Mancante"
    elif readiness_item.anamnesi_state == "legacy":
        anamnesi_status = "warning"
        anamnesi_detail = "Da aggiornare (v1)"
    checks.append(SessionPrepHealthCheck(
        domain="anamnesi",
        label="Anamnesi",
        status=anamnesi_status,
        detail=anamnesi_detail,
        cta_href=readiness_item.next_action_href if anamnesi_status != "ok" else None,
    ))

    # 2. Misurazioni
    mf = readiness_item.measurement_freshness
    checks.append(SessionPrepHealthCheck(
        domain="measurements",
        label="Misurazioni",
        status=mf.status,
        detail=mf.label,
        days_since_last=mf.days_since_last,
        cta_href=mf.cta_href if mf.status != "ok" else None,
    ))

    # 3. Scheda
    wf = readiness_item.workout_freshness
    checks.append(SessionPrepHealthCheck(
        domain="workout",
        label="Scheda",
        status=wf.status,
        detail=wf.label,
        days_since_last=wf.days_since_last,
        cta_href=wf.cta_href if wf.status != "ok" else None,
    ))

    # 4. Programma attivo
    if readiness_item.workout_activated:
        checks.append(SessionPrepHealthCheck(
            domain="program",
            label="Programma",
            status="ok",
            detail=readiness_item.workout_plan_name or "Attivo",
        ))
    elif readiness_item.has_workout_plan:
        checks.append(SessionPrepHealthCheck(
            domain="program",
            label="Programma",
            status="warning",
            detail="Non attivato",
            cta_href=f"/allenamenti?idCliente={readiness_item.client_id}",
        ))
    else:
        checks.append(SessionPrepHealthCheck(
            domain="program",
            label="Programma",
            status="missing",
            detail="Nessuna scheda",
        ))

    return checks


def _build_quality_hints(
    *,
    readiness_item,
    days_since_last_session: int | None,
    contract_expiring_days: int | None,
    total_sessions: int,
    is_new: bool,
) -> list[SessionPrepHint]:
    hints: list[SessionPrepHint] = []

    # Hint: misurazioni scadute
    mf = readiness_item.measurement_freshness
    if mf.status in ("warning", "critical") and mf.days_since_last is not None:
        hints.append(SessionPrepHint(
            code="measurements_stale",
            text=f"Misurazioni non aggiornate da {mf.days_since_last} giorni",
            severity="high" if mf.status == "critical" else "medium",
            cta_href=mf.cta_href,
        ))

    # Hint: contratto in scadenza
    if contract_expiring_days is not None and 0 < contract_expiring_days <= 14:
        hints.append(SessionPrepHint(
            code="contract_expiring",
            text=f"Contratto in scadenza tra {contract_expiring_days} giorni",
            severity="high" if contract_expiring_days <= 7 else "medium",
            cta_href=f"/clienti/{readiness_item.client_id}?tab=contratti",
        ))

    # Hint: gap lungo tra sessioni
    if days_since_last_session is not None and days_since_last_session > 14:
        hints.append(SessionPrepHint(
            code="session_gap",
            text=f"Non si allena da {days_since_last_session} giorni",
            severity="medium",
        ))

    # Hint: cliente nuovo — preparazione extra
    if is_new and total_sessions <= 3:
        hints.append(SessionPrepHint(
            code="new_client",
            text="Cliente nuovo: attenzione extra su postura e tecnica",
            severity="low",
        ))

    return hints[:2]  # Max 2 hints


def build_session_prep(
    *,
    trainer_id: int,
    session: Session,
) -> SessionPrepResponse:
    now_dt = datetime.now()
    today = now_dt.date()

    # ── 1. Eventi del giorno (non cancellati, non passati) ──
    day_start = datetime.combine(today, datetime.min.time())
    day_end = datetime.combine(today, datetime.max.time())

    events_with_clients = session.exec(
        select(Event, Client)
        .join(Client, Event.id_cliente == Client.id, isouter=True)
        .where(
            Event.trainer_id == trainer_id,
            Event.data_inizio >= day_start,
            Event.data_inizio <= day_end,
            Event.stato != "Cancellato",
            Event.deleted_at == None,
        )
        .order_by(Event.data_inizio.asc())
    ).all()

    if not events_with_clients:
        return SessionPrepResponse(
            date=today,
            current_time=now_dt,
        )

    # ── 2. Batch: client IDs ──
    client_ids: list[int] = []
    client_map: dict[int, Client] = {}
    for _event, client in events_with_clients:
        if client and client.id is not None and client.id not in client_map:
            client_ids.append(client.id)
            client_map[client.id] = client

    # ── 3. Batch: session counts per client (total + completed) ──
    session_counts: dict[int, tuple[int, int]] = {}
    last_session_dates: dict[int, date] = {}
    if client_ids:
        count_rows = session.exec(
            select(
                Event.id_cliente,
                func.count(Event.id),
                func.sum(
                    case(
                        (Event.stato == "Completato", 1),
                        else_=0,
                    )
                ),
            )
            .where(
                Event.trainer_id == trainer_id,
                Event.id_cliente.in_(client_ids),
                Event.deleted_at == None,
                Event.stato != "Cancellato",
                Event.categoria == "PT",
            )
            .group_by(Event.id_cliente)
        ).all()
        for row in count_rows:
            if row[0] is not None:
                session_counts[row[0]] = (int(row[1] or 0), int(row[2] or 0))

        # Last completed session per client
        last_rows = session.exec(
            select(
                Event.id_cliente,
                func.max(Event.data_inizio),
            )
            .where(
                Event.trainer_id == trainer_id,
                Event.id_cliente.in_(client_ids),
                Event.deleted_at == None,
                Event.stato == "Completato",
                Event.categoria == "PT",
            )
            .group_by(Event.id_cliente)
        ).all()
        for row in last_rows:
            if row[0] is not None and row[1] is not None:
                if isinstance(row[1], str):
                    try:
                        last_session_dates[row[0]] = datetime.fromisoformat(row[1]).date()
                    except (ValueError, TypeError):
                        pass
                elif isinstance(row[1], datetime):
                    last_session_dates[row[0]] = row[1].date()
                elif isinstance(row[1], date):
                    last_session_dates[row[0]] = row[1]

    # ── 4. Clinical readiness (reuses existing shared service) ──
    readiness_by_client: dict[int, object] = {}
    if client_ids:
        _summary, readiness_items = compute_clinical_readiness_data(
            trainer_id=trainer_id,
            session=session,
            reference_date=today,
        )
        for item in readiness_items:
            readiness_by_client[item.client_id] = item

    # ── 5. Safety engine: condizioni mediche per client ──
    conditions_by_client: dict[int, list[SessionPrepAlert]] = {}
    if client_ids:
        condition_ids_by_client: dict[int, set[int]] = {}
        all_condition_ids: set[int] = set()
        for cid in client_ids:
            client_obj = client_map[cid]
            cond_ids = extract_client_conditions(client_obj.anamnesi_json)
            if cond_ids:
                condition_ids_by_client[cid] = cond_ids
                all_condition_ids.update(cond_ids)

        # Batch fetch condition names from catalog DB
        condition_names: dict[int, tuple[str, str | None]] = {}
        if all_condition_ids:
            with Session(catalog_engine) as catalog:
                cond_rows = catalog.exec(
                    select(MedicalCondition.id, MedicalCondition.nome, MedicalCondition.categoria)
                    .where(MedicalCondition.id.in_(list(all_condition_ids)))
                ).all()
                for crow in cond_rows:
                    condition_names[crow[0]] = (crow[1], crow[2])

        for cid, cond_ids in condition_ids_by_client.items():
            alerts = []
            for cond_id in sorted(cond_ids)[:5]:  # Max 5 alerts
                name_cat = condition_names.get(cond_id)
                if name_cat:
                    alerts.append(SessionPrepAlert(
                        condition_name=name_cat[0],
                        category=name_cat[1],
                    ))
            conditions_by_client[cid] = alerts

    # ── 6. Active contracts per client ──
    contract_info: dict[int, tuple[int | None, int | None, int | None]] = {}
    if client_ids:
        contract_rows = session.exec(
            select(
                Contract.id_cliente,
                Contract.crediti_totali,
                Contract.crediti_usati,
                Contract.data_scadenza,
            )
            .where(
                Contract.trainer_id == trainer_id,
                Contract.id_cliente.in_(client_ids),
                Contract.chiuso == False,
                Contract.deleted_at == None,
            )
            .order_by(Contract.data_scadenza.asc())
        ).all()
        for crow in contract_rows:
            cid = crow[0]
            if cid is not None and cid not in contract_info:
                credits_total = crow[1]
                credits_used = crow[2] or 0
                remaining = (credits_total - credits_used) if credits_total else None
                exp_date = crow[3]
                exp_days = None
                if exp_date:
                    if isinstance(exp_date, str):
                        try:
                            exp_date = date.fromisoformat(exp_date)
                        except (ValueError, TypeError):
                            exp_date = None
                    if exp_date:
                        exp_days = (exp_date - today).days
                contract_info[cid] = (remaining, credits_total, exp_days)

    # ── 7. Build SessionPrepItems ──
    session_items: list[SessionPrepItem] = []
    non_client_items: list[SessionPrepItem] = []
    clients_with_alerts_count = 0

    for event, client in events_with_clients:
        # Skip past events
        if event.data_fine and event.data_fine < now_dt:
            continue

        if not client or client.id is None:
            non_client_items.append(SessionPrepItem(
                event_id=event.id or 0,
                starts_at=event.data_inizio,
                ends_at=event.data_fine,
                category=event.categoria,
                event_title=event.titolo,
                event_notes=event.note,
            ))
            continue

        cid = client.id
        readiness = readiness_by_client.get(cid)
        counts = session_counts.get(cid, (0, 0))
        total_sess, completed_sess = counts
        last_sess = last_session_dates.get(cid)
        days_since = (today - last_sess).days if last_sess else None
        is_new = _is_new_client(client.data_creazione, today)
        clinical_alerts = conditions_by_client.get(cid, [])
        cinfo = contract_info.get(cid)
        contract_exp_days = cinfo[2] if cinfo else None

        health_checks = _build_health_checks(readiness) if readiness else []
        quality_hints = _build_quality_hints(
            readiness_item=readiness,
            days_since_last_session=days_since,
            contract_expiring_days=contract_exp_days,
            total_sessions=total_sess,
            is_new=is_new,
        ) if readiness else []

        if clinical_alerts:
            clients_with_alerts_count += 1

        client_name = " ".join(
            part for part in [client.nome, client.cognome] if part
        ).strip()

        data_nascita = client.data_nascita
        if isinstance(data_nascita, str):
            try:
                data_nascita = date.fromisoformat(data_nascita)
            except (ValueError, TypeError):
                data_nascita = None

        session_items.append(SessionPrepItem(
            event_id=event.id or 0,
            starts_at=event.data_inizio,
            ends_at=event.data_fine,
            category=event.categoria,
            event_title=event.titolo,
            event_notes=event.note,
            client_id=cid,
            client_name=client_name,
            client_age=_client_age(data_nascita, today),
            client_sex=client.sesso,
            client_since=client.data_creazione.date() if client.data_creazione else None,
            is_new_client=is_new,
            total_sessions=total_sess,
            completed_sessions=completed_sess,
            last_session_date=last_sess,
            days_since_last_session=days_since,
            health_checks=health_checks,
            clinical_alerts=clinical_alerts,
            quality_hints=quality_hints,
            active_plan_name=readiness.workout_plan_name if readiness else None,
            contract_credits_remaining=cinfo[0] if cinfo else None,
            contract_credits_total=cinfo[1] if cinfo else None,
            readiness_score=readiness.readiness_score if readiness else None,
        ))

    return SessionPrepResponse(
        date=today,
        current_time=now_dt,
        sessions=session_items,
        non_client_events=non_client_items,
        total_sessions=len(session_items),
        clients_with_alerts=clients_with_alerts_count,
    )
