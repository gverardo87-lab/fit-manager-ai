"use client";

/**
 * MuscleMapPanel — body map compatta nel builder.
 *
 * Fonte preferita: analisi backend condivisa con SmartAnalysisPanel.
 * Fallback: analisi locale legacy solo se il backend non e' ancora disponibile.
 */

import { useMemo, useState } from "react";
import { useTheme } from "next-themes";
import { Activity, ChevronDown } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { MuscleMap } from "@/components/exercises/MuscleMap";
import { MUSCLE_SLUG_MAP } from "@/lib/muscle-map-utils";
import { buildBackendMuscleMapBuckets, getBackendVolumeCounts } from "@/lib/training-science-display";
import {
  computeSmartAnalysis,
  type MuscleCoverage,
  type FitnessLevel,
} from "@/lib/smart-programming";
import type { Exercise, TSAnalisiPiano } from "@/types/api";
const TEAL_COLORS_LIGHT = ["#0d9488", "#99f6e4"] as const;
const TEAL_COLORS_DARK = ["#2dd4bf", "#0f766e"] as const;
const STATUS_COLORS_LIGHT = ["#10b981", "#0ea5e9", "#f59e0b", "#ef4444"] as const;
const STATUS_COLORS_DARK = ["#34d399", "#38bdf8", "#fbbf24", "#f87171"] as const;
const TOTAL_GROUPS = 15;
const VALID_LEVELS: FitnessLevel[] = ["beginner", "intermedio", "avanzato"];

interface ExerciseInSession {
  id_esercizio: number;
  serie: number;
}
interface SessionInput {
  nome_sessione?: string;
  esercizi: ExerciseInSession[];
}

interface MuscleMapPanelProps {
  sessions: SessionInput[];
  exerciseMap: Map<number, Exercise> | null;
  livello?: string;
  sessioniPerSettimana?: number;
  backendAnalysis?: TSAnalisiPiano | null;
}

function mapLegacyCoverageToSlug(muscolo: string): string | null {
  if (muscolo === "spalle") return "shoulders";
  return muscolo in MUSCLE_SLUG_MAP ? muscolo : null;
}

