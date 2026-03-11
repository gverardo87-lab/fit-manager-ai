"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, CalendarClock, ShieldAlert } from "lucide-react";

import { getGreeting } from "@/lib/dashboard-helpers";
import { getStoredTrainer } from "@/lib/auth";
import { cn } from "@/lib/utils";
import type { SessionPrepResponse, WorkspaceTodayResponse } from "@/types/api";

/* ── Conic-Gradient Progress Ring (OLED-feel) ── */

function ProgressRing({
  completed,
  total,
  size = 80,
  strokeWidth = 5,
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
  const conicAngle = ratio * 360;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      {/* Conic gradient glow (subtle ambient) */}
      <div
        className="absolute inset-0 rounded-full"
        style={{
          background: isDone
            ? `conic-gradient(from -90deg, oklch(0.65 0.12 150), oklch(0.65 0.10 170), oklch(0.65 0.12 150))`
            : `conic-gradient(from -90deg, oklch(0.65 0.10 170) 0deg, oklch(0.70 0.08 160) ${conicAngle * 0.5}deg, oklch(0.65 0.10 170) ${conicAngle}deg, transparent ${conicAngle}deg)`,
          mask: `radial-gradient(farthest-side, transparent ${radius - strokeWidth / 2}px, #000 ${radius - strokeWidth / 2}px ${radius + strokeWidth / 2}px, transparent ${radius + strokeWidth / 2}px)`,
          WebkitMask: `radial-gradient(farthest-side, transparent ${radius - strokeWidth / 2}px, #000 ${radius - strokeWidth / 2}px ${radius + strokeWidth / 2}px, transparent ${radius + strokeWidth / 2}px)`,
          opacity: 0.15,
        }}
      />
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="absolute inset-0">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" strokeWidth={strokeWidth}
          className="stroke-stone-200/60 dark:stroke-white/[0.06]"
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none"
          stroke={isDone ? "oklch(0.62 0.15 150)" : "oklch(0.65 0.12 170)"}
          strokeWidth={strokeWidth} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-1000 ease-out motion-reduce:transition-none"
          style={{ transformOrigin: "center", transform: "rotate(-90deg)" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-[24px] font-extrabold tabular-nums leading-none tracking-tighter text-stone-900 dark:text-white">
          {total}
        </span>
        <span className="mt-0.5 text-[8px] font-semibold uppercase tracking-[0.2em] text-stone-400 dark:text-white/40">
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
    pieces.push(`${completed} di ${total} completate`);
  } else {
    pieces.push(`${total} ${total === 1 ? "sessione" : "sessioni"}`);
  }

  if (alertClients > 0) pieces.push(`${alertClients} alert`);
  if (focusCount > 0) pieces.push(`${focusCount} ${focusCount === 1 ? "caso" : "casi"}`);

  return pieces.join(" · ");
}

/* ── Next Event Preview ── */

function NextEventPreview({ prep, now }: { prep: SessionPrepResponse; now: Date }) {
  const nextSession = prep.sessions.find((s) => {
    const start = new Date(s.starts_at);
    return !Number.isNaN(start.getTime()) && start.getTime() > now.getTime();
  });
  if (!nextSession) return null;

  const mins = minutesUntil(nextSession.starts_at);
  if (mins === null || mins > 120) return null;

  const timeLabel = mins <= 0 ? "in corso" : mins < 60 ? `tra ${mins} min` : `tra ${Math.round(mins / 60)}h`;
  const isImminent = mins > 0 && mins <= 15;

  return (
    <div className="mt-4 flex items-center gap-3 rounded-xl border px-3 py-2 backdrop-blur-sm"
      style={{
        borderColor: "oklch(0.70 0.02 200 / 0.10)",
        background: "oklch(0.97 0.005 200 / 0.5)",
      }}
    >
      <CalendarClock className="h-3.5 w-3.5 shrink-0 text-stone-400 dark:text-zinc-500" />
      <div className="min-w-0 flex-1">
        <span className="text-[13px] font-semibold text-stone-700 dark:text-zinc-200">
          {nextSession.client_name ?? nextSession.event_title ?? nextSession.category}
        </span>
        <span className="ml-2 text-[12px] tabular-nums text-stone-400 dark:text-zinc-500">
          {TIME_FMT.format(new Date(nextSession.starts_at))}
        </span>
      </div>
      <span className={cn(
        "shrink-0 rounded-full px-2.5 py-1 text-[10px] font-bold tabular-nums",
        isImminent
          ? "text-amber-700 dark:text-amber-300 oggi-pulse-dot"
          : "text-stone-500 dark:text-zinc-400",
      )}
        style={{
          background: isImminent ? "oklch(0.75 0.12 70 / 0.10)" : "oklch(0.92 0.005 200 / 0.5)",
        }}
      >
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
    const id = window.setInterval(() => setNow(new Date()), 5_000);
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
      {/* Glass hero — invisible header, backdrop-blur, thin border */}
      <div
        className="relative overflow-hidden rounded-2xl p-6 backdrop-blur-xl sm:p-7"
        style={{
          background: "linear-gradient(145deg, oklch(0.97 0.008 170 / 0.5), oklch(0.99 0.003 200 / 0.4))",
          borderBottom: "0.5px solid oklch(0.80 0.02 170 / 0.10)",
        }}
      >
        {/* Atmospheric refraction — teal ghost sphere */}
        <div
          className="pointer-events-none absolute -left-16 -top-16 h-48 w-48 rounded-full blur-[80px]"
          style={{ background: "oklch(0.65 0.12 170 / 0.06)" }}
        />

        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          {/* Left: greeting + brief + next event */}
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-stone-400 dark:text-zinc-500">
              {dateLabel}
            </p>
            <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-stone-900 sm:text-3xl dark:text-zinc-50">
              {getGreeting()}{trainerName ? `, ${trainerName}` : ""}
            </h1>

            {/* Clock + brief */}
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <div
                className="rounded-xl px-3.5 py-2 backdrop-blur-sm"
                style={{
                  border: "0.5px solid oklch(0.70 0.02 200 / 0.10)",
                  background: "oklch(0.97 0.005 200 / 0.5)",
                }}
              >
                <span className="text-xl font-extrabold tabular-nums leading-none text-stone-800 dark:text-zinc-100">
                  {nowLabel}
                </span>
              </div>
              <p className="text-[13px] leading-5 text-stone-500 dark:text-zinc-400">{brief}</p>
            </div>

            {/* Alert badge — semantic ruby glow */}
            {alertClients > 0 && (
              <div
                className="mt-3 inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-semibold text-red-700 dark:text-red-300"
                style={{ background: "oklch(0.55 0.15 25 / 0.08)" }}
              >
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
                className="mt-3 inline-flex items-center gap-1.5 text-[11px] font-medium text-stone-400 transition-colors hover:text-stone-600 dark:text-zinc-500 dark:hover:text-zinc-300"
              >
                Apri agenda completa
                <ArrowRight className="h-3 w-3" />
              </Link>
            )}
          </div>

          {/* Right: progress ring */}
          <div className="flex items-center">
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
    <div
      className="rounded-2xl p-6 backdrop-blur-xl sm:p-7"
      style={{
        background: "linear-gradient(145deg, oklch(0.97 0.008 170 / 0.3), oklch(0.99 0.003 200 / 0.2))",
        borderBottom: "0.5px solid oklch(0.80 0.02 170 / 0.08)",
      }}
    >
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-3">
          <div className="h-3 w-32 rounded bg-stone-200/60 dark:bg-white/10" />
          <div className="h-8 w-56 rounded-lg bg-stone-200/60 dark:bg-white/10" />
          <div className="flex gap-3">
            <div className="h-10 w-20 rounded-xl bg-stone-200/40 dark:bg-white/10" />
            <div className="h-10 w-48 rounded-xl bg-stone-200/40 dark:bg-white/10" />
          </div>
        </div>
        <div className="h-[80px] w-[80px] rounded-full bg-stone-200/40 dark:bg-white/10" />
      </div>
    </div>
  );
}
