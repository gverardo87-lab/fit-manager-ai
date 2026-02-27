// src/app/(dashboard)/esercizi/page.tsx
"use client";

/**
 * Pagina Archivio Esercizi.
 *
 * Layout:
 * - Header con titolo + conteggio + "Nuovo Esercizio"
 * - KPI cards (totale, custom, attrezzature, per categoria)
 * - FilterBar chip interattivi (pattern Clienti/Agenda):
 *     Categoria (multi-toggle) + Movimento/Muscolo/Attrezzatura/Livello (select-one)
 *     + Biomeccanica collapsibile (Forza + Lateralita)
 * - Ricerca testuale (livello pagina)
 * - ExercisesTable con dati pre-filtrati
 * - Sheet per crea/modifica + Dialog per elimina
 */

import { useState, useMemo, useCallback } from "react";
import {
  Plus,
  Dumbbell,
  Layers,
  User,
  Activity,
  Eye,
  EyeOff,
  Search,
  X,
  ChevronDown,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

import { ExercisesTable } from "@/components/exercises/ExercisesTable";
import { ExerciseSheet } from "@/components/exercises/ExerciseSheet";
import { DeleteExerciseDialog } from "@/components/exercises/DeleteExerciseDialog";
import { useExercises } from "@/hooks/useExercises";
import {
  CATEGORY_OPTIONS,
  CATEGORY_LABELS,
  CATEGORY_CHIP_COLORS,
  EQUIPMENT_LABELS,
  DIFFICULTY_LABELS,
  MUSCLE_LABELS,
  FORCE_TYPE_LABELS,
  LATERAL_PATTERN_LABELS,
} from "@/components/exercises/exercise-constants";
import type { Exercise } from "@/types/api";

// ════════════════════════════════════════════════════════════
// COSTANTI FILTRI
// ════════════════════════════════════════════════════════════

// Label compatte per pattern_movimento (chip)
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

// Ordinamento anatomico per muscoli (regione corpo)
const MUSCLE_SORT_ORDER: string[] = [
  "chest", "shoulders", "triceps",
  "back", "lats", "traps", "biceps", "forearms",
  "quadriceps", "hamstrings", "glutes", "adductors", "calves",
  "core",
];

const DIFFICULTY_ORDER: string[] = ["beginner", "intermediate", "advanced"];
const FORCE_TYPE_ORDER: string[] = ["push", "pull", "static"];
const LATERAL_ORDER: string[] = ["bilateral", "unilateral", "alternating"];

// Tutte le categorie disponibili per il multi-toggle
const ALL_CATEGORIES = CATEGORY_OPTIONS.map((o) => o.value);

// ════════════════════════════════════════════════════════════
// KPI HELPER
// ════════════════════════════════════════════════════════════

function useExerciseKpi(exercises: Exercise[]) {
  return useMemo(() => {
    const total = exercises.length;
    const custom = exercises.filter((e) => !e.is_builtin).length;
    const byCategory = exercises.reduce<Record<string, number>>((acc, e) => {
      acc[e.categoria] = (acc[e.categoria] ?? 0) + 1;
      return acc;
    }, {});
    const equipmentCount = new Set(exercises.map((e) => e.attrezzatura)).size;

    return { total, custom, byCategory, equipmentCount };
  }, [exercises]);
}

// ════════════════════════════════════════════════════════════
// PAGE COMPONENT
// ════════════════════════════════════════════════════════════

export default function EserciziPage() {
  // Carica TUTTI gli esercizi (client-side filtering, come ExerciseSelector)
  const { data, isLoading, isError, refetch } = useExercises();

  // Sheet/Dialog state
  const [sheetOpen, setSheetOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedExercise, setSelectedExercise] = useState<Exercise | null>(null);

  // ── Filter state ──
  const [activeCategories, setActiveCategories] = useState<Set<string>>(
    () => new Set(ALL_CATEGORIES)
  );
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null);
  const [selectedMuscle, setSelectedMuscle] = useState<string | null>(null);
  const [selectedEquipment, setSelectedEquipment] = useState<string | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string | null>(null);
  const [selectedForceType, setSelectedForceType] = useState<string | null>(null);
  const [selectedLateral, setSelectedLateral] = useState<string | null>(null);
  const [showBiomechanics, setShowBiomechanics] = useState(false);
  const [search, setSearch] = useState("");

  const allExercises = data?.items ?? [];
  const kpi = useExerciseKpi(allExercises);

  // ── Pool post-categoria (base per chip dinamici) ──

  const categoryPool = useMemo(() => {
    if (activeCategories.size === ALL_CATEGORIES.length) return allExercises;
    return allExercises.filter((e) => activeCategories.has(e.categoria));
  }, [allExercises, activeCategories]);

  // ── Available filter options (dinamici dal pool post-categoria) ──

  const availablePatterns = useMemo(() => {
    const counts = new Map<string, number>();
    for (const ex of categoryPool) {
      if (ex.pattern_movimento) {
        counts.set(ex.pattern_movimento, (counts.get(ex.pattern_movimento) ?? 0) + 1);
      }
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([value, count]) => ({ value, count }));
  }, [categoryPool]);

  const availableMuscles = useMemo(() => {
    const counts = new Map<string, number>();
    for (const ex of categoryPool) {
      for (const m of ex.muscoli_primari) {
        counts.set(m, (counts.get(m) ?? 0) + 1);
      }
    }
    return MUSCLE_SORT_ORDER
      .filter((m) => counts.has(m))
      .map((m) => ({ value: m, count: counts.get(m)! }));
  }, [categoryPool]);

  const availableEquipment = useMemo(() => {
    const counts = new Map<string, number>();
    for (const ex of categoryPool) {
      counts.set(ex.attrezzatura, (counts.get(ex.attrezzatura) ?? 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([value, count]) => ({ value, count }));
  }, [categoryPool]);

  const availableDifficulties = useMemo(() => {
    const counts = new Map<string, number>();
    for (const ex of categoryPool) {
      counts.set(ex.difficolta, (counts.get(ex.difficolta) ?? 0) + 1);
    }
    return DIFFICULTY_ORDER
      .filter((d) => counts.has(d))
      .map((d) => ({ value: d, count: counts.get(d)! }));
  }, [categoryPool]);

  const availableForceTypes = useMemo(() => {
    const counts = new Map<string, number>();
    for (const ex of categoryPool) {
      if (ex.force_type) counts.set(ex.force_type, (counts.get(ex.force_type) ?? 0) + 1);
    }
    return FORCE_TYPE_ORDER
      .filter((f) => counts.has(f))
      .map((f) => ({ value: f, count: counts.get(f)! }));
  }, [categoryPool]);

  const availableLaterals = useMemo(() => {
    const counts = new Map<string, number>();
    for (const ex of categoryPool) {
      if (ex.lateral_pattern) counts.set(ex.lateral_pattern, (counts.get(ex.lateral_pattern) ?? 0) + 1);
    }
    return LATERAL_ORDER
      .filter((l) => counts.has(l))
      .map((l) => ({ value: l, count: counts.get(l)! }));
  }, [categoryPool]);

  const hasBiomechanicsData = availableForceTypes.length > 0 || availableLaterals.length > 0;

  // ── Filtering pipeline ──

  const filtered = useMemo(() => {
    let result = categoryPool;

    if (selectedPattern) result = result.filter((e) => e.pattern_movimento === selectedPattern);
    if (selectedMuscle) result = result.filter((e) => e.muscoli_primari.includes(selectedMuscle));
    if (selectedEquipment) result = result.filter((e) => e.attrezzatura === selectedEquipment);
    if (selectedDifficulty) result = result.filter((e) => e.difficolta === selectedDifficulty);
    if (selectedForceType) result = result.filter((e) => e.force_type === selectedForceType);
    if (selectedLateral) result = result.filter((e) => e.lateral_pattern === selectedLateral);

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((e) =>
        e.nome.toLowerCase().includes(q) ||
        e.nome_en?.toLowerCase().includes(q) ||
        e.muscoli_primari.some((m) => m.toLowerCase().includes(q)) ||
        e.muscoli_primari.some((m) => (MUSCLE_LABELS[m] ?? "").toLowerCase().includes(q)) ||
        e.attrezzatura.toLowerCase().includes(q) ||
        (EQUIPMENT_LABELS[e.attrezzatura] ?? "").toLowerCase().includes(q),
      );
    }

    return result;
  }, [categoryPool, selectedPattern, selectedMuscle, selectedEquipment,
      selectedDifficulty, selectedForceType, selectedLateral, search]);

  // ── Stato filtri ──

  const isFiltered = activeCategories.size < ALL_CATEGORIES.length ||
    !!selectedPattern || !!selectedMuscle || !!selectedEquipment ||
    !!selectedDifficulty || !!selectedForceType || !!selectedLateral || !!search;

  const resetFilters = useCallback(() => {
    setActiveCategories(new Set(ALL_CATEGORIES));
    setSelectedPattern(null);
    setSelectedMuscle(null);
    setSelectedEquipment(null);
    setSelectedDifficulty(null);
    setSelectedForceType(null);
    setSelectedLateral(null);
    setShowBiomechanics(false);
    setSearch("");
  }, []);

  // ── Handlers ──

  const handleToggleCategory = useCallback((key: string) => {
    setActiveCategories((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
    // Reset filtri dipendenti quando cambia la base
    setSelectedPattern(null);
    setSelectedMuscle(null);
    setSelectedEquipment(null);
    setSelectedDifficulty(null);
    setSelectedForceType(null);
    setSelectedLateral(null);
  }, []);

  const handleNewExercise = useCallback(() => {
    setSelectedExercise(null);
    setSheetOpen(true);
  }, []);

  const handleEdit = useCallback((exercise: Exercise) => {
    setSelectedExercise(exercise);
    setSheetOpen(true);
  }, []);

  const handleDelete = useCallback((exercise: Exercise) => {
    setSelectedExercise(exercise);
    setDeleteOpen(true);
  }, []);

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-violet-100 to-violet-200 dark:from-violet-900/40 dark:to-violet-800/30">
            <Dumbbell className="h-5 w-5 text-violet-600 dark:text-violet-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Esercizi
              {isFiltered && (
                <span className="text-muted-foreground/60 text-base font-normal"> ({filtered.length})</span>
              )}
            </h1>
            {data && (
              <p className="text-sm text-muted-foreground">
                {allExercises.length} eserciz{allExercises.length === 1 ? "io" : "i"} nel tuo archivio
              </p>
            )}
          </div>
        </div>
        <Button onClick={handleNewExercise}>
          <Plus className="h-4 w-4 sm:mr-2" />
          <span className="hidden sm:inline">Nuovo Esercizio</span>
        </Button>
      </div>

      {/* ── KPI Cards ── */}
      {data && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <KpiCard
            label="Totale"
            value={kpi.total}
            icon={<Layers className="h-4 w-4" />}
            gradient="from-blue-50 to-blue-100 dark:from-blue-950/30 dark:to-blue-900/20"
            border="border-blue-200 dark:border-blue-800"
          />
          <KpiCard
            label="Custom"
            value={kpi.custom}
            icon={<User className="h-4 w-4" />}
            gradient="from-emerald-50 to-emerald-100 dark:from-emerald-950/30 dark:to-emerald-900/20"
            border="border-emerald-200 dark:border-emerald-800"
          />
          <KpiCard
            label="Attrezzature"
            value={kpi.equipmentCount}
            icon={<Dumbbell className="h-4 w-4" />}
            gradient="from-amber-50 to-amber-100 dark:from-amber-950/30 dark:to-amber-900/20"
            border="border-amber-200 dark:border-amber-800"
          />
          <div className="rounded-xl border border-violet-200 bg-gradient-to-br from-violet-50 to-violet-100 p-4 dark:border-violet-800 dark:from-violet-950/30 dark:to-violet-900/20">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Activity className="h-4 w-4" />
              Per Categoria
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {Object.entries(kpi.byCategory).map(([cat, count]) => (
                <Badge key={cat} variant="outline" className="text-xs">
                  {CATEGORY_LABELS[cat] ?? cat}: {count}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── FilterBar chip interattivi ── */}
      {data && (
        <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-3 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
          <div className="flex flex-col gap-2">
            {/* Riga 1: Categoria (multi-toggle, pattern Clienti) */}
            <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
              <span className="w-20 shrink-0 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                Categoria:
              </span>
              {CATEGORY_OPTIONS.map((opt) => {
                const active = activeCategories.has(opt.value);
                const Icon = active ? Eye : EyeOff;
                const color = CATEGORY_CHIP_COLORS[opt.value] ?? "#888";
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleToggleCategory(opt.value)}
                    className={`flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-medium transition-all duration-200 sm:gap-1.5 sm:px-3 sm:text-xs ${
                      active
                        ? "border-transparent shadow-sm"
                        : "border-dashed border-muted-foreground/30 opacity-40"
                    }`}
                    style={active ? { backgroundColor: color + "20", color } : undefined}
                  >
                    <div
                      className="h-2.5 w-2.5 rounded-full transition-opacity"
                      style={{ backgroundColor: color, opacity: active ? 1 : 0.3 }}
                    />
                    {opt.label}
                    <Icon className="h-3 w-3" />
                  </button>
                );
              })}
            </div>

            {/* Riga 2: Pattern movimento (select-one) */}
            {availablePatterns.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                <span className="w-20 shrink-0 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  Movimento:
                </span>
                {availablePatterns.map(({ value, count }) => (
                  <SelectOneChip
                    key={value}
                    label={PATTERN_CHIP_LABELS[value] ?? value}
                    count={count}
                    active={selectedPattern === value}
                    onClick={() => setSelectedPattern(selectedPattern === value ? null : value)}
                  />
                ))}
              </div>
            )}

            {/* Riga 3: Muscolo (select-one, ordinamento anatomico) */}
            {availableMuscles.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                <span className="w-20 shrink-0 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  Muscolo:
                </span>
                {availableMuscles.map(({ value, count }) => (
                  <SelectOneChip
                    key={value}
                    label={MUSCLE_LABELS[value] ?? value}
                    count={count}
                    active={selectedMuscle === value}
                    onClick={() => setSelectedMuscle(selectedMuscle === value ? null : value)}
                  />
                ))}
              </div>
            )}

            {/* Riga 4: Attrezzatura (select-one) */}
            {availableEquipment.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                <span className="w-20 shrink-0 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  Attrezz.:
                </span>
                {availableEquipment.map(({ value, count }) => (
                  <SelectOneChip
                    key={value}
                    label={EQUIPMENT_LABELS[value] ?? value}
                    count={count}
                    active={selectedEquipment === value}
                    onClick={() => setSelectedEquipment(selectedEquipment === value ? null : value)}
                  />
                ))}
              </div>
            )}

            {/* Riga 5: Livello (select-one) */}
            {availableDifficulties.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                <span className="w-20 shrink-0 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  Livello:
                </span>
                {availableDifficulties.map(({ value, count }) => (
                  <SelectOneChip
                    key={value}
                    label={DIFFICULTY_LABELS[value] ?? value}
                    count={count}
                    active={selectedDifficulty === value}
                    onClick={() => setSelectedDifficulty(selectedDifficulty === value ? null : value)}
                  />
                ))}

                {/* Biomeccanica toggle */}
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

            {/* Righe biomeccanica (collapsibili) */}
            {showBiomechanics && (
              <>
                {availableForceTypes.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                    <span className="w-20 shrink-0 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                      Forza:
                    </span>
                    {availableForceTypes.map(({ value, count }) => (
                      <SelectOneChip
                        key={value}
                        label={FORCE_TYPE_LABELS[value] ?? value}
                        count={count}
                        active={selectedForceType === value}
                        onClick={() => setSelectedForceType(selectedForceType === value ? null : value)}
                      />
                    ))}
                  </div>
                )}

                {availableLaterals.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                    <span className="w-20 shrink-0 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                      Lateralita:
                    </span>
                    {availableLaterals.map(({ value, count }) => (
                      <SelectOneChip
                        key={value}
                        label={LATERAL_PATTERN_LABELS[value] ?? value}
                        count={count}
                        active={selectedLateral === value}
                        onClick={() => setSelectedLateral(selectedLateral === value ? null : value)}
                      />
                    ))}
                  </div>
                )}
              </>
            )}

            {/* Reset filtri */}
            {isFiltered && (
              <div className="flex items-center justify-between pt-1 border-t border-muted/50">
                <span className="text-[11px] text-muted-foreground">
                  {filtered.length} eserciz{filtered.length === 1 ? "io" : "i"} trovati
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetFilters}
                  className="h-6 text-xs text-muted-foreground"
                >
                  Resetta filtri
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Ricerca testuale ── */}
      {data && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Cerca per nome, muscolo, attrezzatura..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
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
      )}

      {/* ── Content ── */}
      {isLoading && <TableSkeleton />}

      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <p className="text-destructive">Errore nel caricamento degli esercizi.</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
            Riprova
          </Button>
        </div>
      )}

      {data && (
        <ExercisesTable
          exercises={filtered}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onNewExercise={handleNewExercise}
        />
      )}

      {/* ── Sheet + Dialog ── */}
      <ExerciseSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        exercise={selectedExercise}
      />

      <DeleteExerciseDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        exercise={selectedExercise}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SHARED UI COMPONENTS
// ════════════════════════════════════════════════════════════

/** Chip select-one: bg-primary quando attivo, muted altrimenti */
function SelectOneChip({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors sm:text-xs ${
        active
          ? "bg-primary text-primary-foreground shadow-sm"
          : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
      }`}
    >
      {label}
      <span className={`text-[9px] ${active ? "text-primary-foreground/70" : "text-muted-foreground/60"}`}>
        {count}
      </span>
    </button>
  );
}

function KpiCard({
  label,
  value,
  icon,
  gradient,
  border,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  gradient: string;
  border: string;
}) {
  return (
    <div className={`rounded-xl border ${border} bg-gradient-to-br ${gradient} p-4`}>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className="mt-1 text-2xl font-bold tabular-nums">{value}</p>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
    </div>
  );
}