export function MuscleMapPanel({
  sessions,
  exerciseMap,
  livello,
  sessioniPerSettimana,
  backendAnalysis,
}: MuscleMapPanelProps) {
  const [open, setOpen] = useState(true);
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  const legacyCoverage = useMemo<MuscleCoverage[] | null>(() => {
    if (backendAnalysis || !livello || !exerciseMap) return null;
    const validLivello = VALID_LEVELS.includes(livello as FitnessLevel)
      ? (livello as FitnessLevel)
      : "intermedio";

    const sessionsForAnalysis = sessions.map((session) => ({
      nome_sessione: session.nome_sessione ?? "",
      esercizi: session.esercizi.map((exercise) => ({
        id_esercizio: exercise.id_esercizio,
        serie: exercise.serie,
      })),
    }));

    try {
      return computeSmartAnalysis(
        sessionsForAnalysis,
        exerciseMap,
        validLivello,
        sessioniPerSettimana ?? 3,
        null,
      ).coverage;
    } catch {
      return null;
    }
  }, [backendAnalysis, livello, exerciseMap, sessions, sessioniPerSettimana]);

  const backendBuckets = useMemo(
    () => buildBackendMuscleMapBuckets(backendAnalysis?.volume),
    [backendAnalysis],
  );

  const legacyBuckets = useMemo(() => {
    const buckets = {
      optimal: [] as string[],
      suboptimal: [] as string[],
      excess: [] as string[],
      deficit: [] as string[],
    };

    if (!legacyCoverage) return buckets;

    for (const muscle of legacyCoverage) {
      if (muscle.setsPerWeek === 0) continue;
      const slugKey = mapLegacyCoverageToSlug(muscle.muscolo);
      if (!slugKey) continue;
      if (muscle.status === "optimal") buckets.optimal.push(slugKey);
      else if (muscle.status === "excess") buckets.excess.push(slugKey);
      else buckets.deficit.push(slugKey);
    }

    return buckets;
  }, [legacyCoverage]);

  const isStatusMode = Boolean(backendAnalysis?.volume || legacyCoverage);
  const primary = isStatusMode
    ? (backendAnalysis?.volume ? backendBuckets.optimal : legacyBuckets.optimal)
    : [];
  const secondary = isStatusMode
    ? (backendAnalysis?.volume ? backendBuckets.suboptimal : legacyBuckets.suboptimal)
    : [];
  const tertiary = isStatusMode
    ? (backendAnalysis?.volume ? backendBuckets.excess : legacyBuckets.excess)
    : undefined;
  const quaternary = isStatusMode
    ? (backendAnalysis?.volume ? backendBuckets.deficit : legacyBuckets.deficit)
    : undefined;

  const fallbackBuckets = useMemo(() => {
    if (isStatusMode) return { primari: [] as string[], secondari: [] as string[] };

    const primari = new Set<string>();
    const secondari = new Set<string>();

    for (const session of sessions) {
      for (const row of session.esercizi) {
        const exercise = exerciseMap?.get(row.id_esercizio);
        if (!exercise) continue;
        exercise.muscoli_primari.forEach((muscle) => primari.add(muscle));
        exercise.muscoli_secondari.forEach((muscle) => secondari.add(muscle));
      }
    }

    primari.forEach((muscle) => secondari.delete(muscle));

    return { primari: [...primari], secondari: [...secondari] };
  }, [exerciseMap, isStatusMode, sessions]);

  const displayPrimary = isStatusMode ? primary : fallbackBuckets.primari;
  const displaySecondary = isStatusMode ? secondary : fallbackBuckets.secondari;
  const displayTertiary = isStatusMode ? tertiary : undefined;
  const displayQuaternary = isStatusMode ? quaternary : undefined;

  const hasData =
    displayPrimary.length > 0 ||
    displaySecondary.length > 0 ||
    (displayTertiary?.length ?? 0) > 0 ||
    (displayQuaternary?.length ?? 0) > 0;

  const backendCounts = useMemo(
    () => getBackendVolumeCounts(backendAnalysis),
    [backendAnalysis],
  );

  const activeGroups = backendAnalysis?.volume
    ? backendBuckets.activeCount
    : legacyCoverage
      ? legacyCoverage.filter((muscle) => muscle.setsPerWeek > 0).length
      : fallbackBuckets.primari.filter((muscle) => muscle in MUSCLE_SLUG_MAP).length;

  const optimalCount = backendAnalysis?.volume
    ? backendCounts.optimal
    : legacyCoverage?.filter((muscle) => muscle.status === "optimal").length ?? 0;
  const attentionCount = backendAnalysis?.volume
    ? backendCounts.attention
    : legacyCoverage
      ? legacyCoverage.filter((muscle) => muscle.status !== "optimal" && muscle.setsPerWeek > 0).length
      : 0;

  const borderColor = isStatusMode
    ? attentionCount > 3
      ? "border-l-amber-400"
      : attentionCount === 0 && activeGroups >= 3
        ? "border-l-emerald-400"
        : "border-l-teal-400"
    : "border-l-teal-500";

  const badgeStyle = isStatusMode
    ? optimalCount >= 6 && attentionCount === 0
      ? "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800"
      : activeGroups >= 1
        ? "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800"
        : "bg-muted text-muted-foreground"
    : activeGroups >= 6
      ? "bg-teal-100 text-teal-700 border-teal-200 dark:bg-teal-900/30 dark:text-teal-400 dark:border-teal-800"
      : activeGroups >= 1
        ? "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800"
        : "bg-muted text-muted-foreground";

  const iconColor = isStatusMode
    ? attentionCount === 0 && activeGroups >= 3
      ? "text-emerald-500"
      : "text-amber-500"
    : "text-teal-500";

  const mapColors = isStatusMode
    ? (isDark ? [...STATUS_COLORS_DARK] : [...STATUS_COLORS_LIGHT])
    : (isDark ? [...TEAL_COLORS_DARK] : [...TEAL_COLORS_LIGHT]);

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card className={`border-l-4 ${borderColor} transition-all duration-200`}>
        <CardContent className="space-y-3 p-4">
          <CollapsibleTrigger asChild>
            <button className="group flex w-full items-center justify-between text-left">
              <div className="flex items-center gap-2">
                <Activity className={`h-4 w-4 ${iconColor}`} />
                <span className="text-sm font-semibold">Mappa Muscolare</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold tabular-nums ${badgeStyle}`}>
                  {activeGroups} / {TOTAL_GROUPS} gruppi
                </span>
                <ChevronDown
                  className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${open ? "rotate-180" : ""}`}
                />
              </div>
            </button>
          </CollapsibleTrigger>

          <CollapsibleContent>
            {hasData ? (
              <div className="pt-1">
                <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <span className={`inline-block h-2.5 w-2.5 rounded-full ${isStatusMode ? "bg-emerald-500" : "bg-teal-500"}`} />
                    {isStatusMode ? "Ottimale" : "Primari"}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className={`inline-block h-2.5 w-2.5 rounded-full ${isStatusMode ? "bg-sky-500" : "bg-teal-200 dark:bg-teal-700"}`} />
                    {isStatusMode ? "Sub-ottimale" : "Secondari"}
                  </span>
                  {isStatusMode && (
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-2.5 w-2.5 rounded-full bg-amber-400 dark:bg-amber-500" />
                      Eccesso
                    </span>
                  )}
                  {isStatusMode && (
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-400 dark:bg-red-500" />
                      Deficit
                    </span>
                  )}
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-zinc-200 dark:bg-zinc-700" />
                    Non allenato
                  </span>
                </div>

                <div className="flex justify-center">
                  <MuscleMap
                    muscoliPrimari={displayPrimary}
                    muscoliSecondari={displaySecondary}
                    muscoliTerziari={displayTertiary}
                    muscoliQuaternari={displayQuaternary}
                    scale={0.5}
                    colors={mapColors}
                  />
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed py-6 text-center">
                <Activity className="h-7 w-7 text-muted-foreground/30" />
                <p className="text-sm text-muted-foreground">Nessun muscolo mappato</p>
                <p className="text-xs text-muted-foreground/60">
                  Aggiungi esercizi per vedere la copertura muscolare
                </p>
              </div>
            )}
          </CollapsibleContent>
        </CardContent>
      </Card>
    </Collapsible>
  );
}
