# UPG-2026-03-07-64 - SMART Runtime Translation Plan v1

> *"Il metodo non entra in produzione con un big bang.
> Entra con un piano di traduzione che protegge il runtime attuale mentre sposta la fonte di verita'."*

**Data**: 2026-03-07  
**Stato**: PHASES A-E DONE — Phase F deferred (matrice non ancora verde su dati reali)
**Ambito**: SMART backend, Training Science Engine, KineScore, Runtime Migration  
**Dipende da**: `UPG-2026-03-07-40`, `UPG-2026-03-07-55`, `UPG-2026-03-07-57`, `UPG-2026-03-07-58`, `UPG-2026-03-07-59`, `UPG-2026-03-07-60`, `UPG-2026-03-07-61`, `UPG-2026-03-07-62`, `UPG-2026-03-07-63`

---

## 1. Obiettivo

Definire il `Runtime Translation Plan v1` del nuovo SMART/KineScore.

Questa spec risponde alla domanda critica:

**come portiamo nel backend reale il nuovo metodo scientifico senza rompere il
motore attuale, il `plan-package`, il builder e i flussi gia' funzionanti?**

Il piano non introduce ancora codice runtime.
Serve a decidere:

- dove vive cosa
- in che ordine migrare i layer
- quali adapter servono
- quali file esistenti preservare
- quali file nuovi creare
- quali gate usare prima di spegnere il vecchio motore

---

## 2. Problema Reale

Oggi il backend ha gia' due mondi che convivono:

1. **Core scientifico legacy ma forte**
   - `principles.py`
   - `volume_model.py`
   - `balance_ratios.py`
   - `split_logic.py`
   - `session_order.py`
   - `plan_builder.py`
   - `plan_analyzer.py`
   - `periodization.py`

2. **Runtime SMART backend-first additivo**
   - `runtime/profile_resolver.py`
   - `runtime/exercise_catalog.py`
   - `runtime/exercise_ranker.py`
   - `runtime/plan_package_service.py`
   - endpoint `/training-science/plan-package`

Il nuovo metodo SMART/KineScore aggiunge ora altri 5 layer concettuali:

- `Evidence Registry`
- `Protocol Registry`
- `Constraint Schema`
- `Demand Vector`
- `Validation Harness`

Il rischio principale e' questo:

- se li inseriamo male, duplicheremo ancora logica
- se li inseriamo troppo presto nel planner, spacchiamo il runtime
- se li lasciamo solo in docs, non cambiera' nulla

---

## 3. Strategia Di Migrazione

La strategia raccomandata e' **adapter-first / strangler pattern**.

Questo significa:

- non riscrivere `plan_builder.py` in un colpo solo
- non sostituire subito `/plan`
- usare `/plan-package` come primo percorso di migrazione
- far convivere vecchio e nuovo finche' la validazione non e' verde

Principio:

`nuovo metodo -> adapter -> runtime esistente -> sostituzione progressiva`

Non:

`nuovo metodo -> riscrittura totale -> speriamo che funzioni`

---

## 4. Baseline Runtime Attuale

## 4.1 Entry points attuali

- [training_science.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/training_science.py)
  - `/plan` puro
  - `/analyze` puro
  - `/mesocycle` puro
  - `/plan-package` runtime DB-aware

## 4.2 Core puro attuale

- [types.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/types.py)
- [principles.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/principles.py)
- [volume_model.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/volume_model.py)
- [balance_ratios.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/balance_ratios.py)
- [split_logic.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/split_logic.py)
- [session_order.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/session_order.py)
- [plan_builder.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/plan_builder.py)
- [plan_analyzer.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/plan_analyzer.py)
- [periodization.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/periodization.py)

## 4.3 Runtime additivo attuale

- [profile_resolver.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/runtime/profile_resolver.py)
- [readiness.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/runtime/readiness.py)
- [exercise_catalog.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/runtime/exercise_catalog.py)
- [exercise_ranker.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/runtime/exercise_ranker.py)
- [plan_package_service.py](/c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/training_science/runtime/plan_package_service.py)

---

## 5. Target Runtime Topology

La topologia target deve restare dentro `api/services/training_science/`, ma
con separazione piu' esplicita.

```text
training_science/
  core/
    principles.py
    volume_model.py
    balance_ratios.py
    split_logic.py
    session_order.py
    plan_builder.py
    plan_analyzer.py
    periodization.py

  registry/
    evidence_registry.py
    protocol_registry.py
    protocol_selector.py

  constraints/
    constraint_types.py
    constraint_engine.py

  demand/
    demand_vector.py
    demand_registry.py
    demand_policy.py

  runtime/
    profile_resolver.py
    exercise_catalog.py
    feasibility_engine.py
    exercise_ranker.py
    plan_package_service.py

  validation/
    validation_catalog.py
    validation_contracts.py
```

