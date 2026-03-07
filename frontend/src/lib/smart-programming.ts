// src/lib/smart-programming.ts
/**
 * Motore di Programmazione SMART — Engine deterministico client-side.
 *
 * Incrocia 14 dimensioni per suggerire gli esercizi ottimali per ogni slot,
 * genera strutture sessione da sessioni/settimana + livello, analizza
 * copertura muscolare, volume, recupero e varieta' biomeccanica.
 *
 * Filosofia: INFORMARE, mai LIMITARE. Zero Ollama. Tutto client-side.
 * Pattern: clinical-analysis.ts, derived-metrics.ts (tipi + funzioni pure).
 *
 * Fonti:
 *   - Volume: NSCA Guidelines (Krieger 2010, Schoenfeld 2017)
 *   - Recupero: ACSM Position Stand
 *   - Forza Relativa: NSCA Strength Benchmarks
 */

import type {
  Exercise,
  ExerciseSafetyEntry,
  ClientGoal,
  AnamnesiData,
} from "@/types/api";
import type { StrengthRatio } from "@/lib/derived-metrics";
import type { SymmetryPair } from "@/lib/clinical-analysis";
import type { TemplateSection } from "@/lib/workout-templates";
import { getSectionForCategory, SECTION_CATEGORIES } from "@/lib/workout-templates";
import { computeAge } from "@/lib/normative-ranges";

// ════════════════════════════════════════════════════════════
// TYPES — Profilo Client Aggregato
// ════════════════════════════════════════════════════════════

/** Profilo client aggregato per scoring. Tutto nullable per graceful degradation. */
export interface ClientProfile {
  sesso: string | null;
  eta: number | null;
  livelloAttivita: string | null;
  safetyMap: Record<number, ExerciseSafetyEntry> | null;
  measurements: {
    peso: number | null;
    altezza: number | null;
    grassoPct: number | null;
  } | null;
  strengthRatios: StrengthRatio[];
  goals: ClientGoal[];
  symmetryDeficits: SymmetryPair[];
  strengthLevel: FitnessLevel | null;
}

// ════════════════════════════════════════════════════════════
// TYPES — Scoring
// ════════════════════════════════════════════════════════════

export interface ScoreDimension {
  id: string;
  label: string;
  score: number;    // 0-1 normalizzato
  weight: number;
  reason: string;   // italiano, per tooltip UI
}

export interface ExerciseScore {
  exerciseId: number;
  exerciseName: string;
  totalScore: number;          // 0-100
  dimensions: ScoreDimension[];
  safetySeverity: "avoid" | "caution" | "modify" | null;
}

// ════════════════════════════════════════════════════════════
// TYPES — Smart Plan
// ════════════════════════════════════════════════════════════

/** Tipo funzionale dello slot — determina strategia di selezione esercizio */
export type SlotType = "compound_primary" | "compound_secondary" | "isolation_target" | "isolation_accessory";

export interface SmartSlot {
  sezione: TemplateSection;
  pattern_hint: string;
  muscoli_target: string[];
  label: string;
  serie: number;
  ripetizioni: string;
  tempo_riposo_sec: number;
  /** Tipo funzionale: compound vs isolation, primario vs accessorio */
  slotType?: SlotType;
}

export interface SmartSession {
  nome_sessione: string;
  focus_muscolare: string;
  durata_minuti: number;
  slots: SmartSlot[];
}

export interface SmartPlan {
  nome: string;
  livello: string;
  obiettivo: string;
  sessioni_per_settimana: number;
  durata_settimane: number;
  sessioni: SmartSession[];
}

// ── Blueprint Types (template-driven generation) ──

export interface BlueprintSlot {
  type: SlotType;
  pattern_hint: string;
  targetMuscle: string;
}

export interface SessionBlueprint {
  nome: string;
  focus: string;
  slots: BlueprintSlot[];
}

export interface SplitBlueprint {
  sessioni: SessionBlueprint[];
}

// ════════════════════════════════════════════════════════════
// TYPES — Analisi
// ════════════════════════════════════════════════════════════

export type CoverageStatus = "deficit" | "optimal" | "excess";

export interface MuscleCoverage {
  muscolo: string;
  setsPerWeek: number;
  target: { min: number; max: number };
  status: CoverageStatus;
}

export interface VolumeAnalysis {
  totalSetsPerWeek: number;
  targetRange: { min: number; max: number };
  status: CoverageStatus;
}

export interface BiomechanicalVariety {
  planes: Record<string, number>;       // sagittal/frontal/transverse/multi → count
  chains: Record<string, number>;       // open/closed → count
  contractions: Record<string, number>; // concentric/eccentric/isometric/dynamic → count
}

export interface RecoveryConflict {
  sessionA: string;
  sessionB: string;
  muscoli: string[];
  oreNecessarie: number;
  oreDisponibili: number;
  severity: "warning" | "alert";
}

export interface SmartAnalysis {
  coverage: MuscleCoverage[];
  volume: VolumeAnalysis;
  biomechanics: BiomechanicalVariety;
  recoveryConflicts: RecoveryConflict[];
  safetyScore: number;  // 0-100, percentuale esercizi safe
}

// ════════════════════════════════════════════════════════════
// TYPES — Fitness Level
// ════════════════════════════════════════════════════════════

export type FitnessLevel = "beginner" | "intermedio" | "avanzato";

// ════════════════════════════════════════════════════════════
// CONSTANTS — Volume Targets (NSCA)
// ════════════════════════════════════════════════════════════

/** Set/muscolo/settimana target base per livello (Krieger 2010, Schoenfeld 2017).
 * Baseline assume 3-4 sessioni/settimana. Usare getScaledVolumeTargets() per
 * adattare alla configurazione reale del piano. */
const BASE_VOLUME_TARGETS: Record<FitnessLevel, { min: number; max: number }> = {
  beginner:   { min: 10, max: 12 },
  intermedio: { min: 14, max: 18 },
  avanzato:   { min: 18, max: 25 },
};

/** Moltiplicatore target per gruppo muscolare (NSCA, Schoenfeld 2017, Israetel MRV).
 *
 * I grandi gruppi motori (petto, dorsali, quad, femorali) necessitano del volume
 * pieno perche' sono i motori primari dei compound e rispondono al volume diretto.
 * I piccoli muscoli (bicipiti, tricipiti, polpacci) ricevono stimolo secondario
 * significativo dai compound → target diretto ridotto e' sufficiente.
 *
 * Tier 1.0 = full NSCA target (grandi motori primari)
 * Tier 0.7 = ricevono volume compound significativo come sinergici
 * Tier 0.5 = piccoli muscoli con forte stimolo secondario
 * Tier 0.35 = stabilizzatori / accessori minimali */
