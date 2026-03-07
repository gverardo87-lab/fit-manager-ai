# UPG-2026-03-07-44 - SMART Ranker Stateful Balance Pass

## Context

Dopo il primo cutover `plan-package`, il backend analyzer ha iniziato a produrre warning sensati su schede SMART reali:

- eccesso orizzontale vs verticale
- sotto-frequenza su bicipiti e femorali
- overlap di recupero su dorsali, trapezio e core tra sessioni consecutive

Il problema non era piu' l'analisi, ma il ranking `slot-by-slot` troppo locale del runtime SMART.

## Goal

Introdurre un primo feedback settimanale deterministico nel ranker, senza toccare:

- planner scientifico puro
- endpoint API
- contratti frontend/backend

## Scope

- nuovo `RankerSelectionState` nel runtime SMART
- feedback incrementale durante la costruzione della settimana
- bonus/penalita' su:
  - balance orizzontale vs verticale
  - rebalance quad/posterior chain
  - frequenza bicipiti/femorali
  - overlap recupero con la sessione precedente
  - duplicazione stesso esercizio nella settimana
- bump `ranking_version`

## Non-Goals

- nessun refactor del `plan_builder`
- nessun cambio di split logic full-body A/B
- nessuna persistenza DB del canonico
- nessuna ottimizzazione globale multi-slot o multi-sessione tipo solver

## Implementation

### 1. Stato incrementale

`exercise_ranker.py` introduce `RankerSelectionState` con:

- conteggi pattern gia' selezionati
- conteggi muscoli gia' esposti
- set esercizi gia' usati
- muscoli sensibili della sessione precedente

### 2. Heuristics deterministiche

Per ogni candidato il ranker applica, oltre a pattern/muscolo/difficolta'/safety:

- `weekly_pattern_rebalance`
- `weekly_pattern_penalty`
- `posterior_chain_rebalance`
- `quad_dominance_penalty`
- `frequency_boost_hamstrings`
- `frequency_boost_biceps`
- `recovery_overlap_penalty`
- `weekly_uniqueness_penalty`

### 3. Orchestrazione

`plan_package_service.py` mantiene e aggiorna il `RankerSelectionState` mentre seleziona i top-1 slot per slot, sessione per sessione.

## Verification

- `venv\Scripts\ruff.exe check api/services/training_science/runtime/exercise_ranker.py api/services/training_science/runtime/plan_package_service.py`

## Residual Risks

- La full-body `3x` A/B/A del planner puo' mantenere un bias strutturale verso i pattern della variante A; questo microstep riduce il drift del ranking, ma non sostituisce un eventuale tuning del planner.
- Il feedback resta greedy e locale nel tempo; non e' ancora un'ottimizzazione globale su tutte le combinazioni candidate.
