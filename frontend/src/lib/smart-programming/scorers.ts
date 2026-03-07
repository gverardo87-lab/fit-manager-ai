// src/lib/smart-programming/scorers.ts
/**
 * 14 scorer composabili + orchestratore.
 * Ogni scorer valuta un esercizio rispetto a uno slot su una dimensione specifica.
 * Lo scoring e' client-side per latenza zero nel builder.
 */

import type { Exercise } from "@/types/api";
import type {
  ScorerConfig,
  ScorerContext,
  ScorerFn,
  ExerciseScore,
  ScoreDimension,
  SmartSlot,
  ClientProfile,
  FitnessLevel,
} from "./types";
import { normalizeMuscleGroup, difficultyDistance, countInRecord } from "./helpers";

// ── Scorer Configuration ──

const SCORER_CONFIGS: ScorerConfig[] = [
  { id: "safety",               label: "Sicurezza",                  weight: 0.15 },
  { id: "muscle_match",         label: "Match Muscolare",            weight: 0.14 },
  { id: "pattern_match",        label: "Pattern Movimento",          weight: 0.13 },
  { id: "difficulty",           label: "Difficolta",                 weight: 0.10 },
  { id: "goal_alignment",       label: "Allineamento Obiettivo",     weight: 0.08 },
  { id: "strength_level",       label: "Livello Forza",              weight: 0.06 },
  { id: "recovery_fit",         label: "Compatibilita Recupero",     weight: 0.06 },
  { id: "slot_fit",             label: "Adeguatezza Slot",           weight: 0.09 },
  { id: "equipment_variety",    label: "Varieta Attrezzatura",       weight: 0.04 },
  { id: "uniqueness",           label: "Unicita",                    weight: 0.05 },
  { id: "plane_variety",        label: "Varieta Piani",              weight: 0.03 },
  { id: "chain_variety",        label: "Varieta Catena Cinetica",    weight: 0.03 },
  { id: "bilateral_balance",    label: "Equilibrio Bilaterale",      weight: 0.02 },
  { id: "contraction_variety",  label: "Varieta Contrazione",        weight: 0.02 },
];

// ── 14 Scorer Functions ──

/** 1. Safety — safe=1.0, modify=0.7, caution=0.5, avoid=0.1 (mai 0 → INFORM) */
function scoreSafety(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  if (!ctx.profile?.safetyMap) return { score: 0.5, reason: "Nessun dato safety" };
  const entry = ctx.profile.safetyMap[ex.id];
  if (!entry) return { score: 1.0, reason: "Nessuna controindicazione" };
  if (entry.severity === "avoid") return { score: 0.1, reason: `Da evitare: ${entry.conditions.map(c => c.nome).join(", ")}` };
  if (entry.severity === "modify") return { score: 0.7, reason: `Adattare: ${entry.conditions.map(c => c.nome).join(", ")}` };
  return { score: 0.5, reason: `Cautela: ${entry.conditions.map(c => c.nome).join(", ")}` };
}

/** 2. Muscle Match — coverage ratio con pattern floor 0.5 */
function scoreMuscleMatch(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const target = ctx.slot.muscoli_target;
  if (target.length === 0) return { score: 0.5, reason: "Nessun target muscolare" };
  const targetSet = new Set(target.map(m => normalizeMuscleGroup(m.toLowerCase())));
  const priSet = new Set(ex.muscoli_primari.map(m => normalizeMuscleGroup(m.toLowerCase())));
  const secSet = new Set(ex.muscoli_secondari.map(m => normalizeMuscleGroup(m.toLowerCase())));
  const patternMatch = ctx.slot.pattern_hint === ex.pattern_movimento;

  let priHits = 0;
  for (const t of targetSet) if (priSet.has(t)) priHits++;
  const coverage = priHits / targetSet.size;
  if (coverage >= 0.5) return { score: 0.8 + coverage * 0.2, reason: `Match muscolare ${Math.round(coverage * 100)}%` };
  if (coverage > 0) return { score: Math.max(patternMatch ? 0.5 : 0, 0.3 + coverage * 0.4), reason: `Match parziale (${priHits}/${targetSet.size})` };
  let secHits = 0;
  for (const t of targetSet) if (secSet.has(t)) secHits++;
  if (secHits > 0) return { score: Math.max(patternMatch ? 0.5 : 0, 0.2 + (secHits / targetSet.size) * 0.3), reason: `Match secondario (${secHits}/${targetSet.size})` };
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

/** 5. Goal Alignment — rep range allineato all'obiettivo */
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
  if (ex.rep_range_forza || ex.rep_range_ipertrofia || ex.rep_range_resistenza) {
    return { score: 0.5, reason: "Rep range disponibile per altro obiettivo" };
  }
  return { score: 0.3, reason: "Nessun rep range specifico" };
}

