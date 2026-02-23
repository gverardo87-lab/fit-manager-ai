# api/routers/dashboard.py
"""
Endpoint Dashboard — KPI aggregati con query SQL ottimizzate.

Tutte le metriche vengono calcolate direttamente nel database
tramite func.count() e func.sum(). Nessun record viene caricato
in Python — latenza zero, scalabile anche con migliaia di record.

Multi-tenancy: ogni query filtra per trainer_id dal JWT.
"""

from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func, text

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.movement import CashMovement
from api.models.rate import Rate
from api.models.event import Event
from api.models.contract import Contract
from api.schemas.financial import (
    DashboardSummary, ReconciliationItem, ReconciliationResponse,
    AlertItem, DashboardAlerts,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    KPI aggregati per la dashboard del trainer.

    Metriche:
    - active_clients: clienti con stato 'Attivo'
    - monthly_revenue: somma ENTRATE del mese corrente
    - pending_rates: rate scadute o in scadenza nei prossimi 7 giorni
    - todays_appointments: eventi di oggi

    Tutte le query usano func.count/func.sum — aggregazione SQL pura.
    """
    today = date.today()

    # 1. Clienti attivi
    active_clients = session.exec(
        select(func.count(Client.id)).where(
            Client.trainer_id == trainer.id,
            Client.stato == "Attivo",
            Client.deleted_at == None,
        )
    ).one()

    # 2. Revenue mese corrente (solo ENTRATE)
    first_of_month = today.replace(day=1)
    if today.month == 12:
        first_of_next = today.replace(year=today.year + 1, month=1, day=1)
    else:
        first_of_next = today.replace(month=today.month + 1, day=1)

    revenue_result = session.exec(
        select(func.sum(CashMovement.importo)).where(
            CashMovement.trainer_id == trainer.id,
            CashMovement.tipo == "ENTRATA",
            CashMovement.data_effettiva >= first_of_month,
            CashMovement.data_effettiva < first_of_next,
            CashMovement.deleted_at == None,
        )
    ).one()
    monthly_revenue = revenue_result or 0.0

    # 3. Rate pendenti: scadute (data_scadenza < oggi) + in scadenza (prossimi 7 giorni)
    #    Deep filter: solo rate di contratti del trainer

    deadline = today + timedelta(days=7)
    pending_rates = session.exec(
        select(func.count(Rate.id))
        .join(Contract, Rate.id_contratto == Contract.id)
        .where(
            Contract.trainer_id == trainer.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.data_scadenza <= deadline,
            Rate.deleted_at == None,
            Contract.deleted_at == None,
            Contract.chiuso == False,
        )
    ).one()

    # 4. Appuntamenti di oggi (solo attivi — escludi Cancellato)
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    todays_appointments = session.exec(
        select(func.count(Event.id)).where(
            Event.trainer_id == trainer.id,
            Event.data_inizio >= today_start,
            Event.data_inizio <= today_end,
            Event.stato != "Cancellato",
            Event.deleted_at == None,
        )
    ).one()

    # 5. Ledger alerts: contratti con divergenza totale_versato vs movimenti
    divergent_count = session.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT c.id
            FROM contratti c
            LEFT JOIN movimenti_cassa m ON m.id_contratto = c.id
                AND m.tipo = 'ENTRATA' AND m.deleted_at IS NULL
            WHERE c.trainer_id = :tid AND c.deleted_at IS NULL
            GROUP BY c.id
            HAVING ROUND(c.totale_versato - COALESCE(SUM(m.importo), 0), 2) > 0.01
               OR ROUND(COALESCE(SUM(m.importo), 0) - c.totale_versato, 2) > 0.01
        )
    """), {"tid": trainer.id}).scalar() or 0

    return DashboardSummary(
        active_clients=active_clients,
        monthly_revenue=round(monthly_revenue, 2),
        pending_rates=pending_rates,
        todays_appointments=todays_appointments,
        ledger_alerts=divergent_count,
    )


