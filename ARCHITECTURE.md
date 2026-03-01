# FitManager AI Studio — Documento Architetturale Completo

> Documento di riferimento per comprendere struttura, scopo e stato del progetto.
> Aggiornato: 26 Febbraio 2026.

---

## 1. Missione e Visione

**FitManager AI Studio** e' il CRM di riferimento per personal trainer e professionisti fitness a P.IVA.
Gestisce salute fisica e contabilita' di persone reali — zero approssimazione.

**Utente target**: Chiara Bassani, personal trainer con P.IVA. Gestisce clienti, contratti, pagamenti,
agenda sessioni e schede allenamento. L'app deve essere il suo strumento principale di lavoro quotidiano.

**Filosofia**:
- **Privacy-first**: tutto in locale, zero cloud, zero dati verso terzi
- **AI locale**: Ollama + ChromaDB, modelli on-device (gemma2:9b, Mixtral)
- **Qualita' contenuti**: l'allenamento e' un sottoramo della medicina — contenuti imprecisi causano infortuni
- **UX premium**: l'app deve far piacere lavorare, non essere un peso
- **Codice elegante**: la base della manutenibilita'

**Stack**: FastAPI + SQLModel | Next.js 16 + React 19 + shadcn/ui | SQLite (PostgreSQL-ready) | Ollama + ChromaDB

---

## 2. Architettura ad Alto Livello

```
┌─────────────────────────────────────────────────┐
│  FRONTEND  (Next.js 16 + React 19 + TypeScript) │
│  ~20,000 LOC · 13 pagine · ~80 componenti       │
│  11 hook modules · React Query v5 · shadcn/ui    │
└────────────────────┬────────────────────────────┘
                     │ REST API (JSON/HTTP, JWT auth)
                     │ Porta 3000(prod) / 3001(dev)
                     ▼
┌─────────────────────────────────────────────────┐
│  BACKEND API  (FastAPI + SQLModel ORM)           │
│  ~8,800 LOC · 11 router · 60+ endpoint          │
│  11 modelli ORM · 40+ Pydantic schema            │
└────────────────────┬────────────────────────────┘
                     │ Porta 8000(prod) / 8001(dev)
                     ▼
┌─────────────────────────────────────────────────┐
│  SQLite Database                                 │
│  23 tabelle · FK enforced · multi-tenant         │
│  crm.db (prod) / crm_dev.db (dev)               │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  CORE  (moduli AI, dormant — non esposti via API)│
│  ~6,900 LOC · workout gen · RAG · card parser    │
│  9 repository legacy (sqlite3 raw)               │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  TOOLS  (admin scripts, migration, seed, test)   │
│  ~4,000 LOC · 20+ script · Ollama enrichment     │
└─────────────────────────────────────────────────┘
```

### Separazione dei Layer (Il Muro)

| Layer | Puo' importare | NON puo' importare |
|-------|---------------|-------------------|
| `api/` | sqlmodel, pydantic, fastapi, stdlib | `core/`, `frontend/` |
| `frontend/` | react, next, tanstack | `api/`, `core/` (solo REST) |
| `core/` | stdlib, pydantic, langchain, ollama | `api/`, `frontend/` |

---

## 3. Database — Schema Completo (23 Tabelle)

### 3.1 Tabelle Principali

#### `trainers` — Tenant Root (multi-tenancy)
```
id (PK), email (UNIQUE), nome, cognome, hashed_password (bcrypt), is_active, created_at
```

#### `clienti` — Clienti del trainer
```
id (PK), trainer_id (FK→trainers), nome, cognome, telefono, email,
data_nascita, sesso ("Uomo"|"Donna"|"Altro"), anamnesi_json (JSON),
stato ("Attivo"|"Inattivo"), note_interne, data_creazione, deleted_at
```

#### `contratti` — Contratti (entita' centrale del sistema)
```
id (PK), trainer_id (FK→trainers), id_cliente (FK→clienti),
tipo_pacchetto, data_vendita, data_inizio, data_scadenza,
crediti_totali (int), crediti_usati (int, computed on read),
prezzo_totale (float), acconto (float), totale_versato (float),
stato_pagamento ("PENDENTE"|"PARZIALE"|"SALDATO"),
chiuso (bool, auto-computed), note, deleted_at
```

#### `rate_programmate` — Rate di pagamento (Deep IDOR → Contract.trainer_id)
```
id (PK), id_contratto (FK→contratti),
data_scadenza (date, <= contract.data_scadenza),
importo_previsto (float), importo_saldato (float),
stato ("PENDENTE"|"PARZIALE"|"SALDATA"), descrizione, deleted_at
```

#### `movimenti_cassa` — Libro mastro
```
id (PK), trainer_id (FK→trainers), data_movimento, data_effettiva,
tipo ("ENTRATA"|"USCITA"), categoria, importo, metodo,
id_cliente (FK), id_contratto (FK), id_rata (FK),
id_spesa_ricorrente (FK), mese_anno (dedup key),
note, operatore, deleted_at
```

#### `agenda` — Eventi/sessioni
```
id (PK), trainer_id (FK→trainers),
data_inizio, data_fine, categoria ("PT"|"SALA"|"CORSO"|"COLLOQUIO"|"PERSONALE"),
titolo, id_cliente (FK), id_contratto (FK),
stato ("Programmato"|"Completato"|"Cancellato"|"Rinviato"),
note, data_creazione, deleted_at
```

