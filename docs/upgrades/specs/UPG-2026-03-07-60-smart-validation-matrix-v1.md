# UPG-2026-03-07-60 - SMART Validation Matrix v1

> *"Un protocollo non e' scientificamente difendibile solo perche' e' ben scritto.
> Lo diventa quando fallisce sempre negli stessi punti e passa sempre negli stessi casi."*

**Data**: 2026-03-07  
**Stato**: HARNESS IMPLEMENTED — Benchmark fixtures e check functions pronti, matrice non ancora eseguita su dati reali
**Ambito**: SMART backend, KineScore, Protocol Engine, Validation Harness  
**Dipende da**: `UPG-2026-03-07-55`, `UPG-2026-03-07-56`, `UPG-2026-03-07-57`, `UPG-2026-03-07-58`, `UPG-2026-03-07-59`

---

## 1. Obiettivo

Definire la `Validation Matrix v1` del nuovo SMART/KineScore.

Questa spec stabilisce:

- quali casi benchmark devono esistere
- quali invarianti devono essere verificati
- quali output devono essere congelati
- quali tolleranze sono ammesse
- quando una release scientifica puo' essere dichiarata valida

Il focus non e' il testing tecnico generico, ma la validazione
scientifico-prescrittiva del motore.

---

## 2. Ruolo Della Validation Matrix

Nel modello target:

- il `Protocol Registry` definisce le famiglie supportate
- il `Constraint Schema` definisce i limiti
- il `Demand Vector` definisce il costo biomeccanico degli esercizi
- la `Validation Matrix` dimostra che il sistema produce output coerenti

Senza questo layer:

- i protocolli restano descrizioni
- i vincoli restano intenzioni
- il planner resta difficile da difendere

Con questo layer:

- il comportamento atteso e' congelato
- le regressioni scientifiche diventano visibili
- la base per audit, pubblicazione e IP si rafforza

---

## 3. Principi Di Design

### 3.1 Determinismo first

Stesso input validato -> stesso protocollo, stesso canonico, stesso draft,
stessi warning attesi.

### 3.2 Validation by protocol, not by anecdote

La matrice deve essere organizzata per protocollo supportato, non per bug spot.

### 3.3 Multi-layer validation

Ogni caso deve validare:

- protocol selection
- canonical plan
- draft suitability
- analyzer output
- safety overlay

### 3.4 Evidence-aware tolerance

Non tutto deve essere snapshot esatto.
Serve distinguere:

- invarianti hard
- snapshot stabili
- range di tolleranza

### 3.5 Release-gated

Una release scientifica SMART non e' promuovibile se rompe la matrice.

---

## 4. Struttura Del Validation Harness v1

La matrice deve essere pensata per vivere in:

`tests/training_science/validation_matrix/`

Con almeno questi elementi:

- `fixtures/clients/`
- `fixtures/protocol_inputs/`
- `fixtures/expected_outputs/`
- `test_protocol_selection.py`
- `test_canonical_invariants.py`
- `test_draft_suitability.py`
- `test_analysis_contract.py`
- `test_clinical_overlay.py`

Nel v1 questa e' ancora una spec, non una patch runtime.

---

## 5. Unita' Di Validazione

Ogni riga della matrice deve rappresentare un `ValidationCase`.

```python
ValidationCase(
    case_id: str,
    protocol_id: str,
    client_fixture_id: str,
    request_fixture_id: str,
    expected_status: str,
    expected_protocol_registry_id: str,
    invariant_checks: list[str],
    snapshot_checks: list[str],
    tolerance_checks: list[str],
    forbidden_warnings: list[str],
    required_warnings: list[str],
    notes: str,
)
```

---

## 6. Tipi Di Check

## 6.1 Invariant checks

Check che non possono fallire.

Esempi:

- protocollo selezionato corretto
- split family corretta
- nessun esercizio auto-draft oltre i ceiling del protocollo
- nessun `advanced_draft_exercise` nei beginner
- nessun violazione hard del `Constraint Schema`

## 6.2 Snapshot checks

Check che devono restare stabili salvo upgrade scientifico esplicito.

Esempi:

- session roles
- pattern exposure per sessione
- famiglie di warning attese
- demand family dei top candidate

## 6.3 Tolerance checks

Check ammessi entro range dichiarato.

Esempi:

- score composito
- totale serie/sett
- ratio biomeccanici entro fascia protocollo
- overlap recovery score

---

## 7. Matrice Minima v1

La `Validation Matrix v1` deve coprire almeno un caso benchmark per ciascuno
dei protocolli supportati `PRT-001 ... PRT-006`.

## 7.1 VM-001

- `case_id`: `VM-001`
- `protocol_id`: `PRT-001`
- `registry_id`: `beginner_general_2x_tonificazione_full_body_v1`
- focus:
  - selezione protocollo base beginner 2x
  - assenza di esercizi advanced
  - volume in `low_mav`
  - nessun ballistic/impact fuori policy

