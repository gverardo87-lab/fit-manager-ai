# UPG-2026-03-07-58 — SMART Protocol Definitions v1

> *"Il registry diventa reale solo quando ogni protocollo smette di essere un nome
> e diventa un contratto prescrittivo completo."*

**Data**: 2026-03-07  
**Stato**: ANALYSIS SPEC  
**Ambito**: SMART backend, KineScore, Protocol Engine  
**Dipende da**: `UPG-2026-03-07-55`, `UPG-2026-03-07-56`, `UPG-2026-03-07-57`

---

## 1. Obiettivo

Definire le prime **Protocol Definitions v1** del nuovo SMART/KineScore.

Questa spec rende concreti i protocolli `PRT-001 ... PRT-006` gia' introdotti nel `Protocol Registry v1`.

Ogni protocollo qui viene definito con:

- identita' e scopo
- popolazione target
- criteri di ingresso/esclusione
- vincoli per sessione, volume, frequenza, bilanciamento, recupero, suitability e clinical mode
- contratto minimo di validazione
- source anchors

Questa spec e' ancora analitica: non introduce runtime code, ma prepara il passaggio a modelli backend veri.

---

## 2. Regole Comuni a Tutti i Protocolli v1

Prima delle singole definizioni, i protocolli v1 condividono queste regole trasversali:

### 2.1 Determinismo

- nessun random
- nessun fallback non dichiarato
- tie-break stabili
- stesso input -> stesso output

### 2.2 Auto-draft vs Override

I protocolli governano il **draft automatico**.
Il professionista puo' comunque forzare scelte fuori protocollo nel builder, ma:

- il draft di default resta vincolato
- le deroghe devono essere esplicite

### 2.3 Multi-layer interpretation

Ogni protocollo va letto su 3 livelli:

1. **Canonico**
   split, ruoli, slot, esposizioni

2. **Feasibility**
   cosa e' ammissibile come esercizio concreto

3. **Validation**
   come giudicare se il protocollo sta producendo un output coerente

### 2.4 Source anchors standard

Le definizioni v1 fanno riferimento ai seguenti anchor:

- `NSCA-2016`
- `ACSM-2009`
- `SCHOENFELD-2016`
- `SCHOENFELD-2017`
- `ISRAETEL-2020`
- `HELMs-2019`
- `SAHRMANN-2002`
- `ALENTORN-GELI-2009`

Nota: la normalizzazione definitiva degli anchor verra' demandata all'`Evidence Registry`.

---

## 3. PRT-001

## `beginner_general_2x_tonificazione_full_body_v1`

### 3.1 Identity

- `protocol_id`: `PRT-001`
- `registry_id`: `beginner_general_2x_tonificazione_full_body_v1`
- `status`: `supported`
- `mode`: `general`
- `livello`: `beginner`
- `frequenza`: `2`
- `obiettivo`: `tonificazione`
- `split_family`: `full_body`
- `evidence_profile`: `high_for_beginner_general`

### 3.2 Clinical/Population intent

Protocollo di ingresso per:

- principianti reali
- soggetti con bassa tolleranza al carico
- clienti con dati incompleti
- riavvio dopo inattivita'

### 3.3 Entry criteria

- nessuna necessita' di specializzazione distrettuale
- aderenza attesa > performance
- readiness incompleta accettabile
- nessun bisogno di frequenza >2x per distretti specifici

### 3.4 Exclusion criteria

- richiesta esplicita di forza prioritaria
- profili che necessitano frequenza piu' alta per pratica tecnica
- contesto performance strutturato

### 3.5 Session constraints

- `max_slots_per_session = 5`
- `max_isolation_slots_per_session = 2`
- `max_primary_compounds_per_session = 3`
- `target_duration_min = 45-60`
- ruoli consentiti: `full_body`
- pattern bucket minimi/settimana:
  - `push = 1`
  - `pull = 1`
  - `knee_dominant = 1`
  - `hip_dominant = 1`

