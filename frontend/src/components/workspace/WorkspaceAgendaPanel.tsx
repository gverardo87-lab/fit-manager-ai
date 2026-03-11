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

function getAgendaLead(items: WorkspaceTodayAgenda["items"], maxItems: number) {
  const relevantItems = items.filter((item) => item.status !== "past");
  return relevantItems.slice(0, maxItems);
}

export function WorkspaceAgendaPanel({
  agenda,
  maxItems = 1,
}: WorkspaceAgendaPanelProps) {
  const currentTime = parseWorkspaceDateTime(agenda.current_time);
  const leadItems = getAgendaLead(agenda.items, maxItems);
  const nextItem = leadItems[0];
  const nextStartsAt = parseWorkspaceDateTime(nextItem?.starts_at ?? null);
  const minutesToNext =
    currentTime && nextStartsAt ? Math.round((nextStartsAt.getTime() - currentTime.getTime()) / 60000) : null;
  const shouldShow =
    nextItem &&
    (nextItem.status === "current" || minutesToNext === null || (minutesToNext >= 0 && minutesToNext <= 120));
  const items = shouldShow ? leadItems : [];

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="rounded-[24px] border border-stone-800/90 bg-stone-950 px-3.5 py-3 text-stone-50 shadow-[0_24px_56px_-34px_rgba(28,25,23,0.72)] dark:border-zinc-700 dark:bg-zinc-950">
      <div className="flex flex-col gap-2.5 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-white/10">
            <CalendarClock className="h-4.5 w-4.5 text-amber-300" />
          </div>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-300">
                Prossimo slot utile
              </p>
              {minutesToNext !== null && minutesToNext > 0 ? (
                <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-300">
                  tra {minutesToNext} min
                </span>
              ) : nextItem?.status === "current" ? (
                <span className="rounded-full border border-emerald-500/30 bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-200">
                  in corso
                </span>
              ) : null}
            </div>

            <div className="mt-1.5 space-y-1.5">
              {items.map((item) => {
                const startsAtLabel = formatWorkspaceDateTime(item.starts_at) ?? item.starts_at;

                return (
                  <Link
                    key={item.event_id}
                    href={item.href}
                    className="block rounded-[18px] border border-white/10 bg-white/5 px-3 py-2 transition-colors hover:bg-white/10"
                  >
                    <div className="flex items-start gap-2.5">
                      <div className="mt-0.5 flex h-7.5 w-7.5 shrink-0 items-center justify-center rounded-xl bg-white/10">
                        <Clock3 className="h-3.5 w-3.5 text-stone-200" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <p className="text-[13px] font-semibold leading-5 text-stone-50">
                            {item.title}
                          </p>
                          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-300">
                            {item.category}
                          </span>
                        </div>
                        <p className="mt-0.5 text-[12px] leading-5 text-stone-300">
                          {startsAtLabel}
                          {item.client_label ? ` · ${item.client_label}` : ""}
                        </p>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>

        <Button
          asChild
          variant="ghost"
          size="sm"
          className="h-8 shrink-0 rounded-full px-3 text-xs text-stone-200 hover:bg-white/10 hover:text-stone-50"
        >
          <Link href="/agenda">
            Apri agenda
            <ArrowRight className="ml-1 h-3.5 w-3.5" />
          </Link>
        </Button>
      </div>
    </div>
  );
}
