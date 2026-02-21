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
from api.schemas.financial import (
    DashboardSummary, ReconciliationItem, ReconciliationResponse,
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
        )
    ).one()
    monthly_revenue = revenue_result or 0.0

    # 3. Rate pendenti: scadute (data_scadenza < oggi) + in scadenza (prossimi 7 giorni)
    #    Deep filter: solo rate di contratti del trainer
    from api.models.contract import Contract

    deadline = today + timedelta(days=7)
    pending_rates = session.exec(
        select(func.count(Rate.id))
        .join(Contract, Rate.id_contratto == Contract.id)
        .where(
            Contract.trainer_id == trainer.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.data_scadenza <= deadline,
        )
    ).one()

    # 4. Appuntamenti di oggi
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    todays_appointments = session.exec(
        select(func.count(Event.id)).where(
            Event.trainer_id == trainer.id,
            Event.data_inizio >= today_start,
            Event.data_inizio <= today_end,
        )
    ).one()

    # 5. Ledger alerts: contratti con divergenza totale_versato vs movimenti
    divergent_count = session.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT c.id
            FROM contratti c
            LEFT JOIN movimenti_cassa m ON m.id_contratto = c.id AND m.tipo = 'ENTRATA'
            WHERE c.trainer_id = :tid
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
        LEFT JOIN movimenti_cassa m ON m.id_contratto = c.id
        WHERE c.trainer_id = :tid
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
