# KineScore Engine — Piano di Sviluppo Scientifico

> Piano strategico per affermare FitManager come unico CRM chinesiologico
> con motore deterministico a 14 dimensioni + Training Science Engine backend.

Data: 2026-03-07
Stato: Fase 0 DONE, Fase 4.1 DONE — In corso integrazione frontend

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

## Fase 0c: Integrazione Frontend (IN CORSO)

> Il frontend consuma il backend scientifico via hook React Query.
> `smart-programming.ts` si riduce a scoring esercizi + utility UI.

### Obiettivi
1. Hook frontend per i 5 endpoint training science
2. SmartAnalysisPanel consuma dati backend (non hardcoded)
3. MuscleMapPanel usa volume dal backend
4. TemplateSelector "Scheda Smart" genera via API
5. Workout builder integra analisi volume live

### Cosa rimane nel frontend
- Exercise scoring 14D (rapido, client-side, dati esercizio locale)
- Safety Engine mapping (gia' backend, hook esistente)
- UI componenti (SmartAnalysisPanel, MuscleMapPanel, ExerciseSelector)

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
| Esercizi attivi | 311 (1059 totali) |
| Muscoli anatomici | 53 (15 gruppi) |
| Articolazioni | 15 |
| Condizioni mediche | 47 |
| Mapping muscolo-esercizio | ~1,271 (con EMG %) |
| Mapping articolazione-esercizio | ~299 (con ROM gradi) |
| Mapping condizione-esercizio | ~3,600 |
| Relazioni esercizi | 426 in 32 catene |
| Scorer composito frontend | 14 dimensioni |
| Training Science Engine backend | 10 moduli, ~2000 LOC |
| Moduli analisi clinica | 5 |
| Fonti scientifiche | 15 peer-reviewed |

---

## Roadmap Sintetica

```
FASE 0  (DONE):  Motore frontend — dilution, bilanciamento, scoring
FASE 0b (DONE):  Training Science Engine backend — 10 moduli + API
FASE 0c (ORA):   Integrazione frontend — hook + UI consuma backend
MESE 1:          Nome metodo + deposito marchio + inizio white paper
MESE 2:          White paper completato + validazione dati reali
MESE 3:          Deposito brevetto + RPE/RIR (P1)
MESE 4:          Frequenza scorer + beta 10 chinesiologi
MESE 5:          Pubblicazione + presentazione AICPE
MESE 6:          Landing page + demo + lancio "v1.0 Scientific"
```

---

*Questo piano e' la guida strategica. La Fase 0b e' il breakthrough architetturale.*
