// src/lib/derived-metrics.ts
/**
 * Metriche Derivate — Calcolo client-side da dati raw misurazione.
 *
 * Ogni metrica derivata e' calcolata da 2+ metriche raw gia' misurate.
 * Il chinesiologo inserisce i dati grezzi, il sistema li incrocia.
 *
 * Fonti:
 *   - BMI: OMS (peso / altezza²)
 *   - LBM: peso × (1 − grasso%/100)
 *   - FFMI: Kouri et al. 1995 (LBM / altezza²)
 *   - WHR: OMS (vita / fianchi)
 *   - MAP: Fisiologia cardiovascolare (diastolica + 1/3 × (sistolica − diastolica))
 *   - Forza Relativa: NSCA (1RM / peso corporeo)
 */

import type { Measurement } from "@/types/api";
import { classifyValue } from "@/lib/normative-ranges";

// ════════════════════════════════════════════════════════════
// METRIC IDS (allineati a catalogo metriche seed)
// ════════════════════════════════════════════════════════════

const ID = {
  PESO: 1,
  ALTEZZA: 2,
  GRASSO_PCT: 3,
  MASSA_MAGRA: 4,
  BMI: 5,
  VITA: 9,
  FIANCHI: 10,
  FC_RIPOSO: 17,
  PA_SISTOLICA: 18,
  PA_DIASTOLICA: 19,
  SQUAT_1RM: 20,
  PANCA_1RM: 21,
  STACCO_1RM: 22,
} as const;

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

export interface DerivedMetric {
  id: string;           // "bmi", "lbm", "whr", "ffmi", "map"
  label: string;        // "BMI", "Massa Magra Stimata"
  value: number;
  unit: string;         // "kg/m²", "kg", "", "mmHg"
  /** Classificazione normativa (se disponibile) */
  classification: { label: string; color: string } | null;
  /** Formula usata (tooltip) */
  formula: string;
  /** Fonte scientifica */
  source: string;
}

export interface StrengthRatio {
  label: string;        // "Squat", "Panca Piana", "Stacco da Terra"
  oneRM: number;        // valore 1RM
  ratio: number;        // 1RM / peso
  level: string;        // "Principiante", "Intermedio", "Avanzato", "Elite"
  levelColor: string;   // "amber", "teal", "emerald", "sky"
}

export interface DerivedMetricsResult {
  metrics: DerivedMetric[];
  strengthRatios: StrengthRatio[];
}

// ════════════════════════════════════════════════════════════
// PURE COMPUTATION
// ════════════════════════════════════════════════════════════

/** BMI = peso / (altezza_m)² */
export function computeBMI(peso: number, altezzaCm: number): number | null {
  if (altezzaCm <= 0) return null;
  const h = altezzaCm / 100;
  return Math.round((peso / (h * h)) * 10) / 10;
}

/** LBM = peso × (1 − grasso%/100) */
export function computeLBM(peso: number, grassoPct: number): number | null {
  if (grassoPct < 0 || grassoPct > 100) return null;
  return Math.round(peso * (1 - grassoPct / 100) * 10) / 10;
}

/** FFMI = LBM / (altezza_m)² — Kouri et al. 1995 */
export function computeFFMI(lbm: number, altezzaCm: number): number | null {
  if (altezzaCm <= 0) return null;
  const h = altezzaCm / 100;
  return Math.round((lbm / (h * h)) * 10) / 10;
}

/** WHR = vita / fianchi */
export function computeWHR(vita: number, fianchi: number): number | null {
  if (fianchi <= 0) return null;
  return Math.round((vita / fianchi) * 100) / 100;
}

/** MAP = PA_d + 1/3 × (PA_s − PA_d) */
export function computeMAP(sistolica: number, diastolica: number): number | null {
  return Math.round(diastolica + (sistolica - diastolica) / 3);
}

// ════════════════════════════════════════════════════════════
// STRENGTH BENCHMARKS (NSCA — ratio 1RM/peso)
// ════════════════════════════════════════════════════════════

interface StrengthBenchmark {
  metricId: number;
  label: string;
  /** Soglie M/F per livello (ratio 1RM/peso) */
  thresholds: {
    M: { principiante: number; intermedio: number; avanzato: number; elite: number };
    F: { principiante: number; intermedio: number; avanzato: number; elite: number };
  };
}

