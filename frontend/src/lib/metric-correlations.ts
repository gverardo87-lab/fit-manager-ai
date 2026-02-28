// src/lib/metric-correlations.ts
/**
 * Correlazione Inter-Metrica — Engine per insight composizione corporea.
 *
 * Analizza coppie di metriche correlate per produrre insight chinesiologici:
 *   1. Peso (1) + Massa Grassa % (3) → Composizione Corporea
 *   2. Vita (9) + Fianchi (10) → Distribuzione Corporea (WHR)
 *   3. PA Sistolica (18) + PA Diastolica (19) → Profilo Cardiovascolare
 *
 * Usato da: CompositionInsights.tsx (card in ProgressiTab)
 */

import type { Measurement } from "@/types/api";
import { classifyValue } from "@/lib/normative-ranges";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

export interface CorrelationPair {
  id: string;
  label: string;
  metricIds: [number, number];
  icon: string; // lucide icon name
}

export type InsightSeverity = "positive" | "neutral" | "warning" | "alert";

export interface CorrelationInsight {
  pairId: string;
  label: string;
  text: string;
  severity: InsightSeverity;
  details?: string;
  values?: string; // "Peso −2.3 kg + Grasso −1.5%"
}

// ════════════════════════════════════════════════════════════
// PAIRS DEFINITION
// ════════════════════════════════════════════════════════════

export const CORRELATION_PAIRS: CorrelationPair[] = [
  {
    id: "peso-grasso",
    label: "Composizione Corporea",
    metricIds: [1, 3],
    icon: "Scale",
  },
  {
    id: "vita-fianchi",
    label: "Distribuzione Corporea",
    metricIds: [9, 10],
    icon: "Ruler",
  },
  {
    id: "pa",
    label: "Profilo Cardiovascolare",
    metricIds: [18, 19],
    icon: "Heart",
  },
];

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

interface MetricSnapshot {
  latest: number;
  previous: number | null;
  delta: number | null;
  unit: string;
}

/** Estrae latest + previous per una metrica dalle misurazioni. */
function extractSnapshot(
  measurements: Measurement[],
  metricId: number
): MetricSnapshot | null {
  // Ordina misurazioni ASC per data
  const sorted = measurements
    .slice()
    .sort((a, b) => a.data_misurazione.localeCompare(b.data_misurazione));

  let latest: { value: number; unit: string } | null = null;
  let previous: { value: number } | null = null;

  // Scansione inversa: trova latest e previous
  for (let i = sorted.length - 1; i >= 0; i--) {
    const val = sorted[i].valori.find((v) => v.id_metrica === metricId);
    if (!val) continue;

    if (!latest) {
      latest = { value: val.valore, unit: val.unita ?? "" };
    } else if (!previous) {
      previous = { value: val.valore };
      break;
    }
  }

  if (!latest) return null;

  return {
    latest: latest.value,
    previous: previous?.value ?? null,
    delta: previous ? latest.value - previous.value : null,
    unit: latest.unit,
  };
}

/** Classifica delta: "up" | "down" | "stable" */
function trend(delta: number | null, threshold = 0.5): "up" | "down" | "stable" {
  if (delta === null) return "stable";
  if (delta > threshold) return "up";
  if (delta < -threshold) return "down";
  return "stable";
}

// ════════════════════════════════════════════════════════════
// ANALYSIS ENGINE
// ════════════════════════════════════════════════════════════

function analyzePesoGrasso(
  peso: MetricSnapshot,
  grasso: MetricSnapshot
): CorrelationInsight {
  const pesoTrend = trend(peso.delta, 0.3);
  const grassoTrend = trend(grasso.delta, 0.3);

  const valuesStr = [
    `Peso ${peso.delta !== null ? (peso.delta > 0 ? "+" : "") + peso.delta.toFixed(1) : "—"} ${peso.unit}`,
    `Grasso ${grasso.delta !== null ? (grasso.delta > 0 ? "+" : "") + grasso.delta.toFixed(1) : "—"} ${grasso.unit}`,
  ].join(" + ");

  let text: string;
  let severity: InsightSeverity;
  let details: string | undefined;

  if (pesoTrend === "down" && grassoTrend === "down") {
    text = "Perdita di grasso";
    severity = "positive";
    details = "Peso e massa grassa in calo: composizione in miglioramento.";
  } else if (pesoTrend === "down" && grassoTrend === "stable") {
    text = "Possibile perdita muscolare";
    severity = "warning";
    details =
      "Il peso cala ma la percentuale di grasso resta stabile. Verificare l'apporto proteico e il volume di allenamento.";
  } else if (pesoTrend === "stable" && grassoTrend === "down") {
    text = "Ricomposizione corporea";
    severity = "positive";
    details =
      "Peso stabile con grasso in calo: la massa magra sta sostituendo il grasso.";
  } else if (pesoTrend === "up" && grassoTrend === "up") {
    text = "Aumento massa grassa";
    severity = "alert";
    details =
      "Peso e grasso in aumento. Valutare bilancio calorico e attivita' fisica.";
  } else if (pesoTrend === "up" && grassoTrend === "stable") {
    text = "Aumento massa magra";
    severity = "positive";
    details =
      "Il peso sale ma il grasso resta stabile: probabile incremento muscolare.";
  } else if (pesoTrend === "up" && grassoTrend === "down") {
    text = "Crescita muscolare ottimale";
    severity = "positive";
    details =
      "Peso in aumento e grasso in calo: fase di crescita muscolare ideale.";
  } else if (pesoTrend === "down" && grassoTrend === "up") {
    text = "Perdita muscolare con aumento grasso";
    severity = "alert";
    details =
      "Peso in calo ma grasso in aumento. Situazione critica: verificare dieta e allenamento.";
  } else {
    text = "Composizione stabile";
    severity = "neutral";
    details = "Peso e massa grassa stabili.";
  }

  return {
    pairId: "peso-grasso",
    label: "Composizione Corporea",
    text,
    severity,
    details,
    values: valuesStr,
  };
}

