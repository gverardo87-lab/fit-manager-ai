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
import { cn } from "@/lib/utils";
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
    <div className={cn("min-w-[130px] rounded-[24px] border px-4 py-3 shadow-sm backdrop-blur", tone)}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em]">{label}</p>
      <p className="mt-2 text-3xl font-black leading-none tracking-[-0.03em] tabular-nums">{value}</p>
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
  tone,
}: {
  title: string;
  subtitle: string;
  total: number;
  items: OperationalCase[];
  selectedCaseId: string;
  onSelect: (caseId: string) => void;
  emptyMessage: string;
  tone: string;
}) {
  return (
    <section className={cn("space-y-4 rounded-[28px] border p-4 shadow-sm", tone)}>
      <div className="border-b border-current/10 pb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-base font-semibold">{title}</h3>
          <span className="rounded-full border border-current/10 bg-white/70 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-current/80 dark:bg-zinc-950/40">
            {total}
          </span>
        </div>
        <p className="mt-1 text-sm text-current/75">{subtitle}</p>
        {total > items.length && items.length > 0 && (
          <p className="mt-2 text-xs text-current/60">
            Mostro {items.length} casi su {total} in questa vista iniziale.
          </p>
        )}
      </div>

      {items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-current/20 bg-white/55 px-4 py-5 text-sm text-current/65 dark:bg-zinc-950/30">
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
              variant="finance"
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
    <div className="space-y-6">
      <div
        className={revealClass(
          0,
          "relative overflow-hidden rounded-[34px] border border-stone-300/80 bg-[linear-gradient(135deg,rgba(255,251,235,0.98),rgba(255,244,230,0.98)_48%,rgba(255,237,213,0.96))] p-6 shadow-[0_35px_90px_-60px_rgba(124,45,18,0.45)] dark:border-zinc-800 dark:bg-[linear-gradient(135deg,rgba(28,25,23,0.98),rgba(39,39,42,0.98)_52%,rgba(17,24,39,0.98))]",
        )}
        style={revealStyle(0)}
      >
        <div className="pointer-events-none absolute inset-0 opacity-60">
          <div className="absolute -right-24 top-0 h-56 w-56 rounded-full bg-orange-300/20 blur-3xl dark:bg-orange-500/10" />
          <div className="absolute bottom-0 left-0 h-40 w-full bg-[linear-gradient(90deg,transparent,rgba(120,53,15,0.06),transparent)] dark:bg-[linear-gradient(90deg,transparent,rgba(251,191,36,0.08),transparent)]" />
        </div>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="relative z-10 max-w-3xl">
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-[20px] border border-stone-300/70 bg-stone-950 shadow-sm dark:border-zinc-700 dark:bg-amber-400">
                <HandCoins className="h-6 w-6 text-amber-300 dark:text-zinc-950" />
              </div>
              <div>
                <span className="inline-flex rounded-full border border-stone-300/80 bg-white/70 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-600 dark:border-zinc-700 dark:bg-zinc-900/70 dark:text-zinc-300">
                  Workspace privato
                </span>
                <h1 className="mt-3 text-3xl font-black tracking-[-0.04em] text-stone-950 sm:text-4xl dark:text-stone-50">
                  Rinnovi & Incassi
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-700 dark:text-zinc-300">
                  Una scrivania economica operativa, non il vecchio pannello cassa. Qui decidi cosa incassare, cosa rinnovare e cosa confermare prima che diventi rumore.
                </p>
              </div>
            </div>
            <p className="mt-5 max-w-2xl text-[15px] leading-7 text-stone-800 dark:text-zinc-200">{brief}</p>
            {totalCases > totalVisible && (
              <p className="mt-4 text-xs uppercase tracking-[0.16em] text-stone-500 dark:text-zinc-400">
                Vista iniziale dei primi {totalVisible} casi su {totalCases}, con budget per bucket e paginazione server-side.
              </p>
            )}
          </div>

          <div className="relative z-10 grid grid-cols-2 gap-3 lg:w-[340px]">
            <HeaderPill
              label="Critici"
              value={financeData.summary.now_count}
              tone="border-red-300/70 bg-red-50/90 text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300"
            />
            <HeaderPill
              label="Oggi"
              value={financeData.summary.today_count}
              tone="border-amber-300/70 bg-amber-50/90 text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300"
            />
            <HeaderPill
              label="Entro 7 giorni"
              value={financeData.summary.upcoming_7d_count}
              tone="border-orange-300/70 bg-orange-50/90 text-orange-700 dark:border-orange-900/50 dark:bg-orange-950/30 dark:text-orange-300"
            />
            <HeaderPill
              label="Da pianificare"
              value={financeData.summary.waiting_count}
              tone="border-stone-300/70 bg-stone-100/90 text-stone-700 dark:border-zinc-700 dark:bg-zinc-900/80 dark:text-zinc-300"
            />
          </div>
        </div>
      </div>

      <div className={revealClass(70)} style={revealStyle(70)}>
        <div className="overflow-x-auto rounded-[28px] border border-stone-300/80 bg-stone-950/95 p-2 shadow-[0_18px_50px_-36px_rgba(28,25,23,0.6)] dark:border-zinc-800 dark:bg-zinc-950">
          <div className="flex w-max min-w-full gap-2">
          {FINANCE_FILTERS.map((item) => {
            const isActive = item.id === filter;
            return (
              <button
                key={item.id}
                type="button"
                className={cn(
                  "rounded-[18px] px-4 py-2.5 text-sm font-medium transition-all",
                  isActive
                    ? "bg-[linear-gradient(135deg,rgba(251,191,36,1),rgba(253,186,116,1))] text-stone-950 shadow-[0_14px_40px_-28px_rgba(251,191,36,0.9)]"
                    : "text-stone-300 hover:bg-white/8 hover:text-stone-50",
                )}
                onClick={() => {
                  setFilter(item.id);
                  setRequestedCaseId("");
                  setShowWaiting(false);
                }}
              >
                {item.label}
              </button>
            );
          })}
          </div>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
        <div className={revealClass(120)} style={revealStyle(120)}>
          <div className="rounded-[32px] border border-stone-300/80 bg-[linear-gradient(180deg,rgba(255,252,248,0.98),rgba(248,245,241,0.96))] shadow-[0_30px_80px_-48px_rgba(120,53,15,0.28)] dark:border-zinc-800 dark:bg-[linear-gradient(180deg,rgba(39,39,42,0.98),rgba(24,24,27,0.96))]">
            <div className="border-b border-stone-300/70 px-5 py-5 dark:border-zinc-800">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-[18px] border border-stone-300/70 bg-stone-950 shadow-sm dark:border-zinc-700 dark:bg-amber-400">
                  <HandCoins className="h-5 w-5 text-amber-300 dark:text-zinc-950" />
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500 dark:text-zinc-400">
                    Coda operativa
                  </p>
                  <h2 className="mt-1 text-xl font-bold tracking-[-0.02em] text-stone-950 dark:text-stone-50">
                    Queue economica
                  </h2>
                  <p className="mt-1 text-sm text-stone-600 dark:text-zinc-400">
                    Prima i soldi che stanno gia bruciando, poi le scadenze che vuoi anticipare.
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
                      tone="border-red-300/70 bg-[linear-gradient(160deg,rgba(254,242,242,0.92),rgba(255,247,237,0.88))] text-red-800 dark:border-red-900/40 dark:bg-[linear-gradient(160deg,rgba(69,10,10,0.32),rgba(67,20,7,0.22))] dark:text-red-200"
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
                      tone="border-amber-300/70 bg-[linear-gradient(160deg,rgba(255,251,235,0.96),rgba(255,247,237,0.9))] text-amber-800 dark:border-amber-900/40 dark:bg-[linear-gradient(160deg,rgba(69,26,3,0.3),rgba(67,20,7,0.22))] dark:text-amber-200"
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
                      tone="border-orange-300/70 bg-[linear-gradient(160deg,rgba(255,247,237,0.96),rgba(255,251,235,0.9))] text-orange-800 dark:border-orange-900/40 dark:bg-[linear-gradient(160deg,rgba(67,20,7,0.28),rgba(69,26,3,0.2))] dark:text-orange-200"
                    />
                  )}

                  {waitingTotal > 0 && (
                    <section className="space-y-3">
                      <button
                        type="button"
                        onClick={() => setShowWaiting((current) => !current)}
                        className="flex w-full items-center justify-between rounded-[26px] border border-stone-300/80 bg-[linear-gradient(160deg,rgba(245,245,244,0.96),rgba(255,255,255,0.86))] px-4 py-4 text-left transition-colors hover:bg-stone-100 dark:border-zinc-800 dark:bg-[linear-gradient(160deg,rgba(39,39,42,0.96),rgba(24,24,27,0.9))] dark:hover:bg-zinc-900"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-base font-semibold text-stone-900 dark:text-stone-50">Da pianificare</h3>
                            <span className="rounded-full border border-stone-300/80 bg-white/80 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-stone-600 dark:border-zinc-700 dark:bg-zinc-950/60 dark:text-zinc-300">
                              {waitingTotal}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-stone-600 dark:text-zinc-400">
                            Backlog economico non urgente, utile quando la giornata si alleggerisce.
                          </p>
                          {showWaiting && waitingTotal > waitingItems.length && (
                            <p className="mt-1 text-xs text-stone-500 dark:text-zinc-500">
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
                              variant="finance"
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
              variant="finance"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
