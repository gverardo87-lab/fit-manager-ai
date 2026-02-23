// src/components/movements/MovementsTable.tsx
"use client";

/**
 * Tabella movimenti di cassa — design "Home Banking".
 *
 * Colonne: Data, Descrizione, Tipo, Categoria, Metodo, Importo, Azioni.
 *
 * Regole UX:
 * - Importi ENTRATA in verde, USCITA in rosso
 * - Badge tri-stato: "Sistema" | "Spesa Fissa" | "Manuale"
 * - Elimina disabilitato su movimenti protetti (Ledger Integrity)
 */

import { useState, useMemo } from "react";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  MoreHorizontal,
  Trash2,
  Search,
  ArrowUpCircle,
  ArrowDownCircle,
  Lock,
  CalendarClock,
  Landmark,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { CashMovement } from "@/types/api";
import { formatCurrency } from "@/lib/format";

interface MovementsTableProps {
  movements: CashMovement[];
  onDelete: (movement: CashMovement) => void;
}

export function MovementsTable({
  movements,
  onDelete,
}: MovementsTableProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return movements;

    const q = search.toLowerCase();
    return movements.filter((m) =>
      (m.note ?? "").toLowerCase().includes(q) ||
      (m.categoria ?? "").toLowerCase().includes(q) ||
      (m.metodo ?? "").toLowerCase().includes(q)
    );
  }, [movements, search]);

  // Raggruppa per data (display-only, zero logic change)
  const grouped = useMemo(() => {
    const map = new Map<string, CashMovement[]>();
    for (const m of filtered) {
      const key = m.data_effettiva;
      const arr = map.get(key);
      if (arr) arr.push(m);
      else map.set(key, [m]);
    }
    return map;
  }, [filtered]);

  return (
    <div className="space-y-4">
      {/* ── Barra ricerca ── */}
      <div className="flex items-center gap-3">
        <div className="relative max-w-md flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Cerca per nota, categoria o metodo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        {search && (
          <Badge variant="secondary" className="text-xs">
            {filtered.length} risultat{filtered.length === 1 ? "o" : "i"}
          </Badge>
        )}
      </div>

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed py-16">
          <Landmark className="mb-3 h-10 w-10 text-muted-foreground/40" />
          <p className="text-sm font-medium text-muted-foreground">
            {search
              ? "Nessun risultato per la ricerca"
              : "Nessun movimento in questo periodo"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground/70">
            {search
              ? "Prova con un termine diverso"
              : "I movimenti appariranno qui"}
          </p>
        </div>
      ) : (
        <div className="rounded-lg border bg-white dark:bg-zinc-900">
          <Table>
            <TableHeader className="sticky top-0 z-10 bg-white dark:bg-zinc-900">
              <TableRow>
                <TableHead>Data</TableHead>
                <TableHead>Descrizione</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Categoria</TableHead>
                <TableHead>Metodo</TableHead>
                <TableHead className="text-right">Importo</TableHead>
                <TableHead className="w-[80px]">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[...grouped.entries()].map(([dateKey, items]) => (
                <DateGroup key={dateKey} dateKey={dateKey} items={items} onDelete={onDelete} />
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

// ── Gruppo per data ──

function DateGroup({
  dateKey,
  items,
  onDelete,
}: {
  dateKey: string;
  items: CashMovement[];
  onDelete: (m: CashMovement) => void;
}) {
  return (
    <>
      <TableRow className="bg-muted/30 hover:bg-muted/30">
        <TableCell colSpan={7} className="py-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {format(parseISO(dateKey), "EEEE d MMMM", { locale: it })}
          </span>
        </TableCell>
      </TableRow>
      {items.map((movement, idx) => (
        <MovementRow key={movement.id} movement={movement} onDelete={onDelete} striped={idx % 2 !== 0} />
      ))}
    </>
  );
}

// ── Riga singola ──

function MovementRow({
  movement,
  onDelete,
  striped,
}: {
  movement: CashMovement;
  onDelete: (m: CashMovement) => void;
  striped: boolean;
}) {
  const isEntrata = movement.tipo === "ENTRATA";
  const isContract = movement.id_contratto !== null;
  const isRecurring = movement.id_spesa_ricorrente !== null;
  const isProtected = isContract || isRecurring;

  const tooltipText = isContract
    ? "Movimento di sistema — non eliminabile"
    : "Spesa fissa generata automaticamente — non eliminabile";

  return (
    <TableRow className={`transition-colors hover:bg-muted/50 ${striped ? "bg-muted/20" : ""}`}>
      {/* ── Data ── */}
      <TableCell className="whitespace-nowrap text-sm">
        {format(parseISO(movement.data_effettiva), "dd MMM yyyy", {
          locale: it,
        })}
      </TableCell>

      {/* ── Descrizione + badge origine ── */}
      <TableCell>
        <div className="flex items-center gap-2">
          <span className="text-sm truncate max-w-[200px]">
            {movement.note || "—"}
          </span>
          <OriginBadge isContract={isContract} isRecurring={isRecurring} />
        </div>
      </TableCell>

      {/* ── Tipo ── */}
      <TableCell>
        <div className="flex items-center gap-1.5">
          {isEntrata ? (
            <ArrowUpCircle className="h-4 w-4 text-emerald-500" />
          ) : (
            <ArrowDownCircle className="h-4 w-4 text-red-500" />
          )}
          <span className={`text-xs font-semibold ${
            isEntrata ? "text-emerald-700 dark:text-emerald-400" : "text-red-700 dark:text-red-400"
          }`}>
            {movement.tipo}
          </span>
        </div>
      </TableCell>

      {/* ── Categoria ── */}
      <TableCell className="text-sm text-muted-foreground">
        {movement.categoria ?? "—"}
      </TableCell>

      {/* ── Metodo ── */}
      <TableCell className="text-sm text-muted-foreground">
        {movement.metodo ?? "—"}
      </TableCell>

      {/* ── Importo ── */}
      <TableCell className="text-right">
        <span className={`text-base font-bold tabular-nums ${
          isEntrata
            ? "text-emerald-600 dark:text-emerald-400"
            : "text-red-600 dark:text-red-400"
        }`}>
          {isEntrata ? "+" : "−"}{formatCurrency(movement.importo)}
        </span>
      </TableCell>

      {/* ── Azioni ── */}
      <TableCell>
        {isProtected ? (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8" disabled>
                  {isRecurring ? (
                    <CalendarClock className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Lock className="h-4 w-4 text-muted-foreground" />
                  )}
                  <span className="sr-only">Protetto</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{tooltipText}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ) : (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">Azioni</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => onDelete(movement)}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Elimina
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </TableCell>
    </TableRow>
  );
}

// ── Badge origine (Sistema / Spesa Fissa / Manuale) ──

function OriginBadge({ isContract, isRecurring }: { isContract: boolean; isRecurring: boolean }) {
  if (isContract) {
    return (
      <Badge
        variant="outline"
        className="shrink-0 border-violet-200 bg-violet-50 text-violet-700 text-[10px] px-1.5 py-0 dark:border-violet-800 dark:bg-violet-900/30 dark:text-violet-400"
      >
        Sistema
      </Badge>
    );
  }
  if (isRecurring) {
    return (
      <Badge
        variant="outline"
        className="shrink-0 border-amber-200 bg-amber-50 text-amber-700 text-[10px] px-1.5 py-0 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-400"
      >
        Spesa Fissa
      </Badge>
    );
  }
  return (
    <Badge
      variant="outline"
      className="shrink-0 border-zinc-200 bg-zinc-50 text-zinc-600 text-[10px] px-1.5 py-0 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400"
    >
      Manuale
    </Badge>
  );
}
