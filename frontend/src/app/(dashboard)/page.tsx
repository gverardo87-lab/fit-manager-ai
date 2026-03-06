// src/app/(dashboard)/page.tsx
"use client";

/**
 * Dashboard — "La Plancia della Nave"
 *
 * Pannello di comando premium in ~1 screen:
 * 1. CommandStrip (hero teal con saluto + clock + 3 GaugeRing)
 * 2. AgendaLive + TodoCard (action zone 50/50)
 * 3. AlertHub (strip compatta alert)
 * 4. WeeklyPulse (chart 7 giorni compatto)
 *
 * Privacy-first: zero dati finanziari (quelli vivono in Cassa).
 */

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  Calendar,
  FileText,
  Rocket,
  Sparkles,
  UserPlus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { CommandStrip, CommandStripSkeleton } from "@/components/dashboard/CommandStrip";
import { AgendaLive } from "@/components/dashboard/AgendaLive";
import { AlertHub } from "@/components/dashboard/AlertHub";
import { WeeklyPulse } from "@/components/dashboard/WeeklyPulse";
import { TodoCard } from "@/components/dashboard/TodoCard";
import { GhostEventsSheet } from "@/components/dashboard/GhostEventsSheet";
import { ExpiringContractsSheet } from "@/components/dashboard/ExpiringContractsSheet";
import { InactiveClientsSheet } from "@/components/dashboard/InactiveClientsSheet";
import { useDashboard, useDashboardAlerts } from "@/hooks/useDashboard";
import { useEvents } from "@/hooks/useAgenda";
import { usePageReveal } from "@/lib/page-reveal";
import {
  formatLocalISODate,
  todayISO,
  tomorrowISO,
  weekStartISO,
  nextWeekStartISO,
} from "@/lib/dashboard-helpers";

// ════════════════════════════════════════════════════════════
// Pagina
// ════════════════════════════════════════════════════════════

export default function DashboardPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const { data: summary, isLoading: summaryLoading, isError, refetch } = useDashboard();
  const { data: alerts } = useDashboardAlerts();

  const [dateAnchor, setDateAnchor] = useState(() => new Date());

  // Auto-advance at midnight
  useEffect(() => {
    const currentTime = new Date();
    const nextMidnight = new Date(currentTime);
    nextMidnight.setHours(24, 0, 0, 0);
    const timeoutMs = Math.max(1000, nextMidnight.getTime() - currentTime.getTime());
    const timeoutId = window.setTimeout(() => setDateAnchor(new Date()), timeoutMs);
    return () => window.clearTimeout(timeoutId);
  }, [dateAnchor]);

  // Date ranges
  const currentDayStart = useMemo(() => todayISO(dateAnchor), [dateAnchor]);
  const nextDayStart = useMemo(() => tomorrowISO(dateAnchor), [dateAnchor]);
  const currentWeekStart = useMemo(() => weekStartISO(dateAnchor), [dateAnchor]);
  const nextWeekStart = useMemo(() => nextWeekStartISO(dateAnchor), [dateAnchor]);

  // API calls: 3 (down from 6)
  const { data: eventsData } = useEvents({ start: currentDayStart, end: nextDayStart });
  const { data: weeklyEventsData } = useEvents({ start: currentWeekStart, end: nextWeekStart });

  // Today events (sorted, non-cancelled)
  const todayEvents = useMemo(() => {
    if (!eventsData?.items) return [];
    const today = currentDayStart;
    return eventsData.items
      .filter((e) => formatLocalISODate(e.data_inizio) === today && e.stato !== "Cancellato")
      .sort((a, b) => a.data_inizio.getTime() - b.data_inizio.getTime());
  }, [eventsData, currentDayStart]);

  // Weekly events
  const weeklyEvents = useMemo(() => {
    if (!weeklyEventsData?.items) return [];
    return [...weeklyEventsData.items].sort((a, b) => a.data_inizio.getTime() - b.data_inizio.getTime());
  }, [weeklyEventsData]);

  // Alert counts for TodoCard
  const visibleAlerts = useMemo(
    () => alerts?.items.filter((item) => item.category !== "overdue_rates") ?? [],
    [alerts],
  );
  const criticalAlertCount = visibleAlerts.filter((item) => item.severity === "critical").length;
  const warningAlertCount = visibleAlerts.filter((item) => item.severity === "warning").length;
  const upcomingSessionsCount = todayEvents.filter(
    (event) => event.stato === "Programmato",
  ).length;

  const isLoading = summaryLoading;

  // Sheet state for inline alert resolution
  const [ghostSheetOpen, setGhostSheetOpen] = useState(false);
  const [expiringSheetOpen, setExpiringSheetOpen] = useState(false);
  const [inactiveSheetOpen, setInactiveSheetOpen] = useState(false);

  const alertActions: Record<string, () => void> = {
    ghost_events: () => setGhostSheetOpen(true),
    expiring_contracts: () => setExpiringSheetOpen(true),
    inactive_clients: () => setInactiveSheetOpen(true),
  };

  return (
    <div className="min-w-0 space-y-4 md:space-y-5">
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
          {/* ── CommandStrip (hero) ── */}
          <div className={revealClass(0)} style={revealStyle(0)}>
            {isLoading ? (
              <CommandStripSkeleton />
            ) : (
              <CommandStrip
                summary={summary}
                todayEvents={todayEvents}
                dateAnchor={dateAnchor}
              />
            )}
          </div>

          {/* ── Action Zone: Agenda + Todo ── */}
          <div className="grid min-w-0 gap-4 md:gap-5 xl:grid-cols-2">
            <div
              className={`min-w-0 ${revealClass(80)}`}
              style={revealStyle(80)}
            >
              <AgendaLive
                events={todayEvents}
                isLoading={!eventsData}
              />
            </div>
            <div
              className={`min-w-0 ${revealClass(120)}`}
              style={revealStyle(120)}
            >
              <TodoCard
                criticalAlertCount={criticalAlertCount}
                warningAlertCount={warningAlertCount}
                upcomingSessionsCount={upcomingSessionsCount}
              />
            </div>
          </div>

          {/* ── AlertHub (compact strip) ── */}
          <div className={revealClass(160)} style={revealStyle(160)}>
            <AlertHub
              alerts={alerts}
              isLoading={!alerts}
              alertActions={alertActions}
            />
          </div>

          {/* ── WeeklyPulse (chart compatto) ── */}
          <div className={revealClass(200)} style={revealStyle(200)}>
            <WeeklyPulse
              events={weeklyEvents}
              dateAnchor={dateAnchor}
              isLoading={!weeklyEventsData}
            />
          </div>
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
