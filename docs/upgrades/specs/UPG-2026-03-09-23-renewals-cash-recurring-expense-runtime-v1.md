# UPG-2026-03-09-23 - Renewals & Cash Recurring Expense Runtime v1

## Context

Il workspace `Rinnovi & Incassi` espone gia:

- `payment_overdue`
- `payment_due_soon`
- `contract_renewal_due`

Resta pero scoperta una famiglia finance reale e quotidiana: le spese ricorrenti previste ma non ancora confermate nel ledger. Il dominio esiste gia tramite `GET /api/movements/pending-expenses` e `POST /api/movements/confirm-expenses`, quindi il rischio principale di questo microstep e duplicare logica o introdurre drift tra workspace e cassa.

## Objective

Aggiungere `recurring_expense_due` al workspace `renewals_cash` riusando come unica sorgente di verita la stessa logica che alimenta `pending-expenses`.

## Scope

### In

- helper condiviso `api/services/recurring_expense_schedule.py`
- reuse del helper in `api/routers/movements.py`
- reuse del helper in `api/routers/recurring_expenses.py`
- case runtime `recurring_expense_due` in `api/services/workspace_engine.py`
- filtro shell finance e copy UI in `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx` e `frontend/src/components/workspace/workspace-ui.ts`
- test workspace mirato
- sync docs governance

### Out

- nessuna mutation dal workspace
- nessun nuovo endpoint
- nessun KPI monetario globale
- nessuna riesposizione di `recurring_expense_due` in `Oggi`

## Hard Decisions

1. La sorgente di verita resta `list_pending_recurring_expense_occurrences(...)`.
2. Il workspace non puo inferire occorrenze o stati dal ledger con una logica diversa da `pending-expenses`.
3. `recurring_expense_due` resta confinato a `renewals_cash`.
4. La CTA primaria porta il trainer nel contesto giusto di cassa, non esegue conferme implicite.

## Runtime Design

## Shared Schedule Helper

Nuovo service condiviso:

- `api/services/recurring_expense_schedule.py`

Responsabilita:

- calcolo start date della ricorrenza
- espansione occorrenze del mese
- risoluzione `occurrence_key -> due_date`
- elenco `pending` trainer-scoped e deduplicato

Consumer riallineati:

- `api/routers/movements.py`
- `api/routers/recurring_expenses.py`
- `api/services/workspace_engine.py`

## Case Definition

- `case_kind`: `recurring_expense_due`
- root entity: `expense`
- merge key: `case:recurring_expense_due:expense:{expense_id}:{occurrence_key}`
- workspace nativo: `renewals_cash`

## Source

Una occorrenza entra nel workspace se:

- la spesa ricorrente e attiva
- l'occorrenza e pending secondo il helper condiviso
- la `due_date` cade tra `reference_date` e `reference_date + 7 giorni`

## Buckets

- `today` se `days_left <= 0`
- `upcoming_3d` se `days_left <= 3`
- `upcoming_7d` se `days_left <= 7`

## Severity

- `high` se `days_left <= 0`
- `medium` se `days_left <= 3`
- `low` se `days_left <= 7`

## Today Exclusion

`recurring_expense_due` e escluso da `workspace=today`.

Motivo:

- `Oggi` deve restare una regia cross-domain compatta
- la conferma di una spesa fissa e un gesto contabile, non un warning operativo generale
- l'importo completo deve restare in un contesto finance dedicato

## Payload Expectations

### List

- `title = "Spesa da confermare: <nome>"`
- `reason = "Occorrenza prevista il YYYY-MM-DD"`
- `finance_context.visibility = "full"`
- `finance_context.total_due_amount = importo occorrenza`
- `root_entity.href = /cassa?tab=recurring&anno=...&mese=...`

### Detail

Il detail deve esporre:

- segnale principale `recurring_expense_due`
- eventuale segnale categoria
- entita collegata `expense`
- preview attivita con creazione spesa, inizio ciclo e occorrenza dovuta

## Frontend Alignment

La shell `/rinnovi-incassi` aggiunge il filtro:

- `Spese ricorrenti`

`workspace-ui.ts` distingue anche il riepilogo finance:

- `payment_due_soon` -> `In arrivo ...`
- `recurring_expense_due` -> `Importo ...`

## Verification Target

- `ruff` su router/service/test toccati
- `eslint` su shell finance e `workspace-ui.ts`
- test workspace:
  - il case e visibile in `renewals_cash`
  - il case non entra in `today`
  - dopo `POST /confirm-expenses` il case sparisce dal workspace e dal pending

## Residual Risks

- il workspace finance puo ancora mostrare insieme `recurring_expense_due` e altri case sullo stesso periodo; e accettabile in v1 perche i root entity sono diversi (`expense` vs `contract`)
- il test backend HTTP copre il ciclo base, ma `pytest` locale resta bloccato dal `venv` che punta al launcher Microsoft Store

## Next Smallest Step

Se il payload reale resta pulito:

1. valutare dominance finance-specifica tra `payment_due_soon` e `contract_renewal_due`
2. solo dopo considerare metriche finance aggregate non derivate da liste paginate
