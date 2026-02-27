// src/components/workouts/WorkoutAnalysisPanel.tsx
"use client";

/**
 * Panel collapsabile per analisi volume e bilancio della scheda.
 *
 * 3 sezioni:
 *   1. Volume muscolare (barre orizzontali per gruppo)
 *   2. Bilancio push/pull e upper/lower (dual-bar)
 *   3. Profilo biomeccanico (chip con conteggio)
 *
 * Pattern: identico a QualityReviewPanel.
 */

import { useState } from "react";
import { BarChart3, ChevronDown, ChevronUp, Dumbbell } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type {
  WorkoutAnalysisData,
  DistributionEntry,
} from "@/lib/workout-analysis-engine";

// ════════════════════════════════════════════════════════════
// CONSTANTS
// ════════════════════════════════════════════════════════════

const BALANCE_THRESHOLD = 0.6; // ratio < 0.6 = squilibrato

// ════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ════════════════════════════════════════════════════════════

/** Barra volume per singolo muscolo */
function MuscleBar({
  label,
  totalSets,
  maxSets,
}: {
  label: string;
  totalSets: number;
  maxSets: number;
}) {
  const pct = maxSets > 0 ? (totalSets / maxSets) * 100 : 0;
  return (
    <div className="flex items-center gap-2">
      <span className="w-[90px] shrink-0 text-[11px] text-muted-foreground truncate text-right">
        {label}
      </span>
      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-primary transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-[36px] shrink-0 text-[11px] font-medium tabular-nums text-right">
        {totalSets % 1 === 0 ? totalSets : totalSets.toFixed(1)}
      </span>
    </div>
  );
}

/** Indicatore bilancio dual-bar (es. push vs pull) */
function BalanceBar({
  labelA,
  valueA,
  labelB,
  valueB,
  colorA,
  colorB,
}: {
  labelA: string;
  valueA: number;
  labelB: string;
  valueB: number;
  colorA: string;
  colorB: string;
}) {
  const total = valueA + valueB;
  const pctA = total > 0 ? (valueA / total) * 100 : 50;
  const isBalanced =
    total === 0 || (total > 0 && Math.min(valueA, valueB) / Math.max(valueA, valueB) >= BALANCE_THRESHOLD);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-muted-foreground">
          {labelA} <span className="font-medium tabular-nums">{valueA}</span>
        </span>
        <Badge
          variant="outline"
          className={`text-[9px] px-1.5 py-0 ${
            isBalanced
              ? "border-emerald-300 text-emerald-600 dark:border-emerald-700 dark:text-emerald-400"
              : "border-amber-300 text-amber-600 dark:border-amber-700 dark:text-amber-400"
          }`}
        >
          {isBalanced ? "Bilanciato" : "Squilibrato"}
        </Badge>
        <span className="text-[11px] text-muted-foreground">
          <span className="font-medium tabular-nums">{valueB}</span> {labelB}
        </span>
      </div>
      <div className="flex h-2 rounded-full overflow-hidden bg-muted">
        {total > 0 ? (
          <>
            <div
              className={`h-full ${colorA} transition-all duration-300`}
              style={{ width: `${pctA}%` }}
            />
            <div
              className={`h-full ${colorB} transition-all duration-300`}
              style={{ width: `${100 - pctA}%` }}
            />
          </>
        ) : (
          <div className="h-full w-full bg-muted" />
        )}
      </div>
    </div>
  );
}

/** Chip per una entry di distribuzione biomeccanica */
function DistributionChip({ entry, total }: { entry: DistributionEntry; total: number }) {
  const pct = total > 0 ? Math.round((entry.count / total) * 100) : 0;
  return (
    <div className="inline-flex items-center gap-1 rounded-full bg-muted/60 px-2 py-0.5 text-[10px]">
      <span className="font-medium">{entry.label}</span>
      <span className="text-muted-foreground tabular-nums">{entry.count}</span>
      <span className="text-muted-foreground/60 tabular-nums">({pct}%)</span>
    </div>
  );
}

