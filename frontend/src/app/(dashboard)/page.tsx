// src/app/(dashboard)/page.tsx
"use client";

/**
 * Dashboard — Command Center operativo:
 *
 * 1. Greeting Header personalizzato (time-aware)
 * 2. 4 KPI card: Clienti, Sedute Oggi, Sedute Settimana (delta), Alert Attivi
 * 3. Agenda Oggi + Grafico Settimanale (stacked BarChart)
 * 4. Todo + Alert Panel
 * 5. Azioni rapide
 *
 * Privacy-first: zero dati finanziari.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Users,
  CalendarCheck,
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
  TrendingUp,
  TrendingDown,
  BarChart3,
  ShieldAlert,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  ReferenceArea,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useDashboard, useDashboardAlerts, useClinicalReadiness } from "@/hooks/useDashboard";
import { useEvents, useUpdateEvent, type EventHydrated } from "@/hooks/useAgenda";
import { AnimatedNumber } from "@/components/ui/animated-number";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart";
import { GhostEventsSheet } from "@/components/dashboard/GhostEventsSheet";
import { ExpiringContractsSheet } from "@/components/dashboard/ExpiringContractsSheet";
import { InactiveClientsSheet } from "@/components/dashboard/InactiveClientsSheet";
import { TodoCard } from "@/components/dashboard/TodoCard";
import { getStoredTrainer } from "@/lib/auth";
import {
  EVENT_STATUSES,
  type DashboardSummary,
  type DashboardAlerts,
  type ClinicalReadinessResponse,
  type ClinicalReadinessClientItem,
} from "@/types/api";
import { getRevealClass, getRevealStyle } from "@/lib/page-reveal";

// ── Date helpers ──

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

function prevWeekStartISO(baseDate: Date = new Date()): string {
  const date = weekStartDate(baseDate);
  date.setDate(date.getDate() - 7);
  return formatLocalISODate(date);
}

function currentWeekLabel(baseDate: Date = new Date()): string {
  const start = weekStartDate(baseDate);
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  const formatOptions: Intl.DateTimeFormatOptions = { day: "2-digit", month: "short" };
  return `${start.toLocaleDateString("it-IT", formatOptions)} - ${end.toLocaleDateString("it-IT", formatOptions)}`;
}

// ── Greeting helpers ──

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 13) return "Buongiorno";
  if (hour < 18) return "Buon pomeriggio";
  return "Buonasera";
}

function buildSummaryLine(
  todayCount: number,
  alertCount: number,
  dateAnchor: Date,
): string {
  const parts: string[] = [];
  if (todayCount > 0) {
    parts.push(`${todayCount} ${todayCount === 1 ? "appuntamento" : "appuntamenti"} oggi`);
  }
  if (alertCount > 0) {
    parts.push(`${alertCount} ${alertCount === 1 ? "alert attivo" : "alert attivi"}`);
  }
  const dateStr = dateAnchor.toLocaleDateString("it-IT", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  return parts.length > 0 ? `${parts.join(", ")} \u2014 ${dateStr}` : dateStr;
}

// ── Category colors (mirror agenda) ──

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

// ── Chart config ──

const CHART_CATEGORY_FILLS: Record<string, string> = {
  PT: "var(--color-blue-500)",
  SALA: "var(--color-emerald-500)",
  CORSO: "var(--color-violet-500)",
  COLLOQUIO: "var(--color-amber-500)",
  PERSONALE: "var(--color-pink-500)",
};

const weeklyChartConfig: ChartConfig = {
  PT: { label: "PT", color: "var(--color-blue-500)" },
  SALA: { label: "Sala", color: "var(--color-emerald-500)" },
  CORSO: { label: "Corso", color: "var(--color-violet-500)" },
  COLLOQUIO: { label: "Colloquio", color: "var(--color-amber-500)" },
  PERSONALE: { label: "Personale", color: "var(--color-pink-500)" },
};

const DAY_LABELS = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"] as const;

interface ChartDayData {
  day: string;
  PT: number;
  SALA: number;
  CORSO: number;
  COLLOQUIO: number;
  PERSONALE: number;
  total: number;
  isToday: boolean;
}

function buildWeeklyChartData(events: EventHydrated[], baseDate: Date): ChartDayData[] {
  const monday = weekStartDate(baseDate);
  const todayDayIndex = Math.floor(
    (new Date().setHours(0, 0, 0, 0) - monday.getTime()) / (1000 * 60 * 60 * 24),
  );
  const result: ChartDayData[] = DAY_LABELS.map((label, idx) => ({
    day: label,
    PT: 0,
    SALA: 0,
    CORSO: 0,
    COLLOQUIO: 0,
    PERSONALE: 0,
    total: 0,
    isToday: idx === todayDayIndex,
  }));

  events.forEach((event) => {
    if (event.stato === "Cancellato") return;
    const dayIndex = Math.floor(
      (event.data_inizio.getTime() - monday.getTime()) / (1000 * 60 * 60 * 24),
    );
    if (dayIndex < 0 || dayIndex > 6) return;
    const category = event.categoria ?? "PERSONALE";
    const key = category as keyof Omit<ChartDayData, "day" | "total" | "isToday">;
    if (key in result[dayIndex]) {
      result[dayIndex][key] += 1;
    }
    result[dayIndex].total += 1;
  });

  return result;
}

// ── Status colors (agenda) ──

const STATUS_COLORS: Record<string, string> = {
  Programmato: "text-blue-600 dark:text-blue-400",
  Completato: "text-emerald-600 dark:text-emerald-400",
  Cancellato: "text-red-400 line-through",
  Rinviato: "text-amber-600 dark:text-amber-400",
};

// POC toggle: disattiva in un punto unico per rollback veloce.
const DASHBOARD_MICROSTEP2_ENABLED = true;

function getRevealMotionClass(_enabled: boolean, ready: boolean): string {
  return getRevealClass(ready);
}

function getRevealDelayStyle(_enabled: boolean, delayMs: number) {
  return getRevealStyle(delayMs);
}

// ════════════════════════════════════════════════════════════
// Pagina
// ════════════════════════════════════════════════════════════

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading, isError, refetch } = useDashboard();
  const { data: alerts } = useDashboardAlerts();
  const { data: clinicalReadiness, isLoading: clinicalReadinessLoading } = useClinicalReadiness();
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
  const previousWeekStart = useMemo(() => prevWeekStartISO(dateAnchor), [dateAnchor]);
  const currentWeekRangeLabel = useMemo(() => currentWeekLabel(dateAnchor), [dateAnchor]);

  const { data: eventsData } = useEvents({ start: currentDayStart, end: nextDayStart });
  const { data: weeklyEventsData } = useEvents({ start: currentWeekStart, end: nextWeekStart });
  const { data: prevWeekEventsData } = useEvents({ start: previousWeekStart, end: currentWeekStart });

  // Trainer name for greeting
  const trainerName = useMemo(() => {
    const trainer = getStoredTrainer();
    return trainer?.nome ?? null;
  }, []);

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

  const prevWeekEvents = useMemo(() => {
    if (!prevWeekEventsData?.items) return [];
    return prevWeekEventsData.items.filter((e) => e.stato !== "Cancellato");
  }, [prevWeekEventsData]);

  // Computed KPI values
  const weeklySessionCount = weeklyEvents.filter((e) => e.stato !== "Cancellato").length;
  const prevWeekSessionCount = prevWeekEvents.length;
  const weeklyDelta = weeklySessionCount - prevWeekSessionCount;

  const visibleAlerts = useMemo(
    () => alerts?.items.filter((item) => item.category !== "overdue_rates") ?? [],
    [alerts],
  );
  const totalAlertCount = visibleAlerts.length;
  const criticalAlertCount = visibleAlerts.filter((item) => item.severity === "critical").length;
  const warningAlertCount = visibleAlerts.filter((item) => item.severity === "warning").length;
  const upcomingSessionsCount = todayEvents.filter(
    (event) => event.stato === "Programmato",
  ).length;

  const isLoading = summaryLoading;

  // Chart data
  const chartData = useMemo(
    () => buildWeeklyChartData(weeklyEvents, dateAnchor),
    [weeklyEvents, dateAnchor],
  );
  const completedEvents = weeklyEvents.filter((e) => e.stato === "Completato").length;

  // Handler CTA per categoria alert
  const alertActions: Record<string, () => void> = {
    ghost_events: () => setGhostSheetOpen(true),
    expiring_contracts: () => setExpiringSheetOpen(true),
    inactive_clients: () => setInactiveSheetOpen(true),
  };

  return (
    <div className="min-w-0 space-y-4 md:space-y-6">
      {/* ── Greeting Header ── */}
      <div
        data-guide="dashboard-header"
        className={`flex flex-col gap-1 ${getRevealMotionClass(DASHBOARD_MICROSTEP2_ENABLED, entranceReady)}`}
        style={getRevealDelayStyle(DASHBOARD_MICROSTEP2_ENABLED, 0)}
      >
        <h1 className="text-xl font-bold tracking-tight sm:text-2xl">
          {getGreeting()}{trainerName ? `, ${trainerName}` : ""}
        </h1>
        <p className="text-xs text-muted-foreground sm:text-sm">
          {buildSummaryLine(
            summary?.todays_appointments ?? todayEvents.length,
            totalAlertCount,
            dateAnchor,
          )}
        </p>
      </div>

      {/* ── Error state ── */}
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

      {/* ── First-run welcome (zero clienti) ── */}
      {!isLoading && summary && summary.active_clients === 0 ? (
        <WelcomeCard />
      ) : (
        <>
          {/* ── Hero KPI ── */}
          {isLoading && <DashboardSkeleton />}
          {summary && (
            <KpiCards
              summary={summary}
              weeklySessionCount={weeklySessionCount}
              weeklyDelta={weeklyDelta}
              totalAlertCount={totalAlertCount}
              criticalAlertCount={criticalAlertCount}
              animateIn={entranceReady}
              animationsEnabled={DASHBOARD_MICROSTEP2_ENABLED}
            />
          )}

          {/* ── Row 1: Agenda + Promemoria (post-it) ── */}
          <div className="grid min-w-0 gap-4 md:gap-5 xl:grid-cols-2">
            <div
              className={`min-w-0 ${getRevealMotionClass(DASHBOARD_MICROSTEP2_ENABLED, entranceReady)}`}
              style={getRevealDelayStyle(DASHBOARD_MICROSTEP2_ENABLED, 200)}
            >
              <TodayAgenda
                events={todayEvents}
                isLoading={!eventsData}
                referenceDate={dateAnchor}
                animateIn={entranceReady}
                animationsEnabled={DASHBOARD_MICROSTEP2_ENABLED}
              />
            </div>
            <div
              className={`min-w-0 ${getRevealMotionClass(DASHBOARD_MICROSTEP2_ENABLED, entranceReady)}`}
              style={getRevealDelayStyle(DASHBOARD_MICROSTEP2_ENABLED, 240)}
            >
              <TodoCard
                criticalAlertCount={criticalAlertCount}
                warningAlertCount={warningAlertCount}
                upcomingSessionsCount={upcomingSessionsCount}
              />
            </div>
          </div>

          {/* ── Row 2: Chart + Alert ── */}
          <div className="grid min-w-0 gap-4 md:gap-5 xl:grid-cols-2">
            <div
              className={`min-w-0 ${getRevealMotionClass(DASHBOARD_MICROSTEP2_ENABLED, entranceReady)}`}
              style={getRevealDelayStyle(DASHBOARD_MICROSTEP2_ENABLED, 280)}
            >
              <WeeklySessionsChart
                chartData={chartData}
                weekLabel={currentWeekRangeLabel}
                completedCount={completedEvents}
                totalCount={weeklySessionCount}
                isLoading={!weeklyEventsData}
              />
            </div>
            <div
              className={`min-w-0 ${getRevealMotionClass(DASHBOARD_MICROSTEP2_ENABLED, entranceReady)}`}
              style={getRevealDelayStyle(DASHBOARD_MICROSTEP2_ENABLED, 320)}
            >
              <AlertPanel alerts={alerts} isLoading={!alerts} alertActions={alertActions} />
            </div>
          </div>

          {/* Row 3: Clinical Readiness Queue */}
          <div
            className={getRevealMotionClass(DASHBOARD_MICROSTEP2_ENABLED, entranceReady)}
            style={getRevealDelayStyle(DASHBOARD_MICROSTEP2_ENABLED, 360)}
          >
            <ClinicalReadinessPanel
              readiness={clinicalReadiness}
              isLoading={clinicalReadinessLoading}
            />
          </div>

          {/* Azioni Rapide */}
          <QuickActions
            animateIn={entranceReady}
            animationsEnabled={DASHBOARD_MICROSTEP2_ENABLED}
          />
        </>
      )}

      {/* ── Sheet risoluzione inline ── */}
      <GhostEventsSheet open={ghostSheetOpen} onOpenChange={setGhostSheetOpen} />
      <ExpiringContractsSheet open={expiringSheetOpen} onOpenChange={setExpiringSheetOpen} />
      <InactiveClientsSheet open={inactiveSheetOpen} onOpenChange={setInactiveSheetOpen} />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// KPI Cards
