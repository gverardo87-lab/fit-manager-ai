# UPG-2026-03-07-57 — SMART Constraint Schema v1

> *"Un protocollo senza vincoli formali e' solo un'intenzione.
> Un protocollo con vincoli formali e' una macchina prescrittiva verificabile."*

**Data**: 2026-03-07  
**Stato**: ANALYSIS SPEC  
**Ambito**: SMART backend, KineScore, Protocol Engine  
**Dipende da**: `UPG-2026-03-07-55`, `UPG-2026-03-07-56`

---

## 1. Obiettivo

Definire il **Constraint Schema v1** del nuovo SMART/KineScore.

Questa spec traduce il metodo in una grammatica implementabile backend-side.
Non e' ancora codice runtime, ma e' pensata per diventare direttamente:

- modelli Python/Pydantic
- input del `Constraint Engine`
- contratto dei protocolli del `Protocol Registry`
- base del `Validation Harness`

---

## 2. Ruolo Del Constraint Schema

Nel modello target:

- il `Protocol Registry` dice **quale** protocollo e' attivo
- il `Constraint Schema` dice **con quali limiti** quel protocollo puo' generare
- il `Canonical Plan Engine` compone il piano
- il `Validation Harness` verifica che quei limiti siano rispettati

Questa separazione e' critica:

- il protocollo e' l'identita'
- il constraint schema e' il contratto tecnico

---

## 3. Principi di Design

### 3.1 Constraints are explicit

Ogni vincolo deve essere dichiarato, non implicito nel codice.

### 3.2 Constraints are typed

Ogni vincolo deve avere:

- tipo
- unita'
- severita'
- scope
- rationale
- source anchor

### 3.3 Constraints are machine-checkable

Ogni vincolo deve essere verificabile da codice, non solo “descritto”.

### 3.4 Constraints support graded enforcement

Non tutti i vincoli sono hard.
Servono almeno 3 livelli:

- `hard_fail`
- `soft_warning`
- `optimization_target`

### 3.5 Constraints are source-linked

Ogni famiglia di vincolo deve poter essere ricondotta a:

- fonte primaria
- razionale biomeccanico/clinico
- confidence/evidence grade

---

## 4. Constraint Taxonomy v1

Il Constraint Schema v1 e' composto da 8 blocchi:

1. `SessionConstraintSet`
2. `VolumeConstraintSet`
3. `FrequencyConstraintSet`
4. `BalanceConstraintSet`
5. `RecoveryConstraintSet`
6. `SuitabilityConstraintSet`
7. `ClinicalConstraintSet`
8. `ValidationContract`

Questi blocchi devono vivere insieme dentro ogni `ProtocolDefinition`.

---

## 5. Meta-Strutture Comuni

Prima dei blocchi specifici servono 3 meta-strutture riusabili.

## 5.1 ConstraintSeverity

```python
ConstraintSeverity = Literal[
    "hard_fail",
    "soft_warning",
    "optimization_target",
]
```

### Uso

- `hard_fail`
  il planner non puo' uscire con quel risultato

- `soft_warning`
  il risultato puo' esistere ma va segnalato

- `optimization_target`
  il sistema deve cercare di convergere verso quel target

## 5.2 ConstraintScope

```python
ConstraintScope = Literal[
    "slot",
    "session",
    "adjacent_sessions",
    "weekly_plan",
    "protocol",
    "draft_projection",
]
```

## 5.3 ConstraintRule Base

```python
ConstraintRule(
    rule_id: str,
    severity: ConstraintSeverity,
    scope: ConstraintScope,
    rationale: str,
    source_anchors: list[str],
    version: str,
)
```

Ogni regola specifica eredita da questa base.

---

## 6. SessionConstraintSet

Serve a controllare la struttura locale di ogni seduta.

### 6.1 Obiettivo

Evitare sedute:

- troppo dense
- troppo lunghe
- troppo mono-pattern
- troppo ricche di isolamento

