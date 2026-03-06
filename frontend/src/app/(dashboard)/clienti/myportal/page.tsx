"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Clock3,
  Filter,
  HeartPulse,
  Search,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useClinicalReadinessWorklist } from "@/hooks/useDashboard";
import { usePageReveal } from "@/lib/page-reveal";
import type { ClinicalReadinessClientItem } from "@/types/api";

type PortalFilter = "all" | "todo" | "ready";
type TimelineStatus = ClinicalReadinessClientItem["timeline_status"];
type PriorityFilter = "all" | ClinicalReadinessClientItem["priority"];
type DueFilter = "all" | Exclude<TimelineStatus, "none">;
type SortMode = "priority" | "due_date";

const DEFAULT_PAGE_SIZE = 20;
const DEFAULT_TIMELINE_PAGE_SIZE = 9;
const PAGE_SIZE_OPTIONS = [10, 20, 30, 50] as const;
const TIMELINE_PAGE_SIZE_OPTIONS = [6, 9, 12, 18] as const;

const PRIORITY_BADGE: Record<ClinicalReadinessClientItem["priority"], string> = {
  high: "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800",
  medium: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800",
  low: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800",
};

const PRIORITY_LABEL: Record<ClinicalReadinessClientItem["priority"], string> = {
  high: "Alta",
  medium: "Media",
  low: "Bassa",
};

const STEP_LABEL: Record<string, string> = {
  anamnesi_missing: "Compila anamnesi",
  anamnesi_legacy: "Rivedi anamnesi",
  baseline: "Registra baseline",
  workout: "Assegna scheda",
};

const TIMELINE_STATUS_LABEL: Record<TimelineStatus, string> = {
  overdue: "Scaduta",
  today: "Oggi",
  upcoming_7d: "Entro 7 giorni",
  upcoming_14d: "Entro 14 giorni",
  future: "Pianificata",
  none: "Nessuna",
};

const TIMELINE_STATUS_BADGE: Record<TimelineStatus, string> = {
  overdue: "border-red-200 bg-red-100 text-red-700 dark:border-red-900/40 dark:bg-red-900/30 dark:text-red-300",
  today: "border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-900/40 dark:bg-amber-900/30 dark:text-amber-300",
  upcoming_7d: "border-orange-200 bg-orange-100 text-orange-700 dark:border-orange-900/40 dark:bg-orange-900/30 dark:text-orange-300",
  upcoming_14d: "border-blue-200 bg-blue-100 text-blue-700 dark:border-blue-900/40 dark:bg-blue-900/30 dark:text-blue-300",
  future: "border-zinc-200 bg-zinc-100 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-800 dark:text-zinc-300",
  none: "border-zinc-200 bg-zinc-100 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-800 dark:text-zinc-300",
};

const TIMELINE_REASON_LABEL: Record<string, string> = {
  anamnesi_missing: "Anamnesi da compilare",
  anamnesi_legacy: "Anamnesi da aggiornare",
  baseline_missing: "Baseline da registrare",
  workout_missing: "Scheda da assegnare",
  measurement_review: "Review misurazioni",
  workout_review: "Review scheda",
  anamnesi_review: "Review anamnesi",
  monitoring: "Monitoraggio",
};

const DUE_FILTER_LABEL: Record<DueFilter, string> = {
  all: "Tutte le scadenze",
  overdue: "Scadute",
  today: "Oggi",
  upcoming_7d: "Entro 7 giorni",
  upcoming_14d: "Entro 14 giorni",
  future: "Pianificate",
};

const SORT_LABEL: Record<SortMode, string> = {
  priority: "Priorita",
  due_date: "Scadenza",
};

function formatIsoDate(isoDate: string | null): string {
  if (!isoDate) return "N/D";
  const parsed = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return isoDate;
  return parsed.toLocaleDateString("it-IT", { day: "2-digit", month: "short", year: "numeric" });
}

