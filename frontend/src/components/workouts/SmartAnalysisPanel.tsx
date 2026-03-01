// src/components/workouts/SmartAnalysisPanel.tsx
"use client";

/**
 * Pannello di analisi SMART per il builder schede allenamento.
 *
 * Mostra 5 sezioni di analisi calcolate dal motore smart-programming.ts:
 * 1. Copertura Muscolare — set/muscolo/settimana vs target NSCA
 * 2. Volume Totale — set/settimana vs target per livello
 * 3. Varieta Biomeccanica — piani, catene, contrazioni
 * 4. Conflitti Recupero — overlap muscolare tra sessioni consecutive
 * 5. Score Sicurezza — % esercizi senza controindicazioni
 *
 * Pattern: Safety Overview Panel (Collapsible card nel builder).
 */

import { useMemo, useState } from "react";
import { BarChart3, ChevronDown, AlertTriangle, CheckCircle2, Activity } from "lucide-react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";

import {
  computeSmartAnalysis,
  type SmartAnalysis,
  type MuscleCoverage,
  type FitnessLevel,
} from "@/lib/smart-programming";
import type { Exercise, ExerciseSafetyEntry } from "@/types/api";

// ════════════════════════════════════════════════════════════
// PROPS
// ════════════════════════════════════════════════════════════

interface SmartAnalysisPanelProps {
  sessions: Array<{
    nome_sessione: string;
    esercizi: Array<{ id_esercizio: number; serie: number }>;
  }>;
  exerciseMap: Map<number, Exercise>;
  livello: string;
  sessioniPerSettimana: number;
  safetyMap: Record<number, ExerciseSafetyEntry> | null;
}

// ════════════════════════════════════════════════════════════
// COVERAGE STATUS COLORS
// ════════════════════════════════════════════════════════════

const STATUS_COLORS = {
  deficit: {
    bg: "bg-red-100 dark:bg-red-950/40",
    text: "text-red-700 dark:text-red-400",
    bar: "bg-red-500",
  },
  optimal: {
    bg: "bg-emerald-100 dark:bg-emerald-950/40",
    text: "text-emerald-700 dark:text-emerald-400",
    bar: "bg-emerald-500",
  },
  excess: {
    bg: "bg-amber-100 dark:bg-amber-950/40",
    text: "text-amber-700 dark:text-amber-400",
    bar: "bg-amber-500",
  },
} as const;

const STATUS_LABELS = {
  deficit: "Deficit",
  optimal: "Ottimale",
  excess: "Eccesso",
} as const;

