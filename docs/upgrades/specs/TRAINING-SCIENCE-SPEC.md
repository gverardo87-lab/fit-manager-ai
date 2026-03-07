# Training Science Engine — Specifica Architetturale

> *"Senza una metodologia codificata, il software e' un calcolatore.
> Con una metodologia codificata, il software e' un sistema esperto."*

**Stato**: IMPLEMENTED — Phase 1 + 2 + 3 completate, API esposta
**Autore**: Claude Opus 4.6 + gvera
**Obiettivo**: Fondazione scientifica per la programmazione dell'allenamento
**Branch**: `codex_02`

---

## 1. Stato Implementazione

### Cosa abbiamo costruito

`api/services/training_science/` — **10 moduli** indipendenti (~2000 LOC) con:
- Architettura a 3 fasi (Fondamenta + Generazione + Periodizzazione)
- Matrice EMG 18 pattern x 15 muscoli con 4 soglie contribuzione
- Volume model MEV/MAV/MRV per muscolo x livello (Israetel RP 2020)
- Generatore deterministico a 4 fasi con feedback loop
- Analizzatore 4D (volume, balance, frequenza, recupero)
- Periodizzazione a blocchi con mesociclo (4-6 settimane)
- 5 endpoint REST (`/api/training-science/*`)
- Ogni numero ha fonte bibliografica nel docstring

### Cosa sostituisce

`smart-programming.ts` (1300 LOC) era un monolite che:
- Hardcodava 15 blueprint (5 freq x 3 livelli) come array di slot
- Usava 4 slot type criptici (CP/CS/IT/IA) che mescolavano ruolo e volume
- Contava il volume come "serie per muscolo" con crediti approssimati (1.0 primario, 0.35 secondario)
- Mescolava 6 responsabilita' in un file solo

**Il nuovo sistema e' il MOTORE SCIENTIFICO**: genera piani basati su principi,
il frontend li consuma e li presenta. I dati scientifici vivono nel backend.

---

## 2. Fondamenta Scientifiche (Implementate)

### 2.1 Le 6 Variabili della Programmazione (NSCA, Haff & Triplett 2016)

| Variabile | Cosa controlla | Unita' | Modulo |
|-----------|---------------|--------|--------|
| **Intensita'** | Carico relativo | % 1RM | `principles.py` |
| **Volume** | Quantita' di lavoro | serie x ripetizioni | `volume_model.py` |
| **Frequenza** | Quante volte/settimana per muscolo | sessioni/sett | `split_logic.py` |
| **Densita'** | Rapporto lavoro/riposo | secondi riposo | `principles.py` |
| **Selezione esercizi** | Quali movimenti | pattern + muscolo target | `muscle_contribution.py` |
| **Ordine esercizi** | Sequenza nella sessione | multi-art -> mono-art | `session_order.py` |

### 2.2 Obiettivi di Allenamento — Parametri Evidence-Based

Implementati in `principles.py` con struttura `ParametriCarico` (Pydantic).

```
                    FORZA      IPERTROFIA  RESISTENZA  DIMAGRIMENTO  TONIFICAZIONE
Intensita' %1RM    85-100     65-85       50-65       65-80         60-75
Rep range          1-5        6-12        15-25       8-15          10-15
Serie compound     3-5        3-4         2-3         3-4           2-3
Serie isolation    2-3        3-4         2-3         2-3           2-3
Riposo compound    180-300    90-120      30-60       45-90         60-90
Riposo isolation   120-180    60-90       30-45       30-60         45-60
Freq/muscolo/sett  2-3        2           2-3         2-3           2
% compound         80%        60%         50%         70%           60%
Fattore volume     0.70       1.00        0.60        0.80          0.70
```

Fonti: NSCA (2016), ACSM (2009), Schoenfeld (2010, 2017, 2021), Krieger (2010).

### 2.3 Volume per Gruppo Muscolare — Modello MEV/MAV/MRV

Implementato in `volume_model.py`. Formato: `(MEV, MAV_min, MAV_max, MRV)`.
Valori per obiettivo IPERTROFIA. Altri obiettivi scalano via `fattore_volume`.

15 gruppi muscolari x 3 livelli = 45 combinazioni.
Ogni combinazione ha 4 soglie con nota bibliografica.

