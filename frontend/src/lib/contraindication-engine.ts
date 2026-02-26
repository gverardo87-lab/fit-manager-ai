// src/lib/contraindication-engine.ts
/**
 * Motore regole controindicazioni: incrocio anamnesi ↔ esercizi.
 *
 * Logica ibrida:
 * 1. Se l'esercizio ha `controindicazioni` esplicite (DB) → match diretto
 * 2. Fallback rule-based: pattern_movimento + muscoli_primari vs body part tags
 *
 * Nessuna dipendenza backend — tutto frontend, deterministico, zero latenza.
 */

import type { AnamnesiData, AnamnesiQuestion, Exercise } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

export type BodyPartTag =
  | "knee"
  | "lower_back"
  | "upper_back"
  | "back"
  | "shoulder"
  | "neck"
  | "hip"
  | "ankle"
  | "wrist"
  | "elbow"
  | "calf";

export type MedicalFlag = "cardiac" | "respiratory" | "metabolic";

export type ExerciseSafety = "safe" | "caution" | "avoid";

export interface SafetyResult {
  safety: ExerciseSafety;
  reasons: string[];
}

interface ContraindicationRule {
  avoid_patterns: string[];
  caution_patterns: string[];
  caution_muscles: string[];
}

// ════════════════════════════════════════════════════════════
// KEYWORD MAPPINGS
// ════════════════════════════════════════════════════════════

/** Italiano → body part tag (substring match, case-insensitive) */
const BODY_PART_KEYWORDS: [string, BodyPartTag][] = [
  // Ginocchio
  ["ginocchio", "knee"], ["ginocchi", "knee"],
  ["menisco", "knee"], ["crociato", "knee"], ["rotula", "knee"], ["rotuleo", "knee"],
  // Spalla
  ["spalla", "shoulder"], ["spalle", "shoulder"], ["cuffia", "shoulder"],
  ["rotator", "shoulder"], ["lussazione", "shoulder"], ["sovraspinato", "shoulder"],
  // Schiena bassa
  ["lombare", "lower_back"], ["lombalgia", "lower_back"],
  ["ernia", "lower_back"], ["disco", "lower_back"], ["discale", "lower_back"],
  ["sciatica", "lower_back"], ["lombo", "lower_back"],
  // Schiena alta
  ["dorsale", "upper_back"], ["toracica", "upper_back"],
  // Schiena generica
  ["schiena", "back"],
  // Collo
  ["cervicale", "neck"], ["cervicalgia", "neck"], ["collo", "neck"],
  // Anca
  ["anca", "hip"], ["anche", "hip"], ["femore", "hip"], ["coxo", "hip"],
  // Caviglia
  ["caviglia", "ankle"], ["distorsione", "ankle"], ["tibio", "ankle"],
  // Polso
  ["polso", "wrist"], ["carpale", "wrist"], ["tunnel", "wrist"],
  // Gomito
  ["gomito", "elbow"], ["epicondil", "elbow"], ["epitrocle", "elbow"],
  // Polpaccio
  ["polpaccio", "calf"], ["achille", "calf"], ["soleo", "calf"],
  ["gastrocnemio", "calf"],
];

/** Condizioni mediche → flag */
const MEDICAL_KEYWORDS: [string, MedicalFlag][] = [
  ["cardiovascol", "cardiac"], ["cuore", "cardiac"], ["aritmia", "cardiac"],
  ["ipertension", "cardiac"], ["cardiopat", "cardiac"], ["infarto", "cardiac"],
  ["asma", "respiratory"], ["respirator", "respiratory"], ["apnea", "respiratory"],
  ["bpco", "respiratory"], ["bronchi", "respiratory"],
  ["diabete", "metabolic"], ["tiroide", "metabolic"], ["insulina", "metabolic"],
];

// ════════════════════════════════════════════════════════════
// CONTRAINDICATION RULES (body part → exercise restrictions)
// ════════════════════════════════════════════════════════════

