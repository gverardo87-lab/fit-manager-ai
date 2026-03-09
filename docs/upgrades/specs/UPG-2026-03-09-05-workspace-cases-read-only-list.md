# UPG-2026-03-09-05 - Workspace Cases Read-only List

## Metadata

- Upgrade ID: `UPG-2026-03-09-05`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Workspace API + Server-side Filtering + Type Sync`
- Priority: `high`
- Target release: `codex_02`

## Problem

Dopo `UPG-2026-03-09-04`, il workspace dispone solo della home aggregata `GET /api/workspace/today`.

Questo non basta ancora per i workspace nativi:

- `Onboarding`
- `Programmi`
- `Rinnovi & Incassi`
- una futura vista `Oggi` completa e filtrabile

Manca infatti una lista casi paginata e filtrabile lato server. Senza questo endpoint il frontend sarebbe costretto a:

- derivare liste dalla sola home `today`;
- duplicare filtri lato client;
- perdere la separazione tra workspace nativi e promozione in `Oggi`.

## Desired Outcome

Introdurre `GET /api/workspace/cases` come lista read-only:

- paginata;
- filtrabile per `workspace`, `bucket`, `severity`, `case_kind`, `search`;
- con ordinamento deterministico `priority | due_date`;
- costruita sullo stesso snapshot casi usato da `today`;
- con policy finance coerente: `redacted` in `today`, `full` in `renewals_cash`.

## Scope

- In scope:
  - refactor minimo del `workspace_engine` per esporre uno snapshot casi condiviso;
  - nuovo schema `WorkspaceCaseListResponse`;
  - nuovo endpoint `GET /api/workspace/cases`;
  - hook frontend `useWorkspaceCases()`;
  - test backend su paginazione, filtri e finance visibility.
- Out of scope:
  - `GET /api/workspace/cases/{case_id}`;
  - nuove mutation workspace;
  - UI workspace list page;
  - dettagli approfonditi per `Programmi` ancora non alimentati da sorgenti dedicate.

## Impact Map

- Files/modules touched:
  - `api/services/workspace_engine.py`
  - `api/schemas/workspace.py`
  - `api/routers/workspace.py`
  - `tests/test_workspace_today.py`
  - `frontend/src/types/api.ts`
  - `frontend/src/hooks/useWorkspace.ts`
  - `docs/upgrades/specs/UPG-2026-03-09-05-workspace-cases-read-only-list.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `api` | `frontend` | `tests`
- Invarianti da preservare:
  - nessuna duplicazione di motore tra `today` e `cases`;
  - redazione finance in `today`;
  - ownership trainer invariata;
  - nessuna nuova mutation introdotta.

## What Changed

- `workspace_engine` ora espone uno snapshot condiviso di casi (`collect_workspace_snapshot`) riusato da:
  - `build_workspace_today()`
  - `build_workspace_case_list()`
- introdotti:
  - filtro per workspace logico (`today` come vista promossa, altri come workspace nativi);
  - filtri server-side per `bucket`, `severity`, `case_kind`, `search`;
  - ordinamento `priority` e `due_date`;
  - policy finance differenziata:
    - `today` -> `redacted`
    - `renewals_cash` -> `full`
- frontend:
  - nuovi tipi `WorkspaceCaseListFilters`, `WorkspaceCaseListResponse`
  - nuovo hook `useWorkspaceCases()`

## Acceptance Criteria

- Funzionale:
  - `GET /api/workspace/cases` restituisce lista casi paginata;
  - il filtro `workspace=onboarding` restituisce solo casi `onboarding_readiness`;
  - il filtro `workspace=renewals_cash` espone casi finance del workspace nativo;
  - `today` continua a mostrare i casi promossi cross-domain.
- UX:
  - il frontend puo consumare `cases` senza filtraggio client-side obbligatorio;
  - la redazione/importi cambia in base al workspace richiesto.
- Tecnico:
  - `today` e `cases` usano lo stesso snapshot casi;
  - type sync frontend aggiornato;
  - test dedicato del nuovo endpoint presente.

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

- Rischio 1: `today` e `cases` divergono nel tempo.
  - Mitigazione 1: snapshot unico riusato da entrambi i builder.
- Rischio 2: redazione finance incoerente tra viste.
  - Mitigazione 2: `_apply_finance_visibility()` centralizzato nel service.
- Rischio 3: `workspace=programmi` resta vuoto nel MVP attuale.
  - Mitigazione 3: comportamento esplicito e accettato finche non viene agganciata una sorgente programmi dedicata.

## Rollback Plan

- revert del solo layer lista:
  - `build_workspace_case_list()` e helpers relativi;
  - endpoint `GET /api/workspace/cases`;
  - `useWorkspaceCases()` e relativi type;
- `GET /api/workspace/today` resta operativo anche senza questo microstep.

## Notes

- Questo step chiude il primo asse API del workspace:
  - home aggregata `today`
  - lista casi `cases`
- Prossimo step consigliato: `GET /api/workspace/cases/{case_id}` per pannello dettaglio e segnali completi.
