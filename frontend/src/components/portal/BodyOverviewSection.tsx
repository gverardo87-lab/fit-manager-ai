"use client";

/**
 * BodyOverviewSection — Hero section del Portale Cliente.
 *
 * MuscleMap interattiva prominente + KPI metriche chiave (peso, grasso%, BMI).
 * Prima cosa che vede la cliente aprendo il portale: "come sto?"
 */

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ChevronDown,
  Plus,
  Printer,
  Scale,
  TrendingDown,
  TrendingUp,
  User,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

import { BodyReportMap } from "@/components/portal/BodyReportMap";

import { formatRate } from "@/lib/measurement-analytics";
import type { ClientGoal, ClinicalFreshnessSignal, Measurement, Metric } from "@/types/api";

// ── Constants ──

const ID_PESO = 1;
const ID_GRASSO_PCT = 3;
const ID_BMI = 5;

const LOWER_IS_BETTER = new Set([ID_PESO, ID_GRASSO_PCT, ID_BMI]);

interface BodyOverviewSectionProps {
  measurements: Measurement[];
  metrics: Metric[];
  goals?: ClientGoal[];
  sesso: string | null;
  dataNascita: string | null;
  clientId: number;
  measurementFreshness: ClinicalFreshnessSignal | null;
  pesoAttuale: number | null;
  pesoRate: number | null;
  grassoPct: number | null;
  grassoClassifica: string | null;
  bmiValue: number | null;
  bmiClassifica: string | null;
}

function getLatestDelta(
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

export function BodyOverviewSection({
  measurements,
  metrics,
  goals,
  sesso,
  dataNascita,
  clientId,
  measurementFreshness,
  pesoAttuale,
  pesoRate,
  grassoPct,
  grassoClassifica,
  bmiValue,
  bmiClassifica,
}: BodyOverviewSectionProps) {
  const router = useRouter();
  const [open, setOpen] = useState(true);

  const hasMeasurements = measurements.length > 0;

  const pesoDelta = useMemo(() => getLatestDelta(measurements, ID_PESO), [measurements]);
  const grassoDelta = useMemo(() => getLatestDelta(measurements, ID_GRASSO_PCT), [measurements]);

  const pesoUnit = useMemo(() => {
    const m = metrics.find((mt) => mt.id === ID_PESO);
    return m?.unita_misura ?? "kg";
  }, [metrics]);

  // Freshness
  const fStatus = measurementFreshness?.status;
  const freshnessLabel = fStatus === "critical" ? "Dati scaduti"
    : fStatus === "warning" ? "Aggiornamento consigliato" : null;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card>
        <CollapsibleTrigger asChild>
          <CardContent className="flex cursor-pointer items-center gap-3 py-4 hover:bg-muted/30 transition-colors">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-100 dark:bg-violet-950/40">
              <User className="h-5 w-5 text-violet-600 dark:text-violet-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold">Panoramica Corpo</h3>
                {hasMeasurements && (
                  <Badge variant="outline" className="text-[10px]">
                    {measurements.length} {measurements.length === 1 ? "sessione" : "sessioni"}
                  </Badge>
                )}
                {freshnessLabel && (
                  <Badge variant={fStatus === "critical" ? "destructive" : "secondary"} className="text-[10px]">
                    {freshnessLabel}
                  </Badge>
                )}
              </div>
            </div>
            {hasMeasurements && (
              <Button
                variant="outline"
                size="sm"
                className="shrink-0 print:hidden"
                onClick={(e) => { e.stopPropagation(); window.print(); }}
              >
                <Printer className="mr-1 h-3.5 w-3.5" />
                <span className="hidden sm:inline">Stampa Referto</span>
              </Button>
            )}
            <Button
              variant="default"
              size="sm"
              className="shrink-0 print:hidden"
              onClick={(e) => { e.stopPropagation(); router.push(`/clienti/${clientId}/misurazioni`); }}
            >
              <Plus className="mr-1 h-3.5 w-3.5" />
              <span className="hidden sm:inline">Nuova Misurazione</span>
            </Button>
            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
          </CardContent>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="space-y-5 pt-0">
            {!hasMeasurements ? (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <div className="rounded-full bg-violet-50 p-4 dark:bg-violet-950/30">
                  <Scale className="h-8 w-8 text-violet-400" />
                </div>
                <p className="mt-3 text-sm text-muted-foreground">
                  Nessuna misurazione registrata. Registra la prima per vedere la panoramica del corpo.
                </p>
                <Button
                  size="sm"
                  className="mt-4"
                  onClick={() => router.push(`/clienti/${clientId}/misurazioni`)}
                >
                  <Plus className="mr-1 h-3.5 w-3.5" />
                  Prima Misurazione
                </Button>
              </div>
            ) : (
              <>
                {/* KPI metriche chiave */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {/* Peso */}
                  <KpiCard
                    label="Peso"
                    value={pesoAttuale !== null ? `${pesoAttuale} ${pesoUnit}` : null}
                    delta={pesoDelta}
                    rate={pesoRate}
                    rateUnit={pesoUnit}
                    classifica={null}
                    borderColor="border-l-teal-500"
                  />
                  {/* Massa Grassa */}
                  <KpiCard
                    label="Massa Grassa"
                    value={grassoPct !== null ? `${grassoPct}%` : null}
                    delta={grassoDelta}
                    rate={null}
                    rateUnit="%"
                    classifica={grassoClassifica}
                    borderColor="border-l-amber-500"
                  />
                  {/* BMI */}
                  <KpiCard
                    label="BMI"
                    value={bmiValue !== null ? `${bmiValue}` : null}
                    delta={null}
                    rate={null}
                    rateUnit=""
                    classifica={bmiClassifica}
                    borderColor="border-l-violet-500"
                  />
                </div>

                {/* Referto corporeo — silhouette con misurazioni */}
                <BodyReportMap
                  measurements={measurements}
                  metrics={metrics}
                  goals={goals}
                />
              </>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

// ── KpiCard sub-component ──

function KpiCard({
  label,
  value,
  delta,
  rate,
  rateUnit,
  classifica,
  borderColor,
}: {
  label: string;
  value: string | null;
  delta: { value: string; positive: boolean } | null;
  rate: number | null;
  rateUnit: string;
  classifica: string | null;
  borderColor: string;
}) {
  return (
    <Card className={`border-l-4 ${borderColor} bg-gradient-to-br from-background to-muted/30`}>
      <CardContent className="p-3">
        <span className="text-[10px] font-medium text-muted-foreground">{label}</span>
        <div className="mt-1 flex items-baseline gap-1.5">
          <span className="text-xl font-extrabold tracking-tighter tabular-nums">
            {value ?? "—"}
          </span>
          {delta && (
            <span className={`flex items-center text-[10px] font-medium ${delta.positive ? "text-emerald-600" : "text-red-500"}`}>
              {delta.positive ? <TrendingDown className="mr-0.5 h-3 w-3" /> : <TrendingUp className="mr-0.5 h-3 w-3" />}
              {delta.value}
            </span>
          )}
        </div>
        {rate !== null && (
          <p className="text-[9px] font-medium tabular-nums text-muted-foreground">
            {formatRate(rate, rateUnit)}
          </p>
        )}
        {classifica && (
          <Badge variant="outline" className="mt-0.5 text-[8px]">
            {classifica}
          </Badge>
        )}
      </CardContent>
    </Card>
  );
}
