// src/lib/smart-programming/types.ts
/**
 * Tipi e interfacce per il motore di Programmazione SMART.
 * Mirror delle strutture backend dove applicabile.
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

// ── Fitness Level ──

export type FitnessLevel = "beginner" | "intermedio" | "avanzato";

// ── Profilo Client Aggregato ──

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

// ── Scoring ──

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

// ── Smart Plan ──

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

// ── Analisi ──

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

export interface SafetyBreakdown {
  avoid: number;
  modify: number;
  caution: number;
  hasConditions: boolean;
}

// ── Scorer Context ──

export interface ScorerContext {
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

export interface ScorerConfig {
  id: string;
  label: string;
  weight: number;
}

export type ScorerFn = (ex: Exercise, ctx: ScorerContext) => { score: number; reason: string };
