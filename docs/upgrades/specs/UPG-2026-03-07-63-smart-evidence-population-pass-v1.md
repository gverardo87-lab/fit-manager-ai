# UPG-2026-03-07-63 - SMART Evidence Population Pass v1

> *"Un registro vuoto e' architettura.
> Un registro popolato e' inizio di metodo scientifico operativo."*

**Data**: 2026-03-07  
**Stato**: ANALYSIS SPEC  
**Ambito**: SMART backend, KineScore, Evidence Registry, Protocol Governance  
**Dipende da**: `UPG-2026-03-07-58`, `UPG-2026-03-07-59`, `UPG-2026-03-07-60`, `UPG-2026-03-07-61`, `UPG-2026-03-07-62`

---

## 1. Obiettivo

Definire il primo `Evidence Population Pass v1` del nuovo SMART/KineScore.

Questa spec non aggiunge ancora codice runtime, ma popola in modo concreto
il registro con i primi oggetti che servono davvero a sostenere:

- `PRT-001 ... PRT-006`
- `Demand Vector v1`
- `Validation Matrix v1`

Lo scopo e' uscire dalla sola forma del registry e iniziare a dichiarare:

- quali fonti sono realmente attive
- quali anchor usiamo davvero
- quali claim sono gia' sufficientemente chiari
- quali parametri sono difendibili adesso
- quali restano ancora `expert-calibrated` o `pending validation`

---

## 2. Regola Di Rigorosita' v1

Nel primo pass non dobbiamo popolare "tutto".
Dobbiamo popolare solo cio' che e' necessario a rendere i protocolli v1
seriamente tracciabili.

Quindi il pass v1 copre solo 4 famiglie prioritarie:

1. `frequency`
2. `volume`
3. `suitability`
4. `recovery/balance`

Le aree come `periodization` avanzata e `metabolic demand` possono restare
parziali nel v1.

---

## 3. Source Catalog Minimo v1

Il primo pass deve popolare almeno queste fonti.

## 3.1 SourceRecord iniziali

### `SRC-NSCA-2016`

- `source_code`: `NSCA-2016`
- `source_type`: `guideline`
- `domain_tags`: `frequency`, `resistance_training`, `exercise_order`, `recovery`

### `SRC-ACSM-2009`

- `source_code`: `ACSM-2009`
- `source_type`: `position_stand`
- `domain_tags`: `exercise_prescription`, `general_fitness`, `beginner`

### `SRC-SCHOENFELD-2016`

- `source_code`: `SCHOENFELD-2016`
- `source_type`: `review`
- `domain_tags`: `frequency`, `hypertrophy`

### `SRC-SCHOENFELD-2017`

- `source_code`: `SCHOENFELD-2017`
- `source_type`: `review`
- `domain_tags`: `volume`, `hypertrophy`

### `SRC-ISRAETEL-2020`

- `source_code`: `ISRAETEL-2020`
- `source_type`: `expert_framework`
- `domain_tags`: `MEV`, `MAV`, `MRV`, `volume_model`

### `SRC-HELMS-2019`

- `source_code`: `HELMS-2019`
- `source_type`: `expert_framework`
- `domain_tags`: `periodization`, `fatigue_management`

### `SRC-SAHRMANN-2002`

- `source_code`: `SAHRMANN-2002`
- `source_type`: `expert_framework`
- `domain_tags`: `movement_quality`, `regional_stress`, `clinical_reasoning`

### `SRC-ALENTORN-GELI-2009`

- `source_code`: `ALENTORN-GELI-2009`
- `source_type`: `review`
- `domain_tags`: `plyometrics`, `landing`, `impact`, `injury_risk`

---

## 4. Anchor Catalog Minimo v1

Il primo pass deve produrre anchor riusabili e non ridondanti.

## 4.1 AnchorRecord iniziali

### `ANC-FREQ-HYP-2X`

