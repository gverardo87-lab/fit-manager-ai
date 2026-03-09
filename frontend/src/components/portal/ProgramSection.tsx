"use client";

/**
 * ProgramSection — Programma attivo + compliance + safety summary.
 */

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, Dumbbell, Plus, Eye, ClipboardList, ShieldAlert, ShieldCheck, ShieldOff } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { getProgramStatus, STATUS_LABELS, STATUS_COLORS, getComplianceColor, getComplianceTextColor } from "@/lib/workout-monitoring";
import type { WorkoutPlan, WorkoutLog, SafetyMapResponse } from "@/types/api";

interface ProgramSectionProps {
  workouts: WorkoutPlan[];
  workoutLogs: WorkoutLog[];
  safetyData: SafetyMapResponse | null;
  clientId: number;
  compliancePct: number | null;
}

function countSafety(
  sessions: WorkoutPlan["sessioni"],
  entries: SafetyMapResponse["entries"] | null,
): { avoid: number; modify: number; caution: number } {
  if (!entries) return { avoid: 0, modify: 0, caution: 0 };
  let avoid = 0, modify = 0, caution = 0;
  const counted = new Set<number>();

  for (const session of sessions) {
    for (const ex of session.esercizi) {
      if (counted.has(ex.id_esercizio)) continue;
      counted.add(ex.id_esercizio);
      const entry = entries[ex.id_esercizio];
      if (!entry) continue;
      if (entry.severity === "avoid") avoid++;
      else if (entry.severity === "modify") modify++;
      else caution++;
    }
  }

  return { avoid, modify, caution };
}

