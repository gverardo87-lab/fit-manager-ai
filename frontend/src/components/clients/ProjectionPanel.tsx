// src/components/clients/ProjectionPanel.tsx
"use client";

/**
 * ProjectionPanel — Macchina del Tempo per il cliente.
 *
 * 3 layer indipendenti:
 *   1. Volume Accumulation (se piano attivo)
 *   2. Metric Trends (se misurazioni)
 *   3. Goal Projections con ETA + Fear of Loss (se goal + trend)
 *
 * Collapsible. Mostra alert/risk flags in cima.
 * Chart predittivi per goal con proiezione visiva.
 */

import { useState } from "react";
import {
  AlertTriangle,
  CalendarClock,
  ChevronDown,
  Clock,
  Flame,
  Rocket,
  Target,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useClientProjection } from "@/hooks/useDashboard";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  ClientProjectionResponse,
  GoalProjectionResponse,
  MetricTrendResponse,
  RiskFlagResponse,
} from "@/types/api";

// ── Helpers ──

function formatRate(rate: number, unit: string): string {
  const sign = rate >= 0 ? "+" : "";
  return `${sign}${rate.toFixed(2)} ${unit}/sett`;
}

function formatEta(eta: string): string {
  try {
    const d = new Date(eta);
    return d.toLocaleDateString("it-IT", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return eta;
  }
}

const CONFIDENCE_CONFIG: Record<
  string,
  { label: string; color: string; bg: string }
> = {
  good: {
    label: "Affidabile",
    color: "text-emerald-700 dark:text-emerald-300",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
  },
  moderate: {
    label: "Moderata",
    color: "text-amber-700 dark:text-amber-300",
    bg: "bg-amber-50 dark:bg-amber-950/30",
  },
  unstable: {
    label: "Instabile",
    color: "text-orange-700 dark:text-orange-300",
    bg: "bg-orange-50 dark:bg-orange-950/30",
  },
  insufficient: {
    label: "Insufficiente",
    color: "text-zinc-500",
    bg: "bg-zinc-50 dark:bg-zinc-800/50",
  },
};

const STATUS_CONFIG: Record<
  string,
  { label: string; icon: React.ComponentType<{ className?: string }>; color: string }
> = {
  projected: { label: "Proiettato", icon: Rocket, color: "text-emerald-600" },
  insufficient_data: { label: "Dati insufficienti", icon: Clock, color: "text-zinc-500" },
  wrong_direction: { label: "Direzione sbagliata", icon: AlertTriangle, color: "text-red-600" },
  plateau: { label: "Plateau", icon: TrendingDown, color: "text-amber-600" },
  unreachable: { label: "Oltre 12 mesi", icon: CalendarClock, color: "text-zinc-500" },
};

// ── Sub-components ──

function RiskFlagBadge({ flag }: { flag: RiskFlagResponse }) {
  const isAlert = flag.severity === "alert";
  return (
    <div
      className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium ${
        isAlert
          ? "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-300"
          : "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-300"
      }`}
    >
      <AlertTriangle className="h-3 w-3" />
      {flag.message}
    </div>
  );
}

function TrendCard({ trend }: { trend: MetricTrendResponse }) {
  const conf = CONFIDENCE_CONFIG[trend.confidence] ?? CONFIDENCE_CONFIG.insufficient;
  const isPositive = trend.weekly_rate >= 0;

  return (
    <div className="flex items-center justify-between rounded-lg border px-3 py-2">
      <div className="flex items-center gap-2 min-w-0">
        {isPositive ? (
          <TrendingUp className="h-4 w-4 shrink-0 text-emerald-500" />
        ) : (
          <TrendingDown className="h-4 w-4 shrink-0 text-red-500" />
        )}
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">{trend.metric_name}</p>
          <p className="text-xs text-muted-foreground">
            {trend.current_value} {trend.unit} — {trend.n_points} misurazioni, {trend.span_days}gg
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-sm font-bold tabular-nums">
          {formatRate(trend.weekly_rate, trend.unit)}
        </span>
        <Badge variant="outline" className={`text-[10px] ${conf.color} ${conf.bg}`}>
          R²={trend.r_squared.toFixed(2)}
        </Badge>
      </div>
    </div>
  );
}

function GoalProjectionCard({ proj }: { proj: GoalProjectionResponse }) {
  const statusConf = STATUS_CONFIG[proj.status] ?? STATUS_CONFIG.insufficient_data;
  const StatusIcon = statusConf.icon;

  return (
    <Card className="border-l-4 border-l-teal-500">
      <CardContent className="space-y-2 p-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <StatusIcon className={`h-4 w-4 ${statusConf.color}`} />
            <span className="text-sm font-semibold">{proj.metric_name}</span>
          </div>
          <Badge variant="outline" className="text-[10px]">
            {statusConf.label}
          </Badge>
        </div>

        {/* Status message for non-projected */}
        {proj.status !== "projected" && proj.message && (
          <p className="text-xs text-muted-foreground">{proj.message}</p>
        )}

        {/* Projected details */}
        {proj.status === "projected" && (
          <>
            {/* Current → Target */}
            <div className="flex items-center gap-2 text-sm">
              <span className="tabular-nums">
                {proj.current_value} {proj.unit}
              </span>
              <span className="text-muted-foreground">→</span>
              <span className="font-bold tabular-nums text-teal-600 dark:text-teal-400">
                {proj.target_value} {proj.unit}
              </span>
            </div>

            {/* ETA */}
            <div className="flex items-center gap-4 text-xs">
              {proj.eta && (
                <div className="flex items-center gap-1">
                  <Target className="h-3 w-3 text-muted-foreground" />
                  <span>ETA: <strong>{formatEta(proj.eta)}</strong></span>
                </div>
              )}
              {proj.on_track !== null && (
                <Badge
                  variant="outline"
                  className={`text-[10px] ${
                    proj.on_track
                      ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300"
                      : "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-300"
                  }`}
                >
                  {proj.on_track ? "In tempo" : "In ritardo"}
                </Badge>
              )}
            </div>

            {/* Fear of Loss section */}
            {(proj.days_saved != null && proj.days_saved > 0) && (
              <div className="rounded-md bg-violet-50 px-3 py-2 dark:bg-violet-950/30">
                <div className="flex items-center gap-1.5 text-xs font-medium text-violet-700 dark:text-violet-300">
                  <Flame className="h-3 w-3" />
                  Con aderenza perfetta: {proj.days_saved} giorni prima
                </div>
                {proj.eta_perfect && (
                  <p className="mt-0.5 text-[10px] text-violet-600/80 dark:text-violet-400/80">
                    Arrivo stimato: {formatEta(proj.eta_perfect)}
                  </p>
                )}
                {proj.days_per_missed_session != null && (
                  <p className="mt-0.5 text-[10px] text-violet-600/80 dark:text-violet-400/80">
                    Ogni sessione saltata = +{proj.days_per_missed_session} giorni
                  </p>
                )}
              </div>
            )}

            {/* Confidence */}
            {proj.confidence && (
              <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                <span>Velocit&agrave;: {formatRate(proj.weekly_rate ?? 0, proj.unit)}</span>
                {proj.r_squared != null && <span>R²={proj.r_squared.toFixed(2)}</span>}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function VolumeSection({ data }: { data: ClientProjectionResponse }) {
  if (!data.volume) return null;
  const vol = data.volume;
  const pct = vol.total_volume_planned > 0
    ? Math.round((vol.total_volume_effective / vol.total_volume_planned) * 100)
    : 0;

  return (
    <div className="space-y-2">
      <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        <Zap className="h-3.5 w-3.5" />
        Stimolo Cumulativo
      </h4>
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg border bg-zinc-50/50 px-3 py-2 dark:bg-zinc-800/50">
          <p className="text-[10px] text-muted-foreground">Pianificato</p>
          <p className="text-lg font-extrabold tabular-nums">{vol.total_volume_planned}</p>
          <p className="text-[10px] text-muted-foreground">serie in {vol.weeks_active} sett</p>
        </div>
        <div className="rounded-lg border bg-zinc-50/50 px-3 py-2 dark:bg-zinc-800/50">
          <p className="text-[10px] text-muted-foreground">Effettivo</p>
          <p className="text-lg font-extrabold tabular-nums text-teal-600 dark:text-teal-400">
            {vol.total_volume_effective}
          </p>
          <p className="text-[10px] text-muted-foreground">{pct}% del pianificato</p>
        </div>
        <div className="rounded-lg border bg-zinc-50/50 px-3 py-2 dark:bg-zinc-800/50">
          <p className="text-[10px] text-muted-foreground">Perso</p>
          <p className="text-lg font-extrabold tabular-nums text-red-500">
            {vol.total_volume_missed}
          </p>
          <p className="text-[10px] text-muted-foreground">serie mancate</p>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ──

interface ProjectionPanelProps {
  clientId: number;
}

export function ProjectionPanel({ clientId }: ProjectionPanelProps) {
  const { data, isLoading } = useClientProjection(clientId);
  const [expanded, setExpanded] = useState(true);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="space-y-3 p-4">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  // Nothing to show if no plan, no measurements, no goals
  const hasContent = data.has_active_plan || data.has_measurements || data.has_goals;
  if (!hasContent) return null;

  const hasProjections = data.projections.some((p) => p.status === "projected");
  const hasRisks = data.risk_flags.length > 0;

  return (
    <Card className="border-l-4 border-l-violet-500">
      <CardContent className="p-0">
        {/* Header — clickable to collapse */}
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
        >
          <div className="flex items-center gap-2">
            <Rocket className="h-5 w-5 text-violet-500" />
            <h3 className="text-sm font-bold">Proiezione Obiettivi</h3>
            {data.plan_name && (
              <Badge variant="outline" className="text-[10px]">
                {data.plan_name}
              </Badge>
            )}
            {data.compliance_pct > 0 && (
              <Badge variant="outline" className="text-[10px]">
                Aderenza {data.compliance_pct}%
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {hasProjections && (
              <Badge className="bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300">
                {data.projections.filter((p) => p.status === "projected").length} proiezioni
              </Badge>
            )}
            {hasRisks && (
              <Badge variant="destructive" className="text-[10px]">
                {data.risk_flags.length} alert
              </Badge>
            )}
            <ChevronDown
              className={`h-4 w-4 text-muted-foreground transition-transform ${
                expanded ? "rotate-180" : ""
              }`}
            />
          </div>
        </button>

        {/* Body — collapsible */}
        {expanded && (
          <div className="space-y-4 border-t px-4 pb-4 pt-3">
            {/* Risk flags */}
            {hasRisks && (
              <div className="flex flex-wrap gap-1.5">
                {data.risk_flags.map((f, i) => (
                  <RiskFlagBadge key={i} flag={f} />
                ))}
              </div>
            )}

            {/* Layer 1: Volume */}
            <VolumeSection data={data} />

            {/* Layer 2: Trends */}
            {data.trends.length > 0 && (
              <div className="space-y-2">
                <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  <TrendingUp className="h-3.5 w-3.5" />
                  Trend Metriche ({data.trends.length})
                </h4>
                <div className="space-y-1.5">
                  {data.trends.map((t) => (
                    <TrendCard key={t.metric_id} trend={t} />
                  ))}
                </div>
              </div>
            )}

            {/* Layer 3: Goal Projections */}
            {data.projections.length > 0 && (
              <div className="space-y-2">
                <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  <Target className="h-3.5 w-3.5" />
                  Proiezioni Obiettivi ({data.projections.length})
                </h4>
                <div className="grid gap-3 sm:grid-cols-2">
                  {data.projections.map((p) => (
                    <GoalProjectionCard key={p.goal_id} proj={p} />
                  ))}
                </div>
              </div>
            )}

            {/* Empty states */}
            {!data.has_active_plan && (
              <div className="rounded-md bg-zinc-50 px-3 py-2 text-xs text-muted-foreground dark:bg-zinc-800/50">
                Nessun piano attivo — attiva un programma per vedere lo stimolo cumulativo
              </div>
            )}
            {!data.has_measurements && (
              <div className="rounded-md bg-zinc-50 px-3 py-2 text-xs text-muted-foreground dark:bg-zinc-800/50">
                Nessuna misurazione — registra almeno 2 misurazioni per attivare i trend
              </div>
            )}
            {data.has_measurements && !data.has_goals && (
              <div className="rounded-md bg-zinc-50 px-3 py-2 text-xs text-muted-foreground dark:bg-zinc-800/50">
                Nessun obiettivo attivo — crea un obiettivo per attivare la proiezione temporale
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
