"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { surfaceRoleClassName } from "@/components/ui/surface-role";
import {
  formatFinanceAmount,
  getCaseDueLabel,
  getFinanceAmountLabel,
  getFinanceSummary,
  getWorkspaceCaseKindLabel,
  getWorkspaceSeverityLabel,
} from "@/components/workspace/workspace-ui";
import {
  getWorkspaceAccentClass,
  getWorkspaceCardClassName,
  getWorkspaceCaseKindTone,
  getWorkspaceChipClassName,
  getWorkspaceSeverityTone,
  type WorkspaceVariant,
} from "@/components/workspace/workspace-visuals";
import { cn } from "@/lib/utils";
import type { OperationalCase } from "@/types/api";

interface WorkspaceCaseCardProps {
  item: OperationalCase;
  selected: boolean;
  onSelect: () => void;
  showFinanceSummary?: boolean;
  variant?: WorkspaceVariant;
  supportingLine?: string | null;
  hrefTransform?: (href: string) => string;
}

export function WorkspaceCaseCard({
  item,
  selected,
  onSelect,
  showFinanceSummary = false,
  variant = "default",
  supportingLine,
  hrefTransform,
}: WorkspaceCaseCardProps) {
  const primaryAction =
    item.suggested_actions.find((action) => action.is_primary) ?? item.suggested_actions[0];
  const primaryActionHref = primaryAction?.href
    ? hrefTransform?.(primaryAction.href) ?? primaryAction.href
    : undefined;
  const financeSummary = showFinanceSummary ? getFinanceSummary(item) : null;
  const dueAmount = formatFinanceAmount(item.finance_context?.total_due_amount);
  const residualAmount = formatFinanceAmount(item.finance_context?.total_residual_amount);
  const dueLabel = getCaseDueLabel(item);
  const accentClass = getWorkspaceAccentClass(item.severity);
  const severityTone = getWorkspaceSeverityTone(item.severity);
  const severityLabel = getWorkspaceSeverityLabel(item.severity);
  const kindTone = getWorkspaceCaseKindTone(item.case_kind, variant);
  const kindLabel = getWorkspaceCaseKindLabel(item.case_kind, variant);
  const entityLabel = item.secondary_entity?.label ?? item.root_entity.label;
  const metaChipClassName = getWorkspaceChipClassName(
    "neutral",
    "px-2.5 py-1 text-[10px] font-medium",
  );

  if (variant === "finance") {
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
        className={getWorkspaceCardClassName({ variant, selected })}
      >
        <div className="flex flex-col gap-3 xl:grid xl:grid-cols-[minmax(0,1fr)_230px] xl:items-start">
          <div className={cn("hidden h-16 w-1.5 shrink-0 rounded-full xl:block", accentClass)} />

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
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
            </div>

            <div className="mt-3 min-w-0">
              <h3 className="text-lg font-bold leading-tight tracking-[-0.015em] text-foreground">
                {item.title}
              </h3>
              <p className="mt-1 max-w-2xl text-[14px] leading-6 text-stone-700 dark:text-zinc-300">
                {item.reason}
              </p>
              {supportingLine ? (
                <p className="mt-2 text-[12px] font-medium leading-5 text-stone-600 dark:text-zinc-300">
                  {supportingLine}
                </p>
              ) : null}
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-2.5 text-xs text-stone-600 dark:text-zinc-300">
              <span className={metaChipClassName}>{dueLabel}</span>
              <span className={metaChipClassName}>
                {item.signal_count} {item.signal_count === 1 ? "segnale" : "segnali"}
              </span>
            </div>

            {financeSummary && (
              <div
                className={surfaceRoleClassName(
                  { role: "context", tone: "neutral" },
                  "mt-4 px-4 py-3 text-sm text-stone-700 dark:text-zinc-300",
                )}
              >
                {financeSummary}
              </div>
            )}
          </div>

          <div className="flex shrink-0 flex-wrap items-center gap-2 xl:flex-col xl:items-stretch">
            <div
              className={surfaceRoleClassName(
                { role: "context", tone: "amber" },
                "px-4 py-4",
              )}
            >
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500 dark:text-zinc-400">
                {getFinanceAmountLabel(item.case_kind)}
              </p>
              <p className="mt-2 text-[28px] font-semibold leading-none tracking-[-0.03em] text-stone-900 dark:text-zinc-50">
                {dueAmount ?? residualAmount ?? "n/d"}
              </p>
              {dueAmount && residualAmount && dueAmount !== residualAmount ? (
                <p className="mt-2 text-xs text-stone-500 dark:text-zinc-400">
                  Residuo {residualAmount}
                </p>
              ) : null}

              <div className="mt-4 flex flex-col gap-2">
                {primaryActionHref ? (
                  <Button asChild size="sm" className="h-10 rounded-full px-4">
                    <Link href={primaryActionHref} onClick={(event) => event.stopPropagation()}>
                      {primaryAction.label}
                      <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
                    </Link>
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    className="h-10 rounded-full px-4"
                    disabled={!primaryAction?.enabled}
                  >
                    {primaryAction?.label ?? "Apri"}
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
      className={getWorkspaceCardClassName({ variant, selected }, "group relative")}
    >
      <div className="flex items-start gap-3 px-3.5 py-3 md:items-center">
        <span className={cn("mt-1.5 h-2 w-2 shrink-0 rounded-full md:mt-0", accentClass)} />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <h3 className="text-[14px] font-bold leading-5 tracking-tight text-stone-900 dark:text-zinc-50">
              {item.title}
            </h3>
            <span className="text-[11px] font-medium text-stone-500 dark:text-zinc-400">
              {entityLabel}
            </span>
          </div>

          <p className="mt-0.5 text-[12px] leading-5 text-stone-600 dark:text-zinc-400">
            {item.reason}
          </p>

          {supportingLine && (
            <p className="mt-1 text-[11px] font-semibold text-primary/90 dark:text-primary">
              {supportingLine}
            </p>
          )}
          {financeSummary && (
            <p className="mt-1 text-[11px] font-medium text-stone-600 dark:text-zinc-400">
              {financeSummary}
            </p>
          )}

          <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[10px] text-stone-400 dark:text-zinc-500">
            <span>{dueLabel}</span>
            {item.signal_count > 0 && (
              <>
                <span className="text-stone-300 dark:text-zinc-600">&middot;</span>
                <span>
                  {item.signal_count} {item.signal_count === 1 ? "segnale" : "segnali"}
                </span>
              </>
            )}
            {!primaryAction?.enabled && primaryAction?.availability_note && (
              <>
                <span className="text-stone-300 dark:text-zinc-600">&middot;</span>
                <span>{primaryAction.availability_note}</span>
              </>
            )}
          </div>
        </div>

        <div className="flex shrink-0 items-center">
          {primaryActionHref ? (
            <Button asChild size="sm" variant="outline" className="h-8 rounded-full px-3 text-xs">
              <Link href={primaryActionHref} onClick={(event) => event.stopPropagation()}>
                {primaryAction.label}
                <ArrowUpRight className="h-3 w-3" />
              </Link>
            </Button>
          ) : (
            <Button
              size="sm"
              variant="outline"
              className="h-8 rounded-full px-3 text-xs"
              disabled={!primaryAction?.enabled}
            >
              {primaryAction?.label ?? "Apri"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
