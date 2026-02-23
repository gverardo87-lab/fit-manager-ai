// src/app/(dashboard)/agenda/page.tsx
"use client";

/**
 * Pagina Agenda — calendario interattivo con react-big-calendar.
 *
 * Il PT vive in questa schermata:
 * - Vista settimanale default, slot da 30 min (06:00-22:00)
 * - Click slot vuoto -> crea evento con date pre-compilate
 * - Click evento -> modifica via Sheet
 * - Navigazione avanti/indietro -> fetch nuovi dati
 * - Color coding per categoria (PT=blu, SALA=grigio, ecc.)
 */

import { useState, useCallback, useMemo } from "react";
import { format, startOfWeek, endOfWeek, startOfMonth, endOfMonth, subMonths, addMonths } from "date-fns";
import { it } from "date-fns/locale";
import { Plus, CalendarDays, Eye, EyeOff, CheckCircle2, Clock, Target, AlertTriangle, Loader2 } from "lucide-react";
import type { SlotInfo } from "react-big-calendar";

import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AgendaCalendar } from "@/components/agenda/AgendaCalendar";
import { EventSheet } from "@/components/agenda/EventSheet";
import { DeleteEventDialog } from "@/components/agenda/DeleteEventDialog";
import { useEvents, useUpdateEvent } from "@/hooks/useAgenda";
import {
  STATUS_LEGEND,
  CATEGORY_LEGEND,
  type CalendarEvent,
} from "@/components/agenda/calendar-setup";
import { EVENT_CATEGORIES } from "@/types/api";

/** Range iniziale: mese corrente +/- 1 mese di buffer. */
function getInitialRange() {
  const now = new Date();
  return {
    start: startOfMonth(subMonths(now, 1)),
    end: endOfMonth(addMonths(now, 1)),
  };
}