**Invariante verificato**: `MEV <= MAV_min <= MAV_max <= MRV` per ogni combinazione.
Bug trovato e corretto nell'audit scientifico (quadricipiti/femorali avanzato avevano MRV < MAV_max).

### 2.4 Matrice di Contribuzione Muscolare (EMG-based)

Implementata in `muscle_contribution.py`. 18 pattern x 15 muscoli.

Scala 4 livelli:
- **1.0** = motore primario (attivazione EMG > 70%)
- **0.7** = sinergista maggiore (attivazione 40-70%)
- **0.4** = sinergista minore (attivazione 20-40%)
- **0.2** = stabilizzatore (attivazione 10-20%)

**Dual volume computation** (innovazione chiave):
- `compute_effective_sets()` — volume meccanico grezzo (per balance/recovery)
- `compute_hypertrophy_sets()` — volume ipertrofico pesato (per MEV/MAV/MRV)
  - Contributi >= 0.7 -> peso 1.0 (stimolo diretto)
  - Contributo 0.4 -> peso 0.5 (sinergismo ridotto)
  - Contributo 0.2 -> peso 0.0 (stabilizzazione, non conta per crescita)
  - Fonte: Schoenfeld 2017 — soglia EMG 40% MVC per stimolo ipertrofico

### 2.5 Split Logic e Frequenza

Implementato in `split_logic.py`.

| Frequenza | Split | Sessioni |
|-----------|-------|----------|
| 2x/sett | Full Body | [FB, FB] |
| 3x/sett | Full Body | [FB, FB, FB] |
| 4x/sett | Upper/Lower | [U, L, U, L] |
| 5x/sett | Upper/Lower | [U, L, U, L, U] |
| 6x/sett | Push/Pull/Legs | [Push, Pull, Legs, Push, Pull, Legs] |

**Frequency clamp** (NSCA 2016):
- Principiante: max 3x/settimana
- Intermedio: max 5x/settimana
- Avanzato: max 6x/settimana

### 2.6 Rapporti Biomeccanici (Balance Ratios)

Implementati in `balance_ratios.py`. 5 rapporti con tolleranze calibrate:

| Rapporto | Target | Tolleranza | Fonte |
|----------|--------|------------|-------|
| Push : Pull | 1.00 | +/- 0.15 | NSCA, Sahrmann 2002 |
| Push H : Push V | 2.00 | +/- 0.25 | NSCA, pratica clinica |
| Pull H : Pull V | 1.00 | +/- 0.35 | NSCA (asimmetria fisiologica) |
| Quad : Ham | 1.25 | +/- 0.30 | Alentorn-Geli 2009 (individuale) |
| Anteriore : Posteriore | 0.85 | +/- 0.15 | Sahrmann, Janda |

### 2.7 Ordine Esercizi nella Sessione

Implementato in `session_order.py`. Gerarchia fisiologica NSCA:

```
1. WARMUP           -> attivazione, mobilita'
2. COMPOUND_HEAVY   -> squat, hinge, push_h (alto SNC)
3. COMPOUND_LIGHT   -> pull_h, pull_v, push_v (SNC moderato)
4. ISOLATION        -> curl, lateral_raise, leg_curl
5. CORE_STABILITY   -> core, rotation, carry
6. COOLDOWN         -> stretching, mobilita'
```

---

## 3. Architettura Implementata

### 3.1 Struttura Backend (10 moduli)

```
api/services/training_science/
  __init__.py              — Re-export pubblico (170 LOC)

  Phase 1 — Fondamenta scientifiche:
    types.py               — Enum e modelli Pydantic (vocabolario del dominio)
    principles.py          — Parametri di carico per obiettivo (NSCA/ACSM/Schoenfeld)
    muscle_contribution.py — Matrice contribuzione EMG + volume ipertrofico pesato
    volume_model.py        — MEV/MAV/MRV per muscolo x livello + classificazione
    balance_ratios.py      — Rapporti biomeccanici push:pull, quad:ham, ant:post

  Phase 2 — Generazione piani:
    split_logic.py         — Frequenza -> split ottimale + struttura sessioni
    session_order.py       — Ordinamento fisiologico (SNC-demanding first)
    plan_builder.py        — Generatore volume-driven a 4 fasi con feedback loop
    plan_analyzer.py       — Analisi 4D (volume, balance, frequenza, recupero)

  Phase 3 — Periodizzazione:
    periodization.py       — Mesociclo (progressione volume + deload)
```