- `anchor_code`: `SCHOENFELD-FREQ-2X`
- `source_id`: `SRC-SCHOENFELD-2016`
- `label`: `Hypertrophy frequency >=2x preferred`
- `domain_tags`: `frequency`, `hypertrophy`
- `evidence_class`: `A`

### `ANC-VOL-MEV-MAV`

- `anchor_code`: `ISRAETEL-MEV-MAV`
- `source_id`: `SRC-ISRAETEL-2020`
- `label`: `Volume landmarks MEV/MAV/MRV`
- `domain_tags`: `volume`, `MEV`, `MAV`, `MRV`
- `evidence_class`: `A`

### `ANC-ORDER-COMPOUND-FIRST`

- `anchor_code`: `NSCA-ORDER-COMPOUND-FIRST`
- `source_id`: `SRC-NSCA-2016`
- `label`: `Complex/high-priority lifts earlier in session`
- `domain_tags`: `session_order`, `recovery`
- `evidence_class`: `A`

### `ANC-BEGINNER-CONSERVATIVE`

- `anchor_code`: `ACSM-BEGINNER-CONSERVATIVE`
- `source_id`: `SRC-ACSM-2009`
- `label`: `Conservative beginner entry prescription`
- `domain_tags`: `beginner`, `general_fitness`
- `evidence_class`: `A`

### `ANC-RECOVERY-48H-SAME-REGION`

- `anchor_code`: `NSCA-RECOVERY-48H`
- `source_id`: `SRC-NSCA-2016`
- `label`: `48h caution for high overlap on same muscle regions`
- `domain_tags`: `recovery`, `session_overlap`
- `evidence_class`: `A`

### `ANC-LOW-SKILL-DRAFTING`

- `anchor_code`: `BEGINNER-LOW-SKILL-DRAFT`
- `source_id`: `SRC-ACSM-2009`
- `label`: `Beginner auto-draft should privilege low skill and controllable exercises`
- `domain_tags`: `suitability`, `beginner`
- `evidence_class`: `B`

### `ANC-BALLISTIC-IMPACT-CAUTION`

- `anchor_code`: `ALENTORN-PLYO-IMPACT`
- `source_id`: `SRC-ALENTORN-GELI-2009`
- `label`: `Ballistic and landing demand require higher tolerance and screening`
- `domain_tags`: `ballistic`, `impact`, `suitability`
- `evidence_class`: `A`

### `ANC-REGIONAL-STRESS-MODEL`

- `anchor_code`: `SAHRMANN-REGIONAL-STRESS`
- `source_id`: `SRC-SAHRMANN-2002`
- `label`: `Regional mechanical stress matters beyond muscle label`
- `domain_tags`: `clinical`, `demand`, `regional_stress`
- `evidence_class`: `B`

---

## 5. Claim Catalog Minimo v1

Il primo pass deve popolare claim che servono davvero ai protocolli v1.

## 5.1 Frequency claims

### `CLM-FREQ-001`

- `claim_code`: `frequency_hypertrophy_prefers_2x_plus`
- `anchor_ids`: `ANC-FREQ-HYP-2X`
- `claim_type`: `frequency`
- `evidence_class`: `A`
- `confidence`: `high`
- `population_scope`:
  - `beginner_general`
  - `intermediate_general`
  - `advanced_performance`

### `CLM-FREQ-002`

- `claim_code`: `small_muscle_low_frequency_is_more_tolerable_than_major_pattern_absence`
- `anchor_ids`: `ANC-FREQ-HYP-2X`, `ANC-BEGINNER-CONSERVATIVE`
- `claim_type`: `frequency`
- `evidence_class`: `B`
- `confidence`: `moderate`
- `population_scope`:
  - `beginner_general`

## 5.2 Volume claims

### `CLM-VOL-001`

- `claim_code`: `volume_should_be_read_against_mev_mav_mrv_landmarks`
- `anchor_ids`: `ANC-VOL-MEV-MAV`
- `claim_type`: `volume`
- `evidence_class`: `A`
- `confidence`: `high`
- `population_scope`:
  - `beginner_general`
  - `intermediate_general`
  - `advanced_performance`

