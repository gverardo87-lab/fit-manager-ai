// src/components/clients/GoalFormDialog.tsx
"use client";

/**
 * GoalFormDialog — Dialog per creare/modificare obiettivi strutturati.
 *
 * Select metrica (raggruppata per categoria), direzione, target opzionale,
 * baseline read-only, date inizio/scadenza, priorita', note.
 *
 * Usato sia in modalita' creazione che modifica (prop `goal` opzionale).
 */

import { useEffect, useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  Equal,
  Target,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { DatePicker } from "@/components/ui/date-picker";

import { useMetrics } from "@/hooks/useMeasurements";
import { useCreateGoal, useUpdateGoal, useClientGoals } from "@/hooks/useGoals";
import { METRIC_CATEGORY_LABELS } from "@/types/api";
import type {
  ClientGoal,
  GoalDirection,
  Metric,
  MetricCategory,
} from "@/types/api";
import { toISOLocal } from "@/lib/format";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

interface GoalFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId: number;
  /** Per edit mode — se presente, pre-popola i campi */
  goal?: ClientGoal | null;
  /** Baseline attuale dalla misurazione piu' recente, per display */
  currentValues?: Map<number, number>;
}

const DIRECTION_OPTIONS: {
  value: GoalDirection;
  label: string;
  icon: typeof ArrowUp;
}[] = [
  { value: "diminuire", label: "Diminuire", icon: ArrowDown },
  { value: "aumentare", label: "Aumentare", icon: ArrowUp },
  { value: "mantenere", label: "Mantenere", icon: Equal },
];

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function GoalFormDialog({
  open,
  onOpenChange,
  clientId,
  goal,
  currentValues,
}: GoalFormDialogProps) {
  const isEdit = !!goal;

  const { data: metrics } = useMetrics();
  const { data: goalsData } = useClientGoals(clientId);
  const createGoal = useCreateGoal(clientId);
  const updateGoal = useUpdateGoal(clientId);

  // Metriche gia' usate da obiettivi attivi (disabilitate nel dropdown)
  const usedMetricIds = useMemo(() => {
    if (!goalsData) return new Set<number>();
    return new Set(
      goalsData.items
        .filter((g) => g.stato === "attivo")
        .map((g) => g.id_metrica)
    );
  }, [goalsData]);

  // ── Form state ──
  const [metricId, setMetricId] = useState<string>("");
  const [direzione, setDirezione] = useState<GoalDirection>("diminuire");
  const [valoreTarget, setValoreTarget] = useState<string>("");
  const [dataInizio, setDataInizio] = useState<Date | undefined>(new Date());
  const [dataScadenza, setDataScadenza] = useState<Date | undefined>();
  const [priorita, setPriorita] = useState<string>("3");
  const [note, setNote] = useState<string>("");

  // ── Sync state on open/goal change ──
  useEffect(() => {
    if (!open) return;

    if (goal) {
      setMetricId(String(goal.id_metrica));
      setDirezione(goal.direzione);
      setValoreTarget(goal.valore_target !== null ? String(goal.valore_target) : "");
      setDataInizio(new Date(goal.data_inizio));
      setDataScadenza(goal.data_scadenza ? new Date(goal.data_scadenza) : undefined);
      setPriorita(String(goal.priorita));
      setNote(goal.note ?? "");
    } else {
      setMetricId("");
      setDirezione("diminuire");
      setValoreTarget("");
      setDataInizio(new Date());
      setDataScadenza(undefined);
      setPriorita("3");
      setNote("");
    }
  }, [open, goal]);

  // ── Metriche raggruppate per categoria ──
  const groupedMetrics = useMemo(() => {
    if (!metrics) return [];
    const groups = new Map<string, Metric[]>();
    for (const m of metrics) {
      if (!groups.has(m.categoria)) groups.set(m.categoria, []);
      groups.get(m.categoria)!.push(m);
    }
    return [...groups.entries()];
  }, [metrics]);

  // ── Selected metric info ──
  const selectedMetric = useMemo(() => {
    if (!metrics || !metricId) return null;
    return metrics.find((m) => m.id === parseInt(metricId, 10)) ?? null;
  }, [metrics, metricId]);

  const baselineValue = useMemo(() => {
    if (!metricId || !currentValues) return null;
    return currentValues.get(parseInt(metricId, 10)) ?? null;
  }, [metricId, currentValues]);

  // ── Submit ──
  const handleSubmit = () => {
    if (!metricId || !dataInizio) return;

    const dataInizioStr = toISOLocal(dataInizio).slice(0, 10);
    const dataScadenzaStr = dataScadenza
      ? toISOLocal(dataScadenza).slice(0, 10)
      : null;
    const targetNum = valoreTarget ? parseFloat(valoreTarget) : null;
    const priNum = parseInt(priorita, 10);

    if (isEdit && goal) {
      updateGoal.mutate(
        {
          goalId: goal.id,
          payload: {
            direzione,
            valore_target: targetNum,
            data_scadenza: dataScadenzaStr,
            priorita: priNum,
            note: note || null,
          },
        },
        { onSuccess: () => onOpenChange(false) }
      );
    } else {
      createGoal.mutate(
        {
          id_metrica: parseInt(metricId, 10),
          direzione,
          valore_target: targetNum,
          data_inizio: dataInizioStr,
          data_scadenza: dataScadenzaStr,
          priorita: priNum,
          note: note || null,
        },
        { onSuccess: () => onOpenChange(false) }
      );
    }
  };

  const isPending = createGoal.isPending || updateGoal.isPending;
  const canSubmit = !!metricId && !!dataInizio && !isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-teal-500" />
            {isEdit ? "Modifica Obiettivo" : "Nuovo Obiettivo"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Modifica target, scadenza e priorita' dell'obiettivo"
              : "Seleziona una metrica e definisci il tuo obiettivo"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Metrica */}
          <div className="space-y-1.5">
            <Label>Metrica</Label>
            <Select
              value={metricId}
              onValueChange={setMetricId}
              disabled={isEdit}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona metrica..." />
              </SelectTrigger>
              <SelectContent position="popper">
                {groupedMetrics.map(([cat, items]) => (
                  <div key={cat}>
                    <div className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      {METRIC_CATEGORY_LABELS[cat as MetricCategory] ?? cat}
                    </div>
                    {items.map((m) => {
                      const isUsed = !isEdit && usedMetricIds.has(m.id);
                      return (
                        <SelectItem
                          key={m.id}
                          value={String(m.id)}
                          disabled={isUsed}
                        >
                          {m.nome} ({m.unita_misura})
                          {isUsed && " — obiettivo attivo"}
                        </SelectItem>
                      );
                    })}
                  </div>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Baseline (read-only) */}
          {selectedMetric && (
            <div className="rounded-lg bg-muted/40 px-3 py-2">
              <span className="text-xs text-muted-foreground">
                Valore attuale:{" "}
              </span>
              <span className="text-sm font-semibold tabular-nums">
                {baselineValue !== null
                  ? `${baselineValue} ${selectedMetric.unita_misura}`
                  : "Nessuna misurazione"}
              </span>
            </div>
          )}

          {/* Direzione */}
          <div className="space-y-1.5">
            <Label>Direzione</Label>
            <div className="grid grid-cols-3 gap-2">
              {DIRECTION_OPTIONS.map((opt) => {
                const Icon = opt.icon;
                const isActive = direzione === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setDirezione(opt.value)}
                    className={`flex items-center justify-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition-all ${
                      isActive
                        ? "border-teal-500 bg-teal-50 text-teal-700 dark:bg-teal-950/30 dark:text-teal-300"
                        : "border-border bg-background text-muted-foreground hover:bg-muted/50"
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Target */}
          <div className="space-y-1.5">
            <Label>
              Valore target{" "}
              <span className="text-muted-foreground font-normal">
                (opzionale)
              </span>
            </Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                step="0.1"
                value={valoreTarget}
                onChange={(e) => setValoreTarget(e.target.value)}
                placeholder="Es. 75"
                className="tabular-nums"
              />
              {selectedMetric && (
                <span className="text-sm text-muted-foreground whitespace-nowrap">
                  {selectedMetric.unita_misura}
                </span>
              )}
            </div>
          </div>

          {/* Date */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Data inizio</Label>
              <DatePicker
                value={dataInizio}
                onChange={setDataInizio}
                placeholder="Inizio..."
              />
            </div>
            <div className="space-y-1.5">
              <Label>
                Scadenza{" "}
                <span className="text-muted-foreground font-normal">
                  (opz.)
                </span>
              </Label>
              <DatePicker
                value={dataScadenza}
                onChange={setDataScadenza}
                placeholder="Nessuna scadenza"
              />
            </div>
          </div>

          {/* Priorita' */}
          <div className="space-y-1.5">
            <Label>Priorita'</Label>
            <Select value={priorita} onValueChange={setPriorita}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent position="popper">
                <SelectItem value="1">1 — Massima</SelectItem>
                <SelectItem value="2">2 — Alta</SelectItem>
                <SelectItem value="3">3 — Media</SelectItem>
                <SelectItem value="4">4 — Bassa</SelectItem>
                <SelectItem value="5">5 — Minima</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Note */}
          <div className="space-y-1.5">
            <Label>
              Note{" "}
              <span className="text-muted-foreground font-normal">
                (opzionale)
              </span>
            </Label>
            <Textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Motivazione, contesto..."
              rows={2}
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isPending}
          >
            Annulla
          </Button>
          <Button onClick={handleSubmit} disabled={!canSubmit}>
            {isPending
              ? "Salvataggio..."
              : isEdit
                ? "Salva"
                : "Crea Obiettivo"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
