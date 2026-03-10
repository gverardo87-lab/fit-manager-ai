"use client";

/**
 * ProgressiSection — Progressi clinici nel Portale Cliente.
 *
 * Visualizzazione grafica dei calcoli clinici: velocità di cambiamento (rate),
 * trend composizione FM/LBM, fase composizione, proiezione obiettivo, profilo rischio.
 */

import { useState } from "react";
import Link from "next/link";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  AlertTriangle,
  ArrowRight,
  Calendar,
  ChevronDown,
  Plus,
  TrendingUp,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

import { RateAssessmentChart, CompositionTrendChart } from "@/components/portal/ProgressiCharts";

import type { ClinicalReport, Severity } from "@/lib/clinical-analysis";
import type { Measurement } from "@/types/api";

// ── Style maps ──

const SEVERITY_BADGE: Record<string, string> = {
  positive: "border-emerald-200 bg-emerald-100 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  neutral: "border-zinc-200 bg-zinc-100 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  info: "border-blue-200 bg-blue-100 text-blue-700 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  warning: "border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  alert: "border-red-200 bg-red-100 text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300",
};

const SEVERITY_BORDER: Record<Severity, string> = {
  positive: "border-l-emerald-500",
  neutral: "border-l-zinc-400",
  info: "border-l-blue-500",
  warning: "border-l-amber-500",
  alert: "border-l-red-500",
};

interface ProgressiSectionProps {
  measurements: Measurement[];
  clinicalReport: ClinicalReport;
  clientId: number;
}

