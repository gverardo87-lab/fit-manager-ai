"use client";

/**
 * CommandStrip — Hero banner gradient teal della dashboard.
 *
 * Saluto contestuale + orologio live + status badge + 3 GaugeRing.
 * "La plancia della nave."
 */

import { useEffect, useMemo, useState } from "react";
import { CalendarCheck } from "lucide-react";
import { GaugeRing } from "@/components/dashboard/GaugeRing";
import { getGreeting, computeAgendaCompletion, buildAgendaLiveInfo, formatCountdown } from "@/lib/dashboard-helpers";
import { getStoredTrainer } from "@/lib/auth";
import type { DashboardSummary } from "@/types/api";
import type { EventHydrated } from "@/hooks/useAgenda";

interface CommandStripProps {
  summary: DashboardSummary | undefined;
  todayEvents: EventHydrated[];
  dateAnchor: Date;
}

export function CommandStrip({ summary, todayEvents, dateAnchor }: CommandStripProps) {
  const [clockTime, setClockTime] = useState(() => new Date());

  useEffect(() => {
    const timerId = window.setInterval(() => setClockTime(new Date()), 5000);
    return () => window.clearInterval(timerId);
  }, []);

  const trainerName = useMemo(() => {
    const trainer = getStoredTrainer();
    return trainer?.nome ?? null;
  }, []);

  const liveInfo = useMemo(
    () => buildAgendaLiveInfo(todayEvents, clockTime),
    [todayEvents, clockTime],
  );

  const agendaCompletion = useMemo(
    () => computeAgendaCompletion(todayEvents),
    [todayEvents],
  );

  const nowLabel = clockTime.toLocaleTimeString("it-IT", {
    hour: "2-digit",
    minute: "2-digit",
  });

  const dateLabel = dateAnchor.toLocaleDateString("it-IT", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  // Live status
  const statusText = liveInfo.mode === "in_progress"
    ? `In corso — fine tra ${formatCountdown(liveInfo.remainingMs)}`
    : liveInfo.mode === "next_up"
      ? `Prossima tra ${formatCountdown(liveInfo.remainingMs)}`
      : todayEvents.length > 0
        ? "Giornata completata"
        : "Nessuna sessione";

  const statusDotColor = liveInfo.mode === "in_progress"
    ? "bg-amber-400 animate-pulse"
    : liveInfo.mode === "next_up"
      ? "bg-blue-400"
      : "bg-emerald-400";

  const activeClients = summary?.active_clients ?? 0;
  const todayAppointments = summary?.todays_appointments ?? todayEvents.length;

  return (
    <div
      data-guide="dashboard-header"
      className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-teal-600 via-teal-700 to-emerald-800 p-5 shadow-lg sm:p-6"
    >
      {/* Decorative background elements */}
      <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-white/5 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-8 -left-8 h-32 w-32 rounded-full bg-emerald-400/10 blur-2xl" />

      <div className="relative flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        {/* Left: greeting + date + live status */}
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
            {getGreeting()}, Dott.ssa Chiara Bassani
          </h1>
          <p className="mt-1 text-sm font-medium capitalize text-white/60">
            {dateLabel}
          </p>

          {/* Live status bar */}
          <div className="mt-3 flex flex-wrap items-center gap-3">
            {/* Clock */}
            <div className="flex items-center gap-2 rounded-lg bg-white/10 px-3 py-1.5 backdrop-blur-sm">
              <span className="text-lg font-extrabold tabular-nums text-white leading-none">
                {nowLabel}
              </span>
            </div>

            {/* Status */}
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${statusDotColor}`} />
              <span className="text-xs font-medium text-white/70">
                {statusText}
              </span>
            </div>

            {/* Today sessions badge */}
            <div className="flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-1 text-xs font-semibold text-white/80">
              <CalendarCheck className="h-3 w-3" />
              {todayAppointments} {todayAppointments === 1 ? "sessione" : "sessioni"}
            </div>
          </div>
        </div>

        {/* Right: 3 GaugeRing */}
        <div className="flex items-center gap-4 sm:gap-5">
          <GaugeRing
            value={activeClients}
            max={Math.max(activeClients, 1)}
            label="Clienti"
            color="oklch(0.85 0.12 170)"
          />
          <GaugeRing
            value={agendaCompletion}
            max={100}
            label="Agenda"
            suffix="%"
            color={agendaCompletion >= 70 ? "oklch(0.80 0.15 155)" : agendaCompletion >= 40 ? "oklch(0.80 0.15 80)" : "oklch(0.75 0.18 25)"}
          />
          <GaugeRing
            value={todayAppointments}
            max={Math.max(todayAppointments, 1)}
            label="Oggi"
            color="oklch(0.85 0.10 200)"
          />
        </div>
      </div>
    </div>
  );
}

// ── Skeleton ──

export function CommandStripSkeleton() {
  return (
    <div className="rounded-2xl bg-gradient-to-br from-teal-600/50 via-teal-700/50 to-emerald-800/50 p-5 sm:p-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-3">
          <div className="h-7 w-56 rounded-lg bg-white/10" />
          <div className="h-4 w-36 rounded bg-white/10" />
          <div className="flex gap-3">
            <div className="h-8 w-20 rounded-lg bg-white/10" />
            <div className="h-8 w-40 rounded-lg bg-white/10" />
          </div>
        </div>
        <div className="flex gap-5">
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex flex-col items-center gap-1">
              <div className="h-14 w-14 rounded-full bg-white/10" />
              <div className="h-2 w-10 rounded bg-white/10" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
