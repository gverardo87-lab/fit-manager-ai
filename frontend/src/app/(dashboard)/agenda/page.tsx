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
import { format, startOfMonth, endOfMonth, subMonths, addMonths } from "date-fns";
import { Plus, CalendarDays } from "lucide-react";
import type { SlotInfo } from "react-big-calendar";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AgendaCalendar } from "@/components/agenda/AgendaCalendar";
import { EventSheet } from "@/components/agenda/EventSheet";
import { DeleteEventDialog } from "@/components/agenda/DeleteEventDialog";
import { useEvents } from "@/hooks/useAgenda";
import type { CalendarEvent } from "@/components/agenda/calendar-setup";

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

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <CalendarDays className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Agenda</h1>
            <p className="text-sm text-muted-foreground">
              {events.length} event{events.length !== 1 ? "i" : "o"} nel periodo
            </p>
          </div>
        </div>
        <Button onClick={handleNewEvent}>
          <Plus className="mr-2 h-4 w-4" />
          Nuovo Evento
        </Button>
      </div>

      {/* ── Contenuto: 3-state rendering ── */}
      {isLoading && <CalendarSkeleton />}

      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <p className="text-destructive">
            Errore nel caricamento degli eventi.
          </p>
          <Button
            variant="outline"
            size="sm"
            className="mt-3"
            onClick={() => refetch()}
          >
            Riprova
          </Button>
        </div>
      )}

      {!isLoading && !isError && (
        <AgendaCalendar
          events={events}
          onSelectSlot={handleSelectSlot}
          onSelectEvent={handleSelectEvent}
          onRangeChange={handleRangeChange}
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

// ── Skeleton per il calendario ──

function CalendarSkeleton() {
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Skeleton className="h-9 w-24" />
        <Skeleton className="h-9 w-24" />
        <Skeleton className="h-9 w-24" />
        <div className="flex-1" />
        <Skeleton className="h-9 w-20" />
        <Skeleton className="h-9 w-20" />
        <Skeleton className="h-9 w-20" />
      </div>
      <Skeleton className="h-[700px] w-full" />
    </div>
  );
}