#### `spese_ricorrenti` — Spese fisse
```
id (PK), trainer_id (FK→trainers),
nome, importo, frequenza ("MENSILE"|"SETTIMANALE"|"TRIMESTRALE"|"SEMESTRALE"|"ANNUALE"),
categoria, giorno_scadenza, data_inizio, data_disattivazione,
attiva (bool), note, deleted_at
```

#### `todos` — Checklist
```
id (PK), trainer_id (FK→trainers),
titolo, descrizione, data_scadenza,
completato (bool), completed_at, deleted_at
```

### 3.2 Tabelle Esercizi

#### `esercizi` — Libreria esercizi (~1080 builtin + custom)
```
id (PK), trainer_id (FK, NULL=builtin),
nome (indexed), nome_en,
— Classificazione:
categoria ("compound"|"isolation"|"bodyweight"|"cardio"|"stretching"|"mobilita"|"avviamento"),
pattern_movimento ("squat"|"hinge"|"push_h"|"push_v"|"pull_h"|"pull_v"|"core"|"rotation"|"carry"|"warmup"|"stretch"|"mobility"),
force_type ("push"|"pull"|"static"),
lateral_pattern ("bilateral"|"unilateral"|"alternating"),
— Muscoli (JSON):
muscoli_primari (JSON array), muscoli_secondari (JSON array),
— Setup:
attrezzatura, difficolta ("beginner"|"intermediate"|"advanced"),
— Training:
rep_range_forza, rep_range_ipertrofia, rep_range_resistenza, ore_recupero,
— Contenuto testuale (v2 rich):
descrizione_anatomica, descrizione_biomeccanica, setup, esecuzione,
respirazione, tempo_consigliato, coaching_cues (JSON), errori_comuni (JSON),
note_sicurezza, controindicazioni (JSON),
— Media:
image_url, video_url, muscle_map_url,
— Meta:
is_builtin, created_at, deleted_at
```

#### `esercizi_media` — Media associati
```
id (PK), exercise_id (FK→esercizi), trainer_id (FK),
tipo ("image"|"video"), url, filename, dimensione, created_at
```

#### `esercizi_relazioni` — Progressioni/regressioni/varianti
```
id (PK), exercise_id (FK), related_exercise_id (FK),
tipo ("progression"|"regression"|"variation")
```

### 3.3 Tabelle Schede Allenamento (3-level hierarchy)

#### `schede_allenamento` — Piano allenamento
```
id (PK), trainer_id (FK→trainers), id_cliente (FK→clienti, opzionale),
nome, obiettivo, livello, durata_settimane, sessioni_per_settimana,
note, ai_commentary, created_at, updated_at, deleted_at
```

#### `sessioni_scheda` — Sessione di allenamento
```
id (PK), id_scheda (FK→schede_allenamento),
numero_sessione, nome_sessione, focus_muscolare,
durata_minuti, note
```

#### `esercizi_sessione` — Esercizio nella sessione
```
id (PK), id_sessione (FK→sessioni_scheda), id_esercizio (FK→esercizi),
ordine, serie, ripetizioni, tempo_riposo_sec, tempo_esecuzione, note
```

### 3.4 Tabella Audit
```
audit_log: id (PK), trainer_id (FK), entity_type, entity_id, action, changes_json, created_at
```

### 3.5 Relazioni Chiave (Deep IDOR Chain)

```
Rate → Contract.trainer_id        (2-hop IDOR)
Event → Event.trainer_id          (direct)
WorkoutSession → Plan.trainer_id  (2-hop)
WorkoutExercise → Plan.trainer_id (3-hop)
Contract → Client.trainer_id      (relational IDOR on create)
```

---

## 4. Backend API (`api/`) — ~8,800 LOC

### 4.1 Struttura Directory

```
api/
├── main.py              (117)   App factory, CORS, router registration, lifespan
├── config.py             (42)   DATABASE_URL, JWT_SECRET, API_PREFIX
├── database.py           (55)   SQLModel engine + session factory
├── dependencies.py       (61)   get_current_trainer() — JWT + multi-tenancy
├── seed_exercises.py    (380)   Idempotent seeding 345 esercizi builtin
├── auth/
│   ├── router.py         (80)   POST /auth/register, /auth/login → JWT
│   ├── service.py        (53)   bcrypt hash + JWT HS256 token creation
│   └── schemas.py        (40)   TrainerRegister, TrainerLogin, TokenResponse
├── models/                      11 modelli ORM (SQLModel table=True)
│   ├── trainer.py        (31)   tenant root
│   ├── client.py         (37)   soft-delete
│   ├── contract.py       (59)   relazioni rate/movements
│   ├── rate.py           (51)   Deep IDOR
│   ├── event.py          (44)   direct trainer_id
│   ├── movement.py       (60)   ledger entry
│   ├── recurring_expense.py (41)
│   ├── todo.py           (28)
│   ├── exercise.py       (79)   v2 rich schema, dual ownership
│   ├── exercise_media.py (20)
│   ├── exercise_relation.py (20)
│   ├── workout.py        (68)   3-level hierarchy
│   └── audit_log.py      (33)
├── routers/                     11 router, 60+ endpoint
│   ├── clients.py       (632)   CRUD + batch-enriched list
│   ├── contracts.py     (635)   CRUD + payment history + integrity guards
│   ├── rates.py         (800)   CRUD + pay/unpay atomic + residual validation
│   ├── agenda.py        (601)   CRUD + credit guard + auto-close/reopen
│   ├── movements.py     (831)   Ledger CRUD + pending/confirm + forecast
│   ├── recurring_expenses.py (240)
│   ├── exercises.py     (472)   CRUD + media + relations
│   ├── workouts.py      (605)   CRUD + duplicate + full-replace sessions
│   ├── todos.py         (201)   CRUD + toggle
│   ├── dashboard.py     (627)   7 KPI endpoint
│   └── backup.py        (315)   Backup/restore/export
└── schemas/                     40+ Pydantic DTOs
    ├── financial.py              Contract/Rate/Movement/Dashboard
    ├── exercise.py               Exercise/Media/Relation
    └── workout.py                WorkoutPlan/Session/Exercise
```

