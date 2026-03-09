# UPG-2026-03-09-03 - Workspace Payload Contract v1

## Metadata

- Upgrade ID: `UPG-2026-03-09-03`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Workspace API + Frontend Type Contract + Read-only Orchestration`
- Priority: `high`
- Target release: `codex_02`
- Status: `planned`

## Problem

La spec prodotto del workspace operativo e stata formalizzata in `UPG-2026-03-09-02`, ma manca ancora il contratto tecnico che permetta a backend e frontend di implementare `Oggi` senza interpretazioni divergenti.

Il rischio attuale e doppio:

1. costruire una UI `Oggi` sopra dati ancora frammentati tra `dashboard`, `agenda`, `todos`, `readiness`, `contratti`, `cassa` e `training methodology`;
2. introdurre un layer nuovo senza agganci chiari alle fonti gia esistenti, duplicando logica e drift tipologico.

Serve quindi una spec tecnica che definisca:

- famiglia di endpoint read-only del workspace;
- tipi condivisi backend/frontend;
- shape delle card/casi operativi;
- regole di deduplica e merge key;
- confini di visibilita dei dati finanziari;
- MVP realistico costruibile sulle sorgenti gia disponibili.

## Desired Outcome

Definire un contratto `Workspace v1` che permetta di implementare il primo shell reale di `Oggi` con comportamento deterministico e basso rischio:

- un endpoint home `today`;
- una lista casi paginata e filtrabile;
- un dettaglio caso read-only;
- riuso esplicito delle fonti dati esistenti;
- redazione dei dati finanziari in `Oggi` e piena visibilita solo in `Rinnovi & Incassi`;
- MVP limitato ai `case type` che hanno gia fonti concrete nel progetto.

## Scope

- In scope:
  - definizione famiglia endpoint `workspace`;
  - definizione tipi `OperationalCase`, `WorkspaceTodayResponse`, `WorkspaceCaseListResponse`, `WorkspaceCaseDetailResponse`;
  - enum e query params;
  - regole di merge key, bucket e severity;
  - policy di visibilita dati finance per workspace;
  - mapping tra case type MVP e fonti dati attuali;
  - ordine di implementazione backend/frontend.
- Out of scope:
  - implementazione API/router/schema reale;
  - introduzione di action endpoint write-capable;
  - cutover della route `/` nella UI;
  - supporto completo a tutti i 15 case type della spec prodotto;
  - ranking AI o automazioni non deterministiche.

## Impact Map

- Future files/modules expected:
  - `api/routers/workspace.py`
  - `api/schemas/workspace.py`
  - `api/services/workspace_engine.py`
  - `frontend/src/hooks/useWorkspace.ts`
  - `frontend/src/types/api.ts`
  - `frontend/src/app/(dashboard)/workspace/oggi/page.tsx`
  - `tests/test_workspace_today.py`
  - `tests/test_workspace_case_merge.py`
  - `docs/upgrades/specs/UPG-2026-03-09-03-workspace-payload-contract-v1.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layers: `api` + `frontend` + `tests` + `docs`
- Invariants:
  - overview dashboard corrente resta privacy-safe;
  - importi completi non appaiono nel workspace `today`;
  - ownership trainer invariata su tutte le sorgenti;
  - v1 workspace resta read-only come orchestration layer;
  - nessuna duplicazione logica non necessaria con `clinical-readiness/worklist`.

## Technical Principles Locked

- Il workspace v1 nasce come orchestration layer read-only, non come nuovo dominio write-first.
- La famiglia endpoint raccomandata e `GET /api/workspace/*`, non un'estensione indefinita di `/api/dashboard/*`.
- `today` e la home operativa aggregata; `cases` e la vista paginata multi-workspace; `cases/{id}` e il dettaglio.
- Tutti i casi espongono `reason`, `severity`, `bucket`, `merge_key`, `root_entity` e `suggested_actions`.
- Le action v1 sono deep-link verso flussi gia esistenti; nessuna mutation API workspace in questa fase.
- La finanza completa e restituita solo quando `workspace = renewals_cash`.

