# FitManager AI Studio — Manifesto Architetturale v2

> *"Il codice, in primis, deve essere elegante e facilmente rileggibile.
> L'eleganza non e' un vezzo estetico: e' la base della manutenibilita'."*

Questo file e' la **Costituzione** del progetto.
Regole dettagliate per backend e frontend: vedi `api/CLAUDE.md` e `frontend/CLAUDE.md`.

---

## Missione

CRM di riferimento per personal trainer e professionisti fitness a P.IVA.
Gestisce salute fisica e contabilita' di persone reali. Zero approssimazione.

**Stack**: FastAPI + SQLModel | Next.js 16 + React 19 + shadcn/ui | SQLite (PostgreSQL-ready) | Ollama + ChromaDB (AI locale)
**Filosofia**: Privacy-first. Tutto in locale, zero cloud, zero dati verso terzi.
**Utente**: Non programmatore esperto, sta imparando il coding con AI.

---

## Esperienza Utente — Pilastro

> *"Il cliente deve aver piacere nell'usare il programma.
> Un'app che migliora la qualita' del lavoro migliora la qualita' della vita."*

L'UX non e' una feature: e' il motivo per cui il cliente sceglie noi.

1. **Actionable, non informativo** — Ogni schermata guida verso l'azione giusta. Alert con CTA contestuali ("Riscuoti", "Aggiorna stato"), mai "Vai" generico.
2. **Gerarchia visiva** — L'occhio arriva prima dove serve. Critico > Avviso > Informativo. Colori, icone e animazioni comunicano urgenza.
3. **Micro-interazioni** — Hover, transizioni, feedback visivo. L'app deve sentirsi *viva* e reattiva.
4. **Zero frustrazione** — Empty state descrittivi, error message utili, loading state chiari. Mai lasciare l'utente senza contesto.
5. **Italiano impeccabile** — Singolare/plurale, accenti, punteggiatura. L'UI e' la voce del prodotto.
6. **Mobile-first responsive** — Ogni pagina funziona su mobile (375px+), tablet (768px+) e desktop. Breakpoints Tailwind (`sm:`, `md:`, `lg:`), zero librerie extra. Dettagli in `frontend/CLAUDE.md`.

### Visual Identity — Teal Accent

Palette colori: oklch color space in `globals.css`. Primary = teal (hue 170).
- Light: `oklch(0.55 0.15 170)` — Dark: `oklch(0.70 0.15 170)`
- Background: warm off-white `oklch(0.995 0.003 180)` / warm charcoal `oklch(0.15 0.01 200)`
- Radius: `0.75rem` — angoli morbidi
- Sidebar warm tint, chart e ring allineati a teal
- KPI typography: extrabold + tracking-tighter + tabular-nums per numeri
- Card hover: `transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg`

### Command Palette (Ctrl+K) — Feature Distintiva

Elemento chiave di UX: ricerca fuzzy globale con 3 capacita' avanzate.

1. **Preview Panel**: pannello dati a destra (solo desktop) con info live dell'elemento selezionato
   (statistiche cliente, muscoli esercizio, KPI finanziari)
2. **Risposte KPI dirette**: digiti "entrate" e vedi il numero inline senza navigare
3. **Azioni Contestuali**: la palette sa dove sei (es. `/clienti/5`) e suggerisce azioni per quel cliente

Implementazione: `cmdk` v1.1.1 + shadcn Command. Custom Dialog (non CommandDialog) per split layout.
Dati lazy-loaded via React Query (`enabled: open`). Zero prop drilling — custom event per apertura da sidebar.

File: `frontend/src/components/layout/CommandPalette.tsx` (~700 LOC).

### Workout Template Builder — Schede Allenamento

Editor strutturato per creare schede allenamento professionali. Layout split: editor (sinistra) + preview live (destra, desktop).

**Backend**: 3 tabelle (`schede_allenamento`, `sessioni_scheda`, `esercizi_sessione`) con Deep IDOR chain: `EsercizioSessione → SessioneScheda → SchedaAllenamento.trainer_id`. CRUD completo + duplicate + full-replace sessioni (atomico). `id_cliente` FK opzionale per collegare schede a clienti (riassegnabile via PUT con bouncer check).

