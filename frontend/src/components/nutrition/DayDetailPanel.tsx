// src/components/nutrition/DayDetailPanel.tsx
"use client";

/**
 * Vista dettaglio giorno: tutti i 7 slot pasto in ordine canonico.
 *
 * Feature PRO++:
 * - F3: rinomina pasto inline (click sul nome → input)
 * - F5: swap alimento (icona ArrowLeftRight → apre sidebar in replace mode)
 * - F6: template pasti ("Da template" in slot vuoto, "Salva template" in slot pieno)
 */

import { useState } from "react";
import { Plus, Trash2, Loader2, UtensilsCrossed, ArrowLeftRight, Pencil, BookMarked } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader,
  AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useAddMeal, useDeleteMeal, useDeleteComponent, useUpdateMeal } from "@/hooks/useNutrition";
import { useMealTemplates, useSaveAsTemplate, useApplyTemplate } from "@/hooks/useNutritionTemplates";
import { NutritionDayHeader } from "./NutritionDayHeader";
import type { NutritionPlanDetail, PlanMealDetail, MealComponentDetail } from "@/types/api";
import { TIPO_PASTO_OPTIONS } from "@/types/api";

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
  onSwapFood?: (mealId: number, compId: number) => void;
}

function getDailyTotals(pasti: PlanMealDetail[], giorno: number) {
  const meals = pasti.filter((m) => m.giorno_settimana === giorno);
  return {
    kcal: meals.reduce((s, m) => s + m.totale_kcal, 0),
    p: meals.reduce((s, m) => s + m.totale_proteine_g, 0),
    c: meals.reduce((s, m) => s + m.totale_carboidrati_g, 0),
    g: meals.reduce((s, m) => s + m.totale_grassi_g, 0),
    fibra: meals.reduce((s, m) =>
      s + m.componenti.reduce((cs, comp) => cs + (comp.fibra_g ?? 0), 0), 0),
  };
}

