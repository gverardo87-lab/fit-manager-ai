# API Layer — Backend Rules

FastAPI + SQLModel + SQLite (PostgreSQL-ready). Multi-tenant via JWT.

## Architettura

```
api/
├── main.py              App factory, CORS, migrations, router registration
├── config.py            DATABASE_URL, JWT_SECRET, API_PREFIX
├── database.py          SQLModel engine + session factory
├── dependencies.py      get_current_trainer() → JWT validation
├── auth/
│   ├── router.py        POST /login, /register
│   ├── service.py       bcrypt hash, JWT create/validate
│   └── schemas.py       TokenResponse, LoginRequest
├── models/              SQLModel ORM (table=True)
│   ├── trainer.py       trainers (tenant root)
│   ├── client.py        clienti
│   ├── contract.py      contratti (+ relationships: rates, movements)
│   ├── rate.py          rate_programmate
│   ├── event.py         agenda
│   ├── movement.py      movimenti_cassa (ledger)
│   └── recurring_expense.py  spese_ricorrenti
├── routers/             REST endpoints con Bouncer Pattern
│   ├── _audit.py        log_audit() helper condiviso
│   ├── clients.py       CRUD clienti
│   ├── contracts.py     CRUD contratti + batch fetch enriched
│   ├── rates.py         CRUD rate + pay/unpay atomic
│   ├── agenda.py        CRUD eventi + credit sync
│   ├── movements.py     Ledger + recurring sync engine
│   ├── recurring_expenses.py  CRUD spese fisse
│   ├── dashboard.py     KPI aggregati (SQL func.count/func.sum)
│   └── backup.py        Backup/Restore/Export (5 endpoint)
└── schemas/
    └── financial.py     Contract/Rate/Movement/Dashboard DTOs
```

## Pattern Obbligatori

### Bouncer Pattern
Ogni endpoint inizia con il bouncer che verifica ownership:
```python
def _bouncer_rate(session, rate_id, trainer_id) -> Rate:
    rate = session.exec(
        select(Rate)
        .join(Contract, Rate.id_contratto == Contract.id)
        .where(Rate.id == rate_id, Contract.trainer_id == trainer_id)
    ).first()
    if not rate:
        raise HTTPException(404, "Rata non trovata")
    return rate
```
Non trovato = 404. Mai 403 (non rivelare esistenza dati altrui).

### Deep Relational IDOR
Catena di verifica ownership attraverso FK:
- Rate → `Contract.trainer_id`
- Contract → verifica `Client.trainer_id` su POST (Relational IDOR)
- Event → `trainer_id` diretto
- Movement → `trainer_id` diretto

### Mass Assignment Prevention
Gli schema Create NON contengono mai:
- `trainer_id` (iniettato dal JWT nel router)
- `id` (auto-generato)
- Campi calcolati (`crediti_usati`, `totale_versato`, `stato`)

```python
class ContractCreate(BaseModel):
    model_config = {"extra": "forbid"}  # rifiuta campi extra
    id_cliente: int  # verificato via Relational IDOR
    # NO trainer_id, NO id
```

### Atomic Transactions
Operazioni multi-tabella usano UN singolo commit:
```python
# pay_rate: aggiorna rata + contratto + crea CashMovement
session.add(rate)
session.add(contract)
session.add(movement)
session.commit()  # UNICO commit — tutto o niente
```

### Batch Fetch (anti N+1)
Liste enriched usano 4 query batch:
```python
contracts = session.exec(query).all()  # 1. contratti
all_rates = session.exec(select(Rate).where(Rate.id_contratto.in_(ids))).all()  # 2. rate
clients = session.exec(select(Client).where(Client.id.in_(client_ids))).all()  # 3. clienti
event_counts = session.exec(select(Event.id_contratto, func.count(...)).group_by(...))  # 4. crediti usati
```

### Contract Integrity Engine
Il contratto e' il nodo centrale del sistema. 5 livelli di protezione:

1. **Residual validation** (`create_rate`): `sum(rate attive) + nuova ≤ prezzo - acconto`
2. **Chiuso guard**: `create_rate`, `generate_payment_plan`, `create_event(id_contratto)`
   rifiutano operazioni su contratti chiusi (400)
