# KineScore Engine — Piano di Sviluppo Scientifico

> Piano strategico per affermare FitManager come unico CRM chinesiologico
> con motore deterministico a 14 dimensioni + Training Science Engine backend.

Data: 2026-03-07
Stato: Fase 0-0e DONE, Fase 4.1 DONE — In corso integrazione frontend

---

## Fase 0: Motore Deterministico Frontend (COMPLETATA)

### 0.1 — Fix Anti-Hub Dilution (Volume Realistico) DONE

- `patternToMuscleRoles()`: mappa pattern->{primari, secondari} differenziati
- `computeEstimatedCoverage()`: crediti differenziati PRIMARY=1.0, SECONDARY=0.35
- Slot `muscoli_target` contiene solo primari

### 0.2 — Smart Plan Generation Bilanciata DONE (Deep Rewrite)

- **fillSmartPlan 2-phase**: greedy fill 14D + `computeRealCoverage()` con swap optimization
- **ACCESSORY_VOLUME**: serie/rep per muscolo (NSCA/Schoenfeld 2017)
- **scoreMuscleMatch v3**: pattern floor 0.5, normalizeDifficulty EN->IT
- Pass 3 validazione + Fase 2 swap = doppio layer di bilanciamento

### 0.3 — Template Esercizi

**Obiettivo futuro**: libreria template professionale per obiettivo, split, attrezzatura, condizioni speciali.

---

## Fase 0b: Training Science Engine Backend (COMPLETATA)

> **Breakthrough architetturale**: motore scientifico deterministico nel backend.
> 10 moduli Python, ~2000 LOC, ogni numero con fonte bibliografica.

### Implementazione (3 sprint)

**Sprint A+B — Fondamenta + Audit scientifico**:
- 10 moduli in `api/services/training_science/`
- Matrice EMG 18x15 con dual volume (effective vs hypertrophy)
- Volume model MEV/MAV/MRV con invariante verificato
- Audit scientifico: 6 correzioni evidence-based, score +38%

**Sprint C — Periodizzazione**:
- Mesociclo a blocchi (accumulazione -> intensificazione -> overreaching -> deload)
- Durata per livello: principiante 4, intermedio 5, avanzato 6 settimane
- Volume interpolato linearmente, deload a 50% (Helms 2019)

**Sprint D — API REST**:
- 5 endpoint in `api/routers/training_science.py`
- POST /plan, /analyze, /mesocycle + GET /parameters, /volume-targets
- Computazione pura (zero DB), JWT auth

### Spec dettagliata

Vedi `docs/upgrades/specs/TRAINING-SCIENCE-SPEC.md`

---

## Fase 0c: Consolidamento SSoT Frontend/Backend (IN CORSO)

> **ADR-001 (2026-03-07)**: Single Source of Truth Scientifica.
> Il backend e' l'UNICA fonte di dati scientifici.
> Il frontend consuma via API REST, mai duplica.

### Principio guida

Se un numero ha una fonte bibliografica → vive SOLO in `api/services/training_science/`.
Il frontend lo fetcha via `hooks/useTrainingScience.ts` e lo cacha con React Query.

### Scope del refactoring

**smart-programming.ts (1868 LOC monolite) → smart-programming/ (5 moduli, ~670 LOC)**

| Step | Azione | File |
|------|--------|------|
| 1 | Creare `hooks/useTrainingScience.ts` con 5 hook per API backend | Nuovo |
| 2 | Spezzare `smart-programming.ts` in 5 moduli (<300 LOC ciascuno) | Refactor |
| 3 | Rimuovere costanti scientifiche duplicate (volume, blueprint, pattern→muscle) | Pulizia |
| 4 | SmartAnalysisPanel → consuma `POST /training-science/analyze` | Migrazione |
| 5 | TemplateSelector → genera via `POST /training-science/plan` | Migrazione |
| 6 | MuscleMapPanel → consuma output di /analyze (coverage per muscolo) | Migrazione |

### Cosa resta nel frontend (UI-only, latenza zero)
- **Scoring 14D** per selezione esercizi live nel builder
- **Profilo client aggregato** (composizione hook locali)
- **Safety breakdown** (conteggio per display)
- **Rendering** (barre, colori, pannelli — pura presentazione)

### Cosa migra al backend (gia' implementato, da connettere)
- Volume targets per muscolo → `GET /training-science/volume-targets`
- Generazione piano → `POST /training-science/plan`
- Analisi 4D (coverage/volume/recovery/balance) → `POST /training-science/analyze`
- Blueprint/split logic → `training_science/split_logic.py`
- Pattern→muscle mapping → `training_science/muscle_contribution.py` (matrice EMG 18×15)

### Dettaglio tecnico
Vedi `docs/upgrades/specs/TRAINING-SCIENCE-SPEC.md` sezione 5.

