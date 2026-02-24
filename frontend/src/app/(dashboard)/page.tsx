// src/app/(dashboard)/page.tsx
"use client";

/**
 * Dashboard — CRM-grade overview con 4 sezioni:
 *
 * 1. Hero KPI: 6 card gradient (clienti, entrate, uscite, margine, rate, appuntamenti)
 * 2. Alert Panel: warning proattivi a 3 livelli di severita'
 * 3. Due colonne: Orizzonte Finanziario (mini aging) + Agenda Oggi
 * 4. Azioni rapide: link a creazione cliente, contratto, movimento
 *
 * Dati da 5 hook — incluso nuovo /dashboard/alerts.
 */

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  Users,
  TrendingUp,
  TrendingDown,
  Target,
  AlertTriangle,
  CalendarCheck,
  LayoutDashboard,
  UserPlus,
  FileText,
  Landmark,
  Clock,
  Calendar,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  ShieldAlert,
  Ghost,
  UserX,
  CreditCard,
  Bell,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useDashboard, useDashboardAlerts } from "@/hooks/useDashboard";
import { useMovementStats } from "@/hooks/useMovements";
import { useAgingReport } from "@/hooks/useRates";
import { useEvents, type EventHydrated } from "@/hooks/useAgenda";
import { formatCurrency } from "@/lib/format";
import { GhostEventsSheet } from "@/components/dashboard/GhostEventsSheet";
import { OverdueRatesSheet } from "@/components/dashboard/OverdueRatesSheet";
import { ExpiringContractsSheet } from "@/components/dashboard/ExpiringContractsSheet";
import { InactiveClientsSheet } from "@/components/dashboard/InactiveClientsSheet";
import { TodoCard } from "@/components/dashboard/TodoCard";
import type { DashboardSummary, MovementStats, AgingResponse, DashboardAlerts } from "@/types/api";

// ── Date helpers ──

const now = new Date();
const ANNO = now.getFullYear();
const MESE = now.getMonth() + 1;

function todayISO(): string {
  return now.toISOString().slice(0, 10);
}

function tomorrowISO(): string {
  const d = new Date(now);
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

const MESE_LABEL = now.toLocaleDateString("it-IT", { month: "long" });

// ── Category colors (mirror agenda) ──

const CATEGORY_COLORS: Record<string, string> = {
  PT: "bg-blue-500",
  SALA: "bg-emerald-500",
  CORSO: "bg-violet-500",
  COLLOQUIO: "bg-amber-500",
  PERSONALE: "bg-pink-500",
};

const STATUS_COLORS: Record<string, string> = {
  Programmato: "text-blue-600 dark:text-blue-400",
  Completato: "text-emerald-600 dark:text-emerald-400",
  Cancellato: "text-red-400 line-through",
  Rinviato: "text-amber-600 dark:text-amber-400",
};

// ════════════════════════════════════════════════════════════
// Pagina
// ════════════════════════════════════════════════════════════

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading, isError, refetch } = useDashboard();
  const { data: stats, isLoading: statsLoading } = useMovementStats(ANNO, MESE);
  const { data: alerts } = useDashboardAlerts();
  const { data: aging } = useAgingReport();
  const { data: eventsData } = useEvents({ start: todayISO(), end: tomorrowISO() });

  // Sheet state per risoluzione inline alert
  const [ghostSheetOpen, setGhostSheetOpen] = useState(false);
  const [overdueSheetOpen, setOverdueSheetOpen] = useState(false);
  const [expiringSheetOpen, setExpiringSheetOpen] = useState(false);
  const [inactiveSheetOpen, setInactiveSheetOpen] = useState(false);

  const todayEvents = useMemo(() => {
    if (!eventsData?.items) return [];
    const today = todayISO();
    return eventsData.items
      .filter((e) => e.data_inizio.toISOString().slice(0, 10) === today && e.stato !== "Cancellato")
      .sort((a, b) => a.data_inizio.getTime() - b.data_inizio.getTime());
  }, [eventsData]);

  const isLoading = summaryLoading || statsLoading;

  // Handler CTA per categoria alert — apre Sheet inline
  const alertActions: Record<string, () => void> = {
    ghost_events: () => setGhostSheetOpen(true),
    overdue_rates: () => setOverdueSheetOpen(true),
    expiring_contracts: () => setExpiringSheetOpen(true),
    inactive_clients: () => setInactiveSheetOpen(true),
  };

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900/40 dark:to-blue-800/30">
          <LayoutDashboard className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Panoramica della tua attivita' — {MESE_LABEL} {ANNO}
          </p>
        </div>
      </div>

      {/* ── Error state ── */}
      {isError && (
        <div className="flex items-center justify-between rounded-xl border border-destructive/50 bg-destructive/5 p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-destructive" />
            <p className="text-sm text-destructive">
              Impossibile caricare i dati della dashboard.
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Riprova
          </Button>
        </div>
      )}

      {/* ── Hero KPI ── */}
      {isLoading && <KpiSkeleton />}
      {summary && stats && <KpiCards summary={summary} stats={stats} />}

      {/* ── Alert Panel ── */}
      <AlertPanel alerts={alerts} isLoading={!alerts} alertActions={alertActions} />

      {/* ── Tre colonne: Aging + Agenda + Todo ── */}
      <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
        <FinancialHealth aging={aging} isLoading={!aging} />
        <TodayAgenda events={todayEvents} isLoading={!eventsData} />
        <TodoCard />
      </div>

      {/* ── Azioni Rapide ── */}
      <QuickActions />

      {/* ── Sheet risoluzione inline ── */}
      <GhostEventsSheet open={ghostSheetOpen} onOpenChange={setGhostSheetOpen} />
      <OverdueRatesSheet open={overdueSheetOpen} onOpenChange={setOverdueSheetOpen} />
      <ExpiringContractsSheet open={expiringSheetOpen} onOpenChange={setExpiringSheetOpen} />
      <InactiveClientsSheet open={inactiveSheetOpen} onOpenChange={setInactiveSheetOpen} />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// KPI Cards (6 card)
