#!/usr/bin/env npx tsx
/**
 * Diagnostica KineScore v3 — Verifica copertura muscolare con TIERED targets.
 *
 * Esegui: cd frontend && npx tsx ../tools/diagnostic_smart_coverage.ts
 *
 * Replica la logica di computeBlueprintCoverage() + MUSCLE_TARGET_TIER per
 * verificare che i blueprint generino programmi bilanciati.
 * Copre TUTTE le frequenze (2-6) × livelli × obiettivi.
 */

// ══════════════════════════════════════════════════════════════
// CONSTANTS — replica esatta da smart-programming.ts (v2)
// ══════════════════════════════════════════════════════════════

type SlotType = "compound_primary" | "compound_secondary" | "isolation_target" | "isolation_accessory";
type FitnessLevel = "beginner" | "intermedio" | "avanzato";

interface BlueprintSlot { type: SlotType; pattern_hint: string; targetMuscle: string; }
interface SessionBlueprint { nome: string; focus: string; slots: BlueprintSlot[]; }
interface SplitBlueprint { sessioni: SessionBlueprint[]; }

// Compact helpers
type BSlot = [SlotType, string, string];
const CP: SlotType = "compound_primary";
const CS: SlotType = "compound_secondary";
const IT: SlotType = "isolation_target";
const IA: SlotType = "isolation_accessory";
function _bp(nome: string, focus: string, slots: BSlot[]): SessionBlueprint {
  return { nome, focus, slots: slots.map(([type, pattern_hint, targetMuscle]) => ({ type, pattern_hint, targetMuscle })) };
}

// Volume per slot × obiettivo (solo serie per questa diagnostica)
const SLOT_VOLUME: Record<SlotType, Record<string, { serie: number }>> = {
  compound_primary:   { forza: { serie: 5 }, ipertrofia: { serie: 4 }, resistenza: { serie: 3 }, dimagrimento: { serie: 3 }, generale: { serie: 3 } },
  compound_secondary: { forza: { serie: 4 }, ipertrofia: { serie: 3 }, resistenza: { serie: 3 }, dimagrimento: { serie: 3 }, generale: { serie: 3 } },
  isolation_target:   { forza: { serie: 3 }, ipertrofia: { serie: 3 }, resistenza: { serie: 3 }, dimagrimento: { serie: 3 }, generale: { serie: 3 } },
  isolation_accessory:{ forza: { serie: 2 }, ipertrofia: { serie: 3 }, resistenza: { serie: 2 }, dimagrimento: { serie: 2 }, generale: { serie: 2 } },
};

function getSlotSerie(type: SlotType, obiettivo: string): number {
  return (SLOT_VOLUME[type][obiettivo] ?? SLOT_VOLUME[type].generale).serie;
}

// Pattern → Muscoli (v2: squat = quad primary, glutei secondary)
function patternToMuscleRoles(pattern: string): { primari: string[]; secondari: string[] } {
  const map: Record<string, { primari: string[]; secondari: string[] }> = {
    squat:    { primari: ["quadricipiti"],                  secondari: ["glutei", "femorali", "adduttori"] },
    hinge:    { primari: ["femorali", "glutei"],           secondari: ["dorsali"] },
    push_h:   { primari: ["petto"],                        secondari: ["tricipiti", "spalle"] },
    push_v:   { primari: ["spalle"],                       secondari: ["tricipiti"] },
    pull_h:   { primari: ["dorsali"],                      secondari: ["bicipiti", "trapezio"] },
    pull_v:   { primari: ["dorsali"],                      secondari: ["bicipiti"] },
    core:     { primari: ["core"],                         secondari: [] },
    rotation: { primari: ["core"],                         secondari: ["spalle"] },
    carry:    { primari: ["core", "avambracci"],           secondari: ["trapezio"] },
    warmup:   { primari: [],                               secondari: [] },
    stretch:  { primari: [],                               secondari: [] },
    mobility: { primari: [],                               secondari: [] },
  };
  return map[pattern] ?? { primari: [], secondari: [] };
}

