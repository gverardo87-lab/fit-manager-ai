// src/lib/measurement-analytics.ts
/**
 * Utility condivise per analisi misurazioni — rate of change.
 *
 * Usato da ProgressiTab (KPI cards) e InteractiveBodyMap (ZoneDetailPanel)
 * per computare velocita' settimanale client-side dalle misurazioni gia' caricate.
 */

import type { Measurement } from "@/types/api";

/**
 * Computa la velocita' di cambiamento settimanale per una metrica.
 *
 * Algoritmo: pendenza su ultimi `windowDays` giorni.
 * Fallback: primo + ultimo se < 2 punti nel window.
 *
 * @returns delta/settimana arrotondato a 2 decimali, null se < 2 data point
 */
export function computeWeeklyRate(
  measurements: Measurement[],
  metricId: number,
  windowDays = 30
): number | null {
  // Estrai time series: (date, value) per questa metrica
  const series: { date: Date; value: number }[] = [];

  for (const m of measurements) {
    const val = m.valori.find((v) => v.id_metrica === metricId);
    if (val) {
      series.push({ date: new Date(m.data_misurazione), value: val.valore });
    }
  }

  if (series.length < 2) return null;

  // Ordina ASC per data
  series.sort((a, b) => a.date.getTime() - b.date.getTime());

  const latest = series[series.length - 1];
  const cutoffMs = latest.date.getTime() - windowDays * 24 * 60 * 60 * 1000;

  let recent = series.filter((p) => p.date.getTime() >= cutoffMs);

  // Fallback a range completo se < 2 punti nel window
  if (recent.length < 2) {
    recent = [series[0], series[series.length - 1]];
  }

  const first = recent[0];
  const last = recent[recent.length - 1];
  const days =
    (last.date.getTime() - first.date.getTime()) / (1000 * 60 * 60 * 24);

  if (days === 0) return null;

  const delta = last.value - first.value;
  const weeklyRate = (delta / days) * 7;

  return Math.round(weeklyRate * 100) / 100;
}

/**
 * Formatta rate settimanale per display.
 * @example formatRate(-0.5, "kg") → "−0.5 kg/sett"
 * @example formatRate(2.3, "%") → "+2.3 %/sett"
 */
export function formatRate(rate: number, unit: string): string {
  const sign = rate > 0 ? "+" : "";
  const rounded =
    Math.abs(rate) >= 10
      ? rate.toFixed(0)
      : Math.abs(rate) >= 1
        ? rate.toFixed(1)
        : rate.toFixed(2);
  return `${sign}${rounded} ${unit}/sett`;
}
