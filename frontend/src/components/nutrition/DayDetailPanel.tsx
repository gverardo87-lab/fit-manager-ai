// src/components/nutrition/DayDetailPanel.tsx
"use client";

/**
 * Vista dettaglio giorno: tutti i 7 slot pasto in ordine canonico.
 * Slot vuoto → CTA "Aggiungi". Slot pieno → lista alimenti + azioni.
 * Header: nome giorno + totali macro + tasto "← Torna alla griglia".
 */

import { ArrowLeft, Plus, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader,
  AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useAddMeal, useDeleteMeal, useDeleteComponent } from "@/hooks/useNutrition";
import type { NutritionPlanDetail, PlanMealDetail, MealComponentDetail } from "@/types/api";
import { GIORNO_OPTIONS, TIPO_PASTO_OPTIONS } from "@/types/api";

const MEAL_SLOTS = [
  { value: "COLAZIONE", label: "Colazione" },
  { value: "SPUNTINO_MATTINA", label: "Spuntino mattina" },
  { value: "PRANZO", label: "Pranzo" },
  { value: "SPUNTINO_POMERIGGIO", label: "Merenda" },
  { value: "CENA", label: "Cena" },
  { value: "PRE_WORKOUT", label: "Pre-workout" },
  { value: "POST_WORKOUT", label: "Post-workout" },
];

interface DayDetailPanelProps {
  plan: NutritionPlanDetail;
  planId: number;
  giorno: number;
  onBack: () => void;
  onAddFood: (mealId: number, mealLabel: string) => void;
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

function ComponentRow({ comp, planId, mealId }: { comp: MealComponentDetail; planId: number; mealId: number }) {
  const deleteComponent = useDeleteComponent();
  return (
    <div className="flex items-center gap-2 py-1">
      <span className="flex-1 text-sm">
        {comp.alimento_nome ?? `Alimento #${comp.alimento_id}`}
        <span className="ml-1.5 text-xs text-muted-foreground">{comp.quantita_g}g</span>
      </span>
      <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
        {Math.round(comp.energia_kcal)} kcal
      </span>
      <Button
        variant="ghost" size="icon"
        className="h-6 w-6 shrink-0 text-muted-foreground hover:text-destructive"
        onClick={() => deleteComponent.mutate({ planId, mealId, compId: comp.id })}
        disabled={deleteComponent.isPending}
      >
        <Trash2 className="h-3 w-3" />
      </Button>
    </div>
  );
}

interface MealSlotCardProps {
  giorno: number;
  tipoPasto: string;
  tipoPastoLabel: string;
  meal: PlanMealDetail | undefined;
  planId: number;
  onAddFood: (mealId: number, label: string) => void;
}

function MealSlotCard({ giorno, tipoPasto, tipoPastoLabel, meal, planId, onAddFood }: MealSlotCardProps) {
  const addMeal = useAddMeal();
  const deleteMeal = useDeleteMeal();

  if (!meal) {
    return (
      <div className="rounded-lg border border-dashed border-border/50 px-4 py-3 flex items-center gap-3">
        <span className="flex-1 text-sm text-muted-foreground/60 italic">Nessun pasto</span>
        <Button
          variant="ghost" size="sm"
          className="h-7 text-xs text-muted-foreground hover:text-foreground gap-1"
          onClick={() => addMeal.mutate({ planId, payload: { giorno_settimana: giorno, tipo_pasto: tipoPasto, ordine: 0 } })}
          disabled={addMeal.isPending}
        >
          {addMeal.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
          Aggiungi {tipoPastoLabel}
        </Button>
      </div>
    );
  }

  const mealLabel = meal.nome ?? TIPO_PASTO_OPTIONS.find((t) => t.value === meal.tipo_pasto)?.label ?? tipoPastoLabel;

  return (
    <div className="rounded-lg border bg-background">
      <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border/50">
        <div className="flex-1 min-w-0">
          <span className="text-sm font-semibold">{mealLabel}</span>
          {meal.totale_kcal > 0 && (
            <span className="ml-2 text-xs text-muted-foreground tabular-nums">
              {Math.round(meal.totale_kcal)} kcal &middot; P {Math.round(meal.totale_proteine_g)}g
              &middot; C {Math.round(meal.totale_carboidrati_g)}g &middot; G {Math.round(meal.totale_grassi_g)}g
            </span>
          )}
        </div>
        {meal.componenti.length > 0 && (
          <Badge variant="secondary" className="h-5 text-[10px] px-1.5">{meal.componenti.length}</Badge>
        )}
      </div>
      <div className="px-4 py-2 space-y-0.5">
        {meal.componenti.length === 0
          ? <p className="text-xs text-muted-foreground italic py-1">Nessun alimento</p>
          : meal.componenti.map((comp) => (
              <ComponentRow key={comp.id} comp={comp} planId={planId} mealId={meal.id} />
            ))
        }
      </div>
      <Separator />
      <div className="flex items-center gap-2 px-4 py-2">
        <Button
          variant="ghost" size="sm"
          className="h-7 gap-1 text-xs text-muted-foreground hover:text-foreground"
          onClick={() => onAddFood(meal.id, mealLabel)}
        >
          <Plus className="h-3 w-3" />
          Aggiungi alimento
        </Button>
        <div className="ml-auto">
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive">
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Elimina pasto</AlertDialogTitle>
                <AlertDialogDescription>
                  Vuoi eliminare {mealLabel} e tutti gli alimenti al suo interno? L&apos;azione non è reversibile.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Annulla</AlertDialogCancel>
                <AlertDialogAction
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  onClick={() => deleteMeal.mutate({ planId, mealId: meal.id })}
                >
                  Elimina
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </div>
  );
}

export function DayDetailPanel({ plan, planId, giorno, onBack, onAddFood }: DayDetailPanelProps) {
  const pasti = plan.pasti ?? [];
  const totals = getDailyTotals(pasti, giorno);
  const giornoLabel = GIORNO_OPTIONS.find((g) => g.value === giorno)?.label ?? "Giorno";

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold">{giornoLabel}</h3>
            {totals.kcal > 0 && (
              <Badge variant="secondary" className="text-xs text-emerald-700 bg-emerald-50">
                {Math.round(totals.kcal)} kcal
              </Badge>
            )}
          </div>
          {totals.kcal > 0 && (
            <p className="text-xs text-muted-foreground tabular-nums">
              P {Math.round(totals.p)}g &middot; C {Math.round(totals.c)}g &middot; G {Math.round(totals.g)}g
            </p>
          )}
        </div>
        <Button
          variant="ghost" size="sm"
          className="gap-1.5 text-muted-foreground hover:text-foreground self-start sm:self-auto"
          onClick={onBack}
        >
          <ArrowLeft className="h-4 w-4" />
          Torna alla griglia
        </Button>
      </div>
      <Separator />
      <div className="space-y-3">
        {MEAL_SLOTS.map((slot) => {
          const meal = pasti.find((m) => m.giorno_settimana === giorno && m.tipo_pasto === slot.value);
          return (
            <MealSlotCard
              key={slot.value}
              giorno={giorno}
              tipoPasto={slot.value}
              tipoPastoLabel={slot.label}
              meal={meal}
              planId={planId}
              onAddFood={onAddFood}
            />
          );
        })}
      </div>
    </div>
  );
}
