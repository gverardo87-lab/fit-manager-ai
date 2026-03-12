"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, CalendarClock, CircleAlert, Clock3 } from "lucide-react";

import { cn } from "@/lib/utils";
import type { OperationalCase, SessionPrepItem, SessionPrepResponse } from "@/types/api";
import type { PreFlightStatus } from "@/components/workspace/OggiTimeline";
import { PREFLIGHT_META } from "@/components/workspace/OggiTimeline";

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

function getSpotlightCopy(session: SessionPrepItem, status: PreFlightStatus): string {
  if (!session.client_id) return "Impegno senza cliente associato.";
  if (status === "blocked") return "Blocca la seduta finche' non hai chiarito contratto o vincoli attivi.";
  if (status === "risk") return "Rivedi alert clinici e readiness prima di entrare in sala.";
  if (status === "incomplete") return "Completa i controlli mancanti prima di iniziare la sessione.";
  if (session.is_new_client) return "Nuovo cliente: entra in seduta con contesto rapido gia' pronto.";
  return "Apri la scheda pre-seduta e conferma che tutto sia pronto.";
}

function StatPill({
  label,
  value,
  detail,
  tone = "neutral",
}: {
  label: string;
  value: number;
  detail: string;
  tone?: "neutral" | "teal" | "amber" | "red";
}) {
  const styles = {
    neutral: {
      border: "oklch(0.83 0.02 170 / 0.16)",
      background:
        "linear-gradient(180deg, oklch(0.995 0.006 95 / 0.96), oklch(0.986 0.01 170 / 0.72))",
    },
    teal: {
      border: "oklch(0.72 0.08 170 / 0.22)",
      background:
        "linear-gradient(180deg, oklch(0.99 0.01 170 / 0.92), oklch(0.97 0.018 170 / 0.68))",
    },
    amber: {
      border: "oklch(0.77 0.08 78 / 0.22)",
      background:
        "linear-gradient(180deg, oklch(0.995 0.014 88 / 0.94), oklch(0.985 0.022 82 / 0.72))",
    },
    red: {
      border: "oklch(0.64 0.12 25 / 0.18)",
      background:
        "linear-gradient(180deg, oklch(0.995 0.01 35 / 0.96), oklch(0.982 0.014 25 / 0.68))",
    },
  }[tone];

  return (
    <div
      className="rounded-[22px] px-3.5 py-3"
      style={{
        border: `0.5px solid ${styles.border}`,
        background: styles.background,
      }}
    >
      <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
        {label}
      </p>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-[24px] font-extrabold tabular-nums tracking-tight text-stone-900 dark:text-zinc-50">
          {value}
        </span>
        <span className="text-[10px] leading-5 text-stone-500 dark:text-zinc-400">
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
  spotlightSession: SessionPrepItem | null;
  spotlightStatus: PreFlightStatus;
  supportCase: OperationalCase | null;
  onSelectSession: (eventId: number) => void;
  className?: string;
}

export function OggiHero({
  prep,
  attentionCount,
  readyCount,
  extraCaseCount,
  alertClients,
  spotlightSession,
  spotlightStatus,
  supportCase,
  onSelectSession,
  className,
}: OggiHeroProps) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(id);
  }, []);

  const spotlightMeta = spotlightSession ? PREFLIGHT_META[spotlightStatus] : null;
  const supportHref = resolveCaseHref(supportCase);

  return (
    <section className={className}>
      <div
        className="rounded-[30px] px-4 py-4 sm:px-5 sm:py-5"
        style={{
          border: "0.5px solid oklch(0.80 0.03 165 / 0.14)",
          background:
            "linear-gradient(145deg, oklch(0.997 0.008 95 / 0.98), oklch(0.989 0.013 168 / 0.78) 52%, oklch(0.985 0.016 195 / 0.72))",
        }}
      >
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px] xl:items-start">
          <div className="min-w-0 space-y-3.5">
            <div className="flex flex-wrap items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
              <span>Oggi</span>
              <span>{DATE_FMT.format(now)}</span>
              <span
                className="rounded-full px-2.5 py-1 text-stone-500 shadow-sm dark:bg-zinc-900/60 dark:text-zinc-400"
                style={{ background: "oklch(1 0 0 / 0.72)" }}
              >
                {TIME_FMT.format(now)}
              </span>
            </div>

            <div className="space-y-1.5">
              <h1 className="text-[1.85rem] font-extrabold tracking-tight text-stone-900 sm:text-[2.15rem] dark:text-zinc-50">
                Prepara le sedute di oggi
              </h1>
              <p className="max-w-3xl text-[13px] leading-6 text-stone-600 dark:text-zinc-300">
                Apri le sedute davvero rilevanti, leggi subito cosa e&apos; a rischio o incompleto e
                muoviti tra sessione, contesto clinico-operativo e follow-up senza dispersione.
              </p>
            </div>

            {supportCase && (
              <div
                className="rounded-[22px] px-3.5 py-3"
                style={{
                  border: "0.5px solid oklch(0.77 0.05 80 / 0.18)",
                  background:
                    "linear-gradient(135deg, oklch(0.994 0.01 90 / 0.94), oklch(0.986 0.016 82 / 0.72))",
                }}
              >
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div className="min-w-0">
                    <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-amber-700/80 dark:text-amber-300/80">
                      Altra attenzione di oggi
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

            <div className="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-4">
              <StatPill
                label="Sedute"
                value={prep.total_sessions}
                detail={prep.total_sessions === 1 ? "in agenda oggi" : "in agenda oggi"}
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
                detail={readyCount === prep.total_sessions ? "giornata allineata" : "sedute senza blocchi visibili"}
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

          <div className="xl:w-[320px] xl:shrink-0">
            <div
              className="rounded-[26px] p-4 sm:p-5"
              style={{
                border: "0.5px solid oklch(0.78 0.03 165 / 0.16)",
                background:
                  "linear-gradient(180deg, oklch(0.995 0.008 92 / 0.96), oklch(0.981 0.018 175 / 0.70))",
              }}
            >
              <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
                <CalendarClock className="h-3.5 w-3.5" />
                Seduta da aprire
              </div>

              {spotlightSession ? (
                <div className="mt-4 space-y-3.5">
                  <div className="space-y-1.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[24px] font-extrabold tabular-nums tracking-tight text-stone-900 dark:text-zinc-50">
                        {TIME_FMT.format(new Date(spotlightSession.starts_at))}
                      </span>
                      {spotlightMeta && (
                        <span
                          className={cn(
                            "rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em]",
                            spotlightMeta.color,
                          )}
                          style={{
                            background:
                              spotlightStatus === "ready"
                                ? "oklch(0.62 0.15 150 / 0.10)"
                                : spotlightStatus === "incomplete"
                                  ? "oklch(0.75 0.12 70 / 0.10)"
                                  : "oklch(0.55 0.15 25 / 0.10)",
                          }}
                        >
                          {spotlightMeta.label}
                        </span>
                      )}
                    </div>

                    <div>
                      <p className="text-[17px] font-extrabold tracking-tight text-stone-900 dark:text-zinc-50">
                        {spotlightSession.client_name ?? spotlightSession.event_title ?? spotlightSession.category}
                      </p>
                      <p className="mt-1 text-[11px] leading-5 text-stone-600 dark:text-zinc-300">
                        {getSpotlightCopy(spotlightSession, spotlightStatus)}
                      </p>
                    </div>
                  </div>

                  <div
                    className="rounded-2xl px-3.5 py-3 shadow-sm dark:bg-zinc-950/40"
                    style={{ background: "oklch(1 0 0 / 0.68)" }}
                  >
                    <div className="flex items-center gap-2 text-[11px] text-stone-500 dark:text-zinc-400">
                      <Clock3 className="h-3.5 w-3.5" />
                      <span>
                        {spotlightSession.is_new_client ? "Nuovo cliente" : "Seduta gia' in carico oggi"}
                      </span>
                    </div>
                    <p className="mt-2 text-[12px] leading-5 text-stone-700 dark:text-zinc-200">
                      {spotlightSession.clinical_alerts.length > 0
                        ? `${spotlightSession.clinical_alerts.length} alert clinici da verificare prima di iniziare.`
                        : spotlightSession.health_checks.some((item) => item.status !== "ok")
                          ? "Sono presenti controlli da rivedere prima della seduta."
                          : "La scheda pre-seduta puo' essere confermata rapidamente."}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => onSelectSession(spotlightSession.event_id)}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-full px-4 py-3 text-sm font-bold text-white transition-transform hover:-translate-y-0.5"
                    style={{
                      background: "linear-gradient(135deg, oklch(0.47 0.11 168), oklch(0.41 0.09 198))",
                    }}
                  >
                    Apri scheda pre-seduta
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <div
                  className="mt-4 rounded-2xl px-4 py-4 shadow-sm dark:bg-zinc-950/40"
                  style={{ background: "oklch(1 0 0 / 0.68)" }}
                >
                  <div className="flex items-center gap-2 text-stone-500 dark:text-zinc-400">
                    <CircleAlert className="h-4 w-4" />
                    <p className="text-sm font-semibold">Nessuna seduta da preparare</p>
                  </div>
                  <p className="mt-2 text-[12px] leading-5 text-stone-600 dark:text-zinc-300">
                    Oggi non risultano appuntamenti con cliente in agenda.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function OggiHeroSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn("rounded-[30px] px-4 py-4 sm:px-5 sm:py-5", className)}
      style={{
        border: "0.5px solid oklch(0.80 0.03 165 / 0.12)",
        background:
          "linear-gradient(145deg, oklch(0.997 0.008 95 / 0.82), oklch(0.989 0.013 168 / 0.64))",
      }}
    >
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-4">
          <div className="h-3 w-44 rounded bg-stone-200/60 dark:bg-white/10" />
          <div className="h-9 w-72 rounded-xl bg-stone-200/60 dark:bg-white/10" />
          <div className="h-16 rounded-2xl bg-stone-200/40 dark:bg-white/10" />
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                key={index}
                className="h-20 rounded-2xl bg-stone-200/40 dark:bg-white/10"
              />
            ))}
          </div>
        </div>
        <div className="h-[248px] rounded-[24px] bg-stone-200/40 dark:bg-white/10" />
      </div>
    </div>
  );
}
