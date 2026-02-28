// src/lib/clinical-analysis.ts
/**
 * Clinical Analysis Engine — Analisi chinesiologica multi-modulo.
 *
 * Orchestratore che combina:
 *   1. Metriche derivate (BMI, LBM, FFMI, WHR, MAP, Forza Relativa)
 *   2. Assessment velocita' di cambiamento (rate vs soglie ACSM)
 *   3. Analisi composizione corporea (fase, decomposizione, proiezione)
 *   4. Simmetria bilaterale (R/L braccia, cosce, polpacci)
 *   5. Profilo rischio composito (metabolico + cardiovascolare)
 *
 * Filosofia: INFORMARE, mai LIMITARE. Il chinesiologo decide sempre.
 */

import type { Measurement, ClientGoal } from "@/types/api";
import { computeWeeklyRate } from "@/lib/measurement-analytics";
import { classifyValue, computeAge } from "@/lib/normative-ranges";
import {
  computeAllDerived,
  getLatestValue,
  type DerivedMetricsResult,
} from "@/lib/derived-metrics";

// ════════════════════════════════════════════════════════════
// METRIC IDS
// ════════════════════════════════════════════════════════════

const ID = {
  PESO: 1,
  ALTEZZA: 2,
  GRASSO_PCT: 3,
  MASSA_MAGRA: 4,
  BMI: 5,
  VITA: 9,
  FIANCHI: 10,
  BRACCIO_DX: 11,
  BRACCIO_SX: 12,
  COSCIA_DX: 13,
  COSCIA_SX: 14,
  POLPACCIO_DX: 15,
  POLPACCIO_SX: 16,
  FC_RIPOSO: 17,
  PA_SISTOLICA: 18,
  PA_DIASTOLICA: 19,
} as const;

// ════════════════════════════════════════════════════════════
// TYPES — Report completo
// ════════════════════════════════════════════════════════════

export type Severity = "positive" | "neutral" | "warning" | "alert" | "info";

export interface RateAssessment {
  metricLabel: string;
  rate: number;          // delta/settimana
  unit: string;
  assessment: string;    // "Velocita' sicura", "Rischio catabolismo"
  severity: Severity;
  guideline: string;     // "ACSM: max 1% peso/sett"
  /** Percentuale peso corporeo (solo per peso) */
  pctBodyWeight?: number;
}

export type CompositionPhase =
  | "cutting"       // peso↓ grasso↓
  | "lean_bulk"     // peso↑ grasso=
  | "recomp"        // peso= grasso↓
  | "bulk"          // peso↑ grasso↑
  | "muscle_loss"   // peso↓ grasso=
  | "optimal_growth" // peso↑ grasso↓
  | "critical"      // peso↓ grasso↑
  | "plateau"       // entrambi stabili
  | null;

export interface CompositionAnalysis {
  phase: CompositionPhase;
  phaseLabel: string;
  phaseSeverity: Severity;
  phaseDescription: string;
  /** Decomposizione delta peso: FM + LBM */
  deltaFM: number | null;    // kg grasso perso/guadagnato
  deltaLBM: number | null;   // kg muscolo perso/guadagnato
  /** Proiezione (se obiettivo peso attivo) */
  projection: {
    weeksToGoal: number;
    targetDate: string;       // ISO date stimata
    targetValue: number;
  } | null;
  /** Rate assessment ACSM */
  rateAssessment: string | null;
}

export interface SymmetryPair {
  label: string;       // "Braccia", "Cosce", "Polpacci"
  rightLabel: string;  // "Destro"
  leftLabel: string;   // "Sinistro"
  right: number;
  left: number;
  delta: number;       // |right - left|
  deltaPct: number;    // % differenza rispetto alla media
  severity: Severity;
  note: string;        // "Nella norma" / "Asimmetria lieve" / "Asimmetria significativa"
}

export interface RiskFactor {
  label: string;       // "WHR elevato", "BMI sovrappeso"
  value: string;       // "0.95", "27.3"
  severity: Severity;
}

