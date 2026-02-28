// src/components/clients/CompositionInsights.tsx
"use client";

/**
 * CompositionInsights — Card analisi composizione corporea inter-metrica.
 *
 * Mostra insight da coppie correlate:
 *   - Peso + Grasso → composizione corporea
 *   - Vita + Fianchi → WHR + distribuzione
 *   - PA Sistolica + Diastolica → profilo cardiovascolare
 *
 * Non renderizza se nessuna coppia ha dati sufficienti.
 * Posizionato in ProgressiTab tra GoalsSummary e KPI cards.
 */

import { useMemo } from "react";
import { Brain, Heart, Ruler, Scale } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import type { Measurement } from "@/types/api";
import {
  analyzeCorrelations,
  type CorrelationInsight,
  type InsightSeverity,
} from "@/lib/metric-correlations";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

interface CompositionInsightsProps {
  measurements: Measurement[];
  sesso?: string | null;
}

// ════════════════════════════════════════════════════════════
// CONSTANTS
// ════════════════════════════════════════════════════════════

const ICON_MAP: Record<string, typeof Scale> = {
  Scale,
  Ruler,
  Heart,
};

const SEVERITY_STYLES: Record<
  InsightSeverity,
  { badge: string; border: string }
> = {
  positive: {
    badge:
      "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400",
    border: "border-l-emerald-500",
  },
  neutral: {
    badge:
      "bg-slate-50 text-slate-600 dark:bg-slate-900/30 dark:text-slate-400",
    border: "border-l-slate-400",
  },
  warning: {
    badge:
      "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400",
    border: "border-l-amber-500",
  },
  alert: {
    badge: "bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400",
    border: "border-l-rose-500",
  },
};

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function CompositionInsights({
  measurements,
  sesso,
}: CompositionInsightsProps) {
  const insights = useMemo(
    () => analyzeCorrelations(measurements, sesso),
    [measurements, sesso]
  );

  // Non renderizzare se nessuna coppia ha dati
  if (insights.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold">
          <Brain className="h-4 w-4 text-teal-500" />
          Analisi Composizione
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2">
          {insights.map((insight) => (
            <InsightRow key={insight.pairId} insight={insight} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ════════════════════════════════════════════════════════════
// SUB-COMPONENT
// ════════════════════════════════════════════════════════════

function InsightRow({ insight }: { insight: CorrelationInsight }) {
  const style = SEVERITY_STYLES[insight.severity];
  const pair = [
    { id: "peso-grasso", icon: "Scale" },
    { id: "vita-fianchi", icon: "Ruler" },
    { id: "pa", icon: "Heart" },
  ].find((p) => p.id === insight.pairId);
  const Icon = ICON_MAP[pair?.icon ?? "Scale"] ?? Scale;

  return (
    <div
      className={`rounded-lg border border-l-4 ${style.border} bg-muted/20 px-3 py-2.5`}
    >
      <div className="flex items-start gap-2">
        <Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
        <div className="min-w-0 flex-1 space-y-0.5">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold">{insight.label}</span>
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${style.badge}`}
            >
              {insight.text}
            </span>
          </div>
          {insight.values && (
            <p className="text-[11px] tabular-nums text-muted-foreground">
              {insight.values}
            </p>
          )}
          {insight.details && (
            <p className="text-[11px] leading-relaxed text-muted-foreground/80">
              {insight.details}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
