// src/app/(dashboard)/page.tsx
"use client";

/**
 * Dashboard â€” CRM-grade overview con 4 sezioni:
 *
 * 1. Hero KPI: card operative (clienti, appuntamenti)
 * 2. Alert Panel: warning proattivi a 3 livelli di severita'
 * 3. Due colonne: Agenda Oggi + Todo
 * 4. Azioni rapide: link a creazione cliente, contratto, scheda
 *
 * Dati da hook operativi + /dashboard/alerts.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Users,
  CalendarCheck,
  LayoutDashboard,
  UserPlus,
  FileText,
  Clock,
  Calendar,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Ghost,
  UserX,
  CreditCard,
  Bell,
  Sparkles,
  Rocket,
  Loader2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useDashboard, useDashboardAlerts } from "@/hooks/useDashboard";
import { useEvents, useUpdateEvent, type EventHydrated } from "@/hooks/useAgenda";
import { AnimatedNumber } from "@/components/ui/animated-number";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { GhostEventsSheet } from "@/components/dashboard/GhostEventsSheet";
import { ExpiringContractsSheet } from "@/components/dashboard/ExpiringContractsSheet";
import { InactiveClientsSheet } from "@/components/dashboard/InactiveClientsSheet";
import { TodoCard } from "@/components/dashboard/TodoCard";
import {
  EVENT_STATUSES,
  type DashboardSummary,
  type DashboardAlerts,
} from "@/types/api";

// â”€â”€ Date helpers â”€â”€

function formatLocalISODate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function todayISO(referenceDate: Date = new Date()): string {
  return formatLocalISODate(referenceDate);
}

function tomorrowISO(referenceDate: Date = new Date()): string {
  const d = new Date(referenceDate);
  d.setDate(d.getDate() + 1);
  return formatLocalISODate(d);
}

function weekStartDate(baseDate: Date = new Date()): Date {
  const date = new Date(baseDate);
  const day = date.getDay();
  const delta = day === 0 ? -6 : 1 - day;
  date.setDate(date.getDate() + delta);
  date.setHours(0, 0, 0, 0);
  return date;
}

function weekStartISO(baseDate: Date = new Date()): string {
  return formatLocalISODate(weekStartDate(baseDate));
}

function nextWeekStartISO(baseDate: Date = new Date()): string {
  const date = weekStartDate(baseDate);
  date.setDate(date.getDate() + 7);
  return formatLocalISODate(date);
}

function currentWeekLabel(baseDate: Date = new Date()): string {
  const start = weekStartDate(baseDate);
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  const formatOptions: Intl.DateTimeFormatOptions = { day: "2-digit", month: "short" };
  return `${start.toLocaleDateString("it-IT", formatOptions)} - ${end.toLocaleDateString("it-IT", formatOptions)}`;
}

// â”€â”€ Category colors (mirror agenda) â”€â”€

const CATEGORY_COLORS: Record<string, string> = {
  PT: "bg-blue-500",
  SALA: "bg-emerald-500",
  CORSO: "bg-violet-500",
  COLLOQUIO: "bg-amber-500",
  PERSONALE: "bg-pink-500",
};

const CATEGORY_LABELS: Record<string, string> = {
  PT: "PT",
  PERSONALE: "Personale",
  COLLOQUIO: "Colloquio",
  SALA: "Sala",
  CORSO: "Corso",
};

const WEEKLY_CATEGORY_ORDER = ["PT", "PERSONALE", "COLLOQUIO", "SALA", "CORSO"] as const;

const WEEKLY_CATEGORY_THEME: Record<string, {
  chip: string;
  card: string;
  border: string;
  total: string;
}> = {
  PT: {
    chip: "bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300",
    card: "from-blue-50/80 to-white dark:from-blue-950/25 dark:to-zinc-900",
    border: "border-blue-200/80 dark:border-blue-800/50",
    total: "text-blue-700 dark:text-blue-300",
  },
  PERSONALE: {
    chip: "bg-pink-100 text-pink-700 dark:bg-pink-950/40 dark:text-pink-300",
    card: "from-pink-50/80 to-white dark:from-pink-950/25 dark:to-zinc-900",
    border: "border-pink-200/80 dark:border-pink-800/50",
    total: "text-pink-700 dark:text-pink-300",
  },
  COLLOQUIO: {
    chip: "bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
    card: "from-amber-50/80 to-white dark:from-amber-950/25 dark:to-zinc-900",
    border: "border-amber-200/80 dark:border-amber-800/50",
    total: "text-amber-700 dark:text-amber-300",
  },
  SALA: {
    chip: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
    card: "from-emerald-50/80 to-white dark:from-emerald-950/25 dark:to-zinc-900",
    border: "border-emerald-200/80 dark:border-emerald-800/50",
    total: "text-emerald-700 dark:text-emerald-300",
  },
  CORSO: {
    chip: "bg-cyan-100 text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-300",
    card: "from-cyan-50/80 to-white dark:from-cyan-950/25 dark:to-zinc-900",
    border: "border-cyan-200/80 dark:border-cyan-800/50",
    total: "text-cyan-700 dark:text-cyan-300",
  },
};

const STATUS_COLORS: Record<string, string> = {
  Programmato: "text-blue-600 dark:text-blue-400",
  Completato: "text-emerald-600 dark:text-emerald-400",
  Cancellato: "text-red-400 line-through",
  Rinviato: "text-amber-600 dark:text-amber-400",
};

// POC toggle: disattiva in un punto unico per rollback veloce.
const DASHBOARD_MICROSTEP2_ENABLED = true;

function getRevealMotionClass(enabled: boolean, ready: boolean): string {
  if (!enabled) return "";
  return `transform-gpu transition-[opacity,transform] duration-500 ease-out motion-reduce:transform-none motion-reduce:transition-none ${
    ready
      ? "translate-y-0 opacity-100"
      : "translate-y-1 opacity-0 motion-reduce:translate-y-0 motion-reduce:opacity-100"
  }`;
}

function getRevealDelayStyle(enabled: boolean, delayMs: number) {
  if (!enabled) return undefined;
  return { transitionDelay: `${delayMs}ms` };
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Pagina
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading, isError, refetch } = useDashboard();
  const { data: alerts } = useDashboardAlerts();
  const [dateAnchor, setDateAnchor] = useState(() => new Date());
  const [entranceReady, setEntranceReady] = useState(() => !DASHBOARD_MICROSTEP2_ENABLED);

  useEffect(() => {
    if (!DASHBOARD_MICROSTEP2_ENABLED) return;
    const rafId = window.requestAnimationFrame(() => setEntranceReady(true));
    return () => window.cancelAnimationFrame(rafId);
  }, []);

  useEffect(() => {
    const currentTime = new Date();
    const nextMidnight = new Date(currentTime);
    nextMidnight.setHours(24, 0, 0, 0);
    const timeoutMs = Math.max(1000, nextMidnight.getTime() - currentTime.getTime());
    const timeoutId = window.setTimeout(() => setDateAnchor(new Date()), timeoutMs);
    return () => window.clearTimeout(timeoutId);
  }, [dateAnchor]);

  const currentDayStart = useMemo(() => todayISO(dateAnchor), [dateAnchor]);
  const nextDayStart = useMemo(() => tomorrowISO(dateAnchor), [dateAnchor]);
  const currentWeekStart = useMemo(() => weekStartISO(dateAnchor), [dateAnchor]);
  const nextWeekStart = useMemo(() => nextWeekStartISO(dateAnchor), [dateAnchor]);
  const currentWeekRangeLabel = useMemo(() => currentWeekLabel(dateAnchor), [dateAnchor]);
  const monthLabel = useMemo(
    () => dateAnchor.toLocaleDateString("it-IT", { month: "long" }),
    [dateAnchor],
  );
  const yearLabel = dateAnchor.getFullYear();

  const { data: eventsData } = useEvents({ start: currentDayStart, end: nextDayStart });
  const { data: weeklyEventsData } = useEvents({ start: currentWeekStart, end: nextWeekStart });

  // Sheet state per risoluzione inline alert
  const [ghostSheetOpen, setGhostSheetOpen] = useState(false);
  const [expiringSheetOpen, setExpiringSheetOpen] = useState(false);
  const [inactiveSheetOpen, setInactiveSheetOpen] = useState(false);

  const todayEvents = useMemo(() => {
    if (!eventsData?.items) return [];
    const today = currentDayStart;
    return eventsData.items
      .filter((e) => formatLocalISODate(e.data_inizio) === today && e.stato !== "Cancellato")
      .sort((a, b) => a.data_inizio.getTime() - b.data_inizio.getTime());
  }, [eventsData, currentDayStart]);

  const weeklyEvents = useMemo(() => {
    if (!weeklyEventsData?.items) return [];
    return [...weeklyEventsData.items].sort((a, b) => a.data_inizio.getTime() - b.data_inizio.getTime());
  }, [weeklyEventsData]);

  const criticalAlertCount = alerts?.items.filter(
    (item) => item.category !== "overdue_rates" && item.severity === "critical",
  ).length ?? 0;
  const warningAlertCount = alerts?.items.filter(
    (item) => item.category !== "overdue_rates" && item.severity === "warning",
  ).length ?? 0;
  const upcomingSessionsCount = todayEvents.filter(
    (event) => event.stato === "Programmato",
  ).length;

  const isLoading = summaryLoading;

  // Handler CTA per categoria alert â€” apre Sheet inline
  const alertActions: Record<string, () => void> = {
    ghost_events: () => setGhostSheetOpen(true),
    expiring_contracts: () => setExpiringSheetOpen(true),
    inactive_clients: () => setInactiveSheetOpen(true),
  };

  return (
    <div className="min-w-0 space-y-4 md:space-y-6">
      {/* â”€â”€ Header â”€â”€ */}
      <div data-guide="dashboard-header" className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-100 to-blue-200 sm:h-11 sm:w-11 dark:from-blue-900/40 dark:to-blue-800/30">
          <LayoutDashboard className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight sm:text-2xl">Dashboard</h1>
          <p className="text-xs text-muted-foreground sm:text-sm">
            Panoramica della tua attivita&apos; â€” {monthLabel} {yearLabel}
          </p>
        </div>
      </div>

      {/* â”€â”€ Error state â”€â”€ */}
      {isError && (
        <div className="flex flex-col gap-3 rounded-xl border border-destructive/50 bg-destructive/5 p-4 sm:flex-row sm:items-center sm:justify-between">
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

      {/* â”€â”€ First-run welcome (zero clienti) â”€â”€ */}
      {!isLoading && summary && summary.active_clients === 0 ? (
        <WelcomeCard />
      ) : (
        <>
          {/* â”€â”€ Hero KPI â”€â”€ */}
          {isLoading && <KpiSkeleton />}
          {summary && (
            <KpiCards
              summary={summary}
              animateIn={entranceReady}
              animationsEnabled={DASHBOARD_MICROSTEP2_ENABLED}
            />
          )}

          <div
            className={`grid min-w-0 gap-4 md:gap-5 xl:grid-cols-2 ${getRevealMotionClass(
              DASHBOARD_MICROSTEP2_ENABLED,
              entranceReady,
            )}`}
            style={getRevealDelayStyle(DASHBOARD_MICROSTEP2_ENABLED, 120)}
          >
            <div className="min-w-0">
              <TodoCard
                criticalAlertCount={criticalAlertCount}
                warningAlertCount={warningAlertCount}
                upcomingSessionsCount={upcomingSessionsCount}
              />
            </div>
            <div className="min-w-0">
              <TodayAgenda
                events={todayEvents}
                isLoading={!eventsData}
                referenceDate={dateAnchor}
                animateIn={entranceReady}
                animationsEnabled={DASHBOARD_MICROSTEP2_ENABLED}
              />
            </div>
          </div>

          <div className="grid min-w-0 gap-5 md:gap-6 xl:grid-cols-12">
            <div className="min-w-0 xl:col-span-7">
              <WeeklyLessons
                events={weeklyEvents}
                isLoading={!weeklyEventsData}
                weekLabel={currentWeekRangeLabel}
              />
            </div>
            <div className="min-w-0 xl:col-span-5">
              <AlertPanel alerts={alerts} isLoading={!alerts} alertActions={alertActions} />
            </div>
          </div>
          {/* â”€â”€ Azioni Rapide â”€â”€ */}
          <QuickActions
            animateIn={entranceReady}
            animationsEnabled={DASHBOARD_MICROSTEP2_ENABLED}
          />
        </>
      )}

      {/* â”€â”€ Sheet risoluzione inline â”€â”€ */}
      <GhostEventsSheet open={ghostSheetOpen} onOpenChange={setGhostSheetOpen} />
      <ExpiringContractsSheet open={expiringSheetOpen} onOpenChange={setExpiringSheetOpen} />
      <InactiveClientsSheet open={inactiveSheetOpen} onOpenChange={setInactiveSheetOpen} />
    </div>
  );
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// KPI Cards
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

interface KpiDef {
  key: string;
  label: string;
  subtitle: string;
  icon: typeof Users;
  value: number;
  format: "number";
  href: string;
  borderColor: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  valueColor: string;
}

function buildKpiList(summary: DashboardSummary): KpiDef[] {
  return [
    {
      key: "clients",
      label: "Clienti Attivi",
      subtitle: "nel sistema",
      icon: Users,
      value: summary.active_clients,
      format: "number",
      href: "/clienti",
      borderColor: "border-l-blue-500",
      gradient: "from-blue-50/80 to-white dark:from-blue-950/40 dark:to-zinc-900",
      iconBg: "bg-blue-100 dark:bg-blue-900/30",
      iconColor: "text-blue-600 dark:text-blue-400",
      valueColor: "text-blue-700 dark:text-blue-400",
    },
    {
      key: "appointments",
      label: "Appuntamenti Oggi",
      subtitle: "in programma",
      icon: CalendarCheck,
      value: summary.todays_appointments,
      format: "number",
      href: "/agenda",
      borderColor: "border-l-violet-500",
      gradient: "from-violet-50/80 to-white dark:from-violet-950/40 dark:to-zinc-900",
      iconBg: "bg-violet-100 dark:bg-violet-900/30",
      iconColor: "text-violet-600 dark:text-violet-400",
      valueColor: "text-violet-700 dark:text-violet-400",
    },
  ];
}

function KpiCards({
  summary,
  animateIn,
  animationsEnabled,
}: {
  summary: DashboardSummary;
  animateIn: boolean;
  animationsEnabled: boolean;
}) {
  const kpis = buildKpiList(summary);

  return (
    <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4">
      {kpis.map((kpi, index) => {
        const Icon = kpi.icon;
        return (
          <Link
            key={kpi.key}
            href={kpi.href}
            className={`block min-w-0 ${getRevealMotionClass(animationsEnabled, animateIn)}`}
            style={getRevealDelayStyle(animationsEnabled, index * 55)}
          >
            <div
              className={`flex h-full min-w-0 items-start gap-2.5 rounded-xl border border-l-4 ${kpi.borderColor} bg-gradient-to-br ${kpi.gradient} p-3.5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg sm:gap-3 sm:p-4`}
            >
              <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg sm:h-10 sm:w-10 ${kpi.iconBg}`}>
                <Icon className={`h-4 w-4 sm:h-5 sm:w-5 ${kpi.iconColor}`} />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] font-semibold tracking-widest text-muted-foreground/70 uppercase leading-tight sm:text-xs">
                  {kpi.label}
                </p>
                <AnimatedNumber
                  value={kpi.value}
                  format={kpi.format}
                  className={`text-2xl font-extrabold tracking-tighter tabular-nums sm:text-3xl ${kpi.valueColor}`}
                />
                <p className="text-[11px] font-medium text-muted-foreground/60 sm:text-xs">{kpi.subtitle}</p>
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Alert Panel â€” Warning proattivi
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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
      <div id="alert-panel" className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-4 shadow-sm sm:p-5 dark:from-zinc-900 dark:to-zinc-800/50">
        <div className="mb-4 flex items-center gap-2">
          <Skeleton className="h-5 w-5 rounded" />
          <Skeleton className="h-5 w-40" />
        </div>
        <div className="grid gap-2.5 sm:grid-cols-2 sm:gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const visibleAlerts = alerts?.items.filter((item) => item.category !== "overdue_rates") ?? [];
  const criticalCount = visibleAlerts.filter((item) => item.severity === "critical").length;
  const warningCount = visibleAlerts.filter((item) => item.severity === "warning").length;

  if (!alerts || visibleAlerts.length === 0) {
    return (
      <div id="alert-panel" className="rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50/80 to-white p-4 shadow-sm sm:p-5 dark:border-emerald-800/50 dark:from-emerald-950/30 dark:to-zinc-900">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-900/30">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <p className="text-sm font-bold text-emerald-700 dark:text-emerald-400">Nessun alert operativo</p>
            <p className="mt-1 text-xs text-muted-foreground">Tutto sotto controllo. Nessuna azione urgente richiesta.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div id="alert-panel" className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-4 shadow-sm sm:p-5 dark:from-zinc-900 dark:to-zinc-800/50">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="relative">
            <Bell className="h-5 w-5 text-amber-500" />
            <span className="absolute -right-1.5 -top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white shadow-sm">
              {visibleAlerts.length}
            </span>
          </div>
          <h3 className="truncate font-semibold">Alert operativi</h3>
        </div>
        <div className="ml-auto flex flex-wrap items-center justify-end gap-1.5 sm:ml-0">
          {criticalCount > 0 && (
            <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-[10px] font-bold text-red-700 dark:bg-red-900/40 dark:text-red-400">
              {criticalCount} {criticalCount === 1 ? "critico" : "critici"}
            </span>
          )}
          {warningCount > 0 && (
            <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-[10px] font-bold text-amber-700 dark:bg-amber-900/40 dark:text-amber-400">
              {warningCount} {warningCount === 1 ? "avviso" : "avvisi"}
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-2.5 sm:grid-cols-2 sm:gap-3">
        {visibleAlerts.map((item, idx) => {
          const catCfg = ALERT_CATEGORY_CONFIG[item.category] ?? ALERT_CATEGORY_CONFIG.ghost_events;
          const CatIcon = catCfg.icon;
          const isCritical = item.severity === "critical";

          return (
            <div
              key={`${item.category}-${idx}`}
              className={`min-w-0 rounded-xl border border-l-4 ${catCfg.borderColor} p-3 transition-all hover:-translate-y-0.5 hover:shadow-md sm:p-3.5 ${
                isCritical ? "bg-red-50/60 dark:bg-red-950/20" : "bg-white dark:bg-zinc-900"
              }`}
            >
              <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${catCfg.bgColor}`}>
                  <CatIcon className={`h-4 w-4 ${catCfg.color}`} />
                </div>
                <div className="flex items-center gap-1.5">
                  {isCritical && (
                    <Badge variant="destructive" className="h-5 px-1.5 py-0 text-[9px] uppercase">
                      Critico
                    </Badge>
                  )}
                  {!isCritical && (
                    <Badge variant="secondary" className="h-5 px-1.5 py-0 text-[9px] uppercase">
                      Avviso
                    </Badge>
                  )}
                  {item.count > 1 && (
                    <Badge variant="outline" className="h-5 px-1.5 py-0 text-[9px]">
                      x{item.count}
                    </Badge>
                  )}
                </div>
              </div>

              <p className="break-words text-sm font-semibold leading-tight">{item.title}</p>
              <p className="mt-1 break-words text-xs leading-snug text-muted-foreground">{item.detail}</p>

              <div className="mt-3">
                {alertActions[item.category] ? (
                  <Button
                    variant={isCritical ? "default" : "outline"}
                    size="sm"
                    className={`h-9 w-full justify-between gap-1.5 text-xs font-medium sm:h-8 ${
                      isCritical ? "bg-red-600 text-white shadow-sm hover:bg-red-700" : ""
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
                      className={`h-9 w-full justify-between gap-1.5 text-xs font-medium sm:h-8 ${
                        isCritical ? "bg-red-600 text-white shadow-sm hover:bg-red-700" : ""
                      }`}
                    >
                      {catCfg.cta}
                      <ArrowRight className="h-3 w-3" />
                    </Button>
                  </Link>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
interface WeeklyCategoryStat {
  category: string;
  label: string;
  total: number;
  scheduled: number;
  completed: number;
  cancelled: number;
}

function buildWeeklyCategoryStats(events: EventHydrated[]): WeeklyCategoryStat[] {
  const statsMap = new Map<string, WeeklyCategoryStat>();

  WEEKLY_CATEGORY_ORDER.forEach((category) => {
    statsMap.set(category, {
      category,
      label: CATEGORY_LABELS[category] ?? category,
      total: 0,
      scheduled: 0,
      completed: 0,
      cancelled: 0,
    });
  });

  events.forEach((event) => {
    const category = event.categoria ?? "ALTRO";
    const stat = statsMap.get(category) ?? {
      category,
      label: CATEGORY_LABELS[category] ?? category,
      total: 0,
      scheduled: 0,
      completed: 0,
      cancelled: 0,
    };

    stat.total += 1;
    if (event.stato === "Completato") {
      stat.completed += 1;
    } else if (event.stato === "Cancellato") {
      stat.cancelled += 1;
    } else {
      stat.scheduled += 1;
    }

    statsMap.set(category, stat);
  });

  const orderMap = new Map<string, number>(WEEKLY_CATEGORY_ORDER.map((key, index) => [key, index]));
  return Array.from(statsMap.values())
    .filter((stat) => stat.total > 0 || orderMap.has(stat.category))
    .sort((a, b) => {
      if (a.total !== b.total) return b.total - a.total;
      return (orderMap.get(a.category) ?? 99) - (orderMap.get(b.category) ?? 99);
    });
}

function WeeklyLessons({
  events,
  isLoading,
  weekLabel,
}: {
  events: EventHydrated[];
  isLoading: boolean;
  weekLabel: string;
}) {
  if (isLoading) {
    return (
      <div className="space-y-4 rounded-xl border p-4 sm:p-5">
        <Skeleton className="h-5 w-52" />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-[148px] w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const stats = buildWeeklyCategoryStats(events);
  const totalEvents = stats.reduce((acc, item) => acc + item.total, 0);
  const completedEvents = stats.reduce((acc, item) => acc + item.completed, 0);

  return (
    <div className="min-w-0 rounded-xl border bg-gradient-to-br from-white via-white to-zinc-50/60 p-4 shadow-sm sm:p-5 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-800/40">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3 sm:mb-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <CalendarCheck className="h-4 w-4 text-blue-500" />
            <h3 className="text-base font-semibold">Lezioni della settimana</h3>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {weekLabel}
          </p>
        </div>
        <div className="flex w-full flex-wrap items-center justify-start gap-2 sm:w-auto sm:justify-end">
          <div className="rounded-lg border bg-gradient-to-br from-white to-zinc-50 px-3 py-1.5 text-right shadow-sm dark:from-zinc-900 dark:to-zinc-800/60">
            <p className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">Completate</p>
            <p className="text-xl font-extrabold leading-none tabular-nums sm:text-2xl">
              {completedEvents}
              <span className="ml-1 text-xs font-semibold text-muted-foreground sm:text-sm">/ {totalEvents}</span>
            </p>
          </div>
          <Link href="/agenda">
            <Button variant="ghost" size="sm" className="h-8 gap-1 text-xs">
              Apri agenda <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        </div>
      </div>

      {totalEvents === 0 ? (
        <div className="rounded-lg border border-dashed p-4 text-center">
          <p className="text-sm text-muted-foreground">Nessuna lezione pianificata questa settimana</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {stats.map((stat) => {
            const color = CATEGORY_COLORS[stat.category] ?? "bg-zinc-400";
            const theme = WEEKLY_CATEGORY_THEME[stat.category] ?? {
              chip: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
              card: "from-zinc-50/80 to-white dark:from-zinc-900/30 dark:to-zinc-900",
              border: "border-zinc-200/80 dark:border-zinc-800/50",
              total: "text-zinc-700 dark:text-zinc-300",
            };
            return (
              <div
                key={stat.category}
                className={`min-w-0 rounded-xl border bg-gradient-to-br ${theme.card} ${theme.border} p-3.5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md sm:p-4`}
              >
                <div className="mb-2.5 flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
                    <span className={`rounded-md px-2 py-0.5 text-[13px] font-bold tracking-tight ${theme.chip}`}>
                      {stat.label}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">Totale</p>
                    <p className={`text-3xl font-extrabold leading-none tabular-nums ${theme.total}`}>{stat.total}</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-[11px] text-muted-foreground sm:text-xs">
                  <div className="rounded-md border bg-zinc-50 px-2 py-1.5 dark:bg-zinc-800/60">
                    <p className="text-lg font-extrabold leading-none tabular-nums text-zinc-700 sm:text-xl dark:text-zinc-300">{stat.scheduled}</p>
                    <p className="mt-1 font-medium">agenda</p>
                  </div>
                  <div className="rounded-md border bg-emerald-50 px-2 py-1.5 dark:bg-emerald-950/30">
                    <p className="text-lg font-extrabold leading-none tabular-nums text-emerald-600 sm:text-xl dark:text-emerald-400">{stat.completed}</p>
                    <p className="mt-1 font-medium">fatte</p>
                  </div>
                  <div className="rounded-md border bg-red-50 px-2 py-1.5 dark:bg-red-950/30">
                    <p className="text-lg font-extrabold leading-none tabular-nums text-red-500 sm:text-xl">{stat.cancelled}</p>
                    <p className="mt-1 font-medium">cancel.</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

interface AgendaLiveInfo {
  mode: "in_progress" | "next_up" | "free";
  event: EventHydrated | null;
  remainingMs: number;
}

function buildAgendaLiveInfo(events: EventHydrated[], currentTime: Date): AgendaLiveInfo {
  const nowTs = currentTime.getTime();
  const actionableEvents = events.filter(
    (event) => event.stato !== "Cancellato" && event.stato !== "Completato",
  );

  const currentEvent = actionableEvents.find(
    (event) => event.data_inizio.getTime() <= nowTs && nowTs < event.data_fine.getTime(),
  );
  if (currentEvent) {
    return {
      mode: "in_progress",
      event: currentEvent,
      remainingMs: Math.max(0, currentEvent.data_fine.getTime() - nowTs),
    };
  }

  const nextEvent = actionableEvents.find((event) => event.data_inizio.getTime() > nowTs);
  if (nextEvent) {
    return {
      mode: "next_up",
      event: nextEvent,
      remainingMs: Math.max(0, nextEvent.data_inizio.getTime() - nowTs),
    };
  }

  return { mode: "free", event: null, remainingMs: 0 };
}

function formatCountdown(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map((value) => String(value).padStart(2, "0")).join(":");
}

function TodayAgenda({
  events,
  isLoading,
  referenceDate,
  animateIn,
  animationsEnabled,
}: {
  events: EventHydrated[];
  isLoading: boolean;
  referenceDate: Date;
  animateIn: boolean;
  animationsEnabled: boolean;
}) {
  const updateEvent = useUpdateEvent();
  const [clockTime, setClockTime] = useState(() => new Date());
  const [updatingEventId, setUpdatingEventId] = useState<number | null>(null);

  useEffect(() => {
    const timerId = window.setInterval(() => setClockTime(new Date()), 1000);
    return () => window.clearInterval(timerId);
  }, []);

  const handleStatusChange = useCallback((event: EventHydrated, nextStatus: string) => {
    if (event.stato === nextStatus) return;
    setUpdatingEventId(event.id);
    updateEvent.mutate(
      { id: event.id, stato: nextStatus },
      {
        onSettled: () => {
          setUpdatingEventId((current) => (current === event.id ? null : current));
        },
      },
    );
  }, [updateEvent]);

  const liveInfo = useMemo(
    () => buildAgendaLiveInfo(events, clockTime),
    [events, clockTime],
  );

  if (isLoading) {
    return (
      <div className="h-[520px] space-y-3 rounded-2xl border p-4 sm:p-5">
        <Skeleton className="h-6 w-52" />
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-8 w-full rounded-lg" />
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  const todayFormatted = referenceDate.toLocaleDateString("it-IT", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
  const nowLabel = clockTime.toLocaleTimeString("it-IT", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const nextCountdown = formatCountdown(liveInfo.remainingMs);
  const statusBadge = liveInfo.mode === "in_progress"
    ? "Occupato"
    : liveInfo.mode === "next_up"
      ? "In arrivo"
      : "Libero";
  const statusTitle = liveInfo.mode === "in_progress"
    ? "Sessione in corso"
    : liveInfo.mode === "next_up"
      ? "Prossima sessione"
      : "Finestra libera";
  const statusTone = liveInfo.mode === "in_progress"
    ? "border-amber-200 bg-amber-50/80 text-amber-700 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-300"
    : liveInfo.mode === "next_up"
      ? "border-blue-200 bg-blue-50/80 text-blue-700 dark:border-blue-900/40 dark:bg-blue-950/20 dark:text-blue-300"
      : "border-zinc-200 bg-zinc-50/80 text-zinc-700 dark:border-zinc-800/70 dark:bg-zinc-900/60 dark:text-zinc-300";

  return (
    <div
      className={`flex h-[520px] min-w-0 flex-col rounded-2xl border bg-gradient-to-br from-white via-white to-zinc-50/70 p-4 shadow-sm sm:p-5 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-800/50 ${getRevealMotionClass(
        animationsEnabled,
        animateIn,
      )}`}
      style={getRevealDelayStyle(animationsEnabled, 170)}
    >
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex min-w-0 items-center gap-2">
            <Clock className="h-4 w-4 text-blue-500" />
            <h3 className="truncate text-sm font-semibold sm:text-base">Operativita giornata</h3>
          </div>
          <p className="mt-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground sm:text-xs">
            {todayFormatted}
          </p>
        </div>
        <Link href="/agenda" className="shrink-0">
          <Button variant="outline" size="sm" className="h-8 gap-1 text-xs">
            Agenda completa <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
      </div>

      <div className="mb-3 grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-2.5">
        <div className="rounded-xl border bg-white/90 px-3 py-2 shadow-sm dark:bg-zinc-900/90">
          <p className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">Ora</p>
          <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-zinc-800 dark:text-zinc-100">
            {nowLabel}
          </p>
        </div>
        <div className={`rounded-xl border px-3 py-2 ${statusTone}`}>
          <p className="text-[10px] font-semibold tracking-wide uppercase">Stato live</p>
          <p className="mt-1 text-sm font-bold">{statusTitle}</p>
          <p className="mt-1 text-xs font-medium tabular-nums">
            {liveInfo.mode === "free"
              ? "Nessun countdown attivo"
              : `${liveInfo.mode === "in_progress" ? "Fine tra" : "Inizio tra"} ${nextCountdown}`}
          </p>
        </div>
      </div>

      <div className="mb-3 flex items-center justify-between rounded-xl border bg-zinc-50/80 px-3 py-2 dark:bg-zinc-900/60">
        <div>
          <p className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">Sedute programmate</p>
          <p className="text-sm font-semibold">{events.length}</p>
        </div>
        <Badge variant="secondary" className="text-[10px] font-semibold uppercase tracking-wide">
          {statusBadge}
        </Badge>
      </div>

      {events.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-6 text-center">
          <CalendarCheck className="h-8 w-8 text-muted-foreground/30" />
          <p className="text-sm text-muted-foreground">Nessun appuntamento oggi</p>
          <p className="text-xs text-muted-foreground/70">La giornata e libera</p>
        </div>
      ) : (
        <ScrollArea className="min-h-0 flex-1 pr-1">
          <div className="space-y-2">
            {events.map((event, index) => {
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
              const timeTone = event.stato === "Completato"
                ? "border-emerald-200 bg-emerald-50/80 dark:border-emerald-900/40 dark:bg-emerald-950/20"
                : "border-violet-200 bg-violet-50/80 dark:border-violet-900/40 dark:bg-violet-950/20";

              return (
                <div
                  key={event.id}
                  className={getRevealMotionClass(animationsEnabled, animateIn)}
                  style={getRevealDelayStyle(animationsEnabled, 210 + Math.min(index, 6) * 35)}
                >
                  <div className="grid min-w-0 grid-cols-[84px_minmax(0,1fr)] items-center gap-2 rounded-xl border bg-white p-2.5 transition-all hover:-translate-y-0.5 hover:shadow-sm md:grid-cols-[88px_minmax(0,1fr)_auto] dark:bg-zinc-900">
                    <div className={`rounded-lg border px-1.5 py-1 text-center ${timeTone}`}>
                      <p className="text-lg font-extrabold leading-none tabular-nums text-zinc-800 dark:text-zinc-100">{time}</p>
                      <p className="mt-1 text-[11px] font-medium tabular-nums text-muted-foreground">{endTime}</p>
                    </div>

                    <div className="min-w-0">
                      <div className="flex min-w-0 items-center gap-2">
                        <span className={`h-2.5 w-2.5 rounded-full ${catColor}`} />
                        <p className={`min-w-0 flex-1 truncate text-sm font-semibold leading-tight ${statusColor}`}>
                          {event.titolo || event.categoria}
                        </p>
                        <Badge variant="outline" className="h-5 shrink-0 px-1.5 py-0 text-[10px] font-semibold md:hidden">
                          {event.categoria}
                        </Badge>
                      </div>
                      {event.cliente_nome ? (
                        <p className="mt-1 truncate text-xs text-muted-foreground">
                          {event.cliente_nome} {event.cliente_cognome}
                        </p>
                      ) : event.note ? (
                        <p className="mt-1 truncate text-xs text-muted-foreground">{event.note}</p>
                      ) : (
                        <p className="mt-1 text-xs text-muted-foreground/60">Nessuna nota</p>
                      )}
                    </div>

                    <div className="md:hidden">
                      <Select
                        value={event.stato}
                        onValueChange={(value) => handleStatusChange(event, value)}
                        disabled={updatingEventId === event.id}
                      >
                        <SelectTrigger className="h-8 w-full text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {EVENT_STATUSES.map((status) => (
                            <SelectItem key={status} value={status} className="text-xs">
                              {status}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="hidden shrink-0 md:flex md:flex-col md:items-end md:gap-1.5">
                      <Badge variant="outline" className="px-2 py-0.5 text-[10px] font-semibold">
                        {event.categoria}
                      </Badge>
                      <Select
                        value={event.stato}
                        onValueChange={(value) => handleStatusChange(event, value)}
                        disabled={updatingEventId === event.id}
                      >
                        <SelectTrigger className="h-8 w-[126px] text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {EVENT_STATUSES.map((status) => (
                            <SelectItem key={status} value={status} className="text-xs">
                              {status}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {updatingEventId === event.id && (
                        <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          Aggiorno...
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

const QUICK_ACTIONS = [
  {
    label: "Nuovo Cliente",
    icon: UserPlus,
    href: "/clienti?new=1",
    gradient: "from-blue-50 to-blue-100/50 dark:from-blue-950/30 dark:to-zinc-900",
    iconColor: "text-blue-600 dark:text-blue-400",
    border: "border-blue-200 dark:border-blue-800/50",
  },
  {
    label: "Nuovo Contratto",
    icon: FileText,
    href: "/contratti?new=1",
    gradient: "from-violet-50 to-violet-100/50 dark:from-violet-950/30 dark:to-zinc-900",
    iconColor: "text-violet-600 dark:text-violet-400",
    border: "border-violet-200 dark:border-violet-800/50",
  },
  {
    label: "Nuova Scheda",
    icon: Rocket,
    href: "/schede",
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

function QuickActions({
  animateIn,
  animationsEnabled,
}: {
  animateIn: boolean;
  animationsEnabled: boolean;
}) {
  return (
    <div className="min-w-0">
      <p className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Azioni rapide
      </p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {QUICK_ACTIONS.map((action, index) => {
          const Icon = action.icon;
          return (
            <Link
              key={action.label}
              href={action.href}
              className={`block min-w-0 ${getRevealMotionClass(animationsEnabled, animateIn)}`}
              style={getRevealDelayStyle(animationsEnabled, 260 + index * 45)}
            >
              <div className={`flex min-w-0 items-center gap-2.5 rounded-xl border ${action.border} bg-gradient-to-br ${action.gradient} p-3 transition-all hover:-translate-y-0.5 hover:shadow-md sm:gap-3 sm:p-4`}>
                <Icon className={`h-5 w-5 ${action.iconColor}`} />
                <span className="min-w-0 text-sm font-medium leading-tight">{action.label}</span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Welcome Card (first-run)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

const FIRST_STEPS = [
  {
    label: "Aggiungi il primo cliente",
    description: "Inserisci nome, contatti e anamnesi",
    icon: UserPlus,
    href: "/clienti?new=1",
    gradient: "from-blue-50 to-blue-100/50 dark:from-blue-950/30 dark:to-zinc-900",
    iconColor: "text-blue-600 dark:text-blue-400",
    border: "border-blue-200 dark:border-blue-800/50",
  },
  {
    label: "Crea un contratto",
    description: "Pacchetto, prezzo e piano rate",
    icon: FileText,
    href: "/contratti?new=1",
    gradient: "from-emerald-50 to-emerald-100/50 dark:from-emerald-950/30 dark:to-zinc-900",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    border: "border-emerald-200 dark:border-emerald-800/50",
  },
  {
    label: "Pianifica un appuntamento",
    description: "Agenda con drag & drop",
    icon: Calendar,
    href: "/agenda",
    gradient: "from-amber-50 to-amber-100/50 dark:from-amber-950/30 dark:to-zinc-900",
    iconColor: "text-amber-600 dark:text-amber-400",
    border: "border-amber-200 dark:border-amber-800/50",
  },
  {
    label: "Esplora gli esercizi",
    description: "269 esercizi con tassonomia scientifica",
    icon: Rocket,
    href: "/esercizi",
    gradient: "from-violet-50 to-violet-100/50 dark:from-violet-950/30 dark:to-zinc-900",
    iconColor: "text-violet-600 dark:text-violet-400",
    border: "border-violet-200 dark:border-violet-800/50",
  },
] as const;

function WelcomeCard() {
  return (
    <div className="space-y-5 md:space-y-6">
      {/* Hero welcome */}
      <div className="relative overflow-hidden rounded-2xl border border-primary/20 bg-gradient-to-br from-primary/5 via-background to-primary/10 p-6 sm:p-8">
        <div className="pointer-events-none absolute -right-12 -top-12 h-48 w-48 rounded-full bg-primary/5 blur-3xl" />
        <div className="relative flex flex-col items-center text-center sm:items-start sm:text-left">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-primary/10">
            <Sparkles className="h-7 w-7 text-primary" />
          </div>
          <h2 className="text-xl font-bold tracking-tight sm:text-2xl">
            Benvenuto in FitManager AI Studio
          </h2>
          <p className="mt-2 max-w-lg text-sm text-muted-foreground">
            Il tuo gestionale fitness e&apos; pronto. Inizia aggiungendo il primo cliente
            per sbloccare tutte le funzionalita&apos;: contratti, agenda, schede allenamento,
            analisi cliniche e molto altro.
          </p>
        </div>
      </div>

      {/* First steps grid */}
      <div>
        <p className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          Primi passi
        </p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {FIRST_STEPS.map((step) => {
            const Icon = step.icon;
            return (
              <Link key={step.label} href={step.href}>
                <div className={`group flex flex-col gap-2 rounded-xl border ${step.border} bg-gradient-to-br ${step.gradient} p-4 transition-all hover:shadow-md hover:-translate-y-0.5`}>
                  <div className="flex items-center gap-3">
                    <Icon className={`h-5 w-5 ${step.iconColor}`} />
                    <span className="text-sm font-medium">{step.label}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{step.description}</p>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Skeleton
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

function KpiSkeleton() {
  const borders = [
    "border-l-blue-500",
    "border-l-violet-500",
  ];
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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


