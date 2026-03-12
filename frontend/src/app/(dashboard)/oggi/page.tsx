"use client";

import { useMemo, useState } from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

import { OggiHero, OggiHeroSkeleton } from "@/components/workspace/OggiHero";
import {
  OggiTimeline,
  getPreFlightStatus,
  type PreFlightStatus,
} from "@/components/workspace/OggiTimeline";
import { OggiCommandCenter } from "@/components/workspace/OggiCommandCenter";
import { OggiPreSessionCard } from "@/components/workspace/OggiPreSessionCard";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { surfaceRoleClassName } from "@/components/ui/surface-role";
import { useSessionPrep, useWorkspaceToday } from "@/hooks/useWorkspace";
import { usePageReveal } from "@/lib/page-reveal";
import type { OperationalCase, SessionPrepItem } from "@/types/api";

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

function getExtraCases(today: ReturnType<typeof useWorkspaceToday>["data"]): OperationalCase[] {
  if (!today) return [];

  return today.sections
    .filter((section) => section.bucket === "now" || section.bucket === "today")
    .flatMap((section) => section.items)
    .filter((item) => item.case_kind !== "session_imminent");
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

  const prioritySession = useMemo(
    () => attentionSessions[0] ?? clientSessions[0] ?? orderedSessions[0] ?? null,
    [attentionSessions, clientSessions, orderedSessions],
  );

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

  const extraCases = useMemo(() => getExtraCases(today), [today]);
  const supportCase = useMemo(() => {
    if (today?.focus_case && today.focus_case.case_kind !== "session_imminent") {
      return today.focus_case;
    }
    return extraCases[0] ?? null;
  }, [today, extraCases]);

  if (prepQuery.isLoading || (!prep && !prepQuery.isError)) {
    return (
      <div className="space-y-4">
        <OggiHeroSkeleton />
        <div className="space-y-4">
          {todayQuery.isError && (
            <div className={surfaceRoleClassName({ role: "context", tone: "amber" }, "px-4 py-3")}>
              <p className="text-[12px] font-semibold text-amber-800 dark:text-amber-300">
                Le attenzioni extra di oggi non sono disponibili.
              </p>
            </div>
          )}
          <Skeleton className="h-[460px] rounded-[32px]" />
        </div>
        <Skeleton className="h-[360px] rounded-[32px]" />
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
    <div className="space-y-4">
      <div className={revealClass(0)} style={revealStyle(0)}>
        <OggiHero
          prep={safePrep}
          attentionCount={sessionSummary.attentionCount}
          readyCount={sessionSummary.readyCount}
          extraCaseCount={extraCases.length}
          alertClients={safePrep.clients_with_alerts}
          supportCase={supportCase}
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

      {selectedSession?.client_id && (
        <div className={revealClass(18)} style={revealStyle(18)}>
          <OggiPreSessionCard session={selectedSession} />
        </div>
      )}

      <div
        className={revealClass(32)}
        style={revealStyle(32)}
      >
        <OggiCommandCenter
          session={selectedSession}
          status={selectedStatus}
        />
      </div>

      <div className={revealClass(48)} style={revealStyle(48)}>
        <OggiTimeline
          sessions={orderedSessions}
          selectedEventId={effectiveSelectedId}
          onSelect={setSelectedEventId}
        />
      </div>
    </div>
  );
}
