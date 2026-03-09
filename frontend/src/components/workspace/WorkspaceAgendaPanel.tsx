"use client";

import Link from "next/link";
import { ArrowRight, CalendarClock, Clock3 } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { WorkspaceTodayAgenda } from "@/types/api";

import { formatWorkspaceDateTime } from "@/components/workspace/workspace-ui";

interface WorkspaceAgendaPanelProps {
  agenda: WorkspaceTodayAgenda;
  maxItems?: number;
}

function parseWorkspaceDateTime(value: string | null): Date | null {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function WorkspaceAgendaPanel({
  agenda,
  maxItems = 1,
}: WorkspaceAgendaPanelProps) {
  const relevantItems = agenda.items.filter((item) => item.status !== "past");
  const nextItem = relevantItems[0];
  const currentTime = parseWorkspaceDateTime(agenda.current_time);
  const nextStartsAt = parseWorkspaceDateTime(nextItem?.starts_at ?? null);
  const minutesToNext =
    currentTime && nextStartsAt ? Math.round((nextStartsAt.getTime() - currentTime.getTime()) / 60000) : null;
  const shouldShow =
    nextItem &&
    (nextItem.status === "current" || minutesToNext === null || (minutesToNext >= 0 && minutesToNext <= 120));
  const items = shouldShow ? relevantItems.slice(0, maxItems) : [];

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="rounded-3xl border border-border/60 bg-stone-50/80 p-4 shadow-sm dark:bg-zinc-900">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-100 to-cyan-100 dark:from-sky-950/30 dark:to-cyan-950/30">
            <CalendarClock className="h-4.5 w-4.5 text-sky-700 dark:text-sky-300" />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Prossimo slot
            </p>
            <p className="text-sm text-muted-foreground">
              Lo metto qui solo quando puo cambiare quello che fai adesso.
            </p>
          </div>
        </div>
        <Button asChild variant="ghost" size="sm" className="h-8 text-xs">
          <Link href="/agenda">
            Apri agenda
            <ArrowRight className="ml-1 h-3.5 w-3.5" />
          </Link>
        </Button>
      </div>

      <div className="mt-3 space-y-2">
        {items.map((item) => {
          const startsAtLabel = formatWorkspaceDateTime(item.starts_at) ?? item.starts_at;

          return (
            <Link
              key={item.event_id}
              href={item.href}
              className="rounded-2xl border border-border/70 bg-white p-3 transition-colors hover:bg-muted/40 dark:bg-zinc-950/50"
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-muted/70">
                  <Clock3 className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold">{item.title}</p>
                    <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                      {item.category}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{startsAtLabel}</p>
                  {item.client_label && (
                    <p className="mt-1 text-xs text-muted-foreground">{item.client_label}</p>
                  )}
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