Il naming esatto puo' variare, ma la separazione di responsabilita' no.

---

## 6. Regole Architetturali Di Traduzione

### 6.1 Il core puro resta puro

`build_plan()`, `analyze_plan()` e `build_mesocycle()` non devono diventare
DB-aware.

### 6.2 Il registry non decide il runtime da solo

`Evidence Registry` e `Protocol Registry` sono dati/contratti, non orchestratori.

### 6.3 Il ranker non deve diventare un secondo planner

Il ranker ordina candidati feasible.
La fattibilita' deve essere sempre piu' spostata in un `feasibility_engine`.

### 6.4 `/plan-package` e' il percorso pilota

Tutta la traduzione del nuovo metodo deve passare prima da `/plan-package`,
non da `/plan`.

### 6.5 Nessun big bang

Ogni nuova entita' del metodo deve entrare prima come `read-only / adapter`,
poi come `runtime dependency`.

---

## 7. File-By-File Translation Map

## 7.1 `api/services/training_science/types.py`

### Stato attuale

Vocabolario del core legacy.

### Ruolo target

Restare il vocabolario del **core planner legacy**, non inglobare tutto il
nuovo metodo.

### Azione

- non gonfiare questo file
- introdurre nuovi tipi del metodo in moduli separati:
  - `protocol_types.py`
  - `constraint_types.py`
  - `evidence_types.py`
  - `demand_types.py`

## 7.2 `api/services/training_science/plan_builder.py`

### Stato attuale

Planner centrale legacy con molte euristiche gia' raffinate.

### Ruolo target

Diventare il **legacy canonical builder** dietro un adapter.

### Azione

- congelare l'API pubblica
- evitare nuove patch locali salvo bug critici
- introdurre un wrapper `build_protocol_plan()` altrove
- usare `plan_builder.py` come engine sottostante finche' il planner v2 non e'
  pronto

## 7.3 `api/services/training_science/plan_analyzer.py`

### Stato attuale

Analyzer puro e gia' forte.

### Ruolo target

Restare l'oracolo di validazione del canonico legacy e base del validation harness.

### Azione

- non duplicare analyzer v2 subito
- aggiungere adapter che leggono i nuovi `protocol/constraint IDs` e li
  confrontano con l'output analyzer esistente

## 7.4 `api/services/training_science/runtime/profile_resolver.py`

### Stato attuale

Risolve cliente, anamnesi, safety, livello.

### Ruolo target

Diventare il punto di ingresso `context -> protocol selection`.

### Azione

- aggiungere output `protocol_selection_input`
- prepararlo a chiamare `protocol_selector`

## 7.5 `api/services/training_science/runtime/exercise_catalog.py`

### Stato attuale

Carica candidati rankabili con filtro ownership-safe.

### Ruolo target

Restare il loader del catalogo, senza logica scientifica forte.

### Azione

- estenderlo solo per portare metadata necessari:
  - future `demand_family`
  - future `demand_vector_ref`
  - suitability tags

## 7.6 `api/services/training_science/runtime/exercise_ranker.py`

### Stato attuale

Ranker con suitability e feedback stateful.

### Ruolo target

Diventare solo `distance-to-protocol scoring`.

### Azione

- spostare il piu' possibile la logica `allowed/discouraged/infeasible`
  in un `feasibility_engine`
- lasciare qui:
  - ordinamento
  - tie-break
  - preferenze
  - soft scoring

## 7.7 `api/services/training_science/runtime/plan_package_service.py`

### Stato attuale

Orchestratore principale del runtime SMART backend-first.

### Ruolo target

Diventare il vero entry point del metodo v2.

### Azione

- fase 1: restare orchestratore
- fase 2: introdurre i passaggi:
  - `select_protocol()`
  - `resolve_constraints()`
  - `build_canonical_plan_v2()` o adapter a legacy builder
  - `compute_feasible_candidates()`
  - `rank_candidates()`
  - `attach_validation_metadata()`

## 7.8 `api/routers/training_science.py`

### Stato attuale

Espone `/plan`, `/plan-package`, `/analyze`, `/mesocycle`.

### Ruolo target

Restare sottile.

### Azione

- non spostare qui logica metodo
- aggiungere solo nuovi response fields quando il runtime li produce davvero

---

## 8. Nuovi Moduli Da Introdurre

Il piano v1 raccomanda questi moduli nuovi.

