// src/lib/builder-utils.ts
/**
 * Tipi, costanti e funzioni pure per il builder schede allenamento.
 * Estratto da schede/[id]/page.tsx per rispettare il limite 300 LOC.
 */

import type { SessionCardData } from "@/components/workouts/SessionCard";
import type { BlockCardData } from "@/components/workouts/BlockCard";
import type { WorkoutExerciseRow, WorkoutSessionInput, Exercise, BlockType } from "@/types/api";

// ════════════════════════════════════════════════════════════
// LABELS
// ════════════════════════════════════════════════════════════

export const OBIETTIVO_LABELS: Record<string, string> = {
  forza: "Forza", ipertrofia: "Ipertrofia", resistenza: "Resistenza",
  dimagrimento: "Dimagrimento", generale: "Generale",
};
export const LIVELLO_LABELS: Record<string, string> = {
  beginner: "Principiante", intermedio: "Intermedio", avanzato: "Avanzato",
};

export const CONDITION_CATEGORY_LABELS: Record<string, string> = {
  orthopedic: "Ortopedico",
  cardiovascular: "Cardiovascolare",
  metabolic: "Metabolico",
  neurological: "Neurologico",
  respiratory: "Respiratorio",
  special: "Speciale",
};

export const CATEGORY_ORDER = ["orthopedic", "cardiovascular", "metabolic", "neurological", "respiratory", "special"];
export const WORKOUT_LOGO_STORAGE_PREFIX = "fitmanager.workout.logo";

// ════════════════════════════════════════════════════════════
// SAVE TYPES & CONSTANTS
// ════════════════════════════════════════════════════════════

export type SaveIssueLevel = "warning" | "critical";
export type SaveIssueCategory = "draft" | "normalization" | "safety" | "integrity";

export interface SaveIssue {
  level: SaveIssueLevel;
  category: SaveIssueCategory;
  message: string;
  sessionId?: number;
  sessionNumber?: number;
  blockId?: number;
  exerciseRowId?: number;
}

export const SAVE_ISSUE_CATEGORY_LABELS: Record<SaveIssueCategory, string> = {
  draft: "Bozza",
  normalization: "Normalizzazione",
  safety: "Sicurezza",
  integrity: "Integrita",
};

const VALID_BLOCK_TYPES: Set<BlockType> = new Set([
  "circuit", "superset", "tabata", "amrap", "emom", "for_time",
]);
const HIGH_LOAD_WARNING_KG = 150;

export const HISTORY_LIMIT = 60;
export const COALESCE_DELAY_MS = 700;

export const SESSION_COALESCE_FIELDS = new Set<keyof SessionCardData>([
  "nome_sessione", "focus_muscolare", "durata_minuti", "note",
]);
export const EXERCISE_COALESCE_FIELDS = new Set<keyof WorkoutExerciseRow>([
  "serie", "ripetizioni", "tempo_riposo_sec", "tempo_esecuzione", "carico_kg", "note",
]);
export const BLOCK_COALESCE_FIELDS = new Set<keyof BlockCardData>([
  "nome", "giri", "durata_lavoro_sec", "durata_riposo_sec", "durata_blocco_sec", "note",
]);

// ════════════════════════════════════════════════════════════
// PURE UTILITY FUNCTIONS
// ════════════════════════════════════════════════════════════

export function cloneSessionsSnapshot(input: SessionCardData[]): SessionCardData[] {
  if (typeof structuredClone === "function") {
    return structuredClone(input);
  }
  return JSON.parse(JSON.stringify(input)) as SessionCardData[];
}

export function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return (
    target.isContentEditable ||
    tag === "INPUT" ||
    tag === "TEXTAREA" ||
    tag === "SELECT"
  );
}

function trimOrNull(value: string | null | undefined, maxLength: number): string | null {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  return trimmed.slice(0, maxLength);
}

function clampInt(value: number, min: number, max: number, fallback: number): number {
  if (!Number.isFinite(value)) return fallback;
  return Math.min(max, Math.max(min, Math.round(value)));
}

