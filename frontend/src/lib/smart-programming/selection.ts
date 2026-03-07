// src/lib/smart-programming/selection.ts
/**
 * Strategie di selezione per varieta' esercizi.
 *
 * 1. resolveAlternatives(): swap pattern negli slot compound per varieta' strutturale.
 * 2. weightedRandomPick(): selezione pesata tra top-N candidati (score² weighting).
 *
 * Problema risolto: senza questi meccanismi, lo scoring deterministico produce
 * sempre lo stesso piano per gli stessi input → monotonia percepita.
 */

import type { BlueprintSlot, ExerciseScore } from "./types";

// ── Pattern Alternatives ──

/**
 * Alternative biomeccanicamente equivalenti per pattern compound.
 * push_h <-> push_v: entrambi pushing, angolo diverso.
 * pull_h <-> pull_v: entrambi pulling, angolo diverso.
 * squat <-> hinge: entrambi lower body compound, catena diversa.
 */
const PATTERN_ALTS: Record<string, { pattern: string; muscle: string }> = {
  push_h: { pattern: "push_v", muscle: "spalle" },
  push_v: { pattern: "push_h", muscle: "petto" },
  pull_h: { pattern: "pull_v", muscle: "dorsali" },
  pull_v: { pattern: "pull_h", muscle: "dorsali" },
  squat:  { pattern: "hinge",  muscle: "glutei" },
  hinge:  { pattern: "squat",  muscle: "quadricipiti" },
};

/**
 * Risolve alternative per slot compound in una sessione.
 * Per ogni slot compound con un'alternativa disponibile, sceglie il pattern
 * meno rappresentato nella sessione (o random se pari).
 * Slot isolation restano invariati — i loro pattern (curl, calf_raise, ecc.)
 * sono specifici e la varieta' viene dal weighted random pick.
 */
export function resolveAlternatives(slots: BlueprintSlot[]): BlueprintSlot[] {
  const patternCount: Record<string, number> = {};

  return slots.map(bs => {
    // Solo slot compound — isolation e accessori restano invariati
    if (bs.type !== "compound_primary" && bs.type !== "compound_secondary") {
      return bs;
    }

    const alt = PATTERN_ALTS[bs.pattern_hint];
    if (!alt) {
      patternCount[bs.pattern_hint] = (patternCount[bs.pattern_hint] ?? 0) + 1;
      return bs;
    }

    const mainCount = patternCount[bs.pattern_hint] ?? 0;
    const altCount = patternCount[alt.pattern] ?? 0;

    // Preferisce il pattern meno usato nella sessione; random se pari
    const useAlt = altCount < mainCount || (altCount === mainCount && Math.random() > 0.5);
    const chosen = useAlt ? alt.pattern : bs.pattern_hint;
    patternCount[chosen] = (patternCount[chosen] ?? 0) + 1;

    if (useAlt) {
      return { ...bs, pattern_hint: alt.pattern, targetMuscle: alt.muscle };
    }
    return bs;
  });
}

// ── Weighted Random Pick ──

/**
 * Selezione pesata tra i top-K candidati.
 * Peso = score² (favorisce i migliori ma non deterministico).
 *
 * Con topK=5 e minRatio=0.70:
 * - Score 78 ha probabilita' ~1.5x rispetto a score 72
 * - Score 55 (sotto 78*0.70=54.6) viene escluso
 * - Ogni generazione produce combinazioni diverse
 *
 * Ritorna l'indice nel array originale (gia' ordinato per score desc).
 */
export function weightedRandomPick(
  scores: ExerciseScore[],
  topK: number = 5,
  minRatio: number = 0.70,
): number {
  if (scores.length <= 1) return 0;

  const best = scores[0].totalScore;
  const threshold = best * minRatio;

  // Raccoglie indici dei candidati eleggibili
  const eligible: number[] = [];
  for (let i = 0; i < Math.min(scores.length, topK); i++) {
    if (scores[i].totalScore >= threshold) eligible.push(i);
  }
  if (eligible.length <= 1) return 0;

  // Peso quadratico: score² favorisce i migliori senza determinismo
  const weights = eligible.map(i => scores[i].totalScore * scores[i].totalScore);
  const total = weights.reduce((a, b) => a + b, 0);

  let r = Math.random() * total;
  for (let j = 0; j < eligible.length; j++) {
    r -= weights[j];
    if (r <= 0) return eligible[j];
  }
  return 0;
}