### 4.2 Tutti gli Endpoint (60+)

#### Auth (2 endpoint)
- `POST /auth/register` → crea trainer
- `POST /auth/login` → JWT token (HS256, 8h expiry)

#### Clients (5 endpoint)
- `GET /clients` → lista paginata con filtri (stato, situazione), batch-fetch contracts+events
- `GET /clients/{id}` → profilo enriched (5 query batch: KPI, contratti, rate scadute)
- `POST /clients` → crea cliente (Mass Assignment: NO trainer_id)
- `PUT /clients/{id}` → aggiorna (Bouncer IDOR)
- `DELETE /clients/{id}` → soft-delete (RESTRICT se contratti attivi)

#### Contracts (5 endpoint)
- `GET /contracts` → lista paginata, batch CONTRACTS+RATES+CLIENTS
- `GET /contracts/{id}` → enriched con receipt_map (storico pagamenti per rata)
- `POST /contracts` → crea + opzionale acconto (Relational IDOR su id_cliente)
- `PUT /contracts/{id}` → aggiorna (Contract Shortening Guard: rate date validation)
- `DELETE /contracts/{id}` → Delete Guard (zero rate pending + zero crediti residui)

#### Rates (8 endpoint)
- `GET /rates` → lista paginata, JOIN 3 tabelle
- `GET /rates/aging` → Aging Report (bucket 0-30, 30-60, 60-90, 90+)
- `GET /rates/{id}` → singola rata (Deep IDOR: Rate→Contract.trainer_id)
- `POST /rates` → crea rata (residual validation: _cap_rateizzabile)
- `PUT /rates/{id}` → aggiorna (flessibile: date+desc sempre, importo se >= saldato)
- `DELETE /rates/{id}` → soft-delete
- `POST /rates/{id}/pay` → **ATOMICO**: incrementa saldato, aggiorna stato, crea CashMovement, auto-close
- `POST /rates/{id}/unpay` → **ATOMICO**: inverso di pay, soft-delete movement, auto-reopen
- `POST /rates/generate-plan/{contract_id}` → genera piano pagamenti (auto-cap date)

#### Agenda (5 endpoint)
- `GET /agenda` → lista con filtri (categoria, stato, date range)
- `GET /agenda/{id}` → singolo evento
- `POST /agenda` → crea evento (Credit Guard: contratto con crediti esauriti → 400)
- `PUT /agenda/{id}` → aggiorna (_sync_contract_chiuso se stato cambia)
- `DELETE /agenda/{id}` → soft-delete (_sync_contract_chiuso per auto-reopen)

#### Movements (7 endpoint)
- `GET /movements` → ledger paginato con filtri (tipo, categoria, date)
- `GET /movements/stats` → KPI (entrate totali, uscite, balance)
- `GET /movements/pending-expenses` → spese ricorrenti da confermare
- `POST /movements/confirm-expenses` → conferma spese pendenti (dedup key: trainer+spesa+mese_anno)
- `POST /movements` → crea movimento manuale
- `DELETE /movements/{id}` → soft-delete (RESTRICT se id_contratto/id_rata)
- `GET /movements/forecast` → proiezione 3 mesi

#### Recurring Expenses (4 endpoint)
- `GET /recurring_expenses` → lista
- `POST /recurring_expenses` → crea (5 frequenze)
- `PUT /recurring_expenses/{id}` → aggiorna
- `DELETE /recurring_expenses/{id}` → soft-delete (data_disattivazione)

#### Exercises (8 endpoint)
- `GET /exercises` → lista filtrabile (categoria, pattern, attrezzatura)
- `GET /exercises/{id}` → singolo esercizio (builtin o custom)
- `POST /exercises` → crea custom (trainer_id da JWT)
- `PUT /exercises/{id}` → aggiorna solo custom
- `DELETE /exercises/{id}` → soft-delete solo custom
- `POST /exercises/{id}/media` → upload media
- `DELETE /exercises/{id}/media/{media_id}` → elimina media
- `POST/DELETE /exercises/{id}/relations` → relazioni progressione/regressione/variante

#### Workouts (7 endpoint)
- `POST /workouts` → crea scheda (nested: sessioni + esercizi)
- `GET /workouts` → lista con filtri (obiettivo, livello, id_cliente)
- `GET /workouts/{id}` → singola scheda enriched
- `PUT /workouts/{id}` → aggiorna metadata
- `PUT /workouts/{id}/sessions` → **ATOMICO**: full-replace sessioni
- `DELETE /workouts/{id}` → soft-delete (CASCADE sessioni + esercizi)
- `POST /workouts/{id}/duplicate` → clone profonda
- `POST /workouts/{id}/generate-commentary` → AI commentary via Ollama