export interface RiskProfile {
  metabolicFactors: RiskFactor[];
  cardiovascularFactors: RiskFactor[];
  metabolicRisk: Severity;
  cardiovascularRisk: Severity;
  summary: string;
  /** Suggerimento referral (solo se alert) */
  referral: string | null;
}

export interface ClinicalReport {
  /** Modulo 1: Metriche derivate */
  derived: DerivedMetricsResult;
  /** Modulo 2: Assessment velocita' */
  rateAssessments: RateAssessment[];
  /** Modulo 3: Composizione corporea */
  composition: CompositionAnalysis | null;
  /** Modulo 4: Simmetria bilaterale */
  symmetry: SymmetryPair[];
  /** Modulo 5: Profilo rischio */
  riskProfile: RiskProfile | null;
  /** Flag: report ha contenuto significativo? */
  hasData: boolean;
}

// ════════════════════════════════════════════════════════════
// MODULE 2: RATE ASSESSMENT
// ════════════════════════════════════════════════════════════

interface RateConfig {
  metricId: number;
  label: string;
  unit: string;
  /** Soglia warning (valore assoluto rate/settimana) */
  warningThreshold: number;
  /** Soglia alert */
  alertThreshold: number;
  /** La direzione "negativa" e' il calo? */
  lowerIsBetter: boolean;
  guideline: string;
}

const RATE_CONFIGS: RateConfig[] = [
  {
    metricId: ID.PESO,
    label: "Peso",
    unit: "kg",
    warningThreshold: 0.7,  // ~0.9% di 80kg
    alertThreshold: 1.0,    // ~1.2% di 80kg
    lowerIsBetter: true,
    guideline: "ACSM: perdita max 0.5\u20131% peso/sett",
  },
  {
    metricId: ID.GRASSO_PCT,
    label: "Massa Grassa",
    unit: "%",
    warningThreshold: 0.5,
    alertThreshold: 0.8,
    lowerIsBetter: true,
    guideline: "Velocita' sostenibile: 0.3\u20130.5%/sett",
  },
  {
    metricId: ID.PA_SISTOLICA,
    label: "PA Sistolica",
    unit: "mmHg",
    warningThreshold: 3,
    alertThreshold: 5,
    lowerIsBetter: true,
    guideline: "Trend in aumento richiede monitoraggio",
  },
  {
    metricId: ID.FC_RIPOSO,
    label: "FC Riposo",
    unit: "bpm",
    warningThreshold: 3,
    alertThreshold: 5,
    lowerIsBetter: true,
    guideline: "Trend in aumento puo' indicare overtraining",
  },
];

function buildRateAssessments(
  measurements: Measurement[],
  peso: number | null,
): RateAssessment[] {
  const results: RateAssessment[] = [];

  for (const cfg of RATE_CONFIGS) {
    const rate = computeWeeklyRate(measurements, cfg.metricId);
    if (rate === null) continue;

    const absRate = Math.abs(rate);
    let assessment: string;
    let severity: Severity;

    // Per metriche "lower is better": rate negativa = buono
    const isGoingDown = rate < 0;
    const isGoodDirection = cfg.lowerIsBetter ? isGoingDown : !isGoingDown;

    if (absRate < 0.1) {
      assessment = "Plateau — nessun cambiamento significativo";
      severity = "neutral";
    } else if (isGoodDirection) {
      // Direzione corretta — ma velocita' ok?
      if (absRate >= cfg.alertThreshold) {
        assessment = "Velocita' eccessiva — rischio salute";
        severity = "alert";
      } else if (absRate >= cfg.warningThreshold) {
        assessment = "Velocita' elevata — monitorare";
        severity = "warning";
      } else {
        assessment = "Progressione ottimale";
        severity = "positive";
      }
    } else {
      // Direzione opposta
      if (absRate >= cfg.alertThreshold) {
        assessment = "Trend avverso significativo";
        severity = "alert";
      } else if (absRate >= cfg.warningThreshold) {
        assessment = "Trend in controtendenza";
        severity = "warning";
      } else {
        assessment = "Variazione lieve";
        severity = "neutral";
      }
    }

    const entry: RateAssessment = {
      metricLabel: cfg.label,
      rate,
      unit: cfg.unit,
      assessment,
      severity,
      guideline: cfg.guideline,
    };

    // Percentuale peso corporeo (solo per peso)
    if (cfg.metricId === ID.PESO && peso !== null && peso > 0) {
      entry.pctBodyWeight = Math.round((absRate / peso) * 10000) / 100;
    }

    results.push(entry);
  }

  return results;
}

