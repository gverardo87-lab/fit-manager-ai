// src/types/api.ts
/**
 * Type Synchronization — Design by Contract.
 *
 * Queste interfacce sono la traduzione 1:1 degli schema Pydantic
 * del backend Python. Ogni campo Optional[X] diventa X | null.
 *
 * Sorgenti:
 *   - api/auth/schemas.py         -> Auth types
 *   - api/routers/clients.py      -> Client types (inline schemas)
 *   - api/routers/agenda.py       -> Event types (inline schemas)
 *   - api/schemas/financial.py    -> Contract, Rate, Movement, Dashboard
 *
 * REGOLA: se cambi uno schema Pydantic, DEVI aggiornare qui.
 */

// ════════════════════════════════════════════════════════════
// COSTANTI (allineate a api/schemas/financial.py)
// ════════════════════════════════════════════════════════════

export const PAYMENT_METHODS = ["CONTANTI", "POS", "BONIFICO", "ASSEGNO", "ALTRO"] as const;
export type PaymentMethod = (typeof PAYMENT_METHODS)[number];

export const RATE_STATUSES = ["PENDENTE", "PARZIALE", "SALDATA"] as const;
export type RateStatus = (typeof RATE_STATUSES)[number];

export const PAYMENT_STATUSES = ["PENDENTE", "PARZIALE", "SALDATO"] as const;
export type PaymentStatus = (typeof PAYMENT_STATUSES)[number];

export const MOVEMENT_TYPES = ["ENTRATA", "USCITA"] as const;
export type MovementType = (typeof MOVEMENT_TYPES)[number];

export const EVENT_CATEGORIES = ["PT", "SALA", "CORSO", "COLLOQUIO"] as const;
export type EventCategory = (typeof EVENT_CATEGORIES)[number];

export const EVENT_STATUSES = ["Programmato", "Completato", "Cancellato", "Rinviato"] as const;
export type EventStatus = (typeof EVENT_STATUSES)[number];

export const PLAN_FREQUENCIES = ["MENSILE", "SETTIMANALE", "TRIMESTRALE"] as const;
export type PlanFrequency = (typeof PLAN_FREQUENCIES)[number];

export const EXPENSE_FREQUENCIES = ["MENSILE", "SETTIMANALE", "TRIMESTRALE", "SEMESTRALE", "ANNUALE"] as const;
export type ExpenseFrequency = (typeof EXPENSE_FREQUENCIES)[number];

export const EXPENSE_CATEGORIES = [
  "Affitto", "Assicurazione", "Utenze", "Attrezzatura",
  "Software", "Formazione", "Commercialista", "Trasporto",
  "Marketing", "Altro",
] as const;
export type ExpenseCategory = (typeof EXPENSE_CATEGORIES)[number];

// ════════════════════════════════════════════════════════════
// AUTH (api/auth/schemas.py)
// ════════════════════════════════════════════════════════════

/** POST /api/auth/register */
export interface TrainerRegister {
  email: string;
  nome: string;
  cognome: string;
  password: string;
}

/** POST /api/auth/login */
export interface TrainerLogin {
  email: string;
  password: string;
}

/** Risposta login/register — TokenResponse */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  trainer_id: number;
  nome: string;
  cognome: string;
}

/** Dati pubblici trainer — TrainerPublic */
export interface Trainer {
  id: number;
  email: string;
  nome: string;
  cognome: string;
  is_active: boolean;
}

// ════════════════════════════════════════════════════════════
// CLIENT (api/routers/clients.py — inline schemas)
// ════════════════════════════════════════════════════════════

/** POST /api/clients */
export interface ClientCreate {
  nome: string;
  cognome: string;
  telefono?: string | null;
  email?: string | null;
  data_nascita?: string | null; // ISO date string "YYYY-MM-DD"
  sesso?: "Uomo" | "Donna" | "Altro" | null;
  anamnesi?: Record<string, unknown>;
  stato?: "Attivo" | "Inattivo";
}

