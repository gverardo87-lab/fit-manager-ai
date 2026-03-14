"use client";

import { useMemo, useState } from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

import "./oggi-workspace.css";

import { OggiHero, OggiHeroSkeleton } from "@/components/workspace/OggiHero";
import {
  OggiTimeline,
  getPreFlightStatus,
  type PreFlightStatus,
} from "@/components/workspace/OggiTimeline";
import { OggiCommandCenter } from "@/components/workspace/OggiCommandCenter";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { surfaceRoleClassName } from "@/components/ui/surface-role";
import { cn } from "@/lib/utils";
import { useSessionPrep, useWorkspaceToday } from "@/hooks/useWorkspace";
import { usePageReveal } from "@/lib/page-reveal";
import type { SessionPrepItem } from "@/types/api";

const ATTENTION_STATUSES = new Set<PreFlightStatus>(["blocked", "risk", "incomplete"]);

function getSessionStartMs(session: SessionPrepItem): number {
  const value = new Date(session.starts_at).getTime();
  return Number.isNaN(value) ? Number.MAX_SAFE_INTEGER : value;
}

function getTemporalBand(session: SessionPrepItem, nowMs: number): number {
  if (!session.client_id) return 3;
  const deltaMs = getSessionStartMs(session) - nowMs;
  if (deltaMs <= 90 * 60 * 1000) return 0;
  if (deltaMs <= 4 * 60 * 60 * 1000) return 1;
  return 2;
}

function sortSessionsForToday(
  sessions: SessionPrepItem[],
  nowMs: number,
): SessionPrepItem[] {
  return [...sessions].sort((left, right) => {
    const leftStatus = getPreFlightStatus(left);
    const rightStatus = getPreFlightStatus(right);

    const leftBand = getTemporalBand(left, nowMs);
    const rightBand = getTemporalBand(right, nowMs);
    if (leftBand !== rightBand) return leftBand - rightBand;

    const leftAttention = ATTENTION_STATUSES.has(leftStatus) ? 0 : 1;
    const rightAttention = ATTENTION_STATUSES.has(rightStatus) ? 0 : 1;
    if (leftAttention !== rightAttention) return leftAttention - rightAttention;

    return getSessionStartMs(left) - getSessionStartMs(right);
  });
}

