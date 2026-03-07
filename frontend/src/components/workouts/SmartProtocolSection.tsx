// src/components/workouts/SmartProtocolSection.tsx
"use client";

/**
 * Sezioni SMART/KineScore per il pannello analisi scientifica.
 *
 * 3 sezioni:
 * 1. Protocollo Selezionato — ID, label, status, exact_match, rationale
 * 2. Feasibility Summary — contatori per-source (beginner, safety, demand)
 * 3. Constraint Findings — lista findings con severity colorata
 *
 * Consuma TSPlanPackage.protocol, .feasibility_summary, .constraint_evaluation.
 */

import {
  CheckCircle2,
  Shield,
  AlertTriangle,
  XCircle,
  FlaskConical,
  Gauge,
  Info,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type {
  TSPlanPackageProtocolInfo,
  TSFeasibilitySummary,
  TSConstraintEvaluationReport,
  TSConstraintFinding,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// PROTOCOL SECTION
// ════════════════════════════════════════════════════════════

const PROTOCOL_STATUS_CONFIG = {
  supported: { label: "Supportato", icon: CheckCircle2, color: "text-emerald-600 dark:text-emerald-400" },
  clinical_only: { label: "Solo clinico", icon: Shield, color: "text-blue-600 dark:text-blue-400" },
  research_only: { label: "Research only", icon: FlaskConical, color: "text-violet-600 dark:text-violet-400" },
  unsupported_by_policy: { label: "Non supportato", icon: XCircle, color: "text-red-600 dark:text-red-400" },
} as const;

export function ProtocolSection({ protocol }: { protocol: TSPlanPackageProtocolInfo }) {
  const statusConfig = PROTOCOL_STATUS_CONFIG[protocol.status] ?? PROTOCOL_STATUS_CONFIG.supported;
  const StatusIcon = statusConfig.icon;

  return (
    <section>
      <div className="flex items-center gap-1.5 mb-2">
        <Gauge className="h-3 w-3 text-muted-foreground" />
        <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Protocollo Selezionato
        </div>
      </div>
      <div className="rounded-lg bg-muted/40 px-3 py-2 space-y-2">
        <div className="flex items-center gap-2">
          <StatusIcon className={`h-3.5 w-3.5 shrink-0 ${statusConfig.color}`} />
          <span className="text-xs font-medium">{protocol.label}</span>
          <Badge variant="outline" className="text-[8px] px-1 py-0 h-3.5 font-mono">
            {protocol.protocol_id}
          </Badge>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Badge variant="outline" className={`text-[9px] font-normal ${statusConfig.color}`}>
            {statusConfig.label}
          </Badge>
          {protocol.exact_match ? (
            <Badge variant="outline" className="text-[9px] font-normal text-emerald-600 dark:text-emerald-400">
              Match esatto
            </Badge>
          ) : (
            <Badge variant="outline" className="text-[9px] font-normal text-amber-600 dark:text-amber-400">
              Adapter mode
            </Badge>
          )}
          <Badge variant="outline" className="text-[9px] font-normal font-mono">
            {protocol.registry_version}
          </Badge>
        </div>
        {protocol.selection_rationale.length > 0 && (
          <div className="space-y-0.5">
            {protocol.selection_rationale.map((reason, i) => (
              <div key={i} className="flex items-start gap-1.5 text-[10px] text-muted-foreground">
                <Info className="h-2.5 w-2.5 shrink-0 mt-0.5" />
                <span>{reason}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

// ════════════════════════════════════════════════════════════
// FEASIBILITY SECTION
// ════════════════════════════════════════════════════════════

interface FeasibilityCounterProps {
  label: string;
  value: number;
  color: string;
  bgColor: string;
}

function FeasibilityCounter({ label, value, color, bgColor }: FeasibilityCounterProps) {
  if (value === 0) return null;
  return (
    <div className={`rounded-md ${bgColor} px-2 py-1`}>
      <div className={`text-sm font-extrabold tabular-nums ${color}`}>{value}</div>
      <div className="text-[9px] text-muted-foreground">{label}</div>
    </div>
  );
}

export function FeasibilitySection({ summary }: { summary: TSFeasibilitySummary }) {
  const total = summary.feasible_count + summary.discouraged_count + summary.infeasible_count;
  if (total === 0) return null;

  const hasIssues = summary.infeasible_count > 0 || summary.discouraged_count > 0;

  return (
    <section>
      <div className="flex items-center gap-1.5 mb-2">
        <Shield className="h-3 w-3 text-muted-foreground" />
        <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Feasibility Esercizi
        </div>
        <span className="text-[10px] text-muted-foreground">({total} valutati)</span>
      </div>

      {/* Main counters */}
      <div className="grid grid-cols-3 gap-1.5 mb-2">
        <div className="rounded-md bg-emerald-50 dark:bg-emerald-950/30 px-2 py-1 text-center">
          <div className="text-sm font-extrabold tabular-nums text-emerald-600 dark:text-emerald-400">
            {summary.feasible_count}
          </div>
          <div className="text-[9px] text-muted-foreground">Idonei</div>
        </div>
        <div className={`rounded-md px-2 py-1 text-center ${summary.discouraged_count > 0 ? "bg-amber-50 dark:bg-amber-950/30" : "bg-muted/30"}`}>
          <div className={`text-sm font-extrabold tabular-nums ${summary.discouraged_count > 0 ? "text-amber-600 dark:text-amber-400" : "text-muted-foreground"}`}>
            {summary.discouraged_count}
          </div>
          <div className="text-[9px] text-muted-foreground">Scoraggiati</div>
        </div>
        <div className={`rounded-md px-2 py-1 text-center ${summary.infeasible_count > 0 ? "bg-red-50 dark:bg-red-950/30" : "bg-muted/30"}`}>
          <div className={`text-sm font-extrabold tabular-nums ${summary.infeasible_count > 0 ? "text-red-600 dark:text-red-400" : "text-muted-foreground"}`}>
            {summary.infeasible_count}
          </div>
          <div className="text-[9px] text-muted-foreground">Esclusi</div>
        </div>
      </div>

      {/* Per-source breakdown (only if issues exist) */}
      {hasIssues && (
        <div className="flex flex-wrap gap-1.5">
          <FeasibilityCounter
            label="Beginner gate"
            value={summary.infeasible_by_beginner_gate}
            color="text-red-600 dark:text-red-400"
            bgColor="bg-red-50/60 dark:bg-red-950/20"
          />
          <FeasibilityCounter
            label="Safety"
            value={summary.infeasible_by_safety + summary.discouraged_by_safety}
            color="text-blue-600 dark:text-blue-400"
            bgColor="bg-blue-50/60 dark:bg-blue-950/20"
          />
          <FeasibilityCounter
            label="Demand"
            value={summary.infeasible_by_demand + summary.discouraged_by_demand}
            color="text-violet-600 dark:text-violet-400"
            bgColor="bg-violet-50/60 dark:bg-violet-950/20"
          />
          <FeasibilityCounter
            label="Ceiling"
            value={summary.demand_ceiling_violations}
            color="text-orange-600 dark:text-orange-400"
            bgColor="bg-orange-50/60 dark:bg-orange-950/20"
          />
        </div>
      )}
    </section>
  );
}

// ════════════════════════════════════════════════════════════
// CONSTRAINT FINDINGS SECTION
// ════════════════════════════════════════════════════════════

const SEVERITY_CONFIG = {
  hard_fail: {
    icon: XCircle,
    color: "text-red-600 dark:text-red-400",
    dot: "bg-red-500",
  },
  soft_warning: {
    icon: AlertTriangle,
    color: "text-amber-600 dark:text-amber-400",
    dot: "bg-amber-500",
  },
  optimization_target: {
    icon: Info,
    color: "text-sky-600 dark:text-sky-400",
    dot: "bg-sky-400",
  },
} as const;

const OVERALL_STATUS_CONFIG = {
  pass: { label: "Tutti i vincoli rispettati", color: "text-emerald-600 dark:text-emerald-400", badge: "border-emerald-300 dark:border-emerald-700" },
  warn: { label: "Vincoli con avvisi", color: "text-amber-600 dark:text-amber-400", badge: "border-amber-300 dark:border-amber-700" },
  fail: { label: "Vincoli violati", color: "text-red-600 dark:text-red-400", badge: "border-red-300 dark:border-red-700" },
} as const;

function FindingRow({ finding }: { finding: TSConstraintFinding }) {
  const config = SEVERITY_CONFIG[finding.severity] ?? SEVERITY_CONFIG.optimization_target;
  return (
    <div className="flex items-start gap-2 text-[11px]">
      <div className={`h-2 w-2 rounded-full shrink-0 mt-1 ${config.dot}`} />
      <span className="text-muted-foreground flex-1">{finding.message}</span>
    </div>
  );
}

export function ConstraintSection({ evaluation }: { evaluation: TSConstraintEvaluationReport }) {
  const { summary, findings } = evaluation;
  const statusConfig = OVERALL_STATUS_CONFIG[summary.overall_status] ?? OVERALL_STATUS_CONFIG.pass;

  // Show only non-pass findings (hard_fail + soft_warning), skip optimization_target (too noisy)
  const actionableFindings = findings.filter(
    (f) => f.severity === "hard_fail" || f.severity === "soft_warning",
  );

  return (
    <section>
      <div className="flex items-center gap-1.5 mb-2">
        <CheckCircle2 className="h-3 w-3 text-muted-foreground" />
        <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Vincoli Protocollo
        </div>
        <Badge variant="outline" className={`text-[8px] px-1 py-0 h-3.5 ${statusConfig.color} ${statusConfig.badge}`}>
          {summary.hard_fail_count > 0
            ? `${summary.hard_fail_count} fail`
            : summary.soft_warning_count > 0
              ? `${summary.soft_warning_count} avvisi`
              : "OK"}
        </Badge>
      </div>

      {actionableFindings.length > 0 ? (
        <div className="space-y-1.5 max-h-32 overflow-y-auto">
          {actionableFindings.map((finding, i) => (
            <FindingRow key={`${finding.rule_id}-${i}`} finding={finding} />
          ))}
        </div>
      ) : (
        <div className="text-[10px] text-muted-foreground">
          {statusConfig.label}
        </div>
      )}

      {/* Score dal constraint analyzer */}
      <div className="mt-1.5 text-[10px] text-muted-foreground">
        Score analisi: <span className="font-medium text-foreground tabular-nums">{Math.round(evaluation.analyzer_score)}</span>/100
      </div>
    </section>
  );
}