**Frontend**: 3 sezioni per sessione — Avviamento, Principale, Stretching & Mobilita.
- **Grid compatto**: principale 7 colonne `[grip_20|info_14|nome_1fr|serie_44|rip_52|riposo_44|del_24]`, compact 6 colonne (senza riposo). Tempo esecuzione e note NON in griglia — accessibili via espansione unificata (Info icon)
- **Espansione unificata**: click Info → riga con nota input + tempo esecuzione input + ExerciseDetailPanel. Un solo toggle, non 3 separati
- **Dot indicator**: teal dot accanto al nome se esercizio ha note/tempo compilati
- **Delete hover-reveal**: bottone elimina semi-trasparente, visibile pieno su hover riga (`group/row`)
- **Session overflow menu**: azioni sessione (note, duplica, elimina) in DropdownMenu (⋮) invece di 3 bottoni icon
- **Smart Defaults**: `getSmartDefaults()` in `workout-templates.ts` — serie/rip/riposo basati su obiettivo scheda + rep range esercizio
- **Badge "In scheda"**: ExerciseSelector mostra badge per esercizi gia' presenti nella scheda corrente
- **Guardia beforeunload**: previene perdita modifiche non salvate su chiusura tab/refresh
- **Template system**: 3 template (Beginner/Intermedio/Avanzato) con matching base esercizi per `pattern_movimento` + difficolta
- **Exercise Selector**: dialog professionale con filtri pattern_movimento + gruppo muscolare + attrezzatura + difficolta + biomeccanica (chip cliccabili) + ricerca testuale. Filtro categoria automatico per sezione. **Pannello dettaglio inline** (icona Info): muscoli, classificazione, setup, note sicurezza, relazioni actionable con "Sostituisci", deep-link a pagina esercizio con ritorno
- **DnD**: `@dnd-kit/sortable` per riordino esercizi dentro ogni sezione
- **Export "Scheda Clinica"**: Excel via `exceljs` — documento medico-sportivo proprietario. 3+ fogli: Copertina (branding + dati programma) → Profilo Clinico (safety, opzionale) → 1 foglio per sessione. Esercizi principali in card-block (header teal + 2 righe dati + immagini 150x100 affiancate + separatore). Avviamento/stretching compatti. Immagini via Next.js rewrite proxy (`/media/*` → backend, evita CORS su StaticFiles). Print/PDF via `@media print`
- **Client linkage**: assegnazione/riassegnazione cliente inline (Select + `"__none__"` sentinel), filtro cliente nella lista, tab "Schede" nel profilo cliente, cross-link bidirezionale
- **TemplateSelector**: dialog con selezione cliente integrata (`selectedClientId` state, pre-compilato da contesto)
- **97 esercizi attivi** (database curato, 100% completo su tutti i campi, 100% con foto) + 962 archiviati (reinserimento graduale post-sviluppo)
- Tassonomia completa: muscoli FK (1,271 righe), articolazioni FK (299), condizioni mediche FK (474+), relazioni (38)
- Categorie: `compound`, `isolation`, `bodyweight`, `cardio`, `stretching`, `mobilita`, `avviamento`
- Pattern: 9 forza (`squat`, `hinge`, `push_h/v`, `pull_h/v`, `core`, `rotation`, `carry`) + 3 complementari (`warmup`, `stretch`, `mobility`)

- **Exercise Detail Panel** (`ExerciseDetailPanel.tsx`): pannello riassuntivo riusabile (muscoli, classificazione, setup, note sicurezza, relazioni con quick-swap "Sostituisci", deep-link con ritorno). Usato sia in SortableExerciseRow che in ExerciseSelector
- **Deep-Link Esercizio**: `/esercizi/{id}?from=scheda-{schedaId}` → banner "Torna alla scheda" + back button condizionale. Navigazione bidirezionale builder↔dettaglio esercizio

File chiave: `lib/workout-templates.ts` (template + `getSectionForCategory` + `getSmartDefaults`), `components/workouts/SessionCard.tsx` (3 sezioni DnD, overflow menu), `components/workouts/SortableExerciseRow.tsx` (grid compatto, espansione unificata), `components/workouts/ExerciseDetailPanel.tsx` (dettaglio inline).

### Exercise Quality Engine — Pipeline Dati

> **Filosofia: l'allenamento e' un sottoramo della medicina.** Il database esercizi e' il nucleo del prodotto.
> Contenuti imprecisi possono causare infortuni. Zero approssimazione.

**Strategia "Database 97"**: i 97 esercizi curati sono l'unico database attivo (`in_subset=True`), tutti con foto.
I 962 esercizi archiviati (`in_subset=False`) verranno reinseriti a lotti post-sviluppo.

Pipeline idempotente, dual-DB (`--db dev|prod|both`), script in `tools/admin_scripts/`:

| Script | Cosa fa | Modello |
|--------|---------|---------|
| `populate_taxonomy.py` | Muscoli + articolazioni FK per subset | Zero Ollama |
| `populate_conditions.py` | Condizioni mediche FK (keyword matching deterministico) | Zero Ollama |
| `populate_exercise_relations.py` | Progressioni/regressioni tra esercizi subset | Zero Ollama |
| `fill_subset_gaps.py` | Muscoli secondari + tempo consigliato (lookup deterministico) | Zero Ollama |
| `fix_subset_classification.py` | Fix pattern/force/plane per subset | Zero Ollama |
| `enrich_exercise_fields.py` | Enrichment campi descrittivi (per reinserimento batch) | Mixtral |
| `backfill_exercise_fields.py` | note_sicurezza + force/lateral (per reinserimento batch) | gemma2:9b |
| `verify_exercise_quality.py` | Audit qualita' (per validazione pre-attivazione) | Zero Ollama |
| `activate_batch.py` | Orchestratore foto-first: audit, deactivate, select, enrich, activate, verify | gemma2:9b |

