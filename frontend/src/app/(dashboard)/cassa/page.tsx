// src/app/(dashboard)/cassa/page.tsx
"use client";

/**
 * Pagina Cassa — Financial Intelligence Dashboard.
 *
 * Layout:
 * 1. Header con filtri globali Mese/Anno
 * 2. Hero Section: 4 KPI cards (Entrate, Uscite Var, Uscite Fisse, Margine Netto)
 * 3. BarChart giornaliero Entrate vs Uscite (recharts via shadcn/chart)
 * 4. Tabs: "Libro Mastro" (tabella movimenti) + "Spese Fisse" (ricorrenti)
 */

import { useState } from "react";
import {
  Plus,
  Landmark,
  TrendingUp,
  TrendingDown,
  Building2,
  Target,
} from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart";
import { MovementsTable } from "@/components/movements/MovementsTable";
import { MovementSheet } from "@/components/movements/MovementSheet";
import { DeleteMovementDialog } from "@/components/movements/DeleteMovementDialog";
import { RecurringExpensesTab } from "@/components/movements/RecurringExpensesTab";
import { useMovements, useMovementStats } from "@/hooks/useMovements";
import type { CashMovement } from "@/types/api";
import { formatCurrency } from "@/lib/format";

// ── Costanti ──

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

const chartConfig: ChartConfig = {
  entrate: {
    label: "Entrate",
    color: "var(--color-emerald-500)",
  },
  uscite: {
    label: "Uscite",
    color: "var(--color-red-500)",
  },
};

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

  const { data: movementsData, isLoading: movementsLoading, isError, refetch } =
    useMovements({ anno, mese });
  const { data: stats, isLoading: statsLoading } =
    useMovementStats(anno, mese);

  const handleDelete = (movement: CashMovement) => {
    setSelectedMovement(movement);
    setDeleteOpen(true);
  };

  const meseLabel = MESI.find((m) => m.value === String(mese))?.label ?? "";

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
            <p className="text-sm text-muted-foreground">
              {meseLabel} {anno}
              {movementsData && ` — ${movementsData.total} movimenti`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
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

      {/* ── Hero Section: 4 KPI ── */}
      {statsLoading && <KpiSkeleton />}
      {stats && <KpiCards stats={stats} />}

      {/* ── Grafico Entrate vs Uscite ── */}
      {stats && stats.chart_data.length > 0 && (
        <DailyChart data={stats.chart_data} meseLabel={meseLabel} />
      )}

      {/* ── Tabs: Libro Mastro + Spese Fisse ── */}
      <Tabs defaultValue="ledger" className="w-full">
        <TabsList>
          <TabsTrigger value="ledger" className="flex-1">
            Libro Mastro
          </TabsTrigger>
          <TabsTrigger value="recurring" className="flex-1">
            Spese Fisse
          </TabsTrigger>
        </TabsList>

        <TabsContent value="ledger" className="mt-4">
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

          {movementsLoading && <TableSkeleton />}

          {movementsData && (
            <MovementsTable
              movements={movementsData.items}
              onDelete={handleDelete}
            />
          )}
        </TabsContent>

        <TabsContent value="recurring" className="mt-4">
          <RecurringExpensesTab />
        </TabsContent>
      </Tabs>

      {/* ── Modals ── */}
      <MovementSheet open={sheetOpen} onOpenChange={setSheetOpen} />
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
  stats,
}: {
  stats: {
    totale_entrate: number;
    totale_uscite_variabili: number;
    totale_uscite_fisse: number;
    margine_netto: number;
  };
}) {
  const isPositive = stats.margine_netto >= 0;

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {/* Entrate */}
      <div className="flex items-start gap-3 rounded-xl border bg-white p-4 shadow-sm dark:bg-zinc-900">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
          <TrendingUp className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
        </div>
        <div className="min-w-0">
          <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            Entrate
          </p>
          <p className="text-xl font-bold tracking-tight text-emerald-700 dark:text-emerald-400">
            {formatCurrency(stats.totale_entrate)}
          </p>
        </div>
      </div>

      {/* Uscite Variabili */}
      <div className="flex items-start gap-3 rounded-xl border bg-white p-4 shadow-sm dark:bg-zinc-900">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-red-100 dark:bg-red-900/30">
          <TrendingDown className="h-5 w-5 text-red-600 dark:text-red-400" />
        </div>
        <div className="min-w-0">
          <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            Uscite Variabili
          </p>
          <p className="text-xl font-bold tracking-tight text-red-700 dark:text-red-400">
            {formatCurrency(stats.totale_uscite_variabili)}
          </p>
        </div>
      </div>

      {/* Uscite Fisse */}
      <div className="flex items-start gap-3 rounded-xl border bg-white p-4 shadow-sm dark:bg-zinc-900">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-orange-100 dark:bg-orange-900/30">
          <Building2 className="h-5 w-5 text-orange-600 dark:text-orange-400" />
        </div>
        <div className="min-w-0">
          <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            Uscite Fisse
          </p>
          <p className="text-xl font-bold tracking-tight text-orange-700 dark:text-orange-400">
            {formatCurrency(stats.totale_uscite_fisse)}
          </p>
        </div>
      </div>

      {/* Margine Netto */}
      <div className={`flex items-start gap-3 rounded-xl border p-4 shadow-sm ${
        isPositive
          ? "bg-white dark:bg-zinc-900"
          : "border-red-200 bg-red-50/50 dark:border-red-900/50 dark:bg-red-950/20"
      }`}>
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
          isPositive
            ? "bg-blue-100 dark:bg-blue-900/30"
            : "bg-red-100 dark:bg-red-900/30"
        }`}>
          <Target className={`h-5 w-5 ${
            isPositive
              ? "text-blue-600 dark:text-blue-400"
              : "text-red-600 dark:text-red-400"
          }`} />
        </div>
        <div className="min-w-0">
          <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            Margine Netto
          </p>
          <p className={`text-xl font-bold tracking-tight ${
            isPositive
              ? "text-blue-700 dark:text-blue-400"
              : "text-red-700 dark:text-red-400"
          }`}>
            {formatCurrency(stats.margine_netto)}
          </p>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Grafico giornaliero
// ════════════════════════════════════════════════════════════

function DailyChart({
  data,
  meseLabel,
}: {
  data: { giorno: number; entrate: number; uscite: number }[];
  meseLabel: string;
}) {
  // Filtra solo i giorni con dati per il grafico
  const hasData = data.some((d) => d.entrate > 0 || d.uscite > 0);
  if (!hasData) return null;

  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm dark:bg-zinc-900">
      <div className="mb-4">
        <h3 className="text-sm font-semibold">
          Andamento Giornaliero — {meseLabel}
        </h3>
        <p className="text-xs text-muted-foreground">
          Entrate e uscite per giorno del mese
        </p>
      </div>

      <ChartContainer config={chartConfig} className="h-[240px] w-full">
        <BarChart data={data} accessibilityLayer>
          <CartesianGrid vertical={false} strokeDasharray="3 3" />
          <XAxis
            dataKey="giorno"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            fontSize={11}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            fontSize={11}
            tickFormatter={(v) => `€${v}`}
          />
          <ChartTooltip
            content={
              <ChartTooltipContent
                formatter={(value, name) => (
                  <span>
                    {name === "entrate" ? "Entrate" : "Uscite"}: {formatCurrency(Number(value))}
                  </span>
                )}
              />
            }
          />
          <ChartLegend content={<ChartLegendContent />} />
          <Bar
            dataKey="entrate"
            fill="var(--color-emerald-500)"
            radius={[4, 4, 0, 0]}
            maxBarSize={20}
          />
          <Bar
            dataKey="uscite"
            fill="var(--color-red-500)"
            radius={[4, 4, 0, 0]}
            maxBarSize={20}
          />
        </BarChart>
      </ChartContainer>
    </div>
  );
}

// ── Skeletons ──

function KpiSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-20 w-full rounded-xl" />
      ))}
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  );
}
