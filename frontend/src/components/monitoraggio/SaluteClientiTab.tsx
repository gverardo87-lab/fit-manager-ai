// src/components/monitoraggio/SaluteClientiTab.tsx
"use client";

/**
 * Tab Salute Clienti — Worklist readiness clinica.
 *
 * Contenuto identico a MyPortal: hero con HealthScoreRing,
 * filtri avanzati, card grid paginata.
 * Estratto come componente tab riusabile.
 */

import { useMemo, useState } from "react";
import {
  Filter,
  Search,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

import { AnimatedNumber } from "@/components/ui/animated-number";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { HealthScoreRing } from "@/components/portal/HealthScoreRing";
import { ReadinessClientCard } from "@/components/portal/ReadinessClientCard";
import { useClinicalReadinessWorklist } from "@/hooks/useDashboard";
import type { ClinicalReadinessClientItem } from "@/types/api";

// ── Types ──

type PortalFilter = "all" | "todo" | "ready";
type PriorityFilter = "all" | ClinicalReadinessClientItem["priority"];
type DueFilter = "all" | Exclude<ClinicalReadinessClientItem["timeline_status"], "none">;
type SortMode = "priority" | "due_date";

const PAGE_SIZE = 24;

// ── Hero Card ──

function ReadinessHeroCard({
  totalClients,
  readyClients,
  highPriority,
  readyPct,
}: {
  totalClients: number;
  readyClients: number;
  highPriority: number;
  readyPct: number;
}) {
  const actionable = totalClients - readyClients;

  return (
    <div className="rounded-xl border border-l-4 border-l-teal-500 bg-gradient-to-br from-teal-50/80 via-white to-emerald-50/60 p-5 shadow-sm dark:from-teal-950/20 dark:via-zinc-900 dark:to-emerald-950/10">
      <div className="flex flex-col items-center gap-6 sm:flex-row">
        <div className="shrink-0">
          <HealthScoreRing score={readyPct} size={96} strokeWidth={8} />
        </div>
        <div className="grid w-full grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 dark:border-amber-900/40 dark:bg-amber-950/20">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Da completare
            </p>
            <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-amber-700 dark:text-amber-300">
              <AnimatedNumber value={actionable} />
            </p>
          </div>
          <div className="rounded-lg border border-emerald-200 bg-emerald-50/80 px-3 py-2 dark:border-emerald-900/40 dark:bg-emerald-950/20">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Pronti
            </p>
            <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-emerald-700 dark:text-emerald-300">
              <AnimatedNumber value={readyClients} />
            </p>
          </div>
          <div className="rounded-lg border border-red-200 bg-red-50/80 px-3 py-2 dark:border-red-900/40 dark:bg-red-950/20">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Alta priorita
            </p>
            <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-red-700 dark:text-red-300">
              <AnimatedNumber value={highPriority} />
            </p>
          </div>
          <div className="rounded-lg border border-teal-200 bg-teal-50/80 px-3 py-2 dark:border-teal-900/40 dark:bg-teal-950/20">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Score medio
            </p>
            <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-teal-700 dark:text-teal-300">
              <AnimatedNumber value={readyPct} /><span className="text-base">%</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

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
        <Skeleton key={i} className="h-44 rounded-xl" />
      ))}
    </div>
  );
}

// ── Tab Content ──