const STRENGTH_BENCHMARKS: StrengthBenchmark[] = [
  {
    metricId: ID.SQUAT_1RM,
    label: "Squat",
    thresholds: {
      M: { principiante: 0.75, intermedio: 1.25, avanzato: 1.75, elite: 2.5 },
      F: { principiante: 0.5, intermedio: 0.85, avanzato: 1.25, elite: 1.75 },
    },
  },
  {
    metricId: ID.PANCA_1RM,
    label: "Panca Piana",
    thresholds: {
      M: { principiante: 0.5, intermedio: 1.0, avanzato: 1.5, elite: 2.0 },
      F: { principiante: 0.35, intermedio: 0.65, avanzato: 1.0, elite: 1.4 },
    },
  },
  {
    metricId: ID.STACCO_1RM,
    label: "Stacco da Terra",
    thresholds: {
      M: { principiante: 1.0, intermedio: 1.5, avanzato: 2.0, elite: 2.75 },
      F: { principiante: 0.65, intermedio: 1.0, avanzato: 1.5, elite: 2.0 },
    },
  },
];

function classifyStrength(
  ratio: number,
  sesso: string | null | undefined,
  thresholds: StrengthBenchmark["thresholds"]
): { level: string; color: string } {
  const sex = sesso?.toLowerCase();
  const t =
    sex === "uomo" || sex === "m" || sex === "maschio"
      ? thresholds.M
      : sex === "donna" || sex === "f" || sex === "femmina"
        ? thresholds.F
        : thresholds.M; // fallback M

  if (ratio >= t.elite) return { level: "Elite", color: "sky" };
  if (ratio >= t.avanzato) return { level: "Avanzato", color: "emerald" };
  if (ratio >= t.intermedio) return { level: "Intermedio", color: "teal" };
  if (ratio >= t.principiante) return { level: "Principiante", color: "amber" };
  return { level: "Iniziale", color: "slate" };
}

// ════════════════════════════════════════════════════════════
// WHR CLASSIFICATION (OMS)
// ════════════════════════════════════════════════════════════

function classifyWHR(
  whr: number,
  sesso: string | null | undefined
): { label: string; color: string } | null {
  const sex = sesso?.toLowerCase();

  if (sex === "uomo" || sex === "m" || sex === "maschio") {
    if (whr < 0.9) return { label: "Basso rischio", color: "emerald" };
    if (whr < 1.0) return { label: "Rischio moderato", color: "amber" };
    return { label: "Alto rischio", color: "rose" };
  }
  if (sex === "donna" || sex === "f" || sex === "femmina") {
    if (whr < 0.8) return { label: "Basso rischio", color: "emerald" };
    if (whr < 0.85) return { label: "Rischio moderato", color: "amber" };
    return { label: "Alto rischio", color: "rose" };
  }
  return null;
}

// ════════════════════════════════════════════════════════════
// FFMI CLASSIFICATION (Kouri et al. 1995)
// ════════════════════════════════════════════════════════════

function classifyFFMI(
  ffmi: number,
  sesso: string | null | undefined
): { label: string; color: string } | null {
  const sex = sesso?.toLowerCase();

  if (sex === "uomo" || sex === "m" || sex === "maschio") {
    if (ffmi < 18) return { label: "Sotto la media", color: "amber" };
    if (ffmi < 20) return { label: "Nella media", color: "teal" };
    if (ffmi < 22) return { label: "Sopra la media", color: "emerald" };
    if (ffmi < 25) return { label: "Eccellente", color: "sky" };
    return { label: "Sospetto", color: "rose" }; // >25 naturalmente improbabile
  }
  if (sex === "donna" || sex === "f" || sex === "femmina") {
    if (ffmi < 14) return { label: "Sotto la media", color: "amber" };
    if (ffmi < 17) return { label: "Nella media", color: "teal" };
    if (ffmi < 19) return { label: "Sopra la media", color: "emerald" };
    if (ffmi < 22) return { label: "Eccellente", color: "sky" };
    return { label: "Sospetto", color: "rose" };
  }
  return null;
}

// ════════════════════════════════════════════════════════════
// MAP CLASSIFICATION
// ════════════════════════════════════════════════════════════

function classifyMAP(map: number): { label: string; color: string } {
  if (map < 70) return { label: "Ipotensione", color: "amber" };
  if (map <= 100) return { label: "Normale", color: "emerald" };
  if (map <= 110) return { label: "Elevata", color: "amber" };
  return { label: "Ipertensione", color: "rose" };
}

