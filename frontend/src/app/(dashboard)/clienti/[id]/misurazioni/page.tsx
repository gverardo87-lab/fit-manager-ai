// src/app/(dashboard)/clienti/[id]/misurazioni/page.tsx
"use client";

/**
 * Pagina dedicata Misurazione Corporea.
 *
 * Task clinico primario: merita una pagina full-page con layout spazioso.
 * Modes:
 *   /clienti/{id}/misurazioni           → nuova misurazione
 *   /clienti/{id}/misurazioni?edit={mid} → modifica misurazione esistente
 *
 * Back button: torna al profilo cliente tab Progressi.
 */

import { use, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import {
  ArrowLeft,
  CalendarIcon,
  CheckCircle2,
  Save,
  Scale,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";

import { useClient } from "@/hooks/useClients";
import {
  useMetrics,
  useClientMeasurements,
  useCreateMeasurement,
  useUpdateMeasurement,
} from "@/hooks/useMeasurements";
import type { Metric, Measurement, MeasurementValueInput, MetricCategory } from "@/types/api";
import { METRIC_CATEGORY_LABELS } from "@/types/api";

// ════════════════════════════════════════════════════════════
// CATEGORY ICONS & COLORS
// ════════════════════════════════════════════════════════════

const CATEGORY_STYLE: Record<MetricCategory, { border: string; bg: string }> = {
  antropometrica: { border: "border-l-teal-500", bg: "bg-teal-50 dark:bg-teal-950/20" },
  composizione: { border: "border-l-violet-500", bg: "bg-violet-50 dark:bg-violet-950/20" },
  circonferenza: { border: "border-l-blue-500", bg: "bg-blue-50 dark:bg-blue-950/20" },
  cardiovascolare: { border: "border-l-rose-500", bg: "bg-rose-50 dark:bg-rose-950/20" },
  forza: { border: "border-l-amber-500", bg: "bg-amber-50 dark:bg-amber-950/20" },
};

// ════════════════════════════════════════════════════════════
// PAGE
// ════════════════════════════════════════════════════════════

export default function MisurazionePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const clientId = parseInt(id, 10);
  const router = useRouter();
  const searchParams = useSearchParams();
  const editId = searchParams.get("edit");

  // Data
  const { data: client, isLoading: clientLoading } = useClient(clientId);
  const { data: metrics, isLoading: metricsLoading } = useMetrics();
  const { data: measurementsData } = useClientMeasurements(editId ? clientId : null);
  const createMutation = useCreateMeasurement(clientId);
  const updateMutation = useUpdateMeasurement(clientId);

  // Find measurement to edit
  const editMeasurement = useMemo(() => {
    if (!editId || !measurementsData) return null;
    return measurementsData.items.find((m) => m.id === parseInt(editId, 10)) ?? null;
  }, [editId, measurementsData]);

  const isEdit = !!editId;

  // Form state
  const [date, setDate] = useState<Date>(new Date());
  const [note, setNote] = useState("");
  const [values, setValues] = useState<Record<number, string>>({});

  // Initialize form from edit measurement
  useEffect(() => {
    if (editMeasurement) {
      setDate(new Date(editMeasurement.data_misurazione));
      setNote(editMeasurement.note ?? "");
      const vals: Record<number, string> = {};
      for (const v of editMeasurement.valori) {
        vals[v.id_metrica] = String(v.valore);
      }
      setValues(vals);
    }
  }, [editMeasurement]);

  // Group metrics by category
  const metricsByCategory = useMemo(() => {
    if (!metrics) return new Map<MetricCategory, Metric[]>();
    const map = new Map<MetricCategory, Metric[]>();
    for (const m of metrics) {
      const cat = m.categoria as MetricCategory;
      if (!map.has(cat)) map.set(cat, []);
      map.get(cat)!.push(m);
    }
    return map;
  }, [metrics]);

  // Filled count
  const filledCount = Object.values(values).filter(
    (v) => v !== "" && v !== undefined
  ).length;

  const handleValueChange = (metricId: number, val: string) => {
    setValues((prev) => ({ ...prev, [metricId]: val }));
  };

  const goBack = () => {
    router.push(`/clienti/${clientId}?tab=progressi`);
  };

  const handleSubmit = () => {
    const valori: MeasurementValueInput[] = [];
    for (const [idStr, valStr] of Object.entries(values)) {
      const numVal = parseFloat(valStr);
      if (!isNaN(numVal)) {
        valori.push({ id_metrica: parseInt(idStr, 10), valore: numVal });
      }
    }

    if (valori.length === 0) return;

    const payload = {
      data_misurazione: format(date, "yyyy-MM-dd"),
      note: note.trim() || null,
      valori,
    };

    if (isEdit && editMeasurement) {
      updateMutation.mutate(
        { measurementId: editMeasurement.id, payload },
        { onSuccess: goBack }
      );
    } else {
      createMutation.mutate(payload, { onSuccess: goBack });
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  // Loading
  if (clientLoading || metricsLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!client) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20">
        <p className="text-lg font-medium">Cliente non trovato</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={goBack}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold tracking-tight">
            {isEdit ? "Modifica Misurazione" : "Nuova Misurazione"}
          </h1>
          <p className="text-sm text-muted-foreground">
            {client.nome} {client.cognome}
          </p>
        </div>
        <Scale className="h-8 w-8 text-teal-500/50" />
      </div>

      <Separator />

      {/* Data misurazione */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <Label className="text-base font-semibold">Data misurazione</Label>
              <p className="text-xs text-muted-foreground">
                Quando sono state rilevate queste misurazioni
              </p>
            </div>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className="w-full justify-start text-left font-normal sm:w-64"
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {format(date, "d MMMM yyyy", { locale: it })}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="end">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={(d) => d && setDate(d)}
                  disabled={{ after: new Date() }}
                  locale={it}
                />
              </PopoverContent>
            </Popover>
          </div>
        </CardContent>
      </Card>

      {/* Metriche per categoria */}
      {Array.from(metricsByCategory.entries()).map(([category, categoryMetrics]) => {
        const style = CATEGORY_STYLE[category];
        const categoryFilled = categoryMetrics.filter(
          (m) => values[m.id] && values[m.id] !== ""
        ).length;

        return (
          <Card key={category} className={`border-l-4 ${style.border}`}>
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  {METRIC_CATEGORY_LABELS[category]}
                </CardTitle>
                {categoryFilled > 0 && (
                  <span className="flex items-center gap-1 text-xs font-medium text-teal-600 dark:text-teal-400">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    {categoryFilled}/{categoryMetrics.length}
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {categoryMetrics.map((metric) => (
                  <div key={metric.id} className="space-y-1.5">
                    <Label
                      htmlFor={`metric-${metric.id}`}
                      className="text-sm font-medium"
                    >
                      {metric.nome}
                    </Label>
                    <div className="relative">
                      <Input
                        id={`metric-${metric.id}`}
                        type="number"
                        step="0.1"
                        placeholder="—"
                        value={values[metric.id] ?? ""}
                        onChange={(e) =>
                          handleValueChange(metric.id, e.target.value)
                        }
                        className="pr-14 tabular-nums"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-muted-foreground">
                        {metric.unita_misura}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        );
      })}

      {/* Note */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-base">Note</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            id="measurement-note"
            placeholder="Appunti sulla sessione di misurazione..."
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={4}
          />
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between rounded-lg border bg-muted/30 p-4">
        <p className="text-sm text-muted-foreground">
          {filledCount === 0
            ? "Compila almeno un valore"
            : `${filledCount} ${filledCount === 1 ? "valore compilato" : "valori compilati"}`}
        </p>
        <div className="flex gap-3">
          <Button variant="outline" onClick={goBack}>
            Annulla
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isPending || filledCount === 0}
          >
            {isPending ? (
              "Salvataggio..."
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                {isEdit ? "Aggiorna" : "Salva Misurazione"}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