/** PUT /api/clients/{id} (partial update) */
export interface ClientUpdate {
  nome?: string | null;
  cognome?: string | null;
  telefono?: string | null;
  email?: string | null;
  data_nascita?: string | null;
  sesso?: "Uomo" | "Donna" | "Altro" | null;
  anamnesi?: Record<string, unknown> | null;
  stato?: "Attivo" | "Inattivo" | null;
}

/** ClientResponse — restituito da GET/POST/PUT */
export interface Client {
  id: number;
  nome: string;
  cognome: string;
  telefono: string | null;
  email: string | null;
  data_nascita: string | null; // Backend restituisce come string
  sesso: string | null;
  stato: string;
  crediti_residui: number;
}

// ════════════════════════════════════════════════════════════
// EVENT (api/routers/agenda.py — inline schemas)
// ════════════════════════════════════════════════════════════

/** POST /api/agenda */
export interface EventCreate {
  data_inizio: string; // ISO datetime "YYYY-MM-DDTHH:MM:SS"
  data_fine: string;
  categoria: string;
  titolo: string;
  id_cliente?: number | null;
  id_contratto?: number | null;
  stato?: string;
  note?: string | null;
}

/** PUT /api/agenda/{id} (partial update) */
export interface EventUpdate {
  data_inizio?: string | null;
  data_fine?: string | null;
  titolo?: string | null;
  note?: string | null;
  stato?: string | null;
}

/** EventResponse — restituito da GET/POST/PUT */
export interface Event {
  id: number;
  data_inizio: string; // ISO datetime string
  data_fine: string;
  categoria: string;
  titolo: string | null;
  id_cliente: number | null;
  id_contratto: number | null;
  stato: string;
  note: string | null;
  cliente_nome: string | null;
  cliente_cognome: string | null;
}

// ════════════════════════════════════════════════════════════
// CONTRACT (api/schemas/financial.py)
// ════════════════════════════════════════════════════════════

/** POST /api/contracts */
export interface ContractCreate {
  id_cliente: number;
  tipo_pacchetto: string;
  crediti_totali: number;
  prezzo_totale: number;
  data_inizio: string; // ISO date "YYYY-MM-DD"
  data_scadenza: string;
  acconto?: number;
  metodo_acconto?: string | null;
  note?: string | null;
}

/** PUT /api/contracts/{id} (partial update) */
export interface ContractUpdate {
  tipo_pacchetto?: string | null;
  crediti_totali?: number | null;
  prezzo_totale?: number | null;
  data_inizio?: string | null;
  data_scadenza?: string | null;
  note?: string | null;
}

/** ContractResponse — restituito da GET/POST/PUT */
export interface Contract {
  id: number;
  id_cliente: number;
  tipo_pacchetto: string | null;
  data_vendita: string | null; // ISO date
  data_inizio: string | null;
  data_scadenza: string | null;
  crediti_totali: number | null;
  crediti_usati: number;
  prezzo_totale: number | null;
  acconto: number;
  totale_versato: number;
  stato_pagamento: string;
  note: string | null;
  chiuso: boolean;
}

/** ContractListResponse — GET /api/contracts (enriched with rate KPI) */
export interface ContractListItem extends Contract {
  client_nome: string;
  client_cognome: string;
  rate_totali: number;
  rate_pagate: number;
  ha_rate_scadute: boolean;
}

/** ContractWithRatesResponse — GET /api/contracts/{id} */
export interface ContractWithRates extends Contract {
  rate: Rate[];
  // KPI computati dal backend (unica fonte di verita')
  residuo: number;
  percentuale_versata: number;
  importo_da_rateizzare: number;
  somma_rate_previste: number;
  somma_rate_saldate: number;
  somma_rate_pendenti: number;
  piano_allineato: boolean;
  importo_disallineamento: number;
  rate_totali: number;
  rate_pagate: number;
  rate_scadute: number;
  // Credit breakdown (computed on read da eventi PT)
  sedute_programmate: number;
  sedute_completate: number;
  sedute_rinviate: number;
  crediti_residui: number;
}