// ════════════════════════════════════════════════════════════

interface KpiDef {
  key: string;
  label: string;
  subtitle: string;
  icon: typeof Users;
  value: number;
  format: "number";
  href?: string;
  scrollTo?: string;
  borderColor: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  valueColor: string;
  delta?: number;
}

function buildKpiList(
  summary: DashboardSummary,
  weeklySessionCount: number,
  weeklyDelta: number,
  totalAlertCount: number,
  criticalAlertCount: number,
): KpiDef[] {
  // Alert KPI: colore dinamico in base a severita
  let alertBorder = "border-l-emerald-500";
  let alertGradient = "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900";
  let alertIconBg = "bg-emerald-100 dark:bg-emerald-900/30";
  let alertIconColor = "text-emerald-600 dark:text-emerald-400";
  let alertValueColor = "text-emerald-700 dark:text-emerald-400";

  if (criticalAlertCount > 0) {
    alertBorder = "border-l-red-500";
    alertGradient = "from-red-50/80 to-white dark:from-red-950/40 dark:to-zinc-900";
    alertIconBg = "bg-red-100 dark:bg-red-900/30";
    alertIconColor = "text-red-600 dark:text-red-400";
    alertValueColor = "text-red-700 dark:text-red-400";
  } else if (totalAlertCount > 0) {
    alertBorder = "border-l-amber-500";
    alertGradient = "from-amber-50/80 to-white dark:from-amber-950/40 dark:to-zinc-900";
    alertIconBg = "bg-amber-100 dark:bg-amber-900/30";
    alertIconColor = "text-amber-600 dark:text-amber-400";
    alertValueColor = "text-amber-700 dark:text-amber-400";
  }

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
      label: "Sedute Oggi",
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
    {
      key: "weekly",
      label: "Sedute Settimana",
      subtitle: "attivita corrente",
      icon: BarChart3,
      value: weeklySessionCount,
      format: "number",
      href: "/agenda",
      borderColor: "border-l-emerald-500",
      gradient: "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900",
      iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
      iconColor: "text-emerald-600 dark:text-emerald-400",
      valueColor: "text-emerald-700 dark:text-emerald-400",
      delta: weeklyDelta,
    },
    {
      key: "alerts",
      label: "Alert Attivi",
      subtitle: totalAlertCount === 0 ? "tutto ok" : "richiedono attenzione",
      icon: ShieldAlert,
      value: totalAlertCount,
      format: "number",
      scrollTo: "#alert-panel",
      borderColor: alertBorder,
      gradient: alertGradient,
      iconBg: alertIconBg,
      iconColor: alertIconColor,
      valueColor: alertValueColor,
    },
  ];
}

