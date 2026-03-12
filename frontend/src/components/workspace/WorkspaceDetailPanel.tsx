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
import { surfaceRoleClassName } from "@/components/ui/surface-role";
import {
  formatWorkspaceDate,
  formatWorkspaceDateTime,
  getCaseDueLabel,
  getCaseImpactLine,
  getFinanceSummary,
  getWorkspaceCaseKindLabel,
  getWorkspaceSeverityLabel,
} from "@/components/workspace/workspace-ui";
import {
  getWorkspaceCaseKindTone,
  getWorkspaceChipClassName,
  getWorkspacePanelClassName,
  getWorkspaceSectionClassName,
  getWorkspaceSeverityTone,
  type WorkspaceVariant,
} from "@/components/workspace/workspace-visuals";
import { cn } from "@/lib/utils";
import type { OperationalCase, WorkspaceCaseDetailResponse } from "@/types/api";

interface WorkspaceDetailPanelProps {
  selectedCase: OperationalCase | null;
  detail: WorkspaceCaseDetailResponse | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  variant?: WorkspaceVariant;
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
  const shellClassName = getWorkspacePanelClassName({ variant, embedded }, className);

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
        <div
          className={surfaceRoleClassName(
            { role: "context", tone: "red" },
            "flex items-start gap-3 px-4 py-4",
          )}
        >
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
  const severityTone = getWorkspaceSeverityTone(currentCase.severity);
  const severityLabel = getWorkspaceSeverityLabel(currentCase.severity);
  const kindTone = getWorkspaceCaseKindTone(currentCase.case_kind, variant);
  const kindLabel = getWorkspaceCaseKindLabel(currentCase.case_kind, variant);
  const financeSummary = getFinanceSummary(currentCase);
  const primaryAction =
    currentCase.suggested_actions.find((action) => action.is_primary) ??
    currentCase.suggested_actions[0];
  const primaryActionHref = primaryAction?.href
    ? hrefTransform?.(primaryAction.href) ?? primaryAction.href
    : undefined;
  const secondaryActions = currentCase.suggested_actions
    .filter((action) => action.id !== primaryAction?.id)
    .slice(0, 2);
  const neutralChipClassName = getWorkspaceChipClassName(
    "neutral",
    "px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em]",
  );
  const contextualChipClassName = getWorkspaceChipClassName(
    variant === "finance" ? "amber" : "neutral",
    "px-3 py-1.5 text-[11px] font-medium",
  );

