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
│   ├── agenda.py        CRUD eventi + _sync_contract_chiuso (auto-close/reopen)
│   ├── movements.py     Ledger + pending/confirm spese ricorrenti
│   ├── recurring_expenses.py  CRUD spese fisse
│   ├── dashboard.py     KPI + alerts + inline resolution endpoints (7 GET)
│   └── backup.py        Backup/Restore/Export (5 endpoint)
└── schemas/
    └── financial.py     Contract/Rate/Movement/Dashboard/PaymentReceipt DTOs
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

### Payment History Enrichment
Il dettaglio contratto (`get_contract`) carica lo storico pagamenti per ogni rata:
```python
# receipt_map: dict[int, list[CashMovement]] — tutte le rate (non solo SALDATE)
movements = session.exec(
    select(CashMovement).where(
        CashMovement.id_rata.in_(rate_ids),
        CashMovement.tipo == "ENTRATA",
        CashMovement.deleted_at == None,
    ).order_by(CashMovement.data_effettiva.asc())
).all()
# Ogni rata riceve campo `pagamenti: list[RatePaymentReceipt]` (cronologico)
# Backward-compat: `data_pagamento` e `metodo_pagamento` = ultimo pagamento
```

### Contract Integrity Engine
Il contratto e' il nodo centrale del sistema. 6 livelli di protezione:

1. **Residual validation** (`create_rate`, `update_rate`): `sum(rate attive) + nuova ≤ prezzo - totale_versato`
2. **Chiuso guard**: `create_rate`, `generate_payment_plan`, `create_event(id_contratto)`
   rifiutano operazioni su contratti chiusi (400)
3. **Overpayment check** (`pay_rate`):
   - B-bis: importo ≤ residuo rata
   - B-ter: importo ≤ residuo contratto (prezzo - totale_versato)
4. **Auto-close/reopen — SIMMETRICO** (INVARIANTE critico):
   - Condizione: `chiuso = (stato_pagamento == "SALDATO") AND (crediti_usati >= crediti_totali)`
   - **Lato rate** (`rates.py`): `pay_rate` → auto-close | `unpay_rate` → auto-reopen (via stato_pagamento)
   - **Lato eventi** (`agenda.py`): `_sync_contract_chiuso()` — helper condiviso chiamato da:
     - `create_event` (crediti_usati sale)
     - `delete_event` (crediti_usati scende)
     - `update_event` quando `stato` cambia (es. Completato ↔ Cancellato)
   - **MAI** aggiungere operazioni che modificano `crediti_usati` senza chiamare `_sync_contract_chiuso()`
5. **Delete guard**: contratto eliminabile solo se zero rate non-saldate + zero crediti residui.
   CASCADE: soft-delete rate SALDATE + tutti CashMovement + detach eventi

### Conferma & Registra (Spese Ricorrenti)
Paradigma esplicito: l'utente vede le spese in attesa e le conferma manualmente.
Nessun auto-sync — `GET /stats` e' pure read-only.

**Endpoint**:
- `GET /movements/pending-expenses?anno=X&mese=Y` — calcola occorrenze non confermate
- `POST /movements/confirm-expenses` — crea CashMovement con `operatore="CONFERMA_UTENTE"`

**Ancoraggio**: basato su `expense.data_inizio` (non `data_creazione`).
Cross-year safe con mese assoluto: `abs_target = anno * 12 + mese`.

5 frequenze supportate:
- **MENSILE**: ogni mese, key `"YYYY-MM"`
- **SETTIMANALE**: ogni lunedi del mese, key `"YYYY-MM-DD"`
- **TRIMESTRALE**: `(abs_target - abs_start) % 3 == 0`, key `"YYYY-MM"`
- **SEMESTRALE**: `(abs_target - abs_start) % 6 == 0`, key `"YYYY-MM"`
- **ANNUALE**: `mese == start.month`, key `"YYYY"`

