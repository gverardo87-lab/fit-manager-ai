// src/lib/workout-quality-engine.ts
/**
 * Motore deterministico di analisi qualita' scheda allenamento.
 *
 * 7 dimensioni di analisi:
 *   1. Bilanciamento muscolare (push/pull, upper/lower)
 *   2. Copertura pattern movimento
 *   3. Volume settimanale
 *   4. Allineamento ripetizioni-obiettivo
 *   5. Varieta' esercizi
 *   6. Coerenza difficolta'
 *   7. Bilanciamento sessioni
 *
 * Pattern identico a contraindication-engine.ts:
 * funzioni pure, zero deps, zero latenza.
 */

import type { Exercise } from "@/types/api";
import type { SessionCardData } from "@/components/workouts/SessionCard";
import { getSectionForCategory } from "@/lib/workout-templates";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

export type QualityLevel = "eccellente" | "buono" | "sufficiente" | "da_migliorare";
export type IssueSeverity = "info" | "warning" | "critical";

export interface QualityIssue {
  severity: IssueSeverity;
  message: string;
  suggestion?: string;
}

export interface QualityDimension {
  key: string;
  label: string;
  score: number;
  level: QualityLevel;
  issues: QualityIssue[];
}

export interface QualityReport {
  overallScore: number;
  level: QualityLevel;
  dimensions: QualityDimension[];
  strengths: string[];
}

// ════════════════════════════════════════════════════════════
// CONSTANTS
// ════════════════════════════════════════════════════════════

const FUNDAMENTAL_PATTERNS = ["squat", "hinge", "push_h", "push_v", "pull_h", "pull_v"];
const COMPLEMENTARY_PATTERNS = ["core", "rotation", "carry"];

const PUSH_PATTERNS = new Set(["push_h", "push_v"]);
const PULL_PATTERNS = new Set(["pull_h", "pull_v"]);
const UPPER_PATTERNS = new Set(["push_h", "push_v", "pull_h", "pull_v"]);
const LOWER_PATTERNS = new Set(["squat", "hinge"]);

/** Label italiane per pattern e muscoli — UX-friendly */
const PATTERN_LABELS: Record<string, string> = {
  squat: "Squat",
  hinge: "Hinge (stacco/hip)",
  push_h: "Push orizzontale",
  push_v: "Push verticale",
  pull_h: "Pull orizzontale",
  pull_v: "Pull verticale",
  core: "Core",
  rotation: "Rotazione",
  carry: "Carry/Trasporto",
};

const MUSCLE_LABELS: Record<string, string> = {
  quadriceps: "Quadricipiti",
  glutes: "Glutei",
  hamstrings: "Femorali",
  calves: "Polpacci",
  adductors: "Adduttori",
  chest: "Petto",
  back: "Schiena",
  lats: "Dorsali",
  shoulders: "Spalle",
  traps: "Trapezi",
  biceps: "Bicipiti",
  triceps: "Tricipiti",
  forearms: "Avambracci",
  core: "Core",
};

/** Serie settimanali ottimali per muscolo maggiore, per livello */
const VOLUME_RANGES: Record<string, [number, number]> = {
  beginner:   [8, 12],
  intermedio: [12, 18],
  avanzato:   [16, 24],
};

/** Range reps per obiettivo (solo sezione principale) */
const REP_RANGES: Record<string, [number, number]> = {
  forza:        [1, 6],
  ipertrofia:   [6, 12],
  resistenza:   [12, 20],
  dimagrimento: [8, 15],
};

/** Mapping livello → indice numerico per confronto difficolta' */
const LEVEL_ORDER: Record<string, number> = {
  beginner: 0, intermediate: 1, advanced: 2,
};
const PLAN_LEVEL_MAP: Record<string, number> = {
  beginner: 0, intermedio: 1, avanzato: 2,
};

/** Gruppi muscolari "maggiori" — assenza = critical */
const MAJOR_MUSCLE_GROUPS = [
  "quadriceps", "glutes", "hamstrings",
  "chest", "back", "lats", "shoulders",
];

/** Pesi dimensioni per overall score */
const DIMENSION_WEIGHTS: Record<string, number> = {
  muscle_balance: 0.20,
  pattern_coverage: 0.20,
  weekly_volume: 0.15,
  rep_alignment: 0.15,
  variety: 0.10,
  difficulty: 0.10,
  session_balance: 0.10,
};

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

