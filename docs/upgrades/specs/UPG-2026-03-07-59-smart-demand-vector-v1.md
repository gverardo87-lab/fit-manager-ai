# UPG-2026-03-07-59 - SMART Demand Vector v1

> *"Un esercizio non e' solo pattern e muscolo.
> E' anche coordinazione, skill, impatto, carico assiale e costo tessutale."*

**Data**: 2026-03-07
**Stato**: IMPLEMENTED (DB-backed, UPG-2026-03-08-01)
**Ambito**: SMART backend, KineScore, Protocol Engine, Exercise Suitability
**Dipende da**: `UPG-2026-03-07-55`, `UPG-2026-03-07-56`, `UPG-2026-03-07-57`, `UPG-2026-03-07-58`
**Implementato in**: `api/models/exercise.py` (10 colonne), `api/services/training_science/runtime/exercise_catalog.py` (`resolve_demand_vector()`), `tools/admin_scripts/populate_demand.py` (seed 391 esercizi)

---

## 1. Obiettivo

Definire il `Demand Vector v1` del nuovo SMART/KineScore.

Questa spec formalizza il layer biomeccanico e medico-funzionale che manca
tra:

- pattern muscolari
- protocollo attivo
- suitability dell'esercizio concreto

Il `Demand Vector` deve impedire che il sistema tratti esercizi molto diversi
come se fossero equivalenti solo per pattern o muscolo target.

Esempio:

- un `muscle-up` non e' solo `pull_v`
- un `box jump` non e' solo `squat`
- un `shoulder press` e un `landmine press` non hanno lo stesso costo
  scapolo-omerale

Questo e' un prerequisito per:

- determinismo scientifico piu' alto
- suitability clinica piu' rigorosa
- protocolli realmente dimostrabili
- futuro posizionamento IP e universitario piu' forte

---

## 2. Ruolo Del Demand Vector

Nel modello target:

- il `Protocol Registry` dice quale protocollo e' attivo
- il `Constraint Schema` dice quali limiti deve rispettare
- il `Demand Vector` descrive il costo biomeccanico-funzionale di ogni esercizio
- il `Ranker` ordina solo candidati gia' plausibili
- il `Validation Harness` verifica che il draft non superi i ceiling del protocollo

Questa separazione e' critica:

- `pattern` dice cosa allena
- `muscle contribution` dice quanto stimola
- `demand vector` dice quanto "costa" eseguirlo

---

## 3. Principi Di Design

### 3.1 Deterministico

Ogni esercizio deve avere un vettore fisso e versionato.

### 3.2 Multidimensionale

Il vettore deve separare skill, coordinazione, impatto, carico assiale e
domande regionali.

### 3.3 Protocol-aware

I protocolli non devono parlare in astratto di "esercizi difficili", ma di
ceiling espliciti per ciascuna dimensione del vettore.

### 3.4 Clinical-overlay ready

Il vettore deve poter essere incrociato con safety clinica senza confondere:

- rischio anatomico/medico
- difficolta' tecnica
- costo biomeccanico

### 3.5 Source-linked

Le famiglie di demand devono essere collegate a fonti e razionali
scientifico-medico-biomeccanici riconoscibili.

---

## 4. Demand Vector v1

Il `Demand Vector v1` usa 10 dimensioni ordinali.

Ogni dimensione e' rappresentata su scala `0..4`:

- `0 = none/minimal`
- `1 = low`
- `2 = moderate`
- `3 = high`
- `4 = very_high`

Questa scala e' volutamente ordinale, non pseudo-metabolica o pseudo-fisica.
Serve a:

- filtrare
- budgettare
- confrontare
- validare

Non serve ancora a produrre stime biomeccaniche continue.

### 4.1 Vector Shape

```python
ExerciseDemandVector(
    skill_demand: int,                # 0..4
    coordination_demand: int,         # 0..4
    stability_demand: int,            # 0..4
    ballistic_demand: int,            # 0..4
    impact_demand: int,               # 0..4
    axial_load_demand: int,           # 0..4
    shoulder_complex_demand: int,     # 0..4
    lumbar_load_demand: int,          # 0..4
    grip_demand: int,                 # 0..4
    metabolic_demand: int,            # 0..4
    demand_version: str,
    rationale_tags: list[str],
    source_anchors: list[str],
)
```

