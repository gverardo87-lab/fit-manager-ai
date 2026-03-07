# UPG-2026-03-07-56 — SMART Protocol Registry v1

> *"Il rigore non nasce dal gestire tutte le combinazioni.
> Nasce dal dichiarare con precisione quali combinazioni sono supportate,
> quali sono vietate e quali richiedono evidenza aggiuntiva."*

**Data**: 2026-03-07  
**Stato**: ANALYSIS SPEC  
**Ambito**: SMART backend, KineScore, Protocol Engine  
**Dipende da**: `UPG-2026-03-07-55`

---

## 1. Obiettivo

Formalizzare il primo `Protocol Registry` del nuovo SMART/KineScore.

Questa spec non implementa ancora il motore runtime, ma definisce:

- la forma dei protocolli
- la politica di supporto della matrice
- le prime celle ufficiali
- i vincoli minimi che ogni protocollo deve dichiarare
- i casi che il sistema deve rifiutare per rigore scientifico

---

## 2. Principio Fondante

Il registry non serve a “contenere preset”.
Serve a dichiarare in modo verificabile:

- cosa SMART sa fare in modo scientificamente difendibile
- in quali condizioni
- con quali limiti
- con quale livello di evidenza

Quindi il registry deve supportare anche la risposta:

- `supported`
- `unsupported_by_policy`
- `clinical_only`
- `research_only`

Questa e' una scelta fondamentale di rigore.

---

## 3. Protocol Status Model

Ogni cella della matrice deve avere uno `status`.

### 3.1 Stati ammessi

- `supported`
  Protocollo pronto per generazione automatica standard.

- `clinical_only`
  Protocollo disponibile solo in `mode=clinical` o con vincoli rafforzati.

- `research_only`
  Protocollo sperimentale, non adatto a produzione standard.

- `unsupported_by_policy`
  Protocollo che il sistema rifiuta per limiti di evidenza o di sicurezza progettuale.

### 3.2 Esempio importante

`beginner 5x forza performance`

non deve produrre un piano “adattato in qualche modo”.
Deve probabilmente risultare:

- `unsupported_by_policy`

con razionale chiaro:

- oltre i frequency clamp del livello
- densita' / fatica non coerente con beginner
- insufficiente base di tolleranza tecnica

Questo e' molto piu' forte scientificamente di un fallback nascosto.

---

## 4. Shape del Protocol Registry

Nuovo layer target:

`api/services/training_science/protocol_registry.py`

### 4.1 Schema concettuale

Ogni protocollo deve avere almeno:

```python
ProtocolDefinition(
    protocol_id: str,
    status: Literal[
        "supported",
        "clinical_only",
        "research_only",
        "unsupported_by_policy",
    ],
    version: str,
    mode: Literal["general", "performance", "clinical"],
    livello: Literal["beginner", "intermedio", "avanzato"],
    frequenza: int,
    obiettivo: Literal["forza", "ipertrofia", "tonificazione", "resistenza", "dimagrimento"],
    split_family: str,
    canonical_template: str,
    evidence_profile: str,
    population_scope: str,
    entry_criteria: list[str],
    exclusion_criteria: list[str],
    session_constraints: SessionConstraintSet,
    volume_constraints: VolumeConstraintSet,
    frequency_constraints: FrequencyConstraintSet,
    balance_constraints: BalanceConstraintSet,
    recovery_constraints: RecoveryConstraintSet,
    suitability_constraints: SuitabilityConstraintSet,
    accessory_policy: AccessoryPolicy,
    validation_contract: ValidationContract,
    source_anchors: list[str],
)
```

### 4.2 Regola architetturale

Il `plan_builder` non deve piu' ragionare “solo” da:

- livello
- frequenza
- obiettivo

ma da:

- `protocol definition`

Questo sposta la logica da euristica implicita a contratto esplicito.

---

## 5. Vincoli Minimi di Ogni Protocollo

Ogni protocollo v1 deve dichiarare almeno 7 famiglie di vincoli.

### 5.1 Session Constraints

- `max_slots_per_session`
- `max_isolation_per_session`
- `allowed_split_families`
- `allowed_session_roles`
- `distribution_pattern` tra sessioni

### 5.2 Volume Constraints

- modello volume di riferimento
- muscoli critici con `floor`
- muscoli da non eccedere
- politica di overage tollerato

### 5.3 Frequency Constraints

- `freq_min` per muscolo/pattern
- `freq_max` per livello
- soglia di `true session stimulus`

### 5.4 Balance Constraints

