"use client";

/**
 * CompositionSection — Composizione corporea, metriche derivate, fase, correlazioni.
 *
 * Sezione piu' ricca del portale: chart duale peso+grasso%, griglia metriche derivate,
 * card fase composizione, rapporti forza NSCA, insight correlazioni.
 */

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, Plus, Scale, TrendingDown, TrendingUp, Minus, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { MeasurementChart } from "@/components/clients/MeasurementChart";
import type { ClinicalReport, Severity } from "@/lib/clinical-analysis";
import type { CorrelationInsight } from "@/lib/metric-correlations";
import type { ClinicalFreshnessSignal, Measurement, Metric } from "@/types/api";

interface CompositionSectionProps {
  measurements: Measurement[];
  metrics: Metric[];
  clinicalReport: ClinicalReport;
  correlations: CorrelationInsight[];
  sesso: string | null;
  dataNascita: string | null;
  clientId: number;
  measurementFreshness: ClinicalFreshnessSignal | null;
}

const SEVERITY_BORDER: Record<Severity, string> = {
  positive: "border-l-emerald-500",
  neutral: "border-l-zinc-400",
  info: "border-l-blue-500",
  warning: "border-l-amber-500",
  alert: "border-l-red-500",
};

const SEVERITY_BG: Record<Severity, string> = {
  positive: "bg-emerald-50/50 dark:bg-emerald-950/20",
  neutral: "bg-zinc-50/50 dark:bg-zinc-900/20",
  info: "bg-blue-50/50 dark:bg-blue-950/20",
  warning: "bg-amber-50/50 dark:bg-amber-950/20",
  alert: "bg-red-50/50 dark:bg-red-950/20",
};

const SEVERITY_BADGE: Record<string, string> = {
  positive: "border-emerald-200 bg-emerald-100 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  neutral: "border-zinc-200 bg-zinc-100 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  info: "border-blue-200 bg-blue-100 text-blue-700 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  warning: "border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  alert: "border-red-200 bg-red-100 text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300",
};