/** 6. Strength Level — match livello forza client con difficolta */
function scoreStrengthLevel(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  if (!ctx.profile?.strengthLevel) return { score: 0.5, reason: "Livello forza non disponibile" };
  const dist = difficultyDistance(
    ex.difficolta,
    ctx.profile.strengthLevel === "beginner" ? "principiante" : ctx.profile.strengthLevel,
  );
  if (dist === 0) return { score: 1.0, reason: "Adeguato al livello di forza" };
  if (dist === 1) return { score: 0.6, reason: "Leggermente fuori livello" };
  return { score: 0.3, reason: "Significativamente fuori livello" };
}

/** 7. Recovery Fit — ore_recupero rispettate */
function scoreRecoveryFit(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  if (ctx.sessioniPerSettimana <= 0) return { score: 0.5, reason: "Sessioni/settimana non valide" };
  const oreTraSessioni = (7 * 24) / ctx.sessioniPerSettimana;
  if (ex.ore_recupero <= oreTraSessioni) return { score: 1.0, reason: `Recupero ${ex.ore_recupero}h ok` };
  if (ex.ore_recupero <= oreTraSessioni * 1.5) return { score: 0.6, reason: `Recupero ${ex.ore_recupero}h accettabile` };
  return { score: 0.3, reason: `Recupero ${ex.ore_recupero}h lungo` };
}

/** 8. Slot Fit — compound slots vogliono compound, isolation slots vogliono isolation */
function scoreSlotFit(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const cat = ex.categoria;
  const slotType = ctx.slot.slotType;
  if (!slotType) return { score: 0.5, reason: "Slot senza tipo (warmup/stretching)" };
  if (slotType === "isolation_target" || slotType === "isolation_accessory") {
    if (cat === "isolation") return { score: 1.0, reason: "Isolation per slot isolamento" };
    if (cat === "bodyweight") return { score: 0.6, reason: "Bodyweight per slot isolamento" };
    if (cat === "compound") return { score: 0.15, reason: "Compound per slot isolamento (penalizzato)" };
    return { score: 0.5, reason: `Categoria ${cat}` };
  }
  if (cat === "compound") return { score: 1.0, reason: "Compound multiarticolare" };
  if (cat === "bodyweight") return { score: 0.7, reason: "Bodyweight funzionale" };
  if (cat === "isolation") return { score: 0.3, reason: "Isolation per slot compound" };
  return { score: 0.5, reason: `Categoria ${cat}` };
}

/** 9. Equipment Variety — penalizza stessa attrezzatura */
function scoreEquipmentVariety(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  if (ctx.sessionEquipment.size === 0) return { score: 0.5, reason: "Primo esercizio" };
  if (ctx.sessionEquipment.has(ex.attrezzatura)) return { score: 0.3, reason: `${ex.attrezzatura} gia usata` };
  return { score: 1.0, reason: `Nuova attrezzatura: ${ex.attrezzatura}` };
}

/** 10. Uniqueness — non usato altrove=1.0, altra sessione=0.3, stessa=0.0 */
function scoreUniqueness(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  if (ctx.sessionExercises.some(e => e.id === ex.id)) return { score: 0.0, reason: "Gia presente in sessione" };
  if (ctx.allPlanExercises.some(e => e.id === ex.id)) return { score: 0.3, reason: "Gia in altra sessione" };
  return { score: 1.0, reason: "Esercizio unico" };
}

/** 11. Plane Variety — premia piani sotto-rappresentati */
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

/** 13. Bilateral Balance — unilaterale bonus se deficit simmetria */
function scoreBilateralBalance(ex: Exercise, ctx: ScorerContext): { score: number; reason: string } {
  const hasDeficits = ctx.profile?.symmetryDeficits && ctx.profile.symmetryDeficits.length > 0;
  if (!hasDeficits) return { score: 0.5, reason: "Nessun dato simmetria" };
  const isUnilateral = ex.lateral_pattern === "unilaterale" || ex.lateral_pattern === "unilateral";
  if (isUnilateral) return { score: 1.0, reason: "Unilaterale — corregge asimmetria" };
  return { score: 0.4, reason: "Bilaterale — non corregge asimmetria" };
}

/** 14. Contraction Variety — varia tipi contrazione */
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

// ── Scoring Orchestrator ──

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
    slot, profile, livello, obiettivo,
    sessionExercises, allPlanExercises,
    sessionEquipment, sessionPlanes, sessionChains, sessionContractions,
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

  scores.sort((a, b) => b.totalScore - a.totalScore);
  return scores;
}
