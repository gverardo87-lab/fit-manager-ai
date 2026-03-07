# UPG-2026-03-07-46 - SMART Plan Builder Balance Guardrails

## Context

Dopo il riequilibrio `A/B/C` del canonico `full_body 3x`, la Smart Analysis mostrava un netto miglioramento su:

- `Push Orizz : Push Vert`
- `Pull Orizz : Pull Vert`
- frequenza bicipiti/femorali

Restavano pero' due warning strutturali:

- `Push : Pull` troppo alto
- `Quad : Ham` troppo basso

Il punto corretto di intervento non era piu' il ranker, ma `plan_builder.py`, in particolare:

- Fase 2: compound boost per muscoli carenti
- Fase 3: compensazione volume con isolamento

## Goal

Introdurre guardrail scientifici nel planner per evitare che la correzione del volume degradi l'equilibrio biomeccanico.

## Scope

- guardrail `Push : Pull` nella Fase 2
- priorita' quad-specifica e correzione `Quad : Ham` nella Fase 3
- nessun cambio API
- nessun cambio UI

## Non-Goals

- nessun refactor del runtime ranker
- nessun cambio ai target in `balance_ratios.py`
- nessun solver globale multi-obiettivo

## Implementation

### 1. Compound boost balance-aware

Durante `_boost_compound_series()`:

- se il pattern e' `push_h` o `push_v`
- il planner verifica che il boost non porti `Push : Pull` oltre la soglia target+tolleranza

Questo impedisce che il recupero del volume di petto/deltoide anteriore faccia deragliare il rapporto spalla-scapola.

### 2. Priorita' quad-specifica negli isolation deficits

Quando `Quad : Ham` e' sotto la soglia accettabile:

- `quadricipiti` viene prioritizzato
- `femorali` e `glutei` scendono in coda tra i deficit isolation

### 3. Correzione mirata del rapporto Quad:Ham

Dopo la Fase 3, il planner puo' aggiungere una piccola correzione `leg_extension` se:

- `Quad : Ham` resta sotto soglia
- i quadricipiti non hanno ancora raggiunto `mav_max`

Questo riconosce che il volume ipertrofico quad puo' essere "ottimale" ma ancora insufficiente per il rapporto biomeccanico.

## Verification

- `venv\Scripts\ruff.exe check api/services/training_science/plan_builder.py`

## Residual Risks

- Il recupero tra `Full Body B -> Full Body C` puo' restare alto sulla catena posteriore anche dopo questa patch.
- Se i warning residui si concentrano sul recupero, il prossimo step corretto e' la distribuzione multi-sessione degli slot di isolamento/posterior chain, non un altro tuning dei ratio.