---

## 5. Significato Delle 10 Dimensioni

## 5.1 skill_demand

Misura quanta abilita' motoria specifica richiede l'esercizio.

Esempi:

- chest press machine -> `0-1`
- goblet squat -> `1`
- back squat -> `2`
- snatch variation -> `4`
- muscle-up -> `4`

Uso:

- gate principale dei protocolli beginner
- filtro forte nei protocolli clinical low-skill

## 5.2 coordination_demand

Misura quanto controllo intersegmentario e timing multi-articolare serve.

Esempi:

- leg extension -> `0-1`
- split squat -> `2`
- clean pull -> `3`
- muscle-up -> `4`

Uso:

- evita che i beginner ricevano esercizi formalmente "fattibili" ma troppo
  difficili da riprodurre bene

## 5.3 stability_demand

Misura il carico di controllo posturale e stabilizzazione locale/globale.

Esempi:

- machine row -> `1`
- dumbbell overhead press -> `2-3`
- single-leg hinge -> `3`

Uso:

- integra suitability
- entra nei budget di recupero e nelle modalita' clinical

## 5.4 ballistic_demand

Misura la componente esplosiva/reattiva.

Esempi:

- seated row -> `0`
- kettlebell swing -> `2-3`
- box jump -> `4`

Uso:

- ceiling hard nei protocolli beginner general e clinical
- rilevante per profili con bassa esposizione tecnica o alta cautela articolare

## 5.5 impact_demand

Misura l'impatto meccanico e il picco di atterraggio/assorbimento.

Esempi:

- leg press -> `0`
- loaded carry -> `1`
- jump lunge -> `3`
- depth jump -> `4`

Uso:

- rilevante per protocolli low-impact
- separa un esercizio esplosivo ma senza atterraggio da uno realmente impattante

## 5.6 axial_load_demand

Misura quanto carico viene trasmesso assialmente lungo la colonna.

Esempi:

- chest-supported row -> `0-1`
- leg press -> `1`
- back squat -> `3`
- yoke carry -> `4`

Uso:

- cruciale per profili lumbar-sensitive
- entra nei budget per seduta e overlap tra sedute

## 5.7 shoulder_complex_demand

Misura il costo scapolo-omerale complessivo, non solo il pattern push/pull.

Esempi:

- machine chest press -> `1-2`
- landmine press -> `2`
- overhead press -> `3`
- muscle-up -> `4`

Uso:

- rende distinguibili esercizi formalmente simili sul piano muscolare
- supporta overlay clinico spalla/cuffia/scapola

## 5.8 lumbar_load_demand

Misura il costo sulla regione lombare come richiesta di estensione/bracing/shear
management.

Esempi:

- leg extension -> `0`
- hip thrust machine -> `1`
- Romanian deadlift -> `3`
- good morning heavy -> `4`

Uso:

- separa axial load da carico lombare locale
- utile nei profili con ipersensibilita' lombare o bassa tolleranza di bracing

## 5.9 grip_demand

Misura quanta limitazione o fatica di presa puo' introdurre.

Esempi:

- machine press -> `0`
- lat machine -> `1`
- farmer carry -> `4`

Uso:

- evita confondenti su upper pulling e recovery locale
- utile per overlap e drafting su giorni consecutivi

## 5.10 metabolic_demand

Misura il costo sistemico/condizionante dell'esercizio, non il semplice volume.

Esempi:

- leg curl -> `1`
- goblet squat high reps -> `2`
- thruster circuit -> `4`

Uso:

- budget di seduta
- controllo densita' principiante
- clinical/performance mode

---

## 6. Regole Di Interpretazione v1

## 6.1 Non tutte le dimensioni pesano uguale

Nel v1 i protocolli useranno soprattutto:

