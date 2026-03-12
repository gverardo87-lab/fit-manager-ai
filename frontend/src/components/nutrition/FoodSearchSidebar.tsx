// src/components/nutrition/FoodSearchSidebar.tsx
"use client";

/**
 * Sidebar Sheet per la ricerca alimenti da aggiungere a un pasto.
 *
 * Flusso batch (rimane aperta dopo ogni aggiunta):
 * 1. Lista risultati (cerca ≥2 caratteri)
 * 2. Alimento selezionato → campo grammi → anteprima macro → Aggiungi
 *    → toast + ritorno automatico a step 1 → pronto per alimento successivo
 * 3. Tasto "Chiudi" esplicito per uscire
 */

import { useState, useEffect, useRef } from "react";
import { Search, Loader2, Plus, ArrowLeft, Utensils, Check, X } from "lucide-react";
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
  const [addedCount, setAddedCount] = useState(0);
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
    setAddedCount(0);
  }, [mealId]);

  // Autofocus sull'input all'apertura
  useEffect(() => {
    if (open && !selectedFood) {
      setTimeout(() => searchRef.current?.focus(), 100);
    }
  }, [open, selectedFood]);

  const handleSelect = (food: Food) => {
    setSelectedFood(food);
    setQuantita("100");
  };

  const handleBack = () => {
    setSelectedFood(null);
    setQuantita("100");
    setTimeout(() => searchRef.current?.focus(), 100);
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

    toast.success(`${selectedFood.nome} aggiunto`);
    setAddedCount((n) => n + 1);
    // Batch-add: torna allo step 1 senza chiudere
    setSelectedFood(null);
    setQuantita("100");
    setQuery("");
    setDebouncedQuery("");
    setTimeout(() => searchRef.current?.focus(), 100);
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
      <SheetContent side="right" className="w-80 sm:w-[400px] flex flex-col p-0">
        <SheetHeader className="px-5 pt-4 pb-3 border-b">
          <div className="flex items-center gap-2">
            <SheetTitle className="flex-1 flex items-center gap-2 text-base">
              <Utensils className="h-4 w-4 text-muted-foreground shrink-0" />
              {headerTitle}
            </SheetTitle>
            {addedCount > 0 && (
              <span className="flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
                <Check className="h-3 w-3" />
                {addedCount}
              </span>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground shrink-0"
              onClick={() => onOpenChange(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </SheetHeader>

        <div className="flex-1 flex flex-col overflow-hidden px-5 pt-4 gap-4">
          {/* Step 1: ricerca */}
          {!selectedFood && (
            <>
              {/* Input ricerca */}
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  ref={searchRef}
                  placeholder="Cerca alimento..."
                  className="pl-9 h-11 text-base"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>

              {/* Lista risultati */}
              <ScrollArea className="flex-1 min-h-0 h-[460px]">
                {isLoading && (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                  </div>
                )}
                {!isLoading && query.length < 2 && (
                  <p className="py-12 text-center text-sm text-muted-foreground">
                    Digita almeno 2 caratteri
                  </p>
                )}
                {!isLoading && query.length >= 2 && foods.length === 0 && (
                  <p className="py-12 text-center text-sm text-muted-foreground">
                    Nessun alimento trovato
                  </p>
                )}
                <div className="space-y-1 pr-1">
                  {foods.map((food) => (
                    <button
                      key={food.id}
                      onClick={() => handleSelect(food)}
                      className="w-full rounded-lg px-4 py-3 text-left transition-colors hover:bg-accent"
                    >
                      <div className="text-base font-semibold">{food.nome}</div>
                      <div className="mt-0.5 flex items-center gap-1.5 flex-wrap">
                        {food.categoria_nome && (
                          <span className="text-xs uppercase tracking-wide text-muted-foreground/60 font-medium">
                            {food.categoria_nome}
                          </span>
                        )}
                        <span className="text-sm text-muted-foreground tabular-nums">
                          {Math.round(food.energia_kcal)} kcal
                        </span>
                        <span className="text-muted-foreground/30">·</span>
                        <span className="text-sm text-blue-600 tabular-nums">P{food.proteine_g}g</span>
                        <span className="text-muted-foreground/30">·</span>
                        <span className="text-sm text-amber-600 tabular-nums">C{food.carboidrati_g}g</span>
                        <span className="text-muted-foreground/30">·</span>
                        <span className="text-sm text-rose-500 tabular-nums">G{food.grassi_g}g</span>
                        <span className="text-xs text-muted-foreground/40">/ 100g</span>
                      </div>
                    </button>
                  ))}
                </div>
              </ScrollArea>
            </>
          )}

          {/* Step 2: alimento selezionato */}
          {selectedFood && (
            <div className="space-y-5">
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
              <div className="rounded-lg border bg-muted/30 px-4 py-3.5 space-y-1.5">
                <div className="text-base font-bold">{selectedFood.nome}</div>
                {selectedFood.categoria_nome && (
                  <div className="text-sm text-muted-foreground font-medium">
                    {selectedFood.categoria_nome}
                  </div>
                )}
                <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
                  <span className="text-sm text-muted-foreground">Per 100g:</span>
                  <span className="text-sm font-medium tabular-nums">{Math.round(selectedFood.energia_kcal)} kcal</span>
                  <span className="text-muted-foreground/30">·</span>
                  <span className="text-sm font-medium text-blue-600 tabular-nums">P{selectedFood.proteine_g}g</span>
                  <span className="text-muted-foreground/30">·</span>
                  <span className="text-sm font-medium text-amber-600 tabular-nums">C{selectedFood.carboidrati_g}g</span>
                  <span className="text-muted-foreground/30">·</span>
                  <span className="text-sm font-medium text-rose-500 tabular-nums">G{selectedFood.grassi_g}g</span>
                </div>
              </div>

              {/* Campo grammi */}
              <div className="space-y-2">
                <label className="text-sm font-semibold text-foreground">
                  Quantità (grammi)
                </label>
                <Input
                  type="number"
                  min={1}
                  max={2000}
                  autoFocus
                  value={quantita}
                  onChange={(e) => setQuantita(e.target.value)}
                  className="text-right tabular-nums h-11 text-base font-semibold"
                />
                {/* Quick portions */}
                <div className="flex flex-wrap gap-1.5 pt-0.5">
                  {[30, 50, 80, 100, 125, 150, 200, 250].map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setQuantita(String(g))}
                      className={`rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                        quantita === String(g)
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border text-muted-foreground hover:border-primary/60 hover:text-foreground hover:bg-muted/50"
                      }`}
                    >
                      {g}g
                    </button>
                  ))}
                </div>
              </div>

              {/* Anteprima macro scalata */}
              {scaledMacro && (
                <>
                  <Separator />
                  <div className="rounded-lg bg-muted/40 px-4 py-4">
                    <p className="text-sm font-semibold text-muted-foreground mb-3">
                      Valori per {quantita}g
                    </p>
                    <div className="grid grid-cols-4 gap-2 text-center">
                      <div>
                        <div className="text-xl font-bold tabular-nums">
                          {scaledMacro.kcal}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">kcal</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold tabular-nums text-blue-600">
                          {scaledMacro.p}g
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">Prot</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold tabular-nums text-amber-600">
                          {scaledMacro.c}g
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">Carb</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold tabular-nums text-rose-500">
                          {scaledMacro.g}g
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">Grassi</div>
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* CTA aggiungi */}
              <Button
                className="w-full h-11 text-base"
                onClick={handleAdd}
                disabled={
                  addComponent.isPending ||
                  !quantita ||
                  parseFloat(quantita) <= 0 ||
                  mealId === null
                }
              >
                {addComponent.isPending ? (
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                ) : (
                  <Plus className="mr-2 h-5 w-5" />
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
