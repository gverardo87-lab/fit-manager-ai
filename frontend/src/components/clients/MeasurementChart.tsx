// src/components/clients/MeasurementChart.tsx
"use client";

/**
 * MeasurementChart — LineChart con recharts per visualizzare trend metriche.
 *
 * Select per scegliere la metrica da visualizzare.
 * Gradient fill sotto la linea. Custom tooltip.
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
// TYPES
// ════════════════════════════════════════════════════════════

interface MeasurementChartProps {
  measurements: Measurement[];
  metrics: Metric[];
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function MeasurementChart({
  measurements,
  metrics,
}: MeasurementChartProps) {
  // Default: prima metrica con dati (peso = id 1 se disponibile)
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

  const [selectedMetricId, setSelectedMetricId] = useState<string>(() => {
    // Default: Peso Corporeo (id=1) se disponibile, altrimenti primo disponibile
    if (availableMetricIds.has(1)) return "1";
    const first = availableMetrics[0];
    return first ? String(first.id) : "1";
  });

  const selectedMetric = metrics.find(
    (m) => m.id === parseInt(selectedMetricId, 10)
  );

  // Build chart data — ordine cronologico (ASC)
  const chartData = useMemo(() => {
    const metricId = parseInt(selectedMetricId, 10);
    return measurements
      .slice()
      .sort((a, b) => a.data_misurazione.localeCompare(b.data_misurazione))
      .map((m) => {
        const val = m.valori.find((v) => v.id_metrica === metricId);
        return val
          ? {
              date: m.data_misurazione,
              label: format(parseISO(m.data_misurazione), "d MMM", {
                locale: it,
              }),
              valore: val.valore,
            }
          : null;
      })
      .filter(Boolean) as { date: string; label: string; valore: number }[];
  }, [measurements, selectedMetricId]);

  const chartConfig: ChartConfig = {
    valore: {
      label: selectedMetric?.nome ?? "Valore",
      color: "oklch(0.55 0.15 170)",
    },
  };

  if (availableMetrics.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Trend</h3>
        <Select value={selectedMetricId} onValueChange={setSelectedMetricId}>
          <SelectTrigger className="w-48">
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
      </div>

      {chartData.length < 2 ? (
        <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
          Servono almeno 2 misurazioni per visualizzare il trend
        </div>
      ) : (
        <ChartContainer config={chartConfig} className="h-[200px] sm:h-[280px] w-full">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="gradientTeal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="oklch(0.55 0.15 170)" stopOpacity={0.3} />
                <stop offset="100%" stopColor="oklch(0.55 0.15 170)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} />
            <YAxis
              tick={{ fontSize: 12 }}
              domain={["auto", "auto"]}
              unit={selectedMetric ? ` ${selectedMetric.unita_misura}` : ""}
            />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  formatter={(value) =>
                    `${value} ${selectedMetric?.unita_misura ?? ""}`
                  }
                />
              }
            />
            <Area
              type="monotone"
              dataKey="valore"
              stroke="oklch(0.55 0.15 170)"
              strokeWidth={2}
              fill="url(#gradientTeal)"
              dot={{ r: 4, fill: "oklch(0.55 0.15 170)" }}
              activeDot={{ r: 6 }}
            />
          </AreaChart>
        </ChartContainer>
      )}
    </div>
  );
}
