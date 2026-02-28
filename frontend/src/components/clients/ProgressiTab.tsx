// src/components/clients/ProgressiTab.tsx
"use client";

/**
 * ProgressiTab v2 — Dashboard completa tracking misurazioni corporee.
 *
 * Layout (top to bottom):
 *   1. Header: titolo + Stampa + Nuova Misurazione
 *   2. KPI Cards (dinamici, basati sulle metriche tracciate)
 *   3. Category Summary (mini-card per categoria con conteggio metriche)
 *   4. Trend Chart (multi-metric con dual Y-axis)
 *   5. Mappa Corporea Interattiva (click zone → misurazioni + esercizi + anamnesi)
 *   6. Confronto Sessioni (Collapsible)
 *   7. Storico Misurazioni (tabella espandibile)
 *
 * Empty state: CTA per prima misurazione.
 * Create/Edit: navigazione a pagina dedicata /clienti/{id}/misurazioni.
 */

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  Activity,
  Calendar,
  ChevronDown,
  Dumbbell,
  Heart,
  Pencil,
  Plus,
  Printer,
  Ruler,
  Scale,
  Trash2,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { GoalsSummary } from "@/components/clients/GoalsSummary";
import { GoalFormDialog } from "@/components/clients/GoalFormDialog";
import { InteractiveBodyMap } from "@/components/clients/InteractiveBodyMap";
import { MeasurementChart } from "@/components/clients/MeasurementChart";
import { ClinicalAnalysisPanel } from "@/components/clients/ClinicalAnalysisPanel";
import { SessionComparison } from "@/components/clients/SessionComparison";
import {
  useClientMeasurements,
  useDeleteMeasurement,
  useMetrics,
} from "@/hooks/useMeasurements";
import { useClientGoals } from "@/hooks/useGoals";
import { computeWeeklyRate, formatRate } from "@/lib/measurement-analytics";
import { classifyValue, computeAge, BAND_COLOR_CLASSES } from "@/lib/normative-ranges";
import type { Measurement, Metric, MetricCategory } from "@/types/api";
import { METRIC_CATEGORY_LABELS } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

interface ProgressiTabProps {
  clientId: number;
  sesso?: string | null;
  dataNascita?: string | null;
}

// ════════════════════════════════════════════════════════════
// KPI LOGIC — Dinamici
// ════════════════════════════════════════════════════════════

// Metriche prioritarie per KPI (ordine di preferenza)
const PRIORITY_METRIC_IDS = [1, 3, 5]; // Peso, Massa Grassa, BMI

// Metriche dove calare e' positivo (peso, grasso, BMI, vita, fianchi)
const LOWER_IS_BETTER = new Set([1, 3, 5, 9, 10]);
// Metriche dove aumentare e' positivo (forza, massa magra)
const HIGHER_IS_BETTER = new Set([4, 20, 21, 22]);

function computeDeltaInfo(
  measurements: Measurement[],
  metricId: number
): { value: string; positive: boolean } | null {
  if (measurements.length < 2) return null;
  const latest = measurements[0].valori.find((v) => v.id_metrica === metricId);
  const prev = measurements[1].valori.find((v) => v.id_metrica === metricId);
  if (!latest || !prev) return null;
  const diff = latest.valore - prev.valore;
  if (diff === 0) return null;
  const sign = diff > 0 ? "+" : "";
  let positive: boolean;
  if (LOWER_IS_BETTER.has(metricId)) {
    positive = diff < 0;
  } else if (HIGHER_IS_BETTER.has(metricId)) {
    positive = diff > 0;
  } else {
    // Neutro — mostra la freccia ma non colora
    positive = diff > 0; // just for icon direction
  }
  return { value: `${sign}${diff.toFixed(1)}`, positive };
}

// Icona + colore per categoria
const CATEGORY_CONFIG: Record<MetricCategory, { icon: typeof Scale; color: string }> = {
  antropometrica: { icon: Scale, color: "border-l-teal-500" },
  composizione: { icon: Activity, color: "border-l-violet-500" },
  circonferenza: { icon: Ruler, color: "border-l-blue-500" },
  cardiovascolare: { icon: Heart, color: "border-l-rose-500" },
  forza: { icon: Dumbbell, color: "border-l-amber-500" },
};

