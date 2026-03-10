"use client";

import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Clock3,
  HeartPulse,
  Lightbulb,
  ShieldAlert,
  Sparkles,
  User,
  XCircle,
} from "lucide-react";

import type {
  HealthCheckStatus,
  SessionPrepAlert,
  SessionPrepHealthCheck,
  SessionPrepHint,
  SessionPrepItem,
} from "@/types/api";

/* ── Status colors ── */

const STATUS_ICON: Record<HealthCheckStatus, typeof CheckCircle2> = {
  ok: CheckCircle2,
  warning: AlertTriangle,
  critical: XCircle,
  missing: XCircle,
};

const STATUS_COLOR: Record<HealthCheckStatus, string> = {
  ok: "text-emerald-600 dark:text-emerald-400",
  warning: "text-amber-600 dark:text-amber-400",
  critical: "text-red-600 dark:text-red-400",
  missing: "text-red-600 dark:text-red-400",
};

const STATUS_BG: Record<HealthCheckStatus, string> = {
  ok: "bg-emerald-50 dark:bg-emerald-950/20",
  warning: "bg-amber-50 dark:bg-amber-950/20",
  critical: "bg-red-50 dark:bg-red-950/20",
  missing: "bg-red-50 dark:bg-red-950/20",
};

/* ── Health Check Mini ── */

function HealthCheckDot({ check }: { check: SessionPrepHealthCheck }) {
  const Icon = STATUS_ICON[check.status];
  const color = STATUS_COLOR[check.status];

  return (
    <div className="flex items-center gap-1.5" title={`${check.label}: ${check.detail ?? check.status}`}>
      <Icon className={`h-3.5 w-3.5 ${color}`} />
      <span className="text-xs text-muted-foreground">{check.label}</span>
    </div>
  );
}

/* ── Health Check Expanded ── */

function HealthCheckRow({ check }: { check: SessionPrepHealthCheck }) {
  const Icon = STATUS_ICON[check.status];
  const color = STATUS_COLOR[check.status];
  const bg = STATUS_BG[check.status];

  return (
    <div className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 ${bg}`}>
      <Icon className={`h-3.5 w-3.5 shrink-0 ${color}`} />
      <span className="text-xs font-medium">{check.label}</span>
      {check.detail && (
        <span className="text-xs text-muted-foreground">— {check.detail}</span>
      )}
      {check.cta_href && (
        <Link
          href={check.cta_href}
          className="ml-auto text-[10px] font-semibold text-primary hover:underline"
        >
          Aggiorna
        </Link>
      )}
    </div>
  );
}

/* ── Clinical Alerts ── */

function AlertsBadge({ alerts }: { alerts: SessionPrepAlert[] }) {
  if (alerts.length === 0) return null;

  return (
    <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50/80 px-3 py-2 dark:border-red-900/40 dark:bg-red-950/20">
      <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-red-600 dark:text-red-400" />
      <div className="min-w-0">
        <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-red-700 dark:text-red-300">
          {alerts.length === 1 ? "Condizione clinica" : `${alerts.length} condizioni cliniche`}
        </p>
        <p className="mt-0.5 text-xs text-red-700/80 dark:text-red-300/80">
          {alerts.map((a) => a.condition_name).join(", ")}
        </p>
      </div>
    </div>
  );
}

/* ── Quality Hints ── */

function HintRow({ hint }: { hint: SessionPrepHint }) {
  const isHigh = hint.severity === "high" || hint.severity === "critical";

  return (
    <div className="flex items-start gap-2">
      <Lightbulb
        className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${isHigh ? "text-amber-500" : "text-muted-foreground"}`}
      />
      <span className="text-xs text-muted-foreground">{hint.text}</span>
    </div>
  );
}

/* ── Readiness Score Ring ── */

function ReadinessRing({ score }: { score: number }) {
  const color =
    score >= 80
      ? "text-emerald-500 dark:text-emerald-400"
      : score >= 50
        ? "text-amber-500 dark:text-amber-400"
        : "text-red-500 dark:text-red-400";

  return (
    <div className="flex flex-col items-center gap-0.5" title={`Readiness ${score}%`}>
      <span className={`text-lg font-extrabold tabular-nums ${color}`}>{score}</span>
      <span className="text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">
        ready
      </span>
    </div>
  );
}

/* ── Time formatting ── */

const TIME_FMT = new Intl.DateTimeFormat("it-IT", {
  hour: "2-digit",
  minute: "2-digit",
});

function formatTimeRange(startsAt: string, endsAt: string | null): string {
  const start = new Date(startsAt);
  if (Number.isNaN(start.getTime())) return startsAt;
  const startLabel = TIME_FMT.format(start);
  if (!endsAt) return startLabel;
  const end = new Date(endsAt);
  if (Number.isNaN(end.getTime())) return startLabel;
  return `${startLabel} – ${TIME_FMT.format(end)}`;
}

