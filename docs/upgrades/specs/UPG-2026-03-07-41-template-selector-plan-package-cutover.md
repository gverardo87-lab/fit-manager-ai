# UPG-2026-03-07-41 - TemplateSelector Plan Package Cutover

## Metadata

- Upgrade ID: `UPG-2026-03-07-41`
- Date: 2026-03-07
- Owner: Codex
- Area: Smart Programming + Workout Builder
- Priority: high
- Target release: `codex_02`

## Problem

Dopo lo scaffold del `plan-package`, il builder SMART continuava a generare
localmente la scheda in `TemplateSelector.tsx` tramite `generateSmartPlan()` e
`fillSmartPlan()`.

Questo manteneva aperto il dual-engine:

- backend per il nuovo contratto scientifico;
- frontend per la generazione reale usata dall'utente.

## Desired Outcome

Fare il primo cutover reale del builder SMART:

- `TemplateSelector` usa solo `useGeneratePlanPackage()`;
- il backend costruisce canonico + ranking + draft;
- il frontend salva il `workout_projection.draft` senza piu' generare in locale;
- template statici e scheda vuota restano invariati.

## Scope

- In scope:
  - refactor di `frontend/src/components/workouts/TemplateSelector.tsx`;
  - wiring del nuovo hook `useGeneratePlanPackage()`;
  - aggiornamento copy/stati loading della card Smart;
  - sync docs/workboard.
- Out of scope:
  - cutover di `SmartAnalysisPanel`;
  - cutover di `MuscleMapPanel`;
  - rimozione dei file legacy `smart-programming/*`;
  - rendering dei warning del `plan-package` nella UI.

## Impact Map

- Files/modules touched:
  - `frontend/src/components/workouts/TemplateSelector.tsx`
  - `docs/upgrades/specs/UPG-2026-03-07-41-template-selector-plan-package-cutover.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `frontend`, `docs`
- Invarianti da preservare:
  - template statici e scheda vuota continuano a funzionare;
  - il salvataggio finale usa ancora `createWorkout`;
  - nessun impatto su `SmartAnalysisPanel` e `MuscleMapPanel`;
  - nessun nuovo dato sensibile mostrato nella card Smart.

## Acceptance Criteria

- Funzionale:
  - la card Smart non usa piu' `generateSmartPlan()` / `fillSmartPlan()`;
  - il click su `Genera` chiama il backend `plan-package`;
  - il draft ritornato dal backend viene salvato via `createWorkout`.
- Tecnico:
  - `TemplateSelector.tsx` non importa piu' il vecchio path di generazione locale;
  - ESLint e' verde sui file frontend coinvolti.

## Test Plan

- Frontend lint:
  - `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/components/workouts/TemplateSelector.tsx" "src/hooks/useTrainingScience.ts" "src/types/api.ts"`
- Manual checks:
  - grep assenza di `generateSmartPlan`, `fillSmartPlan`, `assessFitnessLevel`, `useSmartProgramming` nel selector;
  - review dei nuovi stati disabled/loading della card Smart.

## Risks and Mitigation

- Rischio 1:
  - la card Smart perde alcuni segnali UI del vecchio profilo frontend.
- Mitigazione 1:
  - mantenere copy chiara e badge neutrali (`Backend-first`, `Cliente collegato`, `Ranking deterministico`) fino al cutover dei warning backend.

- Rischio 2:
  - il `plan-package` genera draft corretti ma i warning non sono ancora mostrati nella UI.
- Mitigazione 2:
  - rimandare il rendering dei warning al microstep successivo insieme al cutover di analisi/pannelli.

## Rollback Plan

- Ripristinare il vecchio handler locale Smart in `TemplateSelector.tsx`.
- Tornare all'uso di `generateSmartPlan()` e `fillSmartPlan()` solo nel selector.

## Notes

- Questo e' il primo taglio reale del dual-engine sul percorso utente SMART.
- I file legacy frontend non vengono ancora rimossi, per non accoppiare troppo il microstep.
