// src/components/nutrition/FoodSearchDialog.tsx
"use client";

/**
 * Dialog ricerca alimento da aggiungere a un pasto.
 *
 * Flusso:
 * 1. Utente digita → debounce 400ms → useFoods(q)
 * 2. Seleziona alimento → campo grammi attivo
 * 3. Conferma → useAddComponent() → dialog si chiude
 */

import { useState, useEffect } from "react";
import { Search, Loader2, Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useFoods, useAddComponent } from "@/hooks/useNutrition";
import type { Food } from "@/types/api";

// ── Props ─────────────────────────────────────────────────────────────────

interface FoodSearchDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  planId: number;
  mealId: number;
}

// ── Componente ────────────────────────────────────────────────────────────

export function FoodSearchDialog({ open, onOpenChange, planId, mealId }: FoodSearchDialogProps) {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [selectedFood, setSelectedFood] = useState<Food | null>(null);
  const [quantita, setQuantita] = useState<string>("100");

  const addComponent = useAddComponent();
  const { data: foods = [], isLoading } = useFoods(debouncedQuery || undefined);

  // Debounce ricerca 400ms
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 400);
    return () => clearTimeout(timer);
  }, [query]);

  // Reset stato all'apertura/chiusura
  useEffect(() => {
    if (!open) {
      setQuery("");
      setDebouncedQuery("");
      setSelectedFood(null);
      setQuantita("100");
    }
  }, [open]);

  const handleSelect = (food: Food) => {
    setSelectedFood(food);
    setQuantita("100");
  };

  const handleAdd = async () => {
    if (!selectedFood) return;
    const g = parseFloat(quantita);
    if (!g || g <= 0) return;

    await addComponent.mutateAsync({
      planId,
      mealId,
      alimento_id: selectedFood.id,
      quantita_g: g,
    });
    onOpenChange(false);
  };

  // Macro scalate sulla quantità selezionata
  const scaledMacro = selectedFood
    ? {
        kcal: Math.round((selectedFood.energia_kcal * parseFloat(quantita || "0")) / 100),
        p: Math.round((selectedFood.proteine_g * parseFloat(quantita || "0")) / 100 * 10) / 10,
        c: Math.round((selectedFood.carboidrati_g * parseFloat(quantita || "0")) / 100 * 10) / 10,
        g: Math.round((selectedFood.grassi_g * parseFloat(quantita || "0")) / 100 * 10) / 10,
      }
    : null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Aggiungi alimento</DialogTitle>
        </DialogHeader>

        {/* Ricerca */}
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            autoFocus
            placeholder="Cerca alimento..."
            className="pl-8"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        {/* Lista risultati */}
        {!selectedFood && (
          <ScrollArea className="h-56">
            {isLoading && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            )}
            {!isLoading && foods.length === 0 && query.length >= 2 && (
              <p className="py-6 text-center text-sm text-muted-foreground">Nessun alimento trovato</p>
            )}
            {!isLoading && query.length < 2 && (
              <p className="py-6 text-center text-sm text-muted-foreground">Digita almeno 2 caratteri</p>
            )}
            <div className="space-y-0.5 px-1">
              {foods.map((food) => (
                <button
                  key={food.id}
                  onClick={() => handleSelect(food)}
                  className="w-full rounded-md px-3 py-2 text-left transition-colors hover:bg-accent"
                >
                  <div className="text-sm font-medium">{food.nome}</div>
                  <div className="text-xs text-muted-foreground">
                    {Math.round(food.energia_kcal)} kcal &middot; P {food.proteine_g}g &middot; C {food.carboidrati_g}g &middot; G {food.grassi_g}g
                    <span className="ml-1 text-[10px] opacity-60">/ 100g</span>
                  </div>
                </button>
              ))}
            </div>
          </ScrollArea>
        )}

        {/* Selezione alimento + grammi */}
        {selectedFood && (
          <div className="space-y-3">
            <div className="rounded-md border bg-muted/30 px-3 py-2">
              <div className="text-sm font-medium">{selectedFood.nome}</div>
              <div className="text-xs text-muted-foreground">{selectedFood.categoria_nome ?? ""}</div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="mb-1 block text-xs text-muted-foreground">Quantità (g)</label>
                <Input
                  type="number"
                  min={1}
                  max={2000}
                  value={quantita}
                  onChange={(e) => setQuantita(e.target.value)}
                  className="text-right"
                  autoFocus
                />
              </div>
              {scaledMacro && (
                <div className="text-xs text-muted-foreground text-right">
                  <div className="font-medium text-foreground">{scaledMacro.kcal} kcal</div>
                  <div>P {scaledMacro.p}g</div>
                  <div>C {scaledMacro.c}g</div>
                  <div>G {scaledMacro.g}g</div>
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => setSelectedFood(null)}
              >
                Indietro
              </Button>
              <Button
                size="sm"
                className="flex-1"
                onClick={handleAdd}
                disabled={addComponent.isPending || !quantita || parseFloat(quantita) <= 0}
              >
                {addComponent.isPending ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : (
                  <Plus className="mr-1 h-3 w-3" />
                )}
                Aggiungi
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