### 3.6 Volume constraints

- `target_volume_zone = low_mav`
- focus su esposizione tecnica, non su saturazione volume
- `critical_mev_floors`:
  - petto
  - dorsali
  - quadricipiti
  - femorali
  - glutei
- eccessi non desiderati su:
  - deltoide anteriore
  - trapezio
  - glutei

### 3.7 Frequency constraints

- `session_stimulus_threshold = 2.0`
- muscoli maggiori: floor `>= 1x`
- piccoli distretti: nessun obbligo hard `2x`
- no specializzazione accessori

### 3.8 Balance constraints

- `push_pull`: dentro banda standard
- `push_h/push_v`: soft target, non hard
- `pull_h/pull_v`: soft target
- `quad_ham`: monitorato, ma non hard-fail

### 3.9 Recovery constraints

- overlap contigue conservativo
- no doppia seduta ad alto costo posteriore consecutivo
- posterior chain budget basso-moderato

### 3.10 Suitability constraints

- `max_skill_demand = low`
- `max_coordination_demand = low`
- `max_ballistic_demand = low`
- `max_impact_demand = low`
- esclusi dall'auto-draft:
  - advanced
  - jump/plyo
  - muscle-up / weighted pull-up

### 3.11 Clinical constraints

- `safety_mode = overlay`
- safety informa ma non domina
- no family gate clinico aggiuntivo se non richiesto dall'anamnesi

### 3.12 Validation contract

- score minimo atteso: `>= 70`
- warning tollerabili:
  - moderato `quad_ham_low`
  - moderato `low_frequency_small_muscle`
- warning non ammessi:
  - `advanced_draft_exercise`
  - `extreme_push_pull_imbalance`

### 3.13 Source anchors

- `NSCA-2016`
- `SCHOENFELD-2016`
- `ISRAETEL-2020`

---

## 4. PRT-002

## `beginner_general_3x_tonificazione_full_body_v1`

### 4.1 Identity

- `protocol_id`: `PRT-002`
- `registry_id`: `beginner_general_3x_tonificazione_full_body_v1`
- `status`: `supported`
- `mode`: `general`
- `livello`: `beginner`
- `frequenza`: `3`
- `obiettivo`: `tonificazione`
- `split_family`: `full_body_abc`
- `evidence_profile`: `core_beginner_protocol`

### 4.2 Clinical/Population intent

Protocollo principale SMART beginner.
Deve essere il riferimento di qualita' del sistema.

### 4.3 Entry criteria

- tolleranza base a 3 sedute/settimana
- obiettivo generalista
- priorita' a controllo tecnico e aderenza

### 4.4 Exclusion criteria

- richiesta di specializzazione avanzata
- anamnesi con bisogno di low-skill dominato -> migrare a `PRT-006`

### 4.5 Session constraints

- `max_slots_per_session = 6`
- `max_isolation_slots_per_session = 2`
- `max_primary_compounds_per_session = 3`
- `target_duration_min = 50-65`
- split: `full_body A/B/C`
- ogni settimana deve esporre:
  - `push_h >= 1`
  - `push_v >= 1`
  - `pull_h >= 1`
  - `pull_v >= 1`
  - `squat >= 2`
  - `hinge >= 2`

### 4.6 Volume constraints

- `target_volume_zone = low_mav`
- piccoli distretti non devono restare sistematicamente sotto MEV
- `critical_mev_floors`:
  - deltoide laterale
  - polpacci
  - bicipiti
  - tricipiti

### 4.7 Frequency constraints

- `session_stimulus_threshold = 2.0`
- piccoli distretti selezionati:
  - `deltoide_laterale >= 2x`
  - `polpacci >= 2x`
  - `bicipiti >= 2x` desiderabile
  - `tricipiti >= 2x` desiderabile

### 4.8 Balance constraints

- `push_pull`: dentro banda standard
- `push_h/push_v`: dentro banda, alto peso
- `pull_h/pull_v`: dentro banda, alto peso
- `quad_ham`: warning importante, ma ancora non hard-fail in v1