// ════════════════════════════════════════════════════════════
// MODULE 3: COMPOSITION ANALYSIS
// ════════════════════════════════════════════════════════════

function buildCompositionAnalysis(
  measurements: Measurement[],
  goals?: ClientGoal[],
): CompositionAnalysis | null {
  const pesoRate = computeWeeklyRate(measurements, ID.PESO);
  const grassoRate = computeWeeklyRate(measurements, ID.GRASSO_PCT);

  if (pesoRate === null && grassoRate === null) return null;

  // ── Phase detection ──
  const pr = pesoRate ?? 0;
  const gr = grassoRate ?? 0;
  const threshold = 0.1;

  let phase: CompositionPhase;
  let phaseLabel: string;
  let phaseSeverity: Severity;
  let phaseDescription: string;

  if (pr < -threshold && gr < -threshold) {
    phase = "cutting";
    phaseLabel = "Fase di Definizione";
    phaseSeverity = "positive";
    phaseDescription = "Peso e massa grassa in calo. Composizione in miglioramento.";
  } else if (pr > threshold && Math.abs(gr) <= threshold) {
    phase = "lean_bulk";
    phaseLabel = "Crescita Pulita";
    phaseSeverity = "positive";
    phaseDescription = "Peso in aumento con grasso stabile. Probabile incremento muscolare.";
  } else if (Math.abs(pr) <= threshold && gr < -threshold) {
    phase = "recomp";
    phaseLabel = "Ricomposizione Corporea";
    phaseSeverity = "positive";
    phaseDescription = "Peso stabile con grasso in calo. La massa magra sta sostituendo il grasso.";
  } else if (pr > threshold && gr > threshold) {
    phase = "bulk";
    phaseLabel = "Fase di Massa";
    phaseSeverity = "warning";
    phaseDescription = "Peso e grasso in aumento. Valutare bilancio calorico e tipo di allenamento.";
  } else if (pr < -threshold && Math.abs(gr) <= threshold) {
    phase = "muscle_loss";
    phaseLabel = "Possibile Perdita Muscolare";
    phaseSeverity = "warning";
    phaseDescription = "Il peso cala ma il grasso resta stabile. Verificare apporto proteico e volume allenamento.";
  } else if (pr > threshold && gr < -threshold) {
    phase = "optimal_growth";
    phaseLabel = "Crescita Muscolare Ottimale";
    phaseSeverity = "positive";
    phaseDescription = "Peso in aumento e grasso in calo. Fase di crescita muscolare ideale.";
  } else if (pr < -threshold && gr > threshold) {
    phase = "critical";
    phaseLabel = "Attenzione — Composizione Critica";
    phaseSeverity = "alert";
    phaseDescription = "Peso in calo ma grasso in aumento. Verificare dieta e programma di allenamento.";
  } else {
    phase = "plateau";
    phaseLabel = "Plateau";
    phaseSeverity = "neutral";
    phaseDescription = "Peso e massa grassa stabili. Considerare cambio strategia se non intenzionale.";
  }

  // ── Decomposizione delta peso in FM + LBM ──
  let deltaFM: number | null = null;
  let deltaLBM: number | null = null;

  const peso = getLatestValue(measurements, ID.PESO);
  const grassoPct = getLatestValue(measurements, ID.GRASSO_PCT);
  // Cerca valori precedenti
  const sorted = measurements
    .slice()
    .sort((a, b) => a.data_misurazione.localeCompare(b.data_misurazione));

  if (sorted.length >= 2 && peso !== null && grassoPct !== null) {
    // Trova la penultima misurazione con entrambi i valori
    for (let i = sorted.length - 2; i >= 0; i--) {
      const prevPeso = sorted[i].valori.find((v) => v.id_metrica === ID.PESO);
      const prevGrasso = sorted[i].valori.find((v) => v.id_metrica === ID.GRASSO_PCT);
      if (prevPeso && prevGrasso) {
        const prevFM = prevPeso.valore * (prevGrasso.valore / 100);
        const prevLBM = prevPeso.valore - prevFM;
        const currFM = peso * (grassoPct / 100);
        const currLBM = peso - currFM;
        deltaFM = Math.round((currFM - prevFM) * 10) / 10;
        deltaLBM = Math.round((currLBM - prevLBM) * 10) / 10;
        break;
      }
    }
  }

  // ── Proiezione tempo-a-target ──
  let projection: CompositionAnalysis["projection"] = null;

  if (goals && pesoRate !== null && Math.abs(pesoRate) > 0.05) {
    const pesoGoal = goals.find(
      (g) => g.id_metrica === ID.PESO && g.stato === "attivo" && g.valore_target !== null
    );
    if (pesoGoal && peso !== null) {
      const remaining = pesoGoal.valore_target! - peso;
      // Solo se la direzione del rate e' coerente col target
      if ((remaining > 0 && pesoRate > 0) || (remaining < 0 && pesoRate < 0)) {
        const weeksToGoal = Math.abs(remaining / pesoRate);
        if (weeksToGoal > 0 && weeksToGoal < 104) { // max 2 anni
          const targetDate = new Date();
          targetDate.setDate(targetDate.getDate() + Math.round(weeksToGoal * 7));
          projection = {
            weeksToGoal: Math.round(weeksToGoal * 10) / 10,
            targetDate: targetDate.toISOString().slice(0, 10),
            targetValue: pesoGoal.valore_target!,
          };
        }
      }
    }
  }

  // ── Rate assessment ACSM (per peso) ──
  let rateAssessment: string | null = null;
  if (pesoRate !== null && peso !== null && peso > 0) {
    const pctPerWeek = Math.abs(pesoRate / peso) * 100;
    if (pesoRate < 0) {
      if (pctPerWeek > 1.0) {
        rateAssessment = `Perdita ${pctPerWeek.toFixed(1)}%/sett — supera il limite ACSM dell'1%. Rischio catabolismo muscolare.`;
      } else if (pctPerWeek > 0.5) {
        rateAssessment = `Perdita ${pctPerWeek.toFixed(1)}%/sett — nella fascia alta ma sicura (ACSM: 0.5\u20131%).`;
      } else {
        rateAssessment = `Perdita ${pctPerWeek.toFixed(1)}%/sett — velocita' conservativa e sostenibile.`;
      }
    }
  }

  return {
    phase,
    phaseLabel,
    phaseSeverity,
    phaseDescription,
    deltaFM,
    deltaLBM,
    projection,
    rateAssessment,
  };
}

