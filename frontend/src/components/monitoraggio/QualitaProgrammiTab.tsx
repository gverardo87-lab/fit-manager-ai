// src/components/monitoraggio/QualitaProgrammiTab.tsx
"use client";

/**
 * Tab Qualita Programmi — Worklist analisi metodologica allenamento.
 *
 * Contenuto identico a MyTrainer: hero KPI + filtri + card grid paginata.
 * Estratto come componente tab riusabile.
 */

import { useState } from "react";
import {
  Filter,
  Search,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Dumbbell,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TrainingHeroCard } from "@/components/training/TrainingHeroCard";
import { TrainingPlanCard } from "@/components/training/TrainingPlanCard";
import {
  useTrainingMethodologyWorklist,
  type TrainingMethodologyWorklistQuery,
} from "@/hooks/useDashboard";

// ── Types ──

type ViewFilter = "all" | "issues" | "excellent";
type StatusFilter = "all" | "attivo" | "da_attivare" | "completato";
type SortMode = "priority" | "science_score" | "compliance";

const PAGE_SIZE = 24;

// ── Skeletons ──

function HeroSkeleton() {
  return (
    <div className="rounded-xl border p-5">
      <div className="flex flex-col items-center gap-6 sm:flex-row">
        <Skeleton className="h-24 w-24 rounded-full" />
        <div className="grid w-full grid-cols-2 gap-3 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}

function CardGridSkeleton() {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-52 rounded-xl" />
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
  const [view, setView] = useState<ViewFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [sortBy, setSortBy] = useState<SortMode>("priority");
  const [page, setPage] = useState(1);

  const trimmedSearch = search.trim();

  const query: TrainingMethodologyWorklistQuery = {
    page,
    page_size: PAGE_SIZE,
    view,
    sort_by: sortBy,
    plan_status: statusFilter === "all" ? undefined : statusFilter,
    search: trimmedSearch || undefined,
  };

  const { data, isLoading, isError, isFetching, refetch } =
    useTrainingMethodologyWorklist(query);

  const summary = data?.summary;
  const pagedItems = data?.items ?? [];
  const totalItems = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE));
  const canGoPrev = page > 1;
  const canGoNext = page < totalPages;

  const hasAdvancedFilters =
    statusFilter !== "all" || sortBy !== "priority";

  const handleViewChange = (next: ViewFilter) => { setView(next); setPage(1); };
  const handleSearchChange = (v: string) => { setSearch(v); setPage(1); };
  const handleResetAdvanced = () => {
    setStatusFilter("all");
    setSortBy("priority");
    setPage(1);
  };

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
        <CardGridSkeleton />
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="space-y-5">
      {/* Hero card */}
      <TrainingHeroCard summary={summary} />

      {/* FilterBar */}
      <div className="rounded-xl border bg-white p-3 shadow-sm dark:bg-zinc-900">
        <div className="space-y-2">
          {/* Row 1: pills + search */}
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
                onChange={(e) => handleSearchChange(e.target.value)}
                placeholder="Cerca piano o cliente..."
                className="pl-9"
              />
            </div>
          </div>

          {/* Row 2: selects + reset */}
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="grid flex-1 gap-2 sm:grid-cols-2">
              <Select
                value={statusFilter}
                onValueChange={(v) => { setStatusFilter(v as StatusFilter); setPage(1); }}
              >
                <SelectTrigger size="sm" className="w-full">
                  <SelectValue placeholder="Stato" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Stato: tutti</SelectItem>
                  <SelectItem value="attivo">Attivi</SelectItem>
                  <SelectItem value="da_attivare">Da attivare</SelectItem>
                  <SelectItem value="completato">Completati</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={sortBy}
                onValueChange={(v) => { setSortBy(v as SortMode); setPage(1); }}
              >
                <SelectTrigger size="sm" className="w-full">
                  <SelectValue placeholder="Ordinamento" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="priority">Per priorita</SelectItem>
                  <SelectItem value="science_score">Per score scientifico</SelectItem>
                  <SelectItem value="compliance">Per aderenza</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {hasAdvancedFilters && (
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="h-8 gap-1 shrink-0"
                onClick={handleResetAdvanced}
              >
                <RotateCcw className="h-3 w-3" />
                Reset
              </Button>
            )}
          </div>

          {/* Counter */}
          <p className="text-xs text-muted-foreground">
            {totalItems} pian{totalItems === 1 ? "o" : "i"} filtrat{totalItems === 1 ? "o" : "i"}
            {isFetching && <span className="ml-1">(aggiornamento...)</span>}
          </p>
        </div>
      </div>

      {/* Card Grid or Empty */}
      {pagedItems.length === 0 ? (
        totalItems === 0 && view === "all" && !trimmedSearch ? (
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
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {pagedItems.map((item) => (
              <TrainingPlanCard key={item.plan_id} item={item} />
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