---

## Fase 0d: SMART Runtime Layers (COMPLETATA)

> **Breakthrough metodologico**: il metodo SMART/KineScore entra nel runtime backend
> con 5 layer di governance scientifica sopra il planner legacy.

### Implementazione (6 UPG, Phases A-E del Runtime Translation Plan)

**Registry layer** (UPG-65):
- 6 protocolli PRT-001..006 con metadata (obiettivo, livello, split, frequenza)
- Evidence registry con anchor bibliografici e classi di evidenza
- Protocol selector deterministico

**Constraint adapter** (UPG-67):
- Valutazione post-build del piano legacy contro i vincoli del protocollo
- 3 severity (hard_fail, soft_warning, optimization_target)
- 4 scope (protocol, weekly_plan, session, adjacent_sessions)

**Feasibility engine** (UPG-67b):
- Pre-ranking filtering: feasible / discouraged / infeasible
- Contatori sintetici allegati al plan-package

**Validation metadata** (UPG-68):
- Envelope auditabile con versioni di tutti i sottosistemi
- Riferimenti ai validation cases del benchmark

**Demand layer** (UPG-69):
- Vettore biomeccanico a 10 dimensioni (0..4) per 18 pattern x 3 difficolta'
- 6 protocol ceilings (PRT-001..006) con limiti per dimensione
- Policy engine deterministico (ceiling + family check)

**Validation harness** (UPG-70):
- 6 benchmark cases (VM-001..006) con 22 check functions
- 3 livelli: invariant (hard gate), snapshot (behavioral), tolerance (range)
- Warning policy: required/allowed/forbidden per caso
- Runner con report e classificazione regressioni

### Architettura (5 submoduli in `api/services/training_science/`)

```
registry/    — 5 file, protocolli + evidenze + selettore
constraints/ — 3 file, tipi + engine read-only
demand/      — 4 file, vettori + ceiling + policy
runtime/     — +3 file (feasibility, validation_metadata, mappings)
validation/  — 3 file, catalogo benchmark + contratti check
```

### Phase F (Legacy Replacement): DEFERRED

Prerequisito: matrice verde su tutti i 6 benchmark con plan-package reale.
Il planner legacy resta attivo come engine sottostante.

### Spec dettagliate

- `UPG-2026-03-07-64` (Runtime Translation Plan)
- `UPG-2026-03-07-65` through `UPG-2026-03-07-70` (implementazione)
- `UPG-2026-03-07-60` (Validation Matrix spec)

---

## Fase 0e: Demand Vector DB + Plan Builder Quality (COMPLETATA)

> **Breakthrough qualitativo**: il demand vector passa da flat defaults (pattern x difficulty)
> a valori per-esercizio nel DB, e il plan builder riceve guardrail scientifici
> che eliminano eccessi di volume e squilibri biomeccanici.

### Demand Vector DB Connection (UPG-2026-03-08-01)

- 10 colonne demand su tabella `esercizi` (migrazione Alembic `faf8d3917048`)
- `resolve_demand_vector()` legge da DB con fallback a pattern x difficulty
- `populate_demand.py`: seed deterministico rule-based per 391 esercizi
- Frontend `Exercise` interface sincronizzata con 10 campi demand
- Feasibility engine e ranker usano vettore DB-backed

### Plan Builder Quality Fixes

- **MAV_max guard**: nessun muscolo oltre MAV × 1.15 in boost/isolation
- **Weekly ceiling**: principiante 35, intermedio 55, avanzato 75 serie raw
- **Full Body A/B/C redesign**: ogni pattern compound compare 2x/settimana (Schoenfeld 2016)
  - A: push_h, pull_h, squat, hinge, calf_raise (orizzontali + gambe)
  - B: push_v, pull_v, squat, hinge (verticali + gambe)
  - C: push_h, push_v, pull_h, pull_v, calf_raise (upper emphasis, gambe a riposo)

### Risultati (beginner 3x general)

| Metrica | Prima | Dopo |
|---------|-------|------|
| Score analisi | 46.8 | 76.5 |
| Muscoli sotto MEV | 2 | 0 |
| Muscoli sopra MAV | 9 | 6* |
| Quad:Ham ratio | 0.42 | 0.94 |
| Warning | 11 | 3 |
| Serie/settimana | 79.8 | 35 |

*6 sopra_mav sono muscoli con MEV=0 (delt_ant, glutei, trapezio) che ricevono
volume collaterale da compound — nessuno sopra MRV, fisiologicamente accettabile.

### Validation Matrix

Score bands ricalibrati per baseline MAV-guarded:
- VM-002: minimum 72 → 60
- VM-003: minimum 78 → 50
- VM-005: minimum 75 → 55

---

## Fase 1: Naming & Protezione IP (Settimane 1-4)

