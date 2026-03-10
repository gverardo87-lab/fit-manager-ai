// src/components/workouts/ExerciseDetailPanel.tsx
"use client";

/**
 * Pannello riassuntivo inline per un esercizio dentro il builder schede.
 *
 * Mostra muscoli, classificazione, setup excerpt, note sicurezza,
 * relazioni actionable (con quick-swap) e deep-link alla pagina esercizio.
 *
 * Dati esercizio dal exerciseMap (gia' cached). Relazioni lazy-loaded.
 */

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowUp, ArrowDown, Shuffle, ArrowRight, RefreshCw } from "lucide-react";
import { getMediaUrl } from "@/lib/media";
import { getReplacementReason, getReplacementScore } from "@/lib/exercise-replacement";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

import { useExerciseRelations } from "@/hooks/useExercises";
import {
  MUSCLE_LABELS,
  CATEGORY_LABELS,
  EQUIPMENT_LABELS,
  DIFFICULTY_LABELS,
  PATTERN_LABELS,
  RELATION_TYPE_LABELS,
} from "@/components/exercises/exercise-constants";
import type { Exercise, ExerciseSafetyEntry } from "@/types/api";

interface ExerciseDetailPanelProps {
  exercise: Exercise;
  exerciseId: number;
  safety?: ExerciseSafetyEntry;
  safetyEntries?: Record<number, ExerciseSafetyEntry>;
  exerciseMap?: Map<number, Exercise>;
  schedaId?: number;
  /** Contesto di provenienza della scheda (es. "allenamenti") — propagato nel deep-link */
  parentFrom?: string | null;
  onQuickReplace?: (newExerciseId: number) => void;
}

const RELATION_ICONS: Record<string, React.ElementType> = {
  progression: ArrowUp,
  regression: ArrowDown,
  variation: Shuffle,
};
const RELATION_COLORS: Record<string, string> = {
  progression: "text-emerald-500",
  regression: "text-amber-500",
  variation: "text-blue-500",
};

function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  return text.slice(0, max).trimEnd() + "...";
}

function ExerciseThumbnails({ exerciseId }: { exerciseId: number }) {
  const [startVisible, setStartVisible] = useState(true);
  const [endVisible, setEndVisible] = useState(true);

  const startUrl = getMediaUrl(`/media/exercises/${exerciseId}/exec_start.jpg`);
  const endUrl = getMediaUrl(`/media/exercises/${exerciseId}/exec_end.jpg`);

  if (!startVisible && !endVisible) return null;

  return (
    <div className="flex gap-2">
      {startVisible && startUrl && (
        <div className="relative">
          {/* eslint-disable-next-line @next/next/no-img-element -- dynamic backend media path */}
          <img
            src={startUrl}
            alt="Posizione iniziale"
            className="h-24 w-auto rounded-lg border object-contain bg-white"
            onError={() => setStartVisible(false)}
            loading="lazy"
          />
          <span className="absolute bottom-0.5 left-0.5 bg-black/60 text-white text-[9px] px-1.5 py-0.5 rounded-sm">
            Start
          </span>
        </div>
      )}
      {endVisible && endUrl && (
        <div className="relative">
          {/* eslint-disable-next-line @next/next/no-img-element -- dynamic backend media path */}
          <img
            src={endUrl}
            alt="Posizione finale"
            className="h-24 w-auto rounded-lg border object-contain bg-white"
            onError={() => setEndVisible(false)}
            loading="lazy"
          />
          <span className="absolute bottom-0.5 left-0.5 bg-black/60 text-white text-[9px] px-1.5 py-0.5 rounded-sm">
            End
          </span>
        </div>
      )}
    </div>
  );
}

