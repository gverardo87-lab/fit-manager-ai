// src/lib/smart-programming/analysis.ts
/**
 * Analisi copertura muscolare, volume, biomeccanica, recupero e safety.
 * Queste funzioni analizzano una scheda gia' compilata nel builder.
 */

import type { Exercise, ExerciseSafetyEntry } from "@/types/api";
import { getSectionForCategory } from "@/lib/workout-templates";
import type {
  FitnessLevel,
  CoverageStatus,
  MuscleCoverage,
  VolumeAnalysis,
  BiomechanicalVariety,
  RecoveryConflict,
  SmartAnalysis,
  SafetyBreakdown,
} from "./types";
import { MUSCLE_GROUPS, normalizeMuscleGroup } from "./helpers";
import { getMuscleTarget, TOTAL_VOLUME_TARGETS } from "./blueprints";

// ── Muscle Coverage ──

/**
 * Analizza la copertura muscolare di un set di sessioni.
 * Conta set/muscolo/settimana con credit: primario=1.0, secondario=max 0.35.
 */
export function computeMuscleCoverage(
  sessions: Array<{ esercizi: Array<{ id_esercizio: number; serie: number }> }>,
  exerciseMap: Map<number, Exercise>,
  livello: FitnessLevel,
  sessioniPerSettimana?: number,
): MuscleCoverage[] {
  const setCounts: Record<string, number> = {};

  for (const session of sessions) {
    for (const ex of session.esercizi) {
      const exercise = exerciseMap.get(ex.id_esercizio);
      if (!exercise) continue;
      if (getSectionForCategory(exercise.categoria) !== "principale") continue;

      for (const m of exercise.muscoli_primari) {
        const group = normalizeMuscleGroup(m);
        setCounts[group] = (setCounts[group] ?? 0) + ex.serie * 1.0;
      }
      // Credito secondario diluted: budget 1.0/N, max 0.35
      const secLen = exercise.muscoli_secondari.length;
      const secCredit = secLen > 0 ? Math.min(0.35, 1.0 / secLen) : 0;
      for (const m of exercise.muscoli_secondari) {
        const group = normalizeMuscleGroup(m);
        setCounts[group] = (setCounts[group] ?? 0) + ex.serie * secCredit;
      }
    }
  }

  const freq = sessioniPerSettimana ?? 4;

  return MUSCLE_GROUPS.map(group => {
    const sets = Math.round((setCounts[group] ?? 0) * 10) / 10;
    const target = getMuscleTarget(group, livello, freq);
    let status: CoverageStatus = "optimal";
    if (sets < target.min) status = "deficit";
    else if (sets > target.max) status = "excess";
    return { muscolo: group, setsPerWeek: sets, target, status };
  });
}

// ── Volume Analysis ──

/** Calcola volume totale set/settimana vs target per livello */
export function computeVolumeAnalysis(
  sessions: Array<{ esercizi: Array<{ id_esercizio: number; serie: number }> }>,
  exerciseMap: Map<number, Exercise>,
  livello: FitnessLevel,
): VolumeAnalysis {
  let totalSets = 0;
  for (const session of sessions) {
    for (const ex of session.esercizi) {
      const exercise = exerciseMap.get(ex.id_esercizio);
      if (!exercise) continue;
      if (getSectionForCategory(exercise.categoria) !== "principale") continue;
      totalSets += ex.serie;
    }
  }

  const target = TOTAL_VOLUME_TARGETS[livello];
  let status: CoverageStatus = "optimal";
  if (totalSets < target.min) status = "deficit";
  else if (totalSets > target.max) status = "excess";

  return { totalSetsPerWeek: totalSets, targetRange: target, status };
}

// ── Biomechanical Variety ──

/** Analizza distribuzione piani/catene/contrazioni */
export function analyzeBiomechanics(
  sessions: Array<{ esercizi: Array<{ id_esercizio: number }> }>,
  exerciseMap: Map<number, Exercise>,
): BiomechanicalVariety {
  const planes: Record<string, number> = {};
  const chains: Record<string, number> = {};
  const contractions: Record<string, number> = {};

  for (const session of sessions) {
    for (const ex of session.esercizi) {
      const exercise = exerciseMap.get(ex.id_esercizio);
      if (!exercise) continue;
      if (getSectionForCategory(exercise.categoria) !== "principale") continue;
      if (exercise.piano_movimento) planes[exercise.piano_movimento] = (planes[exercise.piano_movimento] ?? 0) + 1;
      if (exercise.catena_cinetica) chains[exercise.catena_cinetica] = (chains[exercise.catena_cinetica] ?? 0) + 1;
      if (exercise.tipo_contrazione) contractions[exercise.tipo_contrazione] = (contractions[exercise.tipo_contrazione] ?? 0) + 1;
    }
  }

  return { planes, chains, contractions };
}

// ── Recovery Analysis ──

/**
 * Analizza conflitti di recupero tra sessioni consecutive.
 * Assume sessioni equamente distribuite nella settimana.
 */
