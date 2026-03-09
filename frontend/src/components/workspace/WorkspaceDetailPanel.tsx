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
  formatFinanceAmount,
  formatWorkspaceDate,
  formatWorkspaceDateTime,
  getFinanceCaseKindMeta,
  getFinanceSeverityMeta,
  getCaseDueLabel,
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
}

export function WorkspaceDetailPanel({
  selectedCase,
  detail,
  isLoading,
  isError,
  onRetry,
  variant = "default",
  hrefTransform,
}: WorkspaceDetailPanelProps) {
  const isFinance = variant === "finance";
  if (!selectedCase) {
    return (
      <div
        className={cn(
          "flex min-h-[460px] items-center p-4",
          isFinance
            ? "rounded-[22px] border border-[#ddd4ca] bg-[linear-gradient(180deg,rgba(255,252,248,0.98),rgba(248,243,236,0.96))] shadow-[0_28px_64px_-48px_rgba(31,42,51,0.14)]"
            : "rounded-3xl border border-border/70 bg-white shadow-sm dark:bg-zinc-900",
        )}
      >
        <EmptyState
          icon={ListTree}
          title="Seleziona un caso operativo"
          subtitle="Qui compariranno il perche ora, il contesto e l'azione giusta per chiuderlo."
          className="w-full border-0 bg-transparent py-4"
        />
      </div>
    );
  }

  if (isError) {
    return (
      <div
        className={cn(
          "p-5",
          isFinance
            ? "rounded-[22px] border border-[#e5c0c0] bg-[linear-gradient(180deg,rgba(255,243,242,0.98),rgba(252,238,236,0.96))] shadow-[0_24px_60px_-48px_rgba(184,92,92,0.28)]"
            : "rounded-3xl border border-destructive/40 bg-destructive/5 shadow-sm",
        )}
      >
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 text-destructive" />
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold text-destructive">Dettaglio non disponibile</h3>
            <p className="mt-1 text-sm text-destructive/90">
              Il caso selezionato esiste, ma il suo contesto dettagliato non si e caricato correttamente.
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
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
  const dueAmount = formatFinanceAmount(currentCase.finance_context?.total_due_amount);
  const residualAmount = formatFinanceAmount(currentCase.finance_context?.total_residual_amount);

  return (
    <div
      className={cn(
        "flex min-h-[460px] flex-col",
        isFinance
          ? "rounded-[22px] border border-[#ddd4ca] bg-[linear-gradient(180deg,rgba(255,252,248,0.98),rgba(248,243,236,0.96))] shadow-[0_28px_64px_-48px_rgba(31,42,51,0.14)]"
          : "rounded-3xl border border-border/70 bg-white shadow-sm dark:bg-zinc-900",
      )}
    >
      <div
        className={cn(
          "px-3.5 py-3.5",
          isFinance
            ? "rounded-t-[22px] border-b border-[#e5ddd4] bg-[radial-gradient(circle_at_top_left,rgba(47,110,115,0.12),transparent_32%),linear-gradient(135deg,rgba(248,244,237,0.98),rgba(244,238,229,0.98)_48%,rgba(238,232,223,0.98))] text-[#1f2a33]"
            : "border-b",
        )}
      >
        <div className={cn("flex flex-col gap-3", isFinance && "lg:grid lg:grid-cols-[minmax(0,1fr)_176px] lg:items-start")}>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${kindMeta.tone}`}>
                {kindMeta.label}
              </span>
              <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${severityMeta.tone}`}>
                {severityMeta.label}
              </span>
            </div>

            <h2 className={cn("mt-2 leading-tight", isFinance ? "text-[22px] font-bold tracking-[-0.03em] text-[#1f2a33]" : "text-lg font-semibold")}>
              {currentCase.title}
            </h2>
            <p className={cn("mt-1 text-sm", isFinance ? "max-w-2xl text-[#5f6b76]" : "text-muted-foreground")}>
              {currentCase.reason}
            </p>

            <div className={cn("mt-3 flex flex-wrap gap-2 text-xs", isFinance ? "text-[#5f6b76]" : "text-muted-foreground")}>
              <span className={cn("rounded-full px-2.5 py-1", isFinance ? "border border-[#d8cec3] bg-white/82" : "bg-muted")}>
                {getCaseDueLabel(currentCase)}
              </span>
              {currentCase.due_date && (
                <span className={cn("rounded-full px-2.5 py-1", isFinance ? FINANCE_TOKEN_TONES.subtlePill : "bg-muted")}>
                  Scadenza {formatWorkspaceDate(currentCase.due_date)}
                </span>
              )}
            </div>
          </div>

          {isFinance && (
            <div className="rounded-[16px] border border-[#cfe0e1] bg-[#eef5f4] px-3.5 py-3 shadow-inner">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#6b7680]">
                Esposizione
              </p>
              <p className="mt-1.5 font-serif text-[26px] font-semibold leading-none tracking-[-0.03em] text-[#1f2a33]">
                {dueAmount ?? residualAmount ?? "n/d"}
              </p>
              {dueAmount && residualAmount && dueAmount !== residualAmount ? (
                <p className="mt-1.5 text-[11px] text-[#6d7b85]">Residuo {residualAmount}</p>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {isLoading && !detail ? (
        <div className="space-y-3 p-3.5">
          <Skeleton className="h-20 rounded-2xl" />
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-16 rounded-2xl" />
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-28 rounded-2xl" />
        </div>
      ) : (
        <ScrollArea className="min-h-0 flex-1">
          <div className="space-y-3 p-3.5">
            <div
              className={cn(
                "rounded-[16px] border p-3",
                isFinance
                  ? "border-[#d8cec3] bg-white/82 text-[#1f2a33] shadow-inner"
                  : "border-border/70 bg-muted/25",
              )}
            >
              <p className={cn("text-[10px] font-semibold uppercase tracking-[0.16em]", isFinance ? "text-[#7c8791]" : "text-muted-foreground")}>
                Azione consigliata
              </p>
              <p className={cn("mt-1.5 text-[13px] leading-5", isFinance ? "text-[#31404b]" : "text-foreground")}>
                Questo e il passo giusto per sbloccare il caso senza sporcare il resto della giornata.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {primaryActionHref ? (
                  <Button
                    asChild
                    size="sm"
                    className={cn("h-8.5", isFinance && "border-0 bg-[#2f6e73] text-[#f8f5ef] hover:bg-[#25585c]")}
                  >
                    <Link href={primaryActionHref}>
                      {primaryAction.label}
                      <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
                    </Link>
                  </Button>
                ) : (
                  <Button size="sm" className="h-8.5" disabled={!primaryAction?.enabled}>
                    {primaryAction?.label ?? "Apri"}
                  </Button>
                )}
                {currentCase.suggested_actions
                  .filter((action) => action.id !== primaryAction?.id)
                  .slice(0, 2)
                  .map((action) =>
                    action.href ? (
                      (() => {
                        const href = hrefTransform?.(action.href) ?? action.href;
                        return (
                      <Button
                        key={action.id}
                        asChild
                        size="sm"
                        variant="outline"
                        className={cn("h-8.5", isFinance && "border-[#d8cec3] bg-transparent text-[#31404b] hover:bg-[#eef5f4] hover:text-[#1f2a33]")}
                      >
                        <Link href={href}>{action.label}</Link>
                      </Button>
                        );
                      })()
                    ) : (
                      <Button
                        key={action.id}
                        size="sm"
                        variant="outline"
                        className={cn("h-8.5", isFinance && "border-[#d8cec3] bg-transparent text-[#31404b] hover:bg-[#eef5f4] hover:text-[#1f2a33]")}
                        disabled={!action.enabled}
                      >
                        {action.label}
                      </Button>
                    ),
                  )}
              </div>
              {financeSummary && (
                <p className={cn("mt-2 text-[11px]", isFinance ? "text-[#6d7b85]" : "text-muted-foreground")}>{financeSummary}</p>
              )}
            </div>

            <div className="grid gap-3 lg:grid-cols-2">
              <div className={cn("rounded-[16px] border p-3", isFinance ? "border-[#e5ddd4] bg-[#fbf8f3]" : "border-border/70 bg-background")}>
                <div className="mb-2 flex items-center gap-2">
                  <AlertCircle className={cn("h-4 w-4", isFinance ? "text-[#7c8791]" : "text-muted-foreground")} />
                  <h3 className="text-[13px] font-semibold">Perche ora</h3>
                </div>
                {detail?.signals.length ? (
                  <div className="space-y-2">
                    {detail.signals.map((signal) => (
                        <div
                          key={`${currentCase.case_id}-${signal.signal_code}`}
                          className={cn(
                            "rounded-[12px] p-2.5",
                            isFinance ? FINANCE_TOKEN_TONES.signalCard : "border border-border/70 bg-background",
                          )}
                        >
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-[13px] font-medium">{signal.label}</p>
                            {signal.due_date && (
                            <span
                              className={cn(
                                "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                                isFinance ? FINANCE_TOKEN_TONES.subtlePill : "bg-muted text-muted-foreground",
                              )}
                            >
                              {formatWorkspaceDate(signal.due_date)}
                            </span>
                          )}
                        </div>
                        <p className={cn("mt-1 text-[11px] leading-5", isFinance ? "text-[#5f6b76]" : "text-muted-foreground")}>{signal.reason}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[13px] text-muted-foreground">Nessun segnale aggiuntivo disponibile.</p>
                )}
              </div>

              <div className={cn("rounded-[16px] border p-3", isFinance ? "border-[#e5ddd4] bg-[#fbf8f3]" : "border-border/70 bg-background")}>
                <div className="mb-2 flex items-center gap-2">
                  <ListTree className={cn("h-4 w-4", isFinance ? "text-[#7c8791]" : "text-muted-foreground")} />
                  <h3 className="text-[13px] font-semibold">Contesto collegato</h3>
                </div>
                {detail?.related_entities.length ? (
                  <div className="flex flex-wrap gap-2">
                    {detail.related_entities.map((entity) =>
                      entity.href ? (
                        (() => {
                          const href = hrefTransform?.(entity.href) ?? entity.href;
                          return (
                        <Link
                          key={`${entity.type}-${entity.id}`}
                          href={href}
                          className={cn(
                            "inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-[11px] font-medium transition-colors",
                            isFinance
                              ? `${FINANCE_TOKEN_TONES.contextChip} hover:bg-[#eef5f4]`
                              : "border border-border/70 bg-background hover:bg-muted",
                          )}
                        >
                          {entity.label}
                          <ArrowUpRight className="h-3 w-3" />
                        </Link>
                          );
                        })()
                      ) : (
                        <span
                          key={`${entity.type}-${entity.id}`}
                          className={cn(
                            "inline-flex items-center rounded-full px-3 py-1.5 text-[11px] font-medium",
                            isFinance
                              ? FINANCE_TOKEN_TONES.contextChip
                              : "border border-border/70 bg-background",
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

            <div className={cn("rounded-[16px] border p-3", isFinance ? "border-[#e5ddd4] bg-[#fbf8f3]" : "border-border/70 bg-background")}>
              <div className="mb-2 flex items-center gap-2">
                <Clock3 className={cn("h-4 w-4", isFinance ? "text-[#7c8791]" : "text-muted-foreground")} />
                <h3 className="text-[13px] font-semibold">Timeline sintetica</h3>
              </div>
              {detail?.activity_preview.length ? (
                <div className="space-y-2.5">
                  {detail.activity_preview.map((item, index) => (
                    <div key={`${item.at}-${item.label}-${index}`} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <span className={cn("h-2.5 w-2.5 rounded-full", isFinance ? "bg-[#2f6e73]" : "bg-primary/70")} />
                        {index < detail.activity_preview.length - 1 && (
                          <span className={cn("mt-1 h-full w-px", isFinance ? "bg-[#ddd4ca]" : "bg-border")} />
                        )}
                      </div>
                      <div className="min-w-0 flex-1 pb-2">
                        <p className="text-[13px] font-medium">{item.label}</p>
                        <p className={cn("mt-1 text-[11px]", isFinance ? "text-[#5f6b76]" : "text-muted-foreground")}>
                          {formatWorkspaceDateTime(item.at)}
                        </p>
                        {item.href && (
                          (() => {
                            const href = hrefTransform?.(item.href) ?? item.href;
                            return (
                          <Link
                            href={href}
                            className={cn("mt-1.5 inline-flex items-center gap-1 text-[11px] font-medium hover:underline", isFinance ? "text-[#2f6e73]" : "text-primary")}
                          >
                            Apri contesto
                            <ArrowUpRight className="h-3 w-3" />
                          </Link>
                            );
                          })()
                        )}
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
