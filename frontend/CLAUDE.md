# Frontend Layer — React Rules

Next.js 16 + React 19 + TypeScript 5 + shadcn/ui + Tailwind CSS 4.

## Architettura

```
frontend/src/
├── app/                     Next.js App Router
│   ├── (dashboard)/         Route group (non appare in URL)
│   │   ├── layout.tsx       Sidebar + AuthGuard wrapper
│   │   ├── page.tsx         Dashboard KPI
│   │   ├── clienti/         Pagina clienti
│   │   ├── contratti/       Pagina contratti
│   │   ├── agenda/          Pagina agenda/calendario
│   │   ├── cassa/           Pagina Cassa (5 tab: Libro Mastro, Spese Fisse, Entrate & Uscite, Scadenze, Previsioni)
│   │   └── impostazioni/   Pagina impostazioni
│   ├── login/page.tsx       Login pubblico
│   └── layout.tsx           Root layout (Providers, fonts)
├── components/
│   ├── auth/AuthGuard.tsx   Client-side route protection
│   ├── layout/Sidebar.tsx   Navigazione + trainer info
│   ├── clients/             Componenti dominio clienti
│   ├── contracts/           Componenti dominio contratti (PaymentPlanTab con
│   │                        RateCard, PayRateForm, PaymentHistory, AddRateForm)
│   ├── agenda/              Componenti dominio agenda/calendario
│   ├── dashboard/           Componenti dashboard (GhostEventsSheet, OverdueRatesSheet,
│   │                        ExpiringContractsSheet, InactiveClientsSheet)
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
│   ├── format.ts            formatCurrency centralizzato
│   └── providers.tsx        QueryClientProvider
└── types/
    └── api.ts               TypeScript interfaces (mirror Pydantic)
```

## Pattern Obbligatori

### Hook per dominio
Un file hook per ogni dominio. Struttura:
```typescript
// useClients.ts
export function useClients(params) { return useQuery({...}) }      // READ
export function useCreateClient() { return useMutation({...}) }    // CREATE
export function useUpdateClient() { return useMutation({...}) }    // UPDATE
export function useDeleteClient() { return useMutation({...}) }    // DELETE
```
Ogni mutation: `invalidateQueries` sulle key correlate + `toast.success/error`.

### Query Key Convention
```typescript
["clients", { page, search }]       // lista con filtri
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
["forecast", { mesi }]              // proiezione finanziaria N mesi
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

### Azioni Distruttive — 2 livelli
- **CRITICA** (delete contratto, revoca pagamento): AlertDialog + conferma testuale ("ANNULLA")
- **MEDIA** (delete rata, delete movimento): AlertDialog standard con 2 bottoni

### Formattazione Valuta
```typescript
import { formatCurrency } from "@/lib/format";
```
Funzione centralizzata in `lib/format.ts`. Importata in tutti i componenti.

### Error Handling
```typescript
import { extractErrorMessage } from "@/lib/api-client";
// In ogni mutation onError:
onError: (error) => {
  toast.error(extractErrorMessage(error, "Messaggio fallback"));
}
```
Estrae `error.response.data.detail` dal backend FastAPI, mostra il messaggio reale all'utente.

## Convenzioni

- Lingua UI: **italiano** (labels, toast, placeholder)
- Lingua codice: **inglese** (nomi variabili, funzioni, commenti)
- Nomi dominio: **italiano** nei tipi API (`id_cliente`, `data_scadenza`)
- CSS: Tailwind utilities, ZERO CSS custom (tranne globals.css per theme)
- Icone: lucide-react (consistente con shadcn/ui)
- Toast: sonner (`toast.success`, `toast.error`)
- Date: date-fns con locale `it` per display, ISO strings per API

## Auth (3 layer)

1. **Edge Middleware** (`middleware.ts`): intercetta route prima del render
2. **AuthGuard** (`components/auth/AuthGuard.tsx`): check cookie client-side
3. **API interceptor** (`lib/api-client.ts`): JWT header + redirect su 401

Token in cookie `fitmanager_token` (8h expiry). Trainer data in `fitmanager_trainer`.

## Pitfalls — Errori Reali, Mai Ripeterli

| Pitfall | Causa | Fix |
|---------|-------|-----|
| `<label>` + Radix Checkbox | Browser propaga click al `<button>` interno → double-toggle | `<div onClick>` + `Checkbox onClick={stopPropagation}` |
| `Set<string>` non-univoca | `mese_anno_key` uguale per N spese mensili stesso mese | Chiave composta `${id}::${key}` |
| React `key={nonUniqueValue}` | Duplica render, stato condiviso tra componenti | Sempre key univoca per item |
| Invalidation asimmetrica | `usePayRate` mancava movements/stats → KPI stale dopo pagamento | Operazioni inverse: stesse invalidazioni |
| ScrollArea in flex senza `min-h-0` | Flex item non puo' ridursi sotto la dimensione del contenuto | `min-h-0 flex-1` su ScrollArea + `overflow-hidden` su container |

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

## Build

```bash
npx next build   # OBBLIGATORIO prima di ogni commit — zero errori TS
npm run dev       # Dev server con hot reload
```

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
```
