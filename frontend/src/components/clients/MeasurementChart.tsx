// src/components/clients/MeasurementChart.tsx
"use client";

/**
 * MeasurementChart — AreaChart con recharts per visualizzare trend metriche.
 *
 * Supporta 2 metriche simultanee con dual Y-axis:
 * - Metrica primaria (teal, Y-axis sinistra)
 * - Metrica secondaria opzionale (violet, Y-axis destra)
 *
 * Gradient fill sotto ogni linea. Custom tooltip.
 */

import { useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";

import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import type { Measurement, Metric } from "@/types/api";

// ════════════════════════════════════════════════════════════
// COLORS
// ════════════════════════════════════════════════════════════

const COLOR_PRIMARY = "oklch(0.55 0.15 170)";   // teal
const COLOR_SECONDARY = "oklch(0.55 0.15 295)"; // violet

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

interface MeasurementChartProps {
  measurements: Measurement[];
  metrics: Metric[];
}

interface ChartDatum {
  date: string;
  label: string;
  valore1?: number;
  valore2?: number;
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

const NONE_VALUE = "__none__";

export function MeasurementChart({
  measurements,
  metrics,
}: MeasurementChartProps) {
  // Metriche disponibili (con almeno 1 dato)
  const availableMetricIds = useMemo(() => {
    const ids = new Set<number>();
    for (const m of measurements) {
      for (const v of m.valori) {
        ids.add(v.id_metrica);
      }
    }
    return ids;
  }, [measurements]);

  const availableMetrics = useMemo(
    () => metrics.filter((m) => availableMetricIds.has(m.id)),
    [metrics, availableMetricIds]
  );

  // Metric 1: default Peso (id=1) se disponibile
  const [metric1Id, setMetric1Id] = useState<string>(() => {
    if (availableMetricIds.has(1)) return "1";
    const first = availableMetrics[0];
    return first ? String(first.id) : "1";
  });

  // Metric 2: opzionale (default: nessuna)
  const [metric2Id, setMetric2Id] = useState<string>(NONE_VALUE);

  const metric1 = metrics.find((m) => m.id === parseInt(metric1Id, 10));
  const metric2 =
    metric2Id !== NONE_VALUE
      ? metrics.find((m) => m.id === parseInt(metric2Id, 10))
      : null;

  const isDual = metric2 !== null;

  // Build chart data — ordine cronologico (ASC)
  const chartData = useMemo(() => {
    const id1 = parseInt(metric1Id, 10);
    const id2 = metric2Id !== NONE_VALUE ? parseInt(metric2Id, 10) : null;

    return measurements
      .slice()
      .sort((a, b) => a.data_misurazione.localeCompare(b.data_misurazione))
      .map((m) => {
        const v1 = m.valori.find((v) => v.id_metrica === id1);
        const v2 = id2 !== null ? m.valori.find((v) => v.id_metrica === id2) : null;

        // Includi solo se almeno una delle due metriche ha valore
        if (!v1 && !v2) return null;

        const datum: ChartDatum = {
          date: m.data_misurazione,
          label: format(parseISO(m.data_misurazione), "d MMM", { locale: it }),
        };
        if (v1) datum.valore1 = v1.valore;
        if (v2) datum.valore2 = v2.valore;
        return datum;
      })
      .filter(Boolean) as ChartDatum[];
  }, [measurements, metric1Id, metric2Id]);

  // Chart config
  const chartConfig: ChartConfig = {
    valore1: {
      label: metric1?.nome ?? "Metrica 1",
      color: COLOR_PRIMARY,
    },
    ...(isDual
      ? {
          valore2: {
            label: metric2?.nome ?? "Metrica 2",
            color: COLOR_SECONDARY,
          },
        }
      : {}),
  };

  if (availableMetrics.length === 0) return null;

  // Metriche selezionabili per il secondo select (esclusa la prima)
  const secondaryOptions = availableMetrics.filter(
    (m) => String(m.id) !== metric1Id
  );

  return (
    <div className="space-y-3">
      {/* Header con selettori */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">Trend</h3>
        <div className="flex items-center gap-2">
          <Select value={metric1Id} onValueChange={setMetric1Id}>
            <SelectTrigger className="w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {availableMetrics.map((m) => (
                <SelectItem key={m.id} value={String(m.id)}>
                  {m.nome} ({m.unita_misura})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {secondaryOptions.length > 0 && (
            <Select value={metric2Id} onValueChange={setMetric2Id}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="Confronta con..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE_VALUE}>Nessuna</SelectItem>
                {secondaryOptions.map((m) => (
                  <SelectItem key={m.id} value={String(m.id)}>
                    {m.nome} ({m.unita_misura})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>
      </div>

      {/* Legenda colori (solo dual) */}
      {isDual && (
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COLOR_PRIMARY }} />
            {metric1?.nome}
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COLOR_SECONDARY }} />
            {metric2?.nome}
          </div>
        </div>
      )}

      {chartData.length < 2 ? (
        <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
          Servono almeno 2 misurazioni per visualizzare il trend
        </div>
      ) : (
        <ChartContainer config={chartConfig} className="h-[200px] sm:h-[280px] w-full">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="gradientTeal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={COLOR_PRIMARY} stopOpacity={0.3} />
                <stop offset="100%" stopColor={COLOR_PRIMARY} stopOpacity={0} />
              </linearGradient>
              {isDual && (
                <linearGradient id="gradientViolet" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={COLOR_SECONDARY} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={COLOR_SECONDARY} stopOpacity={0} />
                </linearGradient>
              )}
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} />

            {/* Y-axis sinistro (metrica primaria) */}
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 12 }}
              domain={["auto", "auto"]}
              unit={metric1 ? ` ${metric1.unita_misura}` : ""}
            />

            {/* Y-axis destro (metrica secondaria — solo dual mode) */}
            {isDual && (
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 12 }}
                domain={["auto", "auto"]}
                unit={metric2 ? ` ${metric2.unita_misura}` : ""}
              />
            )}

            <ChartTooltip
              content={
                <ChartTooltipContent
                  formatter={(value, name) => {
                    const unit =
                      name === "valore1"
                        ? metric1?.unita_misura ?? ""
                        : metric2?.unita_misura ?? "";
                    return `${value} ${unit}`;
                  }}
                />
              }
            />

            {/* Area primaria */}
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="valore1"
              stroke={COLOR_PRIMARY}
              strokeWidth={2}
              fill="url(#gradientTeal)"
              dot={{ r: 4, fill: COLOR_PRIMARY }}
              activeDot={{ r: 6 }}
              connectNulls
            />

            {/* Area secondaria (solo dual mode) */}
            {isDual && (
              <Area
                yAxisId="right"
                type="monotone"
                dataKey="valore2"
                stroke={COLOR_SECONDARY}
                strokeWidth={2}
                fill="url(#gradientViolet)"
                dot={{ r: 4, fill: COLOR_SECONDARY }}
                activeDot={{ r: 6 }}
                connectNulls
              />
            )}
          </AreaChart>
        </ChartContainer>
      )}
    </div>
  );
}