## Recommended Endpoint Family v1

### 1. `GET /api/workspace/today`

Home operativa read-only.

Restituisce:

- summary compatto;
- focus case dominante;
- agenda oraria del giorno;
- sezioni deduplicate per bucket;
- contatori `waiting/completed_today` sintetici.

### 2. `GET /api/workspace/cases`

Lista paginata e filtrabile dei casi.

Serve per:

- workspace dedicati (`onboarding`, `programmi`, `renewals_cash`);
- pagination e filtri server-side;
- futura sostituzione delle board top-N statiche.

### 3. `GET /api/workspace/cases/{case_id}`

Dettaglio read-only di un caso.

Restituisce:

- caso base;
- segnali aggregati;
- entita correlate;
- mini storico;
- eventuale contesto finance completo se permesso dal workspace chiamante.

## Why `/api/workspace/*` and not more `/api/dashboard/*`

Motivazione:

- `dashboard` oggi rappresenta overview neutra e privacy-safe;
- `workspace` rappresenta orchestration operativa cross-domain;
- tenere tutto sotto `dashboard` aumenterebbe coupling con una pagina che il prodotto vuole riposizionare come `Panoramica`;
- le fonti legacy restano riusabili, ma il consumer nuovo ha una semantica diversa.

## Type Contract v1

### Shared Enums

```ts
type WorkspaceId = "today" | "onboarding" | "programmi" | "renewals_cash";

type CaseSeverity = "critical" | "high" | "medium" | "low";

type CaseBucket = "now" | "today" | "upcoming_3d" | "upcoming_7d" | "waiting";

type AgendaStatus = "past" | "current" | "upcoming";

type RootEntityType =
  | "client"
  | "contract"
  | "plan"
  | "event"
  | "todo"
  | "expense"
  | "portal_share"
  | "system";

type CaseKind =
  | "onboarding_readiness"
  | "session_imminent"
  | "followup_post_session"
  | "todo_manual"
  | "plan_activation"
  | "plan_review_due"
  | "plan_compliance_risk"
  | "plan_cycle_closing"
  | "payment_overdue"
  | "payment_due_soon"
  | "contract_renewal_due"
  | "recurring_expense_due"
  | "client_reactivation"
  | "ops_anomaly"
  | "portal_questionnaire_pending";
```

### `WorkspaceRootEntity`

```ts
interface WorkspaceRootEntity {
  type: RootEntityType;
  id: number | string;
  label: string;
  href: string | null;
}
```

### `WorkspaceAction`

V1 solo read-only / deep-link oriented.

```ts
type WorkspaceActionKind =
  | "navigate"
  | "deep_link"
  | "snooze_future"
  | "mark_managed_future"
  | "convert_todo_future";

interface WorkspaceAction {
  id: string;
  label: string;
  kind: WorkspaceActionKind;
  href: string | null;
  enabled: boolean;
  availability_note: string | null;
  is_primary: boolean;
}
```

Regola: in v1 i campi `*_future` possono essere esposti come disabled/coming soon, ma non devono implicare una mutation API gia attiva.

### `WorkspaceSignal`

```ts
interface WorkspaceSignal {
  signal_code: string;
  source: string;
  label: string;
  severity: CaseSeverity;
  due_date: string | null;
  reason: string;
}
```

### `WorkspaceFinanceContext`

```ts
type FinanceVisibility = "hidden" | "redacted" | "full";

interface WorkspaceFinanceContext {
  visibility: FinanceVisibility;
  due_date: string | null;
  overdue_count: number | null;
  currency: "EUR" | null;
  total_due_amount: number | null;
  total_residual_amount: number | null;
  contract_id: number | null;
}
```

Policy:

- `today`, `onboarding`, `programmi` -> `visibility = "hidden"` o `redacted"`
- `renewals_cash` -> `visibility = "full"`

### `OperationalCase`