// KPI card border colors (cycle through)
const KPI_BORDER_COLORS = [
  "border-l-teal-500",
  "border-l-amber-500",
  "border-l-violet-500",
  "border-l-blue-500",
];

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function ProgressiTab({ clientId, sesso, dataNascita }: ProgressiTabProps) {
  const router = useRouter();
  const { data: measurementsData, isLoading } = useClientMeasurements(clientId);
  const { data: metrics } = useMetrics();
  const { data: goalsData } = useClientGoals(clientId);
  const deleteMutation = useDeleteMeasurement(clientId);

  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [goalFormOpen, setGoalFormOpen] = useState(false);

  const measurements = measurementsData?.items ?? [];

  // ── Metriche tracciate (con almeno 1 valore) ──
  const trackedMetricIds = useMemo(() => {
    const ids = new Set<number>();
    for (const m of measurements) {
      for (const v of m.valori) {
        ids.add(v.id_metrica);
      }
    }
    return ids;
  }, [measurements]);

  // ── Metric lookup ──
  const metricMap = useMemo(() => {
    if (!metrics) return new Map<number, Metric>();
    return new Map(metrics.map((m) => [m.id, m]));
  }, [metrics]);

  // ── Valori correnti (dalla sessione piu' recente) per GoalFormDialog ──
  const currentValues = useMemo(() => {
    if (measurements.length === 0) return new Map<number, number>();
    const latest = measurements[0];
    return new Map(latest.valori.map((v) => [v.id_metrica, v.valore]));
  }, [measurements]);

  // ── KPI dinamici: top metriche prioritarie + fill con piu' tracciate ──
  const dynamicKpiMetrics = useMemo(() => {
    // Start with priority metrics that have data
    const kpis: Metric[] = [];
    for (const id of PRIORITY_METRIC_IDS) {
      if (trackedMetricIds.has(id)) {
        const m = metricMap.get(id);
        if (m) kpis.push(m);
      }
    }
    // Fill up to 2 metric KPIs with most tracked metrics
    if (kpis.length < 2 && metrics) {
      const usedIds = new Set(kpis.map((m) => m.id));
      // Count occurrences per metric
      const counts = new Map<number, number>();
      for (const m of measurements) {
        for (const v of m.valori) {
          if (!usedIds.has(v.id_metrica)) {
            counts.set(v.id_metrica, (counts.get(v.id_metrica) ?? 0) + 1);
          }
        }
      }
      const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]);
      for (const [id] of sorted) {
        if (kpis.length >= 2) break;
        const m = metricMap.get(id);
        if (m) kpis.push(m);
      }
    }
    return kpis;
  }, [trackedMetricIds, metricMap, metrics, measurements]);

  // ── Category summary (categorie con dati) ──
  const categorySummary = useMemo(() => {
    if (!metrics) return [];
    const catCounts = new Map<MetricCategory, number>();
    for (const id of trackedMetricIds) {
      const m = metricMap.get(id);
      if (m) {
        const cat = m.categoria as MetricCategory;
        catCounts.set(cat, (catCounts.get(cat) ?? 0) + 1);
      }
    }
    return [...catCounts.entries()].map(([cat, count]) => ({
      category: cat,
      count,
      label: METRIC_CATEGORY_LABELS[cat],
      ...CATEGORY_CONFIG[cat],
    }));
  }, [metrics, trackedMetricIds, metricMap]);

  // ── Top colonne per tabella storico ──
  const tableMetricIds = useMemo(() => {
    // Conta frequenza per trovare le metriche piu' tracciate
    const counts = new Map<number, number>();
    for (const m of measurements) {
      for (const v of m.valori) {
        counts.set(v.id_metrica, (counts.get(v.id_metrica) ?? 0) + 1);
      }
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
      .map(([id]) => id);
  }, [measurements]);

  // ── Handlers ──
  const handleNewMeasurement = () => {
    router.push(`/clienti/${clientId}/misurazioni`);
  };

  const handleEditMeasurement = (m: Measurement) => {
    router.push(`/clienti/${clientId}/misurazioni?edit=${m.id}`);
  };

  const handleDeleteConfirm = () => {
    if (deleteId !== null) {
      deleteMutation.mutate(deleteId, {
        onSuccess: () => setDeleteId(null),
      });
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const toggleExpanded = (id: number) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  // ── Loading state ──
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="h-24 animate-pulse bg-muted/50" />
          ))}
        </div>
      </div>
    );
  }

  // ── Goals limit check ──
  const activeGoalsCount = goalsData?.attivi ?? 0;
  const goalsMaxed = activeGoalsCount >= 3;

  // ── Empty state ──
  if (measurements.length === 0) {
    return (
      <>
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center gap-4 py-16">
            <div className="rounded-full bg-teal-50 p-4 dark:bg-teal-950/30">
              <Scale className="h-10 w-10 text-teal-500" />
            </div>
            <div className="text-center">
              <p className="text-lg font-semibold">Nessuna misurazione registrata</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Registra la prima misurazione o imposta gli obiettivi del cliente
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setGoalFormOpen(true)}
                disabled={goalsMaxed}
                title={goalsMaxed ? "Max 3 obiettivi attivi" : undefined}
              >
                <Target className="mr-2 h-4 w-4" />
                Nuovo Obiettivo
              </Button>
              <Button onClick={handleNewMeasurement}>
                <Plus className="mr-2 h-4 w-4" />
                Nuova Misurazione
              </Button>
            </div>
          </CardContent>
        </Card>
        <GoalFormDialog
          open={goalFormOpen}
          onOpenChange={setGoalFormOpen}
          clientId={clientId}
          goal={null}
          currentValues={currentValues}
          sesso={sesso}
          dataNascita={dataNascita}
        />
      </>
    );
  }

  return (
    <>
      <div className="space-y-6">
        {/* ── 1. Header ── */}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Progressi Fisici</h2>
          <div className="flex gap-2" data-print-hide>
            <Button variant="outline" size="sm" onClick={handlePrint}>
              <Printer className="mr-2 h-4 w-4" />
              Stampa
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setGoalFormOpen(true)}
              disabled={goalsMaxed}
              title={goalsMaxed ? "Max 3 obiettivi attivi" : undefined}
            >
              <Target className="mr-2 h-4 w-4" />
              Nuovo Obiettivo
            </Button>
            <Button size="sm" onClick={handleNewMeasurement}>
              <Plus className="mr-2 h-4 w-4" />
              Nuova Misurazione
            </Button>
          </div>
        </div>

        {/* ── 2. Obiettivi ── */}
        <GoalsSummary clientId={clientId} currentValues={currentValues} sesso={sesso} dataNascita={dataNascita} />

        {/* ── 2b. Analisi Clinica ── */}
        <ClinicalAnalysisPanel
          measurements={measurements}
          sesso={sesso}
          dataNascita={dataNascita}
          goals={goalsData?.items}
        />

        {/* ── 3. KPI Cards (dinamici) ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Metric-based KPIs */}
          {dynamicKpiMetrics.map((metric, idx) => {
            const latest = measurements[0]?.valori.find(
              (v) => v.id_metrica === metric.id
            );
            const delta = computeDeltaInfo(measurements, metric.id);
            const rate = computeWeeklyRate(measurements, metric.id);
            const clientAge = computeAge(dataNascita);
            const normClass = latest
              ? classifyValue(metric.id, latest.valore, sesso, clientAge)
              : null;
            const borderColor = KPI_BORDER_COLORS[idx % KPI_BORDER_COLORS.length];

            return (
              <Card
                key={metric.id}
                className={`border-l-4 ${borderColor} bg-gradient-to-br from-background to-muted/30 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg`}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">
                      {metric.nome}
                    </span>
                    <Scale className="h-4 w-4 text-muted-foreground/50" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-2xl font-extrabold tracking-tighter tabular-nums">
                      {latest
                        ? `${latest.valore} ${metric.unita_misura}`
                        : "—"}
                    </span>
                    {delta && (
                      <span
                        className={`flex items-center text-xs font-medium ${
                          delta.positive
                            ? "text-emerald-600"
                            : "text-red-500"
                        }`}
                      >
                        {delta.positive ? (
                          <TrendingDown className="mr-0.5 h-3 w-3" />
                        ) : (
                          <TrendingUp className="mr-0.5 h-3 w-3" />
                        )}
                        {delta.value}
                      </span>
                    )}
                  </div>
                  {rate !== null && (
                    <p className="mt-1 text-[10px] font-medium tabular-nums text-muted-foreground">
                      {formatRate(rate, metric.unita_misura)}
                    </p>
                  )}
                  {normClass && (
                    <span
                      className={`mt-1 inline-block rounded-full px-2 py-0.5 text-[9px] font-semibold ${
                        BAND_COLOR_CLASSES[normClass.color]?.bg ?? ""
                      } ${BAND_COLOR_CLASSES[normClass.color]?.text ?? ""}`}
                    >
                      {normClass.label}
                    </span>
                  )}
                </CardContent>
              </Card>
            );
          })}

          {/* Ultima Misurazione */}
          <Card className="border-l-4 border-l-blue-500 bg-gradient-to-br from-background to-muted/30 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground">
                  Ultima Misurazione
                </span>
                <Calendar className="h-4 w-4 text-muted-foreground/50" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-extrabold tracking-tighter tabular-nums">
                  {format(parseISO(measurements[0].data_misurazione), "d MMM yyyy", {
                    locale: it,
                  })}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Sessioni Totali */}
          <Card className="border-l-4 border-l-emerald-500 bg-gradient-to-br from-background to-muted/30 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground">
                  Sessioni Totali
                </span>
                <TrendingUp className="h-4 w-4 text-muted-foreground/50" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-extrabold tracking-tighter tabular-nums">
                  {measurements.length}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── 3. Category Summary ── */}
        {categorySummary.length > 1 && (
          <div className="flex flex-wrap gap-2">
            {categorySummary.map(({ category, count, label, icon: CatIcon, color }) => (
              <div
                key={category}
                className={`inline-flex items-center gap-2 rounded-lg border-l-4 ${color} bg-muted/30 px-3 py-2`}
              >
                <CatIcon className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs font-medium">{label}</span>
                <span className="rounded-full bg-background px-1.5 py-0.5 text-[10px] font-bold tabular-nums">
                  {count}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* ── 4. Chart ── */}
        {metrics && (
          <Card>
            <CardContent className="pt-6">
              <MeasurementChart
                measurements={measurements}
                metrics={metrics}
                sesso={sesso}
                dataNascita={dataNascita}
              />
            </CardContent>
          </Card>
        )}

        {/* ── 5. Mappa Corporea Interattiva ── */}
        {metrics && (
          <InteractiveBodyMap
            clientId={clientId}
            measurements={measurements}
            metrics={metrics}
          />
        )}

        {/* ── 6. Confronto Sessioni ── */}
        {metrics && (
          <SessionComparison
            measurements={measurements}
            metrics={metrics}
          />
        )}

        {/* ── 7. Storico Misurazioni (espandibile) ── */}
        <Card>
          <CardContent className="pt-6">
            <h3 className="mb-4 text-sm font-semibold">Storico Misurazioni</h3>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-8" data-print-hide />
                    <TableHead>Data</TableHead>
                    {tableMetricIds.map((id) => (
                      <TableHead key={id} className="text-right">
                        {metricMap.get(id)?.nome ?? `#${id}`}
                      </TableHead>
                    ))}
                    <TableHead>Note</TableHead>
                    <TableHead className="text-right" data-print-hide>
                      Azioni
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {measurements.map((m) => {
                    const isExpanded = expandedId === m.id;
                    return (
                      <HistoryRow
                        key={m.id}
                        measurement={m}
                        tableMetricIds={tableMetricIds}
                        metricMap={metricMap}
                        isExpanded={isExpanded}
                        onToggleExpand={() => toggleExpanded(m.id)}
                        onEdit={() => handleEditMeasurement(m)}
                        onDelete={() => setDeleteId(m.id)}
                      />
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Delete confirm */}
      <AlertDialog
        open={deleteId !== null}
        onOpenChange={(open) => !open && setDeleteId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Elimina misurazione</AlertDialogTitle>
            <AlertDialogDescription>
              Sei sicuro di voler eliminare questa sessione di misurazione?
              L&apos;operazione non puo&apos; essere annullata.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annulla</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Elimina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Goal form dialog (header CTA) */}
      <GoalFormDialog
        open={goalFormOpen}
        onOpenChange={setGoalFormOpen}
        clientId={clientId}
        goal={null}
        currentValues={currentValues}
      />
    </>
  );
}

// ════════════════════════════════════════════════════════════
// HISTORY ROW — Espandibile con tutti i valori
// ════════════════════════════════════════════════════════════

function HistoryRow({
  measurement,
  tableMetricIds,
  metricMap,
  isExpanded,
  onToggleExpand,
  onEdit,
  onDelete,
}: {
  measurement: Measurement;
  tableMetricIds: number[];
  metricMap: Map<number, Metric>;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onEdit: () => void;
  onDelete: () => void;
}) {
  // Group expanded values by category
  const expandedGroups = useMemo(() => {
    if (!isExpanded) return [];
    const groups = new Map<MetricCategory, { nome: string; valore: number; unita: string }[]>();
    for (const v of measurement.valori) {
      const metric = metricMap.get(v.id_metrica);
      if (!metric) continue;
      const cat = metric.categoria as MetricCategory;
      if (!groups.has(cat)) groups.set(cat, []);
      groups.get(cat)!.push({
        nome: metric.nome,
        valore: v.valore,
        unita: metric.unita_misura,
      });
    }
    return [...groups.entries()];
  }, [isExpanded, measurement.valori, metricMap]);

  const colSpan = 2 + tableMetricIds.length + 2; // chevron + data + metrics + note + azioni

  return (
    <>
      <TableRow
        className="cursor-pointer hover:bg-muted/50"
        onClick={onToggleExpand}
      >
        <TableCell className="w-8 px-2" data-print-hide>
          <ChevronDown
            className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${
              isExpanded ? "rotate-180" : ""
            }`}
          />
        </TableCell>
        <TableCell className="font-medium whitespace-nowrap">
          {format(parseISO(measurement.data_misurazione), "d MMM yyyy", {
            locale: it,
          })}
        </TableCell>
        {tableMetricIds.map((metricId) => {
          const val = measurement.valori.find(
            (v) => v.id_metrica === metricId
          );
          return (
            <TableCell key={metricId} className="text-right tabular-nums">
              {val ? `${val.valore} ${val.unita}` : "—"}
            </TableCell>
          );
        })}
        <TableCell className="max-w-[200px] truncate text-muted-foreground">
          {measurement.note ?? "—"}
        </TableCell>
        <TableCell className="text-right" data-print-hide>
          <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onEdit}
            >
              <Pencil className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-destructive hover:text-destructive"
              onClick={onDelete}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </TableCell>
      </TableRow>

      {/* Riga espansa con tutti i valori raggruppati per categoria */}
      {isExpanded && (
        <TableRow>
          <TableCell colSpan={colSpan} className="bg-muted/20 px-6 py-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {expandedGroups.map(([category, values]) => (
                <div key={category} className="space-y-1.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    {METRIC_CATEGORY_LABELS[category]}
                  </span>
                  <div className="space-y-1">
                    {values.map((v) => (
                      <div
                        key={v.nome}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="text-muted-foreground">{v.nome}</span>
                        <span className="font-medium tabular-nums">
                          {v.valore} {v.unita}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}
