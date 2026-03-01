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
  safetySeverity: "avoid" | "caution" | null;
}

// ════════════════════════════════════════════════════════════
// TYPES — Smart Plan
// ════════════════════════════════════════════════════════════

export interface SmartSlot {
  sezione: TemplateSection;
  pattern_hint: string;
  muscoli_target: string[];
  label: string;
  serie: number;
  ripetizioni: string;
  tempo_riposo_sec: number;
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

/** Set/muscolo/settimana target per livello (Krieger 2010, Schoenfeld 2017) */
const VOLUME_TARGETS: Record<FitnessLevel, { min: number; max: number }> = {
  beginner:   { min: 10, max: 12 },
  intermedio: { min: 14, max: 18 },
  avanzato:   { min: 18, max: 25 },
};

/** Set totali/settimana per livello */
const TOTAL_VOLUME_TARGETS: Record<FitnessLevel, { min: number; max: number }> = {
  beginner:   { min: 30, max: 50 },
  intermedio: { min: 50, max: 80 },
  avanzato:   { min: 70, max: 120 },
};

// ════════════════════════════════════════════════════════════
// CONSTANTS — Split Patterns
// ════════════════════════════════════════════════════════════

interface SplitPattern {
  sessioni: Array<{ nome: string; focus: string; patterns: string[] }>;
}

const SPLIT_PATTERNS: Record<number, Record<FitnessLevel, SplitPattern>> = {
  // ── 2 sessioni: Full Body A/B ──
  2: {
    beginner: { sessioni: [
      { nome: "Full Body A", focus: "quadricipiti, petto, dorsali", patterns: ["squat", "push_h", "pull_h", "hinge", "core"] },
      { nome: "Full Body B", focus: "glutei, spalle, braccia", patterns: ["hinge", "push_v", "pull_v", "squat", "core"] },
    ]},
    intermedio: { sessioni: [
      { nome: "Full Body A", focus: "quadricipiti, petto, dorsali", patterns: ["squat", "push_h", "pull_h", "hinge", "push_v", "core"] },
      { nome: "Full Body B", focus: "glutei, spalle, braccia", patterns: ["hinge", "push_v", "pull_v", "squat", "pull_h", "core"] },
    ]},
    avanzato: { sessioni: [
      { nome: "Full Body A", focus: "quadricipiti, petto, dorsali", patterns: ["squat", "push_h", "pull_h", "hinge", "push_v", "core"] },
      { nome: "Full Body B", focus: "glutei, spalle, braccia", patterns: ["hinge", "push_v", "pull_v", "squat", "pull_h", "core"] },
    ]},
  },
  // ── 3 sessioni: Full Body (beginner) / PPL (intermedio+) ──
  3: {
    beginner: { sessioni: [
      { nome: "Full Body A", focus: "quadricipiti, petto", patterns: ["squat", "push_h", "pull_h", "core"] },
      { nome: "Full Body B", focus: "glutei, dorsali", patterns: ["hinge", "pull_v", "push_v", "core"] },
      { nome: "Full Body C", focus: "spalle, braccia, core", patterns: ["squat", "pull_h", "push_v", "rotation"] },
    ]},
    intermedio: { sessioni: [
      { nome: "Push", focus: "petto, spalle, tricipiti", patterns: ["push_h", "push_v", "push_h", "push_v"] },
      { nome: "Pull", focus: "dorsali, trapezio, bicipiti", patterns: ["pull_v", "pull_h", "pull_v", "pull_h"] },
      { nome: "Legs", focus: "quadricipiti, glutei, core", patterns: ["squat", "hinge", "squat", "hinge", "core"] },
    ]},
    avanzato: { sessioni: [
      { nome: "Push", focus: "petto, spalle, tricipiti", patterns: ["push_h", "push_v", "push_h", "push_v", "push_h"] },
      { nome: "Pull", focus: "dorsali, trapezio, bicipiti", patterns: ["pull_v", "pull_h", "pull_v", "pull_h", "pull_h"] },
      { nome: "Legs", focus: "quadricipiti, glutei, core", patterns: ["squat", "hinge", "squat", "hinge", "core"] },
    ]},
  },
  // ── 4 sessioni: Upper/Lower x2 (bilanciato push/pull per Upper, squat/hinge per Lower) ──
  4: {
    beginner: { sessioni: [
      { nome: "Upper A", focus: "petto, dorsali, spalle", patterns: ["push_h", "pull_h", "push_v", "pull_v"] },
      { nome: "Lower A", focus: "quadricipiti, glutei", patterns: ["squat", "hinge", "squat", "core"] },
      { nome: "Upper B", focus: "dorsali, petto, braccia", patterns: ["pull_h", "push_h", "pull_v", "push_v"] },
      { nome: "Lower B", focus: "glutei, femorali, core", patterns: ["hinge", "squat", "hinge", "core"] },
    ]},
    intermedio: { sessioni: [
      { nome: "Upper A", focus: "petto, dorsali, spalle", patterns: ["push_h", "pull_h", "push_v", "pull_v", "core"] },
      { nome: "Lower A", focus: "quadricipiti, glutei, femorali", patterns: ["squat", "hinge", "squat", "hinge", "core"] },
      { nome: "Upper B", focus: "dorsali, petto, braccia", patterns: ["pull_h", "push_h", "pull_v", "push_v", "core"] },
      { nome: "Lower B", focus: "glutei, femorali, quadricipiti", patterns: ["hinge", "squat", "hinge", "squat", "core"] },
    ]},
    avanzato: { sessioni: [
      { nome: "Upper A", focus: "petto, dorsali, spalle", patterns: ["push_h", "pull_h", "push_v", "pull_v", "push_h", "core"] },
      { nome: "Lower A", focus: "quadricipiti, glutei, femorali", patterns: ["squat", "hinge", "squat", "hinge", "squat", "core"] },
      { nome: "Upper B", focus: "dorsali, petto, braccia", patterns: ["pull_h", "push_h", "pull_v", "push_v", "pull_h", "core"] },
      { nome: "Lower B", focus: "glutei, femorali, core", patterns: ["hinge", "squat", "hinge", "squat", "hinge", "core"] },
    ]},
  },
  // ── 5 sessioni: Upper/Lower x2 + Full Body ──
  5: {
    beginner: { sessioni: [
      { nome: "Upper A", focus: "petto, dorsali", patterns: ["push_h", "pull_h", "push_v", "pull_v"] },
      { nome: "Lower A", focus: "quadricipiti, glutei", patterns: ["squat", "hinge", "squat", "core"] },
      { nome: "Upper B", focus: "dorsali, spalle", patterns: ["pull_h", "push_h", "pull_v", "push_v"] },
      { nome: "Lower B", focus: "glutei, femorali", patterns: ["hinge", "squat", "hinge", "core"] },
      { nome: "Full Body", focus: "recupero attivo, core", patterns: ["squat", "push_h", "pull_v", "hinge", "core"] },
    ]},
    intermedio: { sessioni: [
      { nome: "Upper A", focus: "petto, dorsali, spalle", patterns: ["push_h", "pull_h", "push_v", "pull_v", "core"] },
      { nome: "Lower A", focus: "quadricipiti, glutei", patterns: ["squat", "hinge", "squat", "hinge", "core"] },
      { nome: "Upper B", focus: "dorsali, petto, braccia", patterns: ["pull_h", "push_h", "pull_v", "push_v", "core"] },
      { nome: "Lower B", focus: "glutei, femorali", patterns: ["hinge", "squat", "hinge", "squat", "core"] },
      { nome: "Full Body", focus: "compenso, core", patterns: ["squat", "push_v", "pull_h", "hinge", "core"] },
    ]},
    avanzato: { sessioni: [
      { nome: "Upper A", focus: "petto, dorsali, spalle", patterns: ["push_h", "pull_h", "push_v", "pull_v", "push_h", "core"] },
      { nome: "Lower A", focus: "quadricipiti, glutei", patterns: ["squat", "hinge", "squat", "hinge", "squat", "core"] },
      { nome: "Upper B", focus: "dorsali, petto, braccia", patterns: ["pull_h", "push_h", "pull_v", "push_v", "pull_h", "core"] },
      { nome: "Lower B", focus: "glutei, femorali", patterns: ["hinge", "squat", "hinge", "squat", "hinge", "core"] },
      { nome: "Full Body", focus: "volume extra", patterns: ["squat", "push_h", "pull_v", "hinge", "push_v", "core"] },
    ]},
  },
  // ── 6 sessioni: PPL x2 (bilanciato push_h/push_v, pull_h/pull_v, squat/hinge) ──
  6: {
    beginner: { sessioni: [
      { nome: "Push A", focus: "petto, spalle, tricipiti", patterns: ["push_h", "push_v", "push_h", "push_v"] },
      { nome: "Pull A", focus: "dorsali, trapezio, bicipiti", patterns: ["pull_v", "pull_h", "pull_v", "pull_h"] },
      { nome: "Legs A", focus: "quadricipiti, glutei", patterns: ["squat", "hinge", "squat", "core"] },
      { nome: "Push B", focus: "petto, spalle, tricipiti", patterns: ["push_h", "push_v", "push_h", "push_v"] },
      { nome: "Pull B", focus: "dorsali, trapezio, bicipiti", patterns: ["pull_h", "pull_v", "pull_h", "pull_v"] },
      { nome: "Legs B", focus: "glutei, femorali, core", patterns: ["hinge", "squat", "hinge", "core"] },
    ]},
    intermedio: { sessioni: [
      { nome: "Push A — Forza", focus: "petto, spalle, tricipiti", patterns: ["push_h", "push_v", "push_h", "push_v", "push_h"] },
      { nome: "Pull A — Forza", focus: "dorsali, trapezio, bicipiti", patterns: ["pull_v", "pull_h", "pull_v", "pull_h", "pull_h"] },
      { nome: "Legs A — Quad", focus: "quadricipiti, glutei, core", patterns: ["squat", "hinge", "squat", "hinge", "core"] },
      { nome: "Push B — Ipertrofia", focus: "petto, spalle, tricipiti", patterns: ["push_h", "push_v", "push_h", "push_v", "push_h"] },
      { nome: "Pull B — Ipertrofia", focus: "dorsali, trapezio, bicipiti", patterns: ["pull_h", "pull_v", "pull_h", "pull_v", "pull_h"] },
      { nome: "Legs B — Hip", focus: "glutei, femorali, core", patterns: ["hinge", "squat", "hinge", "squat", "core"] },
    ]},
    avanzato: { sessioni: [
      { nome: "Push A — Forza", focus: "petto, spalle, tricipiti", patterns: ["push_h", "push_v", "push_h", "push_v", "push_h", "push_h"] },
      { nome: "Pull A — Forza", focus: "dorsali, trapezio, bicipiti", patterns: ["pull_v", "pull_h", "pull_v", "pull_h", "pull_h", "pull_h"] },
      { nome: "Legs A — Quad", focus: "quadricipiti, glutei, core", patterns: ["squat", "hinge", "squat", "hinge", "squat", "core"] },
      { nome: "Push B — Ipertrofia", focus: "petto, spalle, tricipiti", patterns: ["push_h", "push_v", "push_h", "push_v", "push_h", "push_h"] },
      { nome: "Pull B — Ipertrofia", focus: "dorsali, trapezio, bicipiti", patterns: ["pull_h", "pull_v", "pull_h", "pull_v", "pull_h", "pull_h"] },
      { nome: "Legs B — Hip", focus: "glutei, femorali, core", patterns: ["hinge", "squat", "hinge", "squat", "hinge", "core"] },
    ]},
  },
};

// ════════════════════════════════════════════════════════════
// CONSTANTS — Difficulty Mapping
// ════════════════════════════════════════════════════════════

const DIFFICULTY_ORDER = ["principiante", "intermedio", "avanzato"] as const;

function difficultyDistance(a: string, b: string): number {
  const idxA = DIFFICULTY_ORDER.indexOf(a as typeof DIFFICULTY_ORDER[number]);
  const idxB = DIFFICULTY_ORDER.indexOf(b as typeof DIFFICULTY_ORDER[number]);
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
  { id: "muscle_match",         label: "Match Muscolare",            weight: 0.12 },
  { id: "pattern_match",        label: "Pattern Movimento",          weight: 0.10 },
  { id: "difficulty",           label: "Difficolta",                 weight: 0.10 },
  { id: "goal_alignment",       label: "Allineamento Obiettivo",     weight: 0.08 },
  { id: "strength_level",       label: "Livello Forza",              weight: 0.06 },
  { id: "recovery_fit",         label: "Compatibilita Recupero",     weight: 0.06 },
  { id: "compound_priority",    label: "Priorita Compound",          weight: 0.05 },
  { id: "equipment_variety",    label: "Varieta Attrezzatura",       weight: 0.05 },
  { id: "uniqueness",           label: "Unicita",                    weight: 0.05 },
  { id: "plane_variety",        label: "Varieta Piani",              weight: 0.05 },
  { id: "chain_variety",        label: "Varieta Catena Cinetica",    weight: 0.04 },
  { id: "bilateral_balance",    label: "Equilibrio Bilaterale",      weight: 0.04 },
  { id: "contraction_variety",  label: "Varieta Contrazione",        weight: 0.05 },
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

/** Intersezione Jaccard tra due array di stringhe */
function jaccard(a: string[], b: string[]): number {
  if (a.length === 0 && b.length === 0) return 0;
  const setA = new Set(a.map(s => s.toLowerCase()));
  const setB = new Set(b.map(s => s.toLowerCase()));
  let intersection = 0;
  for (const item of setA) {
    if (setB.has(item)) intersection++;
  }
  const union = new Set([...setA, ...setB]).size;
  return union > 0 ? intersection / union : 0;
}

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

/** 1. Safety — safe=1.0, caution=0.5, avoid=0.1 (mai 0 → INFORM) */
function scoreSafety(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  if (!ctx.profile?.safetyMap) return { score: 0.5, reason: "Nessun dato safety" };
  const entry = ctx.profile.safetyMap[ex.id];
  if (!entry) return { score: 1.0, reason: "Nessuna controindicazione" };
  if (entry.severity === "avoid") return { score: 0.1, reason: `Da evitare: ${entry.conditions.map(c => c.nome).join(", ")}` };
  return { score: 0.5, reason: `Cautela: ${entry.conditions.map(c => c.nome).join(", ")}` };
}

/** 2. Muscle Match — coverage ratio (quanti target sono coperti dall'esercizio) */
function scoreMuscleMatch(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const target = ctx.slot.muscoli_target;
  if (target.length === 0) return { score: 0.5, reason: "Nessun target muscolare" };
  const targetSet = new Set(target.map(m => m.toLowerCase()));
  const priSet = new Set(ex.muscoli_primari.map(m => m.toLowerCase()));
  const secSet = new Set(ex.muscoli_secondari.map(m => m.toLowerCase()));
  // Coverage: quanti muscoli target sono tra i primari dell'esercizio
  let priHits = 0;
  for (const t of targetSet) if (priSet.has(t)) priHits++;
  const coverage = priHits / targetSet.size;
  if (coverage >= 0.5) return { score: 0.8 + coverage * 0.2, reason: `Match muscolare ${Math.round(coverage * 100)}%` };
  if (coverage > 0) return { score: 0.3 + coverage * 0.4, reason: `Match parziale (${priHits}/${targetSet.size})` };
  // Prova sui secondari
  let secHits = 0;
  for (const t of targetSet) if (secSet.has(t)) secHits++;
  if (secHits > 0) return { score: 0.2 + (secHits / targetSet.size) * 0.3, reason: `Match secondario (${secHits}/${targetSet.size})` };
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
  const oreTraSessioni = (7 * 24) / ctx.sessioniPerSettimana;
  if (ex.ore_recupero <= oreTraSessioni) return { score: 1.0, reason: `Recupero ${ex.ore_recupero}h ok` };
  if (ex.ore_recupero <= oreTraSessioni * 1.5) return { score: 0.6, reason: `Recupero ${ex.ore_recupero}h accettabile` };
  return { score: 0.3, reason: `Recupero ${ex.ore_recupero}h lungo` };
}

/** 8. Compound Priority — compound > bodyweight > isolation */
function scoreCompoundPriority(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const cat = ex.categoria;
  if (cat === "compound") return { score: 1.0, reason: "Compound multiarticolare" };
  if (cat === "bodyweight") return { score: 0.7, reason: "Bodyweight funzionale" };
  if (cat === "isolation") return { score: 0.4, reason: "Isolation monoarticolare" };
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
  compound_priority: scoreCompoundPriority,
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
  if (profile.strengthRatios.length > 0) {
    const levels = profile.strengthRatios.map(sr => sr.level.toLowerCase());
    const hasAvanzato = levels.some(l => l === "avanzato" || l === "elite");
    const hasIntermedio = levels.some(l => l === "intermedio");
    if (hasAvanzato) return "avanzato";
    if (hasIntermedio) return "intermedio";
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

/** Determina la struttura split ottimale da sessioni/settimana + livello */
export function determineSplit(
  sessioniPerSettimana: number,
  livello: FitnessLevel,
): SplitPattern {
  const clamped = Math.max(2, Math.min(6, sessioniPerSettimana));
  const levelPatterns = SPLIT_PATTERNS[clamped];
  if (!levelPatterns) return SPLIT_PATTERNS[3][livello];
  return levelPatterns[livello] ?? levelPatterns.beginner;
}

// ════════════════════════════════════════════════════════════
// SMART PLAN GENERATOR
// ════════════════════════════════════════════════════════════

/**
 * Genera una struttura SmartPlan completa con slot per ogni sessione.
 * NON assegna esercizi — genera solo la struttura (slot con hint).
 */
export function generateSmartPlan(
  sessioniPerSettimana: number,
  livello: FitnessLevel,
  obiettivo: string,
  durataSettimane: number = 4,
): SmartPlan {
  const split = determineSplit(sessioniPerSettimana, livello);

  const sessioni: SmartSession[] = split.sessioni.map(s => {
    // Genera slot
    const slots: SmartSlot[] = [];

    // Avviamento: 2-3 slot
    const warmupCount = livello === "beginner" ? 2 : 3;
    for (let i = 0; i < warmupCount; i++) {
      slots.push({
        sezione: "avviamento",
        pattern_hint: i === 0 ? "warmup" : (i === 1 ? "warmup" : "mobility"),
        muscoli_target: [],
        label: i === 0 ? "Riscaldamento Generale" : (i === 1 ? "Attivazione Dinamica" : "Mobilita Articolare"),
        serie: i === 0 ? 1 : 2,
        ripetizioni: i === 0 ? "5 min" : "10",
        tempo_riposo_sec: 0,
      });
    }

    // Principale: slot basati sui pattern
    for (const pattern of s.patterns) {
      const muscoliTarget = patternToMuscoli(pattern);
      slots.push({
        sezione: "principale",
        pattern_hint: pattern,
        muscoli_target: muscoliTarget,
        label: patternToLabel(pattern),
        serie: obiettivo === "forza" ? 4 : 3,
        ripetizioni: obiettivo === "forza" ? "5-6" : "8-12",
        tempo_riposo_sec: obiettivo === "forza" ? 120 : 90,
      });
    }

    // Accessori: 1-2 slot per muscoli non coperti dai pattern principali
    const coveredMuscles = new Set(s.patterns.flatMap(p => patternToMuscoli(p)));
    const ACCESSORY_PRIORITY = ["polpacci", "bicipiti", "tricipiti", "adduttori", "avambracci", "trapezio"];
    const uncovered = ACCESSORY_PRIORITY.filter(m => !coveredMuscles.has(m));
    const maxAccessories = livello === "beginner" ? 1 : 2;
    const accessoryTargets = uncovered.slice(0, maxAccessories);
    for (const muscle of accessoryTargets) {
      slots.push({
        sezione: "principale",
        pattern_hint: "accessory",
        muscoli_target: [muscle],
        label: `Accessorio ${capitalizeFirst(muscle)}`,
        serie: 3,
        ripetizioni: "10-15",
        tempo_riposo_sec: 60,
      });
    }

    // Stretching: 2-3 slot mirati ai muscoli lavorati
    const stretchCount = livello === "avanzato" ? 3 : 2;
    const workedMuscles = new Set(s.patterns.flatMap(p => patternToMuscoli(p)));
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
    const durataMinuti = warmupCount * 5 + s.patterns.length * 8 + stretchCount * 2;

    return {
      nome_sessione: s.nome,
      focus_muscolare: s.focus,
      durata_minuti: durataMinuti,
      slots,
    };
  });

  // Nome automatico
  const splitName = sessioniPerSettimana <= 3 ? "Full Body" :
    sessioniPerSettimana <= 4 ? "Upper/Lower" : "PPL";

  return {
    nome: `Smart ${splitName} — ${capitalizeFirst(obiettivo)}`,
    livello,
    obiettivo,
    sessioni_per_settimana: sessioniPerSettimana,
    durata_settimane: durataSettimane,
    sessioni,
  };
}

/**
 * Riempie gli slot di un SmartPlan con esercizi ottimali.
 * Ritorna mappa sessionIndex → slotIndex → ExerciseScore[] (top N).
 */
export function fillSmartPlan(
  plan: SmartPlan,
  exercises: Exercise[],
  profile: ClientProfile | null,
): Map<number, Map<number, ExerciseScore[]>> {
  const result = new Map<number, Map<number, ExerciseScore[]>>();
  const allAssigned: Exercise[] = [];
  const livello = plan.livello as FitnessLevel;

  for (let si = 0; si < plan.sessioni.length; si++) {
    const session = plan.sessioni[si];
    const sessionMap = new Map<number, ExerciseScore[]>();
    const sessionAssigned: Exercise[] = [];

    for (let sli = 0; sli < session.slots.length; sli++) {
      const slot = session.slots[sli];

      // Filtra esercizi candidati per sezione
      const sectionCats = SECTION_CATEGORIES[slot.sezione];
      const candidates = exercises.filter(e => sectionCats.includes(e.categoria));

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

      sessionMap.set(sli, scores.slice(0, 10)); // top 10 per slot

      // Assegna il migliore
      if (scores.length > 0) {
        const bestEx = exercises.find(e => e.id === scores[0].exerciseId);
        if (bestEx) {
          sessionAssigned.push(bestEx);
          allAssigned.push(bestEx);
        }
      }
    }

    result.set(si, sessionMap);
  }

  return result;
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
 * Conta set/muscolo/settimana con credit: primario=1.0, secondario=0.5.
 */
export function computeMuscleCoverage(
  sessions: Array<{ esercizi: Array<{ id_esercizio: number; serie: number }> }>,
  exerciseMap: Map<number, Exercise>,
  livello: FitnessLevel,
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
      for (const m of exercise.muscoli_secondari) {
        const group = normalizeMuscleGroup(m);
        setCounts[group] = (setCounts[group] ?? 0) + ex.serie * 0.5;
      }
    }
  }

  const target = VOLUME_TARGETS[livello];

  return MUSCLE_GROUPS.map(group => {
    const sets = Math.round((setCounts[group] ?? 0) * 10) / 10;
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
  if (sessions.length < 2) return [];

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
      else if (entry.severity === "caution") safe += 0.5;
    }
  }

  return total > 0 ? Math.round((safe / total) * 100) : 100;
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
    coverage: computeMuscleCoverage(sessions, exerciseMap, livello),
    volume: computeVolumeAnalysis(sessions, exerciseMap, livello),
    biomechanics: analyzeBiomechanics(sessions, exerciseMap),
    recoveryConflicts: analyzeRecovery(sessions, sessioniPerSettimana, exerciseMap),
    safetyScore: computeSafetyScore(sessions, safetyMap),
  };
}

// ════════════════════════════════════════════════════════════
// HELPERS — Pattern ↔ Muscoli/Label
// ════════════════════════════════════════════════════════════

function patternToMuscoli(pattern: string): string[] {
  const map: Record<string, string[]> = {
    squat: ["quadricipiti", "glutei"],
    hinge: ["femorali", "glutei", "dorsali"],
    push_h: ["petto", "tricipiti", "spalle"],
    push_v: ["spalle", "tricipiti"],
    pull_h: ["dorsali", "bicipiti", "trapezio"],
    pull_v: ["dorsali", "bicipiti"],
    core: ["core"],
    rotation: ["core", "spalle"],
    carry: ["core", "avambracci", "trapezio"],
    warmup: [],
    stretch: [],
    mobility: [],
  };
  return map[pattern] ?? [];
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