// ════════════════════════════════════════════════════════════
// MODULE 4: SYMMETRY
// ════════════════════════════════════════════════════════════

interface SymmetryConfig {
  label: string;
  rightId: number;
  leftId: number;
  rightLabel: string;
  leftLabel: string;
  /** Soglia warning (cm) */
  warningThreshold: number;
  /** Soglia alert (cm) */
  alertThreshold: number;
}

const SYMMETRY_CONFIGS: SymmetryConfig[] = [
  {
    label: "Braccia",
    rightId: ID.BRACCIO_DX,
    leftId: ID.BRACCIO_SX,
    rightLabel: "Destro",
    leftLabel: "Sinistro",
    warningThreshold: 1.0,
    alertThreshold: 2.0,
  },
  {
    label: "Cosce",
    rightId: ID.COSCIA_DX,
    leftId: ID.COSCIA_SX,
    rightLabel: "Destra",
    leftLabel: "Sinistra",
    warningThreshold: 1.5,
    alertThreshold: 2.5,
  },
  {
    label: "Polpacci",
    rightId: ID.POLPACCIO_DX,
    leftId: ID.POLPACCIO_SX,
    rightLabel: "Destro",
    leftLabel: "Sinistro",
    warningThreshold: 1.0,
    alertThreshold: 2.0,
  },
];