const MUSCLE_TARGET_TIER: Record<string, number> = {
  // Grandi gruppi motori: full target
  petto: 1.0, dorsali: 1.0, quadricipiti: 1.0, femorali: 1.0,
  // Medi: volume compound significativo come sinergici
  glutei: 0.7, spalle: 0.7,
  // Piccoli: forte stimolo secondario dai compound
  bicipiti: 0.5, tricipiti: 0.5, trapezio: 0.5,
  // Accessori: stabilizzatori, volume diretto minimale sufficiente
  core: 0.4, polpacci: 0.4, adduttori: 0.35, avambracci: 0.35,
};

/** Scala target volume in base alle sessioni/settimana.
 * NSCA baseline assume 3-4 sessioni. Meno sessioni → target raggiungibili piu' bassi. */
function getScaledVolumeTargets(
  livello: FitnessLevel, sessioniPerSettimana: number,
): { min: number; max: number } {
  const base = BASE_VOLUME_TARGETS[livello];
  // 2x/3x scalati in base al volume realizzabile con N sessioni.
  // NSCA baseline = 4x. Con 2-3 sessioni Full Body il volume per-muscolo
  // e' fisicamente limitato dal numero di slot disponibili.
  const SCALE: Record<number, number> = { 2: 0.50, 3: 0.65, 4: 1.0, 5: 1.1, 6: 1.2 };
  const factor = SCALE[Math.max(2, Math.min(6, sessioniPerSettimana))] ?? 1.0;
  return { min: Math.round(base.min * factor), max: Math.round(base.max * factor) };
}

/** Target per-muscolo: base × scala frequenza × tier muscolare.
 * Un beginner 2x/sett ha target petto=6, polpacci=2.4, avambracci=2.1 */
