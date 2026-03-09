"use client";

/**
 * CardiovascularSection — Profilo cardiovascolare: PA, FC, classificazione ESH, rischio.
 */

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, Heart, Plus, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { MeasurementChart } from "@/components/clients/MeasurementChart";
import type { RiskProfile, Severity } from "@/lib/clinical-analysis";
import type { Measurement, Metric } from "@/types/api";

// Metric IDs
const ID_FC_RIPOSO = 17;
const ID_PA_SISTOLICA = 18;
const ID_PA_DIASTOLICA = 19;

interface CardiovascularSectionProps {
  measurements: Measurement[];
  metrics: Metric[];
  riskProfile: RiskProfile | null;
  sesso: string | null;
  dataNascita: string | null;
  clientId: number;
}

const SEVERITY_BADGE: Record<string, string> = {
  positive: "border-emerald-200 bg-emerald-100 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  neutral: "border-zinc-200 bg-zinc-100 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  info: "border-blue-200 bg-blue-100 text-blue-700 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  warning: "border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  alert: "border-red-200 bg-red-100 text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300",
};

const SEVERITY_LABEL: Record<Severity, string> = {
  positive: "Nella norma",
  neutral: "Neutro",
  info: "Informativo",
  warning: "Attenzione",
  alert: "Rischio",
};

function hasMetricData(measurements: Measurement[], metricId: number): boolean {
  return measurements.some((m) => m.valori.some((v) => v.id_metrica === metricId));
}

export function CardiovascularSection({
  measurements,
  metrics,
  riskProfile,
  sesso,
  dataNascita,
  clientId,
}: CardiovascularSectionProps) {
  const [open, setOpen] = useState(true);

  const hasPAData = hasMetricData(measurements, ID_PA_SISTOLICA);
  const hasFCData = hasMetricData(measurements, ID_FC_RIPOSO);
  const hasAnyData = hasPAData || hasFCData;

  // Severity complessiva per il bordo
  const overallSeverity: Severity = riskProfile
    ? ([riskProfile.cardiovascularRisk, riskProfile.metabolicRisk].includes("alert")
        ? "alert"
        : [riskProfile.cardiovascularRisk, riskProfile.metabolicRisk].includes("warning")
          ? "warning"
          : "positive")
    : "neutral";

  const borderColor =
    overallSeverity === "alert"
      ? "border-l-red-500"
      : overallSeverity === "warning"
        ? "border-l-amber-500"
        : "border-l-rose-400";

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className={`rounded-xl border border-l-4 ${borderColor} bg-white shadow-sm dark:bg-zinc-900`}>
        <CollapsibleTrigger asChild>
          <button type="button" className="flex w-full items-center justify-between p-4 text-left">
            <div className="flex items-center gap-2">
              <Heart className="h-4 w-4 text-rose-500" />
              <h2 className="text-sm font-semibold">Profilo Cardiovascolare</h2>
              {riskProfile && (
                <Badge variant="outline" className={`text-[10px] ${SEVERITY_BADGE[riskProfile.cardiovascularRisk]}`}>
                  {SEVERITY_LABEL[riskProfile.cardiovascularRisk]}
                </Badge>
              )}
            </div>
            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="space-y-4 border-t px-4 pb-4 pt-3">
            {!hasAnyData && (
              <div className="rounded-lg border border-dashed p-6 text-center">
                <p className="text-sm text-muted-foreground">
                  Nessun dato cardiovascolare registrato (PA, FC riposo)
                </p>
              </div>
            )}

            {/* Chart PA Sistolica + Diastolica */}
            {hasPAData && (
              <div>
                <p className="mb-2 text-xs font-semibold text-muted-foreground">Pressione Arteriosa</p>
                <div className="rounded-lg border bg-zinc-50/50 p-3 dark:bg-zinc-900/50">
                  <MeasurementChart
                    measurements={measurements}
                    metrics={metrics}
                    sesso={sesso}
                    dataNascita={dataNascita}
                    defaultMetric1Id={ID_PA_SISTOLICA}
                    defaultMetric2Id={ID_PA_DIASTOLICA}
                  />
                </div>
              </div>
            )}

            {/* Chart FC Riposo */}
            {hasFCData && (
              <div>
                <p className="mb-2 text-xs font-semibold text-muted-foreground">Frequenza Cardiaca a Riposo</p>
                <div className="rounded-lg border bg-zinc-50/50 p-3 dark:bg-zinc-900/50">
                  <MeasurementChart
                    measurements={measurements}
                    metrics={metrics}
                    sesso={sesso}
                    dataNascita={dataNascita}
                    defaultMetric1Id={ID_FC_RIPOSO}
                  />
                </div>
              </div>
            )}

            {/* Risk Profile */}
            {riskProfile && (
              <div className="grid gap-3 sm:grid-cols-2">
                {/* Cardiovascolare */}
                <div className="rounded-lg border p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold">Rischio Cardiovascolare</p>
                    <Badge variant="outline" className={`text-[10px] ${SEVERITY_BADGE[riskProfile.cardiovascularRisk]}`}>
                      {SEVERITY_LABEL[riskProfile.cardiovascularRisk]}
                    </Badge>
                  </div>
                  <div className="mt-2 space-y-1">
                    {riskProfile.cardiovascularFactors.map((f) => (
                      <div key={f.label} className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">{f.label}</span>
                        <span className="font-medium tabular-nums">{f.value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Metabolico */}
                <div className="rounded-lg border p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold">Rischio Metabolico</p>
                    <Badge variant="outline" className={`text-[10px] ${SEVERITY_BADGE[riskProfile.metabolicRisk]}`}>
                      {SEVERITY_LABEL[riskProfile.metabolicRisk]}
                    </Badge>
                  </div>
                  <div className="mt-2 space-y-1">
                    {riskProfile.metabolicFactors.map((f) => (
                      <div key={f.label} className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">{f.label}</span>
                        <span className="font-medium tabular-nums">{f.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Summary + Referral */}
            {riskProfile?.summary && (
              <p className="text-xs text-muted-foreground">{riskProfile.summary}</p>
            )}

            {riskProfile?.referral && (
              <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50/80 p-3 dark:border-amber-800 dark:bg-amber-950/20">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
                <p className="text-xs text-amber-700 dark:text-amber-300">{riskProfile.referral}</p>
              </div>
            )}

            {/* CTA */}
            <div className="flex justify-end">
              <Link href={`/clienti/${clientId}/misurazioni?new=1&from=monitoraggio-${clientId}`}>
                <Button size="sm" variant="outline" className="gap-1.5">
                  <Plus className="h-3.5 w-3.5" />
                  Registra Misurazioni
                </Button>
              </Link>
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