// ════════════════════════════════════════════════════════════
// PUBLIC API
// ════════════════════════════════════════════════════════════

/** Estrae il valore piu' recente per una metrica. */
export function getLatestValue(measurements: Measurement[], metricId: number): number | null {
  for (let i = measurements.length - 1; i >= 0; i--) {
    // measurements arrivano gia' ordinate DESC dal backend
    const val = measurements[i].valori.find((v) => v.id_metrica === metricId);
    if (val) return val.valore;
  }
  return null;
}

/**
 * Calcola tutte le metriche derivate disponibili dalle misurazioni.
 * Ritorna solo quelle per cui i dati raw sono presenti.
 */
export function computeAllDerived(
  measurements: Measurement[],
  sesso?: string | null,
  age?: number | null,
): DerivedMetricsResult {
  const metrics: DerivedMetric[] = [];
  const strengthRatios: StrengthRatio[] = [];

  const peso = getLatestValue(measurements, ID.PESO);
  const altezza = getLatestValue(measurements, ID.ALTEZZA);
  const grassoPct = getLatestValue(measurements, ID.GRASSO_PCT);
  const vita = getLatestValue(measurements, ID.VITA);
  const fianchi = getLatestValue(measurements, ID.FIANCHI);
  const paSist = getLatestValue(measurements, ID.PA_SISTOLICA);
  const paDiast = getLatestValue(measurements, ID.PA_DIASTOLICA);

  // ── BMI ──
  if (peso !== null && altezza !== null) {
    const bmi = computeBMI(peso, altezza);
    if (bmi !== null) {
      metrics.push({
        id: "bmi",
        label: "BMI",
        value: bmi,
        unit: "kg/m\u00B2",
        classification: classifyValue(ID.BMI, bmi, sesso, age),
        formula: `${peso} / (${altezza}/100)\u00B2`,
        source: "OMS",
      });
    }
  }

  // ── LBM (Massa Magra Stimata) ──
  let lbm: number | null = null;
  if (peso !== null && grassoPct !== null) {
    lbm = computeLBM(peso, grassoPct);
    if (lbm !== null) {
      metrics.push({
        id: "lbm",
        label: "Massa Magra Stimata",
        value: lbm,
        unit: "kg",
        classification: null, // no normative bands for LBM
        formula: `${peso} \u00D7 (1 \u2212 ${grassoPct}/100)`,
        source: "Derivata",
      });
    }
  }

  // ── FFMI ──
  if (lbm !== null && altezza !== null) {
    const ffmi = computeFFMI(lbm, altezza);
    if (ffmi !== null) {
      metrics.push({
        id: "ffmi",
        label: "FFMI",
        value: ffmi,
        unit: "kg/m\u00B2",
        classification: classifyFFMI(ffmi, sesso),
        formula: `${lbm} / (${altezza}/100)\u00B2`,
        source: "Kouri et al. 1995",
      });
    }
  }

  // ── WHR ──
  if (vita !== null && fianchi !== null) {
    const whr = computeWHR(vita, fianchi);
    if (whr !== null) {
      metrics.push({
        id: "whr",
        label: "WHR",
        value: whr,
        unit: "",
        classification: classifyWHR(whr, sesso),
        formula: `${vita} / ${fianchi}`,
        source: "OMS",
      });
    }
  }

  // ── MAP ──
  if (paSist !== null && paDiast !== null) {
    const map = computeMAP(paSist, paDiast);
    if (map !== null) {
      metrics.push({
        id: "map",
        label: "PAM",
        value: map,
        unit: "mmHg",
        classification: classifyMAP(map),
        formula: `${paDiast} + \u2153 \u00D7 (${paSist} \u2212 ${paDiast})`,
        source: "Fisiologia CV",
      });
    }
  }

  // ── Forza Relativa ──
  if (peso !== null) {
    for (const bench of STRENGTH_BENCHMARKS) {
      const oneRM = getLatestValue(measurements, bench.metricId);
      if (oneRM !== null) {
        const ratio = Math.round((oneRM / peso) * 100) / 100;
        const { level, color } = classifyStrength(ratio, sesso, bench.thresholds);
        strengthRatios.push({
          label: bench.label,
          oneRM,
          ratio,
          level,
          levelColor: color,
        });
      }
    }
  }

  return { metrics, strengthRatios };
}
