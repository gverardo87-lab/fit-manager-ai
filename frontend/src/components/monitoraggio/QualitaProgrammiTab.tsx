// src/components/monitoraggio/QualitaProgrammiTab.tsx
"use client";

/**
 * Tab Qualita Programmi — Worklist analisi metodologica allenamento.
 *
 * Hero KPI + filtri semplificati con ricerca debounced + righe espandibili full-width.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
  Dumbbell,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { TrainingHeroCard } from "@/components/training/TrainingHeroCard";
import { TrainingPlanRow } from "@/components/training/TrainingPlanCard";
import {
  useTrainingMethodologyWorklist,
  type TrainingMethodologyWorklistQuery,
} from "@/hooks/useDashboard";

// ── Types ──

type ViewFilter = "all" | "issues" | "excellent";

const PAGE_SIZE = 24;
const DEBOUNCE_MS = 400;

// ── Skeletons ──

function HeroSkeleton() {
  return (
    <div className="rounded-xl border p-5">
      <div className="flex flex-col items-center gap-6 sm:flex-row">
        <Skeleton className="h-24 w-24 rounded-full" />
        <div className="grid w-full grid-cols-2 gap-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}

function RowListSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-14 rounded-xl" />
      ))}
    </div>
  );
}

function EmptyStateCard({
  icon: Icon,
  title,
  subtitle,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed py-16 text-center">
      <Icon className="mb-3 h-10 w-10 text-muted-foreground/40" />
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
    </div>
  );
}

// ── Tab Content ──

export function QualitaProgrammiTab() {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [view, setView] = useState<ViewFilter>("all");
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounce search: input updates immediately, query fires after delay
  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setDebouncedSearch(search.trim());
      setPage(1);
    }, DEBOUNCE_MS);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [search]);

  const query: TrainingMethodologyWorklistQuery = {
    page,
    page_size: PAGE_SIZE,
    view,
    sort_by: "priority",
    search: debouncedSearch || undefined,
  };

  const { data, isLoading, isError, isFetching, refetch } =
    useTrainingMethodologyWorklist(query);

  const summary = data?.summary;
  const pagedItems = data?.items ?? [];
  const totalItems = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE));
  const canGoPrev = page > 1;
  const canGoNext = page < totalPages;

  const handleViewChange = (next: ViewFilter) => { setView(next); setPage(1); setExpandedId(null); };

  const handleToggle = useCallback((planId: number) => {
    setExpandedId((prev) => (prev === planId ? null : planId));
  }, []);

  if (isError) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
        <p className="text-sm text-destructive">Impossibile caricare i dati dei programmi.</p>
        <Button variant="outline" size="sm" className="mt-2" onClick={() => void refetch()}>
          Riprova
        </Button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-5">
        <HeroSkeleton />
        <Skeleton className="h-14 w-full rounded-xl" />
        <RowListSkeleton />
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="space-y-5">
      {/* Hero card */}
      <TrainingHeroCard summary={summary} />

      {/* FilterBar — pills + search */}
      <div className="rounded-xl border bg-white p-3 shadow-sm dark:bg-zinc-900">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-1.5">
            {(["all", "issues", "excellent"] as const).map((f) => (
              <Button
                key={f}
                type="button"
                size="sm"
                variant={view === f ? "default" : "outline"}
                onClick={() => handleViewChange(f)}
                className="h-8"
              >
                {f === "all" ? "Tutti" : f === "issues" ? "Con problemi" : "Eccellenti"}
              </Button>
            ))}
          </div>
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cerca piano o cliente..."
              className="pl-9"
            />
          </div>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          {totalItems} pian{totalItems === 1 ? "o" : "i"} filtrat{totalItems === 1 ? "o" : "i"}
          {isFetching && !isLoading && <span className="ml-1 text-muted-foreground/60">(aggiornamento...)</span>}
        </p>
      </div>

      {/* Row List or Empty */}
      {pagedItems.length === 0 ? (
        totalItems === 0 && view === "all" && !debouncedSearch ? (
          <EmptyStateCard
            icon={Dumbbell}
            title="Nessun piano con cliente assegnato"
            subtitle="Crea una scheda e assegnala a un cliente per vederla qui"
          />
        ) : (
          <EmptyStateCard
            icon={Filter}
            title="Nessun piano per il filtro selezionato"
            subtitle="Cambia filtro oppure cerca per nome piano o cliente"
          />
        )
      ) : (
        <>
          <div className="space-y-2">
            {pagedItems.map((item) => (
              <TrainingPlanRow
                key={item.plan_id}
                item={item}
                expanded={expandedId === item.plan_id}
                onToggle={() => handleToggle(item.plan_id)}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex flex-col items-center gap-2 sm:flex-row sm:justify-between">
              <p className="text-xs text-muted-foreground">
                {totalItems} pian{totalItems === 1 ? "o" : "i"} - Pagina {page}/{totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={!canGoPrev}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="gap-1"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                  Precedente
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={!canGoNext}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="gap-1"
                >
                  Successiva
                  <ChevronRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
