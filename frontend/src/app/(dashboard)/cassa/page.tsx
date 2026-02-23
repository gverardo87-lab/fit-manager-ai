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
  BookOpen,
  CalendarClock,
  ArrowLeftRight,
  Clock,
  LineChart,
} from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
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
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart";
import { MovementsTable } from "@/components/movements/MovementsTable";
import { MovementSheet } from "@/components/movements/MovementSheet";
import { DeleteMovementDialog } from "@/components/movements/DeleteMovementDialog";
import { RecurringExpensesTab } from "@/components/movements/RecurringExpensesTab";
import { SplitLedgerView } from "@/components/movements/SplitLedgerView";
import { AgingReport } from "@/components/movements/AgingReport";
import { ForecastTab } from "@/components/movements/ForecastTab";
import { useMovements, useMovementStats, usePendingExpenses } from "@/hooks/useMovements";
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
  const { data: pendingData } = usePendingExpenses(anno, mese);
  const pendingCount = pendingData?.items.length ?? 0;

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
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-100 to-emerald-200 dark:from-emerald-900/40 dark:to-emerald-800/30">
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

          <Button onClick={() => setSheetOpen(true)} className="bg-emerald-600 hover:bg-emerald-700 text-white">
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
        <TabsList className="bg-muted/50 p-1">
          <TabsTrigger value="ledger" className="flex-1 gap-1.5">
            <BookOpen className="h-3.5 w-3.5" />
            Libro Mastro
          </TabsTrigger>
          <TabsTrigger value="recurring" className="flex-1 gap-1.5">
            <CalendarClock className="h-3.5 w-3.5" />
            Spese Fisse
            {pendingCount > 0 && (
              <Badge variant="destructive" className="ml-1 h-5 min-w-5 px-1.5 text-[10px]">
                {pendingCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="split" className="flex-1 gap-1.5">
            <ArrowLeftRight className="h-3.5 w-3.5" />
            Entrate & Uscite
          </TabsTrigger>
          <TabsTrigger value="aging" className="flex-1 gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            Scadenze
          </TabsTrigger>
          <TabsTrigger value="forecast" className="flex-1 gap-1.5">
            <LineChart className="h-3.5 w-3.5" />
            Previsioni
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
          <RecurringExpensesTab anno={anno} mese={mese} />
        </TabsContent>

        <TabsContent value="split" className="mt-4">
          <SplitLedgerView />
        </TabsContent>

        <TabsContent value="aging" className="mt-4">
          <AgingReport />
        </TabsContent>

        <TabsContent value="forecast" className="mt-4">
          <ForecastTab />
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

// ── KPI Config ──

type KpiKey = "totale_entrate" | "totale_uscite_variabili" | "totale_uscite_fisse" | "margine_netto";

interface KpiDef {
  key: KpiKey;
  label: string;
  icon: typeof TrendingUp;
  borderColor: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  valueColor: string;
}

const CASSA_KPI: KpiDef[] = [
  {
    key: "totale_entrate",
    label: "Entrate",
    icon: TrendingUp,
    borderColor: "border-l-emerald-500",
    gradient: "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    valueColor: "text-emerald-700 dark:text-emerald-400",
  },
  {
    key: "totale_uscite_variabili",
    label: "Uscite Variabili",
    icon: TrendingDown,
    borderColor: "border-l-red-500",
    gradient: "from-red-50/80 to-white dark:from-red-950/40 dark:to-zinc-900",
    iconBg: "bg-red-100 dark:bg-red-900/30",
    iconColor: "text-red-600 dark:text-red-400",
    valueColor: "text-red-700 dark:text-red-400",
  },
  {
    key: "totale_uscite_fisse",
    label: "Uscite Fisse",
    icon: Building2,
    borderColor: "border-l-orange-500",
    gradient: "from-orange-50/80 to-white dark:from-orange-950/40 dark:to-zinc-900",
    iconBg: "bg-orange-100 dark:bg-orange-900/30",
    iconColor: "text-orange-600 dark:text-orange-400",
    valueColor: "text-orange-700 dark:text-orange-400",
  },
  {
    key: "margine_netto",
    label: "Margine Netto",
    icon: Target,
    borderColor: "", // condizionale
    gradient: "",    // condizionale
    iconBg: "",      // condizionale
    iconColor: "",   // condizionale
    valueColor: "",  // condizionale
  },
];

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
      {CASSA_KPI.map((kpi) => {
        const Icon = kpi.icon;
        const isMargin = kpi.key === "margine_netto";

        const borderColor = isMargin
          ? (isPositive ? "border-l-blue-500" : "border-l-red-500")
          : kpi.borderColor;
        const gradient = isMargin
          ? (isPositive
              ? "from-blue-50/80 to-white dark:from-blue-950/40 dark:to-zinc-900"
              : "from-red-50/80 to-white dark:from-red-950/40 dark:to-zinc-900")
          : kpi.gradient;
        const iconBg = isMargin
          ? (isPositive ? "bg-blue-100 dark:bg-blue-900/30" : "bg-red-100 dark:bg-red-900/30")
          : kpi.iconBg;
        const iconColor = isMargin
          ? (isPositive ? "text-blue-600 dark:text-blue-400" : "text-red-600 dark:text-red-400")
          : kpi.iconColor;
        const valueColor = isMargin
          ? (isPositive ? "text-blue-700 dark:text-blue-400" : "text-red-700 dark:text-red-400")
          : kpi.valueColor;

        return (
          <div
            key={kpi.key}
            className={`flex items-start gap-3 rounded-xl border border-l-4 ${borderColor} bg-gradient-to-br ${gradient} p-4 shadow-sm transition-shadow hover:shadow-md`}
          >
            <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
              <Icon className={`h-5 w-5 ${iconColor}`} />
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
                {kpi.label}
              </p>
              <p className={`text-2xl font-bold tracking-tight ${valueColor}`}>
                {formatCurrency(stats[kpi.key])}
              </p>
              <p className="text-[10px] text-muted-foreground/70">questo mese</p>
            </div>
          </div>
        );
      })}
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
  const hasData = data.some((d) => d.entrate > 0 || d.uscite > 0);
  if (!hasData) return null;

  const giorniAttivi = data.filter((d) => d.entrate > 0 || d.uscite > 0).length;

  return (
    <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-5 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">
            Andamento Giornaliero — {meseLabel}
          </h3>
          <p className="text-xs text-muted-foreground">
            Entrate e uscite per giorno del mese
          </p>
        </div>
        <Badge variant="outline" className="text-[10px]">
          {giorniAttivi} giorni attivi
        </Badge>
      </div>

      <ChartContainer config={chartConfig} className="h-[280px] w-full">
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
            cursor={{ fill: "var(--color-muted)", opacity: 0.3 }}
            content={({ payload, label }) => {
              if (!payload?.length) return null;
              return (
                <div className="rounded-lg border bg-white p-3 shadow-md dark:bg-zinc-900">
                  <p className="mb-1.5 text-xs font-semibold text-muted-foreground">
                    Giorno {label}
                  </p>
                  {payload.map((entry) => (
                    <div key={entry.name} className="flex items-center gap-2 text-sm">
                      <div
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: entry.color }}
                      />
                      <span className="text-muted-foreground">
                        {entry.name === "entrate" ? "Entrate" : "Uscite"}
                      </span>
                      <span className="ml-auto font-bold tabular-nums">
                        {formatCurrency(Number(entry.value))}
                      </span>
                    </div>
                  ))}
                </div>
              );
            }}
          />
          <ChartLegend content={<ChartLegendContent />} />
          <Bar
            dataKey="entrate"
            fill="var(--color-emerald-500)"
            radius={[4, 4, 2, 2]}
            maxBarSize={20}
            animationBegin={0}
            animationDuration={800}
          />
          <Bar
            dataKey="uscite"
            fill="var(--color-red-500)"
            radius={[4, 4, 2, 2]}
            maxBarSize={20}
            animationBegin={100}
            animationDuration={800}
          />
        </BarChart>
      </ChartContainer>
    </div>
  );
}

// ── Skeletons ──

function KpiSkeleton() {
  const borders = ["border-l-emerald-500", "border-l-red-500", "border-l-orange-500", "border-l-blue-500"];
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {borders.map((border, i) => (
        <div key={i} className={`flex items-start gap-3 rounded-xl border border-l-4 ${border} p-4`}>
          <Skeleton className="h-10 w-10 shrink-0 rounded-lg" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-6 w-28" />
            <Skeleton className="h-2 w-16" />
          </div>
        </div>
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
