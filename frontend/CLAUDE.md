# Frontend Layer — React Rules

Next.js 16 + React 19 + TypeScript 5 + shadcn/ui + Tailwind CSS 4.

## Architettura

```
frontend/src/
├── app/                     Next.js App Router
│   ├── (dashboard)/         Route group (non appare in URL)
│   │   ├── layout.tsx       Sidebar + AuthGuard wrapper
│   │   ├── page.tsx         Dashboard KPI
│   │   ├── clienti/         Pagina clienti + [id]/ scheda cliente
│   │   ├── contratti/       Pagina contratti + [id]/ scheda contratto
│   │   ├── agenda/          Pagina agenda/calendario
│   │   ├── cassa/           Pagina Cassa (5 tab: Libro Mastro, Spese Fisse, Entrate & Uscite, Scadenze, Previsioni)
│   │   ├── esercizi/        Pagina esercizi + [id]/ scheda esercizio (MuscleMap SVG hero)
│   │   └── impostazioni/   Pagina impostazioni
│   ├── login/page.tsx       Login pubblico
│   └── layout.tsx           Root layout (Providers, fonts)
├── components/
│   ├── auth/AuthGuard.tsx   Client-side route protection
│   ├── layout/
│   │   ├── Sidebar.tsx      Navigazione sezioni + trainer info + search trigger
│   │   └── CommandPalette.tsx  Ctrl+K — preview panel + KPI + azioni contestuali
│   ├── clients/             Componenti dominio clienti
│   ├── contracts/           Componenti dominio contratti (PaymentPlanTab con
│   │                        RateCard, PayRateForm, PaymentHistory, AddRateForm)
│   ├── agenda/              Componenti dominio agenda/calendario
│   │                        (AgendaCalendar, CustomToolbar, CustomEvent,
│   │                         EventHoverCard, EventSheet, EventForm,
│   │                         DeleteEventDialog, calendar-setup.ts)
│   ├── dashboard/           Componenti dashboard (TodoCard, GhostEventsSheet,
│   │                        OverdueRatesSheet, ExpiringContractsSheet, InactiveClientsSheet)
│   ├── exercises/           Componenti dominio esercizi (ExercisesTable, ExerciseSheet,
│   │                        ExerciseForm, DeleteExerciseDialog, MuscleMap, exercise-constants)
│   ├── movements/           Componenti dominio cassa (MovementsTable, MovementSheet,
│   │                        DeleteMovementDialog, RecurringExpensesTab (con EditDialog,
│   │                        AddForm, ExpensesTable, AlertDialog delete confirm),
│   │                        SplitLedgerView, AdvancedFilters, LedgerColumn, AgingReport,
│   │                        ForecastTab (KPI + AreaChart + Runway + Timeline))
│   └── ui/                  shadcn/ui primitives
├── hooks/                   React Query hooks (1 per dominio)
├── lib/
│   ├── api-client.ts        Axios + JWT interceptor + extractErrorMessage
│   ├── auth.ts              Login/logout/cookie management
│   ├── format.ts            formatCurrency + toISOLocal centralizzati
│   └── providers.tsx        QueryClientProvider
└── types/
    └── api.ts               TypeScript interfaces (mirror Pydantic)
```

## Pattern Obbligatori

### Hook per dominio
Un file hook per ogni dominio. Struttura:
```typescript
// useClients.ts
export function useClients() { return useQuery({...}) }            // READ (tutti, filtro client-side)
export function useCreateClient() { return useMutation({...}) }    // CREATE
export function useUpdateClient() { return useMutation({...}) }    // UPDATE
export function useDeleteClient() { return useMutation({...}) }    // DELETE
```
Ogni mutation: `invalidateQueries` sulle key correlate + `toast.success/error`.