### 4.9 Recovery constraints

- overlap `B -> C` su posterior chain sotto cap conservativo
- no doppia seduta alta su dorsali/femorali/glutei in sequenza senza compensazione
- trapezio/core sotto budget moderato

### 4.10 Suitability constraints

- `allow_advanced_exercises_in_draft = False`
- esclusi dall'auto-draft:
  - advanced
  - jump/plyo/skill
  - cardio non `resistenza`
- il draft deve privilegiare esercizi con `rep_range_ipertrofia` coerente

### 4.11 Clinical constraints

- `safety_mode = overlay`

### 4.12 Validation contract

- score minimo atteso: `>= 75`
- warning non ammessi:
  - `advanced_draft_exercise`
  - `push_h_push_v_imbalance`
  - `pull_h_pull_v_imbalance`
- warning tollerabili ma da ridurre:
  - `quad_ham_low`
  - posterior-chain overlap

### 4.13 Source anchors

- `NSCA-2016`
- `SCHOENFELD-2016`
- `SCHOENFELD-2017`
- `ISRAETEL-2020`
- `ALENTORN-GELI-2009`

---

## 5. PRT-003

## `intermediate_general_4x_ipertrofia_upper_lower_v1`

### 5.1 Identity

- `protocol_id`: `PRT-003`
- `registry_id`: `intermediate_general_4x_ipertrofia_upper_lower_v1`
- `status`: `supported`
- `mode`: `general`
- `livello`: `intermedio`
- `frequenza`: `4`
- `obiettivo`: `ipertrofia`
- `split_family`: `upper_lower`
- `evidence_profile`: `mainstream_hypertrophy_core`

### 5.2 Population intent

Protocollo principale ipertrofia per utenti intermedi generalisti.

### 5.3 Entry criteria

- tolleranza a 4 sedute
- nessuna richiesta di performance specialistica
- aderenza stabile

### 5.4 Session constraints

- `max_slots_per_session = 8`
- `max_isolation_slots_per_session = 3`
- `target_duration_min = 60-75`
- distribuzione `U/L/U/L`

### 5.5 Volume constraints

- `target_volume_zone = mid_mav`
- muscoli principali al centro del range MAV
- eccessi tollerati moderati su deltoide anteriore/tricipiti solo se non sporcano i ratio

### 5.6 Frequency constraints

- gruppi principali `>= 2x`
- accessori principali `>= 2x` dove rilevante

### 5.7 Balance constraints

- tutti i ratio dentro banda standard
- `push_pull` con priorita' alta
- `quad_ham` importante ma non dominante sul volume ipertrofico

### 5.8 Recovery constraints

- overlap piu' permissivo del beginner
- posterior chain budget medio
- axial load da monitorare se lower days sono dense

### 5.9 Suitability constraints

- `max_skill_demand = medium`
- advanced ammessi solo se coerenti col protocollo e con draft plausibile
- no ballistic gratuito

### 5.10 Clinical constraints

- `safety_mode = overlay`

### 5.11 Validation contract

- score minimo atteso: `>= 80`
- warning non ammessi:
  - `major_push_pull_imbalance`
  - `advanced_draft_without_need`
- warning tollerabili:
  - lieve overlap locale

### 5.12 Source anchors

- `NSCA-2016`
- `SCHOENFELD-2017`
- `ISRAETEL-2020`

---

## 6. PRT-004

## `intermediate_performance_3x_forza_full_body_v1`

### 6.1 Identity

- `protocol_id`: `PRT-004`
- `registry_id`: `intermediate_performance_3x_forza_full_body_v1`
- `status`: `supported`
- `mode`: `performance`
- `livello`: `intermedio`
- `frequenza`: `3`
- `obiettivo`: `forza`
- `split_family`: `full_body_strength_bias`
- `evidence_profile`: `strength_foundation`