Idempotenza: `INSERT WHERE NOT EXISTS` con dedup key `(trainer_id, id_spesa_ricorrente, mese_anno)`.

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
- operatore: "API" (manuale), "CONFERMA_UTENTE" (spese confermate), "SISTEMA_RECURRING" (legacy)

## Soft Delete

Tutte le tabelle business hanno `deleted_at: Optional[datetime]`.
- SELECT: filtrano sempre `deleted_at == None`
- DELETE: impostano `deleted_at = datetime.now(timezone.utc)`
- Delete contratto: RESTRICT se rate non-saldate o crediti residui (409).
  CASCADE: soft-delete rate SALDATE + tutti CashMovement + detach eventi
- Delete cliente: RESTRICT se ha contratti attivi (chiuso=False, non eliminati)
- Sync engine: il NOT EXISTS filtra `AND deleted_at IS NULL`
- UNIQUE index: `uq_recurring_per_month` esclude record con `deleted_at IS NOT NULL`

## Audit Trail

Tabella `audit_log` + helper `log_audit()` in `api/routers/_audit.py`.
- Ogni CREATE/UPDATE/DELETE su entity business viene loggato
- Il campo `changes` contiene JSON diff campo-per-campo (solo UPDATE)
- `log_audit()` NON fa commit — il chiamante committa atomicamente
- `pay_rate` e `unpay_rate` generano 2 audit entries: rata + contratto

## Dashboard Alert System

7 endpoint in `dashboard.py`:

| Endpoint | Scopo | Tipo query |
|----------|-------|------------|
| `GET /summary` | KPI aggregati (4 metriche) | `func.count/func.sum` |
| `GET /reconciliation` | Audit contratti vs ledger | Raw SQL con GROUP BY |
| `GET /alerts` | Warning proattivi (4 categorie) | 4 query aggregate |
| `GET /ghost-events` | Eventi fantasma per risoluzione inline | ORM + batch fetch clienti |
| `GET /overdue-rates` | Rate scadute per pagamento inline | ORM join 3 entita' |
| `GET /expiring-contracts` | Contratti in scadenza con crediti | ORM + batch fetch crediti |
| `GET /inactive-clients` | Clienti inattivi con ultimo evento | Raw SQL + batch fetch ultimo evento |

Pattern condiviso per endpoint inline resolution:
- **Anti-N+1**: batch fetch dati correlati dopo query principale
- **Multi-entity select**: `session.exec(select(Rate, Contract, Client).join(...))` restituisce tuple
- **Date parse**: SQLite restituisce date come stringhe — `date.fromisoformat()` per confronti
- **Ordinamento urgenza**: record piu' vecchi/urgenti prima

## Test

Due famiglie di test:

**pytest** (`tests/` — 60 test):
- DB SQLite in-memory, isolamento totale (StaticPool)
- `test_pay_rate.py` (12): pagamento atomico, overpayment, deep IDOR, storico pagamenti parziali
- `test_unpay_rate.py` (4): revoca pagamento, decrements, soft delete movement
- `test_rate_guards.py` (9): immutabilita' rate con pagamenti, residuo su update
- `test_soft_delete_integrity.py` (5): delete blocked with rates, restrict, stats filtrate
- `test_sync_recurring.py` (10): pending/confirm, idempotenza, data_inizio, trimestrale, semestrale cross-year, soft delete resync, stats read-only
- `test_contract_integrity.py` (16): residual, chiuso guard, auto-close, delete guards + cascade
- `test_aging_report.py` (4): bucket assignment, exclude saldate/chiusi, empty zeroes
- Run: `pytest tests/ -v`

**E2E** (`tools/admin_scripts/test_*.py`):
- Richiedono server avviato + DB reale
- Coprono: CRUD, IDOR, multi-tenant, mass assignment, pagamento atomico, dashboard
- Run: `python tools/admin_scripts/test_crud_idor.py` (etc.)

**Legacy** (`tests/legacy/`):
- Rotti — referenziano moduli eliminati (WorkoutGeneratorV2, ExerciseArchive)
- Da non eseguire finche' core/ non viene aggiornato