### Query Key Convention
```typescript
["clients"]                          // lista tutti (filtro client-side)
["client", clientId]                 // dettaglio singolo
["contracts", { page, idCliente }]  // lista filtrata
["contract", contractId]             // dettaglio con rate
["movements", { anno, mese }]       // lista mensile
["movement-stats", anno, mese]      // KPI mensili (entrate, uscite, margine)
["aging-report"]                     // orizzonte finanziario (scadenze)
["dashboard", "summary"]             // KPI aggregati
["dashboard", "alerts"]              // warning proattivi (4 categorie)
["dashboard", "ghost-events"]        // eventi fantasma per risoluzione inline
["dashboard", "overdue-rates"]       // rate scadute per pagamento inline
["dashboard", "expiring-contracts"]  // contratti in scadenza con crediti
["dashboard", "inactive-clients"]    // clienti inattivi con ultimo evento
["events", { start, end }]          // eventi per range temporale
["events", { idCliente }]           // eventi per cliente (profilo)
["events", { idContratto }]         // eventi per contratto (scheda)
["exercises", categoryOrUndefined]   // lista esercizi (filtro categoria opzionale)
["exercise", exerciseId]             // dettaglio singolo esercizio
["forecast", { mesi }]              // proiezione finanziaria N mesi
["todos", { completato }]           // lista todo (filtro opzionale)
```

### Invalidazione Simmetrica (Regola Ferrea)
Operazioni inverse (pay/unpay, create/delete) DEVONO invalidare le stesse query.
Se `useUnpayRate` invalida `["movements"]`, allora `usePayRate` DEVE fare lo stesso.
Ogni mutation che crea/modifica CashMovement deve invalidare: `["movements"]`, `["movement-stats"]`, `["aging-report"]`.

### Type Synchronization
`frontend/src/types/api.ts` e' il CONTRATTO tra frontend e backend.
Ogni campo `Optional[X]` in Pydantic → `X | null` in TypeScript.
```python
# Backend (api/schemas/financial.py)
class ContractResponse(BaseModel):
    prezzo_totale: Optional[float] = None
```
```typescript
// Frontend (src/types/api.ts)
export interface Contract {
    prezzo_totale: number | null;
}
```

### Componente Page Pattern
```typescript
export default function PageName() {
  const [sheetOpen, setSheetOpen] = useState(false);
  const { data, isLoading, isError, refetch } = useQuery();

  // Handlers
  const handleCreate = () => { ... };

  return (
    <div className="space-y-6">
      {/* Header con titolo + bottone azione */}
      {isLoading && <Skeleton />}
      {isError && <ErrorBanner onRetry={refetch} />}
      {data && <DataTable items={data.items} />}
      {/* Sheet/Dialog modali */}
    </div>
  );
}
```

### Pagamento Guidato (PayRateForm)
Il form pagamento rata guida l'utente verso pagamenti parziali:
- **Quick buttons**: "Tutto (€X)" e "50%" per compilare l'importo velocemente
- **Helper text**: mostra il residuo e spiega che il parziale e' possibile
- **Validazione max**: importo > residuo → errore rosso + bottone disabilitato
- **Label dinamica**: "Paga €X (parziale)" vs "Paga €X (saldo)"
- **Smart Date Default**: `scadenza <= oggi ? scadenza : oggi` — rate arretrate usano la data scadenza come default, rate future usano oggi. DatePicker sempre visibile per override manuale.
- **Grid 3 colonne**: `grid-cols-1 sm:grid-cols-3` (importo, metodo, data)

### Modifica Rate Pagate (RateEditDialog)
Rate SALDATE e PARZIALI sono modificabili con vincoli smart:
- **Info banner blu**: mostra importo gia' versato quando la rata ha pagamenti
- **Campi sempre editabili**: `data_scadenza`, `descrizione`
- **Importo condizionato**: `importo_previsto` editabile se >= importo_saldato (errore rosso se sotto)
- **Min validation**: attributo HTML `min={importo_saldato}` + messaggio esplicito
- **Dropdown azioni**: "Modifica" visibile su TUTTE le rate, "Revoca" su pagate, "Elimina" su non pagate