export function ProgramSection({
  workouts,
  workoutLogs,
  safetyData,
  clientId,
  compliancePct,
}: ProgramSectionProps) {
  const [open, setOpen] = useState(true);

  // Active program
  const activeProgram = workouts.find((w) => getProgramStatus(w) === "attivo") ?? null;
  const hasPrograms = workouts.length > 0;

  // Safety breakdown
  const safety = activeProgram
    ? countSafety(activeProgram.sessioni, safetyData?.entries ?? null)
    : { avoid: 0, modify: 0, caution: 0 };

  // Completed logs for active program
  const activeLogs = activeProgram
    ? workoutLogs.filter((l) => l.id_scheda === activeProgram.id).length
    : 0;

  const borderColor = !hasPrograms
    ? "border-l-zinc-300"
    : compliancePct !== null && compliancePct >= 80
      ? "border-l-emerald-500"
      : compliancePct !== null && compliancePct >= 50
        ? "border-l-amber-500"
        : "border-l-teal-500";

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className={`rounded-xl border border-l-4 ${borderColor} bg-white shadow-sm dark:bg-zinc-900`}>
        <CollapsibleTrigger asChild>
          <button type="button" className="flex w-full items-center justify-between p-4 text-left">
            <div className="flex items-center gap-2">
              <Dumbbell className="h-4 w-4 text-teal-500" />
              <h2 className="text-sm font-semibold">Programma Attivo</h2>
              {activeProgram && (
                <Badge variant="outline" className={`text-[10px] ${STATUS_COLORS.attivo}`}>
                  {STATUS_LABELS.attivo}
                </Badge>
              )}
            </div>
            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="space-y-4 border-t px-4 pb-4 pt-3">
            {!hasPrograms && (
              <div className="rounded-lg border border-dashed p-6 text-center">
                <p className="text-sm text-muted-foreground">
                  Nessun programma di allenamento assegnato
                </p>
              </div>
            )}

            {/* Active program card */}
            {activeProgram && (
              <div className="rounded-lg border p-3">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-semibold">{activeProgram.nome}</p>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      <Badge variant="outline" className="text-[10px]">
                        {activeProgram.obiettivo}
                      </Badge>
                      <Badge variant="outline" className="text-[10px]">
                        {activeProgram.livello}
                      </Badge>
                      <Badge variant="outline" className="text-[10px]">
                        {activeProgram.sessioni_per_settimana} sess/sett
                      </Badge>
                    </div>
                  </div>
                  <Link href={`/schede/${activeProgram.id}?from=monitoraggio-${clientId}`}>
                    <Button size="sm" variant="ghost" className="gap-1 text-xs">
                      <Eye className="h-3.5 w-3.5" />
                      Vedi
                    </Button>
                  </Link>
                </div>

                {/* Date range */}
                {activeProgram.data_inizio && activeProgram.data_fine && (
                  <p className="mt-2 text-[10px] text-muted-foreground">
                    {new Date(activeProgram.data_inizio + "T00:00:00").toLocaleDateString("it-IT", { day: "numeric", month: "short" })}
                    {" — "}
                    {new Date(activeProgram.data_fine + "T00:00:00").toLocaleDateString("it-IT", { day: "numeric", month: "short", year: "numeric" })}
                  </p>
                )}
              </div>
            )}

            {/* Compliance bar */}
            {compliancePct !== null && (
              <div className="rounded-lg border p-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold">Aderenza</p>
                  <span className={`text-sm font-extrabold tabular-nums ${getComplianceTextColor(compliancePct)}`}>
                    {compliancePct}%
                  </span>
                </div>
                <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${getComplianceColor(compliancePct)}`}
                    style={{ width: `${compliancePct}%` }}
                  />
                </div>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  {activeLogs} sessioni registrate
                </p>
              </div>
            )}

            {/* Safety summary */}
            {safetyData && safetyData.condition_count > 0 && activeProgram && (
              <div className="rounded-lg border p-3">
                <p className="mb-2 text-xs font-semibold">Compatibilità Clinica</p>
                <div className="flex flex-wrap gap-3">
                  {safety.avoid > 0 && (
                    <div className="flex items-center gap-1.5">
                      <ShieldOff className="h-3.5 w-3.5 text-red-500" />
                      <span className="text-xs font-medium text-red-600 dark:text-red-400">
                        {safety.avoid} da evitare
                      </span>
                    </div>
                  )}
                  {safety.modify > 0 && (
                    <div className="flex items-center gap-1.5">
                      <ShieldAlert className="h-3.5 w-3.5 text-amber-500" />
                      <span className="text-xs font-medium text-amber-600 dark:text-amber-400">
                        {safety.modify} da adattare
                      </span>
                    </div>
                  )}
                  {safety.caution > 0 && (
                    <div className="flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5 text-blue-500" />
                      <span className="text-xs font-medium text-blue-600 dark:text-blue-400">
                        {safety.caution} cautela
                      </span>
                    </div>
                  )}
                  {safety.avoid === 0 && safety.modify === 0 && safety.caution === 0 && (
                    <div className="flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
                      <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
                        Nessun conflitto rilevato
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Other programs summary */}
            {workouts.length > 1 && (
              <div className="rounded-lg border bg-zinc-50/50 p-3 dark:bg-zinc-900/50">
                <p className="text-xs text-muted-foreground">
                  {workouts.length - (activeProgram ? 1 : 0)} altr{workouts.length - (activeProgram ? 1 : 0) === 1 ? "a" : "e"} schede
                  {" "}({workouts.filter((w) => getProgramStatus(w) === "completato").length} completate,{" "}
                  {workouts.filter((w) => getProgramStatus(w) === "da_attivare").length} da attivare)
                </p>
              </div>
            )}

            {/* CTAs */}
            <div className="flex flex-wrap justify-end gap-2">
              <Link href={`/allenamenti?idCliente=${clientId}&from=monitoraggio-${clientId}`}>
                <Button size="sm" variant="outline" className="gap-1.5">
                  <ClipboardList className="h-3.5 w-3.5" />
                  Vedi aderenza
                </Button>
              </Link>
              <Link href={`/clienti/${clientId}?tab=schede&startScheda=1`}>
                <Button size="sm" variant="outline" className="gap-1.5">
                  <Plus className="h-3.5 w-3.5" />
                  Nuova Scheda
                </Button>
              </Link>
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