export function CompositionSection({
  measurements,
  metrics,
  clinicalReport,
  correlations,
  sesso,
  dataNascita,
  clientId,
  measurementFreshness,
}: CompositionSectionProps) {
  const [open, setOpen] = useState(true);
  const { composition, derived } = clinicalReport;
  const hasData = measurements.length >= 2;
  const measurementAlert =
    measurementFreshness && (measurementFreshness.status === "warning" || measurementFreshness.status === "critical")
      ? measurementFreshness
      : null;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className="rounded-xl border border-l-4 border-l-teal-500 bg-white shadow-sm dark:bg-zinc-900">
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="flex w-full items-center justify-between p-4 text-left"
          >
            <div className="flex items-center gap-2">
              <Scale className="h-4 w-4 text-teal-600 dark:text-teal-400" />
              <h2 className="text-sm font-semibold">Composizione Corporea</h2>
              {composition && (
                <Badge variant="outline" className={`text-[10px] ${SEVERITY_BADGE[composition.phaseSeverity]}`}>
                  {composition.phaseLabel}
                </Badge>
              )}
              {measurementAlert && (
                <Badge
                  variant="outline"
                  className={`gap-1 text-[10px] ${
                    measurementAlert.status === "critical"
                      ? "border-red-300 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300"
                      : "border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
                  }`}
                >
                  <AlertTriangle className="h-3 w-3" />
                  {measurementAlert.days_since_last ?? 0}gg
                </Badge>
              )}
            </div>
            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="space-y-4 border-t px-4 pb-4 pt-3">
            {/* Chart Peso + Grasso% */}
            {hasData ? (
              <div className="rounded-lg border bg-zinc-50/50 p-3 dark:bg-zinc-900/50">
                <MeasurementChart
                  measurements={measurements}
                  metrics={metrics}
                  sesso={sesso}
                  dataNascita={dataNascita}
                  defaultMetric1Id={1}
                  defaultMetric2Id={3}
                />
              </div>
            ) : (
              <div className="rounded-lg border border-dashed p-6 text-center">
                <p className="text-sm text-muted-foreground">
                  Servono almeno 2 misurazioni per visualizzare i trend
                </p>
              </div>
            )}

            {/* Fase Composizione */}
            {composition && (
              <div className={`rounded-lg border border-l-4 ${SEVERITY_BORDER[composition.phaseSeverity]} ${SEVERITY_BG[composition.phaseSeverity]} p-3`}>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-xs font-semibold">{composition.phaseLabel}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{composition.phaseDescription}</p>
                  </div>
                </div>

                {/* Decomposizione FM/LBM */}
                {(composition.deltaFM !== null || composition.deltaLBM !== null) && (
                  <div className="mt-2 flex gap-3">
                    {composition.deltaFM !== null && (
                      <div className="flex items-center gap-1 text-xs">
                        {composition.deltaFM < 0 ? (
                          <TrendingDown className="h-3 w-3 text-emerald-500" />
                        ) : composition.deltaFM > 0 ? (
                          <TrendingUp className="h-3 w-3 text-amber-500" />
                        ) : (
                          <Minus className="h-3 w-3 text-zinc-400" />
                        )}
                        <span className="font-medium">
                          Grasso: {composition.deltaFM > 0 ? "+" : ""}{composition.deltaFM.toFixed(1)} kg
                        </span>
                      </div>
                    )}
                    {composition.deltaLBM !== null && (
                      <div className="flex items-center gap-1 text-xs">
                        {composition.deltaLBM > 0 ? (
                          <TrendingUp className="h-3 w-3 text-emerald-500" />
                        ) : composition.deltaLBM < 0 ? (
                          <TrendingDown className="h-3 w-3 text-red-500" />
                        ) : (
                          <Minus className="h-3 w-3 text-zinc-400" />
                        )}
                        <span className="font-medium">
                          Muscolo: {composition.deltaLBM > 0 ? "+" : ""}{composition.deltaLBM.toFixed(1)} kg
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Proiezione */}
                {composition.projection && (
                  <div className="mt-2 rounded-md border bg-white/60 px-2.5 py-1.5 dark:bg-zinc-800/60">
                    <p className="text-[11px] text-muted-foreground">
                      Al ritmo attuale → <strong>{composition.projection.targetValue} kg</strong> entro{" "}
                      <strong>
                        {new Date(`${composition.projection.targetDate}T00:00:00`).toLocaleDateString("it-IT", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        })}
                      </strong>{" "}
                      ({composition.projection.weeksToGoal} settimane)
                    </p>
                  </div>
                )}

                {composition.rateAssessment && (
                  <p className="mt-1.5 text-[10px] text-muted-foreground">{composition.rateAssessment}</p>
                )}
              </div>
            )}

            {/* Metriche Derivate Grid */}
            {derived.metrics.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-semibold text-muted-foreground">Metriche Derivate</p>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {derived.metrics.map((m) => (
                    <div key={m.id} className="rounded-lg border px-2.5 py-2">
                      <p className="text-[10px] font-medium text-muted-foreground">{m.label}</p>
                      <p className="text-base font-extrabold tabular-nums">{m.value.toFixed(1)}</p>
                      <div className="flex items-center gap-1">
                        <span className="text-[10px] text-muted-foreground">{m.unit}</span>
                        {m.classification && (
                          <Badge variant="outline" className={`text-[9px] px-1 py-0 ${SEVERITY_BADGE[m.classification.color] ?? ""}`}>
                            {m.classification.label}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Rapporti Forza NSCA */}
            {derived.strengthRatios.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-semibold text-muted-foreground">Forza Relativa (NSCA)</p>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  {derived.strengthRatios.map((sr) => (
                    <div key={sr.label} className="flex items-center justify-between rounded-lg border px-2.5 py-2">
                      <div>
                        <p className="text-xs font-medium">{sr.label}</p>
                        <p className="text-[10px] text-muted-foreground">{sr.ratio.toFixed(2)}x BW</p>
                      </div>
                      <Badge
                        variant="outline"
                        className="text-[10px]"
                        style={{ color: sr.levelColor, borderColor: sr.levelColor }}
                      >
                        {sr.level}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Insight Correlazioni */}
            {correlations.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-semibold text-muted-foreground">Insight</p>
                <div className="space-y-2">
                  {correlations.map((insight) => (
                    <div
                      key={insight.pairId}
                      className={`rounded-lg border border-l-4 ${SEVERITY_BORDER[insight.severity]} p-2.5`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="text-xs font-semibold">{insight.label}</p>
                          <p className="mt-0.5 text-[11px] text-muted-foreground">{insight.text}</p>
                        </div>
                        <Badge variant="outline" className={`shrink-0 text-[9px] ${SEVERITY_BADGE[insight.severity]}`}>
                          {insight.severity === "positive" ? "Positivo" : insight.severity === "warning" ? "Attenzione" : insight.severity === "alert" ? "Critico" : "Neutro"}
                        </Badge>
                      </div>
                      {insight.values && (
                        <p className="mt-1 text-[10px] font-medium tabular-nums text-muted-foreground">{insight.values}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CTA */}
            <div className="flex justify-end">
              <Link href={`/clienti/${clientId}/misurazioni?new=1&from=monitoraggio-${clientId}`}>
                <Button size="sm" variant="outline" className="gap-1.5">
                  <Plus className="h-3.5 w-3.5" />
                  Nuova Misurazione
                </Button>
              </Link>
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