const MUSCLE_LABELS: Record<string, string> = {
  petto: "Petto",
  dorsali: "Dorsali",
  spalle: "Spalle",
  bicipiti: "Bicipiti",
  tricipiti: "Tricipiti",
  quadricipiti: "Quadricipiti",
  femorali: "Femorali",
  glutei: "Glutei",
  polpacci: "Polpacci",
  core: "Core",
  trapezio: "Trapezio",
  adduttori: "Adduttori",
  avambracci: "Avambracci",
};

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function SmartAnalysisPanel({
  sessions,
  exerciseMap,
  livello,
  sessioniPerSettimana,
  safetyMap,
}: SmartAnalysisPanelProps) {
  const [expanded, setExpanded] = useState(false);

  const analysis = useMemo<SmartAnalysis | null>(() => {
    // Serve almeno 1 esercizio per analizzare
    const hasExercises = sessions.some(s => s.esercizi.length > 0);
    if (!hasExercises) return null;

    const VALID_LEVELS: FitnessLevel[] = ["beginner", "intermedio", "avanzato"];
    const validLivello: FitnessLevel = VALID_LEVELS.includes(livello as FitnessLevel)
      ? (livello as FitnessLevel)
      : "intermedio";

    return computeSmartAnalysis(
      sessions,
      exerciseMap,
      validLivello,
      sessioniPerSettimana,
      safetyMap,
    );
  }, [sessions, exerciseMap, livello, sessioniPerSettimana, safetyMap]);

  if (!analysis) return null;

  // KPI riassuntivi
  const deficitCount = analysis.coverage.filter(c => c.status === "deficit").length;
  const excessCount = analysis.coverage.filter(c => c.status === "excess").length;
  const optimalCount = analysis.coverage.filter(c => c.status === "optimal").length;
  const conflictCount = analysis.recoveryConflicts.length;

  // Colore bordo sinistro
  const borderColor = deficitCount > 3 || conflictCount > 2
    ? "border-l-amber-400"
    : deficitCount === 0 && conflictCount === 0
      ? "border-l-emerald-400"
      : "border-l-teal-400";

  return (
    <Collapsible open={expanded} onOpenChange={setExpanded}>
      <Card className={`border-l-4 ${borderColor} transition-all duration-200`}>
        <CardContent className="p-4 space-y-3">
          {/* Header — sempre visibile */}
          <CollapsibleTrigger asChild>
            <button className="flex items-center justify-between w-full text-left group">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4.5 w-4.5 text-teal-600 dark:text-teal-400" />
                <span className="text-sm font-semibold">Analisi Smart</span>
              </div>
              <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${expanded ? "rotate-180" : ""}`} />
            </button>
          </CollapsibleTrigger>

          {/* KPI mini-row */}
          <div className="grid grid-cols-4 gap-2">
            <div className="rounded-lg bg-muted/50 px-2 py-2 text-center">
              <div className="text-lg font-extrabold tracking-tighter tabular-nums">{analysis.volume.totalSetsPerWeek}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Set/Sett</div>
            </div>
            <div className={`rounded-lg ${STATUS_COLORS.optimal.bg} px-2 py-2 text-center`}>
              <div className={`text-lg font-extrabold tracking-tighter tabular-nums ${STATUS_COLORS.optimal.text}`}>{optimalCount}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Ottimali</div>
            </div>
            <div className={`rounded-lg ${STATUS_COLORS.deficit.bg} px-2 py-2 text-center`}>
              <div className={`text-lg font-extrabold tracking-tighter tabular-nums ${STATUS_COLORS.deficit.text}`}>{deficitCount}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Deficit</div>
            </div>
            <div className="rounded-lg bg-muted/50 px-2 py-2 text-center">
              <div className={`text-lg font-extrabold tracking-tighter tabular-nums ${analysis.safetyScore >= 80 ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"}`}>
                {analysis.safetyScore}%
              </div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Safety</div>
            </div>
          </div>

          {/* Contenuto espanso */}
          <CollapsibleContent className="space-y-4">
            <Separator />

            {/* 1. Copertura Muscolare */}
            <section>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Copertura Muscolare (set/settimana)
              </div>
              <div className="space-y-1.5">
                {analysis.coverage
                  .filter(c => c.setsPerWeek > 0 || c.status === "deficit")
                  .map((cov) => (
                    <CoverageRow key={cov.muscolo} coverage={cov} />
                  ))}
              </div>
            </section>

            {/* 2. Volume Totale */}
            <section>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Volume Totale
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <Progress
                    value={Math.min(100, (analysis.volume.totalSetsPerWeek / analysis.volume.targetRange.max) * 100)}
                    className="h-2"
                  />
                </div>
                <span className={`text-xs font-medium ${STATUS_COLORS[analysis.volume.status].text}`}>
                  {analysis.volume.totalSetsPerWeek}/{analysis.volume.targetRange.min}-{analysis.volume.targetRange.max}
                </span>
                <Badge variant="outline" className={`text-[10px] ${STATUS_COLORS[analysis.volume.status].text}`}>
                  {STATUS_LABELS[analysis.volume.status]}
                </Badge>
              </div>
            </section>

            {/* 3. Varieta Biomeccanica */}
            <section>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Varieta Biomeccanica
              </div>
              <div className="grid grid-cols-3 gap-2">
                <BiomechanicsChip label="Piani" data={analysis.biomechanics.planes} />
                <BiomechanicsChip label="Catene" data={analysis.biomechanics.chains} />
                <BiomechanicsChip label="Contrazioni" data={analysis.biomechanics.contractions} />
              </div>
            </section>

            {/* 4. Conflitti Recupero */}
            {analysis.recoveryConflicts.length > 0 && (
              <section>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Conflitti Recupero
                </div>
                <div className="space-y-2">
                  {analysis.recoveryConflicts.map((conflict, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <AlertTriangle className={`h-3.5 w-3.5 shrink-0 mt-0.5 ${conflict.severity === "alert" ? "text-red-500" : "text-amber-500"}`} />
                      <div>
                        <span className="font-medium">{conflict.sessionA}</span>
                        <span className="text-muted-foreground"> → </span>
                        <span className="font-medium">{conflict.sessionB}</span>
                        <div className="text-muted-foreground mt-0.5">
                          {conflict.muscoli.join(", ")} — servono {conflict.oreNecessarie}h, disponibili {conflict.oreDisponibili}h
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* 5. Safety Score */}
            {analysis.safetyScore < 100 && (
              <section>
                <div className="flex items-center gap-2">
                  {analysis.safetyScore >= 80 ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                  ) : (
                    <Activity className="h-3.5 w-3.5 text-amber-500" />
                  )}
                  <span className="text-xs">
                    <span className="font-medium">{analysis.safetyScore}%</span>
                    <span className="text-muted-foreground"> degli esercizi sono compatibili con il profilo clinico</span>
                  </span>
                </div>
              </section>
            )}
          </CollapsibleContent>
        </CardContent>
      </Card>
    </Collapsible>
  );
}

// ════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ════════════════════════════════════════════════════════════

function CoverageRow({ coverage }: { coverage: MuscleCoverage }) {
  const colors = STATUS_COLORS[coverage.status];
  const pct = coverage.target.max > 0
    ? Math.min(100, (coverage.setsPerWeek / coverage.target.max) * 100)
    : 0;

  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] w-24 truncate text-right text-muted-foreground">
        {MUSCLE_LABELS[coverage.muscolo] ?? coverage.muscolo}
      </span>
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${colors.bar}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-[10px] font-medium tabular-nums w-8 text-right ${colors.text}`}>
        {coverage.setsPerWeek}
      </span>
    </div>
  );
}

function BiomechanicsChip({ label, data }: { label: string; data: Record<string, number> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((sum, [, v]) => sum + v, 0);
  const variety = entries.length;

  return (
    <div className="rounded-lg bg-muted/50 px-2 py-1.5 text-center">
      <div className="text-xs font-semibold tabular-nums">{variety}</div>
      <div className="text-[10px] text-muted-foreground">{label}</div>
      {entries.length > 0 && total > 0 && (
        <div className="text-[9px] text-muted-foreground mt-0.5 truncate" title={entries.map(([k, v]) => `${k}: ${v}`).join(", ")}>
          {entries.slice(0, 2).map(([k, v]) => `${k} ${Math.round(v / total * 100)}%`).join(", ")}
        </div>
      )}
    </div>
  );
}