export function scoreToLevel(score: number): QualityLevel {
  if (score >= 85) return "eccellente";
  if (score >= 70) return "buono";
  if (score >= 50) return "sufficiente";
  return "da_migliorare";
}

/** Parse "8-12" → 10, "5" → 5, "30s" / "45sec" → null */
function parseReps(ripetizioni: string): number | null {
  const trimmed = ripetizioni.trim().toLowerCase();
  if (trimmed.includes("s") || trimmed.includes("sec")) return null;

  const rangeMatch = trimmed.match(/^(\d+)\s*-\s*(\d+)$/);
  if (rangeMatch) {
    return (parseInt(rangeMatch[1]) + parseInt(rangeMatch[2])) / 2;
  }

  const singleMatch = trimmed.match(/^(\d+)$/);
  if (singleMatch) return parseInt(singleMatch[1]);

  return null;
}

/** Clamp a value between 0 and 100 */
function clamp100(v: number): number {
  return Math.max(0, Math.min(100, Math.round(v)));
}

/** Raccoglie esercizi "principali" (no avviamento/stretching) da tutte le sessioni */
function getPrincipalExercises(
  sessions: SessionCardData[],
  exMap: Map<number, Exercise>,
): { ex: Exercise; serie: number; reps: string; sessionIdx: number }[] {
  const result: { ex: Exercise; serie: number; reps: string; sessionIdx: number }[] = [];
  for (let si = 0; si < sessions.length; si++) {
    for (const we of sessions[si].esercizi) {
      const ex = exMap.get(we.id_esercizio);
      if (!ex) continue;
      if (getSectionForCategory(ex.categoria) === "principale") {
        result.push({ ex, serie: we.serie, reps: we.ripetizioni, sessionIdx: si });
      }
    }
  }
  return result;
}

/** Raccoglie TUTTI gli esercizi con i loro dati enriched */
function getAllExercises(
  sessions: SessionCardData[],
  exMap: Map<number, Exercise>,
): { ex: Exercise; serie: number; reps: string; sessionIdx: number }[] {
  const result: { ex: Exercise; serie: number; reps: string; sessionIdx: number }[] = [];
  for (let si = 0; si < sessions.length; si++) {
    for (const we of sessions[si].esercizi) {
      const ex = exMap.get(we.id_esercizio);
      if (!ex) continue;
      result.push({ ex, serie: we.serie, reps: we.ripetizioni, sessionIdx: si });
    }
  }
  return result;
}

// ════════════════════════════════════════════════════════════
// DIMENSIONE 1: BILANCIAMENTO MUSCOLARE
// ════════════════════════════════════════════════════════════

