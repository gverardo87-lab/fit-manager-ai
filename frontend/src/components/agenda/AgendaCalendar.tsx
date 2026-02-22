// src/components/agenda/AgendaCalendar.tsx
"use client";

/**
 * Wrapper react-big-calendar con:
 * - Drag & Drop (withDragAndDrop HOC)
 * - Controlled state (date + view)
 * - Custom Toolbar (shadcn/ui)
 * - Custom Event (nome cliente per PT)
 * - Vista settimanale default, slot 30 min, 06:00-22:00
 */

import { useState, useCallback, useMemo } from "react";
import { Calendar, Views, type View, type SlotInfo } from "react-big-calendar";
import withDragAndDrop from "react-big-calendar/lib/addons/dragAndDrop";

import {
  localizer,
  italianMessages,
  getEventStyle,
  toCalendarEvent,
  type CalendarEvent,
} from "./calendar-setup";
import { CustomToolbar } from "./CustomToolbar";
import { CustomEvent } from "./CustomEvent";
import type { EventHydrated } from "@/hooks/useAgenda";

// HOC: abilita drag & drop + resize sugli eventi
const DnDCalendar = withDragAndDrop<CalendarEvent>(Calendar);

interface AgendaCalendarProps {
  events: EventHydrated[];
  onSelectSlot: (slotInfo: SlotInfo) => void;
  onSelectEvent: (event: CalendarEvent) => void;
  onRangeChange: (range: { start: Date; end: Date }) => void;
  onEventDrop: (args: { event: CalendarEvent; start: Date; end: Date }) => void;
  onEventResize: (args: { event: CalendarEvent; start: Date; end: Date }) => void;
}

export function AgendaCalendar({
  events,
  onSelectSlot,
  onSelectEvent,
  onRangeChange,
  onEventDrop,
  onEventResize,
}: AgendaCalendarProps) {
  // ── Controlled state: data corrente + vista attiva ──
  const [currentDate, setCurrentDate] = useState(new Date());
  const [currentView, setCurrentView] = useState<View>(Views.WEEK);

  const calendarEvents = useMemo(
    () => events.map(toCalendarEvent),
    [events]
  );

  const eventPropGetter = useCallback(
    (event: CalendarEvent) => ({ style: getEventStyle(event) }),
    []
  );

  /**
   * onRangeChange riceve formati diversi a seconda della vista:
   * - Month/Week: { start: Date, end: Date }
   * - Day: Date[]
   * Normalizziamo sempre a { start, end }.
   */
  const handleRangeChange = useCallback(
    (range: Date[] | { start: Date; end: Date }) => {
      if (Array.isArray(range)) {
        onRangeChange({ start: range[0], end: range[range.length - 1] });
      } else {
        onRangeChange(range);
      }
    },
    [onRangeChange]
  );

  /** D&D: evento trascinato in un nuovo slot */
  const handleEventDrop = useCallback(
    ({ event, start, end }: { event: CalendarEvent; start: string | Date; end: string | Date }) => {
      onEventDrop({
        event,
        start: new Date(start),
        end: new Date(end),
      });
    },
    [onEventDrop]
  );

  /** D&D: evento ridimensionato (resize bordo inferiore) */
  const handleEventResize = useCallback(
    ({ event, start, end }: { event: CalendarEvent; start: string | Date; end: string | Date }) => {
      onEventResize({
        event,
        start: new Date(start),
        end: new Date(end),
      });
    },
    [onEventResize]
  );

  return (
    <DnDCalendar
      localizer={localizer}
      events={calendarEvents}
      date={currentDate}
      view={currentView}
      onNavigate={setCurrentDate}
      onView={setCurrentView}
      views={[Views.MONTH, Views.WEEK, Views.DAY]}
      selectable
      resizable
      onSelectSlot={onSelectSlot}
      onSelectEvent={onSelectEvent}
      onRangeChange={handleRangeChange}
      onEventDrop={handleEventDrop}
      onEventResize={handleEventResize}
      eventPropGetter={eventPropGetter}
      messages={italianMessages}
      components={{
        toolbar: CustomToolbar,
        event: CustomEvent,
      }}
      step={30}
      timeslots={2}
      min={new Date(0, 0, 0, 6, 0)}
      max={new Date(0, 0, 0, 22, 0)}
      popup
      style={{ minHeight: 700 }}
    />
  );
}