## 7.2 VM-002

- `case_id`: `VM-002`
- `protocol_id`: `PRT-002`
- `registry_id`: `beginner_general_3x_tonificazione_full_body_v1`
- focus:
  - rotazione `full_body_abc`
  - controllo frequenza piccoli distretti
  - no `muscle-up`, no `box jump` nel draft
  - recovery overlap sotto soglia protocollo

## 7.3 VM-003

- `case_id`: `VM-003`
- `protocol_id`: `PRT-003`
- `registry_id`: `intermediate_general_4x_ipertrofia_upper_lower_v1`
- focus:
  - split `upper_lower`
  - `mid/high_mav`
  - ratio push/pull dentro banda
  - suitability non beginner-gated ma ancora non performance-extreme

## 7.4 VM-004

- `case_id`: `VM-004`
- `protocol_id`: `PRT-004`
- `registry_id`: `intermediate_performance_3x_forza_full_body_v1`
- focus:
  - strength bias reale
  - compound priority
  - intensita' tecnico-neuromuscolare piu' alta
  - demand ceilings performance ma non advanced specialist

## 7.5 VM-005

- `case_id`: `VM-005`
- `protocol_id`: `PRT-005`
- `registry_id`: `advanced_performance_5x_ipertrofia_upper_lower_plus_v1`
- focus:
  - volume alto controllato
  - densita' avanzata
  - suitability advanced ammessa
  - recovery budgets piu' permissivi ma non incoerenti

## 7.6 VM-006

- `case_id`: `VM-006`
- `protocol_id`: `PRT-006`
- `registry_id`: `beginner_clinical_3x_tonificazione_full_body_low_skill_v1`
- focus:
  - low-skill hard gating
  - low-impact / low-ballistic
  - clinical overlay dominante rispetto al general beginner
  - draft con costo scapolo-omerale/lombare contenuto

---

## 8. Client Fixture Classes

Per evitare benchmark finti, la matrice deve usare fixture cliente tipizzate.

### 8.1 CFG-A Minimal beginner

- anamnesi legacy
- dati parziali
- nessuna specializzazione
- profilo general beginner

### 8.2 CFG-B Beginner clinical low-skill

- anamnesi strutturata
- sensibilita' spalla/lombare o profilo low-impact
- candidabile a `PRT-006`

### 8.3 CFG-C Intermediate general

- dati sufficienti
- buona tolleranza al carico
- nessun vincolo clinical dominante

### 8.4 CFG-D Intermediate performance

- forza relativa o obiettivo esplicito performance
- readiness adeguata

### 8.5 CFG-E Advanced hypertrophy

- alta tolleranza volume
- contesto performance
- nessun gate beginner/clinical

---

## 9. Request Fixture Classes

Ogni caso deve separare il cliente dal `request envelope`.

Campi minimi:

- `frequenza`
- `obiettivo_builder`
- `livello_choice`
- `mode`
- `trainer_overrides`

Questo permette di distinguere:

- errore del resolver profilo
- errore del protocol selector
- errore del planner
- errore del ranker

---

## 10. Invarianti Minimi Obbligatori

Questi invarianti devono valere su tutta la matrice v1.

### 10.1 Protocol selection invariants

- il protocollo selezionato deve essere quello atteso
- nessuna cella `unsupported_by_policy` puo' auto-risolversi in supported

### 10.2 Canonical invariants

- split family coerente con il protocollo
- numero sessioni coerente con `frequenza`
- ruoli di sessione coerenti con il protocollo
- nessun superamento dei `hard_fail` del `Constraint Schema`

### 10.3 Draft suitability invariants

- beginner: nessun auto-draft `advanced`
- beginner clinical: nessun auto-draft con `ballistic > 0` o `impact > 0`
  se il protocollo lo vieta
- nessun esercizio con demand oltre i ceiling del protocollo
- nessun draft che violi i family gate espliciti

### 10.4 Analyzer invariants

- nessun warning hard non previsto
- ratio biomeccanici dentro le bande tollerate dal protocollo
- numero di muscoli sotto `MEV` sotto la soglia del protocollo

### 10.5 Safety invariants

- nessun esercizio `avoid` puo' finire top-1 se esiste una alternativa
  protocol-compatible non `avoid`
- i conteggi `avoid / modify / caution` devono essere stabili a parita' di input

---

## 11. Warning Policy v1

La matrice deve distinguere:

- `required_warnings`
- `allowed_warnings`
- `forbidden_warnings`

Esempio per `PRT-002`:

- `required_warnings`
  - nessuno obbligatorio in condizioni ideali

- `allowed_warnings`
  - moderato `quad_ham_low`
  - moderato `recovery_overlap_posterior`