function clampOptionalInt(value: number | null | undefined, min: number, max: number): number | null {
  if (value == null || !Number.isFinite(value)) return null;
  return Math.min(max, Math.max(min, Math.round(value)));
}

function clampOptionalFloat(value: number | null | undefined, min: number, max: number): number | null {
  if (value == null || !Number.isFinite(value)) return null;
  return Math.min(max, Math.max(min, value));
}

// ════════════════════════════════════════════════════════════
// SAVE PIPELINE
// ════════════════════════════════════════════════════════════

function sanitizeExerciseForSave(
  ex: WorkoutExerciseRow,
  ordine: number,
  issues: SaveIssue[],
  contextLabel: string,
  exerciseMap: Map<number, Exercise>,
  oneRMByPattern?: Record<string, number> | null,
  location?: Pick<SaveIssue, "sessionId" | "sessionNumber" | "blockId" | "exerciseRowId">,
): WorkoutSessionInput["esercizi"][number] | null {
  if (!ex.id_esercizio || !exerciseMap.has(ex.id_esercizio)) {
    issues.push({
      level: "warning",
      category: "integrity",
      message: `${contextLabel}: esercizio non valido rimosso dal salvataggio.`,
      ...location,
    });
    return null;
  }

  const serie = clampInt(ex.serie, 1, 10, 3);
  const tempoRiposo = clampInt(ex.tempo_riposo_sec, 0, 300, 90);
  const caricoKg = clampOptionalFloat(ex.carico_kg, 0, 500);
  const ripRaw = (ex.ripetizioni ?? "").trim();
  const ripetizioni = (ripRaw || "8-12").slice(0, 20);

  if (!ripRaw) {
    issues.push({
      level: "warning",
      category: "normalization",
      message: `${contextLabel}: ripetizioni mancanti, applicato default 8-12.`,
      ...location,
    });
  }

  if (caricoKg != null && caricoKg >= HIGH_LOAD_WARNING_KG) {
    issues.push({
      level: "warning",
      category: "safety",
      message: `${contextLabel}: carico elevato (${caricoKg} kg), verifica sicurezza e progressione.`,
      ...location,
    });
  }

  const exData = exerciseMap.get(ex.id_esercizio);
  const pattern = exData?.pattern_movimento;
  if (caricoKg != null && oneRMByPattern && pattern) {
    const oneRM = oneRMByPattern[pattern];
    if (oneRM && oneRM > 0) {
      const percent = Math.round((caricoKg / oneRM) * 100);
      if (percent > 105) {
        issues.push({
          level: "warning",
          category: "safety",
          message: `${contextLabel}: carico ${percent}% 1RM, controlla che sia intenzionale.`,
          ...location,
        });
      }
    }
  }

  return {
    id_esercizio: ex.id_esercizio,
    ordine,
    serie,
    ripetizioni,
    tempo_riposo_sec: tempoRiposo,
    tempo_esecuzione: trimOrNull(ex.tempo_esecuzione, 20),
    carico_kg: caricoKg,
    note: trimOrNull(ex.note, 500),
  };
}