### 3.2 API REST (5 endpoint)

Router: `api/routers/training_science.py`
Prefix: `/api/training-science`
Auth: JWT obbligatorio. Zero DB — computazione pura.

| Endpoint | Metodo | Input | Output | Descrizione |
|----------|--------|-------|--------|-------------|
| `/plan` | POST | `{frequenza, obiettivo, livello}` | `TemplatePiano` | Genera piano volume-driven |
| `/analyze` | POST | `{piano: TemplatePiano}` | `AnalisiPiano` | Analisi 4D completa |
| `/mesocycle` | POST | `{piano_base: TemplatePiano}` | `Mesociclo` | Genera mesociclo periodizzato |
| `/parameters/{obiettivo}` | GET | path param | `ParametriCarico` | Parametri di carico NSCA |
| `/volume-targets` | GET | `?livello=X&obiettivo=Y` | `list[VolumeTarget]` | Target MEV/MAV/MRV |

### 3.3 Principi Architetturali

1. **Separation of Concerns**: ogni file ha UNA responsabilita'
2. **Data over Code**: la scienza e' nei dati (costanti, tabelle), non nella logica
3. **Composability**: ogni modulo e' usabile indipendentemente
4. **Traceability**: ogni costante ha la fonte bibliografica nel docstring
5. **No Magic Numbers**: ogni numero ha un nome e una spiegazione
6. **Testability**: input/output puri, zero side effects, unit test semplici
7. **Determinism**: dato lo stesso input, l'output e' SEMPRE identico

### 3.4 Flusso Dati — Generazione Piano

```
Input utente: frequenza (2-6), obiettivo, livello

1. clamp_frequenza()          — guardrail per livello (NSCA 2016)
2. get_split(frequenza)       — split ottimale
3. get_session_roles()        — ruoli sessione

FASE 1 — Struttura compound base:
  Per ogni sessione → pattern compound dal ruolo → slot con parametri carico

FASE 2 — Boost compound per muscoli carenti:
  compute_hypertrophy_sets() → deficit compound-only → +1 serie ai compound

FASE 3 — Compensazione isolation:
  deficit muscoli con isolamento → aggiunge slot isolation nelle sessioni affini

FASE 4 — Feedback loop (max 1 iterazione):
  Se muscoli critici ancora sotto MEV → ripete Fase 2+3

Output: TemplatePiano con sessioni ordinate, volume-driven
```

### 3.5 Flusso Dati — Periodizzazione Mesociclo

```
Input: TemplatePiano (da build_plan)

1. Durata mesociclo dal livello:
   Principiante: 4 sett (3 carico + 1 deload)
   Intermedio:   5 sett (4 carico + 1 deload)
   Avanzato:     6 sett (5 carico + 1 deload)

2. Fattori volume per settimana (interpolazione lineare):
   Base: 0.85-0.90 → Picco: 1.10-1.30 → Deload: 0.50

3. Classificazione fase:
   0-33% range → accumulazione
   33-66%      → intensificazione
   66-100%     → overreaching
   Ultima      → deload

4. Scalatura piano:
   Serie scalate per fattore (min 1). Intensita' invariata.
   Fonte: Israetel RP 2020 cap. 8-9, Helms 2019.

Output: Mesociclo con N piani settimanali scalati
```

---

## 4. Audit Scientifico (Completato)

### Correzioni Evidence-Based Applicate