### `CLM-VOL-002`

- `claim_code`: `beginner_general_should_bias_low_mav_over_saturation`
- `anchor_ids`: `ANC-BEGINNER-CONSERVATIVE`, `ANC-VOL-MEV-MAV`
- `claim_type`: `volume`
- `evidence_class`: `A`
- `confidence`: `high`
- `population_scope`:
  - `beginner_general`
  - `beginner_clinical_low_skill`

## 5.3 Recovery/balance claims

### `CLM-REC-001`

- `claim_code`: `high_same_region_overlap_requires_48h_caution`
- `anchor_ids`: `ANC-RECOVERY-48H-SAME-REGION`
- `claim_type`: `recovery`
- `evidence_class`: `A`
- `confidence`: `high`
- `population_scope`:
  - `all_supported_protocols`

### `CLM-BAL-001`

- `claim_code`: `push_pull_and_quad_ham_should_stay_inside_protocol_bands`
- `anchor_ids`: `ANC-VOL-MEV-MAV`, `ANC-RECOVERY-48H-SAME-REGION`
- `claim_type`: `balance`
- `evidence_class`: `B`
- `confidence`: `moderate`
- `population_scope`:
  - `all_supported_protocols`

## 5.4 Suitability / demand claims

### `CLM-SUIT-001`

- `claim_code`: `beginner_auto_draft_must_favor_low_skill_low_ballistic_options`
- `anchor_ids`: `ANC-BEGINNER-CONSERVATIVE`, `ANC-LOW-SKILL-DRAFTING`
- `claim_type`: `suitability`
- `evidence_class`: `A`
- `confidence`: `high`
- `population_scope`:
  - `beginner_general`
  - `beginner_clinical_low_skill`

### `CLM-SUIT-002`

- `claim_code`: `ballistic_and_high_impact_exercises_are_not_default_low_skill_draft_choices`
- `anchor_ids`: `ANC-BALLISTIC-IMPACT-CAUTION`
- `claim_type`: `suitability`
- `evidence_class`: `A`
- `confidence`: `high`
- `population_scope`:
  - `beginner_general`
  - `beginner_clinical_low_skill`

### `CLM-DEMAND-001`

- `claim_code`: `regional_stress_cannot_be_reduced_to_pattern_only`
- `anchor_ids`: `ANC-REGIONAL-STRESS-MODEL`
- `claim_type`: `demand_model`
- `evidence_class`: `B`
- `confidence`: `moderate`
- `population_scope`:
  - `all_supported_protocols`

---

## 6. Parameter Catalog Minimo v1

Nel primo pass non dobbiamo popolare centinaia di parametri.
Dobbiamo popolare i parametri che gia' sostengono i protocolli v1.

## 6.1 ParameterRecord iniziali

### `PAR-FREQ-001`

- `parameter_code`: `session_stimulus_threshold`
- `claim_ids`: `CLM-FREQ-001`
- `value`: `2.0`
- `unit`: `hypertrophy_sets_per_session`
- `parameter_type`: `threshold`
- `evidence_origin`: `expert-calibrated`
- `evidence_class`: `B`
- `population_scope`: `all_supported_protocols`

### `PAR-FREQ-002`

- `parameter_code`: `beginner_small_muscle_frequency_floor_preferred`
- `claim_ids`: `CLM-FREQ-001`, `CLM-FREQ-002`
- `value`: `2`
- `unit`: `sessions_per_week`
- `parameter_type`: `floor`
- `evidence_origin`: `expert-calibrated`
- `evidence_class`: `B`
- `population_scope`: `beginner_general_3x`, `beginner_clinical_3x`

### `PAR-VOL-001`

- `parameter_code`: `beginner_general_target_volume_zone`
- `claim_ids`: `CLM-VOL-001`, `CLM-VOL-002`
- `value`: `low_mav`
- `unit`: null
- `parameter_type`: `categorical_policy`
- `evidence_origin`: `literature-derived`
- `evidence_class`: `A`
- `population_scope`: `beginner_general`, `beginner_clinical_low_skill`

