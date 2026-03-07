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

### Visual Upgrade Sprint — Micro-Interazioni (test_react)

Upgrade puramente visivi senza nuove dipendenze pesanti. Zero framer-motion, tutto CSS + rAF.

- **AnimatedNumber** (`components/ui/animated-number.tsx`): KPI contano da 0 al mount, animano su cambio con ease-out-cubic via `requestAnimationFrame`. Format: `"currency"` | `"number"`. Usato in Dashboard (KPI operativi non-finanziari) e Cassa (SaldoHeroCard + 4 KPI mensili).
- **Skeleton shimmer** (`components/ui/skeleton.tsx`): rimpiazza `animate-pulse` con sweep CSS (`@keyframes shimmer`, `translateX` via `::after` pseudo-element). Skeleton anatomicamente accurati in 4 pagine (clienti/contratti/esercizi/schede).
- **Gradient mesh** (`globals.css`): `.bg-mesh-login` (animated gradient 4-stop, 400% background-size) sulla login. `.bg-mesh-app` (radial-gradient teal ellisse top-left) sul layout dashboard.
- **Confetti** (`lib/confetti.ts`): `celebrateRatePaid()` (burst singolo, 70 particelle) e `celebrateContractSaldato()` (cannoni L+R, 150ms offset). Lazy dynamic import di `canvas-confetti` (3KB). Triggerato da `usePayRate` in `onSuccess` quando `data.stato === "SALDATA"`.
- **Page Reveal** (`lib/page-reveal.ts`): `usePageReveal()` hook — fade-in + slide-up con stagger configurabile.
  `revealClass(delayMs)` + `revealStyle(delayMs)`. Rispetta `prefers-reduced-motion`. Usato in 6+ pagine
  (Dashboard, MyPortal, Clienti, Cassa, Allenamenti, Agenda).
- **Logo SVG** (`components/ui/logo.tsx`): `LogoIcon` — onda spirale + bar chart ascendente + foglia.
  `currentColor` per inheritance, scale 20px-200px+. Usato in Sidebar header (sfondo teal) e Login hero.
- **MuscleMapPanel status-aware**: vedi sezione Workout Template Builder.

### Guide Tour Interattivo — SpotlightTour 19 Passi

Tour guidato con overlay spotlight che naviga automaticamente tra le pagine.
Copre l'intero ciclo operativo: dashboard, clienti, contratti, agenda, cassa, esercizi,
schede allenamento, monitoraggio, impostazioni e ricerca rapida.

**Architettura**:
- **SpotlightTour** (`components/guide/SpotlightTour.tsx`): overlay leggero con box-shadow cutout (singolo DOM element).
  Portal in `document.body`. Zero librerie esterne. CSS `spotlight-cutout` in `globals.css`.
  Vive nel `layout.tsx` che non si smonta mai → stato sopravvive alla navigazione client-side.
- **data-guide attributes**: `data-guide="step-id"` su elementi target in 8 pagine. `getTargetRect()` cerca via `querySelector`.
- **Navigazione cross-page**: campo `navigateTo` su TourStep → `router.push()` via callback `onNavigate` dal layout.
  Navigazione centralizzata nell'useEffect di `tryFind` (singola fonte di verita').
- **Retry mechanism**: 20 tentativi × 200ms (4s) per step same-page, 25 × 200ms (5s) per cross-page.
  Auto-skip se target non trovato dopo retry esauriti.
- **Keyboard**: ArrowRight/Enter = avanti, ArrowLeft = indietro, Escape = chiudi.
- **Mobile-aware**: step con `desktopOnly: true` filtrati sotto 1024px (solo sidebar-search).
- **Auto-trigger**: prima visita dashboard → tour parte dopo 1.5s (`shouldShowOnboarding`).
- **Manual trigger**: `window.dispatchEvent(new Event("start-guide-tour"))` da `/guida`.

**Dati** (`lib/guide-tours.ts`, ~300 LOC, file puro dati zero React):
- `TOUR_SCOPRI_FITMANAGER`: 19 step cross-page (ID: `"scopri-fitmanager"`)
- `GUIDE_FAQ`: 7 domande frequenti con risposte actionable
- `KEYBOARD_SHORTCUTS`: 5 scorciatoie
- `FEATURE_CARDS`: 4 card feature discovery (assistente, smart programming, scudo clinico, export)

**Progresso** (`hooks/useGuideProgress.ts`): localStorage `fitmanager.guide.progress.v1`.
Traccia `completedTours` e `dismissedTours`. `shouldShowOnboarding` verifica se il tour principale e' stato completato o dismissato.

**Hub Guida** (`app/(dashboard)/guida/page.tsx`):
Hero card con CTA "Lancia tour" / "Rifai il tour", scorciatoie da tastiera, FAQ collapsibili, feature discovery cards.

File chiave: `lib/guide-tours.ts` (dati), `components/guide/SpotlightTour.tsx` (overlay),
`hooks/useGuideProgress.ts` (progresso), `app/(dashboard)/guida/page.tsx` (hub),
`app/(dashboard)/layout.tsx` (integrazione tour + navigazione).

### Command Palette (Ctrl+K) — Feature Distintiva

Elemento chiave di UX: ricerca fuzzy globale con 3 capacita' avanzate.

1. **Preview Panel**: pannello dati a destra (solo desktop) con info live dell'elemento selezionato
   (statistiche cliente, muscoli esercizio, KPI finanziari)
2. **Risposte KPI dirette**: digiti "entrate" e vedi il numero inline senza navigare
3. **Azioni Contestuali**: la palette sa dove sei (es. `/clienti/5`) e suggerisce azioni per quel cliente

Implementazione: `cmdk` v1.1.1 + shadcn Command. Custom Dialog (non CommandDialog) per split layout.
Dati lazy-loaded via React Query (`enabled: open`). Zero prop drilling — custom event per apertura da sidebar.

File: `frontend/src/components/layout/CommandPalette.tsx` (~1170 LOC).

### Assistant CRM Deterministico V0.5 — NLP nella Command Palette

> **Filosofia: PARSE + PREVIEW + CONFIRM.** Mai eseguire operazioni senza conferma esplicita.
> Parser deterministico (regex + fuzzy match), zero Ollama, zero latenza percepita.

Digitando `>` nella Command Palette si attiva l'**assistant mode**: testo in italiano naturale
viene parsato dal backend e trasformato in operazioni strutturate con preview prima della conferma.

**3 Intent Pilota:**
1. **agenda.create_event** — "Marco Rossi domani alle 18 PT"
2. **movement.create_manual** — "spesa affitto 800 euro bonifico"
3. **measurement.create** — "Marco peso 82 massa grassa 18"

**Architettura (two-phase flow):**
```
CommandPalette (prefisso ">", debounce 300ms)
  |  POST /assistant/parse   (read-only preview)
  |  POST /assistant/commit  (write su conferma utente)
  v
api/routers/assistant.py (feature flag ASSISTANT_V1_ENABLED)
  → orchestrator.py: normalize → classify → extract → resolve → build_payload → score
  → commit_dispatcher.py: chiama funzioni dominio direttamente (zero HTTP)
      → agenda.create_event()
      → movements.create_manual_movement()
      → measurements.create_measurement()
```

**Backend — 6 moduli parser** (`api/services/assistant_parser/`):
- **normalizer.py**: lowercase, accenti italiani, numeri IT→float (`1.200,50`→`1200.50`), abbreviazioni giorni
- **intent_classifier.py**: regex weighted triggers per 3 intent, score 0-1
- **entity_extractor.py**: 10 tipi entita' (date relative/assolute, orari, importi, nomi persona, metriche con catalog ID, categorie, metodi pagamento, tipi movimento)
- **entity_resolver.py**: fuzzy client matching con `difflib.SequenceMatcher` (stdlib). Soglie: `>=0.90` auto, `0.70-0.89` ambiguo, `<0.50` reject
- **confidence.py**: score composito 4 fattori (intent 0.35, entities 0.30, slots 0.20, validation 0.15)
- **orchestrator.py**: pipeline completa, 3 payload builder (event, movement, measurement)

**Commit Dispatcher**: chiama funzioni router **direttamente** (non via HTTP).
`Depends()` e' solo un default FastAPI — passando trainer/session esplicitamente, riusa
tutta la business logic (bouncer, IDOR, audit, atomic commit).

**Frontend** (`CommandPalette.tsx`):
- `assistantMode` come stato separato (non derivato da `>`). Digitando `>` si entra, Backspace su vuoto si esce
- Layout **full-width** in assistant mode (preview panel destro nascosto → tutta la larghezza)
- **Header teal** con indicatore stato + spinner loading + hint "← torna"
- **Discovery section** nella ricerca normale: gruppo "Assistente" con 3 esempi cliccabili
- **Suggestion chips** context-aware sotto l'input (adattati alla pagina cliente corrente)
- **AssistantResultCard**: card prominente con bordo colorato (verde/ambra/rosso per confidenza),
  icona intent, preview, entita' key/value, bottone CTA "Conferma ↵"
- **Enter-to-commit** via capture-phase keydown handler (bypassa cmdk)
- **Shimmer bar** durante il parsing (animate-pulse)
- Debounce 300ms → POST /assistant/parse
- Commit su Enter → POST /assistant/commit → toast + invalidation dinamica da backend + navigazione

**Invalidation**: `CommitResponse.invalidate` contiene React Query keys dal backend →
`useCommitAssistant` invalida dinamicamente (stesse chiavi degli hook dominio esistenti).

**Feature flag**: `ASSISTANT_V1_ENABLED=false` (default) → entrambi endpoint ritornano 404.

**Metric ID mapping** (hardcoded, allineato a catalog.db):
peso=1, massa_grassa=3, vita=9, fianchi=10, fc_riposo=11, sistolica=12, diastolica=13.

Riferimenti spec (Codex): `docs/upgrades/specs/UPG-2026-03-04-04-assistant-parser-v1-*.md` (6 file).

File chiave: `api/services/assistant_parser/` (6 moduli), `api/routers/assistant.py` (2 endpoint),
`api/schemas/assistant.py` (6 schema Pydantic), `frontend/src/hooks/useAssistant.ts` (2 hook),
`frontend/src/components/layout/CommandPalette.tsx` (assistant mode + preview).

### Dashboard Operativa — Reminder-First Board + Clinical Readiness

> **Filosofia: la dashboard e' un pannello di controllo, non una bacheca.**
> Layout reminder-first: azioni urgenti in primo piano, KPI ridotti all'essenziale.

**Layout 50/50 split** (desktop):
- **Sinistra**: TodoCard "post-it" con hero action (h-[480px] fisso)
- **Destra**: pannello unificato con orologio live + lista sessioni giorno scrollabile
- KPI ridotti a 2 essenziali: clienti attivi + appuntamenti oggi
- Alert Panel sotto con 4 categorie di warning proattivi (invariato)

