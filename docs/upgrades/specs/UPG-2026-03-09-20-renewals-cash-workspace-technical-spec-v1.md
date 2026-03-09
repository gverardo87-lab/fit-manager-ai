# UPG-2026-03-09-20 - Renewals & Cash Workspace Technical Spec v1

## Metadata

- Upgrade ID: `UPG-2026-03-09-20`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Workspace Finance UX + API Contract Evolution + Operational Cashflow`
- Priority: `high`
- Target release: `codex_02`
- Status: `planned`

## Context

Il workspace engine e il contratto read-only esistono gia:

- `workspace=today` e la home operativa generale;
- `workspace=renewals_cash` e gia supportato nel contratto API;
- la finanza completa e gia redatta in `today` e pienamente visibile solo in `renewals_cash`.

Runtime reale oggi:

- `payment_overdue` esiste gia come case type finance attivo;
- `contract_renewal_due` esiste gia come case type finance attivo;
- `GET /api/workspace/cases?workspace=renewals_cash` e `GET /api/workspace/cases/{case_id}?workspace=renewals_cash` sono gia disponibili;
- `payment_due_soon` e `recurring_expense_due` esistono nel contratto tipologico, ma non ancora nel motore runtime;
- il dominio `spese ricorrenti` esiste gia nel prodotto tramite `RecurringExpense` e `GET /api/movements/pending-expenses`.

Quindi il prossimo workspace non parte da zero: parte da un backend reale gia funzionante e lo porta a una surface finance dedicata.

## Problem

FitManager ha gia il dato economico giusto, ma non ha ancora la surface operativa giusta per usarlo ogni giorno.

Oggi la situazione e questa:

1. La dashboard resta correttamente neutra e non deve essere contaminata da importi e scadenze finance.
2. `Oggi` puo mostrare solo i casi economici critici in forma redatta, ma non puo diventare il posto dove gestire davvero rinnovi e incassi.
3. `/cassa` resta la superficie contabile completa, ma e un contesto ledger-first, non una coda operativa “chi devo incassare / quali rinnovi sto perdendo”.

Serve quindi un workspace dedicato che:

- renda visibili importi, date e residui;
- resti coerente con il case engine esistente;
- non duplichi la logica della cassa;
- diventi il cockpit privato di rinnovi, incassi e spese ricorrenti.

## Desired Outcome

Introdurre il workspace `Rinnovi & Incassi` come surface operativa dedicata alla pressione economico-contabile del trainer.

Il workspace deve:

- mostrare la queue finance in forma completa e non redatta;
- separare con chiarezza `scaduti`, `imminenti`, `rinnovi` e `spese ricorrenti`;
- riusare il motore `OperationalCase` gia esistente;
- supportare il trainer con CTA audit-safe verso `/cassa`, `/contratti`, `/clienti`;
- evitare KPI o aggregazioni inventate dal solo subset paginato.

## Scope

- In scope:
  - spec tecnica del workspace `renewals_cash`;
  - IA della pagina dedicata;
  - mappa dei case type MVP e delle estensioni immediate;
  - regole di priorita e bucket display;
  - strategia frontend MVP additiva;
  - evoluzione contrattuale minima per KPI finance aggregati corretti.
- Out of scope:
  - implementazione runtime/frontend;
  - sostituzione di `/cassa`;
  - nuove mutation API workspace;
  - analytics manageriali tipo margine, forecast ricavi o conto economico completo;
  - cutover di dashboard o `Oggi`.

## Impact Map

- Future files/modules expected:
  - `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx`
  - `frontend/src/components/workspace/WorkspaceFinanceCaseCard.tsx` oppure riuso controllato di `WorkspaceCaseCard.tsx`
  - `frontend/src/components/workspace/WorkspaceFinanceDetailPanel.tsx` oppure estensione minimale di `WorkspaceDetailPanel.tsx`
  - `frontend/src/hooks/useWorkspace.ts` (solo se serve un helper page-specifico)
  - `frontend/src/types/api.ts` (solo per la fase contrattuale B)
  - `api/services/workspace_engine.py` (fase B)
  - `api/schemas/workspace.py` (fase B)
  - `tests/test_workspace_today.py` oppure nuovo `tests/test_workspace_renewals_cash.py`
  - `docs/upgrades/specs/UPG-2026-03-09-20-renewals-cash-workspace-technical-spec-v1.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layers: `frontend`, `api`, `tests`, `docs`
