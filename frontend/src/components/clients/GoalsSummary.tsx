// src/components/clients/GoalsSummary.tsx
"use client";

/**
 * GoalsSummary — Card obiettivi attivi + sezione raggiunti collapsibile.
 *
 * Mostra:
 * - Contatore X/3 obiettivi attivi
 * - Card per ogni obiettivo attivo (nome metrica + direzione + progress bar)
 * - Quick actions: Modifica / Abbandona / Elimina (NO Completa — auto dal backend)
 * - Sezione "Raggiunti" collapsibile con badge "Automatico" e bottone "Riattiva"
 *
 * Posizionato in ProgressiTab tra header e KPI cards.
 */

import { useMemo, useState } from "react";
import { differenceInDays } from "date-fns";
import {
  ArrowDown,
  ArrowUp,
  ChevronDown,
  Equal,
  Pencil,
  RotateCcw,
  Target,
  Trash2,
  X,
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
import { GoalFormDialog } from "@/components/clients/GoalFormDialog";

import { useClientGoals, useUpdateGoal, useDeleteGoal } from "@/hooks/useGoals";
import type { ClientGoal } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

interface GoalsSummaryProps {
  clientId: number;
  /** Valori correnti dalla misurazione piu' recente — per il form dialog */
  currentValues?: Map<number, number>;
}

// Colore progress bar basato su tendenza
function getProgressColor(goal: ClientGoal): string {
  if (goal.stato === "raggiunto") return "bg-emerald-500";
  if (goal.stato === "abbandonato") return "bg-muted-foreground/30";

  const trend = goal.progresso.tendenza_positiva;
  if (trend === null) return "bg-teal-500";
  if (trend === true) return "bg-emerald-500";
  return "bg-rose-500";
}

// Icona direzione
function DirectionIcon({ direzione }: { direzione: string }) {
  if (direzione === "aumentare")
    return <ArrowUp className="h-3.5 w-3.5 text-emerald-500" />;
  if (direzione === "diminuire")
    return <ArrowDown className="h-3.5 w-3.5 text-blue-500" />;
  return <Equal className="h-3.5 w-3.5 text-amber-500" />;
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function GoalsSummary({ clientId, currentValues }: GoalsSummaryProps) {
  const { data: goalsData } = useClientGoals(clientId);
  const updateGoal = useUpdateGoal(clientId);
  const deleteGoal = useDeleteGoal(clientId);

  const [formOpen, setFormOpen] = useState(false);
  const [editGoal, setEditGoal] = useState<ClientGoal | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [showRaggiunti, setShowRaggiunti] = useState(false);

  // Filtra attivi e raggiunti
  const activeGoals = useMemo(
    () => goalsData?.items.filter((g) => g.stato === "attivo") ?? [],
    [goalsData]
  );

  const completedGoals = useMemo(
    () => goalsData?.items.filter((g) => g.stato === "raggiunto") ?? [],
    [goalsData]
  );

  const handleEdit = (goal: ClientGoal) => {
    setEditGoal(goal);
    setFormOpen(true);
  };

  const handleAbandon = (goalId: number) => {
    updateGoal.mutate({ goalId, payload: { stato: "abbandonato" } });
  };

  const handleReactivate = (goalId: number) => {
    updateGoal.mutate({ goalId, payload: { stato: "attivo" } });
  };

  const handleDeleteConfirm = () => {
    if (deleteId !== null) {
      deleteGoal.mutate(deleteId, { onSuccess: () => setDeleteId(null) });
    }
  };

  // Niente da mostrare
  if (activeGoals.length === 0 && completedGoals.length === 0) {
    return null;
  }

  return (
    <>
      <div className="space-y-3">
        {/* Header con contatore */}
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-teal-500" />
          <span className="text-sm font-semibold">Obiettivi</span>
          <span className="rounded-full bg-teal-50 px-2 py-0.5 text-[10px] font-semibold text-teal-700 dark:bg-teal-950/30 dark:text-teal-400">
            {activeGoals.length}/3
          </span>
        </div>

        {/* Goal cards attivi */}
        {activeGoals.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {activeGoals.map((goal) => (
              <GoalCard
                key={goal.id}
                goal={goal}
                onEdit={() => handleEdit(goal)}
                onAbandon={() => handleAbandon(goal.id)}
                onDelete={() => setDeleteId(goal.id)}
              />
            ))}
          </div>
        )}

        {/* Sezione Raggiunti (collapsibile) */}
        {completedGoals.length > 0 && (
          <div>
            <button
              onClick={() => setShowRaggiunti((prev) => !prev)}
              className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              <ChevronDown
                className={`h-3.5 w-3.5 transition-transform duration-200 ${
                  showRaggiunti ? "rotate-180" : ""
                }`}
              />
              {completedGoals.length} {completedGoals.length === 1 ? "raggiunto" : "raggiunti"}
            </button>

            {showRaggiunti && (
              <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {completedGoals.map((goal) => (
                  <CompletedGoalCard
                    key={goal.id}
                    goal={goal}
                    onReactivate={() => handleReactivate(goal.id)}
                    onDelete={() => setDeleteId(goal.id)}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Form dialog (solo edit) */}
      <GoalFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        clientId={clientId}
        goal={editGoal}
        currentValues={currentValues}
      />

      {/* Delete confirm */}
      <AlertDialog
        open={deleteId !== null}
        onOpenChange={(open) => !open && setDeleteId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Elimina obiettivo</AlertDialogTitle>
            <AlertDialogDescription>
              Sei sicuro di voler eliminare questo obiettivo?
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

// ════════════════════════════════════════════════════════════
// GOAL CARD (attivo)
// ════════════════════════════════════════════════════════════

function GoalCard({
  goal,
  onEdit,
  onAbandon,
  onDelete,
}: {
  goal: ClientGoal;
  onEdit: () => void;
  onAbandon: () => void;
  onDelete: () => void;
}) {
  const { progresso } = goal;
  const progressColor = getProgressColor(goal);
  const progressValue = progresso.percentuale_progresso ?? 0;

  // Countdown scadenza
  const deadlineText = useMemo(() => {
    if (!goal.data_scadenza) return null;
    const days = differenceInDays(new Date(goal.data_scadenza), new Date());
    if (days < 0) return `Scaduto da ${Math.abs(days)} giorni`;
    if (days === 0) return "Scade oggi";
    return `${days} ${days === 1 ? "giorno" : "giorni"} rimasti`;
  }, [goal.data_scadenza]);

  const deadlineUrgent = useMemo(() => {
    if (!goal.data_scadenza) return false;
    return differenceInDays(new Date(goal.data_scadenza), new Date()) < 0;
  }, [goal.data_scadenza]);

  return (
    <Card className="border-l-4 border-l-teal-500 bg-gradient-to-br from-background to-muted/20 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
      <CardContent className="p-4 space-y-3">
        {/* Header: nome + direzione */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <DirectionIcon direzione={goal.direzione} />
            <span className="text-sm font-semibold truncate">
              {goal.nome_metrica}
            </span>
          </div>
          {/* Quick actions — NO Completa (auto dal backend) */}
          <div className="flex items-center gap-0.5 shrink-0" data-print-hide>
            <button
              onClick={onEdit}
              title="Modifica"
              className="rounded-md p-1 text-muted-foreground hover:bg-muted"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={onAbandon}
              title="Abbandona"
              className="rounded-md p-1 text-muted-foreground hover:bg-amber-50 hover:text-amber-600 dark:hover:bg-amber-950/30"
            >
              <X className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={onDelete}
              title="Elimina"
              className="rounded-md p-1 text-muted-foreground hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/30"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Values: baseline → corrente → target */}
        <div className="flex items-baseline gap-1 text-xs text-muted-foreground">
          {goal.valore_baseline !== null && (
            <>
              <span className="tabular-nums">
                {goal.valore_baseline} {goal.unita_misura}
              </span>
              <span>→</span>
            </>
          )}
          {progresso.valore_corrente !== null ? (
            <span className="text-sm font-bold text-foreground tabular-nums">
              {progresso.valore_corrente} {goal.unita_misura}
            </span>
          ) : (
            <span className="text-sm text-muted-foreground">—</span>
          )}
          {goal.valore_target !== null && (
            <>
              <span>→</span>
              <span className="tabular-nums font-medium">
                {goal.valore_target} {goal.unita_misura}
              </span>
            </>
          )}
        </div>

        {/* Progress bar */}
        {goal.valore_target !== null && (
          <div className="space-y-1">
            <div className="relative h-2 w-full overflow-hidden rounded-full bg-primary/10">
              <div
                className={`h-full rounded-full transition-all duration-500 ${progressColor}`}
                style={{ width: `${Math.min(100, progressValue)}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-[10px] text-muted-foreground">
              <span className="tabular-nums">
                {progressValue.toFixed(0)}%
              </span>
              {progresso.delta_da_baseline !== null && (
                <span className="tabular-nums">
                  {progresso.delta_da_baseline > 0 ? "+" : ""}
                  {progresso.delta_da_baseline} {goal.unita_misura}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Delta badge (when no target, just show trend) */}
        {goal.valore_target === null && progresso.delta_da_baseline !== null && (
          <div className="flex items-center gap-1.5">
            <span
              className={`inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[10px] font-semibold tabular-nums ${
                progresso.tendenza_positiva
                  ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400"
                  : "bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400"
              }`}
            >
              {progresso.delta_da_baseline > 0 ? "+" : ""}
              {progresso.delta_da_baseline} {goal.unita_misura}
            </span>
          </div>
        )}

        {/* Deadline */}
        {deadlineText && (
          <span
            className={`text-[10px] ${
              deadlineUrgent ? "text-rose-500 font-medium" : "text-muted-foreground"
            }`}
          >
            {deadlineText}
          </span>
        )}
      </CardContent>
    </Card>
  );
}

// ════════════════════════════════════════════════════════════
// COMPLETED GOAL CARD
// ════════════════════════════════════════════════════════════

function CompletedGoalCard({
  goal,
  onReactivate,
  onDelete,
}: {
  goal: ClientGoal;
  onReactivate: () => void;
  onDelete: () => void;
}) {
  return (
    <Card className="border-l-4 border-l-emerald-400 bg-muted/20 opacity-80">
      <CardContent className="p-3 space-y-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <DirectionIcon direzione={goal.direzione} />
            <span className="text-xs font-semibold truncate text-muted-foreground">
              {goal.nome_metrica}
            </span>
          </div>
          <div className="flex items-center gap-1 shrink-0" data-print-hide>
            {goal.completato_automaticamente && (
              <span className="rounded-full bg-teal-50 px-1.5 py-0.5 text-[9px] font-medium text-teal-600 dark:bg-teal-950/30 dark:text-teal-400">
                Automatico
              </span>
            )}
            <button
              onClick={onReactivate}
              title="Riattiva"
              className="rounded-md p-1 text-muted-foreground hover:bg-teal-50 hover:text-teal-600 dark:hover:bg-teal-950/30"
            >
              <RotateCcw className="h-3 w-3" />
            </button>
            <button
              onClick={onDelete}
              title="Elimina"
              className="rounded-md p-1 text-muted-foreground hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/30"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        </div>

        {/* Valori finali */}
        <div className="flex items-baseline gap-1 text-[10px] text-muted-foreground">
          {goal.valore_baseline !== null && (
            <>
              <span className="tabular-nums">{goal.valore_baseline}</span>
              <span>→</span>
            </>
          )}
          {goal.progresso.valore_corrente !== null && (
            <span className="font-semibold text-emerald-600 dark:text-emerald-400 tabular-nums">
              {goal.progresso.valore_corrente}
            </span>
          )}
          {goal.valore_target !== null && (
            <>
              <span>/ {goal.valore_target}</span>
            </>
          )}
          <span>{goal.unita_misura}</span>
        </div>
      </CardContent>
    </Card>
  );
}
