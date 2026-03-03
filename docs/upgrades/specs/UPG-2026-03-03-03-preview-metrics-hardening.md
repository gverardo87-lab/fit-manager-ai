# Patch Spec - Preview Metrics Hardening

## Metadata

- Upgrade ID: UPG-2026-03-03-03
- Date: 2026-03-03
- Owner: gvera + codex
- Area: Workout Preview (`WorkoutPreview.tsx`)
- Priority: medium
- Target release: 2026-03-03 (`codex_01`)
- Status: in_progress

## Problem

La logica KPI dei blocchi (`Tabata`, `AMRAP`, `EMOM`, ecc.) e' accoppiata dentro il componente preview.
Questo rende difficile testarla in isolamento e aumenta il rischio di regressioni grafiche non intenzionali.

## Desired Outcome

Separare la logica KPI in utility pura testata, mantenendo la resa UI identica.
Ogni variazione di ordering/label dei KPI deve essere verificabile con test automatici veloci.

## Scope

- In scope:
  - estrazione `buildBlockMetrics` in `frontend/src/lib/`
  - test Vitest su ordinamento/label per i principali tipi blocco
  - nessun cambio intenzionale di resa visiva
- Out of scope:
  - redesign UI dei blocchi
  - cambi backend o API

## Impact Map

- Files/modules da toccare:
  - `frontend/src/components/workouts/WorkoutPreview.tsx`
  - `frontend/src/lib/workout-preview-block-metrics.ts`
  - `frontend/src/__tests__/workouts/workout-preview-block-metrics.test.ts`
- Layer coinvolti: `frontend`
- Invarianti da preservare:
  - stesso ordering KPI gia' in produzione
  - stessa semantica label (`Minuti` per EMOM, `Giri` altrove)

## Acceptance Criteria

- Funzionale:
  - KPI dei blocchi mostrati in preview restano invariati rispetto a prima.
- UX:
  - nessuna regressione visiva sul pannello preview/export.
- Tecnico:
  - utility pura testata con Vitest.
  - build frontend verde.

## Test Plan

- Unit/Integration:
  - test su `buildBlockMetrics` per `tabata`, `emom`, `amrap`, `for_time`, fallback.
- Manual checks:
  - verificare preview di almeno una sessione con blocchi diversi.
- Build/Lint gates:
  - `cd frontend && npm test`
  - `cd frontend && npx next build`

## Risks and Mitigation

- Rischio 1: invertire accidentalmente ordine KPI.
  - Mitigazione: snapshot espliciti array `label/value` nei test.

## Rollback Plan

- Reintegrare `buildBlockMetrics` dentro `WorkoutPreview.tsx` e rimuovere utility/test.

## Notes

- Patch tecnica di hardening, senza cambi UX previsti.