// ════════════════════════════════════════════════════════════
// RATE (api/schemas/financial.py)
// ════════════════════════════════════════════════════════════

/** POST /api/rates */
export interface RateCreate {
  id_contratto: number;
  data_scadenza: string;
  importo_previsto: number;
  descrizione?: string | null;
}

/** PUT /api/rates/{id} (partial update, solo PENDENTI) */
export interface RateUpdate {
  data_scadenza?: string | null;
  importo_previsto?: number | null;
  descrizione?: string | null;
}

/** POST /api/rates/{id}/pay — Pagamento atomico */
export interface RatePayment {
  importo: number;
  metodo?: string;
  data_pagamento?: string;
  note?: string | null;
}

/** Singolo pagamento registrato su una rata (da CashMovement) */
export interface RatePaymentReceipt {
  id: number;
  importo: number;
  metodo: string | null;
  data_pagamento: string; // ISO date
  note: string | null;
}

/** RateResponse — restituito da GET/POST/PUT/PAY */
export interface Rate {
  id: number;
  id_contratto: number;
  data_scadenza: string; // ISO date
  importo_previsto: number;
  descrizione: string | null;
  stato: string;
  importo_saldato: number;
  data_pagamento: string | null;   // Ultimo pagamento (backward-compat)
  metodo_pagamento: string | null; // Ultimo pagamento (backward-compat)
  pagamenti: RatePaymentReceipt[]; // Storico completo cronologico
  // Computed dal backend
  importo_residuo: number;
  is_scaduta: boolean;
  giorni_ritardo: number;
}

/** POST /api/rates/generate-plan/{contract_id} */
export interface PaymentPlanCreate {
  importo_da_rateizzare: number;
  numero_rate: number;
  data_prima_rata: string;
  frequenza?: string;
}

// ════════════════════════════════════════════════════════════
// CASH MOVEMENT (api/schemas/financial.py)
// ════════════════════════════════════════════════════════════

/** POST /api/movements (solo manuali — Ledger Integrity) */
export interface MovementManualCreate {
  importo: number;
  tipo: MovementType;
  categoria?: string | null;
  metodo?: string | null;
  data_effettiva: string; // ISO date
  note?: string | null;
}

/** MovementResponse — restituito da GET/POST */
export interface CashMovement {
  id: number;
  data_movimento: string | null; // ISO datetime
  data_effettiva: string; // ISO date
  tipo: string;
  categoria: string | null;
  importo: number;
  metodo: string | null;
  id_cliente: number | null;
  id_contratto: number | null;
  id_rata: number | null;
  id_spesa_ricorrente: number | null;
  note: string | null;
  operatore: string;
}

// ════════════════════════════════════════════════════════════
// MOVEMENT STATS (api/routers/movements.py)
// ════════════════════════════════════════════════════════════

/** Punto dati per il grafico giornaliero entrate/uscite */
export interface ChartDataPoint {
  giorno: number;
  entrate: number;
  uscite: number;
}

/** GET /api/movements/stats?anno=X&mese=Y */
export interface MovementStats {
  totale_entrate: number;
  totale_uscite_variabili: number;
  totale_uscite_fisse: number;
  margine_netto: number;
  chart_data: ChartDataPoint[];
}

// ════════════════════════════════════════════════════════════
// RECURRING EXPENSES (api/routers/recurring_expenses.py)
// ════════════════════════════════════════════════════════════

/** POST /api/recurring-expenses */
export interface RecurringExpenseCreate {
  nome: string;
  categoria?: string | null;
  importo: number;
  giorno_scadenza?: number;
  frequenza?: ExpenseFrequency;
  data_inizio?: string | null; // ISO date "YYYY-MM-DD"
}