export default function AgendaPage() {
  // ── State: date range per la query API ──
  const [dateRange, setDateRange] = useState(getInitialRange);

  // ── State: Sheet crea/modifica ──
  const [sheetOpen, setSheetOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [slotStart, setSlotStart] = useState<Date | undefined>();
  const [slotEnd, setSlotEnd] = useState<Date | undefined>();

  // ── State: Dialog elimina ──
  const [deleteOpen, setDeleteOpen] = useState(false);

  // ── State: filtri categoria ──
  const [activeCategories, setActiveCategories] = useState<Set<string>>(
    () => new Set(EVENT_CATEGORIES)
  );

  // ── Query: eventi nel range ──
  const queryParams = useMemo(
    () => ({
      start: format(dateRange.start, "yyyy-MM-dd"),
      end: format(dateRange.end, "yyyy-MM-dd"),
    }),
    [dateRange]
  );

  const { data: eventsData, isLoading, isError, refetch } = useEvents(queryParams);
  const events = eventsData?.items ?? [];

  // ── Eventi filtrati per categoria ──
  const filteredEvents = useMemo(
    () => events.filter((e) => activeCategories.has(e.categoria)),
    [events, activeCategories]
  );

  const handleToggleCategory = useCallback((cat: string) => {
    setActiveCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) {
        next.delete(cat);
      } else {
        next.add(cat);
      }
      return next;
    });
  }, []);

  // ── KPI settimanali (calcolati da eventi gia' fetchati) ──
  const weekStats = useMemo(() => {
    const now = new Date();
    const weekStart = startOfWeek(now, { locale: it });
    const weekEnd = endOfWeek(now, { locale: it });
    const thisWeek = events.filter(
      (e) => e.data_inizio >= weekStart && e.data_inizio <= weekEnd
    );
    const completed = thisWeek.filter((e) => e.stato === "Completato").length;
    const scheduled = thisWeek.filter((e) => e.stato === "Programmato").length;
    const cancelled = thisWeek.filter((e) => e.stato === "Cancellato").length;
    const denominator = completed + cancelled + scheduled;
    const rate = denominator > 0 ? Math.round((completed / denominator) * 100) : 0;
    return { total: thisWeek.length, completed, scheduled, rate };
  }, [events]);

  // ── Eventi passati ancora "Programmato" (per bulk complete) ──
  const pastProgrammed = useMemo(() => {
    const now = new Date();
    return events.filter((e) => e.data_fine < now && e.stato === "Programmato");
  }, [events]);

  // ── Mutation per Drag & Drop + Quick Actions ──
  const updateEvent = useUpdateEvent();

  const [bulkCompleting, setBulkCompleting] = useState(false);

  /** Quick action dall'hover card: aggiorna stato evento */
  const handleQuickAction = useCallback(
    (eventId: number, stato: string) => {
      updateEvent.mutate({ id: eventId, stato });
    },
    [updateEvent]
  );

  /** Bulk complete: completa tutti gli eventi passati ancora Programmato */
  const handleBulkComplete = useCallback(async () => {
    if (pastProgrammed.length === 0) return;
    setBulkCompleting(true);
    const promises = pastProgrammed.map((e) =>
      updateEvent.mutateAsync({ id: e.id, stato: "Completato" }).catch(() => null)
    );
    const results = await Promise.allSettled(promises);
    const succeeded = results.filter((r) => r.status === "fulfilled" && r.value !== null).length;
    setBulkCompleting(false);
    toast.success(
      `${succeeded} ${succeeded === 1 ? "sessione completata" : "sessioni completate"}`
    );
  }, [pastProgrammed, updateEvent]);

  // ── Handlers ──

  const handleNewEvent = () => {
    setSelectedEvent(null);
    setSlotStart(undefined);
    setSlotEnd(undefined);
    setSheetOpen(true);
  };

  const handleSelectSlot = useCallback((slotInfo: SlotInfo) => {
    setSelectedEvent(null);
    setSlotStart(slotInfo.start);
    setSlotEnd(slotInfo.end);
    setSheetOpen(true);
  }, []);

  const handleSelectEvent = useCallback((event: CalendarEvent) => {
    setSelectedEvent(event);
    setSlotStart(undefined);
    setSlotEnd(undefined);
    setSheetOpen(true);
  }, []);

  const handleDeleteRequest = () => {
    setSheetOpen(false);
    setDeleteOpen(true);
  };

  const handleRangeChange = useCallback((range: { start: Date; end: Date }) => {
    // Buffer di 1 mese in entrambe le direzioni per navigazione fluida
    setDateRange({
      start: startOfMonth(subMonths(range.start, 1)),
      end: endOfMonth(addMonths(range.end, 1)),
    });
  }, []);

  /** D&D: evento spostato in un nuovo slot */
  const handleEventDrop = useCallback(
    ({ event, start, end }: { event: CalendarEvent; start: Date; end: Date }) => {
      updateEvent.mutate({
        id: event.id,
        data_inizio: start.toISOString(),
        data_fine: end.toISOString(),
      });
    },
    [updateEvent]
  );

  /** D&D: evento ridimensionato */
  const handleEventResize = useCallback(
    ({ event, start, end }: { event: CalendarEvent; start: Date; end: Date }) => {
      updateEvent.mutate({
        id: event.id,
        data_inizio: start.toISOString(),
        data_fine: end.toISOString(),
      });
    },
    [updateEvent]
  );

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900/40 dark:to-blue-800/30">
            <CalendarDays className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Agenda</h1>
            <p className="text-sm text-muted-foreground">
              {filteredEvents.length} event{filteredEvents.length !== 1 ? "i" : "o"} nel periodo
              {filteredEvents.length !== events.length && (
                <span className="text-muted-foreground/60"> (filtrati da {events.length})</span>
              )}
            </p>
          </div>
        </div>
        <Button
          onClick={handleNewEvent}
          className="bg-blue-600 text-white shadow-sm hover:bg-blue-700"
        >
          <Plus className="mr-2 h-4 w-4" />
          Nuovo Evento
        </Button>
      </div>

      {/* ── Filtri + Legenda ── */}
      <FilterBar activeCategories={activeCategories} onToggle={handleToggleCategory} />

      {/* ── Bulk Complete Banner ── */}
      {!isLoading && pastProgrammed.length > 0 && (
        <BulkCompleteBanner
          count={pastProgrammed.length}
          onComplete={handleBulkComplete}
          isPending={bulkCompleting}
        />
      )}

      {/* ── KPI settimanali ── */}
      {!isLoading && <WeeklyStatsBar stats={weekStats} />}

      {/* ── Contenuto: 3-state rendering ── */}
      {isLoading && <CalendarSkeleton />}

      {isError && (
        <div className="flex items-center justify-between rounded-xl border border-destructive/50 bg-destructive/5 p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-destructive" />
            <p className="text-sm text-destructive">
              Errore nel caricamento degli eventi.
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Riprova
          </Button>
        </div>
      )}

      {!isLoading && !isError && (
        <AgendaCalendar
          events={filteredEvents}
          onSelectSlot={handleSelectSlot}
          onSelectEvent={handleSelectEvent}
          onRangeChange={handleRangeChange}
          onEventDrop={handleEventDrop}
          onEventResize={handleEventResize}
          onQuickAction={handleQuickAction}
        />
      )}

      {/* ── Sheet crea/modifica ── */}
      <EventSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        event={selectedEvent}
        defaultStart={slotStart}
        defaultEnd={slotEnd}
        onDeleteRequest={handleDeleteRequest}
      />

      {/* ── Dialog elimina ── */}
      <DeleteEventDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        event={selectedEvent}
      />
    </div>
  );
}