### 6.2 Schema v1

```python
SessionConstraintSet(
    max_slots_per_session: int,
    max_isolation_slots_per_session: int,
    max_same_pattern_occurrences_per_session: int,
    max_primary_compounds_per_session: int,
    target_duration_min: int,
    upper_duration_tolerance_min: int,
    allowed_session_roles: list[str],
    required_pattern_buckets_by_role: dict[str, list[str]],
)
```

### 6.3 Esempi

- beginner full body:
  - `max_slots_per_session = 6`
  - `max_isolation_slots_per_session = 2`

- advanced 5x hypertrophy:
  - `max_slots_per_session = 8-10`
  - `max_isolation_slots_per_session = 4`

### 6.4 Razionale

- densita' eccessiva riduce qualita' tecnica
- troppe isolation in beginner degradano coerenza del protocollo
- la seduta deve riflettere il ruolo canonico assegnato

---

## 7. VolumeConstraintSet

Questo blocco collega il protocollo al modello `MEV/MAV/MRV`.

### 7.1 Obiettivo

Definire:

- dove il protocollo vuole stare rispetto alla MAV
- quali distretti hanno floor piu' rigido
- quali overage sono tollerabili

### 7.2 Schema v1

```python
VolumeConstraintSet(
    target_volume_zone: Literal["low_mav", "mid_mav", "high_mav"],
    critical_mev_floors: dict[str, float],
    preferred_mav_targets: dict[str, tuple[float, float]],
    allowed_excess_muscles: list[str],
    excess_tolerance_rules: dict[str, float],
    global_volume_cap_factor: float,
)
```

### 7.3 Significato dei campi

- `target_volume_zone`
  posizionamento medio del protocollo nel range MAV

- `critical_mev_floors`
  muscoli che non devono scendere sotto floor rigorosi

- `preferred_mav_targets`
  sotto-range preferito di volume per protocollo

- `allowed_excess_muscles`
  distretti dove un eccesso moderato puo' essere tollerato

- `global_volume_cap_factor`
  limite globale protocollo-specifico sul volume totale

### 7.4 Esempi

- beginner general 3x:
  - `target_volume_zone = low_mav`
  - cap conservativo

- advanced hypertrophy 5x:
  - `target_volume_zone = high_mav`
  - cap piu' alto

### 7.5 Rationale scientifico

- Israetel / RP 2020
- Schoenfeld 2017
- NSCA 2016

---

## 8. FrequencyConstraintSet

Questo blocco definisce la minima esposizione utile e la massima frequenza tollerata.

### 8.1 Obiettivo

Evitare sia:

- muscoli “presenti ma non davvero stimolati”
- frequenze incompatibili con il livello

### 8.2 Schema v1

```python
FrequencyConstraintSet(
    session_stimulus_threshold: float,
    muscle_frequency_floor: dict[str, int],
    pattern_frequency_floor: dict[str, int],
    muscle_frequency_cap: dict[str, int],
    weekly_split_frequency_cap: int,
    direct_accessory_floor: dict[str, int],
)
```

### 8.3 Significato

- `session_stimulus_threshold`
  soglia minima per considerare “vera esposizione” di un muscolo in una seduta

- `muscle_frequency_floor`
  numero minimo di sedute/settimana per muscolo

- `pattern_frequency_floor`
  esposizione minima per pattern motori chiave

- `direct_accessory_floor`
  minima presenza diretta di accessori selezionati

### 8.4 Esempio

`PRT-002 beginner_general_3x_tonificazione_full_body_v1`

- piccoli distretti come deltoide laterale e polpacci:
  `floor >= 2`

### 8.5 Fonti

- Schoenfeld 2016
- NSCA 2016

---

## 9. BalanceConstraintSet

Questo blocco formalizza i range biomeccanici del protocollo.

### 9.1 Obiettivo

Dire chiaramente:

- quali ratio sono essenziali
- con quale tolleranza
- con quale priorita'

### 9.2 Schema v1

```python
BalanceConstraintSet(
    ratio_targets: dict[str, float],
    ratio_bands: dict[str, tuple[float, float]],
    ratio_priority: list[str],
    ratio_severity: dict[str, ConstraintSeverity],
)
```

### 9.3 Ratio v1 minimi

- `push_pull`
- `push_horizontal_vertical`
- `pull_horizontal_vertical`
- `quad_ham`
- `anterior_posterior`

### 9.4 Esempio di severita'

- `push_pull`: `soft_warning`
- `push_horizontal_vertical`: `optimization_target`
- `quad_ham`: `soft_warning` o `hard_fail` nei protocolli clinical-specific

### 9.5 Rationale

- NSCA
- Sahrmann
- Alentorn-Geli

---

## 10. RecoveryConstraintSet

Questo blocco rappresenta il costo sistemico e locale del microciclo.

### 10.1 Obiettivo

Evitare overlap non accettabili su:

- posterior chain
- trapezio/scapole
- core
- axial load

### 10.2 Schema v1

```python
RecoveryConstraintSet(
    adjacent_overlap_caps: dict[str, float],
    weekly_load_budgets: dict[str, float],
    max_high_stress_sessions_in_row: int,
    posterior_chain_budget: float,
    scapular_complex_budget: float,
    axial_load_budget: float,
)
```

### 10.3 Significato

- `adjacent_overlap_caps`
  massimo overlap accettato tra sedute contigue per sistemi sensibili

- `weekly_load_budgets`
  budget cumulativi protocollo-specifici

- `max_high_stress_sessions_in_row`
  protezione anti-densita'

### 10.4 Nota importante

In v1 il recovery model puo' partire da proxy muscolari.
In v2 deve agganciarsi al `demand vector`.

---

## 11. SuitabilityConstraintSet

Questo blocco e' il ponte tra canonico e draft.

### 11.1 Obiettivo

Stabilire quando un candidato:

- e' pienamente ammissibile
- e' sconsigliato
- e' infeasible per l'auto-draft

### 11.2 Schema v1

```python
SuitabilityConstraintSet(
    max_skill_demand: str,
    max_coordination_demand: str,
    max_ballistic_demand: str,
    max_impact_demand: str,
    excluded_auto_draft_families: list[str],
    discouraged_families: list[str],
    preferred_families: list[str],
    allow_advanced_exercises_in_draft: bool,
)
```

### 11.3 Esempi

Beginner general:

- `max_skill_demand = low`
- `max_ballistic_demand = low`
- `allow_advanced_exercises_in_draft = False`
- `excluded_auto_draft_families = ["jump", "muscle_up", "weighted_pullup"]`

Advanced performance:

- piu' permissivo
- ma comunque no ballistic inutile fuori contesto

### 11.4 Punto chiave

Questo blocco deve diventare piu' forte del rank score.

Un `muscle-up` non deve perdere “per poco”.
Deve risultare `infeasible_for_auto_draft` nel protocollo beginner, salvo override esplicito.

---

## 12. ClinicalConstraintSet

Questo blocco collega il protocollo al KineShield / Safety Engine.

### 12.1 Obiettivo

Tradurre il mode clinico in vincoli strutturali, non solo in warning.

### 12.2 Schema v1

```python
ClinicalConstraintSet(
    safety_mode: Literal["none", "overlay", "dominant"],
    avoid_families_when_conditioned: list[str],
    modify_families_when_conditioned: list[str],
    force_low_skill_auto_draft: bool,
    require_clinical_rationale_in_draft: bool,
)
```

### 12.3 Significato

- `overlay`
  la safety informa ma non domina il protocollo

- `dominant`
  la safety entra nella feasibility e restringe il draft automatico

### 12.4 Nota

