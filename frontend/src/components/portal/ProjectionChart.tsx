"use client";

/**
 * ProjectionChart — Grafico predittivo con trend EWMA + proiezione futura.
 *
 * Estetica "clinical scan" su sfondo scuro (stessa palette di BodyReportMap).
 * Visualizza: punti raw, linea EWMA, proiezione tratteggiata, cono di confidenza,
 * linea obiettivo, ETA marker, narrativa contestuale.
 */

import { useMemo } from "react";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Crosshair,
  Flag,
  Rocket,
  Target,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  Minus,
} from "lucide-react";

import { ChartContainer } from "@/components/ui/chart";
import { buildTrendProjection } from "@/lib/trend-projection";
import type { TrendProjectionResult, NarrativeKey } from "@/lib/trend-projection";
import type { ClientGoal, Measurement, Metric } from "@/types/api";

// ── Narrative config ──

const NARRATIVE_CONFIG: Record<NarrativeKey, { icon: React.ElementType; color: string; bg: string; border: string }> = {
  on_track:          { icon: Target,        color: "text-teal-300",    bg: "bg-teal-500/10",    border: "border-teal-500/30" },
  ahead_of_schedule: { icon: Rocket,        color: "text-emerald-300", bg: "bg-emerald-500/10", border: "border-emerald-500/30" },
  plateau:           { icon: Minus,          color: "text-amber-300",   bg: "bg-amber-500/10",   border: "border-amber-500/30" },
  wrong_direction:   { icon: AlertTriangle,  color: "text-rose-300",    bg: "bg-rose-500/10",    border: "border-rose-500/30" },
  no_goal:           { icon: Flag,           color: "text-slate-300",   bg: "bg-slate-500/10",   border: "border-slate-500/30" },
  insufficient:      { icon: Crosshair,      color: "text-slate-400",   bg: "bg-slate-500/10",   border: "border-slate-500/30" },
};

// ── Chart data builder ──

interface ChartDatum {
  date: string;
  label: string;
  raw?: number;
  trend?: number;
  projected?: number;
  upper?: number;
  lower?: number;
}

function buildChartData(result: TrendProjectionResult): ChartDatum[] {
  const data: ChartDatum[] = [];

  for (const tp of result.trendPoints) {
    data.push({
      date: tp.date,
      label: format(parseISO(tp.date), "d MMM", { locale: it }),
      raw: tp.raw,
      trend: tp.trend,
    });
  }

  // Bridge: last trend point duplicated as first projection
  if (result.trendPoints.length > 0 && result.projectedPoints.length > 0) {
    const last = result.trendPoints[result.trendPoints.length - 1];
    data[data.length - 1].projected = last.trend;
    data[data.length - 1].upper = last.trend;
    data[data.length - 1].lower = last.trend;
  }

  for (const pp of result.projectedPoints) {
    data.push({
      date: pp.date,
      label: format(parseISO(pp.date), "d MMM", { locale: it }),
      projected: pp.value,
      upper: pp.upper,
      lower: pp.lower,
    });
  }

  return data;
}

// ── Y-axis domain — tight around real data, not blown out by confidence bands ──

function computeYDomain(chartData: ChartDatum[], targetValue: number | null): [number, number] {
  const values: number[] = [];
  for (const d of chartData) {
    if (d.raw !== undefined) values.push(d.raw);
    if (d.trend !== undefined) values.push(d.trend);
    if (d.projected !== undefined) values.push(d.projected);
  }
  if (targetValue !== null) values.push(targetValue);
  if (values.length === 0) return [0, 100];

  const dataMin = Math.min(...values);
  const dataMax = Math.max(...values);
  const range = dataMax - dataMin;
  // Padding: at least 15% of range, minimum 0.5 unit (for cm-scale metrics)
  const pad = Math.max(range * 0.15, 0.5);
  return [Math.floor((dataMin - pad) * 10) / 10, Math.ceil((dataMax + pad) * 10) / 10];
}

// ── Narrative-aware color palette ──

type TrendTone = "positive" | "negative" | "neutral";

function getTrendTone(narrative: NarrativeKey): TrendTone {
  if (narrative === "on_track" || narrative === "ahead_of_schedule") return "positive";
  if (narrative === "wrong_direction") return "negative";
  return "neutral";
}