### 6.2 Population intent

Protocollo forza general/performance non specialistico.

### 6.3 Entry criteria

- base tecnica intermedia
- tolleranza a compound principali
- priorita' a forza e skill dei fondamentali

### 6.4 Session constraints

- `max_slots_per_session = 6`
- `max_isolation_slots_per_session = 2`
- riposi alti
- densita' contenuta

### 6.5 Volume constraints

- `target_volume_zone = low_mav`
- volume moderato, intensita' alta
- isolation subordinata al compound

### 6.6 Frequency constraints

- `squat`, `hinge`, `push`, `pull` almeno `2x` aggregate dove possibile
- frequenza tecnica prioritaria ai pattern, non ai piccoli distretti

### 6.7 Balance constraints

- `push_pull` prioritario
- `quad_ham` monitorato
- `anterior_posterior` importante per salute della spalla

### 6.8 Recovery constraints

- massimo 2 sedute high-stress di fila
- core/axial load sotto budget rigido

### 6.9 Suitability constraints

- `max_skill_demand = medium`
- no esercizi advanced non necessari
- bodyweight skill esclusi se non strettamente funzionali al goal di forza

### 6.10 Clinical constraints

- `safety_mode = overlay`

### 6.11 Validation contract

- score minimo atteso: `>= 78`
- warning non ammessi:
  - `draft_with_skill_noise`
  - `major_recovery_failure`

### 6.12 Source anchors

- `NSCA-2016`
- `RALSTON-2017`
- `ZOURDOS-2016`

---

## 7. PRT-005

## `advanced_performance_5x_ipertrofia_upper_lower_plus_v1`

### 7.1 Identity

- `protocol_id`: `PRT-005`
- `registry_id`: `advanced_performance_5x_ipertrofia_upper_lower_plus_v1`
- `status`: `supported`
- `mode`: `performance`
- `livello`: `avanzato`
- `frequenza`: `5`
- `obiettivo`: `ipertrofia`
- `split_family`: `upper_lower_plus`
- `evidence_profile`: `advanced_hypertrophy_high_volume`

### 7.2 Population intent

Protocollo avanzato ad alta densita' per ipertrofia non specialistica estrema.

### 7.3 Entry criteria

- tolleranza alta a volume/frequenza
- storico allenante consistente
- buona recovery capacity

### 7.4 Session constraints

- `max_slots_per_session = 10`
- `max_isolation_slots_per_session = 4`
- `target_duration_min = 70-90`
- split `U/L/U/L/U`

### 7.5 Volume constraints

- `target_volume_zone = high_mav`
- alcuni distretti possono stare in upper MAV
- eccessi moderati possibili se sotto controllo recovery

### 7.6 Frequency constraints

- gruppi principali `>= 2x`
- piccoli distretti specializzabili

### 7.7 Balance constraints

- ratio tutti dentro banda
- priorita' alta a `push_pull` e `quad_ham`

### 7.8 Recovery constraints

- fatigue budget esplicito
- posterior chain e axial load monitorati a livello settimanale

### 7.9 Suitability constraints

- `max_skill_demand = high`
- advanced ammessi
- ballistic consentito solo se coerente con protocollo, mai ornamentale

### 7.10 Clinical constraints

- `safety_mode = overlay`

### 7.11 Validation contract

- score minimo atteso: `>= 82`
- warning non ammessi:
  - `systemic_overload_extreme`
  - `gross_pattern_imbalance`

### 7.12 Source anchors

- `NSCA-2016`
- `SCHOENFELD-2017`
- `ISRAETEL-2020`
- `HELMs-2019`

---

## 8. PRT-006

## `beginner_clinical_3x_tonificazione_full_body_low_skill_v1`

### 8.1 Identity

- `protocol_id`: `PRT-006`
- `registry_id`: `beginner_clinical_3x_tonificazione_full_body_low_skill_v1`
- `status`: `clinical_only`
- `mode`: `clinical`
- `livello`: `beginner`
- `frequenza`: `3`
- `obiettivo`: `tonificazione`
- `split_family`: `full_body_low_skill`
- `evidence_profile`: `clinical_prudence_protocol`

