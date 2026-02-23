// src/components/dashboard/GhostEventsSheet.tsx
/**
 * Sheet per risoluzione inline eventi fantasma.
 *
 * Mostra sessioni passate ancora "Programmato" con azioni 1-click:
 * - Completata / Cancellata per singolo evento
 * - Completa tutte / Cancella tutte per azioni di massa
 *
 * Usa useUpdateEvent() dall'agenda — invalida automaticamente
 * dashboard, events, clients, contracts (credit engine).
 */

"use client";

import { useState } from "react";
import {
  Ghost,
  CheckCircle2,
  XCircle,
  Calendar,
  User,
  Loader2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { useGhostEvents } from "@/hooks/useDashboard";
import { useUpdateEvent } from "@/hooks/useAgenda";
import type { Event } from "@/types/api";

// ── Colori categoria (mirror agenda) ──

const CATEGORY_COLORS: Record<string, string> = {
  PT: "bg-blue-500",
  SALA: "bg-emerald-500",
  CORSO: "bg-violet-500",
  COLLOQUIO: "bg-amber-500",
};

// ── Helpers ──

function formatEventDate(iso: string): string {
  const d = new Date(iso.replace(" ", "T"));
  return d.toLocaleDateString("it-IT", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

function formatEventTime(iso: string): string {
  const d = new Date(iso.replace(" ", "T"));
  return d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
}

function daysAgo(iso: string): number {
  const d = new Date(iso.replace(" ", "T"));
  const now = new Date();
  return Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
}

// ════════════════════════════════════════════════════════════

interface GhostEventsSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function GhostEventsSheet({ open, onOpenChange }: GhostEventsSheetProps) {
  const { data, isLoading } = useGhostEvents(open);
  const updateEvent = useUpdateEvent();
  const [resolving, setResolving] = useState<Set<number>>(new Set());
  const [bulkAction, setBulkAction] = useState<string | null>(null);

  const events = data?.items ?? [];
  const unresolvedCount = events.filter((e) => !resolving.has(e.id)).length;

  // ── Risolvi singolo evento ──
  const handleResolve = (event: Event, stato: "Completato" | "Cancellato") => {
    setResolving((prev) => new Set(prev).add(event.id));
    updateEvent.mutate(
      { id: event.id, stato },
      {
        onSettled: () => {
          setResolving((prev) => {
            const next = new Set(prev);
            next.delete(event.id);
            return next;
          });
        },
      }
    );
  };

  // ── Risolvi tutti ──
  const handleBulkResolve = (stato: "Completato" | "Cancellato") => {
    setBulkAction(stato);
    const pending = events.filter((e) => !resolving.has(e.id));
    const ids = new Set(pending.map((e) => e.id));
    setResolving((prev) => new Set([...prev, ...ids]));

    let completed = 0;
    for (const event of pending) {
      updateEvent.mutate(
        { id: event.id, stato },
        {
          onSettled: () => {
            completed++;
            if (completed === pending.length) {
              setBulkAction(null);
              setResolving(new Set());
            }
          },
        }
      );
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-hidden sm:max-w-lg">
        <SheetHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-100 dark:bg-red-900/30">
              <Ghost className="h-5 w-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <SheetTitle>Eventi da aggiornare</SheetTitle>
              <SheetDescription>
                Sessioni passate ancora in stato &quot;Programmato&quot;
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <Separator />

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3 p-1">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        )}

        {/* Empty — tutti risolti */}
        {!isLoading && events.length === 0 && (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
              <CheckCircle2 className="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
            </div>
            <p className="text-sm font-semibold text-emerald-700 dark:text-emerald-400">
              Tutto aggiornato!
            </p>
            <p className="text-xs text-muted-foreground">
              Nessun evento in sospeso
            </p>
          </div>
        )}

        {/* Lista eventi */}
        {!isLoading && events.length > 0 && (
          <>
            <ScrollArea className="min-h-0 flex-1 -mx-1 px-1">
              <div className="space-y-3 pb-4">
                {events.map((event) => {
                  const isResolving = resolving.has(event.id);
                  const catColor = CATEGORY_COLORS[event.categoria] ?? "bg-zinc-400";
                  const days = daysAgo(event.data_inizio);

                  return (
                    <div
                      key={event.id}
                      className={`rounded-lg border p-4 transition-all ${
                        isResolving
                          ? "opacity-40 scale-[0.98]"
                          : "hover:shadow-sm"
                      }`}
                    >
                      {/* Header: categoria + data */}
                      <div className="mb-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={`h-2.5 w-2.5 rounded-full ${catColor}`} />
                          <Badge variant="outline" className="text-[10px]">
                            {event.categoria}
                          </Badge>
                          {days > 7 && (
                            <Badge variant="destructive" className="text-[9px] px-1.5 py-0 h-4">
                              {days}gg fa
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          <span>{formatEventDate(event.data_inizio)}</span>
                        </div>
                      </div>

                      {/* Titolo + orario */}
                      <p className="text-sm font-semibold leading-tight">
                        {event.titolo || event.categoria}
                      </p>
                      <p className="text-xs text-muted-foreground tabular-nums">
                        {formatEventTime(event.data_inizio)} — {formatEventTime(event.data_fine)}
                      </p>

                      {/* Cliente */}
                      {event.cliente_nome && (
                        <div className="mt-1.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                          <User className="h-3 w-3" />
                          <span>{event.cliente_nome} {event.cliente_cognome}</span>
                        </div>
                      )}

                      {/* Azioni */}
                      <div className="mt-3 flex gap-2">
                        <Button
                          size="sm"
                          className="h-8 flex-1 gap-1.5 bg-emerald-600 text-xs font-medium text-white hover:bg-emerald-700"
                          disabled={isResolving}
                          onClick={() => handleResolve(event, "Completato")}
                        >
                          {isResolving ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <CheckCircle2 className="h-3.5 w-3.5" />
                          )}
                          Completata
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 flex-1 gap-1.5 text-xs font-medium text-red-600 hover:bg-red-50 hover:text-red-700 dark:text-red-400 dark:hover:bg-red-950/30"
                          disabled={isResolving}
                          onClick={() => handleResolve(event, "Cancellato")}
                        >
                          {isResolving ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <XCircle className="h-3.5 w-3.5" />
                          )}
                          Cancellata
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>

            {/* Azioni di massa */}
            {unresolvedCount > 1 && (
              <>
                <Separator />
                <div className="pt-2 pb-1">
                  <p className="mb-2.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                    Azioni di massa ({unresolvedCount} {unresolvedCount === 1 ? "evento" : "eventi"})
                  </p>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      className="h-9 flex-1 gap-1.5 bg-emerald-600 text-xs font-medium text-white hover:bg-emerald-700"
                      disabled={!!bulkAction}
                      onClick={() => handleBulkResolve("Completato")}
                    >
                      {bulkAction === "Completato" ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <CheckCircle2 className="h-3.5 w-3.5" />
                      )}
                      Completa tutte
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-9 flex-1 gap-1.5 text-xs font-medium text-red-600 hover:bg-red-50 hover:text-red-700 dark:text-red-400 dark:hover:bg-red-950/30"
                      disabled={!!bulkAction}
                      onClick={() => handleBulkResolve("Cancellato")}
                    >
                      {bulkAction === "Cancellato" ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <XCircle className="h-3.5 w-3.5" />
                      )}
                      Cancella tutte
                    </Button>
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
