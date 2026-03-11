"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { OperationalCase } from "@/types/api";

import {
  formatFinanceAmount,
  getFinanceSummary,
  getCaseDueLabel,
  WORKSPACE_CASE_KIND_META,
  WORKSPACE_SEVERITY_META,
} from "@/components/workspace/workspace-ui";

interface WorkspaceCaseCardProps {
  item: OperationalCase;
  selected: boolean;
  onSelect: () => void;
  showFinanceSummary?: boolean;
  variant?: "default" | "finance";
  supportingLine?: string | null;
  hrefTransform?: (href: string) => string;
}

function getAccentClass(severity: OperationalCase["severity"]) {
  if (severity === "critical") {
    return "bg-red-500";
  }
  if (severity === "high") {
    return "bg-amber-500";
  }
  if (severity === "medium") {
    return "bg-sky-500";
  }
  return "bg-stone-400";
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
  const severityMeta = WORKSPACE_SEVERITY_META[item.severity];
  const kindMeta = WORKSPACE_CASE_KIND_META[item.case_kind];
  const primaryAction = item.suggested_actions.find((action) => action.is_primary) ?? item.suggested_actions[0];
  const primaryActionHref = primaryAction?.href ? hrefTransform?.(primaryAction.href) ?? primaryAction.href : undefined;
  const financeSummary = showFinanceSummary ? getFinanceSummary(item) : null;
  const isFinance = variant === "finance";
  const dueAmount = formatFinanceAmount(item.finance_context?.total_due_amount);
  const residualAmount = formatFinanceAmount(item.finance_context?.total_residual_amount);
  const dueLabel = getCaseDueLabel(item);
  const accentClass = getAccentClass(item.severity);
  const entityLabel = item.secondary_entity?.label ?? item.root_entity.label;

  if (isFinance) {
    const amountLabel =
      item.case_kind === "recurring_expense_due"
        ? "Uscita"
        : item.case_kind === "payment_due_soon"
          ? "In arrivo"
          : item.case_kind === "contract_renewal_due"
            ? "Residuo"
            : "Da incassare";

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
          "rounded-[28px] border p-4 shadow-[0_24px_60px_-38px_rgba(68,64,60,0.55)] transition-all hover:-translate-y-0.5 dark:bg-zinc-900",
          selected
            ? "border-stone-800 bg-[linear-gradient(145deg,rgba(255,251,235,0.98),rgba(255,237,213,0.92))] shadow-[0_28px_80px_-42px_rgba(120,53,15,0.45)] dark:border-amber-500/40 dark:bg-[linear-gradient(145deg,rgba(39,39,42,0.98),rgba(24,24,27,0.94))]"
            : "border-stone-300/80 bg-[linear-gradient(145deg,rgba(255,255,255,0.98),rgba(250,245,240,0.96))] hover:border-stone-500/60 dark:border-zinc-800 dark:bg-[linear-gradient(145deg,rgba(39,39,42,0.98),rgba(24,24,27,0.94))]",
        )}
      >
        <div className="flex flex-col gap-3 xl:grid xl:grid-cols-[minmax(0,1fr)_230px] xl:items-start">
          <div className={cn("hidden h-16 w-1.5 shrink-0 rounded-full xl:block", accentClass)} />

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className={cn("rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]", kindMeta.tone)}>
                {kindMeta.label}
              </span>
              <span className={cn("rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]", severityMeta.tone)}>
                {severityMeta.label}
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

            <div className="mt-4 flex flex-wrap items-center gap-2.5 text-xs text-[#5f6b76]">
              <span className="rounded-full border border-stone-300/70 bg-white/80 px-2.5 py-1 text-stone-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
                {dueLabel}
              </span>
              <span className="rounded-full border border-stone-300/70 bg-white/80 px-2.5 py-1 text-stone-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
                {item.signal_count} {item.signal_count === 1 ? "segnale" : "segnali"}
              </span>
            </div>

            {financeSummary && (
              <div className="mt-4 rounded-[22px] border border-stone-300/80 bg-white/65 px-4 py-3 text-sm text-stone-700 dark:border-zinc-800 dark:bg-zinc-950/40 dark:text-zinc-300">
                {financeSummary}
              </div>
            )}
          </div>

          <div className="flex shrink-0 flex-wrap items-center gap-2 xl:flex-col xl:items-stretch">
            <div className="rounded-[24px] border border-stone-300/80 bg-stone-950 px-4 py-4 text-stone-50 shadow-[0_16px_42px_-28px_rgba(28,25,23,0.65)] dark:border-zinc-700 dark:bg-zinc-950">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-300">
                {amountLabel}
              </p>
              <p className="mt-2 font-serif text-[28px] font-semibold leading-none tracking-[-0.03em] text-stone-50">
                {dueAmount ?? residualAmount ?? "n/d"}
              </p>
              {dueAmount && residualAmount && dueAmount !== residualAmount ? (
                <p className="mt-2 text-xs text-stone-300">Residuo {residualAmount}</p>
              ) : null}

              <div className="mt-4 flex flex-col gap-2">
                {primaryActionHref ? (
                  <Button
                    asChild
                    size="sm"
                    className="h-10 border-0 bg-amber-400 text-stone-950 hover:bg-amber-300"
                    onClick={(event) => event.stopPropagation()}
                  >
                    <Link href={primaryActionHref}>
                      {primaryAction.label}
                      <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
                    </Link>
                  </Button>
                ) : (
                  <Button size="sm" className="h-10" disabled={!primaryAction?.enabled}>
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
      className={cn(
        "group relative overflow-hidden rounded-[22px] border transition-all",
        selected
          ? "border-emerald-500/30 bg-[linear-gradient(135deg,rgba(255,255,255,0.99),rgba(240,253,250,0.96))] shadow-[0_26px_54px_-38px_rgba(13,148,136,0.45)] dark:border-emerald-400/30 dark:bg-[linear-gradient(135deg,rgba(20,24,24,0.98),rgba(18,32,30,0.98))]"
          : "border-stone-200/80 bg-[linear-gradient(135deg,rgba(255,255,255,0.98),rgba(248,246,242,0.98))] shadow-[0_18px_46px_-40px_rgba(41,37,36,0.28)] hover:border-stone-300 hover:shadow-[0_22px_54px_-42px_rgba(41,37,36,0.38)] dark:border-zinc-800 dark:bg-[linear-gradient(135deg,rgba(24,24,27,0.96),rgba(20,20,24,0.98))]",
      )}
    >
      <span className={cn("absolute inset-y-0 left-0 w-1.5", accentClass)} />

      <div className="grid gap-3 px-4 py-3.5 md:grid-cols-[minmax(0,1fr)_auto] md:items-center md:gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className={cn("rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]", kindMeta.tone)}>
              {kindMeta.label}
            </span>
            <span className={cn("rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]", severityMeta.tone)}>
              {severityMeta.label}
            </span>
            <span className="rounded-full border border-stone-200/80 bg-stone-50/90 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-600 dark:border-zinc-700 dark:bg-zinc-950/70 dark:text-zinc-300">
              {dueLabel}
            </span>
          </div>

          <div className="mt-2 min-w-0">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <h3 className="text-[15px] font-semibold leading-5 text-stone-950 dark:text-zinc-50">
                {item.title}
              </h3>
              <span className="rounded-full bg-stone-100 px-2 py-0.5 text-[11px] font-medium text-stone-600 dark:bg-zinc-800 dark:text-zinc-300">
                {entityLabel}
              </span>
            </div>
            <p className="mt-1 text-[13px] leading-5 text-stone-700 dark:text-zinc-300">
              {item.reason}
            </p>
            {supportingLine ? (
              <p className="mt-1.5 text-[12px] font-medium leading-5 text-stone-600 dark:text-zinc-400">
                {supportingLine}
              </p>
            ) : null}
            {financeSummary ? (
              <p className="mt-1.5 text-[12px] font-medium leading-5 text-stone-700 dark:text-zinc-300">
                {financeSummary}
              </p>
            ) : null}
          </div>

            <div className="mt-2.5 flex flex-wrap items-center gap-1.5 text-[11px] text-stone-600 dark:text-zinc-400">
              <span className="rounded-full border border-stone-200/80 bg-white/80 px-2.5 py-1 dark:border-zinc-700 dark:bg-zinc-950/70">
                {item.signal_count} {item.signal_count === 1 ? "segnale" : "segnali"}
              </span>
              {item.secondary_entity && item.root_entity.label !== entityLabel ? (
                <span className="rounded-full border border-stone-200/80 bg-white/80 px-2.5 py-1 dark:border-zinc-700 dark:bg-zinc-950/70">
                  {item.root_entity.label}
                </span>
              ) : null}
            {!primaryAction?.enabled && primaryAction?.availability_note ? (
              <span className="rounded-full border border-stone-200/80 bg-white/80 px-2.5 py-1 dark:border-zinc-700 dark:bg-zinc-950/70">
                {primaryAction.availability_note}
              </span>
            ) : null}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 md:justify-end">
          {primaryActionHref ? (
            <Button
              asChild
              size="sm"
              className={cn(
                "h-9 rounded-full px-3.5 shadow-none",
                selected
                  ? "border-0 bg-stone-950 text-stone-50 hover:bg-stone-800 dark:bg-emerald-400 dark:text-stone-950 dark:hover:bg-emerald-300"
                  : "border-0 bg-stone-900 text-stone-50 hover:bg-stone-800 dark:bg-zinc-100 dark:text-stone-950 dark:hover:bg-zinc-200",
              )}
              onClick={(event) => event.stopPropagation()}
            >
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
        </div>
      </div>
    </div>
  );
}
