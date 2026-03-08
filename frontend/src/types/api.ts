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

/** Punto dati per il grafico giornaliero entrate/uscite + saldo */
export interface ChartDataPoint {
  giorno: number;
  entrate: number;
  uscite: number;
  saldo: number;
}

/** GET /api/movements/stats?anno=X&mese=Y */
export interface MovementStats {
  totale_entrate: number;
  totale_uscite_variabili: number;
  totale_uscite_fisse: number;
  margine_netto: number;
  saldo_inizio_mese: number;
  saldo_fine_mese: number;
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

/** DELETE /api/recurring-expenses/{id} */
export interface RecurringExpenseDeleteResponse {
  deleted_movements: number;
}

/** POST /api/recurring-expenses/{id}/close */
export interface RecurringExpenseCloseRequest {
  effective_mese_anno_key: string;
  last_occurrence_due: boolean;
}

/** POST /api/recurring-expenses/{id}/close */
export interface RecurringExpenseCloseResponse {
  cutoff_key: string;
  cutoff_data: string;
  created_last_due_movement: boolean;
  storni_creati: number;
  storni_rimossi: number;
}

/** POST /api/recurring-expenses/{id}/close-preview */
export interface RecurringExpenseClosePreviewResponse {
  cutoff_key: string;
  cutoff_data: string;
  created_last_due_movement: boolean;
  storni_creati_previsti: number;
  storni_rimossi_previsti: number;
  saldo_attuale_before: number;
  saldo_attuale_after: number;
  saldo_previsto_before: number;
  saldo_previsto_after: number;
  delta_saldo_attuale: number;
  delta_saldo_previsto: number;
  delta_netto: number;
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
  ledger_alerts: number;
  saldo_attuale: number;
}

export interface CashProtection {
  stato: "OK" | "ATTENZIONE" | "CRITICO";
  soglia_sicurezza: number;
  margine_sicurezza: number;
  copertura_giorni: number;
  uscite_fisse_mensili_stimate: number;
  burn_rate_variabile_mensile: number;
  costo_operativo_mensile: number;
}

/** GET /api/movements/balance */
export interface BalanceResponse {
  saldo_attuale: number;
  saldo_previsto: number;
  delta_movimenti_futuri: number;
  saldo_iniziale: number;
  totale_entrate_storico: number;
  totale_uscite_storico: number;
  totale_entrate_future_confermate: number;
  totale_uscite_future_confermate: number;
  data_riferimento: string;
  data_saldo_iniziale: string | null;
  protezione_cassa: CashProtection;
}

/** PUT /api/movements/saldo-iniziale */
export interface SaldoInizialeUpdate {
  saldo_iniziale_cassa: number;
  data_saldo_iniziale: string | null;
}

/** GET /api/movements/saldo-iniziale */
export interface SaldoInizialeResponse {
  saldo_iniziale_cassa: number;
  data_saldo_iniziale: string | null;
}

/** Response paginata movimenti con saldo fine periodo */
export interface MovementsPaginatedResponse extends PaginatedResponse<CashMovement> {
  saldo_fine_periodo: number;
}

/** POST /api/movements/impact-preview/* */
export interface ImpactPreviewResponse {
  operation: string;
  saldo_attuale_before: number;
  saldo_attuale_after: number;
  saldo_previsto_before: number;
  saldo_previsto_after: number;
  delta_saldo_attuale: number;
  delta_saldo_previsto: number;
  delta_netto: number;
  details: Record<string, unknown>;
}

/** GET /api/movements/audit-log */
export interface CashAuditTimelineItem {
  id: number;
  created_at: string; // ISO datetime
  entity_type: string;
  entity_id: number;
  action: string;
  flow_hint: "ENTRATA" | "USCITA" | null;
  reason: string | null;
  correlation_id: string | null;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  details: Record<string, unknown>;
  link_href: string | null;
  link_label: string | null;
}

/** GET /api/movements/audit-log */
export interface CashAuditTimelineResponse {
  items: CashAuditTimelineItem[];
  total: number;
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

/** Stato anamnesi nella coda readiness */
export type AnamnesiReadinessState = "missing" | "legacy" | "structured";

/** Step mancanti nella coda readiness */
export type ClinicalMissingStep =
  | "anamnesi_missing"
  | "anamnesi_legacy"
  | "baseline"
  | "workout";

/** Priorita operativa readiness */
export type ClinicalPriority = "high" | "medium" | "low";

/** Next action deterministica nella coda readiness */
export type ClinicalNextActionCode =
  | "collect_anamnesi"
  | "migrate_anamnesi"
  | "collect_baseline"
  | "assign_workout"
  | "ready";

/** Singolo cliente nella coda readiness clinica */
export interface ClinicalReadinessClientItem {
  client_id: number;
  client_nome: string;
  client_cognome: string;
  anamnesi_state: AnamnesiReadinessState;
  has_measurements: boolean;
  has_workout_plan: boolean;
  missing_steps: ClinicalMissingStep[];
  readiness_score: number;
  priority: ClinicalPriority;
  priority_score: number;
  next_action_code: ClinicalNextActionCode;
  next_action_label: string;
  next_action_href: string;
  next_due_date: string | null; // ISO date YYYY-MM-DD
  days_to_due: number | null;
  timeline_status: "overdue" | "today" | "upcoming_7d" | "upcoming_14d" | "future" | "none";
  timeline_reason: string | null;
}

/** Contatori aggregati della coda readiness */
export interface ClinicalReadinessSummary {
  total_clients: number;
  ready_clients: number;
  missing_anamnesi: number;
  legacy_anamnesi: number;
  missing_measurements: number;
  missing_workout_plan: number;
  high_priority: number;
  medium_priority: number;
  low_priority: number;
}

/** GET /api/dashboard/clinical-readiness */
export interface ClinicalReadinessResponse {
  summary: ClinicalReadinessSummary;
  items: ClinicalReadinessClientItem[];
}

/** GET /api/dashboard/clinical-readiness/worklist */
export interface ClinicalReadinessWorklistResponse {
  summary: ClinicalReadinessSummary;
  items: ClinicalReadinessClientItem[];
  total: number;
  page: number;
  page_size: number;
}

// ════════════════════════════════════════════════════════════
// TRAINING METHODOLOGY — MyTrainer (api/schemas/training_methodology.py)
// ════════════════════════════════════════════════════════════

/** Compliance per singola sessione di un piano */
export interface SessionComplianceItem {
  session_id: number;
  session_name: string;
  expected: number;
  completed: number;
  compliance_pct: number;
}

/** Singolo piano nella worklist MyTrainer */
export interface TrainingMethodologyPlanItem {
  plan_id: number;
  plan_nome: string;
  client_id: number;
  client_nome: string;
  client_cognome: string;
  obiettivo: string;
  livello: string;
  status: string;
  sessioni_count: number;
  data_inizio: string | null;
  data_fine: string | null;
  science_score: number;
  sotto_mev_count: number;
  sopra_mrv_count: number;
  ottimali_count: number;
  squilibri_count: number;
  warning_count: number;
  volume_totale: number;
  compliance_pct: number;
  sessions_expected: number;
  sessions_completed: number;
  session_compliance: SessionComplianceItem[];
  worst_session_name: string | null;
  session_imbalance: boolean;
  training_score: number;
  priority: string;
  priority_score: number;
  next_action_code: string;
  next_action_label: string;
  next_action_href: string;
  analyzable: boolean;
}

/** KPI aggregati MyTrainer hero */
export interface TrainingMethodologySummary {
  total_plans: number;
  active_plans: number;
  avg_science_score: number;
  avg_compliance: number;
  avg_training_score: number;
  plans_with_issues: number;
  plans_excellent: number;
  high_priority: number;
  medium_priority: number;
  low_priority: number;
}

/** GET /api/training-methodology/worklist */
export interface TrainingMethodologyWorklistResponse {
  summary: TrainingMethodologySummary;
  items: TrainingMethodologyPlanItem[];
  total: number;
  page: number;
  page_size: number;
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
  checksum: string | null;
}

/** POST /api/backup/create */
export interface BackupCreateResponse {
  filename: string;
  size_bytes: number;
  checksum: string;
  message: string;
}

/** POST /api/backup/verify/{filename} */
export interface BackupVerifyResponse {
  filename: string;
  valid: boolean;
  checksum_match: boolean;
  integrity_ok: boolean;
  detail: string;
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

/** Tassonomia: muscolo anatomico con ruolo nell'esercizio */
export interface TaxonomyMuscle {
  id: number;
  nome: string;
  nome_en: string;
  gruppo: string;
  ruolo: "primary" | "secondary" | "stabilizer";
  attivazione: number | null;
}

/** Tassonomia: articolazione coinvolta nell'esercizio */
export interface TaxonomyJoint {
  id: number;
  nome: string;
  nome_en: string;
  tipo: string;
  ruolo: "agonist" | "stabilizer";
  rom_gradi: number | null;
}

/** Tassonomia: condizione medica associata all'esercizio */
export interface TaxonomyCondition {
  id: number;
  nome: string;
  nome_en: string;
  categoria: string; // orthopedic, cardiovascular, metabolic, neurological
  severita: "avoid" | "caution" | "modify";
  nota: string | null;
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
  controindicazioni: string[];
  // Biomeccanica avanzata (tassonomia v3)
  catena_cinetica: string | null;
  piano_movimento: string | null;
  tipo_contrazione: string | null;