const RULES: Record<BodyPartTag, ContraindicationRule> = {
  knee: {
    avoid_patterns: ["squat"],
    caution_patterns: [],
    caution_muscles: ["quadriceps", "hamstrings", "calves"],
  },
  lower_back: {
    avoid_patterns: ["hinge"],
    caution_patterns: ["squat"],
    caution_muscles: ["back", "core"],
  },
  upper_back: {
    avoid_patterns: [],
    caution_patterns: ["pull_h", "pull_v"],
    caution_muscles: ["back", "lats", "traps"],
  },
  back: {
    avoid_patterns: ["hinge"],
    caution_patterns: ["squat", "pull_h", "pull_v"],
    caution_muscles: ["back", "lats", "core"],
  },
  shoulder: {
    avoid_patterns: ["push_v"],
    caution_patterns: ["push_h", "pull_v"],
    caution_muscles: ["shoulders", "traps"],
  },
  neck: {
    avoid_patterns: [],
    caution_patterns: ["push_v"],
    caution_muscles: ["traps"],
  },
  hip: {
    avoid_patterns: ["squat", "hinge"],
    caution_patterns: [],
    caution_muscles: ["glutes", "adductors", "hamstrings"],
  },
  ankle: {
    avoid_patterns: ["squat"],
    caution_patterns: [],
    caution_muscles: ["calves"],
  },
  wrist: {
    avoid_patterns: [],
    caution_patterns: ["push_h", "push_v"],
    caution_muscles: ["forearms"],
  },
  elbow: {
    avoid_patterns: [],
    caution_patterns: ["push_h", "push_v", "pull_h", "pull_v"],
    caution_muscles: ["biceps", "triceps", "forearms"],
  },
  calf: {
    avoid_patterns: [],
    caution_patterns: [],
    caution_muscles: ["calves"],
  },
};

/** Body part tag → etichetta italiana per UI */
const BODY_PART_LABELS: Record<BodyPartTag, string> = {
  knee: "ginocchio",
  lower_back: "zona lombare",
  upper_back: "dorsale",
  back: "schiena",
  shoulder: "spalla",
  neck: "cervicale",
  hip: "anca",
  ankle: "caviglia",
  wrist: "polso",
  elbow: "gomito",
  calf: "polpaccio",
};

// ════════════════════════════════════════════════════════════
// EXTRACTION
// ════════════════════════════════════════════════════════════

/** Scansiona un testo italiano e restituisce body part tags trovati */
function scanText(text: string): { bodyParts: Set<BodyPartTag>; medical: Set<MedicalFlag> } {
  const lower = text.toLowerCase();
  const bodyParts = new Set<BodyPartTag>();
  const medical = new Set<MedicalFlag>();

  for (const [keyword, tag] of BODY_PART_KEYWORDS) {
    if (lower.includes(keyword)) bodyParts.add(tag);
  }
  for (const [keyword, flag] of MEDICAL_KEYWORDS) {
    if (lower.includes(keyword)) medical.add(flag);
  }

  // "schiena" generica → se non piu' specifico, tieni "back"
  // Se gia' c'e' lower_back o upper_back, rimuovi "back" generico
  if (bodyParts.has("back") && (bodyParts.has("lower_back") || bodyParts.has("upper_back"))) {
    bodyParts.delete("back");
  }

  return { bodyParts, medical };
}

/** Estrae dettaglio da un campo AnamnesiQuestion (se presente) */
function collectQuestionText(q: AnamnesiQuestion): string {
  return q.presente && q.dettaglio ? q.dettaglio : "";
}

/**
 * Estrae tutti i body part tags e medical flags dall'anamnesi completa.
 * Scansiona TUTTI i campi (non solo 3 come extractContraindications).
 */
export function extractTagsFromAnamnesi(
  anamnesi: AnamnesiData,
): { bodyParts: BodyPartTag[]; medicalFlags: MedicalFlag[] } {
  const allText = [
    collectQuestionText(anamnesi.infortuni_attuali),
    collectQuestionText(anamnesi.infortuni_pregressi),
    collectQuestionText(anamnesi.interventi_chirurgici),
    collectQuestionText(anamnesi.dolori_cronici),
    collectQuestionText(anamnesi.patologie),
    collectQuestionText(anamnesi.problemi_cardiovascolari),
    collectQuestionText(anamnesi.problemi_respiratori),
    anamnesi.limitazioni_funzionali ?? "",
    anamnesi.note ?? "",
  ].join(" ");

  // Flag diretti da campi booleani (senza bisogno di keyword)
  const result = scanText(allText);
  if (anamnesi.problemi_cardiovascolari.presente) result.medical.add("cardiac");
  if (anamnesi.problemi_respiratori.presente) result.medical.add("respiratory");

  return {
    bodyParts: [...result.bodyParts],
    medicalFlags: [...result.medical],
  };
}

// ════════════════════════════════════════════════════════════
// CLASSIFICATION
// ════════════════════════════════════════════════════════════

/**
 * Classifica un esercizio rispetto ai body part tags e medical flags.
 *
 * Logica (ordine priorita'):
 * 1. exercise.controindicazioni (DB, esplicite) overlap → avoid
 * 2. pattern_movimento in avoid_patterns → avoid
 * 3. pattern_movimento in caution_patterns → caution
 * 4. muscoli_primari overlap con caution_muscles → caution
 * 5. Condizione cardiaca + compound/cardio → caution
 * 6. Altrimenti → safe
 */
