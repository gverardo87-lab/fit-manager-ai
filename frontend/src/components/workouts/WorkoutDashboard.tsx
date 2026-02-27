// src/components/workouts/WorkoutDashboard.tsx
"use client";

/**
 * Dashboard unificato analisi scheda allenamento.
 *
 * Sostituisce QualityReviewPanel + WorkoutAnalysisPanel con un singolo
 * panel collapsabile a 3 colonne:
 *   1. Volume muscolare (barre orizzontali)
 *   2. Bilancio push/pull, upper/lower + copertura pattern
 *   3. Problemi concreti (issues dal quality engine)
 *
 * Filosofia: FATTI VISIVI, non voti. Zero score 0-100, zero livelli.
 */

import { useState } from "react";
import {
  BarChart3,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  XCircle,
  CheckCircle2,
  Check,
  X as XIcon,
  Circle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { WorkoutAnalysisData } from "@/lib/workout-analysis-engine";
import type { QualityIssue } from "@/lib/workout-quality-engine";
import { PATTERN_LABELS } from "@/components/exercises/exercise-constants";

// ════════════════════════════════════════════════════════════
// CONSTANTS
// ════════════════════════════════════════════════════════════

const BALANCE_THRESHOLD = 0.6;

const FUNDAMENTAL_PATTERNS = ["squat", "hinge", "push_h", "push_v", "pull_h", "pull_v"];
const COMPLEMENTARY_PATTERNS = ["core", "rotation", "carry"];

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
    <div className="flex items-center gap-1.5">
      <span className="w-[72px] shrink-0 text-[10px] text-muted-foreground truncate text-right">
        {label}
      </span>
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-primary transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-[28px] shrink-0 text-[10px] font-medium tabular-nums text-right">
        {totalSets % 1 === 0 ? totalSets : totalSets.toFixed(1)}
      </span>
    </div>
  );
}

/** Dual-bar bilancio (push/pull o upper/lower) */
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
  const max = Math.max(valueA, valueB);
  const min = Math.min(valueA, valueB);
  const isBalanced = total === 0 || (max > 0 && min / max >= BALANCE_THRESHOLD);

  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between text-[10px]">
        <span className="text-muted-foreground">
          {labelA} <span className="font-medium tabular-nums">{valueA}</span>
        </span>
        <Badge
          variant="outline"
          className={`text-[8px] px-1 py-0 leading-tight ${
            isBalanced
              ? "border-emerald-300 text-emerald-600 dark:border-emerald-700 dark:text-emerald-400"
              : "border-amber-300 text-amber-600 dark:border-amber-700 dark:text-amber-400"
          }`}
        >
          {isBalanced ? "OK" : "Squilibrato"}
        </Badge>
        <span className="text-muted-foreground">
          <span className="font-medium tabular-nums">{valueB}</span> {labelB}
        </span>
      </div>
      <div className="flex h-1.5 rounded-full overflow-hidden bg-muted">
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

