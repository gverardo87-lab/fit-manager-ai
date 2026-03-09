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
}

export function WorkspaceDetailPanel({
  selectedCase,
  detail,
  isLoading,
  isError,
  onRetry,
}: WorkspaceDetailPanelProps) {
  if (!selectedCase) {
    return (
      <div className="flex min-h-[620px] items-center rounded-3xl border border-border/70 bg-white p-6 shadow-sm dark:bg-zinc-900">
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
      <div className="rounded-3xl border border-destructive/40 bg-destructive/5 p-5 shadow-sm">
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
    <div className="flex min-h-[620px] flex-col rounded-3xl border border-border/70 bg-white shadow-sm dark:bg-zinc-900">
      <div className="border-b px-5 py-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${kindMeta.tone}`}>
            {kindMeta.label}
          </span>
          <span className={`rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${severityMeta.tone}`}>
            {severityMeta.label}
          </span>
        </div>

        <h2 className="mt-3 text-lg font-semibold leading-tight">{currentCase.title}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{currentCase.reason}</p>

        <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
          <span className="rounded-full bg-muted px-2.5 py-1">{getCaseDueLabel(currentCase)}</span>
          {currentCase.due_date && (
            <span className="rounded-full bg-muted px-2.5 py-1">
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
            <div className="rounded-2xl border border-border/70 bg-muted/25 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Azione consigliata
              </p>
              <p className="mt-2 text-sm text-foreground">
                Questo e il passo giusto per sbloccare il caso senza sporcare il resto della giornata.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {primaryAction?.href ? (
                  <Button asChild size="sm" className="h-10">
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
                      <Button key={action.id} asChild size="sm" variant="outline" className="h-10">
                        <Link href={action.href}>{action.label}</Link>
                      </Button>
                    ) : (
                      <Button key={action.id} size="sm" variant="outline" className="h-10" disabled={!action.enabled}>
                        {action.label}
                      </Button>
                    ),
                  )}
              </div>
              {financeSummary && (
                <p className="mt-3 text-xs text-muted-foreground">{financeSummary}</p>
              )}
            </div>

            <div>
              <div className="mb-3 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold">Perche ora</h3>
              </div>
              {detail?.signals.length ? (
                <div className="space-y-2">
                  {detail.signals.map((signal) => (
                    <div
                      key={`${currentCase.case_id}-${signal.signal_code}`}
                      className="rounded-2xl border border-border/70 bg-background p-3"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-medium">{signal.label}</p>
                        {signal.due_date && (
                          <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                            {formatWorkspaceDate(signal.due_date)}
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">{signal.reason}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Nessun segnale aggiuntivo disponibile.</p>
              )}
            </div>

            <Separator />

            <div>
              <div className="mb-3 flex items-center gap-2">
                <ListTree className="h-4 w-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold">Contesto collegato</h3>
              </div>
              {detail?.related_entities.length ? (
                <div className="flex flex-wrap gap-2">
                  {detail.related_entities.map((entity) =>
                    entity.href ? (
                      <Link
                        key={`${entity.type}-${entity.id}`}
                        href={entity.href}
                        className="inline-flex items-center gap-1 rounded-full border border-border/70 bg-background px-3 py-1.5 text-xs font-medium transition-colors hover:bg-muted"
                      >
                        {entity.label}
                        <ArrowUpRight className="h-3 w-3" />
                      </Link>
                    ) : (
                      <span
                        key={`${entity.type}-${entity.id}`}
                        className="inline-flex items-center rounded-full border border-border/70 bg-background px-3 py-1.5 text-xs font-medium"
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

            <Separator />

            <div>
              <div className="mb-3 flex items-center gap-2">
                <Clock3 className="h-4 w-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold">Timeline sintetica</h3>
              </div>
              {detail?.activity_preview.length ? (
                <div className="space-y-3">
                  {detail.activity_preview.map((item, index) => (
                    <div key={`${item.at}-${item.label}-${index}`} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <span className="h-2.5 w-2.5 rounded-full bg-primary/70" />
                        {index < detail.activity_preview.length - 1 && (
                          <span className="mt-1 h-full w-px bg-border" />
                        )}
                      </div>
                      <div className="min-w-0 flex-1 pb-3">
                        <p className="text-sm font-medium">{item.label}</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {formatWorkspaceDateTime(item.at)}
                        </p>
                        {item.href && (
                          <Link
                            href={item.href}
                            className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
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
