"use client";

/**
 * AlertHub — Pannello alert operativi con card severity-aware.
 *
 * Layout griglia 2 colonne, card con bordo accent sinistro,
 * icone in sfondo colorato, expand/collapse.
 */

import { useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  Bell,
  CheckCircle2,
  ChevronDown,
  CreditCard,
  Ghost,
  UserX,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { DashboardAlerts, AlertItem } from "@/types/api";
import { MAX_VISIBLE_ALERTS } from "@/lib/dashboard-helpers";

// ── Config ──

const ALERT_ICON: Record<string, typeof Ghost> = {
  ghost_events: Ghost,
  expiring_contracts: CreditCard,
  inactive_clients: UserX,
};

const SEVERITY_STYLES: Record<string, {
  accent: string;
  bg: string;
  iconBg: string;
  icon: string;
  text: string;
}> = {
  critical: {
    accent: "border-l-red-500",
    bg: "bg-red-50/60 dark:bg-red-950/15",
    iconBg: "bg-red-100 dark:bg-red-900/30",
    icon: "text-red-500 dark:text-red-400",
    text: "text-red-700 dark:text-red-300",
  },
  warning: {
    accent: "border-l-amber-500",
    bg: "bg-amber-50/60 dark:bg-amber-950/15",
    iconBg: "bg-amber-100 dark:bg-amber-900/30",
    icon: "text-amber-500 dark:text-amber-400",
    text: "text-amber-700 dark:text-amber-300",
  },
  info: {
    accent: "border-l-blue-500",
    bg: "bg-blue-50/60 dark:bg-blue-950/15",
    iconBg: "bg-blue-100 dark:bg-blue-900/30",
    icon: "text-blue-500 dark:text-blue-400",
    text: "text-blue-700 dark:text-blue-300",
  },
};

// ── Component ──

interface AlertHubProps {
  alerts: DashboardAlerts | undefined;
  isLoading: boolean;
  alertActions: Record<string, () => void>;
}

export function AlertHub({ alerts, isLoading, alertActions }: AlertHubProps) {
  const [expanded, setExpanded] = useState(false);

  if (isLoading) {
    return <AlertHubSkeleton />;
  }

  const visibleAlerts = alerts?.items.filter((item) => item.category !== "overdue_rates") ?? [];

  if (visibleAlerts.length === 0) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50/60 px-4 py-3 dark:border-emerald-900/40 dark:bg-emerald-950/20">
        <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
        <p className="text-sm font-medium text-emerald-700 dark:text-emerald-400">
          Nessun alert operativo — tutto sotto controllo
        </p>
      </div>
    );
  }

  const displayAlerts = expanded ? visibleAlerts : visibleAlerts.slice(0, MAX_VISIBLE_ALERTS);
  const hasMore = visibleAlerts.length > MAX_VISIBLE_ALERTS;
  const criticalCount = visibleAlerts.filter((a) => a.severity === "critical").length;
  const remaining = visibleAlerts.length - MAX_VISIBLE_ALERTS;

  return (
    <div id="alert-panel" className="rounded-2xl border bg-gradient-to-br from-white via-white to-zinc-50/70 p-4 shadow-sm sm:p-5 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-800/50">
      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-amber-100 to-orange-100 dark:from-amber-900/30 dark:to-orange-900/30">
            <Bell className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            {criticalCount > 0 && (
              <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white shadow-sm shadow-red-500/30">
                {criticalCount}
              </span>
            )}
          </div>
          <div>
            <h3 className="text-sm font-bold sm:text-base">Alert operativi</h3>
            <p className="text-[11px] font-medium text-muted-foreground/70">
              {visibleAlerts.length} {visibleAlerts.length === 1 ? "notifica attiva" : "notifiche attive"}
            </p>
          </div>
        </div>
      </div>

      {/* Alert grid */}
      <div className="grid gap-2 sm:grid-cols-2">
        {displayAlerts.map((item, idx) => (
          <AlertCard
            key={`${item.category}-${idx}`}
            item={item}
            onAction={alertActions[item.category]}
          />
        ))}

        {hasMore && !expanded && (
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="flex items-center justify-center gap-1.5 rounded-xl border border-dashed border-zinc-300 px-3 py-3 text-xs font-medium text-muted-foreground transition-colors hover:border-zinc-400 hover:bg-zinc-50 hover:text-foreground dark:border-zinc-700 dark:hover:border-zinc-600 dark:hover:bg-zinc-800/50"
          >
            +{remaining} {remaining === 1 ? "altro" : "altri"}
            <ChevronDown className="h-3 w-3" />
          </button>
        )}
      </div>
    </div>
  );
}

// ── Single Alert Card ──

function AlertCard({ item, onAction }: { item: AlertItem; onAction?: () => void }) {
  const styles = SEVERITY_STYLES[item.severity] ?? SEVERITY_STYLES.warning;
  const Icon = ALERT_ICON[item.category] ?? AlertCircle;

  const content = (
    <div className={`flex items-center gap-3 rounded-xl border-l-[3px] ${styles.accent} ${styles.bg} px-3.5 py-3 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md`}>
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${styles.iconBg}`}>
        <Icon className={`h-4 w-4 ${styles.icon}`} />
      </div>
      <div className="min-w-0 flex-1">
        <p className={`text-sm font-semibold leading-tight ${styles.text}`}>
          {item.title}
        </p>
        <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
          {item.detail}
        </p>
      </div>
      {item.count > 1 && (
        <Badge variant="secondary" className="h-5 shrink-0 px-1.5 py-0 text-[10px] font-bold tabular-nums">
          {item.count}
        </Badge>
      )}
      <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/40" />
    </div>
  );

  if (onAction) {
    return (
      <button type="button" onClick={onAction} className="w-full text-left">
        {content}
      </button>
    );
  }

  if (item.link) {
    return (
      <Link href={item.link} className="w-full">
        {content}
      </Link>
    );
  }

  return <div className="w-full">{content}</div>;
}

// ── Skeleton ──

function AlertHubSkeleton() {
  return (
    <div className="rounded-2xl border p-4 sm:p-5">
      <div className="mb-3 flex items-center gap-2.5">
        <Skeleton className="h-8 w-8 rounded-lg" />
        <div className="space-y-1">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-2.5 w-24" />
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <Skeleton className="h-[60px] rounded-xl" />
        <Skeleton className="h-[60px] rounded-xl" />
      </div>
    </div>
  );
}
