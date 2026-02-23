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
│   │   ├── cassa/           Pagina Cassa (4 tab: Libro Mastro, Spese Fisse, Entrate & Uscite, Scadenze)
│   ├── login/page.tsx       Login pubblico
│   └── layout.tsx           Root layout (Providers, fonts)
├── components/
│   ├── auth/AuthGuard.tsx   Client-side route protection
│   ├── layout/Sidebar.tsx   Navigazione + trainer info
│   ├── clients/             Componenti dominio clienti
│   ├── contracts/           Componenti dominio contratti (PaymentPlanTab con
│   │                        RateCard, PayRateForm, PaymentHistory, AddRateForm)
│   ├── agenda/              Componenti dominio agenda/calendario
│   ├── movements/           Componenti dominio cassa (MovementsTable, MovementSheet,
│   │                        DeleteMovementDialog, RecurringExpensesTab (con EditDialog,
│   │                        AddForm, ExpensesTable, AlertDialog delete confirm),
│   │                        SplitLedgerView, AdvancedFilters, LedgerColumn, AgingReport)
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
["aging-report"]                     // orizzonte finanziario (scadenze)
["dashboard"]                        // KPI aggregati
```

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

### Spese Ricorrenti (RecurringExpensesTab)
Componente completo con 3 sotto-componenti inline:
- **AddExpenseForm**: form creazione con Select categoria (EXPENSE_CATEGORIES) e frequenza (EXPENSE_FREQUENCIES, 5 opzioni)
- **ExpenseEditDialog**: Dialog con useEffect state sync da props (pattern RateEditDialog), 5 campi editabili
- **ExpensesTable**: tabella con colonna Categoria, bottone Edit (Pencil), delete con AlertDialog confirm
- **Costanti**: `EXPENSE_CATEGORIES` (10 predefinite) e `EXPENSE_FREQUENCIES` (5) esportate da `types/api.ts`
- **FREQUENZA_LABELS**: mappa display label per 5 frequenze

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