### Storico Pagamenti (PaymentHistory)
Ogni rata con pagamenti mostra la lista cronologica completa:
- Icone colorate: emerald (SALDATA), amber (PARZIALE)
- Collapsible: mostra max 2, "Mostra altri N" se > 2
- Summary: "Totale versato: €X / €Y" con multipli pagamenti

### Spese Ricorrenti — Conferma & Registra (RecurringExpensesTab)
Paradigma esplicito: le spese ricorrenti non vengono create automaticamente.
L'utente vede un banner con le spese in attesa e le conferma manualmente.

Componente con 4 sotto-componenti inline:
- **PendingExpensesBanner**: banner gradient arancione con checkbox per spesa, "Seleziona tutte", "Conferma selezionate".
  Usa `usePendingExpenses(anno, mese)` + `useConfirmExpenses()`. Reset selezione su cambio mese.
  **Selezione**: `Set<string>` con chiave composta `${id_spesa}::${mese_anno_key}` (MAI solo `mese_anno_key` —
  spese diverse dello stesso mese condividono la stessa key, il Set le collassa).
  **PendingItemRow**: usa `<div onClick={onToggle}>` + `Checkbox onClick={stopPropagation}`.
  MAI `<label>` con Radix Checkbox (causa double-toggle: browser propaga click a form control interno).
- **AddExpenseForm**: form creazione con Select categoria, frequenza (5 opzioni), DatePicker `data_inizio` ("Attiva dal")
- **ExpenseEditDialog**: Dialog con useEffect state sync da props, 6 campi (+ data_inizio via DatePicker)
- **ExpensesTable**: tabella con colonne Categoria, Frequenza, Giorno, Attiva dal, Stato + Edit/Toggle/Delete
- **KPI pesato**: "Stima Mensile Spese Fisse" con `estimateMonthly()` che pesa per frequenza
  (SETTIMANALE ×4.33, TRIMESTRALE /3, SEMESTRALE /6, ANNUALE /12)
- Props: riceve `anno` e `mese` da `cassa/page.tsx`
- Badge tab: `cassa/page.tsx` mostra badge numerico pending sul tab "Spese Fisse"

### Badge Contratti (7 livelli priorita')
`getPaymentBadge()` in `ContractsTable.tsx` — scala priorita' fissa:
1. **Chiuso** (zinc secondary) — contratto chiuso
2. **Insolvente** (red-600 solid white) — `ha_rate_scadute && isExpired` — caso peggiore
3. **Rate in Ritardo** (red-100) — `ha_rate_scadute` senza contratto scaduto
4. **Scaduto** (amber-100) — `data_scadenza < oggi` senza rate scadute
5. **Saldato** (emerald-100) — `totale_versato >= prezzo_totale`
6. **In corso (X/Y)** (blue-100) — rate in progress
7. **Nessuna rata** (zinc-100) — default

Colonna Scadenza: color-coded con `getScadenzaStyle()` (red < 0gg, amber < 7gg, amber-light < 30gg).

### FilterBar Clienti (pattern Agenda)
Stessa architettura `Set<string>` + chip toggle dell'Agenda, applicata a Clienti:
- **Riga 1 (Stato)**: Attivi (emerald) · Inattivi (zinc) — filtro `client.stato`
- **Riga 2 (Filtro)**: Con Rate Scadute (red) · Con Crediti (blue) — filtro enriched fields
- Filtraggio interamente client-side — `useClients()` carica tutti (page_size=200)
- Colonna **Finanze**: progress bar compatta `versato / prezzo_totale_attivo` (emerald >= 80%, amber >= 40%, red < 40%)

### DatePicker maxDate (Boundary Protection)
`DatePicker` accetta `maxDate?: Date` → passa come `toDate` al Calendar (react-day-picker).
Blocca navigazione e selezione oltre la data. Applicato a:
- `RateEditDialog` (via `contractScadenza` prop)
- `GeneratePlanForm` (data prima rata)
- `AddRateForm` (data scadenza rata manuale)