export function prepareSessionsInputForSave(
  sessions: SessionCardData[],
  exerciseMap: Map<number, Exercise>,
  oneRMByPattern?: Record<string, number> | null,
): { sessionsInput: WorkoutSessionInput[]; issues: SaveIssue[]; criticalCount: number; warningCount: number } {
  const issues: SaveIssue[] = [];
  if (sessions.length === 0) {
    issues.push({
      level: "critical",
      category: "integrity",
      message: "Serve almeno una sessione per salvare la scheda.",
    });
    return { sessionsInput: [], issues, criticalCount: 1, warningCount: 0 };
  }

  const sessionsInput: WorkoutSessionInput[] = sessions.map((s, si) => {
    const sessionLabel = `Sessione ${si + 1}`;
    const sessionNumber = s.numero_sessione > 0 ? s.numero_sessione : si + 1;

    const nomeSessione = (s.nome_sessione ?? "").trim() || sessionLabel;
    if ((s.nome_sessione ?? "").trim() === "") {
      issues.push({
        level: "warning",
        category: "normalization",
        message: `${sessionLabel}: nome mancante, applicato "${nomeSessione}".`,
        sessionId: s.id,
        sessionNumber,
      });
    }

    const durataMinuti = clampInt(s.durata_minuti, 15, 180, 60);
    if (durataMinuti !== s.durata_minuti) {
      issues.push({
        level: "warning",
        category: "normalization",
        message: `${sessionLabel}: durata fuori range, normalizzata a ${durataMinuti} min.`,
        sessionId: s.id,
        sessionNumber,
      });
    }

    const esercizi = s.esercizi
      .map((ex, idx) =>
        sanitizeExerciseForSave(ex, idx + 1, issues, sessionLabel, exerciseMap, oneRMByPattern,
          { sessionId: s.id, sessionNumber, exerciseRowId: ex.id }),
      )
      .filter((ex): ex is WorkoutSessionInput["esercizi"][number] => ex !== null);

    const blocchi: NonNullable<WorkoutSessionInput["blocchi"]> = [];
    for (const [bi, b] of s.blocchi.entries()) {
      const blockLabel = (b.nome ?? "").trim() || `Blocco ${bi + 1}`;
      const tipoBlocco = VALID_BLOCK_TYPES.has(b.tipo_blocco) ? b.tipo_blocco : "circuit";

      if (tipoBlocco !== b.tipo_blocco) {
        issues.push({
          level: "warning",
          category: "integrity",
          message: `${sessionLabel}: tipo blocco non valido, convertito in "circuit".`,
          sessionId: s.id,
          sessionNumber,
          blockId: b.id,
        });
      }

      const eserciziBlocco = b.esercizi
        .map((ex, ei) =>
          sanitizeExerciseForSave(ex, ei + 1, issues, `${sessionLabel} • ${blockLabel}`, exerciseMap, oneRMByPattern,
            { sessionId: s.id, sessionNumber, blockId: b.id, exerciseRowId: ex.id }),
        )
        .filter((ex): ex is WorkoutSessionInput["esercizi"][number] => ex !== null);

      if (eserciziBlocco.length === 0) {
        issues.push({
          level: "warning",
          category: "draft",
          message: `${sessionLabel}: ${blockLabel} non salvato perche vuoto.`,
          sessionId: s.id,
          sessionNumber,
          blockId: b.id,
        });
        continue;
      }

      blocchi.push({
        tipo_blocco: tipoBlocco,
        ordine: blocchi.length + 1,
        nome: trimOrNull(b.nome, 100),
        giri: clampInt(b.giri, 1, 20, 3),
        durata_lavoro_sec: clampOptionalInt(b.durata_lavoro_sec, 5, 600),
        durata_riposo_sec: clampOptionalInt(b.durata_riposo_sec, 0, 300),
        durata_blocco_sec: clampOptionalInt(b.durata_blocco_sec, 60, 7200),
        note: trimOrNull(b.note, 500),
        esercizi: eserciziBlocco,
      });
    }

    if (esercizi.length === 0 && blocchi.length === 0) {
      issues.push({
        level: "warning",
        category: "draft",
        message: `${sessionLabel}: sessione salvata vuota (bozza parziale).`,
        sessionId: s.id,
        sessionNumber,
      });
    }

    return {
      nome_sessione: nomeSessione,
      focus_muscolare: trimOrNull(s.focus_muscolare, 200),
      durata_minuti: durataMinuti,
      notes: trimOrNull(s.note, 500),
      esercizi,
      blocchi,
    };
  });

  const totalSavedExercises = sessionsInput.reduce((sum, session) => {
    const straight = session.esercizi.length;
    const inBlocks = (session.blocchi ?? []).reduce((acc, b) => acc + b.esercizi.length, 0);
    return sum + straight + inBlocks;
  }, 0);
  if (totalSavedExercises === 0) {
    issues.push({
      level: "warning",
      category: "draft",
      message: "Scheda salvata senza esercizi: bozza valida ma incompleta.",
    });
  }

  const criticalCount = issues.filter((i) => i.level === "critical").length;
  const warningCount = issues.filter((i) => i.level === "warning").length;
  return { sessionsInput, issues, criticalCount, warningCount };
}
