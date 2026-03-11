"use client";

import { useState, useMemo } from "react";
import { AlertCircle, RefreshCw, ShieldAlert, Users } from "lucide-react";

import { OggiHero, OggiHeroSkeleton } from "@/components/workspace/OggiHero";
import { OggiQueue, type QueueView } from "@/components/workspace/OggiQueue";
import { OggiClientContextPanel } from "@/components/workspace/OggiClientContextPanel";
import { WorkspaceDetailPanel } from "@/components/workspace/WorkspaceDetailPanel";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useSessionPrep,
  useWorkspaceCaseDetail,
  useWorkspaceCases,
  useWorkspaceToday,
} from "@/hooks/useWorkspace";
import { usePageReveal } from "@/lib/page-reveal";
import { appendFromParam } from "@/lib/url-state";
import type {
  OperationalCase,
  SessionPrepItem,
  WorkspaceTodaySection,
} from "@/types/api";

/* ── Helpers ── */

function coerceId(value: number | string | null | undefined): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const n = Number.parseInt(value, 10);
    return Number.isNaN(n) ? null : n;
  }
  return null;
}

function getCaseClientId(item: OperationalCase): number | null {
  if (item.root_entity.type === "client") return coerceId(item.root_entity.id);
  if (item.secondary_entity?.type === "client") return coerceId(item.secondary_entity.id);
  return null;
}

function getCaseEventId(item: OperationalCase): number | null {
  if (item.root_entity.type === "event") return coerceId(item.root_entity.id);
  return null;
}

function findSessionMatch(item: OperationalCase, sessions: SessionPrepItem[]): SessionPrepItem | null {
  if (sessions.length === 0) return null;
  const eventId = getCaseEventId(item);
  if (eventId !== null) {
    const m = sessions.find((s) => s.event_id === eventId);
    if (m) return m;
  }
  const clientId = getCaseClientId(item);
  if (clientId !== null) {
    const m = sessions.find((s) => s.client_id === clientId);
    if (m) return m;
  }
  return null;
}

function buildSupportLine(item: SessionPrepItem): string | null {
  const parts: string[] = [];
  if (item.readiness_score !== null) parts.push(`Readiness ${item.readiness_score}%`);
  if (item.active_plan_name) parts.push(item.active_plan_name);
  if (item.contract_credits_remaining !== null && item.contract_credits_total !== null) {
    parts.push(`${item.contract_credits_remaining}/${item.contract_credits_total} crediti`);
  }
  if (item.clinical_alerts.length > 0) {
    parts.push(`${item.clinical_alerts.length} alert`);
  } else {
    const issues = item.health_checks.filter((c) => c.status !== "ok").length;
    if (issues > 0) parts.push(`${issues} check`);
  }
  return parts.slice(0, 3).join(" · ") || null;
}

/* ── Page ── */

