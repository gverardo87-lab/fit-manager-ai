// src/lib/workout-analysis-engine.ts
/**
 * Motore di analisi volume e bilancio per il workout builder.
 *
 * Estrae FATTI NUMERICI per la visualizzazione (zero scoring/giudizi).
 * Complementare al quality engine che fa scoring 0-100 con issues.
 *
 * Pattern: funzioni pure, zero deps, zero latenza.
 */

import type { Exercise } from "@/types/api";
import type { SessionCardData } from "@/components/workouts/SessionCard";
import { getSectionForCategory } from "@/lib/workout-templates";
import {
  MUSCLE_LABELS,
  FORCE_TYPE_LABELS,
  LATERAL_PATTERN_LABELS,
  KINETIC_CHAIN_LABELS,
  MOVEMENT_PLANE_LABELS,
  CONTRACTION_TYPE_LABELS,
} from "@/components/exercises/exercise-constants";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

export interface MuscleVolumeEntry {
  muscle: string;
  label: string;
  primarySets: number;
  secondarySets: number;
  totalSets: number; // primarySets + secondarySets * 0.5
}

export interface BalanceData {
  push: number;
  pull: number;
  upper: number;
  lower: number;
}

export interface DistributionEntry {
  value: string;
  label: string;
  count: number; // numero esercizi
  sets: number;  // serie totali
}

export interface SessionSummary {
  name: string;
  totalSets: number;
  totalExercises: number;
  dominantMuscles: string[]; // top 2 gruppi
  dominantPattern: string | null;
}

export interface SessionMuscleEntry {
  muscle: string;
  label: string;
  sets: number; // serie primarie
}

export interface SessionDetailedAnalysis {
  name: string;
  sessionIndex: number;
  totalPrincipalSets: number;
  totalPrincipalExercises: number;
  /** Tutti i muscoli lavorati (primari), ordinamento anatomico */
  muscleVolume: SessionMuscleEntry[];
  /** Top 3 muscoli per serie */
  dominantMuscles: SessionMuscleEntry[];
  pushSets: number;
  pullSets: number;
  upperSets: number;
  lowerSets: number;
  patternsUsed: string[];
}

export interface WorkoutAnalysisData {
  muscleVolume: MuscleVolumeEntry[];
  balance: BalanceData;
  forceTypes: DistributionEntry[];
  lateralPatterns: DistributionEntry[];
  kineticChains: DistributionEntry[];
  movementPlanes: DistributionEntry[];
  contractionTypes: DistributionEntry[];
  patternsUsed: Set<string>;
  sessionSummaries: SessionSummary[];
  totalPrincipalSets: number;
  totalPrincipalExercises: number;
  musclesCovered: number;
}

// ════════════════════════════════════════════════════════════
// CONSTANTS
// ════════════════════════════════════════════════════════════

/** Ordinamento anatomico: upper push → upper pull → lower → core */
const MUSCLE_SORT_ORDER: string[] = [
  "chest", "shoulders", "triceps",       // upper push
  "back", "lats", "traps", "biceps", "forearms", // upper pull
  "quadriceps", "hamstrings", "glutes", "calves", "adductors", // lower
  "core",                                 // core
];

const PUSH_PATTERNS = new Set(["push_h", "push_v"]);
const PULL_PATTERNS = new Set(["pull_h", "pull_v"]);
const UPPER_PATTERNS = new Set(["push_h", "push_v", "pull_h", "pull_v"]);
const LOWER_PATTERNS = new Set(["squat", "hinge"]);

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

/** Raccoglie esercizi sezione "principale" con dati enriched */
function getPrincipalExercises(
  sessions: SessionCardData[],
  exMap: Map<number, Exercise>,
): { ex: Exercise; serie: number; sessionIdx: number }[] {
  const result: { ex: Exercise; serie: number; sessionIdx: number }[] = [];
  for (let si = 0; si < sessions.length; si++) {
    for (const we of sessions[si].esercizi) {
      const ex = exMap.get(we.id_esercizio);
      if (!ex) continue;
      if (getSectionForCategory(ex.categoria) === "principale") {
        result.push({ ex, serie: we.serie, sessionIdx: si });
      }
    }
  }
  return result;
}