function getMuscleTarget(
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
const TOTAL_VOLUME_TARGETS: Record<FitnessLevel, { min: number; max: number }> = {
  beginner:   { min: 30, max: 50 },
  intermedio: { min: 50, max: 80 },
  avanzato:   { min: 70, max: 120 },
};

// ════════════════════════════════════════════════════════════
// SESSION BLUEPRINTS — Template-driven plan generation
// ════════════════════════════════════════════════════════════
//
// Ogni blueprint definisce la struttura COMPLETA di una settimana di allenamento:
// - Slot tipizzati (compound_primary → isolation_accessory) con piramide di volume
// - Sessioni progettate come SISTEMA complementare (A+B si bilanciano)
// - Derivati dai template gold standard + principi NSCA/ACSM
//
// SlotType determina la strategia di selezione esercizio:
//   compound_primary:    compound pesante, primo della sessione (es. Squat 4x6-8)
//   compound_secondary:  compound complementare o antagonista (es. RDL 3x8-10)
//   isolation_target:    isolation per muscolo focus sessione (es. Leg Ext 3x12-15)
//   isolation_accessory: isolation per muscolo piccolo/secondario (es. Curl 2x12-15)

// Compact notation: [type, pattern_hint, targetMuscle]
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

/** Volume per slot type × obiettivo. Compound_primary = piu' serie/peso, isolation = meno serie/piu' rep. */
const SLOT_VOLUME: Record<SlotType, Record<string, { serie: number; ripetizioni: string; riposo: number }>> = {
  compound_primary: {
    forza:        { serie: 5, ripetizioni: "3-5",   riposo: 180 },
    ipertrofia:   { serie: 4, ripetizioni: "6-8",   riposo: 120 },
    resistenza:   { serie: 3, ripetizioni: "12-15", riposo: 60  },
    dimagrimento: { serie: 3, ripetizioni: "10-12", riposo: 75  },
    generale:     { serie: 3, ripetizioni: "8-12",  riposo: 90  },
  },
  compound_secondary: {
    forza:        { serie: 4, ripetizioni: "5-6",   riposo: 150 },
    ipertrofia:   { serie: 3, ripetizioni: "8-10",  riposo: 90  },
    resistenza:   { serie: 3, ripetizioni: "12-15", riposo: 45  },
    dimagrimento: { serie: 3, ripetizioni: "10-12", riposo: 60  },
    generale:     { serie: 3, ripetizioni: "8-12",  riposo: 90  },
  },
  isolation_target: {
    forza:        { serie: 3, ripetizioni: "8-10",  riposo: 90  },
    ipertrofia:   { serie: 3, ripetizioni: "10-12", riposo: 60  },
    resistenza:   { serie: 3, ripetizioni: "15-20", riposo: 45  },
    dimagrimento: { serie: 3, ripetizioni: "12-15", riposo: 45  },
    generale:     { serie: 3, ripetizioni: "10-12", riposo: 60  },
  },
  isolation_accessory: {
    forza:        { serie: 2, ripetizioni: "10-12", riposo: 60  },
    ipertrofia:   { serie: 3, ripetizioni: "12-15", riposo: 45  },
    resistenza:   { serie: 2, ripetizioni: "15-20", riposo: 30  },
    dimagrimento: { serie: 2, ripetizioni: "12-15", riposo: 45  },
    generale:     { serie: 2, ripetizioni: "10-15", riposo: 60  },
  },
};

function getSlotVolume(type: SlotType, obiettivo: string): { serie: number; ripetizioni: string; riposo: number } {
  return SLOT_VOLUME[type][obiettivo] ?? SLOT_VOLUME[type].generale;
}

/** Label slot per UI — descrive il ruolo funzionale */
function blueprintSlotLabel(type: SlotType, targetMuscle: string, pattern: string): string {
  switch (type) {
    case "compound_primary":   return patternToLabel(pattern);
    case "compound_secondary": return `${patternToLabel(pattern)} Complementare`;
    case "isolation_target":   return `Isolation ${capitalizeFirst(targetMuscle)}`;
    case "isolation_accessory":return `Accessorio ${capitalizeFirst(targetMuscle)}`;
  }
}

const SESSION_BLUEPRINTS: Record<number, Record<FitnessLevel, SplitBlueprint>> = {
  // ══════════════════════════════════════════════════
  // 2 sessioni: Full Body A/B (complementari)
  // Push_h in entrambe le sessioni (CP+CS) per garantire copertura petto.
  // A = push focus + quad, B = pull focus + hip
  // ══════════════════════════════════════════════════
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

  // ══════════════════════════════════════════════════
  // 3 sessioni: Full Body A/B/C (tutti i livelli)
  // 3x/sett = ogni muscolo allenato 3x/sett (frequenza ottimale Schoenfeld 2016).
  // PPL a 3x = 1x/sett per muscolo → subottimale. Full Body a 3x = 3x/sett.
  // A = push focus, B = pull focus, C = legs focus
  // ══════════════════════════════════════════════════
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

  // ══════════════════════════════════════════════════
  // 4 sessioni: Upper/Lower x2
  // Upper A (push focus) + Lower A (quad focus)
  // Upper B (pull focus) + Lower B (hip focus)
  // ══════════════════════════════════════════════════
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

  // ══════════════════════════════════════════════════
  // 5 sessioni: Upper/Lower x2 + Full Body
  // ══════════════════════════════════════════════════
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

  // ══════════════════════════════════════════════════
  // 6 sessioni: PPL x2
  // A = forza (serie alte, rep basse), B = ipertrofia (rep medie-alte)
  // ══════════════════════════════════════════════════
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

// ════════════════════════════════════════════════════════════
// CONSTANTS — Session Accessory Affinity (per split-aware accessories)
// ════════════════════════════════════════════════════════════

/** Serie e rep raccomandate per accessori/correzioni per gruppo muscolare.
 * Muscoli grandi tollerano piu' volume, piccoli meno (NSCA, Schoenfeld 2017). */
const ACCESSORY_VOLUME: Record<string, { serie: number; ripetizioni: string }> = {
  // Grandi: 3-4 serie, rep moderate
  petto:       { serie: 3, ripetizioni: "8-12" },
  dorsali:     { serie: 3, ripetizioni: "8-12" },
  quadricipiti:{ serie: 3, ripetizioni: "8-12" },
  femorali:    { serie: 3, ripetizioni: "10-12" },
  glutei:      { serie: 3, ripetizioni: "10-15" },
  // Medi: 3 serie
  spalle:      { serie: 3, ripetizioni: "10-15" },
  trapezio:    { serie: 3, ripetizioni: "12-15" },
  core:        { serie: 3, ripetizioni: "12-15" },
  // Piccoli: 2-3 serie, rep piu' alte
  bicipiti:    { serie: 2, ripetizioni: "10-15" },
  tricipiti:   { serie: 2, ripetizioni: "10-15" },
  avambracci:  { serie: 2, ripetizioni: "12-15" },
  polpacci:    { serie: 4, ripetizioni: "15-20" },  // polpacci = alta frequenza/rep
  adduttori:   { serie: 3, ripetizioni: "12-15" },
};
const DEFAULT_ACC_VOLUME = { serie: 3, ripetizioni: "10-15" };

function getAccessoryVolume(muscle: string): { serie: number; ripetizioni: string } {
  return ACCESSORY_VOLUME[muscle] ?? DEFAULT_ACC_VOLUME;
}

// ════════════════════════════════════════════════════════════
// CONSTANTS — Difficulty Mapping
// ════════════════════════════════════════════════════════════

const DIFFICULTY_ORDER = ["principiante", "intermedio", "avanzato"] as const;

/** Mappa difficolta' EN (DB) → IT (engine). Accetta entrambe le lingue. */
function normalizeDifficulty(d: string): string {
  const map: Record<string, string> = {
    beginner: "principiante", intermediate: "intermedio", advanced: "avanzato",
  };
  return map[d.toLowerCase()] ?? d.toLowerCase();
}

function difficultyDistance(a: string, b: string): number {
  const idxA = DIFFICULTY_ORDER.indexOf(normalizeDifficulty(a) as typeof DIFFICULTY_ORDER[number]);
  const idxB = DIFFICULTY_ORDER.indexOf(normalizeDifficulty(b) as typeof DIFFICULTY_ORDER[number]);
  if (idxA < 0 || idxB < 0) return 2;
  return Math.abs(idxA - idxB);
}

// ════════════════════════════════════════════════════════════
// CONSTANTS — Scorer Configuration
// ════════════════════════════════════════════════════════════

interface ScorerConfig {
  id: string;
  label: string;
  weight: number;
}

const SCORER_CONFIGS: ScorerConfig[] = [
  { id: "safety",               label: "Sicurezza",                  weight: 0.15 },
  { id: "muscle_match",         label: "Match Muscolare",            weight: 0.14 },
  { id: "pattern_match",        label: "Pattern Movimento",          weight: 0.13 },
  { id: "difficulty",           label: "Difficolta",                 weight: 0.10 },
  { id: "goal_alignment",       label: "Allineamento Obiettivo",     weight: 0.08 },
  { id: "strength_level",       label: "Livello Forza",              weight: 0.06 },
  { id: "recovery_fit",         label: "Compatibilita Recupero",     weight: 0.06 },
  { id: "slot_fit",              label: "Adeguatezza Slot",           weight: 0.09 },
  { id: "equipment_variety",    label: "Varieta Attrezzatura",       weight: 0.04 },
  { id: "uniqueness",           label: "Unicita",                    weight: 0.05 },
  { id: "plane_variety",        label: "Varieta Piani",              weight: 0.03 },
  { id: "chain_variety",        label: "Varieta Catena Cinetica",    weight: 0.03 },
  { id: "bilateral_balance",    label: "Equilibrio Bilaterale",      weight: 0.02 },
  { id: "contraction_variety",  label: "Varieta Contrazione",        weight: 0.02 },
];

// ════════════════════════════════════════════════════════════
// SCORER CONTEXT — stato sessione per scoring contestuale
// ════════════════════════════════════════════════════════════

interface ScorerContext {
  slot: SmartSlot;
  profile: ClientProfile | null;
  livello: FitnessLevel;
  obiettivo: string;
  /** Esercizi gia' assegnati in QUESTA sessione */
  sessionExercises: Exercise[];
  /** Esercizi gia' assegnati in TUTTE le sessioni del piano */
  allPlanExercises: Exercise[];
  /** Mappa attrezzatura gia' usata nella sessione */
  sessionEquipment: Set<string>;
  /** Piani di movimento gia' usati nella sessione */
  sessionPlanes: Record<string, number>;
  /** Catene cinetiche gia' usate nella sessione */
  sessionChains: Record<string, number>;
  /** Tipi contrazione gia' usati nella sessione */
  sessionContractions: Record<string, number>;
  /** Sessioni per settimana (per scoring recupero) */
  sessioniPerSettimana: number;
}

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

/** Parsa rep range tipo "8-12" → media 10, "5" → 5, "30s" → 0 */
export function parseAvgReps(rip: string): number {
  const match = rip.match(/^(\d+)\s*-\s*(\d+)$/);
  if (match) return (parseInt(match[1]) + parseInt(match[2])) / 2;
  const single = rip.match(/^(\d+)$/);
  if (single) return parseInt(single[1]);
  return 0;
}

/** Conta occorrenze di un valore in un Record */
function countInRecord(rec: Record<string, number>, key: string): number {
  return rec[key] ?? 0;
}

/** Mappa livello attivita' anamnesi → FitnessLevel approssimato */
function activityToLevel(livello: string | null): FitnessLevel | null {
  if (!livello) return null;
  const l = livello.toLowerCase();
  if (l === "sedentario" || l === "leggero") return "beginner";
  if (l === "moderato") return "intermedio";
  if (l === "intenso") return "avanzato";
  return null;
}

// ════════════════════════════════════════════════════════════
// 14 SCORER FUNCTIONS
// ════════════════════════════════════════════════════════════

type ScorerFn = (ex: Exercise, ctx: ScorerContext) => { score: number; reason: string };

/** 1. Safety — safe=1.0, modify=0.7, caution=0.5, avoid=0.1 (mai 0 → INFORM) */
function scoreSafety(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  if (!ctx.profile?.safetyMap) return { score: 0.5, reason: "Nessun dato safety" };
  const entry = ctx.profile.safetyMap[ex.id];
  if (!entry) return { score: 1.0, reason: "Nessuna controindicazione" };
  if (entry.severity === "avoid") return { score: 0.1, reason: `Da evitare: ${entry.conditions.map(c => c.nome).join(", ")}` };
  if (entry.severity === "modify") return { score: 0.7, reason: `Adattare: ${entry.conditions.map(c => c.nome).join(", ")}` };
  return { score: 0.5, reason: `Cautela: ${entry.conditions.map(c => c.nome).join(", ")}` };
}

/** 2. Muscle Match — coverage ratio (quanti target sono coperti dall'esercizio).
 * Se il pattern dell'esercizio corrisponde allo slot hint, il floor minimo e' 0.5
 * (l'esercizio e' comunque del tipo giusto anche se i suoi muscoli DB specifici
 * non coincidono esattamente con i target stimati — il DB e' piu' preciso dello schema). */
function scoreMuscleMatch(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const target = ctx.slot.muscoli_target;
  if (target.length === 0) return { score: 0.5, reason: "Nessun target muscolare" };
  const targetSet = new Set(target.map(m => normalizeMuscleGroup(m.toLowerCase())));
  const priSet = new Set(ex.muscoli_primari.map(m => normalizeMuscleGroup(m.toLowerCase())));
  const secSet = new Set(ex.muscoli_secondari.map(m => normalizeMuscleGroup(m.toLowerCase())));

  // Pattern match bonus: se pattern esatto, floor a 0.5
  const patternMatch = ctx.slot.pattern_hint === ex.pattern_movimento;

  let priHits = 0;
  for (const t of targetSet) if (priSet.has(t)) priHits++;
  const coverage = priHits / targetSet.size;
  if (coverage >= 0.5) return { score: 0.8 + coverage * 0.2, reason: `Match muscolare ${Math.round(coverage * 100)}%` };
  if (coverage > 0) return { score: Math.max(patternMatch ? 0.5 : 0, 0.3 + coverage * 0.4), reason: `Match parziale (${priHits}/${targetSet.size})` };
  // Prova sui secondari
  let secHits = 0;
  for (const t of targetSet) if (secSet.has(t)) secHits++;
  if (secHits > 0) return { score: Math.max(patternMatch ? 0.5 : 0, 0.2 + (secHits / targetSet.size) * 0.3), reason: `Match secondario (${secHits}/${targetSet.size})` };
  // Pattern esatto ma muscoli non nel target schema? Almeno 0.5
  if (patternMatch) return { score: 0.5, reason: `Pattern ${ctx.slot.pattern_hint} corretto` };
  return { score: 0.1, reason: "Nessun match muscolare" };
}

/** 3. Pattern Match — pattern esatto=1.0, stesso force_type=0.4, else=0.1 */
function scorePatternMatch(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const hint = ctx.slot.pattern_hint;
  if (!hint || hint === "warmup" || hint === "stretch" || hint === "mobility" || hint === "accessory") {
    return { score: 0.5, reason: "Pattern complementare" };
  }
  if (ex.pattern_movimento === hint) return { score: 1.0, reason: `Pattern ${hint} esatto` };
  // Stesso "tipo" di forza (push/pull)
  const hintType = hint.split("_")[0];
  const exType = ex.pattern_movimento.split("_")[0];
  if (hintType === exType) return { score: 0.4, reason: `Stesso tipo ${hintType}` };
  return { score: 0.1, reason: `Pattern diverso (${ex.pattern_movimento})` };
}

/** 4. Difficulty — match livello scheda vs difficolta esercizio */
function scoreDifficulty(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const targetDiff = ctx.livello === "beginner" ? "principiante" : ctx.livello;
  const dist = difficultyDistance(ex.difficolta, targetDiff);
  if (dist === 0) return { score: 1.0, reason: `Difficolta ${ex.difficolta} corretta` };
  if (dist === 1) return { score: 0.5, reason: `Difficolta adiacente (${ex.difficolta})` };
  return { score: 0.2, reason: `Difficolta distante (${ex.difficolta})` };
}

/** 5. Goal Alignment — rep range dell'esercizio allineato all'obiettivo scheda */
function scoreGoalAlignment(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const obj = ctx.obiettivo;
  const repMap: Record<string, string | null> = {
    forza: ex.rep_range_forza,
    ipertrofia: ex.rep_range_ipertrofia,
    resistenza: ex.rep_range_resistenza,
    dimagrimento: ex.rep_range_resistenza,
  };
  const range = repMap[obj];
  if (range) return { score: 1.0, reason: `Rep range ${obj} definito (${range})` };
  // Se ha almeno un rep range definito, mezzo punto
  if (ex.rep_range_forza || ex.rep_range_ipertrofia || ex.rep_range_resistenza) {
    return { score: 0.5, reason: "Rep range disponibile per altro obiettivo" };
  }
  return { score: 0.3, reason: "Nessun rep range specifico" };
}

/** 6. Strength Level — match livello forza client con difficolta reale */
function scoreStrengthLevel(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  if (!ctx.profile?.strengthLevel) return { score: 0.5, reason: "Livello forza non disponibile" };
  const clientLevel = ctx.profile.strengthLevel;
  const dist = difficultyDistance(
    ex.difficolta,
    clientLevel === "beginner" ? "principiante" : clientLevel,
  );
  if (dist === 0) return { score: 1.0, reason: "Adeguato al livello di forza" };
  if (dist === 1) return { score: 0.6, reason: "Leggermente fuori livello" };
  return { score: 0.3, reason: "Significativamente fuori livello" };
}

/** 7. Recovery Fit — ore_recupero rispettate (solo indicativo nella generazione) */
function scoreRecoveryFit(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  if (ctx.sessioniPerSettimana <= 0) return { score: 0.5, reason: "Sessioni/settimana non valide" };
  const oreTraSessioni = (7 * 24) / ctx.sessioniPerSettimana;
  if (ex.ore_recupero <= oreTraSessioni) return { score: 1.0, reason: `Recupero ${ex.ore_recupero}h ok` };
  if (ex.ore_recupero <= oreTraSessioni * 1.5) return { score: 0.6, reason: `Recupero ${ex.ore_recupero}h accettabile` };
  return { score: 0.3, reason: `Recupero ${ex.ore_recupero}h lungo` };
}

/** 8. Slot Fit — slot-type-aware: compound slots vogliono compound, isolation slots vogliono isolation */
function scoreSlotFit(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const cat = ex.categoria;
  const slotType = ctx.slot.slotType;

  // Warmup/stretching: nessuna preferenza compound/isolation
  if (!slotType) return { score: 0.5, reason: "Slot senza tipo (warmup/stretching)" };

  // Isolation slots: preferiscono isolation exercises
  if (slotType === "isolation_target" || slotType === "isolation_accessory") {
    if (cat === "isolation") return { score: 1.0, reason: "Isolation per slot isolamento" };
    if (cat === "bodyweight") return { score: 0.6, reason: "Bodyweight per slot isolamento" };
    if (cat === "compound") return { score: 0.15, reason: "Compound per slot isolamento (penalizzato)" };
    return { score: 0.5, reason: `Categoria ${cat}` };
  }

  // Compound slots (default): preferiscono compound exercises
  if (cat === "compound") return { score: 1.0, reason: "Compound multiarticolare" };
  if (cat === "bodyweight") return { score: 0.7, reason: "Bodyweight funzionale" };
  if (cat === "isolation") return { score: 0.3, reason: "Isolation per slot compound" };
  return { score: 0.5, reason: `Categoria ${cat}` };
}

/** 9. Equipment Variety — penalizza stessa attrezzatura consecutiva */
function scoreEquipmentVariety(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  if (ctx.sessionEquipment.size === 0) return { score: 0.5, reason: "Primo esercizio" };
  if (ctx.sessionEquipment.has(ex.attrezzatura)) {
    return { score: 0.3, reason: `${ex.attrezzatura} gia usata` };
  }
  return { score: 1.0, reason: `Nuova attrezzatura: ${ex.attrezzatura}` };
}

/** 10. Uniqueness — non usato altrove=1.0, altra sessione=0.3, stessa=0.0 */
function scoreUniqueness(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const inSession = ctx.sessionExercises.some(e => e.id === ex.id);
  if (inSession) return { score: 0.0, reason: "Gia presente in sessione" };
  const inPlan = ctx.allPlanExercises.some(e => e.id === ex.id);
  if (inPlan) return { score: 0.3, reason: "Gia in altra sessione" };
  return { score: 1.0, reason: "Esercizio unico" };
}

/** 11. Plane Variety — premia piani di movimento sotto-rappresentati */
function scorePlaneVariety(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const plane = ex.piano_movimento;
  if (!plane) return { score: 0.5, reason: "Piano non specificato" };
  const count = countInRecord(ctx.sessionPlanes, plane);
  if (count === 0) return { score: 1.0, reason: `Nuovo piano: ${plane}` };
  if (count <= 2) return { score: 0.6, reason: `Piano ${plane} (${count}x)` };
  return { score: 0.3, reason: `Piano ${plane} sovra-rappresentato (${count}x)` };
}

/** 12. Chain Variety — alterna catena cinetica open/closed */
function scoreChainVariety(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const chain = ex.catena_cinetica;
  if (!chain) return { score: 0.5, reason: "Catena non specificata" };
  const count = countInRecord(ctx.sessionChains, chain);
  const otherCount = Object.values(ctx.sessionChains).reduce((s, v) => s + v, 0) - count;
  if (count <= otherCount) return { score: 0.8, reason: `Catena ${chain} bilanciata` };
  return { score: 0.4, reason: `Catena ${chain} dominante` };
}

/** 13. Bilateral Balance — unilaterale bonus se deficit simmetria client */
function scoreBilateralBalance(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const hasDeficits = ctx.profile?.symmetryDeficits && ctx.profile.symmetryDeficits.length > 0;
  if (!hasDeficits) return { score: 0.5, reason: "Nessun dato simmetria" };
  const isUnilateral = ex.lateral_pattern === "unilaterale" || ex.lateral_pattern === "unilateral";
  if (isUnilateral) return { score: 1.0, reason: "Unilaterale — corregge asimmetria" };
  return { score: 0.4, reason: "Bilaterale — non corregge asimmetria" };
}

/** 14. Contraction Variety — varia tipi contrazione nella sessione */
function scoreContractionVariety(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const tipo = ex.tipo_contrazione;
  if (!tipo) return { score: 0.5, reason: "Contrazione non specificata" };
  const count = countInRecord(ctx.sessionContractions, tipo);
  if (count === 0) return { score: 1.0, reason: `Nuovo tipo: ${tipo}` };
  if (count <= 2) return { score: 0.6, reason: `Tipo ${tipo} (${count}x)` };
  return { score: 0.3, reason: `Tipo ${tipo} sovra-rappresentato (${count}x)` };
}

/** Registry scorer functions */
const SCORER_FNS: Record<string, ScorerFn> = {
  safety: scoreSafety,
  muscle_match: scoreMuscleMatch,
  pattern_match: scorePatternMatch,
  difficulty: scoreDifficulty,
  goal_alignment: scoreGoalAlignment,
  strength_level: scoreStrengthLevel,
  recovery_fit: scoreRecoveryFit,
  slot_fit: scoreSlotFit,
  equipment_variety: scoreEquipmentVariety,
  uniqueness: scoreUniqueness,
  plane_variety: scorePlaneVariety,
  chain_variety: scoreChainVariety,
  bilateral_balance: scoreBilateralBalance,
  contraction_variety: scoreContractionVariety,
};

// ════════════════════════════════════════════════════════════
// SCORING ORCHESTRATOR
// ════════════════════════════════════════════════════════════

/**
 * Calcola lo score per tutti gli esercizi rispetto a uno slot.
 * Ritorna array ordinato per score decrescente.
 */
export function scoreExercisesForSlot(
  exercises: Exercise[],
  slot: SmartSlot,
  profile: ClientProfile | null,
  livello: FitnessLevel,
  obiettivo: string,
  sessionExercises: Exercise[],
  allPlanExercises: Exercise[],
  sessioniPerSettimana: number = 4,
): ExerciseScore[] {
  // Costruisci contesto sessione
  const sessionEquipment = new Set(sessionExercises.map(e => e.attrezzatura));
  const sessionPlanes: Record<string, number> = {};
  const sessionChains: Record<string, number> = {};
  const sessionContractions: Record<string, number> = {};

  for (const e of sessionExercises) {
    if (e.piano_movimento) sessionPlanes[e.piano_movimento] = (sessionPlanes[e.piano_movimento] ?? 0) + 1;
    if (e.catena_cinetica) sessionChains[e.catena_cinetica] = (sessionChains[e.catena_cinetica] ?? 0) + 1;
    if (e.tipo_contrazione) sessionContractions[e.tipo_contrazione] = (sessionContractions[e.tipo_contrazione] ?? 0) + 1;
  }

  const ctx: ScorerContext = {
    slot,
    profile,
    livello,
    obiettivo,
    sessionExercises,
    allPlanExercises,
    sessionEquipment,
    sessionPlanes,
    sessionChains,
    sessionContractions,
    sessioniPerSettimana,
  };

  const scores: ExerciseScore[] = exercises.map(ex => {
    const dimensions: ScoreDimension[] = SCORER_CONFIGS.map(cfg => {
      const fn = SCORER_FNS[cfg.id];
      const { score, reason } = fn(ex, ctx);
      return { id: cfg.id, label: cfg.label, score, weight: cfg.weight, reason };
    });

    const totalWeight = dimensions.reduce((sum, d) => sum + d.weight, 0);
    const weightedSum = dimensions.reduce((sum, d) => sum + d.score * d.weight, 0);
    const totalScore = Math.round((weightedSum / totalWeight) * 100);

    const safetyEntry = profile?.safetyMap?.[ex.id] ?? null;

    return {
      exerciseId: ex.id,
      exerciseName: ex.nome,
      totalScore,
      dimensions,
      safetySeverity: safetyEntry?.severity ?? null,
    };
  });

  // Ordina per score decrescente
  scores.sort((a, b) => b.totalScore - a.totalScore);
  return scores;
}

// ════════════════════════════════════════════════════════════
// FITNESS LEVEL ASSESSOR
// ════════════════════════════════════════════════════════════

/**
 * Determina il livello fitness del client da dati disponibili.
 * Combina livello attivita' (anamnesi) + strength ratios (NSCA).
 */
export function assessFitnessLevel(profile: ClientProfile | null): FitnessLevel {
  if (!profile) return "beginner";

  // Livello da strength ratios (piu' affidabile)
  // StrengthRatio.level puo' essere IT o EN: mappiamo entrambi
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

  // Fallback: livello attivita' anamnesi
  const fromActivity = activityToLevel(profile.livelloAttivita);
  if (fromActivity) return fromActivity;

  return "beginner";
}

// ════════════════════════════════════════════════════════════
// SPLIT DETERMINATION
// ════════════════════════════════════════════════════════════

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

// ════════════════════════════════════════════════════════════
// SMART PLAN GENERATOR (Blueprint-driven)
// ════════════════════════════════════════════════════════════

/**
 * Genera una struttura SmartPlan completa con slot tipizzati per ogni sessione.
 * Blueprint-driven: ogni slot ha un tipo funzionale (compound_primary → isolation_accessory)
 * che determina volume (serie/rep/riposo) e strategia di selezione esercizio.
 *
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

    // ── Avviamento: 2-3 slot (auto-generati) ──
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

    // ── Principale: slot dal blueprint con volume per slot type × obiettivo ──
    for (const bs of sb.slots) {
      const vol = getSlotVolume(bs.type, obiettivo);
      const roles = patternToMuscleRoles(bs.pattern_hint);

      // Isolation slots: target = muscolo specifico dello slot
      // Compound slots: target = muscoli primari del pattern
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

    // ── Stretching: 2-3 slot mirati ai muscoli lavorati nella sessione ──
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

    // Durata stimata (minuti)
    const durataMinuti = warmupCount * 5 + sb.slots.length * 7 + stretchCount * 2;

    return {
      nome_sessione: sb.nome,
      focus_muscolare: sb.focus,
      durata_minuti: durataMinuti,
      slots,
    };
  });

  // ── Safety-net validation: verifica copertura dal blueprint ──
  // I blueprint sono pre-bilanciati, ma se qualche muscolo ha zero copertura
  // aggiungiamo max 1 slot correttivo per sessione.
  const blueprintSets = computeBlueprintCoverage(blueprint, obiettivo);
  // Per-muscle tiered targets: muscoli piccoli hanno soglia piu' bassa.
  // Threshold 40%: aggiunge slot correttivo se copertura stimata < 40% del target tiered.
  const deficits = MUSCLE_GROUPS.filter(m => {
    const mt = getMuscleTarget(m, livello, sessioniPerSettimana);
    return (blueprintSets.get(m) ?? 0) < mt.min * 0.4;
  });

  if (deficits.length > 0) {
    deficits.sort((a, b) => (blueprintSets.get(a) ?? 0) - (blueprintSets.get(b) ?? 0));
    for (const muscle of deficits.slice(0, sessioni.length)) {
      // Trova sessione con meno slot (piu' spazio)
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
function computeBlueprintCoverage(
  blueprint: SplitBlueprint,
  obiettivo: string,
): Map<string, number> {
  const sets = new Map<string, number>();

  for (const session of blueprint.sessioni) {
    for (const slot of session.slots) {
      const vol = getSlotVolume(slot.type, obiettivo);
      const serie = vol.serie;

      if (slot.type === "isolation_target" || slot.type === "isolation_accessory") {
        // Isolation: conta solo il muscolo target
        const group = normalizeMuscleGroup(slot.targetMuscle.toLowerCase());
        sets.set(group, (sets.get(group) ?? 0) + serie);
      } else {
        // Compound: primari full credit, secondari diluted
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

/**
 * Riempie gli slot di un SmartPlan con esercizi ottimali.
 * Ritorna mappa sessionIndex → slotIndex → ExerciseScore[] (top N).
 *
 * Architettura a 2 fasi:
 *   Fase 1 — Greedy fill: assegna l'esercizio con score 14D piu' alto per ogni slot.
 *   Fase 2 — Coverage optimization: calcola copertura muscolare REALE dagli esercizi
 *     assegnati, identifica deficit, e prova swap con alternative (top 5) che migliorano
 *     la copertura globale senza degradare troppo lo score individuale.
 */
export function fillSmartPlan(
  plan: SmartPlan,
  exercises: Exercise[],
  profile: ClientProfile | null,
): Map<number, Map<number, ExerciseScore[]>> {
  const result = new Map<number, Map<number, ExerciseScore[]>>();
  const allAssigned: Exercise[] = [];
  const livello = plan.livello as FitnessLevel;

  // Track assigned exercise per slot: [sessionIdx][slotIdx] = Exercise
  const assigned: (Exercise | null)[][] = [];

  // ── Fase 1: Greedy fill ──
  for (let si = 0; si < plan.sessioni.length; si++) {
    const session = plan.sessioni[si];
    const sessionMap = new Map<number, ExerciseScore[]>();
    const sessionAssigned: Exercise[] = [];
    assigned[si] = [];

    for (let sli = 0; sli < session.slots.length; sli++) {
      const slot = session.slots[sli];

      const sectionCats = SECTION_CATEGORIES[slot.sezione];
      let candidates = exercises.filter(e => sectionCats.includes(e.categoria));

      // ── Pre-filter per slot type: hard gate, non soft score ──
      // Senza questo, compound con pattern_match alto (0.13) battono isolation
      // per slot isolation perche' scoreSlotFit (0.09) e' troppo debole.
      if (slot.slotType === "isolation_target" || slot.slotType === "isolation_accessory") {
        const preferred = candidates.filter(e => e.categoria === "isolation" || e.categoria === "bodyweight");
        if (preferred.length >= 3) candidates = preferred;
      } else if (slot.slotType === "compound_primary" || slot.slotType === "compound_secondary") {
        const preferred = candidates.filter(e => e.categoria === "compound" || e.categoria === "bodyweight");
        if (preferred.length >= 3) candidates = preferred;

        // ── Pattern gate: impedisce gambe in upper body, pull in push day ──
        // pattern_match (0.13) da solo non basta vs altri scorer combinati.
        // Senza questo gate, un barbell row puo' battere una bench press
        // in uno slot push_h se ha score migliore su safety/equipment/uniqueness.
        const hint = slot.pattern_hint;
        if (hint && !["warmup", "stretch", "mobility", "accessory"].includes(hint)) {
          // 1. Prova pattern esatto (push_h → solo esercizi push_h)
          const exact = candidates.filter(e => e.pattern_movimento === hint);
          if (exact.length >= 2) {
            candidates = exact;
          } else {
            // 2. Fallback: stessa famiglia di movimento
            //    push_h/push_v condividono "push", pull_h/pull_v condividono "pull"
            //    squat/hinge/core/carry/rotation restano isolati (no "_" o famiglia unica)
            const family = hint.split("_")[0];
            const familyMatch = candidates.filter(e => {
              const exFamily = e.pattern_movimento.split("_")[0];
              return exFamily === family;
            });
            if (familyMatch.length >= 2) candidates = familyMatch;
          }
        }
      }

      const scores = scoreExercisesForSlot(
        candidates,
        slot,
        profile,
        livello,
        plan.obiettivo,
        sessionAssigned,
        allAssigned,
        plan.sessioni_per_settimana,
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

  // ── Fase 2: Coverage-aware swap optimization ──
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

            // Skip se gia' assegnato nella stessa sessione
            const inSession = assigned[si].some((e, idx) => idx !== sli && e?.id === altEx.id);
            if (inSession) continue;

            // Swap
            const oldEx = assigned[si][sli]!;
            assigned[si][sli] = altEx;
            const oldIdx = allAssigned.findIndex(e => e.id === oldEx.id);
            if (oldIdx >= 0) allAssigned[oldIdx] = altEx;

            // Riordina scores per riflettere lo swap
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

/** Calcola copertura muscolare reale dagli esercizi effettivamente assegnati.
 * Credito: primario 1.0 * serie, secondario diluted (budget 1.0/N, max 0.35). */
function computeRealCoverage(
  assigned: (Exercise | null)[][],
  plan: SmartPlan,
): Map<string, number> {
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

/** Verifica se un esercizio copre un gruppo muscolare (primario o secondario) */
function exerciseCoversGroup(ex: Exercise, group: string): boolean {
  const normalizedGroup = normalizeMuscleGroup(group.toLowerCase());
  for (const m of ex.muscoli_primari) {
    if (normalizeMuscleGroup(m.toLowerCase()) === normalizedGroup) return true;
  }
  for (const m of ex.muscoli_secondari) {
    if (normalizeMuscleGroup(m.toLowerCase()) === normalizedGroup) return true;
  }
  return false;
}

// ════════════════════════════════════════════════════════════
// MUSCLE COVERAGE ANALYSIS
// ════════════════════════════════════════════════════════════

/** Gruppi muscolari principali per analisi copertura */
const MUSCLE_GROUPS = [
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

function normalizeMuscleGroup(name: string): string {
  const lower = name.toLowerCase();
  return MUSCLE_GROUP_ALIASES[lower] ?? lower;
}

/**
 * Analizza la copertura muscolare di un set di sessioni.
 * Conta set/muscolo/settimana con credit: primario=1.0, secondario=max 0.35.
 * Target per-muscolo con tier (grandi 1.0, medi 0.7, piccoli 0.5, accessori 0.35).
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

      const sezione = getSectionForCategory(exercise.categoria);
      if (sezione !== "principale") continue; // Solo sezione principale conta per volume

      for (const m of exercise.muscoli_primari) {
        const group = normalizeMuscleGroup(m);
        setCounts[group] = (setCounts[group] ?? 0) + ex.serie * 1.0;
      }
      // Credito secondario diluted: budget di 1.0 set-equivalente distribuito
      // tra tutti i secondari, max 0.35 ciascuno. Evita che muscoli "hub"
      // (core, spalle, dorsali, glutei) — listati come secondari su quasi ogni
      // compound — accumulino credito irrealistico (30-45 set/sett).
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

// ════════════════════════════════════════════════════════════
// VOLUME ANALYSIS
// ════════════════════════════════════════════════════════════

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

// ════════════════════════════════════════════════════════════
// BIOMECHANICAL VARIETY
// ════════════════════════════════════════════════════════════

/** Analizza distribuzione piani/catene/contrazioni nella scheda */
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

// ════════════════════════════════════════════════════════════
// RECOVERY ANALYSIS
// ════════════════════════════════════════════════════════════

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

    // Raccogli muscoli + ore_recupero per sessione A
    const muscoliA = new Map<string, number>(); // muscolo → max ore_recupero
    for (const ex of sessionA.esercizi) {
      const exercise = exerciseMap.get(ex.id_esercizio);
      if (!exercise) continue;
      for (const m of exercise.muscoli_primari) {
        const group = normalizeMuscleGroup(m);
        const current = muscoliA.get(group) ?? 0;
        muscoliA.set(group, Math.max(current, exercise.ore_recupero));
      }
    }

    // Trova overlap con sessione B
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

// ════════════════════════════════════════════════════════════
// SAFETY ANALYSIS
// ════════════════════════════════════════════════════════════

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
      else safe += 0.5; // caution
    }
  }

  return total > 0 ? Math.round((safe / total) * 100) : 100;
}

export interface SafetyBreakdown {
  avoid: number;
  modify: number;
  caution: number;
  hasConditions: boolean;
}

/** Conta esercizi per severita' safety — usato dal SmartAnalysisPanel per display actionable */
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

// ════════════════════════════════════════════════════════════
// SMART ANALYSIS — Orchestratore
// ════════════════════════════════════════════════════════════

/**
 * Computa l'analisi SMART completa di una scheda.
 * Usato dal SmartAnalysisPanel nel builder.
 */
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

// ════════════════════════════════════════════════════════════
// HELPERS — Pattern ↔ Muscoli/Label
// ════════════════════════════════════════════════════════════

/**
 * Mappa pattern → muscoli con ruolo differenziato (primari vs secondari).
 * I primari sono i motori del movimento. I secondari sono sinergici/stabilizzatori.
 * Questa distinzione e' fondamentale per:
 *   - computeBlueprintCoverage: crediti differenziati (1.0 vs diluted)
 *   - slot muscoli_target: solo primari (migliora scoring esercizi)
 *   - stretching: tutti i muscoli lavorati (primari + secondari)
 *
 * NOTA: Core e' RIMOSSO dai secondari di squat/hinge — e' stabilizzatore,
 * il suo credito reale viene dai pattern "core"/"rotation"/"carry" dove e' primario.
 * Stessa logica: spalle rimosse da push_h (primario = petto), petto da push_v,
 * trapezio da pull_v. Previene inflazione hub muscles.
 */
function patternToMuscleRoles(pattern: string): { primari: string[]; secondari: string[] } {
  const map: Record<string, { primari: string[]; secondari: string[] }> = {
    // Compound patterns
    squat:         { primari: ["quadricipiti"],                  secondari: ["glutei", "femorali", "adduttori"] },
    hinge:         { primari: ["femorali", "glutei"],           secondari: ["dorsali"] },
    push_h:        { primari: ["petto"],                        secondari: ["tricipiti", "spalle"] },
    push_v:        { primari: ["spalle"],                       secondari: ["tricipiti"] },
    pull_h:        { primari: ["dorsali"],                      secondari: ["bicipiti", "trapezio"] },
    pull_v:        { primari: ["dorsali"],                      secondari: ["bicipiti"] },
    core:          { primari: ["core"],                         secondari: [] },
    rotation:      { primari: ["core"],                         secondari: ["spalle"] },
    carry:         { primari: ["core", "avambracci"],           secondari: ["trapezio"] },
    // Isolation patterns
    curl:          { primari: ["bicipiti"],                     secondari: ["avambracci"] },
    extension_tri: { primari: ["tricipiti"],                    secondari: [] },
    lateral_raise: { primari: ["spalle"],                       secondari: [] },
    face_pull:     { primari: ["spalle"],                       secondari: ["trapezio"] },
    calf_raise:    { primari: ["polpacci"],                     secondari: [] },
    leg_curl:      { primari: ["femorali"],                     secondari: [] },
    leg_extension: { primari: ["quadricipiti"],                 secondari: [] },
    hip_thrust:    { primari: ["glutei"],                       secondari: ["femorali"] },
    adductor:      { primari: ["adduttori"],                    secondari: [] },
    // Non-training
    warmup:        { primari: [],                               secondari: [] },
    stretch:       { primari: [],                               secondari: [] },
    mobility:      { primari: [],                               secondari: [] },
  };
  return map[pattern] ?? { primari: [], secondari: [] };
}

function patternToLabel(pattern: string): string {
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

function capitalizeFirst(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ════════════════════════════════════════════════════════════
// PROFILE BUILDER — Utility per costruire ClientProfile
// ════════════════════════════════════════════════════════════

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
    measurements: null, // Arricchito dal hook se dati disponibili
    strengthRatios,
    goals,
    symmetryDeficits,
    strengthLevel: null, // Calcolato dopo
  };

  profile.strengthLevel = assessFitnessLevel(profile);
  return profile;
}

