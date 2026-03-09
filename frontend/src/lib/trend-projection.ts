/**
 * Trend Projection Engine — EWMA smoothing + linear projection + confidence bands.
 *
 * Algoritmo ispirato a MacroFactor (EWMA), Libra (regressione su trend),
 * Hacker's Diet (alpha adattivo). Zero dipendenze esterne.
 *
 * Usato da ProjectionChart per visualizzare trend storico + proiezione futura.
 */

import type { ClientGoal, Measurement } from "@/types/api";

// ── Types ──

export interface TrendPoint {
  date: string;
  raw: number;
  trend: number;
}

export interface ProjectedPoint {
  date: string;
  value: number;
  upper: number;
  lower: number;
}

export type NarrativeKey =
  | "on_track"
  | "ahead_of_schedule"
  | "plateau"
  | "wrong_direction"
  | "no_goal"
  | "insufficient";

export interface TrendProjectionResult {
  trendPoints: TrendPoint[];
  projectedPoints: ProjectedPoint[];
  weeklyRate: number | null;
  weeksToGoal: number | null;
  etaDate: string | null;
  targetValue: number | null;
  goalDirection: "aumentare" | "diminuire" | "mantenere" | null;
  narrative: NarrativeKey;
  narrativeText: string;
  metricName: string;
  unit: string;
}

// ── EWMA Smoothing ──

function computeEWMA(series: { date: Date; value: number }[]): { date: Date; value: number; trend: number }[] {
  if (series.length === 0) return [];

  // Adaptive alpha basato sulla densita' misurazioni
  const spanDays = (series[series.length - 1].date.getTime() - series[0].date.getTime()) / 864e5;
  const avgGap = series.length > 1 ? spanDays / (series.length - 1) : 30;
  const alpha = avgGap <= 3 ? 0.1 : avgGap <= 10 ? 0.2 : avgGap <= 21 ? 0.35 : 0.5;

  const result: { date: Date; value: number; trend: number }[] = [];
  let trend = series[0].value;

  for (const pt of series) {
    trend = alpha * pt.value + (1 - alpha) * trend;
    result.push({ date: pt.date, value: pt.value, trend: Math.round(trend * 100) / 100 });
  }
  return result;
}

// ── Linear Regression (on trend values) ──

function linearRegression(points: { x: number; y: number }[]): { slope: number; intercept: number; r2: number } {
  const n = points.length;
  if (n < 2) return { slope: 0, intercept: points[0]?.y ?? 0, r2: 0 };

  let sx = 0, sy = 0, sxx = 0, sxy = 0, syy = 0;
  for (const p of points) {
    sx += p.x; sy += p.y; sxx += p.x * p.x; sxy += p.x * p.y; syy += p.y * p.y;
  }
  const denom = n * sxx - sx * sx;
  if (Math.abs(denom) < 1e-10) return { slope: 0, intercept: sy / n, r2: 0 };

  const slope = (n * sxy - sx * sy) / denom;
  const intercept = (sy - slope * sx) / n;

  const ssTot = syy - (sy * sy) / n;
  const ssRes = points.reduce((acc, p) => acc + (p.y - (slope * p.x + intercept)) ** 2, 0);
  const r2 = ssTot > 0 ? 1 - ssRes / ssTot : 0;

  return { slope, intercept, r2 };
}

// ── Projection ──

function projectForward(
  ewmaPoints: { date: Date; trend: number }[],
  projectionDays: number,
): { projectedPoints: ProjectedPoint[]; slopePerDay: number; sigma: number } {
  // Regression on last min(all, 60 days) of EWMA trend values
  const lastDate = ewmaPoints[ewmaPoints.length - 1].date;
  const cutoff = lastDate.getTime() - 60 * 864e5;
  const recent = ewmaPoints.filter(p => p.date.getTime() >= cutoff);
  const baseT = recent[0].date.getTime();

  const regPoints = recent.map(p => ({ x: (p.date.getTime() - baseT) / 864e5, y: p.trend }));
  const { slope: slopePerDay } = linearRegression(regPoints);

  // Residuals for confidence band
  const residuals = ewmaPoints.map(p => p.trend - (slopePerDay * ((p.date.getTime() - baseT) / 864e5)));
  const sigma = Math.sqrt(residuals.reduce((s, r) => s + r * r, 0) / Math.max(residuals.length - 1, 1));

  const lastTrend = ewmaPoints[ewmaPoints.length - 1].trend;
  const projected: ProjectedPoint[] = [];
  const STEP = 7; // weekly steps

  for (let d = STEP; d <= projectionDays; d += STEP) {
    const futureDate = new Date(lastDate.getTime() + d * 864e5);
    const value = Math.round((lastTrend + slopePerDay * d) * 100) / 100;
    const band = 1.96 * sigma * Math.sqrt(d / Math.max(regPoints.length, 7));
    projected.push({
      date: futureDate.toISOString().slice(0, 10),
      value,
      upper: Math.round((value + band) * 100) / 100,
      lower: Math.round((value - band) * 100) / 100,
    });
  }

  return { projectedPoints: projected, slopePerDay, sigma };
}

