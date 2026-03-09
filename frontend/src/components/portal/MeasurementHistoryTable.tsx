"use client";

/**
 * MeasurementHistoryTable — Storico misurazioni espandibile con edit/delete.
 * Sotto-componente del portale cliente, sezione Misurazioni.
 */

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import { ChevronDown, Pencil, Trash2 } from "lucide-react";

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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { useDeleteMeasurement } from "@/hooks/useMeasurements";
import type { Measurement, Metric, MetricCategory } from "@/types/api";
import { METRIC_CATEGORY_LABELS } from "@/types/api";

interface MeasurementHistoryTableProps {
  measurements: Measurement[];
  metricMap: Map<number, Metric>;
  clientId: number;
}

export function MeasurementHistoryTable({
  measurements,
  metricMap,
  clientId,
}: MeasurementHistoryTableProps) {
  const router = useRouter();
  const deleteMutation = useDeleteMeasurement(clientId);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // Top 4 metriche piu' tracciate per colonne tabella
  const tableMetricIds = useMemo(() => {
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

  const handleDeleteConfirm = () => {
    if (deleteId !== null) {
      deleteMutation.mutate(deleteId, { onSuccess: () => setDeleteId(null) });
    }
  };

  if (measurements.length === 0) return null;

  return (
    <>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8" />
              <TableHead>Data</TableHead>
              {tableMetricIds.map((id) => (
                <TableHead key={id} className="text-right hidden sm:table-cell">
                  {metricMap.get(id)?.nome ?? `#${id}`}
                </TableHead>
              ))}
              <TableHead className="hidden md:table-cell">Note</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {measurements.map((m) => (
              <HistoryRow
                key={m.id}
                measurement={m}
                tableMetricIds={tableMetricIds}
                metricMap={metricMap}
                isExpanded={expandedId === m.id}
                onToggleExpand={() => setExpandedId((prev) => (prev === m.id ? null : m.id))}
                onEdit={() => router.push(`/clienti/${clientId}/misurazioni?edit=${m.id}`)}
                onDelete={() => setDeleteId(m.id)}
              />
            ))}
          </TableBody>
        </Table>
      </div>

      <AlertDialog open={deleteId !== null} onOpenChange={(open) => !open && setDeleteId(null)}>
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

// ── HistoryRow — riga espandibile con valori raggruppati per categoria ──

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
  const expandedGroups = useMemo(() => {
    if (!isExpanded) return [];
    const groups = new Map<MetricCategory, { nome: string; valore: number; unita: string }[]>();
    for (const v of measurement.valori) {
      const metric = metricMap.get(v.id_metrica);
      if (!metric) continue;
      const cat = metric.categoria as MetricCategory;
      if (!groups.has(cat)) groups.set(cat, []);
      groups.get(cat)!.push({ nome: metric.nome, valore: v.valore, unita: metric.unita_misura });
    }
    return [...groups.entries()];
  }, [isExpanded, measurement.valori, metricMap]);

  const colSpan = 2 + tableMetricIds.length + 2;

  return (
    <>
      <TableRow className="cursor-pointer hover:bg-muted/50" onClick={onToggleExpand}>
        <TableCell className="w-8 px-2">
          <ChevronDown
            className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
          />
        </TableCell>
        <TableCell className="font-medium whitespace-nowrap">
          {format(parseISO(measurement.data_misurazione), "d MMM yyyy", { locale: it })}
        </TableCell>
        {tableMetricIds.map((metricId) => {
          const val = measurement.valori.find((v) => v.id_metrica === metricId);
          return (
            <TableCell key={metricId} className="text-right tabular-nums hidden sm:table-cell">
              {val ? `${val.valore} ${val.unita}` : "—"}
            </TableCell>
          );
        })}
        <TableCell className="max-w-[200px] truncate text-muted-foreground hidden md:table-cell">
          {measurement.note ?? "—"}
        </TableCell>
        <TableCell className="text-right">
          <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onEdit}>
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
                      <div key={v.nome} className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{v.nome}</span>
                        <span className="font-medium tabular-nums">{v.valore} {v.unita}</span>
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
