"use client";

import { useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  ArrowRight,
  LayoutList,
  RefreshCw,
  ShieldAlert,
  SunMedium,
  Users,
} from "lucide-react";

import { OggiClientContextPanel } from "@/components/workspace/OggiClientContextPanel";
import { WorkspaceAgendaPanel } from "@/components/workspace/WorkspaceAgendaPanel";
import { WorkspaceCaseCard } from "@/components/workspace/WorkspaceCaseCard";
import { WorkspaceDetailPanel } from "@/components/workspace/WorkspaceDetailPanel";
import { WORKSPACE_BUCKET_META } from "@/components/workspace/workspace-ui";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useSessionPrep,
  useWorkspaceCaseDetail,
  useWorkspaceCases,
  useWorkspaceToday,
} from "@/hooks/useWorkspace";
import { usePageReveal } from "@/lib/page-reveal";
import { appendFromParam } from "@/lib/url-state";
import { cn } from "@/lib/utils";
import type {
  CaseBucket,
  OperationalCase,
  SessionPrepItem,
  WorkspaceTodaySection,
} from "@/types/api";

const DATE_FORMATTER = new Intl.DateTimeFormat("it-IT", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

const LANE_COPY: Record<CaseBucket, string> = {
  now: "Muovi questi casi prima di tutto.",
  today: "Chiudi qui il grosso della giornata.",
  upcoming_3d: "Tienili caldi prima che salgano di priorita.",
  upcoming_7d: "Mantieni trazione senza sporcare il presente.",
  waiting: "Backlog vivo ma fuori dal centro del tavolo.",
};

type QueueView = "focus" | "all" | "backlog";

function formatDateLabel(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return DATE_FORMATTER.format(parsed);
}

function buildOggiBrief({
  focusCount,
  backlogCount,
  totalSessions,
  alertClients,
  sessionsToPrepare,
}: {
  focusCount: number;
  backlogCount: number;
  totalSessions: number;
  alertClients: number;
  sessionsToPrepare: number;
}) {
  const pieces: string[] = [];

  if (focusCount > 0) {
    pieces.push(`${focusCount} ${focusCount === 1 ? "caso guida" : "casi guidano"} la giornata`);
  } else if (backlogCount > 0) {
    pieces.push(`niente di urgente, ma ${backlogCount} ${backlogCount === 1 ? "caso resta" : "casi restano"} da presidiare`);
  } else {
    pieces.push("giornata pulita sul fronte operativo");
  }

  if (totalSessions > 0) {
    pieces.push(`${totalSessions} ${totalSessions === 1 ? "sessione in agenda" : "sessioni in agenda"}`);
  }

  if (alertClients > 0) {
    pieces.push(`${alertClients} ${alertClients === 1 ? "cliente con alert" : "clienti con alert"}`);
  } else if (sessionsToPrepare > 0) {
    pieces.push(`${sessionsToPrepare} ${sessionsToPrepare === 1 ? "profilo da ripassare" : "profili da ripassare"}`);
  }

  return `${pieces.join(", ")}.`;
}

function InlineCounter({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div className={cn("inline-flex items-center gap-2 rounded-full border px-3 py-1.5", tone)}>
      <span className="text-[10px] font-semibold uppercase tracking-[0.16em]">{label}</span>
      <span className="text-[15px] font-bold leading-none tabular-nums">{value}</span>
    </div>
  );
}

function QueueViewButton({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-2 text-left transition-colors",
        active
          ? "border-stone-900 bg-stone-950 text-stone-50 dark:border-zinc-100 dark:bg-zinc-100 dark:text-stone-950"
          : "border-stone-200/80 bg-white/80 text-stone-700 hover:bg-stone-50 dark:border-zinc-800 dark:bg-zinc-950/60 dark:text-zinc-200 dark:hover:bg-zinc-900",
      )}
    >
      <span className="text-[11px] font-semibold uppercase tracking-[0.16em]">{label}</span>
      <span className="text-[12px] font-semibold tabular-nums opacity-80">{count}</span>
    </button>
  );
}

function coerceNumericId(value: number | string | null | undefined): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string" && value.trim().length > 0) {
    const parsed = Number.parseInt(value, 10);
    return Number.isNaN(parsed) ? null : parsed;
  }

  return null;
}

function getCaseClientId(item: OperationalCase): number | null {
  if (item.root_entity.type === "client") {
    return coerceNumericId(item.root_entity.id);
  }

  if (item.secondary_entity?.type === "client") {
    return coerceNumericId(item.secondary_entity.id);
  }

  return null;
}