Questo non trasforma SMART in dispositivo medico.
Trasforma pero' la modalita' `clinical` in un protocollo piu' prudente e spiegabile.

---

## 13. ValidationContract

Questo blocco lega il protocollo al validation harness.

### 13.1 Obiettivo

Definire cosa significa “protocollo riuscito”.

### 13.2 Schema v1

```python
ValidationContract(
    minimum_composite_score: int,
    forbidden_warnings: list[str],
    tolerated_warnings: dict[str, int],
    required_case_ids: list[str],
    snapshot_tolerance: dict[str, float],
)
```

### 13.3 Esempio

Per un beginner general 3x:

- warning non ammessi:
  - `advanced_draft_exercise`
  - `push_h_pull_v_extreme_imbalance`

- warning tollerabili entro budget:
  - `quad_ham_low`
  - `posterior_chain_overlap`

Questo permette di trattare il protocollo come entita' verificabile.

---

## 14. Constraint Resolution Model

Serve anche definire come i vincoli interagiscono tra loro.

### 14.1 Ordine consigliato v1

1. `SessionConstraintSet`
2. `SuitabilityConstraintSet`
3. `ClinicalConstraintSet`
4. `VolumeConstraintSet`
5. `FrequencyConstraintSet`
6. `BalanceConstraintSet`
7. `RecoveryConstraintSet`
8. `ValidationContract`

### 14.2 Razionale

- prima si limita lo spazio delle soluzioni
- poi si costruisce il piano
- infine si valuta la qualita'

Questo riduce il comportamento patch-like.

---

## 15. Mapping a Runtime Modules

Questa spec implica i seguenti moduli target:

- `constraint_types.py`
- `constraint_engine.py`
- `constraint_evaluator.py`
- `constraint_messages.py`

### 15.1 constraint_types.py

Contiene i modelli dei blocchi.

### 15.2 constraint_engine.py

Materializza i vincoli del protocollo selezionato.

### 15.3 constraint_evaluator.py

Controlla canonico e draft rispetto ai vincoli.

### 15.4 constraint_messages.py

Traduce fail/warning in messaggi scientificamente consistenti.

---

## 16. Esempio Completo — PRT-002

Per `beginner_general_3x_tonificazione_full_body_v1` il constraint schema v1 dovrebbe portare almeno:

- `max_slots_per_session = 6`
- `max_isolation_slots_per_session = 2`
- `target_volume_zone = low_mav`
- `session_stimulus_threshold = 2.0`
- `muscle_frequency_floor["deltoide_laterale"] = 2`
- `muscle_frequency_floor["polpacci"] = 2`
- `allow_advanced_exercises_in_draft = False`
- `excluded_auto_draft_families = ["jump", "muscle_up"]`
- posterior chain overlap cap conservativo
- validation contract con divieto assoluto di `advanced_draft_exercise`

Questo rende il protocollo implementabile senza nuove euristiche ad hoc.

---

## 17. Anti-Pattern Da Vietare

- hardcodare il significato di un vincolo in `plan_builder.py`
- lasciare che il ranker scopra da solo cosa e' ammissibile
- usare stringhe warning come unico sistema di controllo
- introdurre ratio o budgets senza definirne:
  - unita'
  - severita'
  - scope
  - source anchor

---

## 18. Prossimo Deliverable

Dopo il `Constraint Schema v1`, il passo giusto e':

1. definire i **Protocol Definitions v1** per `PRT-001 ... PRT-006`
2. poi modellare il **Demand Vector v1**
3. solo dopo entrare in implementazione runtime

---

## 19. Sintesi

Il `Constraint Schema v1` e' il punto in cui SMART smette di essere governato da “fix” e inizia a essere governato da:

- oggetti tipizzati
- vincoli verificabili
- livelli di severita'
- scope espliciti
- legame con fonti e validazione

Questa e' la base minima per un backend scientificamente deterministico, dimostrabile e coerente con l'ambizione KineScore.
