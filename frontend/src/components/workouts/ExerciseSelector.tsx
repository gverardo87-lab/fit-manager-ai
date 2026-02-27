// src/components/workouts/ExerciseSelector.tsx
"use client";

/**
 * Dialog professionale per selezione esercizi nel workout builder.
 *
 * Filtri multi-dimensione (tutti dinamici — mostrano solo opzioni presenti nel pool):
 * - Pattern movimento (come ragiona il PT: squat, hinge, push, pull...)
 * - Gruppo muscolare (tassonomia anatomica, ordinamento regione corpo)
 * - Attrezzatura disponibile
 * - Difficolta (base/intermedio/avanzato)
 * - Biomeccanica avanzata (collapsibile): tipo forza, lateralita
 *
 * Ricerca testuale: nome + muscoli (italiano e inglese) + attrezzatura (italiano).
 */

import { useState, useMemo } from "react";
import { Search, X, ChevronDown, SlidersHorizontal } from "lucide-react";

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
import {
  MUSCLE_LABELS,
  EQUIPMENT_LABELS,
  DIFFICULTY_LABELS,
  FORCE_TYPE_LABELS,
  LATERAL_PATTERN_LABELS,
} from "@/components/exercises/exercise-constants";

interface ExerciseSelectorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (exercise: Exercise) => void;
  patternHint?: string;
  /** Filtra per categorie specifiche (es. ["stretching", "mobilita"]) */
  categoryFilter?: string[];
}

// ── Chip labels compatte per pattern ──

const PATTERN_CHIP_LABELS: Record<string, string> = {
  squat: "Squat",
  hinge: "Hinge",
  push_h: "Push Orizz.",
  push_v: "Push Vert.",
  pull_h: "Pull Orizz.",
  pull_v: "Pull Vert.",
  core: "Core",
  rotation: "Rotazione",
  carry: "Carry",
  warmup: "Warmup",
  stretch: "Stretch",
  mobility: "Mobilita",
};

// ── Ordinamento anatomico per chip muscoli ──

const MUSCLE_SORT_ORDER: string[] = [
  // Upper body — push
  "chest", "shoulders", "triceps",
  // Upper body — pull
  "back", "lats", "traps", "biceps", "forearms",
  // Lower body
  "quadriceps", "hamstrings", "glutes", "adductors", "calves",
  // Core
  "core",
];

// ── Ordinamento logico per filtri a opzioni fisse ──

const DIFFICULTY_ORDER: string[] = ["beginner", "intermediate", "advanced"];
const FORCE_TYPE_ORDER: string[] = ["push", "pull", "static"];
const LATERAL_ORDER: string[] = ["bilateral", "unilateral", "alternating"];

// ════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════