export function ExerciseDetailPanel({
  exercise,
  exerciseId,
  safety: _safety,
  safetyEntries,
  exerciseMap,
  schedaId,
  parentFrom,
  onQuickReplace,
}: ExerciseDetailPanelProps) {
  const { data: relations } = useExerciseRelations(exerciseId);

  // Relazioni ordinate per coerenza con il contesto attuale (con spiegazione breve)
  const groupedRelations = useMemo(() => {
    if (!relations) return { progressions: [], regressions: [], variations: [] };
    const grouped = {
      progressions: [] as Array<{
        id: number;
        related_exercise_id: number;
        related_exercise_nome: string;
        tipo_relazione: string;
        score: number;
        reason: string;
        isAvoid: boolean;
      }>,
      regressions: [] as Array<{
        id: number;
        related_exercise_id: number;
        related_exercise_nome: string;
        tipo_relazione: string;
        score: number;
        reason: string;
        isAvoid: boolean;
      }>,
      variations: [] as Array<{
        id: number;
        related_exercise_id: number;
        related_exercise_nome: string;
        tipo_relazione: string;
        score: number;
        reason: string;
        isAvoid: boolean;
      }>,
    };

    for (const rel of relations) {
      const relatedExercise = exerciseMap?.get(rel.related_exercise_id);
      const relSafety = safetyEntries?.[rel.related_exercise_id];
      const isAvoid = relSafety?.severity === "avoid";
      const hasCaution = relSafety?.severity === "caution";
      const enriched = {
        ...rel,
        score: getReplacementScore(exercise, relatedExercise, rel.tipo_relazione, hasCaution),
        reason: getReplacementReason(exercise, relatedExercise, rel.tipo_relazione, hasCaution),
        isAvoid,
      };
      if (rel.tipo_relazione === "progression") grouped.progressions.push(enriched);
      else if (rel.tipo_relazione === "regression") grouped.regressions.push(enriched);
      else grouped.variations.push(enriched);
    }

    grouped.progressions.sort((a, b) => b.score - a.score);
    grouped.regressions.sort((a, b) => b.score - a.score);
    grouped.variations.sort((a, b) => b.score - a.score);

    return grouped;
  }, [relations, exerciseMap, safetyEntries, exercise]);

  const hasRelations = relations && relations.length > 0;

  return (
    <div className="col-span-full rounded-lg border bg-muted/30 p-3 space-y-3 animate-in fade-in slide-in-from-top-1 duration-200">
      {/* Illustrazioni esecuzione */}
      <ExerciseThumbnails exerciseId={exerciseId} />

      {/* Muscoli */}
      <div className="flex flex-wrap gap-1.5">
        {exercise.muscoli_primari.map((m) => (
          <span
            key={m}
            className="inline-flex items-center gap-1 rounded-full border border-blue-300 bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700 dark:border-blue-700 dark:bg-blue-900/20 dark:text-blue-400"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-blue-600 dark:bg-blue-400" />
            {MUSCLE_LABELS[m] || m}
          </span>
        ))}
        {exercise.muscoli_secondari.map((m) => (
          <span
            key={m}
            className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50/50 px-2 py-0.5 text-[11px] font-medium text-blue-400 dark:border-blue-800 dark:bg-blue-900/10 dark:text-blue-400/70"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-blue-300 dark:bg-blue-500/50" />
            {MUSCLE_LABELS[m] || m}
          </span>
        ))}
      </div>

      {/* Classificazione badges */}
      <div className="flex flex-wrap gap-1.5">
        <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
          {CATEGORY_LABELS[exercise.categoria] || exercise.categoria}
        </span>
        <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
          {PATTERN_LABELS[exercise.pattern_movimento] || exercise.pattern_movimento}
        </span>
        <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
          {EQUIPMENT_LABELS[exercise.attrezzatura] || exercise.attrezzatura}
        </span>
        <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
          {DIFFICULTY_LABELS[exercise.difficolta] || exercise.difficolta}
        </span>
      </div>

      {/* Setup excerpt */}
      {exercise.setup && (
        <p className="text-[11px] text-muted-foreground leading-relaxed">
          {truncate(exercise.setup, 150)}
        </p>
      )}

      {/* Note sicurezza */}
      {exercise.note_sicurezza && (
        <p className="text-[11px] text-amber-600 dark:text-amber-400 leading-relaxed">
          {truncate(exercise.note_sicurezza, 150)}
        </p>
      )}

      {/* Relazioni actionable */}
      {hasRelations && (
        <>
          <Separator />
          <div className="space-y-1.5">
            {(["progressions", "regressions", "variations"] as const).map((group) => {
              const items = groupedRelations[group];
              if (items.length === 0) return null;
              return items.map((rel) => {
                const Icon = RELATION_ICONS[rel.tipo_relazione] || Shuffle;
                const color = RELATION_COLORS[rel.tipo_relazione] || "text-muted-foreground";

                return (
                  <div key={rel.id} className="flex items-center gap-1.5 text-[11px]">
                    <Icon className={`h-3 w-3 shrink-0 ${color}`} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5">
                        <span className="truncate">{rel.related_exercise_nome}</span>
                        <span className="text-[9px] text-muted-foreground shrink-0">
                          {RELATION_TYPE_LABELS[rel.tipo_relazione] ?? rel.tipo_relazione}
                        </span>
                      </div>
                      <p className="text-[10px] text-muted-foreground truncate">
                        {rel.reason}
                      </p>
                    </div>
                    {rel.isAvoid && (
                      <span className="text-[9px] text-red-500 shrink-0">Evitare</span>
                    )}
                    {onQuickReplace && !rel.isAvoid && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-5 px-1.5 text-[10px] text-primary hover:text-primary"
                        onClick={(e) => {
                          e.stopPropagation();
                          onQuickReplace(rel.related_exercise_id);
                        }}
                      >
                        <RefreshCw className="h-2.5 w-2.5 mr-0.5" />
                        Sostituisci
                      </Button>
                    )}
                  </div>
                );
              });
            })}
          </div>
        </>
      )}

      {/* Deep link */}
      <div className="pt-1">
        <Link
          href={`/esercizi/${exerciseId}${schedaId ? `?from=scheda-${schedaId}${parentFrom ? `&parentFrom=${parentFrom}` : ""}` : ""}`}
          className="inline-flex items-center gap-1 text-[11px] text-primary hover:underline"
        >
          Vedi dettaglio completo
          <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