@router.get("/reconciliation", response_model=ReconciliationResponse)
def get_reconciliation(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Audit riconciliazione: confronta totale_versato di ogni contratto
    con la somma dei CashMovement ENTRATA legati.

    Rileva divergenze in entrambe le direzioni:
    - totale_versato > ledger: pagamenti registrati su contratto ma senza CashMovement
    - ledger > totale_versato: CashMovement orfani o doppi

    Soglia: 0.01 EUR (tolleranza arrotondamento).
    """
    rows = session.execute(text("""
        SELECT c.id, cl.nome, cl.cognome, c.totale_versato,
               COALESCE(SUM(CASE WHEN m.tipo = 'ENTRATA' THEN m.importo ELSE 0 END), 0) as ledger
        FROM contratti c
        LEFT JOIN clienti cl ON cl.id = c.id_cliente
        LEFT JOIN movimenti_cassa m ON m.id_contratto = c.id AND m.deleted_at IS NULL
        WHERE c.trainer_id = :tid AND c.deleted_at IS NULL
        GROUP BY c.id
    """), {"tid": trainer.id}).fetchall()

    items = []
    aligned = 0
    for row in rows:
        cid, nome, cognome, versato, ledger = row
        delta = round(versato - ledger, 2)
        if abs(delta) > 0.01:
            items.append(ReconciliationItem(
                contract_id=cid,
                client_name=f"{nome or ''} {cognome or ''}".strip(),
                totale_versato=round(versato, 2),
                ledger_total=round(ledger, 2),
                delta=delta,
            ))
        else:
            aligned += 1

    return ReconciliationResponse(
        total_contracts=len(rows),
        aligned=aligned,
        divergent=len(items),
        items=items,
    )


@router.get("/ghost-events")
def get_ghost_events(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Eventi fantasma: sessioni passate ancora in stato 'Programmato'.

    Restituisce la lista completa con dati cliente per risoluzione inline
    dalla Dashboard (Sheet con azioni 'Completata'/'Cancellata').

    Ordinamento: piu' vecchi prima (urgenza decrescente).
    """
    today_start = datetime.combine(date.today(), datetime.min.time())

    stmt = (
        select(Event)
        .where(
            Event.trainer_id == trainer.id,
            Event.data_fine < today_start,
            Event.stato == "Programmato",
            Event.deleted_at == None,
        )
        .order_by(Event.data_inizio.asc())
    )
    events = session.exec(stmt).all()

    # Batch fetch nomi clienti (anti-N+1)
    client_ids = {e.id_cliente for e in events if e.id_cliente}
    clients_map: dict[int, Client] = {}
    if client_ids:
        clients = session.exec(
            select(Client).where(Client.id.in_(client_ids))
        ).all()
        clients_map = {c.id: c for c in clients}

    items = []
    for e in events:
        cl = clients_map.get(e.id_cliente) if e.id_cliente else None
        items.append({
            "id": e.id,
            "data_inizio": e.data_inizio.isoformat() if isinstance(e.data_inizio, datetime) else str(e.data_inizio),
            "data_fine": e.data_fine.isoformat() if isinstance(e.data_fine, datetime) else str(e.data_fine),
            "categoria": e.categoria,
            "titolo": e.titolo,
            "id_cliente": e.id_cliente,
            "id_contratto": e.id_contratto,
            "stato": e.stato,
            "note": e.note,
            "cliente_nome": cl.nome if cl else None,
            "cliente_cognome": cl.cognome if cl else None,
        })

    return {"items": items, "total": len(items)}


@router.get("/overdue-rates")
def get_overdue_rates(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Rate scadute: rate PENDENTI/PARZIALI con data_scadenza < oggi.

    Restituisce dati completi per risoluzione inline dalla Dashboard
    (Sheet con pagamento rapido). Include dati cliente e contratto.

    Ordinamento: piu' vecchie prima (urgenza decrescente).
    """
    today = date.today()

    stmt = (
        select(Rate, Contract, Client)
        .join(Contract, Rate.id_contratto == Contract.id)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.trainer_id == trainer.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.data_scadenza < today,
            Rate.deleted_at == None,
            Contract.deleted_at == None,
            Contract.chiuso == False,
        )
        .order_by(Rate.data_scadenza.asc())
    )
    rows = session.exec(stmt).all()

    items = []
    for rate, contract, client in rows:
        residuo = round(rate.importo_previsto - rate.importo_saldato, 2)
        giorni = (today - rate.data_scadenza).days if isinstance(rate.data_scadenza, date) else 0
        items.append({
            "rate_id": rate.id,
            "data_scadenza": rate.data_scadenza.isoformat() if isinstance(rate.data_scadenza, date) else str(rate.data_scadenza),
            "importo_previsto": rate.importo_previsto,
            "importo_saldato": rate.importo_saldato,
            "importo_residuo": residuo,
            "giorni_ritardo": giorni,
            "stato": rate.stato,
            "contract_id": contract.id,
            "tipo_pacchetto": contract.tipo_pacchetto,
            "client_id": client.id,
            "client_nome": client.nome,
            "client_cognome": client.cognome,
        })

    return {"items": items, "total": len(items)}


@router.get("/expiring-contracts")
def get_expiring_contracts(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Contratti in scadenza con crediti inutilizzati (30 giorni).

    Restituisce dati completi per risoluzione inline dalla Dashboard
    (Sheet con progress bar crediti e countdown). Include credit engine
    computed-on-read: crediti_usati da COUNT eventi PT non cancellati.

    Ordinamento: scadenza piu' vicina prima.
    """
    today = date.today()
    deadline_30 = today + timedelta(days=30)

    # Step 1: contratti in finestra scadenza con crediti
    contracts = session.exec(
        select(Contract, Client)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.trainer_id == trainer.id,
            Contract.deleted_at == None,
            Contract.chiuso == False,
            Contract.data_scadenza != None,
            Contract.data_scadenza <= deadline_30,
            Contract.data_scadenza >= today,
            Contract.crediti_totali != None,
        )
        .order_by(Contract.data_scadenza.asc())
    ).all()

    if not contracts:
        return {"items": [], "total": 0}

    # Step 2: batch fetch crediti usati (anti-N+1)
    contract_ids = [c.id for c, _ in contracts]
    credit_rows = session.execute(text("""
        SELECT e.id_contratto, COUNT(*) as usati
        FROM agenda e
        WHERE e.id_contratto IN ({})
          AND e.categoria = 'PT'
          AND e.stato != 'Cancellato'
          AND e.deleted_at IS NULL
        GROUP BY e.id_contratto
    """.format(",".join(str(cid) for cid in contract_ids)))).fetchall()

    credits_map = {row[0]: row[1] for row in credit_rows}

    items = []
    for contract, client in contracts:
        usati = credits_map.get(contract.id, 0)
        totali = contract.crediti_totali or 0
        residui = max(totali - usati, 0)

        # Solo contratti con crediti residui
        if residui <= 0:
            continue

        scadenza = contract.data_scadenza
        if isinstance(scadenza, str):
            scadenza = date.fromisoformat(scadenza)
        giorni_rimasti = (scadenza - today).days if isinstance(scadenza, date) else 0

        items.append({
            "contract_id": contract.id,
            "tipo_pacchetto": contract.tipo_pacchetto,
            "data_scadenza": scadenza.isoformat() if isinstance(scadenza, date) else str(scadenza),
            "giorni_rimasti": giorni_rimasti,
            "crediti_totali": totali,
            "crediti_usati": usati,
            "crediti_residui": residui,
            "prezzo_totale": contract.prezzo_totale,
            "client_id": client.id,
            "client_nome": client.nome,
            "client_cognome": client.cognome,
        })

    return {"items": items, "total": len(items)}


@router.get("/inactive-clients")
def get_inactive_clients(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Clienti inattivi: attivi senza eventi negli ultimi 14 giorni.

    Restituisce dati completi per risoluzione inline dalla Dashboard
    (Sheet con info contatto e ultimo evento). Include telefono, email,
    data/categoria ultimo evento.

    Ordinamento: piu' a lungo inattivi prima.
    """
    today = date.today()
    cutoff_14 = today - timedelta(days=14)
    cutoff_start = datetime.combine(cutoff_14, datetime.min.time())

    # Step 1: clienti attivi senza eventi recenti
    inactive_clients = session.execute(text("""
        SELECT cl.id, cl.nome, cl.cognome, cl.telefono, cl.email
        FROM clienti cl
        WHERE cl.trainer_id = :tid
          AND cl.stato = 'Attivo'
          AND cl.deleted_at IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM agenda e
              WHERE e.id_cliente = cl.id
                AND e.data_inizio >= :cutoff
                AND e.stato != 'Cancellato'
                AND e.deleted_at IS NULL
          )
        ORDER BY cl.nome, cl.cognome
    """), {"tid": trainer.id, "cutoff": cutoff_start.isoformat()}).fetchall()

    if not inactive_clients:
        return {"items": [], "total": 0}

    # Step 2: batch fetch ultimo evento per ciascuno (anti-N+1)
    client_ids = [row[0] for row in inactive_clients]
    last_events = session.execute(text("""
        SELECT e.id_cliente, e.data_inizio, e.categoria
        FROM agenda e
        INNER JOIN (
            SELECT id_cliente, MAX(data_inizio) as max_data
            FROM agenda
            WHERE id_cliente IN ({})
              AND stato != 'Cancellato'
              AND deleted_at IS NULL
            GROUP BY id_cliente
        ) latest ON e.id_cliente = latest.id_cliente AND e.data_inizio = latest.max_data
        WHERE e.deleted_at IS NULL AND e.stato != 'Cancellato'
    """.format(",".join(str(cid) for cid in client_ids)))).fetchall()

    last_event_map: dict[int, tuple] = {}
    for row in last_events:
        last_event_map[row[0]] = (row[1], row[2])

    items = []
    for cid, nome, cognome, telefono, email in inactive_clients:
        last = last_event_map.get(cid)
        last_data = None
        last_cat = None
        giorni_inattivo = 14  # minimo

        if last:
            last_data_raw = last[0]
            last_cat = last[1]
            # Parse datetime string
            if isinstance(last_data_raw, str):
                try:
                    last_dt = datetime.fromisoformat(last_data_raw.replace(" ", "T"))
                    last_data = last_dt.date().isoformat()
                    giorni_inattivo = (today - last_dt.date()).days
                except ValueError:
                    last_data = last_data_raw
            elif isinstance(last_data_raw, datetime):
                last_data = last_data_raw.date().isoformat()
                giorni_inattivo = (today - last_data_raw.date()).days
            elif isinstance(last_data_raw, date):
                last_data = last_data_raw.isoformat()
                giorni_inattivo = (today - last_data_raw).days

        items.append({
            "client_id": cid,
            "nome": nome,
            "cognome": cognome,
            "telefono": telefono,
            "email": email,
            "giorni_inattivo": giorni_inattivo,
            "ultimo_evento_data": last_data,
            "ultimo_evento_categoria": last_cat,
        })

    # Ordinamento: piu' inattivi prima
    items.sort(key=lambda x: -x["giorni_inattivo"])

    return {"items": items, "total": len(items)}


@router.get("/alerts", response_model=DashboardAlerts)
def get_dashboard_alerts(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Warning proattivi — "Cosa richiede la mia attenzione ORA?"

    4 categorie di alert (query SQL aggregate, zero N+1):
    1. ghost_events: eventi passati ancora 'Programmato'
    2. expiring_contracts: contratti in scadenza (30gg) con crediti residui
    3. overdue_rates: rate scadute (data_scadenza < oggi)
    4. inactive_clients: clienti attivi senza eventi da >14 giorni
    """
    today = date.today()
    items: list[AlertItem] = []

    # ── 1. Eventi fantasma: ieri o prima, ancora "Programmato" ──
    yesterday_end = datetime.combine(today, datetime.min.time())
    ghost_count = session.exec(
        select(func.count(Event.id)).where(
            Event.trainer_id == trainer.id,
            Event.data_fine < yesterday_end,
            Event.stato == "Programmato",
            Event.deleted_at == None,
        )
    ).one()

    if ghost_count > 0:
        items.append(AlertItem(
            severity="critical",
            category="ghost_events",
            title=f"{ghost_count} {'evento' if ghost_count == 1 else 'eventi'} senza esito",
            detail="Aggiorna lo stato: completate o cancellate?",
            count=ghost_count,
            link="/agenda",
        ))

    # ── 2. Contratti in scadenza con crediti inutilizzati ──
    deadline_30 = today + timedelta(days=30)

    # Wrapped subquery: SQLite non accetta HAVING senza GROUP BY.
    # Calcoliamo crediti_usati come subquery scalare, poi filtriamo nel WHERE esterno.
    expiring_rows = session.execute(text("""
        SELECT * FROM (
            SELECT c.id, cl.nome, cl.cognome, c.tipo_pacchetto,
                   c.data_scadenza, c.crediti_totali,
                   COALESCE(
                       (SELECT COUNT(*) FROM agenda e
                        WHERE e.id_contratto = c.id
                          AND e.categoria = 'PT'
                          AND e.stato != 'Cancellato'
                          AND e.deleted_at IS NULL), 0
                   ) as crediti_usati
            FROM contratti c
            JOIN clienti cl ON cl.id = c.id_cliente
            WHERE c.trainer_id = :tid
              AND c.deleted_at IS NULL
              AND c.chiuso = 0
              AND c.data_scadenza IS NOT NULL
              AND c.data_scadenza <= :deadline
              AND c.data_scadenza >= :today
              AND c.crediti_totali IS NOT NULL
        ) sub
        WHERE sub.crediti_usati < sub.crediti_totali
    """), {"tid": trainer.id, "deadline": deadline_30.isoformat(), "today": today.isoformat()}).fetchall()

    if expiring_rows:
        for row in expiring_rows:
            cid, nome, cognome, pacchetto, scadenza_raw, totali, usati = row
            residui = totali - usati
            # Raw SQL restituisce date come stringa ISO — parse esplicito
            scadenza = date.fromisoformat(scadenza_raw) if isinstance(scadenza_raw, str) else scadenza_raw
            days_left = (scadenza - today).days if isinstance(scadenza, date) else 0
            # Grammatica condizionale: singolare/plurale
            crediti_label = "credito inutilizzato" if residui == 1 else "crediti inutilizzati"
            if days_left == 0:
                scadenza_label = f"{pacchetto or 'Contratto'} scade oggi"
            elif days_left == 1:
                scadenza_label = f"{pacchetto or 'Contratto'} scade domani"
            else:
                scadenza_label = f"{pacchetto or 'Contratto'} scade tra {days_left} giorni"
            items.append(AlertItem(
                severity="warning" if days_left > 7 else "critical",
                category="expiring_contracts",
                title=f"{nome} {cognome} — {residui} {crediti_label}",
                detail=scadenza_label,
                count=1,
                link="/contratti",
            ))

    # ── 3. Rate scadute (non solo "in scadenza", ma GIA' scadute) ──
    overdue_data = session.execute(text("""
        SELECT COUNT(*) as cnt,
               COALESCE(SUM(r.importo_previsto - r.importo_saldato), 0) as tot
        FROM rate_programmate r
        JOIN contratti c ON r.id_contratto = c.id
        WHERE c.trainer_id = :tid
          AND r.stato IN ('PENDENTE', 'PARZIALE')
          AND r.data_scadenza < :today
          AND r.deleted_at IS NULL
          AND c.deleted_at IS NULL
          AND c.chiuso = 0
    """), {"tid": trainer.id, "today": today.isoformat()}).fetchone()

    overdue_count = overdue_data[0] if overdue_data else 0
    overdue_amount = overdue_data[1] if overdue_data else 0

    if overdue_count > 0:
        items.append(AlertItem(
            severity="critical",
            category="overdue_rates",
            title=f"{overdue_count} {'rata scaduta' if overdue_count == 1 else 'rate scadute'}",
            detail=f"€{overdue_amount:,.2f} da riscuotere — registra i pagamenti".replace(",", "."),
            count=overdue_count,
            link="/cassa",
        ))

    # ── 4. Clienti inattivi: attivi senza eventi negli ultimi 14 giorni ──
    cutoff_14 = today - timedelta(days=14)
    cutoff_start = datetime.combine(cutoff_14, datetime.min.time())

    inactive_count = session.execute(text("""
        SELECT COUNT(*) FROM clienti cl
        WHERE cl.trainer_id = :tid
          AND cl.stato = 'Attivo'
          AND cl.deleted_at IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM agenda e
              WHERE e.id_cliente = cl.id
                AND e.data_inizio >= :cutoff
                AND e.stato != 'Cancellato'
                AND e.deleted_at IS NULL
          )
    """), {"tid": trainer.id, "cutoff": cutoff_start.isoformat()}).scalar() or 0

    if inactive_count > 0:
        items.append(AlertItem(
            severity="warning" if inactive_count <= 2 else "critical",
            category="inactive_clients",
            title=f"{inactive_count} {'cliente inattivo' if inactive_count == 1 else 'clienti inattivi'}",
            detail="Nessuna sessione da 14+ giorni — pianifica un contatto",
            count=inactive_count,
            link="/clienti",
        ))

    # ── Conteggi severity ──
    critical = sum(1 for i in items if i.severity == "critical")
    warning = sum(1 for i in items if i.severity == "warning")
    info = sum(1 for i in items if i.severity == "info")

    return DashboardAlerts(
        total_alerts=len(items),
        critical_count=critical,
        warning_count=warning,
        info_count=info,
        items=items,
    )