function analyzeMuscleBalance(
  sessions: SessionCardData[],
  exMap: Map<number, Exercise>,
): QualityDimension {
  const issues: QualityIssue[] = [];
  const principal = getPrincipalExercises(sessions, exMap);

  // Conta serie per gruppo muscolare
  const muscleSets: Record<string, number> = {};
  let pushSets = 0;
  let pullSets = 0;
  let upperSets = 0;
  let lowerSets = 0;

  for (const { ex, serie } of principal) {
    // Muscoli primari: credito pieno
    for (const m of ex.muscoli_primari) {
      muscleSets[m] = (muscleSets[m] ?? 0) + serie;
    }
    // Muscoli secondari: mezzo credito
    for (const m of ex.muscoli_secondari) {
      muscleSets[m] = (muscleSets[m] ?? 0) + serie * 0.5;
    }

    // Push/Pull/Upper/Lower
    if (PUSH_PATTERNS.has(ex.pattern_movimento)) pushSets += serie;
    if (PULL_PATTERNS.has(ex.pattern_movimento)) pullSets += serie;
    if (UPPER_PATTERNS.has(ex.pattern_movimento)) upperSets += serie;
    if (LOWER_PATTERNS.has(ex.pattern_movimento)) lowerSets += serie;
  }

  let score = 100;

  // Check push/pull ratio
  if (pushSets > 0 && pullSets > 0) {
    const ratio = pushSets / pullSets;
    if (ratio > 1.5 || ratio < 0.67) {
      const dominant = ratio > 1 ? "spinta" : "trazione";
      score -= 20;
      issues.push({
        severity: "warning",
        message: `Rapporto push/pull sbilanciato (${pushSets.toFixed(0)}:${pullSets.toFixed(0)} serie) — troppa ${dominant}`,
        suggestion: `Aggiungi esercizi di ${dominant === "spinta" ? "trazione (rematori, trazioni, pulldown)" : "spinta (panca, military press, push-up)"}`,
      });
    }
  } else if (pushSets > 0 && pullSets === 0) {
    score -= 30;
    issues.push({
      severity: "critical",
      message: "Zero esercizi di trazione — manca tutto il lavoro pull",
      suggestion: "Aggiungi rematori, trazioni o pulldown",
    });
  } else if (pullSets > 0 && pushSets === 0) {
    score -= 30;
    issues.push({
      severity: "critical",
      message: "Zero esercizi di spinta — manca tutto il lavoro push",
      suggestion: "Aggiungi panca, military press o push-up",
    });
  }

  // Check upper/lower
  if (upperSets > 0 && lowerSets > 0) {
    const ratio = upperSets / lowerSets;
    if (ratio > 2) {
      score -= 15;
      issues.push({
        severity: "warning",
        message: `Troppo upper body rispetto al lower (${upperSets.toFixed(0)}:${lowerSets.toFixed(0)} serie)`,
        suggestion: "Aggiungi squat, stacchi o affondi",
      });
    } else if (ratio < 0.5) {
      score -= 15;
      issues.push({
        severity: "warning",
        message: `Troppo lower body rispetto all'upper (${lowerSets.toFixed(0)}:${upperSets.toFixed(0)} serie)`,
        suggestion: "Aggiungi panca, rematori o press sopra la testa",
      });
    }
  }

  // Check major muscle groups
  for (const group of MAJOR_MUSCLE_GROUPS) {
    if (!muscleSets[group] || muscleSets[group] < 1) {
      score -= 5;
      issues.push({
        severity: "info",
        message: `Nessun lavoro diretto per: ${MUSCLE_LABELS[group] ?? group}`,
      });
    }
  }

  return {
    key: "muscle_balance",
    label: "Bilanciamento Muscolare",
    score: clamp100(score),
    level: scoreToLevel(clamp100(score)),
    issues,
  };
}

// ════════════════════════════════════════════════════════════
// DIMENSIONE 2: COPERTURA PATTERN MOVIMENTO
// ════════════════════════════════════════════════════════════

function analyzePatternCoverage(
  sessions: SessionCardData[],
  exMap: Map<number, Exercise>,
): QualityDimension {
  const issues: QualityIssue[] = [];
  const principal = getPrincipalExercises(sessions, exMap);

  const patternsUsed = new Set(principal.map((p) => p.ex.pattern_movimento));
  let score = 100;

  // Pattern fondamentali
  for (const pat of FUNDAMENTAL_PATTERNS) {
    if (!patternsUsed.has(pat)) {
      score -= 15;
      issues.push({
        severity: "warning",
        message: `Pattern fondamentale mancante: ${PATTERN_LABELS[pat] ?? pat}`,
        suggestion: `Aggiungi un esercizio di tipo ${PATTERN_LABELS[pat] ?? pat}`,
      });
    }
  }

  // Pattern complementari
  for (const pat of COMPLEMENTARY_PATTERNS) {
    if (!patternsUsed.has(pat)) {
      score -= 5;
      issues.push({
        severity: "info",
        message: `Pattern complementare mancante: ${PATTERN_LABELS[pat] ?? pat}`,
        suggestion: `Considera di aggiungere un esercizio di ${PATTERN_LABELS[pat] ?? pat}`,
      });
    }
  }

  return {
    key: "pattern_coverage",
    label: "Copertura Pattern",
    score: clamp100(score),
    level: scoreToLevel(clamp100(score)),
    issues,
  };
}

// ════════════════════════════════════════════════════════════
// DIMENSIONE 3: VOLUME SETTIMANALE
// ════════════════════════════════════════════════════════════

