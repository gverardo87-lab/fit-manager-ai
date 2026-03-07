# UPG-2026-03-07-54 — SMART Ranker Beginner Compatible Draft Gating

## Contesto

Dopo `UPG-2026-03-07-53`, il ranker beginner penalizzava di piu' i candidati troppo tecnici, ma in alcuni slot potevano ancora comparire movimenti come `Muscle-Up alla Sbarra`.

Il punto scientifico qui non e' solo il punteggio: per un draft automatico beginner, un esercizio `advanced` o chiaramente `skill/plyo` non dovrebbe vincere se esiste gia' nello stesso slot un'alternativa compatibile e prescrivibile.

## Decisione

Nel runtime ranker:

1. definire un criterio di **beginner unsuitability**
   - `difficolta == advanced`
   - nome esercizio con marker `jump/salto/muscle-up/plyo`
   - esercizi `cardio` usati in slot non `resistenza`

2. se nello stesso slot esiste almeno un candidato compatibile beginner, i candidati beginner-unsuitable vengono esclusi dal draft automatico

3. eccezioni:
   - `pinned_exercise_id`
   - `preferred_exercise_ids`

Quindi il trainer mantiene la possibilita' di forzare/scalare manualmente, ma l'auto-fill SMART non propone piu' un draft tecnicamente incoerente.

## Obiettivo

Bloccare scientificamente i falsi top-rank beginner quando sono disponibili alternative semplici, stabili e prescrivibili.

## Impatto

- draft automatici beginner piu' realistici
- meno scelte skill-based non giustificate
- nessun cambio API
- nessun cambio UI

## Verifica

- `venv\Scripts\ruff.exe check api/services/training_science/runtime/exercise_ranker.py`

## Rischi Residui

- il seed esercizi contiene ancora classificazioni permissive che possono riemergere in altri profili
- `Quad : Ham` e warning di recupero restano problemi del planner
- frequenza `bicipiti/tricipiti` nel canonico beginner resta un tuning separato
