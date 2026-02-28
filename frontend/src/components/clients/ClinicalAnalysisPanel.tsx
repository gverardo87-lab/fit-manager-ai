// src/components/clients/ClinicalAnalysisPanel.tsx
"use client";

/**
 * ClinicalAnalysisPanel — Pannello analisi chinesiologica completo.
 *
 * 5 sezioni espandibili:
 *   1. Metriche Derivate (BMI, LBM, FFMI, WHR, MAP + Forza Relativa)
 *   2. Assessment Velocita' (rate vs soglie ACSM)
 *   3. Composizione Corporea (fase, decomposizione, proiezione)
 *   4. Simmetria Bilaterale (R/L braccia, cosce, polpacci)
 *   5. Profilo Rischio (metabolico + cardiovascolare)
 *
 * Sostituisce CompositionInsights. Non renderizza se zero dati.
 */

import { useMemo, useState } from "react";
import {
  Activity,
  Brain,
  Calculator,
  ChevronDown,
  Dumbbell,
  Heart,
  Ruler,
  Scale,
  Shield,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BAND_COLOR_CLASSES } from "@/lib/normative-ranges";

import type { Measurement, ClientGoal } from "@/types/api";
import {
  generateClinicalReport,
  type ClinicalReport,
  type Severity,
  type RateAssessment,
  type CompositionAnalysis,
  type SymmetryPair,
  type RiskProfile,
  type RiskFactor,
} from "@/lib/clinical-analysis";
import type { DerivedMetric, StrengthRatio } from "@/lib/derived-metrics";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

interface ClinicalAnalysisPanelProps {
  measurements: Measurement[];
  sesso?: string | null;
  dataNascita?: string | null;
  goals?: ClientGoal[];
}

// ════════════════════════════════════════════════════════════
// SEVERITY STYLES
// ════════════════════════════════════════════════════════════

const SEVERITY_STYLES: Record<Severity, { border: string; badge: string; dot: string }> = {
  positive: {
    border: "border-l-emerald-500",
    badge: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400",
    dot: "bg-emerald-500",
  },
  neutral: {
    border: "border-l-slate-400",
    badge: "bg-slate-100 text-slate-600 dark:bg-slate-800/30 dark:text-slate-400",
    dot: "bg-slate-400",
  },
  info: {
    border: "border-l-sky-500",
    badge: "bg-sky-50 text-sky-700 dark:bg-sky-950/30 dark:text-sky-400",
    dot: "bg-sky-500",
  },
  warning: {
    border: "border-l-amber-500",
    badge: "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400",
    dot: "bg-amber-500",
  },
  alert: {
    border: "border-l-rose-500",
    badge: "bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400",
    dot: "bg-rose-500",
  },
};

// ════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════

export function ClinicalAnalysisPanel({
  measurements,
  sesso,
  dataNascita,
  goals,
}: ClinicalAnalysisPanelProps) {
  const report = useMemo(
    () => generateClinicalReport(measurements, sesso, dataNascita, goals),
    [measurements, sesso, dataNascita, goals]
  );

  if (!report.hasData) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold">
          <Brain className="h-4 w-4 text-teal-500" />
          Analisi Clinica
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1 pt-0">
        {/* Modulo 1: Metriche Derivate */}
        {(report.derived.metrics.length > 0 || report.derived.strengthRatios.length > 0) && (
          <CollapsibleSection
            icon={Calculator}
            title="Metriche Derivate"
            defaultOpen
          >
            <DerivedMetricsSection
              metrics={report.derived.metrics}
              strengthRatios={report.derived.strengthRatios}
            />
          </CollapsibleSection>
        )}

        {/* Modulo 2: Rate Assessment */}
        {report.rateAssessments.length > 0 && (
          <CollapsibleSection
            icon={Activity}
            title="Velocita' di Cambiamento"
            defaultOpen
          >
            <RateAssessmentSection assessments={report.rateAssessments} />
          </CollapsibleSection>
        )}

        {/* Modulo 3: Composizione Corporea */}
        {report.composition && (
          <CollapsibleSection
            icon={Scale}
            title="Composizione Corporea"
            defaultOpen
          >
            <CompositionSection composition={report.composition} />
          </CollapsibleSection>
        )}

        {/* Modulo 4: Simmetria Bilaterale */}
        {report.symmetry.length > 0 && (
          <CollapsibleSection icon={Ruler} title="Simmetria Bilaterale">
            <SymmetrySection pairs={report.symmetry} />
          </CollapsibleSection>
        )}

        {/* Modulo 5: Profilo Rischio */}
        {report.riskProfile && (
          <CollapsibleSection icon={Shield} title="Profilo Rischio">
            <RiskProfileSection profile={report.riskProfile} />
          </CollapsibleSection>
        )}
      </CardContent>
    </Card>
  );
}

