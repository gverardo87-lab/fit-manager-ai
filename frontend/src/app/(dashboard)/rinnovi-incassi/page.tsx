"use client";

import Link from "next/link";
import { useRef } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  AlertCircle,
  ArrowUpRight,
  ChevronDown,
  ChevronRight,
  HandCoins,
  RefreshCw,
} from "lucide-react";

import { WorkspaceDetailPanel } from "@/components/workspace/WorkspaceDetailPanel";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceCaseDetail, useWorkspaceCases } from "@/hooks/useWorkspace";
import type { WorkspaceCasesQuery } from "@/hooks/useWorkspace";
import { usePageReveal } from "@/lib/page-reveal";
import { cn } from "@/lib/utils";
import type { OperationalCase } from "@/types/api";
import {
  getFinanceCaseKindMeta,
  getFinanceSeverityMeta,
  formatFinanceAmount,
  formatWorkspaceDate,
  getCaseDueLabel,
  getFinanceSummary,
} from "@/components/workspace/workspace-ui";

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
    <div className={cn("min-w-[108px] rounded-[18px] border px-3 py-2 shadow-[0_16px_38px_-28px_rgba(31,42,51,0.18)] backdrop-blur", tone)}>
      <p className="text-[9px] font-semibold uppercase tracking-[0.18em]">{label}</p>
      <p className="mt-1 text-[26px] font-black leading-none tracking-[-0.04em] tabular-nums">{value}</p>
    </div>
  );
}

function getFinanceAmountMeta(item: OperationalCase): { label: string; value: string; secondary: string | null } {
  const dueAmount = formatFinanceAmount(item.finance_context?.total_due_amount);
  const residualAmount = formatFinanceAmount(item.finance_context?.total_residual_amount);

  if (item.case_kind === "recurring_expense_due") {
    return {
      label: "Uscita",
      value: dueAmount ?? residualAmount ?? "n/d",
      secondary: null,
    };
  }

  if (item.case_kind === "payment_due_soon") {
    return {
      label: "In arrivo",
      value: dueAmount ?? residualAmount ?? "n/d",
      secondary: residualAmount && residualAmount !== dueAmount ? `Residuo ${residualAmount}` : null,
    };
  }

  if (item.case_kind === "contract_renewal_due") {
    return {
      label: "Residuo",
      value: residualAmount ?? dueAmount ?? "n/d",
      secondary: dueAmount ? `Incasso ${dueAmount}` : null,
    };
  }

  return {
    label: "Da incassare",
    value: dueAmount ?? residualAmount ?? "n/d",
    secondary: residualAmount && residualAmount !== dueAmount ? `Residuo ${residualAmount}` : null,
  };
}

