// src/components/workouts/PatternRadarChart.tsx
"use client";

/**
 * Radar Chart per la distribuzione dei pattern di movimento.
 *
 * Mostra la copertura dei 7 pattern primari (push_h, pull_h, push_v, pull_v,
 * squat, hinge, core) + carry su un grafico radar, con zona ideale
 * evidenziata e tooltip interattivi.
 *
 * Dati: DemandProfile da demand-aggregation.ts (puro frontend).
 * Fonte: NSCA 2016 cap.17 — distribuzione bilanciata dei pattern.
 */

import { useMemo } from "react";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type {
  DemandProfile,
  PrimaryDimension,
} from "@/lib/demand-aggregation";
import { PRIMARY_DIMENSIONS, DIMENSION_LABELS } from "@/lib/demand-aggregation";

// ════════════════════════════════════════════════════════════
// TIPI
// ════════════════════════════════════════════════════════════

interface PatternRadarChartProps {
  profile: DemandProfile;
  concentrations: Array<{ dimension: PrimaryDimension; percentage: number }>;
}

interface RadarDataPoint {
  pattern: string;
  label: string;
  /** Percentuale 0-100 del volume su questa dimensione */
  value: number;
  /** Serie effettive */
  series: number;
  /** Target bilanciato (100/N) */
  ideal: number;
  /** Dimensione concentrata? */
  concentrated: boolean;
}

// ════════════════════════════════════════════════════════════
// LABEL CORTE PER IL RADAR
// ════════════════════════════════════════════════════════════

const SHORT_LABELS: Record<PrimaryDimension, string> = {
  push_h: "Push H",
  pull_h: "Pull H",
  push_v: "Push V",
  pull_v: "Pull V",
  squat: "Squat",
  hinge: "Hinge",
  core: "Core",
};

// ════════════════════════════════════════════════════════════
// COMPONENTE
// ════════════════════════════════════════════════════════════

export function PatternRadarChart({
  profile,
  concentrations,
}: PatternRadarChartProps) {
  const concentrationSet = useMemo(
    () => new Set(concentrations.map((c) => c.dimension)),
    [concentrations],
  );

  const data = useMemo<RadarDataPoint[]>(() => {
    const idealPct = 100 / PRIMARY_DIMENSIONS.length;
    return PRIMARY_DIMENSIONS.map((dim) => ({
      pattern: dim,
      label: SHORT_LABELS[dim],
      value: Math.round(profile.distribution[dim] * 100),
      series: profile.values[dim],
      ideal: Math.round(idealPct),
      concentrated: concentrationSet.has(dim),
    }));
  }, [profile, concentrationSet]);

  if (profile.totalSeries === 0) return null;

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={240}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid
            stroke="currentColor"
            className="text-border"
            strokeOpacity={0.3}
          />
          <PolarAngleAxis
            dataKey="label"
            tick={({ x, y, payload }) => (
              <CustomAxisTick
                x={x}
                y={y}
                value={payload.value}
                concentrated={
                  concentrationSet.has(
                    data.find((d) => d.label === payload.value)?.pattern as PrimaryDimension,
                  )
                }
              />
            )}
            className="text-[10px]"
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, "auto"]}
            tick={false}
            axisLine={false}
          />

          {/* Zona ideale (distribuzione bilanciata) */}
          <Radar
            name="Ideale"
            dataKey="ideal"
            stroke="hsl(var(--primary))"
            fill="hsl(var(--primary))"
            fillOpacity={0.05}
            strokeWidth={1}
            strokeDasharray="4 4"
            strokeOpacity={0.4}
          />

          {/* Volume reale */}
          <Radar
            name="Volume"
            dataKey="value"
            stroke="hsl(var(--primary))"
            fill="hsl(var(--primary))"
            fillOpacity={0.2}
            strokeWidth={2}
          />

          <Tooltip content={<CustomTooltip />} />
        </RadarChart>
      </ResponsiveContainer>

      {/* Legenda compatta */}
      <div className="flex justify-center gap-4 -mt-2">
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 bg-primary rounded" />
          <span className="text-[10px] text-muted-foreground">Volume attuale</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 border-t border-dashed border-primary/40" />
          <span className="text-[10px] text-muted-foreground">Distribuzione ideale</span>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// AXIS TICK PERSONALIZZATO
// ════════════════════════════════════════════════════════════

function CustomAxisTick({
  x,
  y,
  value,
  concentrated,
}: {
  x: number;
  y: number;
  value: string;
  concentrated: boolean;
}) {
  return (
    <text
      x={x}
      y={y}
      textAnchor="middle"
      dominantBaseline="central"
      className={`text-[10px] ${
        concentrated
          ? "fill-amber-600 dark:fill-amber-400 font-bold"
          : "fill-muted-foreground"
      }`}
    >
      {value}
    </text>
  );
}

// ════════════════════════════════════════════════════════════
// TOOLTIP PERSONALIZZATO
// ════════════════════════════════════════════════════════════

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: RadarDataPoint }>;
}) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;

  return (
    <div className="rounded-md border bg-popover px-3 py-2 shadow-md text-popover-foreground">
      <p className="text-xs font-semibold">
        {DIMENSION_LABELS[d.pattern as PrimaryDimension]}
      </p>
      <div className="flex items-center gap-3 mt-1 text-[11px]">
        <span className="text-muted-foreground">
          {d.series} serie ({d.value}%)
        </span>
        {d.concentrated && (
          <span className="text-amber-600 dark:text-amber-400 font-medium">
            Concentrato
          </span>
        )}
      </div>
      <p className="text-[10px] text-muted-foreground mt-0.5">
        Ideale: ~{d.ideal}%
      </p>
    </div>
  );
}