/** Griglia copertura pattern: ✓/✗ per fondamentali, ○ per complementari */
function PatternCoverageGrid({ patternsUsed }: { patternsUsed: Set<string> }) {
  return (
    <div className="space-y-1">
      <span className="text-[10px] font-medium text-muted-foreground">Pattern</span>
      <div className="grid grid-cols-3 gap-x-2 gap-y-0.5">
        {FUNDAMENTAL_PATTERNS.map((pat) => {
          const covered = patternsUsed.has(pat);
          return (
            <div key={pat} className="flex items-center gap-1">
              {covered ? (
                <Check className="h-3 w-3 text-emerald-500" />
              ) : (
                <XIcon className="h-3 w-3 text-red-400" />
              )}
              <span className={`text-[10px] ${covered ? "text-foreground" : "text-muted-foreground"}`}>
                {PATTERN_LABELS[pat] ?? pat}
              </span>
            </div>
          );
        })}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-0.5">
        {COMPLEMENTARY_PATTERNS.map((pat) => {
          const covered = patternsUsed.has(pat);
          return (
            <div key={pat} className="flex items-center gap-1">
              {covered ? (
                <Check className="h-3 w-3 text-emerald-500" />
              ) : (
                <Circle className="h-2.5 w-2.5 text-muted-foreground/40" />
              )}
              <span className={`text-[10px] ${covered ? "text-foreground" : "text-muted-foreground/60"}`}>
                {PATTERN_LABELS[pat] ?? pat}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/** Singolo problema nella colonna issues */
function IssueRow({ issue }: { issue: QualityIssue }) {
  const Icon = issue.severity === "critical" ? XCircle : AlertTriangle;
  const color = issue.severity === "critical"
    ? "text-red-500 dark:text-red-400"
    : "text-amber-500 dark:text-amber-400";

  return (
    <div className="flex items-start gap-1.5">
      <Icon className={`h-3 w-3 mt-0.5 shrink-0 ${color}`} />
      <div>
        <p className="text-[10px] text-muted-foreground leading-tight">{issue.message}</p>
        {issue.suggestion && (
          <p className="text-[10px] text-primary leading-tight mt-0.5">{issue.suggestion}</p>
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

interface WorkoutDashboardProps {
  analysisData: WorkoutAnalysisData | null;
  issues: QualityIssue[];
}

export function WorkoutDashboard({ analysisData, issues }: WorkoutDashboardProps) {
  const [expanded, setExpanded] = useState(false);

  if (!analysisData) return null;

  const hasPrincipal = analysisData.totalPrincipalExercises > 0;

  // Empty state
  if (!hasPrincipal) {
    return (
      <div className="rounded-lg border bg-card" data-print-hide>
        <div className="flex items-center gap-3 px-4 py-2.5">
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            Aggiungi esercizi nella sezione principale per vedere l&apos;analisi
          </span>
        </div>
      </div>
    );
  }

  const warningCount = issues.length;

  return (
    <div className="rounded-lg border bg-card" data-print-hide>
      {/* ── Header compatto ── */}
      <Button
        variant="ghost"
        className="w-full flex items-center justify-between px-4 py-2.5 h-auto"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3 flex-wrap">
          <BarChart3 className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Analisi Scheda</span>
          <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
            <span className="tabular-nums font-medium">
              {analysisData.totalPrincipalSets} serie
            </span>
            <span className="text-muted-foreground/40">·</span>
            <span className="tabular-nums">
              Push:Pull {analysisData.balance.push}:{analysisData.balance.pull}
            </span>
            <span className="text-muted-foreground/40">·</span>
            <span className="tabular-nums">
              Upper:Lower {analysisData.balance.upper}:{analysisData.balance.lower}
            </span>
            <span className="text-muted-foreground/40">·</span>
            <span>{analysisData.musclesCovered} muscoli</span>
            {warningCount > 0 && (
              <>
                <span className="text-muted-foreground/40">·</span>
                <span className="flex items-center gap-0.5 text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="h-3 w-3" />
                  {warningCount}
                </span>
              </>
            )}
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground shrink-0" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
        )}
      </Button>

      {/* ── Contenuto espanso — griglia 3 colonne ── */}
      {expanded && (
        <div className="border-t px-4 pb-4 pt-3">
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {/* ── Colonna 1: Volume Muscolare ── */}
            <div>
              <span className="text-[10px] font-medium text-muted-foreground block mb-1.5">
                Volume per Muscolo
              </span>
              <div className="space-y-0.5">
                {analysisData.muscleVolume.map((mv) => (
                  <MuscleBar
                    key={mv.muscle}
                    label={mv.label}
                    totalSets={mv.totalSets}
                    maxSets={Math.max(...analysisData.muscleVolume.map((m) => m.totalSets), 1)}
                  />
                ))}
              </div>
            </div>

            {/* ── Colonna 2: Bilancio & Copertura Pattern ── */}
            <div className="space-y-3">
              <div>
                <span className="text-[10px] font-medium text-muted-foreground block mb-1.5">
                  Bilancio
                </span>
                <div className="space-y-2">
                  <BalanceBar
                    labelA="Push"
                    valueA={analysisData.balance.push}
                    labelB="Pull"
                    valueB={analysisData.balance.pull}
                    colorA="bg-sky-400 dark:bg-sky-500"
                    colorB="bg-indigo-400 dark:bg-indigo-500"
                  />
                  <BalanceBar
                    labelA="Upper"
                    valueA={analysisData.balance.upper}
                    labelB="Lower"
                    valueB={analysisData.balance.lower}
                    colorA="bg-violet-400 dark:bg-violet-500"
                    colorB="bg-emerald-400 dark:bg-emerald-500"
                  />
                </div>
              </div>
              <PatternCoverageGrid patternsUsed={analysisData.patternsUsed} />
            </div>

            {/* ── Colonna 3: Problemi ── */}
            <div>
              <span className="text-[10px] font-medium text-muted-foreground block mb-1.5">
                Problemi
              </span>
              {issues.length === 0 ? (
                <div className="flex items-center gap-1.5 py-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                  <span className="text-[10px] text-emerald-600 dark:text-emerald-400">
                    Nessun problema rilevato
                  </span>
                </div>
              ) : (
                <div className="space-y-1.5">
                  {issues.map((issue, idx) => (
                    <IssueRow key={idx} issue={issue} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
