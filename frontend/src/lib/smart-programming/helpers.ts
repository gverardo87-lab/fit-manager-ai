// src/lib/smart-programming/helpers.ts
/**
 * Utility fondamentali: normalizzazione muscoli/difficolta', mapping pattern→muscoli,
 * costruzione profilo client, assessment fitness level.
 */

import type {
  ExerciseSafetyEntry,
  ClientGoal,
  AnamnesiData,
} from "@/types/api";
import type { StrengthRatio } from "@/lib/derived-metrics";
import type { SymmetryPair } from "@/lib/clinical-analysis";
import { computeAge } from "@/lib/normative-ranges";
import type { ClientProfile, FitnessLevel } from "./types";

// ── Gruppi muscolari principali per analisi copertura ──

export const MUSCLE_GROUPS = [
  "petto", "dorsali", "spalle", "bicipiti", "tricipiti",
  "quadricipiti", "femorali", "glutei", "polpacci",
  "core", "trapezio", "adduttori", "avambracci",
] as const;

const MUSCLE_GROUP_ALIASES: Record<string, string> = {
  chest: "petto", pectorals: "petto",
  lats: "dorsali", back: "dorsali", latissimus: "dorsali",
  shoulders: "spalle", deltoids: "spalle", deltoidi: "spalle",
  biceps: "bicipiti",
  triceps: "tricipiti",
  quadriceps: "quadricipiti", quads: "quadricipiti",
  hamstrings: "femorali",
  glutes: "glutei", gluteus: "glutei",
  calves: "polpacci",
  abs: "core", abdominals: "core", addominali: "core",
  traps: "trapezio", trapezius: "trapezio",
  adductors: "adduttori",
  forearms: "avambracci",
};

export function normalizeMuscleGroup(name: string): string {
  const lower = name.toLowerCase();
  return MUSCLE_GROUP_ALIASES[lower] ?? lower;
}

// ── Difficolta' ──

const DIFFICULTY_ORDER = ["principiante", "intermedio", "avanzato"] as const;

/** Mappa difficolta' EN (DB) → IT (engine). Accetta entrambe le lingue. */
export function normalizeDifficulty(d: string): string {
  const map: Record<string, string> = {
    beginner: "principiante", intermediate: "intermedio", advanced: "avanzato",
  };
  return map[d.toLowerCase()] ?? d.toLowerCase();
}

export function difficultyDistance(a: string, b: string): number {
  const idxA = DIFFICULTY_ORDER.indexOf(normalizeDifficulty(a) as typeof DIFFICULTY_ORDER[number]);
  const idxB = DIFFICULTY_ORDER.indexOf(normalizeDifficulty(b) as typeof DIFFICULTY_ORDER[number]);
  if (idxA < 0 || idxB < 0) return 2;
  return Math.abs(idxA - idxB);
}

// ── Utility ──

/** Parsa rep range tipo "8-12" → media 10, "5" → 5, "30s" → 0 */
export function parseAvgReps(rip: string): number {
  const match = rip.match(/^(\d+)\s*-\s*(\d+)$/);
  if (match) return (parseInt(match[1]) + parseInt(match[2])) / 2;
  const single = rip.match(/^(\d+)$/);
  if (single) return parseInt(single[1]);
  return 0;
}

export function countInRecord(rec: Record<string, number>, key: string): number {
  return rec[key] ?? 0;
}