function ComponentRow({
  comp, planId, mealId, onSwap,
}: { comp: MealComponentDetail; planId: number; mealId: number; onSwap?: () => void }) {
  const deleteComponent = useDeleteComponent();
  return (
    <div className="flex items-center gap-3 py-2 px-1">
      <div className="flex-1 min-w-0">
        <span className="text-base font-medium">
          {comp.alimento_nome ?? `Alimento #${comp.alimento_id}`}
        </span>
        <span className="ml-2 text-sm text-muted-foreground font-medium">{comp.quantita_g}g</span>
      </div>
      <span className="shrink-0 text-sm font-semibold tabular-nums text-foreground">
        {Math.round(comp.energia_kcal)} kcal
      </span>
      {onSwap && (
        <Button variant="ghost" size="icon"
          className="h-7 w-7 shrink-0 text-muted-foreground/50 hover:text-primary"
          onClick={onSwap} title="Sostituisci alimento">
          <ArrowLeftRight className="h-3.5 w-3.5" />
        </Button>
      )}
      <Button variant="ghost" size="icon"
        className="h-7 w-7 shrink-0 text-muted-foreground/50 hover:text-destructive"
        onClick={() => deleteComponent.mutate({ planId, mealId, compId: comp.id })}
        disabled={deleteComponent.isPending}>
        {deleteComponent.isPending
          ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
          : <Trash2 className="h-3.5 w-3.5" />}
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
  onSwapFood?: (mealId: number, compId: number) => void;
}

function MealSlotCard({ giorno, tipoPasto, tipoPastoLabel, meal, planId, onAddFood, onSwapFood }: MealSlotCardProps) {
  const addMeal = useAddMeal();
  const deleteMeal = useDeleteMeal();
  const updateMeal = useUpdateMeal();
  const saveAsTemplate = useSaveAsTemplate();
  const applyTemplate = useApplyTemplate();
  const { data: templates = [] } = useMealTemplates();

  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [templateDropOpen, setTemplateDropOpen] = useState(false);
  const [saveTemplateOpen, setSaveTemplateOpen] = useState(false);
  const [saveTemplateName, setSaveTemplateName] = useState("");

  const mealLabel = meal
    ? meal.nome ?? TIPO_PASTO_OPTIONS.find((t) => t.value === meal.tipo_pasto)?.label ?? tipoPastoLabel
    : tipoPastoLabel;

  const handleRenameCommit = () => {
    if (!meal || !renameValue.trim()) { setRenaming(false); return; }
    updateMeal.mutate({ planId, mealId: meal.id, nome: renameValue.trim() });
    setRenaming(false);
  };

  const handleSaveTemplate = () => {
    if (!meal || !saveTemplateName.trim()) return;
    saveAsTemplate.mutate({ planId, mealId: meal.id, nome: saveTemplateName.trim(), tipo_pasto: meal.tipo_pasto });
    setSaveTemplateOpen(false);
    setSaveTemplateName("");
  };

  // Empty slot
  if (!meal) {
    return (
      <div className="rounded-lg border border-dashed border-border/60 px-5 py-4 flex items-center gap-3 flex-wrap transition-colors hover:border-primary/40 hover:bg-primary/5">
        <UtensilsCrossed className="h-5 w-5 text-muted-foreground/30 shrink-0" />
        <span className="flex-1 text-sm text-muted-foreground/60 min-w-0">{tipoPastoLabel}</span>
        {templates.length > 0 && (
          <div className="relative">
            <Button variant="ghost" size="sm"
              className="gap-1 text-xs text-muted-foreground hover:text-foreground h-7 px-2"
              onClick={() => setTemplateDropOpen((v) => !v)}>
              <BookMarked className="h-3.5 w-3.5" />
              Da template
            </Button>
            {templateDropOpen && (
              <div className="absolute right-0 top-9 z-20 min-w-[180px] max-h-52 overflow-y-auto rounded-lg border bg-popover shadow-md">
                <p className="px-3 py-2 text-xs uppercase tracking-wide text-muted-foreground border-b">Template</p>
                {templates.map((t) => (
                  <button key={t.id}
                    onClick={async () => {
                      setTemplateDropOpen(false);
                      const res = await addMeal.mutateAsync({ planId, payload: { giorno_settimana: giorno, tipo_pasto: tipoPasto, ordine: 0 } });
                      applyTemplate.mutate({ planId, mealId: res.id, templateId: t.id });
                    }}
                    className="w-full px-3 py-2 text-left text-sm transition-colors hover:bg-accent">
                    <div className="font-medium">{t.nome}</div>
                    {t.totale_kcal > 0 && (
                      <div className="text-xs text-muted-foreground">{Math.round(t.totale_kcal)} kcal</div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        <Button variant="ghost" size="sm"
          className="gap-1.5 text-sm text-muted-foreground hover:text-foreground"
          onClick={() => addMeal.mutate({ planId, payload: { giorno_settimana: giorno, tipo_pasto: tipoPasto, ordine: 0 } })}
          disabled={addMeal.isPending}>
          {addMeal.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Aggiungi pasto
        </Button>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-background">
      {/* Header pasto */}
      <div className="flex items-start gap-3 px-5 py-3.5 border-b border-border/50">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {renaming ? (
              <Input autoFocus value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onBlur={handleRenameCommit}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleRenameCommit();
                  if (e.key === "Escape") setRenaming(false);
                }}
                className="h-7 text-base font-bold w-44 px-2" />
            ) : (
              <button
                onClick={() => { setRenameValue(mealLabel); setRenaming(true); }}
                className="flex items-center gap-1.5 text-base font-bold hover:text-primary/80 transition-colors group"
                title="Clicca per rinominare">
                {mealLabel}
                <Pencil className="h-3.5 w-3.5 text-muted-foreground/0 group-hover:text-muted-foreground/60 transition-colors" />
              </button>
            )}
            {meal.componenti.length > 0 && (
              <Badge variant="secondary" className="h-5 text-xs px-2">
                {meal.componenti.length} aliment{meal.componenti.length === 1 ? "o" : "i"}
              </Badge>
            )}
          </div>
          {meal.totale_kcal > 0 && (
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="text-sm font-semibold text-foreground tabular-nums">{Math.round(meal.totale_kcal)} kcal</span>
              <span className="text-muted-foreground/40 text-xs">·</span>
              <span className="text-sm font-medium text-blue-600 tabular-nums">P {Math.round(meal.totale_proteine_g)}g</span>
              <span className="text-muted-foreground/40 text-xs">·</span>
              <span className="text-sm font-medium text-amber-600 tabular-nums">C {Math.round(meal.totale_carboidrati_g)}g</span>
              <span className="text-muted-foreground/40 text-xs">·</span>
              <span className="text-sm font-medium text-rose-500 tabular-nums">G {Math.round(meal.totale_grassi_g)}g</span>
            </div>
          )}
        </div>
      </div>

      {/* Lista alimenti */}
      <div className="px-4 py-1">
        {meal.componenti.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-5 text-center">
            <UtensilsCrossed className="h-6 w-6 text-muted-foreground/20" />
            <p className="text-sm text-muted-foreground/60">Nessun alimento ancora</p>
            <Button variant="outline" size="sm" className="gap-1.5 mt-1"
              onClick={() => onAddFood(meal.id, mealLabel)}>
              <Plus className="h-3.5 w-3.5" />
              Aggiungi primo alimento
            </Button>
          </div>
        ) : (
          <div className="divide-y divide-border/40">
            {meal.componenti.map((comp) => (
              <ComponentRow key={comp.id} comp={comp} planId={planId} mealId={meal.id}
                onSwap={onSwapFood ? () => onSwapFood(meal.id, comp.id) : undefined} />
            ))}
          </div>
        )}
      </div>

      {meal.componenti.length > 0 && (
        <>
          <Separator />
          <div className="flex items-center gap-2 px-4 py-2.5 flex-wrap">
            <Button variant="ghost" size="sm"
              className="gap-1.5 text-sm text-muted-foreground hover:text-foreground"
              onClick={() => onAddFood(meal.id, mealLabel)}>
              <Plus className="h-4 w-4" />
              Aggiungi alimento
            </Button>

            {/* Salva come template */}
            {saveTemplateOpen ? (
              <div className="flex items-center gap-1">
                <Input value={saveTemplateName} onChange={(e) => setSaveTemplateName(e.target.value)}
                  placeholder="Nome template..." className="h-7 text-xs w-36"
                  onKeyDown={(e) => { if (e.key === "Enter") handleSaveTemplate(); if (e.key === "Escape") setSaveTemplateOpen(false); }}
                  autoFocus />
                <Button size="sm" className="h-7 text-xs px-2"
                  onClick={handleSaveTemplate}
                  disabled={saveAsTemplate.isPending || !saveTemplateName.trim()}>
                  Salva
                </Button>
                <Button variant="ghost" size="sm" className="h-7 text-xs px-2"
                  onClick={() => setSaveTemplateOpen(false)}>✕</Button>
              </div>
            ) : (
              <Button variant="ghost" size="sm"
                className="gap-1 text-xs text-muted-foreground hover:text-foreground h-7"
                onClick={() => { setSaveTemplateName(mealLabel); setSaveTemplateOpen(true); }}>
                <BookMarked className="h-3.5 w-3.5" />
                Salva template
              </Button>
            )}

            <div className="ml-auto">
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground/50 hover:text-destructive">
                    <Trash2 className="h-4 w-4" />
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
                      onClick={() => deleteMeal.mutate({ planId, mealId: meal.id })}>
                      Elimina
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function DayDetailPanel({ plan, planId, giorno, onBack, onAddFood, onSwapFood }: DayDetailPanelProps) {
  const pasti = plan.pasti ?? [];
  const totals = getDailyTotals(pasti, giorno);

  return (
    <div className="space-y-5">
      <NutritionDayHeader plan={plan} planId={planId} giorno={giorno} totals={totals} onBack={onBack} />
      <Separator />
      <div className="space-y-3">
        {MEAL_SLOTS.map((slot) => {
          const meal = pasti.find((m) => m.giorno_settimana === giorno && m.tipo_pasto === slot.value);
          return (
            <MealSlotCard key={slot.value} giorno={giorno} tipoPasto={slot.value} tipoPastoLabel={slot.label}
              meal={meal} planId={planId} onAddFood={onAddFood} onSwapFood={onSwapFood} />
          );
        })}
      </div>
    </div>
  );
}
