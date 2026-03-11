"use client";

import { LayoutList, SunMedium } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { ScrollArea } from "@/components/ui/scroll-area";
import { WorkspaceCaseCard } from "@/components/workspace/WorkspaceCaseCard";
import { WORKSPACE_BUCKET_META } from "@/components/workspace/workspace-ui";
import { cn } from "@/lib/utils";
import type { OperationalCase, WorkspaceTodaySection } from "@/types/api";

/* ── Types ── */

export type QueueView = "focus" | "all" | "backlog";

/* ── Lane Section ── */

const LANE_HINT: Record<string, string> = {
  now: "Da gestire subito",
  today: "Chiudi entro oggi",
  upcoming_3d: "Entro 3 giorni",
  upcoming_7d: "Entro 7 giorni",
  waiting: "In attesa",
};

function LaneSection({
  section,
  selectedCaseId,
  onSelect,
  supportLineForItem,
  hrefTransform,
}: {
  section: WorkspaceTodaySection;
  selectedCaseId: string;
  onSelect: (caseId: string) => void;
  supportLineForItem: (item: OperationalCase) => string | null;
  hrefTransform: (href: string) => string;
}) {
  const meta = WORKSPACE_BUCKET_META[section.bucket];

  if (section.total === 0 && section.items.length === 0) return null;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 px-1">
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            section.bucket === "now" ? "bg-red-500" :
            section.bucket === "today" ? "bg-amber-500" :
            "bg-stone-400 dark:bg-zinc-500",
          )}
        />
        <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-stone-500 dark:text-zinc-400">
          {LANE_HINT[section.bucket] ?? meta.label}
        </span>
        <span className="text-[11px] font-semibold tabular-nums text-stone-400 dark:text-zinc-500">
          {section.total}
        </span>
      </div>

      <div className="space-y-1.5">
        {section.items.map((item) => (
          <WorkspaceCaseCard
            key={item.case_id}
            item={item}
            selected={item.case_id === selectedCaseId}
            onSelect={() => onSelect(item.case_id)}
            supportingLine={supportLineForItem(item)}
            hrefTransform={hrefTransform}
          />
        ))}
      </div>
    </div>
  );
}

/* ── View Switcher ── */

function ViewTab({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full px-3 py-1.5 text-[11px] font-semibold transition-colors",
        active
          ? "bg-stone-900 text-white dark:bg-zinc-100 dark:text-stone-900"
          : "text-stone-500 hover:bg-stone-100 dark:text-zinc-400 dark:hover:bg-zinc-800",
      )}
    >
      {label}
      <span className="ml-1.5 tabular-nums opacity-70">{count}</span>
    </button>
  );
}

/* ── Main Queue Panel ── */

interface OggiQueueProps {
  sections: WorkspaceTodaySection[];
  focusTotal: number;
  backlogTotal: number;
  completedCount: number;
  snoozedCount: number;
  selectedCaseId: string;
  onSelect: (caseId: string) => void;
  queueView: QueueView;
  onChangeView: (view: QueueView) => void;
  supportLineForItem: (item: OperationalCase) => string | null;
  hrefTransform: (href: string) => string;
  isLoadingBacklog?: boolean;
  className?: string;
}

export function OggiQueue({
  sections,
  focusTotal,
  backlogTotal,
  completedCount,
  snoozedCount,
  selectedCaseId,
  onSelect,
  queueView,
  onChangeView,
  supportLineForItem,
  hrefTransform,
  isLoadingBacklog,
  className,
}: OggiQueueProps) {
  const effectiveView = queueView === "focus" && focusTotal === 0 && backlogTotal > 0 ? "backlog" : queueView;

  const activeSections =
    effectiveView === "all"
      ? sections.filter((s) => s.total > 0 || s.items.length > 0)
      : effectiveView === "backlog"
        ? sections
            .filter((s) => s.bucket === "upcoming_3d" || s.bucket === "upcoming_7d" || s.bucket === "waiting")
            .filter((s) => s.total > 0 || s.items.length > 0)
        : sections
            .filter((s) => s.bucket === "now" || s.bucket === "today")
            .filter((s) => s.total > 0 || s.items.length > 0);

  const hasAnyCases = sections.some((s) => s.total > 0 || s.items.length > 0);

  return (
    <section className={cn("flex flex-col overflow-hidden rounded-2xl border border-stone-200/60 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950/80", className)}>
      {/* Header */}
      <div className="border-b border-stone-100 px-4 py-3 dark:border-zinc-800/80">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <LayoutList className="h-4 w-4 text-stone-400 dark:text-zinc-500" />
            <h2 className="text-sm font-semibold text-stone-900 dark:text-zinc-100">
              Casi operativi
            </h2>
          </div>
          <div className="flex items-center gap-1">
            <ViewTab label="Focus" count={focusTotal} active={effectiveView === "focus"} onClick={() => onChangeView("focus")} />
            <ViewTab label="Tutti" count={focusTotal + backlogTotal} active={effectiveView === "all"} onClick={() => onChangeView("all")} />
            <ViewTab label="Prossimi" count={backlogTotal} active={effectiveView === "backlog"} onClick={() => onChangeView("backlog")} />
          </div>
        </div>

        {/* Meta counters */}
        <div className="mt-2 flex gap-3 text-[11px] text-stone-400 dark:text-zinc-500">
          {completedCount > 0 && <span>{completedCount} completati oggi</span>}
          {snoozedCount > 0 && <span>{snoozedCount} in pausa</span>}
          {isLoadingBacklog && <span className="animate-pulse">Carico prossimi...</span>}
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="min-h-0 flex-1 xl:h-[calc(100vh-20rem)]">
        <div className="space-y-4 p-3">
          {!hasAnyCases ? (
            <EmptyState
              icon={SunMedium}
              title="Giornata libera"
              subtitle="Nessun caso aperto. Perfetta per follow-up o programmazione."
            />
          ) : activeSections.length === 0 ? (
            <div className="rounded-xl border border-dashed border-stone-200 px-4 py-5 text-center text-sm text-stone-500 dark:border-zinc-700 dark:text-zinc-400">
              Nessun caso in questa vista.
            </div>
          ) : (
            activeSections.map((section) => (
              <LaneSection
                key={section.bucket}
                section={section}
                selectedCaseId={selectedCaseId}
                onSelect={onSelect}
                supportLineForItem={supportLineForItem}
                hrefTransform={hrefTransform}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </section>
  );
}
