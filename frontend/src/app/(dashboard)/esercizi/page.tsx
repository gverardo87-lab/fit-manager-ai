// src/app/(dashboard)/esercizi/page.tsx
"use client";

/**
 * Pagina Archivio Esercizi.
 *
 * Layout:
 * - Header con titolo + conteggio + "Nuovo Esercizio"
 * - KPI cards (totale, custom, per categoria)
 * - FilterBar con dropdown per categoria, attrezzatura, difficolta'
 * - ExercisesTable con ricerca client-side
 * - Sheet per crea/modifica + Dialog per elimina
 */

import { useState, useMemo, useCallback } from "react";
import {
  Plus,
  Dumbbell,
  Layers,
  User,
  Activity,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { ExercisesTable } from "@/components/exercises/ExercisesTable";
import { ExerciseSheet } from "@/components/exercises/ExerciseSheet";
import { DeleteExerciseDialog } from "@/components/exercises/DeleteExerciseDialog";
import { useExercises, type ExerciseFilters } from "@/hooks/useExercises";
import {
  CATEGORY_OPTIONS,
  EQUIPMENT_OPTIONS,
  DIFFICULTY_OPTIONS,
  CATEGORY_LABELS,
} from "@/components/exercises/exercise-constants";
import type { Exercise } from "@/types/api";

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

const NONE_VALUE = "__none__";

export default function EserciziPage() {
  // Filters (backend-side)
  const [filters, setFilters] = useState<ExerciseFilters>({});
  const { data, isLoading, isError, refetch } = useExercises(filters);

  // Sheet/Dialog state
  const [sheetOpen, setSheetOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedExercise, setSelectedExercise] = useState<Exercise | null>(null);

  const exercises = data?.items ?? [];
  const kpi = useExerciseKpi(exercises);

  // Handlers
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

  const updateFilter = useCallback((key: keyof ExerciseFilters, value: string) => {
    setFilters((prev) => {
      const next = { ...prev };
      if (value === NONE_VALUE || !value) {
        delete next[key];
      } else {
        next[key] = value;
      }
      return next;
    });
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
            <h1 className="text-2xl font-bold tracking-tight">Esercizi</h1>
            {data && (
              <p className="text-sm text-muted-foreground">
                {data.total} eserciz{data.total === 1 ? "io" : "i"} nel tuo archivio
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
          <div className={`rounded-xl border border-violet-200 bg-gradient-to-br from-violet-50 to-violet-100 p-4 dark:border-violet-800 dark:from-violet-950/30 dark:to-violet-900/20`}>
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

      {/* ── Filter Bar ── */}
      <div className="flex flex-wrap gap-2">
        <FilterSelect
          placeholder="Categoria"
          options={CATEGORY_OPTIONS}
          value={filters.categoria}
          onChange={(v) => updateFilter("categoria", v)}
        />
        <FilterSelect
          placeholder="Attrezzatura"
          options={EQUIPMENT_OPTIONS}
          value={filters.attrezzatura}
          onChange={(v) => updateFilter("attrezzatura", v)}
        />
        <FilterSelect
          placeholder="Difficolta'"
          options={DIFFICULTY_OPTIONS}
          value={filters.difficolta}
          onChange={(v) => updateFilter("difficolta", v)}
        />
        {Object.keys(filters).length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setFilters({})}
            className="text-muted-foreground"
          >
            Rimuovi filtri
          </Button>
        )}
      </div>

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
          exercises={exercises}
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
// SHARED UI
// ════════════════════════════════════════════════════════════

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

function FilterSelect({
  placeholder,
  options,
  value,
  onChange,
}: {
  placeholder: string;
  options: { value: string; label: string }[];
  value?: string;
  onChange: (value: string) => void;
}) {
  return (
    <Select value={value ?? NONE_VALUE} onValueChange={onChange}>
      <SelectTrigger className="w-[160px]">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={NONE_VALUE}>Tutti</SelectItem>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
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