// ════════════════════════════════════════════════════════════

interface KpiDef {
  key: string;
  label: string;
  subtitle: string;
  icon: typeof Users;
  value: number;
  format: "number" | "currency";
  borderColor: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  valueColor: string;
}

function buildKpiList(summary: DashboardSummary, stats: MovementStats): KpiDef[] {
  const isPositive = stats.margine_netto >= 0;

  return [
    {
      key: "clients",
      label: "Clienti Attivi",
      subtitle: "nel sistema",
      icon: Users,
      value: summary.active_clients,
      format: "number",
      borderColor: "border-l-blue-500",
      gradient: "from-blue-50/80 to-white dark:from-blue-950/40 dark:to-zinc-900",
      iconBg: "bg-blue-100 dark:bg-blue-900/30",
      iconColor: "text-blue-600 dark:text-blue-400",
      valueColor: "text-blue-700 dark:text-blue-400",
    },
    {
      key: "revenue",
      label: "Entrate",
      subtitle: "questo mese",
      icon: TrendingUp,
      value: stats.totale_entrate,
      format: "currency",
      borderColor: "border-l-emerald-500",
      gradient: "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900",
      iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
      iconColor: "text-emerald-600 dark:text-emerald-400",
      valueColor: "text-emerald-700 dark:text-emerald-400",
    },
    {
      key: "expenses",
      label: "Uscite Totali",
      subtitle: "questo mese",
      icon: TrendingDown,
      value: stats.totale_uscite_variabili + stats.totale_uscite_fisse,
      format: "currency",
      borderColor: "border-l-red-500",
      gradient: "from-red-50/80 to-white dark:from-red-950/40 dark:to-zinc-900",
      iconBg: "bg-red-100 dark:bg-red-900/30",
      iconColor: "text-red-600 dark:text-red-400",
      valueColor: "text-red-700 dark:text-red-400",
    },
    {
      key: "margin",
      label: "Margine Netto",
      subtitle: "questo mese",
      icon: Target,
      value: stats.margine_netto,
      format: "currency",
      borderColor: isPositive ? "border-l-emerald-500" : "border-l-red-500",
      gradient: isPositive
        ? "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900"
        : "from-red-50/80 to-white dark:from-red-950/40 dark:to-zinc-900",
      iconBg: isPositive ? "bg-emerald-100 dark:bg-emerald-900/30" : "bg-red-100 dark:bg-red-900/30",
      iconColor: isPositive ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400",
      valueColor: isPositive ? "text-emerald-700 dark:text-emerald-400" : "text-red-700 dark:text-red-400",
    },
    {
      key: "rates",
      label: "Rate in Scadenza",
      subtitle: "prossimi 7 giorni",
      icon: AlertTriangle,
      value: summary.pending_rates,
      format: "number",
      borderColor: summary.pending_rates > 0 ? "border-l-amber-500" : "border-l-zinc-300",
      gradient: summary.pending_rates > 0
        ? "from-amber-50/80 to-white dark:from-amber-950/40 dark:to-zinc-900"
        : "from-zinc-50/80 to-white dark:from-zinc-900/40 dark:to-zinc-900",
      iconBg: summary.pending_rates > 0 ? "bg-amber-100 dark:bg-amber-900/30" : "bg-zinc-100 dark:bg-zinc-800/30",
      iconColor: summary.pending_rates > 0 ? "text-amber-600 dark:text-amber-400" : "text-zinc-500 dark:text-zinc-400",
      valueColor: summary.pending_rates > 0 ? "text-amber-700 dark:text-amber-400" : "text-zinc-700 dark:text-zinc-400",
    },
    {
      key: "appointments",
      label: "Appuntamenti Oggi",
      subtitle: "in programma",
      icon: CalendarCheck,
      value: summary.todays_appointments,
      format: "number",
      borderColor: "border-l-violet-500",
      gradient: "from-violet-50/80 to-white dark:from-violet-950/40 dark:to-zinc-900",
      iconBg: "bg-violet-100 dark:bg-violet-900/30",
      iconColor: "text-violet-600 dark:text-violet-400",
      valueColor: "text-violet-700 dark:text-violet-400",
    },
  ];
}

