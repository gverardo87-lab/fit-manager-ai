// src/components/nutrition/WeeklyPlanGrid.tsx
"use client";

/**
 * Griglia settimanale piano alimentare.
 *
 * Layout: righe = tipo pasto, colonne = giorni della settimana.
 * Ogni cella mostra macro del pasto se esiste, oppure "+" per aggiungere.
 * Footer: totali giornalieri. Ultima colonna: aggiungi nuovo giorno.
 */

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAddMeal } from "@/hooks/useNutrition";
import type { NutritionPlanDetail, PlanMealDetail } from "@/types/api";
import { GIORNO_OPTIONS } from "@/types/api";

// ── Costanti locali ───────────────────────────────────────────────────────

const MEAL_SLOTS = [
  { value: "COLAZIONE", label: "Colazione", short: "Cola." },
  { value: "SPUNTINO_MATTINA", label: "Spuntino matt.", short: "Spunt." },
  { value: "PRANZO", label: "Pranzo", short: "Pranzo" },
  { value: "SPUNTINO_POMERIGGIO", label: "Merenda", short: "Merenda" },
  { value: "CENA", label: "Cena", short: "Cena" },
  { value: "PRE_WORKOUT", label: "Pre-workout", short: "Pre" },
  { value: "POST_WORKOUT", label: "Post-workout", short: "Post" },
];

// ── Props ─────────────────────────────────────────────────────────────────

interface WeeklyPlanGridProps {
  plan: NutritionPlanDetail;
  planId: number;
  onSelectDay: (giorno: number) => void;
  activeDay?: number;
}

// ── Helpers ───────────────────────────────────────────────────────────────

function getMealForCell(
  pasti: PlanMealDetail[],
  giorno: number,
  tipoPasto: string
): PlanMealDetail | undefined {
  return pasti.find(
    (m) => m.giorno_settimana === giorno && m.tipo_pasto === tipoPasto
  );
}

function getDailyTotals(pasti: PlanMealDetail[], giorno: number) {
  const meals = pasti.filter((m) => m.giorno_settimana === giorno);
  return {
    kcal: meals.reduce((s, m) => s + m.totale_kcal, 0),
    p: meals.reduce((s, m) => s + m.totale_proteine_g, 0),
    c: meals.reduce((s, m) => s + m.totale_carboidrati_g, 0),
    g: meals.reduce((s, m) => s + m.totale_grassi_g, 0),
  };
}

// ── Componente principale ─────────────────────────────────────────────────