### `PAR-REC-001`

- `parameter_code`: `adjacent_session_same_region_caution_window`
- `claim_ids`: `CLM-REC-001`
- `value`: `48`
- `unit`: `hours`
- `parameter_type`: `threshold`
- `evidence_origin`: `literature-derived`
- `evidence_class`: `A`
- `population_scope`: `all_supported_protocols`

### `PAR-SUIT-001`

- `parameter_code`: `max_skill_demand_beginner_general`
- `claim_ids`: `CLM-SUIT-001`
- `value`: `1`
- `unit`: `ordinal_0_4`
- `parameter_type`: `ceiling`
- `evidence_origin`: `expert-calibrated`
- `evidence_class`: `B`
- `population_scope`: `beginner_general`

### `PAR-SUIT-002`

- `parameter_code`: `max_ballistic_demand_beginner_general`
- `claim_ids`: `CLM-SUIT-001`, `CLM-SUIT-002`
- `value`: `1`
- `unit`: `ordinal_0_4`
- `parameter_type`: `ceiling`
- `evidence_origin`: `expert-calibrated`
- `evidence_class`: `B`
- `population_scope`: `beginner_general`

### `PAR-SUIT-003`

- `parameter_code`: `max_impact_demand_beginner_clinical_low_skill`
- `claim_ids`: `CLM-SUIT-002`
- `value`: `0`
- `unit`: `ordinal_0_4`
- `parameter_type`: `ceiling`
- `evidence_origin`: `expert-calibrated`
- `evidence_class`: `A`
- `population_scope`: `beginner_clinical_low_skill`

### `PAR-BAL-001`

- `parameter_code`: `quad_ham_target_beginner_general`
- `claim_ids`: `CLM-BAL-001`
- `value`: `1.25`
- `unit`: `ratio`
- `parameter_type`: `target_range`
- `evidence_origin`: `internal-heuristic-pending-validation`
- `evidence_class`: `C`
- `population_scope`: `beginner_general`

### `PAR-BAL-002`

- `parameter_code`: `push_pull_target_default`
- `claim_ids`: `CLM-BAL-001`
- `value`: `1.00`
- `unit`: `ratio`
- `parameter_type`: `target_range`
- `evidence_origin`: `expert-calibrated`
- `evidence_class`: `B`
- `population_scope`: `all_supported_protocols`

---

## 7. Usage Map Iniziale

Il primo pass deve popolare almeno alcune `UsageRecord` ad alto valore.

## 7.1 Uso nei protocolli

### `USE-PRT-001-CORE`

- `target_type`: `protocol`
- `target_id`: `PRT-001`
- `parameter_ids`:
  - `PAR-VOL-001`
  - `PAR-SUIT-001`
  - `PAR-SUIT-002`
- `claim_ids`:
  - `CLM-VOL-002`
  - `CLM-SUIT-001`
  - `CLM-SUIT-002`

### `USE-PRT-002-CORE`

- `target_type`: `protocol`
- `target_id`: `PRT-002`
- `parameter_ids`:
  - `PAR-FREQ-001`
  - `PAR-FREQ-002`
  - `PAR-BAL-001`
  - `PAR-SUIT-001`
  - `PAR-SUIT-002`
- `claim_ids`:
  - `CLM-FREQ-001`
  - `CLM-FREQ-002`
  - `CLM-BAL-001`
  - `CLM-SUIT-001`

### `USE-PRT-006-CLINICAL`

- `target_type`: `protocol`
- `target_id`: `PRT-006`
- `parameter_ids`:
  - `PAR-VOL-001`
  - `PAR-SUIT-003`
  - `PAR-REC-001`
- `claim_ids`:
  - `CLM-VOL-002`
  - `CLM-SUIT-002`
  - `CLM-REC-001`

## 7.2 Uso nelle validation cases

