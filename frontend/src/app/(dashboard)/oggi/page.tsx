"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
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
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceCaseDetail, useWorkspaceCases, useWorkspaceToday } from "@/hooks/useWorkspace";
import { usePageReveal } from "@/lib/page-reveal";
import type { CaseBucket, OperationalCase, WorkspaceTodaySection } from "@/types/api";

interface SummaryMetricProps {
  label: string;
  value: number;
  tone: string;
}

function SummaryMetric({ label, value, tone }: SummaryMetricProps) {
  return (
    <div className={`rounded-2xl border p-4 ${tone}`}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-2 text-3xl font-extrabold tabular-nums leading-none">{value}</p>
    </div>
  );
}

function FocusCasePanel({
  item,
  onOpenInQueue,
}: {
  item: OperationalCase;
  onOpenInQueue: () => void;
}) {
  const primaryAction = item.suggested_actions.find((action) => action.is_primary) ?? item.suggested_actions[0];

  return (
    <div className="relative overflow-hidden rounded-[28px] border border-teal-300/40 bg-gradient-to-br from-teal-600 via-teal-700 to-emerald-800 p-6 text-white shadow-[0_30px_70px_-36px_rgba(13,148,136,0.85)]">
      <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-12 left-0 h-36 w-36 rounded-full bg-emerald-300/10 blur-3xl" />

      <div className="relative">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-white/15 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/80">
            Next Best Action
          </span>
          <span className="rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/75">
            {item.signal_count} segnali
          </span>
        </div>

        <h2 className="mt-4 text-2xl font-bold tracking-tight sm:text-[30px]">{item.title}</h2>
        <p className="mt-2 max-w-2xl text-sm text-white/75 sm:text-[15px]">{item.reason}</p>

        <div className="mt-5 flex flex-wrap gap-2">
          {primaryAction?.href ? (
            <Button asChild size="sm" className="h-10 bg-white text-teal-800 hover:bg-white/90">
              <Link href={primaryAction.href}>
                {primaryAction.label}
                <ArrowRight className="ml-1 h-3.5 w-3.5" />
              </Link>
            </Button>
          ) : (
            <Button size="sm" className="h-10 bg-white text-teal-800 hover:bg-white/90" disabled>
              {primaryAction?.label ?? "Apri"}
            </Button>
          )}
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="h-10 border-white/20 bg-white/10 text-white hover:bg-white/15 hover:text-white"
            onClick={onOpenInQueue}
          >
            Apri in coda
          </Button>
        </div>

        {item.preview_signals.length > 0 && (
          <div className="mt-5 grid gap-2 sm:grid-cols-2">
            {item.preview_signals.map((signal) => (
              <div
                key={`${item.case_id}-${signal.signal_code}`}
                className="rounded-2xl border border-white/10 bg-white/10 px-3 py-3 backdrop-blur-sm"
              >
                <p className="text-sm font-medium text-white">{signal.label}</p>
                <p className="mt-1 text-xs text-white/70">{signal.reason}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function QueueSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, index) => (
        <Skeleton key={index} className="h-36 rounded-2xl" />
      ))}
    </div>
  );
}

export default function OggiWorkspacePage() {
  const { revealClass, revealStyle } = usePageReveal();
  const todayQuery = useWorkspaceToday();
  const today = todayQuery.data;
  const sections = useMemo(() => today?.sections ?? [], [today?.sections]);

  const [requestedBucket, setRequestedBucket] = useState<CaseBucket>("now");
  const [requestedCaseId, setRequestedCaseId] = useState("");

  const firstNonEmptyBucket = useMemo(() => {
    return sections.find((section) => section.total > 0)?.bucket ?? "today";
  }, [sections]);
  const activeBucket = useMemo(() => {
    const matchingSection = sections.find((section) => section.bucket === requestedBucket);
    if (matchingSection?.total) return requestedBucket;
    return firstNonEmptyBucket;
  }, [firstNonEmptyBucket, requestedBucket, sections]);

  const casesQuery = useWorkspaceCases(
    {
      workspace: "today",
      bucket: activeBucket,
      page_size: 24,
      sort_by: "priority",
    },
    Boolean(today),
  );
  const selectedCaseId = (() => {
    const items = casesQuery.data?.items ?? [];
    if (requestedCaseId && items.some((item) => item.case_id === requestedCaseId)) {
      return requestedCaseId;
    }
    if (
      today?.focus_case?.bucket === activeBucket &&
      items.some((item) => item.case_id === today.focus_case!.case_id)
    ) {
      return today.focus_case!.case_id;
    }
    return items[0]?.case_id ?? today?.focus_case?.case_id ?? "";
  })();

  const selectedCase = (() => {
    const listMatch = casesQuery.data?.items.find((item) => item.case_id === selectedCaseId);
    if (listMatch) return listMatch;
    if (today?.focus_case?.case_id === selectedCaseId) return today.focus_case;
    return casesQuery.data?.items[0] ?? today?.focus_case ?? null;
  })();

  const detailQuery = useWorkspaceCaseDetail(
    {
      workspace: "today",
      caseId: selectedCase?.case_id ?? "",
    },
    Boolean(selectedCase?.case_id),
  );

  const activeSection = sections.find((section) => section.bucket === activeBucket);

  if (todayQuery.isLoading) {
    return (
      <div className="space-y-5">
        <Skeleton className="h-40 rounded-[28px]" />
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-28 rounded-2xl" />
          ))}
        </div>
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
          <Skeleton className="h-[360px] rounded-3xl" />
          <Skeleton className="h-[360px] rounded-3xl" />
        </div>
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
          <Skeleton className="h-[620px] rounded-3xl" />
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
            <h1 className="text-base font-semibold text-destructive">Impossibile caricare il workspace Oggi</h1>
            <p className="mt-1 text-sm text-destructive/90">
              La home operativa non e disponibile in questo momento. Puoi riprovare oppure tornare alla dashboard classica.
            </p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button size="sm" onClick={() => void todayQuery.refetch()}>
            <RefreshCw className="mr-2 h-3.5 w-3.5" />
            Riprova
          </Button>
          <Button asChild size="sm" variant="outline">
            <Link href="/">Apri Dashboard</Link>
          </Button>
        </div>
      </div>
    );
  }

  const hasOperationalCases = sections.some((section) => section.total > 0);

  return (
    <div className="space-y-5">
      <div
        className={revealClass(0, "rounded-[28px] border border-border/70 bg-gradient-to-br from-stone-50 via-white to-emerald-50/50 p-6 shadow-sm dark:from-zinc-900 dark:via-zinc-900 dark:to-emerald-950/10")}
        style={revealStyle(0)}
      >
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-100 to-emerald-100 dark:from-amber-950/30 dark:to-emerald-950/30">
                <SunMedium className="h-5 w-5 text-amber-700 dark:text-amber-300" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Oggi</h1>
                <p className="text-sm text-muted-foreground">
                  La tua coda operativa unificata: agenda, onboarding, rinnovi e follow-up.
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline" size="sm" className="h-9">
              <Link href="/">Dashboard classica</Link>
            </Button>
            <Button asChild size="sm" className="h-9">
              <Link href="/agenda">
                Apri agenda
                <ArrowRight className="ml-1 h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <SummaryMetric
            label="Da fare ora"
            value={today.summary.now_count}
            tone="border-red-200 bg-red-50/80 text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300"
          />
          <SummaryMetric
            label="Oggi"
            value={today.summary.today_count}
            tone="border-amber-200 bg-amber-50/80 text-amber-700 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-300"
          />
          <SummaryMetric
            label="Entro 7 giorni"
            value={today.summary.upcoming_7d_count}
            tone="border-blue-200 bg-blue-50/80 text-blue-700 dark:border-blue-900/40 dark:bg-blue-950/20 dark:text-blue-300"
          />
          <SummaryMetric
            label="Completati oggi"
            value={today.completed_today_count}
            tone="border-emerald-200 bg-emerald-50/80 text-emerald-700 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-300"
          />
        </div>
      </div>

      {hasOperationalCases ? (
        <>
          <div
            className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]"
          >
            <div className={revealClass(60)} style={revealStyle(60)}>
              {today.focus_case ? (
                <FocusCasePanel
                  item={today.focus_case}
                  onOpenInQueue={() => {
                    setRequestedBucket(today.focus_case?.bucket ?? activeBucket);
                    setRequestedCaseId(today.focus_case?.case_id ?? "");
                  }}
                />
              ) : (
                <div className="rounded-[28px] border border-border/70 bg-white p-6 shadow-sm dark:bg-zinc-900">
                  <EmptyState
                    icon={SunMedium}
                    title="Nessun caso prioritario in questo momento"
                    subtitle="La coda Oggi e pulita. Puoi usare la giornata per pianificare rinnovi o follow-up."
                    className="w-full border-0 bg-transparent py-6"
                  />
                </div>
              )}
            </div>
            <div className={revealClass(110)} style={revealStyle(110)}>
              <WorkspaceAgendaPanel agenda={today.agenda} />
            </div>
          </div>

          <div
            className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]"
          >
            <div className={revealClass(160)} style={revealStyle(160)}>
              <div className="rounded-3xl border border-border/70 bg-white shadow-sm dark:bg-zinc-900">
                <div className="border-b px-5 py-5">
                  <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-100 to-amber-100 dark:from-orange-950/30 dark:to-amber-950/30">
                          <LayoutList className="h-4.5 w-4.5 text-orange-700 dark:text-orange-300" />
                        </div>
                        <div>
                          <h2 className="text-lg font-semibold">Coda operativa</h2>
                          <p className="text-sm text-muted-foreground">
                            Seleziona un bucket per lavorare senza rumore.
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {sections.map((section: WorkspaceTodaySection) => {
                        const meta = WORKSPACE_BUCKET_META[section.bucket];
                        const isActive = activeBucket === section.bucket;
                        const disabled = section.total === 0;

                        return (
                          <button
                            key={section.bucket}
                            type="button"
                            disabled={disabled}
                            onClick={() => setRequestedBucket(section.bucket)}
                            className={[
                              "min-w-[88px] rounded-2xl border px-3 py-2 text-left transition-all",
                              isActive
                                ? "border-primary/40 bg-primary/5 shadow-sm"
                                : "border-border/70 bg-background hover:bg-muted/40",
                              disabled ? "cursor-not-allowed opacity-45" : "",
                            ].join(" ")}
                          >
                            <p className={`text-[10px] font-semibold uppercase tracking-[0.16em] ${meta.tone}`}>
                              {meta.shortLabel}
                            </p>
                            <p className="mt-1 text-xl font-bold tabular-nums">{section.total}</p>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                <div className="px-5 pb-5 pt-4">
                  {casesQuery.isLoading ? (
                    <QueueSkeleton />
                  ) : casesQuery.isError ? (
                    <div className="rounded-2xl border border-destructive/40 bg-destructive/5 p-4">
                      <p className="text-sm text-destructive">
                        Impossibile caricare il bucket selezionato.
                      </p>
                      <Button variant="outline" size="sm" className="mt-3" onClick={() => void casesQuery.refetch()}>
                        Riprova
                      </Button>
                    </div>
                  ) : activeSection?.total === 0 || !casesQuery.data?.items.length ? (
                    <EmptyState
                      icon={LayoutList}
                      title={`Nessun caso in ${WORKSPACE_BUCKET_META[activeBucket].label.toLowerCase()}`}
                      subtitle="Il bucket selezionato non contiene ancora casi operativi visibili."
                    />
                  ) : (
                    <ScrollArea className="xl:h-[620px]">
                      <div className="space-y-3">
                        {casesQuery.data.items.map((item) => (
                          <WorkspaceCaseCard
                            key={item.case_id}
                            item={item}
                            selected={item.case_id === selectedCase?.case_id}
                            onSelect={() => setRequestedCaseId(item.case_id)}
                          />
                        ))}
                      </div>
                    </ScrollArea>
                  )}
                </div>
              </div>
            </div>

            <div className={revealClass(210)} style={revealStyle(210)}>
              <WorkspaceDetailPanel
                selectedCase={selectedCase}
                detail={detailQuery.data}
                isLoading={detailQuery.isLoading}
                isError={detailQuery.isError}
                onRetry={() => void detailQuery.refetch()}
              />
            </div>
          </div>
        </>
      ) : (
        <div className={revealClass(80)} style={revealStyle(80)}>
          <EmptyState
            icon={SunMedium}
            title="Oggi e vuoto"
            subtitle="Non risultano casi operativi attivi. Puoi iniziare da agenda, clienti o dashboard classica."
            action={{
              label: "Apri dashboard",
              onClick: () => {
                window.location.href = "/";
              },
            }}
            className="rounded-3xl bg-white py-20 shadow-sm dark:bg-zinc-900"
          />
        </div>
      )}
    </div>
  );
}
