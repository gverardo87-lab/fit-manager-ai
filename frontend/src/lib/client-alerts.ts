/**
 * client-alerts.ts — Utility pure per alert scheda e misurazioni.
 *
 * Calcola "eta'" della scheda piu' recente e gap dall'ultima misurazione.
 * Soglie configurabili, severity 3 livelli (ok / warning / critical).
 * Zero dipendenze da React — puro TypeScript.
 */

import type { WorkoutPlan, Measurement } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

export type AlertSeverity = "ok" | "warning" | "critical";

export interface ClientAlert {
  type: "scheda_age" | "measurement_gap";
  severity: AlertSeverity;
  daysElapsed: number;
  label: string;
  /** CTA testuale per il banner */
  cta: string;
}

// ════════════════════════════════════════════════════════════
// THRESHOLDS (giorni)
// ════════════════════════════════════════════════════════════

/** Scheda: verde < 21d, ambra 21-35d, rosso > 35d */
const SCHEDA_WARNING_DAYS = 21;
const SCHEDA_CRITICAL_DAYS = 35;

/** Misurazioni: verde < 25d, ambra 25-35d, rosso > 35d */
const MEASUREMENT_WARNING_DAYS = 25;
const MEASUREMENT_CRITICAL_DAYS = 35;

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

function daysBetween(from: Date, to: Date): number {
  const msPerDay = 86_400_000;
  return Math.floor((to.getTime() - from.getTime()) / msPerDay);
}

function getSeverity(
  days: number,
  warningThreshold: number,
  criticalThreshold: number,
): AlertSeverity {
  if (days >= criticalThreshold) return "critical";
  if (days >= warningThreshold) return "warning";
  return "ok";
}

// ════════════════════════════════════════════════════════════
// SCHEDA AGE
// ════════════════════════════════════════════════════════════

/**
 * Data di riferimento della scheda piu' recente.
 * Priorita': updated_at > created_at > data_inizio.
 */
function getLatestSchedaDate(workouts: WorkoutPlan[]): Date | null {
  if (workouts.length === 0) return null;

  let latest: Date | null = null;

  for (const w of workouts) {
    const candidates = [w.updated_at, w.created_at, w.data_inizio].filter(Boolean) as string[];
    for (const c of candidates) {
      const d = new Date(c.includes("T") ? c : c + "T00:00:00");
      if (!latest || d > latest) latest = d;
    }
  }

  return latest;
}

/**
 * Calcola l'eta' della scheda piu' recente.
 * Ritorna null se non ci sono schede.
 */
export function computeSchedaAge(
  workouts: WorkoutPlan[],
  now: Date = new Date(),
): ClientAlert | null {
  const latestDate = getLatestSchedaDate(workouts);
  if (!latestDate) return null;

  const days = daysBetween(latestDate, now);
  if (days < 0) return null; // data futura (edge case)

  const severity = getSeverity(days, SCHEDA_WARNING_DAYS, SCHEDA_CRITICAL_DAYS);
  if (severity === "ok") return null;

  const weeksElapsed = Math.floor(days / 7);

  return {
    type: "scheda_age",
    severity,
    daysElapsed: days,
    label:
      severity === "critical"
        ? `Scheda da aggiornare (${weeksElapsed} settimane)`
        : `Scheda creata ${weeksElapsed} settimane fa`,
    cta: "Aggiorna scheda",
  };
}

// ════════════════════════════════════════════════════════════
// MEASUREMENT GAP
// ════════════════════════════════════════════════════════════

/**
 * Data dell'ultima misurazione.
 */
function getLatestMeasurementDate(measurements: Measurement[]): Date | null {
  if (measurements.length === 0) return null;

  let latest: Date | null = null;
  for (const m of measurements) {
    const d = new Date(
      m.data_misurazione.includes("T")
        ? m.data_misurazione
        : m.data_misurazione + "T00:00:00",
    );
    if (!latest || d > latest) latest = d;
  }

  return latest;
}

/**
 * Calcola il gap dall'ultima misurazione.
 * Ritorna null se non ci sono misurazioni.
 */
export function computeMeasurementGap(
  measurements: Measurement[],
  now: Date = new Date(),
): ClientAlert | null {
  const latestDate = getLatestMeasurementDate(measurements);
  if (!latestDate) return null;

  const days = daysBetween(latestDate, now);
  if (days < 0) return null;

  const severity = getSeverity(days, MEASUREMENT_WARNING_DAYS, MEASUREMENT_CRITICAL_DAYS);
  if (severity === "ok") return null;

  return {
    type: "measurement_gap",
    severity,
    daysElapsed: days,
    label:
      severity === "critical"
        ? `Misurazioni da riprendere (${days} giorni)`
        : `Ultima misurazione ${days} giorni fa`,
    cta: "Nuova misurazione",
  };
}

// ════════════════════════════════════════════════════════════
// SEVERITY STYLES (consumati dai componenti UI)
// ════════════════════════════════════════════════════════════

export const ALERT_SEVERITY_STYLES: Record<
  "warning" | "critical",
  { border: string; bg: string; text: string; icon: string }
> = {
  warning: {
    border: "border-l-amber-500",
    bg: "bg-amber-50/60 dark:bg-amber-950/20",
    text: "text-amber-700 dark:text-amber-300",
    icon: "text-amber-500 dark:text-amber-400",
  },
  critical: {
    border: "border-l-red-500",
    bg: "bg-red-50/60 dark:bg-red-950/20",
    text: "text-red-700 dark:text-red-300",
    icon: "text-red-500 dark:text-red-400",
  },
};