export default function OggiWorkspacePage() {
  const { revealClass, revealStyle } = usePageReveal();
  const todayQuery = useWorkspaceToday();
  const prepQuery = useSessionPrep();
  const today = todayQuery.data;
  const prep = prepQuery.data;

  const [requestedCaseId, setRequestedCaseId] = useState("");
  const [queueView, setQueueView] = useState<QueueView>("focus");

  /* ── Section mapping ── */
  const sectionsByBucket = useMemo(
    () => new Map(today?.sections.map((s) => [s.bucket, s]) ?? []),
    [today?.sections],
  );

  const nowSection = sectionsByBucket.get("now");
  const todaySection = sectionsByBucket.get("today");
  const upcoming3d = sectionsByBucket.get("upcoming_3d");
  const upcoming7d = sectionsByBucket.get("upcoming_7d");
  const waitingSection = sectionsByBucket.get("waiting");

  const focusTotal = (nowSection?.total ?? 0) + (todaySection?.total ?? 0);
  const backlogTotal = (upcoming3d?.total ?? 0) + (upcoming7d?.total ?? 0) + (waitingSection?.total ?? 0);

  /* ── Expanded backlog ── */
  const waitingPreview = waitingSection?.items ?? [];
  const effectiveView = queueView === "focus" && focusTotal === 0 && backlogTotal > 0 ? "backlog" : queueView;
  const needsExpanded = Boolean(today) && effectiveView !== "focus" && (waitingSection?.total ?? 0) > waitingPreview.length;
  const waitingQuery = useWorkspaceCases({ workspace: "today", bucket: "waiting", page_size: 8, sort_by: "priority" }, needsExpanded);
  const waitingItems = effectiveView !== "focus" && waitingQuery.data?.items.length ? waitingQuery.data.items : waitingPreview;

  const allSections: WorkspaceTodaySection[] = useMemo(() => [
    nowSection ?? { bucket: "now", label: "Adesso", total: 0, items: [] },
    todaySection ?? { bucket: "today", label: "Oggi", total: 0, items: [] },
    upcoming3d ?? { bucket: "upcoming_3d", label: "Entro 3 giorni", total: 0, items: [] },
    upcoming7d ?? { bucket: "upcoming_7d", label: "Entro 7 giorni", total: 0, items: [] },
    { ...(waitingSection ?? { bucket: "waiting" as const, label: "In attesa", total: 0 }), items: waitingItems },
  ], [nowSection, todaySection, upcoming3d, upcoming7d, waitingSection, waitingItems]);

  /* ── Case selection ── */
  const activeItems = useMemo(() => {
    const visible =
      effectiveView === "all"
        ? allSections.filter((s) => s.total > 0 || s.items.length > 0)
        : effectiveView === "backlog"
          ? allSections.filter((s) => ["upcoming_3d", "upcoming_7d", "waiting"].includes(s.bucket)).filter((s) => s.total > 0 || s.items.length > 0)
          : allSections.filter((s) => s.bucket === "now" || s.bucket === "today").filter((s) => s.total > 0 || s.items.length > 0);
    return visible.flatMap((s) => s.items);
  }, [allSections, effectiveView]);

  const focusCaseVisible = Boolean(today?.focus_case && activeItems.some((i) => i.case_id === today.focus_case?.case_id));
  const selectedCaseId =
    (requestedCaseId && activeItems.some((i) => i.case_id === requestedCaseId) && requestedCaseId) ||
    (focusCaseVisible ? today?.focus_case?.case_id ?? "" : "") ||
    activeItems[0]?.case_id || "";

  const selectedCase = activeItems.find((i) => i.case_id === selectedCaseId) ?? null;
  const detailQuery = useWorkspaceCaseDetail({ workspace: "today", caseId: selectedCase?.case_id ?? "" }, Boolean(selectedCase?.case_id));

  /* ── Session prep matching ── */
  const prepSessions = prep?.sessions ?? [];
  const selectedPrepItem = selectedCase ? findSessionMatch(selectedCase, prepSessions) : null;
  const alertClients = prep?.clients_with_alerts ?? 0;

  const withFromParam = (href: string) => appendFromParam(href, "oggi");
  const supportLineForItem = (item: OperationalCase) => {
    const prepItem = findSessionMatch(item, prepSessions);
    return prepItem ? buildSupportLine(prepItem) : null;
  };

  /* ── Loading ── */
  if (todayQuery.isLoading) {
    return (
      <div className="space-y-4">
        <OggiHeroSkeleton />
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(340px,0.9fr)]">
          <Skeleton className="h-[600px] rounded-2xl" />
          <Skeleton className="h-[600px] rounded-2xl" />
        </div>
      </div>
    );
  }

  /* ── Error ── */
  if (todayQuery.isError || !today) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 text-destructive" />
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-semibold text-destructive">Impossibile caricare Oggi</h1>
            <p className="mt-1 text-sm text-destructive/80">Il workspace non e' disponibile.</p>
          </div>
        </div>
        <Button size="sm" className="mt-4 rounded-full" onClick={() => void todayQuery.refetch()}>
          <RefreshCw className="mr-2 h-3.5 w-3.5" /> Riprova
        </Button>
      </div>
    );
  }

  /* ── Main ── */
  return (
    <div className="space-y-4">
      {/* Hero */}
      <div className={revealClass(0)} style={revealStyle(0)}>
        <OggiHero
          today={today}
          prep={prep}
          focusCount={focusTotal}
          alertClients={alertClients}
        />
      </div>

      {/* 2-column: queue + detail */}
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(340px,0.9fr)] xl:items-start">
        {/* Left: Queue */}
        <div className={revealClass(80)} style={revealStyle(80)}>
          <OggiQueue
            sections={allSections}
            focusTotal={focusTotal}
            backlogTotal={backlogTotal}
            completedCount={today.completed_today_count}
            snoozedCount={today.snoozed_count}
            selectedCaseId={selectedCaseId}
            onSelect={setRequestedCaseId}
            queueView={queueView}
            onChangeView={setQueueView}
            supportLineForItem={supportLineForItem}
            hrefTransform={withFromParam}
            isLoadingBacklog={needsExpanded && waitingQuery.isLoading}
          />
        </div>

        {/* Right: Detail + Client Context */}
        <section
          className={revealClass(
            140,
            "flex flex-col overflow-hidden rounded-2xl border border-stone-200/60 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950/80 xl:sticky xl:top-5",
          )}
          style={revealStyle(140)}
        >
          <div className="flex flex-col xl:h-[calc(100vh-20rem)]">
            <WorkspaceDetailPanel
              selectedCase={selectedCase}
              detail={detailQuery.data}
              isLoading={detailQuery.isLoading}
              isError={detailQuery.isError}
              onRetry={() => void detailQuery.refetch()}
              hrefTransform={withFromParam}
              embedded
              className="min-h-0 flex-1"
            />

            <div className="border-t border-stone-100 dark:border-zinc-800/80">
              {selectedPrepItem ? (
                <OggiClientContextPanel item={selectedPrepItem} embedded className="min-h-0" />
              ) : prepQuery.isError && selectedCase ? (
                <div className="px-4 py-4">
                  <div className="rounded-xl border border-stone-200/60 bg-stone-50/50 px-3.5 py-3 text-sm text-stone-500 dark:border-zinc-800 dark:bg-zinc-950/50 dark:text-zinc-400">
                    Contesto sessione non disponibile.
                  </div>
                </div>
              ) : selectedCase ? (
                <div className="space-y-3 px-4 py-4">
                  <div className="flex items-start gap-3 rounded-xl border border-stone-200/60 bg-stone-50/50 px-3.5 py-3 dark:border-zinc-800 dark:bg-zinc-950/50">
                    <Users className="mt-0.5 h-4 w-4 text-stone-400 dark:text-zinc-500" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-stone-700 dark:text-zinc-200">Nessuna sessione collegata</p>
                      <p className="mt-0.5 text-xs text-stone-500 dark:text-zinc-400">Il caso resta operativo.</p>
                    </div>
                  </div>

                  {prep && alertClients > 0 && (
                    <div className="flex items-start gap-3 rounded-xl border border-red-200/60 bg-red-50/50 px-3.5 py-3 dark:border-red-900/30 dark:bg-red-950/20">
                      <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-red-500 dark:text-red-400" />
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-red-700 dark:text-red-300">Alert clinici aperti</p>
                        <p className="mt-0.5 text-xs text-red-600/80 dark:text-red-300/80">
                          {alertClients} {alertClients === 1 ? "cliente" : "clienti"} con condizioni cliniche.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
