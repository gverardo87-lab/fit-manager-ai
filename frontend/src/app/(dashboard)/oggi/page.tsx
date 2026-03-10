"use client";

import { useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  ArrowRight,
  CalendarClock,
  HeartPulse,
  RefreshCw,
  ShieldAlert,
  SunMedium,
  Users,
} from "lucide-react";

import { SessionPrepCard } from "@/components/workspace/SessionPrepCard";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useSessionPrep } from "@/hooks/useWorkspace";
import { usePageReveal } from "@/lib/page-reveal";

/* ── KPI Pill ── */

function KpiPill({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Users;
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div className={`flex items-center gap-2.5 rounded-2xl border px-4 py-3 ${tone}`}>
      <Icon className="h-4 w-4 shrink-0 opacity-70" />
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] opacity-70">{label}</p>
        <p className="text-xl font-extrabold leading-none tabular-nums">{value}</p>
      </div>
    </div>
  );
}

/* ── Time greeting ── */

function getGreeting(currentTime: string): string {
  const date = new Date(currentTime);
  if (Number.isNaN(date.getTime())) return "Buongiorno";
  const h = date.getHours();
  if (h < 12) return "Buongiorno";
  if (h < 18) return "Buon pomeriggio";
  return "Buonasera";
}

function formatDateLabel(dateStr: string): string {
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return dateStr;
  return date.toLocaleDateString("it-IT", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

/* ── Cockpit Brief ── */

function buildBrief(totalSessions: number, alertsCount: number): string {
  if (totalSessions === 0) {
    return "Nessuna sessione in programma. Puoi usare la giornata per onboarding e follow-up.";
  }
  const sessionWord = totalSessions === 1 ? "sessione" : "sessioni";
  if (alertsCount > 0) {
    const alertWord = alertsCount === 1 ? "cliente con criticita cliniche" : "clienti con criticita cliniche";
    return `${totalSessions} ${sessionWord} in programma, ${alertsCount} ${alertWord} da tenere sotto controllo.`;
  }
  return `${totalSessions} ${sessionWord} in programma. Tutto nella norma — qui sotto il profilo di ciascuno.`;
}

/* ── Page ── */

export default function OggiCockpitPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const prepQuery = useSessionPrep();
  const prep = prepQuery.data;

  const [expandedEventId, setExpandedEventId] = useState<number | null>(null);

  const handleToggleExpand = (eventId: number) => {
    setExpandedEventId((prev) => (prev === eventId ? null : eventId));
  };

  /* ── Loading ── */
  if (prepQuery.isLoading) {
    return (
      <div className="space-y-5">
        <Skeleton className="h-32 rounded-3xl" />
        <div className="space-y-4">
          <Skeleton className="h-28 rounded-2xl" />
          <Skeleton className="h-28 rounded-2xl" />
          <Skeleton className="h-28 rounded-2xl" />
        </div>
      </div>
    );
  }

  /* ── Error ── */
  if (prepQuery.isError || !prep) {
    return (
      <div className="rounded-3xl border border-destructive/40 bg-destructive/5 p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 text-destructive" />
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-semibold text-destructive">Impossibile caricare la preparazione</h1>
            <p className="mt-1 text-sm text-destructive/90">
              I dati delle sessioni di oggi non sono disponibili.
            </p>
          </div>
        </div>
        <Button size="sm" className="mt-4" onClick={() => void prepQuery.refetch()}>
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Riprova
        </Button>
      </div>
    );
  }

  const greeting = getGreeting(prep.current_time);
  const dateLabel = formatDateLabel(prep.date);
  const brief = buildBrief(prep.total_sessions, prep.clients_with_alerts);
  const allSessions = prep.sessions;
  const nonClientEvents = prep.non_client_events;
  const sessionsWithAlerts = allSessions.filter((s) => s.clinical_alerts.length > 0);
  const sessionsWithIssues = allSessions.filter(
    (s) => s.health_checks.some((c) => c.status !== "ok") && s.clinical_alerts.length === 0,
  );

  return (
    <div className="space-y-5">
      {/* ── Hero Header ── */}
      <div
        className={revealClass(
          0,
          "rounded-3xl border border-border/70 bg-gradient-to-br from-stone-50 via-white to-primary/5 p-5 shadow-sm dark:from-zinc-900 dark:via-zinc-900 dark:to-primary/5",
        )}
        style={revealStyle(0)}
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-100 to-primary/20 dark:from-amber-950/30 dark:to-primary/20">
                <SunMedium className="h-5 w-5 text-amber-700 dark:text-amber-300" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight">{greeting}</h1>
                <p className="text-sm capitalize text-muted-foreground">{dateLabel}</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-foreground/85 sm:text-[15px]">{brief}</p>
          </div>

          <div className="flex flex-wrap gap-2">
            <KpiPill
              icon={CalendarClock}
              label="Sessioni"
              value={prep.total_sessions}
              tone="border-primary/20 bg-primary/5 text-primary"
            />
            {prep.clients_with_alerts > 0 && (
              <KpiPill
                icon={ShieldAlert}
                label="Alert clinici"
                value={prep.clients_with_alerts}
                tone="border-red-200 bg-red-50/80 text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300"
              />
            )}
          </div>
        </div>
      </div>

      {/* ── Session Prep Cards ── */}
      {allSessions.length === 0 && nonClientEvents.length === 0 ? (
        <div
          className={revealClass(80, "rounded-3xl border border-dashed border-border/70 px-6 py-12 text-center")}
          style={revealStyle(80)}
        >
          <SunMedium className="mx-auto h-10 w-10 text-muted-foreground/40" />
          <h2 className="mt-4 text-lg font-semibold">Giornata libera</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Nessun appuntamento in programma. Puoi dedicarti ad onboarding e pianificazione.
          </p>
          <div className="mt-4 flex justify-center gap-3">
            <Button asChild variant="outline" size="sm">
              <Link href="/clienti/myportal">
                <HeartPulse className="mr-1.5 h-3.5 w-3.5" />
                Monitoraggio
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href="/agenda">
                <CalendarClock className="mr-1.5 h-3.5 w-3.5" />
                Agenda
              </Link>
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Sessions with clinical alerts first */}
          {sessionsWithAlerts.length > 0 && (
            <section className={revealClass(80)} style={revealStyle(80)}>
              <div className="mb-3 flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-red-600 dark:text-red-400" />
                <h2 className="text-sm font-semibold text-red-700 dark:text-red-300">
                  Attenzione clinica richiesta
                </h2>
              </div>
              <div className="space-y-3">
                {sessionsWithAlerts.map((item) => (
                  <SessionPrepCard
                    key={item.event_id}
                    item={item}
                    expanded={expandedEventId === item.event_id}
                    onToggleExpand={() => handleToggleExpand(item.event_id)}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Sessions with health issues (no clinical alerts) */}
          {sessionsWithIssues.length > 0 && (
            <section className={revealClass(140)} style={revealStyle(140)}>
              <div className="mb-3 flex items-center gap-2">
                <HeartPulse className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                <h2 className="text-sm font-semibold text-amber-700 dark:text-amber-300">
                  Profili da completare
                </h2>
              </div>
              <div className="space-y-3">
                {sessionsWithIssues.map((item) => (
                  <SessionPrepCard
                    key={item.event_id}
                    item={item}
                    expanded={expandedEventId === item.event_id}
                    onToggleExpand={() => handleToggleExpand(item.event_id)}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Clean sessions */}
          {allSessions.filter(
            (s) => s.clinical_alerts.length === 0 && !s.health_checks.some((c) => c.status !== "ok"),
          ).length > 0 && (
            <section className={revealClass(200)} style={revealStyle(200)}>
              <div className="mb-3 flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold">Pronti</h2>
              </div>
              <div className="space-y-3">
                {allSessions
                  .filter(
                    (s) => s.clinical_alerts.length === 0 && !s.health_checks.some((c) => c.status !== "ok"),
                  )
                  .map((item) => (
                    <SessionPrepCard
                      key={item.event_id}
                      item={item}
                      expanded={expandedEventId === item.event_id}
                      onToggleExpand={() => handleToggleExpand(item.event_id)}
                    />
                  ))}
              </div>
            </section>
          )}

          {/* Non-client events */}
          {nonClientEvents.length > 0 && (
            <section className={revealClass(260)} style={revealStyle(260)}>
              <div className="mb-3 flex items-center gap-2">
                <CalendarClock className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold">Altri impegni</h2>
              </div>
              <div className="space-y-3">
                {nonClientEvents.map((item) => (
                  <SessionPrepCard key={item.event_id} item={item} />
                ))}
              </div>
            </section>
          )}

          {/* Agenda link */}
          <div className={revealClass(300)} style={revealStyle(300)}>
            <Button asChild variant="ghost" size="sm" className="text-xs text-muted-foreground">
              <Link href="/agenda">
                Apri agenda completa
                <ArrowRight className="ml-1 h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
