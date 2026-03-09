"use client";

import { useState } from "react";
import {
  AlertCircle,
  ChevronDown,
  ChevronRight,
  HandCoins,
  RefreshCw,
} from "lucide-react";

import { WorkspaceCaseCard } from "@/components/workspace/WorkspaceCaseCard";
import { WorkspaceDetailPanel } from "@/components/workspace/WorkspaceDetailPanel";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceCaseDetail, useWorkspaceCases } from "@/hooks/useWorkspace";
import type { WorkspaceCasesQuery } from "@/hooks/useWorkspace";
import { usePageReveal } from "@/lib/page-reveal";
import type { OperationalCase } from "@/types/api";

type FinanceFilter =
  | "all"
  | "payment_overdue"
  | "payment_due_soon"
  | "contract_renewal_due"
  | "recurring_expense_due";

const FINANCE_FILTERS: Array<{
  id: FinanceFilter;
  label: string;
  caseKind?: WorkspaceCasesQuery["case_kind"];
}> = [
  { id: "all", label: "Tutti" },
  { id: "payment_overdue", label: "Incassi in ritardo", caseKind: "payment_overdue" },
  { id: "payment_due_soon", label: "Incassi in arrivo", caseKind: "payment_due_soon" },
  { id: "contract_renewal_due", label: "Rinnovi", caseKind: "contract_renewal_due" },
  { id: "recurring_expense_due", label: "Spese ricorrenti", caseKind: "recurring_expense_due" },
];

const FINANCE_VIEWPORT_LIMITS = {
  now: 3,
  today: 4,
  upcoming_3d: 3,
  upcoming_7d: 3,
  waiting: 6,
} as const;

function buildFinanceBrief({
  criticalCount,
  todayCount,
  upcomingCount,
  waitingCount,
}: {
  criticalCount: number;
  todayCount: number;
  upcomingCount: number;
  waitingCount: number;
}) {
  if (criticalCount > 0) {
    return `Hai ${criticalCount} casi economici critici. Parti dagli incassi gia in ritardo, poi passa a rinnovi e scadenze vicine.`;
  }
  if (todayCount > 0) {
    return `Hai ${todayCount} casi economici da muovere oggi. Qui puoi lavorare rinnovi e incassi senza entrare subito nel ledger.`;
  }
  if (upcomingCount > 0) {
    return `Non hai urgenze economiche forti oggi. Puoi usare questa pagina per anticipare ${upcomingCount} scadenze dei prossimi 7 giorni.`;
  }
  if (waitingCount > 0) {
    return `La pressione economica e bassa. Ti resta solo backlog da pianificare con calma.`;
  }
  return "Nessuna pressione economica aperta in questo momento.";
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

function FinanceQueueSection({
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
  emptyMessage: string;
}) {
  return (
    <section className="space-y-3">
      <div>
        <div className="flex items-center gap-2">
          <h3 className="text-base font-semibold">{title}</h3>
          <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            {total}
          </span>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
        {total > items.length && items.length > 0 && (
          <p className="mt-1 text-xs text-muted-foreground">
            Mostro {items.length} casi su {total} in questa vista iniziale.
          </p>
        )}
      </div>

      {items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border/70 px-4 py-5 text-sm text-muted-foreground">
          {emptyMessage}
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <WorkspaceCaseCard
              key={item.case_id}
              item={item}
              selected={item.case_id === selectedCaseId}
              onSelect={() => onSelect(item.case_id)}
              showFinanceSummary
            />
          ))}
        </div>
      )}
    </section>
  );
}