// ── Narrative Builder ──

function buildNarrative(
  key: NarrativeKey,
  weeklyRate: number | null,
  unit: string,
  metricName: string,
  targetValue: number | null,
  etaDate: string | null,
  weeksToGoal: number | null,
): string {
  const rateStr = weeklyRate !== null
    ? `${weeklyRate > 0 ? "+" : ""}${Math.abs(weeklyRate) >= 1 ? weeklyRate.toFixed(1) : weeklyRate.toFixed(2)} ${unit}/sett`
    : "";

  switch (key) {
    case "on_track":
      return `Con il passo attuale (${rateStr}), raggiungerà ${targetValue} ${unit} entro ${formatItalianDate(etaDate!)} — fra circa ${Math.round(weeksToGoal!)} settimane.`;
    case "ahead_of_schedule":
      return `Ottimo ritmo! Con ${rateStr}, l'obiettivo di ${targetValue} ${unit} è raggiungibile entro ${formatItalianDate(etaDate!)} — fra ${Math.round(weeksToGoal!)} settimane.`;
    case "plateau":
      return `Il progresso di ${metricName.toLowerCase()} si è stabilizzato. La misura è rimasta costante nelle ultime settimane.`;
    case "wrong_direction":
      return `Attenzione: il trend attuale (${rateStr}) si allontana dall'obiettivo di ${targetValue} ${unit}.`;
    case "no_goal":
      return `Trend attuale: ${rateStr}. Imposta un obiettivo per vedere la proiezione temporale.`;
    case "insufficient":
      return `Servono almeno 3 misurazioni per calcolare il trend e la proiezione.`;
  }
}

function formatItalianDate(iso: string): string {
  const MONTHS = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"];
  const d = new Date(iso);
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

// ── Main Orchestrator ──

export function buildTrendProjection(
  measurements: Measurement[],
  metricId: number,
  metricName: string,
  unit: string,
  goals?: ClientGoal[],
): TrendProjectionResult | null {
  // Extract time series for this metric
  const series: { date: Date; value: number }[] = [];
  for (const m of measurements) {
    const val = m.valori.find(v => v.id_metrica === metricId);
    if (val) series.push({ date: new Date(m.data_misurazione), value: val.valore });
  }
  series.sort((a, b) => a.date.getTime() - b.date.getTime());

  if (series.length < 2) {
    return {
      trendPoints: series.map(s => ({ date: s.date.toISOString().slice(0, 10), raw: s.value, trend: s.value })),
      projectedPoints: [], weeklyRate: null, weeksToGoal: null, etaDate: null,
      targetValue: null, goalDirection: null, narrative: "insufficient",
      narrativeText: buildNarrative("insufficient", null, unit, metricName, null, null, null),
      metricName, unit,
    };
  }

  // EWMA
  const ewma = computeEWMA(series);
  const trendPoints: TrendPoint[] = ewma.map(p => ({
    date: p.date.toISOString().slice(0, 10), raw: p.value, trend: p.trend,
  }));

  // Projection (max 12 weeks = 84 days)
  const { projectedPoints, slopePerDay } = projectForward(ewma, 84);
  const weeklyRate = Math.round(slopePerDay * 7 * 100) / 100;

  // Find active goal for this metric
  const goal = goals?.find(g => g.id_metrica === metricId && g.stato === "attivo") ?? null;
  const targetValue = goal?.valore_target ?? null;
  const goalDirection = goal?.direzione ?? null;

  // Determine narrative
  let narrative: NarrativeKey;
  let weeksToGoal: number | null = null;
  let etaDate: string | null = null;

  if (!goal || targetValue === null) {
    narrative = Math.abs(weeklyRate) < 0.05 ? "plateau" : "no_goal";
  } else {
    const currentTrend = ewma[ewma.length - 1].trend;
    const remaining = targetValue - currentTrend;
    const ratePerDay = slopePerDay;

    if (Math.abs(weeklyRate) < 0.05) {
      narrative = "plateau";
    } else if ((remaining > 0 && ratePerDay <= 0) || (remaining < 0 && ratePerDay >= 0)) {
      narrative = "wrong_direction";
    } else {
      const daysToGoal = Math.abs(remaining / ratePerDay);
      weeksToGoal = daysToGoal / 7;
      if (weeksToGoal > 104) {
        narrative = "wrong_direction"; // unreachable within 2 years
      } else {
        const eta = new Date(ewma[ewma.length - 1].date.getTime() + daysToGoal * 864e5);
        etaDate = eta.toISOString().slice(0, 10);
        narrative = weeksToGoal < 6 ? "ahead_of_schedule" : "on_track";
      }
    }
  }

  const narrativeText = buildNarrative(narrative, weeklyRate, unit, metricName, targetValue, etaDate, weeksToGoal);

  return {
    trendPoints, projectedPoints, weeklyRate, weeksToGoal, etaDate,
    targetValue, goalDirection, narrative, narrativeText, metricName, unit,
  };
}