  return (
    <div className={shellClassName}>
      <div className={cn("px-4 py-4", !embedded && "border-b border-border/70")}>
        <div className="flex flex-wrap items-center gap-1.5">
          <span
            className={getWorkspaceChipClassName(
              kindTone,
              "px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]",
            )}
          >
            {kindLabel}
          </span>
          <span
            className={getWorkspaceChipClassName(
              severityTone,
              "px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]",
            )}
          >
            {severityLabel}
          </span>
          <span className={neutralChipClassName}>{getCaseDueLabel(currentCase)}</span>
        </div>

        <h2 className="mt-3 text-[20px] font-semibold leading-tight tracking-[-0.02em] text-stone-950 dark:text-zinc-50">
          {currentCase.title}
        </h2>
        <p className="mt-1 text-[13px] leading-5 text-stone-600 dark:text-zinc-300">
          {currentCase.reason}
        </p>

        <div className="mt-3 flex flex-wrap gap-1.5 text-[11px] text-stone-600 dark:text-zinc-300">
          {currentCase.due_date ? (
            <span className={neutralChipClassName}>
              Scadenza {formatWorkspaceDate(currentCase.due_date)}
            </span>
          ) : null}
          <span className={neutralChipClassName}>
            {currentCase.signal_count} {currentCase.signal_count === 1 ? "segnale" : "segnali"}
          </span>
          {financeSummary ? (
            <span className="text-[11px] font-medium text-stone-500 dark:text-zinc-400">
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
              className={getWorkspaceSectionClassName(
                { variant, emphasis: "accent" },
                "px-4 py-4",
              )}
            >
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500 dark:text-zinc-400">
                Prossima mossa
              </p>
              <p className="mt-2 text-[13px] leading-5 text-stone-800 dark:text-zinc-100">
                {getCaseImpactLine(currentCase)}
              </p>

              <div className="mt-3 flex flex-wrap gap-2">
                {primaryActionHref ? (
                  <Button asChild size="sm" className="h-9 rounded-full px-3.5">
                    <Link href={primaryActionHref}>
                      {primaryAction.label}
                      <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
                    </Link>
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    className="h-9 rounded-full px-3.5"
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
                      className="h-9 rounded-full px-3.5"
                    >
                      <Link href={hrefTransform?.(action.href) ?? action.href}>{action.label}</Link>
                    </Button>
                  ) : (
                    <Button
                      key={action.id}
                      size="sm"
                      variant="outline"
                      className="h-9 rounded-full px-3.5"
                      disabled={!action.enabled}
                    >
                      {action.label}
                    </Button>
                  ),
                )}
              </div>
            </div>

            <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.92fr)]">
              <div
                className={getWorkspaceSectionClassName(
                  { variant, emphasis: "neutral" },
                  "px-3.5 py-3.5",
                )}
              >
                <div className="mb-2 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-stone-500 dark:text-zinc-400" />
                  <h3 className="text-[13px] font-semibold">Perche adesso</h3>
                </div>
                {detail?.signals.length ? (
                  <div className="space-y-2">
                    {detail.signals.slice(0, 3).map((signal) => (
                      <div
                        key={`${currentCase.case_id}-${signal.signal_code}`}
                        className={surfaceRoleClassName(
                          { role: "signal", tone: "neutral" },
                          "px-3 py-3",
                        )}
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="text-[13px] font-medium">{signal.label}</p>
                          {signal.due_date ? (
                            <span className={neutralChipClassName}>
                              {formatWorkspaceDate(signal.due_date)}
                            </span>
                          ) : null}
                        </div>
                        <p className="mt-1 text-[11px] leading-5 text-stone-600 dark:text-zinc-300">
                          {signal.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[13px] text-muted-foreground">
                    Nessun segnale aggiuntivo disponibile.
                  </p>
                )}
              </div>

              <div
                className={getWorkspaceSectionClassName(
                  { variant, emphasis: "neutral" },
                  "px-3.5 py-3.5",
                )}
              >
                <div className="mb-2 flex items-center gap-2">
                  <ListTree className="h-4 w-4 text-stone-500 dark:text-zinc-400" />
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
                            "inline-flex items-center gap-1 transition-colors hover:bg-accent/70",
                            contextualChipClassName,
                          )}
                        >
                          {entity.label}
                          <ArrowUpRight className="h-3 w-3" />
                        </Link>
                      ) : (
                        <span
                          key={`${entity.type}-${entity.id}`}
                          className={contextualChipClassName}
                        >
                          {entity.label}
                        </span>
                      ),
                    )}
                  </div>
                ) : (
                  <p className="text-[13px] text-muted-foreground">
                    Nessun contesto aggiuntivo disponibile.
                  </p>
                )}
              </div>
            </div>

            <div
              className={getWorkspaceSectionClassName(
                { variant, emphasis: "neutral" },
                "px-3.5 py-3.5",
              )}
            >
              <div className="mb-2 flex items-center gap-2">
                <Clock3 className="h-4 w-4 text-stone-500 dark:text-zinc-400" />
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
                          "border-b border-border/60",
                      )}
                    >
                      <div className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-stone-100 text-stone-600 dark:bg-zinc-800 dark:text-zinc-300">
                        <Clock3 className="h-3.5 w-3.5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-[13px] font-medium">{item.label}</p>
                        <p className="mt-0.5 text-[11px] text-stone-600 dark:text-zinc-300">
                          {formatWorkspaceDateTime(item.at)}
                        </p>
                        {item.href ? (
                          <Link
                            href={hrefTransform?.(item.href) ?? item.href}
                            className="mt-1 inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline"
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
                <p className="text-[13px] text-muted-foreground">
                  Nessuna timeline disponibile.
                </p>
              )}
            </div>
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
