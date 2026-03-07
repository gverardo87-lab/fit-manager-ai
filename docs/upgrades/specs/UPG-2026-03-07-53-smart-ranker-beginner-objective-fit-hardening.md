# UPG-2026-03-07-53 — SMART Ranker Beginner Objective-Fit Hardening

## Contesto

Nel `plan-package` SMART il canonico `3x beginner` stava migliorando, ma la proiezione concreta continuava a scegliere esercizi non plausibili per un principiante generale, ad esempio:

- `Muscle-Up alla Sbarra`
- `Box Jump`
- `Salto su Cassone`

Il problema non era nel planner, ma nel ranker runtime: pattern e muscolo bastavano ancora a far vincere esercizi troppo skill-based o privi di `rep_range` utile per l'obiettivo.

## Decisione

Rafforzare il runtime ranker con due criteri additivi:

1. **Objective fit**
   - bonus agli esercizi che hanno il `rep_range` coerente con l'obiettivo scientifico
   - penalita' a quelli che ne sono privi

2. **Beginner suitability**
   - penalita' piu' forte sugli esercizi `advanced` per profilo `beginner`
   - penalita' aggiuntiva su slot beginner per esercizi `cardio`
   - penalita' mirata su movimenti chiaramente `jump/skill/plyo`

## Obiettivo

Evitare che il builder SMART principiante proponga in top-rank movimenti troppo esplosivi, skill-based o poco prescrivibili per tonificazione generale, pur mantenendo il ranking deterministico e senza hard-block assoluti.

## Impatto

- migliore coerenza tra canonico scientifico e scheda concreta
- riduzione dei falsi positivi su `muscle-up` / `jump` nei profili beginner
- nessun cambio API
- nessun cambio UI

## Verifica

- `venv\Scripts\ruff.exe check api/services/training_science/runtime/exercise_catalog.py api/services/training_science/runtime/exercise_ranker.py`

## Rischi Residui

- il seed esercizi contiene ancora qualche movimento esplosivo classificato in modo permissivo
- `Quad : Ham` e overlap `Full Body B -> Full Body C` restano problemi del planner, non del ranker
- i warning di frequenza su `bicipiti/tricipiti` nel canonico richiedono un microstep planner-specifico separato
