"use client";

/**
 * MuscleMapPanel — Pannello Copertura Muscolare nel Workout Builder
 *
 * Quando `livello` è fornito (caso normale nel builder):
 *   - Calcola la copertura NSCA via computeSmartAnalysis
 *   - Colora i muscoli per stato: emerald = ottimale, amber = eccesso/deficit
 *   - Legenda allineata con SmartAnalysisPanel → la body map è la sua rappresentazione spaziale
 *
 * Senza `livello` (fallback):
 *   - Comportamento originale: teal per primari/secondari
 *
 * - Coverage badge: "X / 14 gruppi" aggiornato live
 * - Collassabile. Si aggiorna ad ogni modifica della scheda (reactive).
 * - Empty state quando non ci sono ancora esercizi.
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
import { MUSCLE_SLUG_MAP, SMART_TO_SLUG_MAP } from "@/lib/muscle-map-utils";
import {
  computeSmartAnalysis,
  type MuscleCoverage,
  type FitnessLevel,
} from "@/lib/smart-programming";
import type { Exercise } from "@/types/api";

// ── Palette teal — fallback senza livello
const TEAL_COLORS_LIGHT = ["#0d9488", "#99f6e4"] as const;
const TEAL_COLORS_DARK  = ["#2dd4bf", "#0f766e"] as const;

// ── Palette status-aware — allineata a SmartAnalysisPanel (emerald / amber / red)
// Stessa semantica delle barre: ottimale → emerald, eccesso → amber, deficit → red
const STATUS_COLORS_LIGHT = ["#10b981", "#f59e0b", "#ef4444"]; // emerald-500, amber-500, red-500
const STATUS_COLORS_DARK  = ["#34d399", "#fbbf24", "#f87171"]; // emerald-400, amber-400, red-400

const TOTAL_GROUPS = Object.keys(MUSCLE_SLUG_MAP).length; // 14
const VALID_LEVELS: FitnessLevel[] = ["beginner", "intermedio", "avanzato"];

// ── Tipi minimi — compatibili con SessionCardData / WorkoutExerciseRow
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
  /** Abilita la colorazione per stato di copertura NSCA (allineata con SmartAnalysisPanel) */
  livello?: string;
  sessioniPerSettimana?: number;
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function MuscleMapPanel({
  sessions,
  exerciseMap,
  livello,
  sessioniPerSettimana,
}: MuscleMapPanelProps) {
  const [open, setOpen] = useState(true);
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  // ── Copertura NSCA (quando livello disponibile)
  const coverage = useMemo<MuscleCoverage[] | null>(() => {
    if (!livello || !exerciseMap) return null;
    const validLivello = VALID_LEVELS.includes(livello as FitnessLevel)
      ? (livello as FitnessLevel)
      : "intermedio";

    const sessionsForAnalysis = sessions.map(s => ({
      nome_sessione: s.nome_sessione ?? "",
      esercizi: s.esercizi.map(e => ({
        id_esercizio: e.id_esercizio,
        serie: e.serie,
      })),
    }));

    try {
      const analysis = computeSmartAnalysis(
        sessionsForAnalysis,
        exerciseMap,
        validLivello,
        sessioniPerSettimana ?? 3,
        null,
      );
      return analysis.coverage;
    } catch {
      return null;
    }
  }, [sessions, exerciseMap, livello, sessioniPerSettimana]);

  // ── Status mode: muscoli separati per i 3 stati NSCA
  // Allineati 1:1 con SmartAnalysisPanel: emerald=ottimale / amber=eccesso / red=deficit
  const { muscoliOttimali, muscoliEccesso, muscoliDeficit } = useMemo(() => {
    if (!coverage) return {
      muscoliOttimali: [] as string[],
      muscoliEccesso:  [] as string[],
      muscoliDeficit:  [] as string[],
    };

    const ottimali: string[] = [];
    const eccesso:  string[] = [];
    const deficit:  string[] = [];

    for (const cov of coverage) {
      if (cov.setsPerWeek === 0) continue; // non allenato → defaultFill (grigio)
      const slugKey = SMART_TO_SLUG_MAP[cov.muscolo];
      if (!slugKey) continue;
      if (cov.status === "optimal") ottimali.push(slugKey);
      else if (cov.status === "excess") eccesso.push(slugKey);
      else deficit.push(slugKey); // "deficit"
    }

    return { muscoliOttimali: ottimali, muscoliEccesso: eccesso, muscoliDeficit: deficit };
  }, [coverage]);

  // ── Fallback teal: aggrega primari/secondari dagli esercizi (senza info di volume)
  const { muscoliPrimari, muscoliSecondari } = useMemo(() => {
    if (coverage) return { muscoliPrimari: [] as string[], muscoliSecondari: [] as string[] };

    const primari  = new Set<string>();
    const secondari = new Set<string>();

    for (const session of sessions) {
      for (const row of session.esercizi) {
        const ex = exerciseMap?.get(row.id_esercizio);
        if (!ex) continue;
        ex.muscoli_primari.forEach((m) => primari.add(m));
        ex.muscoli_secondari.forEach((m) => secondari.add(m));
      }
    }

    primari.forEach((m) => secondari.delete(m));
    return { muscoliPrimari: [...primari], muscoliSecondari: [...secondari] };
  }, [sessions, exerciseMap, coverage]);

  // ── Dati effettivi per MuscleMap (status mode o fallback)
  const isStatusMode = coverage !== null;
  const displayPrimary   = isStatusMode ? muscoliOttimali : muscoliPrimari;
  const displaySecondary = isStatusMode ? muscoliEccesso  : muscoliSecondari;
  const displayTertiary  = isStatusMode ? muscoliDeficit  : undefined;
  const mapColors: string[] = isStatusMode
    ? (isDark ? STATUS_COLORS_DARK : STATUS_COLORS_LIGHT)
    : (isDark ? [...TEAL_COLORS_DARK] : [...TEAL_COLORS_LIGHT]); // spread → string[] da readonly tuple

  const hasData = displayPrimary.length > 0 || displaySecondary.length > 0 || (displayTertiary?.length ?? 0) > 0;

  // ── KPI per badge e bordo
  const activeGroups = isStatusMode
    ? (coverage?.filter(c => c.setsPerWeek > 0).length ?? 0)
    : [...muscoliPrimari].filter((m) => m in MUSCLE_SLUG_MAP).length;

  const deficitCount = coverage?.filter(c => c.status === "deficit" && c.setsPerWeek > 0).length ?? 0;
  const optimalCount = coverage?.filter(c => c.status === "optimal").length ?? 0;

  // Colore bordo — stessa logica di SmartAnalysisPanel
  const borderColor = isStatusMode
    ? (deficitCount > 3
        ? "border-l-amber-400"
        : deficitCount === 0 && activeGroups >= 3
          ? "border-l-emerald-400"
          : "border-l-teal-400")
    : "border-l-teal-500";

  // Badge colore
  const badgeStyle = isStatusMode
    ? (optimalCount >= 6 && deficitCount === 0
        ? "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800"
        : activeGroups >= 1
          ? "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800"
          : "bg-muted text-muted-foreground")
    : (activeGroups >= 6
        ? "bg-teal-100 text-teal-700 border-teal-200 dark:bg-teal-900/30 dark:text-teal-400 dark:border-teal-800"
        : activeGroups >= 1
          ? "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800"
          : "bg-muted text-muted-foreground");

  // Icon color
  const iconColor = isStatusMode
    ? (deficitCount === 0 && activeGroups >= 3 ? "text-emerald-500" : "text-amber-500")
    : "text-teal-500";

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card className={`border-l-4 ${borderColor} transition-all duration-200`}>
        <CardContent className="p-4 space-y-3">

          {/* ── Header ── */}
          <CollapsibleTrigger asChild>
            <button className="flex w-full items-center justify-between text-left group">
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

          {/* ── Body collassabile ── */}
          <CollapsibleContent>
            {hasData ? (
              <div className="pt-1">
                {/* Legenda */}
                <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <span className={`inline-block h-2.5 w-2.5 rounded-full ${isStatusMode ? "bg-emerald-500" : "bg-teal-500"}`} />
                    {isStatusMode ? "Ottimale" : "Primari"}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className={`inline-block h-2.5 w-2.5 rounded-full ${isStatusMode ? "bg-amber-400 dark:bg-amber-500" : "bg-teal-200 dark:bg-teal-700"}`} />
                    {isStatusMode ? "Eccesso" : "Secondari"}
                  </span>
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

                {/* MuscleMap a scala compatta (0.5) */}
                <div className="flex justify-center">
                  <MuscleMap
                    muscoliPrimari={displayPrimary}
                    muscoliSecondari={displaySecondary}
                    muscoliTerziari={displayTertiary}
                    scale={0.5}
                    colors={mapColors}
                  />
                </div>
              </div>
            ) : (
              // Empty state — nessun esercizio ancora
              <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed py-6 text-center">
                <Activity className="h-7 w-7 text-muted-foreground/30" />
                <p className="text-sm text-muted-foreground">
                  Nessun muscolo mappato
                </p>
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