function KpiCards({
  summary,
  weeklySessionCount,
  weeklyDelta,
  totalAlertCount,
  criticalAlertCount,
  animateIn,
  animationsEnabled,
}: {
  summary: DashboardSummary;
  weeklySessionCount: number;
  weeklyDelta: number;
  totalAlertCount: number;
  criticalAlertCount: number;
  animateIn: boolean;
  animationsEnabled: boolean;
}) {
  const kpis = buildKpiList(summary, weeklySessionCount, weeklyDelta, totalAlertCount, criticalAlertCount);

  return (
    <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 sm:gap-4">
      {kpis.map((kpi, index) => {
        const Icon = kpi.icon;

        const inner = (
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
              <div className="flex items-baseline gap-2">
                <AnimatedNumber
                  value={kpi.value}
                  format={kpi.format}
                  className={`text-2xl font-extrabold tracking-tighter tabular-nums sm:text-3xl ${kpi.valueColor}`}
                />
                {kpi.delta !== undefined && kpi.delta !== 0 && (
                  <span
                    className={`inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[11px] font-bold tabular-nums ${
                      kpi.delta > 0
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400"
                        : "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400"
                    }`}
                  >
                    {kpi.delta > 0 ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : (
                      <TrendingDown className="h-3 w-3" />
                    )}
                    {kpi.delta > 0 ? `+${kpi.delta}` : kpi.delta}
                  </span>
                )}
              </div>
              <p className="text-[11px] font-medium text-muted-foreground/60 sm:text-xs">{kpi.subtitle}</p>
            </div>
          </div>
        );

        if (kpi.scrollTo) {
          return (
            <button
              key={kpi.key}
              type="button"
              onClick={() => document.querySelector(kpi.scrollTo!)?.scrollIntoView({ behavior: "smooth" })}
              className={`block min-w-0 text-left ${getRevealMotionClass(animationsEnabled, animateIn)}`}
              style={getRevealDelayStyle(animationsEnabled, 40 + index * 40)}
            >
              {inner}
            </button>
          );
        }

        return (
          <Link
            key={kpi.key}
            href={kpi.href!}
            className={`block min-w-0 ${getRevealMotionClass(animationsEnabled, animateIn)}`}
            style={getRevealDelayStyle(animationsEnabled, 40 + index * 40)}
          >
            {inner}
          </Link>
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Weekly Sessions Chart
// ════════════════════════════════════════════════════════════

function WeeklySessionsChart({
  chartData,
  weekLabel,
  completedCount,
  totalCount,
  isLoading,
}: {
  chartData: ChartDayData[];
  weekLabel: string;
  completedCount: number;
  totalCount: number;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="flex h-[480px] flex-col rounded-2xl border p-4 sm:p-5">
        <Skeleton className="mb-4 h-5 w-52" />
        <Skeleton className="flex-1 w-full rounded-xl" />
      </div>
    );
  }

  const hasData = totalCount > 0;
  const activeCategories = (["PT", "SALA", "CORSO", "COLLOQUIO", "PERSONALE"] as const).filter(
    (cat) => chartData.some((d) => d[cat] > 0),
  );

  return (
    <div className="flex h-[480px] min-w-0 flex-col rounded-2xl border bg-gradient-to-br from-white via-white to-zinc-50/70 p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04),_0_4px_12px_rgba(0,0,0,0.03)] sm:p-5 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-800/50">
      {/* Header */}
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900/30 dark:to-teal-900/30">
              <BarChart3 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <h3 className="truncate text-sm font-bold sm:text-base">Sedute della settimana</h3>
              <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
                {weekLabel}
              </p>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {hasData && (
            <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/80 px-3.5 py-2 text-right shadow-sm dark:from-zinc-900 dark:to-zinc-800/60">
              <p className="text-[9px] font-bold tracking-widest text-muted-foreground/70 uppercase">Completate</p>
              <p className="text-xl font-extrabold leading-none tabular-nums tracking-tight sm:text-2xl">
                {completedCount}
                <span className="ml-1 text-xs font-semibold text-muted-foreground/60 sm:text-sm">/ {totalCount}</span>
              </p>
            </div>
          )}
          <Link href="/agenda">
            <Button variant="ghost" size="sm" className="h-8 gap-1 text-xs text-muted-foreground hover:text-foreground">
              Agenda <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        </div>
      </div>

      {!hasData ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-muted-foreground/15 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted/50">
            <CalendarCheck className="h-6 w-6 text-muted-foreground/30" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">Nessuna seduta pianificata questa settimana</p>
          <p className="text-xs text-muted-foreground/60">Pianifica appuntamenti dall&apos;agenda</p>
        </div>
      ) : (
        <div className="min-h-0 flex-1">
          <ChartContainer config={weeklyChartConfig} className="h-full w-full">
            <BarChart data={chartData} accessibilityLayer barGap={2} barCategoryGap="20%">
              <defs>
                <linearGradient id="chartGridGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--color-muted-foreground)" stopOpacity={0.06} />
                  <stop offset="100%" stopColor="var(--color-muted-foreground)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid
                vertical={false}
                stroke="var(--color-muted-foreground)"
                strokeOpacity={0.08}
                strokeDasharray="4 6"
              />
              {/* Today highlight band */}
              {chartData.map((d, idx) =>
                d.isToday ? (
                  <ReferenceArea
                    key={`today-${idx}`}
                    x1={d.day}
                    x2={d.day}
                    fill="var(--color-primary)"
                    fillOpacity={0.04}
                    stroke="var(--color-primary)"
                    strokeOpacity={0.12}
                    strokeDasharray="3 3"
                  />
                ) : null,
              )}
              <XAxis
                dataKey="day"
                tickLine={false}
                axisLine={false}
                tickMargin={10}
                fontSize={12}
                fontWeight={500}
                tick={({ x, y, payload }) => {
                  const entry = chartData.find((d) => d.day === payload.value);
                  const isTodayTick = entry?.isToday ?? false;
                  return (
                    <g transform={`translate(${x},${y})`}>
                      <text
                        x={0}
                        y={0}
                        dy={4}
                        textAnchor="middle"
                        fontSize={12}
                        fontWeight={isTodayTick ? 700 : 500}
                        fill={isTodayTick ? "var(--color-primary)" : "var(--color-muted-foreground)"}
                      >
                        {payload.value}
                      </text>
                      {isTodayTick && (
                        <circle cx={0} cy={12} r={2} fill="var(--color-primary)" />
                      )}
                    </g>
                  );
                }}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tickMargin={4}
                fontSize={11}
                allowDecimals={false}
                stroke="var(--color-muted-foreground)"
                strokeOpacity={0.5}
              />
              <ChartTooltip
                cursor={{ fill: "var(--color-muted)", opacity: 0.15, radius: 6 }}
                content={({ payload, label }) => {
                  if (!payload?.length) return null;
                  const dayTotal = payload.reduce((sum, entry) => sum + (Number(entry.value) || 0), 0);
                  const entry = chartData.find((d) => d.day === label);
                  const isTodayTooltip = entry?.isToday ?? false;
                  return (
                    <div className="overflow-hidden rounded-xl border bg-white/95 shadow-lg backdrop-blur-sm dark:bg-zinc-900/95">
                      <div className={`px-3.5 py-2 ${isTodayTooltip ? "bg-primary/5" : "bg-muted/30"}`}>
                        <p className="text-xs font-bold tracking-wide">
                          {label}
                          {isTodayTooltip && <span className="ml-1.5 text-[10px] font-semibold text-primary">(oggi)</span>}
                        </p>
                      </div>
                      <div className="space-y-1 px-3.5 py-2.5">
                        {payload
                          .filter((pEntry) => Number(pEntry.value) > 0)
                          .map((pEntry) => (
                            <div key={pEntry.name} className="flex items-center gap-2.5 text-sm">
                              <div
                                className="h-3 w-3 rounded-[3px] shadow-sm"
                                style={{ backgroundColor: pEntry.color }}
                              />
                              <span className="text-muted-foreground">
                                {CATEGORY_LABELS[pEntry.name as string] ?? pEntry.name}
                              </span>
                              <span className="ml-auto font-bold tabular-nums">{pEntry.value}</span>
                            </div>
                          ))}
                      </div>
                      {dayTotal > 0 && (
                        <div className="flex items-center justify-between border-t px-3.5 py-2 text-sm">
                          <span className="font-semibold text-muted-foreground">Totale</span>
                          <span className="font-extrabold tabular-nums">{dayTotal}</span>
                        </div>
                      )}
                    </div>
                  );
                }}
              />
              {activeCategories.map((cat, i) => (
                <Bar
                  key={cat}
                  dataKey={cat}
                  stackId="sessions"
                  fill={CHART_CATEGORY_FILLS[cat]}
                  radius={i === activeCategories.length - 1 ? [6, 6, 0, 0] : [0, 0, 0, 0]}
                  maxBarSize={40}
                  animationBegin={i * 100}
                  animationDuration={900}
                  animationEasing="ease-out"
                />
              ))}
              <ChartLegend content={<ChartLegendContent />} />
            </BarChart>
          </ChartContainer>
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Alert Panel
// ════════════════════════════════════════════════════════════

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

// ════════════════════════════════════════════════════════════
// Today Agenda
// ════════════════════════════════════════════════════════════

const CLINICAL_PRIORITY_BADGE: Record<ClinicalReadinessClientItem["priority"], string> = {
  high: "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800",
  medium: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800",
  low: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800",
};

const CLINICAL_PRIORITY_LABEL: Record<ClinicalReadinessClientItem["priority"], string> = {
  high: "Alta",
  medium: "Media",
  low: "Bassa",
};

const CLINICAL_ANAMNESI_LABEL: Record<ClinicalReadinessClientItem["anamnesi_state"], string> = {
  missing: "Anamnesi assente",
  legacy: "Anamnesi legacy",
  structured: "Anamnesi allineata",
};

const CLINICAL_STEP_LABEL: Record<string, string> = {
  anamnesi_missing: "Compila anamnesi",
  anamnesi_legacy: "Rivedi anamnesi",
  baseline: "Registra baseline",
  workout: "Assegna scheda",
};

function ClinicalReadinessPanel({
  readiness,
  isLoading,
}: {
  readiness: ClinicalReadinessResponse | undefined;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border p-4 sm:p-5">
        <Skeleton className="h-5 w-56" />
        <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <Skeleton className="h-16 rounded-xl" />
          <Skeleton className="h-16 rounded-xl" />
          <Skeleton className="h-16 rounded-xl" />
          <Skeleton className="h-16 rounded-xl" />
        </div>
        <div className="mt-4 grid gap-2.5 md:grid-cols-2">
          <Skeleton className="h-28 rounded-xl" />
          <Skeleton className="h-28 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!readiness || readiness.summary.total_clients === 0) {
    return (
      <div className="rounded-2xl border bg-gradient-to-br from-white to-zinc-50/60 p-4 sm:p-5 dark:from-zinc-900 dark:to-zinc-800/40">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
          <h3 className="text-sm font-semibold sm:text-base">Readiness clinica</h3>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">Nessun cliente attivo da analizzare.</p>
      </div>
    );
  }

  const summary = readiness.summary;
  const actionableItems = readiness.items.filter((item) => item.next_action_code !== "ready");
  const topItems = actionableItems.slice(0, 6);

  return (
    <div className="rounded-2xl border bg-gradient-to-br from-white via-white to-zinc-50/70 p-4 shadow-sm sm:p-5 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-800/50">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <h3 className="truncate text-sm font-bold sm:text-base">Coda readiness clinica</h3>
              <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
                onboarding legacy con next-action
              </p>
            </div>
          </div>
        </div>
        <Link href="/clienti">
          <Button variant="ghost" size="sm" className="h-8 gap-1 text-xs text-muted-foreground hover:text-foreground">
            Clienti <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
      </div>

      <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border bg-zinc-50/80 px-3 py-2 dark:bg-zinc-900/60">
          <p className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">Clienti attivi</p>
          <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums">{summary.total_clients}</p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/80 px-3 py-2 dark:border-emerald-900/40 dark:bg-emerald-950/20">
          <p className="text-[10px] font-semibold tracking-wide text-emerald-700 uppercase dark:text-emerald-300">Pronti</p>
          <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-emerald-700 dark:text-emerald-300">
            {summary.ready_clients}
          </p>
        </div>
        <div className="rounded-xl border border-red-200 bg-red-50/80 px-3 py-2 dark:border-red-900/40 dark:bg-red-950/20">
          <p className="text-[10px] font-semibold tracking-wide text-red-700 uppercase dark:text-red-300">Alta priorita</p>
          <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-red-700 dark:text-red-300">
            {summary.high_priority}
          </p>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50/80 px-3 py-2 dark:border-amber-900/40 dark:bg-amber-950/20">
          <p className="text-[10px] font-semibold tracking-wide text-amber-700 uppercase dark:text-amber-300">Anamnesi da allineare</p>
          <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-amber-700 dark:text-amber-300">
            {summary.missing_anamnesi + summary.legacy_anamnesi}
          </p>
        </div>
      </div>

      {topItems.length === 0 ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/80 p-4 text-sm text-emerald-700 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-300">
          Tutti i clienti attivi hanno anamnesi, baseline e scheda allineate.
        </div>
      ) : (
        <div className="grid gap-2.5 md:grid-cols-2">
          {topItems.map((item) => (
            <div key={item.client_id} className="rounded-xl border bg-white p-3 shadow-sm dark:bg-zinc-900">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">
                    {item.client_nome} {item.client_cognome}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {CLINICAL_ANAMNESI_LABEL[item.anamnesi_state]} · score {item.readiness_score}%
                  </p>
                </div>
                <Badge
                  variant="outline"
                  className={`h-6 px-2 text-[10px] font-semibold uppercase ${CLINICAL_PRIORITY_BADGE[item.priority]}`}
                >
                  {CLINICAL_PRIORITY_LABEL[item.priority]}
                </Badge>
              </div>

              <div className="mt-2 flex flex-wrap gap-1.5">
                {item.missing_steps.map((step) => (
                  <Badge key={`${item.client_id}-${step}`} variant="secondary" className="text-[10px]">
                    {CLINICAL_STEP_LABEL[step] ?? step}
                  </Badge>
                ))}
              </div>

              <div className="mt-3 flex justify-end">
                <Link href={item.next_action_href}>
                  <Button size="sm" className="h-8 gap-1.5 text-xs">
                    {item.next_action_label}
                    <ArrowRight className="h-3 w-3" />
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {actionableItems.length > topItems.length && (
        <p className="mt-3 text-xs text-muted-foreground">
          Mostrati i primi {topItems.length} clienti su {actionableItems.length} da completare.
        </p>
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
      <div className="h-[480px] space-y-3 rounded-2xl border p-4 sm:p-5">
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
      className={`flex h-[480px] min-w-0 flex-col rounded-2xl border bg-gradient-to-br from-white via-white to-zinc-50/70 p-4 shadow-sm sm:p-5 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-800/50 ${getRevealMotionClass(
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

// ════════════════════════════════════════════════════════════
// Quick Actions
// ════════════════════════════════════════════════════════════

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
              style={getRevealDelayStyle(animationsEnabled, 360 + index * 40)}
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

// ════════════════════════════════════════════════════════════
// Welcome Card (first-run)
// ════════════════════════════════════════════════════════════

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

// ════════════════════════════════════════════════════════════
// Dashboard Skeleton
// ════════════════════════════════════════════════════════════

function DashboardSkeleton() {
  const borders = [
    "border-l-blue-500",
    "border-l-violet-500",
    "border-l-emerald-500",
    "border-l-amber-500",
  ];

  return (
    <div className="space-y-4 md:space-y-6">
      {/* 4 KPI */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 sm:gap-4">
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

      {/* Row 1: Agenda + Promemoria */}
      <div className="grid gap-4 md:gap-5 xl:grid-cols-2">
        <div className="h-[480px] space-y-3 rounded-2xl border p-4 sm:p-5">
          <Skeleton className="h-6 w-52" />
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-8 w-full rounded-lg" />
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-xl" />
          ))}
        </div>
        <div className="flex h-[480px] flex-col rounded-2xl border-2 border-amber-300/40 p-4 sm:p-5">
          <Skeleton className="mb-3 h-6 w-32" />
          <Skeleton className="mb-3 h-24 w-full rounded-lg" />
          <Skeleton className="mb-3 h-9 w-full rounded-lg" />
          <Skeleton className="flex-1 w-full rounded-lg" />
        </div>
      </div>

      {/* Row 2: Chart + Alert */}
      <div className="grid gap-4 md:gap-5 xl:grid-cols-2">
        <div className="flex h-[480px] flex-col rounded-2xl border p-4 sm:p-5">
          <Skeleton className="mb-4 h-5 w-52" />
          <Skeleton className="flex-1 w-full rounded-xl" />
        </div>
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    </div>
  );
}