- `skill_demand`
- `coordination_demand`
- `ballistic_demand`
- `impact_demand`
- `axial_load_demand`
- `shoulder_complex_demand`
- `lumbar_load_demand`

`stability`, `grip` e `metabolic` restano gia' nel vettore ma con impatto
runtime inizialmente piu' moderato.

## 6.2 Beginner e clinical usano ceiling piu' rigidi

Esempio concettuale:

- beginner general:
  `skill <= 1-2`, `ballistic <= 1`, `impact <= 1`

- beginner clinical low-skill:
  `skill <= 1`, `ballistic = 0`, `impact = 0`, `lumbar <= 2`,
  `shoulder_complex <= 2`

## 6.3 Performance usa ceiling piu' alti ma sempre dichiarati

Il protocollo performance non e' "tutto permesso".
Ha solo limiti diversi, espliciti e verificabili.

## 6.4 Demand Vector non sostituisce Safety Engine

Il `Demand Vector` non decide il rischio clinico.
Descrive il costo biomeccanico/funzionale dell'esercizio.

La safety clinica resta in:

- anamnesi
- safety map
- regole `avoid / modify / caution`

Il backend deve poi comporre i due layer.

---

## 7. Demand Families v1

Per evitare che il v1 resti troppo astratto, il vettore deve anche produrre
famiglie semanticamente leggibili.

Ogni esercizio puo' essere taggato con 0..N `demand_family`.

### 7.1 Famiglie minime v1

- `low_skill_general`
- `high_skill_upper`
- `ballistic_lower`
- `high_axial_loading`
- `shoulder_overhead_heavy`
- `lumbar_bracing_heavy`
- `grip_limited`
- `metabolic_dense`

Queste famiglie non sostituiscono il vettore numerico.
Servono come superficie di:

- debug
- explainability
- filtering leggibile lato protocollo

---

## 8. Evidence Model v1

Il `Demand Vector` deve usare un modello di evidenza onesto.

Non tutte le dimensioni hanno oggi lo stesso livello di supporto bibliografico
diretto nel repo.

### 8.1 Evidence classes

- `A_direct_repo_anchor`
  coperta da fonti gia' allineate nel repository

- `B_biomechanical_inference`
  inferenza biomeccanica forte ma non ancora formalizzata in un anchor dedicato

- `C_provisional_expert_model`
  utile operativamente ma da consolidare prima della certificazione forte

### 8.2 Regola di rigore

Per ogni dimensione o mapping esercizio:

- dichiarare `evidence_class`
- dichiarare `rationale_tags`
- dichiarare `source_anchors`

Nel v1, le dimensioni piu' solide per uso immediato sono:

- `skill_demand`
- `ballistic_demand`
- `impact_demand`
- `axial_load_demand`
- `shoulder_complex_demand`
- `lumbar_load_demand`

Le dimensioni che richiedono consolidamento aggiuntivo sono:

- `stability_demand`
- `metabolic_demand`

Questa trasparenza e' fondamentale per un metodo scientificamente difendibile.

---

## 9. Integrazione Con I Protocolli

Ogni `ProtocolDefinition` deve poter dichiarare:

```python
SuitabilityConstraintSet(
    max_skill_demand: int,
    max_coordination_demand: int,
    max_ballistic_demand: int,
    max_impact_demand: int,
    max_axial_load_demand: int,
    max_shoulder_complex_demand: int,
    max_lumbar_load_demand: int,
    discouraged_demand_families: list[str],
    excluded_demand_families: list[str],
)
```

Questo e' il ponte diretto tra `Constraint Schema v1` e `Demand Vector v1`.

---

## 10. Integrazione Con Il Ranker

Il ranker v2 non dovra' piu' solo penalizzare "advanced".
Dovra' applicare una pipeline piu' rigorosa:

1. `hard feasibility filter`
   scarta candidati che superano i ceiling del protocollo

2. `clinical overlay filter`
   applica `avoid / modify / caution`

3. `distance-to-protocol scoring`
   ordina i candidati plausibili per vicinanza al profilo ideale del protocollo

4. `draft projection`
   sceglie il top candidate con tie-break deterministico