function CompletionBadge({
  complete,
  completeLabel = "Completa",
  missingLabel = "Manca",
}: {
  complete: boolean;
  completeLabel?: string;
  missingLabel?: string;
}) {
  if (complete) {
    return (
      <Badge className="border-emerald-200 bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:border-emerald-900/40 dark:bg-emerald-900/30 dark:text-emerald-300">
        {completeLabel}
      </Badge>
    );
  }
  return (
    <Badge className="border-red-200 bg-red-100 text-red-700 hover:bg-red-100 dark:border-red-900/40 dark:bg-red-900/30 dark:text-red-300">
      {missingLabel}
    </Badge>
  );
}

function AnamnesiBadge({ state }: { state: ClinicalReadinessClientItem["anamnesi_state"] }) {
  if (state === "structured") {
    return <CompletionBadge complete completeLabel="Allineata" missingLabel="Manca" />;
  }
  if (state === "legacy") {
    return (
      <Badge className="border-amber-200 bg-amber-100 text-amber-700 hover:bg-amber-100 dark:border-amber-900/40 dark:bg-amber-900/30 dark:text-amber-300">
        Legacy
      </Badge>
    );
  }
  return <CompletionBadge complete={false} completeLabel="Allineata" missingLabel="Assente" />;
}

function KpiCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "neutral" | "ok" | "warn" | "danger";
}) {
  const toneClass =
    tone === "ok"
      ? "border-emerald-200 bg-emerald-50/80 dark:border-emerald-900/40 dark:bg-emerald-950/20"
      : tone === "warn"
        ? "border-amber-200 bg-amber-50/80 dark:border-amber-900/40 dark:bg-amber-950/20"
        : tone === "danger"
          ? "border-red-200 bg-red-50/80 dark:border-red-900/40 dark:bg-red-950/20"
          : "border-zinc-200 bg-zinc-50/80 dark:border-zinc-800 dark:bg-zinc-900/60";

  return (
    <div className={`rounded-xl border px-3 py-2 ${toneClass}`}>
      <p className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">{label}</p>
      <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums">{value}</p>
    </div>
  );
}

