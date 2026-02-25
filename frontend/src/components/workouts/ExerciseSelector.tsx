// src/components/workouts/ExerciseSelector.tsx
"use client";

/**
 * Dialog per cercare e selezionare un esercizio dal database.
 *
 * Filosofia: INFORMARE, mai LIMITARE.
 * Il trainer (laureato in scienze motorie) decide sempre.
 *
 * UX professionale:
 * - Filtri per pattern_movimento (come ragiona il PT: squat, hinge, push, pull...)
 * - Filtri per attrezzatura disponibile
 * - Indicatori anamnesi informativi (badge, non blocchi)
 * - Ricerca per nome/categoria/attrezzatura
 * - Nessun limite artificiale: il PT vede TUTTO il catalogo
 */

import { useState, useMemo } from "react";
import { Search, X, AlertTriangle, ShieldAlert, Filter } from "lucide-react";

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
  /** Se fornita, mostra indicatori sicurezza anamnesi */
  clientAnamnesi?: AnamnesiData | null;
}

// ── Labels professionali (come ragiona il PT) ──

const DIFFICULTY_LABELS: Record<string, string> = {
  beginner: "Base",
  intermediate: "Intermedio",
  advanced: "Avanzato",
};

const PATTERN_LABELS: Record<string, string> = {
  squat: "Squat",
  hinge: "Hinge",
  push_h: "Push Orizz.",
  push_v: "Push Vert.",
  pull_h: "Pull Orizz.",
  pull_v: "Pull Vert.",
  core: "Core",
  rotation: "Rotazione",
  carry: "Carry",
};