function FinanceLedgerRow({
  item,
  selected,
  onSelect,
  onRevealDetail,
  hrefTransform,
}: {
  item: OperationalCase;
  selected: boolean;
  onSelect: () => void;
  onRevealDetail: () => void;
  hrefTransform: (href: string, caseId: string) => string;
}) {
  const kindMeta = getFinanceCaseKindMeta(item.case_kind);
  const severityMeta = getFinanceSeverityMeta(item.severity);
  const primaryAction = item.suggested_actions.find((action) => action.is_primary) ?? item.suggested_actions[0];
  const primaryActionHref = primaryAction?.href ? hrefTransform(primaryAction.href, item.case_id) : undefined;
  const financeSummary = getFinanceSummary(item);
  const amountMeta = getFinanceAmountMeta(item);
  const dueDateLabel = item.due_date ? formatWorkspaceDate(item.due_date) : null;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect();
        }
      }}
      className={cn(
        "group rounded-[16px] px-3 py-2.5 transition-all",
        selected
          ? "border border-[#b8d0d1] bg-[#eef5f4] text-[#1f2a33] shadow-[0_18px_36px_-28px_rgba(47,110,115,0.22)]"
          : "border border-transparent bg-transparent text-[#1f2a33] hover:bg-[#f6f1ea]",
      )}
    >
      <div className="grid gap-3 xl:grid-cols-[minmax(0,2.2fr)_120px_150px_132px] xl:items-center">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn("rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.16em]", kindMeta.tone)}>
              {kindMeta.label}
            </span>
            <span className={cn("rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.16em]", severityMeta.tone)}>
              {severityMeta.label}
            </span>
          </div>
          <div className="mt-2 min-w-0">
            <h3 className="truncate text-[14px] font-bold tracking-[-0.02em]">{item.title}</h3>
            <p className={cn("mt-1 line-clamp-1 text-[12px]", selected ? "text-[#4c5b66]" : "text-[#5f6b76]")}>
              {item.reason}
            </p>
            {financeSummary ? (
              <p className={cn("mt-1 line-clamp-1 text-[11px]", selected ? "text-[#5b6a74]" : "text-[#7c8791]")}>
                {financeSummary}
              </p>
            ) : null}
          </div>
        </div>

        <div className={cn("space-y-1 text-[11px]", selected ? "text-[#4c5b66]" : "text-[#5f6b76]")}>
          <p className="font-semibold uppercase tracking-[0.14em] text-[10px]">Tempo</p>
          <p className="font-medium">{getCaseDueLabel(item)}</p>
          {dueDateLabel ? <p>{dueDateLabel}</p> : <p>{item.signal_count} segnali</p>}
        </div>

        <div className={cn("rounded-[14px] border px-3 py-2", selected ? "border-[#d8e6e5] bg-white/85" : "border-[#e5ddd3] bg-[#fbf8f3]")}>
          <p className={cn("text-[9px] font-semibold uppercase tracking-[0.18em]", selected ? "text-[#6d7b85]" : "text-[#7c8791]")}>
            {amountMeta.label}
          </p>
          <p className="mt-1 font-serif text-[24px] font-semibold leading-none tracking-[-0.04em]">
            {amountMeta.value}
          </p>
          {amountMeta.secondary ? (
            <p className={cn("mt-1 text-[10px]", selected ? "text-[#6d7b85]" : "text-[#7c8791]")}>
              {amountMeta.secondary}
            </p>
          ) : null}
        </div>

        <div className="flex items-center gap-2 xl:flex-col xl:items-stretch">
          {primaryActionHref ? (
            <Button
              asChild
              size="sm"
              className={cn(
                "h-9 flex-1 xl:w-full",
                selected
                  ? "border-0 bg-[#2f6e73] text-[#f8f5ef] hover:bg-[#25585c]"
                  : "border-0 bg-[#2f6e73] text-[#f8f5ef] hover:bg-[#25585c]",
              )}
              onClick={(event) => event.stopPropagation()}
            >
              <Link href={primaryActionHref}>
                {primaryAction.label}
                <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
              </Link>
            </Button>
          ) : (
            <Button size="sm" className="h-9 flex-1 xl:w-full" disabled={!primaryAction?.enabled}>
              {primaryAction?.label ?? "Apri"}
            </Button>
          )}

          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={cn(
              "h-9 flex-1 justify-between xl:w-full xl:flex-none",
              selected
                ? "text-[#4c5b66] hover:bg-[#dfeceb] hover:text-[#1f2a33]"
                : "text-[#5f6b76] hover:bg-[#edf2f1] hover:text-[#1f2a33]",
            )}
            onClick={(event) => {
              event.stopPropagation();
              onRevealDetail();
            }}
          >
            Dettaglio
            <ChevronRight className="ml-1 h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
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
  onRevealDetail,
  hrefTransform,
  emptyMessage,
}: {
  title: string;
  subtitle: string;
  total: number;
  items: OperationalCase[];
  selectedCaseId: string;
  onSelect: (caseId: string) => void;
  onRevealDetail: (caseId: string) => void;
  hrefTransform: (href: string, caseId: string) => string;
  emptyMessage: string;
}) {
  return (
    <section className="space-y-3">
      <div className="flex flex-col gap-1.5 rounded-[18px] border border-[#ded5ca] bg-[#f4efe8] px-4 py-3">
        <div className="flex items-center gap-2">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#41505c]">{title}</h3>
          <span className="rounded-full border border-[#d8cec3] bg-white/85 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-[#6b7680]">
            {total}
          </span>
        </div>
        <p className="text-[13px] text-[#5f6b76]">{subtitle}</p>
        {total > items.length && items.length > 0 && (
          <p className="text-[10px] uppercase tracking-[0.16em] text-[#7c8791]">
            Mostro {items.length} casi su {total} in questa vista iniziale.
          </p>
        )}
      </div>

      {items.length === 0 ? (
        <div className="rounded-[18px] border border-dashed border-[#ded5ca] bg-[#fbf8f3] px-4 py-4 text-sm text-[#7c8791]">
          {emptyMessage}
        </div>
      ) : (
        <div className="overflow-hidden rounded-[20px] border border-[#ded5ca] bg-[linear-gradient(180deg,rgba(255,252,248,0.98),rgba(247,242,234,0.96))] shadow-[0_24px_56px_-42px_rgba(31,42,51,0.14)]">
          <div className="hidden border-b border-[#e8dfd5] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.18em] text-[#7c8791] xl:grid xl:grid-cols-[minmax(0,2.2fr)_120px_150px_132px]">
            <span>Caso</span>
            <span>Tempo</span>
            <span>Importo</span>
            <span>Azione</span>
          </div>
          <div className="divide-y divide-[#ebe3d9] p-1">
          {items.map((item) => (
            <FinanceLedgerRow
              key={item.case_id}
              item={item}
              selected={item.case_id === selectedCaseId}
              onSelect={() => onSelect(item.case_id)}
              onRevealDetail={() => onRevealDetail(item.case_id)}
              hrefTransform={hrefTransform}
            />
          ))}
          </div>
        </div>
      )}
    </section>
  );
}