/* ── Main Card ── */

interface SessionPrepCardProps {
  item: SessionPrepItem;
  expanded?: boolean;
  onToggleExpand?: () => void;
}

export function SessionPrepCard({ item, expanded = false, onToggleExpand }: SessionPrepCardProps) {
  const isClientSession = item.client_id !== null;
  const hasIssues = item.health_checks.some((c) => c.status !== "ok");
  const borderColor = item.clinical_alerts.length > 0
    ? "border-red-200/80 dark:border-red-900/30"
    : hasIssues
      ? "border-amber-200/80 dark:border-amber-900/30"
      : "border-border/70";

  /* Non-client events (SALA, PERSONALE, etc.) */
  if (!isClientSession) {
    return (
      <div className={`rounded-2xl border ${borderColor} bg-white p-4 dark:bg-zinc-950/50`}>
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-muted/70">
            <Clock3 className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold">{item.event_title ?? item.category}</p>
              <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                {item.category}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {formatTimeRange(item.starts_at, item.ends_at)}
            </p>
          </div>
        </div>
      </div>
    );
  }

  /* Client session — rich profile card */
  const daysLabel = item.days_since_last_session !== null
    ? item.days_since_last_session === 0
      ? "oggi"
      : item.days_since_last_session === 1
        ? "ieri"
        : `${item.days_since_last_session}g fa`
    : null;

  const creditsLabel = item.contract_credits_remaining !== null && item.contract_credits_total !== null
    ? `${item.contract_credits_remaining}/${item.contract_credits_total}`
    : null;

  return (
    <button
      type="button"
      onClick={onToggleExpand}
      className={`w-full rounded-2xl border ${borderColor} bg-white p-4 text-left transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md dark:bg-zinc-950/50`}
    >
      {/* ── Row 1: Time + Name + Readiness ── */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary/10 to-primary/5">
            <User className="h-4.5 w-4.5 text-primary" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-bold">{item.client_name}</p>
              {item.is_new_client && (
                <span className="flex items-center gap-0.5 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300">
                  <Sparkles className="h-3 w-3" />
                  Nuovo
                </span>
              )}
              {item.client_age && (
                <span className="text-xs text-muted-foreground">{item.client_age} anni</span>
              )}
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock3 className="h-3 w-3" />
                {formatTimeRange(item.starts_at, item.ends_at)}
              </span>
              <span className="flex items-center gap-1">
                <CalendarDays className="h-3 w-3" />
                {item.total_sessions} session{item.total_sessions !== 1 ? "i" : "e"}
                {daysLabel && ` · ultima ${daysLabel}`}
              </span>
              {creditsLabel && (
                <span className="flex items-center gap-1">
                  <Activity className="h-3 w-3" />
                  {creditsLabel} crediti
                </span>
              )}
            </div>
          </div>
        </div>

        {item.readiness_score !== null && (
          <ReadinessRing score={item.readiness_score} />
        )}
      </div>

      {/* ── Row 2: Health check dots (always visible) ── */}
      {item.health_checks.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-3">
          {item.health_checks.map((check) => (
            <HealthCheckDot key={check.domain} check={check} />
          ))}
          {item.active_plan_name && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <HeartPulse className="h-3 w-3 text-primary" />
              {item.active_plan_name}
            </span>
          )}
        </div>
      )}

      {/* ── Row 3: Clinical alerts (always visible if present) ── */}
      {item.clinical_alerts.length > 0 && (
        <div className="mt-3">
          <AlertsBadge alerts={item.clinical_alerts} />
        </div>
      )}

      {/* ── Expanded section ── */}
      {expanded && (
        <div className="mt-4 space-y-3 border-t border-border/50 pt-4">
          {/* Health checks expanded */}
          {item.health_checks.length > 0 && (
            <div className="space-y-1.5">
              {item.health_checks.map((check) => (
                <HealthCheckRow key={check.domain} check={check} />
              ))}
            </div>
          )}

          {/* Quality hints */}
          {item.quality_hints.length > 0 && (
            <div className="space-y-1.5">
              {item.quality_hints.map((hint) => (
                <HintRow key={hint.code} hint={hint} />
              ))}
            </div>
          )}

          {/* Quick actions */}
          <div className="flex flex-wrap gap-2 pt-1">
            <Link
              href={`/clienti/${item.client_id}`}
              className="rounded-lg border border-border/70 px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted/50"
              onClick={(e) => e.stopPropagation()}
            >
              Profilo
            </Link>
            <Link
              href={`/clienti/${item.client_id}/progressi?from=oggi`}
              className="rounded-lg border border-border/70 px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted/50"
              onClick={(e) => e.stopPropagation()}
            >
              Progressi
            </Link>
          </div>
        </div>
      )}
    </button>
  );
}
