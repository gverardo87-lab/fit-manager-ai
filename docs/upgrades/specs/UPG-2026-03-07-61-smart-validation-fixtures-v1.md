# UPG-2026-03-07-61 - SMART Validation Fixtures v1

> *"La matrice dice quali casi esistono.
> Le fixture dicono con quali dati esatti quei casi devono vivere."*

**Data**: 2026-03-07  
**Stato**: ANALYSIS SPEC  
**Ambito**: SMART backend, KineScore, Validation Harness, Test Data Contract  
**Dipende da**: `UPG-2026-03-07-55`, `UPG-2026-03-07-58`, `UPG-2026-03-07-59`, `UPG-2026-03-07-60`

---

## 1. Obiettivo

Definire le `Validation Fixtures v1` del nuovo SMART/KineScore.

Questa spec traduce la `Validation Matrix v1` in una shape concreta di dati
congelati, pronta per diventare:

- file fixture versionati nel repository
- input dei test scientifici
- baseline di regressione planner/ranker/analyzer
- supporto ad audit e benchmark contro esperto

Non introduce ancora test runtime, ma chiude il contratto dei dati di test.

---

## 2. Ruolo Delle Fixture

La `Validation Matrix` definisce:

- quali casi esistono
- quali controlli fare

Le `Validation Fixtures` definiscono:

- con quali dati minimi e deterministici eseguire quei casi
- quale output aspettarsi
- cosa puo' oscillare e cosa deve restare congelato

Senza fixture congelate:

- la matrice resta descrittiva
- i test diventano dipendenti dal DB reale o da stati impliciti

Con fixture congelate:

- il motore puo' essere validato in modo riproducibile
- i benchmark scientifici diventano confrontabili nel tempo

---

## 3. Principi Di Design

### 3.1 Self-contained

Ogni caso deve essere eseguibile senza dipendere dal DB operativo del trainer.

### 3.2 Privacy-safe

Nessuna fixture deve contenere PII reale.

### 3.3 Minimal but sufficient

Le fixture devono contenere solo i dati necessari a far emergere:

- protocol selection
- canonical plan behavior
- draft suitability
- analyzer output
- safety overlay

### 3.4 Stable IDs

Ogni fixture deve avere ID stabili e parlanti.

### 3.5 Layer-separated

Client profile, request envelope ed expected output devono stare in file distinti.

---

## 4. Directory Target v1

Le fixture devono vivere in:

`tests/training_science/validation_matrix/fixtures/`

Con questa struttura minima:

```text
fixtures/
  clients/
    CFG-A-minimal-beginner.json
    CFG-B-beginner-clinical-low-skill.json
    CFG-C-intermediate-general.json
    CFG-D-intermediate-performance.json
    CFG-E-advanced-hypertrophy.json
  requests/
    RQ-VM-001.json
    RQ-VM-002.json
    RQ-VM-003.json
    RQ-VM-004.json
    RQ-VM-005.json
    RQ-VM-006.json
  expected/
    EXP-VM-001.json
    EXP-VM-002.json
    EXP-VM-003.json
    EXP-VM-004.json
    EXP-VM-005.json
    EXP-VM-006.json
  registry/
    VALIDATION_MATRIX_INDEX.json
```

---

## 5. Fixture Families v1

Le fixture v1 sono divise in 4 famiglie.

## 5.1 Client Fixtures

Rappresentano il profilo scientifico-clinico minimo del soggetto.

## 5.2 Request Fixtures

Rappresentano il `plan-package request envelope`.

## 5.3 Expected Fixtures

Rappresentano il comportamento atteso del sistema.

## 5.4 Registry Fixture

Indice unico che collega `VM-*`, `CFG-*`, `RQ-*`, `EXP-*`.

---

## 6. Client Fixture Schema v1

Ogni `client fixture` deve essere una rappresentazione backend-neutral del
profilo cliente.

```json
{
  "client_fixture_id": "CFG-A",
  "label": "minimal beginner",
  "sesso": "F",
  "eta_bucket": "30-39",
  "anamnesi_state": "legacy",
  "readiness_state": "partial",
  "activity_level": "low",
  "training_age": "novice",
  "goals_profile": ["general_fitness", "tonificazione"],
  "safety_conditions": [],
  "body_regions_sensitive": [],
  "measurement_profile": {
    "has_strength_data": false,
    "has_body_comp_data": true,
    "has_readiness_metrics": false
  },
  "notes": "Fixture minimale beginner general senza overlay clinico dominante."
}
```

### Regole

- niente nomi reali
- niente date di nascita reali
- bucket invece di PII granulari quando non servono
- safety e readiness espliciti

---

## 7. Request Fixture Schema v1

Ogni `request fixture` deve mappare 1:1 il contract del `plan-package`.

```json
{
  "request_fixture_id": "RQ-VM-002",
  "case_id": "VM-002",
  "client_fixture_id": "CFG-A",
  "preset": {
    "frequenza": 3,
    "obiettivo_builder": "generale",
    "livello_choice": "auto",
    "mode": "general",
    "durata_target_min": 60
  },
  "trainer_overrides": {
    "excluded_exercise_ids": [],
    "preferred_exercise_ids": [],
    "pinned_exercise_ids_by_slot": {},
    "notes": null
  }
}
```

### Regole

- nessun trainer reale
- override vuoti salvo casi specifici di test
- formato identico al futuro input runtime

---

## 8. Expected Fixture Schema v1

Le fixture `expected` non devono essere dump completi enormi.
Devono congelare cio' che serve davvero a validare il comportamento.

