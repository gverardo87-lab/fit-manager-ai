// src/components/workouts/ExerciseSelector.tsx
"use client";

/**
 * Dialog/Popover per cercare e selezionare un esercizio dal database.
 * Ricerca per nome + filtri rapidi (categoria, attrezzatura).
 * Risultati mostrano nome + categoria + difficolta' + muscoli primari.
 */

import { useState, useMemo } from "react";
import { Search, X } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

import { useExercises } from "@/hooks/useExercises";
import type { Exercise } from "@/types/api";

interface ExerciseSelectorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (exercise: Exercise) => void;
  patternHint?: string;
  /** Filtra per categorie specifiche (es. ["stretching", "mobilita"]) */
  categoryFilter?: string[];
}

const DIFFICULTY_LABELS: Record<string, string> = {
  beginner: "Base",
  intermediate: "Intermedio",
  advanced: "Avanzato",
};

export function ExerciseSelector({
  open,
  onOpenChange,
  onSelect,
  patternHint,
  categoryFilter,
}: ExerciseSelectorProps) {
  const [search, setSearch] = useState("");
  const { data } = useExercises();

  const exercises = data?.items ?? [];

  // Filtra per nome e categoria (client-side, gia' tutti in memoria)
  const filtered = useMemo(() => {
    let result = exercises;

    // Filtro per categorie (es. solo avviamento o solo stretching/mobilita)
    if (categoryFilter && categoryFilter.length > 0) {
      result = result.filter((e) => categoryFilter.includes(e.categoria));
    }

    // Se c'e' un hint pattern_movimento, ordina quelli per primi
    if (patternHint) {
      result = [
        ...result.filter((e) => e.pattern_movimento === patternHint),
        ...result.filter((e) => e.pattern_movimento !== patternHint),
      ];
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (e) =>
          e.nome.toLowerCase().includes(q) ||
          e.categoria.toLowerCase().includes(q) ||
          e.attrezzatura.toLowerCase().includes(q),
      );
    }

    return result.slice(0, 50); // Limita per performance
  }, [exercises, search, patternHint, categoryFilter]);

  const handleSelect = (exercise: Exercise) => {
    onSelect(exercise);
    onOpenChange(false);
    setSearch("");
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); if (!o) setSearch(""); }}>
      <DialogContent className="max-w-lg p-0">
        <DialogHeader className="px-4 pt-4 pb-0">
          <DialogTitle>Seleziona Esercizio</DialogTitle>
        </DialogHeader>

        {/* Search bar */}
        <div className="relative px-4 pb-2">
          <Search className="absolute left-7 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Cerca per nome, categoria, attrezzatura..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            autoFocus
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-7 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {patternHint && (
          <div className="px-4 pb-1">
            <Badge variant="outline" className="text-xs">
              Suggerito: {patternHint}
            </Badge>
          </div>
        )}

        {/* Results */}
        <ScrollArea className="h-[350px] px-2 pb-2">
          {filtered.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
              Nessun esercizio trovato
            </div>
          ) : (
            <div className="space-y-0.5">
              {filtered.map((exercise) => (
                <button
                  key={exercise.id}
                  onClick={() => handleSelect(exercise)}
                  className="flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-muted/70"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{exercise.nome}</p>
                    <div className="mt-0.5 flex flex-wrap gap-1">
                      <Badge variant="outline" className="text-[10px]">
                        {exercise.categoria}
                      </Badge>
                      <Badge variant="outline" className="text-[10px]">
                        {exercise.attrezzatura}
                      </Badge>
                      <Badge variant="outline" className="text-[10px]">
                        {DIFFICULTY_LABELS[exercise.difficolta] ?? exercise.difficolta}
                      </Badge>
                    </div>
                    {exercise.muscoli_primari.length > 0 && (
                      <p className="mt-0.5 text-[11px] text-muted-foreground truncate">
                        {exercise.muscoli_primari.join(", ")}
                      </p>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