**Todo Hero — Next-Best-Action** (deterministic state machine):
`buildTodoHeroState()` calcola la priorita' del momento e presenta CTA contestuale:
1. `"overdue"` — todo scaduti → rosso + "Completa prossimo"
2. `"today"` — todo oggi → ambra + "Completa prossimo"
3. `"critical_alerts"` — alert critici operativi → rosso + "Apri alert"
4. `"warning_alerts"` — alert warning → ambra + "Apri alert"
5. `"upcoming_sessions"` — sessioni imminenti → blu + "Apri agenda"
6. `"free"` — tutto ok → verde + "Aggiungi follow-up"

**Clinical Readiness Queue** (`GET /api/dashboard/clinical-readiness`):
Coda deterministica per onboarding/migrazione clienti. Ogni cliente riceve:
- `anamnesi_state`: "missing" | "legacy" | "structured"
- `readiness_score`: 0-100 (anamnesi 40pt + misurazioni 30pt + scheda 30pt)
- `priority`: "high" | "medium" | "low" (da `priority_score` deterministico)
- `next_action_code` + `next_action_label` + `next_action_href`: CTA actionable con deep-link
- `timeline_status`: "overdue" | "today" | "upcoming_7d" | "upcoming_14d" | "future" | "none"
- `next_due_date` + `days_to_due`: deadline per prossima azione

**Timeline computation**: gap immediati (anamnesi/baseline mancanti) → `overdue`.
Profili pronti: review periodiche (misurazioni 30gg, scheda 21gg, anamnesi 180gg).

**One-Click CTA Auto-Start**: deep-link flags consumati dal frontend:
- `?startWizard=1` → auto-apre AnamnesiWizard su `/clienti/[id]/anamnesi`
- `?startScheda=1` → auto-apre TemplateSelector su `/clienti/[id]?tab=schede`
- Pattern: `useSearchParams().get("flag")` + `requestAnimationFrame` + consume URL

**Hook**: `useClinicalReadiness()` — query key `["dashboard", "clinical-readiness"]`, refetch 60s.

File chiave: `api/routers/dashboard.py` (~980 LOC, 8 endpoint), `api/schemas/financial.py` (3 schema readiness),
`frontend/src/hooks/useDashboard.ts` (6 hook), `frontend/src/app/(dashboard)/page.tsx` (~1760 LOC).

### MyPortal — Tracking Board Clinico

Pagina dedicata (`/clienti/myportal`) per monitorare progressione readiness clienti.

**Features**:
- **4 KPI card**: clienti totali, da completare, pronti, alta priorita'
- **Filtro**: "Da completare" | "Tutti" | "Pronti" + ricerca fuzzy accent-insensitive
- **Timeline Scadenze**: griglia deadline con badge status colorati (overdue/today/7d/14d/future)
- **Dual layout**: tabella desktop (md+) con 8 colonne, card stack mobile
- **Badge stati**: AnamnesiBadge (structured=verde, legacy=ambra, missing=rosso), CompletionBadge (completa/manca)
- **CTA dirette**: ogni riga ha bottone azione che naviga con flag auto-start

**Data source**: `useClinicalReadiness()` (stesso hook della dashboard, zero API aggiuntive).

**Sidebar**: voce "MyPortal" (icona HeartPulse) nella sezione Clienti.

File chiave: `frontend/src/app/(dashboard)/clienti/myportal/page.tsx` (~490 LOC).

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
- **Export Schede (doppio formato)**:
  - **Anteprima**: `window.print()` sulla `WorkoutPreview` esistente (formato operativo rapido).
  - **Scarica Clinico**: `downloadWorkoutClinicalHtml()` genera file HTML locale ottimizzato PDF (copertina + safety opzionale + 1 pagina per sessione), senza dipendere da popup browser.
  - **Foto esercizi embedded**: start/end caricate da `/media/exercises/{id}/...` e incorporate in base64 per resa stabile offline/print.
  - **Branding cliente**: logo upload/change/remove da `ExportButtons`, persistito per trainer in localStorage (`fitmanager.workout.logo.{trainerId}`), visibile in preview e cover clinica.
  - **Print hardening**: `@media print` con `print-color-adjust`, regole A4 di page-break, split controllato blocchi/tabelle e densita media compattata per ridurre pagine/inchiostro.
- **Blocchi Strutturati** (circuit/superset/tabata/amrap/emom/for_time): layout format-specific in builder, preview e export. `BLOCK_EXERCISE_CONFIG` (esportata da `SortableExerciseRow.tsx`) governa griglia, colonne Rip/Kg, notazione (A1/A2 superset, 1./2. altri, nessuna tabata). `BlockPreview` in preview con `border-l-4` + sfondo header colorato per tipo (`BLOCK_TYPE_PREVIEW_CONFIG`). Export: `addBlockExerciseCard()` con header colorato (`BLOCK_TYPE_HEADER_COLORS` scuri, testo bianco) + Rip ±Kg condizionali (tabata = solo nome). No Serie/Riposo per-esercizio nei blocchi (sono parametri del blocco). Notazione A1/A2 per superset in export (viola scuro).
- **Client linkage**: assegnazione/riassegnazione cliente inline (Select + `"__none__"` sentinel), filtro cliente nella lista, tab "Schede" nel profilo cliente, cross-link bidirezionale
- **TemplateSelector**: dialog con selezione cliente integrata (`selectedClientId` state, pre-compilato da contesto)
- **269 esercizi attivi** (87 compound, 69 isolation, 41 stretching, 31 bodyweight, 17 mobilita, 14 avviamento, 10 cardio) + 790 archiviati
- Tassonomia completa: muscoli FK (3,370 righe), articolazioni FK (858), condizioni mediche FK (1,280), relazioni (460)
- Categorie: `compound`, `isolation`, `bodyweight`, `cardio`, `stretching`, `mobilita`, `avviamento`
- Pattern: 9 forza (`squat`, `hinge`, `push_h/v`, `pull_h/v`, `core`, `rotation`, `carry`) + 3 complementari (`warmup`, `stretch`, `mobility`)

- **Exercise Detail Panel** (`ExerciseDetailPanel.tsx`): pannello riassuntivo riusabile (muscoli, classificazione, setup, note sicurezza, relazioni con quick-swap "Sostituisci", deep-link con ritorno). Usato sia in SortableExerciseRow che in ExerciseSelector
- **Deep-Link Esercizio**: `/esercizi/{id}?from=scheda-{schedaId}` → banner "Torna alla scheda" + back button condizionale. Navigazione bidirezionale builder↔dettaglio esercizio

Riferimenti UPG log (workout export):
- `UPG-2026-03-04-02` (export clinico scaricabile con logo + foto embedded)
- `UPG-2026-03-04-03` (impaginazione stampa + compattazione densita media)

**Carico & Analytics** (Fase 1+2):
- `carico_kg` opzionale su ogni esercizio (Float nullable, 0-500 kg)
- Volume sessione: `Σ(serie × parseAvgReps(rip) × carico_kg)` — KPI in SessionCard header
- Volume totale scheda: badge nell'header builder + preview
- **% 1RM**: badge `78% 1RM` sotto campo kg per esercizi squat/panca/stacco
  - Mapping: `PATTERN_TO_1RM` in `derived-metrics.ts` (squat→id20, push_h→id21, hinge→id22)
  - Fetch: `useLatestMeasurement(clientId)` lazy nel builder → `oneRMByPattern` useMemo
  - Visibile solo se: cliente assegnato + misurazione 1RM presente + carico compilato
- `parseAvgReps()`: exported da SessionCard, parsa "8-12"→10, "5"→5, "30s"→0

- **MuscleMapPanel** (`components/workouts/MuscleMapPanel.tsx`): pannello collassabile con silhouette anatomica live. Due modalità:
  - **Status mode** (quando `livello` passato): usa `computeSmartAnalysis` internamente → colora muscoli per stato NSCA con 3 colori allineati a SmartAnalysisPanel: emerald=ottimale (intensity 1), amber=eccesso (intensity 2), red=deficit (intensity 3). Body map = rappresentazione spaziale delle barre di copertura.
  - **Fallback teal**: aggrega `muscoli_primari`/`muscoli_secondari` dagli esercizi senza info di volume.
  - Legenda a 4 voci in status mode: Ottimale / Eccesso / Deficit / Non allenato. Badge e bordo seguono stessa logica cromatica di SmartAnalysisPanel.
  - `SMART_TO_SLUG_MAP` in `lib/muscle-map-utils.ts`: ponte IT→EN tra nomi italiani di `computeSmartAnalysis` e chiavi inglesi di `MUSCLE_SLUG_MAP` (es. `petto→chest`, `dorsali→back`).
  - `MuscleMap.tsx` esteso: prop `muscoliTerziari?: string[]` (intensity 3), `colors?: string[]` (da tupla fissa a array generico per supportare 3+ intensità).

File chiave: `lib/workout-templates.ts` (template + `getSectionForCategory` + `getSmartDefaults`), `lib/derived-metrics.ts` (PATTERN_TO_1RM), `lib/muscle-map-utils.ts` (`MUSCLE_SLUG_MAP`, `SMART_TO_SLUG_MAP`, `buildBodyData`), `lib/export-workout.ts` (export Excel legacy), `lib/export-workout-pdf.ts` (export clinico HTML->PDF con foto embedded + print CSS), `components/workouts/ExportButtons.tsx` (switch formato + logo), `components/workouts/SessionCard.tsx` (3 sezioni DnD, volume, overflow menu), `components/workouts/BlockCard.tsx` (blocchi strutturati, usa `BLOCK_EXERCISE_CONFIG`), `components/workouts/SortableExerciseRow.tsx` (grid 8-col, `BLOCK_EXERCISE_CONFIG` export, % 1RM badge, espansione unificata), `components/workouts/WorkoutPreview.tsx` (`BlockPreview` con `BLOCK_TYPE_PREVIEW_CONFIG` + logo preview), `components/workouts/ExerciseDetailPanel.tsx` (dettaglio inline), `components/workouts/MuscleMapPanel.tsx` (silhouette 3-colori status-aware).

### Workout Monitoring — Pagina `/allenamenti`

Pagina top-level per monitorare aderenza ai programmi di allenamento. Ogni piano con cliente
assegnato puo' essere "attivato" impostando date inizio/fine, poi tracciato su griglia
settimane x sessioni con compliance %.

**Backend**: `data_inizio`/`data_fine` su `WorkoutPlan` (Optional[date], migrazione `9d7720a02d95`).
`WorkoutLog` (allenamenti_eseguiti) — modello + router + schema per CRUD esecuzioni.
Conversione stringa→date nel router prima di `setattr` (pitfall documentato).

**Frontend**:
- **Status derivato client-side**: `getProgramStatus(plan)` → `da_attivare` | `attivo` | `completato`
  (nessun campo `stato` nel DB — calcolato da date)
- **Utility** `lib/workout-monitoring.ts`: `computeWeeks()`, `matchLogsToGrid()`, `computeCompliance()`,
  `STATUS_LABELS`, `STATUS_COLORS`, helper data/formattazione
