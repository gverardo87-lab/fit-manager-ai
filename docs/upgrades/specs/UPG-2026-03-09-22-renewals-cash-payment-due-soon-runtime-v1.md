# UPG-2026-03-09-22 - Renewals & Cash Payment Due Soon Runtime v1

## Context

Il workspace `Rinnovi & Incassi` esiste gia come shell frontend additiva sopra `workspace=renewals_cash`, ma il motore runtime espone ancora solo:

- `payment_overdue`
- `contract_renewal_due`

Questo lascia vuota o troppo povera la parte `Oggi / Entro 7 giorni` della surface finance, nonostante il contratto tipologico supporti gia `payment_due_soon`.

## Objective

Aggiungere il case runtime `payment_due_soon` in modo stretto, deterministico e senza sporcare `Oggi`.

## Scope

### In

- `api/services/workspace_engine.py`
- `tests/test_workspace_today.py`
- shell frontend finance su `/rinnovi-incassi`
- sync docs governance

### Out

- nessuna mutation finance dal workspace
- nessun KPI monetario globale
- nessun nuovo endpoint
- nessun `recurring_expense_due` in questo microstep

## Decisioni Dure

1. `payment_due_soon` nasce solo dal dominio `Rate`.
2. Un contratto con almeno una rata overdue non genera `payment_due_soon`.
3. `payment_due_soon` non entra nel workspace `today`.
4. La visibilita completa degli importi resta confinata a `renewals_cash`.

## Runtime Rules

### Source

- tabella `Rate`
- `stato in ("PENDENTE", "PARZIALE")`
- `data_scadenza >= reference_date`
- `data_scadenza <= reference_date + 7 giorni`
- `Contract.chiuso == False`

### Merge

- root entity: `contract`
- merge key: `case:payment_due_soon:contract:{contract_id}`
- aggregazione per contratto

### Suppression

- se lo stesso contratto ha gia `payment_overdue`, il case non viene generato

### Buckets

- `today` se `days_left == 0`
- `upcoming_3d` se `days_left <= 3`
- `upcoming_7d` se `days_left <= 7`

### Severity

- `high` se `days_left == 0`
- `medium` se `days_left <= 3`
- `low` se `days_left <= 7`

### Today Exclusion

`payment_due_soon` resta escluso da `workspace=today`.

Motivo:

- `Oggi` deve restare collega operativo generale, non backlog contabile;
- il nuovo case serve il workspace finance dedicato;
- il trainer deve vedere gli incassi in arrivo nel contesto privato corretto, non come rumore cross-domain.

## Payload Expectations

### List

- `workspace = "renewals_cash"`
- `case_kind = "payment_due_soon"`
- `title = "Incasso in arrivo: <cliente>"`
- `reason` singola e spiegabile
- `finance_context.visibility = "full"`

### Detail

Il detail deve esporre:

- segnali sulle rate in scadenza
- contratto collegato
- cliente collegato
- timeline sintetica con scadenze rate

## Frontend Alignment

La shell `/rinnovi-incassi` aggiunge un filtro dedicato:

- `Incassi in arrivo`

Nessun altro cambio di IA in questo step.

## Verification Target

- `ruff` su `workspace_engine.py` e test workspace
- `eslint` sul page shell finance e su `workspace-ui.ts`
- test backend mirati:
  - `payment_due_soon` visibile in `renewals_cash`
  - `payment_due_soon` assente in `today`
  - soppressione se lo stesso contratto ha `payment_overdue`

## Residual Risks

- `contract_renewal_due` e `payment_due_soon` possono ancora coesistere sullo stesso contratto dentro `renewals_cash`; e accettabile in v1, ma potra richiedere una dominance finance-specifica se la densita aumenta.
- `recurring_expense_due` resta fuori dal runtime e dal shell finche non viene estratto il dominio `pending-expenses` in helper condiviso.

## Next Smallest Step

Se il payload reale su `crm_dev.db` conferma buon rapporto segnale/rumore:

1. aggiungere `recurring_expense_due`
2. valutare dominance finance-specifica `payment_due_soon > contract_renewal_due` sullo stesso contratto