function analyzeWeeklyVolume(
  sessions: SessionCardData[],
  exMap: Map<number, Exercise>,
  livello: string,
  sessioniPerSettimana: number,
): QualityDimension {
  const issues: QualityIssue[] = [];
  const principal = getPrincipalExercises(sessions, exMap);
  const range = VOLUME_RANGES[livello] ?? VOLUME_RANGES.intermedio;

  // Conta serie totali per muscolo primario
  const muscleSetsTotal: Record<string, number> = {};
  for (const { ex, serie } of principal) {
    for (const m of ex.muscoli_primari) {
      muscleSetsTotal[m] = (muscleSetsTotal[m] ?? 0) + serie;
    }
  }

  // Serie per sessione nel piano → serie settimanali
  // Se il piano ha 3 sessioni ma il programma prevede 4/settimana, usiamo il min
  const sessionsInPlan = sessions.length;
  const ratio = sessionsInPlan > 0 ? sessioniPerSettimana / sessionsInPlan : 1;

  let underCount = 0;
  let overCount = 0;
  let totalChecked = 0;

  for (const group of MAJOR_MUSCLE_GROUPS) {
    const totalSets = (muscleSetsTotal[group] ?? 0) * ratio;
    if (totalSets === 0) continue; // gia' flaggato da muscle balance
    totalChecked++;

    if (totalSets < range[0]) {
      underCount++;
      issues.push({
        severity: "warning",
        message: `Volume basso per ${MUSCLE_LABELS[group] ?? group}: ${totalSets.toFixed(0)} serie/sett. (consigliato: ${range[0]}-${range[1]})`,
        suggestion: `Aggiungi 1-2 serie in piu' per ${MUSCLE_LABELS[group] ?? group}`,
      });
    } else if (totalSets > range[1] * 1.3) {
      overCount++;
      issues.push({
        severity: "info",
        message: `Volume alto per ${MUSCLE_LABELS[group] ?? group}: ${totalSets.toFixed(0)} serie/sett. (consigliato: ${range[0]}-${range[1]})`,
      });
    }
  }

  let score = 100;
  if (totalChecked > 0) {
    const underPenalty = (underCount / totalChecked) * 50;
    const overPenalty = (overCount / totalChecked) * 20;
    score = clamp100(100 - underPenalty - overPenalty);
  }

  return {
    key: "weekly_volume",
    label: "Volume Settimanale",
    score,
    level: scoreToLevel(score),
    issues,
  };
}

// ════════════════════════════════════════════════════════════
// DIMENSIONE 4: ALLINEAMENTO RIPETIZIONI-OBIETTIVO
// ════════════════════════════════════════════════════════════

function analyzeRepAlignment(
  sessions: SessionCardData[],
  exMap: Map<number, Exercise>,
  obiettivo: string,
): QualityDimension {
  const issues: QualityIssue[] = [];
  const principal = getPrincipalExercises(sessions, exMap);
  const targetRange = REP_RANGES[obiettivo];

  // "generale" = no penalty
  if (!targetRange) {
    return {
      key: "rep_alignment",
      label: "Allineamento Ripetizioni",
      score: 100,
      level: "eccellente",
      issues: [],
    };
  }

  let aligned = 0;
  let total = 0;

  for (const { ex, reps } of principal) {
    const parsed = parseReps(reps);
    if (parsed === null) continue; // skip time-based
    total++;

    if (parsed >= targetRange[0] && parsed <= targetRange[1]) {
      aligned++;
    } else {
      const direction = parsed < targetRange[0] ? "basse" : "alte";
      issues.push({
        severity: "info",
        message: `${ex.nome}: ${reps} reps troppo ${direction} per ${obiettivo} (range ideale: ${targetRange[0]}-${targetRange[1]})`,
      });
    }
  }

  const score = total > 0 ? clamp100((aligned / total) * 100) : 100;

  if (total > 0 && aligned / total < 0.5) {
    issues.unshift({
      severity: "warning",
      message: `Solo il ${Math.round((aligned / total) * 100)}% delle ripetizioni e' nel range ideale per ${obiettivo} (${targetRange[0]}-${targetRange[1]} reps)`,
      suggestion: `Adatta le ripetizioni al range ${targetRange[0]}-${targetRange[1]}`,
    });
  }

  return {
    key: "rep_alignment",
    label: "Allineamento Ripetizioni",
    score,
    level: scoreToLevel(score),
    issues,
  };
}

// ════════════════════════════════════════════════════════════
// DIMENSIONE 5: VARIETA' ESERCIZI
// ════════════════════════════════════════════════════════════

