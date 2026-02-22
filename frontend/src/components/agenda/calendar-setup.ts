// src/components/agenda/calendar-setup.ts
/**
 * Setup react-big-calendar: localizer italiano, colori per categoria, mapper.
 *
 * File puro TS — nessun import React.
 */

import { dateFnsLocalizer } from "react-big-calendar";
import { format, parse, startOfWeek, getDay } from "date-fns";
import { it } from "date-fns/locale";
import { parseISO } from "date-fns";
import type { Event as ApiEvent, EventCategory } from "@/types/api";

// ── Localizer italiano (lunedi' primo giorno) ──

const locales = { "it-IT": it };

export const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date(), { weekStartsOn: 1 }),
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
}

/**
 * Converte un Event del backend in CalendarEvent per react-big-calendar.
 *
 * Il backend serializza con spazio ("2026-02-22 10:00:00") o T.
 * parseISO di date-fns gestisce entrambi.
 */
export function toCalendarEvent(event: ApiEvent): CalendarEvent {
  return {
    id: event.id,
    title: event.titolo || event.categoria,
    start: parseISO(event.data_inizio.replace(" ", "T")),
    end: parseISO(event.data_fine.replace(" ", "T")),
    categoria: event.categoria,
    stato: event.stato,
    id_cliente: event.id_cliente,
    id_contratto: event.id_contratto,
    note: event.note,
  };
}

// ── Stili per categoria (eventPropGetter) ──

interface CategoryStyle {
  backgroundColor: string;
  borderColor: string;
  color: string;
}

const CATEGORY_STYLE_MAP: Record<string, CategoryStyle> = {
  PT:          { backgroundColor: "#dbeafe", borderColor: "#3b82f6", color: "#1e3a5f" },
  SALA:        { backgroundColor: "#f4f4f5", borderColor: "#a1a1aa", color: "#3f3f46" },
  NUOTO:       { backgroundColor: "#cffafe", borderColor: "#06b6d4", color: "#164e63" },
  YOGA:        { backgroundColor: "#f3e8ff", borderColor: "#a855f7", color: "#581c87" },
  CONSULENZA:  { backgroundColor: "#fef3c7", borderColor: "#f59e0b", color: "#78350f" },
  CORSO:       { backgroundColor: "#d1fae5", borderColor: "#10b981", color: "#064e3b" },
};

const DEFAULT_STYLE: CategoryStyle = {
  backgroundColor: "#f1f5f9",
  borderColor: "#94a3b8",
  color: "#334155",
};

export function getEventStyle(event: CalendarEvent): React.CSSProperties {
  const style = CATEGORY_STYLE_MAP[event.categoria] ?? DEFAULT_STYLE;
  return {
    backgroundColor: style.backgroundColor,
    borderLeft: `3px solid ${style.borderColor}`,
    color: style.color,
    borderRadius: "4px",
    padding: "2px 4px",
    fontSize: "0.8rem",
  };
}

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
  NUOTO: "Nuoto",
  YOGA: "Yoga",
  CONSULENZA: "Consulenza",
  CORSO: "Corso",
};
