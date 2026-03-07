# UPG-2026-03-07-66 - SMART Constraint Adapter v1

> *"Prima di riscrivere il planner, dobbiamo misurare il legacy rispetto al
> protocollo selezionato."*

**Data**: 2026-03-07  
**Stato**: IMPLEMENTED  
**Ambito**: Training Science Engine, SMART Runtime, KineScore  
**Dipende da**: `UPG-2026-03-07-57`, `UPG-2026-03-07-64`, `UPG-2026-03-07-65`

---

## 1. Obiettivo

Introdurre il primo `Constraint Adapter v1` dentro `/training-science/plan-package`.

Questo microstep non cambia ancora il planner legacy.
Fa invece una cosa piu' importante per il metodo:

- prende il `protocol_id` gia' selezionato
- analizza il piano legacy rispetto al protocollo
- restituisce un report strutturato, tracciabile e tipizzato

In questo modo il runtime inizia a misurare la distanza tra
`protocol registry` e `legacy planner output`.

---

## 2. Cosa Cambia

### Backend

Nuovi moduli:

- [constraints/__init__.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/constraints/__init__.py)
- [constraint_types.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/constraints/constraint_types.py)
- [constraint_engine.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/constraints/constraint_engine.py)

Modifiche:

- [training_science.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/schemas/training_science.py)
- [plan_package_service.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/runtime/plan_package_service.py)

### Frontend

Type sync:

- [api.ts](/c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/types/api.ts)

---

## 3. Output API Nuovo

`TSPlanPackage` ora include `constraint_evaluation` con:

- `protocol_id`
- `constraint_profile_id`
- `analyzer_score`
- `findings[]`
- `summary`

Ogni finding ha:

- `rule_id`
- `severity`
- `scope`
- `status`
- `message`

---

## 4. Cosa Valuta v1

Il constraint adapter v1 controlla:

1. stato dichiarato del protocollo (`supported`, `clinical_only`, ecc.)
2. match esatto o fallback del protocol selector
3. range frequenza del protocollo
4. allineamento tra `split_family` dichiarata e `tipo_split` canonico
5. muscoli sotto MEV dal planner legacy
6. squilibri biomeccanici rilevati dall'analyzer legacy
7. overlap di recupero rilevati dall'analyzer legacy

Non e' ancora enforcement.
E' un report read-only affiancato al planner legacy.

---

## 5. Design

Il punto chiave e' questo:

- il protocol registry dichiara il target
- il planner legacy genera ancora il piano
- il constraint adapter misura la distanza tra i due

Questo passaggio e' essenziale per:

- evitare big bang rewrite
- raccogliere evidenza prima di cambiare il planner
- costruire il futuro `ConstraintEvaluationReport`
- preparare `Constraint Adapter v2` e `Feasibility Engine v1`

---

## 6. Invarianti Preservati

- `build_plan()` resta invariato
- `/training-science/plan` resta invariato
- nessun enforcement nuovo lato runtime
- nessun blocco nuovo lato builder
- nessuna dipendenza DB nel constraint engine

---

## 7. Verifica

Backend:

```powershell
venv\Scripts\ruff.exe check api\schemas\training_science.py api\services\training_science\runtime\plan_package_service.py api\services\training_science\constraints
```

Frontend:

```powershell
C:\Program Files\nodejs\npm.cmd --prefix frontend run lint -- "src/types/api.ts"
```

---

## 8. Rischi Residui

- Il report misura, ma non governa ancora la generazione.
- I vincoli sono ancora derivati dall'analyzer legacy, non da un vero `Constraint Engine v2`.
- La UI non consuma ancora `constraint_evaluation`.

---

## 9. Prossimo Step Minimo

Microstep successivo consigliato:

**Constraint Adapter v1.1 / UI Exposure**

Obiettivo:

- mostrare `protocol_id` e sintesi `constraint_evaluation` nel builder SMART
- senza aprire ancora il gate del planner v2
