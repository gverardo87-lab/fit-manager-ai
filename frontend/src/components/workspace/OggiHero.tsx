"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

import {
  surfaceChipClassName,
  surfaceRoleClassName,
  type SurfaceTone,
} from "@/components/ui/surface-role";
import { cn } from "@/lib/utils";
import type { OperationalCase, SessionPrepResponse } from "@/types/api";

const TIME_FMT = new Intl.DateTimeFormat("it-IT", {
  hour: "2-digit",
  minute: "2-digit",
});

const DATE_FMT = new Intl.DateTimeFormat("it-IT", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

function resolveCaseHref(item: OperationalCase | null): string | null {
  if (!item) return null;
  const primaryAction = item.suggested_actions.find(
    (action) => action.enabled && action.href && action.is_primary,
  );
  if (primaryAction?.href) return primaryAction.href;
  return item.root_entity.href;
}

function getDayBrief(
  prep: SessionPrepResponse,
  attentionCount: number,
  readyCount: number,
  extraCaseCount: number,
): {
  tone: SurfaceTone;
  title: string;
  detail: string;
} {
  if (attentionCount > 0) {
    return {
      tone: "red",
      title:
        attentionCount === 1
          ? "Una seduta chiede attenzione piena"
          : `${attentionCount} sedute chiedono attenzione piena`,
      detail:
        extraCaseCount > 0
          ? "Apri prima il focus attivo e lascia gli altri casi come supporto leggero della giornata."
          : "Apri prima il focus attivo e porta in sala solo il contesto che puo' davvero cambiare la seduta.",
    };
  }

  if (prep.total_sessions > 0 && readyCount === prep.total_sessions) {
    return {
      tone: "teal",
      title: "La giornata e' in linea",
      detail:
        "Usa il focus attivo per confermare rapidamente le sedute e tenere vicino solo il contesto che serve davvero.",
    };
  }

  return {
    tone: "neutral",
    title: prep.total_sessions > 0 ? "La giornata e' sotto controllo" : "Nessuna seduta cliente in agenda",
    detail:
      prep.total_sessions > 0
        ? "La regia di oggi vive nel focus attivo: sedute, note e contesto restano compatti e leggibili."
        : "Resta a vista solo il supporto della giornata e usa l'agenda per eventuali impegni interni o follow-up.",
  };
}

function StatPill({
  label,
  value,
  detail,
  tone = "neutral",
  compact = false,
}: {
  label: string;
  value: number;
  detail: string;
  tone?: SurfaceTone;
  compact?: boolean;
}) {
  return (
    <div
      className={surfaceRoleClassName(
        { role: "signal", tone },
        compact ? "px-3 py-2.5" : "px-3.5 py-3",
      )}
    >
      <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
        {label}
      </p>
      <div className={cn("mt-1 flex items-baseline gap-2", compact && "gap-1.5")}>
        <span
          className={cn(
            "font-extrabold tabular-nums tracking-tight text-stone-900 dark:text-zinc-50",
            compact ? "text-[20px]" : "text-[24px]",
          )}
        >
          {value}
        </span>
        <span
          className={cn(
            "text-stone-500 dark:text-zinc-400",
            compact ? "text-[9.5px] leading-4" : "text-[10px] leading-5",
          )}
        >
          {detail}
        </span>
      </div>
    </div>
  );
}

interface OggiHeroProps {
  prep: SessionPrepResponse;
  attentionCount: number;
  readyCount: number;
  extraCaseCount: number;
  alertClients: number;
  supportCase: OperationalCase | null;
  compact?: boolean;
  lastUpdatedAt?: number | null;
  isRefreshing?: boolean;
  className?: string;
}

export function OggiHero({
  prep,
  attentionCount,
  readyCount,
  extraCaseCount,
  alertClients,
  supportCase,
  compact = false,
  lastUpdatedAt = null,
  isRefreshing = false,
  className,
}: OggiHeroProps) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(id);
  }, []);

  const supportHref = resolveCaseHref(supportCase);
  const dayBrief = getDayBrief(prep, attentionCount, readyCount, extraCaseCount);
  const syncLabel = lastUpdatedAt ? TIME_FMT.format(new Date(lastUpdatedAt)) : null;

  if (compact) {
    const directionColor =
      dayBrief.tone === "red"
        ? "text-red-700 dark:text-red-300"
        : dayBrief.tone === "teal"
          ? "text-emerald-700 dark:text-emerald-300"
          : "text-stone-800 dark:text-zinc-100";

    return (
      <section className={className}>
        <div
          className={surfaceRoleClassName(
            { role: "page", tone: "neutral" },
            "oggi-command-bar px-4 py-3.5 sm:px-5",
          )}
        >
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
                <span className="text-stone-500 dark:text-zinc-300">Regia di oggi</span>
                <span>{DATE_FMT.format(now)}</span>
                <span
                  className={surfaceChipClassName(
                    { tone: "neutral" },
                    "px-2.5 py-1 text-[11px] font-bold tabular-nums text-stone-500 dark:text-zinc-400",
                  )}
                >
                  {TIME_FMT.format(now)}
                </span>
                {syncLabel && (
                  <span
                    className={surfaceChipClassName(
                      { tone: isRefreshing ? "amber" : "teal" },
                      "px-2.5 py-1 text-[10px] font-bold",
                    )}
                  >
                    <span
                      className={cn(
                        "h-1.5 w-1.5 rounded-full",
                        isRefreshing ? "oggi-pulse-dot bg-amber-500" : "bg-emerald-500",
                      )}
                    />
                    {isRefreshing ? "Sync live" : `Agg. ${syncLabel}`}
                  </span>
                )}
              </div>

              <div className="mt-2.5 space-y-1.5">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
                    Cabina operativa
                  </span>
                  {supportCase && supportHref && (
                    <Link
                      href={supportHref}
                      className="inline-flex max-w-full items-center gap-1.5 text-[11px] font-semibold text-stone-600 transition-colors hover:text-stone-900 dark:text-zinc-300 dark:hover:text-zinc-100"
                    >
                      <span className="shrink-0 text-stone-400 dark:text-zinc-500">Supporto</span>
                      <span className="max-w-[280px] truncate">{supportCase.title}</span>
                      <ArrowRight className="h-3.5 w-3.5 shrink-0" />
                    </Link>
                  )}
                </div>

                <div className="space-y-1">
                  <h1 className={cn("text-[1.3rem] font-black tracking-tight sm:text-[1.55rem]", directionColor)}>
                    {dayBrief.title}
                  </h1>
                  <p className="max-w-3xl text-[11px] leading-5 text-stone-600 dark:text-zinc-300">
                    {dayBrief.detail}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-2 sm:grid-cols-2 lg:w-[440px] lg:grid-cols-4">
              <StatPill
                compact
                label="Sedute"
                value={prep.total_sessions}
                detail="clienti in agenda"
                tone="neutral"
              />
              <StatPill
                compact
                label="Attenzione"
                value={attentionCount}
                detail={
                  alertClients > 0
                    ? `${alertClients} alert clinici`
                    : "nessun blocco clinico"
                }
                tone={attentionCount > 0 ? "red" : "neutral"}
              />
              <StatPill
                compact
                label="In linea"
                value={readyCount}
                detail={
                  readyCount === prep.total_sessions && prep.total_sessions > 0
                    ? "giornata allineata"
                    : "sedute confermate"
                }
                tone={readyCount > 0 ? "teal" : "neutral"}
              />
              <StatPill
                compact
                label="Fuori seduta"
                value={extraCaseCount}
                detail={extraCaseCount > 0 ? "altre attenzioni" : "nessun caso extra"}
                tone={extraCaseCount > 0 ? "amber" : "neutral"}
              />
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className={className}>
      <div className={surfaceRoleClassName({ role: "page", tone: "neutral" }, "px-4 py-4 sm:px-5 sm:py-5")}>
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
            <span>Regia di oggi</span>
            <span>{DATE_FMT.format(now)}</span>
            <span
              className={surfaceChipClassName(
                { tone: "neutral" },
                "px-2.5 py-1 text-stone-500 dark:text-zinc-400",
              )}
            >
              {TIME_FMT.format(now)}
            </span>
          </div>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(280px,0.8fr)] xl:items-start">
            <div className="min-w-0 space-y-3.5">
              <div className="space-y-1.5">
                <h1 className="text-[1.55rem] font-extrabold tracking-tight text-stone-900 sm:text-[1.8rem] dark:text-zinc-50">
                  Regia operativa della giornata
                </h1>
                <p className="max-w-3xl text-[12px] leading-6 text-stone-600 dark:text-zinc-300">
                  La seduta in focus resta centrale. Qui sopra leggi quanto pesa davvero la giornata,
                  mentre il lavoro operativo vive piu&apos; sotto in una superficie unica e leggibile.
                </p>
              </div>

              <div
                className={surfaceRoleClassName(
                  { role: "signal", tone: dayBrief.tone },
                  "px-3.5 py-3",
                )}
              >
                <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
                  Direzione del momento
                </p>
                <p className="mt-1.5 text-[14px] font-bold tracking-tight text-stone-900 dark:text-zinc-50">
                  {dayBrief.title}
                </p>
                <p className="mt-1 text-[11px] leading-5 text-stone-600 dark:text-zinc-300">
                  {dayBrief.detail}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {supportCase && (
                <div className={surfaceRoleClassName({ role: "signal", tone: "amber" }, "px-3.5 py-3")}>
                  <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div className="min-w-0">
                      <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-amber-700/80 dark:text-amber-300/80">
                        Supporto della giornata
                      </p>
                      <p className="mt-1 truncate text-[13px] font-bold text-stone-900 dark:text-zinc-100">
                        {supportCase.title}
                      </p>
                      <p className="mt-1 text-[11px] leading-5 text-stone-600 dark:text-zinc-300">
                        {supportCase.reason}
                      </p>
                    </div>
                    {supportHref && (
                      <Link
                        href={supportHref}
                        className="inline-flex shrink-0 items-center gap-1.5 text-[12px] font-semibold text-amber-800 transition-colors hover:text-amber-900 dark:text-amber-300 dark:hover:text-amber-200"
                      >
                        Apri attenzione
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    )}
                  </div>
                </div>
              )}

              <div className="grid gap-2.5 sm:grid-cols-2">
                <StatPill
                  label="Sedute"
                  value={prep.total_sessions}
                  detail="in agenda oggi"
                  tone="neutral"
                />
                <StatPill
                  label="Da attenzionare"
                  value={attentionCount}
                  detail={
                    alertClients > 0
                      ? `${alertClients} con alert clinici`
                      : "nessun alert clinico extra"
                  }
                  tone={attentionCount > 0 ? "red" : "neutral"}
                />
                <StatPill
                  label="Pronte"
                  value={readyCount}
                  detail={
                    readyCount === prep.total_sessions ? "giornata allineata" : "sedute senza blocchi visibili"
                  }
                  tone={readyCount > 0 ? "teal" : "neutral"}
                />
                <StatPill
                  label="Fuori seduta"
                  value={extraCaseCount}
                  detail={extraCaseCount > 0 ? "altre attenzioni oggi" : "nessun caso extra"}
                  tone={extraCaseCount > 0 ? "amber" : "neutral"}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function OggiHeroSkeleton({ className }: { className?: string }) {
  return (
    <div className={surfaceRoleClassName({ role: "page", tone: "neutral" }, cn("px-4 py-4 sm:px-5 sm:py-5", className))}>
      <div className="space-y-4">
        <div className="h-3 w-44 rounded bg-stone-200/60 dark:bg-white/10" />
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(280px,0.8fr)]">
          <div className="space-y-3.5">
            <div className="h-8 w-64 rounded-xl bg-stone-200/60 dark:bg-white/10" />
            <div className="h-14 rounded-2xl bg-stone-200/40 dark:bg-white/10" />
            <div className="h-20 rounded-[24px] bg-stone-200/40 dark:bg-white/10" />
          </div>
          <div className="space-y-3">
            <div className="h-24 rounded-[24px] bg-stone-200/40 dark:bg-white/10" />
            <div className="grid gap-3 sm:grid-cols-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <div
                  key={index}
                  className="h-20 rounded-2xl bg-stone-200/40 dark:bg-white/10"
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
