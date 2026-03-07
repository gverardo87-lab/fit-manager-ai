// src/lib/smart-programming/plan-generator.ts
/**
 * Generazione piani SMART (blueprint-driven) + fill con scoring 14D.
 *
 * generateSmartPlan(): genera struttura slot tipizzati da blueprint
 * fillSmartPlan(): assegna esercizi ottimali con 2-phase optimization
 */

import type { Exercise } from "@/types/api";
import { SECTION_CATEGORIES } from "@/lib/workout-templates";
import type {
  FitnessLevel,
  SmartSlot,
  SmartSession,
  SmartPlan,
  SplitBlueprint,
  ClientProfile,
  ExerciseScore,
} from "./types";
import {
  MUSCLE_GROUPS,
  normalizeMuscleGroup,
  patternToMuscleRoles,
  capitalizeFirst,
} from "./helpers";
import {
  SESSION_BLUEPRINTS,
  getSlotVolume,
  getAccessoryVolume,
  getMuscleTarget,
  blueprintSlotLabel,
} from "./blueprints";
import { scoreExercisesForSlot } from "./scorers";

// ── Split Determination ──

/** Determina la struttura blueprint ottimale da sessioni/settimana + livello */
export function determineSplit(
  sessioniPerSettimana: number,
  livello: FitnessLevel,
): SplitBlueprint {
  const clamped = Math.max(2, Math.min(6, sessioniPerSettimana));
  const levelBlueprints = SESSION_BLUEPRINTS[clamped];
  if (!levelBlueprints) return SESSION_BLUEPRINTS[3][livello];
  return levelBlueprints[livello] ?? levelBlueprints.beginner;
}

/** Deduce il nome split dal blueprint */
function detectSplitName(blueprint: SplitBlueprint): string {
  const names = blueprint.sessioni.map(s => s.nome.toLowerCase());
  if (names.some(n => n.includes("push")) && names.some(n => n.includes("pull"))) return "PPL";
  if (names.some(n => n.includes("upper")) && names.some(n => n.includes("lower"))) return "Upper/Lower";
  return "Full Body";
}

// ── Plan Generator ──

/**
 * Genera una struttura SmartPlan completa con slot tipizzati.
 * NON assegna esercizi — genera solo la struttura. Usa fillSmartPlan() per il fill.
 */
export function generateSmartPlan(
  sessioniPerSettimana: number,
  livello: FitnessLevel,
  obiettivo: string,
  durataSettimane: number = 4,
): SmartPlan {
  const blueprint = determineSplit(sessioniPerSettimana, livello);

  const sessioni: SmartSession[] = blueprint.sessioni.map(sb => {
    const slots: SmartSlot[] = [];

    // Avviamento: 2-3 slot
    const warmupCount = livello === "beginner" ? 2 : 3;
    for (let i = 0; i < warmupCount; i++) {
      slots.push({
        sezione: "avviamento",
        pattern_hint: i < 2 ? "warmup" : "mobility",
        muscoli_target: [],
        label: i === 0 ? "Riscaldamento Generale" : (i === 1 ? "Attivazione Dinamica" : "Mobilita Articolare"),
        serie: i === 0 ? 1 : 2,
        ripetizioni: i === 0 ? "5 min" : "10",
        tempo_riposo_sec: 0,
      });
    }

    // Principale: slot dal blueprint con volume per slot type × obiettivo
    for (const bs of sb.slots) {
      const vol = getSlotVolume(bs.type, obiettivo);
      const roles = patternToMuscleRoles(bs.pattern_hint);
      const muscoli_target = (bs.type === "isolation_target" || bs.type === "isolation_accessory")
        ? [bs.targetMuscle]
        : roles.primari.length > 0 ? roles.primari : [bs.targetMuscle];

      slots.push({
        sezione: "principale",
        pattern_hint: bs.pattern_hint,
        muscoli_target,
        label: blueprintSlotLabel(bs.type, bs.targetMuscle, bs.pattern_hint),
        serie: vol.serie,
        ripetizioni: vol.ripetizioni,
        tempo_riposo_sec: vol.riposo,
        slotType: bs.type,
      });
    }

    // Stretching: 2-3 slot mirati ai muscoli lavorati
    const stretchCount = livello === "avanzato" ? 3 : 2;
    const workedMuscles = new Set(sb.slots.map(s => s.targetMuscle));
    const muscleArr = [...workedMuscles];
    for (let i = 0; i < stretchCount; i++) {
      const target = muscleArr[i % muscleArr.length] ?? "generale";
      slots.push({
        sezione: "stretching",
        pattern_hint: "stretch",
        muscoli_target: [target],
        label: `Stretching ${capitalizeFirst(target)}`,
        serie: 1,
        ripetizioni: "30s",
        tempo_riposo_sec: 0,
      });
    }

    const durataMinuti = warmupCount * 5 + sb.slots.length * 7 + stretchCount * 2;
    return { nome_sessione: sb.nome, focus_muscolare: sb.focus, durata_minuti: durataMinuti, slots };
  });

  // Safety-net: verifica copertura dal blueprint, aggiungi slot correttivi
  const blueprintSets = computeBlueprintCoverage(blueprint, obiettivo);
  const deficits = MUSCLE_GROUPS.filter(m => {
    const mt = getMuscleTarget(m, livello, sessioniPerSettimana);
    return (blueprintSets.get(m) ?? 0) < mt.min * 0.4;
  });

  if (deficits.length > 0) {
    deficits.sort((a, b) => (blueprintSets.get(a) ?? 0) - (blueprintSets.get(b) ?? 0));
    for (const muscle of deficits.slice(0, sessioni.length)) {
      const bestIdx = sessioni.reduce((bi, s, i) =>
        bi === -1 || s.slots.length < sessioni[bi].slots.length ? i : bi, -1);
      if (bestIdx === -1) continue;
      const vol = getAccessoryVolume(muscle);
      sessioni[bestIdx].slots.push({
        sezione: "principale",
        pattern_hint: "accessory",
        muscoli_target: [muscle],
        label: `Correzione ${capitalizeFirst(muscle)}`,
        serie: vol.serie,
        ripetizioni: vol.ripetizioni,
        tempo_riposo_sec: 60,
        slotType: "isolation_accessory",
      });
      sessioni[bestIdx].durata_minuti += 5;
    }
  }

  const splitName = detectSplitName(blueprint);
  return {
    nome: `Smart ${splitName} — ${capitalizeFirst(obiettivo)}`,
    livello,
    obiettivo,
    sessioni_per_settimana: sessioniPerSettimana,
    durata_settimane: durataSettimane,
    sessioni,
  };
}

