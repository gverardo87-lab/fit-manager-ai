# KineScore Engine — Piano di Sviluppo Scientifico

> Piano strategico per affermare FitManager come unico CRM chinesiologico
> con motore deterministico a 14 dimensioni.

Data: 2026-03-06
Stato: DRAFT — In affinamento pre-implementazione

---

## Fase 0: Affinamento Motore Deterministico (PRIORITA' MASSIMA)

Prima di brevettare o pubblicare, il motore DEVE produrre risultati corretti.

### 0.1 — Fix Anti-Hub Dilution (Volume Realistico) ✅ DONE

**Problema**: dorsali, spalle, glutei, core accumulano troppi set come secondari/stabilizzatori.

**Fix implementati**:
- `patternToMuscleRoles()`: mappa pattern→{primari, secondari} differenziati.
  Core RIMOSSO da squat/hinge secondari (stabilizzatore, non sinergico)
- `computeEstimatedCoverage()`: crediti differenziati PRIMARY=1.0, SECONDARY=0.35
  (sostituisce flat AVG_CREDIT=0.8 che gonfiava hub muscles)
- Slot `muscoli_target` contiene solo primari — lo scorer cerca match primario

### 0.2 — Smart Plan Generation Bilanciata ✅ DONE (Deep Rewrite)

**Problema originale**: programmazioni intelligenti scompensate — muscoli in eccesso/deficit.
**Diagnosi profonda (7 problemi radicali)**:
- P1: Disconnessione stima pre-fill vs realta' post-fill
- P2: Validazione operava su stima, non su esercizi reali
- P3: fillSmartPlan "fire and forget" senza feedback loop
- P4: Pool carry/rotation piccolo (8 ciascuno) + scoring punitivo
- P5: Volume set fisso, non differenziato per muscolo grande/piccolo
- P6: Accessori tutti 3×10-15, ignorando raccomandazioni NSCA per gruppo
- P7: Stima pre-fill usava serie uniformi (non reali)

**Fix implementati (deep rewrite)**:
- **SPLIT_PATTERNS**: `"core"` → `"carry"` (Lower) / `"rotation"` (Upper) per varieta' funzionale
- **fillSmartPlan 2-phase**: Fase 1 = greedy fill 14D. Fase 2 = `computeRealCoverage()`
  sugli esercizi REALI assegnati + swap optimization con top-5 alternative (3 pass, min score 60%)
- **ACCESSORY_VOLUME**: serie/rep per muscolo (polpacci 4×15-20, bicipiti 2×10-15, petto 3×8-12)
- **scoreMuscleMatch v3**: pattern floor 0.5 per esercizi con pattern esatto ma muscoli DB diversi
- **isPPL detection**: aggiornata per carry/rotation come shared patterns
- Pass 3 validazione pre-fill + Fase 2 post-fill = doppio layer di bilanciamento

### 0.3 — Template Esercizi (Gap vs EvolutionFit/Trainerize)

**Problema**: competitor forti su template pre-costruiti e generazione smart.
I nostri template sono basilari (Beginner/Intermedio/Avanzato).

**Obiettivo**: libreria template professionale comparabile ai competitor.

**Azioni**:
- Analizzare template EvolutionFit e Trainerize (struttura, varieta')
- Creare template per obiettivo (forza, ipertrofia, dimagrimento, riabilitazione, sport-specifico)
- Template per split (PPL, Upper/Lower, Full Body, Bro Split)
- Template per attrezzatura disponibile (solo corpo libero, home gym, palestra completa)
- Template per condizioni speciali (gravidanza, over 60, post-infortunio)

---

## Fase 1: Naming & Protezione IP (Settimane 1-4)

### 1.1 — Nome del Metodo
- Proposta: "KineScore" (Kine = chinesiologia + Score = punteggio composito)
- Sotto-componenti: KineScore-14D, KineShield, KineTrack, KineVolume
- Deposito marchio UIBM (~200 EUR)

### 1.2 — Protezione Legale
- Marchio registrato: "KineScore" presso UIBM
- Brevetto modello di utilita': metodo computazionale 14D + credit dilution + safety mapping
- Copyright: deposito SIAE del white paper

---

## Fase 2: White Paper & Validazione (Settimane 2-8)

### 2.1 — White Paper Tecnico
```
"KineScore: A Deterministic 14-Dimensional Scoring Method
for Exercise Selection in Personalized Training Programs"

Struttura:
1. Abstract
2. Introduction — gap nei software fitness attuali
3. Related Work — PT Distinction, Trainerize, Everfit, EvolutionFit, My PT Hub
4. The KineScore Method
   4.1 Data Foundation (taxonomy, 311 esercizi, 53 muscoli, 47 condizioni)
   4.2 14-Dimensional Scoring (formule, pesi, rationale)
   4.3 Anti-Hub Credit Dilution System
   4.4 Clinical Safety Mapping (80 pattern rules)
   4.5 Plan Generation (2-pass accessory system)
5. Clinical Analysis Engine (5 moduli)
6. Implementation — TypeScript/Python, zero-cloud, deterministico
7. Validation — case studies con dati anonimizzati
8. Discussion & Future Work
9. References
```

### 2.2 — Validazione Empirica
- Dati reali anonimizzati (clienti Chiara)
- 5-10 schede generate e validate da chinesiologo certificato
- Metriche: safety score medio, coverage muscolare %, conflitti clinici

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

### 4.1 — Periodizzazione (P0 — Gap Critico)
- Mesocicli (4-6 settimane) con obiettivo specifico
- Deload automatico (-40% volume)
- Progressione carico: lineare o ondulata
- Fasi: accumulo → intensificazione → realizzazione → deload
- Nuovo scorer (dimensione 15): "Periodization Fit"

### 4.2 — RPE/RIR (P1)
- Scala percezione sforzo soggettivo
- RPE target per slot basato su fase mesociclo + livello cliente

### 4.3 — Frequenza Muscolare Ottimale (P1)
- Schoenfeld 2016: 2x/settimana > 1x per ipertrofia
- Nuovo scorer: penalizzare muscoli allenati 1x/sett

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
| OMS (WHO) | — | BMI, WHR |
| ACSM | 10th ed. | Massa grassa %, velocita' perdita peso |
| AHA | — | FC riposo |
| ESH/ESC | 2023 | Pressione arteriosa |
| Kouri et al. | 1995 | FFMI |
| NSCA | — | Strength benchmarks, volume targets |
| Krieger | 2010 | Meta-analisi dose-risposta volume |
| Schoenfeld | 2017 | Target ipertrofia |
| Schoenfeld | 2016 | Frequenza muscolare ottimale |

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
| Scorer composito | 14 dimensioni |
| Moduli analisi clinica | 5 |
| Fonti scientifiche | 9 peer-reviewed |

---

## Roadmap Sintetica

```
FASE 0 (ORA):   Affinamento motore — dilution, bilanciamento, template
MESE 1:         Nome metodo + deposito marchio + inizio white paper
MESE 2:         White paper completato + validazione dati reali
MESE 3:         Deposito brevetto + periodizzazione (P0)
MESE 4:         RPE/RIR + frequenza muscolare + beta 10 chinesiologi
MESE 5:         Pubblicazione + presentazione AICPE
MESE 6:         Landing page + demo + lancio "v1.0 Scientific"
```

---

*Questo piano e' la guida strategica. La Fase 0 e' prerequisito a tutto il resto.*
