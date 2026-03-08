# UPG-2026-03-08-02 — Tab Analisi Scientifica v1

> *"Il sistema non ti dice come allenare.*
> *Ti mostra cosa stai facendo, perche' funziona, e dove puoi migliorare."*

**Data**: 2026-03-08
**Stato**: SPEC ARCHITETTURALE
**Ambito**: Workout Builder, Training Science Engine, Frontend UX
**Fonti primarie**: NSCA 2016, ACSM 2021, Schoenfeld 2016/2017

---

## 1. Problema

Il backend calcola ~270 valori scientifici per scheda.
Il trainer ne vede ~30. Il 90% del lavoro e' invisibile.

| Dato calcolato | Come arriva oggi | Cosa manca |
|----------------|-----------------|------------|
| EMG 18x15 (attivazione %) | Barre colorate con badge | PERCHE' un muscolo e' coperto, da quali esercizi, con quale % |
| MEV/MAV/MRV targets | Zona colorata su progress bar | Valori numerici, shortfall esatto, cosa significa in pratica |
| 5 rapporti biomeccanici | Tabella con pallino verde/ambra | Spiegazione clinica, conseguenze, cosa fare |
| Demand vector 10D | Quasi invisibile (contatori) | 10 dimensioni calcolate, il trainer non ne vede nessuna |
| Safety 47 condizioni | Popover per esercizio | Contesto biomeccanico, logica della severita' |
| Ordine sessione SNC | Implicito e invisibile | Il trainer riordina con DnD senza sapere che rompe la logica |
| Recovery overlap | Una riga di testo | Nessun dato quantitativo, nessuna azione suggerita |
| Frequenza muscolare | Testo solo se < 2x | Frequenza completa invisibile, mostrata solo se sbagliata |

---

## 2. Visione

Una **tab dedicata** nel builder delle schede, alla pari delle sessioni.
Non un pannello collassabile laterale — uno spazio pieno per analisi approfondita.

**Principio UX**: non un report accademico. Un consulto con un collega esperto.
Ogni dato ha tre livelli: (1) vista rapida, (2) drill-down dettaglio, (3) fonte scientifica.

**Fonti**: solo 3 pilastri con credibilita' mondiale indiscutibile.

| Pilastro | Riferimento | Copertura |
|----------|------------|-----------|
| **NSCA** | Haff & Triplett, *Essentials of S&C*, 4th ed. 2016 | Carico, ordine, frequenza, volume, tecnica |
| **ACSM** | *Guidelines for Exercise Testing and Prescription*, 11th ed. 2021 | Screening, range normativi, prescrizione clinica |
| **Schoenfeld** | Meta-analisi 2016-2021 | Volume ottimale, frequenza, dose-risposta |

Tutto il resto (Israetel, Sahrmann, Contreras) citato come riferimento secondario
attraverso questi tre pilastri.

---

## 3. Architettura Frontend

### 3.1 Posizionamento nel builder

La pagina `schede/[id]/page.tsx` oggi ha un layout lineare:
```
Safety Overview → MuscleMapPanel → SmartAnalysisPanel → SessionCard[]
```

Diventa un layout con **due viste** switchabili:

```
[Tab: Sessioni]  [Tab: Analisi Scientifica]

Vista Sessioni (default — come oggi):
  Safety Overview → SessionCard[] → Aggiungi Sessione

Vista Analisi:
  ScientificAnalysisTab (componente dedicato, ~4 sezioni)
```

Il MuscleMapPanel si sposta DENTRO la tab Analisi (sezione 1).
Lo SmartAnalysisPanel attuale viene **sostituito** dalla nuova tab.

### 3.2 Switch Tab

Implementazione leggera con stato locale — no `Tabs` shadcn per evitare
nesting complesso. Un semplice `activeView: "sessions" | "analysis"`.

```typescript
const [activeView, setActiveView] = useState<"sessions" | "analysis">("sessions");
```