function analyzeVariety(
  sessions: SessionCardData[],
  exMap: Map<number, Exercise>,
): QualityDimension {
  const issues: QualityIssue[] = [];
  const all = getAllExercises(sessions, exMap);

  if (all.length === 0) {
    return {
      key: "variety",
      label: "Varieta' Esercizi",
      score: 0,
      level: "da_migliorare",
      issues: [{ severity: "critical", message: "Nessun esercizio nella scheda" }],
    };
  }

  // Unicita' esercizi
  const exerciseIds = all.map((e) => e.ex.id);
  const uniqueIds = new Set(exerciseIds);
  const uniqueRatio = uniqueIds.size / exerciseIds.length;

  // Duplicati cross-sessione (O(n) — una passata sola)
  const exerciseSessionSets: Record<number, Set<number>> = {};
  for (const { ex, sessionIdx } of all) {
    if (!exerciseSessionSets[ex.id]) exerciseSessionSets[ex.id] = new Set();
    exerciseSessionSets[ex.id].add(sessionIdx);
  }
  for (const [exId, sessionsSet] of Object.entries(exerciseSessionSets)) {
    if (sessionsSet.size >= 3) {
      const ex = exMap.get(Number(exId));
      issues.push({
        severity: "warning",
        message: `${ex?.nome ?? `Esercizio #${exId}`} ripetuto in ${sessionsSet.size} sessioni su ${sessions.length}`,
        suggestion: "Varia lo stimolo con alternative che lavorino gli stessi muscoli",
      });
    }
  }

  // Diversita' attrezzatura
  const equipmentTypes = new Set(all.map((e) => e.ex.attrezzatura));
  if (equipmentTypes.size < 3 && all.length >= 6) {
    issues.push({
      severity: "info",
      message: `Solo ${equipmentTypes.size} tipi di attrezzatura — poca diversita'`,
      suggestion: "Varia tra bilanciere, manubri, cavi, corpo libero",
    });
  }

  let score = uniqueRatio * 100;
  // Penalita' duplicati
  const dupCount = Object.values(exerciseSessionSets).filter((s) => s.size >= 3).length;
  score -= dupCount * 10;
  // Penalita' attrezzatura monotona
  if (equipmentTypes.size < 3 && all.length >= 6) score -= 10;

  return {
    key: "variety",
    label: "Varieta' Esercizi",
    score: clamp100(score),
    level: scoreToLevel(clamp100(score)),
    issues,
  };
}

// ════════════════════════════════════════════════════════════
// DIMENSIONE 6: COERENZA DIFFICOLTA'
// ════════════════════════════════════════════════════════════

function analyzeDifficultyCoherence(
  sessions: SessionCardData[],
  exMap: Map<number, Exercise>,
  livello: string,
): QualityDimension {
  const issues: QualityIssue[] = [];
  const principal = getPrincipalExercises(sessions, exMap);
  const planLevel = PLAN_LEVEL_MAP[livello] ?? 1;

  let coherent = 0;
  let total = 0;
  let tooHardCount = 0;

  for (const { ex } of principal) {
    const exLevel = LEVEL_ORDER[ex.difficolta] ?? 1;
    total++;
    const diff = Math.abs(exLevel - planLevel);

    if (diff === 0) {
      coherent++;
    } else if (diff === 1) {
      coherent += 0.7; // Parzialmente coerente
    } else {
      // 2 livelli di differenza
      if (exLevel > planLevel) {
        tooHardCount++;
        issues.push({
          severity: "warning",
          message: `${ex.nome} e' di livello ${ex.difficolta} — troppo avanzato per una scheda ${livello}`,
          suggestion: "Considera un'alternativa piu' accessibile",
        });
      }
    }
  }

  let score = total > 0 ? clamp100((coherent / total) * 100) : 100;

  if (total > 0 && tooHardCount / total > 0.3) {
    issues.unshift({
      severity: "critical",
      message: `${Math.round((tooHardCount / total) * 100)}% degli esercizi troppo avanzati per il livello ${livello}`,
      suggestion: "Riduci la difficolta' complessiva della scheda",
    });
    score = Math.min(score, 40);
  }

  return {
    key: "difficulty",
    label: "Coerenza Difficolta'",
    score,
    level: scoreToLevel(score),
    issues,
  };
}

