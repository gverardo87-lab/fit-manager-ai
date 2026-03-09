"use client";

import Link from "next/link";
import { ArrowUpRight, ChevronRight } from "lucide-react";

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
}

export function WorkspaceCaseCard({
  item,
  selected,
  onSelect,
  showFinanceSummary = false,
  variant = "default",
}: WorkspaceCaseCardProps) {
  const severityMeta = WORKSPACE_SEVERITY_META[item.severity];
  const kindMeta = WORKSPACE_CASE_KIND_META[item.case_kind];
  const primaryAction = item.suggested_actions.find((action) => action.is_primary) ?? item.suggested_actions[0];
  const financeSummary = showFinanceSummary ? getFinanceSummary(item) : null;
  const isFinance = variant === "finance";
  const dueAmount = formatFinanceAmount(item.finance_context?.total_due_amount);
  const residualAmount = formatFinanceAmount(item.finance_context?.total_residual_amount);
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
        "transition-all",
        isFinance
          ? "rounded-[28px] border p-4 shadow-[0_24px_60px_-38px_rgba(68,64,60,0.55)] hover:-translate-y-0.5 dark:bg-zinc-900"
          : "rounded-3xl border bg-white p-3.5 shadow-sm hover:border-primary/30 hover:shadow-md dark:bg-zinc-900",
        isFinance
          ? selected
            ? "border-stone-800 bg-[linear-gradient(145deg,rgba(255,251,235,0.98),rgba(255,237,213,0.92))] shadow-[0_28px_80px_-42px_rgba(120,53,15,0.45)] dark:border-amber-500/40 dark:bg-[linear-gradient(145deg,rgba(39,39,42,0.98),rgba(24,24,27,0.94))]"
            : "border-stone-300/80 bg-[linear-gradient(145deg,rgba(255,255,255,0.98),rgba(250,245,240,0.96))] hover:border-stone-500/60 dark:border-zinc-800 dark:bg-[linear-gradient(145deg,rgba(39,39,42,0.98),rgba(24,24,27,0.94))]"
          : selected
            ? "border-primary/40 bg-primary/5 shadow-[0_20px_45px_-30px_rgba(14,165,164,0.6)]"
            : "border-border/70",
      )}
    >
      <div className={cn("flex flex-col gap-3", isFinance ? "xl:grid xl:grid-cols-[minmax(0,1fr)_230px] xl:items-start" : "lg:flex-row lg:items-start")}>
        <div
          className={cn(
            "hidden shrink-0 rounded-full",
            isFinance ? "xl:block h-16 w-1.5" : "lg:block h-14 w-1",
            item.severity === "critical"
              ? "bg-red-500"
              : item.severity === "high"
                ? "bg-amber-500"
                : item.severity === "medium"
                  ? "bg-blue-500"
                  : "bg-zinc-400",
          )}
        />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn("rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]", kindMeta.tone)}>
              {kindMeta.label}
            </span>
            <span className={cn("rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]", severityMeta.tone)}>
              {severityMeta.label}
            </span>
          </div>

          <div className={cn("mt-3", isFinance && "min-w-0")}>
            <div className="min-w-0">
              <h3
                className={cn(
                  "leading-tight text-foreground",
                  isFinance ? "text-lg font-bold tracking-[-0.015em]" : "text-base font-semibold",
                )}
              >
                {item.title}
              </h3>
              <p className={cn("mt-1 text-sm text-muted-foreground", isFinance && "max-w-2xl text-[14px] leading-6 text-stone-700 dark:text-zinc-300")}>
                {item.reason}
              </p>
            </div>
          </div>
          {!isFinance && financeSummary && <p className="mt-2 text-sm font-medium text-foreground/85">{financeSummary}</p>}

          <div className={cn("mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground", isFinance && "mt-4 gap-2.5")}>
            <span
              className={cn(
                "rounded-full px-2.5 py-1",
                isFinance ? "border border-stone-300/70 bg-white/80 text-stone-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300" : "bg-muted",
              )}
            >
              {getCaseDueLabel(item)}
            </span>
            <span
              className={cn(
                "rounded-full px-2.5 py-1",
                isFinance ? "border border-stone-300/70 bg-white/80 text-stone-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300" : "bg-muted",
              )}
            >
              {item.signal_count} {item.signal_count === 1 ? "segnale" : "segnali"}
            </span>
          </div>

          {isFinance && financeSummary && (
            <div className="mt-4 rounded-[22px] border border-stone-300/80 bg-white/65 px-4 py-3 text-sm text-stone-700 dark:border-zinc-800 dark:bg-zinc-950/40 dark:text-zinc-300">
              {financeSummary}
            </div>
          )}
        </div>

        <div className={cn("flex shrink-0 flex-wrap items-center gap-2", isFinance ? "xl:flex-col xl:items-stretch" : "lg:flex-col lg:items-end")}>
          {isFinance ? (
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
                {primaryAction?.href ? (
                  <Button
                    asChild
                    size="sm"
                    className="h-10 border-0 bg-amber-400 text-stone-950 hover:bg-amber-300"
                    onClick={(event) => event.stopPropagation()}
                  >
                    <Link href={primaryAction.href}>
                      {primaryAction.label}
                      <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
                    </Link>
                  </Button>
                ) : (
                  <Button size="sm" className="h-10" disabled={!primaryAction?.enabled}>
                    {primaryAction?.label ?? "Apri"}
                  </Button>
                )}

                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-10 justify-between px-0 text-stone-300 hover:bg-transparent hover:text-stone-50"
                  onClick={(event) => {
                    event.stopPropagation();
                    onSelect();
                  }}
                >
                  Dettaglio
                  <ChevronRight className="ml-1 h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ) : (
            <>
              {primaryAction?.href ? (
                <Button
                  asChild
                  size="sm"
                  className="h-10"
                  onClick={(event) => event.stopPropagation()}
                >
                  <Link href={primaryAction.href}>
                    {primaryAction.label}
                    <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
                  </Link>
                </Button>
              ) : (
                <Button size="sm" className="h-10" disabled={!primaryAction?.enabled}>
                  {primaryAction?.label ?? "Apri"}
                </Button>
              )}

              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-10 text-muted-foreground"
                onClick={(event) => {
                  event.stopPropagation();
                  onSelect();
                }}
              >
                Dettaglio
                <ChevronRight className="ml-1 h-3.5 w-3.5" />
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