  // Demand Vector 10D — costo biomeccanico-funzionale (scala 0-4)
  skill_demand: number | null;
  coordination_demand: number | null;
  stability_demand: number | null;
  ballistic_demand: number | null;
  impact_demand: number | null;
  axial_load_demand: number | null;
  shoulder_complex_demand: number | null;
  lumbar_load_demand: number | null;
  grip_demand: number | null;
  metabolic_demand: number | null;

  muscle_map_url: string | null;
  is_builtin: boolean;
  created_at: string | null;
  media: ExerciseMedia[];
  relazioni: ExerciseRelation[];
  muscoli_dettaglio: TaxonomyMuscle[];
  articolazioni: TaxonomyJoint[];
  condizioni: TaxonomyCondition[];
  suggerimenti: string[];
}

// ═══════════════════════════════════════════════════════════════
// SAFETY MAP (anamnesi × condizioni mediche)
// ═══════════════════════════════════════════════════════════════

/** Singola condizione medica rilevante per un esercizio nella safety map */
export interface SafetyConditionDetail {
  id: number;
  nome: string;
  severita: "avoid" | "caution" | "modify";
  nota: string | null;
  categoria: string;
  body_tags: string[];  // zone anatomiche per Risk Body Map
}

/** Safety entry per un singolo esercizio */
export interface ExerciseSafetyEntry {
  exercise_id: number;
  severity: "avoid" | "caution" | "modify";
  conditions: SafetyConditionDetail[];
}

/** Flag farmacologico rilevante per la programmazione */
export interface MedicationFlag {
  flag: string;   // beta_blocker, anticoagulant, corticosteroid, insulin, statin
  nota: string;   // nota clinica per il trainer
}

/** GET /api/exercises/safety-map?client_id=X */
export interface SafetyMapResponse {
  client_id: number;
  client_nome: string;
  has_anamnesi: boolean;
  condition_count: number;
  condition_names: string[];
  entries: Record<number, ExerciseSafetyEntry>;
  medication_flags: MedicationFlag[];
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
  catena_cinetica?: string | null;
  piano_movimento?: string | null;
  tipo_contrazione?: string | null;
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
  carico_kg: number | null;
  note: string | null;
}

// Tipo blocco — allineato a VALID_BLOCK_TYPES in api/schemas/workout.py
export const BLOCK_TYPES = ["circuit", "superset", "tabata", "amrap", "emom", "for_time"] as const;
export type BlockType = (typeof BLOCK_TYPES)[number];

export const BLOCK_TYPE_LABELS: Record<BlockType, string> = {
  circuit:  "Circuito",
  superset: "Superset",
  tabata:   "Tabata",
  amrap:    "AMRAP",
  emom:     "EMOM",
  for_time: "For Time",
};

/** Blocco strutturato — circuit, tabata, AMRAP, EMOM, superset */
export interface SessionBlock {
  id: number;
  tipo_blocco: BlockType;
  ordine: number;
  nome: string | null;
  giri: number;
  durata_lavoro_sec: number | null;
  durata_riposo_sec: number | null;
  durata_blocco_sec: number | null;
  note: string | null;
  esercizi: WorkoutExerciseRow[];
}

/** Sessione di allenamento — output con esercizi straight + blocchi nested */
export interface WorkoutSession {
  id: number;
  numero_sessione: number;
  nome_sessione: string;
  focus_muscolare: string | null;
  durata_minuti: number;
  note: string | null;
  esercizi: WorkoutExerciseRow[];
  blocchi: SessionBlock[];
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
  sessioni: WorkoutSession[];
  created_at: string | null;
  updated_at: string | null;
  data_inizio: string | null;
  data_fine: string | null;
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
  carico_kg?: number | null;
  note?: string | null;
}

/** Blocco input per creazione/modifica scheda */
export interface SessionBlockInput {
  tipo_blocco: BlockType;
  ordine: number;
  nome?: string | null;
  giri?: number;
  durata_lavoro_sec?: number | null;
  durata_riposo_sec?: number | null;
  durata_blocco_sec?: number | null;
  note?: string | null;
  esercizi: WorkoutExerciseInput[];
}

/** Sessione input per creazione/modifica scheda */
export interface WorkoutSessionInput {
  nome_sessione: string;
  focus_muscolare?: string | null;
  durata_minuti?: number;
  note?: string | null;
  esercizi: WorkoutExerciseInput[];
  blocchi?: SessionBlockInput[];
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
  data_inizio?: string | null;
  data_fine?: string | null;
}

// ════════════════════════════════════════════════════════════
// WORKOUT LOGS (api/schemas/workout_log.py)
// ════════════════════════════════════════════════════════════

/** POST /api/clients/{id}/workout-logs */
export interface WorkoutLogCreate {
  id_scheda: number;
  id_sessione: number;
  data_esecuzione: string; // ISO date "YYYY-MM-DD"
  id_evento?: number | null;
  note?: string | null;
}

/** WorkoutLogResponse — restituito da GET/POST */
export interface WorkoutLog {
  id: number;
  id_scheda: number;
  id_sessione: number;
  id_cliente: number;
  data_esecuzione: string;
  id_evento: number | null;
  note: string | null;
  created_at: string | null;
  scheda_nome: string;
  sessione_nome: string;
}

/** GET /api/clients/{id}/workout-logs */
export interface WorkoutLogListResponse {
  items: WorkoutLog[];
  total: number;
}

// ════════════════════════════════════════════════════════════
// MISURAZIONI CORPOREE (api/schemas/measurement.py)
// ════════════════════════════════════════════════════════════

export const METRIC_CATEGORIES = [
  "antropometrica",
  "composizione",
  "circonferenza",
  "cardiovascolare",
  "forza",
] as const;
export type MetricCategory = (typeof METRIC_CATEGORIES)[number];

export const METRIC_CATEGORY_LABELS: Record<MetricCategory, string> = {
  antropometrica: "Antropometrica",
  composizione: "Composizione Corporea",
  circonferenza: "Circonferenze",
  cardiovascolare: "Cardiovascolare",
  forza: "Forza",
};

/** GET /api/metrics — catalogo metriche */
export interface Metric {
  id: number;
  nome: string;
  nome_en: string;
  unita_misura: string;
  categoria: MetricCategory;
  ordinamento: number;
}

/** Singolo valore misurato (input) */
export interface MeasurementValueInput {
  id_metrica: number;
  valore: number;
}

/** POST /api/clients/{id}/measurements */
export interface MeasurementCreate {
  data_misurazione: string;
  note?: string | null;
  valori: MeasurementValueInput[];
}

/** PUT /api/clients/{id}/measurements/{session_id} */
export interface MeasurementUpdate {
  data_misurazione?: string | null;
  note?: string | null;
  valori?: MeasurementValueInput[] | null;
}

/** Singolo valore misurato (output enriched) */
export interface MeasurementValue {
  id_metrica: number;
  nome_metrica: string;
  unita: string;
  valore: number;
}

/** Info obiettivo auto-completato — per toast frontend */
export interface GoalCompletionInfo {
  id: number;
  nome_metrica: string;
  valore_target: number;
  valore_raggiunto: number;
}

/** Sessione di misurazione — output con valori nested */
export interface Measurement {
  id: number;
  id_cliente: number;
  data_misurazione: string;
  note: string | null;
  valori: MeasurementValue[];
  obiettivi_raggiunti?: GoalCompletionInfo[];
}

/** GET /api/clients/{id}/measurements — lista paginata */
export interface MeasurementListResponse {
  items: Measurement[];
  total: number;
}

// ════════════════════════════════════════════════════════════
// CLIENT GOALS (api/schemas/goal.py)
// ════════════════════════════════════════════════════════════

export const GOAL_DIRECTIONS = ["aumentare", "diminuire", "mantenere"] as const;
export type GoalDirection = (typeof GOAL_DIRECTIONS)[number];

export const GOAL_DIRECTION_LABELS: Record<GoalDirection, string> = {
  aumentare: "Aumentare",
  diminuire: "Diminuire",
  mantenere: "Mantenere",
};

export const GOAL_STATUSES = ["attivo", "raggiunto", "abbandonato"] as const;
export type GoalStatus = (typeof GOAL_STATUSES)[number];

export const GOAL_STATUS_LABELS: Record<GoalStatus, string> = {
  attivo: "Attivo",
  raggiunto: "Raggiunto",
  abbandonato: "Abbandonato",
};

/** POST /api/clients/{id}/goals */
export interface GoalCreate {
  id_metrica: number;
  direzione: GoalDirection;
  valore_target?: number | null;
  data_inizio: string;
  data_scadenza?: string | null;
  priorita?: number;
  note?: string | null;
}

/** PUT /api/clients/{id}/goals/{goalId} */
export interface GoalUpdate {
  direzione?: GoalDirection | null;
  valore_target?: number | null;
  data_scadenza?: string | null;
  priorita?: number | null;
  stato?: GoalStatus | null;
  note?: string | null;
}

/** Progresso computato dal backend */
export interface GoalProgress {
  valore_corrente: number | null;
  data_corrente: string | null;
  delta_da_baseline: number | null;
  percentuale_progresso: number | null;
  tendenza_positiva: boolean | null;
  velocita_settimanale: number | null;
  num_misurazioni: number;
}

/** Obiettivo con progresso inline */
export interface ClientGoal {
  id: number;
  id_cliente: number;
  id_metrica: number;
  nome_metrica: string;
  unita_misura: string;
  categoria_metrica: string;
  tipo_obiettivo: "corporeo" | "atletico";
  direzione: GoalDirection;
  valore_target: number | null;
  valore_baseline: number | null;
  data_baseline: string | null;
  data_inizio: string;
  data_scadenza: string | null;
  priorita: number;
  stato: GoalStatus;
  completed_at: string | null;
  completato_automaticamente: boolean;
  note: string | null;
  progresso: GoalProgress;
}

/** GET /api/clients/{id}/goals */
export interface GoalListResponse {
  items: ClientGoal[];
  total: number;
  attivi: number;
  raggiunti: number;
}

// ════════════════════════════════════════════════════════════
// ASSISTANT (api/schemas/assistant.py)
// ════════════════════════════════════════════════════════════

/** Entita' risolta dal parser */
export interface ResolvedEntity {
  type: string;
  raw: string;
  value: string | number;
  label: string;
  confidence: number;
}

/** Ambiguita' — piu' candidati possibili */
export interface AmbiguityItem {
  field: string;
  candidates: ResolvedEntity[];
  message: string;
}

/** Singola operazione riconosciuta */
export interface ParsedOperation {
  intent: string;
  payload: Record<string, unknown>;
  preview_label: string;
  confidence: number;
}

/** POST /api/assistant/parse — request */
export interface AssistantParseRequest {
  text: string;
}

/** POST /api/assistant/parse — response */
export interface AssistantParseResponse {
  success: boolean;
  operations: ParsedOperation[];
  ambiguities: AmbiguityItem[];
  entities: ResolvedEntity[];
  message: string;
  raw_text: string;
}

/** POST /api/assistant/commit — request */
export interface AssistantCommitRequest {
  intent: string;
  payload: Record<string, unknown>;
}

/** POST /api/assistant/commit — response */
export interface AssistantCommitResponse {
  success: boolean;
  message: string;
  created_id: number | null;
  entity_type: string;
  invalidate: string[];
  navigate_to: string | null;
}

// ════════════════════════════════════════════════════════════
// TRAINING SCIENCE ENGINE (api/services/training_science/types.py + periodization.py)
// ════════════════════════════════════════════════════════════

/** Obiettivo di allenamento — determina tutti i parametri di carico */
export const TS_OBIETTIVI = ["forza", "ipertrofia", "resistenza", "dimagrimento", "tonificazione"] as const;
export type TSObjective = (typeof TS_OBIETTIVI)[number];

/** Livello di esperienza — determina volume tollerabile (MEV/MAV/MRV) */
export const TS_LIVELLI = ["principiante", "intermedio", "avanzato"] as const;
export type TSLevel = (typeof TS_LIVELLI)[number];

/** 15 gruppi muscolari funzionali (NSCA 2016, Contreras 2010) */
export const TS_GRUPPI_MUSCOLARI = [
  "petto", "dorsali", "deltoide_anteriore", "deltoide_laterale", "deltoide_posteriore",
  "bicipiti", "tricipiti", "quadricipiti", "femorali", "glutei",
  "polpacci", "trapezio", "core", "avambracci", "adduttori",
] as const;
export type TSMuscleGroup = (typeof TS_GRUPPI_MUSCOLARI)[number];

/** Pattern di movimento — 9 compound + 9 isolation */
export const TS_PATTERN = [
  "push_h", "push_v", "squat", "hinge", "pull_h", "pull_v", "core", "rotation", "carry",
  "hip_thrust", "curl", "extension_tri", "lateral_raise", "face_pull",
  "calf_raise", "leg_curl", "leg_extension", "adductor",
] as const;
export type TSPattern = (typeof TS_PATTERN)[number];

/** Tipo di split settimanale */
export type TSSplitType = "full_body" | "upper_lower" | "push_pull_legs";

/** Ruolo funzionale della sessione */
export type TSSessionRole = "full_body" | "upper" | "lower" | "push" | "pull" | "legs";

/** Priorita' di ordinamento nella sessione (NSCA: SNC-demanding first) */
export type TSSlotPriority = 1 | 2 | 3 | 4 | 5 | 6;

/** Parametri di carico per obiettivo (NSCA 2016, ACSM 2009, Schoenfeld 2017) */
export interface TSParametriCarico {
  obiettivo: TSObjective;
  intensita_min: number;
  intensita_max: number;
  rep_min: number;
  rep_max: number;
  serie_compound: [number, number];
  serie_isolation: [number, number];
  riposo_compound: [number, number];
  riposo_isolation: [number, number];
  percentuale_compound: number;
  freq_per_muscolo: [number, number];
  fattore_volume: number;
  fonte: string;
}

/** Volume target per gruppo muscolare (Israetel RP 2020, Schoenfeld 2017) */
export interface TSVolumeTarget {
  muscolo: TSMuscleGroup;
  mev: number;
  mav_min: number;
  mav_max: number;
  mrv: number;
  note: string;
}

/** Slot in una sessione — "qui va un esercizio di questo tipo" */
export interface TSSlotSessione {
  pattern: TSPattern;
  priorita: TSSlotPriority;
  serie: number;
  rep_min: number;
  rep_max: number;
  riposo_sec: number;
  muscolo_target: TSMuscleGroup | null;
  note: string;
  /** Carico in kg (opzionale). Abilita tonnellaggio e intensità relativa. NSCA 2016. */
  carico_kg: number | null;
}

/** Template sessione con slot tipizzati */
export interface TSTemplateSessione {
  nome: string;
  ruolo: TSSessionRole;
  focus: string;
  slots: TSSlotSessione[];
}

/** Piano settimanale completo generato dal motore scientifico */
export interface TSTemplatePiano {
  frequenza: number;
  obiettivo: TSObjective;
  livello: TSLevel;
  tipo_split: TSSplitType;
  sessioni: TSTemplateSessione[];
  note_generazione: string[];
  /** Sesso biologico ('M' o 'F'). Scala target MAV per differenze ormonali. */
  sesso?: string | null;
  /** Eta' in anni. Scala target MAV per capacita' di recupero. */
  eta?: number | null;
}

/** Volume effettivo calcolato per un gruppo muscolare */
export interface TSVolumeEffettivo {
  muscolo: TSMuscleGroup;
  serie_effettive: number;
  target_mev: number;
  target_mav_min: number;
  target_mav_max: number;
  target_mrv: number;
  stato: "sotto_mev" | "mev_mav" | "ottimale" | "sopra_mav" | "sopra_mrv";
  /** Tensione meccanica in kg (tonnage × EMG). Presente solo con carico. Schoenfeld 2010. */
  tensione_kg: number | null;
}

/** Analisi volume di un piano */
export interface TSAnalisiVolume {
  per_muscolo: TSVolumeEffettivo[];
  volume_totale_settimana: number;
  muscoli_sotto_mev: string[];
  muscoli_sopra_mrv: string[];
  /** True se almeno uno slot ha carico_kg. Le serie sono pesate per intensità (dose-response). */
  has_load_data: boolean;
  /** Volume-Load totale settimanale in kg (NSCA 2016). Presente solo con carico. */
  tonnellaggio_totale: number | null;
  /** Zona NSCA prevalente. Presente solo con carico. */
  zona_prevalente: string | null;
}

/** Analisi rapporti biomeccanici */
export interface TSAnalisiBalance {
  rapporti: Record<string, number>;
  target: Record<string, number>;
  squilibri: string[];
}

/** Volume ipertrofico di un singolo esercizio su un muscolo */
export interface TSContributoEsercizio {
  nome_esercizio: string;
  pattern: TSPattern;
  serie: number;
  contributo_emg: number;
  serie_ipertrofiche: number;
  /** Carico in kg dello slot (se presente nel piano) */
  carico_kg: number | null;
}

/** Dettaglio completo per un muscolo — drill-down nella tab analisi */
export interface TSDettaglioMuscolo {
  muscolo: TSMuscleGroup;
  serie_effettive: number;
  target_mev: number;
  target_mav_min: number;
  target_mav_max: number;
  target_mrv: number;
  stato: "sotto_mev" | "mev_mav" | "ottimale" | "sopra_mav" | "sopra_mrv";
  frequenza: number;
  contributi: TSContributoEsercizio[];
  /** Tensione meccanica in kg (Schoenfeld 2010). Presente solo con carico. */
  tensione_kg: number | null;
}

/** Dettaglio di un rapporto biomeccanico con volume per lato */
export interface TSDettaglioRapporto {
  nome: string;
  valore: number;
  target: number;
  tolleranza: number;
  in_tolleranza: boolean;
  volume_numeratore: number;
  volume_denominatore: number;
  fonte: string;
}

/** Overlap muscolare tra due sessioni consecutive */
export interface TSDettaglioRecovery {
  sessione_a: string;
  sessione_b: string;
  muscoli_overlap: string[];
  serie_overlap_a: Record<string, number>;
  serie_overlap_b: Record<string, number>;
}

/** Tonnellaggio calcolato per un singolo slot con carico assegnato */
export interface TSTonnellaggioSlotAnalisi {
  pattern: string;
  sessione: string;
  serie: number;
  rep_medie: number;
  carico_kg: number;
  /** serie × rep_medie × carico_kg (Haff & Triplett, NSCA 2016) */
  tonnellaggio: number;
  /** %1RM se 1RM noto (Kraemer & Ratamess 2004) */
  intensita_relativa: number | null;
  /** Zona NSCA (massimale/sub_massimale/ipertrofia/resistenza/attivazione) */
  zona_intensita: string | null;
}

/** Analisi biomeccanica Volume-Load — tonnage + tensione meccanica per muscolo.
 * NSCA 2016, McBride 2009, Schoenfeld 2010 (mechanical tension), Contreras 2010 (EMG). */
export interface TSAnalisiTonnellaggio {
  tonnellaggio_totale: number;
  tonnellaggio_per_sessione: Record<string, number>;
  intensita_media_ponderata: number | null;
  slot_detail: TSTonnellaggioSlotAnalisi[];
  zona_prevalente: string | null;
  /** Tensione meccanica per gruppo muscolare (kg) — tonnage × EMG coefficient.
   * Schoenfeld 2010: mechanical tension = primary hypertrophy driver. */
  tensione_per_muscolo: Record<string, number>;
  /** Tensione ipertrofica per muscolo (kg) — pesata con hypertrophy weights.
   * Israetel RP 2020 half-set rule, soglia EMG 40% MVC (Schoenfeld 2017). */
  tensione_ipertrofica_per_muscolo: Record<string, number>;
  fonte: string;
}

/** Analisi completa 4D di un piano — score 0-100 + dati strutturati */
export interface TSAnalisiPiano {
  volume: TSAnalisiVolume;
  balance: TSAnalisiBalance;
  warnings: string[];
  score: number;
  dettaglio_muscoli: TSDettaglioMuscolo[];
  dettaglio_rapporti: TSDettaglioRapporto[];
  frequenza_per_muscolo: Record<string, number>;
  recovery_overlaps: TSDettaglioRecovery[];
  /** Volume-Load (v3) — presente solo se almeno uno slot ha carico_kg. NSCA 2016. */
  tonnellaggio: TSAnalisiTonnellaggio | null;
}

/** Prescrizione di intensità per una settimana del mesociclo (Zourdos 2016, NSCA 2016) */
export interface TSIntensityPrescription {
  rpe_min: number;
  rpe_max: number;
  rir_min: number;
  rir_max: number;
  pct_1rm_min: number;
  pct_1rm_max: number;
  /** Zona NSCA prevalente (massimale/sub_massimale/ipertrofia/resistenza/attivazione) */
  zona: string;
  nota: string;
}

/** Configurazione singola settimana nel mesociclo */
export interface TSSettimanaConfig {
  numero: number;
  fase: "accumulazione" | "intensificazione" | "overreaching" | "deload";
  fattore_volume: number;
  /** Prescrizione intensità: RPE/RIR + %1RM + zona NSCA (Zourdos 2016, Helms 2019) */
  intensita: TSIntensityPrescription;
  note: string;
}

/** Mesociclo completo — piano base + variazione volume nel tempo */
export interface TSMesociclo {
  piano_base: TSTemplatePiano;
  settimane: TSSettimanaConfig[];
  piani_settimanali: TSTemplatePiano[];
  durata_settimane: number;
}

/** Obiettivo builder SMART lato UI/runtime orchestration */
export type TSBuilderObjective = "generale" | "forza" | "ipertrofia" | "resistenza" | "dimagrimento";

/** Livello builder SMART: auto o scelta esplicita compatibile col workout builder */
export type TSBuilderLevelChoice = "auto" | "beginner" | "intermedio" | "avanzato";

/** Modalita' builder SMART */
export type TSBuilderMode = "general" | "performance" | "clinical";

/** Severita' safety per candidato ranking */
export type TSSafetySeverity = "avoid" | "modify" | "caution" | null;

/** Bucket ordinato per presentare i candidati in UI */
export type TSCandidateBucket = "recommended" | "allowed" | "discouraged";

/** Stato sintetico anamnesi lato profile resolver */
export type TSAnamnesiState = "missing" | "legacy" | "structured";

/** Preset intenzionale inviato dal builder SMART */
export interface TSPlanPresetInput {
  frequenza: number;
  obiettivo_builder: TSBuilderObjective;
  livello_choice: TSBuilderLevelChoice;
  livello_override?: Exclude<TSBuilderLevelChoice, "auto"> | null;
  mode?: TSBuilderMode;
  durata_target_min?: number | null;
}

/** Override operativi del trainer sul ranking */
export interface TSTrainerOverridesInput {
  excluded_exercise_ids?: number[];
  preferred_exercise_ids?: number[];
  pinned_exercise_ids_by_slot?: Record<string, number>;
  notes?: string | null;
}

/** POST /api/training-science/plan-package */
export interface TSPlanPackageRequest {
  client_id?: number | null;
  preset: TSPlanPresetInput;
  trainer_overrides?: TSTrainerOverridesInput;
}

/** Profilo scientifico risolto lato backend */
export interface TSScientificProfileResolved {
  obiettivo_builder: TSBuilderObjective;
  obiettivo_scientifico: TSObjective;
  livello_scientifico: TSLevel;
  livello_workout: "beginner" | "intermedio" | "avanzato";
  mode: TSBuilderMode;
  anamnesi_state: TSAnamnesiState;
  safety_condition_count: number;
  profile_warnings: string[];
}

/** Slot canonico backend-owned con identita' stabile */
export interface TSCanonicalSlot {
  slot_id: string;
  pattern: TSPattern;
  priorita: TSSlotPriority;
  serie: number;
  rep_min: number;
  rep_max: number;
  riposo_sec: number;
  muscolo_target: TSMuscleGroup | null;
  note: string;
}

/** Sessione canonica backend-owned */
export interface TSCanonicalSession {
  session_id: string;
  nome: string;
  ruolo: TSSessionRole;
  focus: string;
  slots: TSCanonicalSlot[];
}

/** Piano scientifico canonico restituito dal backend */
export interface TSCanonicalPlan {
  plan_id: string;
  frequenza: number;
  obiettivo: TSObjective;
  livello: TSLevel;
  tipo_split: TSSplitType;
  sessioni: TSCanonicalSession[];
  note_generazione: string[];
}

/** Candidato rankato per slot canonico */
export interface TSSlotCandidate {
  slot_id: string;
  exercise_id: number;
  rank: number;
  total_score: number;
  safety_severity: TSSafetySeverity;
  bucket: TSCandidateBucket;
  rationale: string[];
  adaptation_hint: string | null;
}

/** Binding tra slot canonico ed esercizio selezionato nella projection */
export interface TSSlotBinding {
  session_id: string;
  slot_id: string;
  exercise_id: number;
  candidate_rank: number;
}

/** Draft workout save-compatible derivato dal canonico */
export interface TSWorkoutProjection {
  draft: WorkoutPlanCreate;
  slot_bindings: TSSlotBinding[];
}

/** Verdetto feasibility per-esercizio (solo non-feasible esposti) */
export type TSFeasibilityVerdict = "feasible" | "discouraged" | "infeasible_for_auto_draft";

export interface TSExerciseFeasibilityEntry {
  verdict: TSFeasibilityVerdict;
  reason_codes: string[];
}

/** Contatori sintetici del feasibility engine pre-ranking */
export interface TSFeasibilitySummary {
  feasible_count: number;
  discouraged_count: number;
  infeasible_count: number;
  demand_ceiling_violations: number;
  demand_family_exclusions: number;
  demand_family_discouraged: number;
  infeasible_by_beginner_gate: number;
  infeasible_by_safety: number;
  infeasible_by_demand: number;
  discouraged_by_safety: number;
  discouraged_by_demand: number;
}

/** Tracciabilita' completa: versioni sottosistemi + riferimenti benchmark */
export interface TSValidationMetadata {
  protocol_id: string;
  protocol_registry_version: string;
  constraint_profile_id: string;
  constraint_engine_version: string;
  evidence_registry_version: string;
  feasibility_engine_version: string;
  validation_case_refs: string[];
  generated_at: string;
}

/** Versioni dei sottosistemi del package */
export interface TSPlanPackageEngineInfo {
  planner_version: string;
  ranking_version: string;
  profile_version: string;
}

/** Stato dichiarato del protocollo selezionato dal registry */
export type TSProtocolStatus =
  | "supported"
  | "clinical_only"
  | "research_only"
  | "unsupported_by_policy";

/** Severita' del primo constraint adapter read-only */
export type TSConstraintSeverity = "hard_fail" | "soft_warning" | "optimization_target";

/** Scope del finding nel report vincoli */
export type TSConstraintScope = "protocol" | "weekly_plan" | "session" | "adjacent_sessions";

/** Stato sintetico di finding/report */
export type TSConstraintOverallStatus = "pass" | "warn" | "fail";

/** Metadata read-only del protocollo SMART/KineScore selezionato */
export interface TSPlanPackageProtocolInfo {
  protocol_id: string;
  label: string;
  status: TSProtocolStatus;
  exact_match: boolean;
  registry_version: string;
  validation_case_ids: string[];
  selection_rationale: string[];
}

/** Singolo finding del constraint adapter */
export interface TSConstraintFinding {
  rule_id: string;
  severity: TSConstraintSeverity;
  scope: TSConstraintScope;
  status: TSConstraintOverallStatus;
  message: string;
}

/** Sintesi del report vincoli */
export interface TSConstraintEvaluationSummary {
  overall_status: TSConstraintOverallStatus;
  hard_fail_count: number;
  soft_warning_count: number;
  optimization_target_count: number;
}

/** Report read-only dei vincoli del protocollo sul piano legacy */
export interface TSConstraintEvaluationReport {
  protocol_id: string;
  constraint_profile_id: string;
  analyzer_score: number;
  findings: TSConstraintFinding[];
  summary: TSConstraintEvaluationSummary;
}

/** Envelope completo per il cutover SMART backend-first */
export interface TSPlanPackage {
  scientific_profile: TSScientificProfileResolved;
  canonical_plan: TSCanonicalPlan;
  rankings: Record<string, TSSlotCandidate[]>;
  workout_projection: TSWorkoutProjection;
  warnings: string[];
  protocol: TSPlanPackageProtocolInfo;
  constraint_evaluation: TSConstraintEvaluationReport;
  feasibility_summary: TSFeasibilitySummary;
  feasibility_details: Record<number, TSExerciseFeasibilityEntry>;
  validation: TSValidationMetadata;
  engine: TSPlanPackageEngineInfo;
}


// ── Portale Clienti Self-Service (UPG-2026-03-06-01) ────────────────────────

export interface ShareTokenResponse {
  token: string;
  url: string;          // path relativo: /public/anamnesi/{token}
  expires_at: string;   // ISO datetime
  client_name: string;  // feedback per il trainer
}

export interface AnamnesiValidateResponse {
  client_name: string;  // "Marco R."
  trainer_name: string; // "Chiara B."
  has_existing: boolean;
  scope: string;
}
