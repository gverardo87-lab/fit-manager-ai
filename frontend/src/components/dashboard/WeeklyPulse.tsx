"use client";

/**
 * WeeklyPulse — Grafico settimanale Recharts BarChart stacked.
 *
 * Barre impilate completate/in programma, tooltip hover,
 * scala Y adattiva (minimo 5), indicatore "oggi" su asse X.
 */

import Link from "next/link";
import { ArrowRight, BarChart3, CalendarCheck } from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import type { EventHydrated } from "@/hooks/useAgenda";
import { weekStartDate } from "@/lib/dashboard-helpers";

const DAY_LABELS = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"] as const;

const chartConfig = {
  completate: { label: "Completate", color: "oklch(0.55 0.16 155)" },
  inProgramma: { label: "In programma", color: "oklch(0.75 0.12 170)" },
} satisfies ChartConfig;

interface TickProps {
  x: number;
  y: number;
  payload: { value: string };
}

interface WeeklyPulseProps {
  events: EventHydrated[];
  dateAnchor: Date;
  isLoading: boolean;
}

export function WeeklyPulse({ events, dateAnchor, isLoading }: WeeklyPulseProps) {
  if (isLoading) return <WeeklyPulseSkeleton />;

  const monday = weekStartDate(dateAnchor);
  const sundayEnd = new Date(monday);
  sundayEnd.setDate(sundayEnd.getDate() + 6);

  const todayIdx = Math.floor(
    (new Date().setHours(0, 0, 0, 0) - monday.getTime()) / (1000 * 60 * 60 * 24),
  );

  const fmtOpts: Intl.DateTimeFormatOptions = { day: "2-digit", month: "short" };
  const weekLabel = `${monday.toLocaleDateString("it-IT", fmtOpts)} — ${sundayEnd.toLocaleDateString("it-IT", fmtOpts)}`;

  // Build per-day data
  const days = Array.from({ length: 7 }, () => ({ total: 0, completed: 0 }));
  for (const event of events) {
    if (event.stato === "Cancellato") continue;
    const dayIndex = Math.floor(
      (event.data_inizio.getTime() - monday.getTime()) / (1000 * 60 * 60 * 24),
    );
    if (dayIndex < 0 || dayIndex > 6) continue;
    days[dayIndex].total += 1;
    if (event.stato === "Completato") days[dayIndex].completed += 1;
  }

  const totalSessions = days.reduce((a, d) => a + d.total, 0);
  const totalCompleted = days.reduce((a, d) => a + d.completed, 0);
  const hasData = totalSessions > 0;

  const chartData = DAY_LABELS.map((label, idx) => ({
    day: label,
    completate: days[idx].completed,
    inProgramma: days[idx].total - days[idx].completed,
  }));

  // Custom XAxis tick: today highlighted teal + dot
  const renderTick = ({ x, y, payload }: TickProps) => {
    const idx = (DAY_LABELS as readonly string[]).indexOf(payload.value);
    const today = idx >= 0 && idx === todayIdx;
    return (
      <g>
        <text
          x={x}
          y={y + 14}
          textAnchor="middle"
          fill={today ? "oklch(0.50 0.15 170)" : "currentColor"}
          fontWeight={today ? 700 : 400}
          fontSize={today ? 12 : 11}
          opacity={today ? 1 : 0.55}
        >
          {payload.value}
        </text>
        {today && <circle cx={x} cy={y + 24} r={2.5} fill="oklch(0.50 0.15 170)" />}
      </g>
    );
  };

  return (
    <div className="rounded-2xl border bg-gradient-to-br from-white via-white to-zinc-50/70 p-4 shadow-sm sm:p-5 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-800/50">
      {/* Header */}
      <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
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
              <p className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground/70">Completate</p>
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

      {/* Chart or empty state */}
      {!hasData ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-muted-foreground/15 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted/50">
            <CalendarCheck className="h-6 w-6 text-muted-foreground/30" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">Nessuna seduta pianificata questa settimana</p>
          <p className="text-xs text-muted-foreground/60">Pianifica appuntamenti dall&apos;agenda</p>
        </div>
      ) : (
        <ChartContainer config={chartConfig} className="h-[200px] w-full">
          <BarChart data={chartData} maxBarSize={44} barCategoryGap="20%">
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis
              dataKey="day"
              tickLine={false}
              axisLine={false}
              tick={renderTick}
              tickMargin={4}
            />
            <YAxis
              allowDecimals={false}
              tickLine={false}
              axisLine={false}
              width={20}
              fontSize={11}
              domain={[0, (dataMax: number) => Math.max(Math.ceil(dataMax * 1.2), 5)]}
            />
            <ChartTooltip
              cursor={{ fill: "oklch(0.55 0.15 170 / 0.06)" }}
              content={<ChartTooltipContent />}
            />
            <Bar
              dataKey="completate"
              stackId="week"
              fill="var(--color-completate)"
              radius={[0, 0, 4, 4]}
            />
            <Bar
              dataKey="inProgramma"
              stackId="week"
              fill="var(--color-inProgramma)"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ChartContainer>
      )}
    </div>
  );
}

function WeeklyPulseSkeleton() {
  return (
    <div className="rounded-2xl border p-4 sm:p-5">
      <div className="mb-2 flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <Skeleton className="h-8 w-8 rounded-lg" />
          <div className="space-y-1">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-2.5 w-28" />
          </div>
        </div>
        <Skeleton className="h-10 w-20 rounded-xl" />
      </div>
      <Skeleton className="h-[200px] w-full rounded-lg" />
    </div>
  );
}