- **Pagina** `app/(dashboard)/allenamenti/page.tsx`:
  - Filtri: Select cliente + chip status (Tutti/Attivi/Da attivare/Completati)
  - **ProgramCard**: header con nome, cliente linkato, badge obiettivo/livello/status, date range
  - **ComplianceGrid**: `<Table>` settimane × sessioni. Celle interattive:
    - Log presente: sfondo verde + check + data. Click → Popover dettaglio + "Rimuovi"
    - Vuota (settimana passata/corrente): bordo tratteggiato + click → Popover con DatePicker + nota + "Registra"
    - Vuota (settimana futura): grigia, non clickable
  - **ComplianceBar**: progress bar colorata (verde >=80%, ambra >=50%, rossa <50%)
  - **ActivateDialog**: Dialog con 2 DatePicker (inizio + fine), validazione fine > inizio
  - URL search param: `?idCliente={id}` per deep-linking dal profilo cliente
- **Sidebar**: voce "Monitoraggio" (icona Activity) nella sezione Allenamento
- **CommandPalette**: "Schede Allenamento" + "Monitoraggio Allenamenti"
- **SchedeTab profilo cliente**: colonna "Stato" con badge colorato + link "Vedi monitoraggio →"

**Data flow**:
```
useWorkouts() → piani con id_cliente (filtro client-side)
useWorkoutLogs(planId) → log per piano (1 query per ProgramCard visibile)
useCreateWorkoutLog(clientId) / useDeleteWorkoutLog(clientId) → CRUD celle griglia
useUpdateWorkout() → attivazione/modifica date
```

File chiave: `lib/workout-monitoring.ts` (utility), `app/(dashboard)/allenamenti/page.tsx` (pagina),
`api/models/workout_log.py` (modello), `api/routers/workout_logs.py` (4 endpoint).

### Training Science Engine — Single Source of Truth Scientifica

> **Filosofia: ogni numero ha una fonte bibliografica.** Zero inventato, zero approssimato.
> Motore deterministico backend che genera piani di allenamento volume-driven
> e li analizza su 4 dimensioni scientifiche.
>
> **Questo e' il CUORE SCIENTIFICO dell'intero prodotto.** Tutti i dati scientifici
> (costanti, coefficienti, matrici, formule) vivono QUI e SOLO QUI.
> Il frontend consuma via API — mai duplica. Vedi sezione SSoT.

**Architettura a 10 moduli** (`api/services/training_science/`, ~2000 LOC):

| Fase | Modulo | Responsabilita' |
|------|--------|----------------|
| Phase 1 | `types.py` | Enum e modelli Pydantic (vocabolario del dominio) |
| Phase 1 | `principles.py` | Parametri di carico per obiettivo (NSCA/ACSM/Schoenfeld) |
| Phase 1 | `muscle_contribution.py` | Matrice contribuzione EMG 18x15 + volume ipertrofico pesato |
| Phase 1 | `volume_model.py` | MEV/MAV/MRV per muscolo x livello + classificazione |
| Phase 1 | `balance_ratios.py` | Rapporti biomeccanici push:pull, quad:ham, ant:post |
| Phase 2 | `split_logic.py` | Frequenza -> split ottimale + struttura sessioni |
| Phase 2 | `session_order.py` | Ordinamento fisiologico (SNC-demanding first) |
| Phase 2 | `plan_builder.py` | Generatore volume-driven a 4 fasi con feedback loop |
| Phase 2 | `plan_analyzer.py` | Analisi 4D (volume, balance, frequenza, recupero) |
| Phase 3 | `periodization.py` | Mesociclo (progressione volume lineare + deload) |

**Concetti chiave**:
- **Dual volume computation**: `compute_effective_sets()` (meccanico, per balance/recovery) vs
  `compute_hypertrophy_sets()` (pesato, per MEV/MAV/MRV — soglia EMG 40% MVC, Schoenfeld 2017)
- **Volume model**: MEV (sotto = zero stimolo), MAV (range ottimale), MRV (oltre = overtraining).
  15 muscoli x 3 livelli = 45 combinazioni. Scalati per obiettivo via `fattore_volume`
- **Plan builder 4 fasi**: (1) compound base, (2) boost compound per deficit, (3) compensazione isolation,
  (4) feedback loop se muscoli critici ancora sotto MEV
- **Periodizzazione a blocchi**: accumulazione -> intensificazione -> overreaching -> deload.
  Durata: principiante 4, intermedio 5, avanzato 6 settimane. Deload a 50% (Helms 2019)
- **Frequency clamp**: principiante max 3x, intermedio max 5x, avanzato max 6x (NSCA 2016)

**API REST** (5 endpoint in `api/routers/training_science.py`, prefix `/training-science`):

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/plan` | POST | Genera piano settimanale volume-driven |
| `/analyze` | POST | Analisi 4D (volume, balance, frequenza, recupero) |
| `/mesocycle` | POST | Genera mesociclo con periodizzazione a blocchi |
| `/parameters/{obiettivo}` | GET | Parametri di carico NSCA/ACSM |
| `/volume-targets` | GET | Target MEV/MAV/MRV per livello x obiettivo |

Tutti computazionali puri (zero DB). JWT auth. Schema input inline nel router (3 Pydantic model).

**Fonti**: NSCA 2016, ACSM 2009, Schoenfeld 2010/2017/2021, Krieger 2010, Israetel RP 2020,
Bompa 2019, Helms 2019, Contreras 2010, Alentorn-Geli 2009, Sahrmann 2002, Zourdos 2016.

Spec dettagliata: `docs/upgrades/specs/TRAINING-SCIENCE-SPEC.md`
Roadmap: `docs/upgrades/specs/KINESCORE-ROADMAP.md`

File chiave: `api/services/training_science/` (10 moduli), `api/routers/training_science.py` (5 endpoint).

### Smart Programming — Layer Frontend (Consumer del Backend)

> **Filosofia: INFORMARE, mai LIMITARE.** Il frontend consuma il Training Science Engine
> backend via API REST e presenta i risultati. L'unica logica client-side e' il
> **scoring 14D** per la selezione esercizi live nel builder.

**Architettura SSoT** (Single Source of Truth):

```
Training Science Engine (backend, fonte unica)
  POST /training-science/plan      → genera piano volume-driven
  POST /training-science/analyze   → analisi 4D (volume, balance, freq, recovery)
  POST /training-science/mesocycle → periodizzazione a blocchi
  GET  /training-science/parameters/{obj} → parametri carico NSCA/ACSM
  GET  /training-science/volume-targets   → target MEV/MAV/MRV per livello
       |
       | React Query (useTrainingScience hooks)
       v
Smart Programming (frontend, UI + scoring)
  lib/smart-programming/
    types.ts       — interfacce (mirror backend)
    scorers.ts     — 14 scorer composabili per selezione esercizi
    helpers.ts     — profilo client, normalizzazione, utility
    analysis.ts    — orchestratore che chiama API backend
    index.ts       — re-export pubblico
```

**Cosa vive nel frontend** (logica UI-only):
- **14 Scorer composabili** per selezione esercizi live nel builder:
  safety (0.15), muscle_match (0.14), pattern_match (0.13), difficulty (0.10),
  goal_alignment (0.08), slot_fit (0.09), strength_level (0.06), recovery_fit (0.06),
  equipment_variety (0.04), uniqueness (0.05), plane_variety (0.03),
  chain_variety (0.03), bilateral_balance (0.02), contraction_variety (0.02)
- **`scoreExercisesForSlot()`**: orchestra tutti i scorer, ritorna `ExerciseScore[]` ordinati
- **`assessFitnessLevel()`**: combina strength ratios NSCA + livello attivita' anamnesi
- **`buildClientProfile()`**: aggrega dati client da hook eterogenei
- **`computeSafetyBreakdown()`**: conteggio avoid/modify/caution per display actionable

**Cosa vive nel backend** (dati scientifici — vedi sezione Training Science Engine):
- Generazione piano (4 fasi volume-driven + feedback loop)
- Analisi 4D (volume per muscolo, balance ratios, frequenza, recupero)
- Matrice EMG 18×15, volume MEV/MAV/MRV, parametri carico
- Split logic, session ordering, periodizzazione

**Hook** (`hooks/useSmartProgramming.ts`, ~60 LOC):
- Aggrega 5 hook: useClient + useExerciseSafetyMap + useLatestMeasurement + useClientMeasurements + useClientGoals
- Calcola: strength ratios (NSCA), simmetria bilaterale, fitness level
- Zero duplicazione di costanti scientifiche

**Hook** (`hooks/useTrainingScience.ts`):
- `useGeneratePlan(freq, obiettivo, livello)` → `POST /training-science/plan`
- `useAnalyzePlan(piano)` → `POST /training-science/analyze` (debounce 300ms)
- `useVolumeTargets(livello, obiettivo)` → `GET /training-science/volume-targets`
- `useTrainingParameters(obiettivo)` → `GET /training-science/parameters/{obj}`

**UI**:
- **Card "Scheda Smart"** in TemplateSelector — configurazione inline (sessioni/sett, obiettivo, livello).
  Genera piano via `POST /training-science/plan`, riempie slot via scoring 14D client-side.
- **SmartAnalysisPanel** nel builder — 5 sezioni con dati da `POST /training-science/analyze`:
  1. Copertura Muscolare — barre colorate per gruppo vs target MEV/MAV/MRV
  2. Volume Totale — set/settimana con dual volume (effective vs hypertrophy)
  3. Varieta Biomeccanica — distribuzione piani/catene/contrazioni
  4. Conflitti Recupero — overlap muscolare tra sessioni consecutive
  5. Compatibilita Clinica — conteggio avoid/modify/caution (no % fuorviante)

File chiave: `lib/smart-programming/` (5 moduli, <300 LOC ciascuno),
`hooks/useSmartProgramming.ts` (profilo client), `hooks/useTrainingScience.ts` (API backend),
`components/workouts/SmartAnalysisPanel.tsx` (pannello), `components/workouts/TemplateSelector.tsx` (card Smart).

### Exercise Quality Engine — Pipeline Dati

> **Filosofia: l'allenamento e' un sottoramo della medicina.** Il database esercizi e' il nucleo del prodotto.
> Contenuti imprecisi possono causare infortuni. Zero approssimazione.

**Strategia "Database 269"**: 269 esercizi attivi (`in_subset=True`): 87 compound, 69 isolation, 41 stretching,
31 bodyweight, 17 mobilita, 14 avviamento, 10 cardio. Avviamento/mobilita photo-optional (semplici bodyweight).
790 esercizi archiviati (`in_subset=False`) reinseribili via `activate_batch.py`.

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
| `seed_qa_clinical.py` | 30 clienti QA × 6 lotti clinici per verifica safety mapping | Zero Ollama |
| `verify_qa_clinical.py` | 150 check clinici: severita' attesa per condizione × pattern | Zero Ollama |

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
| `condizioni_mediche` | Catalogo | 47 | Condizioni rilevanti (5 categorie, body_tags JSON) |
| `esercizi_muscoli` | Junction M:N | ~1271 | Esercizio↔muscolo con ruolo (primary/secondary/stabilizer) + attivazione % |
| `esercizi_articolazioni` | Junction M:N | ~299 | Esercizio↔articolazione con ruolo (agonist/stabilizer) + ROM gradi |
| `esercizi_condizioni` | Junction M:N | ~3600 | Esercizio↔condizione con severita' (avoid/modify/caution) + nota |

Colonne su `esercizi`: `in_subset` (flag sviluppo), `catena_cinetica` (open/closed),
`piano_movimento` (sagittal/frontal/transverse/multi), `tipo_contrazione` (concentric/eccentric/isometric/dynamic).

**Subset attivo**: 97 esercizi (`in_subset=1`) selezionati algoritmicamente per copertura
su 11 pattern × 14 gruppi muscolari × 8 attrezzature × 3 difficolta' × 6 categorie, tutti con foto.
L'API filtra `Exercise.in_subset == True` — rimuovere per riattivare catalogo completo.

**Modelli API**: `muscle.py` (Muscle + ExerciseMuscle), `joint.py` (Joint + ExerciseJoint),
`medical_condition.py` (MedicalCondition + ExerciseCondition).

**Script**: `seed_taxonomy.py` (cataloghi hardcoded), `populate_taxonomy.py` (mapping deterministico),
`populate_conditions.py` (mapping condizioni mediche, 80 pattern rules).

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
- 47 condizioni mediche (30 specifiche + 9 generiche + 8 aggiuntive) — 0 condizioni morte (tutte raggiungibili)
- `match_keywords()` accent-insensitive: normalizza `a'` == `a` == Unicode accent (italiano)
- `obiettivi_specifici` ESCLUSO dal keyword scanning (previene falsi positivi da goal text)
- Endpoint: `GET /exercises/safety-map?client_id=N` (JWT auth + trainer bouncer)
- Response: `SafetyMapResponse` con `entries: dict[exercise_id, ExerciseSafetyEntry]`, `condition_names`, `condition_count`
- Severita' per esercizio: worst-case aggregation (`_SEVERITY_ORDER`: **avoid > modify > caution**)
  - "modify" prevale su "caution" perche' richiede azione specifica (adattare ROM, grip, carico)
  - "caution" e' solo consapevolezza generica
