"use client";

import { useEffect, useState } from "react";

import {
  surfaceChipClassName,
  surfaceRoleClassName,
  type SurfaceTone,
} from "@/components/ui/surface-role";
import { cn } from "@/lib/utils";
import type { OperationalCase, SessionPrepResponse } from "@/types/api";

const TIME_FMT = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });
const DATE_FMT = new Intl.DateTimeFormat("it-IT", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

function getDayBrief(
  prep: SessionPrepResponse,
  attentionCount: number,
  readyCount: number,
): { tone: SurfaceTone; title: string } {
  if (attentionCount > 0) {
    return {
      tone: "red",
      title:
        attentionCount === 1
          ? "Una seduta chiede attenzione"
          : `${attentionCount} sedute chiedono attenzione`,
    };
  }
  if (prep.total_sessions > 0 && readyCount === prep.total_sessions) {
    return { tone: "teal", title: "La giornata è in linea" };
  }
  return {
    tone: "neutral",
    title: prep.total_sessions > 0 ? "La giornata è sotto controllo" : "Nessuna seduta oggi",
  };
}

export interface OggiHeroProps {
  prep: SessionPrepResponse;
  attentionCount: number;
  readyCount: number;
  extraCaseCount: number;
  alertClients: number;
  supportCase?: OperationalCase | null;
  compact?: boolean;
  lastUpdatedAt?: number | null;
  isRefreshing?: boolean;
  className?: string;
}

export function OggiHero({
  prep,
  attentionCount,
  readyCount,
  extraCaseCount,
  lastUpdatedAt,
  isRefreshing = false,
  className,
}: OggiHeroProps) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(id);
  }, []);

  const { tone, title } = getDayBrief(prep, attentionCount, readyCount);
  const syncLabel = lastUpdatedAt ? TIME_FMT.format(new Date(lastUpdatedAt)) : null;

  const titleColor =
    tone === "red"
      ? "text-red-700 dark:text-red-300"
      : tone === "teal"
        ? "text-emerald-700 dark:text-emerald-300"
        : "text-foreground";

  return (
    <section className={className}>
      <div
        className={surfaceRoleClassName(
          { role: "page", tone: "neutral" },
          "oggi-command-bar px-5 py-4",
        )}
      >
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {/* Sinistra: data + status */}
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              {DATE_FMT.format(now)}
              <span className="mx-2 opacity-40">·</span>
              {TIME_FMT.format(now)}
            </p>
            <h1 className={cn("mt-1.5 text-[2rem] font-black tracking-tight leading-none", titleColor)}>
              {title}
            </h1>
          </div>

          {/* Destra: KPI chips inline + sync */}
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={surfaceChipClassName(
                { tone: "neutral" },
                "px-3 py-1.5 text-[11px] font-bold tabular-nums",
              )}
            >
              {prep.total_sessions} {prep.total_sessions === 1 ? "seduta" : "sedute"}
            </span>

            {attentionCount > 0 && (
              <span
                className={surfaceChipClassName(
                  { tone: "red" },
                  "px-3 py-1.5 text-[11px] font-bold tabular-nums",
                )}
              >
                {attentionCount} da sbloccare
              </span>
            )}

            {readyCount > 0 && (
              <span
                className={surfaceChipClassName(
                  { tone: "teal" },
                  "px-3 py-1.5 text-[11px] font-bold tabular-nums",
                )}
              >
                {readyCount} {readyCount === 1 ? "pronta" : "pronte"}
              </span>
            )}

            {extraCaseCount > 0 && (
              <span
                className={surfaceChipClassName(
                  { tone: "amber" },
                  "px-3 py-1.5 text-[11px] font-bold tabular-nums",
                )}
              >
                {extraCaseCount} extra
              </span>
            )}

            {syncLabel && (
              <span
                className={surfaceChipClassName(
                  { tone: isRefreshing ? "amber" : "neutral" },
                  "px-2.5 py-1.5 text-[10px] font-bold",
                )}
              >
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    isRefreshing ? "oggi-pulse-dot bg-amber-500" : "bg-emerald-500",
                  )}
                />
                {isRefreshing ? "Sync" : syncLabel}
              </span>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

export function OggiHeroSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={surfaceRoleClassName(
        { role: "page", tone: "neutral" },
        cn("px-5 py-4", className),
      )}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="h-3 w-36 rounded bg-muted/60" />
          <div className="h-7 w-52 rounded-xl bg-muted/40" />
        </div>
        <div className="flex gap-2">
          <div className="h-7 w-20 rounded-full bg-muted/40" />
          <div className="h-7 w-24 rounded-full bg-muted/40" />
        </div>
      </div>
    </div>
  );
}
