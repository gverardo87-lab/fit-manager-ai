// src/lib/smart-programming/blueprints.ts
/**
 * Session blueprints + volume data — configurazione pura.
 *
 * Ogni blueprint definisce la struttura COMPLETA di una settimana di allenamento:
 * - Slot tipizzati (compound_primary → isolation_accessory) con piramide di volume
 * - Sessioni progettate come SISTEMA complementare (A+B si bilanciano)
 * - Derivati dai template gold standard + principi NSCA/ACSM
 *
 * File di puri dati/configurazione (max 400 LOC).
 */

import type { FitnessLevel, SlotType, SessionBlueprint, SplitBlueprint } from "./types";
import { patternToLabel, capitalizeFirst } from "./helpers";

// ── Volume Targets (NSCA) ──

/** Set/muscolo/settimana target base per livello (Krieger 2010, Schoenfeld 2017). */
export const BASE_VOLUME_TARGETS: Record<FitnessLevel, { min: number; max: number }> = {
  beginner:   { min: 10, max: 12 },
  intermedio: { min: 14, max: 18 },
  avanzato:   { min: 18, max: 25 },
};

/** Moltiplicatore target per gruppo muscolare (NSCA, Schoenfeld 2017, Israetel MRV).
 * Tier 1.0 = full target, 0.7 = sinergici, 0.5 = secondari, 0.35 = accessori. */
export const MUSCLE_TARGET_TIER: Record<string, number> = {
  petto: 1.0, dorsali: 1.0, quadricipiti: 1.0, femorali: 1.0,
  glutei: 0.7, spalle: 0.7,
  bicipiti: 0.5, tricipiti: 0.5, trapezio: 0.5,
  core: 0.4, polpacci: 0.4, adduttori: 0.35, avambracci: 0.35,
};

/** Scala target volume in base alle sessioni/settimana. NSCA baseline = 4x. */
export function getScaledVolumeTargets(
  livello: FitnessLevel, sessioniPerSettimana: number,
): { min: number; max: number } {
  const base = BASE_VOLUME_TARGETS[livello];
  const SCALE: Record<number, number> = { 2: 0.50, 3: 0.65, 4: 1.0, 5: 1.1, 6: 1.2 };
  const factor = SCALE[Math.max(2, Math.min(6, sessioniPerSettimana))] ?? 1.0;
  return { min: Math.round(base.min * factor), max: Math.round(base.max * factor) };
}

/** Target per-muscolo: base × scala frequenza × tier muscolare. */
export function getMuscleTarget(
  muscolo: string, livello: FitnessLevel, sessioniPerSettimana: number,
): { min: number; max: number } {
  const base = getScaledVolumeTargets(livello, sessioniPerSettimana);
  const tier = MUSCLE_TARGET_TIER[muscolo] ?? 0.5;
  return {
    min: Math.round(base.min * tier * 10) / 10,
    max: Math.round(base.max * tier * 10) / 10,
  };
}

/** Set totali/settimana per livello */
export const TOTAL_VOLUME_TARGETS: Record<FitnessLevel, { min: number; max: number }> = {
  beginner:   { min: 30, max: 50 },
  intermedio: { min: 50, max: 80 },
  avanzato:   { min: 70, max: 120 },
};

// ── Slot Volume ──

type BSlot = [SlotType, string, string];
const CP: SlotType = "compound_primary";
const CS: SlotType = "compound_secondary";
const IT: SlotType = "isolation_target";
const IA: SlotType = "isolation_accessory";

function _bp(nome: string, focus: string, slots: BSlot[]): SessionBlueprint {
  return {
    nome, focus,
    slots: slots.map(([type, pattern_hint, targetMuscle]) => ({ type, pattern_hint, targetMuscle })),
  };
}

