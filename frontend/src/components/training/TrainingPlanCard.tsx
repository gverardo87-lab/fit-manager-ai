"use client";

/**
 * TrainingPlanRow — Riga espandibile full-width per worklist Qualita Programmi.
 *
 * Compact: nome piano + cliente + stato + mini score bars + CTA + chevron.
 * Expanded: timeline, score dettagliati, compliance per sessione, issue indicators.
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
  Zap,
  ChevronDown,
  Calendar,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { TrainingMethodologyPlanItem } from "@/types/api";

// ── Costanti ──

const PRIORITY_BORDER: Record<string, string> = {
  high: "border-l-red-500",
  medium: "border-l-amber-500",
  low: "",
};

const STATUS_DOT: Record<string, string> = {
  attivo: "bg-emerald-500",
  da_attivare: "bg-amber-500",
  completato: "bg-zinc-400",
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

function MiniBar({ value, className }: { value: number; className?: string }) {
  const color =
    value >= 70 ? "bg-emerald-500" : value >= 40 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className={`flex items-center gap-1.5 ${className ?? ""}`}>
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-[11px] font-semibold tabular-nums text-muted-foreground">
        {value}
      </span>
    </div>
  );
}

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
    value >= 70 ? "bg-emerald-500" : value >= 40 ? "bg-amber-500" : "bg-red-500";
  const textColor =
    value >= 70
      ? "text-emerald-600 dark:text-emerald-400"
      : value >= 40
        ? "text-amber-600 dark:text-amber-400"
        : "text-red-600 dark:text-red-400";

  return (
    <div className="flex items-center gap-2">
      <Icon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
      <span className="w-20 shrink-0 text-[11px] text-muted-foreground">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${color}`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className={`w-8 text-right text-xs font-bold tabular-nums ${textColor}`}>
        {value}
      </span>
    </div>
  );
}

function formatDateShort(dateStr: string | null): string {
  if (!dateStr) return "–";
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("it-IT", { day: "numeric", month: "short" });
}

function computeWeekCount(start: string | null, end: string | null): number | null {
  if (!start || !end) return null;
  const s = new Date(start + "T00:00:00");
  const e = new Date(end + "T00:00:00");
  const diff = e.getTime() - s.getTime();
  return Math.max(1, Math.ceil(diff / (7 * 24 * 60 * 60 * 1000)));
}

// ── Main Component ──

interface TrainingPlanRowProps {
  item: TrainingMethodologyPlanItem;
  expanded: boolean;
  onToggle: () => void;
}

export function TrainingPlanRow({ item, expanded, onToggle }: TrainingPlanRowProps) {
  const isQuiet = item.priority === "low";
  const hasIssues =
    item.sotto_mev_count > 0 || item.squilibri_count > 0 || item.warning_count > 3;
  const weekCount = computeWeekCount(item.data_inizio, item.data_fine);

  return (
    <div
      className={`rounded-xl border transition-all duration-200 dark:bg-zinc-900 ${
        isQuiet
          ? "bg-zinc-50/50 dark:bg-zinc-900/50"
          : `border-l-4 ${PRIORITY_BORDER[item.priority]} bg-white shadow-sm`
      }`}
    >
      {/* ── Compact Row (always visible) ── */}
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center gap-3 p-3 text-left sm:px-4"
      >
        {/* Status dot */}
        <div className={`h-2 w-2 shrink-0 rounded-full ${STATUS_DOT[item.status] ?? "bg-zinc-400"}`} />

        {/* Name + client */}
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">{item.plan_nome}</p>
          <p className="truncate text-xs text-muted-foreground">
            {item.client_cognome} {item.client_nome}
          </p>
        </div>

        {/* Mini score bars (desktop) */}
        {item.analyzable && (
          <div className="hidden shrink-0 items-center gap-4 sm:flex">
            <div className="flex items-center gap-1">
              <Beaker className="h-3 w-3 text-muted-foreground" />
              <MiniBar value={Math.round(item.science_score)} />
            </div>
            {item.status !== "da_attivare" && (
              <div className="flex items-center gap-1">
                <Activity className="h-3 w-3 text-muted-foreground" />
                <MiniBar value={item.compliance_pct} />
              </div>
            )}
          </div>
        )}

        {/* Issue count badge */}
        {hasIssues && item.analyzable && (
          <Badge variant="outline" className="shrink-0 border-red-200 bg-red-50 text-[10px] text-red-700 dark:border-red-900/40 dark:bg-red-900/30 dark:text-red-300">
            {item.sotto_mev_count + item.squilibri_count} problemi
          </Badge>
        )}

        {/* Training score */}
        {item.analyzable && (
          <span className="hidden shrink-0 text-sm font-extrabold tabular-nums sm:inline">
            {item.training_score}
            <span className="text-[10px] font-normal text-muted-foreground">/100</span>
          </span>
        )}

        {/* CTA */}
        <Link
          href={item.next_action_href}
          onClick={(e) => e.stopPropagation()}
          className="shrink-0"
        >
          <Button size="sm" variant={isQuiet ? "outline" : "default"} className="gap-1 text-xs">
            <span className="hidden sm:inline">{item.next_action_label}</span>
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
            {/* Left: timeline + info */}
            <div className="space-y-3">
              {/* Timeline */}
              <div className="flex items-start gap-2">
                <Calendar className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                <div className="text-xs">
                  {item.data_inizio ? (
                    <p>
                      {formatDateShort(item.data_inizio)} → {formatDateShort(item.data_fine)}
                      {weekCount && (
                        <span className="ml-1.5 text-muted-foreground">
                          ({weekCount} settiman{weekCount === 1 ? "a" : "e"})
                        </span>
                      )}
                    </p>
                  ) : (
                    <p className="text-muted-foreground">Date non impostate</p>
                  )}
                </div>
              </div>

              {/* Info badges */}
              <div className="flex flex-wrap gap-1.5">
                <Badge variant="outline" className="text-[10px]">
                  {STATUS_LABEL[item.status] ?? item.status}
                </Badge>
                <Badge variant="outline" className="text-[10px]">
                  {OBIETTIVO_LABEL[item.obiettivo] ?? item.obiettivo}
                </Badge>
                <Badge variant="outline" className="text-[10px]">
                  {item.sessioni_count} session{item.sessioni_count !== 1 ? "i" : "e"}
                </Badge>
                {item.sessions_expected > 0 && (
                  <Badge variant="outline" className="text-[10px]">
                    {item.sessions_completed}/{item.sessions_expected} completate
                  </Badge>
                )}
              </div>

              {/* Issue indicators */}
              {(hasIssues || item.session_imbalance) && item.analyzable && (
                <div className="flex flex-wrap gap-1.5">
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
            </div>

            {/* Right: score bars + compliance breakdown */}
            <div className="space-y-3">
              {/* Score bars */}
              {item.analyzable ? (
                <div className="space-y-1.5">
                  <ScoreBar label="Scientifica" value={Math.round(item.science_score)} icon={Beaker} />
                  {item.status !== "da_attivare" && (
                    <ScoreBar label="Aderenza" value={item.compliance_pct} icon={Activity} />
                  )}
                  {item.effective_score != null && (
                    <ScoreBar label="Effettiva" value={Math.round(item.effective_score)} icon={Zap} />
                  )}
                </div>
              ) : (
                <div className="rounded-md bg-zinc-50 px-3 py-2 text-xs text-muted-foreground dark:bg-zinc-800/50">
                  Nessun esercizio con pattern analizzabile
                </div>
              )}

              {/* Per-session compliance */}
              {item.session_compliance.length >= 2 && item.status !== "da_attivare" && (
                <div className="space-y-1">
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
                      item.session_imbalance && sc.session_name === item.worst_session_name;
                    return (
                      <div key={sc.session_id} className="flex items-center gap-1.5">
                        <span
                          className={`w-20 shrink-0 truncate text-[10px] ${
                            isWorst
                              ? "font-semibold text-red-600 dark:text-red-400"
                              : "text-muted-foreground"
                          }`}
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

              {/* Training score + delta */}
              {item.analyzable && (
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-extrabold tabular-nums text-foreground">
                    {item.training_score}
                    <span className="text-xs font-normal text-muted-foreground">/100</span>
                  </span>
                  {item.score_delta != null && item.score_delta > 0 && (
                    <span className="text-[10px] font-semibold tabular-nums text-red-600 dark:text-red-400">
                      −{item.score_delta} pts persi
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Bottom links */}
          <div className="mt-3 flex items-center justify-between border-t pt-3">
            <Link
              href={`/schede/${item.plan_id}`}
              className="text-xs text-muted-foreground hover:text-foreground hover:underline"
            >
              Apri scheda →
            </Link>
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