```ts
interface OperationalCase {
  case_id: string;
  merge_key: string;
  workspace: WorkspaceId;
  case_kind: CaseKind;
  title: string;
  reason: string;
  severity: CaseSeverity;
  bucket: CaseBucket;
  due_date: string | null;
  days_to_due: number | null;
  root_entity: WorkspaceRootEntity;
  secondary_entity: WorkspaceRootEntity | null;
  signal_count: number;
  preview_signals: WorkspaceSignal[];
  finance_context: WorkspaceFinanceContext | null;
  suggested_actions: WorkspaceAction[];
  source_refs: string[];
}
```

Rules:

- `preview_signals.length <= 3`
- `signal_count` puo essere > `preview_signals.length`
- `case_id` e `merge_key` devono essere stabili sullo stesso root case
- `source_refs` elenca le sorgenti principali, non i record raw completi

### `WorkspaceAgendaItem`

```ts
interface WorkspaceAgendaItem {
  event_id: number;
  client_id: number | null;
  client_label: string | null;
  title: string;
  category: string;
  status: AgendaStatus;
  starts_at: string;
  ends_at: string | null;
  href: string;
  has_case_warning: boolean;
}
```

### `WorkspaceSummary`

```ts
interface WorkspaceSummary {
  workspace: WorkspaceId;
  generated_at: string;
  critical_count: number;
  now_count: number;
  today_count: number;
  upcoming_7d_count: number;
  waiting_count: number;
}
```

### `WorkspaceTodayResponse`

```ts
interface WorkspaceTodaySection {
  bucket: CaseBucket;
  label: string;
  total: number;
  items: OperationalCase[];
}

interface WorkspaceTodayResponse {
  summary: WorkspaceSummary;
  focus_case: OperationalCase | null;
  agenda: {
    date: string;
    current_time: string;
    next_event_id: number | null;
    items: WorkspaceAgendaItem[];
  };
  sections: WorkspaceTodaySection[];
  completed_today_count: number;
  snoozed_count: number;
}
```

### `WorkspaceCaseListResponse`

```ts
interface WorkspaceCaseListResponse {
  summary: WorkspaceSummary;
  items: OperationalCase[];
  total: number;
  page: number;
  page_size: number;
  filters_applied: {
    workspace: WorkspaceId;
    bucket: CaseBucket | null;
    severity: CaseSeverity | null;
    case_kind: CaseKind | null;
    search: string | null;
  };
}
```

### `WorkspaceCaseDetailResponse`

```ts
interface WorkspaceCaseDetailResponse {
  case: OperationalCase;
  signals: WorkspaceSignal[];
  related_entities: WorkspaceRootEntity[];
  activity_preview: Array<{
    at: string;
    label: string;
    href: string | null;
  }>;
}
```

## Stable IDs and Merge Keys

Regola v1:

- `case_id` e `merge_key` possono coincidere.
- formato raccomandato:

```text
case:{case_kind}:{root_entity_type}:{root_entity_id}
```

Esempi:

- `case:onboarding_readiness:client:184`
- `case:payment_overdue:contract:72`
- `case:session_imminent:event:901`

Vantaggi:

- determinismo;
- debugging facile;
- nessun bisogno di id separato nel MVP;
- compatibile con `GET /cases/{case_id}` via URL-encoding standard.

## Query Contract for `GET /api/workspace/cases`

Query params raccomandati:

```text
workspace=today|onboarding|programmi|renewals_cash
page=1
page_size=25
bucket=now|today|upcoming_3d|upcoming_7d|waiting
severity=critical|high|medium|low
case_kind=...
search=...
sort_by=priority|due_date
expand=none|signals|finance
```

Default raccomandati:

- `workspace=today`
- `page=1`
- `page_size=25`
- `sort_by=priority`
- `expand=none`

## Finance Visibility Rules

### `today`

- ammessi:
  - presenza del problema;
  - stato `overdue` o `renewal due`;
  - date di scadenza;
  - contatori sintetici.
