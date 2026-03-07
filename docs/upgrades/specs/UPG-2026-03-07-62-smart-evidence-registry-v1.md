# UPG-2026-03-07-62 - SMART Evidence Registry v1

> *"La scienza del motore non inizia dal planner.
> Inizia da un registro esplicito di fonti, claim, parametri e limiti di applicabilita'."*

**Data**: 2026-03-07  
**Stato**: ANALYSIS SPEC  
**Ambito**: SMART backend, KineScore, Evidence Layer, Scientific Governance  
**Dipende da**: `UPG-2026-03-07-55`, `UPG-2026-03-07-57`, `UPG-2026-03-07-58`, `UPG-2026-03-07-59`, `UPG-2026-03-07-60`, `UPG-2026-03-07-61`

---

## 1. Obiettivo

Definire `Evidence Registry v1` del nuovo SMART/KineScore.

Questa spec formalizza il layer che collega in modo tracciabile:

- fonti scientifiche
- anchor interni
- claim utilizzabili dal motore
- parametri e coefficienti
- protocolli e vincoli che li consumano

Il suo scopo e' evitare che il backend si basi su:

- costanti disperse nel codice
- riferimenti impliciti
- inferenze non dichiarate
- patch scientifiche non versionate

L'`Evidence Registry` e' il primo elemento che rende il metodo seriamente
auditabile, difendibile e potenzialmente certificabile.

---

## 2. Ruolo Dell'Evidence Registry

Nel modello target:

- `Evidence Registry` = sorgente dichiarata di claim, anchor, classi di evidenza
- `Protocol Registry` = combinazioni supportate e loro identita'
- `Constraint Schema` = traduzione dei claim in limiti machine-checkable
- `Demand Vector` = modellazione biomeccanico-funzionale degli esercizi
- `Validation Harness` = verifica che il sistema usi i claim in modo coerente

Questa separazione e' fondamentale:

- la fonte non e' il protocollo
- il protocollo non e' il coefficiente
- il coefficiente non e' il warning

Serve una catena esplicita:

`source -> anchor -> claim -> parameter -> protocol/constraint -> output -> validation`

---

## 3. Principi Di Design

### 3.1 Source-linked by default

Ogni claim del sistema deve essere ricondotto a uno o piu' anchor.

### 3.2 Evidence is typed

Non tutte le regole hanno lo stesso peso epistemico.
Serve distinguere cosa deriva da letteratura forte, cosa da inferenza
biomeccanica e cosa da calibrazione esperta.

### 3.3 Population-scoped

Ogni claim deve dichiarare il proprio campo di applicabilita':

- beginner / intermediate / advanced
- healthy general / clinical overlay / performance
- upper / lower / global

### 3.4 Versioned and reviewable

Ogni modifica di claim o parametro deve essere versionata.

### 3.5 Runtime-decoupled

Il registry deve poter essere letto dal motore, ma non vivere come logica
sparsa nel planner.

---

## 4. Cosa Deve Contenere

L'`Evidence Registry v1` deve contenere almeno 5 famiglie di entita'.

1. `SourceRecord`
2. `AnchorRecord`
3. `ClaimRecord`
4. `ParameterRecord`
5. `UsageRecord`

Queste 5 famiglie sono sufficienti a costruire il primo layer scientifico
tracciabile.

---

## 5. SourceRecord

`SourceRecord` rappresenta la fonte bibliografica o linee guida.

```python
SourceRecord(
    source_id: str,
    source_code: str,
    title: str,
    authors: list[str],
    year: int,
    source_type: Literal[
        "guideline",
        "position_stand",
        "review",
        "meta_analysis",
        "primary_study",
        "expert_framework",
    ],
    publisher_or_journal: str,
    domain_tags: list[str],
    notes: str | None,
    registry_version: str,
)
```

### Esempi v1

- `SRC-NSCA-2016`
- `SRC-ACSM-2009`
- `SRC-SCHOENFELD-2016`
- `SRC-SCHOENFELD-2017`
- `SRC-ISRAETEL-2020`
- `SRC-HELMS-2019`
- `SRC-SAHRMANN-2002`
- `SRC-ALENTORN-GELI-2009`

---

## 6. AnchorRecord

`AnchorRecord` rappresenta l'anchor operativo usato nel progetto.

Un anchor e' un riferimento stabile e corto, adatto a:

- protocolli
- vincoli
- demand vector
- warning
- validation fixtures