export function classifyExercise(
  exercise: Exercise,
  bodyParts: BodyPartTag[],
  medicalFlags: MedicalFlag[],
): SafetyResult {
  if (bodyParts.length === 0 && medicalFlags.length === 0) {
    return { safety: "safe", reasons: [] };
  }

  const reasons: string[] = [];
  let worst: ExerciseSafety = "safe";

  const upgrade = (level: ExerciseSafety, reason: string) => {
    reasons.push(reason);
    if (level === "avoid") worst = "avoid";
    else if (level === "caution" && worst !== "avoid") worst = "caution";
  };

  // 1. Controindicazioni esplicite dal DB
  if (exercise.controindicazioni.length > 0) {
    for (const tag of bodyParts) {
      const label = BODY_PART_LABELS[tag];
      for (const c of exercise.controindicazioni) {
        if (c.toLowerCase().includes(tag) || c.toLowerCase().includes(label)) {
          upgrade("avoid", `Controindicato per ${label}`);
        }
      }
    }
  }

  // 2-4. Rule-based per ogni body part tag
  for (const tag of bodyParts) {
    const rule = RULES[tag];
    if (!rule) continue;
    const label = BODY_PART_LABELS[tag];

    // Avoid patterns
    if (rule.avoid_patterns.includes(exercise.pattern_movimento)) {
      upgrade("avoid", `Pattern ${exercise.pattern_movimento} da evitare per ${label}`);
    }

    // Caution patterns
    if (rule.caution_patterns.includes(exercise.pattern_movimento)) {
      upgrade("caution", `Pattern ${exercise.pattern_movimento} con cautela per ${label}`);
    }

    // Caution muscles
    const muscleOverlap = exercise.muscoli_primari.filter((m) =>
      rule.caution_muscles.includes(m),
    );
    if (muscleOverlap.length > 0) {
      upgrade("caution", `Muscoli ${muscleOverlap.join(", ")} — cautela per ${label}`);
    }
  }

  // 5. Condizioni mediche
  if (medicalFlags.includes("cardiac")) {
    if (exercise.categoria === "compound" || exercise.categoria === "cardio") {
      upgrade("caution", "Alta intensita' — cautela cardiovascolare");
    }
  }
  if (medicalFlags.includes("respiratory")) {
    if (exercise.categoria === "cardio") {
      upgrade("caution", "Cardio — cautela respiratoria");
    }
  }

  return { safety: worst, reasons: [...new Set(reasons)] };
}

// ════════════════════════════════════════════════════════════
// BATCH HELPERS
// ════════════════════════════════════════════════════════════

/**
 * Classifica un array di esercizi rispetto all'anamnesi di un cliente.
 * Ritorna Map<exerciseId, SafetyResult> per lookup O(1) nella UI.
 */
export function classifyExercises(
  exercises: Exercise[],
  anamnesi: AnamnesiData,
): Map<number, SafetyResult> {
  const { bodyParts, medicalFlags } = extractTagsFromAnamnesi(anamnesi);
  const map = new Map<number, SafetyResult>();

  for (const ex of exercises) {
    map.set(ex.id, classifyExercise(ex, bodyParts, medicalFlags));
  }

  return map;
}

/**
 * Sommario leggibile dell'anamnesi per banner UI.
 * Es: ["Infortunio ginocchio", "Dolori lombari", "Problemi cardiovascolari"]
 */
export function getAnamnesiSummary(anamnesi: AnamnesiData): string[] {
  const items: string[] = [];

  const addIfPresent = (q: AnamnesiQuestion | undefined, label: string) => {
    if (q?.presente) items.push(label);
  };

  addIfPresent(anamnesi.infortuni_attuali, "Infortuni attuali");
  addIfPresent(anamnesi.infortuni_pregressi, "Infortuni pregressi");
  addIfPresent(anamnesi.interventi_chirurgici, "Interventi chirurgici");
  addIfPresent(anamnesi.dolori_cronici, "Dolori cronici");
  addIfPresent(anamnesi.patologie, "Patologie");
  addIfPresent(anamnesi.problemi_cardiovascolari, "Problemi cardiovascolari");
  addIfPresent(anamnesi.problemi_respiratori, "Problemi respiratori");

  return items;
}

/** Etichetta italiana per livello sicurezza */
export function getSafetyLabel(safety: ExerciseSafety): string {
  switch (safety) {
    case "avoid": return "Controindicato";
    case "caution": return "Attenzione";
    case "safe": return "Sicuro";
  }
}
