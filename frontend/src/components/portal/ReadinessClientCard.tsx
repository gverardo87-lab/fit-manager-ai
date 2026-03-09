"use client";

/**
 * ReadinessClientRow — Riga espandibile full-width per worklist Salute Clienti.
 *
 * Compact: nome + readiness mini-bar + 3 status dots + timeline badge + CTA + chevron.
 * Expanded: readiness bar full, dettaglio step mancanti, timeline, link profilo.
 */

import Link from "next/link";
import { ArrowRight, Check, X, AlertTriangle, ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ClinicalReadinessClientItem } from "@/types/api";

// ── Costanti ──

const PRIORITY_BORDER: Record<string, string> = {
  high: "border-l-red-500",
  medium: "border-l-amber-500",
  low: "",
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

function MiniBar({ score }: { score: number }) {
  const color = score >= 70 ? "bg-emerald-500" : score >= 40 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-1.5">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-[11px] font-semibold tabular-nums text-muted-foreground">
        {score}%
      </span>
    </div>
  );
}

function StatusDot({ state, label }: { state: "ok" | "warn" | "missing"; label: string }) {
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

function formatDaysTo(days: number | null): string {
  if (days === null) return "";
  if (days < 0) return `${Math.abs(days)}gg fa`;
  if (days === 0) return "oggi";
  return `tra ${days}gg`;
}

// ── Main Component ──

interface ReadinessClientRowProps {
  item: ClinicalReadinessClientItem;
  expanded: boolean;
  onToggle: () => void;
}

export function ReadinessClientRow({ item, expanded, onToggle }: ReadinessClientRowProps) {
  const anamnesiState: "ok" | "warn" | "missing" =
    item.anamnesi_state === "structured" ? "ok"
    : item.anamnesi_state === "legacy" ? "warn"
    : "missing";

  const isReady = item.readiness_score >= 100;
  const isQuiet = item.priority === "low";

  return (
    <div
      className={`rounded-xl border transition-all duration-200 dark:bg-zinc-900 ${
        isQuiet
          ? "bg-zinc-50/50 dark:bg-zinc-900/50"
          : `border-l-4 ${PRIORITY_BORDER[item.priority]} bg-white shadow-sm`
      }`}
    >
      {/* ── Compact Row ── */}
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center gap-3 p-3 text-left sm:px-4"
      >
        {/* Readiness score dot */}
        <div className={`h-2 w-2 shrink-0 rounded-full ${
          isReady ? "bg-emerald-500" : item.readiness_score >= 40 ? "bg-amber-500" : "bg-red-500"
        }`} />

        {/* Name */}
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">
            {item.client_cognome} {item.client_nome}
          </p>
        </div>

        {/* Mini readiness bar (desktop) */}
        <div className="hidden shrink-0 sm:block">
          <MiniBar score={item.readiness_score} />
        </div>

        {/* Status dots compact (desktop) */}
        <div className="hidden shrink-0 items-center gap-2 md:flex">
          <StatusDot state={anamnesiState} label="Ana" />
          <StatusDot state={item.has_measurements ? "ok" : "missing"} label="Mis" />
          <StatusDot state={item.has_workout_plan ? "ok" : "missing"} label="Sch" />
        </div>

        {/* Timeline badge */}
        {item.timeline_status !== "none" && (
          <Badge variant="outline" className={`hidden shrink-0 text-[10px] sm:inline-flex ${TIMELINE_STATUS_BADGE[item.timeline_status]}`}>
            {TIMELINE_STATUS_LABEL[item.timeline_status]}
          </Badge>
        )}

        {/* CTA */}
        <Link
          href={isReady ? `/monitoraggio/${item.client_id}` : item.next_action_href}
          onClick={(e) => e.stopPropagation()}
          className="shrink-0"
        >
          <Button size="sm" variant={isReady ? "outline" : "default"} className="gap-1 text-xs">
            <span className="hidden sm:inline">{isReady ? "Portale" : item.next_action_label}</span>
            <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>

        {/* Chevron */}
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* ── Expanded Drill-Down ── */}
      {expanded && (
        <div className="border-t px-4 pb-4 pt-3">
          <div className="grid gap-4 sm:grid-cols-2">
            {/* Left: readiness bar + status dots full */}
            <div className="space-y-3">
              <div>
                <p className="mb-1 text-[10px] font-medium uppercase text-muted-foreground">
                  Readiness
                </p>
                <ReadinessBar score={item.readiness_score} />
              </div>

              <div className="flex flex-wrap gap-3">
                <StatusDot state={anamnesiState} label="Anamnesi" />
                <StatusDot state={item.has_measurements ? "ok" : "missing"} label="Misurazioni" />
                <StatusDot state={item.has_workout_plan ? "ok" : "missing"} label="Scheda" />
              </div>
            </div>

            {/* Right: timeline + missing steps */}
            <div className="space-y-3">
              {/* Timeline */}
              {item.timeline_status !== "none" && (
                <div className="flex items-center gap-2">
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

              {/* Missing steps */}
              {item.missing_steps.length > 0 && (
                <div>
                  <p className="mb-1 text-[10px] font-medium uppercase text-muted-foreground">
                    Step mancanti
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {item.missing_steps.map((step) => (
                      <Badge key={step} variant="outline" className="border-red-200 bg-red-50 text-[10px] text-red-700 dark:border-red-900/40 dark:bg-red-900/30 dark:text-red-300">
                        {step}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Timeline reason */}
              {item.timeline_reason && (
                <p className="text-xs text-muted-foreground">{item.timeline_reason}</p>
              )}
            </div>
          </div>

          {/* Bottom link */}
          <div className="mt-3 flex items-center justify-end border-t pt-3">
            <Link
              href={`/monitoraggio/${item.client_id}`}
              className="text-xs text-muted-foreground hover:text-foreground hover:underline"
            >
              Profilo cliente →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
