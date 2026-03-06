# Training Science Engine — Specifica Architetturale

> *"Senza una metodologia codificata, il software e' un calcolatore.*
> *Con una metodologia codificata, il software e' un sistema esperto."*

**Stato**: DRAFT — In analisi
**Autore**: Claude Opus 4.6 + gvera
**Obiettivo**: Fondazione scientifica per la programmazione dell'allenamento

---

## 1. Analisi dello Stato Attuale

### Cosa abbiamo (e perche' non funziona)

`smart-programming.ts` (1300 LOC) e' un monolite che:
- Hardcoda 15 blueprint (5 freq x 3 livelli) come array di slot
- Usa 4 slot type criptici (CP/CS/IT/IA) che mescolano ruolo e volume
- Conta il volume come "serie per muscolo" con crediti approssimati (1.0 primario, 0.35 secondario)
- Non ha una metodologia: i numeri sono stati scelti "a occhio" e corretti a tentativi
- Mescola 6 responsabilita' in un file solo

### Cosa serve

Un sistema che codifica i **principi della programmazione dell'allenamento** come regole,
e genera piani che rispettano quei principi. Il codice deve parlare il linguaggio
della chinesiologia, non quello dei moltiplicatori numerici.

---

## 2. Fondamenta Scientifiche

### 2.1 Le 6 Variabili della Programmazione (NSCA, Haff & Triplett 2016)

Ogni programma di allenamento e' definito da 6 variabili interdipendenti:

| Variabile | Cosa controlla | Unita' |
|-----------|---------------|--------|
| **Intensita'** | Carico relativo | % 1RM |
| **Volume** | Quantita' di lavoro | serie x ripetizioni |
| **Frequenza** | Quante volte/settimana per muscolo | sessioni/sett |
| **Densita'** | Rapporto lavoro/riposo | secondi riposo |
| **Selezione esercizi** | Quali movimenti | pattern + muscolo target |
| **Ordine esercizi** | Sequenza nella sessione | multi-art → mono-art |

Queste 6 variabili cambiano in modo **coordinato** in base all'obiettivo.
Non si puo' cambiare una senza influenzare le altre.

### 2.2 Obiettivi di Allenamento — Parametri Evidence-Based

Fonti: NSCA (2016), ACSM (2009), Schoenfeld (2010, 2017, 2021), Krieger (2010).

#### FORZA MASSIMA
- **Principio**: adattamento neurale + reclutamento fibre tipo IIx
- **Intensita'**: 85-100% 1RM (carichi pesanti, poche ripetizioni)
- **Rep range**: 1-5 per serie
- **Serie per esercizio**: 3-5
- **Riposo**: 180-300s (recupero sistema nervoso + fosfocreatina)
- **Frequenza per muscolo**: 2-3x/settimana (NSCA: alta frequenza, basso volume per sessione)
- **Selezione**: 80%+ multi-articolari (squat, stacco, panca, trazioni)
- **Ordine**: multi-articolari PRIMA, accessori dopo
- **Volume settimanale**: 10-15 serie/muscolo principale (Ralston et al. 2017)
- **Progressione**: +2.5-5 kg/settimana (linear periodization per principianti)

#### IPERTROFIA
- **Principio**: stress meccanico + danno muscolare + stress metabolico (Schoenfeld 2010)
- **Intensita'**: 65-85% 1RM (carico moderato-alto)
- **Rep range**: 6-12 per serie (sweet spot: 8-12)
- **Serie per esercizio**: 3-4
- **Riposo**: 60-120s (accumulo metaboliti, GH release)
- **Frequenza per muscolo**: 2x/settimana (Schoenfeld 2016 meta-analisi: 2x > 1x)
- **Selezione**: 60% multi-articolari + 40% mono-articolari (stimolo diretto per ipertrofia locale)
- **Ordine**: multi-articolari → mono-articolari → isolamento
- **Volume settimanale**: 10-20+ serie/muscolo (Schoenfeld 2017: dose-response fino a 20+)
- **Progressione**: doppia progressione (reps → carico)

