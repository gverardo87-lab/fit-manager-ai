// src/hooks/useBuilderHandlers.ts
/**
 * Handler per il builder schede: sessioni, esercizi, blocchi, selector.
 * Tutti i handler usano applySessionsChange dal useBuilderState.
 */

import { useState, useCallback } from "react";
import type { SessionCardData } from "@/components/workouts/SessionCard";
import { createBlockCardData, type BlockCardData } from "@/components/workouts/BlockCard";
import {
  SESSION_COALESCE_FIELDS,
  EXERCISE_COALESCE_FIELDS,
  BLOCK_COALESCE_FIELDS,
} from "@/lib/builder-utils";
import {
  getSectionForCategory,
  getSmartDefaults,
  type TemplateSection,
} from "@/lib/workout-templates";
import type { WorkoutExerciseRow, Exercise, BlockType } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

export interface SelectorContext {
  sessionId: number;
  exerciseId?: number;
  sezione?: TemplateSection;
  blockId?: number;
}

type ApplyFn = (
  updater: (prev: SessionCardData[]) => SessionCardData[],
  options?: { trackHistory?: boolean; markDirty?: boolean; coalesceKey?: string },
) => void;

export interface UseBuilderHandlersOptions {
  applySessionsChange: ApplyFn;
  sessions: SessionCardData[];
  exerciseMap: Map<number, Exercise>;
  obiettivo: string;
}

// ════════════════════════════════════════════════════════════
// HOOK
// ════════════════════════════════════════════════════════════