/** Riga distribuzione biomeccanica con label + chips */
function DistributionRow({
  label,
  entries,
}: {
  label: string;
  entries: DistributionEntry[];
}) {
  if (entries.length === 0) return null;
  const total = entries.reduce((sum, e) => sum + e.count, 0);
  return (
    <div className="flex items-start gap-2">
      <span className="w-[70px] shrink-0 text-[11px] text-muted-foreground pt-0.5">
        {label}
      </span>
      <div className="flex flex-wrap gap-1">
        {entries.map((e) => (
          <DistributionChip key={e.value} entry={e} total={total} />
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

interface WorkoutAnalysisPanelProps {
  data: WorkoutAnalysisData | null;
}

export function WorkoutAnalysisPanel({ data }: WorkoutAnalysisPanelProps) {
  const [expanded, setExpanded] = useState(false);

  if (!data) return null;

  const hasPrincipal = data.totalPrincipalExercises > 0;

  // Empty state
  if (!hasPrincipal) {
    return (
      <div className="rounded-lg border bg-card" data-print-hide>
        <div className="flex items-center gap-3 px-4 py-2.5">
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            Aggiungi esercizi per vedere l&apos;analisi volume
          </span>
        </div>
      </div>
    );
  }

  // Compact header summary
  const pushPullLabel = `Push:Pull ${data.balance.push}:${data.balance.pull}`;

  return (
    <div className="rounded-lg border bg-card" data-print-hide>
      {/* ── Header compatto ── */}
      <Button
        variant="ghost"
        className="w-full flex items-center justify-between px-4 py-2.5 h-auto"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <BarChart3 className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Analisi Volume</span>
          <span className="text-[10px] text-muted-foreground">
            {data.totalPrincipalSets} serie principali
            {" · "}{pushPullLabel}
            {" · "}{data.musclesCovered} muscoli
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </Button>

      {/* ── Dettagli espansi ── */}
      {expanded && (
        <div className="px-4 pb-4 space-y-5 border-t">
          {/* Sezione 1: Volume Muscolare */}
          <div className="pt-3">
            <div className="flex items-center gap-2 mb-2">
              <Dumbbell className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground">
                Volume per Muscolo (serie)
              </span>
            </div>
            <div className="space-y-1">
              {data.muscleVolume.map((mv) => (
                <MuscleBar
                  key={mv.muscle}
                  label={mv.label}
                  totalSets={mv.totalSets}
                  maxSets={Math.max(...data.muscleVolume.map((m) => m.totalSets), 1)}
                />
              ))}
            </div>
          </div>

          {/* Sezione 2: Bilancio */}
          <div>
            <span className="text-xs font-medium text-muted-foreground block mb-2">
              Bilancio
            </span>
            <div className="space-y-3">
              <BalanceBar
                labelA="Push"
                valueA={data.balance.push}
                labelB="Pull"
                valueB={data.balance.pull}
                colorA="bg-sky-400 dark:bg-sky-500"
                colorB="bg-indigo-400 dark:bg-indigo-500"
              />
              <BalanceBar
                labelA="Upper"
                valueA={data.balance.upper}
                labelB="Lower"
                valueB={data.balance.lower}
                colorA="bg-violet-400 dark:bg-violet-500"
                colorB="bg-emerald-400 dark:bg-emerald-500"
              />
            </div>
          </div>

          {/* Sezione 3: Profilo Biomeccanico */}
          {(data.forceTypes.length > 0 ||
            data.lateralPatterns.length > 0 ||
            data.kineticChains.length > 0 ||
            data.movementPlanes.length > 0 ||
            data.contractionTypes.length > 0) && (
            <div>
              <span className="text-xs font-medium text-muted-foreground block mb-2">
                Profilo Biomeccanico
              </span>
              <div className="space-y-1.5">
                <DistributionRow label="Forza" entries={data.forceTypes} />
                <DistributionRow label="Lateralita'" entries={data.lateralPatterns} />
                <DistributionRow label="Catena" entries={data.kineticChains} />
                <DistributionRow label="Piano" entries={data.movementPlanes} />
                <DistributionRow label="Contraz." entries={data.contractionTypes} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