**Reinserimento futuro**: `activate_batch.py --db both` — coverage-driven selection, enrichment Ollama, quality gate con rollback automatico.
Mai attivare esercizi con campi critici mancanti o senza foto.

### Tassonomia Scientifica Esercizi — Architettura a Strati

> **Filosofia: senza classi, nessuna AI puo' ragionare.** Ispirata alla classificazione BIC/YOLO:
> dati strutturati a strati con capacita' di incrociare ogni dimensione.

Approccio ML: subset perfetto (~97 esercizi, 100% foto) → pipeline completa → scala a ~1059.

**Schema** (migrazione `949f3f3fd5ed` — 6 tabelle + 4 colonne):

| Tabella | Tipo | Record | Descrizione |
|---------|------|--------|-------------|
| `muscoli` | Catalogo | 53 | Muscoli anatomici NSCA/ACSM (15 gruppi, 3 regioni) |
| `articolazioni` | Catalogo | 15 | Articolazioni principali (5 tipi, 3 regioni) |
| `condizioni_mediche` | Catalogo | 39 | Condizioni rilevanti (5 categorie, body_tags JSON) |
| `esercizi_muscoli` | Junction M:N | ~1271 | Esercizio↔muscolo con ruolo (primary/secondary/stabilizer) + attivazione % |
| `esercizi_articolazioni` | Junction M:N | ~299 | Esercizio↔articolazione con ruolo (agonist/stabilizer) + ROM gradi |
| `esercizi_condizioni` | Junction M:N | ~474 | Esercizio↔condizione con severita' (avoid/caution/modify) + nota |

Colonne su `esercizi`: `in_subset` (flag sviluppo), `catena_cinetica` (open/closed),
`piano_movimento` (sagittal/frontal/transverse/multi), `tipo_contrazione` (concentric/eccentric/isometric/dynamic).

**Subset attivo**: 97 esercizi (`in_subset=1`) selezionati algoritmicamente per copertura
su 11 pattern × 14 gruppi muscolari × 8 attrezzature × 3 difficolta' × 6 categorie, tutti con foto.
L'API filtra `Exercise.in_subset == True` — rimuovere per riattivare catalogo completo.

**Modelli API**: `muscle.py` (Muscle + ExerciseMuscle), `joint.py` (Joint + ExerciseJoint),
`medical_condition.py` (MedicalCondition + ExerciseCondition).

**Script**: `seed_taxonomy.py` (cataloghi hardcoded), `populate_taxonomy.py` (mapping deterministico).

**Frontend**: hero esercizio mostra muscoli anatomici raggruppati, articolazioni con ruolo,
classificazione biomeccanica (catena, piano, contrazione). Fallback gruppi generici per esercizi fuori subset.

### Safety Engine — Scudo Clinico Interattivo

> **Filosofia: INFORMARE, mai LIMITARE.** Il sistema e' progettato per laureati in scienze motorie.
> Il trainer decide SEMPRE. Il motore fornisce indicatori visivi, mai blocchi o restrizioni.

Motore backend deterministico che incrocia anamnesi cliente con condizioni mediche per produrre
una safety map per-esercizio. Zero Ollama, zero latenza percepita.

**Backend** (`api/services/safety_engine.py`, `api/services/condition_rules.py`, `api/schemas/safety.py`):
- `extract_client_conditions(anamnesi_json)` → `set[condition_id]` (2 livelli: flag strutturali + keyword matching)
- `build_safety_map(session, client_id, trainer_id)` → `SafetyMapResponse` (bouncer + anti-N+1: 3 query)
- `condition_rules.py`: regole deterministiche (`ANAMNESI_KEYWORD_RULES`, `STRUCTURAL_FLAGS`, `match_keywords`)
- 39 condizioni mediche (30 specifiche + 9 generiche: 7 post-traumatiche per zona + cervicalgia + lombalgia)
- `match_keywords()` accent-insensitive: normalizza `a'` == `a` == Unicode accent (italiano)
- `obiettivi_specifici` ESCLUSO dal keyword scanning (previene falsi positivi da goal text)
- Endpoint: `GET /exercises/safety-map?client_id=N` (JWT auth + trainer bouncer)
- Response: `SafetyMapResponse` con `entries: dict[exercise_id, ExerciseSafetyEntry]`, `condition_names`, `condition_count`
- Severita' per esercizio: worst-case aggregation (`_SEVERITY_ORDER`: avoid > caution > modify)
- `SafetyConditionDetail` include `categoria` (orthopedic, cardiovascular, metabolic, neurological, respiratory, special)

**Frontend** — 4 livelli di visualizzazione (dal macro al micro):

1. **Safety Overview Panel** (`schede/[id]/page.tsx`): Card collapsibile con KPI (condizioni/evitare/cautela),
   badge condizioni, e dettaglio espanso raggruppato per categoria. Sostituisce il vecchio banner ambra.