#### Todos (5 endpoint)
- CRUD standard + `PATCH /todos/{id}/toggle` (toggle completato)

#### Dashboard (7 endpoint)
- `GET /dashboard/summary` → 4 KPI aggregati
- `GET /dashboard/alerts` → warning proattivi
- `GET /dashboard/reconciliation` → audit contratti vs ledger
- `GET /dashboard/ghost-events` → eventi PT senza contratto
- `GET /dashboard/overdue-rates` → rate scadute con risoluzione inline
- `GET /dashboard/expiring-contracts` → contratti in scadenza con crediti
- `GET /dashboard/inactive-clients` → clienti inattivi (no eventi 90gg)

#### Backup (5 endpoint)
- `POST /backup/create` → export completo dati trainer
- `GET /backup/list` → lista backup
- `GET /backup/download/{filename}` → download
- `POST /backup/restore` → restore da backup
- `GET /backup/export` → export JSON real-time

### 4.3 Contract Integrity Engine — 11 Layer Protettivi

Il contratto e' l'entita' centrale. 11 guard lo proteggono:

1. **Residual validation** (`_cap_rateizzabile`): formula `acconto = totale_versato - sum(saldato)`, `cap = prezzo - acconto`
2. **Chiuso guard**: create_rate, generate_plan, create_event rifiutano su contratti chiusi (400)
3. **Overpayment check**: pay_rate verifica importo <= residuo rata E <= cap contratto
4. **Auto-close/reopen** (SIMMETRICO): `chiuso = (SALDATO) AND (crediti_usati >= crediti_totali)`. pay_rate chiude, unpay_rate riapre; create/delete/update evento → _sync_contract_chiuso()
5. **Flexible rate editing**: rate pagate editabili (data/desc sempre, importo se >= saldato, stato auto-ricalcolato)
6. **CashMovement date sync**: modifica scadenza rata → aggiorna data_effettiva movimenti (atomico)
7. **Delete guard**: contratto eliminabile solo se zero rate pending/parziali + zero crediti residui
8. **Credit guard**: create_event rifiuta se crediti_usati >= crediti_totali (400)
9. **Rate date boundary**: data_scadenza rata <= contract.data_scadenza (422)
10. **Contract shortening guard**: update_contract rifiuta se rate oltre nuova data_scadenza (422)
11. **Expired contract detection**: ha_rate_scadute include rate su contratti scaduti

### 4.4 Security Pattern

- **JWT HS256**: token con trainer_id, email, 8h expiry, bcrypt password
- **3-layer auth**: Edge Middleware → AuthGuard client → JWT dependency
- **Deep Relational IDOR**: ogni operazione verifica ownership via FK chain → 404 (mai 403)
- **Mass Assignment Prevention**: schema input senza trainer_id, id, campi computati
- **Soft Delete**: deleted_at su tutte le entita' business
- **Audit Trail**: audit_log traccia tutte le mutazioni
- **Parametrized queries**: SQLModel ORM (zero SQL injection)

---

## 5. Frontend (`frontend/`) — ~20,000 LOC

### 5.1 Struttura Directory

```
frontend/src/
├── app/                           Next.js App Router
│   ├── layout.tsx                 Root layout (fonts, providers)
│   ├── login/page.tsx      (188)  Login pubblico
│   └── (dashboard)/               Route group autenticato
│       ├── layout.tsx             Sidebar + CommandPalette + AuthGuard
│       ├── page.tsx        (799)  Dashboard KPI
│       ├── clienti/
│       │   ├── page.tsx    (451)  Lista clienti + FilterBar
│       │   └── [id]/page.tsx (575) Profilo cliente (header + 5 tab)
│       ├── contratti/
│       │   ├── page.tsx    (483)  Lista contratti (7-level badge)
│       │   └── [id]/page.tsx (371) Dettaglio contratto (FinancialHero)
│       ├── agenda/page.tsx (535)  Calendario DnD
│       ├── cassa/page.tsx  (520)  Finanze (5 tab)
│       ├── esercizi/
│       │   ├── page.tsx    (310)  Lista esercizi
│       │   └── [id]/page.tsx (705) Dettaglio esercizio (MuscleMap SVG)
│       ├── schede/
│       │   ├── page.tsx    (450)  Lista schede
│       │   └── [id]/page.tsx (584) Builder split layout
│       └── impostazioni/page.tsx (325) Backup + account
├── components/
│   ├── auth/AuthGuard.tsx         Route protection (cookie check)
│   ├── layout/
│   │   ├── Sidebar.tsx     (232)  Navigazione + search trigger
│   │   └── CommandPalette.tsx (699) Ctrl+K con preview panel
│   ├── clients/           (6)    ClientsTable, ClientForm, ProfileHeader, ProfileKpi, Delete, Anamnesi
│   ├── contracts/         (8)    ContractsTable, ContractForm, PaymentPlanTab(880!), FinancialHero, RateEdit, RateUnpay
│   ├── agenda/            (8)    AgendaCalendar, CustomToolbar, EventForm, EventHoverCard, calendar-setup
│   ├── dashboard/         (5)    TodoCard, GhostEvents, OverdueRates, ExpiringContracts, InactiveClients
│   ├── exercises/         (5)    ExercisesTable, ExerciseForm, MuscleMap, Sheet, Delete
│   ├── workouts/          (7)    SessionCard, ExerciseSelector, TemplateSelector, WorkoutPreview, DnD, Export, QualityReview
│   ├── movements/         (8)    MovementsTable, MovementForm, RecurringExpenses(760!), Forecast(615), Aging(333), SplitLedger
│   └── ui/               (30)    shadcn/ui primitives (button, dialog, form, select, table, tabs...)
├── hooks/                 (11)   React Query domain hooks
│   ├── useClients.ts      (144)  GET + CRUD
│   ├── useContracts.ts    (133)  GET + CRUD + payment history
│   ├── useRates.ts        (186)  CRUD + pay/unpay + aging
│   ├── useAgenda.ts       (185)  Events + hydration
│   ├── useMovements.ts    (179)  Ledger + forecast + pending
│   ├── useWorkouts.ts     (211)  CRUD + duplicate + commentary
│   ├── useExercises.ts    (227)  CRUD + media + relations
│   ├── useDashboard.ts    (100)  Summary + alerts (refetch 60s)
│   ├── useRecurringExpenses.ts (106)
│   ├── useTodos.ts         (89)
│   └── useBackup.ts       (120)
├── lib/
│   ├── api-client.ts              Axios + JWT interceptor + dynamic baseURL
│   ├── format.ts                  formatCurrency, toISOLocal, formatShortDate, formatDateTime, getFinanceBarColor
│   ├── auth.ts                    login/logout + cookie management
│   ├── contraindication-engine.ts (250) Motore scudo anamnesi → safe/caution/avoid
│   ├── workout-templates.ts       3 template (Beginner/Intermedio/Avanzato) + getSectionForCategory
│   ├── workout-quality-engine.ts  AI commentary via Ollama
│   ├── export-workout.ts          Excel (exceljs) + PDF (@media print)
│   ├── muscle-map-utils.ts        SVG utilities
│   ├── providers.tsx              QueryClient + ThemeProvider + Toaster
│   └── utils.ts                   shadcn cn()
├── types/
│   └── api.ts             (900+) TypeScript interfaces mirroring Pydantic
└── middleware.ts                  Edge Middleware auth redirects
```