- non ammessi:
  - `total_due_amount`
  - `total_residual_amount`
  - saldo/margine/metriche cassa

### `renewals_cash`

- ammessi:
  - importi completi;
  - date complete;
  - aging e residui;
  - contratto associato.

### `onboarding` / `programmi`

- finance context assente o redatto;
- nessuna ragione per mostrare importi in queste viste.

## Case Registry v1

### MVP Enabled Now

Questi casi hanno gia sorgenti dati concrete nel progetto attuale.

| Code | `case_kind` | Fonte primaria | `merge_key` | Workspace default | Note |
|---|---|---|---|---|---|
| `DAY-01` | `session_imminent` | `/events` tramite `useEvents()` | `case:session_imminent:event:{event_id}` | `today` | usa agenda giornaliera gia presente nella dashboard |
| `ONB-01` | `onboarding_readiness` | `/dashboard/clinical-readiness/worklist` | `case:onboarding_readiness:client:{client_id}` | `onboarding` | deriva dalla readiness worklist esistente |
| `TODO-01` | `todo_manual` | `/todos` | `case:todo_manual:todo:{todo_id}` | `today` | nessun merge extra nel MVP |
| `FIN-01` | `payment_overdue` | `/dashboard/overdue-rates` | `case:payment_overdue:contract:{contract_id}` | `renewals_cash` | aggrega piu rate scadute dello stesso contratto |
| `FIN-03` | `contract_renewal_due` | `/dashboard/expiring-contracts` | `case:contract_renewal_due:contract:{contract_id}` | `renewals_cash` | rinnovo e crediti residui bassi |
| `REL-01` | `client_reactivation` | `/dashboard/inactive-clients` | `case:client_reactivation:client:{client_id}` | `today` | opportunita, non deve superare casi critici |

### Deferred Case Types

Questi restano nel catalogo prodotto ma non entrano nel primo payload implementation pass:

- `DAY-02` `followup_post_session`
- `PRG-01` `plan_activation`
- `PRG-02` `plan_review_due`
- `PRG-03` `plan_compliance_risk`
- `PRG-04` `plan_cycle_closing`
- `FIN-02` `payment_due_soon`
- `FIN-04` `recurring_expense_due`
- `OPS-01` `ops_anomaly`
- `PORT-01` `portal_questionnaire_pending`

Motivo: richiedono o una nuova sorgente aggregata o un adattamento ulteriore di `training-methodology`, `expenses`, `public portal` e workflow follow-up.

## Merge Rules v1

- `DAY-01`: no merge oltre l'evento stesso.
- `ONB-01`: un solo caso per cliente, aggregando missing step readiness.
- `TODO-01`: nessun merge nel MVP.
- `FIN-01`: tutte le rate overdue dello stesso contratto collassano in un solo caso.
- `FIN-03`: un solo caso rinnovo per contratto.
- `REL-01`: un solo caso per cliente inattivo.

Regola generale:

- nel MVP non esiste merge cross-case su domini diversi;
- il merge opera solo dentro lo stesso `case_kind` e sulla stessa root entity;
- il pannello dettaglio mostra i segnali raw che hanno generato il caso.

## Bucket Rules v1

Mapping raccomandato:

- `now`
  - eventi in corso o entro 2 ore;
  - casi `critical` con azione immediata.
- `today`
  - scadenza oggi;
  - eventi restanti della giornata.
- `upcoming_3d`
  - scadenza entro 3 giorni.
- `upcoming_7d`
  - scadenza tra 4 e 7 giorni.
- `waiting`
  - elementi snoozed/paused in una fase futura del progetto.

Nota: `waiting` puo essere sempre vuoto nel MVP read-only.

## Priority Rules v1

Ordinamento raccomandato:

1. `session_imminent`
2. `payment_overdue`
3. `onboarding_readiness`
4. `contract_renewal_due`
5. `client_reactivation`
6. `todo_manual`

Tie-break raccomandati:

1. severity
2. bucket
3. due_date piu vicina
4. root entity label alfabetica