function getCaseEventId(item: OperationalCase): number | null {
  if (item.root_entity.type === "event") {
    return coerceNumericId(item.root_entity.id);
  }

  return null;
}

function findSessionPrepMatch(item: OperationalCase, sessions: SessionPrepItem[]): SessionPrepItem | null {
  if (sessions.length === 0) {
    return null;
  }

  const eventId = getCaseEventId(item);
  if (eventId !== null) {
    const eventMatch = sessions.find((session) => session.event_id === eventId);
    if (eventMatch) {
      return eventMatch;
    }
  }

  const clientId = getCaseClientId(item);
  if (clientId !== null) {
    const clientMatch = sessions.find((session) => session.client_id === clientId);
    if (clientMatch) {
      return clientMatch;
    }
  }

  return null;
}

function buildClientSupportLine(item: SessionPrepItem): string | null {
  const pieces: string[] = [];

  if (item.readiness_score !== null) {
    pieces.push(`Readiness ${item.readiness_score}%`);
  }

  if (item.active_plan_name) {
    pieces.push(item.active_plan_name);
  }

  if (item.contract_credits_remaining !== null && item.contract_credits_total !== null) {
    pieces.push(`${item.contract_credits_remaining}/${item.contract_credits_total} crediti`);
  }

  if (item.clinical_alerts.length > 0) {
    pieces.push(
      item.clinical_alerts.length === 1
        ? "1 alert clinico"
        : `${item.clinical_alerts.length} alert clinici`,
    );
  } else {
    const checksToReview = item.health_checks.filter((check) => check.status !== "ok").length;
    if (checksToReview > 0) {
      pieces.push(
        checksToReview === 1 ? "1 check da rivedere" : `${checksToReview} check da rivedere`,
      );
    }
  }

  return pieces.slice(0, 3).join(" | ") || null;
}

function LaneSection({
  section,
  selectedCaseId,
  onSelect,
  supportLineForItem,
  hrefTransform,
}: {
  section: WorkspaceTodaySection;
  selectedCaseId: string;
  onSelect: (caseId: string) => void;
  supportLineForItem: (item: OperationalCase) => string | null;
  hrefTransform: (href: string) => string;
}) {
  const meta = WORKSPACE_BUCKET_META[section.bucket];

  if (section.total === 0 && section.items.length === 0) {
    return null;
  }

  return (
    <section className="space-y-2.5">
      <div className="flex flex-col gap-1.5 border-b border-stone-200/80 pb-2 dark:border-zinc-800 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <span className={cn("rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]", meta.pillTone)}>
            {meta.label}
          </span>
          <span className="text-[12px] font-semibold text-stone-700 dark:text-zinc-200">
            {section.total}
          </span>
        </div>
        <p className="text-[11px] leading-5 text-stone-500 dark:text-zinc-400">
          {LANE_COPY[section.bucket]}
        </p>
      </div>

      <div className="space-y-2">
        {section.items.map((item) => (
          <WorkspaceCaseCard
            key={item.case_id}
            item={item}
            selected={item.case_id === selectedCaseId}
            onSelect={() => onSelect(item.case_id)}
            supportingLine={supportLineForItem(item)}
            hrefTransform={hrefTransform}
          />
        ))}
      </div>
    </section>
  );
}

