"use client";

/**
 * ReadinessClientCard — Card ricca per singolo cliente nella worklist MyPortal.
 *
 * Border-left per priorità, readiness bar, 3 status dot, timeline + CTA.
 */

import Link from "next/link";
import { ArrowRight, Check, X, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ClinicalReadinessClientItem } from "@/types/api";

// ── Costanti ──

const PRIORITY_BORDER: Record<string, string> = {
  high: "border-l-red-500",
  medium: "border-l-amber-500",
  low: "border-l-emerald-500",
};

const PRIORITY_BADGE: Record<string, string> = {
  high: "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800",
  medium: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800",
  low: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800",
};

const PRIORITY_LABEL: Record<string, string> = {
  high: "Alta",
  medium: "Media",
  low: "Bassa",
};

const TIMELINE_STATUS_BADGE: Record<string, string> = {
  overdue: "border-red-200 bg-red-100 text-red-700 dark:border-red-900/40 dark:bg-red-900/30 dark:text-red-300",
  today: "border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-900/40 dark:bg-amber-900/30 dark:text-amber-300",
  upcoming_7d: "border-orange-200 bg-orange-100 text-orange-700 dark:border-orange-900/40 dark:bg-orange-900/30 dark:text-orange-300",
  upcoming_14d: "border-blue-200 bg-blue-100 text-blue-700 dark:border-blue-900/40 dark:bg-blue-900/30 dark:text-blue-300",
  future: "border-zinc-200 bg-zinc-100 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400",
  none: "border-zinc-200 bg-zinc-50 text-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400",
};

const TIMELINE_STATUS_LABEL: Record<string, string> = {
  overdue: "Scaduta",
  today: "Oggi",
  upcoming_7d: "Entro 7gg",
  upcoming_14d: "Entro 14gg",
  future: "Pianificata",
  none: "Nessuna",
};

// ── Helpers ──

function ReadinessBar({ score }: { score: number }) {
  const color = score >= 70 ? "bg-emerald-500" : score >= 40 ? "bg-amber-500" : "bg-red-500";
  const textColor = score >= 70
    ? "text-emerald-600 dark:text-emerald-400"
    : score >= 40
      ? "text-amber-600 dark:text-amber-400"
      : "text-red-600 dark:text-red-400";

  return (
    <div className="flex items-center gap-2.5">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${color}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={`text-xs font-bold tabular-nums ${textColor}`}>{score}%</span>
    </div>
  );
}

function StatusDot({
  state,
  label,
}: {
  state: "ok" | "warn" | "missing";
  label: string;
}) {
  return (
    <div className="flex items-center gap-1">
      {state === "ok" && (
        <div className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
          <Check className="h-2.5 w-2.5 text-emerald-600 dark:text-emerald-400" />
        </div>
      )}
      {state === "warn" && (
        <div className="flex h-4 w-4 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
          <AlertTriangle className="h-2.5 w-2.5 text-amber-600 dark:text-amber-400" />
        </div>
      )}
      {state === "missing" && (
        <div className="flex h-4 w-4 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
          <X className="h-2.5 w-2.5 text-red-600 dark:text-red-400" />
        </div>
      )}
      <span className="text-[11px] text-muted-foreground">{label}</span>
    </div>
  );
}

function formatDaysTo(days: number | null): string {
  if (days === null) return "";
  if (days < 0) return `${Math.abs(days)}gg fa`;
  if (days === 0) return "oggi";
  return `tra ${days}gg`;
}

// ── Main Component ──

interface ReadinessClientCardProps {
  item: ClinicalReadinessClientItem;
}

export function ReadinessClientCard({ item }: ReadinessClientCardProps) {
  const anamnesiState: "ok" | "warn" | "missing" =
    item.anamnesi_state === "structured" ? "ok"
    : item.anamnesi_state === "legacy" ? "warn"
    : "missing";

  const isReady = item.readiness_score >= 100;

  return (
    <div
      className={`rounded-xl border border-l-4 ${PRIORITY_BORDER[item.priority]} bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg dark:bg-zinc-900`}
    >
      {/* Header: nome + priorità */}
      <div className="flex items-start justify-between gap-2">
        <Link
          href={`/monitoraggio/${item.client_id}`}
          className="text-sm font-semibold hover:underline"
        >
          {item.client_cognome} {item.client_nome}
        </Link>
        <Badge variant="outline" className={`shrink-0 text-[10px] font-semibold uppercase ${PRIORITY_BADGE[item.priority]}`}>
          {PRIORITY_LABEL[item.priority]}
        </Badge>
      </div>

      {/* Readiness bar */}
      <div className="mt-3">
        <ReadinessBar score={item.readiness_score} />
      </div>

      {/* Status dots */}
      <div className="mt-3 flex flex-wrap gap-3">
        <StatusDot state={anamnesiState} label="Anamnesi" />
        <StatusDot state={item.has_measurements ? "ok" : "missing"} label="Misurazioni" />
        <StatusDot state={item.has_workout_plan ? "ok" : "missing"} label="Scheda" />
      </div>

      {/* Timeline */}
      {item.timeline_status !== "none" && (
        <div className="mt-3 flex items-center gap-2">
          <Badge variant="outline" className={`text-[10px] ${TIMELINE_STATUS_BADGE[item.timeline_status]}`}>
            {TIMELINE_STATUS_LABEL[item.timeline_status]}
          </Badge>
          {item.days_to_due !== null && (
            <span className="text-[11px] tabular-nums text-muted-foreground">
              {formatDaysTo(item.days_to_due)}
            </span>
          )}
        </div>
      )}

      {/* CTA */}
      <div className="mt-3 flex justify-end">
        {isReady ? (
          <Link href={`/monitoraggio/${item.client_id}`}>
            <Button size="sm" variant="outline" className="gap-1 text-xs">
              Portale
              <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        ) : (
          <Link href={item.next_action_href}>
            <Button size="sm" className="gap-1 text-xs">
              {item.next_action_label}
              <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}
