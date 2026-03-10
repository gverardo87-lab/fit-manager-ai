"use client";

/**
 * WeeklyPulse — Grafico settimanale premium con Recharts BarChart.
 *
 * Barre impilate per categoria evento con gradiente SVG,
 * tooltip ricco con breakdown, scala Y adattiva (minimo 5),
 * indicatore "oggi" su asse X, legenda dinamica solo categorie attive.
 */

import { useMemo } from "react";
import Link from "next/link";
import { ArrowRight, BarChart3, CalendarCheck } from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ChartContainer,
  ChartTooltip,
  type ChartConfig,
} from "@/components/ui/chart";
import type { EventHydrated } from "@/hooks/useAgenda";
import { weekStartDate } from "@/lib/dashboard-helpers";

// ── Categorie evento ──

const CATEGORIES = [
  { key: "PT",         label: "Personal Training", color: "#3b82f6", light: "#93c5fd" },
  { key: "SALA",       label: "Sala",              color: "#10b981", light: "#6ee7b7" },
  { key: "CORSO",      label: "Corso",             color: "#8b5cf6", light: "#c4b5fd" },
  { key: "COLLOQUIO",  label: "Colloquio",         color: "#f59e0b", light: "#fcd34d" },
  { key: "PERSONALE",  label: "Personale",         color: "#ec4899", light: "#f9a8d4" },
] as const;

type CategoryKey = (typeof CATEGORIES)[number]["key"];
type CategoryInfo = (typeof CATEGORIES)[number];

const chartConfig = Object.fromEntries(
  CATEGORIES.map((c) => [c.key, { label: c.label, color: c.color }]),
) as Record<CategoryKey, { label: string; color: string }> satisfies ChartConfig;

const DAY_LABELS = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"] as const;

const FULL_DAY_NAMES: Record<string, string> = {
  Lun: "Lunedì", Mar: "Martedì", Mer: "Mercoledì",
  Gio: "Giovedì", Ven: "Venerdì", Sab: "Sabato", Dom: "Domenica",
};

// ── Types ──

interface DayEntry {
  day: string;
  PT: number;
  SALA: number;
  CORSO: number;
  COLLOQUIO: number;
  PERSONALE: number;
}

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

// ── Component ──

export function WeeklyPulse({ events, dateAnchor, isLoading }: WeeklyPulseProps) {
  const monday = weekStartDate(dateAnchor);
  const mondayTs = monday.getTime();
  const sundayEnd = new Date(monday);
  sundayEnd.setDate(sundayEnd.getDate() + 6);

  const todayIdx = Math.floor(
    (new Date().setHours(0, 0, 0, 0) - mondayTs) / (1000 * 60 * 60 * 24),
  );

  const fmtOpts: Intl.DateTimeFormatOptions = { day: "2-digit", month: "short" };
  const weekLabel = `${monday.toLocaleDateString("it-IT", fmtOpts)} — ${sundayEnd.toLocaleDateString("it-IT", fmtOpts)}`;

  // Build per-day per-category data
  const { chartData, totalSessions, totalCompleted, activeCats } = useMemo(() => {
    const data: DayEntry[] = DAY_LABELS.map((label) => ({
      day: label, PT: 0, SALA: 0, CORSO: 0, COLLOQUIO: 0, PERSONALE: 0,
    }));
    let total = 0;
    let completed = 0;
    const catSet = new Set<CategoryKey>();

    for (const event of events) {
      if (event.stato === "Cancellato") continue;
      const dayIndex = Math.floor(
        (event.data_inizio.getTime() - mondayTs) / (1000 * 60 * 60 * 24),
      );
      if (dayIndex < 0 || dayIndex > 6) continue;
      const cat = event.categoria as CategoryKey;
      if (cat in data[dayIndex]) {
        data[dayIndex][cat] += 1;
        catSet.add(cat);
      }
      total += 1;
      if (event.stato === "Completato") completed += 1;
    }

    const active = CATEGORIES.filter((c) => catSet.has(c.key));
    return { chartData: data, totalSessions: total, totalCompleted: completed, activeCats: active };
  }, [events, mondayTs]);

  if (isLoading) return <WeeklyPulseSkeleton />;

  const hasData = totalSessions > 0;

  // Custom XAxis tick: today highlighted + dot
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
        <>
          <ChartContainer config={chartConfig} className="h-[200px] w-full sm:h-[220px]">
            <BarChart data={chartData} maxBarSize={46} barCategoryGap="18%">
              {/* SVG gradient definitions for premium bar fills */}
              <defs>
                {CATEGORIES.map((cat) => (
                  <linearGradient key={cat.key} id={`grad-${cat.key}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={cat.light} stopOpacity={0.85} />
                    <stop offset="100%" stopColor={cat.color} />
                  </linearGradient>
                ))}
              </defs>
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
                content={<WeeklyTooltip activeCats={activeCats} />}
              />
              {activeCats.map((cat, i) => {
                const isFirst = i === 0;
                const isLast = i === activeCats.length - 1;
                const isOnly = activeCats.length === 1;
                return (
                  <Bar
                    key={cat.key}
                    dataKey={cat.key}
                    stackId="week"
                    fill={`url(#grad-${cat.key})`}
                    radius={
                      isOnly
                        ? [4, 4, 4, 4]
                        : isLast
                          ? [4, 4, 0, 0]
                          : isFirst
                            ? [0, 0, 4, 4]
                            : [0, 0, 0, 0]
                    }
                  />
                );
              })}
            </BarChart>
          </ChartContainer>

          {/* Custom legend — only active categories */}
          <div className="mt-1 flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
            {activeCats.map((cat) => (
              <div key={cat.key} className="flex items-center gap-1.5">
                <div
                  className="h-2.5 w-2.5 rounded-full shadow-sm"
                  style={{ background: `linear-gradient(135deg, ${cat.light}, ${cat.color})` }}
                />
                <span className="text-[11px] font-medium text-muted-foreground">{cat.label}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ── Custom Tooltip ──

interface TooltipPayloadItem {
  dataKey: string;
  value: number;
}

function WeeklyTooltip({
  active,
  payload,
  label,
  activeCats,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
  activeCats: CategoryInfo[];
}) {
  if (!active || !payload?.length) return null;

  const items = payload.filter((p) => (p.value ?? 0) > 0);
  if (items.length === 0) return null;

  const total = items.reduce((s, p) => s + p.value, 0);
  const fullDay = FULL_DAY_NAMES[label ?? ""] ?? label;

  return (
    <div className="rounded-lg border bg-background/95 px-3 py-2.5 text-xs shadow-xl backdrop-blur-sm">
      <p className="mb-2 font-semibold">{fullDay}</p>
      <div className="space-y-1.5">
        {items.map((p) => {
          const cat = activeCats.find((c) => c.key === p.dataKey);
          return (
            <div key={p.dataKey} className="flex items-center justify-between gap-6">
              <div className="flex items-center gap-1.5">
                <div
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ background: cat?.color }}
                />
                <span className="text-muted-foreground">{cat?.label ?? p.dataKey}</span>
              </div>
              <span className="font-bold tabular-nums">{p.value}</span>
            </div>
          );
        })}
      </div>
      {items.length > 1 && (
        <div className="mt-2 flex items-center justify-between border-t pt-2 font-bold">
          <span>Totale</span>
          <span className="tabular-nums">{total}</span>
        </div>
      )}
    </div>
  );
}

// ── Skeleton ──

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
      <Skeleton className="h-[200px] w-full rounded-lg sm:h-[220px]" />
    </div>
  );
}