### 5.2 Pagine e Route (13 pagine)

| Route | LOC | Funzionalita' |
|-------|-----|---------------|
| `/` | 799 | Dashboard: 6 KPI cards + Alert Panel + Aging + eventi oggi |
| `/login` | 188 | Login pubblico con JWT |
| `/clienti` | 451 | Lista clienti + FilterBar (Stato + Situazione) + inline creation |
| `/clienti/[id]` | 575 | Profilo: header + 5 tab (Panoramica, Contratti, Sessioni, Movimenti, Schede) |
| `/contratti` | 483 | Lista contratti, 7-level badge, scadenza color-coded |
| `/contratti/[id]` | 371 | Dettaglio: FinancialHero + PaymentPlanTab + sessioni + dettagli |
| `/agenda` | 535 | Calendario react-big-calendar + DnD + FilterBar + RangeStatsBar |
| `/cassa` | 520 | Finanze: 5 tab (Libro Mastro, Spese Fisse, Entrate&Uscite, Aging, Previsioni) |
| `/esercizi` | 310 | Lista esercizi + filtri + CRUD custom |
| `/esercizi/[id]` | 705 | Dettaglio: MuscleMap SVG hero + form + media + relazioni |
| `/schede` | 450 | Lista schede + filtro obiettivo/livello/cliente |
| `/schede/[id]` | 584 | Builder: split layout (editor sinistra, preview destra) |
| `/impostazioni` | 325 | Backup management + account settings |

### 5.3 Componenti Chiave

#### PaymentPlanTab (880 LOC) — Componente piu' complesso
- Tabella rate con CRUD inline
- PayRateForm: quick buttons ("Tutto", "50%"), smart date default, residuo helper, grid 3 colonne
- PaymentHistory per rata (collapsible, cronologico, badge emerald/amber)
- AddRateForm + GeneratePlanForm

#### CommandPalette (699 LOC) — Feature distintiva
- Ctrl+K apre ricerca fuzzy globale
- Preview panel (desktop): info live dell'elemento selezionato
- Risposte KPI dirette: digiti "entrate" e vedi il numero inline
- Azioni contestuali: la palette sa dove sei e suggerisce azioni
- Lazy-loaded via React Query (`enabled: open`)

#### RecurringExpensesTab (760 LOC) — Conferma & Registra
- PendingExpensesBanner con checkbox + conferma
- ExpenseEditDialog con 6 campi
- Selection con Set<string> chiave composta `${id}::${key}`

#### ForecastTab (615 LOC) — Proiezione finanziaria
- 4 KPI gradient cards (entrate, uscite, burn rate, margine)
- AreaChart (3 curve: entrate, uscite, stimate)
- Runway chart con saldo cumulativo

#### ExerciseSelector (456 LOC) — Selezione esercizi professionale
- Chip filter pattern_movimento + attrezzatura (solo sezione principale)
- Filtro categoria automatico per sezione (avviamento/stretching/principale)
- Badge controindicazione (rosso/ambra) con motivo
- Toggle "Filtra" safety (OFF default — trainer decide sempre)

#### TemplateSelector (419 LOC) — Template intelligenti
- 3 template (Beginner/Intermedio/Avanzato)
- Smart matching multi-dimensionale (+10 difficulty, +8 muscle overlap, +3 compound, -15 caution, filter avoid)
- Selezione cliente integrata + banner anamnesi