- `SafetyConditionDetail` include `categoria` (orthopedic, cardiovascular, metabolic, neurological, respiratory, special)

**Pipeline Mapping** (`tools/admin_scripts/populate_conditions.py`):
- 80 `PATTERN_CONDITION_RULES`: regole pattern_movimento × condizione → severita' clinica specifica
  - Organizzate per zona: spalla (14), ginocchio (5), anca (4), colonna (11), caviglia (4),
    polso/gomito (7), cardiovascolare (4), metabolico (5), neurologico (6), respiratorio (2),
    reumatologico (3), special (15 — gravidanza, diastasi, fibromialgia, ipotiroidismo, diabete T1)
- **Override logic**: pattern rules sovrascrivono keyword severity, MAI degradano da avoid
- ~3,600 mapping totali: avoid ~12%, modify ~45%, caution ~43%

**QA Clinica** (`tools/admin_scripts/`):
- `seed_qa_clinical.py`: 30 clienti × 6 lotti clinici (ortopedico, cardio, metabolico, neuro, combo, edge)
- `verify_qa_clinical.py`: 150 check clinici (0 FAIL, 0 WARN atteso)

**Frontend** — 4 livelli di visualizzazione (dal macro al micro):

1. **Safety Overview Panel** (`schede/[id]/page.tsx`): Card collapsibile con KPI (condizioni/evitare/adattare/cautela),
   badge condizioni, e dettaglio espanso raggruppato per categoria. Sostituisce il vecchio banner ambra.
2. **Session Pills** (`SessionCard.tsx`): contatori avoid/modify/caution nel CardHeader di ogni sessione.
3. **Exercise Popover** (`SortableExerciseRow.tsx`): click su icona safety → Popover ricco (w-72) con
   condizioni dettagliate (severita + nome + nota) + **alternative sicure con "Sostituisci"** (quick-swap).
4. **Selector Detail** (`ExerciseSelector.tsx`): badge safety cliccabile → pannello espandibile inline
   con dettaglio condizioni per ogni esercizio nel dialog di selezione.
5. **Exercise Detail Panel** (inline nel builder + selector): icona Info → pannello riassuntivo con
   muscoli, classificazione, setup, note sicurezza, relazioni actionable (progressioni/regressioni con "Sostituisci").
6. **RiskBodyMap** (`components/workouts/RiskBodyMap.tsx`): silhouette anatomica colorata per severity
   (avoid→rosso, modify→blu, caution→ambra). `_SEV_RANK`: avoid(3) > modify(2) > caution(1).

**Hook**: `useExerciseSafetyMap(clientId)` in `hooks/useWorkouts.ts` — React Query con `enabled: !!clientId`.

File chiave: `api/services/safety_engine.py` (engine), `api/services/condition_rules.py` (regole),
`tools/admin_scripts/populate_conditions.py` (pipeline mapping con 80 pattern rules),
`components/workouts/SortableExerciseRow.tsx` (SafetyPopover + Info panel), `components/workouts/ExerciseDetailPanel.tsx` (dettaglio inline riusabile),
`components/workouts/ExerciseSelector.tsx` (selettore con dettaglio), `components/workouts/RiskBodyMap.tsx` (body map severity-aware),
`schede/[id]/page.tsx` (Overview Panel + quick-replace handler).

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

**Frontend**: `ClinicalAnalysisPanel.tsx` (~510 LOC) nella pagina Progressi (`/clienti/[id]/progressi`) — 5 sezioni collassabili
con bordo severity-colorato + badge. Riceve `measurements`, `sesso`, `dataNascita`, `goals`.

**Integrazione**: `MeasurementChart` mostra `<ReferenceArea>` bande normative.
`GoalFormDialog` mostra hint range sano sotto target. `GoalsSummary` propaga sesso/dataNascita.

### Saldo Contabile Cumulativo — Running Balance

> **Filosofia: Computed on Read.** Nessun campo saldo nel DB — calcolato a runtime.
> Formula: `saldo = saldo_iniziale_cassa + SUM(CASE tipo WHEN 'ENTRATA' THEN importo ELSE -importo END)`.

**Backend** (`api/routers/movements.py`):
- `_signed_importo`: case expression module-level (ENTRATA → +importo, USCITA → -importo)
- `_compute_saldo(session, trainer)`: saldo cassa attuale (usato da balance, dashboard, forecast)
- `_compute_saldo_before(session, trainer, before_date)`: saldo cumulativo fino a una data
- `GET /movements/balance` → `BalanceResponse` (saldo_attuale, storico entrate/uscite)
- `GET /movements/saldo-iniziale` + `PUT /movements/saldo-iniziale` → configurazione trainer
- `GET /movements/stats` += `saldo_inizio_mese`, `saldo_fine_mese`, `chart_data[].saldo`
- `GET /movements/stats` netta gli storni di spese fisse (`STORNO_SPESA_FISSA`) nei KPI e nel grafico giornaliero
- `GET /movements` += `saldo_fine_periodo` (per running balance frontend)
- `GET /movements/forecast` → saldo_iniziale ora usa `_compute_saldo()` (saldo reale)
- `POST /recurring-expenses/{id}/close` idempotente/rettificabile: supporta cutoff retroattivo su spesa già disattivata (`storni_creati`, `storni_rimossi`)
- `DashboardSummary` += `saldo_attuale`

**Modello Trainer** (`api/models/trainer.py`):
- `saldo_iniziale_cassa: float = Field(default=0.0)` — configurabile da Impostazioni
- `data_saldo_iniziale: Optional[date] = None` — se presente, filtra movimenti >= questa data

**Frontend**:
- `useCashBalance()` — `GET /movements/balance`, queryKey `["cash-balance"]`
- `useSaldoIniziale()` + `useUpdateSaldoIniziale()` — configurazione saldo iniziale
- `["cash-balance"]` invalidato da TUTTE le mutation che modificano movimenti (useMovements, useRates, useContracts)
- **SaldoHeroCard** (cassa/page.tsx): card teal full-width con saldo attuale + 3 sub-KPI mese
- **ComposedChart** (cassa/page.tsx): `BarChart` → `ComposedChart` con `Line` teal per saldo (dual Y-axis)
- **Running Balance** (MovementsTable.tsx): colonna "Saldo" (`hidden lg:table-cell`), balance progressivo dal `saldoFinePeriodo`
- **Dashboard (privacy-first)**: overview operativa senza importi economici; i KPI finanziari restano nella pagina Cassa
- **Impostazioni**: sezione "Saldo Iniziale di Cassa" (importo + data + salva)

File chiave: `api/routers/movements.py` (_compute_saldo, _compute_saldo_before, balance/saldo-iniziale endpoints),
`frontend/src/hooks/useMovements.ts` (useCashBalance, useSaldoIniziale, useUpdateSaldoIniziale),
`frontend/src/app/(dashboard)/cassa/page.tsx` (SaldoHeroCard, ComposedChart),
`frontend/src/components/movements/MovementsTable.tsx` (running balance column).

### Registro Modifiche Cassa — Audit Consultabile

> **Filosofia: ledger e audit sono complementari.**
> Il libro mastro mostra i movimenti economici, il registro audit mostra chi/come/perche sono cambiati.

**Backend** (`api/routers/movements.py`):
- `GET /movements/audit-log`: timeline audit paginata con filtri `data_da`, `data_a`, `action`, `entity_type`, `flow`.
- Item arricchiti con `before/after`, `reason`, `correlation_id`, `flow_hint`, `link_href`, `link_label`.
- Per `entity_type="movement"` il link include `focus_movement` e, se disponibile, range `da/a` sul giorno del movimento.

**Frontend**:
- `CashAuditSheet.tsx`: sheet consultabile con filtri combinabili (periodo, flusso, azione, entita), paginazione incrementale, detail diff.
- `cassa/page.tsx`: callback di navigazione interna per deep-link `/cassa?...` (stessa route) che sincronizza `tab`, filtri ledger e `focus_movement`.
- `MovementsTable.tsx`: scroll + highlight sulla riga target (`focusMovementId`) con consumo focus dopo animazione.

**Regola critica**:
- I link cross-page (`/contratti/...`) possono usare navigazione standard.
- I link intra-page (`/cassa?...`) devono passare da gestione stato esplicita, altrimenti i parametri URL non garantiscono allineamento UI.

Riferimenti UPG log:
- `UPG-2026-03-03-09` (registro audit consultabile)
- `UPG-2026-03-03-10` (deep-link audit same-route affidabile)

### Navigation UX — Filtri + Scroll + Cross-Link

> **Filosofia: Sidebar = fresh start, Back = ripristina.**
> sessionStorage e' la fonte di verita'. L'URL e' solo feedback visivo.
> La Sidebar cancella lo stato salvato onClick → pagina parte da zero.
> Il browser back NON passa dalla Sidebar → stato intatto → ripristinato.