2. **Session Pills** (`SessionCard.tsx`): contatori avoid/caution nel CardHeader di ogni sessione.
3. **Exercise Popover** (`SortableExerciseRow.tsx`): click su icona safety → Popover ricco (w-72) con
   condizioni dettagliate (severita + nome + nota) + **alternative sicure con "Sostituisci"** (quick-swap).
4. **Selector Detail** (`ExerciseSelector.tsx`): badge safety cliccabile → pannello espandibile inline
   con dettaglio condizioni per ogni esercizio nel dialog di selezione.
5. **Exercise Detail Panel** (inline nel builder + selector): icona Info → pannello riassuntivo con
   muscoli, classificazione, setup, note sicurezza, relazioni actionable (progressioni/regressioni con "Sostituisci").

**Hook**: `useExerciseSafetyMap(clientId)` in `hooks/useWorkouts.ts` — React Query con `enabled: !!clientId`.

File chiave: `api/services/safety_engine.py` (engine), `api/services/condition_rules.py` (regole),
`components/workouts/SortableExerciseRow.tsx` (SafetyPopover + Info panel), `components/workouts/ExerciseDetailPanel.tsx` (dettaglio inline riusabile),
`components/workouts/ExerciseSelector.tsx` (selettore con dettaglio), `schede/[id]/page.tsx` (Overview Panel + quick-replace handler).

### Analisi Clinica — Motore Chinesiologico Client-Side

> **Filosofia: il chinesiologo non guarda solo "dove sei" ma "come cambi" e "dove vai".**
> Il sistema trasforma dati grezzi in insight actionable basati su fonti scientifiche.

4 librerie TypeScript pure (zero backend, dati statici + computazione da misurazioni):