Due bottoni nella toolbar del builder (sotto l'header, sopra il contenuto).
L'analisi si aggiorna in tempo reale quando il trainer torna dalla vista sessioni.

### 3.3 Componente principale

```
frontend/src/components/workouts/ScientificAnalysisTab.tsx  (~300 LOC max)
  |
  +-- Sezione 1: MuscleCoverageSection.tsx   (~250 LOC)
  +-- Sezione 2: BiomechanicalBalance.tsx    (~250 LOC, 2A demand + 2B ratios)
  +-- Sezione 3: ClinicalSafetySection.tsx   (~200 LOC)
  +-- Sezione 4: ActionableSummary.tsx        (~150 LOC)
  |
frontend/src/lib/demand-aggregation.ts        (~80 LOC, utility demand 10D)
```

Totale stimato: ~1,230 LOC in 6 file (sotto il limite 300 LOC per file).

---

## 4. Le 4 Sezioni

### 4.1 Copertura Muscolare

**Vista rapida** (sempre visibile):
- Body map interattiva (MuscleMapPanel evoluto) con 15 muscoli colorati per stato
- Legenda: deficit (rosso) / sotto-ottimale (blu) / ottimale (verde) / eccesso (ambra)
- KPI inline: "12/15 muscoli coperti — 3 deficit"

**Drill-down** (click su muscolo o espandi lista):
Per ogni muscolo, card espandibile con:

```
┌─────────────────────────────────────────────────────┐
│ PETTO                              8.0 serie/sett   │
│ ████████████░░░░░░  Ottimale                        │
│ MEV 4 ──── MAV 6-8 ──── MRV 12                     │
│                                                     │
│ Contributo per esercizio:                           │
│   Panca Piana (push_h)    3 serie × 1.0  = 3.0     │
│   Croci Cavi (push_h)     3 serie × 0.7  = 1.5     │
│   Dip (push_v)            3 serie × 0.7  = 1.5     │
│   OHP (push_v)            3 serie × 0.4  = 1.0     │
│   Plank (core)            3 serie × 0.2  = 0.0 *   │
│                                            ─────    │
│                                   Totale   7.0      │
│                                                     │
│ * Sotto soglia EMG 40% — non conta per ipertrofia   │
│                                                     │
│ Frequenza: stimolato in 3/3 sessioni (ottimale)     │
│ Fonte: Schoenfeld 2017 — 10-20 serie/sett ipertrofia│
└─────────────────────────────────────────────────────┘
```

**Dati necessari** (gia' calcolati nel backend):
- `VolumeEffettivo.serie_effettive` + targets MEV/MAV/MRV → `plan_analyzer.py`
- Contributo per esercizio → richiede **nuovo campo** nella response API
- Frequenza per muscolo → calcolata in `_analyze_frequency()` ma non nella response

### 4.2 Equilibrio Biomeccanico — Due Livelli

L'analisi biomeccanica si articola su due livelli complementari:
- **2A — Profilo di Carico** (demand aggregato): COSA fa il corpo durante l'allenamento
- **2B — Rapporti di Forza** (balance ratios): quanto e' BILANCIATO il carico

#### 4.2A — Profilo di Carico (Demand Profile)

Aggrega i vettori biomeccanici 10D di ogni esercizio (gia' in `exerciseMap`)
per sessione e per settimana intera, mostrando la distribuzione del carico
sulle 7 dimensioni primarie + 3 secondarie.

**Logica** (puro frontend, zero backend):
- Per ogni esercizio in scheda, legge il demand vector (10 float 0-4) da `exerciseMap`
- Moltiplica per numero di serie → contributo pesato
- Somma per sessione e per settimana

**Vista rapida**:
- 7 barre orizzontali (dimensioni primarie) con budget percentuale sulla settimana
- Alert se una dimensione supera il 40% del carico totale ("concentrazione")
- Palette teal (bilanciato) → ambra (concentrato) → rosso (>50%)

```
┌─────────────────────────────────────────────────────┐
│ PROFILO DI CARICO SETTIMANALE                       │
│                                                     │
│ Spinta orizz.  ████████████░░░░░░░░  28%            │
│ Trazione orizz. ██████████░░░░░░░░░░  22%            │
│ Spinta vert.   ██████░░░░░░░░░░░░░░  14%            │
│ Trazione vert. █████░░░░░░░░░░░░░░░  12%            │
│ Accosciata     █████░░░░░░░░░░░░░░░  11%            │
│ Hip hinge      ████░░░░░░░░░░░░░░░░   8%            │
│ Core           ██░░░░░░░░░░░░░░░░░░   5%            │
│                                                     │
│ ℹ Distribuzione bilanciata — nessuna concentrazione │
└─────────────────────────────────────────────────────┘
```

**Drill-down** (click su dimensione):
- Dettaglio per sessione: quale sessione contribuisce di piu' a quella dimensione
- Lista esercizi che alimentano la dimensione con serie × demand = contributo
- Confronto tra sessioni (distribuzione equilibrata o concentrata)

```
┌─────────────────────────────────────────────────────┐
│ SPINTA ORIZZONTALE — Dettaglio                      │
│ 28% del carico settimanale                          │
│                                                     │
│ Sessione A (Upper):   16 punti demand               │
│   Panca Piana         4 serie × 4.0 = 16.0          │
│   Croci Cavi          3 serie × 2.0 =  6.0          │
│                                                     │
│ Sessione B (Lower):    0 punti demand               │
│   (nessun esercizio)                                │
│                                                     │
│ Sessione C (Push):    12 punti demand               │
│   Chest Press         3 serie × 3.0 =  9.0          │
│   Piegamenti          3 serie × 3.0 =  9.0          │
│                                                     │
│ Dimensioni secondarie correlate:                    │
│   Carico assiale: basso (1.2)                       │
│   Stress articolare: medio (2.1)                    │
│                                                     │
│ Cosa significa:                                     │
│ La spinta orizzontale e' la dimensione dominante.   │
│ Se non bilanciata da trazione orizzontale, puo'     │
│ portare a protrazione scapolare.                    │
│ Fonte: NSCA 2016 cap. 17                            │
└─────────────────────────────────────────────────────┘
```

**7 dimensioni primarie**:
`push_h`, `pull_h`, `push_v`, `pull_v`, `squat`, `hinge`, `core`

**3 dimensioni secondarie** (mostrate nel drill-down):
`carry`, `axial_load`, `joint_stress`

**Utility** (nuovo file `frontend/src/lib/demand-aggregation.ts`, ~80 LOC):
- `aggregateSessionDemand(exercises, exerciseMap)` → `DemandVector` per sessione
- `aggregateWeeklyDemand(sessions)` → `DemandVector` settimanale con % distribuzione
- `detectDemandConcentration(weekly, threshold=0.40)` → dimensioni concentrate
- Tipi: `DemandVector = Record<DemandDimension, number>`

**Dati necessari**:
- Demand vector per esercizio → gia' in `exerciseMap` (10 colonne DB, `UPG-2026-03-08-01`)
- Serie per esercizio → gia' nel builder state
- Zero API call — puro calcolo frontend dall'`exerciseMap` gia' in memoria

#### 4.2B — Rapporti di Forza (Balance Ratios)

I 5 rapporti biomeccanici classici dal backend (`balance_ratios.py`), arricchiti
con spiegazione clinica e azioni correttive.

**Vista rapida**:
5 card compatte, ciascuna con:
- Nome rapporto + valore attuale + target + stato (OK / Squilibrio)
- Barra visuale che mostra posizione relativa nel range di tolleranza

**Drill-down** (click su rapporto):

```
┌─────────────────────────────────────────────────────┐
│ PUSH : PULL                                         │
│ Valore: 1.35   Target: 1.0 ± 0.15   ⚠ Squilibrio  │
│                                                     │
│ ◄──────[===●=========]──────►                       │
│ 0.5        1.0        1.5                           │
│        ▲ target  ▲ attuale                          │
│                                                     │
│ Cosa significa:                                     │
│ Il volume di spinta (push) e' superiore al volume   │
│ di trazione (pull) del 35%. Questo puo' portare a   │
│ squilibrio posturale con protrazione scapolare e    │
│ sovraccarico della cuffia dei rotatori.             │
│                                                     │
│ Cosa fare:                                          │
│ Aggiungi 2-3 serie di trazione orizzontale          │
│ (row, face pull) o riduci 1-2 serie di push.        │
│                                                     │
│ Dettaglio volume:                                   │
│   Push totale: 18 serie (push_h: 12, push_v: 6)    │
│   Pull totale: 13 serie (pull_h: 8, pull_v: 5)     │
│                                                     │
│ Coerenza con Profilo di Carico:                     │
│   Spinta orizz. (28%) + vert. (14%) = 42% totale   │
│   Trazione orizz. (22%) + vert. (12%) = 34% totale  │
│   Delta: +8% verso la spinta                        │
│                                                     │
│ Fonte: NSCA 2016 cap.17, Sahrmann 2002              │
└─────────────────────────────────────────────────────┘
```

**Dati necessari** (gia' calcolati):
- `AnalisiBalance.rapporti` + `target` + `squilibri` → `balance_ratios.py`
- Volume per pattern group → richiede **nuovo campo** nella response
- Spiegazione clinica + azione → **testo statico** nel frontend (3 fonti)
- Cross-reference con demand profile → calcolato in 2A (frontend)

### 4.3 Profilo Clinico-Safety

**Vista rapida**:
- KPI: "3 condizioni rilevate — 2 esercizi da evitare, 4 da adattare, 1 cautela"
- RiskBodyMap (silhouette colorata per severity)

**Drill-down** (click su condizione o esercizio):

```
┌─────────────────────────────────────────────────────┐
│ ERNIA DISCALE L4-L5                    ● Ortopedica │
│                                                     │
│ Esercizi impattati in questa scheda:                │
│                                                     │
│ 🔴 EVITARE                                          │
│   Romanian Deadlift (hinge)                         │
│   → Carico assiale diretto sulla colonna lombare    │
│   → Demand lombare: 3/4 (alto)                     │
│   → Alternative: Hip Thrust, Leg Curl          [↗]  │
│                                                     │
│ 🔵 ADATTARE                                         │
│   Back Squat (squat)                                │
│   → ROM limitato, carico moderato                   │
│   → Demand assiale: 3/4 — Demand lombare: 3/4      │
│   → Suggerimento: Goblet Squat (demand lombare 1/4) │
│                                                     │
│ 🟡 CAUTELA                                          │
│   Plank (core)                                      │
│   → Monitorare dolore durante isometria lombare     │
│                                                     │
│ Fonte: ACSM 2021 cap. popolazioni speciali          │
└─────────────────────────────────────────────────────┘
```

**Dati necessari**:
- Safety map → gia' esposta via `GET /exercises/safety-map`
- Demand vector per esercizio → gia' in DB (10 colonne)
- Demand vector richiede **nuovo endpoint** o estensione della response esercizi
- Testo spiegazione severita' → testo statico per 80 pattern rules

### 4.4 Riepilogo Operativo

**Vista unica** (non ha drill-down — e' gia' il riassunto):

```
┌─────────────────────────────────────────────────────┐
│ RIEPILOGO — 2 azioni prioritarie                    │
│                                                     │
│ 1. ⚠ Aggiungi trazione orizzontale                 │
│    Il rapporto Push:Pull e' sbilanciato (1.35 vs    │
│    target 1.0). Rischio: protrazione scapolare.     │
│    → Suggerimento: aggiungi 1 serie di Row     [+]  │
│    Fonte: NSCA 2016                                 │
│                                                     │
│ 2. 🔴 Romanian Deadlift controindicato              │
│    Il tuo cliente ha ernia L4-L5. Il RDL ha demand  │
│    lombare 3/4. Considerare Hip Thrust (demand 1/4).│
│    → Sostituisci con Hip Thrust               [↗]   │
│    Fonte: ACSM 2021                                 │
│                                                     │
│ ✅ Copertura muscolare: 12/15 ottimali              │
│ ✅ Frequenza: tutti i muscoli >= 2x/sett            │
│ ✅ Ordine sessione: compound-first rispettato       │
│ ✅ Recovery: nessun overlap critico                  │
└─────────────────────────────────────────────────────┘
```

**Logica di prioritizzazione** (deterministica):
1. Safety avoid (rosso) — esercizi controindicati presenti nella scheda
2. Safety modify (blu) — esercizi che richiedono adattamento
3. Squilibri biomeccanici — rapporti fuori tolleranza
4. Muscoli sotto MEV — deficit di volume
5. Frequenza < 2x — muscoli stimolati insufficientemente
6. Recovery overlap — sessioni consecutive con sovrapposizione
7. Ordine sessione violato — isolation prima di compound

Le voci "tutto ok" (check verdi) appaiono in fondo, compatte.

**Dati necessari**: tutti gia' disponibili dalle sezioni 1-3. Questa sezione
e' pura aggregazione e prioritizzazione client-side.

---

## 5. Modifiche Backend

### 5.1 Estendere `AnalisiPiano` con dati strutturati

Oggi `analyze_plan()` ritorna volume, balance, warnings (stringhe), score.
Il frontend ha bisogno di dati strutturati, non stringhe da parsare.

**Nuovi campi in `AnalisiPiano`**:

```python
class ContributoEsercizio(BaseModel):
    """Volume ipertrofico di un singolo esercizio su un muscolo."""
    pattern: PatternMovimento
    serie: int
    contributo_emg: float       # 0.0-1.0 dalla matrice EMG
    serie_ipertrofiche: float   # serie × peso ipertrofico

class DettaglioMuscolo(BaseModel):
    """Dettaglio completo per un muscolo — drill-down nella tab analisi."""
    muscolo: GruppoMuscolare
    serie_effettive: float
    target_mev: float
    target_mav_min: float
    target_mav_max: float
    target_mrv: float
    stato: str                  # sotto_mev | mev_mav | ottimale | sopra_mav | sopra_mrv
    frequenza: int              # sessioni/settimana che stimolano questo muscolo
    contributi: list[ContributoEsercizio]  # breakdown per esercizio

class DettaglioRapporto(BaseModel):
    """Dettaglio di un rapporto biomeccanico con volume per lato."""
    nome: str
    valore: float
    target: float
    tolleranza: float
    in_tolleranza: bool
    volume_numeratore: float    # es. push totale
    volume_denominatore: float  # es. pull totale
    fonte: str

class DettaglioRecovery(BaseModel):
    """Overlap muscolare tra due sessioni consecutive."""
    sessione_a: str
    sessione_b: str
    muscoli_overlap: list[str]
    serie_overlap_a: dict[str, float]  # muscolo → serie nella sessione A
    serie_overlap_b: dict[str, float]  # muscolo → serie nella sessione B

class AnalisiPianoV2(BaseModel):
    """Analisi completa — versione estesa per la tab scientifica."""
    # Dati esistenti (backward-compatible)
    volume: AnalisiVolume
    balance: AnalisiBalance
    warnings: list[str]
    score: float

    # Nuovi dati strutturati
    dettaglio_muscoli: list[DettaglioMuscolo]
    dettaglio_rapporti: list[DettaglioRapporto]
    frequenza_per_muscolo: dict[str, int]
    recovery_overlaps: list[DettaglioRecovery]
```

### 5.2 Nuovo endpoint o estensione

**Opzione A** (raccomandata): estendere `POST /training-science/analyze`
aggiungendo i nuovi campi alla response esistente. I campi sono opzionali
nel frontend — chi non li usa (SmartAnalysisPanel legacy) li ignora.

**Opzione B**: nuovo endpoint `POST /training-science/analyze-detailed`.
Separa la response leggera (per debounce 300ms) da quella completa (per la tab).
Pro: non appesantisce il debounce. Contro: duplicazione logica.

**Raccomandazione**: Opzione A con lazy loading. La tab Analisi chiama
l'endpoint solo quando e' attiva, con debounce piu' lungo (1s).

### 5.3 Demand vector per esercizio nella response

Oggi il demand vector per esercizio e' nel DB ma non esposto nell'endpoint
`/exercises` standard. Per la sezione Safety serve il demand degli esercizi
presenti nella scheda.

**Soluzione**: aggiungere `demand_summary` opzionale alla `ExerciseResponse`,
popolato solo quando richiesto (query param `?include_demand=true`).
Oppure: calcolarlo nel frontend dal campo gia' presente in `Exercise`
(i 10 campi demand sono gia' nel type TypeScript).

I 10 campi demand sono GIA' nella response `Exercise` (aggiornamento
`UPG-2026-03-08-01`) — il frontend puo' usarli direttamente
dall'`exerciseMap` gia' in memoria nel builder.

---

## 6. Modifiche Frontend

### 6.1 Nuovi file

```
frontend/src/components/workouts/
  ScientificAnalysisTab.tsx     — orchestratore 4 sezioni (~300 LOC)
  MuscleCoverageSection.tsx     — body map + drill-down muscoli (~250 LOC)
  BiomechanicalBalance.tsx      — 2A demand profile + 2B force ratios (~250 LOC)
  ClinicalSafetySection.tsx     — condizioni × esercizi (~200 LOC)
  ActionableSummary.tsx         — riepilogo prioritizzato (~150 LOC)

frontend/src/lib/
  demand-aggregation.ts         — aggregazione demand 10D per sessione/settimana (~80 LOC)
```

### 6.2 Dati statici — spiegazioni cliniche

Testi di spiegazione per i 5 rapporti biomeccanici e per le categorie
safety. Sono testi fissi (non calcolati) referenziati alle 3 fonti.

```
frontend/src/lib/scientific-explanations.ts  (~200 LOC, file di puri dati)
```

Contenuto: `DEMAND_DIMENSION_LABELS`, `RATIO_EXPLANATIONS`,
`SAFETY_CATEGORY_EXPLANATIONS`, `VOLUME_STATUS_EXPLANATIONS`. Ogni entry con:
- `significato`: cosa misura (1 frase)
- `conseguenza`: cosa succede se sbilanciato (1-2 frasi)
- `azione`: cosa fare concretamente (1 frase)
- `fonte`: riferimento primario (NSCA/ACSM/Schoenfeld)

### 6.3 File modificati

- `schede/[id]/page.tsx` — aggiunta switch sessioni/analisi, rimozione
  SmartAnalysisPanel e MuscleMapPanel dalla vista sessioni
- `hooks/useTrainingScience.ts` — nuovo hook per analisi dettagliata
  (se si sceglie Opzione B nell'endpoint)
- `types/api.ts` — nuovi tipi `DettaglioMuscolo`, `DettaglioRapporto`,
  `DettaglioRecovery`, `AnalisiPianoV2`

### 6.4 File rimossi / deprecati

- `SmartAnalysisPanel.tsx` — sostituito dalla tab intera (il codice
  utile migra nelle 4 sezioni)
- `lib/smart-programming/analysis.ts` — le funzioni di analisi frontend
  legacy non servono piu' (il backend fa tutto)

---

## 7. Piano di Implementazione

### Sprint 1 — Backend (estensione analyze)

1. Aggiungere `DettaglioMuscolo`, `DettaglioRapporto`, `DettaglioRecovery`
   a `types.py`
2. Modificare `plan_analyzer.py`:
   - `_analyze_volume()` ritorna anche contributi per esercizio
   - `_analyze_frequency()` ritorna dict strutturato (non solo warnings)
   - `_analyze_recovery()` ritorna dati strutturati (non solo warnings)
   - `_analyze_plan_balance()` ritorna dettaglio volume per lato
3. Estendere `AnalisiPiano` con i nuovi campi (opzionali, default None)
4. Aggiornare `types/api.ts` con i nuovi tipi
5. Test: verificare che l'endpoint esistente continua a funzionare
   e i nuovi campi sono presenti

### Sprint 2 — Frontend (tab + sezioni 1-2)

1. Creare lo switch sessioni/analisi in `schede/[id]/page.tsx`
2. Implementare `ScientificAnalysisTab.tsx` (orchestratore)
3. Implementare `MuscleCoverageSection.tsx` (body map + drill-down)
4. Creare `demand-aggregation.ts` (aggregazione demand 10D da exerciseMap)
5. Implementare `BiomechanicalBalance.tsx` (2A demand profile + 2B force ratios)
6. Creare `scientific-explanations.ts` (testi statici: demand labels, ratios, safety)

### Sprint 3 — Frontend (sezioni 3-4 + pulizia)

1. Implementare `ClinicalSafetySection.tsx` (condizioni × demand)
2. Implementare `ActionableSummary.tsx` (riepilogo prioritizzato)
3. Rimuovere `SmartAnalysisPanel.tsx` e `analysis.ts` legacy
4. Spostare `MuscleMapPanel` dentro la sezione 1

### Sprint 4 — Rifinitura UX

1. Animazioni drill-down (expand/collapse)
2. Responsive (mobile: stack verticale, drill-down come sheet bottom)
3. Print-friendly (la tab analisi deve essere esportabile)
4. Test Chiara — iterare in base al feedback

---

## 8. Cosa NON fare nel v1

- **Non generare schede** — la tab analizza, non propone
- **Non aggiungere fonti** — solo NSCA, ACSM, Schoenfeld
- **Non aggiungere dimensioni** — le 4 sezioni coprono tutto
- **Non creare un "metodo KineScore"** — il trainer ha il suo metodo,
  noi misuriamo e informiamo
- **Non bloccare nulla** — la tab informa. Il trainer decide.
  Zero popup, zero blocchi, zero "non puoi salvare perche'..."

---

## 9. Metriche di Successo

Il v1 funziona se Chiara:

1. Apre la tab analisi dopo aver costruito una scheda a mano
2. Capisce in 5 secondi se la scheda e' bilanciata
3. Trova almeno 1 informazione utile che non sapeva
4. Non la trova frustrante o accademica
5. La usa di nuovo la volta dopo

---

## 10. Dipendenze Tecniche

| Dipendenza | Stato | Note |
|-----------|-------|------|
| `plan_analyzer.py` (backend) | Esistente, da estendere | Gia' calcola tutto, manca strutturare l'output |
| `muscle_contribution.py` | Esistente, read-only | Matrice EMG usata per contributi per esercizio |
| `balance_ratios.py` | Esistente, read-only | 5 rapporti con target e tolleranza |
| `safety_engine.py` | Esistente, read-only | Safety map gia' esposta via API |
| Demand vector DB | Esistente (UPG-2026-03-08-01) | 10 colonne gia' nella response Exercise |
| `exerciseMap` (frontend) | Esistente, in memoria nel builder | Demand vector per esercizio, usato per sezione 2A |
| `MuscleMapPanel.tsx` | Esistente, da spostare | Migra dentro sezione 1 |
| `SmartAnalysisPanel.tsx` | Esistente, da sostituire | Codice utile migra nelle nuove sezioni |

**Zero nuovi moduli backend** per la sezione 2A (demand profile = puro frontend).
Zero nuove tabelle DB. Zero nuove API (solo estensione della response esistente).
La tab e' costruita quasi interamente su dati che gia' calcoliamo.
