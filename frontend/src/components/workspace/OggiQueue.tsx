"use client";

import { LayoutList, SunMedium } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { ScrollArea } from "@/components/ui/scroll-area";
import { surfaceRoleClassName, type SurfaceTone } from "@/components/ui/surface-role";
import { WorkspaceCaseCard } from "@/components/workspace/WorkspaceCaseCard";
import { WORKSPACE_BUCKET_META } from "@/components/workspace/workspace-ui";
import {
  getWorkspaceBucketMarkerClass,
  getWorkspaceBucketRailClass,
  getWorkspaceBucketTone,
  getWorkspaceChipClassName,
} from "@/components/workspace/workspace-visuals";
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

const VIEW_TONE: Record<QueueView, SurfaceTone> = {
  focus: "amber",
  all: "neutral",
  backlog: "teal",
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
  const bucketTone = getWorkspaceBucketTone(section.bucket);

  if (section.total === 0 && section.items.length === 0) return null;

  return (
    <div className="space-y-2.5">
      <div className="flex items-center gap-2 px-1">
        <span className={cn("h-1.5 w-1.5 rounded-full", getWorkspaceBucketMarkerClass(section.bucket))} />
        <span
          className={getWorkspaceChipClassName(
            bucketTone,
            "px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em]",
          )}
        >
          {LANE_HINT[section.bucket] ?? meta.label}
        </span>
        <span className="text-[11px] tabular-nums text-stone-400 dark:text-zinc-500">
          {section.total}
        </span>
      </div>

      <div className={cn("ml-[2.5px] space-y-1.5 border-l-2 pl-3", getWorkspaceBucketRailClass(section.bucket))}>
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
  view,
  label,
  count,
  active,
  onClick,
}: {
  view: QueueView;
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={getWorkspaceChipClassName(
        active ? VIEW_TONE[view] : "neutral",
        cn(
          "px-3 py-1.5 text-[11px] font-semibold transition-all",
          active
            ? "shadow-sm"
            : "text-stone-500 opacity-75 hover:opacity-100 dark:text-zinc-400",
        ),
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
    <section
      className={surfaceRoleClassName(
        { role: "page", tone: "neutral" },
        cn("flex flex-col overflow-hidden", className),
      )}
    >
      {/* Header */}
      <div className="border-b border-border/70 px-4 py-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <LayoutList className="h-4 w-4 text-stone-400 dark:text-zinc-500" />
            <h2 className="text-sm font-semibold text-stone-900 dark:text-zinc-100">
              Da fare
            </h2>
          </div>
          <div className="flex items-center gap-1">
            <ViewTab view="focus" label="Focus" count={focusTotal} active={effectiveView === "focus"} onClick={() => onChangeView("focus")} />
            <ViewTab view="all" label="Tutti" count={focusTotal + backlogTotal} active={effectiveView === "all"} onClick={() => onChangeView("all")} />
            <ViewTab view="backlog" label="Prossimi" count={backlogTotal} active={effectiveView === "backlog"} onClick={() => onChangeView("backlog")} />
          </div>
        </div>

        {/* Meta counters */}
        <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-stone-400 dark:text-zinc-500">
          {completedCount > 0 && (
            <span className={getWorkspaceChipClassName("neutral", "px-2.5 py-1 text-[10px] font-medium")}>
              {completedCount} completati oggi
            </span>
          )}
          {snoozedCount > 0 && (
            <span className={getWorkspaceChipClassName("neutral", "px-2.5 py-1 text-[10px] font-medium")}>
              {snoozedCount} in pausa
            </span>
          )}
          {isLoadingBacklog && (
            <span className={getWorkspaceChipClassName("teal", "animate-pulse px-2.5 py-1 text-[10px] font-medium")}>
              Carico prossimi...
            </span>
          )}
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
            <div
              className={surfaceRoleClassName(
                { role: "context", tone: "neutral" },
                "px-4 py-5 text-center text-sm text-stone-500 dark:text-zinc-400",
              )}
            >
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