const EQUIPMENT_LABELS: Record<string, string> = {
  bodyweight: "Corpo libero",
  barbell: "Bilanciere",
  dumbbell: "Manubri",
  kettlebell: "Kettlebell",
  cable: "Cavi",
  machine: "Macchina",
  trx: "TRX",
  band: "Elastici",
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
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null);
  const [selectedEquipment, setSelectedEquipment] = useState<string | null>(null);
  // Default OFF — il trainer vede SEMPRE tutti gli esercizi
  const [filterUnsafe, setFilterUnsafe] = useState(false);
  const { data } = useExercises();

  const exercises = data?.items ?? [];

  // E' la sezione "principale"? (mostra filtri pattern/attrezzatura)
  const isPrincipale = !categoryFilter || categoryFilter.length === 0 ||
    categoryFilter.some((c) => ["compound", "isolation", "bodyweight", "cardio"].includes(c));

  // Classificazione sicurezza (solo se anamnesi presente)
  const safetyMap = useMemo(() => {
    if (!clientAnamnesi) return null;
    return classifyExercises(exercises, clientAnamnesi);
  }, [exercises, clientAnamnesi]);

  // Pool base: esercizi filtrati per sezione (categoria)
  const sectionPool = useMemo(() => {
    if (categoryFilter && categoryFilter.length > 0) {
      return exercises.filter((e) => categoryFilter.includes(e.categoria));
    }
    return exercises;
  }, [exercises, categoryFilter]);

  // Pattern e attrezzature disponibili nella sezione corrente
  const availablePatterns = useMemo(() => {
    if (!isPrincipale) return [];
    const counts = new Map<string, number>();
    for (const ex of sectionPool) {
      const p = ex.pattern_movimento;
      if (p) counts.set(p, (counts.get(p) ?? 0) + 1);
    }
    // Ordina per count decrescente
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([pattern, count]) => ({ pattern, count }));
  }, [sectionPool, isPrincipale]);

  const availableEquipment = useMemo(() => {
    if (!isPrincipale) return [];
    const counts = new Map<string, number>();
    for (const ex of sectionPool) {
      counts.set(ex.attrezzatura, (counts.get(ex.attrezzatura) ?? 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([equip, count]) => ({ equip, count }));
  }, [sectionPool, isPrincipale]);

  // Pipeline filtraggio completa
  const filtered = useMemo(() => {
    let result = sectionPool;

    // Filtro pattern_movimento (chip attivo)
    if (selectedPattern) {
      result = result.filter((e) => e.pattern_movimento === selectedPattern);
    }

    // Filtro attrezzatura (chip attivo)
    if (selectedEquipment) {
      result = result.filter((e) => e.attrezzatura === selectedEquipment);
    }

    // Se c'e' un hint pattern_movimento (dal template slot), ordina quelli per primi
    if (patternHint && !selectedPattern) {
      result = [
        ...result.filter((e) => e.pattern_movimento === patternHint),
        ...result.filter((e) => e.pattern_movimento !== patternHint),
      ];
    }

    // Ricerca testuale
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (e) =>
          e.nome.toLowerCase().includes(q) ||
          e.categoria.toLowerCase().includes(q) ||
          e.attrezzatura.toLowerCase().includes(q) ||
          e.muscoli_primari.some((m) => m.toLowerCase().includes(q)),
      );
    }

    // Filtro opzionale controindicati (solo se attivato dal trainer)
    if (safetyMap && filterUnsafe) {
      result = result.filter((e) => safetyMap.get(e.id)?.safety !== "avoid");
    }

    // NESSUN riordinamento per safety — ordine naturale del database
    return result;
  }, [sectionPool, search, patternHint, selectedPattern, selectedEquipment, safetyMap, filterUnsafe]);

  // Contatori sicurezza (sui candidati della sezione)
  const safetyCounts = useMemo(() => {
    if (!safetyMap) return null;
    let safe = 0, caution = 0, avoid = 0;
    for (const ex of sectionPool) {
      const r = safetyMap.get(ex.id);
      if (!r || r.safety === "safe") safe++;
      else if (r.safety === "caution") caution++;
      else avoid++;
    }
    return { safe, caution, avoid };
  }, [safetyMap, sectionPool]);

  const handleSelect = (exercise: Exercise) => {
    onSelect(exercise);
    onOpenChange(false);
    setSearch("");
  };

  const resetFilters = () => {
    setSearch("");
    setSelectedPattern(null);
    setSelectedEquipment(null);
    setFilterUnsafe(false);
  };

  // Label dinamica per la sezione
  const sectionLabel = categoryFilter?.includes("avviamento")
    ? "Avviamento"
    : categoryFilter?.includes("stretching")
      ? "Stretching & Mobilita"
      : null;

  const hasActiveFilters = !!selectedPattern || !!selectedEquipment || !!search || filterUnsafe;

  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); if (!o) resetFilters(); }}>
      <DialogContent className="max-w-lg p-0">
        <DialogHeader className="px-4 pt-4 pb-0">
          <div className="flex items-center justify-between">
            <DialogTitle>
              {sectionLabel ? `Seleziona ${sectionLabel}` : "Seleziona Esercizio"}
            </DialogTitle>
            <span className="text-xs text-muted-foreground">
              {filtered.length} esercizi
            </span>
          </div>
        </DialogHeader>

        {/* Search bar */}
        <div className="relative px-4 pb-1">
          <Search className="absolute left-7 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={isPrincipale
              ? "Cerca per nome, muscolo, attrezzatura..."
              : "Cerca per nome, categoria..."
            }
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

        {/* ── Filtri pattern movimento (solo per sezione principale) ── */}
        {isPrincipale && availablePatterns.length > 0 && (
          <div className="px-4 pb-1">
            <div className="flex flex-wrap gap-1">
              {availablePatterns.map(({ pattern, count }) => (
                <button
                  key={pattern}
                  onClick={() => setSelectedPattern(selectedPattern === pattern ? null : pattern)}
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
                    selectedPattern === pattern
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  {PATTERN_LABELS[pattern] ?? pattern}
                  <span className={`text-[9px] ${selectedPattern === pattern ? "text-primary-foreground/70" : "text-muted-foreground/60"}`}>
                    {count}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Filtri attrezzatura (solo per sezione principale) ── */}
        {isPrincipale && availableEquipment.length > 0 && (
          <div className="px-4 pb-1">
            <div className="flex flex-wrap gap-1">
              {availableEquipment.map(({ equip, count }) => (
                <button
                  key={equip}
                  onClick={() => setSelectedEquipment(selectedEquipment === equip ? null : equip)}
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
                    selectedEquipment === equip
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted/40 text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  {EQUIPMENT_LABELS[equip] ?? equip}
                  <span className={`text-[9px] ${selectedEquipment === equip ? "text-primary-foreground/70" : "text-muted-foreground/60"}`}>
                    {count}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Anamnesi info bar + reset filtri ── */}
        <div className="flex items-center gap-2 px-4 pb-1 flex-wrap">
          {safetyCounts && (
            <>
              <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                <span className="text-emerald-600">{safetyCounts.safe} sicuri</span>
                <span>&middot;</span>
                <span className="text-amber-600">{safetyCounts.caution} cautela</span>
                {safetyCounts.avoid > 0 && (
                  <>
                    <span>&middot;</span>
                    <span className="text-red-600">{safetyCounts.avoid} controindicati</span>
                  </>
                )}
              </div>

              {safetyCounts.avoid > 0 && (
                <button
                  onClick={() => setFilterUnsafe((v) => !v)}
                  className={`flex items-center gap-1 text-[11px] transition-colors ${
                    filterUnsafe
                      ? "text-primary font-medium"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  title={filterUnsafe ? "Mostra tutti gli esercizi" : "Nascondi controindicati"}
                >
                  <Filter className="h-3 w-3" />
                  {filterUnsafe ? "Filtro attivo" : "Filtra"}
                </button>
              )}
            </>
          )}

          {hasActiveFilters && (
            <button
              onClick={resetFilters}
              className="ml-auto text-[11px] text-muted-foreground hover:text-foreground transition-colors"
            >
              Resetta filtri
            </button>
          )}
        </div>

        {/* Results */}
        <ScrollArea className="h-[350px] px-2 pb-2">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-2">
              <p className="text-sm text-muted-foreground">Nessun esercizio trovato</p>
              {hasActiveFilters && (
                <button
                  onClick={resetFilters}
                  className="text-xs text-primary hover:underline"
                >
                  Resetta filtri
                </button>
              )}
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
      className="flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-muted/70"
    >
      {/* Safety icon — informativo, non bloccante */}
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
          <p className="text-sm font-medium truncate">
            {exercise.nome}
          </p>
          {isAvoid && (
            <Badge className="shrink-0 bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 text-[9px] px-1.5 py-0">
              Controindicato
            </Badge>
          )}
          {isCaution && (
            <Badge className="shrink-0 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 text-[9px] px-1.5 py-0">
              Cautela
            </Badge>
          )}
        </div>
        <div className="mt-0.5 flex flex-wrap gap-1">
          <Badge variant="outline" className="text-[10px]">
            {exercise.categoria}
          </Badge>
          <Badge variant="outline" className="text-[10px]">
            {EQUIPMENT_LABELS[exercise.attrezzatura] ?? exercise.attrezzatura}
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
        {/* Motivo controindicazione — sempre visibile per avoid E caution */}
        {safety && safety.safety !== "safe" && safety.reasons.length > 0 && (
          <p className={`mt-0.5 text-[10px] truncate ${
            isAvoid ? "text-red-600 dark:text-red-400" : "text-amber-600 dark:text-amber-400"
          }`}>
            {safety.reasons[0]}
          </p>
        )}
      </div>
    </button>
  );
}
