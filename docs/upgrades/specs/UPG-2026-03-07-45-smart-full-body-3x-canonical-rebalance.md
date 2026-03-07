# UPG-2026-03-07-45 - SMART Full Body 3x Canonical Rebalance

## Context

Dopo il pass stateful sul ranker, la Smart Analysis di una `3x generale intermedio` risultava ancora invariata su:

- `Push Orizz : Push Vert` troppo alto
- `Pull Orizz : Pull Vert` troppo alto
- `Quad : Ham` troppo basso
- frequenza bassa su bicipiti e femorali

La causa non era piu' il ranking degli esercizi, ma il piano scientifico canonico letto dal builder in modalita' pristine.

## Goal

Ridurre il bias strutturale del canonico `full_body 3x` senza toccare:

- endpoint API
- ranker runtime
- UI builder/pannelli

## Scope

- aggiornamento della rotazione full body in `split_logic.py`
- passaggio da logica implicita `A/B/A` a rotazione `A/B/C` per la frequenza `3x`

## Non-Goals

- nessun cambio a `plan_analyzer.py`
- nessun cambio ai target biomeccanici
- nessun cambio al ranking `plan-package`
- nessuna persistenza DB del canonico

## Implementation

Nuova rotazione:

- A: `push_h`, `pull_h`, `squat`, `carry`, `calf_raise`
- B: `push_v`, `pull_v`, `hinge`, `rotation`
- C: `squat`, `hinge`, `pull_h`, `pull_v`, `push_h`, `push_v`

Razionale:

- la terza seduta smette di ripetere la variante A
- upper horizontal e vertical ricevono una seconda esposizione
- femorali/catena posteriore ricevono una seconda esposizione canonica
- il riequilibrio avviene nel planner, cioe' nel layer che la Smart Analysis sta misurando

## Verification

- `venv\Scripts\ruff.exe check api/services/training_science/split_logic.py`

## Residual Risks

- La seduta C porta la full body 3x verso una sessione piu' densa; e' un compromesso intenzionale per correggere il bias canonico senza aprire ancora un refactor piu' profondo del planner.
- Se i warning residui restano alti, il prossimo step corretto sara' distribuire in modo piu' esplicito anche gli slot di isolamento su almeno 2 sessioni, non solo correggere i pattern compound.