### `USE-VM-002`

- `target_type`: `validation_case`
- `target_id`: `VM-002`
- `parameter_ids`:
  - `PAR-FREQ-001`
  - `PAR-FREQ-002`
  - `PAR-SUIT-001`
  - `PAR-SUIT-002`
  - `PAR-BAL-001`
- `claim_ids`:
  - `CLM-FREQ-001`
  - `CLM-SUIT-001`
  - `CLM-SUIT-002`
  - `CLM-BAL-001`

### `USE-VM-006`

- `target_type`: `validation_case`
- `target_id`: `VM-006`
- `parameter_ids`:
  - `PAR-SUIT-003`
  - `PAR-REC-001`
- `claim_ids`:
  - `CLM-SUIT-002`
  - `CLM-REC-001`

---

## 8. Cosa E' Gia' Difendibile E Cosa No

Questo pass deve essere epistemicamente onesto.

## 8.1 Gia' relativamente forte

- `freq >= 2x` come preferenza ipertrofica generale
- uso `MEV/MAV/MRV`
- approccio beginner conservativo
- attenzione a overlap e recupero regionale
- cautela su ballistic/impact in low-skill drafting

## 8.2 Intermedio ma non ancora forte

- soglie numeriche esatte di `skill_demand`
- mapping puntuale tra ordinali e categorie di esercizio
- alcuni target ratio per protocollo

## 8.3 Ancora provvisorio

- alcuni target balance numerici specifici del sistema
- alcune calibrazioni di budget multi-seduta
- parte del `Demand Vector` su `metabolic/stability`

Questo e' il punto che rende il registro serio: dichiarare apertamente dove la
base e' `A`, `B` o `C`.

---

## 9. Deliverable Minimi Del Pass v1

Il primo pass non deve mirare alla completezza totale.
Deve produrre almeno:

1. `8 SourceRecord`
2. `8 AnchorRecord`
3. `8 ClaimRecord`
4. `9 ParameterRecord`
5. `5 UsageRecord`

Questo e' sufficiente per sostenere in modo non vuoto i protocolli v1.

---

## 10. Acceptance Criteria v1

Il pass e' considerato metodologicamente sufficiente se:

1. ogni protocollo `PRT-001 ... PRT-006` richiama almeno un `UsageRecord`
2. nessun parametro chiave dei protocolli beginner resta senza `claim_ids`
3. ogni parametro dichiarato ha `evidence_origin`
4. ogni claim ha almeno un anchor
5. ogni anchor ha un source record

---

## 11. Non-Goals del v1

Questa spec non fa ancora:

- popolamento esaustivo di tutti i coefficienti del planner attuale
- migrazione del codice runtime ai `ParameterRecord`
- bibliografia completa con DOI/PMID
- revisione critica formale paper-per-paper

Il v1 serve a popolare il nucleo utile, non l'intero atlante scientifico.

---

## 12. Roadmap Immediata

Dopo questo pass, i passi corretti sono:

1. `Runtime Translation Plan`
   come portare il registry nel backend senza rompere il motore attuale

2. `Catalog Mapping Spec v1`
   collegare il `Demand Vector` agli esercizi del catalogo

3. `Evidence Population Pass v2`
   estendere il registry a `periodization`, `metabolic demand`, `advanced performance`

4. `Validation Harness Implementation v1`
   legare `VM-*` ai `claim_ids` e ai `parameter_ids`

---

## 13. Fonti e Anchor Attivi Nel Pass v1

Questo pass usa soltanto anchor gia' coerenti con il metodo dichiarato:

- `NSCA-2016`
- `ACSM-2009`
- `SCHOENFELD-2016`
- `SCHOENFELD-2017`
- `ISRAETEL-2020`
- `HELMS-2019`
- `SAHRMANN-2002`
- `ALENTORN-GELI-2009`

Le fonti aggiuntive presenti nel manifesto possono entrare nei pass successivi,
ma non servono per chiudere il primo nucleo difendibile del registry.
