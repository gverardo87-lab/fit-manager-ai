# UPG-2026-03-07-67 - SMART Feasibility Engine v1

> *"Il ranker ordina. Il feasibility engine decide chi puo' partecipare."*

**Data**: 2026-03-07
**Stato**: IMPLEMENTED
**Ambito**: Training Science Engine, SMART Runtime
**Dipende da**: `UPG-2026-03-07-64` (Phase D), `UPG-2026-03-07-65`, `UPG-2026-03-07-66`

---

## 1. Obiettivo

Separare la logica di ammissibilita' (puo'/non-puo' entrare nel draft)
dalla logica di ordinamento (quale esercizio e' migliore per lo slot).

Prima di questa fase, il ranker conteneva sia gate hard (beginner suitability,
safety avoid) che scoring soft. Questo violava il principio di separazione
delle responsabilita' e rendeva i gate non testabili in isolamento.

---

## 2. Cosa Cambia

### Nuovo modulo

- `api/services/training_science/runtime/feasibility_engine.py`

### Modifiche

- `api/services/training_science/runtime/exercise_ranker.py`
- `api/services/training_science/runtime/plan_package_service.py`
- `api/schemas/training_science.py`
- `frontend/src/types/api.ts`

---

## 3. Design

### 3 verdetti

| Verdetto | Significato | Effetto nel ranker |
|----------|-------------|-------------------|
| `feasible` | Esercizio ammissibile senza restrizioni | Candidato normale |
| `discouraged` | Ammissibile ma con penalita' clinica (modify) | Candidato con safety penalty |
| `infeasible_for_auto_draft` | Escluso dal draft automatico | Filtrato (a meno che pinned/preferred) |

### Gate implementati in v1

1. **Beginner gates** (3 regole):
   - `beginner_advanced_difficulty`: esercizio advanced per profilo beginner
   - `beginner_power_skill_exercise`: token di skill/power nel nome (jump, plyo, muscle-up)
   - `beginner_cardio_non_endurance`: cardio per obiettivo non-resistenza in profilo beginner

2. **Safety gates** (2 regole):
   - `clinical_avoid`: safety severity = avoid -> infeasible_for_auto_draft
   - `clinical_modify_required`: safety severity = modify -> discouraged

### Merge verdetti

Worst-case: `infeasible > discouraged > feasible`.
Se un esercizio e' sia beginner-unsuitable che clinical-avoid, il verdetto e' `infeasible_for_auto_draft`.

---

## 4. Flusso Runtime

```
load_rankable_exercises(session, trainer_id)
    |
    v
compute_feasibility(exercises, profile, safety_entries)  <- NUOVO
    |
    v
rank_slot_candidates(..., feasibility=report)            <- MODIFICATO
    |
    v
TSPlanPackage { ..., feasibility_summary }               <- ESTESO
```

Il ranker consuma il `FeasibilityReport` senza duplicare la logica.
Se `feasibility` non e' fornito, il ranker funziona come prima (backward-compatible).

---

## 5. Output API

`TSPlanPackage` ora include `feasibility_summary`:

```json
{
  "feasibility_summary": {
    "feasible_count": 340,
    "discouraged_count": 12,
    "infeasible_count": 39
  }
}
```

Engine version aggiornata: `ranking_version: "ts-rank-v2-feasibility"`.

---

## 6. Invarianti Preservati

- `build_plan()` resta invariato
- `rank_slot_candidates()` resta backward-compatible (feasibility opzionale)
- Lo scoring soft (safety penalty, beginner penalty) resta nel ranker
- Il ranker rispetta ancora `pinned_exercise_id` e `preferred_exercise_ids`
- Nessuna dipendenza DB nel feasibility engine
- Nessun blocco nuovo lato builder

---

## 7. Verifica

Backend:
```powershell
venv\Scripts\ruff.exe check api\schemas\training_science.py api\services\training_science\runtime
```

Frontend:
```powershell
cd frontend && npx next build
```

---

## 8. Prossimo Step Minimo

**Phase E - Validation Metadata**: aggiungere metadata di validazione ai protocolli
per rendere i benchmark case (VM-001..006) eseguibili a runtime.