### Azioni Distruttive — 2 livelli
- **CRITICA** (delete contratto, revoca pagamento): AlertDialog + conferma testuale ("ANNULLA")
- **MEDIA** (delete rata, delete movimento): AlertDialog standard con 2 bottoni

### Utility centralizzate (`lib/format.ts`)
```typescript
import { formatCurrency, toISOLocal } from "@/lib/format";
```
- `formatCurrency(amount)` — formatta EUR italiana ("€ 1.200,00")
- `toISOLocal(date)` — ISO string in ora locale SENZA suffisso "Z".
  Critico per D&D e form: `toISOString()` converte in UTC perdendo l'offset
  fuso orario (es. 12:00 CET → 11:00Z). Il backend salva datetime naive,
  quindi DEVE ricevere l'ora locale. MAI usare `toISOString()` per payload API.

### Error Handling
```typescript
import { extractErrorMessage } from "@/lib/api-client";
// In ogni mutation onError:
onError: (error) => {
  toast.error(extractErrorMessage(error, "Messaggio fallback"));
}
```
Estrae `error.response.data.detail` dal backend FastAPI, mostra il messaggio reale all'utente.

## Responsive Design (Mobile-first)

L'app e' ottimizzata per 3 viewport: mobile (375px+), tablet (768px+), desktop (1024px+).
Approccio mobile-first con breakpoints Tailwind (`sm:`, `md:`, `lg:`). Zero librerie extra.

### Pattern consolidati

| Pattern | Classi Tailwind | Dove usato |
|---------|----------------|------------|
| Form grid stacking | `grid grid-cols-1 sm:grid-cols-2` | ClientForm, ContractForm, EventForm, ExpenseEditDialog |
| Hide colonne tabella | `hidden sm:table-cell`, `hidden md:table-cell`, `hidden lg:table-cell` | Tutte le tabelle (Clienti, Contratti, Movimenti, Spese) |
| Header page stacking | `flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between` | clienti, contratti, cassa |
| Icon-only button mobile | `<span className="hidden sm:inline">Label</span>` | Tutti i bottoni "Nuovo X" + tab Cassa |
| Tabs scrollabili | `w-full overflow-x-auto` su TabsList | Cassa (5 tab) |
| Chart ridotto | `h-[200px] sm:h-[280px]` | Cassa chart |
| KPI compatti | `text-lg sm:text-2xl` + `h-8 w-8 sm:h-10 sm:w-10` | Dashboard, Cassa |
| Calendar viewport | `minHeight: "calc(100vh - 280px)"` | AgendaCalendar |
| Toolbar flex-wrap | `flex-wrap` + `order-` per riordino mobile | CustomToolbar |
| Login card | `max-w-sm sm:max-w-md` | login/page.tsx |
| Backup table compact | `hidden sm:table-cell` su Dimensione/Data + azioni icon-only | impostazioni/page.tsx |

### CSS mobile overrides (globals.css)
```css
@media (max-width: 640px) {
  .rbc-header { font-size: 0.7rem; }
  .rbc-event { font-size: 0.7rem; }
  .rbc-time-content { font-size: 0.75rem; }
  .rbc-label { font-size: 0.7rem; }
}
```

### Regole
- **Mai width fissi** su mobile — usare `w-full`, `min-w-0`, classi responsive
- **colSpan={99}** per row separatrici (copre qualsiasi numero di colonne visibili)
- **Tabelle**: su mobile mostrare solo 3-4 colonne essenziali, le altre `hidden md:table-cell`
- **Layout sidebar**: gia' responsive (hamburger su mobile, sidebar full su desktop) — NON toccare

## Convenzioni

- Lingua UI: **italiano** (labels, toast, placeholder)
- Lingua codice: **inglese** (nomi variabili, funzioni, commenti)
- Nomi dominio: **italiano** nei tipi API (`id_cliente`, `data_scadenza`)
- CSS: Tailwind utilities, ZERO CSS custom (tranne globals.css per theme + mobile overrides)
- Icone: lucide-react (consistente con shadcn/ui)
- Toast: sonner (`toast.success`, `toast.error`)
- Date: date-fns con locale `it` per display, `toISOLocal()` per payload API (MAI `toISOString()`)

