"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, CalendarClock, ShieldAlert } from "lucide-react";

import { getGreeting } from "@/lib/dashboard-helpers";
import { getStoredTrainer } from "@/lib/auth";
import type { SessionPrepResponse, WorkspaceTodayResponse } from "@/types/api";

/* ── Progress Ring SVG ── */

function ProgressRing({
  completed,
  total,
  size = 80,
  strokeWidth = 6,
}: {
  completed: number;
  total: number;
  size?: number;
  strokeWidth?: number;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const ratio = total > 0 ? Math.min(completed / total, 1) : 0;
  const offset = circumference - ratio * circumference;
  const isDone = total > 0 && completed >= total;

  return (
    <div className="relative">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="motion-reduce:transition-none"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.12)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={isDone ? "oklch(0.80 0.16 155)" : "oklch(0.85 0.12 170)"}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-1000 ease-out motion-reduce:transition-none"
          style={{ transformOrigin: "center", transform: "rotate(-90deg)" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-extrabold tabular-nums leading-none text-white">
          {total}
        </span>
        <span className="mt-0.5 text-[9px] font-semibold uppercase tracking-wider text-white/60">
          {total === 1 ? "sessione" : "sessioni"}
        </span>
      </div>
    </div>
  );
}

/* ── Time helpers ── */

const TIME_FMT = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });
const DATE_FMT = new Intl.DateTimeFormat("it-IT", { weekday: "long", day: "numeric", month: "long" });

function minutesUntil(isoDate: string): number | null {
  const target = new Date(isoDate);
  if (Number.isNaN(target.getTime())) return null;
  return Math.round((target.getTime() - Date.now()) / 60_000);
}

/* ── Brief builder ── */

function buildBrief(
  prep: SessionPrepResponse | undefined,
  focusCount: number,
  alertClients: number,
): string {
  if (!prep) return "Caricamento...";
  const total = prep.total_sessions;
  const completed = prep.sessions.filter((s) => s.category === "COMPLETATA").length;

  const pieces: string[] = [];

  if (total === 0) {
    pieces.push("Nessuna sessione in programma");
  } else if (completed === total) {
    pieces.push("Tutte le sessioni completate");
  } else if (completed > 0) {
    pieces.push(`${completed} di ${total} ${total === 1 ? "sessione completata" : "sessioni completate"}`);
  } else {
    pieces.push(`${total} ${total === 1 ? "sessione" : "sessioni"} in programma`);
  }

  if (alertClients > 0) {
    pieces.push(`${alertClients} ${alertClients === 1 ? "alert clinico" : "alert clinici"}`);
  }

  if (focusCount > 0) {
    pieces.push(`${focusCount} ${focusCount === 1 ? "caso da gestire" : "casi da gestire"}`);
  }

  return `${pieces.join(" · ")}.`;
}

/* ── Next Event Preview ── */

function NextEventPreview({
  prep,
  now,
}: {
  prep: SessionPrepResponse;
  now: Date;
}) {
  const nextSession = prep.sessions.find((s) => {
    const start = new Date(s.starts_at);
    return !Number.isNaN(start.getTime()) && start.getTime() > now.getTime();
  });

  if (!nextSession) return null;

  const mins = minutesUntil(nextSession.starts_at);
  if (mins === null || mins > 120) return null;

  const timeLabel = mins <= 0
    ? "in corso"
    : mins < 60
      ? `tra ${mins} min`
      : `tra ${Math.round(mins / 60)}h`;

  return (
    <div className="mt-3 flex items-center gap-3 rounded-xl bg-white/10 px-3 py-2 backdrop-blur-sm">
      <CalendarClock className="h-4 w-4 shrink-0 text-white/70" />
      <div className="min-w-0 flex-1">
        <span className="text-xs font-semibold text-white/90">
          {nextSession.client_name ?? nextSession.event_title ?? nextSession.category}
        </span>
        <span className="ml-2 text-xs text-white/50">
          {TIME_FMT.format(new Date(nextSession.starts_at))}
        </span>
      </div>
      <span className="shrink-0 rounded-full bg-white/15 px-2 py-0.5 text-[10px] font-bold text-white/80">
        {timeLabel}
      </span>
    </div>
  );
}

/* ── Main Hero ── */

interface OggiHeroProps {
  today: WorkspaceTodayResponse | undefined;
  prep: SessionPrepResponse | undefined;
  focusCount: number;
  alertClients: number;
  className?: string;
}

export function OggiHero({ today, prep, focusCount, alertClients, className }: OggiHeroProps) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 30_000);
    return () => window.clearInterval(id);
  }, []);

  const trainerName = useMemo(() => getStoredTrainer()?.nome ?? null, []);

  const totalSessions = prep?.total_sessions ?? 0;
  const completedSessions = prep?.sessions.filter((s) => s.category === "COMPLETATA").length ?? 0;
  const dateLabel = DATE_FMT.format(now);
  const brief = buildBrief(prep, focusCount, alertClients);
  const nowLabel = TIME_FMT.format(now);

  return (
    <section className={className}>
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-teal-600 via-teal-700 to-emerald-800 p-5 shadow-lg sm:p-6">
        {/* Decorative */}
        <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-white/5 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-8 -left-8 h-32 w-32 rounded-full bg-emerald-400/10 blur-2xl" />

        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          {/* Left: greeting + brief + next event */}
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
              {getGreeting()}{trainerName ? `, ${trainerName}` : ""}
            </h1>
            <p className="mt-1 text-sm font-medium capitalize text-white/50">{dateLabel}</p>

            {/* Live clock + brief */}
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <div className="rounded-lg bg-white/10 px-3 py-1.5 backdrop-blur-sm">
                <span className="text-lg font-extrabold tabular-nums leading-none text-white">
                  {nowLabel}
                </span>
              </div>
              <p className="text-[13px] leading-5 text-white/70">{brief}</p>
            </div>

            {/* Alert badge (solo se presenti) */}
            {alertClients > 0 && (
              <div className="mt-2.5 inline-flex items-center gap-1.5 rounded-full bg-red-500/20 px-2.5 py-1 text-xs font-semibold text-red-200">
                <ShieldAlert className="h-3 w-3" />
                {alertClients} {alertClients === 1 ? "alert clinico" : "alert clinici"}
              </div>
            )}

            {/* Next event preview */}
            {prep && <NextEventPreview prep={prep} now={now} />}

            {/* Agenda link */}
            {today && (
              <Link
                href="/agenda"
                className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-white/50 transition-colors hover:text-white/80"
              >
                Apri agenda completa
                <ArrowRight className="h-3 w-3" />
              </Link>
            )}
          </div>

          {/* Right: progress ring */}
          <div className="flex items-center gap-5">
            <ProgressRing completed={completedSessions} total={totalSessions} />
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── Skeleton ── */

export function OggiHeroSkeleton() {
  return (
    <div className="rounded-2xl bg-gradient-to-br from-teal-600/50 via-teal-700/50 to-emerald-800/50 p-5 sm:p-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-3">
          <div className="h-7 w-56 rounded-lg bg-white/10" />
          <div className="h-4 w-36 rounded bg-white/10" />
          <div className="flex gap-3">
            <div className="h-8 w-20 rounded-lg bg-white/10" />
            <div className="h-8 w-48 rounded-lg bg-white/10" />
          </div>
        </div>
        <div className="h-20 w-20 rounded-full bg-white/10" />
      </div>
    </div>
  );
}