| Problema | Causa | Fix | Fonte |
|----------|-------|-----|-------|
| Delt_ant MRV violation (3/5 obiettivi) | MRV troppo basso (10) per muscolo con volume indiretto alto | MRV alzato a 14 (int) / 16 (adv) | Israetel RP 2020: recupero rapido |
| Quadricipiti/femorali avanzato MRV < MAV_max | Incoerenza tabella volume | MRV = MAV_max + 2 | Invariante fisiologico |
| Core MRV overaccumulation | P.CORE esplicito + alto volume indiretto | Rimosso P.CORE da full_body/lower/legs | Carry + rotation coprono core |
| Polpacci sotto MEV (4/5 obiettivi) | Solo volume indiretto da squat (0.2 = peso 0) | Aggiunto calf_raise come pattern obbligatorio | Polpacci: alta freq necessaria |
| Pull H:V falso positivo | Tolleranza troppo stretta (+/-0.20) | Allargata a +/-0.35 | Asimmetria fisiologica NSCA |
| Principiante 4-5x MRV violations | Nessun clamp frequenza | Freq clamp: principiante max 3x | NSCA 2016 |

### Risultati Audit (prima -> dopo)

- Score minimo: 36.0 -> 49.7 (+38%)
- MEV violations: 73 -> 57 (-22%)
- Balance violations: 144 -> 132 (-8%)
- Volume table integrity: 2 bug -> 0
- Reference config core: 17.2 sopra_mrv -> 11.2 ottimale

---

## 5. Integrazione Frontend — Architettura SSoT

> **Decisione architetturale ADR-001 (2026-03-07)**: il Training Science Engine backend
> e' la Single Source of Truth (SSoT) per TUTTI i dati scientifici. Il frontend consuma
> via API REST, mai duplica costanti o coefficienti.

### 5.1 Cosa resta nel frontend (logica UI-only)

| Modulo | LOC | Responsabilita' |
|--------|-----|----------------|
| `smart-programming/types.ts` | ~120 | Interfacce mirror backend |
| `smart-programming/scorers.ts` | ~280 | 14 scorer composabili per selezione esercizi live |
| `smart-programming/helpers.ts` | ~150 | Profilo client, normalizzazione, utility |
| `smart-programming/analysis.ts` | ~100 | Orchestratore che chiama API backend |
| `smart-programming/index.ts` | ~20 | Re-export pubblico |

**Rationale**: lo scoring 14D serve latenza zero per UX (selezione esercizio nel builder).
Non contiene dati scientifici — solo logica di ranking basata su proprieta' dell'esercizio.

### 5.2 Cosa migra al backend (gia' implementato)

| Frontend (RIMOSSO) | Backend (SSoT) | Endpoint |
|--------------------|----------------|----------|
| `BASE_VOLUME_TARGETS` (hardcoded) | `volume_model.py` (MEV/MAV/MRV) | `GET /volume-targets` |
| `SESSION_BLUEPRINTS` (400 LOC) | `split_logic.py` + `plan_builder.py` | `POST /plan` |
| `computeMuscleCoverage()` | `plan_analyzer.py` | `POST /analyze` |
| `computeVolumeAnalysis()` | `plan_analyzer.py` | `POST /analyze` |
| `analyzeBiomechanics()` | `plan_analyzer.py` | `POST /analyze` |
| `analyzeRecovery()` | `plan_analyzer.py` | `POST /analyze` |
| `patternToMuscleRoles()` | `muscle_contribution.py` (matrice EMG) | Dentro /plan e /analyze |
| `MUSCLE_TARGET_TIER` | `volume_model.py` | `GET /volume-targets` |

### 5.3 Hook frontend per API backend

```typescript
// hooks/useTrainingScience.ts
useGeneratePlan(freq, obiettivo, livello)    // POST /training-science/plan
useAnalyzePlan(piano)                        // POST /training-science/analyze (debounce 300ms)
useGenerateMesocycle(piano)                  // POST /training-science/mesocycle
useVolumeTargets(livello, obiettivo)         // GET /training-science/volume-targets
useTrainingParameters(obiettivo)             // GET /training-science/parameters/{obj}
```

### 5.4 Flusso dati — Generazione piano nel builder

```
Utente: sceglie freq=4, obiettivo=ipertrofia, livello=intermedio
  |
  v
TemplateSelector → POST /training-science/plan
  → Backend: split_logic → plan_builder (4 fasi) → session_order
  → Ritorna: TemplatePiano con sessioni + slot tipizzati
  |
  v
fillSmartPlan() (client-side, scoring 14D)
  → Per ogni slot: scoreExercisesForSlot() con 14 dimensioni
  → Assegna esercizio con score piu' alto
  → Coverage swap optimization (3 pass)
  |
  v
Builder: scheda pronta, utente puo' modificare
  |
  v (onChange, debounce 300ms)
SmartAnalysisPanel → POST /training-science/analyze
  → Backend: plan_analyzer.py (dual volume, balance, recovery)
  → Ritorna: AnalisiPiano con coverage per muscolo + score
  → Frontend: renderizza barre colorate + badge
```

