// src/components/agenda/CustomEvent.tsx
"use client";

/**
 * Componente evento personalizzato per react-big-calendar.
 *
 * - PT con cliente: mostra "Nome Cognome" (categoria implicita dal bordo)
 * - Altri eventi: mostra il titolo
 * - Cancellato: line-through + opacity ridotta
 * - Hover: mostra EventHoverCard con info + quick actions
 */

import { createContext, useContext, type ReactNode } from "react";
import type { EventProps } from "react-big-calendar";
import type { CalendarEvent } from "./calendar-setup";
import { EventHoverCard } from "./EventHoverCard";

// ── Context per passare onQuickAction al CustomEvent ──

type QuickActionFn = (eventId: number, stato: string) => void;

const QuickActionContext = createContext<QuickActionFn | undefined>(undefined);

export function QuickActionProvider({
  onQuickAction,
  children,
}: {
  onQuickAction?: QuickActionFn;
  children: ReactNode;
}) {
  return (
    <QuickActionContext.Provider value={onQuickAction}>
      {children}
    </QuickActionContext.Provider>
  );
}

// ── Custom Event ──

export function CustomEvent({ event }: EventProps<CalendarEvent>) {
  const onQuickAction = useContext(QuickActionContext);
  const isCancelled = event.stato === "Cancellato";

  // PT con cliente: nome del cliente. Tutto il resto: titolo.
  const label = event.cliente_nome
    ? `${event.cliente_nome} ${event.cliente_cognome ?? ""}`.trim()
    : event.title;

  return (
    <EventHoverCard event={event} onQuickAction={onQuickAction}>
      <div className="truncate text-xs leading-tight">
        <span
          className={`font-medium ${isCancelled ? "line-through opacity-60" : ""}`}
        >
          {label}
        </span>
      </div>
    </EventHoverCard>
  );
}