### 1.1 — Nome del Metodo
- Proposta: "KineScore" (Kine = chinesiologia + Score = punteggio composito)
- Sotto-componenti: KineScore-14D, KineShield, KineTrack, KineVolume
- Deposito marchio UIBM (~200 EUR)

### 1.2 — Protezione Legale
- Marchio registrato: "KineScore" presso UIBM
- Brevetto modello di utilita': metodo computazionale 14D + credit dilution + safety mapping
  + Training Science Engine (volume-driven plan generation + periodizzazione)
- Copyright: deposito SIAE del white paper

---

## Fase 2: White Paper & Validazione (Settimane 2-8)

### 2.1 — White Paper Tecnico
```
"KineScore: A Deterministic Multi-Dimensional Scoring Method
for Exercise Selection and Volume-Driven Plan Generation
in Personalized Training Programs"

Struttura aggiornata:
1. Abstract
2. Introduction — gap nei software fitness attuali
3. Related Work — PT Distinction, Trainerize, Everfit, EvolutionFit, My PT Hub
4. The KineScore Method
   4.1 Data Foundation (taxonomy, 311 esercizi, 53 muscoli, 47 condizioni)
   4.2 14-Dimensional Exercise Scoring (formule, pesi, rationale)
   4.3 Anti-Hub Credit Dilution System
   4.4 Clinical Safety Mapping (80 pattern rules)
   4.5 Plan Generation (2-pass frontend + 4-phase backend)
5. Training Science Engine (NUOVO)
   5.1 EMG-Based Muscle Contribution Matrix (18x15, 4-tier)
   5.2 Volume Model: MEV/MAV/MRV (Israetel/Schoenfeld framework)
   5.3 Dual Volume Computation (effective vs hypertrophy)
   5.4 Deterministic Plan Builder (4-phase with feedback loop)
   5.5 4D Plan Analyzer (volume, balance, frequency, recovery)
   5.6 Block Periodization (mesocycle with linear interpolation)
6. Clinical Analysis Engine (5 moduli)
7. Implementation — TypeScript/Python, zero-cloud, deterministico
8. Validation — case studies con dati anonimizzati
9. Discussion & Future Work
10. References
```

### 2.2 — Validazione Empirica
- Dati reali anonimizzati (clienti Chiara)
- 5-10 schede generate e validate da chinesiologo certificato
- Metriche: safety score medio, coverage muscolare %, conflitti clinici
- **NUOVO**: confronto piano backend vs piano manuale esperto

---

## Fase 3: Posizionamento Mercato (Settimane 4-12)

### 3.1 — Competitor Analysis Formale
Feature-by-feature vs PT Distinction, Trainerize, Everfit, EvolutionFit, My PT Hub

### 3.2 — Canali di Lancio
1. Associazioni professionali (AICPE)
2. Pubblicazione settoriale + preprint ResearchGate
3. Demo video workflow completo
4. Landing page dedicata
5. Beta program 10-20 chinesiologi

---

## Fase 4: Evoluzione Scientifica (Mesi 3-6)

### 4.1 — Periodizzazione DONE
- Mesocicli (4-6 settimane) con progressione volume
- Deload automatico a 50%
- Fasi: accumulazione -> intensificazione -> overreaching -> deload
- Implementato in `periodization.py`, esposto via POST /mesocycle

### 4.2 — RPE/RIR (P1)
- Scala percezione sforzo soggettivo
- RPE target per slot basato su fase mesociclo + livello cliente

### 4.3 — Frequenza Muscolare Ottimale (P1)
- Gia' implementata nell'analyzer (warning freq < 2x)
- Prossimo step: scorer dimensione 15 "Periodization Fit"

### 4.4 — Fatigue Management (P2)
- Modello SFR (Stimulus-Fatigue-Recovery)
- Fatica accumulata influenza la programmazione

### 4.5 — Cardio Integration (P2)
- Zone HR, EPOC, condizionamento metabolico

### 4.6 — Nutrition Bridge (P3)
- Suggerimento intake calorico/proteico basato su fase e obiettivo

---

## Fonti Scientifiche Utilizzate

| Fonte | Anno | Applicazione |
|-------|------|-------------|
| OMS (WHO) | -- | BMI, WHR |
| ACSM | 10th ed. | Massa grassa %, velocita' perdita peso |
| AHA | -- | FC riposo |
| ESH/ESC | 2023 | Pressione arteriosa |
| Kouri et al. | 1995 | FFMI |
| NSCA (Haff & Triplett) | 2016 | Strength benchmarks, volume targets, frequenza, ordine |
| Krieger | 2010 | Meta-analisi dose-risposta volume |
| Schoenfeld | 2010, 2017, 2021 | Ipertrofia, volume targets, frequenza |
| Israetel (RP) | 2020 | MEV/MAV/MRV framework, periodizzazione |
| Bompa & Buzzichelli | 2019 | Teoria periodizzazione, supercompensazione |
| Helms | 2019 | Deload protocol |
| Contreras | 2010 | EMG attivazione muscolare |
| Alentorn-Geli | 2009 | Rapporto quad:ham, prevenzione ACL |
| Sahrmann | 2002 | Rapporti biomeccanici push:pull, ant:post |
| Zourdos et al. | 2016 | Validazione periodizzazione ondulata |

