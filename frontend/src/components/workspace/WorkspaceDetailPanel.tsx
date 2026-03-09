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
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { OperationalCase, WorkspaceCaseDetailResponse } from "@/types/api";

import {
  formatWorkspaceDate,
  formatWorkspaceDateTime,
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
}

export function WorkspaceDetailPanel({
  selectedCase,
  detail,
  isLoading,
  isError,
  onRetry,
  variant = "default",
}: WorkspaceDetailPanelProps) {
  const isFinance = variant === "finance";
  if (!selectedCase) {
    return (
      <div
        className={cn(
          "flex min-h-[620px] items-center p-6",
          isFinance
            ? "rounded-[32px] border border-stone-300/80 bg-[linear-gradient(160deg,rgba(255,251,235,0.98),rgba(255,245,238,0.94))] shadow-[0_30px_80px_-50px_rgba(120,53,15,0.35)] dark:border-zinc-800 dark:bg-[linear-gradient(160deg,rgba(39,39,42,0.98),rgba(24,24,27,0.94))]"
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
            ? "rounded-[32px] border border-red-300/60 bg-[linear-gradient(160deg,rgba(254,242,242,0.98),rgba(255,247,237,0.94))] shadow-[0_24px_70px_-48px_rgba(185,28,28,0.4)]"
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
  const severityMeta = WORKSPACE_SEVERITY_META[currentCase.severity];
  const kindMeta = WORKSPACE_CASE_KIND_META[currentCase.case_kind];
  const financeSummary = getFinanceSummary(currentCase);
  const primaryAction = currentCase.suggested_actions.find((action) => action.is_primary) ?? currentCase.suggested_actions[0];

  return (
    <div
      className={cn(
        "flex min-h-[620px] flex-col",
        isFinance
          ? "rounded-[32px] border border-stone-300/80 bg-[linear-gradient(160deg,rgba(255,251,235,0.98),rgba(255,245,238,0.94))] shadow-[0_30px_80px_-50px_rgba(120,53,15,0.35)] dark:border-zinc-800 dark:bg-[linear-gradient(160deg,rgba(39,39,42,0.98),rgba(24,24,27,0.94))]"
          : "rounded-3xl border border-border/70 bg-white shadow-sm dark:bg-zinc-900",
      )}
    >
      <div
        className={cn(
          "px-5 py-5",
          isFinance
            ? "rounded-t-[32px] border-b border-stone-300/70 bg-stone-950 text-stone-50 dark:border-zinc-800 dark:bg-zinc-950"
            : "border-b",
        )}
      >
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${kindMeta.tone}`}>
            {kindMeta.label}
          </span>
          <span className={`rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${severityMeta.tone}`}>
            {severityMeta.label}
          </span>
        </div>

        <h2 className={cn("mt-3 leading-tight", isFinance ? "text-[26px] font-bold tracking-[-0.02em] text-stone-50" : "text-lg font-semibold")}>
          {currentCase.title}
        </h2>
        <p className={cn("mt-1 text-sm", isFinance ? "max-w-2xl text-stone-300" : "text-muted-foreground")}>
          {currentCase.reason}
        </p>

        <div className={cn("mt-4 flex flex-wrap gap-2 text-xs", isFinance ? "text-stone-300" : "text-muted-foreground")}>
          <span className={cn("rounded-full px-2.5 py-1", isFinance ? "border border-stone-700 bg-stone-900/80" : "bg-muted")}>
            {getCaseDueLabel(currentCase)}
          </span>
          {currentCase.due_date && (
            <span className={cn("rounded-full px-2.5 py-1", isFinance ? "border border-stone-700 bg-stone-900/80" : "bg-muted")}>
              Scadenza {formatWorkspaceDate(currentCase.due_date)}
            </span>
          )}
        </div>
      </div>

      {isLoading && !detail ? (
        <div className="space-y-4 p-5">
          <Skeleton className="h-20 rounded-2xl" />
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-16 rounded-2xl" />
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-28 rounded-2xl" />
        </div>
      ) : (
        <ScrollArea className="min-h-0 flex-1">
          <div className="space-y-5 p-5">
            <div
              className={cn(
                "rounded-[24px] border p-4",
                isFinance
                  ? "border-stone-300/80 bg-[linear-gradient(160deg,rgba(28,25,23,0.98),rgba(68,64,60,0.96))] text-stone-50 shadow-inner dark:border-zinc-700 dark:bg-[linear-gradient(160deg,rgba(24,24,27,0.98),rgba(39,39,42,0.98))]"
                  : "border-border/70 bg-muted/25",
              )}
            >
              <p className={cn("text-[11px] font-semibold uppercase tracking-[0.16em]", isFinance ? "text-stone-300" : "text-muted-foreground")}>
                Azione consigliata
              </p>
              <p className={cn("mt-2 text-sm", isFinance ? "text-stone-100" : "text-foreground")}>
                Questo e il passo giusto per sbloccare il caso senza sporcare il resto della giornata.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {primaryAction?.href ? (
                  <Button
                    asChild
                    size="sm"
                    className={cn("h-10", isFinance && "border-0 bg-amber-400 text-stone-950 hover:bg-amber-300")}
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
                {currentCase.suggested_actions
                  .filter((action) => action.id !== primaryAction?.id)
                  .slice(0, 2)
                  .map((action) =>
                    action.href ? (
                      <Button
                        key={action.id}
                        asChild
                        size="sm"
                        variant="outline"
                        className={cn("h-10", isFinance && "border-stone-600 bg-transparent text-stone-100 hover:bg-stone-800 hover:text-stone-50")}
                      >
                        <Link href={action.href}>{action.label}</Link>
                      </Button>
                    ) : (
                      <Button
                        key={action.id}
                        size="sm"
                        variant="outline"
                        className={cn("h-10", isFinance && "border-stone-600 bg-transparent text-stone-100 hover:bg-stone-800 hover:text-stone-50")}
                        disabled={!action.enabled}
                      >
                        {action.label}
                      </Button>
                    ),
                  )}
              </div>
              {financeSummary && (
                <p className={cn("mt-3 text-xs", isFinance ? "text-stone-300" : "text-muted-foreground")}>{financeSummary}</p>
              )}
            </div>

            <div>
              <div className="mb-3 flex items-center gap-2">
                <AlertCircle className={cn("h-4 w-4", isFinance ? "text-stone-500" : "text-muted-foreground")} />
                <h3 className="text-sm font-semibold">Perche ora</h3>
              </div>
              {detail?.signals.length ? (
                <div className="space-y-2">
                  {detail.signals.map((signal) => (
                    <div
                      key={`${currentCase.case_id}-${signal.signal_code}`}
                      className={cn(
                        "rounded-2xl border p-3",
                        isFinance
                          ? "border-stone-300/80 bg-white/75 dark:border-zinc-800 dark:bg-zinc-950/50"
                          : "border-border/70 bg-background",
                      )}
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-medium">{signal.label}</p>
                        {signal.due_date && (
                          <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide", isFinance ? "border border-stone-300/80 bg-stone-100 text-stone-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300" : "bg-muted text-muted-foreground")}>
                            {formatWorkspaceDate(signal.due_date)}
                          </span>
                        )}
                      </div>
                      <p className={cn("mt-1 text-xs", isFinance ? "text-stone-600 dark:text-zinc-400" : "text-muted-foreground")}>{signal.reason}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Nessun segnale aggiuntivo disponibile.</p>
              )}
            </div>

            <Separator className={cn(isFinance && "bg-stone-300/80 dark:bg-zinc-800")} />

            <div>
              <div className="mb-3 flex items-center gap-2">
                <ListTree className={cn("h-4 w-4", isFinance ? "text-stone-500" : "text-muted-foreground")} />
                <h3 className="text-sm font-semibold">Contesto collegato</h3>
              </div>
              {detail?.related_entities.length ? (
                <div className="flex flex-wrap gap-2">
                  {detail.related_entities.map((entity) =>
                    entity.href ? (
                      <Link
                        key={`${entity.type}-${entity.id}`}
                        href={entity.href}
                        className={cn(
                          "inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
                          isFinance
                            ? "border border-stone-300/80 bg-white/75 text-stone-700 hover:bg-stone-100 dark:border-zinc-800 dark:bg-zinc-950/50 dark:text-zinc-200 dark:hover:bg-zinc-900"
                            : "border border-border/70 bg-background hover:bg-muted",
                        )}
                      >
                        {entity.label}
                        <ArrowUpRight className="h-3 w-3" />
                      </Link>
                    ) : (
                      <span
                        key={`${entity.type}-${entity.id}`}
                        className={cn(
                          "inline-flex items-center rounded-full px-3 py-1.5 text-xs font-medium",
                          isFinance
                            ? "border border-stone-300/80 bg-white/75 text-stone-700 dark:border-zinc-800 dark:bg-zinc-950/50 dark:text-zinc-200"
                            : "border border-border/70 bg-background",
                        )}
                      >
                        {entity.label}
                      </span>
                    ),
                  )}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Nessun contesto aggiuntivo disponibile.</p>
              )}
            </div>

            <Separator className={cn(isFinance && "bg-stone-300/80 dark:bg-zinc-800")} />

            <div>
              <div className="mb-3 flex items-center gap-2">
                <Clock3 className={cn("h-4 w-4", isFinance ? "text-stone-500" : "text-muted-foreground")} />
                <h3 className="text-sm font-semibold">Timeline sintetica</h3>
              </div>
              {detail?.activity_preview.length ? (
                <div className="space-y-3">
                  {detail.activity_preview.map((item, index) => (
                    <div key={`${item.at}-${item.label}-${index}`} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <span className={cn("h-2.5 w-2.5 rounded-full", isFinance ? "bg-amber-500" : "bg-primary/70")} />
                        {index < detail.activity_preview.length - 1 && (
                          <span className={cn("mt-1 h-full w-px", isFinance ? "bg-stone-300 dark:bg-zinc-800" : "bg-border")} />
                        )}
                      </div>
                      <div className="min-w-0 flex-1 pb-3">
                        <p className="text-sm font-medium">{item.label}</p>
                        <p className={cn("mt-1 text-xs", isFinance ? "text-stone-600 dark:text-zinc-400" : "text-muted-foreground")}>
                          {formatWorkspaceDateTime(item.at)}
                        </p>
                        {item.href && (
                          <Link
                            href={item.href}
                            className={cn("mt-2 inline-flex items-center gap-1 text-xs font-medium hover:underline", isFinance ? "text-amber-700 dark:text-amber-400" : "text-primary")}
                          >
                            Apri contesto
                            <ArrowUpRight className="h-3 w-3" />
                          </Link>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Nessuna timeline disponibile.</p>
              )}
            </div>
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