**`lib/normative-ranges.ts`** — Range normativi OMS/ACSM/AHA/ESH per classificare valori:
- BMI (OMS universale), Massa Grassa % (ACSM × sesso × 5 fasce eta'), FC Riposo (AHA),
  PA Sistolica/Diastolica (ESH/ESC 2023)
- `classifyValue(metricId, value, sesso, age)` → `{ label, color }` o null
- `getNormativeBands(metricId, sesso, age)` → bande per chart ReferenceArea
- `getHealthyRange(metricId, sesso, age)` → fascia sana per hint target goal
- `BAND_COLOR_CLASSES` / `BAND_CHART_FILLS` per styling coerente

**`lib/measurement-analytics.ts`** — Velocita' di cambiamento settimanale:
- `computeWeeklyRate(measurements, metricId, windowDays)` → delta/settimana
- `formatRate(rate, unit)` → "−0.5 kg/sett"
- Backend: `velocita_settimanale` + `num_misurazioni` in `GoalProgress`

**`lib/derived-metrics.ts`** — Metriche derivate da dati raw:
- BMI, LBM (massa magra), FFMI (Kouri et al. 1995), WHR, MAP (pressione arteriosa media)
- Forza relativa: NSCA benchmarks (squat/panca/stacco × sesso) con 5 livelli
- `computeAllDerived(measurements, sesso, age)` → `DerivedMetricsResult`

**`lib/clinical-analysis.ts`** — Orchestratore 5 moduli clinici:
1. **Metriche Derivate** — BMI + LBM + FFMI + WHR + MAP con classificazione
2. **Assessment Velocita'** — rate vs soglie ACSM (>1% peso/sett = rischio catabolismo)
3. **Composizione Espansa** — 8 fasi (cutting/recomp/lean_bulk/plateau/muscle_loss/optimal_growth/critical/bulk),
   decomposizione ΔFM + ΔLBM, proiezione temporale al goal
4. **Simmetria Bilaterale** — braccia/cosce/polpacci R/L con soglie (1.0-2.5cm per body part)
5. **Profilo Rischio** — screening metabolico (WHR + BMI + grasso%) + cardiovascolare (PA + FC),
   suggerimento referral se alto rischio

**`lib/metric-correlations.ts`** — Correlazione inter-metrica (3 coppie):
- Peso + Grasso % → 8 scenari composizione (perdita grasso, catabolismo, ricomposizione...)
- Vita + Fianchi → WHR con classificazione OMS per sesso + trend
- PA Sistolica + Diastolica → classificazione ESH combinata + pressione differenziale

**Frontend**: `ClinicalAnalysisPanel.tsx` (~510 LOC) in ProgressiTab — 5 sezioni collassabili
con bordo severity-colorato + badge. Riceve `measurements`, `sesso`, `dataNascita`, `goals`.

**Integrazione**: `MeasurementChart` mostra `<ReferenceArea>` bande normative.
`GoalFormDialog` mostra hint range sano sotto target. `GoalsSummary` propaga sesso/dataNascita.

---

## Architettura

```
frontend/          Next.js 16 + React 19 + TypeScript
  src/hooks/       React Query (server state) — 11 hook modules
  src/components/  shadcn/ui + componenti dominio — ~80 componenti
  src/types/       Interfacce TypeScript (mirror Pydantic)
       |
       | REST API (JSON over HTTP, JWT auth)
       v
api/               FastAPI + SQLModel ORM
  models/          11 modelli ORM (SQLAlchemy table=True)
  routers/         11 router con Bouncer Pattern + Deep IDOR
  schemas/         Pydantic v2 (input/output validation)
       |
       v
SQLite             data/crm.db — 23 tabelle, FK enforced
       |
core/              Moduli AI (dormant, non esposti via API — prossima fase)
  exercise_archive, knowledge_chain, card_parser, ...
```

### Separazione dei layer (Il Muro)

| Layer | Puo' importare | NON puo' importare |
|-------|---------------|-------------------|
| `api/` | sqlmodel, pydantic, fastapi, stdlib | `core/`, `streamlit`, `frontend/` |
| `frontend/` | react, next, @tanstack/react-query | `api/`, `core/` (solo REST calls) |
| `core/` | stdlib, pydantic, langchain, ollama | `api/`, `streamlit` |

`api/` e `core/` sono **completamente indipendenti**. Operano sullo stesso DB con ORM diversi.
Il frontend comunica col backend SOLO via HTTP.

---

## Design Pattern Universali

### 1. Bouncer Pattern (Early Returns)
Ogni funzione valida le precondizioni e esce subito. Max 2 livelli di nesting.
```python
# Backend
def update_rate(rate_id, data, trainer, session):
    rate = _bouncer_rate(session, rate_id, trainer.id)  # 404 se non suo
    contract = session.get(Contract, rate.id_contratto)
    if contract.chiuso:
        raise HTTPException(400, "Contratto chiuso")     # business rule
    # flusso principale — piatto
```

### 2. Deep Relational IDOR (Backend)
Ogni operazione verifica ownership attraverso la catena FK:
`Rate → Contract.trainer_id` | `Contract → Client.trainer_id` | `Event → trainer_id` | `SchedaAllenamento.id_cliente → Client.trainer_id`

Se non trovato → 404. Mai 403 (non rivelare esistenza di dati altrui).

### 3. Atomic Transactions (Backend)
Operazioni multi-tabella (pay_rate, unpay_rate) usano un singolo `session.commit()`.
Se qualsiasi step fallisce → rollback automatico. Tutto o niente.

### 3b. Contract Integrity Engine (Backend)
Il contratto e' l'entita' centrale: collega pagamenti, crediti, sessioni.
- **Residual validation**: `_cap_rateizzabile()` centralizzato — calcola `acconto = totale_versato - sum(saldato)`, `cap = prezzo - acconto`, `spazio = cap - sum(previsto)`. Usato da `create_rate` e `update_rate` (con `exclude_rate_id` per escludere la rata in modifica)
- **Chiuso guard**: rate, piani, eventi bloccati su contratti chiusi
- **Credit guard**: `create_event` rifiuta assegnazione a contratti con crediti esauriti (400)
- **Auto-close/reopen** (SIMMETRICO):
  - Condizione chiusura: `stato_pagamento == "SALDATO"` AND `crediti_usati >= crediti_totali`
  - **Lato rate**: `pay_rate` chiude, `unpay_rate` riapre (via stato_pagamento)
  - **Lato eventi**: `create_event`, `delete_event`, `update_event(stato)` — tutti usano `_sync_contract_chiuso()`
  - INVARIANTE: ogni operazione che modifica `crediti_usati` o `stato_pagamento` DEVE ricalcolare `chiuso`
- **Overpayment check**: `pay_rate` verifica sia rata-level che contract-level
- **Flexible rate editing**: rate pagate (SALDATA/PARZIALE) modificabili — `data_scadenza` e `descrizione` sempre, `importo_previsto` se >= saldato. Stato auto-ricalcolato (SALDATA↔PARZIALE)
- **CashMovement date sync**: modifica `data_scadenza` su rata pagata → aggiorna `data_effettiva` di tutti i CashMovement collegati (atomico)
- **Rate date boundary**: `create_rate` e `update_rate` rifiutano `data_scadenza` oltre `contract.data_scadenza` (422). `generate_payment_plan` auto-cap: se `due_date > contract.data_scadenza` → `due_date = contract.data_scadenza`
- **Contract shortening guard**: `update_contract` rifiuta nuova `data_scadenza` se rate esistono oltre la nuova data (422, messaggio con conteggio rate)
- **Expired contract detection**: `ha_rate_scadute` include rate non saldate su contratti scaduti (`or_(rate.data_scadenza < today, contract.data_scadenza < today)`) — sia su contratti che su clienti
- **Delete guard**: contratto eliminabile solo se zero rate non-saldate + zero crediti residui
- **Payment history**: `receipt_map` come `dict[int, list[CashMovement]]` — storico completo per rata

### 4. React Query + Toast (Frontend)
Ogni hook: `useQuery` per lettura, `useMutation` per scrittura.
Ogni mutation invalida le query correlate + mostra toast (sonner).

### 5. Type Synchronization
Pydantic schema (backend) == TypeScript interface (frontend).
Se cambi uno, DEVI aggiornare l'altro. File: `api/schemas/` ↔ `frontend/src/types/api.ts`.

---

## Anti-Pattern Vietati

1. **Arrow code** — Nesting > 3 livelli. Usare Bouncer + list comprehension.
2. **Catch-all** — `except Exception: pass` e bare `except:`. Solo eccezioni specifiche.
3. **Magic strings** — Usare Enum/costanti. Mai `"PENDENTE"` inline.
4. **print() per logging** — Usare `logger` (core) o `console.error` (frontend).
5. **Dict raw** — I repository/router restituiscono modelli Pydantic tipizzati.
6. **any** — TypeScript: mai `any`. Definire interfacce in `types/api.ts`.
7. **N+1 queries** — Batch fetch con `IN (...)` o `selectinload`. Mai loop di query.
8. **Mass Assignment** — Input schema SENZA campi protetti (trainer_id, id dal JWT).

### 6. Chiavi Univoche per Selezione UI (Frontend)
Quando un `Set<string>` gestisce selezione multipla, la chiave DEVE essere univoca per item.
Se piu' record condividono la stessa chiave (es. `mese_anno_key = "2026-02"` per 3 spese mensili),
il Set li collassa → selezione "tutto o niente". Usare chiavi composte: `${id}::${key}`.

---

## Pitfalls Documentati

Errori reali trovati e corretti. MAI ripeterli.

| Pitfall | Causa | Fix |
|---------|-------|-----|
| `<label>` + Radix Checkbox | Browser propaga click al form control interno → double-toggle | Usare `<div onClick>` + `Checkbox onClick={stopPropagation}` |
| `datetime(y, m, day+N)` con N grande | `day=35` → `ValueError` (mese ha max 31 giorni) | Usare `base_date + timedelta(weeks=N)` |
| `Set<string>` con chiave non-univoca | `mese_anno_key` identica per piu' spese dello stesso mese | Chiave composta `${id}::${key}` |
| Auto-close senza auto-reopen eventi | Contratto chiuso restava bloccato dopo delete/cancel eventi | `_sync_contract_chiuso()` simmetrico su create/delete/update |
| Seed atomico crash a meta' | Transazione unica → rollback → DB vuoto → login impossibile | Validare i dati PRIMA del commit (es. date overflow) |
| Invalidation asimmetrica pay/unpay | `usePayRate` mancava `["movements"]`, `["movement-stats"]` | Operazioni inverse DEVONO avere invalidazione identica |
| Popup inside `.rbc-event` | `overflow:hidden` clippava popup absolute-positioned | `createPortal(popup, document.body)` + `position:fixed` |
| Calendar unmount su navigazione | `onRangeChange` → new query key → `isLoading=true` → unmount → reset | `keepPreviousData` + smart range buffering |
| KPI mese sfasato | react-big-calendar grid start in mese precedente (es. 23 feb per marzo) | `rangeLabel` usa midpoint del range per vista mese |
| KPI esclude ultimo giorno | `visibleRange.end` = mezzanotte 00:00 → eventi quel giorno esclusi | `endOfDay()` su `visibleRange.end` in `handleRangeChange` |
| D&D sposta evento -1h | `toISOString()` converte Date locale in UTC → perde offset fuso orario | `toISOLocal()` centralizzata in `lib/format.ts` — formatta in ora locale senza `Z` |
| 401 interceptor loop su login | Interceptor cattura 401 del login (credenziali errate) → redirect silenzioso → perde errore | Skip redirect se `pathname.startsWith("/login")` |
| Cap residuo double-counting | `cap = prezzo - totale_versato` conta saldato 2x (in totale_versato E sum rate) → edit rate pagata blocca | `_cap_rateizzabile()`: `acconto = totale_versato - sum(saldato)`, `cap = prezzo - acconto` |
| uvicorn senza `--host 0.0.0.0` | Backend ascolta solo `127.0.0.1` → LAN (`192.168.1.23`) rifiutata → Chiara vede errore su tutte le pagine ma localhost funziona | SEMPRE `--host 0.0.0.0` su entrambi i backend |
| `next start` senza `-H 0.0.0.0` | Frontend ascolta solo localhost → iPad/Tailscale (`100.x.x.x`) riceve "Application error: client-side exception" | SEMPRE `-H 0.0.0.0` su `next start` prod: `next start -p 3000 -H 0.0.0.0` |
| Zombie uvicorn: PID morto nel netstat | `netstat` mostra PID padre (morto), `taskkill` dice "non trovato", figlio zombie ha PID diverso | `kill-port.sh` (tree-kill) oppure cercare figli: `Get-CimInstance Win32_Process \| Where ParentProcessId -eq <PID>` |
| KPI NaN da worker zombie | Worker zombie serve codice vecchio (senza campi KPI) → `data.kpi_X` = undefined → `formatCurrency(undefined)` = NaN | `?? 0` guard su ogni `getKpiValue` + kill zombie e riavviare |
| Rate oltre scadenza contratto | Nessuna validazione date rate vs contratto → rate orfane dopo scadenza | Boundary check bidirezionale: create/update rate (422) + update contract (422) + DatePicker maxDate |
| `ha_rate_scadute` ignora contratti scaduti | Solo `rate.data_scadenza < today`, non considera contratto expired con rate future non saldate | `or_(Rate.data_scadenza < today, Contract.data_scadenza < today)` in contracts.py e clients.py |
| KPI "Rate Scadute" conta contratti | `func.count(func.distinct(Rate.id_contratto))` conta contratti, non rate reali | `func.count(Rate.id)` per conteggio rate effettive (contracts), label corretta per clienti |
| Badge dentro `SelectTrigger` Radix | `position="item-aligned"` (default) richiede `SelectValue` nel trigger per calcolare posizione dropdown. Badge/div sostitutivo → dropdown non si apre silenziosamente | Usare SEMPRE `SelectValue` + `position="popper"` per trigger custom. Mai sostituire `SelectValue` con Badge |
| `useUpdateClient` stale profile | `onSuccess` invalidava `["clients"]` lista ma non `["client", id]` → profilo cliente non si aggiornava dopo modifica | Invalidare SEMPRE sia la lista `["entities"]` che il dettaglio `["entity", id]` in ogni mutation di update |
| Utility duplicate in 8+ file | `formatShortDate`, `getFinanceBarColor` copia-incollate in ogni componente → divergenza e manutenzione impossibile | Centralizzare in `lib/format.ts` e importare. MAI definire utility di formattazione localmente |
| `<button>` nested in `<button>` | PopoverTrigger (button) dentro button nome esercizio → hydration error Next.js | SafetyPopover e name button come siblings dentro `<div>`, MAI annidati |
| `fetch()` CORS su StaticFiles | `fetch()` cross-origin bloccato da CORS su StaticFiles backend, ma `<img>` funziona (esente da CORS) → export Excel senza foto | Next.js `rewrites` in `next.config.ts` proxya `/media/*` al backend → fetch same-origin. MAI `getMediaUrl()` per fetch, solo URL relativi |

---

## Sicurezza (Non Negoziabile)

1. **Multi-tenancy**: trainer_id da JWT, iniettato server-side, mai dal body
2. **Query parametrizzate**: `WHERE id = ?` (core/) o `select().where()` (api/)
3. **3 layer auth**: Edge Middleware → AuthGuard client → JWT API validation
4. **Niente PII nei prompt LLM**: usare attributi anonimi
5. **Solo LLM locale** (Ollama): mai inviare dati a cloud senza consenso

---

## Workflow di Sviluppo

Ogni feature segue 4 step in ordine. Il codice non passa al successivo finche' il precedente e' solido.

### Step 1: Schema + Types
- Backend: Pydantic schema in `api/schemas/` + SQLModel in `api/models/`
- Frontend: TypeScript interface in `frontend/src/types/api.ts`

### Step 2: Router / Endpoint
- Endpoint in `api/routers/` con Bouncer Pattern + Deep IDOR
- Atomic transactions dove serve (pagamenti, revoche)

### Step 3: Hook + UI
- Custom hook in `frontend/src/hooks/`
- Componente React in `frontend/src/components/`
- Pagina in `frontend/src/app/(dashboard)/`

### Step 4: Build + Verifica
- `npx next build` (frontend) — zero errori TypeScript
- Test end-to-end: avvia API → avvia frontend → login → verifica flusso
- Commit con messaggio chiaro

---

## Architettura Dual Environment (Produzione + Sviluppo)

> **Runbook operativo completo**: `tools/DUAL_ENV.md` — procedure, troubleshooting, checklist.

Due ambienti completamente isolati. Stessa codebase, DB e porte diversi.

```
PRODUZIONE (Chiara — sempre acceso, dati reali):
  Backend:  porta 8000  →  data/crm.db
  Frontend: porta 3000  →  next start (production mode)
  Accesso LAN:       http://192.168.1.23:3000
  Accesso Tailscale: http://100.127.28.16:3000  (da qualsiasi rete)

SVILUPPO (gvera — dati di test, libero per esperimenti):
  Backend:  porta 8001  →  data/crm_dev.db
  Frontend: porta 3001  →  next dev (hot reload)
  Accesso: http://localhost:3001
```

### API URL Dinamico (zero IP hardcodati nel build)
Il frontend deduce l'API URL da `window.location` a runtime:
- `hostname:3000` → `hostname:8000/api` (prod)
- `hostname:3001` → `hostname:8001/api` (dev)
- Funziona automaticamente da LAN, Tailscale, localhost — zero `.env` da aggiornare
- Logica: `frontend/src/lib/api-client.ts` → `getApiBaseUrl()`
- CORS: regex in `api/main.py` accetta localhost, LAN (192.168.x.x), Tailscale (100.x.x.x)

### Accesso remoto — Tailscale VPN
Chiara accede da **qualsiasi rete** (lavoro, 4G) tramite Tailscale (WireGuard P2P).
- PC gvera: `100.127.28.16` — Tailscale sempre attivo
- iPad Chiara: stesso account Tailscale
- Privacy: dati P2P crittografati, zero transito su server terzi

### Script di gestione (`tools/scripts/`)
```bash
bash tools/scripts/migrate-all.sh        # Alembic su ENTRAMBI i DB
bash tools/scripts/kill-port.sh 8000     # Kill pulito (tree-kill, no zombie)
bash tools/scripts/restart-backend.sh dev   # Kill + restart porta 8001
bash tools/scripts/restart-backend.sh prod  # Kill + restart porta 8000
```

### Regole blindate
1. **Migrazioni**: `bash tools/scripts/migrate-all.sh` — MAI `alembic upgrade head` da solo
2. **Kill backend**: `bash tools/scripts/kill-port.sh <porta>` — MAI `Ctrl+C` senza verificare
3. **crm.db sacro**: dati reali di Chiara. MAI toccare con seed/reset
4. **crm_dev.db libero**: dati di test (50 clienti). Seed/reset quando vuoi
5. **Frontend dev**: `npm run dev` → porta 3001 automatica, API a 8001 automatica
6. **Frontend prod**: `npm run build && npm run prod` → porta 3000, API a 8000

### Pitfall Windows: zombie uvicorn worker
Su Windows, `Ctrl+C` uccide il master uvicorn ma i worker figli (multiprocessing.spawn)
restano vivi con il socket aperto → servono codice vecchio. Soluzione: `kill-port.sh`
usa `taskkill /T /F` per uccidere l'intero albero di processi.

---

## Comandi

```bash
# ── Avvio rapido (copia-incolla) ──
# Dev:
DATABASE_URL=sqlite:///data/crm_dev.db uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
cd frontend && npm run dev                                # porta 3001, API → localhost:8001

# Prod:
uvicorn api.main:app --host 0.0.0.0 --port 8000          # crm.db (default)
cd frontend && npm run build && npm run prod              # porta 3000, API → 192.168.1.23:8000

# ── Script di gestione ──
bash tools/scripts/migrate-all.sh                         # Alembic su entrambi i DB
bash tools/scripts/kill-port.sh 8000                      # Kill pulito (tree-kill)
bash tools/scripts/restart-backend.sh dev                 # Kill + restart 8001
bash tools/scripts/restart-backend.sh prod                # Kill + restart 8000

# ── Build + Test ──
cd frontend && npx next build                             # OBBLIGATORIO prima di ogni commit
pytest tests/ -v                                          # 63 test

# Test E2E (richiede server avviato)
python tools/admin_scripts/test_crud_idor.py
python tools/admin_scripts/test_financial_idor.py
python tools/admin_scripts/test_agenda_idor.py
python tools/admin_scripts/test_ledger_dashboard.py

# Test Safety Engine (puro, no server — 10 profili clinici + edge cases)
python -m tools.admin_scripts.test_safety_engine

# ── Migrazioni ──
alembic revision -m "desc"                                # crea nuova migrazione
bash tools/scripts/migrate-all.sh                         # applica a ENTRAMBI i DB
# MAI usare `alembic upgrade head` da solo!

# ── Backup ──
# POST /api/backup/create     (richiede JWT)
# GET  /api/backup/export     (JSON dati trainer)

# ── Reset & Seed (FERMA il server API prima!) ──
python tools/admin_scripts/reset_production.py            # DB pulito con solo Chiara
python -m tools.admin_scripts.seed_dev                    # 50 clienti su crm_dev.db
# Credenziali prod: chiarabassani96@gmail.com / chiarabassani
# Credenziali dev:  chiarabassani96@gmail.com / Fitness2026!

# ── Database ──
sqlite3 data/crm.db ".tables"
sqlite3 data/crm_dev.db ".tables"
```

---

## Metriche Progetto

- **api/**: ~4,900 LOC Python — 17 modelli ORM, 10 router, 1 schema module
- **frontend/**: ~14,500 LOC TypeScript — ~70 componenti, 11 hook modules, 13 pagine
- **core/**: ~10,300 LOC Python — moduli AI (RAG, exercise archive) in attesa di API endpoints
- **tools/admin_scripts/**: ~2,800 LOC Python — 14 script (import, quality engine, taxonomy, seed, test)
- **DB**: 29 tabelle SQLite, FK enforced, multi-tenant via trainer_id
- **Esercizi**: 97 attivi (100% completi, 100% foto, tassonomia completa) + 962 archiviati (reinserimento graduale)
- **Test**: 63 pytest + 67 E2E
- **Sicurezza**: JWT auth, bcrypt, Deep Relational IDOR, 3-layer route protection
- **Cloud**: 0 dipendenze, 0 dati verso terzi

---

*Questo file e' la legge. Il codice che non la rispetta non viene mergiato.*
