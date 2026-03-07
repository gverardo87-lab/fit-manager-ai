# UPG-2026-03-07-40 - SMART Plan Package Runtime Scaffold

## Metadata

- Upgrade ID: `UPG-2026-03-07-40`
- Date: 2026-03-07
- Owner: Codex
- Area: Training Science Engine + Smart Programming
- Priority: high
- Target release: `codex_02`

## Problem

Il filone SMART ha ancora un'architettura ibrida:

- il backend espone solo endpoint computazionali puri (`/plan`, `/analyze`, `/mesocycle`);
- il builder continua a dipendere da un percorso frontend-local per generazione e ranking;
- non esiste ancora un envelope backend-first che unisca profilo cliente reale, canonico scientifico, ranking deterministico e draft save-compatible.

Prima del cutover UI serve uno scaffold architetturale additivo che chiuda il contratto API e il runtime layer senza rompere il builder attuale.

## Desired Outcome

Introdurre il primo `plan-package` SMART come contratto backend/frontend additivo, con:

- schema dedicato separato dal core scientifico puro;
- runtime orchestration DB-aware separata da `build_plan()` e dagli endpoint puri;
- endpoint `POST /training-science/plan-package`;
- mirror TypeScript e hook frontend additivo;
- nessun cambio ancora al flusso `TemplateSelector`.

## Scope

- In scope:
  - nuovo schema transport `api/schemas/training_science.py`;
  - nuovo runtime layer `api/services/training_science/runtime/`;
  - endpoint additivo `/training-science/plan-package`;
  - type sync frontend in `frontend/src/types/api.ts`;
  - nuovo hook `useGeneratePlanPackage()`;
  - sync docs upgrade/workboard.
- Out of scope:
  - migrazione del builder a `plan-package`;
  - persistenza DB del piano scientifico canonico;
  - unificazione di `SmartAnalysisPanel` / `MuscleMapPanel`;
  - modellazione scientifica dei blocchi.

## Impact Map

- Files/modules touched:
  - `api/routers/training_science.py`
  - `api/schemas/training_science.py`
  - `api/services/training_science/runtime/__init__.py`
  - `api/services/training_science/runtime/mappings.py`
  - `api/services/training_science/runtime/readiness.py`
  - `api/services/training_science/runtime/exercise_catalog.py`
  - `api/services/training_science/runtime/exercise_ranker.py`
  - `api/services/training_science/runtime/profile_resolver.py`
  - `api/services/training_science/runtime/plan_package_service.py`
  - `frontend/src/types/api.ts`
  - `frontend/src/hooks/useTrainingScience.ts`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `api`, `frontend`, `docs`
- Invarianti da preservare:
  - `build_plan()` e gli endpoint storici restano puri e zero-DB;
  - ownership trainer/cliente verificata server-side;
  - ranking deterministico, zero random;
  - nessuna rottura del builder corrente;
  - nessuna duplicazione silenziosa del contratto API tra backend e frontend.

## Acceptance Criteria

- Funzionale:
  - `POST /training-science/plan-package` esiste ed e' additivo;
  - il backend restituisce `scientific_profile`, `canonical_plan`, `rankings`, `workout_projection`, `warnings`, `engine`;
  - il frontend dispone del mirror TS e del hook `useGeneratePlanPackage()`.
- Architetturale:
  - il runtime layer DB-aware e' separato dal core scientifico puro;
  - readiness/anamnesi shared logic non vive nel router dashboard;
  - catalog loader e ranker non bypassano la ownership multi-tenant.
- Tecnico:
  - lint backend e frontend verdi sui file toccati.

## Test Plan

- Backend lint:
  - `venv\\Scripts\\ruff.exe check api/routers/training_science.py api/schemas/training_science.py api/services/training_science/runtime`
- Frontend lint:
  - `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/hooks/useTrainingScience.ts" "src/types/api.ts"`
- Manual checks:
  - review del boundary tra core puro e runtime layer;
  - review del filtro multi-tenant nel catalog loader;
  - review del mapping esplicito builder -> scientific -> workout.

## Risks and Mitigation

- Rischio 1:
  - il ranking minimo v1 usa alias pattern conservativi, non ancora una semantica completa pattern-to-exercise.
- Mitigazione 1:
  - tenere il ranker puro, minimale e additivo; raffinare in microstep successivo con dataset e test dedicati.

- Rischio 2:
  - `build_safety_map()` reesegue internamente query cliente/safety e introduce duplicazione leggera nel resolver.
- Mitigazione 2:
  - accettare il costo nel primo scaffold; ottimizzare solo dopo il cutover API stabile.

- Rischio 3:
  - il venv Python locale e' corrotto e limita gli smoke test runtime/import.
- Mitigazione 3:
  - usare `ruff.exe` e `npm.cmd` come verifiche reali minime nel microstep; pianificare fix del venv o un interpreter stabile prima dei test piu' profondi.

## Rollback Plan

- Rimuovere il nuovo endpoint `/training-science/plan-package`.
- Eliminare `api/schemas/training_science.py`.
- Eliminare il runtime layer `api/services/training_science/runtime/`.
- Rimuovere i tipi `TSPlanPackage*` e il hook additivo dal frontend.

## Notes

- Questo microstep chiude solo lo scaffold contrattuale e runtime.
- Il prossimo microstep naturale e' il cutover di `TemplateSelector` al nuovo hook backend-first.