```python
AnchorRecord(
    anchor_id: str,
    anchor_code: str,
    source_id: str,
    label: str,
    summary: str,
    domain_tags: list[str],
    evidence_class: Literal["A", "B", "C"],
    usage_scope: list[str],
    deprecated: bool,
    registry_version: str,
)
```

### Regola v1

- `source_id` punta alla fonte piena
- `anchor_code` e' la stringa corta usata nel motore
- un anchor puo' coprire piu' claim, ma ogni claim deve dichiararlo esplicitamente

---

## 7. ClaimRecord

`ClaimRecord` rappresenta un'affermazione scientifica usabile dal sistema.

Esempi:

- `freq >= 2x` e' generalmente superiore a `1x` per MPS/ipertrofia
- i beginner hanno ceiling di pratica tecnica e recovery diversi dagli advanced
- ballistic/impact demand elevata non e' adatta ai draft low-skill

```python
ClaimRecord(
    claim_id: str,
    claim_code: str,
    anchor_ids: list[str],
    statement: str,
    claim_type: Literal[
        "volume",
        "frequency",
        "balance",
        "recovery",
        "suitability",
        "clinical_overlay",
        "demand_model",
        "periodization",
    ],
    evidence_class: Literal["A", "B", "C"],
    confidence: Literal["high", "moderate", "provisional"],
    population_scope: list[str],
    contraindication_scope: list[str],
    notes: str | None,
    registry_version: str,
)
```

### Regola v1

Il claim non e' ancora un numero.
E' una proposizione usabile, versionata e tracciabile.

---

## 8. ParameterRecord

`ParameterRecord` rappresenta la traduzione computazionale di uno o piu' claim.

Esempi:

- `session_stimulus_threshold = 2.0`
- `max_skill_demand_beginner_general = 1`
- `quad_ham_target_beginner_general = 1.25`

```python
ParameterRecord(
    parameter_id: str,
    parameter_code: str,
    claim_ids: list[str],
    value: str,
    unit: str | None,
    parameter_type: Literal[
        "threshold",
        "target_range",
        "budget",
        "ceiling",
        "floor",
        "categorical_policy",
    ],
    evidence_origin: Literal[
        "literature-derived",
        "expert-calibrated",
        "internal-heuristic-pending-validation",
    ],
    evidence_class: Literal["A", "B", "C"],
    population_scope: list[str],
    notes: str | None,
    version: str,
)
```

### Regola v1

Ogni parametro deve avere almeno:

- `claim_ids`
- `evidence_origin`
- `population_scope`
- `version`

Senza questi campi, il parametro non e' scientificamente governato.

---

## 9. UsageRecord

`UsageRecord` collega i parametri agli oggetti del metodo.

```python
UsageRecord(
    usage_id: str,
    target_type: Literal[
        "protocol",
        "constraint_rule",
        "demand_dimension",
        "validation_case",
        "warning_family",
    ],
    target_id: str,
    parameter_ids: list[str],
    claim_ids: list[str],
    anchor_ids: list[str],
    notes: str | None,
    version: str,
)
```

Questo e' il pezzo che chiude davvero la catena tracciabile.

---

## 10. Evidence Classes v1

Per il registry v1 usiamo 3 classi di evidenza.

### 10.1 Class A

`A = direct_repo_anchor`

Uso quando il progetto ha gia' un anchor forte e riconosciuto nel metodo.

Esempi tipici:

- linee guida NSCA/ACSM
- letteratura Schoenfeld su frequenza/volume

### 10.2 Class B

`B = biomechanical_inference`

Uso quando il claim e' una inferenza biomeccanica forte e coerente,
ma non ancora ridotta a una fonte univoca di alto livello nel registry.

Esempi tipici:

- alcune dimensioni del `Demand Vector`
- alcune suitability families

### 10.3 Class C

`C = provisional_expert_model`

Uso quando il claim serve operativamente ma e' ancora in attesa di
validazione forte o consolidamento bibliografico.

Esempi tipici:

- calibrazioni iniziali di budget
- regole transitorie di tuning protocol-driven

### Regola v1

Un claim `C` puo' esistere.
Ma non puo' fingersi `A`.

---

## 11. Evidence Origin v1

Per evitare ambiguita', il registry deve distinguere anche l'origine
computazionale del parametro.

### 11.1 literature-derived

Il parametro discende quasi direttamente dalla fonte.

### 11.2 expert-calibrated

Il parametro nasce da una traduzione progettuale della letteratura.

### 11.3 internal-heuristic-pending-validation

Il parametro e' ancora una soluzione interna utile, ma non ancora difendibile
come scelta scientifica forte.