- range accettabile per ratio biomeccanici
- priorita' tra i ratio

### 5.5 Recovery Constraints

- overlap massimo tra sessioni contigue
- budget per posterior chain
- budget per scapular/trap load
- budget per core/axial load

### 5.6 Suitability Constraints

- skill demand massimo
- ballistic/impact demand massimo
- categorie/famiglie sconsigliate
- exercise families escluse dall'auto-draft

### 5.7 Validation Contract

- score minimo atteso
- warning ammessi
- warning non ammessi
- benchmark cases da passare

---

## 6. Politica di Supporto v1 della Matrice

La matrice teorica e':

- 3 livelli
- 5 frequenze
- 5 obiettivi
- 3 mode

Totale teorico: 225 celle.

Questo **non significa** che 225 protocolli debbano essere attivi in v1.

### 6.1 Scelta scientificamente rigorosa

In v1 il sistema deve distinguere:

- celle ufficialmente supportate
- celle rifiutate
- celle future

### 6.2 Regole v1 di support policy

#### Beginner

- `2x`, `3x`: supportabili
- `4x+`: non supportati di default in `general`
- `4x` puo' esistere solo come `clinical_only` o `research_only` in fasi future, non in v1

#### Intermedio

- `3x`, `4x`, `5x`: supportabili
- `2x`: supportabile ma con copertura piu' limitata
- `6x`: non supportato in v1 general, possibile `research_only`

#### Avanzato

- `4x`, `5x`, `6x`: supportabili
- `3x`: supportabile per certi obiettivi
- `2x`: fuori focus SMART v1 ad alta specificita'

### 6.3 Implicazione forte

Il registry v1 non deve cercare di coprire tutto.
Deve coprire **poche celle molto bene**.

---

## 7. Prime Celle Ufficiali del Registry v1

Queste sono le prime 6 celle consigliate come base formale.

## 7.1 PRT-001

### `beginner_general_2x_tonificazione_full_body_v1`

**Status**: `supported`

**Uso**
- onboarding standard
- clienti con profilo dati parziale
- bassa tolleranza al carico

**Split**
- `full_body`

**Vincoli chiave**
- max 5 slot/seduta
- max 2 isolation/seduta
- almeno 1 push, 1 pull, 1 knee dominant, 1 hip dominant per settimana
- no ballistic/skill auto-draft
- recovery overlap conservativo

**Target**
- volume basso-moderato
- focus su aderenza, tecnica e tolleranza

---

## 7.2 PRT-002

### `beginner_general_3x_tonificazione_full_body_v1`

**Status**: `supported`

**Uso**
- protocollo core beginner SMART

**Split**
- `full_body A/B/C`

**Vincoli chiave**
- max 6 slot/seduta
- max 2 isolation/seduta
- `freq >= 2x` per piccoli distretti selezionati
- push_h/push_v e pull_h/pull_v bilanciati
- no `advanced`, no `jump/plyo/skill` in auto-draft
- posterior chain overlap limitato su B->C

**Target**
- tonificazione generalista, controllo tecnico, moderata copertura totale

---

## 7.3 PRT-003

### `intermediate_general_4x_ipertrofia_upper_lower_v1`

**Status**: `supported`

**Uso**
- protocollo core ipertrofia intermedio general

**Split**
- `upper/lower`

**Vincoli chiave**
- distribuzione U/L/U/L
- `freq >= 2x` per gruppi principali
- volume ipertrofico vicino al centro MAV
- balance ratios dentro tolleranza standard
- recovery meno conservativo del beginner

**Target**
- primo protocollo “mainstream hypertrophy” serio e stabile

---

## 7.4 PRT-004

### `intermediate_performance_3x_forza_full_body_v1`

**Status**: `supported`

**Uso**
- forza general/performance con frequenza moderata

**Split**
- `full_body strength-bias`

**Vincoli chiave**
- slot principali orientati a compound
- density piu' bassa, rest piu' alto
- isolation minimizzata
- skill demand ammessa fino a `intermediate`
- no high-impact non necessario

**Target**
- sviluppo forza senza entrare in powerlifting specialistico

---

## 7.5 PRT-005

### `advanced_performance_5x_ipertrofia_upper_lower_plus_v1`

**Status**: `supported`

**Uso**
- ipertrofia avanzata ad alto volume, ma ancora tracciabile

**Split**
- `upper/lower/upper/lower/upper`

**Vincoli chiave**
- volume vicino a MAV alto
- fatigue budget esplicito
- suitability puo' accettare `advanced` ma non ballistic inutile
- accessory specialization consentita