export default function RenewalsCashWorkspacePage() {
  const { revealClass, revealStyle } = usePageReveal();
  const detailPanelRef = useRef<HTMLDivElement | null>(null);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const rawFilter = searchParams.get("filter");
  const filter = FINANCE_FILTERS.some((item) => item.id === rawFilter)
    ? (rawFilter as FinanceFilter)
    : "all";
  const requestedCaseId = searchParams.get("case") ?? "";
  const showWaiting = searchParams.get("waiting") === "1";
  const searchParamsString = searchParams.toString();

  function replaceFinanceState(mutator: (params: URLSearchParams) => void) {
    const params = new URLSearchParams(searchParamsString);
    mutator(params);
    const next = params.toString();
    router.replace(`${pathname}${next ? `?${next}` : ""}`, { scroll: false });
  }

  function decorateFinanceHref(href: string) {
    return decorateFinanceHrefForCase(href, requestedCaseId);
  }

  function decorateFinanceHrefForCase(href: string, caseId: string) {
    if (!href.startsWith("/")) return href;
    const financeParams = new URLSearchParams(searchParamsString);
    if (caseId) financeParams.set("case", caseId);
    const url = new URL(href, "http://fitmanager.local");
    url.searchParams.set("returnTo", `${pathname}${financeParams.toString() ? `?${financeParams.toString()}` : ""}`);
    return `${url.pathname}${url.search}${url.hash}`;
  }

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

  function selectCase(caseId: string) {
    replaceFinanceState((params) => {
      params.set("case", caseId);
    });
  }

  function revealCaseDetail(caseId: string) {
    selectCase(caseId);

    if (typeof window === "undefined") return;
    if (window.matchMedia("(min-width: 1280px)").matches) return;

    window.requestAnimationFrame(() => {
      detailPanelRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }

  return (
    <div className="space-y-4">
      <div
        className={revealClass(
          0,
          "relative overflow-hidden rounded-[24px] border border-[#ddd4ca] bg-[radial-gradient(circle_at_top_left,rgba(47,110,115,0.12),transparent_34%),linear-gradient(135deg,rgba(248,244,237,0.98),rgba(244,238,229,0.98)_48%,rgba(238,232,223,0.98))] p-4 shadow-[0_28px_72px_-54px_rgba(47,110,115,0.22)]",
        )}
        style={revealStyle(0)}
      >
        <div className="pointer-events-none absolute inset-0 opacity-80">
          <div className="absolute -right-20 top-0 h-44 w-44 rounded-full bg-[#c9785c]/12 blur-3xl" />
          <div className="absolute bottom-0 left-0 h-24 w-full bg-[linear-gradient(90deg,transparent,rgba(47,110,115,0.08),transparent)]" />
        </div>
        <div className="flex flex-col gap-4 xl:grid xl:grid-cols-[minmax(0,1.35fr)_320px] xl:items-end">
          <div className="relative z-10 max-w-3xl">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[14px] border border-[#d8cec3] bg-white/82 shadow-sm">
                <HandCoins className="h-4 w-4 text-[#2f6e73]" />
              </div>
              <div>
                <span className="inline-flex rounded-full border border-[#d8cec3] bg-white/82 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[#6b7680]">
                  Workspace privato
                </span>
                <h1 className="mt-2 text-[30px] font-black tracking-[-0.05em] text-[#1f2a33] sm:text-[34px]">
                  Rinnovi & Incassi
                </h1>
                <p className="mt-1.5 max-w-2xl text-[13px] leading-6 text-[#5f6b76]">
                  Una scrivania economica privata e densa. Qui muovi denaro, rinnovi e scadenze senza disperderti in pannelli alti e rumore grafico.
                </p>
              </div>
            </div>
            <p className="mt-3 max-w-2xl text-[13px] leading-6 text-[#31404b]">{brief}</p>
            {totalCases > totalVisible && (
              <p className="mt-3 text-[10px] uppercase tracking-[0.16em] text-[#7c8791]">
                Vista iniziale dei primi {totalVisible} casi su {totalCases}, con budget per bucket e paginazione server-side.
              </p>
            )}
          </div>

          <div className="relative z-10 grid grid-cols-2 gap-2.5 xl:w-[320px]">
            <HeaderPill
              label="Critici"
              value={financeData.summary.now_count}
              tone="border-[#e5c0c0] bg-[#fff3f2] text-[#b85c5c]"
            />
            <HeaderPill
              label="Oggi"
              value={financeData.summary.today_count}
              tone="border-[#e8d3bf] bg-[#fbf4ec] text-[#c58a36]"
            />
            <HeaderPill
              label="Entro 7 giorni"
              value={financeData.summary.upcoming_7d_count}
              tone="border-[#cfe0e1] bg-[#f0f7f6] text-[#2f6e73]"
            />
            <HeaderPill
              label="Da pianificare"
              value={financeData.summary.waiting_count}
              tone="border-[#ddd4ca] bg-white/82 text-[#6b7680]"
            />
          </div>
        </div>
      </div>

      <div className={revealClass(70)} style={revealStyle(70)}>
        <div className="overflow-x-auto rounded-[18px] border border-[#ddd4ca] bg-[#f4efe8] p-1.5 shadow-[0_18px_50px_-40px_rgba(31,42,51,0.12)]">
          <div className="flex w-max min-w-full gap-2">
          {FINANCE_FILTERS.map((item) => {
            const isActive = item.id === filter;
            return (
              <button
                key={item.id}
                type="button"
                className={cn(
                  "rounded-[12px] px-3 py-1.5 text-[13px] font-medium transition-all",
                  isActive
                    ? "bg-[#2f6e73] text-[#f8f5ef] shadow-[0_12px_30px_-24px_rgba(47,110,115,0.42)]"
                    : "text-[#5f6b76] hover:bg-white/84 hover:text-[#1f2a33]",
                )}
                onClick={() => {
                  replaceFinanceState((params) => {
                    if (item.id === "all") params.delete("filter");
                    else params.set("filter", item.id);
                    params.delete("case");
                    params.delete("waiting");
                  });
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
          <div className="rounded-[22px] border border-[#ddd4ca] bg-[linear-gradient(180deg,rgba(255,252,248,0.98),rgba(248,243,236,0.96))] shadow-[0_28px_64px_-48px_rgba(31,42,51,0.14)]">
            <div className="border-b border-[#e5ddd4] px-4 py-3">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-[12px] border border-[#d8cec3] bg-white/82 shadow-sm">
                  <HandCoins className="h-4 w-4 text-[#2f6e73]" />
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#7c8791]">
                    Coda operativa
                  </p>
                  <h2 className="mt-1 text-lg font-bold tracking-[-0.02em] text-[#1f2a33]">
                    Queue economica
                  </h2>
                  <p className="mt-1 text-[12px] text-[#5f6b76]">
                    Prima i soldi che stanno gia bruciando, poi le scadenze che vuoi anticipare.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-4 p-4">
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
                      onSelect={selectCase}
                      onRevealDetail={revealCaseDetail}
                      hrefTransform={decorateFinanceHrefForCase}
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
                      onSelect={selectCase}
                      onRevealDetail={revealCaseDetail}
                      hrefTransform={decorateFinanceHrefForCase}
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
                      onSelect={selectCase}
                      onRevealDetail={revealCaseDetail}
                      hrefTransform={decorateFinanceHrefForCase}
                      emptyMessage="Nessun caso economico in arrivo nei prossimi 7 giorni."
                    />
                  )}

                  {waitingTotal > 0 && (
                    <section className="space-y-3">
                      <button
                        type="button"
                        onClick={() =>
                          replaceFinanceState((params) => {
                            const nextOpen = !showWaiting;
                            if (nextOpen) params.set("waiting", "1");
                            else params.delete("waiting");
                          })
                        }
                        className="flex w-full items-center justify-between rounded-[18px] border border-[#ddd4ca] bg-[#f4efe8] px-4 py-3 text-left transition-colors hover:bg-[#efe8de]"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#1f2a33]">Da pianificare</h3>
                            <span className="rounded-full border border-[#d8cec3] bg-white/82 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-[#6b7680]">
                              {waitingTotal}
                            </span>
                          </div>
                          <p className="mt-1 text-[13px] text-[#5f6b76]">
                            Backlog economico non urgente, utile quando la giornata si alleggerisce.
                          </p>
                          {showWaiting && waitingTotal > waitingItems.length && (
                            <p className="mt-1 text-[10px] uppercase tracking-[0.16em] text-[#7c8791]">
                              Mostro {waitingItems.length} casi su {waitingTotal} in questa vista iniziale.
                            </p>
                          )}
                        </div>
                        {showWaiting ? (
                          <ChevronDown className="h-4 w-4 text-[#7c8791]" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-[#7c8791]" />
                        )}
                      </button>

                      {showWaiting && (
                        <div className="overflow-hidden rounded-[20px] border border-[#ded5ca] bg-[linear-gradient(180deg,rgba(255,252,248,0.98),rgba(247,242,234,0.96))] shadow-[0_24px_56px_-42px_rgba(31,42,51,0.14)]">
                          <div className="hidden border-b border-[#e8dfd5] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.18em] text-[#7c8791] xl:grid xl:grid-cols-[minmax(0,2.2fr)_120px_150px_132px]">
                            <span>Caso</span>
                            <span>Tempo</span>
                            <span>Importo</span>
                            <span>Azione</span>
                          </div>
                          <div className="divide-y divide-[#ebe3d9] p-1">
                          {waitingItems.map((item) => (
                            <FinanceLedgerRow
                              key={item.case_id}
                              item={item}
                              selected={item.case_id === selectedCaseId}
                              onSelect={() => selectCase(item.case_id)}
                              onRevealDetail={() => revealCaseDetail(item.case_id)}
                              hrefTransform={decorateFinanceHrefForCase}
                            />
                          ))}
                          </div>
                        </div>
                      )}
                    </section>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        <div ref={detailPanelRef} className={revealClass(170)} style={revealStyle(170)}>
          <div className="xl:sticky xl:top-6">
            <WorkspaceDetailPanel
              selectedCase={selectedCase}
              detail={detailQuery.data}
              isLoading={detailQuery.isLoading}
              isError={detailQuery.isError}
              onRetry={() => void detailQuery.refetch()}
              variant="finance"
              hrefTransform={decorateFinanceHref}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