function buildSymmetryChecks(measurements: Measurement[]): SymmetryPair[] {
  const results: SymmetryPair[] = [];

  for (const cfg of SYMMETRY_CONFIGS) {
    const right = getLatestValue(measurements, cfg.rightId);
    const left = getLatestValue(measurements, cfg.leftId);

    if (right === null || left === null) continue;

    const delta = Math.abs(right - left);
    const avg = (right + left) / 2;
    const deltaPct = avg > 0 ? Math.round((delta / avg) * 1000) / 10 : 0;

    let severity: Severity;
    let note: string;

    if (delta >= cfg.alertThreshold) {
      severity = "alert";
      note = `Asimmetria significativa (\u0394 ${delta.toFixed(1)} cm). Consigliare lavoro unilaterale compensativo.`;
    } else if (delta >= cfg.warningThreshold) {
      severity = "warning";
      note = `Asimmetria lieve (\u0394 ${delta.toFixed(1)} cm). Monitorare nel tempo.`;
    } else {
      severity = "positive";
      note = "Nella norma";
    }

    results.push({
      label: cfg.label,
      rightLabel: cfg.rightLabel,
      leftLabel: cfg.leftLabel,
      right: Math.round(right * 10) / 10,
      left: Math.round(left * 10) / 10,
      delta: Math.round(delta * 10) / 10,
      deltaPct,
      severity,
      note,
    });
  }

  return results;
}

// ════════════════════════════════════════════════════════════
// MODULE 5: RISK PROFILE
// ════════════════════════════════════════════════════════════

function buildRiskProfile(
  measurements: Measurement[],
  derived: DerivedMetricsResult,
  sesso?: string | null,
  age?: number | null,
): RiskProfile | null {
  const metabolicFactors: RiskFactor[] = [];
  const cardiovascularFactors: RiskFactor[] = [];

  // ── Fattori metabolici ──
  const bmiDerived = derived.metrics.find((m) => m.id === "bmi");
  if (bmiDerived) {
    const cls = bmiDerived.classification;
    if (cls) {
      const severity: Severity =
        cls.color === "rose" ? "alert" :
        cls.color === "orange" ? "warning" :
        cls.color === "amber" && bmiDerived.value >= 25 ? "warning" :
        "positive";
      metabolicFactors.push({
        label: `BMI: ${cls.label}`,
        value: `${bmiDerived.value} kg/m\u00B2`,
        severity,
      });
    }
  }

  const whrDerived = derived.metrics.find((m) => m.id === "whr");
  if (whrDerived && whrDerived.classification) {
    const cls = whrDerived.classification;
    const severity: Severity =
      cls.color === "rose" ? "alert" :
      cls.color === "amber" ? "warning" :
      "positive";
    metabolicFactors.push({
      label: `WHR: ${cls.label}`,
      value: `${whrDerived.value}`,
      severity,
    });
  }

  const grassoPct = getLatestValue(measurements, ID.GRASSO_PCT);
  if (grassoPct !== null) {
    const cls = classifyValue(ID.GRASSO_PCT, grassoPct, sesso, age);
    if (cls) {
      const severity: Severity =
        cls.color === "rose" ? "alert" :
        cls.color === "amber" ? "warning" :
        "positive";
      metabolicFactors.push({
        label: `Grasso %: ${cls.label}`,
        value: `${grassoPct}%`,
        severity,
      });
    }
  }

  // ── Fattori cardiovascolari ──
  const paSist = getLatestValue(measurements, ID.PA_SISTOLICA);
  const paDiast = getLatestValue(measurements, ID.PA_DIASTOLICA);

  if (paSist !== null) {
    const cls = classifyValue(ID.PA_SISTOLICA, paSist, sesso, age);
    if (cls) {
      const severity: Severity =
        cls.color === "rose" ? "alert" :
        cls.color === "orange" ? "warning" :
        cls.color === "amber" ? "warning" :
        "positive";
      cardiovascularFactors.push({
        label: `PA Sistolica: ${cls.label}`,
        value: `${paSist} mmHg`,
        severity,
      });
    }
  }

  if (paDiast !== null) {
    const cls = classifyValue(ID.PA_DIASTOLICA, paDiast, sesso, age);
    if (cls) {
      const severity: Severity =
        cls.color === "rose" ? "alert" :
        cls.color === "orange" ? "warning" :
        cls.color === "amber" ? "warning" :
        "positive";
      cardiovascularFactors.push({
        label: `PA Diastolica: ${cls.label}`,
        value: `${paDiast} mmHg`,
        severity,
      });
    }
  }

  const fcRiposo = getLatestValue(measurements, ID.FC_RIPOSO);
  if (fcRiposo !== null) {
    const cls = classifyValue(ID.FC_RIPOSO, fcRiposo, sesso, age);
    if (cls) {
      const severity: Severity =
        cls.color === "rose" ? "alert" :
        cls.color === "orange" ? "warning" :
        cls.color === "amber" ? "neutral" :
        "positive";
      cardiovascularFactors.push({
        label: `FC Riposo: ${cls.label}`,
        value: `${fcRiposo} bpm`,
        severity,
      });
    }
  }

  // Se nessun fattore, non mostrare il profilo
  if (metabolicFactors.length === 0 && cardiovascularFactors.length === 0) {
    return null;
  }

  // ── Severity composita ──
  const allFactors = [...metabolicFactors, ...cardiovascularFactors];
  const hasAlert = allFactors.some((f) => f.severity === "alert");
  const hasWarning = allFactors.some((f) => f.severity === "warning");

  const metabolicRisk: Severity = metabolicFactors.some((f) => f.severity === "alert")
    ? "alert" : metabolicFactors.some((f) => f.severity === "warning")
    ? "warning" : "positive";

  const cardiovascularRisk: Severity = cardiovascularFactors.some((f) => f.severity === "alert")
    ? "alert" : cardiovascularFactors.some((f) => f.severity === "warning")
    ? "warning" : "positive";

  // ── Summary ──
  let summary: string;
  let referral: string | null = null;

  if (hasAlert) {
    const alertCount = allFactors.filter((f) => f.severity === "alert").length;
    summary = `${alertCount} ${alertCount === 1 ? "indicatore critico" : "indicatori critici"} rilevat${alertCount === 1 ? "o" : "i"}. Valutare referral medico.`;
    referral = "Indicatori fuori range suggeriscono una valutazione medica di approfondimento.";
  } else if (hasWarning) {
    summary = "Alcuni indicatori da monitorare. Nessun intervento urgente.";
  } else {
    summary = "Tutti gli indicatori nella norma.";
  }

  return {
    metabolicFactors,
    cardiovascularFactors,
    metabolicRisk,
    cardiovascularRisk,
    summary,
    referral,
  };
}

