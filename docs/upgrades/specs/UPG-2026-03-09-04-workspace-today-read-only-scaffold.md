# UPG-2026-03-09-04 - Workspace Today Read-only Scaffold

## Metadata

- Upgrade ID: `UPG-2026-03-09-04`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Workspace API + Type Sync + Read-only Orchestration`
- Priority: `high`
- Target release: `codex_02`

## Problem

Le spec `UPG-2026-03-09-02` e `UPG-2026-03-09-03` hanno definito direzione prodotto e contratto tecnico del workspace operativo, ma mancava ancora il primo scaffold runtime reale.

Senza questo step il progetto restava in uno stato ambiguo:

- nessun endpoint `/api/workspace/*` ancora disponibile;
- nessun payload reale aggregato per la futura home `Oggi`;
- type contract frontend assente;
- rischio di iniziare la UI senza verificare l'orchestration backend.

## Desired Outcome

Introdurre il primo microstep implementativo del workspace:

- inaugurare la famiglia `/api/workspace/*` con `GET /api/workspace/today`;
- costruire un orchestration layer read-only sopra fonti gia esistenti;
- estrarre la readiness condivisa fuori dal router dashboard;
- allineare `frontend/src/types/api.ts` e creare un hook minimo `useWorkspaceToday()`;
- coprire il nuovo percorso con test dedicato e verifiche statiche.

## Scope

- In scope:
  - `api/services/clinical_readiness.py` condiviso tra dashboard e workspace;
  - `api/schemas/workspace.py`;
  - `api/services/workspace_engine.py`;
  - `api/routers/workspace.py` con `GET /api/workspace/today`;
  - registrazione router in `api/main.py`;
  - type sync frontend per payload `WorkspaceTodayResponse`;
  - nuovo hook `frontend/src/hooks/useWorkspace.ts`;
  - test backend `tests/test_workspace_today.py`.
- Out of scope:
  - `GET /api/workspace/cases`;
  - `GET /api/workspace/cases/{case_id}`;
  - mutation workspace (`snooze`, `mark managed`, `convert to todo`);
  - nuova UI `Oggi`;
  - cutover della home `/`.

## Impact Map

- Files/modules touched:
  - `api/services/clinical_readiness.py`
  - `api/services/workspace_engine.py`
  - `api/schemas/workspace.py`
  - `api/routers/workspace.py`
  - `api/routers/dashboard.py`
  - `api/main.py`
  - `tests/test_workspace_today.py`
  - `frontend/src/types/api.ts`
  - `frontend/src/hooks/useWorkspace.ts`
  - `docs/upgrades/specs/UPG-2026-03-09-04-workspace-today-read-only-scaffold.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `api` | `frontend` | `tests`
- Invarianti da preservare:
  - multi-tenant safety su tutte le sorgenti aggregate;
  - nessuna mutation nuova dal workspace;
  - finanza completa non esposta in `today`;
  - dashboard readiness legacy non regressiva.

## Acceptance Criteria

- Funzionale:
  - `GET /api/workspace/today` restituisce summary, focus case, agenda e sections;
  - il payload aggrega almeno `session_imminent`, `onboarding_readiness`, `todo_manual`, `payment_overdue`, `contract_renewal_due`, `client_reactivation`;
  - `payment_overdue` aggrega piu rate dello stesso contratto in un solo case.
- UX:
  - il payload distingue agenda oraria e queue operativa;
  - `today` redige il contesto finance (`visibility = redacted`);
  - ogni case espone `reason`, `bucket`, `suggested_actions`.
- Tecnico:
  - readiness condivisa estratta in service;
  - type sync frontend aggiornata;
  - hook `useWorkspaceToday()` disponibile;
  - test dedicato del nuovo endpoint presente.

## Test Plan

- Backend static:
  - `venv\Scripts\ruff.exe check api\routers\dashboard.py api\routers\workspace.py api\schemas\workspace.py api\services\clinical_readiness.py api\services\workspace_engine.py tests\test_workspace_today.py`
- Backend runtime:
  - `venv\Scripts\python.exe -m pytest -q tests\test_workspace_today.py tests\test_dashboard_clinical_readiness.py -p no:cacheprovider`
- Frontend:
  - `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/types/api.ts" "src/hooks/useWorkspace.ts"`

## Verification Outcome

- `ruff` sui file backend nuovi/modificati: `PASS`
- lint frontend su `src/types/api.ts` e `src/hooks/useWorkspace.ts`: `PASS`
- `pytest` backend mirato: `BLOCKED` da ambiente locale Python/venv rotto (`venv` risolve verso il launcher Microsoft Store invece che a un interprete reale)

## Risks and Mitigation

- Rischio 1: divergenza futura tra sorgenti dashboard e workspace su overdue/renewals/reactivation.
  - Mitigazione 1: readiness e stata gia estratta in service condiviso; prossima rifinitura consigliata e spostare anche gli adapter finance/inactive in un modulo condiviso.
- Rischio 2: `today` usa ancora href transizionali (`/`, `/cassa`, `/agenda`) prima del cutover UI definitivo.
  - Mitigazione 2: considerare questi link come deep-link temporanei validi nel CRM attuale.
- Rischio 3: contatori `snoozed` non ancora supportati dal dominio.
  - Mitigazione 3: esposto `0` in modo esplicito finche non esiste uno stato caso persistente.

## Rollback Plan

- Rimuovere il router `workspace` da `api/main.py`;
- revert dei file:
  - `api/services/clinical_readiness.py`
  - `api/services/workspace_engine.py`
  - `api/schemas/workspace.py`
  - `api/routers/workspace.py`
  - `tests/test_workspace_today.py`
  - `frontend/src/hooks/useWorkspace.ts`
  - blocco types workspace in `frontend/src/types/api.ts`

## Notes

- Questo microstep e volutamente backend-first e read-only.
- Prossimo step consigliato:
  - `GET /api/workspace/cases`
  - `GET /api/workspace/cases/{case_id}`
  - eventuale refactor delle sorgenti finance/inactive in service condivisi
