# UPG-2026-03-07-55 — SMART Scientific Method v1

> *"Il planner non deve inseguire i warning dell'analyzer.
> Deve nascere gia' dentro un recinto scientifico verificabile."*

**Data**: 2026-03-07  
**Stato**: ANALYSIS SPEC  
**Ambito**: SMART backend, Training Science Engine, KineScore roadmap  
**Tipo**: Architecture + Scientific Method + Validation Framework

---

## 1. Problema Reale

Il refactor SMART degli ultimi microstep ha corretto problemi veri:

- drift frontend/backend
- `plan-package` backend-first
- ranker deterministic runtime
- primi guardrail su `full_body 3x`
- suitability beginner nel draft automatico

Ma il pattern emerso e' chiaro: stiamo ancora correggendo casi specifici (`beginner 3x`, `push:pull`, `muscle-up`, `deltoide_laterale`) invece di governare il sistema con un metodo prescrittivo formale.

Questo ha tre conseguenze strutturali:

1. **Scarsa dimostrabilita' scientifica**
   Il comportamento e' migliorabile, ma non ancora spiegabile come metodo coerente across-matrix.

2. **Bassa certificabilita'**
   Se il planner evolve tramite patch locali, non esiste una catena chiara:
   `fonte -> parametro -> protocollo -> vincolo -> output -> verifica`.

3. **Base debole per KineScore IP / universita' / brevetto**
   Un sistema che migliora per euristiche puntuali e' difficile da difendere come metodo tecnico riproducibile.

---

## 2. Decisione Strategica

SMART deve evolvere da:

- `plan builder + analyzer + ranker + correzioni locali`

a:

- **Scientific Protocol Engine**

Il nuovo motore deve essere backend-first e composto da 5 strati formali:

1. **Evidence Registry**
2. **Protocol Registry**
3. **Constraint Engine**
4. **Canonical Plan Engine**
5. **Validation Harness**

Il ranker esercizi resta importante, ma deve diventare solo il layer di **projection and feasibility**, non il posto dove si decide la scienza del metodo.

---

## 3. Principi Non Negoziabili

### 3.1 Determinismo massimo

A parita' di:

- profilo cliente
- preset builder
- catalogo esercizi
- versione protocollo
- versione coefficienti

l'output deve essere identico.

Nessun random.
Nessun tie-break implicito.
Nessuna euristica nascosta non versionata.

### 3.2 Fonte scientifica tracciabile

Ogni parametro che influenza il planner deve essere riconducibile a:

- fonte bibliografica
- razionale
- range di applicabilita'
- versione interna del coefficiente

### 3.3 Distinzione fra scienza e proiezione

Va separato in modo netto:

- **prescrizione scientifica**
- **scelta dell'esercizio concreto**
- **rendering/UX**

### 3.4 Validazione prima della sofisticazione

Nessun nuovo layer “intelligente” ha valore se non e' testabile su una matrice di casi fissi.

### 3.5 Clinical seriousness

Il livello “medico-biomeccanico” non significa fare diagnosi medica.
Significa modellare meglio:

- demand meccanica
- demand coordinativa
- stress per distretto/articolazione
- suitability rispetto all'anamnesi
- costo di recupero

in modo coerente con fonti riconosciute.

---

## 4. Collocazione Dentro KineScore

KineScore deve essere trattato come umbrella method con sottosistemi distinti.

### 4.1 Tassonomia proposta

- **KineScore Core**
  Metodo deterministico di scoring + validazione scientifica.

- **KineVolume**
  Modello volume-driven: MEV / MAV / MRV + dual volume computation.

- **KineProtocol**
  Registro protocolli prescrittivi: livello x frequenza x obiettivo x mode.

- **KineConstraint**
  Motore vincoli biomeccanici, clinici e di recupero.

- **KineSelect**
  Ranker deterministic exercise selection, solo su candidati gia' feasible.

- **KineShield**
  Overlay safety clinico.

- **KineScore Validation Suite**
  Harness di benchmark, regression e audit.

Questa scomposizione e' piu' forte sia scientificamente sia lato IP, perche' trasforma SMART in una famiglia di componenti descrivibili e testabili.

---

## 5. Smart Scientific Method v1 — Architettura Target

## 5.1 Evidence Registry

Nuovo layer concettuale backend:

`api/services/training_science/evidence_registry.py`

Responsabilita':

- registrare fonti, classi di evidenza e riferimenti
- mappare ogni coefficiente a una o piu' fonti
- distinguere:
  - `literature-derived`
  - `expert-calibrated`
  - `internal heuristic pending validation`

### 5.1.1 Schema minimo

Ogni parametro scientifico dovrebbe avere:

- `parameter_id`
- `parameter_name`
- `value`
- `unit`
- `source_code`
- `source_reference`
- `evidence_grade`
- `population_scope`
- `notes`
- `version`

### 5.1.2 Fonti riconosciute da ancorare

Almeno queste, gia' presenti nel progetto:

- NSCA
- ACSM
- Schoenfeld
- Israetel / RP
- Helms
- Bompa
- Contreras
- Alentorn-Geli
- Sahrmann
- Zourdos
- WHO
- AHA
- ESH/ESC

Obiettivo: nessun coefficiente “vive solo in codice”.

---

## 5.2 Protocol Registry

Questo e' il cuore del salto metodologico.

Nuovo layer:

`api/services/training_science/protocol_registry.py`

Il planner non deve “inventare il comportamento” da poche enum.
Deve istanziare un protocollo esplicito selezionato da una matrice.

### 5.2.1 Dimensioni della matrice

- **Livello**
  - beginner
  - intermedio
  - avanzato

- **Frequenza**
  - 2x
  - 3x
  - 4x
  - 5x
  - 6x

- **Obiettivo**
  - forza
  - ipertrofia
  - tonificazione
  - resistenza
  - dimagrimento

- **Mode**
  - general
  - performance
  - clinical

### 5.2.2 Esempio di protocol ID

- `beginner_general_3x_tonificazione_full_body_v1`
- `intermediate_performance_4x_ipertrofia_upper_lower_v1`
- `advanced_performance_5x_forza_upper_lower_plus_v1`
- `beginner_clinical_3x_tonificazione_full_body_low_skill_v1`

### 5.2.3 Cosa definisce un protocollo

Ogni protocollo deve dichiarare:

- split ammessi
- pattern exposure minima/massima
- target di distribuzione tra sessioni
- massimale di slot/sessione
- profilo accessori obbligati
- vincoli di recovery overlap
- limiti di skill demand
- suitability families per livello
- limiti su ballistic / impact / coordination demand
- relazione con safety/clinical mode

Il planner non deve piu' partire da “costruisco e poi correggo”.
Deve partire da:

`protocol -> vincoli -> composizione -> analisi`

---

## 5.3 Constraint Engine

Nuovo layer:

`api/services/training_science/constraint_engine.py`

Qui va definita la grammatica dei vincoli.

### 5.3.1 Tipi di vincolo

- **Volume constraints**
  - MEV/MAV/MRV
  - minimo e massimo per distretto

- **Frequency constraints**
  - esposizioni minime e massime per settimana
  - soglie di “true stimulus per session”

- **Balance constraints**
  - push:pull
  - push_h:push_v
  - pull_h:pull_v
  - quad:ham
  - anterior:posterior

- **Recovery constraints**
  - overlap massimo tra sessioni contigue
  - budget di posterior chain
  - budget di scapular load
  - budget di axial load

- **Suitability constraints**
  - livello skill ammesso
  - impact/ballistic demand
  - coordination demand
  - equipment availability

- **Clinical constraints**
  - hard disincentive families
  - allowed with modification
  - contextual caution

### 5.3.2 Output del constraint engine

Il motore deve poter dire per ogni scelta:

- `allowed`
- `discouraged`
- `infeasible_for_auto_draft`

Questo e' fondamentale: oggi il ranker fa parte di questo lavoro.
Domani deve solo consumare un risultato di feasibility gia' deciso.

---

## 5.4 Canonical Plan Engine

Il planner v2 deve essere rifattorizzato con fasi piu' formali:

1. **Protocol Selection**
2. **Session Skeleton**
3. **Volume Allocation**
4. **Frequency Satisfaction**
5. **Balance Satisfaction**
6. **Recovery Budget Satisfaction**
7. **Canonical Validation**

### 5.4.1 Struttura ideale

`plan_builder.py` va progressivamente spezzato in:

- `protocol_selector.py`
- `session_skeleton.py`
- `volume_allocator.py`
- `frequency_allocator.py`
- `balance_allocator.py`
- `recovery_allocator.py`
- `canonical_validator.py`

Questo alza moltissimo la dimostrabilita':
ogni fase ha un obiettivo chiaro e misurabile.

### 5.4.2 Regola chiave

L'analyzer non deve piu' essere il posto dove scopriamo il fallimento del planner.
Deve essere il posto dove:

- confermiamo che il planner ha rispettato il protocollo
- spieghiamo il risultato
- produciamo score e warning controllati

---

## 5.5 Projection and Feasibility Layer

Qui vive l'attuale runtime ranker, ma con ruolo ridimensionato.

### 5.5.1 Ordine corretto

1. protocollo decide cosa e' necessario
2. constraint engine decide cosa e' ammissibile
3. ranker ordina solo i candidati feasible
4. draft prende il top candidate

### 5.5.2 Effetto pratico

Un `muscle-up` non deve “perdere per punteggio”.
Deve essere classificato:

- `not suitable for beginner auto-draft`

se esistono alternative beginner-compatible nello stesso slot.

Questa e' una differenza metodologica importante.

---

## 6. Nuovo Modello Scientifico di Demand

Per salire di livello biomeccanico e clinico, SMART deve smettere di trattare l'esercizio solo come:

- pattern
- muscoli primari/secondari
- difficolta'

Serve una tassonomia di demand.

