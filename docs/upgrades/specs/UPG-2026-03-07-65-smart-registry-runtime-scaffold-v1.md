# UPG-2026-03-07-65 - SMART Registry Runtime Scaffold v1

> *"Il metodo entra nel runtime prima come identificazione dichiarata, non come
> riscrittura totale del planner."*

**Data**: 2026-03-07  
**Stato**: IMPLEMENTED  
**Ambito**: Training Science Engine, SMART Runtime, KineScore  
**Dipende da**: `UPG-2026-03-07-40`, `UPG-2026-03-07-56`, `UPG-2026-03-07-64`

---

## 1. Obiettivo

Introdurre il primo scaffold runtime read-only del nuovo `Protocol Registry`
SMART/KineScore senza toccare il planner legacy.

Questo microstep chiude il primo ponte concreto tra il metodo formalizzato nelle
spec e il backend reale:

- crea i moduli `registry/` minimi
- risolve un `protocol_id` deterministico in `/training-science/plan-package`
- espone metadata di protocollo nel `TSPlanPackage`
- lascia invariato `build_plan()`

---

## 2. Cosa Cambia

### Backend

Nuovi moduli:

- [registry/__init__.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/registry/__init__.py)
- [registry/evidence_types.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/registry/evidence_types.py)
- [registry/protocol_types.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/registry/protocol_types.py)
- [registry/protocol_registry.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/registry/protocol_registry.py)
- [registry/protocol_selector.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/registry/protocol_selector.py)

Modifiche:

- [training_science.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/schemas/training_science.py)
- [plan_package_service.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/runtime/plan_package_service.py)

### Frontend

Type sync:

- [api.ts](/c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/types/api.ts)

---

## 3. Design

Il runtime continua a generare il canonico con il planner legacy.

Il nuovo metodo entra solo come:

1. selezione protocollo read-only
2. metadata ritornati nel `plan-package`
3. base per i prossimi step (`constraint adapter`, `feasibility engine`)

Il selector e' puro e deterministic-first:

- legge `mode`, `obiettivo_scientifico`, `livello_scientifico`, `frequenza`
- confronta contro `PRT-001 ... PRT-006`
- ritorna il miglior match o fallback dichiarato
- rende esplicito se il match e' `exact` o `fallback`

---

## 4. Output API Nuovo

`TSPlanPackage` ora include:

- `protocol.protocol_id`
- `protocol.label`
- `protocol.status`
- `protocol.exact_match`
- `protocol.registry_version`
- `protocol.validation_case_ids`
- `protocol.selection_rationale`

Questo non cambia ancora il comportamento del planner, ma rende il runtime
tracciabile e pronto alla validazione.

---

## 5. Invarianti Preservati

- nessun cambio a `build_plan()`
- nessun cambio a `/training-science/plan`
- nessuna logica DB nel registry
- nessun coupling nuovo tra planner legacy e protocol registry
- nessun blocco nuovo lato builder

---

## 6. Verifica

Backend:

```powershell
venv\Scripts\ruff.exe check api\schemas\training_science.py api\services\training_science\runtime\plan_package_service.py api\services\training_science\registry
```

Frontend:

```powershell
C:\Program Files\nodejs\npm.cmd --prefix frontend run lint -- "src/types/api.ts" "src/hooks/useTrainingScience.ts"
```

---

## 7. Rischi Residui

- Il selector e' ancora un layer read-only: non influenza ancora il planner.
- I protocolli sono dichiarati, ma non ancora tradotti in `constraint execution`.
- `protocol_id` e' tracciato nel package, ma non ancora visualizzato nella UI.

---

## 8. Prossimo Step Minimo

Microstep successivo consigliato:

**Constraint Adapter v1**

Obiettivo:

- leggere il protocollo selezionato
- costruire un `ConstraintEvaluationReport`
- affiancarlo al planner legacy dentro `/plan-package`
- senza ancora cambiare il motore di generazione
