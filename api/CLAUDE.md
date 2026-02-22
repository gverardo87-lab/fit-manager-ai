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
│   ├── clients.py       CRUD clienti
│   ├── contracts.py     CRUD contratti + batch fetch enriched
│   ├── rates.py         CRUD rate + pay/unpay atomic
│   ├── agenda.py        CRUD eventi + credit sync
│   ├── movements.py     Ledger + recurring sync engine
│   ├── recurring_expenses.py  CRUD spese fisse
│   └── dashboard.py     KPI aggregati (SQL func.count/func.sum)
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

### Idempotent Sync Engine
`sync_recurring_expenses_for_month()`: genera CashMovement per spese ricorrenti.
Check esistenza prima di creare. Sicuro rieseguire.

## Convenzioni

- Nomi endpoint: italiano nel dominio (`id_cliente`, `data_scadenza`), inglese infrastruttura (`trainer_id`)
- Response: sempre Pydantic `model_validate(orm_object)` con `from_attributes=True`
- Error response: `HTTPException` con status code + detail string
- Logging: `import logging; logger = logging.getLogger(__name__)`
- Migrations: idempotenti in `main.py._run_migrations()` (ALTER TABLE IF NOT EXISTS)

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