### 8.2 Population intent

Protocollo prudenziale per profili con anamnesi attiva o fragilita' biomeccanica,
senza sconfinare in riabilitazione medica specialistica.

### 8.3 Entry criteria

- anamnesi legacy/structured con segnali di rischio
- bisogno di draft low-skill, low-impact
- priorita' safety > performance

### 8.4 Exclusion criteria

- casi di rehab clinica specialistica fuori perimetro SMART
- profili che richiedono prescrizione medica dedicata

### 8.5 Session constraints

- `max_slots_per_session = 5`
- `max_isolation_slots_per_session = 2`
- sedute brevi, dense il giusto
- no cluster high-stress

### 8.6 Volume constraints

- `target_volume_zone = low_mav`
- volume conservativo
- no inseguimento aggressivo del massimo coverage

### 8.7 Frequency constraints

- gruppi maggiori `>= 1-2x`
- piccoli distretti solo se sostenibili e sicuri

### 8.8 Balance constraints

- `push_pull` e `anterior_posterior` con peso alto
- `quad_ham` importante per prudenza articolare

### 8.9 Recovery constraints

- overlap molto conservativo
- budget basso per posterior chain, trapezio, core

### 8.10 Suitability constraints

- `max_skill_demand = low`
- `max_ballistic_demand = low`
- `max_impact_demand = low`
- advanced esclusi dall'auto-draft
- families clinicamente sensibili spesso `infeasible_for_auto_draft`

### 8.11 Clinical constraints

- `safety_mode = dominant`
- safety entra nella feasibility, non solo nel ranking
- il draft deve mostrare rationale clinico chiaro

### 8.12 Validation contract

- score minimo atteso: `>= 78`
- warning non ammessi:
  - `advanced_draft_exercise`
  - `high_skill_candidate_in_clinical_draft`
  - `high_impact_candidate_in_clinical_draft`

### 8.13 Source anchors

- `NSCA-2016`
- `SCHOENFELD-2016`
- `SAHRMANN-2002`
- `ALENTORN-GELI-2009`

---

## 9. Cross-Protocol Comparison Rules

Per evitare drift tra protocolli, v1 deve rispettare anche queste relazioni:

### 9.1 Beginner vs Intermediate vs Advanced

- beginner:
  - meno densita'
  - meno skill demand
  - meno isolation
  - piu' prudenza recovery

- intermedio:
  - piu' volume e piu' flessibilita'

- avanzato:
  - maggiore tolleranza volume/frequenza
  - ma non permissivita' cieca

### 9.2 General vs Performance vs Clinical

- general:
  equilibrio e aderenza

- performance:
  piu' specificita' e priorita' ai pattern

- clinical:
  suitability e prudenza dominano il draft

---

## 10. Criteri di Qualita' del Registry v1

Il registry v1 e' buono solo se:

- ogni protocollo e' distinguibile dagli altri
- ogni protocollo ha una ragione scientifica chiara
- ogni protocollo e' implementabile nel constraint engine
- il sistema sa anche dire cosa NON supporta

---

## 11. Prossimo Deliverable

Dopo questa spec il passo piu' naturale e':

1. **Demand Vector v1**
   per dare significato biomeccanico/clinico piu' forte alla suitability

oppure, se preferisci restare sul filone prescrittivo puro:

2. **Validation Matrix v1**
   per congelare i casi benchmark dei protocolli `PRT-001 ... PRT-006`

---

## 12. Sintesi

Con questa spec SMART ha ora:

- un metodo scientifico v1
- un protocol registry v1
- un constraint schema v1
- le prime protocol definitions v1

Questo e' il primo punto in cui il sistema diventa descrivibile come metodo prescrittivo serio, e non piu' solo come planner che si corregge a colpi di patch.