#### MuscleMap — SVG interattivo
- Highlight muscoli primari/secondari su body map
- Responsive hero section nella pagina esercizio

#### Contraindication Engine (250 LOC) — Scudo anamnesi
- Motore deterministico frontend-only (zero latenza)
- extractTagsFromAnamnesi(): 30+ keyword italiani → 11 body part tags + 3 medical flags
- classifyExercise(): ibrido (DB controindicazioni + regole pattern/muscoli)
- **Filosofia**: INFORMARE mai LIMITARE — il trainer (laureato scienze motorie) decide SEMPRE

### 5.4 Pattern React Query

Ogni hook module segue la struttura:
```typescript
useEntities()              // GET lista
useEntity(id)              // GET singolo
useCreateEntity()          // POST (mutation)
useUpdateEntity()          // PUT (mutation)
useDeleteEntity()          // DELETE (mutation)
```

Ogni mutation invalida query correlate + mostra toast (sonner).
Operazioni inverse (pay/unpay) hanno invalidazione IDENTICA.

### 5.5 Visual Identity

- **Teal accent**: oklch hue 170 (light `oklch(0.55 0.15 170)`, dark `oklch(0.70 0.15 170)`)
- **Background**: warm off-white / warm charcoal
- **Radius**: 0.75rem (angoli morbidi)
- **KPI**: font-extrabold + tracking-tighter + tabular-nums
- **Card hover**: transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg
- **Badge 7 livelli contratti**: Chiuso > Insolvente > Rate in Ritardo > Scaduto > Saldato > In corso > Nessuna rata

### 5.6 Dipendenze Principali

```
next 16.1.6, react 19.2.3, typescript 5
@tanstack/react-query 5.90.21
react-hook-form 7.71.2, zod 4.3.6
axios 1.13.5, date-fns 4.1.0
recharts 2.15.4, sonner 2.0.7
cmdk 1.1.1, react-big-calendar 1.19.4
@dnd-kit/core 6.3.1, @dnd-kit/sortable 10.0.0
exceljs 4.4.0, lucide-react 0.575.0
radix-ui 1.4.3, next-themes 0.4.6
```

---

## 6. Core — Moduli AI Dormant (~6,900 LOC)

```
core/
├── exercise_archive.py     (1,132)  Archive esercizi + scored selection
├── card_parser.py          (1,092)  Parse schede da PDF/IMG (OCR Ollama)
├── financial_analytics.py    (699)  Cash flow + forecasting + risk
├── periodization_models.py   (688)  5 modelli periodizzazione
├── models.py                 (681)  Domain models (legacy)
├── workout_generator.py      (458)  3 modi: archive|dna|combined
├── workout_ai_pipeline.py    (383)  Pipeline AI workout generation
├── session_template.py       (341)  Session templates (slot-based)
├── pattern_extractor.py      (328)  Pattern recognition
├── knowledge_chain.py        (302)  RAG chain (LLMs)
├── error_handler.py          (284)  Logging + error strategies
├── methodology_chain.py      (171)  Trainer methodology extraction
├── db_migrations.py          (108)  Legacy migration helpers
├── document_manager.py        (82)  PDF/image handling
├── constants.py               (80)  Enums (allineate a api/)
├── config.py                  (72)  Ollama endpoint, DB path
└── repositories/                    9 repository legacy (sqlite3 raw)
    ├── financial_repository.py      15+ metodi, dict raw (DEBITO ALTO)
    ├── card_import_repository.py    Card parsing
    ├── workout_repository.py        Workout storage
    ├── exercise_archive.py          Exercise queries
    ├── client_repository.py         Client queries
    ├── contract_repository.py       Contract queries
    ├── trainer_dna_repository.py    Trainer DNA
    ├── agenda_repository.py         Agenda queries
    └── assessment_repository.py     Assessment data
```

**Stato**: Completamente dormant. Nessun endpoint API li chiama.
**Piano**: Fase 2 del progetto — esporre via REST endpoint:
- `POST /workouts/ai-generate` → WorkoutGenerator
- `POST /workouts/import-card` → CardParser
- `GET /dashboard/forecast-ai` → FinancialAnalytics

**Debito tecnico**: 9 repository usano sqlite3 raw → migrare a SQLModel ORM.

---

## 7. Tools & Infrastructure

### 7.1 Shell Scripts (`tools/scripts/`)

| Script | Funzione |
|--------|----------|
| `migrate-all.sh` | Alembic su ENTRAMBI i DB (crm.db + crm_dev.db), verifica allineamento |
| `kill-port.sh` | Kill pulito processo + figli (risolve zombie uvicorn Windows) |
| `restart-backend.sh dev\|prod` | Kill + restart uvicorn con DB/porta corretti |

### 7.2 Admin Scripts (`tools/admin_scripts/`)

#### Database & Seed
| Script | Funzione |
|--------|----------|
| `reset_production.py` | Reset DB prod (solo Chiara) — **PERICOLOSO** |
| `seed_dev.py` | Popola crm_dev.db con 50 clienti realistici |
| `seed_realistic.py` | Engine seed: 50 clienti, 60 contratti, 900 eventi, 700 movimenti (1 anno) |
| `setup_chiara.py` | Setup iniziale trainer (idempotente) |