const TONE_COLORS: Record<TrendTone, { trend: string; projection: string; cone: string; rateText: string }> = {
  positive: { trend: "#34d399", projection: "#6ee7b7", cone: "rgba(52,211,153,0.10)", rateText: "text-emerald-400" },
  negative: { trend: "#fb7185", projection: "#fda4af", cone: "rgba(251,113,133,0.10)", rateText: "text-rose-400" },
  neutral:  { trend: "#94a3b8", projection: "#cbd5e1", cone: "rgba(148,163,184,0.08)", rateText: "text-slate-400" },
};

// ── Custom Tooltip ──

function ChartTooltipContent({ active, payload, label, unit, toneColors }: {
  active?: boolean; payload?: Array<{ dataKey: string; value?: number }>; label?: string;
  unit?: string; toneColors?: { trend: string; projection: string };
}) {
  if (!active || !payload?.length) return null;
  const raw = payload.find(p => p.dataKey === "raw")?.value;
  const trend = payload.find(p => p.dataKey === "trend")?.value;
  const proj = payload.find(p => p.dataKey === "projected")?.value;
  const u = unit ? ` ${unit}` : "";

  return (
    <div className="rounded-lg border border-slate-600 bg-slate-800/95 px-3 py-2 shadow-xl backdrop-blur">
      <p className="mb-1 text-[10px] font-medium text-slate-400">{label}</p>
      {raw !== undefined && (
        <div className="flex items-center gap-1.5 text-xs">
          <div className="h-1.5 w-1.5 rounded-full bg-white/60" />
          <span className="text-slate-300">Misurato:</span>
          <span className="font-bold tabular-nums text-white">{raw}{u}</span>
        </div>
      )}
      {trend !== undefined && (
        <div className="flex items-center gap-1.5 text-xs">
          <div className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: toneColors?.trend ?? "#2dd4bf" }} />
          <span className="text-slate-300">Trend:</span>
          <span className="font-bold tabular-nums" style={{ color: toneColors?.trend ?? "#2dd4bf" }}>{trend}{u}</span>
        </div>
      )}
      {proj !== undefined && (
        <div className="flex items-center gap-1.5 text-xs">
          <div className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: toneColors?.projection ?? "#6ee7b7", opacity: 0.6 }} />
          <span className="text-slate-300">Proiezione:</span>
          <span className="font-bold tabular-nums" style={{ color: toneColors?.projection ?? "#6ee7b7" }}>{proj}{u}</span>
        </div>
      )}
    </div>
  );
}

// ── Props ──

interface ProjectionChartProps {
  measurements: Measurement[];
  metrics: Metric[];
  metricId: number;
  goals?: ClientGoal[];
}

// ── Component ──