// ════════════════════════════════════════════════════════════
// COLLAPSIBLE SECTION
// ════════════════════════════════════════════════════════════

function CollapsibleSection({
  icon: Icon,
  title,
  defaultOpen = false,
  children,
}: {
  icon: typeof Calculator;
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-lg border bg-muted/10">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left transition-colors hover:bg-muted/30"
      >
        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="flex-1 text-xs font-semibold">{title}</span>
        <ChevronDown
          className={`h-3.5 w-3.5 text-muted-foreground transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>
      {open && <div className="border-t px-3 py-2.5">{children}</div>}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// MODULE 1: DERIVED METRICS
// ════════════════════════════════════════════════════════════

function DerivedMetricsSection({
  metrics,
  strengthRatios,
}: {
  metrics: DerivedMetric[];
  strengthRatios: StrengthRatio[];
}) {
  return (
    <div className="space-y-2">
      {/* Grid metriche derivate */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 sm:grid-cols-3">
        {metrics.map((m) => {
          const colors = m.classification
            ? BAND_COLOR_CLASSES[m.classification.color]
            : null;
          return (
            <div key={m.id} className="flex items-baseline gap-1.5">
              <span className="text-[11px] text-muted-foreground">{m.label}:</span>
              <span className="text-xs font-semibold tabular-nums">
                {m.value}
                {m.unit && (
                  <span className="ml-0.5 font-normal text-muted-foreground">{m.unit}</span>
                )}
              </span>
              {m.classification && colors && (
                <span
                  className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${colors.bg} ${colors.text}`}
                >
                  {m.classification.label}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Forza relativa */}
      {strengthRatios.length > 0 && (
        <div className="border-t pt-2">
          <div className="mb-1 flex items-center gap-1.5">
            <Dumbbell className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Forza Relativa (1RM / Peso)
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {strengthRatios.map((sr) => {
              const colors = BAND_COLOR_CLASSES[sr.levelColor];
              return (
                <div key={sr.label} className="text-center">
                  <p className="text-[10px] text-muted-foreground">{sr.label}</p>
                  <p className="text-sm font-bold tabular-nums">{sr.ratio}x</p>
                  {colors && (
                    <span
                      className={`inline-block rounded-full px-1.5 py-0.5 text-[9px] font-medium ${colors.bg} ${colors.text}`}
                    >
                      {sr.level}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Fonti */}
      <p className="text-[9px] text-muted-foreground/60">
        Fonti: {[...new Set(metrics.map((m) => m.source))].join(", ")}
      </p>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// MODULE 2: RATE ASSESSMENT
// ════════════════════════════════════════════════════════════

function RateAssessmentSection({ assessments }: { assessments: RateAssessment[] }) {
  return (
    <div className="space-y-1.5">
      {assessments.map((a) => {
        const style = SEVERITY_STYLES[a.severity];
        const sign = a.rate > 0 ? "+" : "";
        return (
          <div
            key={a.metricLabel}
            className={`flex items-start gap-2 rounded-md border-l-2 ${style.border} bg-muted/20 px-2.5 py-1.5`}
          >
            {a.rate < 0 ? (
              <TrendingDown className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            ) : (
              <TrendingUp className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            )}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold">{a.metricLabel}</span>
                <span className="text-[11px] font-medium tabular-nums">
                  {sign}{a.rate.toFixed(1)} {a.unit}/sett
                </span>
                {a.pctBodyWeight !== undefined && (
                  <span className="text-[10px] text-muted-foreground tabular-nums">
                    ({a.pctBodyWeight}%/sett)
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${style.badge}`}>
                  {a.assessment}
                </span>
              </div>
              <p className="mt-0.5 text-[9px] text-muted-foreground/70">{a.guideline}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// MODULE 3: COMPOSITION
// ════════════════════════════════════════════════════════════

function CompositionSection({ composition }: { composition: CompositionAnalysis }) {
  const style = SEVERITY_STYLES[composition.phaseSeverity];

  return (
    <div className="space-y-2">
      {/* Fase */}
      <div className={`rounded-md border-l-2 ${style.border} bg-muted/20 px-2.5 py-2`}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold">{composition.phaseLabel}</span>
          <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${style.badge}`}>
            {composition.phase === "plateau" ? "Stabile" : composition.phaseSeverity === "positive" ? "Ottimo" : composition.phaseSeverity === "warning" ? "Attenzione" : composition.phaseSeverity === "alert" ? "Critico" : ""}
          </span>
        </div>
        <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
          {composition.phaseDescription}
        </p>
      </div>

      {/* Decomposizione FM/LBM */}
      {(composition.deltaFM !== null || composition.deltaLBM !== null) && (
        <div className="rounded-md bg-muted/20 px-2.5 py-2">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Decomposizione Variazione Peso
          </p>
          <div className="flex items-center gap-3 text-xs tabular-nums">
            {composition.deltaFM !== null && (
              <span className={composition.deltaFM < 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}>
                Grasso: {composition.deltaFM > 0 ? "+" : ""}{composition.deltaFM} kg
              </span>
            )}
            {composition.deltaFM !== null && composition.deltaLBM !== null && (
              <span className="text-muted-foreground/40">|</span>
            )}
            {composition.deltaLBM !== null && (
              <span className={composition.deltaLBM > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}>
                Muscolo: {composition.deltaLBM > 0 ? "+" : ""}{composition.deltaLBM} kg
              </span>
            )}
          </div>
        </div>
      )}

      {/* Proiezione */}
      {composition.projection && (
        <div className="rounded-md bg-sky-50/50 px-2.5 py-2 dark:bg-sky-950/20">
          <p className="text-[11px]">
            <span className="font-medium text-sky-700 dark:text-sky-400">Proiezione:</span>{" "}
            <span className="text-muted-foreground">
              target {composition.projection.targetValue} kg in{" "}
              <span className="font-semibold tabular-nums">{composition.projection.weeksToGoal}</span>{" "}
              settimane (~{composition.projection.targetDate})
            </span>
          </p>
        </div>
      )}

      {/* Rate assessment ACSM */}
      {composition.rateAssessment && (
        <p className="text-[10px] leading-relaxed text-muted-foreground/80">
          {composition.rateAssessment}
        </p>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// MODULE 4: SYMMETRY
// ════════════════════════════════════════════════════════════

function SymmetrySection({ pairs }: { pairs: SymmetryPair[] }) {
  return (
    <div className="space-y-1.5">
      {pairs.map((pair) => {
        const style = SEVERITY_STYLES[pair.severity];
        return (
          <div
            key={pair.label}
            className={`rounded-md border-l-2 ${style.border} bg-muted/20 px-2.5 py-1.5`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold">{pair.label}</span>
              <div className="flex items-center gap-2 text-[11px] tabular-nums">
                <span>{pair.rightLabel} {pair.right} cm</span>
                <span className="text-muted-foreground/40">/</span>
                <span>{pair.leftLabel} {pair.left} cm</span>
                <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${style.badge}`}>
                  {"\u0394"} {pair.delta} cm ({pair.deltaPct}%)
                </span>
              </div>
            </div>
            {pair.severity !== "positive" && (
              <p className="mt-0.5 text-[10px] text-muted-foreground/80">{pair.note}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// MODULE 5: RISK PROFILE
// ════════════════════════════════════════════════════════════

function RiskFactorRow({ factor }: { factor: RiskFactor }) {
  const style = SEVERITY_STYLES[factor.severity];
  return (
    <div className="flex items-center gap-2">
      <div className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      <span className="text-[11px]">{factor.label}</span>
      <span className="text-[10px] tabular-nums text-muted-foreground">({factor.value})</span>
    </div>
  );
}

function RiskProfileSection({ profile }: { profile: RiskProfile }) {
  const overallSeverity: Severity =
    profile.metabolicRisk === "alert" || profile.cardiovascularRisk === "alert"
      ? "alert"
      : profile.metabolicRisk === "warning" || profile.cardiovascularRisk === "warning"
        ? "warning"
        : "positive";
  const style = SEVERITY_STYLES[overallSeverity];

  return (
    <div className="space-y-2">
      {/* Summary */}
      <div className={`rounded-md border-l-2 ${style.border} bg-muted/20 px-2.5 py-2`}>
        <p className="text-[11px] font-medium">{profile.summary}</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {/* Metabolico */}
        {profile.metabolicFactors.length > 0 && (
          <div>
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Metabolico
            </p>
            <div className="space-y-0.5">
              {profile.metabolicFactors.map((f, i) => (
                <RiskFactorRow key={i} factor={f} />
              ))}
            </div>
          </div>
        )}

        {/* Cardiovascolare */}
        {profile.cardiovascularFactors.length > 0 && (
          <div>
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Cardiovascolare
            </p>
            <div className="space-y-0.5">
              {profile.cardiovascularFactors.map((f, i) => (
                <RiskFactorRow key={i} factor={f} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Referral */}
      {profile.referral && (
        <div className="rounded-md bg-rose-50/50 px-2.5 py-2 dark:bg-rose-950/20">
          <div className="flex items-start gap-1.5">
            <Heart className="mt-0.5 h-3 w-3 shrink-0 text-rose-500" />
            <p className="text-[10px] leading-relaxed text-rose-700 dark:text-rose-400">
              {profile.referral}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