#### Exercise Quality Engine — Pipeline 6 Fasi
| Script | Fase | Funzione |
|--------|------|----------|
| `fix_exercise_data_v2.py` | 0 | Pulizia deterministica (punteggiatura, duplicati, misclassificazioni) |
| `fix_exercise_names.py` | 1 | Correzione nomi italiani (manual + Ollama + term substitutions) |
| `translate_fdb_instructions.py` | 2A | Traduzione istruzioni FDB EN→IT (preserva step-by-step) |
| `upgrade_exercise_instructions.py` | 2B | Upgrade esecuzione originali in formato step-by-step |
| `enrich_exercise_fields.py` | 3 | Enrichment campi descrittivi (category-aware, Ollama) |
| `backfill_exercise_fields.py` | 4 | Backfill note_sicurezza + force_type/lateral_pattern |
| `verify_exercise_quality.py` | 5 | Audit qualita' finale (coverage, lingua, duplicati, enum) |

#### Import & Enrichment
| Script | Funzione |
|--------|----------|
| `import_fdb_new_exercises.py` | Import esercizi da free-exercise-db |
| `populate_exercises.py` | Enrichment Ollama (descrizioni, istruzioni, errori) |
| `fdb_mapping.py` | Mapping FDB → DB (muscoli, categorie, pattern) |
| `fdb_diagnostic.py` | Diagnostica dati FDB |

#### Test E2E (richiede API avviato)
| Script | Copertura |
|--------|-----------|
| `test_crud_idor.py` | CRUD + Deep IDOR + Mass Assignment su tutti i router |
| `test_financial_idor.py` | Contratti + Rate + pagamenti atomici + IDOR finanziario |
| `test_agenda_idor.py` | Eventi + auto-close/reopen + SlotGrid + IDOR agenda |
| `test_ledger_dashboard.py` | Ledger integrity + Dashboard KPI |

### 7.3 Alembic (Database Migration)

```
alembic/
├── env.py                 Legge DATABASE_URL da environment (fallback alembic.ini)
└── versions/              11 migrazioni
    ├── initial_schema_stamp
    ├── soft_delete_unique_index
    ├── data_inizio_cleanup_legacy
    ├── esercizi_table (345 builtin)
    ├── enrich_esercizi_v2
    ├── workout_plan_tables (3 tabelle)
    ├── note_interne_to_clienti
    ├── todos_table
    ├── ai_commentary_to_schede
    └── muscle_map_url_to_exercises
```

**Regola**: SEMPRE `bash tools/scripts/migrate-all.sh` — MAI `alembic upgrade head` da solo.

---

## 8. Dual Environment

```
PRODUZIONE (Chiara — dati reali, sempre acceso):
  Backend:  porta 8000  →  data/crm.db
  Frontend: porta 3000  →  next start -p 3000 -H 0.0.0.0
  LAN:      http://192.168.1.23:3000
  Tailscale: http://100.127.28.16:3000

SVILUPPO (gvera — dati test, esperimenti liberi):
  Backend:  porta 8001  →  data/crm_dev.db
  Frontend: porta 3001  →  next dev
  Accesso:  http://localhost:3001
```

**API URL dinamico**: il frontend deduce l'API URL da `window.location` a runtime:
- hostname:3000 → hostname:8000/api (prod)
- hostname:3001 → hostname:8001/api (dev)

**Tailscale VPN**: Chiara accede da qualsiasi rete (P2P crittografato, WireGuard).

**Credenziali**:
| Ambiente | Email | Password |
|----------|-------|----------|
| PROD | chiarabassani96@gmail.com | chiarabassani |
| DEV | chiarabassani96@gmail.com | Fitness2026! |

---

## 9. Design Pattern Consolidati

### Backend
1. **Bouncer Pattern**: validate precondizioni → exit subito → flusso piatto (max 2 nesting)
2. **Deep Relational IDOR**: verifica ownership via FK chain → 404 (mai 403)
3. **Atomic Transactions**: single session.commit() per operazioni multi-tabella
4. **Batch Fetch anti-N+1**: 4 query (contratti, rate, clienti, eventi) → enrich in memoria
5. **Mass Assignment Prevention**: schema input senza campi protetti
6. **Computed on Read**: crediti_usati calcolati da GROUP BY eventi, mai stored
7. **Soft Delete**: deleted_at su tutte le entita' business

### Frontend
1. **React Query + Toast**: useQuery per lettura, useMutation per scrittura, toast su ogni mutation
2. **Invalidation simmetrica**: operazioni inverse (pay/unpay) invalidano le stesse query
3. **Type Synchronization**: Pydantic → TypeScript (api/schemas ↔ types/api.ts)
4. **FilterBar 2 assi**: Set<string> per categorie + Set<string> per stati (riusato su 4 pagine)
5. **Select nullable**: sentinel `"__none__"` per null (Radix Select non accetta value="")
6. **createPortal escape**: popup sopra overflow:hidden (EventHoverCard → body, position:fixed)
7. **Config-driven KPI**: array KPIS + .map() (zero copy-paste)
8. **Smart date default**: scadenza <= oggi ? scadenza : oggi (rate arretrate)

---

## 10. Testing

### Unit Tests (pytest, 63 test)
```bash
pytest tests/ -v
```
- test_pay_rate, test_unpay_rate (pagamenti atomici)
- test_rate_guards (editing flessibile, residual)
- test_contract_integrity (auto-close, delete guard, credit guard)
- test_soft_delete_integrity (restrict, stats filtered)
- test_sync_recurring (dedup, cross-year)
- test_aging_report (bucket assignment)

