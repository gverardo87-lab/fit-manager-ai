import type { Exercise } from "@/types/api";

const RELATION_BASE_SCORE: Record<string, number> = {
  regression: 30,
  variation: 24,
  progression: 20,
};

const RELATION_REASON_PREFIX: Record<string, string> = {
  regression: "Regressione",
  variation: "Variante",
  progression: "Progressione",
};

const DIFFICULTY_RANK: Record<string, number> = {
  beginner: 1,
  intermediate: 2,
  intermedio: 2,
  advanced: 3,
  avanzato: 3,
};

function countSharedPrimaryMuscles(source: Exercise, target: Exercise): number {
  const sourceSet = new Set(source.muscoli_primari);
  let shared = 0;
  for (const muscle of target.muscoli_primari) {
    if (sourceSet.has(muscle)) {
      shared += 1;
    }
  }
  return shared;
}

function getDifficultyRank(value?: string | null): number {
  if (!value) return 0;
  return DIFFICULTY_RANK[value] ?? 0;
}

export function getReplacementScore(
  source: Exercise | undefined,
  target: Exercise | undefined,
  relationType: string,
  hasCaution = false,
): number {
  let score = RELATION_BASE_SCORE[relationType] ?? 12;

  if (source && target) {
    if (source.pattern_movimento === target.pattern_movimento) score += 12;
    if (source.attrezzatura === target.attrezzatura) score += 8;
    if (source.categoria === target.categoria) score += 4;

    const sharedPrimary = countSharedPrimaryMuscles(source, target);
    score += Math.min(6, sharedPrimary * 2);

    const sourceRank = getDifficultyRank(source.difficolta);
    const targetRank = getDifficultyRank(target.difficolta);
    if (sourceRank > 0 && targetRank > 0) {
      if (sourceRank === targetRank) score += 3;
      if (relationType === "regression" && targetRank < sourceRank) score += 2;
      if (relationType === "progression" && targetRank > sourceRank) score += 2;
    }
  }

  if (hasCaution) score -= 8;
  return score;
}

export function getReplacementReason(
  source: Exercise | undefined,
  target: Exercise | undefined,
  relationType: string,
  hasCaution = false,
): string {
  const prefix = RELATION_REASON_PREFIX[relationType] ?? "Alternativa";

  if (!source || !target) {
    return hasCaution
      ? `${prefix}: esercizio collegato; richiede cautela clinica.`
      : `${prefix}: esercizio collegato e rapido da inserire.`;
  }

  const sharedPrimary = countSharedPrimaryMuscles(source, target);
  let context = "stimolo compatibile con il piano corrente";

  if (
    source.pattern_movimento === target.pattern_movimento &&
    source.attrezzatura === target.attrezzatura
  ) {
    context = "stesso pattern e stessa attrezzatura";
  } else if (source.pattern_movimento === target.pattern_movimento) {
    context = "stesso pattern motorio";
  } else if (sharedPrimary >= 2) {
    context = "stessi distretti muscolari principali";
  } else if (sharedPrimary === 1) {
    context = "stesso distretto muscolare chiave";
  } else if (source.attrezzatura === target.attrezzatura) {
    context = "stessa attrezzatura, cambio immediato";
  } else if (source.categoria === target.categoria) {
    context = "stessa categoria con stimolo diverso";
  }

  if (hasCaution) {
    return `${prefix}: ${context}; usa cautela clinica.`;
  }
  return `${prefix}: ${context}.`;
}