- `forbidden_warnings`
  - `advanced_draft_exercise`
  - `extreme_push_pull_imbalance`
  - `ballistic_beginner_draft`

Questo impedisce che i warning vengano letti in modo troppo binario.

---

## 12. Score Policy v1

Il punteggio composito non deve essere validato come numero assoluto fisso
senza contesto.

Serve una policy a bande:

- beginner general 2x:
  `score >= 70`

- beginner general 3x:
  `score >= 72`

- intermediate general 4x:
  `score >= 78`

- intermediate performance 3x forza:
  `score >= 78`

- advanced performance 5x:
  `score >= 80`

- beginner clinical 3x:
  `score >= 75`

Oltre alla soglia minima, il test deve controllare che:

- il breakdown per dimensione non collassi
- un miglioramento di score non derivi da un draft biomeccanicamente peggiore

---

## 13. Output Congelati v1

Per ogni caso benchmark v1 devono essere congelati almeno:

- `scientific_profile`
- `protocol_id`
- `canonical_plan`
- `top_3_candidates_per_slot`
- `workout_projection`
- `analysis_summary`
- `warning_set`

Non tutto deve essere snapshot verbatim.
Ma questi layer devono avere rappresentazioni testabili.

---

## 14. Failure Semantics

Quando la matrice fallisce, il motivo deve essere classificato.

### 14.1 Failure classes

- `protocol_selection_regression`
- `constraint_violation`
- `draft_suitability_regression`
- `analysis_regression`
- `clinical_overlay_regression`
- `score_regression`

Questo e' essenziale per evitare debug ambiguo.

---

## 15. Release Gate v1

Una release SMART/KineScore puo' essere dichiarata valida solo se:

1. tutti gli invariant checks passano
2. nessun `forbidden_warning` appare nei casi benchmark
3. i tolerance checks restano dentro le bande approvate
4. ogni caso supportato `PRT-001 ... PRT-006` ha un benchmark verde
5. eventuali cambi attesi sono accompagnati da nuovo `UPG` e nuova baseline

Questo e' il primo vero gate di dimostrabilita' del metodo.

---

## 16. Roadmap Immediata

Dopo questa spec, i passi corretti sono:

1. `Catalog Mapping Spec v1`
   come assegnare `Demand Vector` e `demand_family` a ogni esercizio

2. `Runtime Translation Plan`
   tradurre protocolli, vincoli e demand vector in modelli backend veri

3. `Validation Fixtures v1`
   creare i primi fixture congelati `CFG-A ... CFG-E` e `VM-001 ... VM-006`

4. `Evidence Registry v1`
   chiudere source anchors ed evidence classes in un registro unico

---

## 17. Fonti e Source Anchors v1

La `Validation Matrix v1` eredita gli anchor gia' formalizzati nel metodo e nei
protocolli:

- `NSCA-2016`
- `ACSM-2009`
- `SCHOENFELD-2016`
- `SCHOENFELD-2017`
- `ISRAETEL-2020`
- `HELMs-2019`
- `SAHRMANN-2002`
- `ALENTORN-GELI-2009`

La matrice non aggiunge nuove fonti operative.
Serve a rendere verificabile e congelato l'uso delle fonti gia' dichiarate.

---

## 18. Implementation Status (aggiornato 2026-03-07)

### Harness implementato (UPG-70)

Il validation harness vive in `api/services/training_science/validation/`:

| File | LOC | Contenuto |
|------|-----|-----------|
| `validation_catalog.py` | ~275 | 6 ValidationCase (VM-001..006) + 5 ClientFixture (CFG-A..E) + 6 RequestFixture (RFX-001..006) |
| `validation_contracts.py` | ~400 | 7 invariant + 7 snapshot + 8 tolerance check + warning policy + runner |
| `__init__.py` | ~40 | Re-export pubblico |

### Check implementati

**Invariant (7)**: protocol_selection_correct, split_family_correct, no_advanced_draft_exercise,
no_ceiling_exceeded, no_hard_constraint_fail, no_ballistic_impact_draft, demand_shoulder_lumbar_contained

**Snapshot (7)**: session_count_matches_frequenza, session_roles_full_body, session_roles_upper_lower,
pattern_exposure_balanced, compound_priority_high, advanced_suitability_allowed, clinical_overlay_dominant

**Tolerance (8)**: score_above_band, push_pull_ratio_in_band, volume_in_low_mav, volume_in_mid_high_mav,
volume_high_controlled, volume_conservative, recovery_overlap_below_threshold, strength_bias_present

### Smoke test (sintetico)

VM-001 (PRT-001 beginner 3x): 12/12 check pass con package sintetico.

### Prossimi passi

- Esecuzione con plan-package reale (endpoint `/training-science/plan-package`)
- Congelamento output baseline per snapshot regression
- Integrazione in CI come gate scientifico pre-release