- Invariants:
  - nessun importo completo sulla dashboard overview;
  - nessun importo completo in `workspace=today`;
  - `/cassa` resta il ledger/audit context canonico;
  - nessuna mutation write-capable sul namespace `/api/workspace/*` in questa fase;
  - ownership trainer e redazione finance restano invariate.

## Product / Technical Decisions Locked

- `Rinnovi & Incassi` non sostituisce `/cassa`; la completa.
- Il workspace usa lo stesso case engine del resto del sistema, non un motore finance separato.
- Il primo shell frontend deve essere additivo e costruito sopra `GET /api/workspace/cases?workspace=renewals_cash` e `GET /api/workspace/cases/{case_id}?workspace=renewals_cash`.
- Il primo MVP non deve inventare KPI monetari globali da una lista paginata incompleta.
- Le azioni del workspace restano deep-link verso flussi esistenti (`/cassa`, `/contratti`, `/clienti`, `confirm-expenses` via pagina cassa), non mutation inline workspace.
- `payment_overdue` resta il caso dominante sul contratto; `contract_renewal_due` non deve oscurarlo.

## Existing Runtime Baseline

### Gia attivo oggi

| Case kind | Workspace | Visibilita finance | Source attuale | Stato |
|---|---|---|---|---|
| `payment_overdue` | `renewals_cash` | `full` | `Rate + Contract + Client` | runtime attivo |
| `contract_renewal_due` | `renewals_cash` | `full` | `Contract + residual credits` | runtime attivo |

### Gia previsto ma non ancora runtime

| Case kind | Workspace | Source candidato | Stato |
|---|---|---|---|
| `payment_due_soon` | `renewals_cash` | rate future `<= 7 giorni` non overdue | contratto esistente, runtime assente |
| `recurring_expense_due` | `renewals_cash` | `RecurringExpense` / pending occurrences mese corrente | dominio esistente, runtime assente |

## IA Pagina - Renewals & Cash

### Route target

- route raccomandata: `/rinnovi-incassi`
- sidebar label: `Rinnovi & Incassi`

### Ruolo prodotto

Pagina privata del trainer per:

- recuperare incassi gia scaduti;
- non perdere rinnovi vicini;
- vedere in anticipo pressione economica dei prossimi giorni;
- confermare uscite ricorrenti senza aprire subito il ledger completo.

### Layout v1

```text
[ Header ]
Rinnovi & Incassi
brief finance di 1 riga

[ KPI strip ]
Critici | Oggi | Entro 7 giorni | Da pianificare

[ Main ]
sinistra: queue finance
destra: detail panel sticky
```

### Cosa non deve essere

- non una seconda pagina `/cassa`;
- non una dashboard con grafici economici;
- non una pagina forecast;
- non un conto economico;
- non un ledger.

## Buckets Display

Il backend mantiene i bucket canonici gia esistenti:

- `now`
- `today`
- `upcoming_3d`
- `upcoming_7d`
- `waiting`

La UI `Rinnovi & Incassi` li rimappa cosi:

| Bucket runtime | Label UI | Significato operativo |
|---|---|---|
| `now` | `Critici` | soldi gia persi o da registrare subito |
| `today` | `Oggi` | scadenze e rinnovi che conviene chiudere oggi |
| `upcoming_3d` + `upcoming_7d` | `Entro 7 giorni` | pressione finance vicina |
| `waiting` | `Da pianificare` | backlog finance non urgente |

Decisione: la shell finance aggrega visivamente `upcoming_3d` e `upcoming_7d` in un’unica sezione, ma preserva il badge `3g` / `7g` sulle singole card.

## Case Families

### MVP-A: shell additiva senza cambiare il contratto

1. `payment_overdue`
   - titolo: `Incasso in ritardo: <cliente>`
   - workspace: `renewals_cash`
   - bucket tipico: `now`
   - CTA primaria: `Apri cassa`

2. `contract_renewal_due`
   - titolo: `Rinnovo in arrivo: <cliente>`
   - workspace: `renewals_cash`
   - bucket tipico: `today / upcoming_3d / upcoming_7d / waiting`
   - CTA primaria: `Apri contratto`