// Tiered targets (v2)
const BASE_VOLUME_TARGETS: Record<FitnessLevel, { min: number; max: number }> = {
  beginner:   { min: 10, max: 12 },
  intermedio: { min: 14, max: 18 },
  avanzato:   { min: 18, max: 25 },
};
const SCALE: Record<number, number> = { 2: 0.50, 3: 0.65, 4: 1.0, 5: 1.1, 6: 1.2 };
function getScaledTargets(livello: FitnessLevel, freq: number) {
  const base = BASE_VOLUME_TARGETS[livello];
  const f = SCALE[Math.max(2, Math.min(6, freq))] ?? 1.0;
  return { min: Math.round(base.min * f), max: Math.round(base.max * f) };
}

const MUSCLE_TARGET_TIER: Record<string, number> = {
  petto: 1.0, dorsali: 1.0, quadricipiti: 1.0, femorali: 1.0,
  glutei: 0.7, spalle: 0.7,
  bicipiti: 0.5, tricipiti: 0.5, trapezio: 0.5,
  core: 0.4, polpacci: 0.4, adduttori: 0.35, avambracci: 0.35,
};

function getMuscleTarget(muscolo: string, livello: FitnessLevel, freq: number) {
  const base = getScaledTargets(livello, freq);
  const tier = MUSCLE_TARGET_TIER[muscolo] ?? 0.5;
  return {
    min: Math.round(base.min * tier * 10) / 10,
    max: Math.round(base.max * tier * 10) / 10,
  };
}

const MUSCLE_GROUPS = [
  "petto", "dorsali", "spalle", "bicipiti", "tricipiti",
  "quadricipiti", "femorali", "glutei", "polpacci",
  "core", "trapezio", "adduttori", "avambracci",
] as const;

// ══════════════════════════════════════════════════════════════
// BLUEPRINTS — copia esatta da smart-programming.ts
// ══════════════════════════════════════════════════════════════

