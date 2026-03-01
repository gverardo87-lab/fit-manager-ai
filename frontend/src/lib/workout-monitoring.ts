// src/lib/workout-monitoring.ts
/**
 * Utility per monitoraggio allenamenti.
 *
 * Calcolo status programma, griglia settimane, matching log, compliance.
 * Tutto client-side — zero backend aggiuntivo.
 */

import type { WorkoutPlan, WorkoutLog } from "@/types/api";

// ── Status programma (derivato da date) ──

export type ProgramStatus = "da_attivare" | "attivo" | "completato";

export function getProgramStatus(plan: WorkoutPlan): ProgramStatus {
  if (!plan.data_inizio || !plan.data_fine) return "da_attivare";
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const fine = new Date(plan.data_fine + "T00:00:00");
  if (today > fine) return "completato";
  return "attivo";
}

export const STATUS_LABELS: Record<ProgramStatus, string> = {
  da_attivare: "Da attivare",
  attivo: "Attivo",
  completato: "Completato",
};

export const STATUS_COLORS: Record<ProgramStatus, string> = {
  da_attivare: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  attivo: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  completato: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

// ── Griglia settimane ──

export interface WeekSlot {
  weekNumber: number;   // 1-based
  startDate: Date;      // primo giorno della settimana
  endDate: Date;        // ultimo giorno della settimana (incluso)
}

/** Genera array di settimane da data_inizio a data_fine (chunk di 7 giorni). */
export function computeWeeks(dataInizio: string, dataFine: string): WeekSlot[] {
  const start = new Date(dataInizio + "T00:00:00");
  const end = new Date(dataFine + "T00:00:00");
  const weeks: WeekSlot[] = [];

  let weekStart = new Date(start);
  let weekNum = 1;

  while (weekStart <= end) {
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 6);
    // Clamp alla data fine
    const clampedEnd = weekEnd > end ? new Date(end) : weekEnd;

    weeks.push({
      weekNumber: weekNum,
      startDate: new Date(weekStart),
      endDate: clampedEnd,
    });

    weekStart.setDate(weekStart.getDate() + 7);
    weekNum++;
  }

  return weeks;
}

// ── Matching log → griglia ──

/**
 * Mappa log alla griglia settimane × sessioni.
 * Chiave: `${weekNumber}-${sessionId}`
 */
export function matchLogsToGrid(
  logs: WorkoutLog[],
  weeks: WeekSlot[],
  sessionIds: number[],
): Map<string, WorkoutLog> {
  const grid = new Map<string, WorkoutLog>();
  const sessionSet = new Set(sessionIds);

  for (const log of logs) {
    if (!sessionSet.has(log.id_sessione)) continue;

    const logDate = new Date(log.data_esecuzione + "T00:00:00");

    // Trova la settimana di appartenenza
    for (const week of weeks) {
      if (logDate >= week.startDate && logDate <= week.endDate) {
        const key = `${week.weekNumber}-${log.id_sessione}`;
        // Se esiste gia' un log per questa cella, tieni il piu' recente
        const existing = grid.get(key);
        if (!existing || log.data_esecuzione > existing.data_esecuzione) {
          grid.set(key, log);
        }
        break;
      }
    }
  }

  return grid;
}

// ── Compliance ──

/** Calcola compliance % (0-100). */
export function computeCompliance(expected: number, completed: number): number {
  if (expected <= 0) return 0;
  return Math.min(100, Math.round((completed / expected) * 100));
}

/** Colore barra compliance basato su percentuale. */
export function getComplianceColor(percentage: number): string {
  if (percentage >= 80) return "bg-emerald-500";
  if (percentage >= 50) return "bg-amber-500";
  return "bg-red-500";
}

/** Colore testo compliance. */
export function getComplianceTextColor(percentage: number): string {
  if (percentage >= 80) return "text-emerald-600 dark:text-emerald-400";
  if (percentage >= 50) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

// ── Helpers data ──

/** Settimana e' passata o corrente (oggi compreso). */
export function isWeekPastOrCurrent(week: WeekSlot): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return week.startDate <= today;
}

/** Settimana e' futura (inizia dopo oggi). */
export function isWeekFuture(week: WeekSlot): boolean {
  return !isWeekPastOrCurrent(week);
}

/** Formatta data in formato corto "3 mar". */
export function formatShortDate(date: Date): string {
  return date.toLocaleDateString("it-IT", { day: "numeric", month: "short" });
}

/** Formatta range date "3 mar — 30 mar 2026". */
export function formatDateRange(start: string, end: string): string {
  const s = new Date(start + "T00:00:00");
  const e = new Date(end + "T00:00:00");
  const sameYear = s.getFullYear() === e.getFullYear();
  const startStr = s.toLocaleDateString("it-IT", {
    day: "numeric",
    month: "short",
    ...(sameYear ? {} : { year: "numeric" }),
  });
  const endStr = e.toLocaleDateString("it-IT", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  return `${startStr} — ${endStr}`;
}