function KpiCards({ summary, stats }: { summary: DashboardSummary; stats: MovementStats }) {
  const kpis = buildKpiList(summary, stats);

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
      {kpis.map((kpi) => {
        const Icon = kpi.icon;
        return (
          <div
            key={kpi.key}
            className={`flex items-start gap-2 rounded-xl border border-l-4 ${kpi.borderColor} bg-gradient-to-br ${kpi.gradient} p-3 shadow-sm transition-shadow hover:shadow-md sm:gap-3 sm:p-4`}
          >
            <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg sm:h-10 sm:w-10 ${kpi.iconBg}`}>
              <Icon className={`h-4 w-4 sm:h-5 sm:w-5 ${kpi.iconColor}`} />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase sm:text-[11px]">
                {kpi.label}
              </p>
              <p className={`text-lg font-bold tracking-tight sm:text-2xl ${kpi.valueColor}`}>
                {kpi.format === "currency" ? formatCurrency(kpi.value) : kpi.value}
              </p>
              <p className="text-[10px] text-muted-foreground/70">{kpi.subtitle}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Alert Panel — Warning proattivi
// ════════════════════════════════════════════════════════════

// Config-driven: ogni categoria ha icona, colori, e CTA contestuale
const ALERT_CATEGORY_CONFIG: Record<string, {
  icon: typeof Ghost;
  color: string;
  bgColor: string;
  borderColor: string;
  cta: string;
}> = {
  ghost_events: {
    icon: Ghost,
    color: "text-red-600 dark:text-red-400",
    bgColor: "bg-red-100 dark:bg-red-900/30",
    borderColor: "border-l-red-500",
    cta: "Aggiorna stato",
  },
  expiring_contracts: {
    icon: CreditCard,
    color: "text-amber-600 dark:text-amber-400",
    bgColor: "bg-amber-100 dark:bg-amber-900/30",
    borderColor: "border-l-amber-500",
    cta: "Vedi contratto",
  },
  overdue_rates: {
    icon: ShieldAlert,
    color: "text-red-600 dark:text-red-400",
    bgColor: "bg-red-100 dark:bg-red-900/30",
    borderColor: "border-l-red-500",
    cta: "Riscuoti",
  },
  inactive_clients: {
    icon: UserX,
    color: "text-orange-600 dark:text-orange-400",
    bgColor: "bg-orange-100 dark:bg-orange-900/30",
    borderColor: "border-l-orange-500",
    cta: "Contatta",
  },
};

function AlertPanel({ alerts, isLoading, alertActions = {} }: {
  alerts: DashboardAlerts | undefined;
  isLoading: boolean;
  alertActions?: Record<string, () => void>;
}) {
  if (isLoading) {
    return (
      <div className="rounded-xl border p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-5 rounded" />
          <Skeleton className="h-5 w-40" />
        </div>
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (!alerts || alerts.total_alerts === 0) {
    return (
      <div className="flex items-center gap-4 rounded-xl border border-emerald-200 bg-gradient-to-r from-emerald-50/80 to-white p-5 shadow-sm dark:border-emerald-800/50 dark:from-emerald-950/30 dark:to-zinc-900">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-900/30">
          <CheckCircle2 className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
        </div>
        <div>
          <p className="text-sm font-bold text-emerald-700 dark:text-emerald-400">
            Tutto sotto controllo
          </p>
          <p className="text-xs text-muted-foreground">
            Nessun alert attivo — ottimo lavoro!
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-5 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
      {/* Header con badge notifica */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <Bell className="h-5 w-5 text-amber-500" />
            <span className="absolute -right-1.5 -top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white shadow-sm">
              {alerts.total_alerts}
            </span>
          </div>
          <h3 className="font-semibold">Attenzione Richiesta</h3>
        </div>
        <div className="flex items-center gap-1.5">
          {alerts.critical_count > 0 && (
            <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-[10px] font-bold text-red-700 dark:bg-red-900/40 dark:text-red-400">
              {alerts.critical_count} {alerts.critical_count === 1 ? "critico" : "critici"}
            </span>
          )}
          {alerts.warning_count > 0 && (
            <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-[10px] font-bold text-amber-700 dark:bg-amber-900/40 dark:text-amber-400">
              {alerts.warning_count} {alerts.warning_count === 1 ? "avviso" : "avvisi"}
            </span>
          )}
        </div>
      </div>

      {/* Alert items — gerarchia visiva per severity */}
      <div className="space-y-2.5">
        {alerts.items.map((item, idx) => {
          const catCfg = ALERT_CATEGORY_CONFIG[item.category] ?? ALERT_CATEGORY_CONFIG.ghost_events;
          const CatIcon = catCfg.icon;
          const isCritical = item.severity === "critical";

          return (
            <div
              key={`${item.category}-${idx}`}
              className={`flex items-center gap-3 rounded-lg border border-l-4 ${catCfg.borderColor} p-3.5 transition-all hover:shadow-md hover:-translate-y-0.5 ${
                isCritical
                  ? "bg-red-50/60 dark:bg-red-950/20"
                  : "bg-white dark:bg-zinc-900"
              }`}
            >
              {/* Icona — piu' grande per critical */}
              <div className={`flex ${isCritical ? "h-10 w-10" : "h-9 w-9"} shrink-0 items-center justify-center rounded-lg ${catCfg.bgColor}`}>
                <CatIcon className={`${isCritical ? "h-5 w-5" : "h-4 w-4"} ${catCfg.color}`} />
              </div>

              {/* Contenuto */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className={`${isCritical ? "text-sm" : "text-[13px]"} font-semibold leading-tight`}>
                    {item.title}
                  </p>
                  {item.count > 1 && (
                    <Badge variant="secondary" className="h-4 px-1.5 py-0 text-[9px]">
                      {item.count}
                    </Badge>
                  )}
                </div>
                <p className="mt-0.5 text-[11px] text-muted-foreground">{item.detail}</p>
              </div>

              {/* CTA contestuale — Sheet inline o navigazione */}
              {alertActions[item.category] ? (
                <Button
                  variant={isCritical ? "default" : "outline"}
                  size="sm"
                  className={`h-8 shrink-0 gap-1.5 text-xs font-medium ${
                    isCritical
                      ? "bg-red-600 text-white shadow-sm hover:bg-red-700"
                      : ""
                  }`}
                  onClick={alertActions[item.category]}
                >
                  {catCfg.cta}
                  <ArrowRight className="h-3 w-3" />
                </Button>
              ) : item.link ? (
                <Link href={item.link}>
                  <Button
                    variant={isCritical ? "default" : "outline"}
                    size="sm"
                    className={`h-8 shrink-0 gap-1.5 text-xs font-medium ${
                      isCritical
                        ? "bg-red-600 text-white shadow-sm hover:bg-red-700"
                        : ""
                    }`}
                  >
                    {catCfg.cta}
                    <ArrowRight className="h-3 w-3" />
                  </Button>
                </Link>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Orizzonte Finanziario (mini aging)
// ════════════════════════════════════════════════════════════

function FinancialHealth({ aging, isLoading }: { aging: AgingResponse | undefined; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="rounded-xl border p-5 space-y-4">
        <Skeleton className="h-5 w-48" />
        <div className="grid grid-cols-2 gap-3">
          <Skeleton className="h-20 rounded-lg" />
          <Skeleton className="h-20 rounded-lg" />
        </div>
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (!aging) return null;

  const hasOverdue = aging.totale_scaduto > 0;

  return (
    <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-5 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className={`h-4 w-4 ${hasOverdue ? "text-amber-500" : "text-emerald-500"}`} />
          <h3 className="text-sm font-semibold">Orizzonte Finanziario</h3>
        </div>
        <Link href="/cassa">
          <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs">
            Dettaglio <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
      </div>

      {/* Mini KPI */}
      <div className="mb-4 grid grid-cols-2 gap-3">
        <div className={`rounded-lg border border-l-4 ${hasOverdue ? "border-l-red-500 bg-red-50/50 dark:bg-red-950/20" : "border-l-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/20"} p-3`}>
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            Scaduto
          </p>
          <p className={`text-lg font-bold ${hasOverdue ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}`}>
            {formatCurrency(aging.totale_scaduto)}
          </p>
          <p className="text-[10px] text-muted-foreground/70">
            {aging.rate_scadute} {aging.rate_scadute === 1 ? "rata" : "rate"} — {aging.clienti_con_scaduto} {aging.clienti_con_scaduto === 1 ? "cliente" : "clienti"}
          </p>
        </div>
        <div className="rounded-lg border border-l-4 border-l-amber-500 bg-amber-50/50 p-3 dark:bg-amber-950/20">
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            In Arrivo
          </p>
          <p className="text-lg font-bold text-amber-600 dark:text-amber-400">
            {formatCurrency(aging.totale_in_arrivo)}
          </p>
          <p className="text-[10px] text-muted-foreground/70">
            {aging.rate_in_arrivo} {aging.rate_in_arrivo === 1 ? "rata" : "rate"} previste
          </p>
        </div>
      </div>

      <Separator className="mb-3" />

      {/* Bucket bars */}
      {hasOverdue ? (
        <div className="space-y-2">
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            Scaduto per fascia
          </p>
          {aging.overdue_buckets.map((bucket) => {
            const maxAmount = Math.max(...aging.overdue_buckets.map((b) => b.totale), 1);
            const widthPct = Math.max((bucket.totale / maxAmount) * 100, 2);
            return (
              <div key={bucket.label} className="flex items-center gap-2">
                <span className="w-12 text-[10px] tabular-nums text-muted-foreground">
                  {bucket.label}gg
                </span>
                <div className="flex-1">
                  <div
                    className="h-2.5 rounded-full bg-gradient-to-r from-red-400 to-red-500 transition-all duration-500"
                    style={{ width: `${widthPct}%` }}
                  />
                </div>
                <span className="w-16 text-right text-[11px] font-medium tabular-nums">
                  {formatCurrency(bucket.totale)}
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50/50 p-3 dark:border-emerald-800 dark:bg-emerald-950/20">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          <p className="text-sm text-emerald-700 dark:text-emerald-400">
            Nessuna rata scaduta — tutto in ordine!
          </p>
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Agenda Oggi
// ════════════════════════════════════════════════════════════

function TodayAgenda({ events, isLoading }: { events: EventHydrated[]; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="rounded-xl border p-5 space-y-4">
        <Skeleton className="h-5 w-40" />
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  const todayFormatted = now.toLocaleDateString("it-IT", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return (
    <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-5 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-violet-500" />
          <h3 className="text-sm font-semibold">Agenda Oggi</h3>
        </div>
        <Link href="/agenda">
          <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs">
            Calendario <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
      </div>

      <p className="mb-3 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
        {todayFormatted}
      </p>

      {events.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed p-6 text-center">
          <CalendarCheck className="h-8 w-8 text-muted-foreground/30" />
          <p className="text-sm text-muted-foreground">
            Nessun appuntamento oggi
          </p>
          <p className="text-xs text-muted-foreground/70">
            La giornata e' libera
          </p>
        </div>
      ) : (
        <ScrollArea className={events.length > 5 ? "h-[220px]" : ""}>
          <div className="space-y-2">
            {events.map((event) => {
              const time = event.data_inizio.toLocaleTimeString("it-IT", {
                hour: "2-digit",
                minute: "2-digit",
              });
              const endTime = event.data_fine.toLocaleTimeString("it-IT", {
                hour: "2-digit",
                minute: "2-digit",
              });
              const catColor = CATEGORY_COLORS[event.categoria] ?? "bg-zinc-400";
              const statusColor = STATUS_COLORS[event.stato] ?? "";

              return (
                <div
                  key={event.id}
                  className="flex items-center gap-3 rounded-lg border bg-white p-3 transition-shadow hover:shadow-sm dark:bg-zinc-900"
                >
                  <div className={`h-8 w-1 shrink-0 rounded-full ${catColor}`} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold tabular-nums text-muted-foreground">
                        {time}
                      </span>
                      <span className="text-[10px] text-muted-foreground/50">—</span>
                      <span className="text-[10px] tabular-nums text-muted-foreground/70">
                        {endTime}
                      </span>
                    </div>
                    <p className={`truncate text-sm font-medium ${statusColor}`}>
                      {event.titolo || event.categoria}
                    </p>
                    {event.cliente_nome && (
                      <p className="truncate text-[11px] text-muted-foreground">
                        {event.cliente_nome} {event.cliente_cognome}
                      </p>
                    )}
                  </div>
                  <Badge variant="outline" className="shrink-0 text-[9px]">
                    {event.categoria}
                  </Badge>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Azioni Rapide
// ════════════════════════════════════════════════════════════

const QUICK_ACTIONS = [
  {
    label: "Nuovo Cliente",
    icon: UserPlus,
    href: "/clienti",
    gradient: "from-blue-50 to-blue-100/50 dark:from-blue-950/30 dark:to-zinc-900",
    iconColor: "text-blue-600 dark:text-blue-400",
    border: "border-blue-200 dark:border-blue-800/50",
  },
  {
    label: "Nuovo Contratto",
    icon: FileText,
    href: "/contratti",
    gradient: "from-violet-50 to-violet-100/50 dark:from-violet-950/30 dark:to-zinc-900",
    iconColor: "text-violet-600 dark:text-violet-400",
    border: "border-violet-200 dark:border-violet-800/50",
  },
  {
    label: "Nuovo Movimento",
    icon: Landmark,
    href: "/cassa",
    gradient: "from-emerald-50 to-emerald-100/50 dark:from-emerald-950/30 dark:to-zinc-900",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    border: "border-emerald-200 dark:border-emerald-800/50",
  },
  {
    label: "Agenda",
    icon: Clock,
    href: "/agenda",
    gradient: "from-amber-50 to-amber-100/50 dark:from-amber-950/30 dark:to-zinc-900",
    iconColor: "text-amber-600 dark:text-amber-400",
    border: "border-amber-200 dark:border-amber-800/50",
  },
] as const;

function QuickActions() {
  return (
    <div>
      <p className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Azioni rapide
      </p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {QUICK_ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <Link key={action.label} href={action.href}>
              <div className={`flex items-center gap-3 rounded-xl border ${action.border} bg-gradient-to-br ${action.gradient} p-4 transition-all hover:shadow-md hover:-translate-y-0.5`}>
                <Icon className={`h-5 w-5 ${action.iconColor}`} />
                <span className="text-sm font-medium">{action.label}</span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Skeleton
// ════════════════════════════════════════════════════════════

function KpiSkeleton() {
  const borders = [
    "border-l-blue-500",
    "border-l-emerald-500",
    "border-l-red-500",
    "border-l-emerald-500",
    "border-l-amber-500",
    "border-l-violet-500",
  ];
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
      {borders.map((border, i) => (
        <div key={i} className={`flex items-start gap-3 rounded-xl border border-l-4 ${border} p-4`}>
          <Skeleton className="h-10 w-10 shrink-0 rounded-lg" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-6 w-20" />
            <Skeleton className="h-2 w-12" />
          </div>
        </div>
      ))}
    </div>
  );
}