## Source Reuse Plan

Il workspace v1 non deve ricopiare logica gia presente se non per orchestrarla.

### Fonti da riusare direttamente

- `GET /api/events`
- `GET /api/todos`
- `GET /api/dashboard/clinical-readiness/worklist`
- `GET /api/dashboard/overdue-rates`
- `GET /api/dashboard/expiring-contracts`
- `GET /api/dashboard/inactive-clients`

### Fonti da non inglobare ancora nel MVP

- `training-methodology/worklist`
- expenses ricorrenti non ancora esposte in dashboard
- segnali portale cliente self-service

## Backend Delivery Order

### M1 - Schemas and Engine

- creare `api/schemas/workspace.py`
- creare `api/services/workspace_engine.py`
- adapter functions per le 6 fonti MVP

### M2 - Router

- creare `api/routers/workspace.py`
- introdurre:
  - `GET /api/workspace/today`
  - `GET /api/workspace/cases`
  - `GET /api/workspace/cases/{case_id}`

### M3 - Frontend Type Sync

- aggiungere tipi in `frontend/src/types/api.ts`
- creare `frontend/src/hooks/useWorkspace.ts`

### M4 - Frontend Shell

- nuova pagina dedicata `workspace/oggi`
- nessun cutover immediato della home `/`

## Acceptance Criteria

- Functional:
  - esiste una famiglia endpoint `workspace` definita in modo completo;
  - il payload `today` e distinguibile dalla lista `cases`;
  - il MVP copre solo case type con sorgenti dati gia reali.
- UX:
  - il contratto consente di separare agenda oraria e queue operativa;
  - la visibilita finance e coerente con le regole di prodotto;
  - ogni caso espone reason, bucket e CTA leggibili.
- Technical:
  - nessuna mutation API richiesta nel v1;
  - type contract backend/frontend e definito;
  - le merge key sono stabili e deterministiche.

## Test Plan

- Docs/manual:
  - review manuale coerenza con `UPG-2026-03-09-02`
  - review manuale coerenza con `UPG-2026-03-06-34`
  - review manuale allineamento a `frontend/src/hooks/useDashboard.ts`
  - review manuale allineamento a `frontend/src/types/api.ts`
- Future API tests:
  - merge deterministico `FIN-01`
  - redazione finance in `today`
  - ownership invariata sulle sorgenti aggregate
  - ordering deterministico dei case per `today`

## Risks and Mitigation

- Risk 1: il workspace diventa un duplicato mascherato della dashboard.
  - Mitigation 1: nuova famiglia `/workspace` con semantica chiara, overview dashboard preservata.
- Risk 2: il MVP prova a coprire troppi case type insieme.
  - Mitigation 2: limitare il primo pass a 6 case con sorgenti gia esistenti.
- Risk 3: leakage finanziario nella home `today`.
  - Mitigation 3: `finance_context.visibility` e policy di omissione importi.
- Risk 4: drift tra worklist readiness esistente e nuovo caso onboarding.
  - Mitigation 4: `ONB-01` deve derivare dalla stessa fonte `clinical-readiness/worklist`, non da logica duplicata.

## Rollback Plan

- Se il router `workspace` risultasse prematuro:
  - mantenere questa spec come target;
  - implementare prima un adapter interno senza endpoint pubblico;
  - usare feature flag per il frontend shell;
  - non toccare la home `/` finche il payload non e stabile.

## Notes

- Nessun nuovo ADR richiesto in questo step: la decisione architetturale di alto livello e gia coperta da `ADR-2026-03-09-operational-workspace-case-engine.md`.
- Documenti correlati:
  - `docs/upgrades/specs/UPG-2026-03-09-02-operational-workspace-home-v1.md`
  - `docs/upgrades/specs/UPG-2026-03-06-34-myportal-v2-worklist-architecture.md`
  - `docs/upgrades/specs/UPG-2026-03-06-30-dashboard-clinical-readiness-queue.md`