/** Costruisce distribuzione per un campo nullable */
function buildDistribution(
  items: { ex: Exercise; serie: number }[],
  fieldFn: (ex: Exercise) => string | null,
  labelMap: Record<string, string>,
): DistributionEntry[] {
  const countMap = new Map<string, { count: number; sets: number }>();
  for (const { ex, serie } of items) {
    const val = fieldFn(ex);
    if (!val) continue;
    const entry = countMap.get(val) ?? { count: 0, sets: 0 };
    entry.count++;
    entry.sets += serie;
    countMap.set(val, entry);
  }
  return Array.from(countMap.entries())
    .map(([value, { count, sets }]) => ({
      value,
      label: labelMap[value] ?? value,
      count,
      sets,
    }))
    .sort((a, b) => b.sets - a.sets);
}

// ════════════════════════════════════════════════════════════
// FUNZIONE PRINCIPALE
// ════════════════════════════════════════════════════════════

export function analyzeWorkoutData(
  sessions: SessionCardData[],
  exerciseMap: Map<number, Exercise>,
): WorkoutAnalysisData {
  const principal = getPrincipalExercises(sessions, exerciseMap);

  // ── Volume muscolare ──
  const primaryMap = new Map<string, number>();
  const secondaryMap = new Map<string, number>();

  for (const { ex, serie } of principal) {
    for (const m of ex.muscoli_primari) {
      primaryMap.set(m, (primaryMap.get(m) ?? 0) + serie);
    }
    for (const m of ex.muscoli_secondari) {
      secondaryMap.set(m, (secondaryMap.get(m) ?? 0) + serie);
    }
  }

  // Unione di tutti i muscoli presenti
  const allMuscles = new Set([...primaryMap.keys(), ...secondaryMap.keys()]);

  const muscleVolume: MuscleVolumeEntry[] = MUSCLE_SORT_ORDER
    .filter((m) => allMuscles.has(m))
    .map((m) => {
      const prim = primaryMap.get(m) ?? 0;
      const sec = secondaryMap.get(m) ?? 0;
      return {
        muscle: m,
        label: MUSCLE_LABELS[m] ?? m,
        primarySets: prim,
        secondarySets: sec,
        totalSets: prim + sec * 0.5,
      };
    });

  // Aggiungi eventuali muscoli non in MUSCLE_SORT_ORDER (safety net)
  for (const m of allMuscles) {
    if (!MUSCLE_SORT_ORDER.includes(m)) {
      const prim = primaryMap.get(m) ?? 0;
      const sec = secondaryMap.get(m) ?? 0;
      muscleVolume.push({
        muscle: m,
        label: MUSCLE_LABELS[m] ?? m,
        primarySets: prim,
        secondarySets: sec,
        totalSets: prim + sec * 0.5,
      });
    }
  }

  // ── Bilancio push/pull e upper/lower ──
  const balance: BalanceData = { push: 0, pull: 0, upper: 0, lower: 0 };
  for (const { ex, serie } of principal) {
    const pat = ex.pattern_movimento;
    if (PUSH_PATTERNS.has(pat)) balance.push += serie;
    if (PULL_PATTERNS.has(pat)) balance.pull += serie;
    if (UPPER_PATTERNS.has(pat)) balance.upper += serie;
    if (LOWER_PATTERNS.has(pat)) balance.lower += serie;
  }

  // ── Pattern movimento usati ──
  const patternsUsed = new Set(principal.map((p) => p.ex.pattern_movimento));

  // ── Distribuzioni biomeccaniche ──
  const forceTypes = buildDistribution(principal, (ex) => ex.force_type, FORCE_TYPE_LABELS);
  const lateralPatterns = buildDistribution(principal, (ex) => ex.lateral_pattern, LATERAL_PATTERN_LABELS);
  const kineticChains = buildDistribution(principal, (ex) => ex.catena_cinetica, KINETIC_CHAIN_LABELS);
  const movementPlanes = buildDistribution(principal, (ex) => ex.piano_movimento, MOVEMENT_PLANE_LABELS);
  const contractionTypes = buildDistribution(principal, (ex) => ex.tipo_contrazione, CONTRACTION_TYPE_LABELS);

  // ── Session summaries ──
  const sessionSummaries: SessionSummary[] = sessions.map((session, si) => {
    const sessionExercises = principal.filter((p) => p.sessionIdx === si);
    const totalSets = sessionExercises.reduce((sum, p) => sum + p.serie, 0);

    // Top 2 muscoli per serie (usando solo primari per chiarezza)
    const muscleCount = new Map<string, number>();
    for (const { ex, serie } of sessionExercises) {
      for (const m of ex.muscoli_primari) {
        muscleCount.set(m, (muscleCount.get(m) ?? 0) + serie);
      }
    }
    const dominantMuscles = Array.from(muscleCount.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 2)
      .map(([m]) => MUSCLE_LABELS[m] ?? m);

    // Pattern dominante
    const patternCount = new Map<string, number>();
    for (const { ex } of sessionExercises) {
      const p = ex.pattern_movimento;
      patternCount.set(p, (patternCount.get(p) ?? 0) + 1);
    }
    const dominantPattern = patternCount.size > 0
      ? Array.from(patternCount.entries()).sort((a, b) => b[1] - a[1])[0][0]
      : null;

    return {
      name: session.nome_sessione || `Sessione ${si + 1}`,
      totalSets,
      totalExercises: sessionExercises.length,
      dominantMuscles,
      dominantPattern,
    };
  });

  return {
    muscleVolume,
    balance,
    forceTypes,
    lateralPatterns,
    kineticChains,
    movementPlanes,
    contractionTypes,
    patternsUsed,
    sessionSummaries,
    totalPrincipalSets: principal.reduce((sum, p) => sum + p.serie, 0),
    totalPrincipalExercises: new Set(principal.map((p) => p.ex.id)).size,
    musclesCovered: allMuscles.size,
  };
}