```json
{
  "expected_fixture_id": "EXP-VM-002",
  "case_id": "VM-002",
  "expected_protocol": {
    "protocol_id": "PRT-002",
    "registry_id": "beginner_general_3x_tonificazione_full_body_v1",
    "status": "supported"
  },
  "canonical_expectations": {
    "split_family": "full_body_abc",
    "session_count": 3,
    "required_session_roles": ["full_body", "full_body", "full_body"],
    "required_pattern_buckets_weekly": {
      "push_h": 1,
      "push_v": 1,
      "pull_h": 1,
      "pull_v": 1,
      "squat": 2,
      "hinge": 2
    }
  },
  "draft_expectations": {
    "forbidden_demand_families": [
      "high_skill_upper",
      "ballistic_lower"
    ],
    "forbidden_exercise_tags": [
      "advanced_draft_exercise",
      "ballistic_beginner_draft"
    ],
    "max_skill_demand": 1,
    "max_ballistic_demand": 1,
    "max_impact_demand": 1
  },
  "analysis_expectations": {
    "min_score": 72,
    "allowed_warnings": [
      "quad_ham_low",
      "recovery_overlap_posterior"
    ],
    "forbidden_warnings": [
      "advanced_draft_exercise",
      "extreme_push_pull_imbalance"
    ],
    "max_muscles_below_mev": 1
  },
  "safety_expectations": {
    "max_avoid_top_1": 0,
    "allow_modify": true,
    "allow_caution": true
  }
}
```

---

## 9. Registry Index Schema v1

Il file `VALIDATION_MATRIX_INDEX.json` deve collegare tutte le fixture.

```json
{
  "validation_matrix_version": "v1",
  "cases": [
    {
      "case_id": "VM-001",
      "protocol_id": "PRT-001",
      "client_fixture_id": "CFG-A",
      "request_fixture_id": "RQ-VM-001",
      "expected_fixture_id": "EXP-VM-001"
    }
  ]
}
```

Questo file diventa la fonte unica del test harness.

---

## 10. Fixture Set Minimo v1

La prima release di fixture deve coprire almeno:

- `CFG-A` minimal beginner
- `CFG-B` beginner clinical low-skill
- `CFG-C` intermediate general
- `CFG-D` intermediate performance
- `CFG-E` advanced hypertrophy

E i 6 casi benchmark:

- `VM-001 -> CFG-A + RQ-VM-001 + EXP-VM-001`
- `VM-002 -> CFG-A + RQ-VM-002 + EXP-VM-002`
- `VM-003 -> CFG-C + RQ-VM-003 + EXP-VM-003`
- `VM-004 -> CFG-D + RQ-VM-004 + EXP-VM-004`
- `VM-005 -> CFG-E + RQ-VM-005 + EXP-VM-005`
- `VM-006 -> CFG-B + RQ-VM-006 + EXP-VM-006`

---

## 11. Cosa Congelare E Cosa No

### Da congelare

- protocol selection
- split family
- session count
- pattern bucket minimi
- warning families
- forbidden demand families
- ceiling di suitability
- score band minima

### Da non congelare integralmente in v1

- testo verbatim di ogni warning
- ordine completo di tutti i candidati oltre i top-3
- tutte le metriche secondarie dell'analyzer
- dettagli UI-only

Questo evita snapshot troppo fragili.

---

## 12. Golden Outputs v1

Per ogni `EXP-*`, i golden outputs devono stare su 3 livelli.

## 12.1 Protocol layer

- `protocol_id`
- `registry_id`
- `status`

## 12.2 Canonical layer

- split
- numero sessioni
- ruoli
- esposizioni minime attese

## 12.3 Draft/analysis layer

- ceiling demand
- famiglie vietate
- warning ammessi/vietati
- score minima

---

## 13. Fixture Evolution Policy

Le fixture non devono cambiare silenziosamente.

Ogni modifica a `CFG-*`, `RQ-*` o `EXP-*` richiede:

1. nuovo `UPG`
2. rationale esplicito
3. indicazione se il cambio e':
   - bugfix
   - scientific upgrade
   - protocol redesign

Questo e' necessario per auditabilita'.

---

## 14. Failure Semantics v1

Quando un caso fallisce, il harness deve poter dire quale fixture layer ha
rotto il contratto:

- `client_profile_resolution_failed`
- `protocol_selection_mismatch`
- `canonical_contract_mismatch`
- `draft_suitability_mismatch`
- `analysis_expectation_mismatch`
- `safety_expectation_mismatch`

Questo velocizza molto il debug scientifico.

---

## 15. Non-Goals del v1

Questa spec non definisce ancora:

- test Python concreti
- seeder automatico di fixture nel DB
- export/import fixture CLI
- benchmark statistici multi-run

Il v1 chiude il contratto dei dati, non ancora l'esecuzione automatica.

---

## 16. Roadmap Immediata

Dopo questa spec, i passi corretti sono:

1. `Evidence Registry v1`
   normalizzare davvero anchor, evidence class e rationale tags

2. `Catalog Mapping Spec v1`
   collegare `Demand Vector` agli esercizi del catalogo

3. `Runtime Translation Plan`
   introdurre i primi modelli backend reali per protocolli, vincoli e fixture

4. `Validation Harness Implementation v1`
   creare i test reali che leggono `VALIDATION_MATRIX_INDEX.json`

---

## 17. Fonti e Source Anchors

Le fixture non introducono nuove fonti.
Ereditano le fonti gia' dichiarate da:

- `SMART Scientific Method v1`
- `Protocol Definitions v1`
- `Demand Vector v1`
- `Validation Matrix v1`

Il loro compito e' congelare il comportamento atteso, non produrre nuova teoria.
