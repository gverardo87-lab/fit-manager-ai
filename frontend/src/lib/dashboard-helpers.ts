/**
 * Dashboard helpers — utility pure per la Plancia della Nave.
 */

import type { EventHydrated } from "@/hooks/useAgenda";

// ── Greeting ──

export function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 13) return "Buongiorno";
  if (hour < 18) return "Buon pomeriggio";
  return "Buonasera";
}

// ── Date helpers ──

export function formatLocalISODate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function todayISO(referenceDate: Date = new Date()): string {
  return formatLocalISODate(referenceDate);
}

export function tomorrowISO(referenceDate: Date = new Date()): string {
  const d = new Date(referenceDate);
  d.setDate(d.getDate() + 1);
  return formatLocalISODate(d);
}

export function weekStartDate(baseDate: Date = new Date()): Date {
  const date = new Date(baseDate);
  const day = date.getDay();
  const delta = day === 0 ? -6 : 1 - day;
  date.setDate(date.getDate() + delta);
  date.setHours(0, 0, 0, 0);
  return date;
}

export function weekStartISO(baseDate: Date = new Date()): string {
  return formatLocalISODate(weekStartDate(baseDate));
}

export function nextWeekStartISO(baseDate: Date = new Date()): string {
  const date = weekStartDate(baseDate);
  date.setDate(date.getDate() + 7);
  return formatLocalISODate(date);
}

// ── Agenda completion ──

export function computeAgendaCompletion(events: EventHydrated[]): number {
  const actionable = events.filter((e) => e.stato !== "Cancellato");
  if (actionable.length === 0) return 100;
  const completed = actionable.filter((e) => e.stato === "Completato").length;
  return Math.round((completed / actionable.length) * 100);
}

// ── Live info ──

export interface AgendaLiveInfo {
  mode: "in_progress" | "next_up" | "free";
  event: EventHydrated | null;
  remainingMs: number;
}

export function buildAgendaLiveInfo(events: EventHydrated[], currentTime: Date): AgendaLiveInfo {
  const nowTs = currentTime.getTime();
  const actionableEvents = events.filter(
    (event) => event.stato !== "Cancellato" && event.stato !== "Completato",
  );

  const currentEvent = actionableEvents.find(
    (event) => event.data_inizio.getTime() <= nowTs && nowTs < event.data_fine.getTime(),
  );
  if (currentEvent) {
    return {
      mode: "in_progress",
      event: currentEvent,
      remainingMs: Math.max(0, currentEvent.data_fine.getTime() - nowTs),
    };
  }

  const nextEvent = actionableEvents.find((event) => event.data_inizio.getTime() > nowTs);
  if (nextEvent) {
    return {
      mode: "next_up",
      event: nextEvent,
      remainingMs: Math.max(0, nextEvent.data_inizio.getTime() - nowTs),
    };
  }

  return { mode: "free", event: null, remainingMs: 0 };
}

export function formatCountdown(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map((v) => String(v).padStart(2, "0")).join(":");
}

// ── Category colors (mirror agenda) ──

export const CATEGORY_COLORS: Record<string, string> = {
  PT: "bg-blue-500",
  SALA: "bg-emerald-500",
  CORSO: "bg-violet-500",
  COLLOQUIO: "bg-amber-500",
  PERSONALE: "bg-pink-500",
};

export const STATUS_COLORS: Record<string, string> = {
  Programmato: "text-blue-600 dark:text-blue-400",
  Completato: "text-emerald-600 dark:text-emerald-400",
  Cancellato: "text-red-400 line-through",
  Rinviato: "text-amber-600 dark:text-amber-400",
};

// ── Alert config ──

export const ALERT_SEVERITY_ORDER = ["critical", "warning", "info"] as const;
export const MAX_VISIBLE_ALERTS = 4;