export default function OggiWorkspacePage() {
  const { revealClass, revealStyle } = usePageReveal();
  const todayQuery = useWorkspaceToday();
  const prepQuery = useSessionPrep();
  const today = todayQuery.data;
  const prep = prepQuery.data;

  const [requestedCaseId, setRequestedCaseId] = useState("");
  const [queueView, setQueueView] = useState<QueueView>("focus");

  const sectionsByBucket = new Map(today?.sections.map((section) => [section.bucket, section]) ?? []);
  const nowSection = sectionsByBucket.get("now");
  const todaySection = sectionsByBucket.get("today");
  const upcoming3dSection = sectionsByBucket.get("upcoming_3d");
  const upcoming7dSection = sectionsByBucket.get("upcoming_7d");
  const waitingSection = sectionsByBucket.get("waiting");

  const waitingPreviewItems = waitingSection?.items ?? [];
  const waitingTotal = waitingSection?.total ?? 0;
  const focusTotal = (nowSection?.total ?? 0) + (todaySection?.total ?? 0);
  const backlogTotal =
    (upcoming3dSection?.total ?? 0) +
    (upcoming7dSection?.total ?? 0) +
    waitingTotal;

  const effectiveQueueView =
    queueView === "focus" && focusTotal === 0 && backlogTotal > 0 ? "backlog" : queueView;
  const needsExpandedWaiting =
    Boolean(today) &&
    effectiveQueueView !== "focus" &&
    waitingTotal > waitingPreviewItems.length;

  const waitingQuery = useWorkspaceCases(
    {
      workspace: "today",
      bucket: "waiting",
      page_size: 8,
      sort_by: "priority",
    },
    needsExpandedWaiting,
  );

  const waitingItems =
    effectiveQueueView !== "focus" && waitingQuery.data?.items.length
      ? waitingQuery.data.items
      : waitingPreviewItems;

  const allSections: WorkspaceTodaySection[] = [
    nowSection ? { ...nowSection, items: nowSection.items ?? [] } : { bucket: "now", label: "Adesso", total: 0, items: [] },
    todaySection ? { ...todaySection, items: todaySection.items ?? [] } : { bucket: "today", label: "Oggi", total: 0, items: [] },
    upcoming3dSection
      ? { ...upcoming3dSection, items: upcoming3dSection.items ?? [] }
      : { bucket: "upcoming_3d", label: "Entro 3 giorni", total: 0, items: [] },
    upcoming7dSection
      ? { ...upcoming7dSection, items: upcoming7dSection.items ?? [] }
      : { bucket: "upcoming_7d", label: "Entro 7 giorni", total: 0, items: [] },
    waitingSection
      ? { ...waitingSection, items: waitingItems }
      : { bucket: "waiting", label: "In attesa", total: 0, items: waitingItems },
  ];

  const activeSections =
    effectiveQueueView === "all"
      ? allSections.filter((section) => section.total > 0 || section.items.length > 0)
      : effectiveQueueView === "backlog"
        ? allSections
            .filter((section) =>
              section.bucket === "upcoming_3d" ||
              section.bucket === "upcoming_7d" ||
              section.bucket === "waiting",
            )
            .filter((section) => section.total > 0 || section.items.length > 0)
        : allSections
            .filter((section) => section.bucket === "now" || section.bucket === "today")
            .filter((section) => section.total > 0 || section.items.length > 0);

  const activeItems = activeSections.flatMap((section) => section.items);
  const hasAnyOperationalCases = allSections.some((section) => section.total > 0 || section.items.length > 0);
  const focusCaseVisible = Boolean(
    today?.focus_case && activeItems.some((item) => item.case_id === today.focus_case?.case_id),
  );

  const selectedCaseId =
    (requestedCaseId && activeItems.some((item) => item.case_id === requestedCaseId) && requestedCaseId) ||
    (focusCaseVisible ? today?.focus_case?.case_id ?? "" : "") ||
    activeItems[0]?.case_id ||
    "";

  const selectedCase = activeItems.find((item) => item.case_id === selectedCaseId) ?? null;
  const detailQuery = useWorkspaceCaseDetail(
    {
      workspace: "today",
      caseId: selectedCase?.case_id ?? "",
    },
    Boolean(selectedCase?.case_id),
  );

  const prepSessions = prep?.sessions ?? [];
  const selectedPrepItem = selectedCase ? findSessionPrepMatch(selectedCase, prepSessions) : null;
  const sessionsToPrepare =
    prep?.sessions.filter(
      (item) =>
        item.clinical_alerts.length > 0 ||
        item.health_checks.some((check) => check.status !== "ok"),
    ).length ?? 0;
  const sessionCount = prep?.total_sessions ?? 0;
  const alertClients = prep?.clients_with_alerts ?? 0;
  const dateLabel = formatDateLabel(prep?.current_time ?? prep?.date ?? today?.agenda.date ?? null);
  const brief = buildOggiBrief({
    focusCount: focusTotal,
    backlogCount: backlogTotal,
    totalSessions: sessionCount,
    alertClients,
    sessionsToPrepare,
  });

  const withFromParam = (href: string) => appendFromParam(href, "oggi");
  const supportLineForItem = (item: OperationalCase) => {
    const prepItem = findSessionPrepMatch(item, prepSessions);
    return prepItem ? buildClientSupportLine(prepItem) : null;
  };

  if (todayQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-28 rounded-[32px]" />
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.14fr)_minmax(360px,0.86fr)]">
          <Skeleton className="h-[720px] rounded-[32px]" />
          <Skeleton className="h-[720px] rounded-[32px]" />
        </div>
      </div>
    );
  }

  if (todayQuery.isError || !today) {
    return (
      <div className="rounded-[28px] border border-destructive/40 bg-destructive/5 p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 text-destructive" />
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-semibold text-destructive">Impossibile caricare Oggi</h1>
            <p className="mt-1 text-sm text-destructive/90">
              Il workspace operativo non e disponibile in questo momento.
            </p>
          </div>
        </div>
        <Button size="sm" className="mt-4 rounded-full" onClick={() => void todayQuery.refetch()}>
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Riprova
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <section
        className={revealClass(
          0,
          "rounded-[32px] border border-stone-200/80 bg-[radial-gradient(circle_at_top_left,rgba(251,191,36,0.12),transparent_28%),linear-gradient(140deg,rgba(255,255,255,0.99),rgba(249,247,243,0.98))] px-4 py-4 shadow-[0_24px_60px_-48px_rgba(41,37,36,0.32)] dark:border-zinc-800 dark:bg-[radial-gradient(circle_at_top_left,rgba(245,158,11,0.12),transparent_28%),linear-gradient(140deg,rgba(24,24,27,0.98),rgba(20,20,24,0.98))]",
        )}
        style={revealStyle(0)}
      >
        <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-stone-950 text-stone-50 dark:bg-zinc-100 dark:text-stone-950">
                <SunMedium className="h-4.5 w-4.5" />
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-[30px] font-bold tracking-[-0.03em] text-stone-950 dark:text-zinc-50">
                    Oggi
                  </h1>
                  <span className="rounded-full border border-stone-200/80 bg-white/80 px-2.5 py-1 text-[11px] font-medium capitalize text-stone-600 dark:border-zinc-700 dark:bg-zinc-950/70 dark:text-zinc-300">
                    {dateLabel ?? "workspace operativo"}
                  </span>
                </div>
                <p className="mt-1 text-[13px] leading-5 text-stone-700 dark:text-zinc-300">{brief}</p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <InlineCounter
              label="Adesso"
              value={today.summary.now_count}
              tone="border-red-200 bg-red-50/90 text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300"
            />
            <InlineCounter
              label="Focus"
              value={focusTotal}
              tone="border-amber-200 bg-amber-50/90 text-amber-700 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-300"
            />
            <InlineCounter
              label={alertClients > 0 ? "Alert" : "Backlog"}
              value={alertClients > 0 ? alertClients : backlogTotal}
              tone={
                alertClients > 0
                  ? "border-red-200 bg-red-50/90 text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300"
                  : "border-sky-200 bg-sky-50/90 text-sky-700 dark:border-sky-900/40 dark:bg-sky-950/20 dark:text-sky-300"
              }
            />
          </div>
        </div>

        <div className="mt-3 border-t border-stone-200/80 pt-3 dark:border-zinc-800">
          <WorkspaceAgendaPanel agenda={today.agenda} maxItems={1} />
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.14fr)_minmax(360px,0.86fr)] xl:items-start">
        <section
          className={revealClass(
            90,
            "overflow-hidden rounded-[32px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.99),rgba(247,245,241,0.98))] shadow-[0_28px_72px_-56px_rgba(41,37,36,0.34)] dark:border-zinc-800 dark:bg-[linear-gradient(180deg,rgba(24,24,27,0.98),rgba(20,20,24,0.98))]",
          )}
          style={revealStyle(90)}
        >
          <div className="border-b border-stone-200/80 px-4 py-4 dark:border-zinc-800">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div className="flex min-w-0 items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-stone-950 text-stone-50 dark:bg-zinc-100 dark:text-stone-950">
                  <LayoutList className="h-4.5 w-4.5" />
                </div>
                <div className="min-w-0">
                  <h2 className="text-[18px] font-semibold tracking-[-0.02em] text-stone-950 dark:text-zinc-50">
                    Queue operativa
                  </h2>
                  <p className="mt-0.5 text-[12px] leading-5 text-stone-600 dark:text-zinc-300">
                    Un feed unico, pochi filtri forti, selezione caso sempre visibile.
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-1.5">
                <QueueViewButton
                  label="Focus"
                  count={focusTotal}
                  active={effectiveQueueView === "focus"}
                  onClick={() => setQueueView("focus")}
                />
                <QueueViewButton
                  label="Linea completa"
                  count={focusTotal + backlogTotal}
                  active={effectiveQueueView === "all"}
                  onClick={() => setQueueView("all")}
                />
                <QueueViewButton
                  label="Backlog"
                  count={backlogTotal}
                  active={effectiveQueueView === "backlog"}
                  onClick={() => setQueueView("backlog")}
                />
              </div>
            </div>

            <div className="mt-3 flex flex-wrap gap-1.5 text-[11px] text-stone-600 dark:text-zinc-300">
              <span className="rounded-full border border-stone-200/80 bg-white/80 px-2.5 py-1 dark:border-zinc-700 dark:bg-zinc-950/70">
                {today.completed_today_count} completati oggi
              </span>
              {today.snoozed_count > 0 ? (
                <span className="rounded-full border border-stone-200/80 bg-white/80 px-2.5 py-1 dark:border-zinc-700 dark:bg-zinc-950/70">
                  {today.snoozed_count} in pausa
                </span>
              ) : null}
              {needsExpandedWaiting && waitingQuery.isLoading ? (
                <span className="rounded-full border border-stone-200/80 bg-white/80 px-2.5 py-1 dark:border-zinc-700 dark:bg-zinc-950/70">
                  Carico backlog completo...
                </span>
              ) : null}
            </div>
          </div>

          <ScrollArea className="xl:h-[calc(100vh-18rem)]">
            <div className="space-y-5 p-4">
              {!hasAnyOperationalCases ? (
                <EmptyState
                  icon={SunMedium}
                  title="Nessun caso aperto"
                  subtitle="La giornata e libera. Se vuoi, usala per follow-up, rinnovi o programmazione."
                />
              ) : activeSections.length === 0 ? (
                <div className="rounded-[24px] border border-dashed border-stone-300/80 px-4 py-5 text-sm text-stone-600 dark:border-zinc-700 dark:text-zinc-300">
                  Nessun caso visibile in questa vista.
                </div>
              ) : (
                activeSections.map((section) => (
                  <LaneSection
                    key={section.bucket}
                    section={section}
                    selectedCaseId={selectedCaseId}
                    onSelect={setRequestedCaseId}
                    supportLineForItem={supportLineForItem}
                    hrefTransform={withFromParam}
                  />
                ))
              )}

              {!hasAnyOperationalCases && prep?.non_client_events.length ? (
                <Button asChild variant="ghost" size="sm" className="w-fit rounded-full text-xs text-muted-foreground">
                  <Link href="/agenda">
                    Apri agenda completa
                    <ArrowRight className="ml-1 h-3.5 w-3.5" />
                  </Link>
                </Button>
              ) : null}
            </div>
          </ScrollArea>
        </section>

        <section
          className={revealClass(
            150,
            "overflow-hidden rounded-[32px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.99),rgba(247,245,241,0.98))] shadow-[0_28px_72px_-56px_rgba(41,37,36,0.34)] dark:border-zinc-800 dark:bg-[linear-gradient(180deg,rgba(24,24,27,0.98),rgba(20,20,24,0.98))] xl:sticky xl:top-5",
          )}
          style={revealStyle(150)}
        >
          <div className="flex flex-col xl:h-[calc(100vh-18rem)]">
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

            <div className="border-t border-stone-200/80 dark:border-zinc-800">
              {selectedPrepItem ? (
                <OggiClientContextPanel item={selectedPrepItem} embedded className="min-h-0" />
              ) : prepQuery.isError && selectedCase ? (
                <div className="px-4 py-4">
                  <div className="rounded-[20px] border border-stone-200/80 bg-white/80 px-3.5 py-3.5 text-sm text-stone-600 dark:border-zinc-800 dark:bg-zinc-950/50 dark:text-zinc-300">
                    Il contesto cliente della vecchia vista session-prep non e disponibile in questo momento.
                  </div>
                </div>
              ) : selectedCase ? (
                <div className="space-y-3 px-4 py-4">
                  <div className="rounded-[20px] border border-stone-200/80 bg-white/80 px-3.5 py-3.5 dark:border-zinc-800 dark:bg-zinc-950/50">
                    <div className="flex items-start gap-3">
                      <Users className="mt-0.5 h-4.5 w-4.5 text-stone-500 dark:text-zinc-400" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-stone-900 dark:text-zinc-50">
                          Contesto cliente non agganciato
                        </p>
                        <p className="mt-1 text-sm text-stone-600 dark:text-zinc-300">
                          Il caso resta operativo, ma non esiste una sessione di oggi da cui leggere readiness, alert o check rapidi.
                        </p>
                      </div>
                    </div>
                  </div>

                  {prep && alertClients > 0 ? (
                    <div className="rounded-[20px] border border-red-200/80 bg-red-50/90 px-3.5 py-3.5 dark:border-red-900/30 dark:bg-red-950/20">
                      <div className="flex items-start gap-3">
                        <ShieldAlert className="mt-0.5 h-4.5 w-4.5 shrink-0 text-red-600 dark:text-red-400" />
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-red-700 dark:text-red-300">
                            Alert clinici da tenere davanti
                          </p>
                          <p className="mt-1 text-sm text-red-700/85 dark:text-red-300/85">
                            {alertClients} {alertClients === 1 ? "cliente ha" : "clienti hanno"} una condizione clinica aperta nelle sessioni di oggi.
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