Database: SQLite in-memory (StaticPool, isolato per test).

### E2E Tests (67 scenari, server richiesto)
```bash
python tools/admin_scripts/test_crud_idor.py
python tools/admin_scripts/test_financial_idor.py
python tools/admin_scripts/test_agenda_idor.py
python tools/admin_scripts/test_ledger_dashboard.py
```

---

## 11. Libreria Esercizi — ~1080 Esercizi

### Composizione
- **345 originali** (id 1-345): 265 principale + 26 avviamento + 27 stretching + 27 mobilita
- **~735 FDB** (id 346+): importati da free-exercise-db, classificati e tradotti

### 7 Categorie
`compound`, `isolation`, `bodyweight`, `cardio`, `stretching`, `mobilita`, `avviamento`

### 12 Pattern Movimento
9 forza: `squat`, `hinge`, `push_h`, `push_v`, `pull_h`, `pull_v`, `core`, `rotation`, `carry`
3 complementari: `warmup`, `stretch`, `mobility`

### Schede Allenamento — 3 Sezioni per Sessione
1. **Avviamento**: categoria avviamento, pattern warmup
2. **Principale**: compound/isolation/bodyweight/cardio
3. **Stretching & Mobilita'**: stretching/mobilita, stretching mirato ai muscoli lavorati

### Exercise Quality Engine — Pipeline 6 Fasi (IN CORSO)
| Fase | Stato | Cosa fa |
|------|-------|---------|
| 0. Pulizia deterministica | Completata | Punteggiatura, duplicati, misclassificazioni |
| 1. Correzione nomi | In corso | Manual overrides + Ollama re-translation |
| 2A. Traduzione istruzioni | Prossima | FDB EN→IT preservando step-by-step |
| 2B. Upgrade esecuzione | Pending | Originali → formato step-by-step |
| 3. Enrichment descrittivi | Pending | Anatomia, biomeccanica, setup, cues, errori |
| 4. Backfill safety | Pending | note_sicurezza + force_type/lateral_pattern |
| 5. Verifica finale | Pending | Audit completezza + lingua + duplicati |

---

## 12. Metriche Progetto

| Metrica | Valore |
|---------|--------|
| **LOC totali** | ~40,000 |
| **api/** | ~8,800 LOC Python |
| **frontend/** | ~20,000 LOC TypeScript |
| **core/** | ~6,900 LOC Python |
| **tools/** | ~4,000 LOC Python/Bash |
| **Modelli ORM** | 11 |
| **Router REST** | 11 |
| **Endpoint** | 60+ |
| **Schema Pydantic** | 40+ |
| **Tabelle DB** | 23 |
| **Pagine frontend** | 13 |
| **Componenti React** | ~80 |
| **Hook React Query** | 11 moduli |
| **Test pytest** | 63 |
| **Test E2E** | 67 scenari |
| **Esercizi builtin** | ~1080 |

---

## 13. Debito Tecnico Noto

| Priorita' | Issue | Impatto |
|-----------|-------|---------|
| ALTO | FinancialRepository legacy (15+ metodi dict raw) | Manutenibilita' |
| ALTO | CardImportRepository legacy | Manutenibilita' |
| MEDIO | 9 repository legacy (sqlite3 raw) in core/ | Core non puo' usare nuovo API layer |
| MEDIO | core/ dormant (no API exposure) | Codice morto, ~7000 LOC inutilizzate |
| BASSO | tests/legacy/ rotti | Non possono girare in CI |

---

## 14. Roadmap Prossimi Step

### Fase attuale: Exercise Quality Engine
Pipeline 6 fasi per portare ~1080 esercizi a qualita' commerciale. Dettagli in CLAUDE.md.

### Fase successiva: API AI Endpoints
- Esporre core/ via REST: `/workouts/ai-generate`, `/workouts/import-card`, `/dashboard/forecast-ai`
- Migrare repository legacy a SQLModel ORM

### Futuro
- PostgreSQL migration (cambio solo `DATABASE_URL`)
- Async support (core/ → async/await + Celery per long-running)
- Multi-trainer (oggi single-tenant prod, multi-tenant predisposto)

---

## 15. Comandi Rapidi

```bash
# ── Avvio ──
# Dev:
DATABASE_URL=sqlite:///data/crm_dev.db uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
cd frontend && npm run dev                              # porta 3001

# Prod:
uvicorn api.main:app --host 0.0.0.0 --port 8000
cd frontend && npm run build && npm run prod            # porta 3000

# ── Gestione ──
bash tools/scripts/migrate-all.sh                       # Alembic su entrambi i DB
bash tools/scripts/kill-port.sh 8000                    # Kill pulito
bash tools/scripts/restart-backend.sh dev|prod          # Kill + restart

# ── Test ──
cd frontend && npx next build                           # Build check
pytest tests/ -v                                        # 63 test
python tools/admin_scripts/test_crud_idor.py            # E2E

# ── Seed ──
python -m tools.admin_scripts.seed_dev                  # 50 clienti test
```

---

*Questo documento cattura l'architettura completa di FitManager AI Studio al 26 Febbraio 2026.*
*Per le regole di sviluppo e i pattern obbligatori, riferirsi a `CLAUDE.md` (la legge del progetto).*
