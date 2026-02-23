// src/components/dashboard/ExpiringContractsSheet.tsx
/**
 * Sheet per contratti in scadenza con crediti inutilizzati.
 *
 * Mostra contratti con data_scadenza <= 30 giorni e crediti residui > 0:
 * - Barra progresso crediti (usati / totali)
 * - Countdown scadenza con colore severity
 * - CTA "Vai al contratto" per gestione completa
 * - Info cliente e valore economico
 */

"use client";

import Link from "next/link";
import {
  CreditCard,
  CheckCircle2,
  User,
  Calendar,
  ArrowRight,
  Dumbbell,
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
import { useExpiringContracts } from "@/hooks/useDashboard";
import { formatCurrency } from "@/lib/format";

// ── Helpers ──

function countdownLabel(giorni: number): string {
  if (giorni === 0) return "Scade oggi";
  if (giorni === 1) return "Scade domani";
  return `${giorni} giorni rimasti`;
}

function countdownColor(giorni: number): string {
  if (giorni <= 3) return "text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800";
  if (giorni <= 7) return "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800";
  return "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800";
}

function formatDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("it-IT", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

// ════════════════════════════════════════════════════════════

interface ExpiringContractsSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ExpiringContractsSheet({ open, onOpenChange }: ExpiringContractsSheetProps) {
  const { data, isLoading } = useExpiringContracts(open);

  const items = data?.items ?? [];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-hidden sm:max-w-lg">
        <SheetHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <CreditCard className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <SheetTitle>Contratti in scadenza</SheetTitle>
              <SheetDescription>
                Crediti inutilizzati che stanno per scadere
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <Separator />

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3 p-1">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-36 w-full rounded-lg" />
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
              Nessun contratto a rischio!
            </p>
            <p className="text-xs text-muted-foreground">
              Tutti i crediti sono utilizzati o le scadenze lontane
            </p>
          </div>
        )}

        {/* Lista contratti */}
        {!isLoading && items.length > 0 && (
          <ScrollArea className="min-h-0 flex-1 -mx-1 px-1">
            <div className="space-y-3 pb-4">
              {items.map((item) => {
                const pct = item.crediti_totali > 0
                  ? Math.round((item.crediti_usati / item.crediti_totali) * 100)
                  : 0;

                return (
                  <div
                    key={item.contract_id}
                    className="rounded-lg border p-4 transition-all hover:shadow-sm"
                  >
                    {/* Header: cliente + countdown */}
                    <div className="mb-2 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <User className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-sm font-semibold">
                          {item.client_nome} {item.client_cognome}
                        </span>
                      </div>
                      <div className={`rounded-md border px-2 py-0.5 text-[10px] font-bold ${countdownColor(item.giorni_rimasti)}`}>
                        {countdownLabel(item.giorni_rimasti)}
                      </div>
                    </div>

                    {/* Pacchetto + scadenza */}
                    <div className="mb-3 flex items-center gap-3 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <CreditCard className="h-3 w-3" />
                        <span>{item.tipo_pacchetto || "Pacchetto"}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>Scade il {formatDate(item.data_scadenza)}</span>
                      </div>
                    </div>

                    {/* Progress bar crediti */}
                    <div className="mb-2">
                      <div className="mb-1 flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">
                          Crediti utilizzati
                        </span>
                        <span className="font-semibold tabular-nums">
                          {item.crediti_usati} / {item.crediti_totali}
                        </span>
                      </div>
                      <div className="h-2.5 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-blue-400 to-blue-600 transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>

                    {/* Crediti residui (evidenziato) */}
                    <div className="mb-3 flex items-center gap-2">
                      <Dumbbell className="h-3.5 w-3.5 text-amber-500" />
                      <span className="text-sm font-bold text-amber-600 dark:text-amber-400">
                        {item.crediti_residui} {item.crediti_residui === 1 ? "seduta" : "sedute"} da usare
                      </span>
                      {item.prezzo_totale && item.crediti_totali > 0 && (
                        <span className="text-[10px] text-muted-foreground">
                          (valore ~{formatCurrency(
                            (item.prezzo_totale / item.crediti_totali) * item.crediti_residui
                          )})
                        </span>
                      )}
                    </div>

                    {/* CTA */}
                    <Link href={`/contratti`}>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 w-full gap-1.5 text-xs font-medium"
                      >
                        Vai al contratto
                        <ArrowRight className="h-3 w-3" />
                      </Button>
                    </Link>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        )}
      </SheetContent>
    </Sheet>
  );
}
