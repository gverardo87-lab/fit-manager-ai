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

export const EVENT_CATEGORIES = ["PT", "SALA", "CORSO", "COLLOQUIO", "PERSONALE"] as const;
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
  note_interne?: string | null;
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
  note_interne?: string | null;
}

// ── Anamnesi (struttura questionario a step) ──

/** Singola domanda anamnesi con toggle si/no + dettaglio testuale */
export interface AnamnesiQuestion {
  presente: boolean;
  dettaglio: string | null;
}

/** Struttura completa anamnesi cliente — 4 step del wizard */
export interface AnamnesiData {
  // Step 1: Muscoloscheletrico
  infortuni_attuali: AnamnesiQuestion;
  infortuni_pregressi: AnamnesiQuestion;
  interventi_chirurgici: AnamnesiQuestion;
  dolori_cronici: AnamnesiQuestion;
  // Step 2: Condizioni Mediche
  patologie: AnamnesiQuestion;
  farmaci: AnamnesiQuestion;
  problemi_cardiovascolari: AnamnesiQuestion;
  problemi_respiratori: AnamnesiQuestion;
  // Step 3: Stile di Vita
  livello_attivita: string;
  ore_sonno: string;
  livello_stress: string;
  dieta_particolare: AnamnesiQuestion;
  // Step 4: Obiettivi e Limitazioni
  obiettivi_specifici: string | null;
  limitazioni_funzionali: string | null;
  note: string | null;
  // Metadata
  data_compilazione: string;
  data_ultimo_aggiornamento: string;
}

export const LIVELLI_ATTIVITA = ["sedentario", "leggero", "moderato", "intenso"] as const;
export const LIVELLI_ATTIVITA_LABELS: Record<string, string> = {
  sedentario: "Sedentario", leggero: "Leggero", moderato: "Moderato", intenso: "Intenso",
};

export const ORE_SONNO = ["<5", "5-6", "6-7", "7-8", "8+"] as const;
export const ORE_SONNO_LABELS: Record<string, string> = {
  "<5": "Meno di 5h", "5-6": "5-6 ore", "6-7": "6-7 ore", "7-8": "7-8 ore", "8+": "Oltre 8h",
};

export const LIVELLI_STRESS = ["basso", "medio", "alto"] as const;
export const LIVELLI_STRESS_LABELS: Record<string, string> = {
  basso: "Basso", medio: "Medio", alto: "Alto",
};

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
  note_interne: string | null;
  crediti_residui: number;
  anamnesi: AnamnesiData | null;
}

/** ClientEnrichedResponse — restituito da GET /api/clients (lista enriched) */
export interface ClientEnriched extends Client {
  contratti_attivi: number;
  totale_versato: number;
  prezzo_totale_attivo: number;
  ha_rate_scadute: boolean;
  ultimo_evento_data: string | null;
}