// ── Weekly Stats Bar ──

interface WeekStatsData {
  total: number;
  completed: number;
  scheduled: number;
  rate: number;
}

const WEEK_KPI = [
  {
    key: "total" as const,
    label: "Sessioni",
    icon: CalendarDays,
    borderColor: "border-l-blue-500",
    iconBg: "bg-blue-100 dark:bg-blue-900/30",
    iconColor: "text-blue-600 dark:text-blue-400",
    valueColor: "text-blue-700 dark:text-blue-300",
  },
  {
    key: "completed" as const,
    label: "Completate",
    icon: CheckCircle2,
    borderColor: "border-l-emerald-500",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    valueColor: "text-emerald-700 dark:text-emerald-300",
  },
  {
    key: "scheduled" as const,
    label: "Programmate",
    icon: Clock,
    borderColor: "border-l-amber-500",
    iconBg: "bg-amber-100 dark:bg-amber-900/30",
    iconColor: "text-amber-600 dark:text-amber-400",
    valueColor: "text-amber-700 dark:text-amber-300",
  },
  {
    key: "rate" as const,
    label: "Completamento",
    icon: Target,
    borderColor: "border-l-violet-500",
    iconBg: "bg-violet-100 dark:bg-violet-900/30",
    iconColor: "text-violet-600 dark:text-violet-400",
    valueColor: "text-violet-700 dark:text-violet-300",
    suffix: "%",
  },
];

