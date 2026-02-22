// src/components/agenda/AgendaCalendar.tsx
"use client";

/**
 * Wrapper react-big-calendar — vista settimanale default, slot 30 min.
 *
 * Props callback per interazione:
 * - onSelectSlot: click su slot vuoto -> crea evento
 * - onSelectEvent: click su evento -> modifica
 * - onRangeChange: navigazione -> aggiorna date range per API query
 */

import { useCallback, useMemo } from "react";
import { Calendar, Views, type SlotInfo } from "react-big-calendar";

import {
  localizer,
  italianMessages,
  getEventStyle,
  toCalendarEvent,
  type CalendarEvent,
} from "./calendar-setup";
import type { Event as ApiEvent } from "@/types/api";

interface AgendaCalendarProps {
  events: ApiEvent[];
  onSelectSlot: (slotInfo: SlotInfo) => void;
  onSelectEvent: (event: CalendarEvent) => void;
  onRangeChange: (range: { start: Date; end: Date }) => void;
}

export function AgendaCalendar({
  events,
  onSelectSlot,
  onSelectEvent,
  onRangeChange,
}: AgendaCalendarProps) {
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

  return (
    <Calendar<CalendarEvent>
      localizer={localizer}
      events={calendarEvents}
      views={[Views.MONTH, Views.WEEK, Views.DAY]}
      defaultView={Views.WEEK}
      selectable
      onSelectSlot={onSelectSlot}
      onSelectEvent={onSelectEvent}
      onRangeChange={handleRangeChange}
      eventPropGetter={eventPropGetter}
      messages={italianMessages}
      step={30}
      timeslots={2}
      min={new Date(0, 0, 0, 6, 0)}
      max={new Date(0, 0, 0, 22, 0)}
      popup
      style={{ minHeight: 700 }}
    />
  );
}
