// src/components/agenda/EventHoverCard.tsx
"use client";

/**
 * Hover card per eventi del calendario.
 *
 * Mostra info dettagliate + azioni rapide (Completa, Rinvia, Cancella)
 * senza aprire il Sheet completo.
 *
 * NOTA: usa createPortal per renderizzare il popup nel <body>.
 * Motivo: react-big-calendar wrappa gli eventi in .rbc-event con
 * overflow:hidden — un popup position:absolute verrebbe clippato.
 */

import { useState, useRef, useCallback, useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import { CheckCircle2, RotateCcw, X, Clock, User } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { CATEGORY_LABELS } from "./calendar-setup";
import type { CalendarEvent } from "./calendar-setup";
import type { EventCategory } from "@/types/api";

const CATEGORY_DOT_COLORS: Record<string, string> = {
  PT: "bg-blue-500",
  SALA: "bg-zinc-400",
  CORSO: "bg-emerald-500",
  COLLOQUIO: "bg-amber-500",
};

const STATUS_BADGES: Record<string, { bg: string; text: string }> = {
  Programmato: { bg: "bg-blue-100 dark:bg-blue-900/40", text: "text-blue-700 dark:text-blue-300" },
  Completato: { bg: "bg-emerald-100 dark:bg-emerald-900/40", text: "text-emerald-700 dark:text-emerald-300" },
  Cancellato: { bg: "bg-zinc-100 dark:bg-zinc-800", text: "text-zinc-500" },
  Rinviato: { bg: "bg-amber-100 dark:bg-amber-900/40", text: "text-amber-700 dark:text-amber-300" },
};

interface EventHoverCardProps {
  event: CalendarEvent;
  onQuickAction?: (eventId: number, stato: string) => void;
  children: ReactNode;
}

export function EventHoverCard({ event, onQuickAction, children }: EventHoverCardProps) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);
  const enterTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const leaveTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = useCallback(() => {
    if (leaveTimeout.current) {
      clearTimeout(leaveTimeout.current);
      leaveTimeout.current = null;
    }
    enterTimeout.current = setTimeout(() => setOpen(true), 350);
  }, []);

  const handleMouseLeave = useCallback(() => {
    if (enterTimeout.current) {
      clearTimeout(enterTimeout.current);
      enterTimeout.current = null;
    }
    leaveTimeout.current = setTimeout(() => setOpen(false), 200);
  }, []);

  // Calcola posizione del popup quando si apre
  useEffect(() => {
    if (!open || !triggerRef.current) {
      setPosition(null);
      return;
    }
    const rect = triggerRef.current.getBoundingClientRect();
    const popupWidth = 260;
    // Centra orizzontalmente rispetto al trigger, sotto di esso
    let left = rect.left + rect.width / 2 - popupWidth / 2;
    // Evita di uscire dal viewport a sinistra/destra
    left = Math.max(8, Math.min(left, window.innerWidth - popupWidth - 8));
    setPosition({ top: rect.bottom + 4, left });
  }, [open]);

  const handleAction = useCallback(
    (stato: string) => {
      setOpen(false);
      onQuickAction?.(event.id, stato);
    },
    [event.id, onQuickAction]
  );

  // Cleanup timeouts
  useEffect(() => {
    return () => {
      if (enterTimeout.current) clearTimeout(enterTimeout.current);
      if (leaveTimeout.current) clearTimeout(leaveTimeout.current);
    };
  }, []);

  const statusBadge = STATUS_BADGES[event.stato] ?? STATUS_BADGES.Programmato;
  const catDot = CATEGORY_DOT_COLORS[event.categoria] ?? "bg-zinc-400";
  const catLabel = CATEGORY_LABELS[event.categoria as EventCategory] ?? event.categoria;
  const canAct = event.stato === "Programmato" || event.stato === "Rinviato";

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {children}
      </div>

      {open && position && createPortal(
        <div
          ref={popupRef}
          className="fixed z-[9999]"
          style={{ top: position.top, left: position.left }}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <div className="w-[260px] rounded-xl border bg-popover p-3.5 shadow-lg animate-in fade-in-0 zoom-in-95 duration-150">
            {/* Header: categoria + stato */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`h-2.5 w-2.5 rounded-full ${catDot}`} />
                <span className="text-xs font-semibold">{catLabel}</span>
              </div>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${statusBadge.bg} ${statusBadge.text}`}>
                {event.stato}
              </span>
            </div>

            {/* Titolo */}
            <p className="mt-1.5 text-sm font-medium leading-tight truncate">
              {event.title}
            </p>

            {/* Cliente (se presente) */}
            {event.cliente_nome && (
              <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
                <User className="h-3 w-3" />
                <span>{event.cliente_nome} {event.cliente_cognome ?? ""}</span>
              </div>
            )}

            {/* Orario */}
            <div className="mt-1.5 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>
                {format(event.start, "HH:mm")} — {format(event.end, "HH:mm")}
                <span className="ml-1.5 text-muted-foreground/60">
                  {format(event.start, "EEEE d MMM", { locale: it })}
                </span>
              </span>
            </div>

            {/* Note (troncate) */}
            {event.note && (
              <p className="mt-1.5 truncate text-[11px] text-muted-foreground/80 italic">
                {event.note}
              </p>
            )}

            {/* Quick Actions */}
            {canAct && onQuickAction && (
              <>
                <Separator className="my-2.5" />
                <div className="flex gap-1.5">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 flex-1 gap-1 text-[11px] text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-950/30"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAction("Completato");
                    }}
                  >
                    <CheckCircle2 className="h-3 w-3" />
                    Completa
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 flex-1 gap-1 text-[11px] text-amber-600 hover:text-amber-700 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-950/30"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAction("Rinviato");
                    }}
                  >
                    <RotateCcw className="h-3 w-3" />
                    Rinvia
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 w-8 shrink-0 p-0 text-[11px] text-red-500 hover:text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAction("Cancellato");
                    }}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