Questo rende la suitability:

- spiegabile
- testabile
- meno dipendente da patch locali

---

## 11. Integrazione Con Il Validation Harness

Il `Validation Contract` di ogni protocollo deve poter esprimere test come:

- nessun esercizio auto-draft con `skill_demand > max_skill_demand`
- nessun esercizio auto-draft con `ballistic_demand > 0` in low-skill clinical
- nessun esercizio auto-draft con `shoulder_complex_demand > 2` nel protocollo
  beginner clinical spalla-sensitive
- budget assiale settimanale sotto soglia per protocolli specifici

Questo e' il punto che rende il metodo piu' certificabile:
il vettore entra nella validazione, non solo nel ranking.

---

## 12. Esempi Illustrativi v1

Questi esempi non sono ancora mapping canonici di catalogo.
Servono a chiarire la semantica del vettore.

### 12.1 Push-up

- `skill = 1`
- `coordination = 1`
- `stability = 2`
- `ballistic = 0`
- `impact = 0`
- `axial = 0`
- `shoulder_complex = 2`
- `lumbar = 1`
- `grip = 0`
- `metabolic = 1`

### 12.2 Landmine Press

- `skill = 1`
- `coordination = 2`
- `stability = 2`
- `ballistic = 0`
- `impact = 0`
- `axial = 1`
- `shoulder_complex = 2`
- `lumbar = 1`
- `grip = 1`
- `metabolic = 1`

### 12.3 Barbell Back Squat

- `skill = 2`
- `coordination = 2`
- `stability = 2`
- `ballistic = 0`
- `impact = 0`
- `axial = 3`
- `shoulder_complex = 1`
- `lumbar = 3`
- `grip = 0`
- `metabolic = 2`

### 12.4 Box Jump

- `skill = 2`
- `coordination = 2`
- `stability = 2`
- `ballistic = 4`
- `impact = 3`
- `axial = 0`
- `shoulder_complex = 0`
- `lumbar = 1`
- `grip = 0`
- `metabolic = 2`

### 12.5 Muscle-up

- `skill = 4`
- `coordination = 4`
- `stability = 3`
- `ballistic = 3`
- `impact = 0`
- `axial = 0`
- `shoulder_complex = 4`
- `lumbar = 1`
- `grip = 3`
- `metabolic = 3`

Questi esempi mostrano perche' `box jump` e `muscle-up` non devono entrare in
un beginner auto-draft solo per pattern coverage.

---

## 13. Non-Goals del v1

Questa spec non fa ancora:

- mapping completo dell'intero catalogo
- algoritmo numerico continuo di tissue stress
- modellazione separata per ginocchio/anca/caviglia
- fatigue model completo multi-seduta
- weighting finale dei demand nel ranker runtime

Il v1 serve a chiudere la grammatica del layer, non il suo deployment completo.

---

## 14. Roadmap Immediata

Dopo questa spec, i passi corretti sono:

1. `Validation Matrix v1`
   casi congelati per `PRT-001 ... PRT-006`

2. `Evidence Registry v1`
   normalizzare anchor, evidence class e rationale

3. `Catalog Mapping Spec v1`
   definire come ogni esercizio riceve il suo `Demand Vector`

4. `Runtime Translation Plan`
   introdurre `ExerciseDemandVector` in backend senza rompere il ranker esistente

---

## 15. Fonti e Source Anchors v1

Per coerenza con il repository, il `Demand Vector v1` si appoggia in prima
battuta a questi anchor gia' compatibili con SMART/KineScore:

- `NSCA-2016`
- `ACSM-2009`
- `SCHOENFELD-2016`
- `SCHOENFELD-2017`
- `ISRAETEL-2020`
- `HELMs-2019`
- `SAHRMANN-2002`
- `ALENTORN-GELI-2009`

Nota metodologica:
alcune dimensioni del vettore sono gia' forti come razionale biomeccanico ma
non ancora coperte da un anchor repo dedicato uno-a-uno. In quei casi il v1
deve dichiarare esplicitamente `evidence_class = B` o `C`, evitando finta
precisione.
