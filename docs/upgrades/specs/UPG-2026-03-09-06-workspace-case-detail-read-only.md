# UPG-2026-03-09-06 - Workspace Case Detail Read-only

## Metadata

- Upgrade ID: `UPG-2026-03-09-06`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Workspace API + Detail Contract + Type Sync`
- Priority: `high`
- Target release: `codex_02`

## Problem

Dopo `UPG-2026-03-09-05`, il workspace dispone di:

- home aggregata `GET /api/workspace/today`
- lista casi paginata `GET /api/workspace/cases`

Manca ancora il terzo asse del contratto `Workspace v1`: il dettaglio read-only del singolo caso.

Senza questo endpoint:

- il frontend non puo costruire un pannello destro o sheet di dettaglio coerente;
- i segnali completi restano compressi in `preview_signals`;
- la policy finance per contesto workspace non e verificabile anche sul dettaglio;
- il trainer non ha ancora una vista unica e spiegabile del "perche lo sto vedendo".

## Desired Outcome

Introdurre `GET /api/workspace/cases/{case_id}` come payload detail read-only:

- trainer-scoped;
- dipendente dal `workspace` richiesto per la visibilita finance;
- basato sullo stesso snapshot casi di `today` e `cases`;
- con `signals`, `related_entities` e `activity_preview` utili al pannello dettaglio;
- senza introdurre mutation o side effect.

## Scope

- In scope:
  - nuovo schema `WorkspaceCaseDetailResponse`;
  - nuovo endpoint `GET /api/workspace/cases/{case_id}`;
  - builder detail read-only nel `workspace_engine`;
  - frontend type sync e hook `useWorkspaceCaseDetail()`;
  - test backend su detail payload, finance visibility e isolamento.
- Out of scope:
  - mutation workspace (`snooze`, `mark managed`, `convert todo`);
  - UI pannello dettaglio;
  - supporto detail profondo per i case type `Programmi` non ancora alimentati;
  - attivita audit-grade o timeline completa per ogni dominio.

## Impact Map

- Files/modules touched:
  - `api/schemas/workspace.py`
  - `api/services/workspace_engine.py`
  - `api/routers/workspace.py`
  - `tests/test_workspace_today.py`
  - `frontend/src/types/api.ts`
  - `frontend/src/hooks/useWorkspace.ts`
  - `docs/upgrades/specs/UPG-2026-03-09-06-workspace-case-detail-read-only.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `api` | `frontend` | `tests`
- Invarianti da preservare:
  - ownership trainer sempre derivata da sorgenti reali, mai dal `case_id` da solo;
  - nessuna visibilita importi completi in `workspace=today`;
  - nessuna duplicazione dello snapshot tra `today`, `cases` e `case detail`;
  - nessuna mutation introdotta nel dominio workspace.

## What Changed

- aggiunto `WorkspaceCaseDetailResponse` con:
  - `case`
  - `signals`
  - `related_entities`
  - `activity_preview`
- introdotto `build_workspace_case_detail()` nel `workspace_engine`
  - riusa `collect_workspace_snapshot()`
  - seleziona il caso solo se visibile nel `workspace` richiesto
  - applica la stessa policy finance di `today`/`cases`
- aggiunti builder detail specifici per i case type MVP attivi:
  - `session_imminent`
  - `onboarding_readiness`
  - `todo_manual`
  - `payment_overdue`
  - `contract_renewal_due`
  - `client_reactivation`
- nuovo endpoint `GET /api/workspace/cases/{case_id}`
  - `404` se il caso non esiste, non e visibile in quel workspace, o non appartiene al trainer
- frontend:
  - nuovo tipo `WorkspaceCaseDetailResponse`
  - nuovo hook `useWorkspaceCaseDetail()`

## Acceptance Criteria

- Funzionale:
  - il case detail restituisce payload coerente con `case_id` stabile;
  - `workspace=today` redige gli importi finance anche sul dettaglio;
  - `workspace=renewals_cash` espone gli importi completi sullo stesso caso;
  - il dettaglio onboarding restituisce tutti i segnali operativi rilevanti, non solo i preview.
- Sicurezza:
  - trainer A non puo leggere il detail di un caso appartenente al trainer B;
  - un case non visibile in un workspace diverso ritorna `404`.
- Tecnico:
  - nessun nuovo motore parallelo al case snapshot;
  - type sync frontend allineato;
  - test backend dedicati presenti.

## Test Plan

- Backend static:
  - `venv\Scripts\ruff.exe check api\routers\workspace.py api\schemas\workspace.py api\services\workspace_engine.py tests\test_workspace_today.py`
- Backend runtime:
  - `venv\Scripts\python.exe -m pytest -q tests\test_workspace_today.py -p no:cacheprovider`
- Frontend:
  - `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/types/api.ts" "src/hooks/useWorkspace.ts"`

## Verification Outcome

- `ruff` sui file backend toccati: `PASS`
- lint frontend su `src/types/api.ts` e `src/hooks/useWorkspace.ts`: `PASS`
- `pytest` backend runtime: `BLOCKED` da ambiente locale Python/venv che continua a risolvere verso il launcher Microsoft Store

## Risks and Mitigation

- Rischio 1: detail builder domain-specific troppo accoppiato al service.
  - Mitigazione 1: builder dispatch limitato ai 6 case type MVP, con fallback deterministic `_default_case_detail()`.
- Rischio 2: finance leak nei segnali o nell'activity preview.
  - Mitigazione 2: importi lasciati solo in `finance_context`; segnali e timeline detail non espongono amount fields.
- Rischio 3: `Programmi` resta ancora privo di detail reale.
  - Mitigazione 3: il workspace `programmi` rimane esplicitamente fuori dal MVP runtime finche non vengono agganciate sorgenti dedicate.

## Rollback Plan

- revert del solo layer detail:
  - `WorkspaceCaseDetailResponse`
  - `build_workspace_case_detail()` e builder detail specifici
  - endpoint `GET /api/workspace/cases/{case_id}`
  - `useWorkspaceCaseDetail()` e type correlati
- `today` e `cases` restano operativi anche senza questo microstep.

## Notes

- Questo step chiude il contratto read-only minimo del workspace:
  - home `today`
  - lista `cases`
  - dettaglio `cases/{case_id}`
- Prossimo step consigliato: shell UI read-only del workspace `Oggi` con focus case, queue bucket e pannello dettaglio realmente consumato dal frontend.
