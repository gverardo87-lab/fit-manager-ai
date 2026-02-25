// src/components/workouts/ExerciseSelector.tsx
"use client";

/**
 * Dialog per cercare e selezionare un esercizio dal database.
 * Ricerca per nome + filtri rapidi (categoria, attrezzatura).
 *
 * Se `clientAnamnesi` fornita: classifica esercizi come safe/caution/avoid
 * e mostra indicatori visivi + toggle per nascondere controindicati.
 */

import { useState, useMemo } from "react";
import { Search, X, AlertTriangle, ShieldAlert, Eye, EyeOff } from "lucide-react";

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
import type { AnamnesiData, Exercise } from "@/types/api";
import {
  classifyExercises,
  type SafetyResult,
} from "@/lib/contraindication-engine";

interface ExerciseSelectorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (exercise: Exercise) => void;
  patternHint?: string;
  /** Filtra per categorie specifiche (es. ["stretching", "mobilita"]) */
  categoryFilter?: string[];
  /** Se fornita, attiva lo scudo protettivo anamnesi */
  clientAnamnesi?: AnamnesiData | null;
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
  clientAnamnesi,
}: ExerciseSelectorProps) {
  const [search, setSearch] = useState("");
  const [hideAvoided, setHideAvoided] = useState(true);
  const { data } = useExercises();

  const exercises = data?.items ?? [];

  // Classificazione sicurezza (solo se anamnesi presente)
  const safetyMap = useMemo(() => {
    if (!clientAnamnesi) return null;
    return classifyExercises(exercises, clientAnamnesi);
  }, [exercises, clientAnamnesi]);

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

    // Filtra e ordina per sicurezza (se anamnesi attiva)
    if (safetyMap) {
      if (hideAvoided) {
        result = result.filter((e) => safetyMap.get(e.id)?.safety !== "avoid");
      }
      // Ordina: safe → caution → avoid
      const order = { safe: 0, caution: 1, avoid: 2 };
      result = [...result].sort((a, b) => {
        const sa = order[safetyMap.get(a.id)?.safety ?? "safe"];
        const sb = order[safetyMap.get(b.id)?.safety ?? "safe"];
        return sa - sb;
      });
    }

    return result.slice(0, 50); // Limita per performance
  }, [exercises, search, patternHint, categoryFilter, safetyMap, hideAvoided]);

  // Contatori sicurezza
  const safetyCounts = useMemo(() => {
    if (!safetyMap) return null;
    let safe = 0, caution = 0, avoid = 0;
    for (const [, r] of safetyMap) {
      if (r.safety === "safe") safe++;
      else if (r.safety === "caution") caution++;
      else avoid++;
    }
    return { safe, caution, avoid };
  }, [safetyMap]);

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

        {/* Hints + Safety bar */}
        <div className="flex items-center gap-2 px-4 pb-1 flex-wrap">
          {patternHint && (
            <Badge variant="outline" className="text-xs">
              Suggerito: {patternHint}
            </Badge>
          )}

          {safetyCounts && (
            <>
              <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground ml-auto">
                <span className="text-emerald-600">{safetyCounts.safe} sicuri</span>
                <span>&middot;</span>
                <span className="text-amber-600">{safetyCounts.caution} attenzione</span>
                <span>&middot;</span>
                <span className="text-red-600">{safetyCounts.avoid} controindicati</span>
              </div>
              <button
                onClick={() => setHideAvoided((v) => !v)}
                className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
                title={hideAvoided ? "Mostra controindicati" : "Nascondi controindicati"}
              >
                {hideAvoided ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                {hideAvoided ? "Nascosti" : "Visibili"}
              </button>
            </>
          )}
        </div>

        {/* Results */}
        <ScrollArea className="h-[350px] px-2 pb-2">
          {filtered.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
              Nessun esercizio trovato
            </div>
          ) : (
            <div className="space-y-0.5">
              {filtered.map((exercise) => {
                const safety = safetyMap?.get(exercise.id);
                return (
                  <ExerciseRow
                    key={exercise.id}
                    exercise={exercise}
                    safety={safety}
                    onSelect={handleSelect}
                  />
                );
              })}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

// ════════════════════════════════════════════════════════════
// EXERCISE ROW (sub-component)
// ════════════════════════════════════════════════════════════

function ExerciseRow({
  exercise,
  safety,
  onSelect,
}: {
  exercise: Exercise;
  safety?: SafetyResult;
  onSelect: (e: Exercise) => void;
}) {
  const isAvoid = safety?.safety === "avoid";
  const isCaution = safety?.safety === "caution";

  return (
    <button
      onClick={() => onSelect(exercise)}
      className={`flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-muted/70 ${
        isAvoid ? "opacity-50" : ""
      }`}
    >
      {/* Safety icon */}
      {safety && safety.safety !== "safe" && (
        <div className="mt-0.5 shrink-0" title={safety.reasons.join("\n")}>
          {isAvoid ? (
            <ShieldAlert className="h-4 w-4 text-red-500" />
          ) : isCaution ? (
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          ) : null}
        </div>
      )}

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <p className={`text-sm font-medium truncate ${isAvoid ? "text-red-600 dark:text-red-400" : ""}`}>
            {exercise.nome}
          </p>
          {isAvoid && (
            <Badge className="shrink-0 bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 text-[9px] px-1.5 py-0">
              Controindicato
            </Badge>
          )}
          {isCaution && (
            <Badge className="shrink-0 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 text-[9px] px-1.5 py-0">
              Attenzione
            </Badge>
          )}
        </div>
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
        {/* Motivo cautela (compatto, una riga) */}
        {isCaution && safety && safety.reasons.length > 0 && (
          <p className="mt-0.5 text-[10px] text-amber-600 dark:text-amber-400 truncate">
            {safety.reasons[0]}
          </p>
        )}
      </div>
    </button>
  );
}
