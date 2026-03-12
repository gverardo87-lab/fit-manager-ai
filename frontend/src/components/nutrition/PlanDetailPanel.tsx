// src/components/nutrition/PlanDetailPanel.tsx
"use client";

/**
 * Pannello dettaglio piano alimentare (inline espanso nella riga).
 *
 * Mostra pasti organizzati per giorno con:
 * - Lista componenti (alimento × grammi × macro calcolati)
 * - Totale macro per pasto
 * - Media giornaliera del piano
 * - CTA "Aggiungi pasto" + "Aggiungi alimento" per ogni pasto
 *
 * Usa FoodSearchDialog per cercare alimenti nel catalogo.
 */

import { useState } from "react";
import { Plus, Trash2, Loader2, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useNutritionPlan,
  useAddMeal,
  useDeleteMeal,
  useDeleteComponent,
} from "@/hooks/useNutrition";
import { FoodSearchDialog } from "@/components/nutrition/FoodSearchDialog";
import type { PlanMealDetail } from "@/types/api";
import { TIPO_PASTO_OPTIONS, GIORNO_OPTIONS } from "@/types/api";

// ── Helper: stringa macro compatta ────────────────────────────────────────

function MacroLine({ kcal, p, c, g }: { kcal: number; p: number; c: number; g: number }) {
  return (
    <span className="text-xs text-muted-foreground">
      {Math.round(kcal)} kcal &middot; P {Math.round(p)}g &middot; C {Math.round(c)}g &middot; G {Math.round(g)}g
    </span>
  );
}

// ── Props ─────────────────────────────────────────────────────────────────

interface PlanDetailPanelProps {
  planId: number;
  clientId: number;
}

// ── Componente principale ─────────────────────────────────────────────────

export function PlanDetailPanel({ planId, clientId }: PlanDetailPanelProps) {
  const { data: plan, isLoading } = useNutritionPlan(clientId, planId);
  const addMeal = useAddMeal();
  const deleteMeal = useDeleteMeal();
  const [foodDialogMealId, setFoodDialogMealId] = useState<number | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    );
  }

  if (!plan) return null;

  const pasti = plan.pasti ?? [];

  // Raggruppa per giorno
  const giorni = Array.from(new Set(pasti.map((m) => m.giorno_settimana))).sort();

  const handleAddMeal = async () => {
    await addMeal.mutateAsync({
      planId,
      payload: {
        giorno_settimana: 0,
        tipo_pasto: "PRANZO",
        ordine: pasti.length,
      },
    });
  };

  return (
    <div className="space-y-3">
      {/* Totale piano */}
      {plan.totale_kcal != null && plan.totale_kcal > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">Media/die:</span>
          <MacroLine
            kcal={plan.totale_kcal}
            p={plan.totale_proteine_g ?? 0}
            c={plan.totale_carboidrati_g ?? 0}
            g={plan.totale_grassi_g ?? 0}
          />
        </div>
      )}

      {/* Pasti vuoti */}
      {pasti.length === 0 && (
        <p className="text-xs text-muted-foreground italic">Nessun pasto ancora. Aggiungi il primo pasto.</p>
      )}

      {/* Pasti per giorno */}
      {giorni.map((giorno) => {
        const pastiGiorno = pasti.filter((m) => m.giorno_settimana === giorno);
        const giornoLabel = GIORNO_OPTIONS.find((g) => g.value === giorno)?.label ?? "Giorno";
        return (
          <div key={giorno} className="space-y-1.5">
            {giorni.length > 1 && (
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{giornoLabel}</h4>
            )}
            {pastiGiorno.map((meal) => (
              <MealRow
                key={meal.id}
                meal={meal}
                planId={planId}
                onAddFood={() => setFoodDialogMealId(meal.id)}
                onDelete={() => deleteMeal.mutate({ planId, mealId: meal.id })}
              />
            ))}
          </div>
        );
      })}

      {/* CTA aggiungi pasto */}
      <Button
        variant="ghost"
        size="sm"
        className="text-xs text-muted-foreground hover:text-foreground"
        onClick={handleAddMeal}
        disabled={addMeal.isPending}
      >
        {addMeal.isPending ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <Plus className="mr-1 h-3 w-3" />}
        Aggiungi pasto
      </Button>

      {/* Dialog ricerca alimenti */}
      <FoodSearchDialog
        open={foodDialogMealId !== null}
        onOpenChange={(v) => { if (!v) setFoodDialogMealId(null); }}
        planId={planId}
        mealId={foodDialogMealId ?? 0}
      />
    </div>
  );
}

// ── Riga pasto ────────────────────────────────────────────────────────────

interface MealRowProps {
  meal: PlanMealDetail;
  planId: number;
  onAddFood: () => void;
  onDelete: () => void;
}

function MealRow({ meal, planId, onAddFood, onDelete }: MealRowProps) {
  const [expanded, setExpanded] = useState(false);
  const deleteComponent = useDeleteComponent();

  const tipoLabel = TIPO_PASTO_OPTIONS.find((t) => t.value === meal.tipo_pasto)?.label
    ?? meal.tipo_pasto_label
    ?? meal.tipo_pasto;

  return (
    <div className="rounded-md border bg-background">
      {/* Header pasto */}
      <div className="flex items-center gap-2 px-3 py-2">
        <button onClick={() => setExpanded(!expanded)} className="flex-1 flex items-center gap-2 text-left">
          <ChevronRight className={`h-3.5 w-3.5 text-muted-foreground transition-transform ${expanded ? "rotate-90" : ""}`} />
          <span className="text-sm font-medium">{meal.nome ?? tipoLabel}</span>
          {meal.componenti.length > 0 && (
            <Badge variant="secondary" className="text-[10px] h-4 px-1">{meal.componenti.length}</Badge>
          )}
        </button>
        {meal.totale_kcal > 0 && (
          <span className="text-xs text-muted-foreground shrink-0">{Math.round(meal.totale_kcal)} kcal</span>
        )}
        <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0" onClick={onAddFood}>
          <Plus className="h-3 w-3" />
        </Button>
        <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0 text-muted-foreground hover:text-destructive" onClick={onDelete}>
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>

      {/* Componenti espansi */}
      {expanded && meal.componenti.length > 0 && (
        <div className="border-t px-3 py-2 space-y-1.5">
          {meal.componenti.map((comp) => (
            <div key={comp.id} className="flex items-center gap-2">
              <span className="flex-1 text-xs">
                {comp.alimento_nome ?? `#${comp.alimento_id}`}
                <span className="text-muted-foreground ml-1">{comp.quantita_g}g</span>
              </span>
              <span className="text-xs text-muted-foreground shrink-0">
                {Math.round(comp.energia_kcal)} kcal
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="h-5 w-5 text-muted-foreground hover:text-destructive shrink-0"
                onClick={() => deleteComponent.mutate({ planId, mealId: meal.id, compId: comp.id })}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          ))}
          {/* Totale pasto */}
          <div className="pt-1 border-t">
            <MacroLine
              kcal={meal.totale_kcal}
              p={meal.totale_proteine_g}
              c={meal.totale_carboidrati_g}
              g={meal.totale_grassi_g}
            />
          </div>
        </div>
      )}
    </div>
  );
}
