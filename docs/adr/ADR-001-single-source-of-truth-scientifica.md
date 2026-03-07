# ADR-001: Single Source of Truth Scientifica

**Stato**: Accettata
**Data**: 2026-03-07
**Autori**: gvera, Claude Opus 4.6

---

## Contesto

Il sistema FitManager ha sviluppato in parallelo due motori di calcolo scientifico:

1. **Backend** (`api/services/training_science/`, ~2000 LOC Python):
   Matrice EMG 18x15, volume MEV/MAV/MRV, parametri carico NSCA/ACSM,
   generatore piano 4 fasi, analizzatore 4D, periodizzazione a blocchi.
   Ogni numero ha una fonte bibliografica.

2. **Frontend** (`lib/smart-programming.ts`, ~1868 LOC TypeScript):
   Volume targets semplificati, blueprint hardcoded (15 template),
   pattern-to-muscle mapping statico, coverage/recovery/biomechanics analysis.
   Copia semplificata del backend senza fonti esplicite.

Questa duplicazione causa:
- **Divergenza**: coefficienti diversi tra backend e frontend
- **Manutenzione doppia**: ogni aggiornamento scientifico va fatto in due posti
- **Rischio brevettuale**: l'algoritmo proprietario e' esposto nel frontend
- **Barriera accademica**: ricercatori lavorano su Python, non TypeScript

## Decisione

**Il backend e' la Single Source of Truth (SSoT) per TUTTI i dati scientifici.**

Regola: se un numero ha una fonte bibliografica (NSCA, Schoenfeld, Israetel, ecc.),
vive SOLO in `api/services/training_science/`. Il frontend lo consuma via REST API.

### Cosa resta nel frontend

Solo logica UI-specific che richiede latenza zero:
- **Scoring 14D** per selezione esercizi live nel builder (interazione real-time)
- **Profilo client aggregato** (composizione di hook locali)
- **Safety breakdown** (conteggio per display, dati gia' dal backend)
- **Rendering** (barre, colori, pannelli — pura presentazione)

### Cosa migra al backend

Tutto il resto:
- Volume targets per muscolo → `GET /training-science/volume-targets`
- Generazione piano → `POST /training-science/plan`
- Analisi copertura/volume/recovery → `POST /training-science/analyze`
- Blueprint/split logic → `training_science/split_logic.py`
- Pattern-to-muscle mapping → `training_science/muscle_contribution.py`
- Parametri carico per obiettivo → `GET /training-science/parameters/{obj}`

### Pattern di consumo

```
Frontend                              Backend
TemplateSelector                      POST /training-science/plan
  → "Genera Scheda Smart"              → piano volume-driven
  → riceve piano strutturato            → 4 fasi + feedback loop
  → riempie slot con scoring 14D       (zero costanti nel frontend)

SmartAnalysisPanel                    POST /training-science/analyze
  → onChange scheda (debounce 300ms)    → analisi 4D completa
  → riceve AnalisiPiano                 → dual volume, balance, recovery
  → renderizza barre/colori            (zero calcolo nel frontend)

MuscleMapPanel                        (consuma output di /analyze)
  → riceve coverage per muscolo         → colora silhouette anatomica
```

## Conseguenze

**Positive**:
- Un solo posto per aggiornare costanti scientifiche
- Algoritmo protetto nel backend (brevettabile)
- Ricercatori universitari lavorano su Python
- Frontend snello e manutenibile (<300 LOC per modulo)
- Zero rischio di divergenza tra i due motori

**Negative**:
- Latenza API per analisi nel builder (mitigata con debounce 300ms + React Query cache)
- Il frontend non funziona offline per generazione piani (accettabile: e' un CRM desktop)
- Scoring 14D resta client-side (accettabile: serve latenza zero per UX)

## File impattati

### Backend (nessun cambio — gia' completo)
- `api/services/training_science/` (10 moduli)
- `api/routers/training_science.py` (5 endpoint)

### Frontend (da refactorare)
- `lib/smart-programming.ts` → `lib/smart-programming/` (5 moduli <300 LOC)
  - Rimuovere: volume targets, blueprint, coverage/recovery/biomechanics analysis
  - Tenere: scorers 14D, profilo client, safety breakdown, helpers UI
- `hooks/useTrainingScience.ts` — nuovo hook per 5 endpoint backend
- `components/workouts/SmartAnalysisPanel.tsx` — consuma API invece di calcolare
- `components/workouts/TemplateSelector.tsx` — genera via API invece di blueprint locali

### Documentazione
- `CLAUDE.md` — sezione SSoT + regola file size + Smart Programming riscritta
- `TRAINING-SCIENCE-SPEC.md` — aggiunta sezione integrazione frontend
- `KINESCORE-ROADMAP.md` — Fase 0c aggiornata con scope preciso
