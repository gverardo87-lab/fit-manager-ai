// src/components/agenda/CustomToolbar.tsx
"use client";

/**
 * Toolbar personalizzata per react-big-calendar con shadcn/ui.
 *
 * Desktop: [< Oggi >]  [Febbraio 2026]  [Mese | Settimana | Giorno]
 * Mobile:  [Febbraio 2026]
 *          [< Oggi >]  [M | S | G]  (icone only)
 */

import { useMemo } from "react";
import type { ToolbarProps, View } from "react-big-calendar";
import { format, isToday } from "date-fns";
import { it } from "date-fns/locale";
import { ChevronLeft, ChevronRight, CalendarDays, CalendarRange, Calendar } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { CalendarEvent } from "./calendar-setup";

const VIEWS: { key: View; label: string; icon: typeof CalendarDays }[] = [
  { key: "month", label: "Mese", icon: Calendar },
  { key: "week", label: "Settimana", icon: CalendarRange },
  { key: "day", label: "Giorno", icon: CalendarDays },
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

  const todayActive = useMemo(() => isToday(date), [date]);

  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
      {/* Label data corrente — prima riga su mobile, centro su desktop */}
      <h2 className="w-full text-center text-base font-bold capitalize tracking-tight sm:w-auto sm:order-2 sm:text-lg">
        {label}
      </h2>

      {/* Navigazione */}
      <div className="flex items-center gap-1 sm:order-1">
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8 sm:h-9 sm:w-9"
          onClick={() => onNavigate("PREV")}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button
          variant={todayActive ? "default" : "outline"}
          size="sm"
          className="relative"
          onClick={() => onNavigate("TODAY")}
        >
          Oggi
          {!todayActive && (
            <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-blue-500" />
          )}
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8 sm:h-9 sm:w-9"
          onClick={() => onNavigate("NEXT")}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Selettore vista — icone only su mobile */}
      <div className="flex items-center gap-1 rounded-lg bg-muted/50 p-1 sm:order-3">
        {VIEWS.map((v) => {
          const Icon = v.icon;
          const active = view === v.key;
          return (
            <Button
              key={v.key}
              variant={active ? "default" : "ghost"}
              size="sm"
              className={`gap-1.5 ${active ? "" : "text-muted-foreground hover:text-foreground"}`}
              onClick={() => onView(v.key)}
            >
              <Icon className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{v.label}</span>
            </Button>
          );
        })}
      </div>
    </div>
  );
}