/** Stima copertura muscolare dal blueprint (pre-fill, per validazione). */
function computeBlueprintCoverage(blueprint: SplitBlueprint, obiettivo: string): Map<string, number> {
  const sets = new Map<string, number>();
  for (const session of blueprint.sessioni) {
    for (const slot of session.slots) {
      const vol = getSlotVolume(slot.type, obiettivo);
      const serie = vol.serie;
      if (slot.type === "isolation_target" || slot.type === "isolation_accessory") {
        const group = normalizeMuscleGroup(slot.targetMuscle.toLowerCase());
        sets.set(group, (sets.get(group) ?? 0) + serie);
      } else {
        const roles = patternToMuscleRoles(slot.pattern_hint);
        for (const m of roles.primari) sets.set(m, (sets.get(m) ?? 0) + serie * 1.0);
        const secLen = roles.secondari.length;
        const secCredit = secLen > 0 ? Math.min(0.35, 1.0 / secLen) : 0;
        for (const m of roles.secondari) sets.set(m, (sets.get(m) ?? 0) + serie * secCredit);
      }
    }
  }
  return sets;
}

// ── Smart Plan Filler (2-phase) ──

/**
 * Riempie gli slot di un SmartPlan con esercizi ottimali.
 * Fase 1: Greedy fill con scoring 14D.
 * Fase 2: Coverage-aware swap optimization.
 */
