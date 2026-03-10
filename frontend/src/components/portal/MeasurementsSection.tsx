"use client";

/**
 * MeasurementsSection — Sezione Misurazioni del Portale Cliente.
 *
 * Contiene: KPI dinamici, chart trend, body map interattiva, confronto sessioni,
 * storico misurazioni con edit/delete. CTA "Nuova Misurazione".
 */

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  ChevronDown,
  Plus,
  Ruler,
  Scale,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

import { MeasurementChart } from "@/components/clients/MeasurementChart";
import { SessionComparison } from "@/components/clients/SessionComparison";
import { MeasurementHistoryTable } from "@/components/portal/MeasurementHistoryTable";

import { computeWeeklyRate, formatRate } from "@/lib/measurement-analytics";
import { classifyValue, computeAge, BAND_COLOR_CLASSES } from "@/lib/normative-ranges";
import type { ClinicalFreshnessSignal, Measurement, Metric } from "@/types/api";

// ── Constants ──

const PRIORITY_METRIC_IDS = [1, 3, 5]; // Peso, Massa Grassa, BMI
const LOWER_IS_BETTER = new Set([1, 3, 5, 9, 10]);

const KPI_BORDER_COLORS = [
  "border-l-teal-500",
  "border-l-amber-500",
  "border-l-violet-500",
  "border-l-blue-500",
];

interface MeasurementsSectionProps {
  measurements: Measurement[];
  metrics: Metric[];
  sesso: string | null;
  dataNascita: string | null;
  clientId: number;
  measurementFreshness: ClinicalFreshnessSignal | null;
}

function computeDeltaInfo(
  measurements: Measurement[],
  metricId: number,
): { value: string; positive: boolean } | null {
  if (measurements.length < 2) return null;
  const latest = measurements[0].valori.find((v) => v.id_metrica === metricId);
  const prev = measurements[1].valori.find((v) => v.id_metrica === metricId);
  if (!latest || !prev) return null;
  const diff = latest.valore - prev.valore;
  if (diff === 0) return null;
  const sign = diff > 0 ? "+" : "";
  const positive = LOWER_IS_BETTER.has(metricId) ? diff < 0 : diff > 0;
  return { value: `${sign}${diff.toFixed(1)}`, positive };
}