/** Risposta paginata enriched per lista clienti + KPI aggregati */
export interface ClientEnrichedListResponse {
  items: ClientEnriched[];
  total: number;
  page: number;
  page_size: number;
  kpi_attivi: number;
  kpi_inattivi: number;
  kpi_con_crediti: number;
  kpi_rate_scadute: number;
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
  // Client info (per la pagina dettaglio)
  client_nome: string;
  client_cognome: string;
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

/** Rate scaduta per risoluzione inline dalla Dashboard */
export interface OverdueRateItem {
  rate_id: number;
  data_scadenza: string; // ISO date
  importo_previsto: number;
  importo_saldato: number;
  importo_residuo: number;
  giorni_ritardo: number;
  stato: string;
  contract_id: number;
  tipo_pacchetto: string | null;
  client_id: number;
  client_nome: string;
  client_cognome: string;
}

/** Contratto in scadenza con crediti inutilizzati per Dashboard Sheet */
export interface ExpiringContractItem {
  contract_id: number;
  tipo_pacchetto: string | null;
  data_scadenza: string; // ISO date
  giorni_rimasti: number;
  crediti_totali: number;
  crediti_usati: number;
  crediti_residui: number;
  prezzo_totale: number | null;
  client_id: number;
  client_nome: string;
  client_cognome: string;
}

/** Cliente inattivo per Dashboard Sheet */
export interface InactiveClientItem {
  client_id: number;
  nome: string;
  cognome: string;
  telefono: string | null;
  email: string | null;
  giorni_inattivo: number;
  ultimo_evento_data: string | null; // ISO date
  ultimo_evento_categoria: string | null;
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
// TODO (api/routers/todos.py — inline schemas)
// ════════════════════════════════════════════════════════════

/** POST /api/todos */
export interface TodoCreate {
  titolo: string;
  descrizione?: string | null;
  data_scadenza?: string | null; // ISO date "YYYY-MM-DD"
}

/** PUT /api/todos/{id} */
export interface TodoUpdate {
  titolo?: string | null;
  descrizione?: string | null;
  data_scadenza?: string | null;
}

/** TodoResponse — restituito da GET/POST/PUT/PATCH */
export interface Todo {
  id: number;
  titolo: string;
  descrizione: string | null;
  data_scadenza: string | null; // ISO date
  completato: boolean;
  completed_at: string | null;
  created_at: string;
}

// ════════════════════════════════════════════════════════════
// GENERIC PAGINATED RESPONSE
// ════════════════════════════════════════════════════════════

/** Wrapper paginato generico — usato da GET /clients, /movements */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** Response paginata contratti con KPI aggregati — GET /api/contracts */
export interface ContractListResponse extends PaginatedResponse<ContractListItem> {
  kpi_attivi: number;
  kpi_chiusi: number;
  kpi_fatturato: number;
  kpi_incassato: number;
  kpi_rate_scadute: number;
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
// FORECAST (api/routers/movements.py — GET /forecast)
// ════════════════════════════════════════════════════════════

export interface ForecastMonthData {
  mese: number;
  anno: number;
  label: string;
  entrate_certe: number;
  uscite_fisse: number;
  uscite_variabili_stimate: number;
  margine_proiettato: number;
}

export interface ForecastTimelineItem {
  data: string;
  descrizione: string;
  tipo: "ENTRATA" | "USCITA";
  importo: number;
  saldo_cumulativo: number;
}

export interface ForecastKpi {
  entrate_attese_90gg: number;
  uscite_previste_90gg: number;
  burn_rate_mensile: number;
  margine_proiettato_90gg: number;
}

export interface ForecastResponse {
  kpi: ForecastKpi;
  monthly_projection: ForecastMonthData[];
  timeline: ForecastTimelineItem[];
  saldo_iniziale: number;
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

// ════════════════════════════════════════════════════════════
// EXERCISE (api/routers/exercises.py + api/schemas/exercise.py)
// ════════════════════════════════════════════════════════════

/** Sub-entity: media galleria esercizio */
export interface ExerciseMedia {
  id: number;
  tipo: string;
  url: string;
  ordine: number;
  descrizione: string | null;
}

/** Sub-entity: relazione tra esercizi */
export interface ExerciseRelation {
  id: number;
  related_exercise_id: number;
  related_exercise_nome: string;
  tipo_relazione: string;
}

/** Errore comune con correzione */
export interface ExerciseError {
  errore: string;
  correzione: string;
}

/** ExerciseResponse — restituito da GET/POST/PUT */
export interface Exercise {
  id: number;
  nome: string;
  nome_en: string | null;
  categoria: string;
  pattern_movimento: string;
  force_type: string | null;
  lateral_pattern: string | null;
  muscoli_primari: string[];
  muscoli_secondari: string[];
  attrezzatura: string;
  difficolta: string;
  rep_range_forza: string | null;
  rep_range_ipertrofia: string | null;
  rep_range_resistenza: string | null;
  ore_recupero: number;
  descrizione_anatomica: string | null;
  descrizione_biomeccanica: string | null;
  setup: string | null;
  esecuzione: string | null;
  respirazione: string | null;
  tempo_consigliato: string | null;
  coaching_cues: string[];
  errori_comuni: ExerciseError[];
  note_sicurezza: string | null;
  istruzioni: { setup?: string; esecuzione?: string; errori_comuni?: string } | null;
  controindicazioni: string[];
  image_url: string | null;
  video_url: string | null;
  muscle_map_url: string | null;
  is_builtin: boolean;
  created_at: string | null;
  media: ExerciseMedia[];
  relazioni: ExerciseRelation[];
}

/** POST /api/exercises */
export interface ExerciseCreate {
  nome: string;
  nome_en?: string | null;
  categoria: string;
  pattern_movimento: string;
  force_type?: string | null;
  lateral_pattern?: string | null;
  muscoli_primari: string[];
  muscoli_secondari?: string[] | null;
  attrezzatura: string;
  difficolta: string;
  rep_range_forza?: string | null;
  rep_range_ipertrofia?: string | null;
  rep_range_resistenza?: string | null;
  ore_recupero?: number;
  descrizione_anatomica?: string | null;
  descrizione_biomeccanica?: string | null;
  setup?: string | null;
  esecuzione?: string | null;
  respirazione?: string | null;
  tempo_consigliato?: string | null;
  coaching_cues?: string[] | null;
  errori_comuni?: ExerciseError[] | null;
  note_sicurezza?: string | null;
  controindicazioni?: string[] | null;
}

/** PUT /api/exercises/{id} (partial update) */
export interface ExerciseUpdate {
  nome?: string | null;
  nome_en?: string | null;
  categoria?: string | null;
  pattern_movimento?: string | null;
  force_type?: string | null;
  lateral_pattern?: string | null;
  muscoli_primari?: string[] | null;
  muscoli_secondari?: string[] | null;
  attrezzatura?: string | null;
  difficolta?: string | null;
  rep_range_forza?: string | null;
  rep_range_ipertrofia?: string | null;
  rep_range_resistenza?: string | null;
  ore_recupero?: number | null;
  descrizione_anatomica?: string | null;
  descrizione_biomeccanica?: string | null;
  setup?: string | null;
  esecuzione?: string | null;
  respirazione?: string | null;
  tempo_consigliato?: string | null;
  coaching_cues?: string[] | null;
  errori_comuni?: ExerciseError[] | null;
  note_sicurezza?: string | null;
  controindicazioni?: string[] | null;
}

/** POST /api/exercises/{id}/relations */
export interface ExerciseRelationCreate {
  related_exercise_id: number;
  tipo_relazione: string;
}

/** GET /api/exercises — lista paginata */
export interface ExerciseListResponse {
  items: Exercise[];
  total: number;
  page: number;
  page_size: number;
}

// ════════════════════════════════════════════════════════════
// WORKOUT PLAN (api/routers/workouts.py + api/schemas/workout.py)
// ════════════════════════════════════════════════════════════

export const OBIETTIVI_SCHEDA = ["forza", "ipertrofia", "resistenza", "dimagrimento", "generale"] as const;
export type ObiettivoScheda = (typeof OBIETTIVI_SCHEDA)[number];

export const LIVELLI_SCHEDA = ["beginner", "intermedio", "avanzato"] as const;
export type LivelloScheda = (typeof LIVELLI_SCHEDA)[number];

/** Esercizio dentro una sessione — output enriched */
export interface WorkoutExerciseRow {
  id: number;
  id_esercizio: number;
  esercizio_nome: string;
  esercizio_categoria: string;
  esercizio_attrezzatura: string;
  ordine: number;
  serie: number;
  ripetizioni: string;
  tempo_riposo_sec: number;
  tempo_esecuzione: string | null;
  note: string | null;
}

/** Sessione di allenamento — output con esercizi nested */
export interface WorkoutSession {
  id: number;
  numero_sessione: number;
  nome_sessione: string;
  focus_muscolare: string | null;
  durata_minuti: number;
  note: string | null;
  esercizi: WorkoutExerciseRow[];
}

/** Scheda allenamento — output completo */
export interface WorkoutPlan {
  id: number;
  id_cliente: number | null;
  client_nome: string | null;
  client_cognome: string | null;
  nome: string;
  obiettivo: string;
  livello: string;
  durata_settimane: number;
  sessioni_per_settimana: number;
  note: string | null;
  ai_commentary: string | null;
  sessioni: WorkoutSession[];
  created_at: string | null;
  updated_at: string | null;
}

/** GET /api/workouts — lista paginata */
export interface WorkoutPlanListResponse {
  items: WorkoutPlan[];
  total: number;
  page: number;
  page_size: number;
}

/** Esercizio input per creazione/modifica sessione */
export interface WorkoutExerciseInput {
  id_esercizio: number;
  ordine: number;
  serie?: number;
  ripetizioni?: string;
  tempo_riposo_sec?: number;
  tempo_esecuzione?: string | null;
  note?: string | null;
}

/** Sessione input per creazione/modifica scheda */
export interface WorkoutSessionInput {
  nome_sessione: string;
  focus_muscolare?: string | null;
  durata_minuti?: number;
  note?: string | null;
  esercizi: WorkoutExerciseInput[];
}

/** POST /api/workouts */
export interface WorkoutPlanCreate {
  id_cliente?: number | null;
  nome: string;
  obiettivo: string;
  livello: string;
  durata_settimane?: number;
  sessioni_per_settimana?: number;
  note?: string | null;
  sessioni: WorkoutSessionInput[];
}

/** PUT /api/workouts/{id} (partial update metadati) */
export interface WorkoutPlanUpdate {
  id_cliente?: number | null;
  nome?: string | null;
  obiettivo?: string | null;
  livello?: string | null;
  durata_settimane?: number | null;
  sessioni_per_settimana?: number | null;
  note?: string | null;
}