export function SaluteClientiTab() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<PortalFilter>("todo");
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("all");
  const [dueFilter, setDueFilter] = useState<DueFilter>("all");
  const [sortBy, setSortBy] = useState<SortMode>("priority");
  const [page, setPage] = useState(1);

  const trimmedSearch = search.trim();

  const {
    data,
    isLoading,
    isError,
    isFetching,
    refetch,
  } = useClinicalReadinessWorklist({
    page,
    page_size: PAGE_SIZE,
    view: filter,
    sort_by: sortBy,
    priority: priorityFilter === "all" ? undefined : priorityFilter,
    timeline_status: dueFilter === "all" ? undefined : dueFilter,
    search: trimmedSearch || undefined,
  });

  const summary = data?.summary;
  const pagedItems = data?.items ?? [];
  const totalItems = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE));
  const canGoPrev = page > 1;
  const canGoNext = page < totalPages;

  const readyPct = useMemo(() => {
    if (!summary || summary.total_clients === 0) return 0;
    return Math.round((summary.ready_clients / summary.total_clients) * 100);
  }, [summary]);

  const hasAdvancedFilters =
    priorityFilter !== "all" || dueFilter !== "all" || sortBy !== "priority";

  const handleFilterChange = (next: PortalFilter) => { setFilter(next); setPage(1); };
  const handleSearchChange = (v: string) => { setSearch(v); setPage(1); };
  const handleResetAdvanced = () => {
    setPriorityFilter("all");
    setDueFilter("all");
    setSortBy("priority");
    setPage(1);
  };

  if (isError) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
        <p className="text-sm text-destructive">Impossibile caricare i dati di salute clienti.</p>
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
      <ReadinessHeroCard
        totalClients={summary.total_clients}
        readyClients={summary.ready_clients}
        highPriority={summary.high_priority}
        readyPct={readyPct}
      />

      {/* FilterBar */}
      <div className="rounded-xl border bg-white p-3 shadow-sm dark:bg-zinc-900">
        <div className="space-y-2">
          {/* Row 1: pills + search */}
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-1.5">
              {(["todo", "all", "ready"] as const).map((f) => (
                <Button
                  key={f}
                  type="button"
                  size="sm"
                  variant={filter === f ? "default" : "outline"}
                  onClick={() => handleFilterChange(f)}
                  className="h-8"
                >
                  {f === "todo" ? "Da completare" : f === "all" ? "Tutti" : "Pronti"}
                </Button>
              ))}
            </div>
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => handleSearchChange(e.target.value)}
                placeholder="Cerca cliente..."
                className="pl-9"
              />
            </div>
          </div>

          {/* Row 2: selects + reset */}
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="grid flex-1 gap-2 sm:grid-cols-3">
              <Select
                value={priorityFilter}
                onValueChange={(v) => { setPriorityFilter(v as PriorityFilter); setPage(1); }}
              >
                <SelectTrigger size="sm" className="w-full">
                  <SelectValue placeholder="Priorita" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Priorita: tutte</SelectItem>
                  <SelectItem value="high">Priorita: alta</SelectItem>
                  <SelectItem value="medium">Priorita: media</SelectItem>
                  <SelectItem value="low">Priorita: bassa</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={dueFilter}
                onValueChange={(v) => { setDueFilter(v as DueFilter); setPage(1); }}
              >
                <SelectTrigger size="sm" className="w-full">
                  <SelectValue placeholder="Scadenza" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Scadenza: tutte</SelectItem>
                  <SelectItem value="overdue">Scadute</SelectItem>
                  <SelectItem value="today">Oggi</SelectItem>
                  <SelectItem value="upcoming_7d">Entro 7 giorni</SelectItem>
                  <SelectItem value="upcoming_14d">Entro 14 giorni</SelectItem>
                  <SelectItem value="future">Pianificate</SelectItem>
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
                  <SelectItem value="due_date">Per scadenza</SelectItem>
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
            {totalItems} client{totalItems === 1 ? "e" : "i"} filtrat{totalItems === 1 ? "o" : "i"}
            {isFetching && <span className="ml-1">(aggiornamento...)</span>}
          </p>
        </div>
      </div>

      {/* Card Grid or Empty */}
      {pagedItems.length === 0 ? (
        <EmptyState
          icon={Filter}
          title="Nessun cliente per il filtro selezionato"
          subtitle="Cambia filtro oppure cerca per nome e cognome"
        />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {pagedItems.map((item) => (
              <ReadinessClientCard key={item.client_id} item={item} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex flex-col items-center gap-2 sm:flex-row sm:justify-between">
              <p className="text-xs text-muted-foreground">
                {totalItems} client{totalItems === 1 ? "e" : "i"} - Pagina {page}/{totalPages}
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
