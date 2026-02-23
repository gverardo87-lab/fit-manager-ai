// src/components/movements/AgingReport.tsx
"use client";

/**
 * Aging Report — Orizzonte Finanziario bidirezionale.
 *
 * Struttura:
 * 1. KPI card: Totale Scaduto | Totale In Arrivo | Clienti con debito
 * 2. Sezione Scadute: 4 bucket (0-30, 31-60, 61-90, 90+)
 * 3. Sezione In Arrivo: 4 bucket (0-7, 8-30, 31-60, 61-90)
 *
 * Dati: singola chiamata GET /api/rates/aging via useAgingReport().
 */

import { AlertTriangle, Clock, Users, TrendingUp } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAgingReport } from "@/hooks/useRates";
import { formatCurrency } from "@/lib/format";
import type { AgingBucket, AgingItem } from "@/types/api";

// ── Colori per bucket ──

const OVERDUE_COLORS = [
  { bg: "bg-amber-50 dark:bg-amber-950/30", border: "border-amber-200 dark:border-amber-800", text: "text-amber-700 dark:text-amber-400", bar: "bg-amber-500", barBg: "bg-amber-100 dark:bg-amber-900/40" },
  { bg: "bg-orange-50 dark:bg-orange-950/30", border: "border-orange-200 dark:border-orange-800", text: "text-orange-700 dark:text-orange-400", bar: "bg-orange-500", barBg: "bg-orange-100 dark:bg-orange-900/40" },
  { bg: "bg-red-50 dark:bg-red-950/30", border: "border-red-200 dark:border-red-800", text: "text-red-700 dark:text-red-400", bar: "bg-red-500", barBg: "bg-red-100 dark:bg-red-900/40" },
  { bg: "bg-rose-50 dark:bg-rose-950/30", border: "border-rose-300 dark:border-rose-800", text: "text-rose-800 dark:text-rose-400", bar: "bg-rose-600", barBg: "bg-rose-100 dark:bg-rose-900/40" },
];

const UPCOMING_COLORS = [
  { bg: "bg-emerald-50 dark:bg-emerald-950/30", border: "border-emerald-200 dark:border-emerald-800", text: "text-emerald-700 dark:text-emerald-400", bar: "bg-emerald-500", barBg: "bg-emerald-100 dark:bg-emerald-900/40" },
  { bg: "bg-green-50 dark:bg-green-950/30", border: "border-green-200 dark:border-green-800", text: "text-green-700 dark:text-green-400", bar: "bg-green-500", barBg: "bg-green-100 dark:bg-green-900/40" },
  { bg: "bg-sky-50 dark:bg-sky-950/30", border: "border-sky-200 dark:border-sky-800", text: "text-sky-700 dark:text-sky-400", bar: "bg-sky-500", barBg: "bg-sky-100 dark:bg-sky-900/40" },
  { bg: "bg-blue-50 dark:bg-blue-950/30", border: "border-blue-200 dark:border-blue-800", text: "text-blue-700 dark:text-blue-400", bar: "bg-blue-500", barBg: "bg-blue-100 dark:bg-blue-900/40" },
];

const OVERDUE_LABELS: Record<string, string> = {
  "0-30": "0-30 giorni",
  "31-60": "31-60 giorni",
  "61-90": "61-90 giorni",
  "90+": "Oltre 90 giorni",
};

const UPCOMING_LABELS: Record<string, string> = {
  "0-7": "Questa settimana",
  "8-30": "Entro 30 giorni",
  "31-60": "31-60 giorni",
  "61-90": "61-90 giorni",
};

// ════════════════════════════════════════════════════════════
// Componente principale
// ════════════════════════════════════════════════════════════