export function fillSmartPlan(
  plan: SmartPlan,
  exercises: Exercise[],
  profile: ClientProfile | null,
): Map<number, Map<number, ExerciseScore[]>> {
  const result = new Map<number, Map<number, ExerciseScore[]>>();
  const allAssigned: Exercise[] = [];
  const livello = plan.livello as FitnessLevel;
  const assigned: (Exercise | null)[][] = [];

  // Fase 1: Greedy fill
  for (let si = 0; si < plan.sessioni.length; si++) {
    const session = plan.sessioni[si];
    const sessionMap = new Map<number, ExerciseScore[]>();
    const sessionAssigned: Exercise[] = [];
    assigned[si] = [];

    for (let sli = 0; sli < session.slots.length; sli++) {
      const slot = session.slots[sli];
      const sectionCats = SECTION_CATEGORIES[slot.sezione];
      let candidates = exercises.filter(e => sectionCats.includes(e.categoria));

      // Pre-filter per slot type
      if (slot.slotType === "isolation_target" || slot.slotType === "isolation_accessory") {
        const preferred = candidates.filter(e => e.categoria === "isolation" || e.categoria === "bodyweight");
        if (preferred.length >= 3) candidates = preferred;
      } else if (slot.slotType === "compound_primary" || slot.slotType === "compound_secondary") {
        const preferred = candidates.filter(e => e.categoria === "compound" || e.categoria === "bodyweight");
        if (preferred.length >= 3) candidates = preferred;

        // Pattern gate: impedisce gambe in upper body, pull in push day
        const hint = slot.pattern_hint;
        if (hint && !["warmup", "stretch", "mobility", "accessory"].includes(hint)) {
          const exact = candidates.filter(e => e.pattern_movimento === hint);
          if (exact.length >= 2) {
            candidates = exact;
          } else {
            const family = hint.split("_")[0];
            const familyMatch = candidates.filter(e => e.pattern_movimento.split("_")[0] === family);
            if (familyMatch.length >= 2) candidates = familyMatch;
          }
        }
      }

      const scores = scoreExercisesForSlot(
        candidates, slot, profile, livello, plan.obiettivo,
        sessionAssigned, allAssigned, plan.sessioni_per_settimana,
      );

      sessionMap.set(sli, scores.slice(0, 10));

      if (scores.length > 0) {
        const bestEx = exercises.find(e => e.id === scores[0].exerciseId);
        if (bestEx) {
          sessionAssigned.push(bestEx);
          allAssigned.push(bestEx);
          assigned[si][sli] = bestEx;
        } else {
          assigned[si][sli] = null;
        }
      } else {
        assigned[si][sli] = null;
      }
    }
    result.set(si, sessionMap);
  }

  // Fase 2: Coverage-aware swap optimization
  const MAX_SWAP_PASSES = 3;
  const TOP_ALTERNATIVES = 5;
  const MIN_SCORE_RATIO = 0.60;

  for (let pass = 0; pass < MAX_SWAP_PASSES; pass++) {
    const realCoverage = computeRealCoverage(assigned, plan);
    const deficits = MUSCLE_GROUPS.filter(m => {
      const mt = getMuscleTarget(m, livello, plan.sessioni_per_settimana);
      return (realCoverage.get(m) ?? 0) < mt.min;
    });

    if (deficits.length <= Math.ceil(MUSCLE_GROUPS.length * 0.2)) break;
    deficits.sort((a, b) => (realCoverage.get(a) ?? 0) - (realCoverage.get(b) ?? 0));

    let swapped = false;
    for (const deficitMuscle of deficits) {
      if (swapped) break;
      for (let si = 0; si < plan.sessioni.length && !swapped; si++) {
        const session = plan.sessioni[si];
        for (let sli = 0; sli < session.slots.length && !swapped; sli++) {
          const slot = session.slots[sli];
          if (slot.sezione !== "principale") continue;
          const currentEx = assigned[si][sli];
          if (!currentEx) continue;
          if (exerciseCoversGroup(currentEx, deficitMuscle)) continue;

          const slotScores = result.get(si)?.get(sli);
          if (!slotScores || slotScores.length < 2) continue;
          const currentScore = slotScores[0].totalScore;

          for (let ai = 1; ai < Math.min(slotScores.length, TOP_ALTERNATIVES + 1); ai++) {
            const altScore = slotScores[ai];
            if (altScore.totalScore < currentScore * MIN_SCORE_RATIO) continue;
            const altEx = exercises.find(e => e.id === altScore.exerciseId);
            if (!altEx) continue;
            if (!exerciseCoversGroup(altEx, deficitMuscle)) continue;
            if (assigned[si].some((e, idx) => idx !== sli && e?.id === altEx.id)) continue;

            const oldEx = assigned[si][sli]!;
            assigned[si][sli] = altEx;
            const oldIdx = allAssigned.findIndex(e => e.id === oldEx.id);
            if (oldIdx >= 0) allAssigned[oldIdx] = altEx;
            const removed = slotScores.splice(ai, 1);
            slotScores.splice(0, 0, ...removed);
            swapped = true;
          }
        }
      }
    }
    if (!swapped) break;
  }

  return result;
}

/** Copertura muscolare reale dagli esercizi assegnati. */
function computeRealCoverage(assigned: (Exercise | null)[][], plan: SmartPlan): Map<string, number> {
  const sets = new Map<string, number>();
  for (let si = 0; si < assigned.length; si++) {
    for (let sli = 0; sli < assigned[si].length; sli++) {
      const ex = assigned[si][sli];
      if (!ex) continue;
      const slot = plan.sessioni[si]?.slots[sli];
      if (!slot || slot.sezione !== "principale") continue;
      const serie = slot.serie;

      for (const m of ex.muscoli_primari) {
        const group = normalizeMuscleGroup(m.toLowerCase());
        sets.set(group, (sets.get(group) ?? 0) + serie * 1.0);
      }
      const secLen = ex.muscoli_secondari.length;
      const secCredit = secLen > 0 ? Math.min(0.35, 1.0 / secLen) : 0;
      for (const m of ex.muscoli_secondari) {
        const group = normalizeMuscleGroup(m.toLowerCase());
        sets.set(group, (sets.get(group) ?? 0) + serie * secCredit);
      }
    }
  }
  return sets;
}

/** Verifica se un esercizio copre un gruppo muscolare */
function exerciseCoversGroup(ex: Exercise, group: string): boolean {
  const normalized = normalizeMuscleGroup(group.toLowerCase());
  for (const m of ex.muscoli_primari) {
    if (normalizeMuscleGroup(m.toLowerCase()) === normalized) return true;
  }
  for (const m of ex.muscoli_secondari) {
    if (normalizeMuscleGroup(m.toLowerCase()) === normalized) return true;
  }
  return false;
}