/** PUT /api/recurring-expenses/{id} */
export interface RecurringExpenseUpdate {
  nome?: string;
  categoria?: string | null;
  importo?: number;
  giorno_scadenza?: number;
  frequenza?: ExpenseFrequency;
  attiva?: boolean;
  data_inizio?: string | null;
}

/** Risposta da GET/POST/PUT */
export interface RecurringExpense {
  id: number;
  nome: string;
  categoria: string | null;
  importo: number;
  frequenza: ExpenseFrequency;
  giorno_scadenza: number;
  data_inizio: string | null; // ISO date — ancoraggio frequenze
  attiva: boolean;
  data_creazione: string | null;
  data_disattivazione: string | null;
}

// ════════════════════════════════════════════════════════════
// PENDING EXPENSES (api/routers/movements.py — Conferma & Registra)
// ════════════════════════════════════════════════════════════

/** Singola spesa in attesa di conferma per un mese */
export interface PendingExpenseItem {
  id_spesa: number;
  nome: string;
  categoria: string | null;
  importo: number;
  frequenza: string;
  data_prevista: string;     // ISO date
  mese_anno_key: string;     // chiave di deduplicazione
}

/** GET /api/movements/pending-expenses?anno=X&mese=Y */
export interface PendingExpensesResponse {
  items: PendingExpenseItem[];
  totale_pending: number;
}

// ════════════════════════════════════════════════════════════
// DASHBOARD (api/schemas/financial.py)
// ════════════════════════════════════════════════════════════

/** GET /api/dashboard/summary */
export interface DashboardSummary {
  active_clients: number;
  monthly_revenue: number;
  pending_rates: number;
  todays_appointments: number;
}

/** Singolo alert con severity, categoria e contesto navigabile */
export interface AlertItem {
  severity: "critical" | "warning" | "info";
  category: "ghost_events" | "expiring_contracts" | "overdue_rates" | "inactive_clients";
  title: string;
  detail: string;
  count: number;
  link: string | null;
}

/** GET /api/dashboard/alerts */
export interface DashboardAlerts {
  total_alerts: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  items: AlertItem[];
}

// ════════════════════════════════════════════════════════════
// GENERIC PAGINATED RESPONSE
// ════════════════════════════════════════════════════════════

/** Wrapper paginato generico — usato da GET /clients, /contracts, /movements */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** Wrapper lista semplice — usato da GET /rates, /rates/generate-plan */
export interface ListResponse<T> {
  items: T[];
  total: number;
}

// ════════════════════════════════════════════════════════════
// AGING REPORT (api/routers/rates.py — GET /rates/aging)
// ════════════════════════════════════════════════════════════

/** Singola rata nell'aging report */
export interface AgingItem {
  rate_id: number;
  contract_id: number;
  client_id: number;
  client_nome: string;
  client_cognome: string;
  data_scadenza: string; // ISO date
  giorni: number;        // positivo = scaduta, negativo = futura
  importo_previsto: number;
  importo_saldato: number;
  importo_residuo: number;
  stato: string;
}

/** Fascia temporale con rate raggruppate */
export interface AgingBucket {
  label: string;
  min_days: number;
  max_days: number;
  totale: number;
  count: number;
  items: AgingItem[];
}

/** GET /api/rates/aging — Orizzonte finanziario completo */
export interface AgingResponse {
  totale_scaduto: number;
  totale_in_arrivo: number;
  rate_scadute: number;
  rate_in_arrivo: number;
  clienti_con_scaduto: number;
  overdue_buckets: AgingBucket[];
  upcoming_buckets: AgingBucket[];
}

// ════════════════════════════════════════════════════════════
// BACKUP (api/routers/backup.py)
// ════════════════════════════════════════════════════════════

/** GET /api/backup/list */
export interface BackupInfo {
  filename: string;
  size_bytes: number;
  created_at: string;
}

/** POST /api/backup/create */
export interface BackupCreateResponse {
  filename: string;
  size_bytes: number;
  message: string;
}

/** POST /api/backup/restore */
export interface BackupRestoreResponse {
  message: string;
  safety_backup: string;
}