**Architettura** — `lib/url-state.ts` (5 utility):
- `saveFilters(pageKey, state)` → scrive in sessionStorage
- `loadFilters(pageKey)` → legge da sessionStorage (null se vuoto)
- `clearPageState(href)` → cancella `filters:` + `scroll:` per la pagina (chiamato da Sidebar onClick)
- `getUrlParams()` → legge da `window.location.search` (fallback deep-link)
- `syncUrlParams(pathname, params)` → scrive URL con `replaceState` (feedback visivo)

**Sidebar** (`Sidebar.tsx`): ogni `NavItem` chiama `clearPageState(item.href)` onClick prima della navigazione.
Questo cancella filtri e scroll salvati → la pagina target parte da zero (default).

**Pattern per ogni pagina con filtri** (6 pagine):
```typescript
// 1. INIT: sessionStorage → URL → default
// Sidebar ha cancellato sessionStorage → loadFilters ritorna null → default
// Back-nav: sessionStorage intatto → loadFilters ritorna valori salvati → ripristinato
const [filter, setFilter] = useState(() => {
  const saved = loadFilters("pageKey");
  if (saved?.field) return saved.field as Type;
  const param = getUrlParams().get("field");
  if (param) return parseParam(param);
  return defaultValue;
});

// 2. WRITE: ogni cambio → sessionStorage + URL
useEffect(() => {
  saveFilters("pageKey", { field: filter !== default ? filter : null });
  const params = new URLSearchParams();
  if (filter !== default) params.set("field", String(filter));
  syncUrlParams(window.location.pathname, params);
}, [filter]);
```

**Pagine**: esercizi (8 filtri), clienti (2), contratti (2), schede (3), cassa (3), allenamenti (2).

**Scroll Restoration** (`layout.tsx`) — 2 hook + constraint CSS:
- **CSS**: `h-screen` sul wrapper esterno → `<main>` e' il vero scroll container (`overflow-y-auto`)
- **Hook 1**: Scroll event listener (debounced rAF) → salva `scroll:{pathname}` in sessionStorage
- **Hook 2**: Pathname change → se `scroll:{pathname}` presente → restore con retry [0-2000ms];
  se assente (cancellato da Sidebar o prima visita) → `scrollTop = 0`
- **Strict Mode guard**: `prevPathnameRef` impedisce double-invocation da React Strict Mode

**Cross-link contestuali**: `?from=clienti-{id}` su contratti/[id] e schede/[id] → banner "Torna al profilo".
`?from=dashboard` su contratti/[id] → banner "Torna alla dashboard". Back button condizionale.

**Deep-link params**: `?newEvent=1&clientId=X` (agenda), `?new=1` (clienti/contratti), `?new=1&cliente=X` (contratti).
Consumati al mount, URL pulito con `replaceState`.

**Tab persistence**: `clienti/[id]` persiste tab attiva via `router.replace(url, { scroll: false })`.

File chiave: `lib/url-state.ts` (utility), `layout.tsx` (scroll restoration),
`components/layout/Sidebar.tsx` (clearPageState onClick),
tutte le 6 pagine filtri (esercizi, clienti, contratti, schede, cassa, allenamenti).

---

## Architettura

```
frontend/          Next.js 16 + React 19 + TypeScript
  src/hooks/       React Query (server state) — 17 hook modules
  src/components/  shadcn/ui + componenti dominio — ~80 componenti
  src/types/       Interfacce TypeScript (mirror Pydantic)
       |
       | REST API (JSON over HTTP, JWT auth)
       v
api/               FastAPI + SQLModel ORM — Dual Engine
  models/          19 modelli ORM (SQLAlchemy table=True)
  routers/         16 router con Bouncer Pattern + Deep IDOR
  schemas/         Pydantic v2 (input/output validation)
  services/        Safety Engine, Goal Engine, Training Science Engine (10 moduli)
       |
       v
SQLite (Dual-DB)
  data/crm.db      Business DB — 22 tabelle dati trainer (clienti, contratti, workout...)
  data/catalog.db  Catalog DB — 7 tabelle tassonomia scientifica (muscoli, articolazioni, condizioni, metriche)
       |
core/              Moduli AI (dormant, non esposti via API — prossima fase)
  exercise_archive, knowledge_chain, card_parser, ...
```

### Dual-Database Architecture

> **Filosofia: dati business (sensibili) e catalogo scientifico (reference) separati.**
> Il trainer backuppa/ripristina solo i SUOI dati. Il catalogo e' shippato pre-costruito.

| Database | Engine | Tabelle | Contenuto | Backup |
|----------|--------|---------|-----------|--------|
| `crm.db` / `crm_dev.db` | `engine` | 22 | Clienti, contratti, rate, eventi, movimenti, workout, misurazioni, obiettivi, esercizi, audit | Automatico al startup (prod) + manuale |
| `catalog.db` | `catalog_engine` | 7 | Muscoli (53), articolazioni (15), condizioni mediche (47), metriche (22), 3 junction tables | Shippato pre-costruito, rebuild via `build_catalog.py` |

**Session dependency**:
- `get_session()` → business DB (la maggior parte degli endpoint)
- `get_catalog_session()` → catalog DB (tassonomia, metriche, safety engine)
- Endpoint dual: ricevono ENTRAMBE le session (es. `get_exercise`, `get_safety_map`, misurazioni, obiettivi)

**Startup sequence** (`api/main.py`):
1. Auto-backup business DB (solo prod, max 5 auto-backup)
2. `create_db_and_tables()` — business tables
3. `create_catalog_tables()` — fallback se catalog.db assente
4. Seed esercizi builtin (311 esercizi + 426 relazioni + 494 media, idempotente, FK guard)
5. `PRAGMA integrity_check` su entrambi i DB

**Seed data** (`data/exercises/`):
- `seed_exercises.json` — 311 esercizi attivi (`in_subset=1`) con ID preservati per FK
- `seed_exercise_relations.json` — 426 relazioni (progressioni/regressioni/varianti)
- `seed_exercise_media.json` — 494 media (foto inizio/fine movimento)
- Inclusi nell'installer e nel bundle PyInstaller (`fitmanager.spec` datas)

**WAL mode**: entrambi i DB usano `PRAGMA journal_mode=WAL` + `foreign_keys=ON` + `busy_timeout=5000` (via event listener).

File chiave: `api/database.py` (dual engine), `api/config.py` (CATALOG_DATABASE_URL), `tools/admin_scripts/build_catalog.py` (costruisce catalog.db da DB sorgente).

### Backup & Data Protection (v2.0)

**Backup atomico**: `sqlite3.backup()` + `PRAGMA integrity_check` + SHA-256 checksum (sidecar `.sha256`).
**Restore robusto**: `sqlite3.backup()` page-level INTO DB live + `PRAGMA wal_checkpoint(TRUNCATE)` post-restore + `create_db_and_tables()` schema sync + `engine.dispose()`. Frontend: clear cookie JWT + redirect `/login` (credenziali backup potrebbero differire).

**7 endpoint** (`api/routers/backup.py`):
- `POST /backup/create` — backup manuale con integrity + checksum
- `GET /backup/list` — lista con checksum da sidecar
- `GET /backup/download/{f}` — download con path traversal protection
- `POST /backup/restore` — upload con magic bytes + integrity pre-check + safety backup + `sqlite3.backup()` page-level restore + WAL checkpoint + schema sync
- `GET /backup/export` — JSON v2.0 con 17 entita' business in ordine FK-safe
- `POST /backup/verify/{f}` — verifica SHA-256 + integrity_check
- `POST /backup/pre-update` — backup pre-aggiornamento app

