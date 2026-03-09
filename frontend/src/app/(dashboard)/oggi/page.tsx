"use client";

import { useState } from "react";
import {
  AlertCircle,
  ChevronDown,
  ChevronRight,
  LayoutList,
  RefreshCw,
  SunMedium,
} from "lucide-react";

import { WorkspaceAgendaPanel } from "@/components/workspace/WorkspaceAgendaPanel";
import { WorkspaceCaseCard } from "@/components/workspace/WorkspaceCaseCard";
import { WorkspaceDetailPanel } from "@/components/workspace/WorkspaceDetailPanel";
import { WORKSPACE_BUCKET_META } from "@/components/workspace/workspace-ui";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceCaseDetail, useWorkspaceToday } from "@/hooks/useWorkspace";
import { usePageReveal } from "@/lib/page-reveal";
import type { OperationalCase } from "@/types/api";

function buildOggiBrief({
  nowCount,
  todayCount,
  laterCount,
  criticalCount,
}: {
  nowCount: number;
  todayCount: number;
  laterCount: number;
  criticalCount: number;
}): string {
  if (nowCount > 0 && criticalCount > 0) {
    return `Ti sto proteggendo da ${criticalCount} criticita e ${todayCount} task da chiudere oggi. Parti dal primo.`;
  }
  if (nowCount > 0) {
    return `Hai ${nowCount} casi che non dovrebbero aspettare. Dopo, ti restano ${todayCount} task da chiudere oggi.`;
  }
  if (todayCount > 0) {
    return `Hai ${todayCount} casi da chiudere oggi. Il primo e gia pronto nel tuo stack operativo.`;
  }
  if (laterCount > 0) {
    return `Oggi non hai urgenze forti. Puoi usare la giornata per anticipare ${laterCount} casi che possono aspettare poco.`;
  }
  return "Giornata pulita: nessun caso operativo urgente aperto in questo momento.";
}

function HeaderPill({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div className={`rounded-full border px-3 py-2 ${tone}`}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.16em]">{label}</p>
      <p className="mt-1 text-xl font-bold leading-none tabular-nums">{value}</p>
    </div>
  );
}

