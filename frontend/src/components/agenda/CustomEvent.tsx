// src/components/agenda/CustomEvent.tsx
"use client";

/**
 * Componente evento personalizzato per react-big-calendar.
 *
 * - PT con cliente: mostra "Nome Cognome"
 * - Altri eventi: mostra il titolo
 * - Tailwind truncate per eventi corti
 */

import type { EventProps } from "react-big-calendar";
import type { CalendarEvent } from "./calendar-setup";

export function CustomEvent({ event }: EventProps<CalendarEvent>) {
  const label =
    event.cliente_nome
      ? `${event.cliente_nome} ${event.cliente_cognome}`
      : event.title;

  return (
    <div className="truncate text-xs leading-tight">
      <span className="font-medium">{label}</span>
    </div>
  );
}
