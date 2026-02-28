// src/components/clients/ProgressiTab.tsx
"use client";

/**
 * ProgressiTab — Tab principale per il tracking misurazioni corporee.
 *
 * Layout: KPI cards -> Chart trend -> Storico tabellare
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
  Pencil,
  Plus,
  Printer,
  Scale,
  Trash2,
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

import { MeasurementChart } from "@/components/clients/MeasurementChart";
import {
  useClientMeasurements,
  useDeleteMeasurement,
  useMetrics,
} from "@/hooks/useMeasurements";
import type { Measurement } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

interface ProgressiTabProps {
  clientId: number;
}

// ════════════════════════════════════════════════════════════
// KPI CONFIG
// ════════════════════════════════════════════════════════════

interface KpiCardConfig {
  key: string;
  label: string;
  icon: typeof Scale;
  borderColor: string;
  getValue: (measurements: Measurement[]) => string;
  getDelta: (measurements: Measurement[]) => { value: string; positive: boolean } | null;
}

function getMetricValue(
  measurements: Measurement[],
  metricId: number
): number | null {
  if (measurements.length === 0) return null;
  const latest = measurements[0];
  const val = latest.valori.find((v) => v.id_metrica === metricId);
  return val ? val.valore : null;
}

function getMetricDelta(
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
  return {
    value: `${sign}${diff.toFixed(1)}`,
    positive: diff < 0, // per peso/grasso: calare e' positivo
  };
}

const PROGRESSI_KPI: KpiCardConfig[] = [
  {
    key: "peso",
    label: "Peso",
    icon: Scale,
    borderColor: "border-l-teal-500",
    getValue: (m) => {
      const v = getMetricValue(m, 1);
      return v !== null ? `${v} kg` : "—";
    },
    getDelta: (m) => getMetricDelta(m, 1),
  },
  {
    key: "grassa",
    label: "Massa Grassa",
    icon: Activity,
    borderColor: "border-l-amber-500",
    getValue: (m) => {
      const v = getMetricValue(m, 3);
      return v !== null ? `${v}%` : "—";
    },
    getDelta: (m) => getMetricDelta(m, 3),
  },
  {
    key: "data",
    label: "Ultima Misurazione",
    icon: Calendar,
    borderColor: "border-l-blue-500",
    getValue: (m) => {
      if (m.length === 0) return "—";
      return format(parseISO(m[0].data_misurazione), "d MMM yyyy", {
        locale: it,
      });
    },
    getDelta: () => null,
  },
  {
    key: "sessioni",
    label: "Sessioni Totali",
    icon: TrendingUp,
    borderColor: "border-l-emerald-500",
    getValue: (m) => String(m.length),
    getDelta: () => null,
  },
];

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function ProgressiTab({ clientId }: ProgressiTabProps) {
  const router = useRouter();
  const { data: measurementsData, isLoading } = useClientMeasurements(clientId);
  const { data: metrics } = useMetrics();
  const deleteMutation = useDeleteMeasurement(clientId);

  const [deleteId, setDeleteId] = useState<number | null>(null);

  const measurements = measurementsData?.items ?? [];

  // Metriche chiave presenti nelle misurazioni (per colonne tabella)
  const keyMetricIds = useMemo(() => {
    const candidates = [1, 3, 9]; // Peso, Massa Grassa, Vita
    const available = new Set<number>();
    for (const m of measurements) {
      for (const v of m.valori) {
        available.add(v.id_metrica);
      }
    }
    return candidates.filter((id) => available.has(id));
  }, [measurements]);

  const metricMap = useMemo(() => {
    if (!metrics) return new Map<number, string>();
    return new Map(metrics.map((m) => [m.id, m.nome]));
  }, [metrics]);

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

  // Loading state
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

  // Empty state
  if (measurements.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center gap-4 py-16">
          <div className="rounded-full bg-teal-50 p-4 dark:bg-teal-950/30">
            <Scale className="h-10 w-10 text-teal-500" />
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold">Nessuna misurazione registrata</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Registra la prima misurazione per visualizzare il trend del cliente
            </p>
          </div>
          <Button onClick={handleNewMeasurement}>
            <Plus className="mr-2 h-4 w-4" />
            Nuova Misurazione
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Progressi Fisici</h2>
          <div className="flex gap-2" data-print-hide>
            <Button variant="outline" size="sm" onClick={handlePrint}>
              <Printer className="mr-2 h-4 w-4" />
              Stampa
            </Button>
            <Button size="sm" onClick={handleNewMeasurement}>
              <Plus className="mr-2 h-4 w-4" />
              Nuova Misurazione
            </Button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {PROGRESSI_KPI.map((kpi) => {
            const delta = kpi.getDelta(measurements);
            return (
              <Card
                key={kpi.key}
                className={`border-l-4 ${kpi.borderColor} bg-gradient-to-br from-background to-muted/30 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg`}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">
                      {kpi.label}
                    </span>
                    <kpi.icon className="h-4 w-4 text-muted-foreground/50" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-2xl font-extrabold tracking-tighter tabular-nums">
                      {kpi.getValue(measurements)}
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
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Chart */}
        {metrics && (
          <Card>
            <CardContent className="pt-6">
              <MeasurementChart
                measurements={measurements}
                metrics={metrics}
              />
            </CardContent>
          </Card>
        )}

        {/* Storico tabellare */}
        <Card>
          <CardContent className="pt-6">
            <h3 className="mb-4 text-sm font-semibold">Storico Misurazioni</h3>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Data</TableHead>
                    {keyMetricIds.map((id) => (
                      <TableHead key={id} className="text-right">
                        {metricMap.get(id) ?? `#${id}`}
                      </TableHead>
                    ))}
                    <TableHead>Note</TableHead>
                    <TableHead className="text-right" data-print-hide>
                      Azioni
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {measurements.map((m) => (
                    <TableRow key={m.id}>
                      <TableCell className="font-medium whitespace-nowrap">
                        {format(parseISO(m.data_misurazione), "d MMM yyyy", {
                          locale: it,
                        })}
                      </TableCell>
                      {keyMetricIds.map((metricId) => {
                        const val = m.valori.find(
                          (v) => v.id_metrica === metricId
                        );
                        return (
                          <TableCell key={metricId} className="text-right tabular-nums">
                            {val ? `${val.valore} ${val.unita}` : "—"}
                          </TableCell>
                        );
                      })}
                      <TableCell className="max-w-[200px] truncate text-muted-foreground">
                        {m.note ?? "—"}
                      </TableCell>
                      <TableCell className="text-right" data-print-hide>
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => handleEditMeasurement(m)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={() => setDeleteId(m.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
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
    </>
  );
}
