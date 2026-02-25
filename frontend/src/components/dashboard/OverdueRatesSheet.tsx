// src/components/dashboard/OverdueRatesSheet.tsx
/**
 * Sheet per pagamento inline rate scadute.
 *
 * Mostra rate PENDENTI/PARZIALI con data_scadenza < oggi:
 * - Info cliente + contratto + giorni di ritardo
 * - Importo residuo pre-compilato
 * - Metodo pagamento selezionabile
 * - Pagamento 1-click con usePayRate()
 *
 * Invalida automaticamente dashboard, contracts, movements.
 */

"use client";

import { useState } from "react";
import {
  ShieldAlert,
  CheckCircle2,
  Loader2,
  User,
  Calendar,
  CreditCard,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { useOverdueRates } from "@/hooks/useDashboard";
import { usePayRate } from "@/hooks/useRates";
import { formatCurrency, formatShortDate } from "@/lib/format";
import type { OverdueRateItem } from "@/types/api";
import { PAYMENT_METHODS } from "@/types/api";

// ── Helpers ──

function ritardoLabel(giorni: number): string {
  if (giorni === 1) return "1 giorno di ritardo";
  return `${giorni} giorni di ritardo`;
}

// ════════════════════════════════════════════════════════════

interface OverdueRatesSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function OverdueRatesSheet({ open, onOpenChange }: OverdueRatesSheetProps) {
  const { data, isLoading } = useOverdueRates(open);
  const payRate = usePayRate();
  const [paying, setPaying] = useState<Set<number>>(new Set());
  const [methods, setMethods] = useState<Record<number, string>>({});

  const items = data?.items ?? [];

  const getMethod = (rateId: number) => methods[rateId] ?? "CONTANTI";
  const setMethod = (rateId: number, method: string) =>
    setMethods((prev) => ({ ...prev, [rateId]: method }));

  // ── Paga singola rata ──
  const handlePay = (item: OverdueRateItem) => {
    setPaying((prev) => new Set(prev).add(item.rate_id));
    payRate.mutate(
      {
        rateId: item.rate_id,
        importo: item.importo_residuo,
        metodo: getMethod(item.rate_id),
      },
      {
        onSettled: () => {
          setPaying((prev) => {
            const next = new Set(prev);
            next.delete(item.rate_id);
            return next;
          });
        },
      }
    );
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-hidden sm:max-w-lg">
        <SheetHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-100 dark:bg-red-900/30">
              <ShieldAlert className="h-5 w-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <SheetTitle>Rate scadute</SheetTitle>
              <SheetDescription>
                Pagamenti in ritardo da riscuotere
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <Separator />

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3 p-1">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-32 w-full rounded-lg" />
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
              Nessuna rata scaduta!
            </p>
            <p className="text-xs text-muted-foreground">
              Tutti i pagamenti sono in regola
            </p>
          </div>
        )}

        {/* Lista rate */}
        {!isLoading && items.length > 0 && (
          <ScrollArea className="min-h-0 flex-1 -mx-1 px-1">
            <div className="space-y-3 pb-4">
              {items.map((item) => {
                const isPaying = paying.has(item.rate_id);

                return (
                  <div
                    key={item.rate_id}
                    className={`rounded-lg border p-4 transition-all ${
                      isPaying
                        ? "opacity-40 scale-[0.98]"
                        : "hover:shadow-sm"
                    }`}
                  >
                    {/* Header: cliente + ritardo */}
                    <div className="mb-2 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <User className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-sm font-semibold">
                          {item.client_nome} {item.client_cognome}
                        </span>
                      </div>
                      <Badge
                        variant="destructive"
                        className="text-[9px] px-1.5 py-0 h-4"
                      >
                        {ritardoLabel(item.giorni_ritardo)}
                      </Badge>
                    </div>

                    {/* Contratto + scadenza */}
                    <div className="mb-2 flex items-center gap-3 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <CreditCard className="h-3 w-3" />
                        <span>{item.tipo_pacchetto || "Contratto"}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>Scad. {formatShortDate(item.data_scadenza)}</span>
                      </div>
                    </div>

                    {/* Importi */}
                    <div className="mb-3 flex items-baseline gap-3">
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase">
                          Da riscuotere
                        </p>
                        <p className="text-lg font-bold text-red-600 dark:text-red-400 tabular-nums">
                          {formatCurrency(item.importo_residuo)}
                        </p>
                      </div>
                      {item.importo_saldato > 0 && (
                        <div>
                          <p className="text-[10px] text-muted-foreground uppercase">
                            Gia' versato
                          </p>
                          <p className="text-sm font-medium text-muted-foreground tabular-nums">
                            {formatCurrency(item.importo_saldato)} / {formatCurrency(item.importo_previsto)}
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Metodo + Paga */}
                    <div className="flex gap-2">
                      <Select
                        value={getMethod(item.rate_id)}
                        onValueChange={(v) => setMethod(item.rate_id, v)}
                        disabled={isPaying}
                      >
                        <SelectTrigger className="h-8 w-[130px] text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {PAYMENT_METHODS.map((m) => (
                            <SelectItem key={m} value={m} className="text-xs">
                              {m}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Button
                        size="sm"
                        className="h-8 flex-1 gap-1.5 bg-emerald-600 text-xs font-medium text-white hover:bg-emerald-700"
                        disabled={isPaying}
                        onClick={() => handlePay(item)}
                      >
                        {isPaying ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <CheckCircle2 className="h-3.5 w-3.5" />
                        )}
                        Incassa {formatCurrency(item.importo_residuo)}
                      </Button>
                    </div>
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
