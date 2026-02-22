// src/components/agenda/CustomToolbar.tsx
"use client";

/**
 * Toolbar personalizzata per react-big-calendar con shadcn/ui.
 *
 * Layout: [< Oggi >]  [Febbraio 2026]  [Mese | Settimana | Giorno]
 */

import type { ToolbarProps, View } from "react-big-calendar";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { CalendarEvent } from "./calendar-setup";

const VIEWS: { key: View; label: string }[] = [
  { key: "month", label: "Mese" },
  { key: "week", label: "Settimana" },
  { key: "day", label: "Giorno" },
];

export function CustomToolbar({
  date,
  view,
  onNavigate,
  onView,
}: ToolbarProps<CalendarEvent, object>) {
  const label = format(
    date,
    view === "day" ? "EEEE d MMMM yyyy" : "MMMM yyyy",
    { locale: it }
  );

  return (
    <div className="flex items-center justify-between mb-4">
      {/* Navigazione */}
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          onClick={() => onNavigate("PREV")}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onNavigate("TODAY")}
        >
          Oggi
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => onNavigate("NEXT")}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Label data corrente */}
      <h2 className="text-lg font-semibold capitalize">{label}</h2>

      {/* Selettore vista */}
      <div className="flex items-center gap-1">
        {VIEWS.map((v) => (
          <Button
            key={v.key}
            variant={view === v.key ? "default" : "outline"}
            size="sm"
            onClick={() => onView(v.key)}
          >
            {v.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