Questa distinzione e' essenziale per onesta' metodologica.

---

## 12. Population Scope v1

Ogni claim/parametro deve dichiarare il proprio `population_scope`.

### Esempi minimi v1

- `beginner_general`
- `intermediate_general`
- `advanced_performance`
- `beginner_clinical_low_skill`
- `upper_lower_hypertrophy`
- `full_body_beginner`

### Regola

Se un parametro non ha `population_scope`, non puo' essere considerato
scientificamente governato.

---

## 13. Domain Tags v1

Per rendere il registry interrogabile, servono `domain_tags`.

### Set minimo consigliato

- `volume`
- `frequency`
- `balance`
- `recovery`
- `suitability`
- `clinical`
- `demand`
- `periodization`
- `protocol_selection`
- `score_validation`

Questi tag permettono:

- query future
- audit rapidi
- mapping automatici

---

## 14. Collegamento Con I Protocolli

Ogni `ProtocolDefinition` deve poter dichiarare i propri anchor principali.

Esempio concettuale:

```python
ProtocolEvidenceMap(
    protocol_id: str,
    anchor_ids: list[str],
    claim_ids: list[str],
    parameter_ids: list[str],
)
```

Questo permette di dire, in modo tracciabile:

- quali fonti sostengono `PRT-002`
- quali claim giustificano i ceiling beginner
- quali parametri implementano quei claim

---

## 15. Collegamento Con Il Demand Vector

Il `Demand Vector v1` deve usare il registry in due modi:

1. per giustificare le dimensioni del vettore
2. per giustificare i ceiling dei protocolli su quelle dimensioni

Quindi ogni dimensione del vettore deve avere almeno:

- `anchor_ids`
- `evidence_class`
- `rationale_tags`

Esempio:

- `skill_demand` -> `A/B`
- `ballistic_demand` -> `A/B`
- `shoulder_complex_demand` -> `B`
- `metabolic_demand` -> `B/C`

---

## 16. Collegamento Con La Validation Matrix

Ogni `ValidationCase` deve poter dichiarare:

- quali `claim_ids` sta realmente stressando
- quali `parameter_ids` non possono regredire

Esempio:

- `VM-002`
  - stressa i claim beginner general 3x su suitability, frequency e recovery
  - non deve regredire su:
    - beginner no advanced draft
    - low ballistic suitability
    - minimum pattern coverage full_body_abc

Questo rende la regressione non solo tecnica, ma anche epistemica.

---

## 17. Output Minimi Del Registry v1

Il registry deve poter produrre almeno questi 4 output logici.

### 17.1 Source catalog

Lista delle fonti note al metodo.

### 17.2 Anchor catalog

Lista corta degli anchor riusabili dai protocolli.

### 17.3 Claim catalog

Lista delle affermazioni scientifiche operative.

### 17.4 Parameter catalog

Lista dei numeri e delle policy usate dal motore.

---

## 18. Non-Goals del v1

Questa spec non fa ancora:

- mapping completo di tutti i parametri runtime attuali
- normalizzazione DOI/PMID
- valutazione critica paper-by-paper
- import automatico bibliografico
- interfaccia UI del registry

Il v1 chiude il contratto logico, non il popolamento completo.

---

## 19. Roadmap Immediata

Dopo questa spec, i passi corretti sono:

1. `Catalog Mapping Spec v1`
   collegare esercizi e `Demand Vector`

2. `Runtime Translation Plan`
   decidere dove vivono i modelli runtime del registry

3. `Evidence Population Pass v1`
   popolare i primi `SourceRecord`, `AnchorRecord`, `ClaimRecord`, `ParameterRecord`
   per `PRT-001 ... PRT-006`

4. `Validation Harness Implementation v1`
   legare benchmark e claim del registry

---

## 20. Fonti e Anchor minimi v1

Il registry v1 deve partire almeno dagli anchor gia' allineati nel progetto:

- `NSCA-2016`
- `ACSM-2009`
- `SCHOENFELD-2016`
- `SCHOENFELD-2017`
- `ISRAETEL-2020`
- `HELMs-2019`
- `SAHRMANN-2002`
- `ALENTORN-GELI-2009`
- `BOMPA-2019`
- `CONTRERAS-2010`
- `ZOURDOS-2016`

La regola metodologica e' semplice:

se un parametro influenza SMART/KineScore ma non riesce ad agganciarsi almeno
a un `AnchorRecord`, deve essere dichiarato `internal-heuristic-pending-validation`.