## 8.1 Registry layer

- `api/services/training_science/registry/evidence_types.py`
- `api/services/training_science/registry/evidence_registry.py`
- `api/services/training_science/registry/protocol_types.py`
- `api/services/training_science/registry/protocol_registry.py`
- `api/services/training_science/registry/protocol_selector.py`

## 8.2 Constraint layer

- `api/services/training_science/constraints/constraint_types.py`
- `api/services/training_science/constraints/constraint_engine.py`
- `api/services/training_science/constraints/constraint_adapters.py`

## 8.3 Demand layer

- `api/services/training_science/demand/demand_types.py`
- `api/services/training_science/demand/demand_registry.py`
- `api/services/training_science/demand/demand_policy.py`

## 8.4 Runtime bridge layer

- `api/services/training_science/runtime/feasibility_engine.py`
- `api/services/training_science/runtime/protocol_plan_adapter.py`
- `api/services/training_science/runtime/validation_metadata.py`

## 8.5 Validation layer

- `api/services/training_science/validation/validation_catalog.py`
- `api/services/training_science/validation/validation_contracts.py`

---

## 9. Fasi Di Traduzione

## 9.1 Phase A - Read-only registries

Introduciamo:

- evidence registry
- protocol registry
- constraint types

Ma solo come dati/lookup.
Nessun impatto ancora sul planner runtime.

### Acceptance

- il backend sa leggere protocolli e anchor
- nessun comportamento runtime cambia

## 9.2 Phase B - Protocol selection in `/plan-package`

Introduciamo:

- `protocol_selector`
- `protocol_id` risolto nel `scientific_profile` o metadata package

Il planner legacy resta ancora sotto.

### Acceptance

- ogni `plan-package` dichiara il protocollo attivo
- nessuna regressione sul draft attuale

## 9.3 Phase C - Constraint adapter over legacy planner

Introduciamo un adapter che:

- legge protocollo e constraint set
- chiama il planner legacy
- verifica post-build il rispetto dei constraint
- annota mismatch e gap

### Acceptance

- mismatch espliciti e tracciabili
- nessuna rottura builder

## 9.4 Phase D - Feasibility engine before ranker

Il ranker smette di fare da solo la suitability hard.

### Acceptance

- `feasible / discouraged / infeasible` calcolati prima del ranker
- beginner/clinical gates spiegabili e testabili

## 9.5 Phase E - Validation metadata in runtime

Il `plan-package` inizia a trasportare anche:

- `protocol_id`
- `constraint_version`
- `evidence_version`
- `validation_case_refs` quando applicabile

### Acceptance

- output piu' auditabile
- builder ancora compatibile

## 9.6 Phase F - Legacy planner replacement decision

Solo dopo matrice verde e parity sufficiente:

- decidere se riscrivere `plan_builder.py`
- o mantenerlo come core tradotto/parametrizzato

Questa decisione non va presa prima.

---

## 10. Bridge Contracts Necessari

Per evitare una migrazione caotica, servono 3 bridge contracts.

## 10.1 `ProtocolSelectionResult`

Output del selector:

- `protocol_id`
- `registry_id`
- `selection_rationale`
- `selection_confidence`
- `fallback_used`

## 10.2 `ConstraintEvaluationReport`

Output dell'adapter:

- `hard_pass`
- `soft_mismatches`
- `optimization_gaps`
- `used_parameter_ids`

## 10.3 `FeasibilityResult`

Output pre-ranker:

- `exercise_id`
- `feasibility`
- `reason_codes`
- `violated_ceiling_ids`

---

## 11. Anti-Pattern Da Evitare

### 11.1 Copiare il registry nel planner

Il planner non deve contenere tabelle locali duplicate di protocollo/evidenza.

### 11.2 Usare il ranker come motore di policy

Il ranker deve ordinare, non governare il metodo.

### 11.3 Agganciare il nuovo metodo direttamente a `/plan`

Il percorso pilota resta `/plan-package`.

### 11.4 Mischiare validation e runtime

Il runtime puo' allegare metadata di validazione, ma il validation harness resta separato.

### 11.5 Fare big bang su `plan_builder.py`

Il planner legacy si spegne solo quando la parity e la validation matrix lo permettono.

---

## 12. Primo Lotto Di Implementazione Raccomandato

Se dopo questa spec torniamo al codice, il primo microstep giusto e' questo:

1. creare `registry/evidence_types.py`
2. creare `registry/protocol_types.py`
3. creare `registry/protocol_registry.py` con i primi `PRT-001 ... PRT-006`
4. introdurre `protocol_id` nel `TSPlanPackage.engine` o metadata vicino
5. far risolvere un protocollo a `/plan-package` senza cambiare ancora il planner