/** Volume per slot type × obiettivo. */
export const SLOT_VOLUME: Record<SlotType, Record<string, { serie: number; ripetizioni: string; riposo: number }>> = {
  compound_primary: {
    forza: { serie: 5, ripetizioni: "3-5", riposo: 180 },
    ipertrofia: { serie: 4, ripetizioni: "6-8", riposo: 120 },
    resistenza: { serie: 3, ripetizioni: "12-15", riposo: 60 },
    dimagrimento: { serie: 3, ripetizioni: "10-12", riposo: 75 },
    generale: { serie: 3, ripetizioni: "8-12", riposo: 90 },
  },
  compound_secondary: {
    forza: { serie: 4, ripetizioni: "5-6", riposo: 150 },
    ipertrofia: { serie: 3, ripetizioni: "8-10", riposo: 90 },
    resistenza: { serie: 3, ripetizioni: "12-15", riposo: 45 },
    dimagrimento: { serie: 3, ripetizioni: "10-12", riposo: 60 },
    generale: { serie: 3, ripetizioni: "8-12", riposo: 90 },
  },
  isolation_target: {
    forza: { serie: 3, ripetizioni: "8-10", riposo: 90 },
    ipertrofia: { serie: 3, ripetizioni: "10-12", riposo: 60 },
    resistenza: { serie: 3, ripetizioni: "15-20", riposo: 45 },
    dimagrimento: { serie: 3, ripetizioni: "12-15", riposo: 45 },
    generale: { serie: 3, ripetizioni: "10-12", riposo: 60 },
  },
  isolation_accessory: {
    forza: { serie: 2, ripetizioni: "10-12", riposo: 60 },
    ipertrofia: { serie: 3, ripetizioni: "12-15", riposo: 45 },
    resistenza: { serie: 2, ripetizioni: "15-20", riposo: 30 },
    dimagrimento: { serie: 2, ripetizioni: "12-15", riposo: 45 },
    generale: { serie: 2, ripetizioni: "10-15", riposo: 60 },
  },
};

export function getSlotVolume(type: SlotType, obiettivo: string): { serie: number; ripetizioni: string; riposo: number } {
  return SLOT_VOLUME[type][obiettivo] ?? SLOT_VOLUME[type].generale;
}

/** Label slot per UI — descrive il ruolo funzionale */
export function blueprintSlotLabel(type: SlotType, targetMuscle: string, pattern: string): string {
  switch (type) {
    case "compound_primary":   return patternToLabel(pattern);
    case "compound_secondary": return `${patternToLabel(pattern)} Complementare`;
    case "isolation_target":   return `Isolation ${capitalizeFirst(targetMuscle)}`;
    case "isolation_accessory":return `Accessorio ${capitalizeFirst(targetMuscle)}`;
  }
}

// ── Accessory Volume ──

/** Serie e rep raccomandate per accessori per gruppo muscolare (NSCA, Schoenfeld 2017). */
const ACCESSORY_VOLUME: Record<string, { serie: number; ripetizioni: string }> = {
  petto: { serie: 3, ripetizioni: "8-12" },
  dorsali: { serie: 3, ripetizioni: "8-12" },
  quadricipiti: { serie: 3, ripetizioni: "8-12" },
  femorali: { serie: 3, ripetizioni: "10-12" },
  glutei: { serie: 3, ripetizioni: "10-15" },
  spalle: { serie: 3, ripetizioni: "10-15" },
  trapezio: { serie: 3, ripetizioni: "12-15" },
  core: { serie: 3, ripetizioni: "12-15" },
  bicipiti: { serie: 2, ripetizioni: "10-15" },
  tricipiti: { serie: 2, ripetizioni: "10-15" },
  avambracci: { serie: 2, ripetizioni: "12-15" },
  polpacci: { serie: 4, ripetizioni: "15-20" },
  adduttori: { serie: 3, ripetizioni: "12-15" },
};
const DEFAULT_ACC_VOLUME = { serie: 3, ripetizioni: "10-15" };