export function analyzeRecovery(
  sessions: Array<{ nome_sessione: string; esercizi: Array<{ id_esercizio: number }> }>,
  sessioniPerSettimana: number,
  exerciseMap: Map<number, Exercise>,
): RecoveryConflict[] {
  if (sessions.length < 2 || sessioniPerSettimana <= 0) return [];

  const oreTraSessioni = (7 * 24) / sessioniPerSettimana;
  const conflicts: RecoveryConflict[] = [];

  for (let i = 0; i < sessions.length; i++) {
    const nextIdx = (i + 1) % sessions.length;
    const sessionA = sessions[i];
    const sessionB = sessions[nextIdx];

    const muscoliA = new Map<string, number>();
    for (const ex of sessionA.esercizi) {
      const exercise = exerciseMap.get(ex.id_esercizio);
      if (!exercise) continue;
      for (const m of exercise.muscoli_primari) {
        const group = normalizeMuscleGroup(m);
        muscoliA.set(group, Math.max(muscoliA.get(group) ?? 0, exercise.ore_recupero));
      }
    }

    const overlapping: string[] = [];
    let maxRecovery = 0;
    for (const ex of sessionB.esercizi) {
      const exercise = exerciseMap.get(ex.id_esercizio);
      if (!exercise) continue;
      for (const m of exercise.muscoli_primari) {
        const group = normalizeMuscleGroup(m);
        const recoveryNeeded = muscoliA.get(group);
        if (recoveryNeeded !== undefined && recoveryNeeded > oreTraSessioni) {
          if (!overlapping.includes(group)) overlapping.push(group);
          maxRecovery = Math.max(maxRecovery, recoveryNeeded);
        }
      }
    }

    if (overlapping.length > 0) {
      conflicts.push({
        sessionA: sessionA.nome_sessione,
        sessionB: sessionB.nome_sessione,
        muscoli: overlapping,
        oreNecessarie: maxRecovery,
        oreDisponibili: Math.round(oreTraSessioni),
        severity: maxRecovery > oreTraSessioni * 1.5 ? "alert" : "warning",
      });
    }
  }

  return conflicts;
}

// ── Safety Analysis ──

/** Calcola score sicurezza: % esercizi senza controindicazioni */
function computeSafetyScore(
  sessions: Array<{ esercizi: Array<{ id_esercizio: number }> }>,
  safetyMap: Record<number, ExerciseSafetyEntry> | null,
): number {
  if (!safetyMap) return 100;

  let total = 0;
  let safe = 0;
  for (const session of sessions) {
    for (const ex of session.esercizi) {
      total++;
      const entry = safetyMap[ex.id_esercizio];
      if (!entry) safe++;
      else if (entry.severity === "avoid") { /* 0 */ }
      else if (entry.severity === "modify") safe += 0.7;
      else safe += 0.5;
    }
  }

  return total > 0 ? Math.round((safe / total) * 100) : 100;
}

/** Conta esercizi per severita' safety — display actionable */
export function computeSafetyBreakdown(
  sessions: Array<{ esercizi: Array<{ id_esercizio: number }> }>,
  safetyMap: Record<number, ExerciseSafetyEntry> | null,
): SafetyBreakdown {
  if (!safetyMap) return { avoid: 0, modify: 0, caution: 0, hasConditions: false };

  const hasConditions = Object.keys(safetyMap).length > 0
    || Object.values(safetyMap).length > 0;
  let avoid = 0, modify = 0, caution = 0;
  const counted = new Set<number>();

  for (const session of sessions) {
    for (const ex of session.esercizi) {
      if (counted.has(ex.id_esercizio)) continue;
      counted.add(ex.id_esercizio);
      const entry = safetyMap[ex.id_esercizio];
      if (!entry) continue;
      if (entry.severity === "avoid") avoid++;
      else if (entry.severity === "modify") modify++;
      else caution++;
    }
  }

  return { avoid, modify, caution, hasConditions: hasConditions || avoid + modify + caution > 0 };
}

// ── Smart Analysis Orchestrator ──

/** Computa l'analisi SMART completa di una scheda. */
export function computeSmartAnalysis(
  sessions: Array<{
    nome_sessione: string;
    esercizi: Array<{ id_esercizio: number; serie: number }>;
  }>,
  exerciseMap: Map<number, Exercise>,
  livello: FitnessLevel,
  sessioniPerSettimana: number,
  safetyMap: Record<number, ExerciseSafetyEntry> | null,
): SmartAnalysis {
  return {
    coverage: computeMuscleCoverage(sessions, exerciseMap, livello, sessioniPerSettimana),
    volume: computeVolumeAnalysis(sessions, exerciseMap, livello),
    biomechanics: analyzeBiomechanics(sessions, exerciseMap),
    recoveryConflicts: analyzeRecovery(sessions, sessioniPerSettimana, exerciseMap),
    safetyScore: computeSafetyScore(sessions, safetyMap),
  };
}