const SESSION_BLUEPRINTS: Record<number, Record<FitnessLevel, SplitBlueprint>> = {
  // ── 2x Full Body ──
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

  // ── 3x Full Body ──
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

  // ── 4x Upper/Lower ──
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

  // ── 5x Upper/Lower + Full Body ──
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

  // ── 6x PPL ──
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

// ══════════════════════════════════════════════════════════════
// COVERAGE COMPUTATION (v2: reduced secondary credit 0.35)
// ══════════════════════════════════════════════════════════════

function computeCoverage(blueprint: SplitBlueprint, obiettivo: string): Map<string, number> {
  const sets = new Map<string, number>();
  for (const session of blueprint.sessioni) {
    for (const slot of session.slots) {
      const serie = getSlotSerie(slot.type, obiettivo);
      if (slot.type === "isolation_target" || slot.type === "isolation_accessory") {
        const m = slot.targetMuscle.toLowerCase();
        sets.set(m, (sets.get(m) ?? 0) + serie);
      } else {
        const roles = patternToMuscleRoles(slot.pattern_hint);
        for (const m of roles.primari) {
          sets.set(m, (sets.get(m) ?? 0) + serie * 1.0);
        }
        const secLen = roles.secondari.length;
        const secCredit = secLen > 0 ? Math.min(0.35, 1.0 / secLen) : 0;
        for (const m of roles.secondari) {
          sets.set(m, (sets.get(m) ?? 0) + serie * secCredit);
        }
      }
    }
  }
  return sets;
}

// ══════════════════════════════════════════════════════════════
// DIAGNOSTICA
// ══════════════════════════════════════════════════════════════

const OBIETTIVI = ["ipertrofia", "forza", "generale"] as const;
const FREQS = [2, 3, 4, 5, 6] as const;
const LIVELLI: FitnessLevel[] = ["beginner", "intermedio", "avanzato"];

console.log("=".repeat(80));
console.log("DIAGNOSTICA KINESCORE v3 — All frequencies (2-6) × Tiered Targets");
console.log("=".repeat(80));
console.log();

let totalConfigs = 0;
let totalDeficits = 0;
let worstConfig = { key: "", deficits: 0 };

// Per-frequency summary
const freqSummary: Record<number, { configs: number; deficits: number }> = {};

for (const freq of FREQS) {
  freqSummary[freq] = { configs: 0, deficits: 0 };
  for (const livello of LIVELLI) {
    const blueprint = SESSION_BLUEPRINTS[freq]?.[livello];
    if (!blueprint) continue;

    for (const obiettivo of OBIETTIVI) {
      totalConfigs++;
      freqSummary[freq].configs++;
      const coverage = computeCoverage(blueprint, obiettivo);

      const deficits: string[] = [];
      const excess: string[] = [];

      for (const m of MUSCLE_GROUPS) {
        const sets = Math.round((coverage.get(m) ?? 0) * 10) / 10;
        const target = getMuscleTarget(m, livello, freq);
        const status = sets < target.min ? "DEFICIT" : sets > target.max ? "excess" : "ok";
        if (status === "DEFICIT") {
          deficits.push(`${m}(${sets}/${target.min})`);
        } else if (status === "excess") {
          excess.push(`${m}(${sets}/${target.max})`);
        }
      }

      totalDeficits += deficits.length;
      freqSummary[freq].deficits += deficits.length;
      if (deficits.length > worstConfig.deficits) {
        worstConfig = { key: `${freq}x ${livello} ${obiettivo}`, deficits: deficits.length };
      }

      // Stampa solo se ci sono deficit
      if (deficits.length > 0) {
        const baseTarget = getScaledTargets(livello, freq);
        const header = `${freq}x/sett | ${livello.padEnd(10)} | ${obiettivo.padEnd(12)} | base: ${baseTarget.min}-${baseTarget.max}`;
        console.log(`--- ${header} ---`);
        console.log(`  DEFICIT (${deficits.length}): ${deficits.join(", ")}`);
        if (excess.length > 0) console.log(`  EXCESS  (${excess.length}): ${excess.join(", ")}`);
        console.log();
      }
    }
  }
}

console.log("=".repeat(80));
console.log("RIEPILOGO PER FREQUENZA");
console.log("=".repeat(80));
for (const freq of FREQS) {
  const s = freqSummary[freq];
  console.log(`  ${freq}x/sett: ${s.deficits} deficit su ${s.configs} config (media ${(s.deficits / s.configs).toFixed(1)})`);
}

console.log();
console.log("=".repeat(80));
console.log("RIEPILOGO GLOBALE");
console.log("=".repeat(80));
console.log(`Configurazioni testate: ${totalConfigs}`);
console.log(`Deficit totali: ${totalDeficits} (media ${(totalDeficits / totalConfigs).toFixed(1)} per config)`);
console.log(`Peggior caso: ${worstConfig.key} con ${worstConfig.deficits} deficit`);
console.log();

// Stampa tier targets per una config di esempio
console.log("=".repeat(80));
console.log("ESEMPIO DETTAGLIATO — 4x intermedio ipertrofia");
console.log("=".repeat(80));
const exCoverage = computeCoverage(SESSION_BLUEPRINTS[4]!.intermedio, "ipertrofia");
console.log(`${"MUSCOLO".padEnd(14)} ${"TIER".padStart(5)} ${"TARGET".padStart(10)} ${"COPERTURA".padStart(10)} ${"STATUS".padStart(8)}`);
for (const m of MUSCLE_GROUPS) {
  const tier = MUSCLE_TARGET_TIER[m] ?? 0.5;
  const target = getMuscleTarget(m, "intermedio", 4);
  const sets = Math.round((exCoverage.get(m) ?? 0) * 10) / 10;
  const status = sets < target.min ? "DEFICIT" : sets > target.max ? "EXCESS" : "OK";
  console.log(`${m.padEnd(14)} ${tier.toFixed(2).padStart(5)} ${`${target.min}-${target.max}`.padStart(10)} ${String(sets).padStart(10)} ${status.padStart(8)}`);
}