export function getAccessoryVolume(muscle: string): { serie: number; ripetizioni: string } {
  return ACCESSORY_VOLUME[muscle] ?? DEFAULT_ACC_VOLUME;
}

// ── Session Blueprints ──
// 2-6 sessioni/settimana × 3 livelli = 15 blueprint

export const SESSION_BLUEPRINTS: Record<number, Record<FitnessLevel, SplitBlueprint>> = {
  2: {
    beginner: { sessioni: [
      _bp("Full Body A", "petto, quadricipiti, dorsali", [
        [CP, "push_h", "petto"], [CS, "pull_h", "dorsali"], [CS, "squat", "quadricipiti"],
        [CS, "hinge", "femorali"], [IA, "push_h", "tricipiti"], [IA, "core", "core"],
      ]),
      _bp("Full Body B", "dorsali, glutei, petto", [
        [CP, "pull_v", "dorsali"], [CS, "push_h", "petto"], [CS, "hinge", "glutei"],
        [CS, "squat", "quadricipiti"], [IA, "pull_h", "bicipiti"], [IA, "squat", "polpacci"],
      ]),
    ]},
    intermedio: { sessioni: [
      _bp("Full Body A", "petto, quadricipiti, dorsali", [
        [CP, "push_h", "petto"], [CS, "pull_h", "dorsali"], [CS, "squat", "quadricipiti"],
        [CS, "hinge", "femorali"], [CS, "push_v", "spalle"], [CS, "carry", "avambracci"],
      ]),
      _bp("Full Body B", "dorsali, glutei, petto", [
        [CP, "pull_v", "dorsali"], [CS, "push_h", "petto"], [CS, "hinge", "glutei"],
        [CS, "squat", "quadricipiti"], [IA, "pull_h", "bicipiti"], [IA, "rotation", "core"],
      ]),
    ]},
    avanzato: { sessioni: [
      _bp("Full Body A", "petto, quadricipiti, dorsali", [
        [CP, "push_h", "petto"], [CS, "pull_h", "dorsali"], [CS, "squat", "quadricipiti"],
        [CS, "hinge", "femorali"], [CS, "push_v", "spalle"], [CS, "carry", "avambracci"],
      ]),
      _bp("Full Body B", "dorsali, glutei, petto", [
        [CP, "pull_v", "dorsali"], [CS, "push_h", "petto"], [CS, "hinge", "glutei"],
        [CS, "squat", "quadricipiti"], [IA, "pull_h", "bicipiti"], [IA, "rotation", "core"],
      ]),
    ]},
  },
  3: {
    beginner: { sessioni: [
      _bp("Full Body A", "petto, dorsali, quadricipiti", [
        [CP, "push_h", "petto"], [CS, "pull_h", "dorsali"], [CS, "squat", "quadricipiti"],
        [CS, "hinge", "femorali"], [IA, "push_h", "tricipiti"],
      ]),
      _bp("Full Body B", "dorsali, glutei, petto", [
        [CP, "pull_v", "dorsali"], [CS, "push_h", "petto"], [CS, "hinge", "glutei"],
        [CS, "squat", "quadricipiti"], [IA, "pull_h", "bicipiti"],
      ]),
      _bp("Full Body C", "quadricipiti, spalle, dorsali", [
        [CP, "squat", "quadricipiti"], [CS, "push_v", "spalle"], [CS, "pull_h", "dorsali"],
        [CS, "hinge", "femorali"], [IA, "squat", "polpacci"],
      ]),
    ]},
    intermedio: { sessioni: [
      _bp("Full Body A — Push", "petto, dorsali, quadricipiti", [
        [CP, "push_h", "petto"], [CS, "pull_h", "dorsali"], [CS, "squat", "quadricipiti"],
        [IT, "push_v", "spalle"], [IA, "push_h", "tricipiti"],
      ]),
      _bp("Full Body B — Pull", "dorsali, petto, femorali", [
        [CP, "pull_v", "dorsali"], [CS, "push_h", "petto"], [CS, "hinge", "femorali"],
        [IT, "pull_h", "bicipiti"], [IA, "squat", "polpacci"],
      ]),
      _bp("Full Body C — Legs", "quadricipiti, femorali, dorsali", [
        [CP, "squat", "quadricipiti"], [CS, "hinge", "glutei"], [CS, "push_v", "spalle"],
        [IT, "pull_h", "trapezio"], [CS, "carry", "avambracci"],
      ]),
    ]},
    avanzato: { sessioni: [
      _bp("Full Body A — Push", "petto, dorsali, quadricipiti", [
        [CP, "push_h", "petto"], [CS, "pull_h", "dorsali"], [CS, "squat", "quadricipiti"],
        [CS, "hinge", "femorali"], [IT, "push_v", "spalle"], [IA, "push_h", "tricipiti"],
      ]),
      _bp("Full Body B — Pull", "dorsali, petto, glutei", [
        [CP, "pull_v", "dorsali"], [CS, "push_h", "petto"], [CS, "hinge", "glutei"],
        [CS, "squat", "quadricipiti"], [IT, "pull_h", "bicipiti"], [IA, "squat", "polpacci"],
      ]),
      _bp("Full Body C — Legs", "quadricipiti, femorali, spalle", [
        [CP, "squat", "quadricipiti"], [CS, "hinge", "femorali"], [CS, "push_v", "spalle"],
        [CS, "pull_h", "dorsali"], [IT, "pull_h", "trapezio"], [CS, "carry", "avambracci"],
      ]),
    ]},
  },
  4: {
    beginner: { sessioni: [
      _bp("Upper A", "petto, dorsali, spalle", [
        [CP, "push_h", "petto"], [CS, "pull_h", "dorsali"], [CS, "push_v", "spalle"],
        [IA, "push_h", "tricipiti"],
      ]),
      _bp("Lower A", "quadricipiti, glutei, femorali", [
        [CP, "squat", "quadricipiti"], [CS, "hinge", "femorali"], [IT, "squat", "quadricipiti"],
        [IA, "squat", "polpacci"],
      ]),
      _bp("Upper B", "dorsali, petto, braccia", [
        [CP, "pull_h", "dorsali"], [CS, "push_h", "petto"], [CS, "pull_v", "dorsali"],
        [IA, "pull_h", "bicipiti"],
      ]),
      _bp("Lower B", "glutei, femorali, core", [
        [CP, "hinge", "glutei"], [CS, "squat", "quadricipiti"], [IT, "hinge", "femorali"],
        [CS, "carry", "avambracci"],
      ]),
    ]},
    intermedio: { sessioni: [
      _bp("Upper A — Push", "petto, spalle, tricipiti", [
        [CP, "push_h", "petto"], [CS, "push_v", "spalle"], [CS, "push_h", "petto"],
        [CS, "pull_h", "dorsali"], [IT, "push_h", "tricipiti"], [IA, "pull_h", "bicipiti"],
      ]),
      _bp("Lower A — Quad", "quadricipiti, glutei, femorali", [
        [CP, "squat", "quadricipiti"], [CS, "squat", "quadricipiti"], [CS, "hinge", "femorali"],
        [IT, "squat", "quadricipiti"], [IT, "hinge", "femorali"], [IA, "squat", "polpacci"],
      ]),
      _bp("Upper B — Pull", "dorsali, trapezio, bicipiti", [
        [CP, "pull_v", "dorsali"], [CS, "pull_h", "dorsali"], [CS, "push_v", "spalle"],
        [IT, "pull_h", "trapezio"], [IT, "pull_h", "bicipiti"], [IA, "push_h", "tricipiti"],
      ]),
      _bp("Lower B — Hip", "glutei, femorali, core", [
        [CP, "hinge", "glutei"], [CS, "hinge", "femorali"], [CS, "squat", "quadricipiti"],
        [IT, "hinge", "femorali"], [IT, "core", "core"], [CS, "carry", "avambracci"],
      ]),
    ]},
    avanzato: { sessioni: [
      _bp("Upper A — Push", "petto, spalle, tricipiti", [
        [CP, "push_h", "petto"], [CS, "push_v", "spalle"], [CS, "push_h", "petto"],
        [CS, "pull_h", "dorsali"], [IT, "push_h", "tricipiti"], [IA, "pull_h", "bicipiti"],
        [IA, "rotation", "core"],
      ]),
      _bp("Lower A — Quad", "quadricipiti, glutei, femorali", [
        [CP, "squat", "quadricipiti"], [CS, "squat", "quadricipiti"], [CS, "hinge", "femorali"],
        [IT, "squat", "quadricipiti"], [IT, "hinge", "femorali"], [IA, "squat", "polpacci"],
        [CS, "carry", "avambracci"],
      ]),
      _bp("Upper B — Pull", "dorsali, trapezio, bicipiti", [
        [CP, "pull_v", "dorsali"], [CS, "pull_h", "dorsali"], [CS, "push_v", "spalle"],
        [IT, "pull_h", "trapezio"], [IT, "pull_h", "bicipiti"], [IA, "push_h", "tricipiti"],
        [IA, "rotation", "core"],
      ]),
      _bp("Lower B — Hip", "glutei, femorali, adduttori", [
        [CP, "hinge", "glutei"], [CS, "hinge", "femorali"], [CS, "squat", "quadricipiti"],
        [IT, "squat", "adduttori"], [IT, "hinge", "femorali"], [IA, "hinge", "polpacci"],
        [CS, "carry", "avambracci"],
      ]),
    ]},
  },
  5: {
    beginner: { sessioni: [
      _bp("Upper A", "petto, dorsali, spalle", [
        [CP, "push_h", "petto"], [CS, "pull_h", "dorsali"], [CS, "push_v", "spalle"],
        [IA, "push_h", "tricipiti"],
      ]),
      _bp("Lower A", "quadricipiti, glutei", [
        [CP, "squat", "quadricipiti"], [CS, "hinge", "femorali"], [IT, "squat", "quadricipiti"],
        [IA, "squat", "polpacci"],
      ]),
      _bp("Upper B", "dorsali, spalle, braccia", [
        [CP, "pull_h", "dorsali"], [CS, "push_h", "petto"], [CS, "pull_v", "dorsali"],
        [IA, "pull_h", "bicipiti"],
      ]),
      _bp("Lower B", "glutei, femorali", [
        [CP, "hinge", "glutei"], [CS, "squat", "quadricipiti"], [IT, "hinge", "femorali"],
        [CS, "carry", "avambracci"],
      ]),
      _bp("Full Body", "bilancio, core", [
        [CP, "squat", "quadricipiti"], [CS, "push_h", "petto"], [CS, "pull_v", "dorsali"],
        [CS, "hinge", "femorali"], [IA, "rotation", "core"],
      ]),
    ]},
    intermedio: { sessioni: [
      _bp("Upper A", "petto, dorsali, spalle", [
        [CP, "push_h", "petto"], [CS, "pull_h", "dorsali"], [CS, "push_v", "spalle"],
        [IT, "pull_v", "dorsali"], [IA, "rotation", "core"],
      ]),
      _bp("Lower A", "quadricipiti, glutei", [
        [CP, "squat", "quadricipiti"], [CS, "hinge", "femorali"], [CS, "squat", "quadricipiti"],
        [IT, "hinge", "femorali"], [CS, "carry", "avambracci"],
      ]),
      _bp("Upper B", "dorsali, petto, braccia", [
        [CP, "pull_h", "dorsali"], [CS, "push_h", "petto"], [CS, "pull_v", "dorsali"],
        [IT, "push_v", "spalle"], [IA, "rotation", "core"],
      ]),
      _bp("Lower B", "glutei, femorali", [
        [CP, "hinge", "glutei"], [CS, "squat", "quadricipiti"], [CS, "hinge", "femorali"],
        [IT, "squat", "polpacci"], [CS, "carry", "avambracci"],
      ]),
      _bp("Full Body", "compenso, varieta'", [
        [CP, "squat", "quadricipiti"], [CS, "push_v", "spalle"], [CS, "pull_h", "dorsali"],
        [CS, "hinge", "femorali"], [CS, "carry", "avambracci"],
      ]),
    ]},
    avanzato: { sessioni: [
      _bp("Upper A", "petto, dorsali, spalle", [
        [CP, "push_h", "petto"], [CS, "pull_h", "dorsali"], [CS, "push_v", "spalle"],
        [IT, "pull_v", "dorsali"], [IA, "push_h", "tricipiti"], [IA, "rotation", "core"],
      ]),
      _bp("Lower A", "quadricipiti, glutei", [
        [CP, "squat", "quadricipiti"], [CS, "hinge", "femorali"], [CS, "squat", "quadricipiti"],
        [IT, "hinge", "femorali"], [IT, "squat", "polpacci"], [CS, "carry", "avambracci"],
      ]),
      _bp("Upper B", "dorsali, petto, braccia", [
        [CP, "pull_h", "dorsali"], [CS, "push_h", "petto"], [CS, "pull_v", "dorsali"],
        [IT, "push_v", "spalle"], [IA, "pull_h", "bicipiti"], [IA, "rotation", "core"],
      ]),
      _bp("Lower B", "glutei, femorali", [
        [CP, "hinge", "glutei"], [CS, "squat", "quadricipiti"], [CS, "hinge", "femorali"],
        [IT, "squat", "adduttori"], [IT, "hinge", "polpacci"], [CS, "carry", "avambracci"],
      ]),
      _bp("Full Body", "volume extra", [
        [CP, "squat", "quadricipiti"], [CS, "push_h", "petto"], [CS, "pull_v", "dorsali"],
        [CS, "hinge", "femorali"], [CS, "push_v", "spalle"], [CS, "carry", "avambracci"],
      ]),
    ]},
  },
  6: {
    beginner: { sessioni: [
      _bp("Push A", "petto, spalle, tricipiti", [
        [CP, "push_h", "petto"], [CS, "push_v", "spalle"], [IT, "push_h", "petto"],
        [IA, "push_h", "tricipiti"],
      ]),
      _bp("Pull A", "dorsali, trapezio, bicipiti", [
        [CP, "pull_v", "dorsali"], [CS, "pull_h", "dorsali"], [IT, "pull_h", "trapezio"],
        [IA, "pull_h", "bicipiti"],
      ]),
      _bp("Legs A", "quadricipiti, glutei, polpacci", [
        [CP, "squat", "quadricipiti"], [CS, "hinge", "femorali"], [IT, "squat", "quadricipiti"],
        [IA, "squat", "polpacci"],
      ]),
      _bp("Push B", "petto, spalle, tricipiti", [
        [CP, "push_h", "petto"], [CS, "push_v", "spalle"], [IT, "push_v", "spalle"],
        [IA, "push_h", "tricipiti"],
      ]),
      _bp("Pull B", "dorsali, trapezio, bicipiti", [
        [CP, "pull_h", "dorsali"], [CS, "pull_v", "dorsali"], [IT, "pull_h", "trapezio"],
        [IA, "pull_h", "bicipiti"],
      ]),
      _bp("Legs B", "glutei, femorali, core", [
        [CP, "hinge", "glutei"], [CS, "squat", "quadricipiti"], [IT, "hinge", "femorali"],
        [CS, "carry", "avambracci"],
      ]),
    ]},
    intermedio: { sessioni: [
      _bp("Push A — Forza", "petto, spalle, tricipiti", [
        [CP, "push_h", "petto"], [CS, "push_v", "spalle"], [CS, "push_h", "petto"],
        [IT, "push_v", "spalle"], [IA, "push_h", "tricipiti"],
      ]),
      _bp("Pull A — Forza", "dorsali, trapezio, bicipiti", [
        [CP, "pull_v", "dorsali"], [CS, "pull_h", "dorsali"], [CS, "pull_v", "dorsali"],
        [IT, "pull_h", "trapezio"], [IA, "pull_h", "bicipiti"],
      ]),
      _bp("Legs A — Quad", "quadricipiti, glutei, femorali", [
        [CP, "squat", "quadricipiti"], [CS, "hinge", "femorali"], [CS, "squat", "quadricipiti"],
        [IT, "hinge", "femorali"], [CS, "carry", "avambracci"],
      ]),
      _bp("Push B — Ipertrofia", "petto, spalle, tricipiti", [
        [CP, "push_h", "petto"], [CS, "push_v", "spalle"], [CS, "push_h", "petto"],
        [IT, "push_v", "spalle"], [IA, "push_h", "tricipiti"],
      ]),
      _bp("Pull B — Ipertrofia", "dorsali, trapezio, bicipiti", [
        [CP, "pull_h", "dorsali"], [CS, "pull_v", "dorsali"], [CS, "pull_h", "dorsali"],
        [IT, "pull_v", "trapezio"], [IA, "pull_h", "bicipiti"],
      ]),
      _bp("Legs B — Hip", "glutei, femorali, polpacci", [
        [CP, "hinge", "glutei"], [CS, "squat", "quadricipiti"], [CS, "hinge", "femorali"],
        [IT, "squat", "polpacci"], [CS, "carry", "avambracci"],
      ]),
    ]},
    avanzato: { sessioni: [
      _bp("Push A — Forza", "petto, spalle, tricipiti, core", [
        [CP, "push_h", "petto"], [CS, "push_v", "spalle"], [CS, "push_h", "petto"],
        [IT, "push_v", "spalle"], [IA, "push_h", "tricipiti"], [IA, "rotation", "core"],
      ]),
      _bp("Pull A — Forza", "dorsali, trapezio, bicipiti, core", [
        [CP, "pull_v", "dorsali"], [CS, "pull_h", "dorsali"], [CS, "pull_v", "dorsali"],
        [IT, "pull_h", "trapezio"], [IA, "pull_h", "bicipiti"], [IA, "core", "core"],
      ]),
      _bp("Legs A — Quad", "quadricipiti, glutei, femorali", [
        [CP, "squat", "quadricipiti"], [CS, "hinge", "femorali"], [CS, "squat", "quadricipiti"],
        [IT, "hinge", "femorali"], [IT, "squat", "polpacci"], [CS, "carry", "avambracci"],
      ]),
      _bp("Push B — Ipertrofia", "petto, spalle, tricipiti, core", [
        [CP, "push_h", "petto"], [CS, "push_v", "spalle"], [CS, "push_h", "petto"],
        [IT, "push_v", "spalle"], [IA, "push_h", "tricipiti"], [IA, "rotation", "core"],
      ]),
      _bp("Pull B — Ipertrofia", "dorsali, trapezio, bicipiti, core", [
        [CP, "pull_h", "dorsali"], [CS, "pull_v", "dorsali"], [CS, "pull_h", "dorsali"],
        [IT, "pull_v", "trapezio"], [IA, "pull_h", "bicipiti"], [IA, "core", "core"],
      ]),
      _bp("Legs B — Hip", "glutei, femorali, adduttori", [
        [CP, "hinge", "glutei"], [CS, "squat", "quadricipiti"], [CS, "hinge", "femorali"],
        [IT, "squat", "adduttori"], [IT, "hinge", "polpacci"], [CS, "carry", "avambracci"],
      ]),
    ]},
  },
};
