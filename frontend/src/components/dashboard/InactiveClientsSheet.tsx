// src/components/dashboard/InactiveClientsSheet.tsx
/**
 * Sheet per clienti inattivi (14+ giorni senza eventi).
 *
 * Mostra clienti attivi senza sessioni recenti:
 * - Giorni di inattivita' + ultima sessione
 * - Contatti rapidi (telefono, email)
 * - CTA "Pianifica sessione" → apre Agenda
 *
 * Obiettivo: ridurre churn con outreach proattivo.
 */

"use client";

import Link from "next/link";
import {
  UserX,
  CheckCircle2,
  Phone,
  Mail,
  Calendar,
  ArrowRight,
  Clock,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { useInactiveClients } from "@/hooks/useDashboard";
import { formatShortDate } from "@/lib/format";

// ── Helpers ──

const CATEGORY_LABELS: Record<string, string> = {
  PT: "Personal Training",
  SALA: "Sala",
  CORSO: "Corso",
  COLLOQUIO: "Colloquio",
};

function inattivitaColor(giorni: number): string {
  if (giorni >= 30) return "text-red-600 dark:text-red-400";
  if (giorni >= 21) return "text-amber-600 dark:text-amber-400";
  return "text-orange-600 dark:text-orange-400";
}

function inattivitaBadge(giorni: number): string {
  if (giorni >= 30) return "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400";
  if (giorni >= 21) return "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400";
  return "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400";
}

// ════════════════════════════════════════════════════════════

interface InactiveClientsSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function InactiveClientsSheet({ open, onOpenChange }: InactiveClientsSheetProps) {
  const { data, isLoading } = useInactiveClients(open);

  const items = data?.items ?? [];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-hidden sm:max-w-lg">
        <SheetHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-orange-100 dark:bg-orange-900/30">
              <UserX className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <SheetTitle>Clienti inattivi</SheetTitle>
              <SheetDescription>
                Nessuna sessione da 14+ giorni
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <Separator />

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3 p-1">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-28 w-full rounded-lg" />
            ))}
          </div>
        )}

        {/* Empty */}
        {!isLoading && items.length === 0 && (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
              <CheckCircle2 className="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
            </div>
            <p className="text-sm font-semibold text-emerald-700 dark:text-emerald-400">
              Tutti i clienti sono attivi!
            </p>
            <p className="text-xs text-muted-foreground">
              Ogni cliente ha sessioni recenti
            </p>
          </div>
        )}

        {/* Lista clienti */}
        {!isLoading && items.length > 0 && (
          <ScrollArea className="min-h-0 flex-1 -mx-1 px-1">
            <div className="space-y-3 pb-4">
              {items.map((item) => (
                <div
                  key={item.client_id}
                  className="rounded-lg border p-4 transition-all hover:shadow-sm"
                >
                  {/* Header: nome + badge inattivita' */}
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-semibold">
                      {item.nome} {item.cognome}
                    </span>
                    <span className={`rounded-md px-2 py-0.5 text-[10px] font-bold ${inattivitaBadge(item.giorni_inattivo)}`}>
                      {item.giorni_inattivo} giorni
                    </span>
                  </div>

                  {/* Ultima sessione */}
                  <div className="mb-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {item.ultimo_evento_data ? (
                      <span>
                        Ultima sessione: {formatShortDate(item.ultimo_evento_data)}
                        {item.ultimo_evento_categoria && (
                          <> ({CATEGORY_LABELS[item.ultimo_evento_categoria] ?? item.ultimo_evento_categoria})</>
                        )}
                      </span>
                    ) : (
                      <span className={inattivitaColor(item.giorni_inattivo)}>
                        Nessuna sessione registrata
                      </span>
                    )}
                  </div>

                  {/* Contatti */}
                  <div className="mb-3 flex flex-wrap gap-2">
                    {item.telefono && (
                      <a
                        href={`tel:${item.telefono}`}
                        className="inline-flex items-center gap-1.5 rounded-md border bg-white px-2.5 py-1 text-xs font-medium transition-colors hover:bg-blue-50 hover:text-blue-600 dark:bg-zinc-900 dark:hover:bg-blue-950/30 dark:hover:text-blue-400"
                      >
                        <Phone className="h-3 w-3" />
                        {item.telefono}
                      </a>
                    )}
                    {item.email && (
                      <a
                        href={`mailto:${item.email}`}
                        className="inline-flex items-center gap-1.5 rounded-md border bg-white px-2.5 py-1 text-xs font-medium transition-colors hover:bg-blue-50 hover:text-blue-600 dark:bg-zinc-900 dark:hover:bg-blue-950/30 dark:hover:text-blue-400"
                      >
                        <Mail className="h-3 w-3" />
                        {item.email}
                      </a>
                    )}
                    {!item.telefono && !item.email && (
                      <span className="text-[11px] text-muted-foreground/60 italic">
                        Nessun contatto registrato
                      </span>
                    )}
                  </div>

                  {/* CTA */}
                  <Link href="/agenda">
                    <Button
                      size="sm"
                      className="h-8 w-full gap-1.5 bg-blue-600 text-xs font-medium text-white hover:bg-blue-700"
                    >
                      <Calendar className="h-3.5 w-3.5" />
                      Pianifica sessione
                      <ArrowRight className="h-3 w-3" />
                    </Button>
                  </Link>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </SheetContent>
    </Sheet>
  );
}