export function capitalizeFirst(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ── Pattern → Muscoli/Label ──

/**
 * Mappa pattern → muscoli con ruolo differenziato (primari vs secondari).
 *
 * NOTA: Core RIMOSSO dai secondari di squat/hinge — e' stabilizzatore,
 * il suo credito reale viene dai pattern "core"/"rotation"/"carry".
 * Previene inflazione hub muscles.
 */
export function patternToMuscleRoles(pattern: string): { primari: string[]; secondari: string[] } {
  const map: Record<string, { primari: string[]; secondari: string[] }> = {
    squat:         { primari: ["quadricipiti"],                  secondari: ["glutei", "femorali", "adduttori"] },
    hinge:         { primari: ["femorali", "glutei"],           secondari: ["dorsali"] },
    push_h:        { primari: ["petto"],                        secondari: ["tricipiti", "spalle"] },
    push_v:        { primari: ["spalle"],                       secondari: ["tricipiti"] },
    pull_h:        { primari: ["dorsali"],                      secondari: ["bicipiti", "trapezio"] },
    pull_v:        { primari: ["dorsali"],                      secondari: ["bicipiti"] },
    core:          { primari: ["core"],                         secondari: [] },
    rotation:      { primari: ["core"],                         secondari: ["spalle"] },
    carry:         { primari: ["core", "avambracci"],           secondari: ["trapezio"] },
    curl:          { primari: ["bicipiti"],                     secondari: ["avambracci"] },
    extension_tri: { primari: ["tricipiti"],                    secondari: [] },
    lateral_raise: { primari: ["spalle"],                       secondari: [] },
    face_pull:     { primari: ["spalle"],                       secondari: ["trapezio"] },
    calf_raise:    { primari: ["polpacci"],                     secondari: [] },
    leg_curl:      { primari: ["femorali"],                     secondari: [] },
    leg_extension: { primari: ["quadricipiti"],                 secondari: [] },
    hip_thrust:    { primari: ["glutei"],                       secondari: ["femorali"] },
    adductor:      { primari: ["adduttori"],                    secondari: [] },
    warmup:        { primari: [],                               secondari: [] },
    stretch:       { primari: [],                               secondari: [] },
    mobility:      { primari: [],                               secondari: [] },
  };
  return map[pattern] ?? { primari: [], secondari: [] };
}

export function patternToLabel(pattern: string): string {
  const map: Record<string, string> = {
    squat: "Squat / Accosciata",
    hinge: "Hinge / Stacco",
    push_h: "Push Orizzontale",
    push_v: "Push Verticale",
    pull_h: "Pull Orizzontale",
    pull_v: "Pull Verticale",
    core: "Core / Stabilizzazione",
    rotation: "Rotazione",
    carry: "Carry / Trasporto",
  };
  return map[pattern] ?? capitalizeFirst(pattern);
}

// ── Livello attivita' → FitnessLevel ──

function activityToLevel(livello: string | null): FitnessLevel | null {
  if (!livello) return null;
  const l = livello.toLowerCase();
  if (l === "sedentario" || l === "leggero") return "beginner";
  if (l === "moderato") return "intermedio";
  if (l === "intenso") return "avanzato";
  return null;
}

// ── Fitness Level Assessor ──

/**
 * Determina il livello fitness del client da dati disponibili.
 * Combina livello attivita' (anamnesi) + strength ratios (NSCA).
 */
export function assessFitnessLevel(profile: ClientProfile | null): FitnessLevel {
  if (!profile) return "beginner";

  if (profile.strengthRatios.length > 0) {
    const LEVEL_MAP: Record<string, FitnessLevel> = {
      elite: "avanzato", avanzato: "avanzato", advanced: "avanzato",
      intermedio: "intermedio", intermediate: "intermedio",
      principiante: "beginner", beginner: "beginner",
    };
    const mapped = profile.strengthRatios.map(sr => LEVEL_MAP[sr.level.toLowerCase()] ?? "beginner");
    if (mapped.some(l => l === "avanzato")) return "avanzato";
    if (mapped.some(l => l === "intermedio")) return "intermedio";
    return "beginner";
  }

  const fromActivity = activityToLevel(profile.livelloAttivita);
  if (fromActivity) return fromActivity;

  return "beginner";
}

// ── Profile Builder ──

/**
 * Costruisce un ClientProfile da dati client eterogenei.
 * Usato dall'hook useSmartProgramming.
 */
export function buildClientProfile(
  client: { sesso: string | null; data_nascita: string | null; anamnesi: AnamnesiData | null } | null,
  safetyMap: Record<number, ExerciseSafetyEntry> | null,
  strengthRatios: StrengthRatio[],
  goals: ClientGoal[],
  symmetryDeficits: SymmetryPair[],
): ClientProfile | null {
  if (!client) return null;

  const eta = client.data_nascita ? computeAge(client.data_nascita) : null;
  const livelloAttivita = client.anamnesi?.livello_attivita ?? null;

  const profile: ClientProfile = {
    sesso: client.sesso,
    eta,
    livelloAttivita,
    safetyMap,
    measurements: null,
    strengthRatios,
    goals,
    symmetryDeficits,
    strengthLevel: null,
  };

  profile.strengthLevel = assessFitnessLevel(profile);
  return profile;
}
