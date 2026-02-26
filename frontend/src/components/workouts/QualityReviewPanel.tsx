// src/components/workouts/QualityReviewPanel.tsx
"use client";

/**
 * Panel collapsibile per il Quality Review della scheda allenamento.
 *
 * Stato compatto: badge score + livello (1 riga).
 * Stato espanso: 7 dimensioni con progress bar + issues.
 */

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  Shield,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type {
  QualityReport,
  QualityDimension,
  QualityLevel,
  IssueSeverity,
} from "@/lib/workout-quality-engine";

// ════════════════════════════════════════════════════════════
// CONSTANTS
// ════════════════════════════════════════════════════════════

const LEVEL_CONFIG: Record<QualityLevel, { label: string; color: string; badgeVariant: string; bgClass: string }> = {
  eccellente: {
    label: "Eccellente",
    color: "text-emerald-600 dark:text-emerald-400",
    badgeVariant: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
    bgClass: "bg-emerald-500",
  },
  buono: {
    label: "Buono",
    color: "text-primary",
    badgeVariant: "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300",
    bgClass: "bg-primary",
  },
  sufficiente: {
    label: "Sufficiente",
    color: "text-amber-600 dark:text-amber-400",
    badgeVariant: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
    bgClass: "bg-amber-500",
  },
  da_migliorare: {
    label: "Da Migliorare",
    color: "text-red-600 dark:text-red-400",
    badgeVariant: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
    bgClass: "bg-red-500",
  },
};

const SEVERITY_ICON: Record<IssueSeverity, typeof Info> = {
  info: Info,
  warning: AlertTriangle,
  critical: XCircle,
};

const SEVERITY_COLOR: Record<IssueSeverity, string> = {
  info: "text-muted-foreground",
  warning: "text-amber-600 dark:text-amber-400",
  critical: "text-red-600 dark:text-red-400",
};

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

interface QualityReviewPanelProps {
  report: QualityReport | null;
}

export function QualityReviewPanel({ report }: QualityReviewPanelProps) {
  const [expanded, setExpanded] = useState(false);

  if (!report) return null;

  const config = LEVEL_CONFIG[report.level];
  const totalIssues = report.dimensions.reduce((sum, d) => sum + d.issues.length, 0);

  return (
    <div className="rounded-lg border bg-card" data-print-hide>
      {/* ── Header compatto ── */}
      <Button
        variant="ghost"
        className="w-full flex items-center justify-between px-4 py-2.5 h-auto"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <Shield className={`h-4 w-4 ${config.color}`} />
          <span className="text-sm font-medium">Qualita' Scheda</span>
          <div className="flex items-center gap-1.5">
            <span className={`text-lg font-extrabold tabular-nums tracking-tighter ${config.color}`}>
              {report.overallScore}
            </span>
            <span className="text-xs text-muted-foreground">/100</span>
          </div>
          <Badge className={`text-[10px] px-1.5 py-0 ${config.badgeVariant}`}>
            {config.label}
          </Badge>
          {totalIssues > 0 && (
            <span className="text-[10px] text-muted-foreground">
              {totalIssues} {totalIssues === 1 ? "suggerimento" : "suggerimenti"}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </Button>

      {/* ── Dettagli espansi ── */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t">
          {/* Dimensioni */}
          <div className="grid gap-2 pt-3">
            {report.dimensions.map((dim) => (
              <DimensionRow key={dim.key} dimension={dim} />
            ))}
          </div>

          {/* Strengths */}
          {report.strengths.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap pt-1">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              <span className="text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
                Punti di forza:
              </span>
              {report.strengths.map((s) => (
                <Badge key={s} variant="outline" className="text-[10px] px-1.5 py-0 border-emerald-300 text-emerald-600 dark:border-emerald-700 dark:text-emerald-400">
                  {s}
                </Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Riga dimensione ──

function DimensionRow({ dimension }: { dimension: QualityDimension }) {
  const [showIssues, setShowIssues] = useState(false);
  const config = LEVEL_CONFIG[dimension.level];
  const hasIssues = dimension.issues.length > 0;

  return (
    <div>
      <div
        className={`flex items-center gap-3 ${hasIssues ? "cursor-pointer" : ""}`}
        onClick={() => hasIssues && setShowIssues(!showIssues)}
      >
        {/* Label */}
        <span className="text-xs text-muted-foreground w-[140px] shrink-0">
          {dimension.label}
        </span>

        {/* Progress bar */}
        <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${config.bgClass}`}
            style={{ width: `${dimension.score}%` }}
          />
        </div>

        {/* Score */}
        <span className={`text-xs font-bold tabular-nums w-8 text-right ${config.color}`}>
          {dimension.score}
        </span>

        {/* Issues indicator */}
        {hasIssues && (
          <span className="text-[10px] text-muted-foreground w-4">
            {showIssues ? "−" : `${dimension.issues.length}`}
          </span>
        )}
        {!hasIssues && <span className="w-4" />}
      </div>

      {/* Issues espanse */}
      {showIssues && hasIssues && (
        <div className="ml-[152px] mt-1 space-y-1 mb-2">
          {dimension.issues.map((issue, idx) => {
            const Icon = SEVERITY_ICON[issue.severity];
            return (
              <div key={idx} className="flex items-start gap-1.5">
                <Icon className={`h-3 w-3 mt-0.5 shrink-0 ${SEVERITY_COLOR[issue.severity]}`} />
                <div>
                  <p className="text-[11px] text-muted-foreground leading-tight">{issue.message}</p>
                  {issue.suggestion && (
                    <p className="text-[10px] text-primary leading-tight mt-0.5">{issue.suggestion}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