export function WeeklyPlanGrid({
  plan,
  planId,
  onSelectDay,
  activeDay,
}: WeeklyPlanGridProps) {
  const [addDayOpen, setAddDayOpen] = useState(false);
  const addMeal = useAddMeal();

  const pasti = plan.pasti ?? [];

  // Giorni presenti nel piano, sempre incluso 0 (ogni giorno)
  const presentDays = Array.from(
    new Set([0, ...pasti.map((m) => m.giorno_settimana)])
  ).sort((a, b) => a - b);

  // Giorni disponibili da aggiungere (1-7 non ancora presenti)
  const availableDays = GIORNO_OPTIONS.filter(
    (g) => g.value >= 1 && !presentDays.includes(g.value)
  );

  const handleAddCellMeal = (giorno: number, tipoPasto: string) => {
    const ordine = pasti.filter((m) => m.giorno_settimana === giorno).length;
    addMeal.mutate({
      planId,
      payload: { giorno_settimana: giorno, tipo_pasto: tipoPasto, ordine },
    });
  };

  const handleAddDay = (giorno: number) => {
    addMeal.mutate({
      planId,
      payload: { giorno_settimana: giorno, tipo_pasto: "COLAZIONE", ordine: 0 },
    });
    setAddDayOpen(false);
  };

  return (
    <div className="overflow-x-auto rounded-lg border bg-background">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/30">
            {/* Intestazione colonna sinistra */}
            <th className="sticky left-0 z-10 w-32 bg-muted/30 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Pasto
            </th>
            {/* Intestazioni giorni */}
            {presentDays.map((giorno) => {
              const label =
                GIORNO_OPTIONS.find((g) => g.value === giorno)?.label ?? "—";
              const isActive = activeDay === giorno;
              return (
                <th
                  key={giorno}
                  className={`min-w-[110px] cursor-pointer px-2 py-2 text-center text-xs font-semibold transition-colors hover:bg-muted/50 ${
                    isActive
                      ? "text-primary underline underline-offset-2"
                      : "text-muted-foreground"
                  }`}
                  onClick={() => onSelectDay(giorno)}
                >
                  {label}
                </th>
              );
            })}
            {/* Colonna aggiungi giorno */}
            <th className="w-12 px-2 py-2 text-center">
              {availableDays.length > 0 && (
                <div className="relative inline-block">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 rounded-full"
                    onClick={() => setAddDayOpen((v) => !v)}
                    title="Aggiungi giorno"
                  >
                    <Plus className="h-3.5 w-3.5" />
                  </Button>
                  {addDayOpen && (
                    <div className="absolute right-0 top-8 z-20 min-w-[130px] rounded-lg border bg-popover shadow-md">
                      <p className="px-3 py-1.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                        Aggiungi giorno
                      </p>
                      {availableDays.map((opt) => (
                        <button
                          key={opt.value}
                          onClick={() => handleAddDay(opt.value)}
                          className="w-full px-3 py-1.5 text-left text-sm transition-colors hover:bg-accent"
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </th>
          </tr>
        </thead>

        <tbody>
          {MEAL_SLOTS.map((slot, slotIdx) => (
            <tr
              key={slot.value}
              className={slotIdx % 2 !== 0 ? "bg-muted/10" : ""}
            >
              {/* Label tipo pasto */}
              <td className="sticky left-0 z-10 w-32 bg-background px-3 py-2 text-xs font-medium text-muted-foreground">
                {slot.label}
              </td>

              {/* Celle per ogni giorno */}
              {presentDays.map((giorno) => {
                const meal = getMealForCell(pasti, giorno, slot.value);
                return (
                  <td key={giorno} className="min-w-[110px] px-1 py-1">
                    {meal ? (
                      <button
                        onClick={() => onSelectDay(giorno)}
                        className="w-full rounded-md border border-border/60 bg-muted/20 px-2 py-1.5 text-left transition-colors hover:bg-muted/50"
                      >
                        <div className="text-xs font-semibold tabular-nums text-foreground">
                          {Math.round(meal.totale_kcal)} kcal
                        </div>
                        <div className="mt-0.5 text-[10px] text-muted-foreground tabular-nums">
                          P:{Math.round(meal.totale_proteine_g)}g C:
                          {Math.round(meal.totale_carboidrati_g)}g G:
                          {Math.round(meal.totale_grassi_g)}g
                        </div>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleAddCellMeal(giorno, slot.value)}
                        className="flex w-full items-center justify-center rounded-md border border-dashed border-border/40 py-2 text-muted-foreground/40 transition-colors hover:border-border hover:text-muted-foreground"
                        title={`Aggiungi ${slot.label}`}
                      >
                        <Plus className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </td>
                );
              })}

              <td />
            </tr>
          ))}

          {/* Footer totali giornalieri */}
          <tr className="border-t bg-muted/20">
            <td className="sticky left-0 z-10 bg-muted/20 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Totale
            </td>
            {presentDays.map((giorno) => {
              const totals = getDailyTotals(pasti, giorno);
              return (
                <td key={giorno} className="px-2 py-2 text-center">
                  {totals.kcal > 0 ? (
                    <div>
                      <Badge
                        variant="secondary"
                        className="mb-0.5 text-[10px] font-semibold text-emerald-700 bg-emerald-50"
                      >
                        {Math.round(totals.kcal)} kcal
                      </Badge>
                      <div className="text-[10px] text-muted-foreground tabular-nums">
                        P:{Math.round(totals.p)}g C:{Math.round(totals.c)}g G:
                        {Math.round(totals.g)}g
                      </div>
                    </div>
                  ) : (
                    <span className="text-xs text-muted-foreground/40">— kcal</span>
                  )}
                </td>
              );
            })}
            <td />
          </tr>
        </tbody>
      </table>
    </div>
  );
}