export default function OggiWorkspacePage() {
  const { revealClass, revealStyle } = usePageReveal();
  const todayQuery = useWorkspaceToday();
  const prepQuery = useSessionPrep();
  const today = todayQuery.data;
  const prep = prepQuery.data;

  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);

  const referenceNowMs = useMemo(() => {
    const rawValue = prep?.current_time ?? today?.agenda.current_time ?? null;
    if (!rawValue) return 0;
    const value = new Date(rawValue).getTime();
    return Number.isNaN(value) ? 0 : value;
  }, [prep?.current_time, today?.agenda.current_time]);

  const orderedSessions = useMemo(() => {
    if (!prep) return [];
    const merged = [...prep.sessions, ...prep.non_client_events];
    return sortSessionsForToday(merged, referenceNowMs);
  }, [prep, referenceNowMs]);

  const clientSessions = useMemo(
    () => orderedSessions.filter((session) => Boolean(session.client_id)),
    [orderedSessions],
  );

  const attentionSessions = useMemo(
    () => clientSessions.filter((session) => ATTENTION_STATUSES.has(getPreFlightStatus(session))),
    [clientSessions],
  );

  const prioritySession = attentionSessions[0] ?? clientSessions[0] ?? orderedSessions[0] ?? null;

  const effectiveSelectedId = useMemo(() => {
    if (selectedEventId !== null && orderedSessions.some((item) => item.event_id === selectedEventId)) {
      return selectedEventId;
    }

    return prioritySession?.event_id ?? null;
  }, [selectedEventId, orderedSessions, prioritySession]);

  const selectedSession = orderedSessions.find((item) => item.event_id === effectiveSelectedId) ?? null;
  const selectedStatus = selectedSession ? getPreFlightStatus(selectedSession) : "no_client";

  const sessionSummary = useMemo(() => {
    const readyCount = clientSessions.filter((session) => getPreFlightStatus(session) === "ready").length;
    const attentionCount = attentionSessions.length;

    return {
      total: clientSessions.length,
      readyCount,
      attentionCount,
    };
  }, [attentionSessions, clientSessions]);

  const lastUpdatedAt = useMemo(() => {
    return Math.max(prepQuery.dataUpdatedAt ?? 0, todayQuery.dataUpdatedAt ?? 0) || null;
  }, [prepQuery.dataUpdatedAt, todayQuery.dataUpdatedAt]);

  if (prepQuery.isLoading || (!prep && !prepQuery.isError)) {
    return (
      <div className="flex flex-col gap-4">
        <OggiHeroSkeleton />
        {todayQuery.isError && (
          <div className={surfaceRoleClassName({ role: "context", tone: "amber" }, "px-4 py-3")}>
            <p className="text-[12px] font-semibold text-amber-800 dark:text-amber-300">
              Le attenzioni extra di oggi non sono disponibili.
            </p>
          </div>
        )}
        <div className="grid gap-4 lg:grid-cols-[minmax(340px,0.84fr)_minmax(0,1.16fr)]">
          <Skeleton className="h-[480px] rounded-2xl" />
          <Skeleton className="h-[480px] rounded-2xl" />
        </div>
      </div>
    );
  }

  if (prepQuery.isError && !prep) {
    return (
      <div className={surfaceRoleClassName({ role: "hero", tone: "red" }, "p-6")}>
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 text-red-500" />
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-bold text-red-700 dark:text-red-300">
              Impossibile aprire le sedute di oggi
            </h1>
            <p className="mt-1 text-sm text-red-600/80 dark:text-red-300/80">
              La preparazione giornaliera non e&apos; disponibile. Riprova il caricamento.
            </p>
          </div>
        </div>
        <Button
          size="sm"
          className="mt-4 rounded-full"
          onClick={() => {
            void prepQuery.refetch();
            void todayQuery.refetch();
          }}
        >
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Riprova
        </Button>
      </div>
    );
  }

  const safePrep = prep!;

  return (
    <div className="flex flex-col gap-4">
      {/* Hero compatto — strip singola riga */}
      <div className={revealClass(0)} style={revealStyle(0)}>
        <OggiHero
          prep={safePrep}
          attentionCount={sessionSummary.attentionCount}
          readyCount={sessionSummary.readyCount}
          internalCount={safePrep.non_client_events.length}
          focusSession={selectedSession}
          focusStatus={selectedSession ? selectedStatus : null}
          lastUpdatedAt={lastUpdatedAt}
          isRefreshing={prepQuery.isFetching || todayQuery.isFetching}
        />
      </div>

      {todayQuery.isError && (
        <div className={revealClass(12)} style={revealStyle(12)}>
          <div className={surfaceRoleClassName({ role: "context", tone: "amber" }, "px-4 py-3")}>
            <p className="text-[12px] font-semibold text-amber-800 dark:text-amber-300">
              Le attenzioni extra di oggi non sono disponibili.
            </p>
            <p className="mt-1 text-[11px] text-amber-700/80 dark:text-amber-300/80">
              La pagina resta operativa sulle sedute di oggi; i casi fuori seduta verranno ricaricati al prossimo refresh.
            </p>
          </div>
        </div>
      )}

      {/* Cockpit 2 colonne: timeline (sinistra) | focus seduta (destra) */}
      <div
        className={cn(
          revealClass(18),
          "grid gap-4 lg:grid-cols-[minmax(340px,0.84fr)_minmax(0,1.16fr)] lg:items-start",
        )}
        style={revealStyle(18)}
      >
        {/* Mobile: CommandCenter prima (order-1), Timeline dopo (order-2) */}
        {/* Desktop: Timeline a sinistra (lg:order-1), CommandCenter a destra (lg:order-2) */}
        <div className="order-2 lg:order-1">
          <OggiTimeline
            className="lg:max-h-[calc(100vh-13.5rem)] lg:overflow-y-auto lg:pr-1"
            sessions={orderedSessions}
            selectedEventId={effectiveSelectedId}
            onSelect={setSelectedEventId}
          />
        </div>
        <div className="order-1 lg:order-2">
          <OggiCommandCenter
            className="lg:max-h-[calc(100vh-13.5rem)] lg:overflow-y-auto lg:pr-1"
            session={selectedSession}
            status={selectedStatus}
          />
        </div>
      </div>
    </div>
  );
}