Questo e' il primo step piccolo ma architetturalmente vero.

---

## 13. Acceptance Criteria Del Piano

Il `Runtime Translation Plan v1` e' utile se rende esplicito:

1. dove vivono i nuovi layer
2. quali file esistenti non vanno riscritti subito
3. quale percorso runtime pilota usare
4. quale ordine di migrazione seguire
5. quale primo microstep implementativo avviare

---

## 14. Roadmap Immediata

Dopo questa spec, i passi corretti sono:

1. `registry scaffolding patch`
   introdurre i primi moduli read-only del registry

2. `protocol selection patch`
   far emergere `protocol_id` nel runtime `plan-package`

3. `constraint adapter patch`
   misurare il planner legacy contro i nuovi constraint senza ancora sostituirlo

4. `feasibility engine patch`
   spostare la suitability hard fuori dal ranker

---

## 15. Note Finali

Questo piano non promette che il planner legacy vada buttato.
Promette qualcosa di piu' utile:

- mettere il nuovo metodo sopra il runtime reale
- misurare la distanza tra metodo e comportamento
- sostituire i pezzi solo quando servono davvero

Questo e' il modo corretto di fare una migrazione scientifica seria.

---

## 16. Implementation Status (aggiornato 2026-03-07)

### Phase A — Read-only registries: DONE (UPG-65)

File creati:
- `registry/evidence_types.py` — EvidenceUsageRecord, EVIDENCE_USAGE_REGISTRY
- `registry/protocol_types.py` — ProtocolRecord, ProtocolSelectionResult, SplitFamily
- `registry/protocol_registry.py` — 6 protocolli PRT-001..006
- `registry/protocol_selector.py` — select_protocol() deterministico
- `registry/__init__.py` — re-export

### Phase B — Protocol selection in `/plan-package`: DONE (UPG-66)

File modificati:
- `runtime/plan_package_service.py` — protocol_id risolto e allegato a TSPlanPackage
- `api/schemas/training_science.py` — TSPlanPackageProtocolInfo aggiunto

### Phase C — Constraint adapter: DONE (UPG-67)

File creati:
- `constraints/constraint_types.py` — ConstraintSeverity, ConstraintScope, ConstraintStatus
- `constraints/constraint_engine.py` — evaluate_protocol_constraints() read-only
- `constraints/__init__.py` — re-export

File modificati:
- `runtime/plan_package_service.py` — constraint evaluation allegata a TSPlanPackage
- `api/schemas/training_science.py` — TSConstraintEvaluationReport, TSConstraintFinding

### Phase D — Feasibility engine: DONE (UPG-67b)

File creati:
- `runtime/feasibility_engine.py` — compute_feasibility_summary() pre-ranking

File modificati:
- `runtime/plan_package_service.py` — feasibility summary allegata
- `api/schemas/training_science.py` — TSFeasibilitySummary

### Phase E — Validation metadata: DONE (UPG-68)

File creati:
- `runtime/validation_metadata.py` — ValidationMetadata con build() factory

File modificati:
- `runtime/plan_package_service.py` — validation metadata allegata
- `api/schemas/training_science.py` — TSValidationMetadata
- `frontend/src/types/api.ts` — TSValidationMetadata interface

### Demand Layer — DONE (UPG-69)

File creati:
- `demand/demand_types.py` — ExerciseDemandVector (10 dim), DemandCeiling, DemandFamily
- `demand/demand_registry.py` — 54 vettori default (18 pattern x 3 diff) + 6 ceiling
- `demand/demand_policy.py` — check_demand_ceiling() deterministico
- `demand/__init__.py` — re-export

### Validation Harness — DONE (UPG-70)

File creati:
- `validation/validation_catalog.py` — 6 benchmark (VM-001..006) + 5 client fixtures + 6 request fixtures
- `validation/validation_contracts.py` — 22 check functions + warning policy + runner
- `validation/__init__.py` — re-export

### Phase F — Legacy planner replacement: DEFERRED

Prerequisito: matrice verde su tutti i 6 benchmark con plan-package reale.
Decisione: non presa, in attesa di integrazione end-to-end.

### Bridge Contracts implementati

| Contract | File | Stato |
|----------|------|-------|
| ProtocolSelectionResult | `registry/protocol_types.py` | DONE |
| ConstraintEvaluationReport | `api/schemas/training_science.py` | DONE |
| FeasibilitySummary | `api/schemas/training_science.py` | DONE |
| ValidationMetadata | `runtime/validation_metadata.py` | DONE |