// ════════════════════════════════════════════════════════════
// DIMENSIONE 7: BILANCIAMENTO SESSIONI
// ════════════════════════════════════════════════════════════

function analyzeSessionBalance(
  sessions: SessionCardData[],
  exMap: Map<number, Exercise>,
): QualityDimension {
  const issues: QualityIssue[] = [];

  if (sessions.length < 2) {
    return {
      key: "session_balance",
      label: "Bilanciamento Sessioni",
      score: 100,
      level: "eccellente",
      issues: [],
    };
  }

  // Serie principali per sessione
  const setsPerSession = sessions.map((s) => {
    let sets = 0;
    for (const we of s.esercizi) {
      const ex = exMap.get(we.id_esercizio);
      if (ex && getSectionForCategory(ex.categoria) === "principale") {
        sets += we.serie;
      }
    }
    return sets;
  });

  // Esercizi principali per sessione
  const exPerSession = sessions.map((s) => {
    let count = 0;
    for (const we of s.esercizi) {
      const ex = exMap.get(we.id_esercizio);
      if (ex && getSectionForCategory(ex.categoria) === "principale") count++;
    }
    return count;
  });

  // Coefficiente di variazione delle serie
  const mean = setsPerSession.reduce((a, b) => a + b, 0) / setsPerSession.length;
  const variance = setsPerSession.reduce((a, b) => a + (b - mean) ** 2, 0) / setsPerSession.length;
  const cv = mean > 0 ? Math.sqrt(variance) / mean : 0;

  let score = 100;

  if (cv > 0.4) {
    score -= 25;
    const maxSession = Math.max(...setsPerSession);
    const minSession = Math.min(...setsPerSession);
    issues.push({
      severity: "warning",
      message: `Volume molto diverso tra sessioni (da ${minSession} a ${maxSession} serie) — distribuisci meglio il carico`,
      suggestion: "Sposta 1-2 esercizi dalla sessione piu' pesante a quella piu' leggera",
    });
  } else if (cv > 0.25) {
    score -= 10;
    issues.push({
      severity: "info",
      message: "Leggero squilibrio di volume tra le sessioni",
    });
  }

  // Check sessioni con pochi esercizi principali
  for (let i = 0; i < sessions.length; i++) {
    if (exPerSession[i] < 3 && exPerSession[i] > 0) {
      score -= 5;
      issues.push({
        severity: "info",
        message: `${sessions[i].nome_sessione || `Sessione ${i + 1}`}: solo ${exPerSession[i]} esercizi principali`,
        suggestion: "Considera di aggiungere 1-2 esercizi",
      });
    }
  }

  return {
    key: "session_balance",
    label: "Bilanciamento Sessioni",
    score: clamp100(score),
    level: scoreToLevel(clamp100(score)),
    issues,
  };
}

// ════════════════════════════════════════════════════════════
// FUNZIONE PRINCIPALE
// ════════════════════════════════════════════════════════════

export function analyzeWorkoutQuality(
  sessions: SessionCardData[],
  exerciseMap: Map<number, Exercise>,
  obiettivo: string,
  livello: string,
  sessioniPerSettimana: number,
): QualityReport {
  const dimensions: QualityDimension[] = [
    analyzeMuscleBalance(sessions, exerciseMap),
    analyzePatternCoverage(sessions, exerciseMap),
    analyzeWeeklyVolume(sessions, exerciseMap, livello, sessioniPerSettimana),
    analyzeRepAlignment(sessions, exerciseMap, obiettivo),
    analyzeVariety(sessions, exerciseMap),
    analyzeDifficultyCoherence(sessions, exerciseMap, livello),
    analyzeSessionBalance(sessions, exerciseMap),
  ];

  // Overall score = media pesata
  let overallScore = 0;
  for (const dim of dimensions) {
    const weight = DIMENSION_WEIGHTS[dim.key] ?? 0;
    overallScore += dim.score * weight;
  }
  overallScore = clamp100(overallScore);

  // Strengths = dimensioni con score >= 85
  const strengths = dimensions
    .filter((d) => d.score >= 85)
    .map((d) => d.label);

  return {
    overallScore,
    level: scoreToLevel(overallScore),
    dimensions,
    strengths,
  };
}