export function useBuilderHandlers({
  applySessionsChange, sessions, exerciseMap, obiettivo,
}: UseBuilderHandlersOptions) {
  // ── Selector state ──
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [selectorContext, setSelectorContext] = useState<SelectorContext | null>(null);

  // ── Session handlers ──
  const handleUpdateSession = useCallback((sessionId: number, updates: Partial<SessionCardData>) => {
    const fields = Object.keys(updates) as (keyof SessionCardData)[];
    const coalesceField = fields.length === 1 && SESSION_COALESCE_FIELDS.has(fields[0]) ? fields[0] : null;
    applySessionsChange(
      (prev) => prev.map((s) => (s.id === sessionId ? { ...s, ...updates } : s)),
      { coalesceKey: coalesceField ? `session:${sessionId}:${coalesceField}` : undefined },
    );
  }, [applySessionsChange]);

  const handleDeleteSession = useCallback((sessionId: number) => {
    applySessionsChange((prev) => {
      const filtered = prev.filter((s) => s.id !== sessionId);
      return filtered.map((s, idx) => ({ ...s, numero_sessione: idx + 1 }));
    });
  }, [applySessionsChange]);

  const handleAddSession = useCallback(() => {
    applySessionsChange((prev) => [
      ...prev,
      { id: -(Date.now()), numero_sessione: prev.length + 1, nome_sessione: `Sessione ${prev.length + 1}`, focus_muscolare: null, durata_minuti: 60, note: null, esercizi: [], blocchi: [] },
    ]);
  }, [applySessionsChange]);

  const handleDuplicateSession = useCallback((sessionId: number) => {
    const source = sessions.find((s) => s.id === sessionId);
    if (!source) return;
    const now = Date.now();
    let tempId = now;
    applySessionsChange((prev) => [
      ...prev,
      {
        ...source, id: -(tempId++), numero_sessione: prev.length + 1,
        nome_sessione: `${source.nome_sessione} (copia)`,
        esercizi: source.esercizi.map((e, idx) => ({ ...e, id: -(tempId + idx), ordine: idx + 1 })),
        blocchi: source.blocchi.map((b, bi) => ({
          ...b, id: -(tempId + source.esercizi.length + bi + 1),
          esercizi: b.esercizi.map((e, ei) => ({ ...e, id: -(tempId + source.esercizi.length + bi * 100 + ei + 100) })),
        })),
      },
    ]);
  }, [sessions, applySessionsChange]);

  // ── Exercise handlers ──
  const handleAddExercise = useCallback((sessionId: number, sezione?: TemplateSection) => {
    setSelectorContext({ sessionId, sezione });
    setSelectorOpen(true);
  }, []);

  const handleReplaceExercise = useCallback((sessionId: number, exerciseId: number) => {
    const session = sessions.find((s) => s.id === sessionId);
    const exercise = session?.esercizi.find((e) => e.id === exerciseId);
    const sezione = exercise ? getSectionForCategory(exercise.esercizio_categoria) : undefined;
    setSelectorContext({ sessionId, exerciseId, sezione });
    setSelectorOpen(true);
  }, [sessions]);

  const handleExerciseSelected = useCallback((exercise: Exercise) => {
    if (!selectorContext) return;
    const isBlockContext = selectorContext.blockId !== undefined;
    applySessionsChange((prev) =>
      prev.map((s) => {
        if (s.id !== selectorContext.sessionId) return s;
        if (isBlockContext) {
          const blockId = selectorContext.blockId!;
          return {
            ...s,
            blocchi: s.blocchi.map((b) => {
              if (b.id !== blockId) return b;
              if (selectorContext.exerciseId) {
                return { ...b, esercizi: b.esercizi.map((e) => e.id === selectorContext.exerciseId ? { ...e, id_esercizio: exercise.id, esercizio_nome: exercise.nome, esercizio_categoria: exercise.categoria, esercizio_attrezzatura: exercise.attrezzatura } : e) };
              }
              return { ...b, esercizi: [...b.esercizi, { id: -(Date.now()), id_esercizio: exercise.id, esercizio_nome: exercise.nome, esercizio_categoria: exercise.categoria, esercizio_attrezzatura: exercise.attrezzatura, ordine: b.esercizi.length + 1, serie: 1, ripetizioni: "12-15", tempo_riposo_sec: 0, tempo_esecuzione: null, carico_kg: null, note: null }] };
            }),
          };
        }
        if (selectorContext.exerciseId) {
          return { ...s, esercizi: s.esercizi.map((e) => e.id === selectorContext.exerciseId ? { ...e, id_esercizio: exercise.id, esercizio_nome: exercise.nome, esercizio_categoria: exercise.categoria, esercizio_attrezzatura: exercise.attrezzatura } : e) };
        }
        const section = getSectionForCategory(exercise.categoria);
        const defaults = getSmartDefaults(exercise, obiettivo, section);
        return { ...s, esercizi: [...s.esercizi, { id: -(Date.now()), id_esercizio: exercise.id, esercizio_nome: exercise.nome, esercizio_categoria: exercise.categoria, esercizio_attrezzatura: exercise.attrezzatura, ordine: s.esercizi.length + 1, serie: defaults.serie, ripetizioni: defaults.ripetizioni, tempo_riposo_sec: defaults.tempo_riposo_sec, tempo_esecuzione: null, carico_kg: null, note: null }] };
      }),
    );
    setSelectorContext(null);
  }, [selectorContext, obiettivo, applySessionsChange]);

  const handleUpdateExercise = useCallback((sessionId: number, exerciseId: number, updates: Partial<WorkoutExerciseRow>) => {
    const fields = Object.keys(updates) as (keyof WorkoutExerciseRow)[];
    const coalesceField = fields.length === 1 && EXERCISE_COALESCE_FIELDS.has(fields[0]) ? fields[0] : null;
    applySessionsChange(
      (prev) => prev.map((s) => s.id === sessionId ? { ...s, esercizi: s.esercizi.map((e) => e.id === exerciseId ? { ...e, ...updates } : e) } : s),
      { coalesceKey: coalesceField ? `exercise:${sessionId}:${exerciseId}:${coalesceField}` : undefined },
    );
  }, [applySessionsChange]);

  const handleDeleteExercise = useCallback((sessionId: number, exerciseId: number) => {
    applySessionsChange((prev) => prev.map((s) => s.id === sessionId ? { ...s, esercizi: s.esercizi.filter((e) => e.id !== exerciseId).map((e, idx) => ({ ...e, ordine: idx + 1 })) } : s));
  }, [applySessionsChange]);

  const handleQuickReplace = useCallback((sessionId: number, exerciseId: number, newExerciseId: number) => {
    const newEx = exerciseMap.get(newExerciseId);
    if (!newEx) return;
    applySessionsChange((prev) => prev.map((s) => s.id !== sessionId ? s : { ...s, esercizi: s.esercizi.map((e) => e.id === exerciseId ? { ...e, id_esercizio: newEx.id, esercizio_nome: newEx.nome, esercizio_categoria: newEx.categoria, esercizio_attrezzatura: newEx.attrezzatura } : e) }));
  }, [exerciseMap, applySessionsChange]);

  // ── Block handlers ──
  const handleAddBlock = useCallback((sessionId: number, tipo: BlockType) => {
    applySessionsChange((prev) => prev.map((s) => {
      if (s.id !== sessionId) return s;
      return { ...s, blocchi: [...s.blocchi, createBlockCardData(tipo, s.blocchi.length + s.esercizi.length + 1)] };
    }));
  }, [applySessionsChange]);

  const handleUpdateBlock = useCallback((sessionId: number, blockId: number, updates: Partial<BlockCardData>) => {
    const fields = Object.keys(updates) as (keyof BlockCardData)[];
    const coalesceField = fields.length === 1 && BLOCK_COALESCE_FIELDS.has(fields[0]) ? fields[0] : null;
    applySessionsChange(
      (prev) => prev.map((s) => s.id === sessionId ? { ...s, blocchi: s.blocchi.map((b) => b.id === blockId ? { ...b, ...updates } : b) } : s),
      { coalesceKey: coalesceField ? `block:${sessionId}:${blockId}:${coalesceField}` : undefined },
    );
  }, [applySessionsChange]);

  const handleDeleteBlock = useCallback((sessionId: number, blockId: number) => {
    applySessionsChange((prev) => prev.map((s) => s.id === sessionId ? { ...s, blocchi: s.blocchi.filter((b) => b.id !== blockId) } : s));
  }, [applySessionsChange]);

  const handleDuplicateBlock = useCallback((sessionId: number, blockId: number) => {
    applySessionsChange((prev) => prev.map((s) => {
      if (s.id !== sessionId) return s;
      const source = s.blocchi.find((b) => b.id === blockId);
      if (!source) return s;
      const newId = -(Date.now());
      const dup: BlockCardData = {
        ...source, id: newId, nome: source.nome ? `${source.nome} (copia)` : null,
        ordine: Math.max(...s.blocchi.map((b) => b.ordine), 0) + 1,
        esercizi: source.esercizi.map((e, i) => ({ ...e, id: -(Date.now() + i + 1) })),
      };
      return { ...s, blocchi: [...s.blocchi, dup] };
    }));
  }, [applySessionsChange]);

  const handleAddExerciseToBlock = useCallback((sessionId: number, blockId: number) => {
    setSelectorContext({ sessionId, blockId });
    setSelectorOpen(true);
  }, []);

  const handleUpdateExerciseInBlock = useCallback((sessionId: number, blockId: number, exerciseId: number, updates: Partial<WorkoutExerciseRow>) => {
    const fields = Object.keys(updates) as (keyof WorkoutExerciseRow)[];
    const coalesceField = fields.length === 1 && EXERCISE_COALESCE_FIELDS.has(fields[0]) ? fields[0] : null;
    applySessionsChange(
      (prev) => prev.map((s) => s.id === sessionId ? { ...s, blocchi: s.blocchi.map((b) => b.id === blockId ? { ...b, esercizi: b.esercizi.map((e) => e.id === exerciseId ? { ...e, ...updates } : e) } : b) } : s),
      { coalesceKey: coalesceField ? `block-exercise:${sessionId}:${blockId}:${exerciseId}:${coalesceField}` : undefined },
    );
  }, [applySessionsChange]);

  const handleDeleteExerciseFromBlock = useCallback((sessionId: number, blockId: number, exerciseId: number) => {
    applySessionsChange((prev) => prev.map((s) => s.id === sessionId ? { ...s, blocchi: s.blocchi.map((b) => b.id === blockId ? { ...b, esercizi: b.esercizi.filter((e) => e.id !== exerciseId).map((e, i) => ({ ...e, ordine: i + 1 })) } : b) } : s));
  }, [applySessionsChange]);

  const handleReplaceExerciseInBlock = useCallback((sessionId: number, blockId: number, exerciseId: number) => {
    setSelectorContext({ sessionId, blockId, exerciseId });
    setSelectorOpen(true);
  }, []);

  const handleQuickReplaceInBlock = useCallback((sessionId: number, blockId: number, exerciseId: number, newExerciseId: number) => {
    const newEx = exerciseMap.get(newExerciseId);
    if (!newEx) return;
    applySessionsChange((prev) => prev.map((s) => s.id !== sessionId ? s : { ...s, blocchi: s.blocchi.map((b) => b.id !== blockId ? b : { ...b, esercizi: b.esercizi.map((e) => e.id !== exerciseId ? e : { ...e, id_esercizio: newEx.id, esercizio_nome: newEx.nome, esercizio_categoria: newEx.categoria, esercizio_attrezzatura: newEx.attrezzatura }) }) }));
  }, [exerciseMap, applySessionsChange]);

  const handleClearSection = useCallback((sessionId: number, sezione: TemplateSection, what: "exercises" | "blocks" | "all") => {
    applySessionsChange((prev) => prev.map((s) => {
      if (s.id !== sessionId) return s;
      const clearEx = what === "exercises" || what === "all";
      const clearBl = (what === "blocks" || what === "all") && sezione === "principale";
      return { ...s, esercizi: clearEx ? s.esercizi.filter((e) => getSectionForCategory(e.esercizio_categoria) !== sezione) : s.esercizi, blocchi: clearBl ? [] : s.blocchi };
    }));
  }, [applySessionsChange]);

  return {
    selectorOpen, setSelectorOpen, selectorContext,
    handleUpdateSession, handleDeleteSession, handleAddSession, handleDuplicateSession,
    handleAddExercise, handleReplaceExercise, handleExerciseSelected,
    handleUpdateExercise, handleDeleteExercise, handleQuickReplace,
    handleAddBlock, handleUpdateBlock, handleDeleteBlock, handleDuplicateBlock,
    handleAddExerciseToBlock, handleUpdateExerciseInBlock, handleDeleteExerciseFromBlock,
    handleReplaceExerciseInBlock, handleQuickReplaceInBlock,
    handleClearSection,
  };
}