### 5.5 Impatto su smart-programming.ts

- Da ~1868 LOC monolite → 5 moduli in `smart-programming/` (~670 LOC totali)
- **RIMOSSI**: `BASE_VOLUME_TARGETS`, `MUSCLE_TARGET_TIER`, `SESSION_BLUEPRINTS` (370 LOC),
  `SLOT_VOLUME`, `computeMuscleCoverage()`, `computeVolumeAnalysis()`, `analyzeBiomechanics()`,
  `analyzeRecovery()`, `computeSafetyScore()`, `computeBlueprintCoverage()`, `computeRealCoverage()`,
  `patternToMuscleRoles()`, `generateSmartPlan()`, `fillSmartPlan()`
- **TENUTI**: 14 scorer functions, `scoreExercisesForSlot()`, `assessFitnessLevel()`,
  `buildClientProfile()`, `computeSafetyBreakdown()`, `parseAvgReps()`
- **AGGIUNTI**: orchestratore API in `analysis.ts`, tipi mirror backend in `types.ts`

### 5.6 Collaborazione Accademica

L'architettura SSoT e' progettata per la collaborazione con universita' di scienze motorie:
- I ricercatori lavorano su Python (`api/services/training_science/`)
- Ogni modulo e' indipendente e testabile isolatamente
- I coefficienti hanno fonte bibliografica nel docstring
- Il frontend non richiede competenze scientifiche (solo UI/UX)
- Il white paper KineScore documenta la metodologia completa

---

## 6. Fonti Bibliografiche

| Fonte | Anno | Contributo | Modulo |
|-------|------|------------|--------|
| NSCA — Essentials of Strength Training (Haff & Triplett) | 2016 | Parametri fondamentali, frequenza, ordine | `principles.py`, `split_logic.py`, `session_order.py` |
| ACSM — Guidelines for Exercise Testing | 2009 | Raccomandazioni volume/intensita' | `principles.py` |
| Schoenfeld — "The mechanisms of muscle hypertrophy" | 2010 | 3 meccanismi ipertrofia | `principles.py` |
| Schoenfeld — "Dose-response for RT volume" | 2017 | Volume-hypertrophy dose-response, soglia EMG 40% | `volume_model.py`, `muscle_contribution.py` |
| Schoenfeld — "Effects of RT frequency on hypertrophy" | 2016 | 2x/sett > 1x/sett meta-analisi | `plan_analyzer.py` |
| Schoenfeld — "Resistance Training Recommendations" | 2021 | Update raccomandazioni | `principles.py` |
| Krieger — "Single vs multiple sets" | 2010 | Multiple sets superiori | `volume_model.py` |
| Israetel — "Scientific Principles of Hypertrophy Training" | 2020 | MEV/MAV/MRV, periodizzazione | `volume_model.py`, `periodization.py` |
| Ralston et al. — "Strength training systematic review" | 2017 | Volume per forza | `principles.py` |
| Bompa & Buzzichelli — "Periodization" | 2019 | Teoria periodizzazione, supercompensazione | `periodization.py` |
| Helms — "Muscle and Strength Pyramid: Training" | 2019 | Deload protocol | `periodization.py` |
| Contreras — "EMG analysis of resistance exercises" | 2010 | Attivazione muscolare per esercizio | `muscle_contribution.py` |
| Alentorn-Geli — "ACL injury prevention" | 2009 | Rapporto quad:ham | `balance_ratios.py` |
| Sahrmann — "Movement System Impairment Syndromes" | 2002 | Rapporti push:pull, ant:post | `balance_ratios.py` |
| Zourdos et al. — "DUP vs traditional periodization" | 2016 | Validazione periodizzazione ondulata | `periodization.py` |

---

*Ogni numero ha una fonte. Ogni scelta architetturale ha una ragione.
Il codice parla il linguaggio della chinesiologia, non quello dei moltiplicatori.*
