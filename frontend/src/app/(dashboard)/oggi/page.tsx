"use client";

import { useState, useMemo } from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

import { OggiHero, OggiHeroSkeleton } from "@/components/workspace/OggiHero";
import { OggiTimeline, getPreFlightStatus } from "@/components/workspace/OggiTimeline";
import { OggiCommandCenter } from "@/components/workspace/OggiCommandCenter";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useSessionPrep, useWorkspaceToday } from "@/hooks/useWorkspace";
import { usePageReveal } from "@/lib/page-reveal";
import type { SessionPrepItem } from "@/types/api";

/* ── Page ── */

export default function OggiWorkspacePage() {
  const { revealClass, revealStyle } = usePageReveal();
  const todayQuery = useWorkspaceToday();
  const prepQuery = useSessionPrep();
  const today = todayQuery.data;
  const prep = prepQuery.data;

  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);

  /* ── Merge sessions + non-client events into timeline ── */
  const allSessions: SessionPrepItem[] = useMemo(() => {
    if (!prep) return [];
    const merged = [...prep.sessions, ...prep.non_client_events];
    return merged.sort((a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime());
  }, [prep]);

  /* ── Auto-select first client session ── */
  const effectiveSelectedId = useMemo(() => {
    if (selectedEventId !== null && allSessions.some((s) => s.event_id === selectedEventId)) {
      return selectedEventId;
    }
    return allSessions.find((s) => s.client_id)?.event_id ?? null;
  }, [selectedEventId, allSessions]);

  const selectedSession = allSessions.find((s) => s.event_id === effectiveSelectedId) ?? null;
  const selectedStatus = selectedSession ? getPreFlightStatus(selectedSession) : "no_client";

  /* ── Pre-flight summary ── */
  const preFlightSummary = useMemo(() => {
    const clientSessions = allSessions.filter((s) => s.client_id);
    const ready = clientSessions.filter((s) => getPreFlightStatus(s) === "ready").length;
    return { ready, total: clientSessions.length };
  }, [allSessions]);

  /* ── Hero props ── */
  const alertClients = prep?.clients_with_alerts ?? 0;
  const focusTotal = today?.sections.reduce(
    (sum, s) => sum + (s.bucket === "now" || s.bucket === "today" ? s.total : 0), 0,
  ) ?? 0;

  /* ── Loading ── */
  if (prepQuery.isLoading && todayQuery.isLoading) {
    return (
      <div className="space-y-4">
        <OggiHeroSkeleton />
        <div className="grid gap-4 lg:grid-cols-[minmax(260px,0.35fr)_minmax(0,0.65fr)]">
          <Skeleton className="h-[500px] rounded-2xl" />
          <Skeleton className="h-[500px] rounded-2xl" />
        </div>
      </div>
    );
  }

  /* ── Error ── */
  if (prepQuery.isError && todayQuery.isError) {
    return (
      <div
        className="rounded-2xl p-6"
        style={{
          border: "0.5px solid oklch(0.55 0.15 25 / 0.15)",
          background: "oklch(0.98 0.005 25 / 0.3)",
        }}
      >
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 text-red-500" />
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-bold text-red-700 dark:text-red-300">
              Impossibile caricare Oggi
            </h1>
            <p className="mt-1 text-sm text-red-600/80 dark:text-red-300/80">
              Il workspace non è disponibile.
            </p>
          </div>
        </div>
        <Button
          size="sm"
          className="mt-4 rounded-full"
          onClick={() => { void prepQuery.refetch(); void todayQuery.refetch(); }}
        >
          <RefreshCw className="mr-2 h-3.5 w-3.5" /> Riprova
        </Button>
      </div>
    );
  }

  /* ── Main: Mission Control ── */
  return (
    <div className="relative space-y-4">
      {/* Refraction gradient ghost — teal ambient sphere behind timeline */}
      <div
        className="pointer-events-none absolute -left-24 top-32 h-[400px] w-[400px] rounded-full blur-[120px]"
        style={{ background: "oklch(0.65 0.12 170 / 0.03)" }}
      />

      {/* Hero */}
      <div className={revealClass(0)} style={revealStyle(0)}>
        <OggiHero
          today={today}
          prep={prep}
          focusCount={focusTotal}
          alertClients={alertClients}
        />
      </div>

      {/* Pre-flight summary bar */}
      {preFlightSummary.total > 0 && (
        <div className={revealClass(30)} style={revealStyle(30)}>
          <div
            className="flex items-center gap-3 rounded-xl px-4 py-2.5 backdrop-blur-sm"
            style={{
              border: "0.5px solid oklch(0.80 0.01 200 / 0.08)",
              background: "oklch(0.99 0.003 200 / 0.5)",
            }}
          >
            <span className="text-[9px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
              Pre-flight
            </span>
            <span className="text-[15px] font-extrabold tabular-nums tracking-tight text-stone-800 dark:text-zinc-200">
              {preFlightSummary.ready}/{preFlightSummary.total}
            </span>
            <span className="text-[11px] text-stone-400 dark:text-zinc-500">
              {preFlightSummary.ready === preFlightSummary.total
                ? "tutte pronte"
                : `${preFlightSummary.total - preFlightSummary.ready} da preparare`}
            </span>
          </div>
        </div>
      )}

      {/* Master-Detail: The Pulse + Command Center */}
      <div
        className={revealClass(
          70,
          "grid gap-4 lg:grid-cols-[minmax(260px,0.35fr)_minmax(0,0.65fr)] lg:items-start",
        )}
        style={revealStyle(70)}
      >
        {/* Left: The Pulse — Timeline */}
        <OggiTimeline
          sessions={allSessions}
          selectedEventId={effectiveSelectedId}
          onSelect={setSelectedEventId}
          className="lg:sticky lg:top-5 lg:h-[calc(100vh-16rem)]"
        />

        {/* Right: Command Center */}
        <OggiCommandCenter
          session={selectedSession}
          status={selectedStatus}
        />
      </div>
    </div>
  );
}