3. **Overpayment check** (`pay_rate`):
   - B-bis: importo ≤ residuo rata
   - B-ter: importo ≤ residuo contratto (prezzo - totale_versato)
4. **Auto-close**: se `stato_pagamento == SALDATO` + `crediti_usati >= crediti_totali`
   → `chiuso = True` (trigger in `pay_rate` e `create_event`)
5. **Auto-reopen**: `unpay_rate` riapre se non piu' SALDATO (`chiuso = False`)

### Idempotent Sync Engine
`sync_recurring_expenses_for_month()`: genera CashMovement per spese ricorrenti.
Check esistenza prima di creare. Sicuro rieseguire.

## Convenzioni

- Nomi endpoint: italiano nel dominio (`id_cliente`, `data_scadenza`), inglese infrastruttura (`trainer_id`)
- Response: sempre Pydantic `model_validate(orm_object)` con `from_attributes=True`
- Error response: `HTTPException` con status code + detail string
- Logging: `import logging; logger = logging.getLogger(__name__)`
- Migrations: Alembic (`alembic/versions/`). Nuova migrazione: `alembic revision -m "desc"` → edit → `alembic upgrade head`

## Dipendenze

```python
# Questo layer importa SOLO:
fastapi, sqlmodel, pydantic, jose, bcrypt, python-dotenv, dateutil
# NON importa MAI da: core/, streamlit, frontend/
```

## Ledger Integrity

Il libro mastro (`movimenti_cassa`) e' sacro:
- Movimenti con `id_contratto` o `id_spesa_ricorrente` → protetti da DELETE
- Ogni pagamento rata → CashMovement ENTRATA (con nota cliente)
- Ogni acconto contratto → CashMovement ENTRATA
- Ogni spesa ricorrente → CashMovement USCITA (sync engine)
- operatore: "API" (manuale), "SISTEMA_RECURRING" (sync automatico)

## Soft Delete

Tutte le tabelle business hanno `deleted_at: Optional[datetime]`.
- SELECT: filtrano sempre `deleted_at == None`
- DELETE: impostano `deleted_at = datetime.now(timezone.utc)`
- Cascade: delete contratto → soft-delete rate associate (solo PENDENTI)
- Restrict: delete cliente bloccato se ha contratti attivi (chiuso=False, non eliminati)
- Sync engine: il NOT EXISTS filtra `AND deleted_at IS NULL`
- UNIQUE index: `uq_recurring_per_month` esclude record con `deleted_at IS NOT NULL`

## Audit Trail

Tabella `audit_log` + helper `log_audit()` in `api/routers/_audit.py`.
- Ogni CREATE/UPDATE/DELETE su entity business viene loggato
- Il campo `changes` contiene JSON diff campo-per-campo (solo UPDATE)
- `log_audit()` NON fa commit — il chiamante committa atomicamente
- `pay_rate` e `unpay_rate` generano 2 audit entries: rata + contratto

## Test

Due famiglie di test:

**pytest** (`tests/` — 38 test):
- DB SQLite in-memory, isolamento totale (StaticPool)
- `test_pay_rate.py` (10): pagamento atomico, overpayment, deep IDOR
- `test_unpay_rate.py` (4): revoca pagamento, decrements, soft delete movement
- `test_soft_delete_integrity.py` (5): delete blocked with rates, restrict, stats filtrate
- `test_sync_recurring.py` (4): idempotenza, disabled, resync
- `test_contract_integrity.py` (15): residual validation, chiuso guard, auto-close/reopen, delete guards strict
- Run: `pytest tests/ -v`

**E2E** (`tools/admin_scripts/test_*.py`):
- Richiedono server avviato + DB reale
- Coprono: CRUD, IDOR, multi-tenant, mass assignment, pagamento atomico, dashboard
- Run: `python tools/admin_scripts/test_crud_idor.py` (etc.)

**Legacy** (`tests/legacy/`):
- Rotti — referenziano moduli eliminati (WorkoutGeneratorV2, ExerciseArchive)
- Da non eseguire finche' core/ non viene aggiornato
