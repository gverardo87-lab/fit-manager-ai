// src/components/movements/LedgerColumn.tsx
"use client";

/**
 * Colonna riusabile per la vista Split Entrate/Uscite.
 *
 * 3 sezioni:
 * 1. Header: totale (big number) + conteggio movimenti
 * 2. Breakdown per categoria (barre proporzionali + importo + %)
 * 3. Lista movimenti compatta (data | nota | importo)
 *
 * Props:
 * - movements: CashMovement[] gia' filtrati per tipo
 * - label: "Entrate" | "Uscite"
 * - variant: "income" | "expense" (colori)
 */

import { useMemo } from "react";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import { TrendingUp, TrendingDown, Inbox } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { CashMovement } from "@/types/api";
import { formatCurrency } from "@/lib/format";

interface LedgerColumnProps {
  movements: CashMovement[];
  label: string;
  variant: "income" | "expense";
}

interface CategoryBreakdown {
  categoria: string;
  totale: number;
  count: number;
  percentuale: number;
}

export function LedgerColumn({ movements, label, variant }: LedgerColumnProps) {
  const isIncome = variant === "income";

  // ── Calcoli ──
  const totale = useMemo(
    () => movements.reduce((sum, m) => sum + m.importo, 0),
    [movements],
  );

  const breakdown = useMemo((): CategoryBreakdown[] => {
    if (totale === 0) return [];

    const map = new Map<string, { totale: number; count: number }>();
    for (const m of movements) {
      const cat = m.categoria ?? "Altro";
      const curr = map.get(cat) ?? { totale: 0, count: 0 };
      curr.totale += m.importo;
      curr.count += 1;
      map.set(cat, curr);
    }

    return Array.from(map.entries())
      .map(([categoria, data]) => ({
        categoria,
        totale: data.totale,
        count: data.count,
        percentuale: Math.round((data.totale / totale) * 100),
      }))
      .sort((a, b) => b.totale - a.totale);
  }, [movements, totale]);

  // Movimenti ordinati per data desc (ultimi prima)
  const sorted = useMemo(
    () => [...movements].sort((a, b) => b.data_effettiva.localeCompare(a.data_effettiva)),
    [movements],
  );

  // ── Colori ──
  const colors = isIncome
    ? {
        bg: "bg-emerald-50 dark:bg-emerald-950/30",
        border: "border-emerald-200 dark:border-emerald-800",
        text: "text-emerald-700 dark:text-emerald-400",
        bar: "bg-emerald-500",
        barBg: "bg-emerald-100 dark:bg-emerald-900/40",
        icon: "bg-emerald-100 dark:bg-emerald-900/30",
      }
    : {
        bg: "bg-red-50 dark:bg-red-950/30",
        border: "border-red-200 dark:border-red-800",
        text: "text-red-700 dark:text-red-400",
        bar: "bg-red-500",
        barBg: "bg-red-100 dark:bg-red-900/40",
        icon: "bg-red-100 dark:bg-red-900/30",
      };

  return (
    <div className={`rounded-xl border ${colors.border} ${colors.bg} p-5 space-y-5`}>
      {/* ── Sezione 1: Header ── */}
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${colors.icon}`}>
          {isIncome ? (
            <TrendingUp className={`h-5 w-5 ${colors.text}`} />
          ) : (
            <TrendingDown className={`h-5 w-5 ${colors.text}`} />
          )}
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          <p className={`text-2xl font-bold tracking-tight ${colors.text}`}>
            {formatCurrency(totale)}
          </p>
          <p className="text-xs text-muted-foreground">
            {movements.length} moviment{movements.length === 1 ? "o" : "i"}
          </p>
        </div>
      </div>

      {/* ── Sezione 2: Breakdown categorie ── */}
      {breakdown.length > 0 && (
        <>
          <Separator className="opacity-50" />
          <div className="space-y-1.5">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Per categoria
            </p>
            {breakdown.map((cat) => (
              <div key={cat.categoria} className="rounded-md px-2 py-1.5 -mx-2 transition-colors hover:bg-white/60 dark:hover:bg-white/5">
                <div className="flex items-center justify-between text-sm">
                  <span className="truncate font-medium">{cat.categoria}</span>
                  <span className={`tabular-nums font-semibold ${colors.text}`}>
                    {formatCurrency(cat.totale)}
                  </span>
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <div className={`h-2.5 flex-1 rounded-full ${colors.barBg}`}>
                    <div
                      className={`h-2.5 rounded-full ${colors.bar} transition-all duration-500`}
                      style={{ width: `${cat.percentuale}%` }}
                    />
                  </div>
                  <span className="text-[11px] tabular-nums text-muted-foreground w-8 text-right">
                    {cat.percentuale}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ── Sezione 3: Lista movimenti compatta ── */}
      {sorted.length > 0 && (
        <>
          <Separator className="opacity-50" />
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Movimenti
            </p>
            <ScrollArea className="h-[320px] pr-1">
              <div className="space-y-1">
                {sorted.map((m) => (
                  <div
                    key={m.id}
                    className="flex items-center justify-between rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-white/60 dark:hover:bg-white/5"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <div className={`h-1.5 w-1.5 shrink-0 rounded-full ${colors.bar}`} />
                      <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                        {format(parseISO(m.data_effettiva), "dd/MM", { locale: it })}
                      </span>
                      <span className="truncate">
                        {m.note || m.categoria || "—"}
                      </span>
                      {m.id_contratto !== null && (
                        <Badge
                          variant="outline"
                          className="shrink-0 border-violet-200 bg-violet-50 text-violet-700 text-[10px] px-1.5 py-0 dark:border-violet-800 dark:bg-violet-900/30 dark:text-violet-400"
                        >
                          Sistema
                        </Badge>
                      )}
                    </div>
                    <span className={`shrink-0 tabular-nums font-semibold ${colors.text}`}>
                      {formatCurrency(m.importo)}
                    </span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        </>
      )}

      {/* ── Empty state ── */}
      {movements.length === 0 && (
        <div className="flex flex-col items-center justify-center py-8">
          <Inbox className="mb-2 h-8 w-8 text-muted-foreground/40" />
          <p className="text-sm font-medium text-muted-foreground">
            Nessun{isIncome ? "a entrata" : "a uscita"} nel periodo selezionato
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground/70">
            Prova a modificare i filtri
          </p>
        </div>
      )}
    </div>
  );
}