export function MeasurementsSection({
  measurements,
  metrics,
  sesso,
  dataNascita,
  clientId,
  measurementFreshness,
}: MeasurementsSectionProps) {
  const router = useRouter();
  const [open, setOpen] = useState(true);

  const metricMap = useMemo(
    () => new Map(metrics.map((m) => [m.id, m])),
    [metrics],
  );

  const trackedMetricIds = useMemo(() => {
    const ids = new Set<number>();
    for (const m of measurements) {
      for (const v of m.valori) ids.add(v.id_metrica);
    }
    return ids;
  }, [measurements]);

  // Top 2 metriche prioritarie tracciate
  const kpiMetrics = useMemo(() => {
    const kpis: Metric[] = [];
    for (const id of PRIORITY_METRIC_IDS) {
      if (trackedMetricIds.has(id)) {
        const m = metricMap.get(id);
        if (m) kpis.push(m);
      }
    }
    if (kpis.length < 2) {
      const usedIds = new Set(kpis.map((m) => m.id));
      const counts = new Map<number, number>();
      for (const m of measurements) {
        for (const v of m.valori) {
          if (!usedIds.has(v.id_metrica)) {
            counts.set(v.id_metrica, (counts.get(v.id_metrica) ?? 0) + 1);
          }
        }
      }
      for (const [id] of [...counts.entries()].sort((a, b) => b[1] - a[1])) {
        if (kpis.length >= 2) break;
        const m = metricMap.get(id);
        if (m) kpis.push(m);
      }
    }
    return kpis;
  }, [trackedMetricIds, metricMap, measurements]);

  const age = computeAge(dataNascita);
  const hasMeasurements = measurements.length > 0;

  // Freshness badge
  const fStatus = measurementFreshness?.status;
  const freshnessColor = fStatus === "critical" ? "destructive"
    : fStatus === "warning" ? "secondary" : undefined;
  const freshnessLabel = fStatus === "critical" ? "Scaduta"
    : fStatus === "warning" ? "In scadenza" : null;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card>
        <CollapsibleTrigger asChild>
          <CardContent className="flex cursor-pointer items-center gap-3 py-4 hover:bg-muted/30 transition-colors">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-950/40">
              <Ruler className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold">Misurazioni</h3>
                <Badge variant="outline" className="text-[10px]">
                  {measurements.length} {measurements.length === 1 ? "sessione" : "sessioni"}
                </Badge>
                {freshnessLabel && (
                  <Badge variant={freshnessColor} className="text-[10px]">
                    {freshnessLabel}
                  </Badge>
                )}
              </div>
            </div>
            <Button
              variant="default"
              size="sm"
              className="shrink-0"
              onClick={(e) => { e.stopPropagation(); router.push(`/clienti/${clientId}/misurazioni`); }}
            >
              <Plus className="mr-1 h-3.5 w-3.5" />
              Nuova Misurazione
            </Button>
            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
          </CardContent>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="space-y-6 pt-0">
            {!hasMeasurements ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <div className="rounded-full bg-indigo-50 p-4 dark:bg-indigo-950/30">
                  <Scale className="h-8 w-8 text-indigo-400" />
                </div>
                <p className="mt-3 text-sm text-muted-foreground">
                  Nessuna misurazione registrata. Registra la prima per iniziare il tracking.
                </p>
              </div>
            ) : (
              <>
                {/* KPI dinamici */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {kpiMetrics.map((metric, idx) => {
                    const latest = measurements[0]?.valori.find((v) => v.id_metrica === metric.id);
                    const delta = computeDeltaInfo(measurements, metric.id);
                    const rate = computeWeeklyRate(measurements, metric.id);
                    const normClass = latest ? classifyValue(metric.id, latest.valore, sesso, age) : null;
                    return (
                      <Card key={metric.id} className={`border-l-4 ${KPI_BORDER_COLORS[idx % KPI_BORDER_COLORS.length]} bg-gradient-to-br from-background to-muted/30`}>
                        <CardContent className="p-3">
                          <span className="text-[10px] font-medium text-muted-foreground">{metric.nome}</span>
                          <div className="mt-1 flex items-baseline gap-1.5">
                            <span className="text-xl font-extrabold tracking-tighter tabular-nums">
                              {latest ? `${latest.valore} ${metric.unita_misura}` : "—"}
                            </span>
                            {delta && (
                              <span className={`flex items-center text-[10px] font-medium ${delta.positive ? "text-emerald-600" : "text-red-500"}`}>
                                {delta.positive ? <TrendingDown className="mr-0.5 h-3 w-3" /> : <TrendingUp className="mr-0.5 h-3 w-3" />}
                                {delta.value}
                              </span>
                            )}
                          </div>
                          {rate !== null && (
                            <p className="text-[9px] font-medium tabular-nums text-muted-foreground">{formatRate(rate, metric.unita_misura)}</p>
                          )}
                          {normClass && (
                            <span className={`mt-0.5 inline-block rounded-full px-1.5 py-0.5 text-[8px] font-semibold ${BAND_COLOR_CLASSES[normClass.color]?.bg ?? ""} ${BAND_COLOR_CLASSES[normClass.color]?.text ?? ""}`}>
                              {normClass.label}
                            </span>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                  {/* Ultima misurazione */}
                  <Card className="border-l-4 border-l-blue-500 bg-gradient-to-br from-background to-muted/30">
                    <CardContent className="p-3">
                      <span className="text-[10px] font-medium text-muted-foreground">Ultima Misurazione</span>
                      <div className="mt-1">
                        <span className="text-xl font-extrabold tracking-tighter tabular-nums">
                          {format(parseISO(measurements[0].data_misurazione), "d MMM yyyy", { locale: it })}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                  {/* Sessioni totali */}
                  <Card className="border-l-4 border-l-emerald-500 bg-gradient-to-br from-background to-muted/30">
                    <CardContent className="p-3">
                      <span className="text-[10px] font-medium text-muted-foreground">Sessioni Totali</span>
                      <div className="mt-1">
                        <span className="text-xl font-extrabold tracking-tighter tabular-nums">{measurements.length}</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Chart trend */}
                <MeasurementChart measurements={measurements} metrics={metrics} sesso={sesso} dataNascita={dataNascita} />

                {/* Confronto sessioni */}
                <SessionComparison measurements={measurements} metrics={metrics} />

                {/* Storico */}
                <div>
                  <h4 className="mb-3 text-sm font-semibold">Storico Misurazioni</h4>
                  <MeasurementHistoryTable measurements={measurements} metricMap={metricMap} clientId={clientId} />
                </div>
              </>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