// ════════════════════════════════════════════════════════════
// PUBLIC API
// ════════════════════════════════════════════════════════════

/**
 * Genera il report clinico completo dalle misurazioni.
 * Ogni modulo produce output solo se i dati necessari sono presenti.
 */
export function generateClinicalReport(
  measurements: Measurement[],
  sesso?: string | null,
  dataNascita?: string | null,
  goals?: ClientGoal[],
): ClinicalReport {
  if (measurements.length === 0) {
    return {
      derived: { metrics: [], strengthRatios: [] },
      rateAssessments: [],
      composition: null,
      symmetry: [],
      riskProfile: null,
      hasData: false,
    };
  }

  const age = computeAge(dataNascita);
  const peso = getLatestValue(measurements, ID.PESO);

  // Modulo 1: Metriche derivate
  const derived = computeAllDerived(measurements, sesso, age);

  // Modulo 2: Rate assessment
  const rateAssessments = buildRateAssessments(measurements, peso);

  // Modulo 3: Composizione corporea
  const composition = buildCompositionAnalysis(measurements, goals);

  // Modulo 4: Simmetria bilaterale
  const symmetry = buildSymmetryChecks(measurements);

  // Modulo 5: Profilo rischio
  const riskProfile = buildRiskProfile(measurements, derived, sesso, age);

  const hasData =
    derived.metrics.length > 0 ||
    derived.strengthRatios.length > 0 ||
    rateAssessments.length > 0 ||
    composition !== null ||
    symmetry.length > 0 ||
    riskProfile !== null;

  return {
    derived,
    rateAssessments,
    composition,
    symmetry,
    riskProfile,
    hasData,
  };
}
