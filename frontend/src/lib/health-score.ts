// src/lib/health-score.ts
/**
 * Health Score Engine — Score composito 0-100 per monitoraggio cliente.
 *
 * Combina 5 domini clinici in un punteggio unico:
 *   - Composizione corporea (25 pt)
 *   - Cardiovascolare (20 pt)
 *   - Training / compliance (25 pt)
 *   - Obiettivi (15 pt)
 *   - Clinico: anamnesi + simmetria (15 pt)
 *
 * Deterministico, zero backend, graceful degradation su dati mancanti.
 */

import type { Severity, CompositionAnalysis, RiskProfile, SymmetryPair } from "@/lib/clinical-analysis";
import type { ClientGoal } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

export interface DomainScore {
  score: number;
  max: number;
  label: string;
  severity: Severity;
}

export interface HealthScoreBreakdown {
  composition: DomainScore;
  cardiovascular: DomainScore;
  training: DomainScore;
  goals: DomainScore;
  clinical: DomainScore;
}

export interface HealthScoreResult {
  total: number;
  breakdown: HealthScoreBreakdown;
  label: string;
  color: string;
}

export interface HealthScoreInput {
  composition: CompositionAnalysis | null;
  riskProfile: RiskProfile | null;
  symmetry: SymmetryPair[];
  goals: ClientGoal[];
  workoutCompliance: number | null;
  anamnesiState: "missing" | "legacy" | "structured";
  hasMeasurements: boolean;
}

// ════════════════════════════════════════════════════════════
// SCORE MAPPINGS
// ════════════════════════════════════════════════════════════

const SEVERITY_TO_COMPOSITION: Record<Severity, number> = {
  positive: 25,
  neutral: 18,
  info: 15,
  warning: 10,
  alert: 5,
};

const SEVERITY_TO_CARDIOVASCULAR: Record<Severity, number> = {
  positive: 20,
  neutral: 15,
  info: 12,
  warning: 8,
  alert: 3,
};

const SEVERITY_TO_SYMMETRY: Record<Severity, number> = {
  positive: 7,
  neutral: 5,
  info: 4,
  warning: 4,
  alert: 2,
};

// ════════════════════════════════════════════════════════════
// MAIN FUNCTION
// ════════════════════════════════════════════════════════════

export function computeHealthScore(input: HealthScoreInput): HealthScoreResult {
  const breakdown: HealthScoreBreakdown = {
    composition: scoreComposition(input),
    cardiovascular: scoreCardiovascular(input),
    training: scoreTraining(input),
    goals: scoreGoals(input),
    clinical: scoreClinical(input),
  };

  const total = Math.min(
    100,
    breakdown.composition.score +
      breakdown.cardiovascular.score +
      breakdown.training.score +
      breakdown.goals.score +
      breakdown.clinical.score,
  );

  return {
    total,
    breakdown,
    label: getScoreLabel(total),
    color: getScoreColor(total),
  };
}

// ════════════════════════════════════════════════════════════
// DOMAIN SCORERS
// ════════════════════════════════════════════════════════════

function scoreComposition(input: HealthScoreInput): DomainScore {
  const max = 25;

  if (!input.composition) {
    // Nessun dato composizione — baseline neutro
    const score = input.hasMeasurements ? 12 : 8;
    return { score, max, label: "Composizione", severity: "neutral" };
  }

  const score = SEVERITY_TO_COMPOSITION[input.composition.phaseSeverity] ?? 12;
  return { score, max, label: "Composizione", severity: input.composition.phaseSeverity };
}

function scoreCardiovascular(input: HealthScoreInput): DomainScore {
  const max = 20;

  if (!input.riskProfile) {
    return { score: 10, max, label: "Cardiovascolare", severity: "neutral" };
  }

  // Usa il worst tra metabolico e cardiovascolare
  const cvScore = SEVERITY_TO_CARDIOVASCULAR[input.riskProfile.cardiovascularRisk] ?? 10;
  const metScore = SEVERITY_TO_CARDIOVASCULAR[input.riskProfile.metabolicRisk] ?? 10;
  const score = Math.min(cvScore, metScore);
  const worst = score <= 8 ? "warning" as Severity : score <= 3 ? "alert" as Severity : input.riskProfile.cardiovascularRisk;

  return { score, max, label: "Cardiovascolare", severity: worst };
}

function scoreTraining(input: HealthScoreInput): DomainScore {
  const max = 25;

  if (input.workoutCompliance === null) {
    // Nessun programma attivo
    return { score: 8, max, label: "Allenamento", severity: "neutral" };
  }

  const pct = input.workoutCompliance;
  let score: number;
  let severity: Severity;

  if (pct >= 90) {
    score = 25;
    severity = "positive";
  } else if (pct >= 80) {
    score = 22;
    severity = "positive";
  } else if (pct >= 70) {
    score = 18;
    severity = "neutral";
  } else if (pct >= 50) {
    score = 12;
    severity = "warning";
  } else {
    score = 6;
    severity = "alert";
  }

  return { score, max, label: "Allenamento", severity };
}

function scoreGoals(input: HealthScoreInput): DomainScore {
  const max = 15;
  const activeGoals = input.goals.filter((g) => g.stato === "attivo");

  if (activeGoals.length === 0) {
    return { score: 5, max, label: "Obiettivi", severity: "neutral" };
  }

  let score = 0;
  for (const goal of activeGoals) {
    const trend = goal.progresso?.tendenza_positiva;
    score += trend === true ? 5 : trend === false ? 2 : 3;
  }

  score = Math.min(max, score);

  const severity: Severity =
    score >= 12 ? "positive" : score >= 8 ? "neutral" : score >= 5 ? "warning" : "alert";

  return { score, max, label: "Obiettivi", severity };
}

function scoreClinical(input: HealthScoreInput): DomainScore {
  const max = 15;

  // Anamnesi: structured=8, legacy=4, missing=0
  const anamnesiScore =
    input.anamnesiState === "structured" ? 8 : input.anamnesiState === "legacy" ? 4 : 0;

  // Simmetria: best score from pairs
  let symmetryScore = 3; // default nessun dato
  if (input.symmetry.length > 0) {
    const worstSeverity = input.symmetry.reduce<Severity>((worst, pair) => {
      const rank: Record<Severity, number> = { positive: 0, neutral: 1, info: 2, warning: 3, alert: 4 };
      return rank[pair.severity] > rank[worst] ? pair.severity : worst;
    }, "positive");
    symmetryScore = SEVERITY_TO_SYMMETRY[worstSeverity] ?? 3;
  }

  const score = anamnesiScore + symmetryScore;
  const severity: Severity =
    score >= 12 ? "positive" : score >= 8 ? "neutral" : score >= 4 ? "warning" : "alert";

  return { score, max, label: "Clinico", severity };
}

// ════════════════════════════════════════════════════════════
// LABELS & COLORS
// ════════════════════════════════════════════════════════════

function getScoreLabel(score: number): string {
  if (score >= 90) return "Eccellente";
  if (score >= 70) return "Buono";
  if (score >= 40) return "Da migliorare";
  return "Critico";
}

function getScoreColor(score: number): string {
  if (score >= 90) return "teal";
  if (score >= 70) return "emerald";
  if (score >= 40) return "amber";
  return "red";
}
