"use client";

import Link from "next/link";
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Clock3,
  HeartPulse,
  Lightbulb,
  ShieldAlert,
  Sparkles,
  UserRound,
  XCircle,
} from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { appendFromParam } from "@/lib/url-state";
import { cn } from "@/lib/utils";
import type { HealthCheckStatus, SessionPrepHint, SessionPrepItem } from "@/types/api";

const STATUS_META: Record<
  HealthCheckStatus,
  {
    icon: typeof CheckCircle2;
    iconClassName: string;
    tone: string;
  }
> = {
  ok: {
    icon: CheckCircle2,
    iconClassName: "text-emerald-600 dark:text-emerald-400",
    tone: "border-emerald-200/80 bg-emerald-50/80 dark:border-emerald-900/30 dark:bg-emerald-950/20",
  },
  warning: {
    icon: AlertTriangle,
    iconClassName: "text-amber-600 dark:text-amber-400",
    tone: "border-amber-200/80 bg-amber-50/80 dark:border-amber-900/30 dark:bg-amber-950/20",
  },
  critical: {
    icon: XCircle,
    iconClassName: "text-red-600 dark:text-red-400",
    tone: "border-red-200/80 bg-red-50/80 dark:border-red-900/30 dark:bg-red-950/20",
  },
  missing: {
    icon: XCircle,
    iconClassName: "text-red-600 dark:text-red-400",
    tone: "border-red-200/80 bg-red-50/80 dark:border-red-900/30 dark:bg-red-950/20",
  },
};

const DATE_FORMATTER = new Intl.DateTimeFormat("it-IT", {
  day: "numeric",
  month: "short",
});

const TIME_FORMATTER = new Intl.DateTimeFormat("it-IT", {
  hour: "2-digit",
  minute: "2-digit",
});

function formatTimeRange(startsAt: string, endsAt: string | null): string {
  const start = new Date(startsAt);
  if (Number.isNaN(start.getTime())) {
    return startsAt;
  }

  const startLabel = TIME_FORMATTER.format(start);
  if (!endsAt) {
    return startLabel;
  }

  const end = new Date(endsAt);
  if (Number.isNaN(end.getTime())) {
    return startLabel;
  }

  return `${startLabel} - ${TIME_FORMATTER.format(end)}`;
}

function formatShortDate(value: string | null): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return DATE_FORMATTER.format(parsed);
}

function buildCreditsLabel(item: SessionPrepItem): string | null {
  if (item.contract_credits_remaining === null || item.contract_credits_total === null) {
    return null;
  }

  return `${item.contract_credits_remaining}/${item.contract_credits_total} crediti`;
}

function buildLastSessionLabel(item: SessionPrepItem): string {
  if (item.days_since_last_session === null) {
    return "Prima sessione o storico incompleto";
  }

  if (item.days_since_last_session === 0) {
    return "Ultima sessione oggi";
  }

  if (item.days_since_last_session === 1) {
    return "Ultima sessione ieri";
  }

  if (item.last_session_date) {
    const lastSessionDate = formatShortDate(item.last_session_date);
    if (lastSessionDate) {
      return `Ultima sessione ${lastSessionDate}`;
    }
  }

  return `Ultima sessione ${item.days_since_last_session} giorni fa`;
}

function CompactStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: string;
}) {
  return (
    <div className={cn("rounded-[16px] border px-3 py-2.5", tone ?? "border-stone-200/80 bg-white/80 dark:border-zinc-800 dark:bg-zinc-950/50")}>
      <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-[12px] font-medium leading-5 text-foreground/90">{value}</p>
    </div>
  );
}

