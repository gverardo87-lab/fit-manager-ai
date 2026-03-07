// src/lib/smart-programming/index.ts
/**
 * Re-export pubblico del motore Smart Programming.
 * Tutti i consumer importano da "@/lib/smart-programming" — questo file
 * garantisce backward compatibility con il vecchio monolite.
 */

// Types
export type {
  FitnessLevel,
  ClientProfile,
  ScoreDimension,
  ExerciseScore,
  SlotType,
  SmartSlot,
  SmartSession,
  SmartPlan,
  BlueprintSlot,
  SessionBlueprint,
  SplitBlueprint,
  CoverageStatus,
  MuscleCoverage,
  VolumeAnalysis,
  BiomechanicalVariety,
  RecoveryConflict,
  SmartAnalysis,
  SafetyBreakdown,
  ScorerContext,
  ScorerConfig,
  ScorerFn,
} from "./types";

// Helpers
export {
  parseAvgReps,
  assessFitnessLevel,
  buildClientProfile,
  normalizeMuscleGroup,
  patternToMuscleRoles,
  MUSCLE_GROUPS,
} from "./helpers";

// Scorers
export { scoreExercisesForSlot } from "./scorers";

// Plan generation
export { generateSmartPlan, fillSmartPlan, determineSplit } from "./plan-generator";

// Analysis
export {
  computeMuscleCoverage,
  computeVolumeAnalysis,
  analyzeBiomechanics,
  analyzeRecovery,
  computeSafetyBreakdown,
  computeSmartAnalysis,
} from "./analysis";
