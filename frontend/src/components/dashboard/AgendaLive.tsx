"use client";

/**
 * AgendaLive — Timeline verticale sessioni del giorno.
 *
 * Linea connettore sinistra, sessione corrente evidenziata,
 * status select inline, ScrollArea h-[420px].
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Calendar, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUpdateEvent, type EventHydrated } from "@/hooks/useAgenda";
import { CATEGORY_COLORS, STATUS_COLORS } from "@/lib/dashboard-helpers";
import { EVENT_STATUSES } from "@/types/api";

interface AgendaLiveProps {
  events: EventHydrated[];
  isLoading: boolean;
}

export function AgendaLive({ events, isLoading }: AgendaLiveProps) {
  const updateEvent = useUpdateEvent();
  const [clockTime, setClockTime] = useState(() => new Date());
  const [updatingEventId, setUpdatingEventId] = useState<number | null>(null);

  useEffect(() => {
    const timerId = window.setInterval(() => setClockTime(new Date()), 60_000);
    return () => window.clearInterval(timerId);
  }, []);

  const handleStatusChange = useCallback((event: EventHydrated, nextStatus: string) => {
    if (event.stato === nextStatus) return;
    setUpdatingEventId(event.id);
    updateEvent.mutate(
      { id: event.id, stato: nextStatus },
      {
        onSettled: () => {
          setUpdatingEventId((current) => (current === event.id ? null : current));
        },
      },
    );
  }, [updateEvent]);

  const nowTs = clockTime.getTime();

  if (isLoading) {
    return <AgendaLiveSkeleton />;
  }

  return (
    <div className="flex h-[420px] min-w-0 flex-col rounded-2xl border bg-gradient-to-br from-white via-white to-zinc-50/70 shadow-sm dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-800/50">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3 sm:px-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-100 to-violet-100 dark:from-blue-900/30 dark:to-violet-900/30">
            <Calendar className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold">Agenda Oggi</h3>
            <p className="text-[10px] font-medium text-muted-foreground">
              {events.length} {events.length === 1 ? "sessione" : "sessioni"}
            </p>
          </div>
        </div>
        <Link href="/agenda">
          <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs text-muted-foreground hover:text-foreground">
            Vedi tutto <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
      </div>

      {/* Content */}
      {events.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 p-6 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted/50">
            <Calendar className="h-6 w-6 text-muted-foreground/30" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">Nessun appuntamento oggi</p>
          <Link href="/agenda">
            <Button variant="outline" size="sm" className="mt-1 gap-1 text-xs">
              Apri agenda <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        </div>
      ) : (
        <ScrollArea className="min-h-0 flex-1">
          <div className="relative px-4 py-3 sm:px-5">
            {/* Vertical connector line */}
            <div className="absolute bottom-3 left-[29px] top-3 w-px bg-zinc-200 sm:left-[33px] dark:bg-zinc-700" />

            <div className="space-y-1">
              {events.map((event) => {
                const time = event.data_inizio.toLocaleTimeString("it-IT", {
                  hour: "2-digit",
                  minute: "2-digit",
                });
                const catColor = CATEGORY_COLORS[event.categoria] ?? "bg-zinc-400";
                const statusColor = STATUS_COLORS[event.stato] ?? "";
                const isActive = event.data_inizio.getTime() <= nowTs && nowTs < event.data_fine.getTime()
                  && event.stato !== "Cancellato" && event.stato !== "Completato";
                const isPast = event.data_fine.getTime() < nowTs || event.stato === "Completato";

                return (
                  <div
                    key={event.id}
                    className={`relative flex min-w-0 items-start gap-3 rounded-xl p-2.5 transition-colors ${
                      isActive
                        ? "bg-teal-50/80 dark:bg-teal-950/20"
                        : isPast
                          ? "opacity-60"
                          : "hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                    }`}
                  >
                    {/* Timeline dot */}
                    <div className="relative z-10 mt-1 flex shrink-0 flex-col items-center">
                      <div className={`h-3 w-3 rounded-full border-2 ${
                        isActive
                          ? "border-teal-500 bg-teal-500 shadow-sm shadow-teal-500/30"
                          : isPast
                            ? "border-emerald-400 bg-emerald-400"
                            : "border-zinc-300 bg-white dark:border-zinc-600 dark:bg-zinc-800"
                      }`} />
                    </div>

                    {/* Event info */}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold tabular-nums text-muted-foreground">
                          {time}
                        </span>
                        <span className={`h-2 w-2 rounded-full ${catColor}`} />
                        <Badge variant="outline" className="h-4 px-1.5 py-0 text-[9px]">
                          {event.categoria}
                        </Badge>
                        {isActive && (
                          <Badge className="h-4 bg-teal-600 px-1.5 py-0 text-[9px] text-white">
                            In corso
                          </Badge>
                        )}
                      </div>
                      <p className={`mt-0.5 truncate text-sm font-semibold leading-tight ${statusColor}`}>
                        {event.titolo || event.categoria}
                      </p>
                      {event.cliente_nome && (
                        <p className="mt-0.5 truncate text-xs text-muted-foreground">
                          {event.cliente_nome} {event.cliente_cognome}
                        </p>
                      )}
                    </div>

                    {/* Status select */}
                    <div className="shrink-0">
                      <Select
                        value={event.stato}
                        onValueChange={(value) => handleStatusChange(event, value)}
                        disabled={updatingEventId === event.id}
                      >
                        <SelectTrigger className="h-7 w-[110px] text-[11px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {EVENT_STATUSES.map((status) => (
                            <SelectItem key={status} value={status} className="text-xs">
                              {status}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {updatingEventId === event.id && (
                        <div className="mt-1 flex items-center gap-1 text-[9px] text-muted-foreground">
                          <Loader2 className="h-2.5 w-2.5 animate-spin" />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

function AgendaLiveSkeleton() {
  return (
    <div className="flex h-[420px] flex-col rounded-2xl border">
      <div className="flex items-center justify-between border-b px-4 py-3 sm:px-5">
        <div className="flex items-center gap-2.5">
          <Skeleton className="h-8 w-8 rounded-lg" />
          <div className="space-y-1">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-2.5 w-16" />
          </div>
        </div>
        <Skeleton className="h-7 w-20" />
      </div>
      <div className="space-y-2 p-4 sm:p-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-start gap-3 rounded-xl p-2.5">
            <Skeleton className="mt-1 h-3 w-3 rounded-full" />
            <div className="flex-1 space-y-1.5">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-2.5 w-28" />
            </div>
            <Skeleton className="h-7 w-[110px]" />
          </div>
        ))}
      </div>
    </div>
  );
}