#### RESISTENZA MUSCOLARE
- **Principio**: adattamento mitocondriale + capillarizzazione + buffer lattato
- **Intensita'**: 50-65% 1RM (carichi leggeri-moderati)
- **Rep range**: 15-25+ per serie
- **Serie per esercizio**: 2-3
- **Riposo**: 30-60s (breve — lo stress metabolico e' l'obiettivo)
- **Frequenza per muscolo**: 2-3x/settimana
- **Selezione**: mix equilibrato, circuiti ammessi
- **Ordine**: flessibile, circuiti ok
- **Volume settimanale**: 8-12 serie/muscolo
- **Progressione**: +reps o -riposo (non +carico)

#### DIMAGRIMENTO (Ricomposizione Corporea)
- **Principio**: preservare massa magra in deficit calorico + alto EPOC
- **Intensita'**: 65-80% 1RM (mantenere intensita' per preservare forza)
- **Rep range**: 8-15 per serie
- **Serie per esercizio**: 3-4
- **Riposo**: 45-90s (densita' alta per EPOC)
- **Frequenza per muscolo**: 2-3x/settimana (stimolo frequente per preservare)
- **Selezione**: multi-articolari prioritari (alto costo metabolico)
- **Ordine**: multi-art → superset → circuito finale
- **Volume settimanale**: 10-15 serie/muscolo (volume moderato — recupero ridotto in deficit)
- **Progressione**: mantenimento carichi (non aspettarsi progressione in deficit)
- **Nota**: l'allenamento PRESERVA. Il dimagrimento avviene in cucina.

#### TONIFICAZIONE (Fitness Generale)
- **Principio**: ipertrofia moderata + dimagrimento leggero + benessere
- **Intensita'**: 60-75% 1RM
- **Rep range**: 10-15 per serie
- **Serie per esercizio**: 2-3
- **Riposo**: 60-90s
- **Frequenza per muscolo**: 2x/settimana
- **Selezione**: equilibrata multi + mono, enfasi postura e funzionalita'
- **Ordine**: multi-art → mono-art → core/stabilita'
- **Volume settimanale**: 8-14 serie/muscolo
- **Progressione**: doppia progressione lenta

#### RIEPILOGO PARAMETRI

```
                    FORZA      IPERTROFIA  RESISTENZA  DIMAGRIMENTO  TONIFICAZIONE
Intensita' %1RM    85-100     65-85       50-65       65-80         60-75
Rep range          1-5        6-12        15-25       8-15          10-15
Serie/esercizio    3-5        3-4         2-3         3-4           2-3
Riposo (sec)       180-300    60-120      30-60       45-90         60-90
Freq/muscolo/sett  2-3        2           2-3         2-3           2
Vol sett (serie)   10-15      10-20+      8-12        10-15         8-14
% multi-art        80%+       60%         50%         70%           60%
```

### 2.3 Volume per Gruppo Muscolare — Modello MEV/MAV/MRV

Fonte principale: Israetel (Renaissance Periodization), validato da meta-analisi
Schoenfeld 2017 e Krieger 2010. Unita': **serie dirette effettive per settimana**.

"Serie diretta effettiva" = serie in cui il muscolo e' un motore primario.
Il lavoro sinergico (es. tricipiti nella panca) conta parzialmente.

| Gruppo Muscolare | MEV | MAV beg | MAV int | MAV adv | MRV |
|-----------------|-----|---------|---------|---------|-----|
| **Petto** | 6 | 8-10 | 12-16 | 16-22 | 22 |
| **Dorsali** (lat+romboidi) | 6 | 8-10 | 14-18 | 18-24 | 25 |
| **Deltoidi laterali** | 6 | 8-10 | 14-18 | 18-24 | 26 |
| **Deltoidi anteriori** | 0* | 0-4* | 0-6* | 0-8* | 12 |
| **Deltoidi posteriori** | 0 | 6-8 | 10-14 | 14-18 | 22 |
| **Bicipiti** | 4 | 6-8 | 10-14 | 14-20 | 26 |
| **Tricipiti** | 4 | 4-6 | 8-12 | 10-16 | 18 |
| **Quadricipiti** | 6 | 8-10 | 12-16 | 16-22 | 20 |
| **Femorali** | 4 | 6-8 | 10-14 | 12-18 | 16 |
| **Glutei** | 0* | 4-6* | 6-10* | 8-14* | 16 |
| **Polpacci** | 6 | 8-10 | 10-14 | 12-16 | 16 |
| **Trapezio** | 0* | 4-6* | 8-12* | 12-18* | 26 |
| **Core/Addominali** | 0* | 4-8 | 8-12 | 10-16 | 20 |
| **Avambracci** | 0* | 2-4* | 4-6* | 4-8* | 12 |
| **Adduttori** | 0* | 2-4 | 4-8 | 6-10 | 12 |

*`0*` = volume indiretto sufficiente dai compound (squat→glutei, panca→deltoidi ant, row→trapezio).
Lavoro diretto opzionale per enfatizzare.

**Nota chiave**: questi range sono per obiettivo IPERTROFIA. Per altri obiettivi si scala:
- Forza: ~70% del MAV ipertrofia (meno volume, piu' intensita')
- Resistenza: ~60% del MAV ipertrofia (meno serie, piu' ripetizioni)
- Dimagrimento: ~80% del MAV ipertrofia (preservare, non costruire)
- Tonificazione: ~70% del MAV ipertrofia

### 2.4 Matrice di Contribuzione Muscolare (EMG-based)

Questa e' la chiave dell'intero sistema. Ogni pattern di movimento
attiva i muscoli con percentuali diverse. Basato su studi EMG
(Contreras 2010, Schoenfeld 2010, NSCA guidelines).

Usiamo una scala 0-1 dove:
- **1.0** = motore primario (attivazione EMG > 70%)
- **0.7** = sinergista maggiore (attivazione 40-70%)
- **0.4** = sinergista minore (attivazione 20-40%)
- **0.2** = stabilizzatore (attivazione 10-20%)
- **0.0** = non coinvolto

```
PATTERN           MUSCOLI COINVOLTI (contribuzione 0-1)

push_h (panca)    petto: 1.0, delt_ant: 0.7, tricipiti: 0.7, core: 0.2
push_v (military) delt_ant: 1.0, delt_lat: 0.7, tricipiti: 0.7, trapezio: 0.4, core: 0.2
squat             quadricipiti: 1.0, glutei: 0.7, femorali: 0.4, adduttori: 0.4, core: 0.4, polpacci: 0.2
hinge (stacco)    femorali: 1.0, glutei: 1.0, dorsali: 0.4, trapezio: 0.4, core: 0.4, avambracci: 0.2
pull_h (row)      dorsali: 1.0, trapezio: 0.7, delt_post: 0.7, bicipiti: 0.7, avambracci: 0.4
pull_v (lat pull) dorsali: 1.0, bicipiti: 0.7, delt_post: 0.4, trapezio: 0.4, avambracci: 0.4
core (plank/cr)   core: 1.0
rotation          core: 0.7, delt_post: 0.4
carry (farmer)    core: 0.7, avambracci: 1.0, trapezio: 0.7, glutei: 0.2
hip_thrust        glutei: 1.0, femorali: 0.4, core: 0.2
curl              bicipiti: 1.0, avambracci: 0.4
extension_tri     tricipiti: 1.0
lateral_raise     delt_lat: 1.0, trapezio: 0.2
face_pull         delt_post: 1.0, trapezio: 0.4
calf_raise        polpacci: 1.0
leg_curl          femorali: 1.0
leg_extension     quadricipiti: 1.0
adductor          adduttori: 1.0
```

**Volume effettivo**: se fai 3 serie di panca piana (push_h), il volume effettivo e':
- Petto: 3 x 1.0 = **3.0 serie effettive**
- Deltoide anteriore: 3 x 0.7 = **2.1 serie effettive**
- Tricipiti: 3 x 0.7 = **2.1 serie effettive**
- Core: 3 x 0.2 = **0.6 serie effettive**

Questo e' RADICALMENTE diverso dal sistema attuale che conta "3 serie per petto + 0.35 per tricipiti".
La contribuzione 0.7 per tricipiti nella panca e' supportata da EMG. Lo 0.35 era arbitrario.

### 2.5 Split Logic — Quale Split per Quale Frequenza

La scelta dello split NON e' arbitraria. Dipende dalla frequenza e dal livello.
Il principio guida e': **ogni muscolo deve essere stimolato 2x/settimana** (Schoenfeld 2016).

| Frequenza | Split | Freq/muscolo | Perche' |
|-----------|-------|-------------|---------|
| 2x/sett | Full Body | 2x | Ogni sessione = tutto il corpo. Unica opzione per 2x |
| 3x/sett | Full Body | 2-3x | 3 sessioni full body. Ogni muscolo 2-3x. Ideale principianti |
| 4x/sett | Upper/Lower | 2x | 2 upper + 2 lower. Ogni muscolo esattamente 2x |
| 5x/sett | U/L/Push/Pull/Legs | 2x | 2 U/L + 1 full, oppure ibrido. Ogni muscolo ~2x |
| 6x/sett | Push/Pull/Legs | 2x | 2 cicli PPL. Ogni muscolo esattamente 2x |

**Regola d'oro**: lo split e' un veicolo per la frequenza, non un fine.
Il 6x PPL non e' "piu' avanzato" del 3x full body — e' solo un modo diverso
di distribuire lo STESSO volume settimanale su piu' sessioni.

### 2.6 Rapporti Biomeccanici (Balance Ratios)

Squilibri tra catene muscolari causano infortuni. Il sistema deve monitorare:

| Rapporto | Target | Fonte | Perche' |
|----------|--------|-------|---------|
| Push : Pull | 1 : 1 (volume settimanale) | NSCA, Sahrmann | Equilibrio articolazione spalla |
| Push Orizz : Push Vert | ~2 : 1 | Pratica clinica | Petto + spalle bilanciati |
| Pull Orizz : Pull Vert | ~1 : 1 | NSCA | Dorsali completi (spessore + larghezza) |
| Quad : Ham | 1 : 0.8 (volume) | Alentorn-Geli 2009 | Stabilita' ginocchio, prevenzione ACL |
| Anteriore : Posteriore | 1 : 1.2 | Sahrmann, Janda | Postura, prevenzione cifosi/lordosi |
| Bilaterale | < 10% differenza | NSCA | Simmetria, prevenzione compensi |

### 2.7 Ordine degli Esercizi nella Sessione

L'ordine nella sessione segue una gerarchia fisiologica (NSCA):

```
1. ATTIVAZIONE     → mobilita' articolare, attivazione muscolare specifica
2. COMPOUND PESANTI → multi-articolari principali (alto SNC, alta intensita')
3. COMPOUND LEGGERI → multi-articolari accessori (intensita' moderata)
4. ISOLAMENTO       → mono-articolari (affaticamento locale, bassa SNC)
5. CORE/STABILITA'  → lavoro core (alla fine: se affaticato prima, compromette compound)
6. DEFATICAMENTO    → stretching, mobilita', ritorno alla calma
```

Questo e' l'ordine che il sistema deve rispettare nella generazione.
Non e' un suggerimento — e' fisiologia.

---

## 3. Architettura Proposta

### 3.1 Struttura Backend

```
api/services/training_science/
  __init__.py
  types.py              — Tipi Pydantic (MuscleContribution, VolumeTarget, SessionTemplate...)
  principles.py         — Costanti scientifiche, parametri per obiettivo, fonti bibliografiche
  muscle_contribution.py — Matrice contribuzione muscolare per pattern (EMG-based)
  volume_model.py       — MEV/MAV/MRV per muscolo × livello, calcolo volume effettivo
  split_logic.py        — Split per frequenza, generazione struttura sessioni
  balance_ratios.py     — Rapporti biomeccanici, validazione equilibrio
  session_order.py      — Regole ordinamento esercizi nella sessione
  plan_builder.py       — Orchestratore: genera piano completo da parametri
  plan_analyzer.py      — Analizza piano esistente (copertura, volume, balance)
```

Ogni file: 100-250 LOC. Totale stimato: ~1500 LOC (vs 1300 LOC attuali in un file solo).
Ma leggibili, testabili, e ognuno con una sola responsabilita'.

### 3.2 Principi Architetturali

1. **Separation of Concerns**: ogni file ha UNA responsabilita'
2. **Data over Code**: la scienza e' nei dati (costanti, tabelle), non nella logica
3. **Composability**: ogni modulo e' usabile indipendentemente
4. **Traceability**: ogni costante ha la fonte bibliografica nel docstring
5. **No Magic Numbers**: ogni numero ha un nome e una spiegazione
6. **Testability**: input/output puri, zero side effects, unit test semplici

### 3.3 Tipi Fondamentali

```python
from enum import Enum
from pydantic import BaseModel

class Obiettivo(str, Enum):
    FORZA = "forza"
    IPERTROFIA = "ipertrofia"
    RESISTENZA = "resistenza"
    DIMAGRIMENTO = "dimagrimento"
    TONIFICAZIONE = "tonificazione"

class Livello(str, Enum):
    PRINCIPIANTE = "principiante"
    INTERMEDIO = "intermedio"
    AVANZATO = "avanzato"

class GruppoMuscolare(str, Enum):
    PETTO = "petto"
    DORSALI = "dorsali"
    DELT_ANT = "deltoide_anteriore"
    DELT_LAT = "deltoide_laterale"
    DELT_POST = "deltoide_posteriore"
    BICIPITI = "bicipiti"
    TRICIPITI = "tricipiti"
    QUADRICIPITI = "quadricipiti"
    FEMORALI = "femorali"
    GLUTEI = "glutei"
    POLPACCI = "polpacci"
    TRAPEZIO = "trapezio"
    CORE = "core"
    AVAMBRACCI = "avambracci"
    ADDUTTORI = "adduttori"

class MovementPattern(str, Enum):
    PUSH_H = "push_h"           # Panca, push-up
    PUSH_V = "push_v"           # Military press, arnold
    SQUAT = "squat"             # Back squat, front squat, goblet
    HINGE = "hinge"             # Stacco, RDL, good morning
    PULL_H = "pull_h"           # Row, cable row
    PULL_V = "pull_v"           # Lat pulldown, trazioni
    CORE = "core"               # Plank, crunch, pallof
    ROTATION = "rotation"       # Russian twist, wood chop
    CARRY = "carry"             # Farmer walk, suitcase carry
    HIP_THRUST = "hip_thrust"   # Hip thrust, glute bridge
    CURL = "curl"               # Bicep curl varianti
    EXTENSION_TRI = "extension_tri"  # Tricep extension varianti
    LATERAL_RAISE = "lateral_raise"  # Alzate laterali
    FACE_PULL = "face_pull"     # Face pull, rear delt fly
    CALF_RAISE = "calf_raise"   # Calf raise varianti
    LEG_CURL = "leg_curl"       # Leg curl
    LEG_EXTENSION = "leg_extension"  # Leg extension
    ADDUCTOR = "adductor"       # Adduttori macchina/cavo

class SplitType(str, Enum):
    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PPL = "push_pull_legs"

class SessionRole(str, Enum):
    """Ruolo della sessione nello split."""
    FULL_BODY = "full_body"
    UPPER = "upper"
    LOWER = "lower"
    PUSH = "push"
    PULL = "pull"
    LEGS = "legs"

class ExerciseOrder(int, Enum):
    """Priorita' nell'ordinamento (1 = primo)."""
    WARMUP = 1
    COMPOUND_HEAVY = 2
    COMPOUND_LIGHT = 3
    ISOLATION = 4
    CORE_STABILITY = 5
    COOLDOWN = 6
```

### 3.4 Flusso Dati

```
Input utente:
  frequenza (2-6), obiettivo, livello, [dati_cliente opzionali]

1. split_logic.py
   → Quale split? (full_body / upper_lower / ppl)
   → Quante e quali sessioni? (ruoli + nomi)
   → Quanti slot per sessione? (basato su tempo disponibile + livello)

2. volume_model.py
   → Volume target per muscolo (MAV per livello, scalato per obiettivo)
   → Volume per sessione (distribuito sulle sessioni dello split)

3. plan_builder.py
   → Per ogni sessione: quali pattern servono? (da ruolo sessione + volume target)
   → Per ogni slot: quale pattern + quale muscolo target?
   → Verifica: copertura muscolare >= MEV per tutti i gruppi

4. muscle_contribution.py
   → Calcola volume effettivo per muscolo da tutti gli esercizi
   → Confronta con target MEV/MAV/MRV

5. balance_ratios.py
   → Verifica push:pull, quad:ham, ant:post
   → Segnala squilibri

6. session_order.py
   → Ordina slot nella sessione (compound pesanti → isolamento → core)

Output: SessionTemplate[] con slot tipizzati, pronti per il fill con esercizi reali
```

### 3.5 Volume Effettivo — Il Concetto Chiave

Il volume effettivo per un muscolo e' la somma dei contributi di TUTTI gli esercizi
della settimana, pesati per la matrice di contribuzione:

```
volume_effettivo[muscolo] = SUM(
  for exercise in settimana:
    serie[exercise] * contribuzione[exercise.pattern][muscolo]
)
```

Esempio concreto — settimana 4x Upper/Lower intermedio ipertrofia:

```
Upper A: Panca 4x8 + OHP 3x10 + Row 3x10 + Curl 3x12 + Lateral 3x12
Upper B: Lat Pull 4x8 + Row 3x10 + Panca incl 3x10 + Tricep ext 3x12 + Face pull 3x12
Lower A: Squat 4x8 + RDL 3x10 + Leg ext 3x12 + Calf 3x15
Lower B: Stacco 4x5 + BSS 3x10 + Leg curl 3x12 + Hip thrust 3x10

Volume effettivo PETTO:
  Panca 4x1.0 + Panca incl 3x1.0 = 7.0 serie dirette
  + OHP 3x0.0 (deltoide ant, non petto)
  = 7.0 serie effettive → MAV intermedio 12-16 → DEFICIT

Questo ci dice: servono piu' esercizi petto, o piu' serie.
Il sistema attuale non puo' fare questo calcolo perche' non ha la matrice.
```

---

## 4. Mapping con il Database Esercizi Esistente

### 4.1 Bridge: pattern_movimento → MovementPattern

Il database ha `pattern_movimento` come stringa con 9 valori forza + 3 complementari.
Il mapping e' quasi 1:1 con `MovementPattern`, ma la nuova tassonomia aggiunge
pattern di isolamento specifici che il DB non ha:

```python
DB_PATTERN_TO_SCIENCE = {
    # 1:1 mapping (gia' nel DB)
    "squat": MovementPattern.SQUAT,
    "hinge": MovementPattern.HINGE,
    "push_h": MovementPattern.PUSH_H,
    "push_v": MovementPattern.PUSH_V,
    "pull_h": MovementPattern.PULL_H,
    "pull_v": MovementPattern.PULL_V,
    "core": MovementPattern.CORE,
    "rotation": MovementPattern.ROTATION,
    "carry": MovementPattern.CARRY,
    # Complementari (mapping ragionevole)
    "warmup": None,   # non ha pattern di forza
    "stretch": None,
    "mobility": None,
}
```

I pattern di isolamento (`curl`, `extension_tri`, `lateral_raise`, ecc.) possono
essere derivati dalla **categoria** dell'esercizio + **muscolo primario**:
- categoria="isolation" + muscolo_primario="bicipiti" → `CURL`
- categoria="isolation" + muscolo_primario="tricipiti" → `EXTENSION_TRI`
- ecc.

### 4.2 Bridge: gruppo_muscolare → GruppoMuscolare

Il DB ha `muscoli` (53 record) raggruppati in `gruppo` (15 gruppi).
Il sistema scientifico ha 15 gruppi muscolari.

Il mapping richiede uno split dei "deltoidi" DB → 3 porzioni funzionali
(anteriore/laterale/posteriore), perche' nella programmazione hanno ruoli diversi.

### 4.3 Verso la Matrice Esercizio-Specifica

Fase 1 (ora): matrice per PATTERN (push_h, squat, ecc.) — ~18 pattern × 15 muscoli.
Approssimazione valida perche' esercizi dello stesso pattern hanno attivazione simile.

Fase 2 (futura): matrice per ESERCIZIO — usiamo i dati `esercizi_muscoli` gia' nel DB
(3370 righe con `ruolo` e `attivazione_percentuale`). Quando disponibile, sovrascrive
la matrice di pattern con dati esercizio-specifici.

---

## 5. API Endpoint

### 5.1 Metodologia (Read-Only Reference)

```
GET /api/training/methodology
  → { obiettivi, livelli, muscoli, patterns, split_types }

GET /api/training/volume-targets?livello=intermedio&obiettivo=ipertrofia&frequenza=4
  → { per_muscolo: { petto: { mev: 6, mav_min: 12, mav_max: 16, mrv: 22 }, ... } }

GET /api/training/contribution-matrix
  → { push_h: { petto: 1.0, tricipiti: 0.7, ... }, ... }

GET /api/training/split-recommendation?frequenza=4&livello=intermedio
  → { split: "upper_lower", sessioni: [...], rationale: "..." }
```

### 5.2 Plan Generation

```
POST /api/training/generate-plan
  body: { frequenza, obiettivo, livello, client_id? }
  → { sessioni: [...], volume_analysis: {...}, balance_check: {...} }

POST /api/training/analyze-plan
  body: { sessioni: [...] }  // piano esistente (anche creato a mano)
  → { volume_per_muscolo: {...}, balance_ratios: {...}, warnings: [...] }
```

---

## 6. Migrazione dal Sistema Attuale

### Cosa rimane
- `workout-templates.ts` → template manuali (non smart) — rimangono, ma usano la nuova API per i volumi
- `useSmartProgramming.ts` → hook aggregatore — rimane, chiama la nuova API
- SmartAnalysisPanel → UI — rimane, consuma nuovi dati
- MuscleMapPanel → UI — rimane, consuma nuovi dati
- Exercise scoring (14 scorer) → rimane nel frontend (rapido, client-side)

### Cosa viene sostituito
- `SESSION_BLUEPRINTS` (400 LOC hardcoded) → generati da `split_logic.py` + `plan_builder.py`
- `patternToMuscleRoles()` (30 LOC) → `muscle_contribution.py` (matrice EMG)
- `computeBlueprintCoverage()` (50 LOC) → `volume_model.py` (volume effettivo)
- `generateSmartPlan()` (200 LOC) → `plan_builder.py` backend
- `computeSmartAnalysis()` (100 LOC) → `plan_analyzer.py` backend
- `MUSCLE_TARGET_TIER` / `BASE_VOLUME_TARGETS` → `volume_model.py` (MEV/MAV/MRV reali)

### Cosa cambia nel frontend
- `smart-programming.ts`: da ~1300 LOC a ~400 LOC (solo scoring esercizi + utility UI)
- Nuovi hook: `useTrainingMethodology()`, `useGeneratePlan()`, `useAnalyzePlan()`
- I dati scientifici vengono dal backend, non sono hardcoded nel frontend

---

## 7. Piano di Implementazione

### Fase 1: Fondamenta (questo sprint)
1. `types.py` — tipi Pydantic
2. `principles.py` — costanti scientifiche per obiettivo
3. `muscle_contribution.py` — matrice contribuzione EMG
4. `volume_model.py` — MEV/MAV/MRV + calcolo volume effettivo
5. Unit test per ogni modulo

### Fase 2: Generazione (sprint successivo)
1. `split_logic.py` — split per frequenza + struttura sessioni
2. `session_order.py` — ordinamento esercizi
3. `balance_ratios.py` — rapporti biomeccanici
4. `plan_builder.py` — orchestratore generazione
5. `plan_analyzer.py` — analisi piani esistenti

### Fase 3: API + Frontend (sprint successivo)
1. Router `api/routers/training.py` — endpoint REST
2. Refactor `smart-programming.ts` — consuma API backend
3. Aggiornamento SmartAnalysisPanel e MuscleMapPanel

---

## 8. Fonti Bibliografiche

| Fonte | Anno | Contributo |
|-------|------|------------|
| NSCA — Essentials of Strength Training (Haff & Triplett) | 2016 | Parametri fondamentali per obiettivo |
| ACSM — Guidelines for Exercise Testing | 2009 | Raccomandazioni volume/intensita' |
| Schoenfeld — "The mechanisms of muscle hypertrophy" | 2010 | 3 meccanismi ipertrofia |
| Schoenfeld — "Dose-response for resistance training volume" | 2017 | Volume-hypertrophy dose-response |
| Schoenfeld — "Effects of RT frequency on hypertrophy" | 2016 | 2x/sett > 1x/sett meta-analisi |
| Schoenfeld — "Resistance Training Recommendations" | 2021 | Update raccomandazioni |
| Krieger — "Single vs multiple sets" | 2010 | Multiple sets superiori |
| Israetel — "Scientific Principles of Hypertrophy Training" | 2020 | MEV/MAV/MRV framework |
| Ralston et al. — "Strength training systematic review" | 2017 | Volume per forza |
| Bompa & Buzzichelli — "Periodization" | 2019 | Teoria periodizzazione |
| Contreras — "EMG analysis of resistance exercises" | 2010 | Attivazione muscolare per esercizio |
| Alentorn-Geli — "ACL injury prevention" | 2009 | Rapporto quad:ham |
| Sahrmann — "Movement System Impairment Syndromes" | 2002 | Rapporti push:pull, ant:post |
| Janda — "Muscles: Testing and Function" | 1983 | Cross syndromes, catene muscolari |

---

*Questo documento e' la base per la discussione. Ogni numero ha una fonte.
Ogni scelta architetturale ha una ragione. Partiamo da qui.*