**Target**
- protocollo avanzato ad alta densita' ma non ancora 6x specialistico

---

## 7.6 PRT-006

### `beginner_clinical_3x_tonificazione_full_body_low_skill_v1`

**Status**: `clinical_only`

**Uso**
- profili con anamnesi legacy/structured e necessità di basso rischio

**Split**
- `full_body`

**Vincoli chiave**
- auto-draft solo low-skill / low-impact
- bias conservativo su shoulder complex, axial load, ballistic demand
- recovery piu' conservativo di `PRT-002`
- safety overlay dominante nella feasibility

**Target**
- protocollo clinic-aware, non rehab medica, ma chinesiologicamente prudente

---

## 8. Celle Da Rifiutare Gia' in v1

Per alzare il rigore, il registry deve dichiarare esempi di combinazioni non ammesse.

### 8.1 Esempi

- `beginner_general_5x_forza_*`
- `beginner_general_6x_ipertrofia_*`
- `beginner_performance_6x_*`
- `intermediate_general_6x_*`

### 8.2 Razionale

- incompatibilita' con frequency clamp e tolleranza del livello
- recovery demand troppo alta
- assenza di validazione sufficiente
- rischio di far degenerare SMART in “generator permissivo”

Questo deve essere un comportamento voluto, non un limite imbarazzante.

---

## 9. Constraint Template v1

Ogni protocollo v1 dovrebbe concretizzare questi blocchi.

## 9.1 SessionConstraintSet

- `max_slots_per_session`
- `max_isolation_per_session`
- `max_same_pattern_per_session`
- `session_duration_target_min`

## 9.2 VolumeConstraintSet

- `target_volume_zone`: `low_mav` | `mid_mav` | `high_mav`
- `critical_mev_floors`
- `allowed_excess_muscles`

## 9.3 FrequencyConstraintSet

- `session_stimulus_threshold`
- `muscle_freq_floor`
- `pattern_freq_floor`

## 9.4 BalanceConstraintSet

- `push_pull_upper_bound`
- `push_horizontal_vertical_band`
- `pull_horizontal_vertical_band`
- `quad_ham_band`
- `anterior_posterior_band`

## 9.5 RecoveryConstraintSet

- `posterior_chain_overlap_cap`
- `trapezius_overlap_cap`
- `core_overlap_cap`
- `axial_load_session_cap`

## 9.6 SuitabilityConstraintSet

- `max_skill_demand`
- `max_ballistic_demand`
- `max_impact_demand`
- `excluded_auto_draft_families`
- `preferred_equipment_families`

---

## 10. Relazione con KineScore Validation Suite

Ogni protocollo v1 deve avere un contratto di validazione esplicito.

### 10.1 ValidationContract minimo

- `minimum_composite_score`
- `forbidden_warnings`
- `expected_warning_budget`
- `required_case_ids`
- `snapshot_tolerance`

### 10.2 Esempio

Per `PRT-002`:

- non ammessi warning su:
  - `push_h : push_v`
  - `pull_h : pull_v`
  - `advanced draft suitability`
- warning tollerabili ma da contenere:
  - `Quad : Ham`
  - posterior-chain overlap

Questo rende ogni protocollo auditabile.

---

## 11. Implicazioni di Implementazione

Quando il registry entrera' nel codice, il flow corretto dovra' essere:

1. `protocol_selector` sceglie la cella
2. il sistema controlla lo `status`
3. se `unsupported_by_policy`, restituisce rifiuto spiegabile
4. se `supported` o `clinical_only`, carica il contratto del protocollo
5. `constraint_engine` costruisce i bounds
6. `plan_builder` compone il canonico dentro quei bounds
7. `ranker` seleziona solo candidati feasible
8. `validation_harness` verifica il contratto

---

## 12. Prossimo Deliverable Consigliato

Dopo questa spec il passo corretto e':

1. `Constraint Schema v1`
2. `Protocol Definitions v1` per `PRT-001 ... PRT-006`
3. solo dopo, implementazione runtime del selettore protocolli

---

## 13. Sintesi

Il `Protocol Registry v1` e' il punto in cui SMART smette di essere un planner che “fa del suo meglio” e comincia a diventare un sistema che dichiara:

- cosa sa fare
- cosa non sa fare
- con quali limiti
- con quali fonti
- con quali test

Questo e' il vero fondamento di un metodo scientifico dimostrabile e coerente con l'ambizione KineScore.