**Export v2.0** (17 entita'): clienti → contratti → rate → eventi → movimenti → spese_ricorrenti → schede → sessioni → blocchi → esercizi_sessione → log_allenamenti → misurazioni → valori → obiettivi → todos → esercizi_custom → media_custom → audit_log.

**Retention**: max 30 backup manuali (auto-cleanup). Safety backup (pre_restore, pre_update) preservati.

**Auto-backup**: al startup prod, `auto_{timestamp}.sqlite` in `data/backups/`, max 5.

### Separazione dei layer (Il Muro)

| Layer | Puo' importare | NON puo' importare |
|-------|---------------|-------------------|
| `api/` | sqlmodel, pydantic, fastapi, stdlib | `core/`, `streamlit`, `frontend/` |
| `frontend/` | react, next, @tanstack/react-query | `api/`, `core/` (solo REST calls) |
| `core/` | stdlib, pydantic, langchain, ollama | `api/`, `streamlit` |

`api/` e `core/` sono **completamente indipendenti**. Operano sullo stesso DB con ORM diversi.
Il frontend comunica col backend SOLO via HTTP.

### Single Source of Truth Scientifica (SSoT)

> **Principio fondante: se un numero ha una fonte bibliografica, vive SOLO nel backend.**
> Il frontend lo consuma via API. Zero duplicazione di costanti, coefficienti o formule scientifiche.

Questo principio nasce dalla necessita' di:
1. **Manutenibilita'**: un coefficiente si aggiorna in UN posto, non in due
2. **Brevettabilita'**: l'algoritmo scientifico e' nel backend (protetto), il frontend e' UI
3. **Collaborazione accademica**: ricercatori lavorano su Python (backend), non TypeScript
4. **Determinismo**: una sola implementazione = zero rischio di divergenza

**Dove vive cosa**:

| Responsabilita' | Layer | Perche' |
|-----------------|-------|---------|
| Matrice EMG, volume MEV/MAV/MRV | Backend (`training_science/`) | Dati scientifici con fonte |
| Parametri carico (NSCA/ACSM) | Backend (`training_science/`) | Costanti evidence-based |
| Generazione piano allenamento | Backend (`POST /training-science/plan`) | Algoritmo proprietario |
| Analisi 4D (volume/balance/freq/recovery) | Backend (`POST /training-science/analyze`) | Calcolo scientifico |
| Periodizzazione mesociclo | Backend (`POST /training-science/mesocycle`) | Modello Israetel/Helms |
| Split ottimale per frequenza | Backend (`training_science/split_logic.py`) | Regole NSCA |
| Scoring 14D selezione esercizi | Frontend (`smart-programming/scorers.ts`) | UX real-time nel builder |
| Safety engine mapping | Backend (`safety_engine.py`) | Dati clinici |
| Profilo client aggregato | Frontend (`smart-programming/helpers.ts`) | Composizione hook locali |
| Rendering analisi (barre, colori) | Frontend (`SmartAnalysisPanel.tsx`) | Presentazione UI |

**Pattern di consumo**: il frontend chiama le API backend via React Query hook (`useTrainingScience`),
cacha i risultati, e li presenta nei componenti UI. Per analisi real-time nel builder,
il frontend invia la scheda corrente a `POST /training-science/analyze` con debounce (300ms).

**Regola ferrea**: MAI duplicare una costante scientifica nel frontend.
Se serve un valore (es. volume target per muscolo), fetcharlo da `GET /training-science/volume-targets`.

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
- **Cross-validation evento↔contratto↔cliente**: `create_event` verifica `contract.id_cliente == data.id_cliente` (400 se mismatch)
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
2. **Catch-all** — `except Exception: pass` e bare `except:` / `catch {}`. Solo eccezioni specifiche. Frontend: `catch(e) { if (axios.isAxiosError(e) && e.response?.status === 404) return null; throw e; }`
3. **Magic strings** — Usare Enum/costanti. Mai `"PENDENTE"` inline.
4. **print() per logging** — Usare `logger` (core) o `console.error` (frontend).
5. **Dict raw** — I repository/router restituiscono modelli Pydantic tipizzati.
6. **any** — TypeScript: mai `any`. Definire interfacce in `types/api.ts`.
7. **N+1 queries** — Batch fetch con `IN (...)` o `selectinload`. Mai loop di query.
8. **Mass Assignment** — Input schema SENZA campi protetti (trainer_id, id dal JWT).
9. **File monolite** — Max **300 LOC** per file di logica (funzioni, componenti, hook). File di puri dati/configurazione (tabelle, costanti, blueprint) possono arrivare a **400 LOC**. Oltre → spezzare in moduli coerenti con `index.ts` per re-export. Questo e' un COMANDAMENTO SACRO: un file lungo e' un file non manutenibile.
10. **Scienza duplicata** — MAI duplicare costanti scientifiche (volume target, coefficienti EMG, parametri carico) tra backend e frontend. Il backend e' la Single Source of Truth (vedi sezione SSoT). Il frontend fetcha via API.

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
| Dev backend usa crm.db (prod) | `api/config.py` default hardcoded a `crm.db`, `DATABASE_URL` non settato | Auto-detect da porta: `--port 8001` → `crm_dev.db`. Logica in `_resolve_database_url()` |
| KPI NaN da worker zombie | Worker zombie serve codice vecchio (senza campi KPI) → `data.kpi_X` = undefined → `formatCurrency(undefined)` = NaN | `?? 0` guard su ogni `getKpiValue` + kill zombie e riavviare |
| Rate oltre scadenza contratto | Nessuna validazione date rate vs contratto → rate orfane dopo scadenza | Boundary check bidirezionale: create/update rate (422) + update contract (422) + DatePicker maxDate |
| `ha_rate_scadute` ignora contratti scaduti | Solo `rate.data_scadenza < today`, non considera contratto expired con rate future non saldate | `or_(Rate.data_scadenza < today, Contract.data_scadenza < today)` in contracts.py e clients.py |
| KPI "Rate Scadute" conta contratti | `func.count(func.distinct(Rate.id_contratto))` conta contratti, non rate reali | `func.count(Rate.id)` per conteggio rate effettive (contracts), label corretta per clienti |
| Badge dentro `SelectTrigger` Radix | `position="item-aligned"` (default) richiede `SelectValue` nel trigger per calcolare posizione dropdown. Badge/div sostitutivo → dropdown non si apre silenziosamente | Usare SEMPRE `SelectValue` + `position="popper"` per trigger custom. Mai sostituire `SelectValue` con Badge |
| `useUpdateClient` stale profile | `onSuccess` invalidava `["clients"]` lista ma non `["client", id]` → profilo cliente non si aggiornava dopo modifica | Invalidare SEMPRE sia la lista `["entities"]` che il dettaglio `["entity", id]` in ogni mutation di update |
| Utility duplicate in 8+ file | `formatShortDate`, `getFinanceBarColor` copia-incollate in ogni componente → divergenza e manutenzione impossibile | Centralizzare in `lib/format.ts` e importare. MAI definire utility di formattazione localmente |
| `<button>` nested in `<button>` | PopoverTrigger (button) dentro button nome esercizio → hydration error Next.js | SafetyPopover e name button come siblings dentro `<div>`, MAI annidati |
| `fetch()` CORS su StaticFiles | `fetch()` cross-origin bloccato da CORS su StaticFiles backend, ma `<img>` funziona (esente da CORS) → export workout senza foto (Excel legacy e clinico HTML/PDF) | Next.js `rewrites` in `next.config.ts` proxya `/media/*` al backend → fetch same-origin. MAI `getMediaUrl()` per fetch, solo URL relativi |
| `next.config.ts` rewrite destination hardcoded | `destination: process.env.NEXT_PUBLIC_API_URL \|\| "http://localhost:8000"` non valorizzato in dev → rewrite proxya a 8000, ma dev backend e' su 8001 → tutte le immagini 404 → export senza foto | Port-aware detection: `const port = parseInt(process.env.PORT ?? "3000"); const backendPort = port >= 3001 ? 8001 : 8000;`. `process.env.PORT` e' impostato da Next.js dalla flag `-p` a startup time (non build time) |
| `setattr(plan, "data_inizio", "str")` su campo Date | Schema Pydantic manda stringhe, modello SQLModel ha `Optional[date]` → SQLAlchemy non converte automaticamente | Convertire `date.fromisoformat(value)` nel router PRIMA di `setattr`. MAI passare stringhe a campi date del modello |
| Spese annuali non confermabili | `_date_from_mese_anno_key("2026", giorno)` ritorna `None` per key annuali (formato "YYYY" senza mese) → `confirm_expenses` skippa silenziosamente | Aggiunto parametro `start_month` a `_date_from_mese_anno_key()`. Call site passa `_get_start_date(expense).month` |
| Invalidazione rate CRUD asimmetrica | `useCreateRate`/`useUpdateRate`/`useDeleteRate`/`useGeneratePaymentPlan` invalidavano 3 query, ma `usePayRate`/`useUnpayRate` ne invalidavano 6 → pagina Cassa stale dopo CRUD rate | Aggiunte `["movements"]`, `["movement-stats"]`, `["aging-report"]` a tutte le 4 mutation |
| Movimenti: aging-report non invalidato | `useCreateMovement`/`useDeleteMovement`/`useConfirmExpenses` non invalidavano `["aging-report"]` → aging stale dopo operazioni ledger | Aggiunta invalidazione `["aging-report"]` a tutte e 3 le mutation |
| Spese ricorrenti: invalidazione incompleta | Le 3 mutation invalidavano solo `["recurring-expenses"]` e `["movement-stats"]`. Mancavano dashboard, pending, forecast | Aggiunte `["dashboard"]`, `["pending-expenses"]`, `["forecast"]` |
| Chiusura spesa fissa bloccata su record disattivato | L'endpoint `close` ritornava 400 "già disattivata", impedendo rettifica cutoff retroattiva | `close` reso idempotente: riconcilia storni anche su spese disattivate |
| Storno contato come entrata operativa | KPI e grafico trattavano `STORNO_SPESA_FISSA` come entrata, generando mismatch sul cashflow mensile | In `movements/stats` lo storno viene nettato su uscite fisse e chart giornaliero |
| Type sync `DashboardSummary.ledger_alerts` | Backend restituisce `ledger_alerts: int` ma interfaccia TypeScript non lo dichiarava → frontend vede `undefined` | Aggiunto `ledger_alerts: number` a `DashboardSummary` in `types/api.ts` |
| Evento assegnabile a contratto di altro cliente | `create_event` validava ownership contratto (trainer) ma non `contract.id_cliente == data.id_cliente` → crediti scalati dal contratto sbagliato | Aggiunto Bouncer 2b: cross-validation cliente↔contratto in `agenda.py` |
| Esercizi builtin modificabili via PUT | `delete_exercise` chiama `_guard_custom()` ma `update_exercise` no → trainer puo' corrompere esercizi builtin | Aggiunto `_guard_custom(exercise)` in `update_exercise` dopo il bouncer |
| Delete media path errato (manca `data/`) | `MEDIA_ROOT.parent.parent.parent / media.url.lstrip("/")` risolve a `project_root/media/...` invece di `project_root/data/media/...` → file orfani su disco | Ricostruito path da `MEDIA_ROOT / str(exercise_id) / Path(media.url).name` |
| `useUpdateContract` stale dettaglio | Invalidava `["contracts"]` e `["dashboard"]` ma non `["contract"]` → pagina dettaglio stale dopo modifica | Aggiunta invalidazione `["contract"]` (prefix match) |
| `useDeleteWorkout` stale builder | Invalidava `["workouts"]` ma non `["workout"]` → builder visibile con dati fantasma dopo eliminazione | Aggiunta invalidazione `["workout"]` |
| `active_count` hardcoded a 118 | `get_archive_stats` ritornava `"active_count": 118` hardcoded (reale: 205, cambia con batch) | Sostituito con query dinamica `func.count(Exercise.id).where(in_subset == True)` |
| JWT_SECRET fallback silenzioso | Se env var mancante, log WARNING facilmente ignorabile + token firmati con stringa pubblica | Upgrade a log CRITICAL con messaggio esplicito |
| `useLatestMeasurement` bare catch inghiotte 5xx | `catch {}` cattura ogni errore e ritorna `null` → 500/network error silenzioso, React Query non ritenta | Separato: 404 → `null`, altri errori → `throw` (React Query gestisce retry) |
| `date.fromisoformat()` senza try/except | Input utente malformato → `ValueError` non gestito → 500 in `workouts.py` e `goals.py` | Aggiunto `try/except (ValueError, TypeError)` → 422 con messaggio specifico |
| `useCreateContract`/`useDeleteContract` invalidazione incompleta | Invalidavano solo `["contracts"]` e `["dashboard"]`. Mancavano contract detail, clients, movements, aging | Aggiunte 6 invalidazioni: `["contract"]`, `["clients"]`, `["client"]`, `["movements"]`, `["movement-stats"]`, `["aging-report"]` |
| SQLAlchemy subquery cross-join | `select(func.sum(case(CashMovement.tipo...))).select_from(query.subquery())` — i riferimenti `CashMovement.*` non vengono adattati alle colonne del subquery → cross-join implicito con tabella originale → somma enorme | Usare `subq = query.subquery()` poi `subq.c.tipo`, `subq.c.importo` nelle espressioni. MAI `CashMovement.*` con `select_from(subquery)` |
| `activate_batch.py` verify rollback asimmetrico | Verify per-DB: DB-A rollbacka 5, DB-B rollbacka 3 → delta silenzioso tra DB. Anche: verify PRIMA di fill_tempo → 43/50 rollbackati per campo auto-fillable | 3 safeguard: (1) pre-check sync (union), (2) fill_tempo_consigliato pre-verify, (3) rollback union (se fallisce su QUALSIASI DB → rollback su TUTTI) |
| `populate_exercise_relations` chain IDs stale | Chain IDs puntano a esercizi disattivati (57/91 stale) → 21% copertura relazioni | Aggiornare chains ad OGNI batch activation. Riscrittura completa chains da 186→269 esercizi |
| Filtri persistenti confondono utente | `loadFilters()` ripristinava filtri su OGNI mount, anche navigazione fresca (sidebar). `popstate`+`nav:back` flag inaffidabile con Next.js App Router | **Sidebar `clearPageState()` onClick** cancella sessionStorage prima della navigazione. Back-nav non passa dalla Sidebar → stato intatto → ripristinato. Zero dipendenza da `popstate` |
| Scroll restoration non funziona | `min-h-screen` su wrapper esterno → `<main>` cresce oltre viewport → scroll avviene su `window`, non su `<main>`. Listener e restore su `mainRef` senza effetto | `h-screen` + `overflow-hidden` su wrapper → `<main>` diventa il vero scroll container. Salvataggio continuo via scroll event (rAF). Restore con retry [0-2000ms]. Sidebar cancella `scroll:` onClick |
| `useEffect([queryData])` sovrascrive form | Mutation inline (cambio obiettivo/livello) invalida query → refetch → useEffect riscrive stato locale con dati server vecchi → TUTTE le modifiche non salvate perse silenziosamente | Guard `isDirtyRef.current` (schede builder), `userHasEdited` state (impostazioni), `initializedEditId` ref (misurazioni). MAI useEffect incondizionato su dati React Query che alimentano form editabili |
| `onClick={goBack}` con default param | `goBack(force = false)` usata come handler: React passa `MouseEvent` come primo arg → truthy → bypass guard | Sempre `onClick={() => goBack()}`. MAI passare funzione con default param direttamente a onClick |
| `router.push()` senza guard dirty | `goBack()` fa navigazione client-side che non triggera `beforeunload` → dati persi senza avviso | `goBack(force = false)` con `window.confirm()` se isDirty. `force=true` solo da mutation `onSuccess` |
| `isDirty` falso positivo in edit mode | `filledCount > 0` vero subito dopo caricamento dati server (non serve modifica utente) → confirm spurio su back | `userHasEditedRef`: ref settato `true` solo su interazione reale (input/note/date), reset a `false` dopo init dal server |
| `DETACH DATABASE` con transazione aperta | INSERT impliciti creano transazione; `DETACH` fallisce con "database src is locked" | `catalog.commit()` PRIMA di `DETACH` in `build_catalog.py` |
| Cross-DB subquery in dual-DB | `select(Exercise.id)` come subquery per filtrare `ExerciseCondition` fallisce (tabelle in DB diversi) | Fetch IDs dal business engine, poi passa lista di IDs al catalog engine. Mai subquery cross-engine |
| Catalog FK cross-DB su `id_esercizio` | Junction tables (esercizi_muscoli/articolazioni/condizioni) hanno FK a `esercizi.id` che non esiste in catalog.db | DDL catalog SENZA FK su `id_esercizio` (referenza cross-DB, validazione application-level). FK intra-catalog enforced |
| Restore DB non funziona con WAL mode | `shutil.copy2` / `write_bytes` sovrascrive solo `.db` ma `-wal` e `-shm` contengono write recenti → WAL replay annulla il restore. Su Windows, file lock impedisce overwrite con connessioni attive | `sqlite3.backup()` page-level copy INTO il DB live (bypassa file lock, gestisce WAL). `engine.dispose()` DOPO il backup forza nuove connessioni. MAI file-level overwrite su DB SQLite con WAL attivo |
| Restore senza WAL checkpoint | Dopo `sqlite3.backup()` i file `-wal`/`-shm` stale del DB precedente interferiscono con i dati ripristinati | `PRAGMA wal_checkpoint(TRUNCATE)` subito dopo il restore per forzare flush WAL e rimuovere file stale |
| Restore senza schema sync | Backup da versione precedente puo' mancare tabelle nuove (es. `esercizi_media`) → crash al primo accesso | `create_db_and_tables()` dopo `engine.dispose()` → CREATE IF NOT EXISTS su tutte le tabelle |
| Restore senza cookie clear | JWT nel cookie referenzia trainer del DB pre-restore → 401 silenzioso dopo redirect | `Cookies.remove(TOKEN_COOKIE)` + `window.location.href = "/login"` nel frontend dopo restore |
| `Path(__file__)` in PyInstaller | In bundle congelato `__file__` punta alla cartella temp di estrazione, non alla cartella installazione | Usare sempre `DATA_DIR` da `api/config.py` che gestisce `sys.frozen` e `sys._MEIPASS` |
| Seed media mancante | Immagini esercizi su disco (`data/media/exercises/`) ma `esercizi_media` DB vuoto → `exercise.media = []` → frontend non renderizza foto | `seed_exercise_media()` al startup con FK guard (skip orfani). JSON: `data/exercises/seed_exercise_media.json` (494 record) |

---

## Sicurezza (Non Negoziabile)

1. **Multi-tenancy**: trainer_id da JWT, iniettato server-side, mai dal body
2. **Query parametrizzate**: `WHERE id = ?` (core/) o `select().where()` (api/)
3. **3 layer auth**: Edge Middleware → AuthGuard client → JWT API validation
4. **Builtin guard**: `_guard_custom(exercise)` blocca modifica/eliminazione esercizi builtin su update E delete
5. **JWT_SECRET**: log CRITICAL se non configurato. Token firmati con chiave di sviluppo — MAI in produzione esposta
6. **Niente PII nei prompt LLM**: usare attributi anonimi
7. **Solo LLM locale** (Ollama): mai inviare dati a cloud senza consenso

---

## Protezione Dati Non Salvati (Data Protection)

> **Filosofia: mai perdere dati silenziosamente.** Ogni form con piu' di 2 campi
> deve proteggere l'utente dalla perdita accidentale di modifiche non salvate.

**Hook centralizzato**: `hooks/useUnsavedChanges.ts` — 2 livelli di difesa:
1. **beforeunload** — avviso su chiusura tab / refresh / navigazione esterna (dirtyRef stale-closure-safe)
2. **Draft sessionStorage** — auto-save bozza, recuperabile al rientro (`saveDraft`/`loadDraft`/`clearDraft`)

**3 pattern anti-overwrite** (prevengono refetch server da sovrascrivere form editabili):
- **isDirtyRef guard** (schede builder): `useEffect([plan])` bloccato se `isDirtyRef.current === true`
- **userHasEdited state** (impostazioni): flag booleano, settato true su onChange, resettato su save
- **initializedEditId ref** (misurazioni): ref con ID gia' inizializzato, previene re-init su refetch

**goBack guard** — pattern per pagine full-page con navigazione esplicita (misurazioni):
- `goBack(force = false)`: se `!force && isDirty` → `window.confirm()`. `force=true` solo da mutation `onSuccess`
- `userHasEditedRef`: distingue "dati caricati dal server" da "utente ha editato" in edit mode
- ATTENZIONE: `onClick={goBack}` passa MouseEvent come `force` (truthy). Sempre `onClick={() => goBack()}`
- `router.push()` e' navigazione client-side → non triggera `beforeunload` → serve guard esplicito

**guardedOpenChange** — pattern per Sheet/Dialog:
```typescript
const guardedOpenChange = useCallback((newOpen: boolean) => {
  if (!newOpen && dirtyRef.current) {
    if (!window.confirm("Hai modifiche non salvate. Vuoi davvero uscire?")) return;
  }
  dirtyRef.current = false;
  onOpenChange(newOpen);
}, [onOpenChange]);
```
Save bypass: `dirtyRef.current = false` in `onSuccess` PRIMA di `onOpenChange(false)`.

**onDirtyChange callback** — per Form con react-hook-form dentro Sheet:
- Form espone `onDirtyChange?: (dirty: boolean) => void` nelle props
- `useEffect(() => { onDirtyChange?.(isDirty); }, [isDirty, onDirtyChange]);`
- Sheet riceve via `handleDirtyChange` → scrive in `dirtyRef`

**Componenti protetti** (12 contesti di editing):
- HIGH: schede builder (beforeunload + draft + isDirtyRef), misurazioni (beforeunload + initializedEditId + goBack guard + userHasEditedRef), AnamnesiWizard (guardedOpenChange), ExerciseSheet (guardedOpenChange + onDirtyChange)
- MEDIUM: ClientSheet, ContractSheet, EventSheet, MovementSheet, GoalFormDialog (tutti: guardedOpenChange + onDirtyChange o dirtyRef)

**Test**: 69 test Vitest in `frontend/src/__tests__/data-protection/` — draft API, guard patterns, edge cases.

File chiave: `hooks/useUnsavedChanges.ts` (hook + draft API), `__tests__/data-protection/` (3 file test).

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
- `bash tools/scripts/check-all.sh` — ruff check + next build, zero errori
- Test end-to-end: avvia API → avvia frontend → login → verifica flusso
- Commit con messaggio chiaro

---

### Coordinamento Multi-Agente AI (Codex + Claude Code)

Quando piu agenti lavorano in parallelo, seguire SEMPRE questo ordine:

1. `AGENTS.md` - priorita, guardrail e quality gate
2. `docs/ai-sync/MULTI_AGENT_SYNC.md` - protocollo operativo comune
3. `docs/ai-sync/WORKBOARD.md` - claim task, lock file, handoff

Workflow minimo obbligatorio:
1. Claim task nel workboard prima di qualsiasi edit.
2. Dichiarare `Locked files` e aggiornarli appena cambia lo scope.
3. Nessun editing su file lockati da altro agente senza handoff scritto.
4. Chiusura task con check rilevanti, aggiornamento docs upgrade, rilascio lock.

Regola di sicurezza: meglio fermarsi e riallineare che aprire merge conflict su file condivisi.

## Workflow Operativo per Claude Code

> Regole imperative per l'agente AI. Seguile alla lettera.

### Quando aggiungi un campo al DB
1. Migrazione Alembic (`alembic revision -m "desc"`)
2. `api/models/` — campo SQLModel
3. `api/schemas/` — campo Pydantic (input + output)
4. `api/routers/` — grep TUTTI i punti che costruiscono/copiano quel modello (insert, build_response, duplicate)
5. `frontend/src/types/api.ts` — interfaccia TypeScript mirror
6. Componenti UI che usano quel tipo — grep e aggiornare
7. `bash tools/scripts/migrate-all.sh` — entrambi i DB
8. `bash tools/scripts/check-all.sh` — zero errori

### Quando modifichi uno schema Pydantic
1. Aggiorna il mirror TypeScript in `types/api.ts`
2. Grep i componenti frontend che consumano quel tipo
3. Verifica che i campi aggiunti/rimossi siano gestiti in UI

### Quando crei un mutation hook (useMutation)
1. `onSuccess` DEVE invalidare TUTTE le query correlate (lista + dettaglio + correlate)
2. Operazioni inverse (pay/unpay, create/delete) DEVONO avere invalidazione IDENTICA
3. Operazioni che toccano entita' collegate (es. contratto → rate → movements) DEVONO invalidare l'intera catena
4. Mostrare toast di conferma (sonner)

### Quando usi date.fromisoformat() su input utente
- SEMPRE wrappare in `try/except (ValueError, TypeError)` → `raise HTTPException(422, "Formato data non valido")`
- Mai fidarsi che il frontend mandi date valide — un client API o un fuzzer puo' mandare qualsiasi stringa
- Pattern: vedi `workout_logs.py:139-145` (corretto) vs `workouts.py:389-391` (corretto con Sprint 3)

### Quando crei un nuovo esercizio in memoria (oggetto JS)
- DEVE avere TUTTI i campi di `WorkoutExerciseRow`, inclusi quelli nullable (= `null`)
- Il build fallisce se manca un campo required nell'interfaccia

### Prima di ogni commit
- `bash tools/scripts/check-all.sh` — OBBLIGATORIO, zero eccezioni

### Regole deployment-aware (SEMPRE)
1. **Path**: `Path(__file__).parent` (Python), import relativi (TS). Zero path assoluti nel codice.
2. **Empty state**: ogni pagina/componente deve gestire zero-records con messaggio + CTA, mai crash o schermo bianco.
3. **Import AI condizionale**: `torch`, `transformers`, `langchain` con `try/except ImportError` → graceful fallback.
4. **Dati solo in `data/`**: DB, media, licenza, log, backup. Mai scrivere file fuori da `data/`.
5. **Nessun seed a runtime**: l'app deve funzionare con DB vuoto (Setup Wizard crea il primo trainer).
6. **Configurazione via env**: ogni parametro configurabile deve leggere da env var con default sensato.

---

## Definition of Done

Checklist da verificare prima di dichiarare una feature completata.

- [ ] `ruff check api/` — zero warning
- [ ] `npx next build` — zero errori TypeScript
- [ ] Type sync: ogni campo Pydantic ha il mirror in `types/api.ts`
- [ ] Invalidation check: ogni `useMutation` invalida lista + dettaglio + correlate
- [ ] Nessun `any` TypeScript introdotto

Shortcut: `bash tools/scripts/check-all.sh` copre i primi 2 punti.

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

### Database Auto-Detect (zero rischio di toccare dati prod)
Il backend rileva automaticamente quale DB usare dalla porta uvicorn:
- `--port 8000` → `crm.db` (prod, default)
- `--port 8001` → `crm_dev.db` (dev, auto)
- Se `DATABASE_URL` e' settato esplicitamente, ha sempre priorita'
- Logica: `api/config.py` → `_resolve_database_url()`
- Log di startup mostra `DEV (crm_dev.db)` o `PROD (crm.db)` per conferma visiva

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
bash tools/scripts/migrate-all.sh            # Alembic su ENTRAMBI i DB
bash tools/scripts/kill-port.sh 8000         # Kill pulito (tree-kill, no zombie)
bash tools/scripts/restart-backend.sh dev    # Kill + restart porta 8001
bash tools/scripts/restart-backend.sh prod   # Kill + restart porta 8000
bash tools/scripts/check-all.sh              # ruff + next build — gate pre-commit
bash tools/scripts/activate-exercises.sh     # Batch 50 esercizi (Ollama + pipeline)
bash tools/scripts/activate-exercises.sh --dry-run  # Solo audit, zero modifiche
```

### Regole blindate
1. **Migrazioni**: `bash tools/scripts/migrate-all.sh` — MAI `alembic upgrade head` da solo
2. **Kill backend**: `bash tools/scripts/kill-port.sh <porta>` — MAI `Ctrl+C` senza verificare
3. **crm.db sacro**: dati reali di Chiara. MAI toccare con seed/reset
4. **crm_dev.db libero**: dati di test (30 clienti, 4 mesi). Seed/reset quando vuoi
5. **Frontend dev**: `npm run dev` → porta 3001 automatica, API a 8001 automatica
6. **Frontend prod**: `npm run build && npm run prod` → porta 3000, API a 8000

### Pitfall Windows: zombie uvicorn worker
Su Windows, `Ctrl+C` uccide il master uvicorn ma i worker figli (multiprocessing.spawn)
restano vivi con il socket aperto → servono codice vecchio. Soluzione: `kill-port.sh`
usa `taskkill /T /F` per uccidere l'intero albero di processi.

---

## Distribuzione Commerciale — Regole di Sviluppo

> Piano completo in `docs/DEPLOYMENT_PLAN.md`. Strategia: **Installer Nativo Windows + Licenza RSA**.
> Queste regole governano lo sviluppo QUOTIDIANO per garantire che il codice sia sempre distribuibile.

### Principi (Da Rispettare SEMPRE)

1. **Zero path assoluti** — Ogni path DEVE essere relativo a `Path(__file__).parent` (backend) o import relativo (frontend). Mai `C:\Users\...` o `/home/...` nel codice.
2. **Graceful first-run** — Se il DB e' vuoto, l'app DEVE funzionare (Setup Wizard). Ogni query che assume dati esistenti deve gestire il caso zero-records.
3. **Self-contained runtime** — A runtime nessuna dipendenza da tool CLI (npm, pip, alembic). Migrazioni DB automatiche all'avvio.
4. **License-aware** — Feature premium (AI, export avanzati) devono poter essere gated per tier di licenza. Middleware licenza su ogni request API.
5. **Versioning esplicito** — `__version__` nel backend (`api/__init__.py`), `version` nel `package.json`, mostrato in UI (Impostazioni). Formato SemVer.
6. **Dipendenze AI opzionali** — `torch`, `transformers`, `langchain`, `chromadb`, `sentence-transformers` NON richiesti per funzionamento base. Import condizionale con `try/except ImportError`.
7. **Configurazione runtime** — `JWT_SECRET`, porta, path DB configurabili via env vars O file `.env` nella cartella dati. Mai hardcoded.
8. **Dati in `data/`** — Tutto cio' che e' persistente (DB, media, licenza, log, backup) va in `data/`. Unica cartella che sopravvive agli aggiornamenti.
9. **Empty state UX** — Ogni pagina con zero dati mostra messaggio descrittivo + CTA per creare il primo record. Mai schermo bianco.
10. **Nessun segreto nel bundle** — La chiave pubblica RSA (verifica licenza) puo' essere embedded. La chiave privata (firma licenze) MAI.

### Architettura Build (Operativa)

```
Source (Git privato)
|
+-- api/           -> PyInstaller -> dist/fitmanager/fitmanager.exe (102MB)
+-- frontend/      -> next build --standalone -> .next/standalone/ (45MB)
+-- installer/     -> Inno Setup -> dist/FitManager_Setup.exe (83MB)
|   launcher.bat      Avvia backend + frontend + apre browser (supporta --port)
|   fitmanager.iss    Script Inno Setup 6 (italiano, data/ preservata)
|   node/             node.exe runtime (copiato, non committato)
|   assets/           EULA.txt
+-- tools/build/
|   build-frontend.sh   npm build + copia static/public nel standalone
|   build-backend.sh    PyInstaller con fitmanager.spec
|   entry_point.py      Wrapper uvicorn (--port support)
|   fitmanager.spec     PyInstaller spec (esclude AI libs ~1.8GB)
+-- data/          -> Sopravvive agli aggiornamenti
    crm.db            Database SQLite
    media/            Foto esercizi
    license.key       JWT firmato RSA
    .env              Configurazione locale (JWT_SECRET auto-generato)
```

**Formula porte**: `frontend_port - 3000 + 8000 = backend_port`
- 3000→8000 (prod), 3001→8001 (dev), 3002→8002 (installer test)

### Checklist Pre-Distribuzione

- [x] Sistema licenza RSA backend — S1.1 DONE
- [x] License middleware HTTP — S1.2 DONE
- [x] License Generation CLI — S1.5 DONE
- [x] JWT_SECRET auto-generato — S1.3 DONE
- [x] `/health` con stato licenza — S1.4 DONE
- [x] Frontend license UX — S1.6 DONE
- [x] Setup Wizard — S2.1 DONE
- [x] Dashboard WelcomeCard first-run — S2.2 DONE
- [x] Next.js standalone bundle (45MB) — S3.1 DONE
- [x] PyInstaller `fitmanager.exe` (102MB) — S3.2 DONE
- [x] Launcher + Inno Setup installer (83MB) — S3.3 DONE
- [x] Smoke test: install → login page funzionante — S3.4 DONE
- [x] Fix post-smoke-test: path PyInstaller, seed media/relazioni, backup restore — S3.5 DONE
- [x] Installer testato: install → login → esercizi con foto → backup/restore — 83MB
- [ ] `__version__` visibile in UI Impostazioni
- [ ] Flusso E2E completo: install → licenza → setup → cliente → contratto → agenda

Tracking dettagliato: `docs/upgrades/specs/UPG-2026-03-04-06-launch-market-readiness-roadmap.md`

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
bash tools/scripts/check-all.sh                           # ruff + next build — OBBLIGATORIO prima di ogni commit
cd frontend && npx next build                             # solo frontend (se serve)
cd frontend && npm test                                   # 69 vitest (data protection)
pytest tests/ -v                                          # 63 test

# ── Build Distribuzione ──
bash tools/build/build-frontend.sh                        # Next.js standalone bundle (45MB)
bash tools/build/build-backend.sh                         # PyInstaller exe (102MB, richiede pip install pyinstaller)
# Inno Setup (compila installer 83MB):
"/c/Users/gvera/AppData/Local/Programs/Inno Setup 6/ISCC.exe" installer/fitmanager.iss
# Test installer: dist/FitManager_Setup.exe

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
# POST /api/backup/create     (richiede JWT — atomico + SHA-256 + integrity)
# POST /api/backup/verify/{f}  (verifica checksum + integrity)
# POST /api/backup/pre-update  (backup pre-aggiornamento)
# GET  /api/backup/export     (JSON v2.0: 17 entita' trainer)

# ── Catalog DB ──
python -m tools.admin_scripts.build_catalog               # Costruisce catalog.db da crm.db
python -m tools.admin_scripts.build_catalog --source crm_dev  # Da crm_dev.db
python -m tools.admin_scripts.build_catalog --dry-run     # Solo conteggi

# ── Reset & Seed (FERMA il server API prima!) ──
python tools/admin_scripts/reset_production.py            # DB pulito con solo Chiara
python -m tools.admin_scripts.seed_dev                    # 30 clienti × 4 mesi su crm_dev.db
# Credenziali prod: chiarabassani96@gmail.com / chiarabassani
# Credenziali dev:  chiarabassani96@gmail.com / Fitness2026!

# ── Database ──
sqlite3 data/crm.db ".tables"
sqlite3 data/crm_dev.db ".tables"
sqlite3 data/catalog.db ".tables"
```

---

## Metriche Progetto

- **api/**: ~17,000 LOC Python — 19 modelli ORM, 16 router, 8 schema modules, 6 services + 1 parser (18 moduli)
- **frontend/**: ~18,000 LOC TypeScript — ~80 componenti, 17 hook modules, 21 pagine
- **core/**: ~10,300 LOC Python — moduli AI (RAG, exercise archive) in attesa di API endpoints
- **tools/admin_scripts/**: ~3,200 LOC Python — 16 script (import, quality engine, taxonomy, seed, test, QA clinica)
- **DB**: Dual-DB SQLite (22 business + 7 catalog), WAL mode, FK enforced, multi-tenant via trainer_id
- **Esercizi**: 311 attivi (tassonomia completa, seed JSON incluso in installer) + 790 archiviati (reinserimento graduale)
- **Test**: 63 pytest + 67 E2E + 69 vitest (data protection)
- **Sicurezza**: JWT auth, bcrypt, Deep Relational IDOR, 3-layer route protection
- **Cloud**: 0 dipendenze, 0 dati verso terzi

---

*Questo file e' la legge. Il codice che non la rispetta non viene mergiato.*