function WeeklyStatsBar({ stats }: { stats: WeekStatsData }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {WEEK_KPI.map((kpi) => {
        const Icon = kpi.icon;
        const value = stats[kpi.key];
        return (
          <div
            key={kpi.key}
            className={`flex items-center gap-3 rounded-lg border border-l-4 ${kpi.borderColor} bg-white p-3 shadow-sm transition-shadow hover:shadow-md dark:bg-zinc-900`}
          >
            <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${kpi.iconBg}`}>
              <Icon className={`h-4 w-4 ${kpi.iconColor}`} />
            </div>
            <div>
              <p className={`text-xl font-bold tabular-nums ${kpi.valueColor}`}>
                {value}{"suffix" in kpi ? kpi.suffix : ""}
              </p>
              <p className="text-[10px] font-medium text-muted-foreground">
                {kpi.label} · questa settimana
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Bulk Complete Banner ──

function BulkCompleteBanner({
  count,
  onComplete,
  isPending,
}: {
  count: number;
  onComplete: () => void;
  isPending: boolean;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-l-4 border-l-amber-500 bg-gradient-to-r from-amber-50/80 to-white p-4 shadow-sm dark:from-amber-950/30 dark:to-zinc-900">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900/30">
        <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">
          {count} {count === 1 ? "sessione passata" : "sessioni passate"} ancora in stato <span className="font-semibold text-amber-600 dark:text-amber-400">Programmato</span>
        </p>
        <p className="text-xs text-muted-foreground">
          Aggiorna lo stato per mantenere le statistiche accurate
        </p>
      </div>
      <Button
        variant="outline"
        size="sm"
        className="shrink-0 gap-1.5 text-xs font-medium text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-950/30"
        onClick={onComplete}
        disabled={isPending}
      >
        {isPending ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <CheckCircle2 className="h-3.5 w-3.5" />
        )}
        Completa tutte
      </Button>
    </div>
  );
}

// ── Filter Bar (categoria interattiva + stato statico) ──

function FilterBar({
  activeCategories,
  onToggle,
}: {
  activeCategories: Set<string>;
  onToggle: (cat: string) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-4 rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 px-4 py-2.5 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
      {/* Filtri categoria (cliccabili) */}
      <span className="text-xs font-medium text-muted-foreground">Filtra:</span>
      {CATEGORY_LEGEND.map((cat) => {
        const active = activeCategories.has(cat.categoria);
        const Icon = active ? Eye : EyeOff;
        return (
          <button
            key={cat.categoria}
            type="button"
            onClick={() => onToggle(cat.categoria)}
            className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-all duration-200 ${
              active
                ? "border-transparent shadow-sm"
                : "border-dashed border-muted-foreground/30 opacity-40"
            }`}
            style={
              active
                ? { backgroundColor: cat.borderColor + "20", color: cat.borderColor }
                : undefined
            }
          >
            <div
              className="h-2.5 w-2.5 rounded-full transition-opacity"
              style={{ backgroundColor: cat.borderColor, opacity: active ? 1 : 0.3 }}
            />
            {cat.label}
            <Icon className="h-3 w-3" />
          </button>
        );
      })}

      {/* Separatore */}
      <div className="h-5 w-px bg-border" />

      {/* Indicatori stato (statici) */}
      <span className="text-xs font-medium text-muted-foreground">Stato:</span>
      {STATUS_LEGEND.map((s) => (
        <Badge
          key={s.stato}
          variant="outline"
          className="text-[10px] px-2 py-0"
          style={{
            backgroundColor: s.backgroundColor,
            color: s.color,
            borderColor: "transparent",
          }}
        >
          {s.label}
        </Badge>
      ))}
    </div>
  );
}

// ── Skeleton per il calendario ──

function CalendarSkeleton() {
  return (
    <div className="space-y-3">
      {/* Toolbar skeleton */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1.5">
          <Skeleton className="h-9 w-9 rounded-md" />
          <Skeleton className="h-9 w-16 rounded-md" />
          <Skeleton className="h-9 w-9 rounded-md" />
        </div>
        <Skeleton className="h-6 w-40 rounded" />
        <div className="flex gap-1.5">
          <Skeleton className="h-9 w-20 rounded-md" />
          <Skeleton className="h-9 w-24 rounded-md" />
          <Skeleton className="h-9 w-20 rounded-md" />
        </div>
      </div>
      {/* Grid skeleton */}
      <div className="rounded-lg border">
        {/* Header row */}
        <div className="flex border-b">
          <Skeleton className="h-10 w-16 shrink-0" />
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="h-10 flex-1 border-l" />
          ))}
        </div>
        {/* Time rows */}
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex border-b last:border-b-0">
            <Skeleton className="h-16 w-16 shrink-0" />
            {Array.from({ length: 7 }).map((_, j) => (
              <div key={j} className="h-16 flex-1 border-l" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
