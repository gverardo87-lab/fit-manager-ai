// src/components/agenda/calendar-setup.ts
/**
 * Setup react-big-calendar: localizer italiano, colori per categoria, mapper.
 *
 * File puro TS — nessun import React.
 */

import { dateFnsLocalizer } from "react-big-calendar";
import { format, parse, startOfWeek, getDay } from "date-fns";
import { it } from "date-fns/locale";
import type { EventCategory } from "@/types/api";
import type { EventHydrated } from "@/hooks/useAgenda";

// ── Localizer italiano (lunedi' primo giorno) ──

const locales = { "it-IT": it };

export const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: (date: Date) => startOfWeek(date, { locale: it }),
  getDay,
  locales,
});

// ── CalendarEvent: adapter backend → react-big-calendar ──

export interface CalendarEvent {
  id: number;
  title: string;
  start: Date;
  end: Date;
  categoria: string;
  stato: string;
  id_cliente: number | null;
  id_contratto: number | null;
  note: string | null;
  cliente_nome: string | null;
  cliente_cognome: string | null;
}

/**
 * Converte un EventHydrated (date gia' Date objects) in CalendarEvent.
 */
export function toCalendarEvent(event: EventHydrated): CalendarEvent {
  return {
    id: event.id,
    title: event.titolo || event.categoria,
    start: event.data_inizio,
    end: event.data_fine,
    categoria: event.categoria,
    stato: event.stato,
    id_cliente: event.id_cliente,
    id_contratto: event.id_contratto,
    note: event.note,
    cliente_nome: event.cliente_nome,
    cliente_cognome: event.cliente_cognome,
  };
}

// ── Color System: Categoria x Stato (two-axis matrix) ──
//
// Asse 1 — CATEGORIA → border color (identita' costante)
// Asse 2 — STATO → background color (indicatore di stato)
//
// Esempio: PT Completato = bordo blu + sfondo verde

// Category border colors (identity — sempre visibili)
const CATEGORY_BORDERS: Record<string, string> = {
  PT:        "#3b82f6",  // blu
  SALA:      "#a1a1aa",  // grigio
  CORSO:     "#10b981",  // verde
  COLLOQUIO: "#f59e0b",  // ambra
};

const DEFAULT_BORDER = "#94a3b8";

// Category backgrounds (solo per stato Programmato)
interface StatusStyle {
  backgroundColor: string;
  color: string;
  opacity?: number;
}

const PROGRAMMATO_STYLES: Record<string, StatusStyle> = {
  PT:        { backgroundColor: "#dbeafe", color: "#1e3a5f" },
  SALA:      { backgroundColor: "#f4f4f5", color: "#3f3f46" },
  CORSO:     { backgroundColor: "#d1fae5", color: "#064e3b" },
  COLLOQUIO: { backgroundColor: "#fef3c7", color: "#78350f" },
};

const DEFAULT_PROGRAMMATO: StatusStyle = {
  backgroundColor: "#f1f5f9",
  color: "#334155",
};

// Status overrides (sovrascrivono il background della categoria)
const STATUS_OVERRIDES: Record<string, StatusStyle> = {
  Completato: { backgroundColor: "#dcfce7", color: "#166534" },
  Cancellato: { backgroundColor: "#f4f4f5", color: "#a1a1aa", opacity: 0.5 },
  Rinviato:   { backgroundColor: "#fef3c7", color: "#92400e" },
};

export function getEventStyle(event: CalendarEvent): React.CSSProperties {
  const borderColor = CATEGORY_BORDERS[event.categoria] ?? DEFAULT_BORDER;

  // Stato override ha la precedenza, poi background categoria, poi default
  const statusOverride = STATUS_OVERRIDES[event.stato];
  const base = statusOverride
    ?? PROGRAMMATO_STYLES[event.categoria]
    ?? DEFAULT_PROGRAMMATO;

  return {
    backgroundColor: base.backgroundColor,
    borderLeft: `3px solid ${borderColor}`,
    color: base.color,
    borderRadius: "4px",
    padding: "2px 4px",
    fontSize: "0.8rem",
    ...(base.opacity != null && { opacity: base.opacity }),
  };
}

// ── Legend data (per StatusLegendBar in page.tsx) ──

export interface StatusLegendItem {
  stato: string;
  label: string;
  backgroundColor: string;
  color: string;
}

export const STATUS_LEGEND: StatusLegendItem[] = [
  { stato: "Programmato", label: "Programmato", backgroundColor: "#dbeafe", color: "#1e3a5f" },
  { stato: "Completato",  label: "Completato",  backgroundColor: "#dcfce7", color: "#166534" },
  { stato: "Cancellato",  label: "Cancellato",  backgroundColor: "#f4f4f5", color: "#a1a1aa" },
  { stato: "Rinviato",    label: "Rinviato",    backgroundColor: "#fef3c7", color: "#92400e" },
];

export interface CategoryLegendItem {
  categoria: string;
  label: string;
  borderColor: string;
}

export const CATEGORY_LEGEND: CategoryLegendItem[] = [
  { categoria: "PT",        label: "Personal Training", borderColor: "#3b82f6" },
  { categoria: "SALA",      label: "Sala",              borderColor: "#a1a1aa" },
  { categoria: "CORSO",     label: "Corso",             borderColor: "#10b981" },
  { categoria: "COLLOQUIO", label: "Colloquio",         borderColor: "#f59e0b" },
];

// ── Messaggi italiani per react-big-calendar ──

export const italianMessages = {
  allDay: "Tutto il giorno",
  previous: "Indietro",
  next: "Avanti",
  today: "Oggi",
  month: "Mese",
  week: "Settimana",
  day: "Giorno",
  agenda: "Agenda",
  date: "Data",
  time: "Ora",
  event: "Evento",
  noEventsInRange: "Nessun evento in questo periodo",
  showMore: (total: number) => `+${total} altri`,
};

// ── Label categorie per UI ──

export const CATEGORY_LABELS: Record<EventCategory, string> = {
  PT: "Personal Training",
  SALA: "Sala",
  CORSO: "Corso",
  COLLOQUIO: "Colloquio",
};
