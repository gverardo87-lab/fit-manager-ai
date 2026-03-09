"use client";

/**
 * PortalHeader — Identita' cliente + Health Score ring + KPI quick row.
 *
 * Layout: back nav + nome + demographics + phase badge + ring gauge + 4 KPI mini.
 */

import Link from "next/link";
import { ArrowLeft, Scale, Droplets, Activity, Dumbbell } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { HealthScoreRing } from "@/components/portal/HealthScoreRing";
import { computeAge } from "@/lib/normative-ranges";
import type { HealthScoreResult } from "@/lib/health-score";
import type { CompositionAnalysis, Severity } from "@/lib/clinical-analysis";
import type { ClientEnriched, ClinicalReadinessClientItem } from "@/types/api";

interface PortalHeaderProps {
  client: ClientEnriched;
  healthScore: HealthScoreResult;
  composition: CompositionAnalysis | null;
  readinessItem: ClinicalReadinessClientItem | null;
  pesoAttuale: number | null;
  pesoRate: number | null;
  grassoPct: number | null;
  grassoClassifica: string | null;
  bmi: number | null;
  bmiClassifica: string | null;
  compliancePct: number | null;
  /** Override back link based on ?from= context */
  backHref?: string;
  backLabel?: string;
}

const SEVERITY_BADGE: Record<Severity, string> = {
  positive: "border-emerald-200 bg-emerald-100 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  neutral: "border-zinc-200 bg-zinc-100 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  info: "border-blue-200 bg-blue-100 text-blue-700 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  warning: "border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  alert: "border-red-200 bg-red-100 text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300",
};

interface KpiMiniDef {
  label: string;
  icon: typeof Scale;
  value: string;
  sub: string;
  color: string;
}

export function PortalHeader({
  client,
  healthScore,
  composition,
  readinessItem,
  pesoAttuale,
  pesoRate,
  grassoPct,
  grassoClassifica,
  bmi,
  bmiClassifica,
  compliancePct,
  backHref,
  backLabel,
}: PortalHeaderProps) {
  const age = computeAge(client.data_nascita);
  const sesso = client.sesso === "M" ? "Uomo" : client.sesso === "F" ? "Donna" : null;
  const demographics = [age ? `${age} anni` : null, sesso].filter(Boolean).join(", ");

  const kpis: KpiMiniDef[] = [
    {
      label: "Peso",
      icon: Scale,
      value: pesoAttuale !== null ? `${pesoAttuale} kg` : "N/D",
      sub: pesoRate !== null ? `${pesoRate > 0 ? "+" : ""}${pesoRate} kg/sett` : "",
      color: "text-blue-600 dark:text-blue-400",
    },
    {
      label: "Grasso %",
      icon: Droplets,
      value: grassoPct !== null ? `${grassoPct}%` : "N/D",
      sub: grassoClassifica ?? "",
      color: "text-violet-600 dark:text-violet-400",
    },
    {
      label: "BMI",
      icon: Activity,
      value: bmi !== null ? `${bmi}` : "N/D",
      sub: bmiClassifica ?? "",
      color: "text-emerald-600 dark:text-emerald-400",
    },
    {
      label: "Compliance",
      icon: Dumbbell,
      value: compliancePct !== null ? `${compliancePct}%` : "N/D",
      sub: compliancePct !== null ? "sessioni" : "Nessun programma",
      color: "text-teal-600 dark:text-teal-400",
    },
  ];

  return (
    <div className="space-y-4">
      {/* Back nav — context-aware */}
      <div className="flex items-center gap-2">
        <Link href={backHref ?? "/monitoraggio"}>
          <Button variant="ghost" size="sm" className="gap-1.5 text-muted-foreground">
            <ArrowLeft className="h-4 w-4" />
            {backLabel ?? "Portale"}
          </Button>
        </Link>
        <span className="text-muted-foreground/40">/</span>
        <Link
          href={`/clienti/${client.id}?from=monitoraggio-${client.id}`}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Profilo
        </Link>
      </div>

      {/* Main header card */}
      <div className="rounded-xl border border-l-4 border-l-teal-500 bg-gradient-to-br from-teal-50/80 to-white p-5 shadow-sm dark:from-teal-950/40 dark:to-zinc-900">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:gap-6">
          {/* Health Score Ring */}
          <div className="flex flex-col items-center gap-1 sm:shrink-0">
            <HealthScoreRing score={healthScore.total} size={96} strokeWidth={8} />
            <span className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">
              {healthScore.label}
            </span>
          </div>

          {/* Client info */}
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight">
                {client.cognome} {client.nome}
              </h1>
              {readinessItem && (
                <Badge variant="outline" className="text-[10px] tabular-nums">
                  Readiness {readinessItem.readiness_score}%
                </Badge>
              )}
            </div>

            {demographics && (
              <p className="mt-0.5 text-sm text-muted-foreground">{demographics}</p>
            )}

            {/* Phase + Score badges */}
            <div className="mt-2 flex flex-wrap items-center gap-2">
              {composition && (
                <Badge
                  variant="outline"
                  className={`text-xs font-medium ${SEVERITY_BADGE[composition.phaseSeverity]}`}
                >
                  {composition.phaseLabel}
                </Badge>
              )}
              {healthScore.breakdown && (
                <div className="flex gap-1">
                  {Object.values(healthScore.breakdown).map((domain) => (
                    <div
                      key={domain.label}
                      className={`h-2 w-2 rounded-full ${
                        domain.severity === "positive"
                          ? "bg-emerald-500"
                          : domain.severity === "neutral"
                            ? "bg-zinc-400"
                            : domain.severity === "warning"
                              ? "bg-amber-500"
                              : domain.severity === "alert"
                                ? "bg-red-500"
                                : "bg-blue-500"
                      }`}
                      title={`${domain.label}: ${domain.score}/${domain.max}`}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* KPI quick row */}
            <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {kpis.map((kpi) => {
                const Icon = kpi.icon;
                return (
                  <div
                    key={kpi.label}
                    className="rounded-lg border bg-white/70 px-2.5 py-2 dark:bg-zinc-800/50"
                  >
                    <div className="flex items-center gap-1.5">
                      <Icon className={`h-3.5 w-3.5 ${kpi.color}`} />
                      <span className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">
                        {kpi.label}
                      </span>
                    </div>
                    <p className="mt-0.5 text-base font-extrabold tabular-nums leading-tight">
                      {kpi.value}
                    </p>
                    {kpi.sub && (
                      <p className="text-[10px] text-muted-foreground">{kpi.sub}</p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
