// src/components/movements/ForecastTab.tsx
"use client";

/**
 * Forecast Tab — Previsioni di Bilancio.
 *
 * 3 sezioni:
 * 1. KPI predittivi (4 card gradient)
 * 2. AreaChart gradient — proiezione entrate vs uscite (3 mesi)
 * 3. AreaChart runway — saldo cumulativo con zona positiva/negativa
 * 4. Timeline cronologica eventi finanziari futuri
 *
 * Dati: singola chiamata GET /api/movements/forecast via useForecast().
 */

import { useMemo } from "react";
import {
  TrendingUp,
  TrendingDown,
  Flame,
  Target,
  ArrowUpRight,
  ArrowDownRight,
  CalendarDays,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
  ReferenceLine,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart";
import { useForecast } from "@/hooks/useMovements";
import { formatCurrency } from "@/lib/format";
import type { ForecastMonthData, ForecastTimelineItem } from "@/types/api";

// ── Chart configs ──

const projectionConfig: ChartConfig = {
  entrate_certe: {
    label: "Entrate Attese",
    color: "var(--color-emerald-500)",
  },
  uscite_fisse: {
    label: "Uscite Fisse",
    color: "var(--color-red-500)",
  },
  uscite_variabili_stimate: {
    label: "Uscite Variabili (stima)",
    color: "var(--color-orange-400)",
  },
};

const runwayConfig: ChartConfig = {
  saldo: {
    label: "Saldo Proiettato",
    color: "var(--color-blue-500)",
  },
};

// ════════════════════════════════════════════════════════════
// Componente principale
// ════════════════════════════════════════════════════════════

export function ForecastTab() {
  const { data, isLoading, isError } = useForecast(3);

  if (isLoading) return <ForecastSkeleton />;

  if (isError || !data) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
        <p className="text-destructive">
          Errore nel caricamento delle previsioni.
        </p>
      </div>
    );
  }

  const hasProjection = data.monthly_projection.length > 0;
  const hasTimeline = data.timeline.length > 0;

  if (!hasProjection) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-blue-200 bg-blue-50/30 py-16 dark:border-blue-800 dark:bg-blue-950/10">
        <Target className="mb-3 h-10 w-10 text-blue-500" />
        <p className="font-semibold text-blue-700 dark:text-blue-400">
          Nessun dato per le previsioni
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          Crea contratti con rate programmate per vedere le proiezioni
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── KPI Predittivi ── */}
      <ForecastKpiCards kpi={data.kpi} />

      {/* ── Grafico Proiezione Mensile (AreaChart gradient) ── */}
      <ProjectionChart data={data.monthly_projection} />

      {/* ── Grafico Runway (saldo cumulativo) ── */}
      {hasTimeline && (
        <RunwayChart
          timeline={data.timeline}
          saldoIniziale={data.saldo_iniziale}
          months={data.monthly_projection}
        />
      )}

      {/* ── Timeline ── */}
      {hasTimeline && (
        <ForecastTimeline
          items={data.timeline}
          saldoIniziale={data.saldo_iniziale}
        />
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// KPI Cards
// ════════════════════════════════════════════════════════════

interface KpiCardDef {
  key: "entrate_attese_90gg" | "uscite_previste_90gg" | "burn_rate_mensile" | "margine_proiettato_90gg";
  label: string;
  sub: string;
  icon: typeof TrendingUp;
  borderColor: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  valueColor: string;
}

const FORECAST_KPI: KpiCardDef[] = [
  {
    key: "entrate_attese_90gg",
    label: "Entrate Attese",
    sub: "prossimi 90 giorni",
    icon: TrendingUp,
    borderColor: "border-l-emerald-500",
    gradient: "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    valueColor: "text-emerald-700 dark:text-emerald-400",
  },
  {
    key: "uscite_previste_90gg",
    label: "Uscite Previste",
    sub: "prossimi 90 giorni",
    icon: TrendingDown,
    borderColor: "border-l-red-500",
    gradient: "from-red-50/80 to-white dark:from-red-950/40 dark:to-zinc-900",
    iconBg: "bg-red-100 dark:bg-red-900/30",
    iconColor: "text-red-600 dark:text-red-400",
    valueColor: "text-red-700 dark:text-red-400",
  },
  {
    key: "burn_rate_mensile",
    label: "Burn Rate",
    sub: "media uscite/mese",
    icon: Flame,
    borderColor: "border-l-orange-500",
    gradient: "from-orange-50/80 to-white dark:from-orange-950/40 dark:to-zinc-900",
    iconBg: "bg-orange-100 dark:bg-orange-900/30",
    iconColor: "text-orange-600 dark:text-orange-400",
    valueColor: "text-orange-700 dark:text-orange-400",
  },
  {
    key: "margine_proiettato_90gg",
    label: "Margine Proiettato",
    sub: "prossimi 90 giorni",
    icon: Target,
    borderColor: "",
    gradient: "",
    iconBg: "",
    iconColor: "",
    valueColor: "",
  },
];

function ForecastKpiCards({ kpi }: { kpi: ForecastKpiCardData }) {
  const isPositive = kpi.margine_proiettato_90gg >= 0;

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {FORECAST_KPI.map((def) => {
        const Icon = def.icon;
        const isMargin = def.key === "margine_proiettato_90gg";

        const borderColor = isMargin
          ? (isPositive ? "border-l-blue-500" : "border-l-red-500")
          : def.borderColor;
        const gradient = isMargin
          ? (isPositive
              ? "from-blue-50/80 to-white dark:from-blue-950/40 dark:to-zinc-900"
              : "from-red-50/80 to-white dark:from-red-950/40 dark:to-zinc-900")
          : def.gradient;
        const iconBg = isMargin
          ? (isPositive ? "bg-blue-100 dark:bg-blue-900/30" : "bg-red-100 dark:bg-red-900/30")
          : def.iconBg;
        const iconColor = isMargin
          ? (isPositive ? "text-blue-600 dark:text-blue-400" : "text-red-600 dark:text-red-400")
          : def.iconColor;
        const valueColor = isMargin
          ? (isPositive ? "text-blue-700 dark:text-blue-400" : "text-red-700 dark:text-red-400")
          : def.valueColor;

        return (
          <div
            key={def.key}
            className={`flex items-start gap-3 rounded-xl border border-l-4 ${borderColor} bg-gradient-to-br ${gradient} p-4 shadow-sm transition-shadow hover:shadow-md`}
          >
            <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
              <Icon className={`h-5 w-5 ${iconColor}`} />
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
                {def.label}
              </p>
              <p className={`text-2xl font-bold tracking-tight ${valueColor}`}>
                {formatCurrency(kpi[def.key])}
              </p>
              <p className="text-[10px] text-muted-foreground/70">{def.sub}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

type ForecastKpiCardData = {
  entrate_attese_90gg: number;
  uscite_previste_90gg: number;
  burn_rate_mensile: number;
  margine_proiettato_90gg: number;
};

// ════════════════════════════════════════════════════════════
// Projection Chart (AreaChart gradient — 3 mesi)
// ════════════════════════════════════════════════════════════

function ProjectionChart({ data }: { data: ForecastMonthData[] }) {
  return (
    <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-5 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">Proiezione Finanziaria</h3>
          <p className="text-xs text-muted-foreground">
            Entrate attese vs uscite previste per i prossimi mesi
          </p>
        </div>
        <Badge variant="outline" className="text-[10px]">
          {data.length} mesi
        </Badge>
      </div>

      <ChartContainer config={projectionConfig} className="h-[280px] w-full">
        <AreaChart data={data} accessibilityLayer>
          <defs>
            <linearGradient id="fillEntrate" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-emerald-500)" stopOpacity={0.4} />
              <stop offset="95%" stopColor="var(--color-emerald-500)" stopOpacity={0.05} />
            </linearGradient>
            <linearGradient id="fillUsciteFisse" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-red-500)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="var(--color-red-500)" stopOpacity={0.05} />
            </linearGradient>
            <linearGradient id="fillUsciteVar" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-orange-400)" stopOpacity={0.25} />
              <stop offset="95%" stopColor="var(--color-orange-400)" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} strokeDasharray="3 3" />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            fontSize={12}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            fontSize={11}
            tickFormatter={(v) => `€${v}`}
          />
          <ChartTooltip
            content={({ payload, label }) => {
              if (!payload?.length) return null;
              return (
                <div className="rounded-lg border bg-white p-3 shadow-md dark:bg-zinc-900">
                  <p className="mb-1.5 text-xs font-semibold text-muted-foreground">
                    {label}
                  </p>
                  {payload.map((entry) => {
                    const labels: Record<string, string> = {
                      entrate_certe: "Entrate Attese",
                      uscite_fisse: "Uscite Fisse",
                      uscite_variabili_stimate: "Uscite Var. (stima)",
                    };
                    return (
                      <div key={entry.name} className="flex items-center gap-2 text-sm">
                        <div
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-muted-foreground">
                          {labels[entry.name as string] ?? entry.name}
                        </span>
                        <span className="ml-auto font-bold tabular-nums">
                          {formatCurrency(Number(entry.value))}
                        </span>
                      </div>
                    );
                  })}
                </div>
              );
            }}
          />
          <ChartLegend content={<ChartLegendContent />} />
          <Area
            type="monotone"
            dataKey="entrate_certe"
            stroke="var(--color-emerald-500)"
            strokeWidth={2.5}
            fill="url(#fillEntrate)"
            animationBegin={0}
            animationDuration={800}
          />
          <Area
            type="monotone"
            dataKey="uscite_fisse"
            stroke="var(--color-red-500)"
            strokeWidth={2}
            fill="url(#fillUsciteFisse)"
            animationBegin={200}
            animationDuration={800}
          />
          <Area
            type="monotone"
            dataKey="uscite_variabili_stimate"
            stroke="var(--color-orange-400)"
            strokeWidth={2}
            strokeDasharray="6 3"
            fill="url(#fillUsciteVar)"
            animationBegin={400}
            animationDuration={800}
          />
        </AreaChart>
      </ChartContainer>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Runway Chart (saldo cumulativo)
// ════════════════════════════════════════════════════════════

function RunwayChart({
  timeline,
  saldoIniziale,
  months,
}: {
  timeline: ForecastTimelineItem[];
  saldoIniziale: number;
  months: ForecastMonthData[];
}) {
  const runwayData = useMemo(() => {
    // Build data points: start with saldo iniziale, then one point per month
    const points: { label: string; saldo: number }[] = [
      { label: "Oggi", saldo: saldoIniziale },
    ];

    let running = saldoIniziale;
    for (const month of months) {
      running += month.entrate_certe - month.uscite_fisse - month.uscite_variabili_stimate;
      points.push({ label: month.label, saldo: Math.round(running * 100) / 100 });
    }

    return points;
  }, [timeline, saldoIniziale, months]);

  const minSaldo = Math.min(...runwayData.map((d) => d.saldo));
  const maxSaldo = Math.max(...runwayData.map((d) => d.saldo));
  const allPositive = minSaldo >= 0;

  return (
    <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-5 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">Runway — Saldo Proiettato</h3>
          <p className="text-xs text-muted-foreground">
            {allPositive
              ? "Il saldo resta positivo nei prossimi mesi"
              : "Attenzione: il saldo potrebbe andare in negativo"}
          </p>
        </div>
        <Badge
          variant={allPositive ? "outline" : "destructive"}
          className="text-[10px]"
        >
          {allPositive ? "Stabile" : "Rischio"}
        </Badge>
      </div>

      <ChartContainer config={runwayConfig} className="h-[220px] w-full">
        <AreaChart data={runwayData} accessibilityLayer>
          <defs>
            <linearGradient id="fillRunwayPos" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-blue-500)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="var(--color-blue-500)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} strokeDasharray="3 3" />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            fontSize={12}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            fontSize={11}
            tickFormatter={(v) => `€${v}`}
            domain={[Math.min(minSaldo * 1.1, 0), maxSaldo * 1.1]}
          />
          <ReferenceLine
            y={0}
            stroke="var(--color-red-400)"
            strokeDasharray="4 4"
            strokeWidth={1.5}
          />
          <ChartTooltip
            content={({ payload, label }) => {
              if (!payload?.length) return null;
              const val = Number(payload[0].value);
              const isNeg = val < 0;
              return (
                <div className="rounded-lg border bg-white p-3 shadow-md dark:bg-zinc-900">
                  <p className="mb-1 text-xs font-semibold text-muted-foreground">
                    {label}
                  </p>
                  <p className={`text-base font-bold ${isNeg ? "text-red-600" : "text-blue-600"}`}>
                    {formatCurrency(val)}
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    Saldo proiettato
                  </p>
                </div>
              );
            }}
          />
          <Area
            type="monotone"
            dataKey="saldo"
            stroke="var(--color-blue-500)"
            strokeWidth={2.5}
            fill="url(#fillRunwayPos)"
            dot={{ r: 4, fill: "var(--color-blue-500)", strokeWidth: 2, stroke: "white" }}
            animationBegin={0}
            animationDuration={1000}
          />
        </AreaChart>
      </ChartContainer>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Timeline
// ════════════════════════════════════════════════════════════

function ForecastTimeline({
  items,
  saldoIniziale,
}: {
  items: ForecastTimelineItem[];
  saldoIniziale: number;
}) {
  return (
    <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-5 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CalendarDays className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">Cash Flow Timeline</h3>
        </div>
        <Badge variant="outline" className="text-[10px]">
          {items.length} eventi
        </Badge>
      </div>

      <div className="mb-3 flex items-center gap-2 rounded-lg bg-muted/40 px-3 py-2">
        <span className="text-xs text-muted-foreground">Saldo attuale:</span>
        <span className={`text-sm font-bold tabular-nums ${saldoIniziale >= 0 ? "text-blue-600" : "text-red-600"}`}>
          {formatCurrency(saldoIniziale)}
        </span>
      </div>

      <Separator className="mb-3" />

      <ScrollArea className="h-[320px]">
        <div className="space-y-0">
          {items.map((item, idx) => (
            <TimelineRow key={`${item.data}-${item.descrizione}-${idx}`} item={item} />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

function TimelineRow({ item }: { item: ForecastTimelineItem }) {
  const isEntrata = item.tipo === "ENTRATA";
  const saldoPositive = item.saldo_cumulativo >= 0;

  return (
    <div className="flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-muted/30">
      {/* Dot + line */}
      <div className="flex flex-col items-center">
        <div
          className={`h-2.5 w-2.5 rounded-full ${
            isEntrata ? "bg-emerald-500" : "bg-red-500"
          }`}
        />
      </div>

      {/* Date */}
      <span className="w-20 shrink-0 text-xs tabular-nums text-muted-foreground">
        {new Date(item.data + "T00:00:00").toLocaleDateString("it-IT", {
          day: "2-digit",
          month: "short",
        })}
      </span>

      {/* Description */}
      <span className="min-w-0 flex-1 truncate text-sm">{item.descrizione}</span>

      {/* Amount */}
      <div className="flex items-center gap-1 shrink-0">
        {isEntrata ? (
          <ArrowUpRight className="h-3.5 w-3.5 text-emerald-500" />
        ) : (
          <ArrowDownRight className="h-3.5 w-3.5 text-red-500" />
        )}
        <span
          className={`text-sm font-semibold tabular-nums ${
            isEntrata ? "text-emerald-600" : "text-red-600"
          }`}
        >
          {isEntrata ? "+" : "-"}{formatCurrency(item.importo)}
        </span>
      </div>

      {/* Running balance */}
      <span
        className={`w-24 shrink-0 text-right text-xs font-medium tabular-nums ${
          saldoPositive ? "text-blue-600" : "text-red-600"
        }`}
      >
        {formatCurrency(item.saldo_cumulativo)}
      </span>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Skeleton
// ════════════════════════════════════════════════════════════

function ForecastSkeleton() {
  const borders = ["border-l-emerald-500", "border-l-red-500", "border-l-orange-500", "border-l-blue-500"];
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {borders.map((border, i) => (
          <div key={i} className={`flex items-start gap-3 rounded-xl border border-l-4 ${border} p-4`}>
            <Skeleton className="h-10 w-10 shrink-0 rounded-lg" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-6 w-28" />
              <Skeleton className="h-2 w-16" />
            </div>
          </div>
        ))}
      </div>
      <Skeleton className="h-[280px] w-full rounded-xl" />
      <Skeleton className="h-[220px] w-full rounded-xl" />
    </div>
  );
}