---

## Asset Attuali

| Asset | Dimensione |
|-------|-----------|
| Esercizi attivi | 391 (1111 totali) |
| Muscoli anatomici | 53 (15 gruppi) |
| Articolazioni | 15 |
| Condizioni mediche | 47 |
| Mapping muscolo-esercizio | ~1,271 (con EMG %) |
| Mapping articolazione-esercizio | ~299 (con ROM gradi) |
| Mapping condizione-esercizio | ~3,600 |
| Relazioni esercizi | 426 in 32 catene |
| Scorer composito frontend | 14 dimensioni |
| Training Science Engine backend | 10 moduli core + 18 moduli SMART runtime, ~3500 LOC + demand DB |
| Moduli analisi clinica | 5 |
| Fonti scientifiche | 15 peer-reviewed |

---

## Fase 5: Collaborazione Universitaria — Scienze Motorie

> **Obiettivo**: validazione accademica del metodo KineScore + affinamento
> dei coefficienti scientifici in collaborazione con universita' di scienze motorie.

### 5.1 — Preparazione (pre-contatto)

L'architettura SSoT e' progettata per questa fase:
- **Backend Python**: i ricercatori lavorano su codice familiare
- **Moduli indipendenti**: ogni modulo e' testabile e modificabile isolatamente
- **Docstring con fonti**: ogni costante ha la referenza bibliografica
- **Zero dipendenze UI**: i moduli scientifici sono puri (input → output, zero side effects)

### 5.2 — Aree di ricerca congiunta

| Area | Modulo backend | Stato attuale | Contributo accademico atteso |
|------|---------------|---------------|------------------------------|
| Matrice EMG | `muscle_contribution.py` | 18×15, 4 livelli da letteratura | Validazione/correzione con dati EMG reali |
| Volume MEV/MAV/MRV | `volume_model.py` | 45 combinazioni da Israetel | Calibrazione per popolazione italiana |
| Balance ratios | `balance_ratios.py` | 5 rapporti, tolleranze da NSCA | Raffinamento tolleranze per sesso/eta' |
| Safety mapping | `condition_rules.py` | 80 pattern rules | Validazione clinica per condizioni specifiche |
| Scoring 14D | Frontend `scorers.ts` | 14 pesi empirici | Ottimizzazione pesi tramite studio comparativo |
| Periodizzazione | `periodization.py` | Blocchi lineari Helms/Israetel | Modelli DUP, ondulati, autoregolati |

### 5.3 — Workflow collaborativo

```
Ricercatore (Python)                    Sviluppatore (Full-stack)
  |                                        |
  |  Modifica coefficiente in              |
  |  volume_model.py con fonte             |
  |                                        |
  |  → Pull Request con:                   |  Review: fonte valida?
  |    - Valore precedente                 |  Test: invariante rispettato?
  |    - Valore nuovo + fonte              |  Deploy: zero impatto frontend
  |    - Razionale scientifico             |  (SSoT: frontend fetcha da API)
  |                                        |
  v                                        v
  Validazione su dati reali (anonimizzati)
```

### 5.4 — Deliverable accademici

1. White paper KineScore (struttura in Fase 2.1)
2. Dataset anonimizzato per riproduzione risultati
3. Benchmark: piano KineScore vs piano esperto umano (5-10 casi)
4. Poster/presentazione per convegno AICPE o SISMES

---

## Roadmap Sintetica

```
FASE 0  (DONE):  Motore frontend — dilution, bilanciamento, scoring
FASE 0b (DONE):  Training Science Engine backend — 10 moduli + API
FASE 0c (ORA):   Consolidamento SSoT — frontend consuma backend via API
FASE 0d (DONE):  SMART Runtime Layers — registry, constraints, demand, validation
FASE 0e (DONE):  Demand Vector DB + Plan Builder Quality — per-exercise vectors, MAV guard
FASE 1:          Nome metodo + deposito marchio + inizio white paper
FASE 2:          White paper completato + validazione dati reali
FASE 3:          Deposito brevetto + posizionamento mercato
FASE 4:          Evoluzione scientifica (RPE, fatigue, cardio, nutrition)
FASE 5:          Collaborazione universita' scienze motorie
```

---

*Questo piano e' la guida strategica. La Fase 0c (SSoT) e' il prerequisito
per tutto il resto: senza architettura pulita, non si scala ne' si brevetta.*
