"use client";

import Link from "next/link";
import { ArrowUpRight, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { OperationalCase } from "@/types/api";

import {
  getCaseDueLabel,
  getCaseImpactLine,
  WORKSPACE_CASE_KIND_META,
  WORKSPACE_SEVERITY_META,
} from "@/components/workspace/workspace-ui";

interface WorkspaceCaseCardProps {
  item: OperationalCase;
  selected: boolean;
  onSelect: () => void;
}

export function WorkspaceCaseCard({ item, selected, onSelect }: WorkspaceCaseCardProps) {
  const severityMeta = WORKSPACE_SEVERITY_META[item.severity];
  const kindMeta = WORKSPACE_CASE_KIND_META[item.case_kind];
  const primaryAction = item.suggested_actions.find((action) => action.is_primary) ?? item.suggested_actions[0];
  const impactLine = getCaseImpactLine(item);

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
        "rounded-3xl border bg-white p-4 shadow-sm transition-all hover:border-primary/30 hover:shadow-md dark:bg-zinc-900",
        selected ? "border-primary/40 bg-primary/5 shadow-[0_20px_45px_-30px_rgba(14,165,164,0.6)]" : "border-border/70",
      )}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
        <div
          className={cn(
            "hidden h-16 w-1 shrink-0 rounded-full lg:block",
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

          <h3 className="mt-3 text-base font-semibold leading-tight text-foreground">{item.title}</h3>
          <p className="mt-1 text-sm text-muted-foreground">{item.reason}</p>
          <p className="mt-3 text-sm font-medium text-foreground/85">{impactLine}</p>

          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span className="rounded-full bg-muted px-2.5 py-1">{getCaseDueLabel(item)}</span>
            <span className="rounded-full bg-muted px-2.5 py-1">
              {item.signal_count} {item.signal_count === 1 ? "segnale" : "segnali"}
            </span>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-2 lg:flex-col lg:items-end">
          {primaryAction?.href ? (
            <Button asChild size="sm" className="h-10" onClick={(event) => event.stopPropagation()}>
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
        </div>
      </div>
    </div>
  );
}