// ════════════════════════════════════════════════════════════
// ANALISI PER-SESSIONE DETTAGLIATA
// ════════════════════════════════════════════════════════════

export function analyzeSessionsDetailed(
  sessions: SessionCardData[],
  exerciseMap: Map<number, Exercise>,
): SessionDetailedAnalysis[] {
  return sessions.map((session, si) => {
    const muscleMap = new Map<string, number>();
    let pushSets = 0;
    let pullSets = 0;
    let upperSets = 0;
    let lowerSets = 0;
    let totalSets = 0;
    let exerciseCount = 0;
    const patterns = new Set<string>();

    for (const we of session.esercizi) {
      const ex = exerciseMap.get(we.id_esercizio);
      if (!ex) continue;
      if (getSectionForCategory(ex.categoria) !== "principale") continue;

      exerciseCount++;
      totalSets += we.serie;
      patterns.add(ex.pattern_movimento);

      for (const m of ex.muscoli_primari) {
        muscleMap.set(m, (muscleMap.get(m) ?? 0) + we.serie);
      }

      const pat = ex.pattern_movimento;
      if (PUSH_PATTERNS.has(pat)) pushSets += we.serie;
      if (PULL_PATTERNS.has(pat)) pullSets += we.serie;
      if (UPPER_PATTERNS.has(pat)) upperSets += we.serie;
      if (LOWER_PATTERNS.has(pat)) lowerSets += we.serie;
    }

    // Volume muscolare completo (ordinamento anatomico)
    const muscleVolume: SessionMuscleEntry[] = MUSCLE_SORT_ORDER
      .filter((m) => muscleMap.has(m))
      .map((m) => ({ muscle: m, label: MUSCLE_LABELS[m] ?? m, sets: muscleMap.get(m)! }));
    // Safety net: muscoli non in MUSCLE_SORT_ORDER
    for (const [m, sets] of muscleMap) {
      if (!MUSCLE_SORT_ORDER.includes(m)) {
        muscleVolume.push({ muscle: m, label: MUSCLE_LABELS[m] ?? m, sets });
      }
    }

    const dominantMuscles = [...muscleVolume]
      .sort((a, b) => b.sets - a.sets)
      .slice(0, 3);

    return {
      name: session.nome_sessione || `Sessione ${si + 1}`,
      sessionIndex: si,
      totalPrincipalSets: totalSets,
      totalPrincipalExercises: exerciseCount,
      muscleVolume,
      dominantMuscles,
      pushSets,
      pullSets,
      upperSets,
      lowerSets,
      patternsUsed: Array.from(patterns),
    };
  });
}