## Auth (3 layer)

1. **Edge Middleware** (`middleware.ts`): intercetta route prima del render
2. **AuthGuard** (`components/auth/AuthGuard.tsx`): check cookie client-side
3. **API interceptor** (`lib/api-client.ts`): JWT header + redirect su 401 (skip se gia' su `/login`)

Token in cookie `fitmanager_token` (8h expiry). Trainer data in `fitmanager_trainer`.

## Pitfalls — Errori Reali, Mai Ripeterli

| Pitfall | Causa | Fix |
|---------|-------|-----|
| `<label>` + Radix Checkbox | Browser propaga click al `<button>` interno → double-toggle | `<div onClick>` + `Checkbox onClick={stopPropagation}` |
| `Set<string>` non-univoca | `mese_anno_key` uguale per N spese mensili stesso mese | Chiave composta `${id}::${key}` |
| React `key={nonUniqueValue}` | Duplica render, stato condiviso tra componenti | Sempre key univoca per item |
| Invalidation asimmetrica | `usePayRate` mancava movements/stats → KPI stale dopo pagamento | Operazioni inverse: stesse invalidazioni |
| ScrollArea in flex senza `min-h-0` | Flex item non puo' ridursi sotto la dimensione del contenuto | `min-h-0 flex-1` su ScrollArea + `overflow-hidden` su container |
| Popup inside `.rbc-event` | `overflow:hidden` su `.rbc-event` clippava popup absolute-positioned | `createPortal(popup, document.body)` + `position:fixed` + `getBoundingClientRect()` |
| Calendar unmount on navigate | `onRangeChange` → new query key → `isLoading=true` → calendar unmounts → state reset a oggi | `keepPreviousData` + smart range check (return `prev` se range dentro buffer) |
| D&D sposta evento -1h | `toISOString()` converte ora locale in UTC → offset perso | `toISOLocal()` da `lib/format.ts` — formatta locale senza `Z` |
| 401 interceptor loop login | Interceptor cattura 401 credenziali errate → redirect a /login → loop | Skip redirect se `pathname.startsWith("/login")` |
| Badge "Scaduto" per rate in ritardo | Confondeva contratto scaduto con rate scadute — significato diverso | 7 livelli badge: Insolvente (red solid), Rate in Ritardo (red light), Scaduto (amber) |
| KPI "Rate Scadute" contava contratti | `func.count(distinct(id_contratto))` → numeri bassi e fuorvianti | `func.count(Rate.id)` per contratti, label "Con Rate Scadute" per clienti |

## Esperienza Utente — Principi Frontend

Pilastro di sviluppo (vedi root `CLAUDE.md`). Regole pratiche:

- **CTA contestuali**: ogni azione ha un verbo specifico ("Riscuoti", "Aggiorna stato", "Contatta"), mai generico "Vai" o "Apri"
- **Gerarchia severity**: critical (rosso, bordo forte, badge contatore), warning (ambra), info (blu chiaro)
- **Grammatica condizionale**: singolare/plurale dinamico in ogni testo (`1 rata scaduta` / `3 rate scadute`)
- **Empty state celebrativi**: quando tutto e' ok, comunicarlo con positivita' (icona verde + messaggio incoraggiante)
- **Feedback immediato**: toast su ogni azione, skeleton su ogni loading, error banner su ogni fallimento
- **Hover & transition**: ogni elemento interattivo ha `transition-*` + hover state visibile

## Dashboard Alert System (Inline Resolution)

La Dashboard ha un Alert Panel con 4 categorie di warning proattivi.
Ogni CTA apre uno Sheet inline — risoluzione senza navigazione.

| Sheet | Hook | Azione inline | Mutation riusata |
|-------|------|---------------|------------------|
| GhostEventsSheet | `useGhostEvents` | Completata/Cancellata 1-click + bulk | `useUpdateEvent` |
| OverdueRatesSheet | `useOverdueRates` | Pagamento con metodo selezionabile | `usePayRate` |
| ExpiringContractsSheet | `useExpiringContracts` | Progress bar crediti + link contratto | — (solo info) |
| InactiveClientsSheet | `useInactiveClients` | Contatti rapidi (tel/email) + link agenda | — (solo info) |

Pattern architetturale:
- **alertActions**: `Record<string, () => void>` passato ad AlertPanel — se la categoria ha un'azione, CTA apre Sheet; altrimenti naviga via Link
- **Config-driven**: `ALERT_CATEGORY_CONFIG` con icona, colori, borderColor, cta per categoria
- **Severity hierarchy**: critical (sfondo rosso, CTA filled), warning (sfondo neutro, CTA outline)
- **ScrollArea flex**: `min-h-0 flex-1` su ScrollArea + `overflow-hidden` su SheetContent per scroll corretto

## Visual Design — Cassa Page (CRM-grade)

La pagina Cassa ha un visual premium ispirato ai CRM leader (HubSpot, Salesforce):

### Pattern consolidati
- **Config-driven KPI**: array `CASSA_KPI` con `.map()` — zero copy-paste tra card
- **Gradient cards**: `bg-gradient-to-br` + `border-l-4` tematico + `hover:shadow-md`
- **Custom Recharts tooltip**: inline render function, non `ChartTooltipContent`
- **Date grouping table**: `useMemo` → `Map<string, items[]>` → header `colSpan` con data formattata
- **Alternating rows**: `idx % 2 !== 0 ? "bg-muted/20" : ""` per leggibilita'
- **Sticky table header**: `sticky top-0 z-10 bg-white dark:bg-zinc-900`
- **ScrollArea shadcn**: sostituisce `overflow-y-auto` per scrollbar stilizzata
- **Separator shadcn**: divide sezioni all'interno di card complesse
- **Empty state ricchi**: icona + titolo + sottotitolo contestuale
- **Tab con icone**: `BookOpen`, `CalendarClock`, `ArrowLeftRight`, `Clock`, `LineChart`

## Forecast Tab (Previsioni di Bilancio)

5a tab della pagina Cassa. Proiezione finanziaria a 3 mesi.

**Componente**: `ForecastTab.tsx` con 4 sezioni:
1. **KPI card gradient** (4): Entrate Attese, Uscite Previste, Burn Rate, Margine Proiettato (90gg)
2. **AreaChart gradient** (proiezione): 3 curve con gradient fill (entrate emerald, uscite fisse red, variabili stimate orange tratteggiato)
3. **AreaChart Runway** (saldo cumulativo): curva singola con dot, linea zero rossa tratteggiata (`ReferenceLine`), badge "Stabile"/"Rischio"
4. **Cash Flow Timeline**: lista cronologica con pallini colorati, importi +/- e running balance

**Hook**: `useForecast(mesi)` in `useMovements.ts` — query key `["forecast", { mesi }]`
**Types**: `ForecastResponse`, `ForecastMonthData`, `ForecastTimelineItem`, `ForecastKpi`
**Pattern**: stessi gradient card e tooltip custom del resto della pagina Cassa

## Agenda Page (Calendario Interattivo)

react-big-calendar v1.19.4 con drag & drop, resize, colori categoria×stato, credit guard.

### Architettura componenti
- **AgendaCalendar**: wrapper `withDragAndDrop(Calendar)` con controlled state (date + view)
- **CustomToolbar**: toolbar shadcn/ui con icone vista, "Oggi" con dot indicator, navigazione
- **CustomEvent**: renderizza label evento (nome cliente per PT, titolo per altri), wrappa in `EventHoverCard`
- **EventHoverCard**: popup su hover via `createPortal` → `document.body` (escape `overflow:hidden` di `.rbc-event`)
- **EventSheet**: sheet CRUD completo (EventForm + DeleteEventDialog)
- **calendar-setup.ts**: localizer, messaggi italiani, stili colore categoria×stato, mapping `EventHydrated → CalendarEvent`

### Pattern: QuickActionProvider (React Context)
react-big-calendar non supporta custom props sui componenti evento.
Soluzione: `QuickActionContext` iniettato da `AgendaCalendar` → consumato da `CustomEvent` → passato a `EventHoverCard`.
```typescript
const QuickActionContext = createContext<QuickActionFn | undefined>(undefined);
// AgendaCalendar wrappa in <QuickActionProvider onQuickAction={...}>
// CustomEvent consuma con useContext(QuickActionContext)
```

### Pattern: createPortal per popup in react-big-calendar
`.rbc-event` ha `overflow: hidden`. Qualsiasi popup positioned inside viene clippato.
`EventHoverCard` usa `createPortal(popup, document.body)` con:
- `getBoundingClientRect()` per posizione relativa al trigger
- `position: fixed` + `z-index: 9999`
- Viewport bounds checking (8px margine da bordi)
- Hover delay: 350ms enter, 200ms leave (con cleanup refs)

### Pattern: Smart Range Buffering + keepPreviousData
Navigazione fluida senza flash/reset. Due meccanismi:
1. **`keepPreviousData`** in `useEvents` — quando la query key cambia (nuovo range), i vecchi dati restano come placeholder → `isLoading` resta `false` → il calendario non si smonta
2. **Smart range check** in `handleRangeChange` — se il range visibile e' gia' dentro il buffer fetchato, ritorna `prev` (stessa reference → zero state change). Il buffer si espande solo quando la navigazione esce dai bordi.
3. **`endOfDay` normalization** — react-big-calendar manda `end` come mezzanotte (00:00). Senza `endOfDay()`, gli eventi dell'ultimo giorno sarebbero esclusi. `handleRangeChange` normalizza `visibleRange.end` a `23:59:59.999`.

Buffer iniziale: mese corrente ±1 mese. Espansione: +1 mese in ogni direzione dal nuovo range visibile.

### Pattern: Filtering Pipeline a 3 livelli (2 assi)
```
events (buffer API ±1 mese)
  ├── calendarEvents = filtro categoria + stato → passa al calendario
  └── visibleEvents  = filtro range + categoria + stato → KPI + header count
```
Due assi di filtraggio indipendenti: **categoria** (PT, SALA, CORSO, COLLOQUIO) e **stato** (Programmato, Completato, Cancellato, Rinviato). Entrambi gestiti da `Set<string>` con toggle on/off.
Il calendario gestisce il range internamente — riceve eventi filtrati per categoria + stato.
I KPI e l'header usano `visibleEvents` che filtra per range + categoria + stato.
`rangeLabel` per vista mese usa il **midpoint** del range (il primo giorno della griglia puo' appartenere al mese precedente).

### Page features (page.tsx)
- **FilterBar**: due righe — riga 1 filtri categoria, riga 2 filtri stato. Entrambi chip interattivi (`Set<string>` toggle on/off, Eye/EyeOff icon). Label a larghezza fissa (`w-16`) per allineamento verticale.
- **RangeStatsBar**: 4 KPI config-driven contestuali al range visibile (Sessioni, Completate, Programmate, Tasso %). Label dinamica: giorno ("lunedi' 24 febbraio"), settimana ("17-23 feb"), mese ("febbraio 2026"). Calcolo da `visibleRange` state, zero query aggiuntive.
- **Quick Actions**: hover card con Completa/Rinvia/Cancella 1-click (no sheet)
- **Dashboard = control center**: eventi fantasma gestiti SOLO da Dashboard (GhostEventsSheet con bulk + single resolve). Zero duplicazione in Agenda.

### CSS Overrides (globals.css)
```css
.rbc-current-time-indicator { background-color: #ef4444; height: 2px; }
.rbc-event:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.15); transform: translateY(-1px); }
.rbc-today { background-color: oklch(0.97 0.01 250) !important; }
/* Mobile: font ridotti per react-big-calendar (vedi sezione Responsive Design) */
@media (max-width: 640px) { .rbc-header, .rbc-event, .rbc-label { font-size: 0.7rem; } }
```

## Command Palette (Ctrl+K)

Componente: `CommandPalette.tsx` (~700 LOC), basato su `cmdk` v1.1.1 + shadcn Command.

### Architettura
- **Custom Dialog** (non `CommandDialog`) — necessario per split layout left/right
- **Split panel**: left (search + results), right (preview panel, `hidden md:block`)
- **value tracking**: `Command value={highlighted} onValueChange={setHighlighted}` + `useMemo` Maps per O(1) lookup
- **Lazy loading**: 4 query React Query con `enabled: open` + `staleTime: 30_000`
- **Zero prop drilling**: custom event `open-command-palette` per apertura da sidebar

### 6 gruppi risultati
1. **Contestuale** (se su `/clienti/[id]`): azioni per il cliente corrente
2. **Dati Rapidi**: KPI inline (entrate, margine, rate pendenti, appuntamenti) con valori live
3. **Pagine**: navigazione statica (7 pagine)
4. **Clienti**: dinamico, `keywords` prop per fuzzy search su nome+cognome+email+telefono
5. **Esercizi**: dinamico, `keywords` prop su nome+nome_en+categoria+attrezzatura
6. **Azioni**: Nuovo Cliente, Nuovo Contratto, Nuova Sessione

### Preview panel (desktop)
- `ClientPreview`: avatar, badge stato, stats grid (crediti, contratti, versato), warning rate scadute, contatti
- `ExercisePreview`: badges (categoria, difficolta', attrezzatura), pattern/forza, chip muscoli primari/secondari
- `KpiPreview`: entrate, uscite, margine, clienti attivi, rate pendenti, appuntamenti

### Integrazione
- Layout: `<CommandPalette />` in `(dashboard)/layout.tsx` dentro `<AuthGuard>`, prima del div flex
- Sidebar: bottone "Cerca... Ctrl K" con `window.dispatchEvent(new Event("open-command-palette"))`

## Sidebar — Section Labels (Linear/Notion style)

Navigazione organizzata in sezioni con label uppercase. Union type:
```typescript
type NavLink = { href: string; label: string; icon: React.ComponentType<{ className?: string }> };
type NavSection = { section: string; items: NavLink[] };
type NavEntry = NavLink | NavSection;
```

Struttura: Dashboard, Agenda (top-level) → Clienti (sezione) → Contabilita' (Contratti, Cassa) → Allenamento (Esercizi).
Impostazioni pinned in fondo via `mt-auto`. Search trigger sopra la nav.

## Build

```bash
npx next build   # OBBLIGATORIO prima di ogni commit — zero errori TS
npm run dev       # Dev server con hot reload
```

### Dual Instance (sviluppo parallelo a produzione)

`next.config.ts` supporta `NEXT_DIST_DIR` per separare la cache:
```bash
# Produzione (Chiara):  .next (default)
npm run dev -- -H 0.0.0.0 -p 3000

# Sviluppo (gvera):     .next-dev (cache separata)
$env:NEXT_DIST_DIR=".next-dev"; $env:NEXT_PUBLIC_API_URL="http://localhost:8001"; npm run dev -- -p 3001
```
`.next-dev/` e' in `.gitignore`. Vedi root `CLAUDE.md` per architettura dual DB completa.

## Dipendenze chiave

```
next 16.1, react 19.2, typescript 5
@tanstack/react-query 5 (server state)
react-hook-form 7 + zod 3 (form validation — NON zod/v4)
axios 1.13 (HTTP client)
date-fns 4 (date formatting)
recharts 2 (charts)
sonner 2 (toast)
lucide-react (icons)
cmdk 1.1.1 (command palette fuzzy search)
```
