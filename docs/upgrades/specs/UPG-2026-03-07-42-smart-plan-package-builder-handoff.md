# UPG-2026-03-07-42 — SMART Plan Package Builder Handoff

## Context

`TemplateSelector` genera ora la scheda SMART via `POST /training-science/plan-package`, ma il builder perdeva subito il contesto canonico restituito dal backend.

Questo lasciava due problemi:

1. `SmartAnalysisPanel` continuava a partire da una ricostruzione approssimata `workout -> TSTemplatePiano`.
2. Il builder non aveva nessun ponte temporaneo verso il `canonical_plan` senza aprire subito il gate di persistenza DB.

## Goal

Introdurre un handoff temporaneo, locale e deterministic-first del `plan-package` dal momento della creazione SMART alla prima apertura del builder.

## Scope

- cache session-scoped del `plan-package` nel frontend
- salvataggio del package alla creazione della scheda SMART
- consumo one-shot nel builder `/schede/[id]`
- `SmartAnalysisPanel` canonico-first finche' la scheda resta pristina
- clear automatico del handoff alla prima modifica utente

## Non-Goals

- nessuna persistenza DB del canonico
- nessun cambio schema workout
- nessun cutover di `MuscleMapPanel`
- nessuna analisi condivisa cross-panel ancora

## Implementation

### 1. Cache temporanea frontend

Nuovo file:

- `frontend/src/lib/smart-plan-package-cache.ts`

Responsabilita':

- `storeSmartPlanPackage(workoutId, planPackage)`
- `consumeSmartPlanPackage(workoutId)`
- storage in `sessionStorage`
- TTL corta per evitare residui stantii
- invalidazione one-shot al consumo

### 2. TemplateSelector

`TemplateSelector` salva il `plan-package` subito dopo `createWorkout.onSuccess(plan)`, usando l'`id` reale della scheda appena creata.

### 3. Builder page

`/schede/[id]`:

- consuma il package solo alla prima apertura del piano
- mantiene il package in stato locale finche' la scheda non viene toccata
- lo invalida alla prima modifica (`isDirty=true`)

### 4. SmartAnalysisPanel

Quando `smartPlanPackage` e' disponibile:

- costruisce `TSTemplatePiano` dal `canonical_plan`, non dal bridge locale
- mostra il contesto di generazione (`mode`, livello scientifico, stato anamnesi, condition count)
- rende visibili `profile_warnings` / `warnings`

Quando il builder viene modificato:

- il package viene scartato
- il pannello torna al bridge attuale `workout -> TSTemplatePiano`

## Verification

- `npm --prefix frontend run lint -- "src/lib/smart-plan-package-cache.ts" "src/components/workouts/TemplateSelector.tsx" "src/components/workouts/SmartAnalysisPanel.tsx" "src/app/(dashboard)/schede/[id]/page.tsx"`
- grep presenza handoff `storeSmartPlanPackage|consumeSmartPlanPackage|smartPlanPackage`

## Residual Risks

- `MuscleMapPanel` resta ancora su `computeSmartAnalysis()` locale.
- Il handoff e' valido solo per la prima apertura del builder nella stessa sessione browser.
- Dopo edit utente, l'analisi torna ancora al bridge workout-based.

## Next Smallest Step

Unificare `SmartAnalysisPanel` e `MuscleMapPanel` su una stessa fonte di analisi, idealmente con hook condiviso builder-side o endpoint backend che analizzi direttamente la scheda salvata.