export function ProgressiSection({
  measurements,
  clinicalReport,
  clientId,
}: ProgressiSectionProps) {
  const [open, setOpen] = useState(true);

  const { rateAssessments, composition, riskProfile } = clinicalReport;
  const hasRates = rateAssessments.length > 0;
  const hasComposition = composition !== null;
  const hasRisk = riskProfile !== null;
  const hasAnyData = hasRates || hasComposition || hasRisk;

  // Overall severity for header badge
  const overallSeverity: Severity = composition?.phaseSeverity === "alert" ? "alert"
    : riskProfile?.metabolicRisk === "alert" || riskProfile?.cardiovascularRisk === "alert" ? "alert"
    : composition?.phaseSeverity === "warning" ? "warning"
    : riskProfile?.metabolicRisk === "warning" || riskProfile?.cardiovascularRisk === "warning" ? "warning"
    : "positive";

  const headerLabel = overallSeverity === "alert" ? "Attenzione"
    : overallSeverity === "warning" ? "Da monitorare"
    : hasAnyData ? "Nella norma" : null;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card>
        <CollapsibleTrigger asChild>
          <CardContent className="flex cursor-pointer items-center gap-3 py-4 hover:bg-muted/30 transition-colors">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-100 dark:bg-cyan-950/40">
              <TrendingUp className="h-5 w-5 text-cyan-600 dark:text-cyan-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold">Progressi</h3>
                {headerLabel && (
                  <Badge variant="outline" className={`text-[10px] ${SEVERITY_BADGE[overallSeverity]}`}>
                    {headerLabel}
                  </Badge>
                )}
              </div>
            </div>
            <Button
              variant="default"
              size="sm"
              className="shrink-0"
              onClick={(e) => { e.stopPropagation(); }}
            >
              <Link href={`/clienti/${clientId}/misurazioni?new=1&from=monitoraggio-${clientId}`} className="flex items-center">
                <Plus className="mr-1 h-3.5 w-3.5" />
                Nuova Misurazione
              </Link>
            </Button>
            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
          </CardContent>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="space-y-5 pt-0">
            {!hasAnyData ? (
              <div className="rounded-lg border border-dashed p-6 text-center">
                <p className="text-sm text-muted-foreground">
                  Servono almeno 2 misurazioni per calcolare i progressi.
                </p>
              </div>
            ) : (
              <>
                {/* Rate Assessment Chart */}
                {hasRates && (
                  <div className="rounded-lg border bg-zinc-50/50 p-3 dark:bg-zinc-900/50">
                    <RateAssessmentChart rateAssessments={rateAssessments} />
                  </div>
                )}

                {/* FM/LBM Composition Trend */}
                <div className="rounded-lg border bg-zinc-50/50 p-3 dark:bg-zinc-900/50">
                  <CompositionTrendChart measurements={measurements} />
                </div>

                {/* Composition Phase + Projection */}
                {hasComposition && (
                  <CompositionPhaseCard composition={composition} />
                )}

                {/* Risk Profile (metabolic + cardiovascular) */}
                {hasRisk && (
                  <RiskProfileGrid riskProfile={riskProfile} />
                )}

                {/* Referral warning */}
                {riskProfile?.referral && (
                  <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50/80 p-3 dark:border-amber-800 dark:bg-amber-950/20">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
                    <p className="text-xs text-amber-700 dark:text-amber-300">{riskProfile.referral}</p>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

// ── Sub-components ──

function CompositionPhaseCard({ composition }: { composition: NonNullable<ClinicalReport["composition"]> }) {
  return (
    <Card className={`border-l-4 ${SEVERITY_BORDER[composition.phaseSeverity]} bg-gradient-to-br from-background to-muted/30`}>
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <Badge variant="outline" className={`text-[10px] ${SEVERITY_BADGE[composition.phaseSeverity]}`}>
              {composition.phaseLabel}
            </Badge>
            <p className="mt-1.5 text-xs text-muted-foreground">{composition.phaseDescription}</p>
          </div>
        </div>

        {/* FM / LBM decomposition */}
        {(composition.deltaFM !== null || composition.deltaLBM !== null) && (
          <div className="grid grid-cols-2 gap-3">
            {composition.deltaFM !== null && (
              <div className="rounded-lg border p-2.5">
                <span className="text-[10px] font-medium text-muted-foreground">Δ Massa Grassa</span>
                <p className={`text-sm font-bold tabular-nums ${composition.deltaFM < 0 ? "text-emerald-600" : composition.deltaFM > 0 ? "text-red-500" : ""}`}>
                  {composition.deltaFM > 0 ? "+" : ""}{composition.deltaFM} kg
                </p>
              </div>
            )}
            {composition.deltaLBM !== null && (
              <div className="rounded-lg border p-2.5">
                <span className="text-[10px] font-medium text-muted-foreground">Δ Massa Magra</span>
                <p className={`text-sm font-bold tabular-nums ${composition.deltaLBM > 0 ? "text-emerald-600" : composition.deltaLBM < 0 ? "text-red-500" : ""}`}>
                  {composition.deltaLBM > 0 ? "+" : ""}{composition.deltaLBM} kg
                </p>
              </div>
            )}
          </div>
        )}

        {/* ACSM rate assessment */}
        {composition.rateAssessment && (
          <p className="text-[10px] italic text-muted-foreground">{composition.rateAssessment}</p>
        )}

        {/* Goal projection */}
        {composition.projection && (
          <div className="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50/80 p-2.5 dark:border-blue-800 dark:bg-blue-950/20">
            <Calendar className="h-4 w-4 text-blue-500 shrink-0" />
            <div className="text-xs">
              <p className="font-semibold text-blue-700 dark:text-blue-300">
                Obiettivo {composition.projection.targetValue} kg
              </p>
              <p className="text-blue-600/80 dark:text-blue-400/80">
                Stima: {format(parseISO(composition.projection.targetDate), "d MMMM yyyy", { locale: it })}
                <span className="ml-1">({Math.round(composition.projection.weeksToGoal)} settimane)</span>
              </p>
            </div>
            <ArrowRight className="ml-auto h-3.5 w-3.5 text-blue-400" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RiskProfileGrid({ riskProfile }: { riskProfile: NonNullable<ClinicalReport["riskProfile"]> }) {
  const SEVERITY_LABEL: Record<Severity, string> = {
    positive: "Nella norma", neutral: "Neutro", info: "Informativo", warning: "Attenzione", alert: "Rischio",
  };

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <div className="rounded-lg border p-3">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold">Profilo Metabolico</p>
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
      <div className="rounded-lg border p-3">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold">Profilo Cardiovascolare</p>
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
      {riskProfile.summary && (
        <p className="sm:col-span-2 text-xs text-muted-foreground">{riskProfile.summary}</p>
      )}
    </div>
  );
}