export function AgingReport() {
  const { data, isLoading, isError } = useAgingReport();

  if (isLoading) return <AgingSkeleton />;

  if (isError || !data) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
        <p className="text-destructive">
          Errore nel caricamento dell&apos;aging report.
        </p>
      </div>
    );
  }

  const hasOverdue = data.rate_scadute > 0;
  const hasUpcoming = data.rate_in_arrivo > 0;

  if (!hasOverdue && !hasUpcoming) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-emerald-200 bg-emerald-50/30 py-16 dark:border-emerald-800 dark:bg-emerald-950/10">
        <TrendingUp className="mb-3 h-10 w-10 text-emerald-500" />
        <p className="font-semibold text-emerald-700 dark:text-emerald-400">Nessuna rata in sospeso</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Tutti i pagamenti sono in regola
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── KPI Card ── */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        <KpiCard
          icon={<AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />}
          iconBg="bg-red-100 dark:bg-red-900/30"
          label="Totale Scaduto"
          value={formatCurrency(data.totale_scaduto)}
          valueClass="text-red-700 dark:text-red-400"
          sub={`${data.rate_scadute} rat${data.rate_scadute === 1 ? "a" : "e"}`}
          borderColor="border-l-red-500"
          gradient="from-red-50/80 to-white dark:from-red-950/40 dark:to-zinc-900"
        />
        <KpiCard
          icon={<TrendingUp className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />}
          iconBg="bg-emerald-100 dark:bg-emerald-900/30"
          label="In Arrivo"
          value={formatCurrency(data.totale_in_arrivo)}
          valueClass="text-emerald-700 dark:text-emerald-400"
          sub={`${data.rate_in_arrivo} rat${data.rate_in_arrivo === 1 ? "a" : "e"}`}
          borderColor="border-l-emerald-500"
          gradient="from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900"
        />
        <KpiCard
          icon={<Users className="h-5 w-5 text-orange-600 dark:text-orange-400" />}
          iconBg="bg-orange-100 dark:bg-orange-900/30"
          label="Clienti con debito"
          value={String(data.clienti_con_scaduto)}
          valueClass="text-orange-700 dark:text-orange-400"
          sub="con rate scadute"
          borderColor="border-l-orange-500"
          gradient="from-orange-50/80 to-white dark:from-orange-950/40 dark:to-zinc-900"
        />
      </div>

      {/* ── Sezione Scadute ── */}
      {hasOverdue && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 border-b pb-2">
            <Clock className="h-4 w-4 text-red-500" />
            <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Rate Scadute
            </h3>
          </div>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {data.overdue_buckets.map((bucket, i) => (
              <BucketCard
                key={bucket.label}
                bucket={bucket}
                colors={OVERDUE_COLORS[i]}
                labelMap={OVERDUE_LABELS}
                showDays
              />
            ))}
          </div>
        </div>
      )}

      {/* ── Sezione In Arrivo ── */}
      {hasUpcoming && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 border-b pb-2">
            <TrendingUp className="h-4 w-4 text-emerald-500" />
            <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Rate In Arrivo
            </h3>
          </div>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {data.upcoming_buckets.map((bucket, i) => (
              <BucketCard
                key={bucket.label}
                bucket={bucket}
                colors={UPCOMING_COLORS[i]}
                labelMap={UPCOMING_LABELS}
                showDays={false}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// KPI Card
// ════════════════════════════════════════════════════════════

function KpiCard({
  icon,
  iconBg,
  label,
  value,
  valueClass,
  sub,
  borderColor,
  gradient,
}: {
  icon: React.ReactNode;
  iconBg: string;
  label: string;
  value: string;
  valueClass: string;
  sub: string;
  borderColor: string;
  gradient: string;
}) {
  return (
    <div className={`flex items-start gap-3 rounded-xl border border-l-4 ${borderColor} bg-gradient-to-br ${gradient} p-4 shadow-sm transition-shadow hover:shadow-md`}>
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
          {label}
        </p>
        <p className={`text-2xl font-bold tracking-tight ${valueClass}`}>
          {value}
        </p>
        <p className="text-xs text-muted-foreground">{sub}</p>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Bucket Card
// ════════════════════════════════════════════════════════════

interface BucketColors {
  bg: string;
  border: string;
  text: string;
  bar: string;
  barBg: string;
}

function BucketCard({
  bucket,
  colors,
  labelMap,
  showDays,
}: {
  bucket: AgingBucket;
  colors: BucketColors;
  labelMap: Record<string, string>;
  showDays: boolean;
}) {
  const isEmpty = bucket.count === 0;

  return (
    <div className={`rounded-xl border ${colors.border} ${colors.bg} p-4 space-y-3 transition-shadow hover:shadow-md`}>
      {/* Header */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {labelMap[bucket.label] ?? bucket.label}
        </p>
        <p className={`text-lg font-bold tracking-tight ${colors.text}`}>
          {formatCurrency(bucket.totale)}
        </p>
        <p className="text-xs text-muted-foreground">
          {bucket.count} rat{bucket.count === 1 ? "a" : "e"}
        </p>
      </div>

      {/* Lista rate */}
      {!isEmpty && (
        <ScrollArea className="h-[200px]">
          <div className="space-y-1">
            {bucket.items.map((item) => (
              <ItemRow key={item.rate_id} item={item} colors={colors} showDays={showDays} />
            ))}
          </div>
        </ScrollArea>
      )}

      {/* Empty bucket */}
      {isEmpty && (
        <p className="py-3 text-center text-xs text-muted-foreground">
          Nessuna rata
        </p>
      )}
    </div>
  );
}

// ── Riga singola rata ──

function ItemRow({
  item,
  colors,
  showDays,
}: {
  item: AgingItem;
  colors: BucketColors;
  showDays: boolean;
}) {
  const daysLabel = showDays
    ? `${item.giorni}g`
    : `${Math.abs(item.giorni)}g`;

  return (
    <div className="flex items-center justify-between rounded-md px-2 py-1 text-sm transition-colors hover:bg-white/60 dark:hover:bg-white/5">
      <div className="flex items-center gap-1.5 min-w-0">
        <div className={`h-1.5 w-1.5 shrink-0 rounded-full ${colors.bar}`} />
        <span className="truncate font-medium">
          {item.client_cognome} {item.client_nome.charAt(0)}.
        </span>
        <span className="shrink-0 text-[11px] tabular-nums text-muted-foreground">
          {daysLabel}
        </span>
      </div>
      <span className={`shrink-0 tabular-nums font-semibold ${colors.text}`}>
        {formatCurrency(item.importo_residuo)}
      </span>
    </div>
  );
}

// ── Skeleton ──

function AgingSkeleton() {
  const kpiBorders = ["border-l-red-500", "border-l-emerald-500", "border-l-orange-500"];
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        {kpiBorders.map((border, i) => (
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
      <Skeleton className="h-4 w-32" />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-48 w-full rounded-xl" />
        ))}
      </div>
    </div>
  );
}
