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
  size = 88,
  strokeWidth = 7,
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

  // Conic gradient via CSS background on a ring div
  const conicAngle = ratio * 360;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      {/* Conic gradient background ring */}
      <div
        className="absolute inset-0 rounded-full"
        style={{
          background: isDone
            ? `conic-gradient(from -90deg, oklch(0.80 0.18 155), oklch(0.75 0.16 170), oklch(0.80 0.18 155))`
            : `conic-gradient(from -90deg, oklch(0.80 0.14 170) 0deg, oklch(0.90 0.12 160) ${conicAngle * 0.5}deg, oklch(0.80 0.14 170) ${conicAngle}deg, transparent ${conicAngle}deg)`,
          mask: `radial-gradient(farthest-side, transparent ${radius - strokeWidth / 2}px, #000 ${radius - strokeWidth / 2}px ${radius + strokeWidth / 2}px, transparent ${radius + strokeWidth / 2}px)`,
          WebkitMask: `radial-gradient(farthest-side, transparent ${radius - strokeWidth / 2}px, #000 ${radius - strokeWidth / 2}px ${radius + strokeWidth / 2}px, transparent ${radius + strokeWidth / 2}px)`,
          opacity: 0.2,
        }}
      />
      {/* SVG stroke ring (sharp, animated) */}
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="absolute inset-0">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none"
          stroke={isDone ? "oklch(0.82 0.18 155)" : "oklch(0.88 0.12 170)"}
          strokeWidth={strokeWidth} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-1000 ease-out motion-reduce:transition-none"
          style={{ transformOrigin: "center", transform: "rotate(-90deg)" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-[28px] font-extrabold tabular-nums leading-none tracking-tighter text-white">
          {total}
        </span>
        <span className="mt-0.5 text-[8px] font-semibold uppercase tracking-[0.2em] text-white/45">
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
    <div className="mt-4 flex items-center gap-3 rounded-2xl border border-white/[0.08] bg-white/[0.06] px-3.5 py-2.5 backdrop-blur-sm">
      <CalendarClock className="h-4 w-4 shrink-0 text-white/60" />
      <div className="min-w-0 flex-1">
        <span className="text-[13px] font-semibold text-white/90">
          {nextSession.client_name ?? nextSession.event_title ?? nextSession.category}
        </span>
        <span className="ml-2 text-[12px] tabular-nums text-white/40">
          {TIME_FMT.format(new Date(nextSession.starts_at))}
        </span>
      </div>
      <span className={cn(
        "shrink-0 rounded-full px-2.5 py-1 text-[10px] font-bold tabular-nums",
        isImminent ? "bg-amber-400/20 text-amber-200 oggi-pulse-dot" : "bg-white/10 text-white/70",
      )}>
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
      <div className="relative overflow-hidden rounded-2xl p-6 sm:p-7"
        style={{
          background: "linear-gradient(135deg, oklch(0.32 0.08 175) 0%, oklch(0.28 0.10 170) 40%, oklch(0.24 0.09 165) 100%)",
          boxShadow: "0 4px 6px oklch(0.20 0.06 170 / 0.15), 0 20px 50px -12px oklch(0.20 0.10 170 / 0.30)",
        }}
      >
        {/* Atmospheric decorations */}
        <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full blur-[80px]"
          style={{ background: "oklch(0.45 0.12 165 / 0.25)" }} />
        <div className="pointer-events-none absolute -bottom-10 -left-10 h-40 w-40 rounded-full blur-[60px]"
          style={{ background: "oklch(0.40 0.10 180 / 0.15)" }} />

        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          {/* Left: greeting + brief + next event */}
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/35">
              {dateLabel}
            </p>
            <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-white sm:text-3xl">
              {getGreeting()}{trainerName ? `, ${trainerName}` : ""}
            </h1>

            {/* Clock + brief */}
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <div className="rounded-xl border border-white/[0.08] bg-white/[0.06] px-3.5 py-2 backdrop-blur-sm">
                <span className="text-xl font-extrabold tabular-nums leading-none text-white">
                  {nowLabel}
                </span>
              </div>
              <p className="text-[13px] leading-5 text-white/55">{brief}</p>
            </div>

            {/* Alert badge */}
            {alertClients > 0 && (
              <div className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-red-500/15 px-3 py-1.5 text-[11px] font-semibold text-red-200/90">
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
                className="mt-3 inline-flex items-center gap-1.5 text-[11px] font-medium text-white/35 transition-colors hover:text-white/65"
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
    <div className="rounded-2xl p-6 sm:p-7"
      style={{ background: "linear-gradient(135deg, oklch(0.32 0.08 175 / 0.5), oklch(0.24 0.09 165 / 0.5))" }}
    >
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-3">
          <div className="h-3 w-32 rounded bg-white/10" />
          <div className="h-8 w-56 rounded-lg bg-white/10" />
          <div className="flex gap-3">
            <div className="h-10 w-20 rounded-xl bg-white/10" />
            <div className="h-10 w-48 rounded-xl bg-white/10" />
          </div>
        </div>
        <div className="h-[88px] w-[88px] rounded-full bg-white/10" />
      </div>
    </div>
  );
}
