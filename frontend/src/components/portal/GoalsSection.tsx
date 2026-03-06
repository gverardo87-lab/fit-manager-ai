"use client";

/**
 * GoalsSection — Obiettivi attivi con progress, velocity, proiezione + GoalFormDialog inline.
 */

import { useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { ChevronDown, Target, Plus, TrendingUp, TrendingDown, Minus, Award } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { GoalFormDialog } from "@/components/clients/GoalFormDialog";
import type { ClientGoal, Measurement, Metric } from "@/types/api";

interface GoalsSectionProps {
  clientId: number;
  goals: ClientGoal[];
  latestMeasurement: Measurement | null;
  metrics: Metric[];
  sesso: string | null;
  dataNascita: string | null;
}

function getProgressColor(pct: number | null): string {
  if (pct === null) return "bg-zinc-300 dark:bg-zinc-600";
  if (pct >= 80) return "bg-emerald-500";
  if (pct >= 40) return "bg-amber-500";
  return "bg-red-500";
}

function getTrendIcon(positive: boolean | null) {
  if (positive === true) return <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />;
  if (positive === false) return <TrendingDown className="h-3.5 w-3.5 text-red-500" />;
  return <Minus className="h-3.5 w-3.5 text-zinc-400" />;
}

export function GoalsSection({
  clientId,
  goals,
  latestMeasurement,
  metrics,
  sesso,
  dataNascita,
}: GoalsSectionProps) {
  const [open, setOpen] = useState(true);
  const [goalDialogOpen, setGoalDialogOpen] = useState(false);
  const [editGoal, setEditGoal] = useState<ClientGoal | null>(null);
  const [showCompleted, setShowCompleted] = useState(false);

  const activeGoals = useMemo(() => goals.filter((g) => g.stato === "attivo"), [goals]);
  const completedGoals = useMemo(() => goals.filter((g) => g.stato === "raggiunto"), [goals]);
  const hasGoals = goals.length > 0;

  // Current values for GoalFormDialog
  const currentValues = useMemo(() => {
    const map = new Map<number, number>();
    if (!latestMeasurement) return map;
    for (const v of latestMeasurement.valori) {
      map.set(v.id_metrica, v.valore);
    }
    return map;
  }, [latestMeasurement]);

  const handleNewGoal = useCallback(() => {
    setEditGoal(null);
    setGoalDialogOpen(true);
  }, []);

  const handleEditGoal = useCallback((goal: ClientGoal) => {
    setEditGoal(goal);
    setGoalDialogOpen(true);
  }, []);

  const borderColor = activeGoals.length === 0
    ? "border-l-zinc-300"
    : activeGoals.some((g) => g.progresso.tendenza_positiva === true)
      ? "border-l-emerald-500"
      : "border-l-amber-500";

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className={`rounded-xl border border-l-4 ${borderColor} bg-white shadow-sm dark:bg-zinc-900`}>
        <CollapsibleTrigger asChild>
          <button type="button" className="flex w-full items-center justify-between p-4 text-left">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-emerald-500" />
              <h2 className="text-sm font-semibold">Obiettivi</h2>
              {activeGoals.length > 0 && (
                <Badge variant="outline" className="text-[10px] tabular-nums">
                  {activeGoals.length} attiv{activeGoals.length === 1 ? "o" : "i"}
                </Badge>
              )}
            </div>
            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="space-y-4 border-t px-4 pb-4 pt-3">
            {!hasGoals && (
              <div className="rounded-lg border border-dashed p-6 text-center">
                <p className="text-sm text-muted-foreground">
                  Nessun obiettivo definito per questo cliente
                </p>
              </div>
            )}

            {/* Active goals */}
            {activeGoals.length > 0 && (
              <div className="space-y-3">
                {activeGoals.map((goal) => {
                  const pct = goal.progresso.percentuale_progresso;
                  const velocity = goal.progresso.velocita_settimanale;

                  return (
                    <div key={goal.id} className="rounded-lg border p-3">
                      <div className="flex items-start justify-between">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            {getTrendIcon(goal.progresso.tendenza_positiva)}
                            <p className="text-xs font-semibold">{goal.nome_metrica}</p>
                            <Badge variant="outline" className="text-[10px]">
                              {goal.tipo_obiettivo}
                            </Badge>
                          </div>

                          {/* Values */}
                          <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-xs">
                            {goal.valore_baseline !== null && (
                              <span className="text-muted-foreground">
                                Base: <span className="font-medium tabular-nums">{goal.valore_baseline} {goal.unita_misura}</span>
                              </span>
                            )}
                            {goal.progresso.valore_corrente !== null && (
                              <span className="text-muted-foreground">
                                Attuale: <span className="font-medium tabular-nums">{goal.progresso.valore_corrente} {goal.unita_misura}</span>
                              </span>
                            )}
                            {goal.valore_target !== null && (
                              <span className="text-muted-foreground">
                                Target: <span className="font-medium tabular-nums">{goal.valore_target} {goal.unita_misura}</span>
                              </span>
                            )}
                          </div>
                        </div>

                        <Button size="sm" variant="ghost" className="text-[10px]" onClick={() => handleEditGoal(goal)}>
                          Modifica
                        </Button>
                      </div>

                      {/* Progress bar */}
                      {pct !== null && (
                        <div className="mt-2">
                          <div className="flex items-center justify-between text-[10px]">
                            <span className="text-muted-foreground">Progresso</span>
                            <span className="font-bold tabular-nums">{Math.round(pct)}%</span>
                          </div>
                          <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${getProgressColor(pct)}`}
                              style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Velocity */}
                      {velocity !== null && velocity !== 0 && (
                        <p className="mt-1 text-[10px] text-muted-foreground">
                          Velocità: <span className="font-medium tabular-nums">{velocity > 0 ? "+" : ""}{velocity.toFixed(2)} {goal.unita_misura}/sett</span>
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Completed goals */}
            {completedGoals.length > 0 && (
              <div>
                <button
                  type="button"
                  className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
                  onClick={() => setShowCompleted(!showCompleted)}
                >
                  <Award className="h-3.5 w-3.5 text-emerald-500" />
                  {completedGoals.length} obiettiv{completedGoals.length === 1 ? "o" : "i"} raggiunt{completedGoals.length === 1 ? "o" : "i"}
                  <ChevronDown className={`h-3 w-3 transition-transform ${showCompleted ? "rotate-180" : ""}`} />
                </button>
                {showCompleted && (
                  <div className="mt-2 space-y-2">
                    {completedGoals.map((goal) => (
                      <div key={goal.id} className="flex items-center justify-between rounded-lg border bg-emerald-50/50 p-2 dark:bg-emerald-950/10">
                        <div className="flex items-center gap-2">
                          <Award className="h-3.5 w-3.5 text-emerald-500" />
                          <span className="text-xs font-medium">{goal.nome_metrica}</span>
                        </div>
                        {goal.completed_at && (
                          <span className="text-[10px] text-muted-foreground">
                            {new Date(goal.completed_at).toLocaleDateString("it-IT", { day: "numeric", month: "short" })}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* CTAs */}
            <div className="flex flex-wrap justify-end gap-2">
              <Link href={`/clienti/${clientId}/progressi`}>
                <Button size="sm" variant="outline" className="gap-1.5">
                  <TrendingUp className="h-3.5 w-3.5" />
                  Vedi Progressi
                </Button>
              </Link>
              <Button size="sm" variant="outline" className="gap-1.5" onClick={handleNewGoal}>
                <Plus className="h-3.5 w-3.5" />
                Nuovo Obiettivo
              </Button>
            </div>
          </div>
        </CollapsibleContent>
      </div>

      {/* GoalFormDialog inline */}
      <GoalFormDialog
        open={goalDialogOpen}
        onOpenChange={setGoalDialogOpen}
        clientId={clientId}
        goal={editGoal}
        currentValues={currentValues}
        sesso={sesso}
        dataNascita={dataNascita}
      />
    </Collapsible>
  );
}
