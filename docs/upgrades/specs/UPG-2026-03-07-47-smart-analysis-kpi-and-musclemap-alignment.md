# UPG-2026-03-07-47 — SMART Analysis KPI + MuscleMap Alignment

## Perche'

Dopo i primi cutover SMART, il builder mostrava due drift UI importanti:

1. il riepilogo alto di `SmartAnalysisPanel` sommava solo `ottimali` e `carenti`, lasciando fuori gli `eccessi`;
2. `MuscleMapPanel` continuava a usare `computeSmartAnalysis()` locale, quindi colori e stati non coincidevano con l'analisi backend mostrata nello stesso builder.

Si aggiungeva inoltre un problema di leggibilita' safety:

- il builder non distingueva in modo esplicito tra condizioni rilevate in anamnesi, condizioni mappate nel catalogo e condizioni che impattano davvero la scheda corrente;
- alcune aggregazioni frontend usavano una priorita' severity incoerente (`avoid > caution > modify`) invece di rispettare la gerarchia backend `avoid > modify > caution`.

## Obiettivo

Allineare il builder SMART a una semantica unica e leggibile:

- KPI volume che includono anche gli eccessi nel conteggio "da correggere";
- MuscleMap alimentata dalla stessa analisi backend del pannello scientifico;
- legenda colori coerente a 4 stati: `ottimale / sub-ottimale / eccesso / deficit`;
- separazione esplicita tra condizioni anamnestiche rilevate e condizioni che impattano la scheda;
- priorita' safety frontend riallineata al backend.

## Microstep

### 1. Riepilogo SMART corretto

- `SmartAnalysisPanel` usa un helper condiviso per derivare i conteggi backend.
- Il KPI alto non mostra piu' "Carenti", ma "Da correggere".
- "Da correggere" include `deficit + suboptimal + excess`, quindi il totale torna coerente con i 15 gruppi muscolari analizzati.

### 2. MuscleMap backend-first

- `MuscleMapPanel` accetta `backendAnalysis`.
- Se disponibile, usa `TSAnalisiPiano.volume` come fonte primaria.
- Il fallback locale resta solo come degradazione temporanea se l'analisi backend non e' ancora arrivata.
- `MuscleMap` viene estesa a 4 intensita' per rappresentare anche il quarto stato.

### 3. Chiarezza safety nel builder

- La pagina scheda espone:
  - condizioni rilevate in anamnesi,
  - condizioni gia' mappate nel catalogo safety,
  - condizioni che impattano la scheda corrente.
- `SmartAnalysisPanel` mostra il rapporto `impattano la scheda / rilevate in anamnesi`.
- Le aggregazioni frontend severity vengono riallineate a `avoid > modify > caution`.

## File toccati

- `frontend/src/components/workouts/SmartAnalysisPanel.tsx`
- `frontend/src/components/workouts/MuscleMapPanel.tsx`
- `frontend/src/components/exercises/MuscleMap.tsx`
- `frontend/src/lib/training-science-display.ts`
- `frontend/src/app/(dashboard)/schede/[id]/page.tsx`

## Verifica

```powershell
venv\Scripts\ruff.exe check api/services/training_science/plan_builder.py api/services/training_science/runtime/exercise_ranker.py api/services/training_science/runtime/plan_package_service.py api/services/training_science/split_logic.py
& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/components/workouts/SmartAnalysisPanel.tsx" "src/components/workouts/MuscleMapPanel.tsx" "src/components/exercises/MuscleMap.tsx" "src/lib/training-science-display.ts" "src/app/(dashboard)/schede/[id]/page.tsx"
```

## Rischi residui

- `SmartAnalysisPanel` resta un file grande: il prossimo refactor utile e' estrarre bridge/helpers shared in un modulo dedicato.
- La body map comprime ancora i tre deltoidi nello stesso distretto visivo `shoulders`; il criterio scelto e' "worst status wins".
- I blocchi del builder restano parzialmente fuori dal path di analisi SMART, anche se la safety overview ora li considera meglio.

## Next Smallest Step

Unificare anche il path di analisi per i blocchi strutturati nel builder, cosi' `SmartAnalysisPanel`, `MuscleMapPanel` e safety summary leggono la stessa superficie completa della scheda.
