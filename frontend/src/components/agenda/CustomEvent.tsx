// src/components/agenda/CustomEvent.tsx
"use client";

/**
 * Componente evento personalizzato per react-big-calendar.
 *
 * - PT con cliente: mostra "Nome Cognome" (categoria implicita dal bordo)
 * - Altri eventi: mostra il titolo
 * - Cancellato: line-through + opacity ridotta
 */

import type { EventProps } from "react-big-calendar";
import type { CalendarEvent } from "./calendar-setup";

export function CustomEvent({ event }: EventProps<CalendarEvent>) {
  const isCancelled = event.stato === "Cancellato";

  // PT con cliente: nome del cliente. Tutto il resto: titolo.
  const label = event.cliente_nome
    ? `${event.cliente_nome} ${event.cliente_cognome ?? ""}`.trim()
    : event.title;

  return (
    <div className="truncate text-xs leading-tight">
      <span
        className={`font-medium ${isCancelled ? "line-through opacity-60" : ""}`}
      >
        {label}
      </span>
    </div>
  );
}
