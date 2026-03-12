// src/components/nutrition/FoodSearchSidebar.tsx
"use client";

/**
 * Sidebar Sheet per la ricerca alimenti da aggiungere a un pasto.
 *
 * Flusso a 2 step:
 * 1. Lista risultati (cerca ≥2 caratteri)
 * 2. Alimento selezionato → campo grammi → anteprima macro → Aggiungi
 *
 * Sostituisce FoodSearchDialog con un pannello laterale persistente.
 */

import { useState, useEffect, useRef } from "react";
import { Search, Loader2, Plus, ArrowLeft, Utensils } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { toast } from "sonner";
import { useFoods, useAddComponent } from "@/hooks/useNutrition";
import type { Food } from "@/types/api";

// ── Props ─────────────────────────────────────────────────────────────────

interface FoodSearchSidebarProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  planId: number;
  mealId: number | null;
  mealLabel?: string;
}

// ── Componente ────────────────────────────────────────────────────────────

export function FoodSearchSidebar({
  open,
  onOpenChange,
  planId,
  mealId,
  mealLabel,
}: FoodSearchSidebarProps) {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [selectedFood, setSelectedFood] = useState<Food | null>(null);
  const [quantita, setQuantita] = useState<string>("100");
  const searchRef = useRef<HTMLInputElement>(null);

  const addComponent = useAddComponent();
  const { data: foods = [], isLoading } = useFoods(debouncedQuery || undefined);

  // Debounce ricerca 400ms
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 400);
    return () => clearTimeout(timer);
  }, [query]);

  // Reset stato quando cambia mealId
  useEffect(() => {
    setQuery("");
    setDebouncedQuery("");
    setSelectedFood(null);
    setQuantita("100");
  }, [mealId]);

  // Autofocus sull'input all'apertura
  useEffect(() => {
    if (open) {
      setTimeout(() => searchRef.current?.focus(), 100);
    }
  }, [open]);

  const handleSelect = (food: Food) => {
    setSelectedFood(food);
    setQuantita("100");
  };

  const handleBack = () => {
    setSelectedFood(null);
    setQuantita("100");
  };

  const handleAdd = async () => {
    if (!selectedFood || mealId === null) return;
    const g = parseFloat(quantita);
    if (!g || g <= 0) return;

    await addComponent.mutateAsync({
      planId,
      mealId,
      alimento_id: selectedFood.id,
      quantita_g: g,
    });

    toast.success(`${selectedFood.nome} aggiunto al pasto`);
    onOpenChange(false);
  };

  // Macro scalate sulla quantità
  const qty = parseFloat(quantita || "0");
  const scaledMacro = selectedFood && qty > 0
    ? {
        kcal: Math.round((selectedFood.energia_kcal * qty) / 100),
        p: Math.round((selectedFood.proteine_g * qty) / 100 * 10) / 10,
        c: Math.round((selectedFood.carboidrati_g * qty) / 100 * 10) / 10,
        g: Math.round((selectedFood.grassi_g * qty) / 100 * 10) / 10,
      }
    : null;

  const headerTitle = mealLabel
    ? `Aggiungi a ${mealLabel}`
    : "Aggiungi alimento";

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-80 sm:w-96 flex flex-col p-0">
        <SheetHeader className="px-4 pt-4 pb-3 border-b">
          <SheetTitle className="flex items-center gap-2 text-base">
            <Utensils className="h-4 w-4 text-muted-foreground" />
            {headerTitle}
          </SheetTitle>
        </SheetHeader>

        <div className="flex-1 flex flex-col overflow-hidden px-4 pt-3 gap-3">
          {/* Step 1: ricerca */}
          {!selectedFood && (
            <>
              {/* Input ricerca */}
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  ref={searchRef}
                  placeholder="Cerca alimento..."
                  className="pl-8"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>

              {/* Lista risultati */}
              <ScrollArea className="h-[400px]">
                {isLoading && (
                  <div className="flex items-center justify-center py-10">
                    <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                  </div>
                )}
                {!isLoading && query.length < 2 && (
                  <p className="py-10 text-center text-sm text-muted-foreground">
                    Cerca almeno 2 caratteri
                  </p>
                )}
                {!isLoading && query.length >= 2 && foods.length === 0 && (
                  <p className="py-10 text-center text-sm text-muted-foreground">
                    Nessun alimento trovato
                  </p>
                )}
                <div className="space-y-0.5 pr-1">
                  {foods.map((food) => (
                    <button
                      key={food.id}
                      onClick={() => handleSelect(food)}
                      className="w-full rounded-md px-3 py-2 text-left transition-colors hover:bg-accent"
                    >
                      <div className="text-sm font-medium">{food.nome}</div>
                      <div className="text-xs text-muted-foreground">
                        {food.categoria_nome && (
                          <span className="mr-1.5 text-[10px] uppercase tracking-wide opacity-60">
                            {food.categoria_nome}
                          </span>
                        )}
                        {Math.round(food.energia_kcal)} kcal &middot; P{" "}
                        {food.proteine_g}g &middot; C {food.carboidrati_g}g
                        &middot; G {food.grassi_g}g
                        <span className="ml-1 text-[10px] opacity-50">/ 100g</span>
                      </div>
                    </button>
                  ))}
                </div>
              </ScrollArea>
            </>
          )}

          {/* Step 2: alimento selezionato */}
          {selectedFood && (
            <div className="space-y-4">
              {/* Bottone indietro */}
              <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 text-muted-foreground hover:text-foreground -ml-1"
                onClick={handleBack}
              >
                <ArrowLeft className="h-4 w-4" />
                Cambia alimento
              </Button>

              {/* Card alimento selezionato */}
              <div className="rounded-lg border bg-muted/30 px-4 py-3 space-y-1">
                <div className="text-sm font-semibold">{selectedFood.nome}</div>
                {selectedFood.categoria_nome && (
                  <div className="text-xs text-muted-foreground">
                    {selectedFood.categoria_nome}
                  </div>
                )}
                <div className="text-xs text-muted-foreground pt-0.5">
                  Per 100g: {Math.round(selectedFood.energia_kcal)} kcal &middot;
                  P {selectedFood.proteine_g}g &middot; C{" "}
                  {selectedFood.carboidrati_g}g &middot; G {selectedFood.grassi_g}g
                </div>
              </div>

              {/* Campo grammi */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">
                  Quantità (grammi)
                </label>
                <Input
                  type="number"
                  min={1}
                  max={2000}
                  autoFocus
                  value={quantita}
                  onChange={(e) => setQuantita(e.target.value)}
                  className="text-right tabular-nums"
                />
              </div>

              {/* Anteprima macro scalata */}
              {scaledMacro && (
                <>
                  <Separator />
                  <div className="rounded-lg bg-muted/40 px-4 py-3">
                    <p className="text-xs font-medium text-muted-foreground mb-2">
                      Valori per {quantita}g
                    </p>
                    <div className="grid grid-cols-4 gap-2 text-center">
                      <div>
                        <div className="text-base font-bold tabular-nums">
                          {scaledMacro.kcal}
                        </div>
                        <div className="text-[10px] text-muted-foreground">kcal</div>
                      </div>
                      <div>
                        <div className="text-base font-bold tabular-nums text-blue-600">
                          {scaledMacro.p}g
                        </div>
                        <div className="text-[10px] text-muted-foreground">Prot</div>
                      </div>
                      <div>
                        <div className="text-base font-bold tabular-nums text-amber-600">
                          {scaledMacro.c}g
                        </div>
                        <div className="text-[10px] text-muted-foreground">Carb</div>
                      </div>
                      <div>
                        <div className="text-base font-bold tabular-nums text-rose-500">
                          {scaledMacro.g}g
                        </div>
                        <div className="text-[10px] text-muted-foreground">Grassi</div>
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* CTA aggiungi */}
              <Button
                className="w-full"
                onClick={handleAdd}
                disabled={
                  addComponent.isPending ||
                  !quantita ||
                  parseFloat(quantita) <= 0 ||
                  mealId === null
                }
              >
                {addComponent.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="mr-2 h-4 w-4" />
                )}
                Aggiungi al pasto
              </Button>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
