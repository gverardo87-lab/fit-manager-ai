"use client";

/**
 * ProgressiCharts — Grafici per la sezione Progressi del Portale Cliente.
 *
 * 1. RateAssessmentChart: barre orizzontali velocità di cambiamento per metrica
 * 2. CompositionTrendChart: area chart FM vs LBM nel tempo
 */

import { useMemo } from "react";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { RateAssessment, Severity } from "@/lib/clinical-analysis";
import type { Measurement } from "@/types/api";

// ── Constants ──

const SEVERITY_COLORS: Record<Severity, string> = {
  positive: "#10b981", // emerald-500
  neutral: "#a1a1aa",  // zinc-400
  info: "#3b82f6",     // blue-500
  warning: "#f59e0b",  // amber-500
  alert: "#ef4444",    // red-500
};

const ID_PESO = 1;
const ID_GRASSO_PCT = 3;

// ── Rate Assessment Chart ──

interface RateChartProps {
  rateAssessments: RateAssessment[];
}

export function RateAssessmentChart({ rateAssessments }: RateChartProps) {
  const data = useMemo(
    () =>
      rateAssessments.map((r) => ({
        name: r.metricLabel,
        rate: Math.round(r.rate * 100) / 100,
        absRate: Math.round(Math.abs(r.rate) * 100) / 100,
        severity: r.severity,
        unit: r.unit,
        assessment: r.assessment,
        guideline: r.guideline,
        pctBodyWeight: r.pctBodyWeight,
      })),
    [rateAssessments],
  );

  if (data.length === 0) return null;

  return (
    <div>
      <p className="mb-2 text-xs font-semibold text-muted-foreground">
        Velocità di Cambiamento (per settimana)
      </p>
      <ResponsiveContainer width="100%" height={data.length * 56 + 20}>
        <BarChart data={data} layout="vertical" margin={{ left: 0, right: 12, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} opacity={0.3} />
          <XAxis type="number" tick={{ fontSize: 10 }} />
          <YAxis
            type="category"
            dataKey="name"
            width={85}
            tick={{ fontSize: 11, fontWeight: 500 }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.[0]) return null;
              const d = payload[0].payload;
              return (
                <div className="rounded-lg border bg-white px-3 py-2 shadow-md dark:bg-zinc-900">
                  <p className="text-xs font-semibold">{d.name}</p>
                  <p className="text-sm tabular-nums">
                    {d.rate > 0 ? "+" : ""}{d.rate} {d.unit}/sett
                    {d.pctBodyWeight != null && (
                      <span className="ml-1 text-muted-foreground">
                        ({d.pctBodyWeight}% peso)
                      </span>
                    )}
                  </p>
                  <p className="mt-0.5 text-[10px] text-muted-foreground">{d.assessment}</p>
                  <p className="text-[9px] italic text-muted-foreground/70">{d.guideline}</p>
                </div>
              );
            }}
          />
          <Bar dataKey="rate" radius={[0, 4, 4, 0]} barSize={20}>
            {data.map((entry, idx) => (
              <Cell key={idx} fill={SEVERITY_COLORS[entry.severity]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Composition Trend Chart (FM vs LBM nel tempo) ──

interface CompositionTrendProps {
  measurements: Measurement[];
}

interface TrendPoint {
  date: string;
  label: string;
  fm: number;
  lbm: number;
  peso: number;
}

export function CompositionTrendChart({ measurements }: CompositionTrendProps) {
  const trendData = useMemo(() => {
    const points: TrendPoint[] = [];
    const sorted = [...measurements].sort((a, b) =>
      a.data_misurazione.localeCompare(b.data_misurazione),
    );

    for (const m of sorted) {
      const peso = m.valori.find((v) => v.id_metrica === ID_PESO);
      const grasso = m.valori.find((v) => v.id_metrica === ID_GRASSO_PCT);
      if (!peso || !grasso) continue;

      const fm = Math.round(peso.valore * (grasso.valore / 100) * 10) / 10;
      const lbm = Math.round((peso.valore - fm) * 10) / 10;

      points.push({
        date: m.data_misurazione,
        label: format(parseISO(m.data_misurazione), "d MMM", { locale: it }),
        fm,
        lbm,
        peso: peso.valore,
      });
    }

    return points;
  }, [measurements]);

  if (trendData.length < 2) return null;

  return (
    <div>
      <p className="mb-2 text-xs font-semibold text-muted-foreground">
        Composizione Corporea nel Tempo
      </p>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={trendData} margin={{ left: 0, right: 12, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis dataKey="label" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} unit=" kg" width={50} />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0]?.payload as TrendPoint;
              return (
                <div className="rounded-lg border bg-white px-3 py-2 shadow-md dark:bg-zinc-900">
                  <p className="text-xs font-semibold">
                    {format(parseISO(d.date), "d MMMM yyyy", { locale: it })}
                  </p>
                  <div className="mt-1 space-y-0.5 text-xs tabular-nums">
                    <p>
                      <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 mr-1" />
                      Massa Magra: <strong>{d.lbm} kg</strong>
                    </p>
                    <p>
                      <span className="inline-block h-2 w-2 rounded-full bg-amber-500 mr-1" />
                      Massa Grassa: <strong>{d.fm} kg</strong>
                    </p>
                    <p className="text-muted-foreground">Peso totale: {d.peso} kg</p>
                  </div>
                </div>
              );
            }}
          />
          <Area
            type="monotone"
            dataKey="lbm"
            stackId="comp"
            stroke="#10b981"
            fill="#10b981"
            fillOpacity={0.3}
            name="Massa Magra"
          />
          <Area
            type="monotone"
            dataKey="fm"
            stackId="comp"
            stroke="#f59e0b"
            fill="#f59e0b"
            fillOpacity={0.3}
            name="Massa Grassa"
          />
        </AreaChart>
      </ResponsiveContainer>
      <div className="mt-1 flex items-center justify-center gap-4 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
          Massa Magra (LBM)
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full bg-amber-500" />
          Massa Grassa (FM)
        </span>
      </div>
    </div>
  );
}
