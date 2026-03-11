"use client";

import Link from "next/link";
import {
  AlertCircle,
  ArrowUpRight,
  Clock3,
  ListTree,
  RefreshCw,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { OperationalCase, WorkspaceCaseDetailResponse } from "@/types/api";

import {
  FINANCE_TOKEN_TONES,
  formatWorkspaceDate,
  formatWorkspaceDateTime,
  getFinanceCaseKindMeta,
  getFinanceSeverityMeta,
  getCaseDueLabel,
  getCaseImpactLine,
  getFinanceSummary,
  WORKSPACE_CASE_KIND_META,
  WORKSPACE_SEVERITY_META,
} from "@/components/workspace/workspace-ui";

interface WorkspaceDetailPanelProps {
  selectedCase: OperationalCase | null;
  detail: WorkspaceCaseDetailResponse | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  variant?: "default" | "finance";
  hrefTransform?: (href: string) => string;
  embedded?: boolean;
  className?: string;
}

export function WorkspaceDetailPanel({
  selectedCase,
  detail,
  isLoading,
  isError,
  onRetry,
  variant = "default",
  hrefTransform,
  embedded = false,
  className,
}: WorkspaceDetailPanelProps) {
  const isFinance = variant === "finance";
  const shellClassName = cn(
    "flex min-h-0 flex-col",
    !embedded &&
      (isFinance
        ? "rounded-[24px] border border-[#ddd4ca] bg-[linear-gradient(180deg,rgba(255,252,248,0.98),rgba(248,243,236,0.96))] shadow-[0_28px_64px_-48px_rgba(31,42,51,0.14)]"
        : "rounded-[28px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,246,242,0.98))] shadow-[0_28px_68px_-52px_rgba(41,37,36,0.34)] dark:border-zinc-800 dark:bg-[linear-gradient(180deg,rgba(24,24,27,0.98),rgba(20,20,24,0.98))]"),
    className,
  );

  if (!selectedCase) {
    return (
      <div className={cn(shellClassName, !embedded && "min-h-[360px] justify-center p-4", embedded && "p-4")}>
        <EmptyState
          icon={ListTree}
          title="Seleziona un caso"
          subtitle="Il dossier a destra ti mostra la prossima mossa, il trigger e il contesto utile."
          className="w-full border-0 bg-transparent py-6"
        />
      </div>
    );
  }

  if (isError) {
    return (
      <div className={cn(shellClassName, "p-4")}>
        <div className="flex items-start gap-3 rounded-[20px] border border-destructive/30 bg-destructive/5 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 text-destructive" />
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold text-destructive">Dettaglio non disponibile</h3>
            <p className="mt-1 text-sm text-destructive/90">
              Il caso esiste, ma il dossier non si e caricato correttamente.
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" className="mt-3 w-fit rounded-full" onClick={onRetry}>
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Riprova
        </Button>
      </div>
    );
  }

  const currentCase = detail?.case ?? selectedCase;
  const severityMeta = isFinance
    ? getFinanceSeverityMeta(currentCase.severity)
    : WORKSPACE_SEVERITY_META[currentCase.severity];
  const kindMeta = isFinance
    ? getFinanceCaseKindMeta(currentCase.case_kind)
    : WORKSPACE_CASE_KIND_META[currentCase.case_kind];
  const financeSummary = getFinanceSummary(currentCase);
  const primaryAction = currentCase.suggested_actions.find((action) => action.is_primary) ?? currentCase.suggested_actions[0];
  const primaryActionHref = primaryAction?.href ? hrefTransform?.(primaryAction.href) ?? primaryAction.href : undefined;
  const secondaryActions = currentCase.suggested_actions
    .filter((action) => action.id !== primaryAction?.id)
    .slice(0, 2);
  const chipClassName = isFinance
    ? FINANCE_TOKEN_TONES.subtlePill
    : "border border-stone-200/80 bg-white/80 text-stone-600 dark:border-zinc-700 dark:bg-zinc-950/70 dark:text-zinc-300";
  const boxClassName = isFinance
    ? "rounded-[20px] border border-[#e5ddd4] bg-[#fbf8f3] p-3.5"
    : "rounded-[20px] border border-stone-200/80 bg-white/80 p-3.5 dark:border-zinc-800 dark:bg-zinc-950/50";

  return (
    <div className={shellClassName}>
      <div
        className={cn(
          "px-4 py-4",
          !embedded &&
            (isFinance
              ? "border-b border-[#e5ddd4]"
              : "border-b border-stone-200/80 dark:border-zinc-800"),
        )}
      >
        <div className="flex flex-wrap items-center gap-1.5">
          <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${kindMeta.tone}`}>
            {kindMeta.label}
          </span>
          <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${severityMeta.tone}`}>
            {severityMeta.label}
          </span>
          <span className={cn("rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em]", chipClassName)}>
            {getCaseDueLabel(currentCase)}
          </span>
        </div>

        <h2
          className={cn(
            "mt-3 leading-tight",
            isFinance ? "text-[22px] font-bold tracking-[-0.03em] text-[#1f2a33]" : "text-[20px] font-semibold tracking-[-0.02em] text-stone-950 dark:text-zinc-50",
          )}
        >
          {currentCase.title}
        </h2>
        <p className={cn("mt-1 text-[13px] leading-5", isFinance ? "text-[#5f6b76]" : "text-stone-600 dark:text-zinc-300")}>
          {currentCase.reason}
        </p>

        <div className={cn("mt-3 flex flex-wrap gap-1.5 text-[11px]", isFinance ? "text-[#5f6b76]" : "text-stone-600 dark:text-zinc-300")}>
          {currentCase.due_date ? (
            <span className={cn("rounded-full px-2.5 py-1", chipClassName)}>
              Scadenza {formatWorkspaceDate(currentCase.due_date)}
            </span>
          ) : null}
          <span className={cn("rounded-full px-2.5 py-1", chipClassName)}>
            {currentCase.signal_count} {currentCase.signal_count === 1 ? "segnale" : "segnali"}
          </span>
          {financeSummary ? (
            <span className={cn("rounded-full px-2.5 py-1", chipClassName)}>
              {financeSummary}
            </span>
          ) : null}
        </div>
      </div>

      {isLoading && !detail ? (
        <div className="space-y-3 p-4">
          <Skeleton className="h-28 rounded-[22px]" />
          <Skeleton className="h-24 rounded-[20px]" />
          <Skeleton className="h-28 rounded-[20px]" />
        </div>
      ) : (
        <ScrollArea className="min-h-0 flex-1">
          <div className="space-y-3.5 p-4">
            <div
              className={cn(
                "rounded-[24px] p-4",
                isFinance
                  ? "border border-[#cfe0e1] bg-[#eef5f4]"
                  : "border border-stone-900 bg-stone-950 text-stone-50 dark:border-emerald-400/30 dark:bg-zinc-950",
              )}
            >
              <p className={cn("text-[10px] font-semibold uppercase tracking-[0.18em]", isFinance ? "text-[#6b7680]" : "text-stone-300")}>
                Prossima mossa
              </p>
              <p className={cn("mt-2 text-[13px] leading-5", isFinance ? "text-[#31404b]" : "text-stone-200")}>
                {getCaseImpactLine(currentCase)}
              </p>

              <div className="mt-3 flex flex-wrap gap-2">
                {primaryActionHref ? (
                  <Button
                    asChild
                    size="sm"
                    className={cn(
                      "h-9 rounded-full px-3.5",
                      isFinance
                        ? "border-0 bg-[#2f6e73] text-[#f8f5ef] hover:bg-[#25585c]"
                        : "border-0 bg-amber-300 text-stone-950 hover:bg-amber-200",
                    )}
                  >
                    <Link href={primaryActionHref}>
                      {primaryAction.label}
                      <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
                    </Link>
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    className={cn("h-9 rounded-full px-3.5", isFinance && "border-0 bg-[#2f6e73] text-[#f8f5ef] hover:bg-[#25585c]")}
                    disabled={!primaryAction?.enabled}
                  >
                    {primaryAction?.label ?? "Apri"}
                  </Button>
                )}

                {secondaryActions.map((action) =>
                  action.href ? (
                    <Button
                      key={action.id}
                      asChild
                      size="sm"
                      variant="outline"
                      className={cn(
                        "h-9 rounded-full px-3.5",
                        isFinance
                          ? "border-[#cfe0e1] bg-transparent text-[#31404b] hover:bg-[#dfeceb] hover:text-[#1f2a33]"
                          : "border-white/15 bg-white/5 text-stone-100 hover:bg-white/10 hover:text-stone-50 dark:border-white/10",
                      )}
                    >
                      <Link href={hrefTransform?.(action.href) ?? action.href}>{action.label}</Link>
                    </Button>
                  ) : (
                    <Button
                      key={action.id}
                      size="sm"
                      variant="outline"
                      className={cn(
                        "h-9 rounded-full px-3.5",
                        isFinance
                          ? "border-[#cfe0e1] bg-transparent text-[#31404b] hover:bg-[#dfeceb] hover:text-[#1f2a33]"
                          : "border-white/15 bg-white/5 text-stone-100 hover:bg-white/10 hover:text-stone-50 dark:border-white/10",
                      )}
                      disabled={!action.enabled}
                    >
                      {action.label}
                    </Button>
                  ),
                )}
              </div>
            </div>

            <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.92fr)]">
              <div className={boxClassName}>
                <div className="mb-2 flex items-center gap-2">
                  <AlertCircle className={cn("h-4 w-4", isFinance ? "text-[#7c8791]" : "text-stone-500 dark:text-zinc-400")} />
                  <h3 className="text-[13px] font-semibold">Perche adesso</h3>
                </div>
                {detail?.signals.length ? (
                  <div className="space-y-2">
                    {detail.signals.slice(0, 3).map((signal) => (
                      <div
                        key={`${currentCase.case_id}-${signal.signal_code}`}
                        className={cn(
                          "rounded-[16px] border p-3",
                          isFinance
                            ? FINANCE_TOKEN_TONES.signalCard
                            : "border-stone-200/80 bg-stone-50/85 dark:border-zinc-800 dark:bg-zinc-900/80",
                        )}
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="text-[13px] font-medium">{signal.label}</p>
                          {signal.due_date ? (
                            <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em]", chipClassName)}>
                              {formatWorkspaceDate(signal.due_date)}
                            </span>
                          ) : null}
                        </div>
                        <p className={cn("mt-1 text-[11px] leading-5", isFinance ? "text-[#5f6b76]" : "text-stone-600 dark:text-zinc-300")}>
                          {signal.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[13px] text-muted-foreground">Nessun segnale aggiuntivo disponibile.</p>
                )}
              </div>

              <div className={boxClassName}>
                <div className="mb-2 flex items-center gap-2">
                  <ListTree className={cn("h-4 w-4", isFinance ? "text-[#7c8791]" : "text-stone-500 dark:text-zinc-400")} />
                  <h3 className="text-[13px] font-semibold">Contesto collegato</h3>
                </div>
                {detail?.related_entities.length ? (
                  <div className="flex flex-wrap gap-2">
                    {detail.related_entities.map((entity) =>
                      entity.href ? (
                        <Link
                          key={`${entity.type}-${entity.id}`}
                          href={hrefTransform?.(entity.href) ?? entity.href}
                          className={cn(
                            "inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-[11px] font-medium transition-colors",
                            isFinance
                              ? `${FINANCE_TOKEN_TONES.contextChip} hover:bg-[#eef5f4]`
                              : "border border-stone-200/80 bg-white/85 text-stone-700 hover:bg-stone-50 dark:border-zinc-700 dark:bg-zinc-950/70 dark:text-zinc-200 dark:hover:bg-zinc-900/90",
                          )}
                        >
                          {entity.label}
                          <ArrowUpRight className="h-3 w-3" />
                        </Link>
                      ) : (
                        <span
                          key={`${entity.type}-${entity.id}`}
                          className={cn(
                            "inline-flex items-center rounded-full px-3 py-1.5 text-[11px] font-medium",
                            isFinance
                              ? FINANCE_TOKEN_TONES.contextChip
                              : "border border-stone-200/80 bg-white/85 text-stone-700 dark:border-zinc-700 dark:bg-zinc-950/70 dark:text-zinc-200",
                          )}
                        >
                          {entity.label}
                        </span>
                      ),
                    )}
                  </div>
                ) : (
                  <p className="text-[13px] text-muted-foreground">Nessun contesto aggiuntivo disponibile.</p>
                )}
              </div>
            </div>

            <div className={boxClassName}>
              <div className="mb-2 flex items-center gap-2">
                <Clock3 className={cn("h-4 w-4", isFinance ? "text-[#7c8791]" : "text-stone-500 dark:text-zinc-400")} />
                <h3 className="text-[13px] font-semibold">Timeline sintetica</h3>
              </div>
              {detail?.activity_preview.length ? (
                <div className="space-y-0">
                  {detail.activity_preview.slice(0, 5).map((item, index) => (
                    <div
                      key={`${item.at}-${item.label}-${index}`}
                      className={cn(
                        "flex gap-3 py-2.5",
                        index < Math.min(detail.activity_preview.length, 5) - 1 &&
                          (isFinance ? "border-b border-[#e5ddd4]" : "border-b border-stone-200/80 dark:border-zinc-800"),
                      )}
                    >
                      <div className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-stone-100 text-stone-600 dark:bg-zinc-800 dark:text-zinc-300">
                        <Clock3 className="h-3.5 w-3.5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-[13px] font-medium">{item.label}</p>
                        <p className={cn("mt-0.5 text-[11px]", isFinance ? "text-[#5f6b76]" : "text-stone-600 dark:text-zinc-300")}>
                          {formatWorkspaceDateTime(item.at)}
                        </p>
                        {item.href ? (
                          <Link
                            href={hrefTransform?.(item.href) ?? item.href}
                            className={cn("mt-1 inline-flex items-center gap-1 text-[11px] font-medium hover:underline", isFinance ? "text-[#2f6e73]" : "text-primary")}
                          >
                            Apri contesto
                            <ArrowUpRight className="h-3 w-3" />
                          </Link>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[13px] text-muted-foreground">Nessuna timeline disponibile.</p>
              )}
            </div>
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