function HealthCheckRow({ item }: { item: SessionPrepItem["health_checks"][number] }) {
  const meta = STATUS_META[item.status];
  const Icon = meta.icon;

  return (
    <div className={cn("rounded-[16px] border px-3 py-2.5", meta.tone)}>
      <div className="flex items-start gap-2.5">
        <Icon className={cn("mt-0.5 h-4 w-4 shrink-0", meta.iconClassName)} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-[12px] font-semibold">{item.label}</p>
            {item.days_since_last !== null ? (
              <span className="rounded-full bg-white/80 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground dark:bg-zinc-950/60">
                {item.days_since_last === 0 ? "oggi" : `${item.days_since_last}g`}
              </span>
            ) : null}
          </div>
          <p className="mt-0.5 text-[11px] leading-5 text-muted-foreground">
            {item.detail ?? "Nessun dettaglio aggiuntivo disponibile."}
          </p>
          {item.cta_href ? (
            <Link
              href={appendFromParam(item.cta_href, "oggi")}
              className="mt-1 inline-flex text-[11px] font-semibold text-primary hover:underline"
            >
              Aggiorna
            </Link>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function HintRow({ hint }: { hint: SessionPrepHint }) {
  return (
    <div className="rounded-[16px] border border-stone-200/80 bg-white/80 px-3 py-2.5 dark:border-zinc-800 dark:bg-zinc-950/50">
      <div className="flex items-start gap-2.5">
        <Lightbulb
          className={cn(
            "mt-0.5 h-4 w-4 shrink-0",
            hint.severity === "critical" || hint.severity === "high"
              ? "text-amber-600 dark:text-amber-400"
              : "text-muted-foreground",
          )}
        />
        <div className="min-w-0">
          <p className="text-[12px] leading-5 text-foreground/85">{hint.text}</p>
          {hint.cta_href ? (
            <Link
              href={appendFromParam(hint.cta_href, "oggi")}
              className="mt-1 inline-flex text-[11px] font-semibold text-primary hover:underline"
            >
              Vai al punto
            </Link>
          ) : null}
        </div>
      </div>
    </div>
  );
}

interface OggiClientContextPanelProps {
  item: SessionPrepItem;
  embedded?: boolean;
  className?: string;
}

export function OggiClientContextPanel({
  item,
  embedded = false,
  className,
}: OggiClientContextPanelProps) {
  if (item.client_id === null || !item.client_name) {
    return null;
  }

  const creditsLabel = buildCreditsLabel(item);
  const lastSessionLabel = buildLastSessionLabel(item);
  const timeRangeLabel = formatTimeRange(item.starts_at, item.ends_at);
  const clientSinceLabel = formatShortDate(item.client_since);
  const checksNeedingAttention = item.health_checks.filter((check) => check.status !== "ok");
  const visibleChecks = checksNeedingAttention.length > 0 ? checksNeedingAttention : item.health_checks.slice(0, 2);
  const visibleHints = item.quality_hints.slice(0, 2);

  return (
    <section
      className={cn(
        "min-h-0",
        !embedded &&
          "overflow-hidden rounded-[26px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,246,242,0.98))] shadow-[0_24px_54px_-44px_rgba(41,37,36,0.28)] dark:border-zinc-800 dark:bg-[linear-gradient(180deg,rgba(24,24,27,0.98),rgba(20,20,24,0.98))]",
        className,
      )}
    >
      <div
        className={cn(
          "px-4 py-3.5",
          !embedded && "border-b border-stone-200/80 dark:border-zinc-800",
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-100 via-white to-amber-100 dark:from-emerald-950/30 dark:to-amber-950/20">
              <UserRound className="h-4.5 w-4.5 text-emerald-700 dark:text-emerald-300" />
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-[15px] font-semibold">{item.client_name}</h3>
                {item.is_new_client ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300">
                    <Sparkles className="h-3 w-3" />
                    Nuovo
                  </span>
                ) : null}
                {item.client_age ? (
                  <span className="text-[11px] text-muted-foreground">{item.client_age} anni</span>
                ) : null}
              </div>
              <p className="mt-0.5 text-[12px] text-muted-foreground">
                Snapshot cliente per questa sessione.
              </p>
            </div>
          </div>

          {item.readiness_score !== null ? (
            <div className="rounded-[18px] border border-emerald-200/80 bg-emerald-50/90 px-3 py-2 text-right dark:border-emerald-900/30 dark:bg-emerald-950/20">
              <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Readiness
              </p>
              <p className="mt-1 text-[20px] font-bold leading-none tabular-nums text-emerald-700 dark:text-emerald-300">
                {item.readiness_score}%
              </p>
            </div>
          ) : null}
        </div>

        <div className="mt-3 flex flex-wrap gap-1.5 text-[11px] text-muted-foreground">
          <span className="inline-flex items-center gap-1 rounded-full bg-stone-100 px-2.5 py-1 dark:bg-zinc-800">
            <Clock3 className="h-3.5 w-3.5" />
            {timeRangeLabel}
          </span>
          <span className="inline-flex items-center gap-1 rounded-full bg-stone-100 px-2.5 py-1 dark:bg-zinc-800">
            <CalendarDays className="h-3.5 w-3.5" />
            {lastSessionLabel}
          </span>
          {item.active_plan_name ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-stone-100 px-2.5 py-1 dark:bg-zinc-800">
              <HeartPulse className="h-3.5 w-3.5" />
              {item.active_plan_name}
            </span>
          ) : null}
          {clientSinceLabel ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-stone-100 px-2.5 py-1 dark:bg-zinc-800">
              <UserRound className="h-3.5 w-3.5" />
              Cliente da {clientSinceLabel}
            </span>
          ) : null}
        </div>
      </div>

      <ScrollArea className={cn("min-h-0", embedded ? "max-h-[320px]" : "max-h-none")}>
        <div className="space-y-3.5 px-4 py-3.5">
          <div className="grid gap-2 sm:grid-cols-2">
            <CompactStat
              label="Progressione"
              value={`${item.completed_sessions}/${item.total_sessions} sessioni completate`}
            />
            <CompactStat
              label="Crediti"
              value={creditsLabel ?? "Nessun pacchetto crediti attivo"}
            />
            <CompactStat
              label="Check da rivedere"
              value={
                checksNeedingAttention.length > 0
                  ? `${checksNeedingAttention.length} aree da sistemare`
                  : "Profilo pronto"
              }
              tone={
                checksNeedingAttention.length > 0
                  ? "border-amber-200/80 bg-amber-50/80 dark:border-amber-900/30 dark:bg-amber-950/20"
                  : "border-emerald-200/80 bg-emerald-50/80 dark:border-emerald-900/30 dark:bg-emerald-950/20"
              }
            />
            <CompactStat
              label="Alert clinici"
              value={
                item.clinical_alerts.length > 0
                  ? `${item.clinical_alerts.length} condizioni segnalate`
                  : "Nessuna criticita aperta"
              }
              tone={
                item.clinical_alerts.length > 0
                  ? "border-red-200/80 bg-red-50/80 dark:border-red-900/30 dark:bg-red-950/20"
                  : "border-stone-200/80 bg-white/80 dark:border-zinc-800 dark:bg-zinc-950/50"
              }
            />
          </div>

          {item.event_notes ? (
            <div className="rounded-[18px] border border-stone-200/80 bg-white/80 px-3 py-2.5 dark:border-zinc-800 dark:bg-zinc-950/50">
              <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Note appuntamento
              </p>
              <p className="mt-1 text-[13px] leading-5 text-foreground/85">{item.event_notes}</p>
            </div>
          ) : null}

          {item.clinical_alerts.length > 0 ? (
            <div className="rounded-[18px] border border-red-200/80 bg-red-50/90 px-3 py-2.5 dark:border-red-900/30 dark:bg-red-950/20">
              <div className="flex items-start gap-2.5">
                <ShieldAlert className="mt-0.5 h-4.5 w-4.5 shrink-0 text-red-600 dark:text-red-400" />
                <div className="min-w-0">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-red-700 dark:text-red-300">
                    Attenzione clinica
                  </p>
                  <p className="mt-1 text-[13px] leading-5 text-red-700/90 dark:text-red-300/85">
                    {item.clinical_alerts.map((alert) => alert.condition_name).join(", ")}
                  </p>
                </div>
              </div>
            </div>
          ) : null}

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <HeartPulse className="h-4 w-4 text-muted-foreground" />
              <h4 className="text-[13px] font-semibold">Checklist rapida</h4>
            </div>
            <div className="space-y-1.5">
              {visibleChecks.length > 0 ? (
                visibleChecks.map((check) => <HealthCheckRow key={check.domain} item={check} />)
              ) : (
                <div className="rounded-[16px] border border-emerald-200/80 bg-emerald-50/80 px-3 py-2.5 dark:border-emerald-900/30 dark:bg-emerald-950/20">
                  <p className="text-[12px] font-medium text-emerald-700 dark:text-emerald-300">
                    Nessun check aperto da rivedere.
                  </p>
                </div>
              )}
            </div>
          </div>

          {visibleHints.length > 0 ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-muted-foreground" />
                <h4 className="text-[13px] font-semibold">Spunti utili</h4>
              </div>
              <div className="space-y-1.5">
                {visibleHints.map((hint) => (
                  <HintRow key={hint.code} hint={hint} />
                ))}
              </div>
            </div>
          ) : null}

          <div className="flex flex-wrap gap-2 pt-0.5">
            <Link
              href={`/clienti/${item.client_id}?from=oggi`}
              className="inline-flex items-center rounded-full border border-stone-200/80 px-3 py-2 text-[12px] font-medium text-foreground transition-colors hover:bg-stone-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
            >
              Profilo cliente
            </Link>
            <Link
              href={`/clienti/${item.client_id}/misurazioni?from=oggi`}
              className="inline-flex items-center rounded-full border border-stone-200/80 px-3 py-2 text-[12px] font-medium text-foreground transition-colors hover:bg-stone-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
            >
              Misurazioni
            </Link>
          </div>
        </div>
      </ScrollArea>
    </section>
  );
}
