// src/app/(dashboard)/cassa/page.tsx
"use client";

/**
 * Pagina Cassa — Ledger con filtri server-side e KPI riassuntivi.
 *
 * Filtri: Mese (Select), Anno (Select), ricerca testuale client-side.
 * KPI: Entrate totali, Uscite totali, Saldo periodo.
 * Tabella: MovementsTable con badge Sistema/Manuale e protezione elimina.
 */

import { useState, useMemo } from "react";
import { Plus, Landmark, TrendingUp, TrendingDown, Scale } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MovementsTable } from "@/components/movements/MovementsTable";
import { MovementSheet } from "@/components/movements/MovementSheet";
import { DeleteMovementDialog } from "@/components/movements/DeleteMovementDialog";
import { useMovements } from "@/hooks/useMovements";
import type { CashMovement } from "@/types/api";

// ── Costanti per i Select ──

const MESI = [
  { value: "1", label: "Gennaio" },
  { value: "2", label: "Febbraio" },
  { value: "3", label: "Marzo" },
  { value: "4", label: "Aprile" },
  { value: "5", label: "Maggio" },
  { value: "6", label: "Giugno" },
  { value: "7", label: "Luglio" },
  { value: "8", label: "Agosto" },
  { value: "9", label: "Settembre" },
  { value: "10", label: "Ottobre" },
  { value: "11", label: "Novembre" },
  { value: "12", label: "Dicembre" },
] as const;

function getYearRange(): number[] {
  const current = new Date().getFullYear();
  return Array.from({ length: 5 }, (_, i) => current - 2 + i);
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

// ════════════════════════════════════════════════════════════
// Pagina
// ════════════════════════════════════════════════════════════

export default function CassaPage() {
  const now = new Date();
  const [mese, setMese] = useState(now.getMonth() + 1);
  const [anno, setAnno] = useState(now.getFullYear());
  const [sheetOpen, setSheetOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedMovement, setSelectedMovement] =
    useState<CashMovement | null>(null);

  const { data, isLoading, isError, refetch } = useMovements({
    anno,
    mese,
  });

  // ── KPI calcolati dai dati ──
  const kpi = useMemo(() => {
    if (!data?.items) return { entrate: 0, uscite: 0, saldo: 0 };

    let entrate = 0;
    let uscite = 0;
    for (const m of data.items) {
      if (m.tipo === "ENTRATA") entrate += m.importo;
      else uscite += m.importo;
    }
    return { entrate, uscite, saldo: entrate - uscite };
  }, [data]);

  // ── Handlers ──

  const handleDelete = (movement: CashMovement) => {
    setSelectedMovement(movement);
    setDeleteOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* ── Header + Filtri ── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
            <Landmark className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Cassa</h1>
            {data && (
              <p className="text-sm text-muted-foreground">
                {data.total} moviment{data.total !== 1 ? "i" : "o"} nel periodo
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* ── Filtro Mese ── */}
          <Select
            value={String(mese)}
            onValueChange={(v) => setMese(parseInt(v, 10))}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MESI.map((m) => (
                <SelectItem key={m.value} value={m.value}>
                  {m.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* ── Filtro Anno ── */}
          <Select
            value={String(anno)}
            onValueChange={(v) => setAnno(parseInt(v, 10))}
          >
            <SelectTrigger className="w-[100px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {getYearRange().map((y) => (
                <SelectItem key={y} value={String(y)}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button onClick={() => setSheetOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Nuovo Movimento
          </Button>
        </div>
      </div>

      {/* ── KPI Cards ── */}
      {data && <KpiCards entrate={kpi.entrate} uscite={kpi.uscite} saldo={kpi.saldo} />}

      {/* ── Contenuto ── */}
      {isLoading && <TableSkeleton />}

      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <p className="text-destructive">
            Errore nel caricamento dei movimenti.
          </p>
          <Button
            variant="outline"
            size="sm"
            className="mt-3"
            onClick={() => refetch()}
          >
            Riprova
          </Button>
        </div>
      )}

      {data && (
        <MovementsTable
          movements={data.items}
          onDelete={handleDelete}
        />
      )}

      {/* ── Sheet nuovo movimento ── */}
      <MovementSheet open={sheetOpen} onOpenChange={setSheetOpen} />

      {/* ── Dialog elimina ── */}
      <DeleteMovementDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        movement={selectedMovement}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// KPI Cards
// ════════════════════════════════════════════════════════════

function KpiCards({
  entrate,
  uscite,
  saldo,
}: {
  entrate: number;
  uscite: number;
  saldo: number;
}) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Entrate */}
      <div className="flex items-start gap-3 rounded-xl border bg-white p-4 shadow-sm dark:bg-zinc-900">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
          <TrendingUp className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
        </div>
        <div>
          <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            Entrate
          </p>
          <p className="text-xl font-bold tracking-tight text-emerald-700 dark:text-emerald-400">
            {formatCurrency(entrate)}
          </p>
        </div>
      </div>

      {/* Uscite */}
      <div className="flex items-start gap-3 rounded-xl border bg-white p-4 shadow-sm dark:bg-zinc-900">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-red-100 dark:bg-red-900/30">
          <TrendingDown className="h-5 w-5 text-red-600 dark:text-red-400" />
        </div>
        <div>
          <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            Uscite
          </p>
          <p className="text-xl font-bold tracking-tight text-red-700 dark:text-red-400">
            {formatCurrency(uscite)}
          </p>
        </div>
      </div>

      {/* Saldo */}
      <div className="flex items-start gap-3 rounded-xl border bg-white p-4 shadow-sm dark:bg-zinc-900">
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
          saldo >= 0
            ? "bg-blue-100 dark:bg-blue-900/30"
            : "bg-amber-100 dark:bg-amber-900/30"
        }`}>
          <Scale className={`h-5 w-5 ${
            saldo >= 0
              ? "text-blue-600 dark:text-blue-400"
              : "text-amber-600 dark:text-amber-400"
          }`} />
        </div>
        <div>
          <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            Saldo Periodo
          </p>
          <p className={`text-xl font-bold tracking-tight ${
            saldo >= 0
              ? "text-blue-700 dark:text-blue-400"
              : "text-amber-700 dark:text-amber-400"
          }`}>
            {formatCurrency(saldo)}
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Skeleton ──

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-4">
        <Skeleton className="h-20 w-full rounded-xl" />
        <Skeleton className="h-20 w-full rounded-xl" />
        <Skeleton className="h-20 w-full rounded-xl" />
      </div>
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  );
}