### MVP-B: estensione motore immediatamente successiva

3. `payment_due_soon`
   - fonte: rate `PENDENTE/PARZIALE` con `data_scadenza >= today` e `<= today + 7 giorni`
   - soppressione: non generare il case se sullo stesso contratto esiste gia `payment_overdue`
   - CTA primaria: `Apri cassa`

4. `recurring_expense_due`
   - fonte: stessa logica del dominio `pending-expenses` del modulo movimenti
   - root entity: `expense`
   - merge key: `case:recurring_expense_due:expense:{id_spesa}:{mese_anno_key}`
   - CTA primaria: `Apri cassa`

## Card Anatomy - Finance

Le card finance devono essere piu dense di quelle generiche del workspace, ma sempre leggibili.

Campi visibili in lista:

- badge tipo: `Incasso`, `Rinnovo`, `Spesa`
- badge urgenza: `Critica`, `Oggi`, `3g`, `7g`, `Da pianificare`
- titolo
- importo principale
- data rilevante
- reason line singola
- CTA primaria

Esempi:

- `Incasso in ritardo: Luca Colombo`
- `€120 residui scaduti dal 2026-02-12`
- `1 rata scaduta sul contratto`

- `Rinnovo in arrivo: Sara Romano`
- `Scadenza 2026-03-14`
- `2 crediti residui`

Regola: qui gli importi sono visibili in lista, perche il workspace e per definizione un contesto finance privato.

## Detail Panel - Finance

Il pannello destro deve riusare il payload `WorkspaceCaseDetailResponse`, ma con semantica finance-first.

Ordine raccomandato:

1. azione consigliata
2. importi e date rilevanti
3. segnali sottostanti
4. entita collegate
5. timeline sintetica

### Requisiti minimi per `payment_overdue`

- importo residuo totale
- numero rate scadute
- prima scadenza
- contratto collegato
- cliente collegato

### Requisiti minimi per `contract_renewal_due`

- data scadenza contratto
- residuo economico
- crediti residui
- contratto collegato
- cliente collegato

### Requisiti minimi per `recurring_expense_due` (fase B)

- nome spesa
- importo
- categoria
- data prevista
- chiave occorrenza / mese

## KPI Strategy

### Decisione dura

Nel primo shell non e corretto calcolare KPI monetari globali dal solo `page=1&page_size=N` di `/api/workspace/cases`.

Questo sarebbe matematicamente scorretto se il backlog supera la pagina.

### MVP-A

Usare solo KPI count-based ricavati dal `summary` gia esistente:

- `Critici` -> `summary.now_count`
- `Oggi` -> `summary.today_count`
- `Entro 7 giorni` -> `summary.upcoming_7d_count`
- `Da pianificare` -> `summary.waiting_count`

Gli importi completi restano nelle card e nel detail panel, non nella header strip.

### MVP-B

Estendere `WorkspaceSummary` con un oggetto opzionale:

```ts
interface WorkspaceFinanceMetrics {
  overdue_case_count: number;
  overdue_amount_total: number;
  due_7d_case_count: number;
  due_7d_amount_total: number;
  renewal_case_count: number;
  renewal_residual_total: number;
  pending_expense_count: number;
  pending_expense_amount_total: number;
}
```

Nuova shape:

```ts
interface WorkspaceSummary {
  workspace: WorkspaceId;
  generated_at: string;
  critical_count: number;
  now_count: number;
  today_count: number;
  upcoming_7d_count: number;
  waiting_count: number;
  finance_metrics?: WorkspaceFinanceMetrics | null;
}
```

Policy:

- `today`, `onboarding`, `programmi` -> `finance_metrics = null`
- `renewals_cash` -> `finance_metrics` valorizzato

Questa estensione evita endpoint specializzati inutili e preserva la famiglia `/api/workspace/*`.

## Frontend Implementation Plan

### Phase A - additive shell without API contract changes

Route:

- `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx`

Data sources:

- `useWorkspaceCases({ workspace: "renewals_cash", page: 1, page_size: 50, sort_by: "priority" })`
- `useWorkspaceCaseDetail({ workspace: "renewals_cash", caseId })`

Sections:

- `Critici` <- items bucket `now`
- `Oggi` <- items bucket `today`
- `Entro 7 giorni` <- items bucket `upcoming_3d` + `upcoming_7d`
- `Da pianificare` <- items bucket `waiting`

Filters initially exposed:

- `Tutti`
- `Incassi in ritardo`
- `Rinnovi`

No local money aggregation from the current page subset.

### Phase B - contract evolution + runtime expansion

Backend:

- add `payment_due_soon`
- add `recurring_expense_due`
- enrich `WorkspaceSummary.finance_metrics`

Frontend:

- upgrade KPI strip from counts-only to counts + amount badges
- add filters:
  - `Incassi in arrivo`
  - `Spese ricorrenti`

## Backend Runtime Plan

### `payment_due_soon`

Source:

- `Rate`
- stato `PENDENTE` / `PARZIALE`
- `data_scadenza >= reference_date`
- `data_scadenza <= reference_date + 7 giorni`
- contratto non chiuso

Suppression:

- se esiste `payment_overdue` sullo stesso contratto, `payment_due_soon` non va mostrato

Buckets:

- `today` se `days_left == 0`
- `upcoming_3d` se `days_left <= 3`
- `upcoming_7d` se `days_left <= 7`

### `recurring_expense_due`

Source:

- stessa regola del dominio `GET /api/movements/pending-expenses`
- preferibilmente estratta in helper/service condiviso, non richiamata via HTTP dal workspace engine

Buckets:

- `today` se `data_prevista <= reference_date`
- `upcoming_3d` se `<= reference_date + 3 giorni`
- `upcoming_7d` se `<= reference_date + 7 giorni`
- `waiting` altrimenti

Severity:

- `high` se spesa prevista oggi o gia oltre data prevista
- `medium` se entro 3 giorni
- `low` se entro 7 giorni

## Query / Sorting Contract

Per il workspace finance la UI deve usare:

- `sort_by=priority` come default

Ordine target:

1. `payment_overdue`
2. `payment_due_soon`
3. `contract_renewal_due`
4. `recurring_expense_due`

Nota: questo ordinamento va inteso dentro il workspace finance, senza rompere la gerarchia generale di `today`.

## Actions and Auditability

Le azioni v1 restano solo deep-link:

- `Apri cassa`
- `Apri contratto`
- `Apri cliente`

Per `recurring_expense_due` v1:

- CTA primaria -> `Apri cassa`
- non esporre ancora una mutation workspace `Conferma spesa`

Motivo:

- la conferma di una spesa ricorrente crea movimenti ledger;
- questo richiede audit trail e invalidazioni gia gestite nell’area `movements`;
- spostare la mutation nel namespace workspace sarebbe prematuro in questa fase.

## Verification Plan

### Docs-only microstep

- `rg -n "UPG-2026-03-09-20|renewals_cash|recurring_expense_due|payment_due_soon" docs api frontend tests`
- review manuale di:
  - `docs/upgrades/specs/UPG-2026-03-09-20-renewals-cash-workspace-technical-spec-v1.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`

### Future implementation gates

- backend:
  - `ruff` su `workspace_engine.py`
  - test dedicati `workspace_renewals_cash`
  - verifica redazione `today` vs `full` in `renewals_cash`
- frontend:
  - lint pagina e componenti workspace finance
  - loading / empty / error espliciti
  - verifica che nessun importo finance appaia fuori dal workspace dedicato

## Risks

- Se il primo shell provasse a mostrare totali monetari presi da una pagina paginata, introdurrebbe subito KPI falsi.
- `renewals_cash` ha gia due famiglie forti; aggiungere subito `payment_due_soon` e `recurring_expense_due` senza un shell leggibile rischierebbe di replicare il rumore che abbiamo appena tolto da `Oggi`.
- Le spese ricorrenti toccano il ledger: le azioni write vanno tenute fuori dal namespace workspace finche il flusso non e deliberatamente progettato con audit trail esplicito.

## Next Smallest Step

Non implementare ancora i nuovi case kind.

Il prossimo microstep corretto e:

1. costruire la shell frontend `Rinnovi & Incassi` sopra il contratto gia esistente (`payment_overdue` + `contract_renewal_due`);
2. misurare il payload reale sul dataset DEV;
3. solo dopo aggiungere `payment_due_soon` e `recurring_expense_due`.
