/**
 * client-alerts.ts — Mapping UI per alert readiness backend-first.
 *
 * La logica di soglia vive nel backend (`api/services/client_freshness.py`).
 * Qui traduciamo solo i segnali gia calcolati dal payload readiness in banner/badge UI.
 */

import type { ClinicalFreshnessSignal, ClinicalReadinessClientItem } from "@/types/api";

export type AlertSeverity = "warning" | "critical";

export interface ClientAlert {
  type: "scheda_age" | "measurement_gap";
  severity: AlertSeverity;
  daysElapsed: number;
  label: string;
  cta: string;
  href: string;
}

function toClientAlert(signal: ClinicalFreshnessSignal | null | undefined): ClientAlert | null {
  if (!signal || (signal.status !== "warning" && signal.status !== "critical")) {
    return null;
  }

  const daysElapsed = signal.days_since_last ?? 0;
  if (signal.domain === "measurements") {
    return {
      type: "measurement_gap",
      severity: signal.status,
      daysElapsed,
      label: signal.label,
      cta: signal.cta_label,
      href: signal.cta_href,
    };
  }

  return {
    type: "scheda_age",
    severity: signal.status,
    daysElapsed,
    label: signal.label,
    cta: signal.cta_label,
    href: signal.cta_href,
  };
}

export function buildReadinessAlerts(readiness: ClinicalReadinessClientItem | null): ClientAlert[] {
  return [
    toClientAlert(readiness?.workout_freshness),
    toClientAlert(readiness?.measurement_freshness),
  ].filter(Boolean) as ClientAlert[];
}

export const ALERT_SEVERITY_STYLES: Record<
  AlertSeverity,
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