// WHR thresholds (OMS)
const WHR_THRESHOLDS = {
  M: { low: 0.9, high: 1.0 },
  F: { low: 0.8, high: 0.85 },
} as const;

function analyzeVitaFianchi(
  vita: MetricSnapshot,
  fianchi: MetricSnapshot,
  sesso?: string | null
): CorrelationInsight {
  const whr = vita.latest / fianchi.latest;
  const whrRounded = Math.round(whr * 100) / 100;

  // Classifica WHR
  const sex = sesso?.toLowerCase();
  const thresholds =
    sex === "uomo" || sex === "m" || sex === "maschio"
      ? WHR_THRESHOLDS.M
      : sex === "donna" || sex === "f" || sex === "femmina"
        ? WHR_THRESHOLDS.F
        : null;

  let riskLabel: string;
  let severity: InsightSeverity;

  if (!thresholds) {
    riskLabel = `WHR: ${whrRounded}`;
    severity = "neutral";
  } else if (whr < thresholds.low) {
    riskLabel = `WHR: ${whrRounded} (basso rischio)`;
    severity = "positive";
  } else if (whr < thresholds.high) {
    riskLabel = `WHR: ${whrRounded} (rischio moderato)`;
    severity = "warning";
  } else {
    riskLabel = `WHR: ${whrRounded} (alto rischio)`;
    severity = "alert";
  }

  // Trend WHR
  let trendText = "";
  if (vita.previous !== null && fianchi.previous !== null) {
    const prevWhr = vita.previous / fianchi.previous;
    const whrDelta = whr - prevWhr;
    if (Math.abs(whrDelta) > 0.01) {
      trendText = whrDelta < 0 ? " — trend in miglioramento" : " — trend in peggioramento";
    }
  }

  return {
    pairId: "vita-fianchi",
    label: "Distribuzione Corporea",
    text: riskLabel + trendText,
    severity,
    values: `Vita ${vita.latest} ${vita.unit} / Fianchi ${fianchi.latest} ${fianchi.unit}`,
  };
}

function analyzePressione(
  sistolica: MetricSnapshot,
  diastolica: MetricSnapshot
): CorrelationInsight {
  // Classificazione combinata ESH: usa peggiore tra sistolica e diastolica
  const sClass = classifyValue(18, sistolica.latest);
  const dClass = classifyValue(19, diastolica.latest);

  // Pressione differenziale
  const pp = sistolica.latest - diastolica.latest;
  const ppNormal = pp >= 30 && pp <= 50;

  const label =
    sClass && dClass
      ? // Usa la classificazione peggiore
        (["rose", "orange", "amber"].indexOf(sClass.color) >=
        ["rose", "orange", "amber"].indexOf(dClass.color)
          ? sClass
          : dClass
        ).label
      : "Non classificabile";

  let ppText = "";
  if (!ppNormal) {
    ppText =
      pp < 30
        ? ` — Differenziale bassa (${pp} mmHg)`
        : ` — Differenziale alta (${pp} mmHg)`;
  } else {
    ppText = ` — Differenziale ${pp} mmHg (nella norma)`;
  }

  // Severity dalla classificazione
  let severity: InsightSeverity = "neutral";
  const worstColor = [sClass?.color, dClass?.color].includes("rose")
    ? "rose"
    : [sClass?.color, dClass?.color].includes("orange")
      ? "orange"
      : [sClass?.color, dClass?.color].includes("amber")
        ? "amber"
        : "emerald";

  if (worstColor === "rose") severity = "alert";
  else if (worstColor === "orange") severity = "warning";
  else if (worstColor === "amber") severity = "neutral";
  else severity = "positive";

  return {
    pairId: "pa",
    label: "Profilo Cardiovascolare",
    text: `${label}${ppText}`,
    severity,
    values: `${sistolica.latest}/${diastolica.latest} mmHg`,
  };
}

// ════════════════════════════════════════════════════════════
// PUBLIC API
// ════════════════════════════════════════════════════════════

/**
 * Analizza correlazioni inter-metrica dalle misurazioni.
 * Ritorna insight solo per coppie con entrambe le metriche presenti.
 */
export function analyzeCorrelations(
  measurements: Measurement[],
  sesso?: string | null,
): CorrelationInsight[] {
  if (measurements.length < 1) return [];

  const insights: CorrelationInsight[] = [];

  // 1. Peso + Grasso
  const peso = extractSnapshot(measurements, 1);
  const grasso = extractSnapshot(measurements, 3);
  if (peso && grasso && peso.delta !== null && grasso.delta !== null) {
    insights.push(analyzePesoGrasso(peso, grasso));
  }

  // 2. Vita + Fianchi
  const vita = extractSnapshot(measurements, 9);
  const fianchi = extractSnapshot(measurements, 10);
  if (vita && fianchi) {
    insights.push(analyzeVitaFianchi(vita, fianchi, sesso));
  }

  // 3. PA Sistolica + Diastolica
  const sistolica = extractSnapshot(measurements, 18);
  const diastolica = extractSnapshot(measurements, 19);
  if (sistolica && diastolica) {
    insights.push(analyzePressione(sistolica, diastolica));
  }

  return insights;
}
