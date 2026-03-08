// src/lib/demand-aggregation.ts
/**
 * Aggregazione del profilo di carico per sessione e settimana.
 *
 * Calcola la distribuzione del volume (serie) per dimensione di movimento
 * aggregando gli esercizi presenti nel builder. Puro frontend, zero API call.
 *
 * 7 dimensioni primarie (pattern di forza):
 *   push_h, pull_h, push_v, pull_v, squat, hinge, core
 * 3 dimensioni secondarie (costo biomeccanico aggregato):
 *   carry, axial_load, joint_stress
 *
 * axial_load e joint_stress derivano dalla media pesata dei demand vector
 * degli esercizi nella sessione (campi axial_load_demand, shoulder_complex_demand).
 */

import type { Exercise } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TIPI
// ════════════════════════════════════════════════════════════

export const PRIMARY_DIMENSIONS = [
  "push_h", "pull_h", "push_v", "pull_v", "squat", "hinge", "core",
] as const;

export const SECONDARY_DIMENSIONS = ["carry", "axial_load", "joint_stress"] as const;

export type PrimaryDimension = (typeof PRIMARY_DIMENSIONS)[number];
export type SecondaryDimension = (typeof SECONDARY_DIMENSIONS)[number];
export type DemandDimension = PrimaryDimension | SecondaryDimension;

export const DIMENSION_LABELS: Record<DemandDimension, string> = {
  push_h: "Spinta orizzontale",
  pull_h: "Trazione orizzontale",
  push_v: "Spinta verticale",
  pull_v: "Trazione verticale",
  squat: "Accosciata",
  hinge: "Hip hinge",
  core: "Core",
  carry: "Trasporto",
  axial_load: "Carico assiale",
  joint_stress: "Stress articolare",
};

export interface DemandProfile {
  /** Serie totali per dimensione */
  values: Record<DemandDimension, number>;
  /** Distribuzione percentuale (0-1) per dimensione primaria */
  distribution: Record<PrimaryDimension, number>;
  /** Serie totali aggregate */
  totalSeries: number;
}

// Pattern isolamento → dimensione primaria mappata
const ISOLATION_TO_PRIMARY: Record<string, PrimaryDimension | null> = {
  hip_thrust: "hinge",
  curl: "pull_h",
  extension_tri: "push_h",
  lateral_raise: "push_v",
  face_pull: "pull_h",
  calf_raise: null,
  leg_curl: "hinge",
  leg_extension: "squat",
  adductor: "squat",
};

// ════════════════════════════════════════════════════════════
// FUNZIONI
// ════════════════════════════════════════════════════════════

function emptyValues(): Record<DemandDimension, number> {
  const v: Partial<Record<DemandDimension, number>> = {};
  for (const d of PRIMARY_DIMENSIONS) v[d] = 0;
  for (const d of SECONDARY_DIMENSIONS) v[d] = 0;
  return v as Record<DemandDimension, number>;
}

function patternToPrimary(pattern: string): PrimaryDimension | null {
  if (PRIMARY_DIMENSIONS.includes(pattern as PrimaryDimension)) {
    return pattern as PrimaryDimension;
  }
  return ISOLATION_TO_PRIMARY[pattern] ?? null;
}

/**
 * Aggrega il profilo di carico per una singola sessione.
 */
export function aggregateSessionDemand(
  esercizi: Array<{ id_esercizio: number; serie: number }>,
  exerciseMap: Map<number, Exercise>,
): DemandProfile {
  const values = emptyValues();
  let totalSeries = 0;

  for (const ex of esercizi) {
    const exercise = exerciseMap.get(ex.id_esercizio);
    if (!exercise) continue;

    const primary = patternToPrimary(exercise.pattern_movimento);
    if (primary) {
      values[primary] += ex.serie;
      totalSeries += ex.serie;
    } else if (exercise.pattern_movimento === "carry") {
      values.carry += ex.serie;
      totalSeries += ex.serie;
    }

    // Secondarie: accumula demand biomeccanico pesato per serie
    values.axial_load += (exercise.axial_load_demand ?? 0) * ex.serie;
    values.joint_stress += (exercise.shoulder_complex_demand ?? 0) * ex.serie;
  }

  // Distribuzione percentuale sulle primarie
  const primaryTotal = PRIMARY_DIMENSIONS.reduce((s, d) => s + values[d], 0);
  const distribution: Record<string, number> = {};
  for (const d of PRIMARY_DIMENSIONS) {
    distribution[d] = primaryTotal > 0 ? values[d] / primaryTotal : 0;
  }

  return {
    values,
    distribution: distribution as Record<PrimaryDimension, number>,
    totalSeries,
  };
}

/**
 * Aggrega il profilo di carico settimanale da tutte le sessioni.
 */
export function aggregateWeeklyDemand(
  sessions: Array<{
    nome_sessione: string;
    esercizi: Array<{ id_esercizio: number; serie: number }>;
  }>,
  exerciseMap: Map<number, Exercise>,
): DemandProfile {
  const values = emptyValues();
  let totalSeries = 0;

  for (const session of sessions) {
    const sessionProfile = aggregateSessionDemand(session.esercizi, exerciseMap);
    for (const d of [...PRIMARY_DIMENSIONS, ...SECONDARY_DIMENSIONS]) {
      values[d] += sessionProfile.values[d];
    }
    totalSeries += sessionProfile.totalSeries;
  }

  const primaryTotal = PRIMARY_DIMENSIONS.reduce((s, d) => s + values[d], 0);
  const distribution: Record<string, number> = {};
  for (const d of PRIMARY_DIMENSIONS) {
    distribution[d] = primaryTotal > 0 ? values[d] / primaryTotal : 0;
  }

  return {
    values,
    distribution: distribution as Record<PrimaryDimension, number>,
    totalSeries,
  };
}

/**
 * Rileva dimensioni primarie concentrate oltre una soglia (default 40%).
 * Ritorna le dimensioni che superano la soglia con il loro valore %.
 */
export function detectDemandConcentration(
  profile: DemandProfile,
  threshold = 0.40,
): Array<{ dimension: PrimaryDimension; percentage: number }> {
  return PRIMARY_DIMENSIONS
    .filter((d) => profile.distribution[d] > threshold)
    .map((d) => ({ dimension: d, percentage: profile.distribution[d] }));
}