export default function MyPortalPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<PortalFilter>("todo");
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("all");
  const [dueFilter, setDueFilter] = useState<DueFilter>("all");
  const [sortBy, setSortBy] = useState<SortMode>("priority");
  const [pageSize, setPageSize] = useState<number>(DEFAULT_PAGE_SIZE);
  const [page, setPage] = useState(1);
  const [timelinePage, setTimelinePage] = useState(1);
  const [timelinePageSize, setTimelinePageSize] = useState<number>(DEFAULT_TIMELINE_PAGE_SIZE);

  const trimmedSearch = search.trim();

  const {
    data,
    isLoading,
    isError,
    isFetching,
    refetch,
  } = useClinicalReadinessWorklist({
    page,
    page_size: pageSize,
    view: filter,
    sort_by: sortBy,
    priority: priorityFilter === "all" ? undefined : priorityFilter,
    timeline_status: dueFilter === "all" ? undefined : dueFilter,
    search: trimmedSearch || undefined,
  });

  const {
    data: timelineData,
    isLoading: timelineLoading,
    isFetching: timelineFetching,
    refetch: refetchTimeline,
  } = useClinicalReadinessWorklist({
    page: timelinePage,
    page_size: timelinePageSize,
    view: filter,
    sort_by: "due_date",
    priority: priorityFilter === "all" ? undefined : priorityFilter,
    timeline_status: dueFilter === "all" ? undefined : dueFilter,
    search: trimmedSearch || undefined,
  });

  const actionableCount = useMemo(
    () => (data?.summary.total_clients ?? 0) - (data?.summary.ready_clients ?? 0),
    [data],
  );

  const timelineItems = useMemo(() => {
    return (timelineData?.items ?? [])
      .filter((item) => item.next_due_date !== null)
      .sort((a, b) => {
        const aDate = a.next_due_date ?? "9999-12-31";
        const bDate = b.next_due_date ?? "9999-12-31";
        if (aDate !== bDate) return aDate.localeCompare(bDate);
        return a.client_cognome.localeCompare(b.client_cognome);
      });
  }, [timelineData]);

  const pagedItems = data?.items ?? [];
  const totalItems = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const summary = data?.summary;
  const canGoPrev = page > 1;
  const canGoNext = page < totalPages;
  const timelineTotalItems = timelineData?.total ?? 0;
  const timelineTotalPages = Math.max(1, Math.ceil(timelineTotalItems / timelinePageSize));
  const timelineCanGoPrev = timelinePage > 1;
  const timelineCanGoNext = timelinePage < timelineTotalPages;
  const hasAdvancedFilters =
    priorityFilter !== "all" || dueFilter !== "all" || sortBy !== "priority" || pageSize !== DEFAULT_PAGE_SIZE;

  const handleRetry = () => {
    void refetch();
    void refetchTimeline();
  };

  const handleFilterChange = (nextFilter: PortalFilter) => {
    setFilter(nextFilter);
    setPage(1);
    setTimelinePage(1);
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setPage(1);
    setTimelinePage(1);
  };

  const handlePriorityFilterChange = (value: PriorityFilter) => {
    setPriorityFilter(value);
    setPage(1);
    setTimelinePage(1);
  };

  const handleDueFilterChange = (value: DueFilter) => {
    setDueFilter(value);
    setPage(1);
    setTimelinePage(1);
  };

  const handleSortByChange = (value: SortMode) => {
    setSortBy(value);
    setPage(1);
  };

  const handlePageSizeChange = (value: number) => {
    setPageSize(value);
    setPage(1);
  };

  const handleTimelinePageSizeChange = (value: number) => {
    setTimelinePageSize(value);
    setTimelinePage(1);
  };

  const handleResetAdvancedFilters = () => {
    setPriorityFilter("all");
    setDueFilter("all");
    setSortBy("priority");
    setPageSize(DEFAULT_PAGE_SIZE);
    setTimelinePage(1);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div className={revealClass(0, "flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between")} style={revealStyle(0)}>
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900/40 dark:to-teal-800/30">
            <HeartPulse className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">MyPortal</h1>
            <p className="text-sm text-muted-foreground">
              Monitoraggio tecnico-operativo clienti (non medico), allineato alla readiness dashboard
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/clienti">
            <Button variant="outline" size="sm">Clienti</Button>
          </Link>
          <Link href="/">
            <Button size="sm" className="gap-1.5">
              Dashboard
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      </div>

      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
          <p className="text-sm text-destructive">Impossibile caricare i dati di MyPortal.</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={handleRetry}>
            Riprova
          </Button>
        </div>
      )}

      {isLoading && (
        <div className={revealClass(40, "space-y-4")} style={revealStyle(40)}>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <Skeleton className="h-16 rounded-xl" />
            <Skeleton className="h-16 rounded-xl" />
            <Skeleton className="h-16 rounded-xl" />
            <Skeleton className="h-16 rounded-xl" />
          </div>
          <Skeleton className="h-12 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      )}

      {!isLoading && summary && (
        <>
          <div className={revealClass(50, "grid gap-2 sm:grid-cols-2 lg:grid-cols-4")} style={revealStyle(50)}>
            <KpiCard label="Clienti attivi" value={summary.total_clients} tone="neutral" />
            <KpiCard label="Da completare" value={actionableCount} tone="warn" />
            <KpiCard label="Pronti" value={summary.ready_clients} tone="ok" />
            <KpiCard label="Alta priorita" value={summary.high_priority} tone="danger" />
          </div>

          <div className={revealClass(90, "rounded-xl border bg-white p-3 shadow-sm dark:bg-zinc-900")} style={revealStyle(90)}>
            <div className="space-y-2">
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div className="flex flex-wrap items-center gap-1.5">
                  <Button
                    type="button"
                    size="sm"
                    variant={filter === "todo" ? "default" : "outline"}
                    onClick={() => handleFilterChange("todo")}
                    className="h-8"
                  >
                    Da completare
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant={filter === "all" ? "default" : "outline"}
                    onClick={() => handleFilterChange("all")}
                    className="h-8"
                  >
                    Tutti
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant={filter === "ready" ? "default" : "outline"}
                    onClick={() => handleFilterChange("ready")}
                    className="h-8"
                  >
                    Pronti
                  </Button>
                </div>
                <div className="relative w-full md:w-80">
                  <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={search}
                    onChange={(event) => handleSearchChange(event.target.value)}
                    placeholder="Cerca cliente..."
                    className="pl-9"
                  />
                </div>
              </div>

              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                <Select value={priorityFilter} onValueChange={(value) => handlePriorityFilterChange(value as PriorityFilter)}>
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

                <Select value={dueFilter} onValueChange={(value) => handleDueFilterChange(value as DueFilter)}>
                  <SelectTrigger size="sm" className="w-full">
                    <SelectValue placeholder="Scadenza" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Scadenza: tutte</SelectItem>
                    <SelectItem value="overdue">Scadenza: scadute</SelectItem>
                    <SelectItem value="today">Scadenza: oggi</SelectItem>
                    <SelectItem value="upcoming_7d">Scadenza: entro 7 giorni</SelectItem>
                    <SelectItem value="upcoming_14d">Scadenza: entro 14 giorni</SelectItem>
                    <SelectItem value="future">Scadenza: pianificate</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={sortBy} onValueChange={(value) => handleSortByChange(value as SortMode)}>
                  <SelectTrigger size="sm" className="w-full">
                    <SelectValue placeholder="Ordinamento" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="priority">Ordinamento: priorita</SelectItem>
                    <SelectItem value="due_date">Ordinamento: scadenza</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={String(pageSize)} onValueChange={(value) => handlePageSizeChange(Number(value))}>
                  <SelectTrigger size="sm" className="w-full">
                    <SelectValue placeholder="Righe per pagina" />
                  </SelectTrigger>
                  <SelectContent>
                    {PAGE_SIZE_OPTIONS.map((size) => (
                      <SelectItem key={size} value={String(size)}>
                        {size} righe
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs text-muted-foreground">
                  {totalItems} risultati filtrati - ordinamento {SORT_LABEL[sortBy].toLowerCase()} - {DUE_FILTER_LABEL[dueFilter].toLowerCase()}
                </p>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="h-8 justify-start sm:justify-center"
                  disabled={!hasAdvancedFilters}
                  onClick={handleResetAdvancedFilters}
                >
                  Reset filtri avanzati
                </Button>
              </div>
            </div>
          </div>

          <div className={revealClass(110, "rounded-xl border bg-white p-3 shadow-sm dark:bg-zinc-900")} style={revealStyle(110)}>
            <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2">
                <Clock3 className="h-4 w-4 text-amber-500" />
                <h2 className="text-sm font-semibold">Timeline scadenze</h2>
                <Badge variant="outline" className="text-[10px]">
                  {timelineTotalItems}
                </Badge>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Select value={String(timelinePageSize)} onValueChange={(value) => handleTimelinePageSizeChange(Number(value))}>
                  <SelectTrigger size="sm" className="w-[130px]">
                    <SelectValue placeholder="Timeline" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIMELINE_PAGE_SIZE_OPTIONS.map((size) => (
                      <SelectItem key={size} value={String(size)}>
                        {size} card
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={!timelineCanGoPrev}
                  onClick={() => setTimelinePage((prev) => Math.max(1, prev - 1))}
                >
                  Precedente
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={!timelineCanGoNext}
                  onClick={() => setTimelinePage((prev) => Math.min(timelineTotalPages, prev + 1))}
                >
                  Successiva
                </Button>
              </div>
            </div>
            {timelineLoading ? (
              <Skeleton className="h-28 rounded-lg" />
            ) : timelineItems.length === 0 ? (
              <p className="text-xs text-muted-foreground">Nessuna scadenza disponibile.</p>
            ) : (
              <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
                {timelineItems.map((item) => (
                  <div key={`timeline-${item.client_id}`} className="rounded-lg border bg-zinc-50/70 p-2.5 dark:bg-zinc-900/70">
                    <div className="flex items-start justify-between gap-2">
                      <p className="truncate text-xs font-semibold">
                        {item.client_cognome} {item.client_nome}
                      </p>
                      <Badge variant="outline" className={`text-[10px] ${TIMELINE_STATUS_BADGE[item.timeline_status]}`}>
                        {TIMELINE_STATUS_LABEL[item.timeline_status]}
                      </Badge>
                    </div>
                    <p className="mt-1 text-[11px] text-muted-foreground">
                      {TIMELINE_REASON_LABEL[item.timeline_reason ?? ""] ?? "Monitoraggio"}
                    </p>
                    <p className="mt-1 text-xs font-medium">
                      {formatIsoDate(item.next_due_date)}
                      {typeof item.days_to_due === "number" && (
                        <span className="ml-1 text-muted-foreground">
                          ({item.days_to_due >= 0 ? `+${item.days_to_due}` : item.days_to_due} gg)
                        </span>
                      )}
                    </p>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
              <p>
                Pagina timeline {timelinePage}/{timelineTotalPages}
                {timelineFetching && <span className="ml-1">(aggiornamento...)</span>}
              </p>
              <p>{DUE_FILTER_LABEL[dueFilter]}</p>
            </div>
          </div>

          {pagedItems.length === 0 ? (
            <div className={revealClass(130)} style={revealStyle(130)}>
              <EmptyState
                icon={Filter}
                title="Nessun cliente per il filtro selezionato"
                subtitle="Cambia filtro oppure ricerca per nome e cognome"
              />
            </div>
          ) : (
            <>
              <div className={revealClass(130, "hidden rounded-xl border bg-white shadow-sm dark:bg-zinc-900 md:block")} style={revealStyle(130)}>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Cliente</TableHead>
                      <TableHead>Anamnesi</TableHead>
                      <TableHead>Misurazioni</TableHead>
                      <TableHead>Scheda</TableHead>
                      <TableHead>Priorita</TableHead>
                      <TableHead>Scadenza</TableHead>
                      <TableHead>Score</TableHead>
                      <TableHead className="text-right">Azione</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pagedItems.map((item) => (
                      <TableRow key={item.client_id}>
                        <TableCell className="font-medium">
                          <Link href={`/clienti/${item.client_id}`} className="hover:underline">
                            {item.client_cognome} {item.client_nome}
                          </Link>
                        </TableCell>
                        <TableCell>
                          <AnamnesiBadge state={item.anamnesi_state} />
                        </TableCell>
                        <TableCell>
                          <CompletionBadge complete={item.has_measurements} completeLabel="Registrate" missingLabel="Mancano" />
                        </TableCell>
                        <TableCell>
                          <CompletionBadge complete={item.has_workout_plan} completeLabel="Presente" missingLabel="Assente" />
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={`font-semibold uppercase ${PRIORITY_BADGE[item.priority]}`}>
                            {PRIORITY_LABEL[item.priority]}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            <p className="text-xs font-medium">{formatIsoDate(item.next_due_date)}</p>
                            <Badge variant="outline" className={`text-[10px] ${TIMELINE_STATUS_BADGE[item.timeline_status]}`}>
                              {TIMELINE_STATUS_LABEL[item.timeline_status]}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell className="font-semibold tabular-nums">{item.readiness_score}%</TableCell>
                        <TableCell className="text-right">
                          <Link href={item.next_action_href}>
                            <Button
                              size="sm"
                              variant={item.next_action_code === "ready" ? "outline" : "default"}
                              className="h-8 gap-1.5"
                            >
                              {item.next_action_label}
                              <ArrowRight className="h-3.5 w-3.5" />
                            </Button>
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className={revealClass(130, "space-y-2 md:hidden")} style={revealStyle(130)}>
                {pagedItems.map((item) => (
                  <div key={item.client_id} className="rounded-xl border bg-white p-3 shadow-sm dark:bg-zinc-900">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <Link href={`/clienti/${item.client_id}`} className="text-sm font-semibold hover:underline">
                          {item.client_cognome} {item.client_nome}
                        </Link>
                        <p className="mt-0.5 text-xs text-muted-foreground">Score {item.readiness_score}%</p>
                      </div>
                      <Badge variant="outline" className={`text-[10px] font-semibold uppercase ${PRIORITY_BADGE[item.priority]}`}>
                        {PRIORITY_LABEL[item.priority]}
                      </Badge>
                    </div>

                    <div className="mt-2 grid grid-cols-3 gap-1.5 text-center">
                      <div className="rounded-lg border p-1.5">
                        <p className="text-[10px] text-muted-foreground">Anamnesi</p>
                        <div className="mt-1 flex justify-center">
                          <AnamnesiBadge state={item.anamnesi_state} />
                        </div>
                      </div>
                      <div className="rounded-lg border p-1.5">
                        <p className="text-[10px] text-muted-foreground">Misure</p>
                        <div className="mt-1 flex justify-center">
                          <CompletionBadge complete={item.has_measurements} completeLabel="Ok" missingLabel="No" />
                        </div>
                      </div>
                      <div className="rounded-lg border p-1.5">
                        <p className="text-[10px] text-muted-foreground">Scheda</p>
                        <div className="mt-1 flex justify-center">
                          <CompletionBadge complete={item.has_workout_plan} completeLabel="Ok" missingLabel="No" />
                        </div>
                      </div>
                    </div>

                    {item.missing_steps.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {item.missing_steps.map((step) => (
                          <Badge key={`${item.client_id}-${step}`} variant="secondary" className="text-[10px]">
                            {STEP_LABEL[step] ?? step}
                          </Badge>
                        ))}
                      </div>
                    )}

                    <div className="mt-2 flex items-center justify-between rounded-lg border bg-zinc-50/70 px-2 py-1.5 dark:bg-zinc-900/70">
                      <div>
                        <p className="text-[10px] text-muted-foreground">Scadenza</p>
                        <p className="text-xs font-medium">{formatIsoDate(item.next_due_date)}</p>
                      </div>
                      <Badge variant="outline" className={`text-[10px] ${TIMELINE_STATUS_BADGE[item.timeline_status]}`}>
                        {TIMELINE_STATUS_LABEL[item.timeline_status]}
                      </Badge>
                    </div>

                    <div className="mt-3 flex justify-end">
                      <Link href={item.next_action_href}>
                        <Button
                          size="sm"
                          variant={item.next_action_code === "ready" ? "outline" : "default"}
                          className="h-8 gap-1.5"
                        >
                          {item.next_action_label}
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>

              <div className={revealClass(140, "rounded-xl border bg-white p-3 shadow-sm dark:bg-zinc-900")} style={revealStyle(140)}>
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-xs text-muted-foreground">
                    {totalItems} clienti - Pagina {page}/{totalPages}
                    {isFetching && <span className="ml-1">(aggiornamento...)</span>}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={!canGoPrev}
                      onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                    >
                      Precedente
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={!canGoNext}
                      onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                    >
                      Successiva
                    </Button>
                  </div>
                </div>
              </div>
            </>
          )}

          <div className={revealClass(170, "rounded-xl border bg-zinc-50/80 p-3 dark:bg-zinc-900/60")} style={revealStyle(170)}>
            <p className="text-xs text-muted-foreground">
              Base operativa MyPortal: anamnesi, misurazioni baseline e schede per cliente. Nessun calcolo nuovo: dati riusati da <strong>Clinical Readiness</strong> della dashboard.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