export default function RenewalsCashWorkspacePage() {
  const { revealClass, revealStyle } = usePageReveal();
  const [filter, setFilter] = useState<FinanceFilter>("all");
  const [requestedCaseId, setRequestedCaseId] = useState("");
  const [showWaiting, setShowWaiting] = useState(false);

  const selectedFilter = FINANCE_FILTERS.find((item) => item.id === filter) ?? FINANCE_FILTERS[0];
  const summaryQuery = useWorkspaceCases(
    {
      workspace: "renewals_cash",
      page: 1,
      page_size: 1,
      sort_by: "priority",
      case_kind: selectedFilter.caseKind,
    },
    true,
  );
  const criticalQuery = useWorkspaceCases(
    {
      workspace: "renewals_cash",
      page: 1,
      page_size: FINANCE_VIEWPORT_LIMITS.now,
      sort_by: "priority",
      bucket: "now",
      case_kind: selectedFilter.caseKind,
    },
    true,
  );
  const todayQuery = useWorkspaceCases(
    {
      workspace: "renewals_cash",
      page: 1,
      page_size: FINANCE_VIEWPORT_LIMITS.today,
      sort_by: "priority",
      bucket: "today",
      case_kind: selectedFilter.caseKind,
    },
    true,
  );
  const upcoming3dQuery = useWorkspaceCases(
    {
      workspace: "renewals_cash",
      page: 1,
      page_size: FINANCE_VIEWPORT_LIMITS.upcoming_3d,
      sort_by: "priority",
      bucket: "upcoming_3d",
      case_kind: selectedFilter.caseKind,
    },
    true,
  );
  const upcoming7dQuery = useWorkspaceCases(
    {
      workspace: "renewals_cash",
      page: 1,
      page_size: FINANCE_VIEWPORT_LIMITS.upcoming_7d,
      sort_by: "priority",
      bucket: "upcoming_7d",
      case_kind: selectedFilter.caseKind,
    },
    true,
  );
  const waitingQuery = useWorkspaceCases(
    {
      workspace: "renewals_cash",
      page: 1,
      page_size: FINANCE_VIEWPORT_LIMITS.waiting,
      sort_by: "priority",
      bucket: "waiting",
      case_kind: selectedFilter.caseKind,
    },
    showWaiting,
  );

  const financeData = summaryQuery.data;
  const criticalItems = criticalQuery.data?.items ?? [];
  const criticalTotal = criticalQuery.data?.total ?? 0;
  const todayItems = todayQuery.data?.items ?? [];
  const todayTotal = todayQuery.data?.total ?? 0;
  const upcoming3dItems = upcoming3dQuery.data?.items ?? [];
  const upcoming7dItems = upcoming7dQuery.data?.items ?? [];
  const upcomingItems = [...upcoming3dItems, ...upcoming7dItems];
  const upcomingTotal = (upcoming3dQuery.data?.total ?? 0) + (upcoming7dQuery.data?.total ?? 0);
  const waitingItems = waitingQuery.data?.items ?? [];
  const waitingTotal = financeData?.summary.waiting_count ?? waitingQuery.data?.total ?? 0;
  const visibleItems = [...criticalItems, ...todayItems, ...upcomingItems, ...(showWaiting ? waitingItems : [])];
  const selectedCaseId =
    (requestedCaseId && visibleItems.some((item) => item.case_id === requestedCaseId) && requestedCaseId) ||
    visibleItems[0]?.case_id ||
    "";
  const selectedCase = visibleItems.find((item) => item.case_id === selectedCaseId) ?? null;
  const detailQuery = useWorkspaceCaseDetail(
    {
      workspace: "renewals_cash",
      caseId: selectedCase?.case_id ?? "",
    },
    Boolean(selectedCase?.case_id),
  );
  const isLoading =
    summaryQuery.isLoading ||
    criticalQuery.isLoading ||
    todayQuery.isLoading ||
    upcoming3dQuery.isLoading ||
    upcoming7dQuery.isLoading ||
    (showWaiting && waitingQuery.isLoading);
  const isError =
    summaryQuery.isError ||
    criticalQuery.isError ||
    todayQuery.isError ||
    upcoming3dQuery.isError ||
    upcoming7dQuery.isError ||
    (showWaiting && waitingQuery.isError);

  if (isLoading && !financeData) {
    return (
      <div className="space-y-5">
        <Skeleton className="h-36 rounded-3xl" />
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
          <Skeleton className="h-[760px] rounded-3xl" />
          <Skeleton className="h-[760px] rounded-3xl" />
        </div>
      </div>
    );
  }

  if (isError || !financeData) {
    return (
      <div className="rounded-3xl border border-destructive/40 bg-destructive/5 p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 text-destructive" />
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-semibold text-destructive">Impossibile caricare Rinnovi & Incassi</h1>
            <p className="mt-1 text-sm text-destructive/90">
              La coda economico-contabile non e disponibile in questo momento.
            </p>
          </div>
        </div>
        <Button
          size="sm"
          className="mt-4"
          onClick={() => {
            void summaryQuery.refetch();
            void criticalQuery.refetch();
            void todayQuery.refetch();
            void upcoming3dQuery.refetch();
            void upcoming7dQuery.refetch();
            if (showWaiting) void waitingQuery.refetch();
          }}
        >
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Riprova
        </Button>
      </div>
    );
  }

  const brief = buildFinanceBrief({
    criticalCount: financeData.summary.now_count,
    todayCount: financeData.summary.today_count,
    upcomingCount: financeData.summary.upcoming_7d_count,
    waitingCount: financeData.summary.waiting_count,
  });
  const totalVisible = criticalItems.length + todayItems.length + upcomingItems.length + (showWaiting ? waitingItems.length : 0);
  const totalCases =
    financeData.summary.now_count +
    financeData.summary.today_count +
    financeData.summary.upcoming_7d_count +
    financeData.summary.waiting_count;
  const hasCases = totalCases > 0;

  return (
    <div className="space-y-5">
      <div
        className={revealClass(
          0,
          "rounded-3xl border border-border/70 bg-gradient-to-br from-stone-50 via-white to-rose-50/40 p-5 shadow-sm dark:from-zinc-900 dark:via-zinc-900 dark:to-rose-950/10",
        )}
        style={revealStyle(0)}
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-100 to-orange-100 dark:from-rose-950/30 dark:to-orange-950/30">
                <HandCoins className="h-5 w-5 text-rose-700 dark:text-rose-300" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Rinnovi & Incassi</h1>
                <p className="text-sm text-muted-foreground">
                  Il tuo cockpit economico privato, separato dalla dashboard e dal ledger.
                </p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-foreground/85 sm:text-[15px]">{brief}</p>
            {totalCases > totalVisible && (
              <p className="mt-3 text-xs text-muted-foreground">
                Vista iniziale dei primi {totalVisible} casi su {totalCases}, con budget per bucket e paginazione server-side.
              </p>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            <HeaderPill
              label="Critici"
              value={financeData.summary.now_count}
              tone="border-red-200 bg-red-50/80 text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300"
            />
            <HeaderPill
              label="Oggi"
              value={financeData.summary.today_count}
              tone="border-amber-200 bg-amber-50/80 text-amber-700 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-300"
            />
            <HeaderPill
              label="Entro 7 giorni"
              value={financeData.summary.upcoming_7d_count}
              tone="border-orange-200 bg-orange-50/80 text-orange-700 dark:border-orange-900/40 dark:bg-orange-950/20 dark:text-orange-300"
            />
            <HeaderPill
              label="Da pianificare"
              value={financeData.summary.waiting_count}
              tone="border-zinc-200 bg-zinc-50/80 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900/70 dark:text-zinc-300"
            />
          </div>
        </div>
      </div>

      <div className={revealClass(70)} style={revealStyle(70)}>
        <div className="flex flex-wrap gap-2">
          {FINANCE_FILTERS.map((item) => {
            const isActive = item.id === filter;
            return (
              <Button
                key={item.id}
                type="button"
                variant={isActive ? "default" : "outline"}
                size="sm"
                className="h-9"
                onClick={() => {
                  setFilter(item.id);
                  setRequestedCaseId("");
                  setShowWaiting(false);
                }}
              >
                {item.label}
              </Button>
            );
          })}
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
        <div className={revealClass(120)} style={revealStyle(120)}>
          <div className="rounded-3xl border border-border/70 bg-white shadow-sm dark:bg-zinc-900">
            <div className="border-b px-5 py-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-100 to-orange-100 dark:from-rose-950/30 dark:to-orange-950/30">
                  <HandCoins className="h-4.5 w-4.5 text-rose-700 dark:text-rose-300" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold">Queue economica</h2>
                  <p className="text-sm text-muted-foreground">
                    Qui lavori prima i soldi che stanno gia bruciando, poi il resto della pressione vicina.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-5 p-5">
              {!hasCases ? (
                <EmptyState
                  icon={HandCoins}
                  title="Nessuna pressione economica aperta"
                  subtitle="In questo filtro non hai casi da gestire. Puoi tornare piu tardi o cambiare vista."
                />
              ) : (
                <>
                  {criticalTotal > 0 && (
                    <FinanceQueueSection
                      title="Critici"
                      subtitle="Incassi gia in ritardo o casi che non dovrebbero aspettare."
                      total={criticalTotal}
                      items={criticalItems}
                      selectedCaseId={selectedCaseId}
                      onSelect={setRequestedCaseId}
                      emptyMessage="Nessun caso economico critico."
                    />
                  )}

                  {todayTotal > 0 && (
                    <FinanceQueueSection
                      title="Oggi"
                      subtitle="Scadenze e rinnovi che conviene chiudere in questa giornata."
                      total={todayTotal}
                      items={todayItems}
                      selectedCaseId={selectedCaseId}
                      onSelect={setRequestedCaseId}
                      emptyMessage="Nessun caso economico da chiudere oggi."
                    />
                  )}

                  {upcomingTotal > 0 && (
                    <FinanceQueueSection
                      title="Entro 7 giorni"
                      subtitle="Pressione economica vicina che vuoi anticipare prima che diventi critica."
                      total={upcomingTotal}
                      items={upcomingItems}
                      selectedCaseId={selectedCaseId}
                      onSelect={setRequestedCaseId}
                      emptyMessage="Nessun caso economico in arrivo nei prossimi 7 giorni."
                    />
                  )}

                  {waitingTotal > 0 && (
                    <section className="space-y-3">
                      <button
                        type="button"
                        onClick={() => setShowWaiting((current) => !current)}
                        className="flex w-full items-center justify-between rounded-2xl border border-border/70 bg-muted/20 px-4 py-3 text-left transition-colors hover:bg-muted/40"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-base font-semibold">Da pianificare</h3>
                            <span className="rounded-full bg-background px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                              {waitingTotal}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-muted-foreground">
                            Backlog economico non urgente, utile quando la giornata si alleggerisce.
                          </p>
                          {showWaiting && waitingTotal > waitingItems.length && (
                            <p className="mt-1 text-xs text-muted-foreground">
                              Mostro {waitingItems.length} casi su {waitingTotal} in questa vista iniziale.
                            </p>
                          )}
                        </div>
                        {showWaiting ? (
                          <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        )}
                      </button>

                      {showWaiting && (
                        <div className="space-y-3">
                          {waitingItems.map((item) => (
                            <WorkspaceCaseCard
                              key={item.case_id}
                              item={item}
                              selected={item.case_id === selectedCaseId}
                              onSelect={() => setRequestedCaseId(item.case_id)}
                              showFinanceSummary
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