function QueueSection({
  title,
  subtitle,
  total,
  items,
  selectedCaseId,
  onSelect,
  emptyMessage,
}: {
  title: string;
  subtitle: string;
  total: number;
  items: OperationalCase[];
  selectedCaseId: string;
  onSelect: (caseId: string) => void;
  emptyMessage?: string;
}) {
  const helperText =
    total > items.length
      ? `${subtitle} Ti mostro i primi ${items.length} su ${total}.`
      : subtitle;

  return (
    <section className="space-y-3">
      <div>
        <div className="flex items-center gap-2">
          <h3 className="text-base font-semibold">{title}</h3>
          <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            {total}
          </span>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">{helperText}</p>
      </div>

      {items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border/70 px-4 py-5 text-sm text-muted-foreground">
          {emptyMessage ?? "Nessun caso in questa sezione."}
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <WorkspaceCaseCard
              key={item.case_id}
              item={item}
              selected={item.case_id === selectedCaseId}
              onSelect={() => onSelect(item.case_id)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

export default function OggiWorkspacePage() {
  const { revealClass, revealStyle } = usePageReveal();
  const todayQuery = useWorkspaceToday();
  const today = todayQuery.data;

  const [requestedCaseId, setRequestedCaseId] = useState("");
  const [showLater, setShowLater] = useState(false);

  const sectionsByBucket = new Map(today?.sections.map((section) => [section.bucket, section]) ?? []);
  const nowSection = sectionsByBucket.get("now");
  const todaySection = sectionsByBucket.get("today");
  const upcoming3dSection = sectionsByBucket.get("upcoming_3d");
  const upcoming7dSection = sectionsByBucket.get("upcoming_7d");
  const queueItems = [
    ...(nowSection?.items ?? []),
    ...(todaySection?.items ?? []),
    ...(upcoming3dSection?.items ?? []),
    ...(upcoming7dSection?.items ?? []),
  ];
  const nowItems = nowSection?.items ?? [];
  const dueTodayItems = todaySection?.items ?? [];
  const laterItems = [...(upcoming3dSection?.items ?? []), ...(upcoming7dSection?.items ?? [])];
  const laterTotal = (upcoming3dSection?.total ?? 0) + (upcoming7dSection?.total ?? 0);
  const selectedCaseId =
    (requestedCaseId && queueItems.some((item) => item.case_id === requestedCaseId) && requestedCaseId) ||
    queueItems[0]?.case_id ||
    today?.focus_case?.case_id ||
    "";
  const selectedCase =
    queueItems.find((item) => item.case_id === selectedCaseId) ??
    (today?.focus_case?.case_id === selectedCaseId ? today.focus_case : null);
  const detailQuery = useWorkspaceCaseDetail(
    {
      workspace: "today",
      caseId: selectedCase?.case_id ?? "",
    },
    Boolean(selectedCase?.case_id),
  );

  if (todayQuery.isLoading) {
    return (
      <div className="space-y-5">
        <Skeleton className="h-36 rounded-3xl" />
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
          <div className="space-y-4">
            <Skeleton className="h-32 rounded-3xl" />
            <Skeleton className="h-[620px] rounded-3xl" />
          </div>
          <Skeleton className="h-[620px] rounded-3xl" />
        </div>
      </div>
    );
  }

  if (todayQuery.isError || !today) {
    return (
      <div className="rounded-3xl border border-destructive/40 bg-destructive/5 p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 text-destructive" />
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-semibold text-destructive">Impossibile caricare Oggi</h1>
            <p className="mt-1 text-sm text-destructive/90">
              La tua modalita operativa non e disponibile in questo momento.
            </p>
          </div>
        </div>
        <Button size="sm" className="mt-4" onClick={() => void todayQuery.refetch()}>
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Riprova
        </Button>
      </div>
    );
  }

  const brief = buildOggiBrief({
    nowCount: today.summary.now_count,
    todayCount: today.summary.today_count,
    laterCount: today.summary.upcoming_7d_count,
    criticalCount: today.summary.critical_count,
  });

  const hasOperationalCases = queueItems.length > 0;

  return (
    <div className="space-y-5">
      <div
        className={revealClass(
          0,
          "rounded-3xl border border-border/70 bg-gradient-to-br from-stone-50 via-white to-emerald-50/40 p-5 shadow-sm dark:from-zinc-900 dark:via-zinc-900 dark:to-emerald-950/10",
        )}
        style={revealStyle(0)}
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-100 to-emerald-100 dark:from-amber-950/30 dark:to-emerald-950/30">
                <SunMedium className="h-5 w-5 text-amber-700 dark:text-amber-300" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Oggi</h1>
                <p className="text-sm text-muted-foreground">La tua modalita operativa, non una seconda dashboard.</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-foreground/85 sm:text-[15px]">{brief}</p>
          </div>

          <div className="flex flex-wrap gap-2">
            <HeaderPill
              label="Adesso"
              value={today.summary.now_count}
              tone="border-red-200 bg-red-50/80 text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300"
            />
            <HeaderPill
              label="Oggi"
              value={today.summary.today_count}
              tone="border-amber-200 bg-amber-50/80 text-amber-700 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-300"
            />
            <HeaderPill
              label="Puo aspettare"
              value={laterTotal}
              tone="border-blue-200 bg-blue-50/80 text-blue-700 dark:border-blue-900/40 dark:bg-blue-950/20 dark:text-blue-300"
            />
          </div>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
        <div className="space-y-4">
          <div className={revealClass(70)} style={revealStyle(70)}>
            <WorkspaceAgendaPanel agenda={today.agenda} maxItems={1} />
          </div>

          <div className={revealClass(120)} style={revealStyle(120)}>
            <div className="rounded-3xl border border-border/70 bg-white shadow-sm dark:bg-zinc-900">
              <div className="border-b px-5 py-5">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-100 to-amber-100 dark:from-orange-950/30 dark:to-amber-950/30">
                    <LayoutList className="h-4.5 w-4.5 text-orange-700 dark:text-orange-300" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold">Stack operativo</h2>
                    <p className="text-sm text-muted-foreground">
                      Ti mostro prima cosa chiudere, poi il resto.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-5 p-5">
                {!hasOperationalCases ? (
                  <EmptyState
                    icon={SunMedium}
                    title="Nessun caso aperto"
                    subtitle="La giornata e libera. Se vuoi, puoi usare oggi per rinnovi o riattivazioni."
                  />
                ) : (
                  <>
                    <QueueSection
                      title={WORKSPACE_BUCKET_META.now.label}
                      subtitle="Quello che non dovrebbe aspettare."
                      total={nowSection?.total ?? 0}
                      items={nowItems}
                      selectedCaseId={selectedCaseId}
                      onSelect={setRequestedCaseId}
                      emptyMessage="Niente che richieda attenzione immediata."
                    />

                    <QueueSection
                      title={WORKSPACE_BUCKET_META.today.label}
                      subtitle="Quello che conviene chiudere in questa giornata."
                      total={todaySection?.total ?? 0}
                      items={dueTodayItems}
                      selectedCaseId={selectedCaseId}
                      onSelect={setRequestedCaseId}
                      emptyMessage="Non hai altri casi da chiudere oggi."
                    />

                    {laterTotal > 0 && (
                      <section className="space-y-3">
                        <button
                          type="button"
                          onClick={() => setShowLater((current) => !current)}
                          className="flex w-full items-center justify-between rounded-2xl border border-border/70 bg-muted/20 px-4 py-3 text-left transition-colors hover:bg-muted/40"
                        >
                          <div>
                            <div className="flex items-center gap-2">
                              <h3 className="text-base font-semibold">Puo aspettare</h3>
                              <span className="rounded-full bg-background px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                                {laterTotal}
                              </span>
                            </div>
                            <p className="mt-1 text-sm text-muted-foreground">
                              Casi che non stanno bruciando ora, ma che non vuoi dimenticare.
                            </p>
                          </div>
                          {showLater ? (
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-muted-foreground" />
                          )}
                        </button>

                        {showLater && (
                          <div className="space-y-3">
                            {laterItems.map((item) => (
                              <WorkspaceCaseCard
                                key={item.case_id}
                                item={item}
                                selected={item.case_id === selectedCaseId}
                                onSelect={() => setRequestedCaseId(item.case_id)}
                              />
                            ))}
                          </div>
                        )}
                      </section>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className={revealClass(170)} style={revealStyle(170)}>
          <div className="xl:sticky xl:top-6">
            <WorkspaceDetailPanel
              selectedCase={selectedCase}
              detail={detailQuery.data}
              isLoading={detailQuery.isLoading}
              isError={detailQuery.isError}
              onRetry={() => void detailQuery.refetch()}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