export function ProjectionChart({ measurements, metrics, metricId, goals }: ProjectionChartProps) {
  const metric = useMemo(() => metrics.find(m => m.id === metricId), [metrics, metricId]);

  const result = useMemo<TrendProjectionResult | null>(() => {
    if (!metric) return null;
    return buildTrendProjection(measurements, metricId, metric.nome, metric.unita_misura, goals);
  }, [measurements, metricId, metric, goals]);

  if (!result || !metric) return null;

  const chartData = useMemo(() => buildChartData(result), [result]);
  const yDomain = useMemo(() => computeYDomain(chartData, result.targetValue), [chartData, result.targetValue]);
  const narrativeCfg = NARRATIVE_CONFIG[result.narrative];
  const NarrIcon = narrativeCfg.icon;
  const tone = getTrendTone(result.narrative);
  const colors = TONE_COLORS[tone];

  // Rate icon
  const RateIcon = result.weeklyRate === null || Math.abs(result.weeklyRate) < 0.05
    ? Minus : result.weeklyRate < 0 ? TrendingDown : TrendingUp;

  const chartConfig = {
    raw: { label: "Misurato", color: "rgba(255,255,255,0.5)" },
    trend: { label: "Trend", color: colors.trend },
    projected: { label: "Proiezione", color: colors.projection },
  };

  return (
    <div className="rounded-xl bg-gradient-to-b from-[#0f172a] to-[#1e293b] border border-slate-700/50 shadow-xl overflow-hidden animate-in slide-in-from-top-2 fade-in duration-300">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-3 pb-2">
        <div className="flex items-center gap-2">
          <Crosshair className="h-3.5 w-3.5 text-teal-400" />
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
            Proiezione {result.metricName}
          </span>
        </div>
        {result.weeklyRate !== null && (
          <div className="flex items-center gap-1 rounded-full bg-slate-800/80 px-2.5 py-1">
            <RateIcon className={`h-3 w-3 ${colors.rateText}`} />
            <span className={`text-[11px] font-bold tabular-nums ${colors.rateText}`}>
              {result.weeklyRate > 0 ? "+" : ""}{result.weeklyRate} {result.unit}/sett
            </span>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="px-2 pb-2">
        <ChartContainer config={chartConfig} className="h-[200px] sm:h-[240px] w-full">
          <ComposedChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.15)" />
            <XAxis
              dataKey="label" tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false}
              interval={Math.max(0, Math.floor(chartData.length / 6) - 1)}
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} width={40}
              domain={yDomain} allowDataOverflow
            />
            <Tooltip content={<ChartTooltipContent unit={result.unit} toneColors={colors} />} />

            {/* Confidence cone */}
            <Area
              dataKey="upper" stroke="none" fill={colors.cone}
              fillOpacity={1} isAnimationActive={false} dot={false} activeDot={false}
            />
            <Area
              dataKey="lower" stroke="none" fill="#0f172a"
              fillOpacity={1} isAnimationActive={false} dot={false} activeDot={false}
            />

            {/* Target line */}
            {result.targetValue !== null && (
              <ReferenceLine
                y={result.targetValue} stroke="#f472b6" strokeDasharray="6 3" strokeWidth={1.5}
                label={{ value: `Obiettivo: ${result.targetValue}`, fill: "#f472b6", fontSize: 10, position: "insideTopRight" }}
              />
            )}

            {/* ETA vertical marker */}
            {result.etaDate !== null && (
              <ReferenceLine
                x={format(parseISO(result.etaDate), "d MMM", { locale: it })}
                stroke={colors.projection} strokeDasharray="4 4" strokeWidth={1}
              />
            )}

            {/* Projection line (dashed) */}
            <Line
              dataKey="projected" type="monotone" stroke={colors.projection} strokeWidth={2}
              strokeDasharray="8 4" dot={false} isAnimationActive={false} connectNulls={false}
            />

            {/* EWMA trend line (bold) */}
            <Line
              dataKey="trend" type="monotone" stroke={colors.trend} strokeWidth={2.5}
              dot={false} activeDot={{ r: 4, fill: colors.trend, stroke: "#0f172a", strokeWidth: 2 }}
              isAnimationActive={false}
            />

            {/* Raw data points */}
            <Scatter
              dataKey="raw" fill="rgba(255,255,255,0.5)" r={3}
              isAnimationActive={false}
              shape={(props: { cx?: number; cy?: number }) => (
                <circle cx={props.cx} cy={props.cy} r={3} fill="rgba(255,255,255,0.5)" stroke="rgba(255,255,255,0.2)" strokeWidth={1} />
              )}
            />
          </ComposedChart>
        </ChartContainer>
      </div>

      {/* Narrative card */}
      <div className={`mx-3 mb-3 rounded-lg border px-3 py-2.5 ${narrativeCfg.bg} ${narrativeCfg.border}`}>
        <div className="flex items-start gap-2">
          <NarrIcon className={`mt-0.5 h-4 w-4 shrink-0 ${narrativeCfg.color}`} />
          <p className={`text-xs leading-relaxed ${narrativeCfg.color}`}>
            {result.narrativeText}
          </p>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 pb-3">
        <LegendItem color="rgba(255,255,255,0.5)" label="Misurato" dashed={false} />
        <LegendItem color={colors.trend} label="Trend EWMA" dashed={false} />
        <LegendItem color={colors.projection} label="Proiezione" dashed />
        {result.targetValue !== null && <LegendItem color="#f472b6" label="Obiettivo" dashed />}
      </div>
    </div>
  );
}

// ── Legend Item ──

function LegendItem({ color, label, dashed }: { color: string; label: string; dashed: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-4 h-0.5" style={{
        backgroundColor: dashed ? "transparent" : color,
        borderTop: dashed ? `2px dashed ${color}` : "none",
      }} />
      <span className="text-[8px] text-slate-500">{label}</span>
    </div>
  );
}