### 6.1 Exercise Demand Vector

Ogni esercizio dovrebbe avere un vettore deterministico:

- `skill_demand`
- `coordination_demand`
- `stability_demand`
- `ballistic_demand`
- `impact_demand`
- `axial_load_demand`
- `shoulder_complex_demand`
- `lumbar_load_demand`
- `grip_demand`
- `metabolic_demand`

### 6.2 Perche' e' fondamentale

Con questo vettore:

- un `muscle-up` non e' solo `pull_v`
- un `box jump` non e' solo `squat`
- un `shoulder press` e un `landmine press` non hanno lo stesso costo clinico

Questo e' il vero salto “medico biomeccanico” che rende il sistema piu' forte.

---

## 7. Validation Harness — Cuore della Dimostrabilita'

Senza questo, non c'e' metodo certificabile.

Nuovo layer:

`tests/training_science/validation_matrix/`

### 7.1 Casi minimi obbligatori

Per ogni release scientifica devono esistere casi congelati almeno per:

- beginner 3x tonificazione general
- beginner 4x tonificazione general
- intermedio 3x forza general
- intermedio 4x ipertrofia performance
- avanzato 5x ipertrofia performance
- clinical 3x tonificazione

### 7.2 Cosa verificare

- split scelto
- pattern exposure
- balance ratios
- frequency minima
- recovery overlap
- suitability del draft
- warning attesi
- score composito

### 7.3 Tipi di test

- **Invariant tests**
  Il protocollo non puo' violare certi limiti hard.

- **Snapshot tests**
  Per casi benchmark, i risultati attesi devono restare stabili.

- **Tolerance tests**
  Alcuni valori possono oscillare entro un range.

- **Expert comparison tests**
  Piano SMART vs piano esperto umano su dataset anonimizzato.

### 7.4 Output research-grade

Ogni generazione dovrebbe poter essere auditata con:

- `protocol_id`
- `evidence_version`
- `constraint_version`
- `planner_version`
- `ranker_version`
- `decision_trace`

Questo e' cruciale per universita' e IP.

---

## 8. Relazione con Brevetto e Universita'

Per essere forte in chiave IP e scientifica, il sistema deve poter affermare:

1. che esiste un **metodo computazionale deterministico**
2. che il metodo e' **strutturato in protocolli e vincoli espliciti**
3. che ogni scelta e' **spiegabile e tracciabile**
4. che il metodo e' **validato su benchmark congelati**
5. che il backend produce una **prescrizione tecnica** e non solo una lista di esercizi

La forza non viene dal numero di patch.
Viene dalla catena:

`fonte -> coefficiente -> protocollo -> vincolo -> canonico -> draft -> analisi -> validazione`

---

## 9. Roadmap Tecnica Consigliata

### Fase A — Method Formalization

Obiettivo: chiudere il linguaggio del sistema.

Deliverable:

- `smart_scientific_method.md` / questa spec
- `protocol_registry.py` design
- `constraint schema` design
- definizione del `demand vector`

### Fase B — Protocol Registry v1

Obiettivo: codificare almeno i protocolli core.

Target minimo:

- beginner 3x tonificazione general
- beginner 4x tonificazione general
- intermedio 4x ipertrofia general
- avanzato 5x forza/performance

### Fase C — Constraint Engine v1

Obiettivo: spostare fuori da `plan_builder.py` i vincoli hard.

### Fase D — Canonical Planner v2

Obiettivo: ridurre le correzioni patch-like in favore di fasi formali.

### Fase E — Validation Matrix v1

Obiettivo: congelare casi benchmark e aprire la strada al confronto con esperti.

### Fase F — KineScore White Paper / Collaboration Pack

Obiettivo: produrre asset accademico/IP-ready.

---

## 10. Anti-Pattern da Vietare Da Ora

- aggiungere nuove patch locali senza decidere se appartengono a:
  - protocol registry
  - constraint engine
  - planner
  - ranker

- trattare un esercizio solo come `pattern + muscle score`

- correggere il draft quando il problema e' nel canonico

- correggere il canonico quando il problema e' di suitability del draft

- introdurre un coefficiente senza:
  - fonte
  - razionale
  - versione

- usare l'analyzer come strumento primario di scoperta bug del planner

---

## 11. Prossimo Step Raccomandato

Il prossimo step corretto non e' un altro tuning locale.

E':

1. creare **Protocol Registry Spec v1**
2. definire il **Constraint Schema v1**
3. scegliere le prime 4-6 celle della matrice da implementare come protocolli ufficiali

Solo dopo ha senso tornare a patch runtime.

---

## 12. Sintesi Finale

SMART puo' diventare un metodo forte solo se smette di essere un planner che si corregge via micro-patch
e diventa un **protocol engine deterministico, evidence-linked, biomechanically constrained, validated by matrix**.

Questo e' il livello giusto per:

- collaborazione universitaria
- white paper serio
- credibilita' scientifica
- base difendibile lato marchio/metodo/IP
- crescita del KineScore come sistema e non come feature
