# UPG-2026-03-09-21 - Renewals & Cash Frontend Shell v1

## Context

`UPG-2026-03-09-20` ha formalizzato la spec tecnica del workspace `Rinnovi & Incassi`.

Il backend necessario per un primo shell additivo esisteva gia:

- `GET /api/workspace/cases?workspace=renewals_cash`
- `GET /api/workspace/cases/{case_id}?workspace=renewals_cash`
- case type runtime attivi:
  - `payment_overdue`
  - `contract_renewal_due`

Mancava ancora la superficie frontend dedicata.

## Problem

La finanza aveva due estremi gia presenti ma incompleti:

- `/cassa`: contesto ledger-first, corretto ma troppo contabile per lavorare i casi economici come queue operativa;
- `Oggi`: puo mostrare solo urgenze economiche redatte, ma non e il posto giusto per gestire importi, residui e rinnovi.

Serveva una pagina privata che:

- mostrasse i casi finance con importi completi;
- riusasse il case engine esistente;
- non introducesse nuove API o nuova logica backend prematura.

## Decision

Introdurre il primo shell frontend `Rinnovi & Incassi` come route additiva basata solo sul contratto `renewals_cash` gia esistente.

Scelte bloccate:

- nessuna nuova API;
- nessun nuovo `case_kind`;
- nessuna mutation workspace;
- nessun KPI monetario globale inventato da una lista paginata.

## Implementation

Touched files:

- `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx`
- `frontend/src/components/workspace/WorkspaceCaseCard.tsx`
- `frontend/src/components/layout/Sidebar.tsx`

### Nuova route

Nuova pagina:

- `/rinnovi-incassi`

La pagina consuma:

- `useWorkspaceCases({ workspace: "renewals_cash", page_size: 100, sort_by: "priority" })`
- `useWorkspaceCaseDetail({ workspace: "renewals_cash", caseId })`

### IA della pagina

- header finance dedicato;
- brief deterministico;
- pill count-based:
  - `Critici`
  - `Oggi`
  - `Entro 7 giorni`
  - `Da pianificare`
- filtri locali:
  - `Tutti`
  - `Incassi in ritardo`
  - `Rinnovi`
- queue bucketizzata:
  - `Critici` <- `now`
  - `Oggi` <- `today`
  - `Entro 7 giorni` <- `upcoming_3d + upcoming_7d`
  - `Da pianificare` <- `waiting`
- detail panel sticky riusato dal workspace engine

### Sidebar

Aggiunta nuova voce nella sezione `Contabilita`:

- `Rinnovi & Incassi`

### Card refinement

`WorkspaceCaseCard` ora supporta un flag opzionale `showFinanceSummary`.

Nel workspace finance questo permette di mostrare in lista:

- importo dovuto;
- residuo;
- contesto economico gia leggibile senza aprire il dettaglio.

`Oggi` non viene alterato, perche il flag resta opt-in.

## Verification

### Frontend lint

- `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/app/(dashboard)/rinnovi-incassi/page.tsx" "src/components/workspace/WorkspaceCaseCard.tsx" "src/components/layout/Sidebar.tsx"`

Result:

- `PASS`

## Risks

- Il shell usa ancora una lista paginata (`page_size=100`), quindi i bucket visualizzati sono una vista iniziale del backlog e non una fotografia matematica completa se il volume futuro cresce molto.
- La pagina copre bene `payment_overdue` e `contract_renewal_due`, ma finche non entrano `payment_due_soon` e `recurring_expense_due` non racconta ancora tutto il workflow finance desiderato.
- I KPI in alto restano correttamente count-based; se venissero trasformati troppo presto in metriche monetarie aggregate, il rischio sarebbe mostrare numeri falsi.

## Next Smallest Step

Il prossimo passo corretto non e rifinire ancora la UI.

E:

1. osservare il payload reale di `renewals_cash` sul dataset DEV;
2. poi aggiungere il primo nuovo case kind finance ad alto valore:
   - `payment_due_soon`
3. solo dopo integrare `recurring_expense_due`.
