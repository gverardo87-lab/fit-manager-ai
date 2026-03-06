# API Layer — Backend Rules

FastAPI + SQLModel + SQLite (PostgreSQL-ready). Multi-tenant via JWT.

## Coordinamento parallelo layer (Codex + Claude Code)

Prima di editare file in `api/`:
1. Claim task su `docs/ai-sync/WORKBOARD.md`.
2. Compila `Locked files` con path reali in `api/`.
3. Se un file e gia lockato da altro agente, fermati e usa handoff.

A fine task:
1. Aggiorna `WORKBOARD.md` (commit, check, note).
2. Sincronizza `docs/upgrades/*` quando cambia comportamento o governance.
3. Rilascia lock file.

## Architettura

```
api/
├── main.py              App factory, CORS, lifespan (backup+seed+integrity), 15 routers
├── config.py            DATABASE_URL (env/port-auto), CATALOG_DATABASE_URL, JWT_SECRET, DATA_DIR (sys.frozen-aware)
├── database.py          Dual engine (business + catalog) + session factories
├── dependencies.py      get_current_trainer() → JWT validation
├── seed_exercises.py    Seed builtin: 311 esercizi + 426 relazioni + 494 media (idempotente, FK guard)
├── auth/
│   ├── router.py        POST /login, /register, /setup/status, /setup/create
│   ├── service.py       bcrypt hash, JWT create/validate
│   └── schemas.py       TokenResponse, LoginRequest
├── models/              SQLModel ORM (table=True) — 19 modelli
│   ├── trainer.py       trainers (tenant root, saldo_iniziale_cassa)
│   ├── client.py        clienti
│   ├── contract.py      contratti (+ relationships: rates, movements)
│   ├── rate.py          rate_programmate
│   ├── event.py         agenda
│   ├── movement.py      movimenti_cassa (ledger)
│   ├── recurring_expense.py  spese_ricorrenti
│   ├── exercise.py      esercizi (builtin + custom, in_subset flag)
│   ├── exercise_media.py esercizi_media (foto start/end)
│   ├── exercise_relation.py esercizi_relazioni (progressione/regressione/variante)
│   ├── workout.py       schede_allenamento + sessioni_scheda + esercizi_sessione + blocchi
│   ├── workout_log.py   allenamenti_eseguiti (monitoraggio compliance)
│   ├── measurement.py   misurazioni + valori_misurazione
│   ├── goal.py          obiettivi_cliente
│   ├── muscle.py        muscoli + esercizi_muscoli (catalog junction)
│   ├── joint.py         articolazioni + esercizi_articolazioni (catalog junction)
│   ├── medical_condition.py condizioni_mediche + esercizi_condizioni (catalog junction)
│   ├── audit_log.py     audit_log (timeline modifiche)
│   └── todo.py          todos (trainer-owned)
├── routers/             REST endpoints con Bouncer Pattern — 15 router
│   ├── _audit.py        log_audit() helper condiviso
│   ├── agenda.py        CRUD eventi + credit guard + _sync_contract_chiuso
│   ├── assistant.py     Parse + commit NLP (feature flag ASSISTANT_V1_ENABLED)
│   ├── backup.py        Backup/Restore/Export/Verify (7 endpoint, WAL-safe)
│   ├── clients.py       CRUD clienti
│   ├── contracts.py     CRUD contratti + batch fetch enriched
│   ├── dashboard.py     KPI + alerts + clinical readiness + inline resolution (8 GET, ~980 LOC)
│   ├── exercises.py     CRUD esercizi + safety-map + tassonomia (dual session)
│   ├── goals.py         CRUD obiettivi + progress tracking (dual session)
│   ├── measurements.py  CRUD misurazioni + valori (dual session)
│   ├── movements.py     Ledger + pending/confirm + forecast + saldo + audit-log
│   ├── rates.py         CRUD rate + pay/unpay atomic
│   ├── recurring_expenses.py  CRUD spese fisse + close/rettifica
│   ├── todos.py         CRUD todos + toggle completato
│   ├── workout_logs.py  CRUD log allenamenti (monitoraggio)
│   └── workouts.py      CRUD schede + sessioni + esercizi (deep IDOR chain)
├── schemas/             Pydantic v2 — 8 moduli
│   ├── assistant.py     ParseRequest/Response, CommitRequest/Response (6 schema)
│   ├── exercise.py      ExerciseCreate/Update/Response + media/relazioni/tassonomia
│   ├── financial.py     Contract/Rate/Movement/Dashboard/ClinicalReadiness/PaymentReceipt DTOs
│   ├── goal.py          GoalCreate/Update/Response + progress
│   ├── measurement.py   MeasurementCreate/Response + valori
│   ├── safety.py        SafetyMapResponse + ExerciseSafetyEntry
│   ├── workout.py       WorkoutPlan/Session/Exercise Create/Update/Response
│   └── workout_log.py   WorkoutLogCreate/Response
└── services/            Business logic — 5 servizi + 1 parser (8 moduli)
    ├── condition_rules.py  Regole deterministiche anamnesi → condizioni (80 pattern rules)
    ├── goal_engine.py      Calcolo progresso obiettivi
    ├── license.py          Verifica licenza JWT RSA (4-tier key resolution)
    ├── safety_engine.py    Safety map per-esercizio (extract conditions + build map)
    └── assistant_parser/   Parser NLP deterministico (6 moduli)
        ├── normalizer.py, intent_classifier.py, entity_extractor.py
        ├── entity_resolver.py, confidence.py, orchestrator.py
        └── commit_dispatcher.py
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
Il contratto e' il nodo centrale del sistema. 7 livelli di protezione:

1. **Residual validation** (`create_rate`, `update_rate`): via `_cap_rateizzabile()` — `acconto = totale_versato - sum(saldato)`, `cap = prezzo - acconto`, `spazio = cap - sum(previsto)`. `update_rate` usa `exclude_rate_id` per escludere la rata in modifica dal calcolo
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
5. **Flexible rate editing** (`update_rate`): rate pagate (SALDATA/PARZIALE) modificabili con vincoli:
   - `data_scadenza`, `descrizione`: sempre modificabili
   - `importo_previsto`: modificabile se >= importo_saldato (422 altrimenti)
   - Stato auto-ricalcolato: se `saldato >= previsto` → SALDATA, altrimenti → PARZIALE
   - Residual check via `_cap_rateizzabile(exclude_rate_id=rate.id)`
6. **CashMovement date sync**: modifica `data_scadenza` su rata pagata → aggiorna atomicamente `data_effettiva` di tutti i CashMovement collegati (ENTRATA, non soft-deleted) + audit trail
7. **Delete guard**: contratto eliminabile solo se zero rate non-saldate + zero crediti residui.
   CASCADE: soft-delete rate SALDATE + tutti CashMovement + detach eventi
8. **Credit guard** (`create_event`): se `id_contratto` esplicito e `crediti_usati >= crediti_totali`
   → 400 "Crediti esauriti". Escape hatch: evento PT senza contratto (campo vuoto).
9. **Rate date boundary** (`create_rate`, `update_rate`): `data_scadenza` rata non puo' superare
   `contract.data_scadenza` (422). `generate_payment_plan`: auto-cap Chargebee-style
   (`if due_date > contract.data_scadenza: due_date = contract.data_scadenza`).
10. **Contract shortening guard** (`update_contract`): nuova `data_scadenza` rifiutata se esistono
    rate con date oltre il nuovo termine (422 con conteggio rate e messaggio chiaro).
11. **Expired contract detection** (lista contratti + lista clienti): `ha_rate_scadute` considera
    tutte le rate non saldate su contratti scaduti: `or_(Rate.data_scadenza < today, Contract.data_scadenza < today)`.

### Conferma & Registra (Spese Ricorrenti)
Paradigma esplicito: l'utente vede le spese in attesa e le conferma manualmente.
Nessun auto-sync — `GET /stats` e' pure read-only.

**Endpoint**:
- `GET /movements/pending-expenses?anno=X&mese=Y` — calcola occorrenze non confermate
- `POST /movements/confirm-expenses` — crea CashMovement con `operatore="CONFERMA_UTENTE"`
- `POST /recurring-expenses/{id}/close` — chiusura/rettifica con cutoff contabile

**Regole chiusura/rettifica** (`/recurring-expenses/{id}/close`):
- Endpoint idempotente: può essere richiamato anche su spesa già disattivata
- Movimenti `> cutoff` devono avere storno attivo (`ENTRATA`, `categoria="STORNO_SPESA_FISSA"`)
- Movimenti `<= cutoff` non devono avere storno attivo (storno soft-delete quando non più necessario)
- Nessun hard-delete dello storico reale: solo storni e soft-delete
- `GET /movements/stats` tratta `STORNO_SPESA_FISSA` come rettifica di uscita fissa, non come entrata operativa

**Ancoraggio**: basato su `expense.data_inizio` (non `data_creazione`).
Cross-year safe con mese assoluto: `abs_target = anno * 12 + mese`.

5 frequenze supportate:
- **MENSILE**: ogni mese, key `"YYYY-MM"`
- **SETTIMANALE**: ogni lunedi del mese, key `"YYYY-MM-DD"`
- **TRIMESTRALE**: `(abs_target - abs_start) % 3 == 0`, key `"YYYY-MM"`
- **SEMESTRALE**: `(abs_target - abs_start) % 6 == 0`, key `"YYYY-MM"`
- **ANNUALE**: `mese == start.month`, key `"YYYY"`

Idempotenza: `INSERT WHERE NOT EXISTS` con dedup key `(trainer_id, id_spesa_ricorrente, mese_anno)`.

### Financial Forecast (Proiezione)
`GET /movements/forecast?mesi=3` — pure read-only, zero side effects.

Aggrega 3 fonti per produrre una proiezione finanziaria:
1. **Rate PENDENTE/PARZIALE** — `importo_residuo` raggruppato per mese scadenza (entrate certe)
2. **Spese ricorrenti attive** — occurrence engine per ogni mese futuro (uscite fisse)
3. **Storico ultimi 3 mesi** — media uscite variabili (`tipo=USCITA AND id_spesa_ricorrente IS NULL`)

Produce: 4 KPI predittivi + proiezione mensile + timeline cronologica con saldo cumulativo.
Riusa `_get_occurrences_in_month()` per le spese ricorrenti (stessa logica del pending engine).

## Convenzioni

- Nomi endpoint: italiano nel dominio (`id_cliente`, `data_scadenza`), inglese infrastruttura (`trainer_id`)
- Response: sempre Pydantic `model_validate(orm_object)` con `from_attributes=True`
- Error response: `HTTPException` con status code + detail string
- Logging: `import logging; logger = logging.getLogger(__name__)`
- Migrations: Alembic (`alembic/versions/`). `env.py` legge `DATABASE_URL` da environment (fallback: `alembic.ini`). Ogni migrazione va applicata a ENTRAMBI i DB (prod + dev)

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
- Ogni spesa ricorrente confermata → CashMovement USCITA
- Ogni rettifica chiusura → CashMovement ENTRATA con `categoria="STORNO_SPESA_FISSA"`
- operatore: "API" (manuale), "CONFERMA_UTENTE", "CONFERMA_CHIUSURA", "STORNO_UTENTE", "SISTEMA_RECURRING" (legacy)

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
- Ogni CREATE/UPDATE/DELETE/RESTORE su entity business viene loggato quando applicabile
- Il campo `changes` contiene JSON diff campo-per-campo (solo UPDATE)
- `log_audit()` NON fa commit — il chiamante committa atomicamente
- `pay_rate` e `unpay_rate` generano 2 audit entries: rata + contratto

## Dashboard System (~980 LOC)

8 endpoint in `dashboard.py`:

| Endpoint | Scopo | Tipo query |
|----------|-------|------------|
| `GET /summary` | KPI aggregati (4 metriche) | `func.count/func.sum` |
| `GET /reconciliation` | Audit contratti vs ledger | Raw SQL con GROUP BY |
| `GET /alerts` | Warning proattivi (4 categorie) | 4 query aggregate |
| `GET /clinical-readiness` | Coda readiness clinica per onboarding | ORM + timeline computation |
| `GET /ghost-events` | Eventi fantasma per risoluzione inline | ORM + batch fetch clienti |
| `GET /overdue-rates` | Rate scadute per pagamento inline | ORM join 3 entita' |
| `GET /expiring-contracts` | Contratti in scadenza con crediti | ORM + batch fetch crediti |
| `GET /inactive-clients` | Clienti inattivi con ultimo evento | Raw SQL + batch fetch ultimo evento |

### Clinical Readiness (`/clinical-readiness`)
Coda deterministica per onboarding/migrazione clienti. Per ogni cliente attivo calcola:
- **anamnesi_state**: "missing" | "legacy" | "structured" (`_get_anamnesi_state()`)
- **readiness_score**: 0-100 composito (anamnesi 40pt + misurazioni 30pt + scheda 30pt)
- **priority**: "high" | "medium" | "low" da `priority_score` deterministico
- **next_action_code/label/href**: CTA actionable con deep-link auto-start
- **timeline**: `_compute_timeline_due()` — gap immediati = overdue, review periodiche (30/21/180gg)
- **Ordinamento**: `priority_score` desc → `readiness_score` asc → cognome/nome

Schema: `ClinicalReadinessClientItem`, `ClinicalReadinessSummary`, `ClinicalReadinessResponse` in `financial.py`.

Pattern condiviso per endpoint inline resolution:
- **Anti-N+1**: batch fetch dati correlati dopo query principale
- **Multi-entity select**: `session.exec(select(Rate, Contract, Client).join(...))` restituisce tuple
- **Date parse**: SQLite restituisce date come stringhe — `date.fromisoformat()` per confronti
- **Ordinamento urgenza**: record piu' vecchi/urgenti prima

## Test

Due famiglie di test:

**pytest** (`tests/`):
- DB SQLite in-memory, isolamento totale (StaticPool)
- `test_pay_rate.py` (12): pagamento atomico, overpayment, deep IDOR, storico pagamenti parziali
- `test_unpay_rate.py` (4): revoca pagamento, decrements, soft delete movement
- `test_rate_guards.py` (12): editing flessibile rate pagate, importo >= saldato, residuo su update, CashMovement date sync
- `test_soft_delete_integrity.py` (5): delete blocked with rates, restrict, stats filtrate
- `test_sync_recurring.py`: pending/confirm, chiusura/rettifica cutoff (anche su spesa disattivata), idempotenza, restore/rimozione storni, coerenza stats/grafico
- `test_contract_integrity.py` (16): residual, chiuso guard, auto-close, delete guards + cascade
- `test_aging_report.py` (4): bucket assignment, exclude saldate/chiusi, empty zeroes
- `test_dashboard_clinical_readiness.py`: readiness score, priority, timeline, CTA generation
- Run: `pytest tests/ -v`

**E2E** (`tools/admin_scripts/test_*.py`):
- Richiedono server avviato + DB reale
- Coprono: CRUD, IDOR, multi-tenant, mass assignment, pagamento atomico, dashboard
- Run: `python tools/admin_scripts/test_crud_idor.py` (etc.)

**Legacy** (`tests/legacy/`):
- Rotti — referenziano moduli eliminati (WorkoutGeneratorV2, ExerciseArchive)
- Da non eseguire finche' core/ non viene aggiornato
