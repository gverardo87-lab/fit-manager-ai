"use client";

/**
 * WeeklyPulse — Chart settimanale compatto con barre CSS gradiente.
 *
 * 7 giorni, barre teal gradiente con overlay completamento emerald,
 * barra oggi evidenziata con glow, conteggio sopra, range label.
 */

import Link from "next/link";
import { ArrowRight, BarChart3, CalendarCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { EventHydrated } from "@/hooks/useAgenda";
import { weekStartDate } from "@/lib/dashboard-helpers";

const DAY_LABELS = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"] as const;

// Deterministic skeleton heights (avoid hydration mismatch)
const SKELETON_HEIGHTS = [45, 72, 55, 80, 38, 65, 50];

interface DayData {
  total: number;
  completed: number;
}

interface WeeklyPulseProps {
  events: EventHydrated[];
  dateAnchor: Date;
  isLoading: boolean;
}

export function WeeklyPulse({ events, dateAnchor, isLoading }: WeeklyPulseProps) {
  if (isLoading) {
    return <WeeklyPulseSkeleton />;
  }

  const monday = weekStartDate(dateAnchor);
  const sundayEnd = new Date(monday);
  sundayEnd.setDate(sundayEnd.getDate() + 6);

  const todayIdx = Math.floor(
    (new Date().setHours(0, 0, 0, 0) - monday.getTime()) / (1000 * 60 * 60 * 24),
  );

  // Week range label
  const fmtOpts: Intl.DateTimeFormatOptions = { day: "2-digit", month: "short" };
  const weekLabel = `${monday.toLocaleDateString("it-IT", fmtOpts)} — ${sundayEnd.toLocaleDateString("it-IT", fmtOpts)}`;

  // Build per-day data
  const days: DayData[] = Array.from({ length: 7 }, () => ({
    total: 0,
    completed: 0,
  }));

  for (const event of events) {
    if (event.stato === "Cancellato") continue;
    const dayIndex = Math.floor(
      (event.data_inizio.getTime() - monday.getTime()) / (1000 * 60 * 60 * 24),
    );
    if (dayIndex < 0 || dayIndex > 6) continue;

    days[dayIndex].total += 1;
    if (event.stato === "Completato") {
      days[dayIndex].completed += 1;
    }
  }

  const maxCount = Math.max(...days.map((d) => d.total), 1);
  // Scala Y: minimo 5 così barre con 1-4 sessioni sono visivamente sostanziose
  const yAxisMax = Math.max(maxCount, 5);
  const totalSessions = days.reduce((a, d) => a + d.total, 0);
  const totalCompleted = days.reduce((a, d) => a + d.completed, 0);

  const hasData = totalSessions > 0;

  return (
    <div className="rounded-2xl border bg-gradient-to-br from-white via-white to-zinc-50/70 p-4 shadow-sm sm:p-5 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-800/50">
      {/* Header */}
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900/30 dark:to-teal-900/30">
            <BarChart3 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold sm:text-base">Sedute della settimana</h3>
            <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
              {weekLabel}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {hasData && (
            <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/80 px-3 py-1.5 text-right shadow-sm dark:from-zinc-900 dark:to-zinc-800/60">
              <p className="text-[9px] font-bold tracking-widest text-muted-foreground/70 uppercase">Completate</p>
              <p className="text-lg font-extrabold leading-none tabular-nums tracking-tight">
                {totalCompleted}
                <span className="ml-1 text-xs font-semibold text-muted-foreground/60">/ {totalSessions}</span>
              </p>
            </div>
          )}
          <Link href="/agenda">
            <Button variant="ghost" size="sm" className="h-8 gap-1 text-xs text-muted-foreground hover:text-foreground">
              Agenda <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Empty state */}
      {!hasData ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-muted-foreground/15 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted/50">
            <CalendarCheck className="h-6 w-6 text-muted-foreground/30" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">Nessuna seduta pianificata questa settimana</p>
          <p className="text-xs text-muted-foreground/60">Pianifica appuntamenti dall&apos;agenda</p>
        </div>
      ) : (
        <>
          {/* Bar chart */}
          <div className="relative flex items-end gap-2 sm:gap-3" style={{ height: "148px" }}>
            {/* Subtle gridlines */}
            <div className="pointer-events-none absolute inset-0 flex flex-col justify-between py-1">
              {[0, 1, 2].map((i) => (
                <div key={i} className="border-b border-zinc-100 dark:border-zinc-800/50" />
              ))}
            </div>

            {DAY_LABELS.map((label, idx) => {
              const day = days[idx];
              const isToday = idx === todayIdx;
              const isPast = idx < todayIdx;
              const barPct = (day.total / yAxisMax) * 100;
              const completedPct = day.total > 0 ? (day.completed / day.total) * 100 : 0;
              const allCompleted = day.completed === day.total && day.completed > 0;

              return (
                <div key={label} className="relative z-10 flex flex-1 flex-col items-center gap-1">
                  {/* Today subtle column highlight */}
                  {isToday && (
                    <div className="absolute -inset-x-0.5 -bottom-1 -top-3 rounded-xl bg-teal-50/60 dark:bg-teal-900/10" />
                  )}

                  {/* Count label above bar */}
                  {day.total > 0 && (
                    <span className={`relative z-10 text-[11px] font-bold tabular-nums leading-none ${
                      isToday
                        ? "text-teal-600 dark:text-teal-400"
                        : allCompleted
                          ? "text-emerald-600 dark:text-emerald-400"
                          : "text-muted-foreground/70"
                    }`}>
                      {day.completed > 0 && day.completed < day.total
                        ? `${day.completed}/${day.total}`
                        : day.total}
                    </span>
                  )}

                  {/* Bar */}
                  <div
                    className={`relative z-10 w-full max-w-[38px] overflow-hidden rounded-lg transition-all duration-700 ease-out ${
                      isToday
                        ? "ring-2 ring-teal-400/40 ring-offset-1 ring-offset-background shadow-lg shadow-teal-500/15"
                        : ""
                    }`}
                    style={{
                      height: day.total > 0 ? `${Math.max(barPct, 20)}%` : "5px",
                    }}
                  >
                    {day.total > 0 ? (
                      <>
                        {/* Background: remaining sessions (lighter teal) */}
                        <div className={`absolute inset-0 transition-colors duration-500 ${
                          isToday
                            ? "bg-gradient-to-t from-teal-400 to-teal-300"
                            : isPast
                              ? "bg-gradient-to-t from-teal-400/70 to-teal-300/50"
                              : "bg-gradient-to-t from-teal-300/40 to-teal-200/25"
                        }`} />
                        {/* Completed overlay (emerald, from bottom) */}
                        {day.completed > 0 && (
                          <div
                            className={`absolute inset-x-0 bottom-0 transition-all duration-700 ease-out ${
                              isToday
                                ? "bg-gradient-to-t from-emerald-600 to-emerald-500"
                                : isPast
                                  ? "bg-gradient-to-t from-emerald-600/85 to-emerald-500/70"
                                  : "bg-gradient-to-t from-emerald-500/60 to-emerald-400/45"
                            }`}
                            style={{ height: `${completedPct}%` }}
                          />
                        )}
                      </>
                    ) : (
                      <div className="h-full w-full bg-zinc-100 dark:bg-zinc-800/40" />
                    )}
                  </div>

                  {/* Day label */}
                  <span className={`relative z-10 text-[10px] tabular-nums ${
                    isToday
                      ? "font-bold text-teal-600 dark:text-teal-400"
                      : "font-medium text-muted-foreground/60"
                  }`}>
                    {label}
                  </span>

                  {/* Today dot indicator */}
                  {isToday && (
                    <div className="relative z-10 h-1.5 w-1.5 rounded-full bg-teal-500 shadow-sm shadow-teal-500/50" />
                  )}
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="mt-3 flex items-center gap-4 border-t pt-3">
            <div className="flex items-center gap-1.5">
              <div className="h-2.5 w-2.5 rounded-sm bg-gradient-to-br from-emerald-500 to-emerald-600" />
              <span className="text-[10px] font-medium text-muted-foreground">Completate</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="h-2.5 w-2.5 rounded-sm bg-gradient-to-br from-teal-300 to-teal-400" />
              <span className="text-[10px] font-medium text-muted-foreground">Programmate</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function WeeklyPulseSkeleton() {
  return (
    <div className="rounded-2xl border p-4 sm:p-5">
      <div className="mb-4 flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <Skeleton className="h-8 w-8 rounded-lg" />
          <div className="space-y-1">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-2.5 w-28" />
          </div>
        </div>
        <Skeleton className="h-10 w-20 rounded-xl" />
      </div>
      <div className="flex items-end gap-2.5" style={{ height: "148px" }}>
        {SKELETON_HEIGHTS.map((h, i) => (
          <div key={i} className="flex flex-1 flex-col items-center gap-1.5">
            <Skeleton className="w-full max-w-[38px] rounded-lg" style={{ height: `${h}%` }} />
            <Skeleton className="h-2.5 w-6" />
          </div>
        ))}
      </div>
    </div>
  );
}