export function ExerciseSelector({
  open,
  onOpenChange,
  onSelect,
  patternHint,
  categoryFilter,
}: ExerciseSelectorProps) {
  // ── Filter state ──
  const [search, setSearch] = useState("");
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null);
  const [selectedMuscle, setSelectedMuscle] = useState<string | null>(null);
  const [selectedEquipment, setSelectedEquipment] = useState<string | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string | null>(null);
  const [selectedForceType, setSelectedForceType] = useState<string | null>(null);
  const [selectedLateral, setSelectedLateral] = useState<string | null>(null);
  const [showBiomechanics, setShowBiomechanics] = useState(false);
  const [showFilters, setShowFilters] = useState(true);

  const { data } = useExercises();
  const exercises = data?.items ?? [];

  // E' la sezione "principale"? (mostra set completo di filtri)
  const isPrincipale = !categoryFilter || categoryFilter.length === 0 ||
    categoryFilter.some((c) => ["compound", "isolation", "bodyweight", "cardio"].includes(c));

  // ── Section pool: base filter by category ──

  const sectionPool = useMemo(() => {
    if (categoryFilter && categoryFilter.length > 0) {
      return exercises.filter((e) => categoryFilter.includes(e.categoria));
    }
    return exercises;
  }, [exercises, categoryFilter]);

  // ── Available filter options (dynamic from current pool) ──

  const availablePatterns = useMemo(() => {
    if (!isPrincipale) return [];
    const counts = new Map<string, number>();
    for (const ex of sectionPool) {
      if (ex.pattern_movimento) {
        counts.set(ex.pattern_movimento, (counts.get(ex.pattern_movimento) ?? 0) + 1);
      }
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([value, count]) => ({ value, count }));
  }, [sectionPool, isPrincipale]);

  const availableMuscles = useMemo(() => {
    const counts = new Map<string, number>();
    for (const ex of sectionPool) {
      for (const m of ex.muscoli_primari) {
        counts.set(m, (counts.get(m) ?? 0) + 1);
      }
    }
    // Ordinamento anatomico (non per frequenza)
    return MUSCLE_SORT_ORDER
      .filter((m) => counts.has(m))
      .map((m) => ({ value: m, count: counts.get(m)! }));
  }, [sectionPool]);

  const availableEquipment = useMemo(() => {
    if (!isPrincipale) return [];
    const counts = new Map<string, number>();
    for (const ex of sectionPool) {
      counts.set(ex.attrezzatura, (counts.get(ex.attrezzatura) ?? 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([value, count]) => ({ value, count }));
  }, [sectionPool, isPrincipale]);

  const availableDifficulties = useMemo(() => {
    if (!isPrincipale) return [];
    const counts = new Map<string, number>();
    for (const ex of sectionPool) {
      counts.set(ex.difficolta, (counts.get(ex.difficolta) ?? 0) + 1);
    }
    return DIFFICULTY_ORDER
      .filter((d) => counts.has(d))
      .map((d) => ({ value: d, count: counts.get(d)! }));
  }, [sectionPool, isPrincipale]);

  const availableForceTypes = useMemo(() => {
    const counts = new Map<string, number>();
    for (const ex of sectionPool) {
      if (ex.force_type) counts.set(ex.force_type, (counts.get(ex.force_type) ?? 0) + 1);
    }
    return FORCE_TYPE_ORDER
      .filter((f) => counts.has(f))
      .map((f) => ({ value: f, count: counts.get(f)! }));
  }, [sectionPool]);

  const availableLaterals = useMemo(() => {
    const counts = new Map<string, number>();
    for (const ex of sectionPool) {
      if (ex.lateral_pattern) counts.set(ex.lateral_pattern, (counts.get(ex.lateral_pattern) ?? 0) + 1);
    }
    return LATERAL_ORDER
      .filter((l) => counts.has(l))
      .map((l) => ({ value: l, count: counts.get(l)! }));
  }, [sectionPool]);

  // ── Filtering pipeline (6 dimensioni + search) ──

  const filtered = useMemo(() => {
    let result = sectionPool;

    // Chip filters
    if (selectedPattern) result = result.filter((e) => e.pattern_movimento === selectedPattern);
    if (selectedMuscle) result = result.filter((e) => e.muscoli_primari.includes(selectedMuscle));
    if (selectedEquipment) result = result.filter((e) => e.attrezzatura === selectedEquipment);
    if (selectedDifficulty) result = result.filter((e) => e.difficolta === selectedDifficulty);
    if (selectedForceType) result = result.filter((e) => e.force_type === selectedForceType);
    if (selectedLateral) result = result.filter((e) => e.lateral_pattern === selectedLateral);

    // Pattern hint ordering (dal template slot)
    if (patternHint && !selectedPattern) {
      result = [
        ...result.filter((e) => e.pattern_movimento === patternHint),
        ...result.filter((e) => e.pattern_movimento !== patternHint),
      ];
    }

    // Ricerca testuale (nome + muscoli IT/EN + attrezzatura IT + categoria)
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((e) =>
        e.nome.toLowerCase().includes(q) ||
        e.categoria.toLowerCase().includes(q) ||
        e.attrezzatura.toLowerCase().includes(q) ||
        (EQUIPMENT_LABELS[e.attrezzatura] ?? "").toLowerCase().includes(q) ||
        e.muscoli_primari.some((m) => m.toLowerCase().includes(q)) ||
        e.muscoli_primari.some((m) => (MUSCLE_LABELS[m] ?? "").toLowerCase().includes(q)),
      );
    }

    return result;
  }, [sectionPool, search, patternHint, selectedPattern, selectedMuscle,
      selectedEquipment, selectedDifficulty, selectedForceType, selectedLateral]);

  // ── Handlers ──

  const handleSelect = (exercise: Exercise) => {
    onSelect(exercise);
    onOpenChange(false);
    resetFilters();
  };

  const resetFilters = () => {
    setSearch("");
    setSelectedPattern(null);
    setSelectedMuscle(null);
    setSelectedEquipment(null);
    setSelectedDifficulty(null);
    setSelectedForceType(null);
    setSelectedLateral(null);
    setShowBiomechanics(false);
  };

  const sectionLabel = categoryFilter?.includes("avviamento")
    ? "Avviamento"
    : categoryFilter?.includes("stretching")
      ? "Stretching & Mobilita"
      : null;

  const hasActiveFilters = !!selectedPattern || !!selectedEquipment || !!selectedMuscle ||
    !!selectedDifficulty || !!selectedForceType || !!selectedLateral || !!search;

  // Conteggio filtri chip attivi (esclusa ricerca testo)
  const activeFilterCount = [selectedPattern, selectedMuscle, selectedEquipment,
    selectedDifficulty, selectedForceType, selectedLateral].filter(Boolean).length;

  // Riepilogo filtri attivi (per riga compatta quando collassati)
  const activeFilterTags = useMemo(() => {
    const tags: { label: string; clear: () => void }[] = [];
    if (selectedPattern) tags.push({ label: PATTERN_CHIP_LABELS[selectedPattern] ?? selectedPattern, clear: () => setSelectedPattern(null) });
    if (selectedMuscle) tags.push({ label: MUSCLE_LABELS[selectedMuscle] ?? selectedMuscle, clear: () => setSelectedMuscle(null) });
    if (selectedEquipment) tags.push({ label: EQUIPMENT_LABELS[selectedEquipment] ?? selectedEquipment, clear: () => setSelectedEquipment(null) });
    if (selectedDifficulty) tags.push({ label: DIFFICULTY_LABELS[selectedDifficulty] ?? selectedDifficulty, clear: () => setSelectedDifficulty(null) });
    if (selectedForceType) tags.push({ label: FORCE_TYPE_LABELS[selectedForceType] ?? selectedForceType, clear: () => setSelectedForceType(null) });
    if (selectedLateral) tags.push({ label: LATERAL_PATTERN_LABELS[selectedLateral] ?? selectedLateral, clear: () => setSelectedLateral(null) });
    return tags;
  }, [selectedPattern, selectedMuscle, selectedEquipment, selectedDifficulty, selectedForceType, selectedLateral]);

  const hasBiomechanicsData = availableForceTypes.length > 0 || availableLaterals.length > 0;

  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); if (!o) resetFilters(); }}>
      <DialogContent className="max-w-xl p-0">
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

        {/* Search bar + filter toggle */}
        <div className="flex items-center gap-2 px-4 pb-1">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Cerca per nome, muscolo, attrezzatura..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
              autoFocus
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          <button
            onClick={() => setShowFilters((v) => !v)}
            className={`flex items-center gap-1 rounded-md border px-2 py-1.5 text-xs transition-colors ${
              showFilters
                ? "border-primary/30 bg-primary/10 text-primary"
                : "border-muted-foreground/20 text-muted-foreground hover:text-foreground hover:border-muted-foreground/40"
            }`}
            title={showFilters ? "Nascondi filtri" : "Mostra filtri"}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            {activeFilterCount > 0 && (
              <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground px-1">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>

        {/* ── Active filter tags (visibili quando filtri collassati) ── */}
        {!showFilters && activeFilterTags.length > 0 && (
          <div className="flex flex-wrap gap-1 px-4 pb-1">
            {activeFilterTags.map((tag) => (
              <button
                key={tag.label}
                onClick={tag.clear}
                className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary transition-colors hover:bg-primary/20"
              >
                {tag.label}
                <X className="h-2.5 w-2.5" />
              </button>
            ))}
            <button
              onClick={resetFilters}
              className="text-[10px] text-muted-foreground hover:text-foreground transition-colors px-1"
            >
              Resetta
            </button>
          </div>
        )}

        {/* ── Collapsible filter section ── */}
        {showFilters && (
          <>
            {/* ── Pattern chips (solo principale) ── */}
            {isPrincipale && availablePatterns.length > 0 && (
              <FilterChipRow
                items={availablePatterns}
                selected={selectedPattern}
                onToggle={(v) => setSelectedPattern(selectedPattern === v ? null : v)}
                labelMap={PATTERN_CHIP_LABELS}
              />
            )}

            {/* ── Muscle group chips (tutte le sezioni — il PT pensa per muscolo) ── */}
            {availableMuscles.length > 0 && (
              <FilterChipRow
                items={availableMuscles}
                selected={selectedMuscle}
                onToggle={(v) => setSelectedMuscle(selectedMuscle === v ? null : v)}
                labelMap={MUSCLE_LABELS}
                variant="soft"
              />
            )}

            {/* ── Equipment chips (solo principale) ── */}
            {isPrincipale && availableEquipment.length > 0 && (
              <FilterChipRow
                items={availableEquipment}
                selected={selectedEquipment}
                onToggle={(v) => setSelectedEquipment(selectedEquipment === v ? null : v)}
                labelMap={EQUIPMENT_LABELS}
              />
            )}

            {/* ── Difficulty + Biomechanics toggle (solo principale) ── */}
            {isPrincipale && (availableDifficulties.length > 0 || hasBiomechanicsData) && (
              <div className="flex items-center gap-1 px-4 pb-1 flex-wrap">
                {availableDifficulties.map(({ value, count }) => (
                  <button
                    key={value}
                    onClick={() => setSelectedDifficulty(selectedDifficulty === value ? null : value)}
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
                      selectedDifficulty === value
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted/40 text-muted-foreground hover:bg-muted hover:text-foreground"
                    }`}
                  >
                    {DIFFICULTY_LABELS[value] ?? value}
                    <span className={`text-[9px] ${selectedDifficulty === value ? "text-primary-foreground/70" : "text-muted-foreground/60"}`}>
                      {count}
                    </span>
                  </button>
                ))}

                {hasBiomechanicsData && (
                  <button
                    onClick={() => setShowBiomechanics(!showBiomechanics)}
                    className={`ml-auto inline-flex items-center gap-1 text-[11px] transition-colors ${
                      showBiomechanics || selectedForceType || selectedLateral
                        ? "text-primary font-medium"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <ChevronDown className={`h-3 w-3 transition-transform ${showBiomechanics ? "rotate-180" : ""}`} />
                    Biomeccanica
                  </button>
                )}
              </div>
            )}

            {/* ── Biomechanics expanded section ── */}
            {showBiomechanics && (
              <div className="px-4 pb-1 space-y-1">
                {availableForceTypes.length > 0 && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-muted-foreground w-16 shrink-0">Forza</span>
                    <div className="flex flex-wrap gap-1">
                      {availableForceTypes.map(({ value, count }) => (
                        <button
                          key={value}
                          onClick={() => setSelectedForceType(selectedForceType === value ? null : value)}
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium transition-colors ${
                            selectedForceType === value
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted/40 text-muted-foreground hover:bg-muted hover:text-foreground"
                          }`}
                        >
                          {FORCE_TYPE_LABELS[value] ?? value}
                          <span className={`text-[8px] ${selectedForceType === value ? "text-primary-foreground/70" : "text-muted-foreground/60"}`}>
                            {count}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {availableLaterals.length > 0 && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-muted-foreground w-16 shrink-0">Lateralita</span>
                    <div className="flex flex-wrap gap-1">
                      {availableLaterals.map(({ value, count }) => (
                        <button
                          key={value}
                          onClick={() => setSelectedLateral(selectedLateral === value ? null : value)}
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium transition-colors ${
                            selectedLateral === value
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted/40 text-muted-foreground hover:bg-muted hover:text-foreground"
                          }`}
                        >
                          {LATERAL_PATTERN_LABELS[value] ?? value}
                          <span className={`text-[8px] ${selectedLateral === value ? "text-primary-foreground/70" : "text-muted-foreground/60"}`}>
                            {count}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── Reset filtri ── */}
            {hasActiveFilters && (
              <div className="flex items-center px-4 pb-1">
                <button
                  onClick={resetFilters}
                  className="ml-auto text-[11px] text-muted-foreground hover:text-foreground transition-colors"
                >
                  Resetta filtri
                </button>
              </div>
            )}
          </>
        )}

        {/* Results */}
        <ScrollArea className="h-[45vh] min-h-[280px] px-2 pb-2">
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
              {filtered.map((exercise) => (
                <ExerciseRow
                  key={exercise.id}
                  exercise={exercise}
                  onSelect={handleSelect}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

// ════════════════════════════════════════════════════════════
// FILTER CHIP ROW (sub-component riusabile)
// ════════════════════════════════════════════════════════════

function FilterChipRow({
  items,
  selected,
  onToggle,
  labelMap,
  variant = "default",
}: {
  items: { value: string; count: number }[];
  selected: string | null;
  onToggle: (value: string) => void;
  labelMap: Record<string, string>;
  variant?: "default" | "soft";
}) {
  const inactiveBg = variant === "soft" ? "bg-muted/30" : "bg-muted/60";

  return (
    <div className="px-4 pb-1">
      <div className="flex flex-wrap gap-1">
        {items.map(({ value, count }) => (
          <button
            key={value}
            onClick={() => onToggle(value)}
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
              selected === value
                ? "bg-primary text-primary-foreground"
                : `${inactiveBg} text-muted-foreground hover:bg-muted hover:text-foreground`
            }`}
          >
            {labelMap[value] ?? value}
            <span className={`text-[9px] ${
              selected === value ? "text-primary-foreground/70" : "text-muted-foreground/60"
            }`}>
              {count}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// EXERCISE ROW (sub-component)
// ════════════════════════════════════════════════════════════

function ExerciseRow({
  exercise,
  onSelect,
}: {
  exercise: Exercise;
  onSelect: (e: Exercise) => void;
}) {
  // Muscoli in italiano
  const muscleLabel = exercise.muscoli_primari
    .map((m) => MUSCLE_LABELS[m] ?? m)
    .join(", ");

  // Metadata biomeccanica inline (force type + lateral pattern)
  const metaParts: string[] = [];
  if (exercise.force_type && FORCE_TYPE_LABELS[exercise.force_type]) {
    metaParts.push(FORCE_TYPE_LABELS[exercise.force_type]);
  }
  if (exercise.lateral_pattern && LATERAL_PATTERN_LABELS[exercise.lateral_pattern]) {
    metaParts.push(LATERAL_PATTERN_LABELS[exercise.lateral_pattern]);
  }

  return (
    <button
      onClick={() => onSelect(exercise)}
      className="flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-muted/70"
    >
      <div className="min-w-0 flex-1">
        {/* Row 1: Nome */}
        <p className="text-sm font-medium truncate">{exercise.nome}</p>

        {/* Row 2: Classification badges */}
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

        {/* Row 3: Muscoli (IT) + tipo forza + lateralita */}
        {(muscleLabel || metaParts.length > 0) && (
          <p className="mt-0.5 text-[11px] text-muted-foreground truncate">
            {muscleLabel}
            {muscleLabel && metaParts.length > 0 && " · "}
            {metaParts.join(" · ")}
          </p>
        )}
      </div>
    </button>
  );
}
