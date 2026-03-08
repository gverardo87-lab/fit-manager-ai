"use client";

/**
 * TrainingPlanCard — Card per singolo piano nella worklist MyTrainer.
 *
 * Parallelo a ReadinessClientCard (MyPortal): border-left per priorita',
 * dual score bar (scientifica + aderenza), issue badges, CTA actionable.
 */

import Link from "next/link";
import {
  ArrowRight,
  Beaker,
  Activity,
  AlertTriangle,
  TrendingDown,
  Scale,
  SkipForward,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { TrainingMethodologyPlanItem } from "@/types/api";

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

const STATUS_BADGE: Record<string, string> = {
  attivo: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300",
  da_attivare: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300",
  completato: "bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400",
};

const STATUS_LABEL: Record<string, string> = {
  attivo: "Attivo",
  da_attivare: "Da attivare",
  completato: "Completato",
};

const OBIETTIVO_LABEL: Record<string, string> = {
  forza: "Forza",
  ipertrofia: "Ipertrofia",
  resistenza: "Resistenza",
  dimagrimento: "Dimagrimento",
  tonificazione: "Tonificazione",
  generale: "Generale",
};

// ── Helpers ──

function ScoreBar({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
}) {
  const color =
    value >= 70
      ? "bg-emerald-500"
      : value >= 40
        ? "bg-amber-500"
        : "bg-red-500";
  const textColor =
    value >= 70
      ? "text-emerald-600 dark:text-emerald-400"
      : value >= 40
        ? "text-amber-600 dark:text-amber-400"
        : "text-red-600 dark:text-red-400";

  return (
    <div className="flex items-center gap-2">
      <Icon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
      <span className="w-20 shrink-0 text-[11px] text-muted-foreground">
        {label}
      </span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${color}`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span
        className={`w-8 text-right text-xs font-bold tabular-nums ${textColor}`}
      >
        {value}
      </span>
    </div>
  );
}

// ── Main Component ──

interface TrainingPlanCardProps {
  item: TrainingMethodologyPlanItem;
}

export function TrainingPlanCard({ item }: TrainingPlanCardProps) {
  const hasIssues =
    item.sotto_mev_count > 0 || item.squilibri_count > 0 || item.warning_count > 3;

  return (
    <div
      className={`rounded-xl border border-l-4 ${PRIORITY_BORDER[item.priority]} bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg dark:bg-zinc-900`}
    >
      {/* Header: piano + client + priority */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <Link
            href={`/schede/${item.plan_id}`}
            className="block truncate text-sm font-semibold hover:underline"
          >
            {item.plan_nome}
          </Link>
          <Link
            href={`/clienti/${item.client_id}`}
            className="text-xs text-muted-foreground hover:underline"
          >
            {item.client_cognome} {item.client_nome}
          </Link>
        </div>
        <Badge
          variant="outline"
          className={`shrink-0 text-[10px] font-semibold uppercase ${PRIORITY_BADGE[item.priority]}`}
        >
          {PRIORITY_LABEL[item.priority]}
        </Badge>
      </div>

      {/* Status badges */}
      <div className="mt-2.5 flex flex-wrap gap-1.5">
        <Badge
          variant="outline"
          className={`text-[10px] ${STATUS_BADGE[item.status] ?? ""}`}
        >
          {STATUS_LABEL[item.status] ?? item.status}
        </Badge>
        <Badge variant="outline" className="text-[10px]">
          {OBIETTIVO_LABEL[item.obiettivo] ?? item.obiettivo}
        </Badge>
        <Badge variant="outline" className="text-[10px]">
          {item.sessioni_count} session{item.sessioni_count !== 1 ? "i" : "e"}
        </Badge>
      </div>

      {/* Dual score bars */}
      {item.analyzable ? (
        <div className="mt-3 space-y-1.5">
          <ScoreBar
            label="Scientifica"
            value={Math.round(item.science_score)}
            icon={Beaker}
          />
          {item.status !== "da_attivare" && (
            <ScoreBar
              label="Aderenza"
              value={item.compliance_pct}
              icon={Activity}
            />
          )}
        </div>
      ) : (
        <div className="mt-3 rounded-md bg-zinc-50 px-3 py-2 text-xs text-muted-foreground dark:bg-zinc-800/50">
          Nessun esercizio con pattern analizzabile
        </div>
      )}

      {/* Per-session compliance breakdown */}
      {item.session_compliance.length >= 2 && item.status !== "da_attivare" && (
        <div className="mt-2.5 space-y-1">
          <p className="text-[10px] font-medium text-muted-foreground">
            Aderenza per sessione
          </p>
          {item.session_compliance.map((sc) => {
            const barColor =
              sc.compliance_pct >= 70
                ? "bg-emerald-400"
                : sc.compliance_pct >= 40
                  ? "bg-amber-400"
                  : "bg-red-400";
            const isWorst =
              item.session_imbalance &&
              sc.session_name === item.worst_session_name;
            return (
              <div key={sc.session_id} className="flex items-center gap-1.5">
                <span
                  className={`w-20 shrink-0 truncate text-[10px] ${isWorst ? "font-semibold text-red-600 dark:text-red-400" : "text-muted-foreground"}`}
                >
                  {sc.session_name}
                </span>
                <div className="h-1 flex-1 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                    style={{ width: `${sc.compliance_pct}%` }}
                  />
                </div>
                <span className="w-6 text-right text-[10px] tabular-nums text-muted-foreground">
                  {sc.completed}/{sc.expected}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Issue indicators */}
      {(hasIssues || item.session_imbalance) && item.analyzable && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {item.sotto_mev_count > 0 && (
            <div className="flex items-center gap-1 rounded-md bg-red-50 px-2 py-0.5 dark:bg-red-950/30">
              <TrendingDown className="h-3 w-3 text-red-500" />
              <span className="text-[10px] font-medium text-red-700 dark:text-red-300">
                {item.sotto_mev_count} sotto MEV
              </span>
            </div>
          )}
          {item.squilibri_count > 0 && (
            <div className="flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 dark:bg-amber-950/30">
              <Scale className="h-3 w-3 text-amber-500" />
              <span className="text-[10px] font-medium text-amber-700 dark:text-amber-300">
                {item.squilibri_count} squilibr{item.squilibri_count !== 1 ? "i" : "io"}
              </span>
            </div>
          )}
          {item.warning_count > 3 && (
            <div className="flex items-center gap-1 rounded-md bg-orange-50 px-2 py-0.5 dark:bg-orange-950/30">
              <AlertTriangle className="h-3 w-3 text-orange-500" />
              <span className="text-[10px] font-medium text-orange-700 dark:text-orange-300">
                {item.warning_count} warning
              </span>
            </div>
          )}
          {item.session_imbalance && item.worst_session_name && (
            <div className="flex items-center gap-1 rounded-md bg-violet-50 px-2 py-0.5 dark:bg-violet-950/30">
              <SkipForward className="h-3 w-3 text-violet-500" />
              <span className="text-[10px] font-medium text-violet-700 dark:text-violet-300">
                {item.worst_session_name} saltata
              </span>
            </div>
          )}
        </div>
      )}

      {/* Training score + CTA */}
      <div className="mt-3 flex items-center justify-between">
        {item.analyzable && (
          <span className="text-lg font-extrabold tabular-nums text-foreground">
            {item.training_score}
            <span className="text-xs font-normal text-muted-foreground">/100</span>
          </span>
        )}
        {!item.analyzable && <span />}
        <Link href={item.next_action_href}>
          <Button size="sm" className="gap-1 text-xs">
            {item.next_action_label}
            <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
      </div>
    </div>
  );
}
