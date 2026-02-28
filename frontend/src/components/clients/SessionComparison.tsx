// src/components/clients/SessionComparison.tsx
"use client";

/**
 * SessionComparison — Confronto affiancato tra 2 sessioni di misurazione.
 *
 * Mostra una tabella delta con tutte le metriche presenti in entrambe le sessioni.
 * Colori: emerald per miglioramento, red per peggioramento,
 * muted per categorie neutre (circonferenze).
 *
 * Collapsible — default chiuso per non sovraccaricare la pagina.
 */

import { useMemo, useState } from "react";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  ArrowDownRight,
  ArrowUpRight,
  ChevronDown,
  GitCompareArrows,
  Minus,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import type { Measurement, Metric } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

interface SessionComparisonProps {
  measurements: Measurement[];
  metrics: Metric[];
}

// Metriche dove calare e' positivo (peso, grasso, BMI)
const LOWER_IS_BETTER = new Set([1, 3, 5]);
// Metriche dove aumentare e' positivo (forza)
const HIGHER_IS_BETTER = new Set([20, 21, 22]);
// Tutto il resto: neutro (circonferenze, cardio, altezza, acqua, massa magra)

type DeltaColor = "emerald" | "red" | "muted";

function getDeltaColor(metricId: number, diff: number): DeltaColor {
  if (diff === 0) return "muted";
  if (LOWER_IS_BETTER.has(metricId)) {
    return diff < 0 ? "emerald" : "red";
  }
  if (HIGHER_IS_BETTER.has(metricId)) {
    return diff > 0 ? "emerald" : "red";
  }
  return "muted";
}

const COLOR_CLASSES: Record<DeltaColor, string> = {
  emerald: "text-emerald-600 dark:text-emerald-400",
  red: "text-red-500 dark:text-red-400",
  muted: "text-muted-foreground",
};

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function SessionComparison({
  measurements,
  metrics,
}: SessionComparisonProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Default: sessione piu' recente (index 0) vs penultima (index 1)
  // measurements sono ordinati DESC dal backend
  const [sessionAId, setSessionAId] = useState<string>(() =>
    measurements.length >= 2 ? String(measurements[1].id) : ""
  );
  const [sessionBId, setSessionBId] = useState<string>(() =>
    measurements.length >= 1 ? String(measurements[0].id) : ""
  );

  const sessionA = measurements.find((m) => m.id === parseInt(sessionAId, 10));
  const sessionB = measurements.find((m) => m.id === parseInt(sessionBId, 10));

  // Metric lookup
  const metricMap = useMemo(
    () => new Map(metrics.map((m) => [m.id, m])),
    [metrics]
  );

  // Tabella delta: solo metriche presenti in entrambe le sessioni
  const deltaRows = useMemo(() => {
    if (!sessionA || !sessionB) return [];

    const valuesA = new Map(sessionA.valori.map((v) => [v.id_metrica, v.valore]));
    const valuesB = new Map(sessionB.valori.map((v) => [v.id_metrica, v.valore]));

    const rows: {
      metricId: number;
      nome: string;
      unita: string;
      valA: number;
      valB: number;
      diff: number;
      color: DeltaColor;
    }[] = [];

    // Ordina per ordinamento metrica
    const sortedMetricIds = [...valuesA.keys()]
      .filter((id) => valuesB.has(id))
      .sort((a, b) => {
        const mA = metricMap.get(a);
        const mB = metricMap.get(b);
        return (mA?.ordinamento ?? 0) - (mB?.ordinamento ?? 0);
      });

    for (const metricId of sortedMetricIds) {
      const metric = metricMap.get(metricId);
      if (!metric) continue;
      const valA = valuesA.get(metricId)!;
      const valB = valuesB.get(metricId)!;
      const diff = valB - valA;
      rows.push({
        metricId,
        nome: metric.nome,
        unita: metric.unita_misura,
        valA,
        valB,
        diff,
        color: getDeltaColor(metricId, diff),
      });
    }

    return rows;
  }, [sessionA, sessionB, metricMap]);

  // Se meno di 2 sessioni → non mostrare
  if (measurements.length < 2) return null;

  const formatSessionDate = (m: Measurement) =>
    format(parseISO(m.data_misurazione), "d MMM yyyy", { locale: it });

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card>
        <CardContent className="p-4 space-y-4">
          {/* Header — sempre visibile */}
          <CollapsibleTrigger asChild>
            <button className="flex items-center justify-between w-full text-left group">
              <div className="flex items-center gap-2">
                <GitCompareArrows className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-semibold">Confronto Sessioni</span>
              </div>
              <ChevronDown
                className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${
                  isOpen ? "rotate-180" : ""
                }`}
              />
            </button>
          </CollapsibleTrigger>

          <CollapsibleContent className="space-y-4">
            {/* Selettori sessioni */}
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
              <div className="flex items-center gap-2 flex-1">
                <span className="text-xs font-medium text-muted-foreground whitespace-nowrap">
                  Prima
                </span>
                <Select value={sessionAId} onValueChange={setSessionAId}>
                  <SelectTrigger className="flex-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {measurements.map((m) => (
                      <SelectItem key={m.id} value={String(m.id)}>
                        {formatSessionDate(m)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <span className="hidden sm:block text-xs font-medium text-muted-foreground">
                vs
              </span>

              <div className="flex items-center gap-2 flex-1">
                <span className="text-xs font-medium text-muted-foreground whitespace-nowrap">
                  Dopo
                </span>
                <Select value={sessionBId} onValueChange={setSessionBId}>
                  <SelectTrigger className="flex-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {measurements.map((m) => (
                      <SelectItem key={m.id} value={String(m.id)}>
                        {formatSessionDate(m)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Tabella delta */}
            {deltaRows.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                Nessuna metrica in comune tra le due sessioni selezionate
              </p>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Metrica</TableHead>
                      <TableHead className="text-right">Prima</TableHead>
                      <TableHead className="text-right">Dopo</TableHead>
                      <TableHead className="text-right">Variazione</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {deltaRows.map((row) => {
                      const sign = row.diff > 0 ? "+" : "";
                      return (
                        <TableRow key={row.metricId}>
                          <TableCell className="font-medium">{row.nome}</TableCell>
                          <TableCell className="text-right tabular-nums">
                            {row.valA} {row.unita}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {row.valB} {row.unita}
                          </TableCell>
                          <TableCell className="text-right">
                            <span
                              className={`inline-flex items-center gap-0.5 text-sm font-medium tabular-nums ${COLOR_CLASSES[row.color]}`}
                            >
                              {row.diff === 0 ? (
                                <>
                                  <Minus className="h-3 w-3" />
                                  0
                                </>
                              ) : (
                                <>
                                  {row.diff > 0 ? (
                                    <ArrowUpRight className="h-3 w-3" />
                                  ) : (
                                    <ArrowDownRight className="h-3 w-3" />
                                  )}
                                  {sign}
                                  {row.diff.toFixed(1)} {row.unita}
                                </>
                              )}
                            </span>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CollapsibleContent>
        </CardContent>
      </Card>
    </Collapsible>
  );
}
