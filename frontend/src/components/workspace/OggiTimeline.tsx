"use client";

import { CalendarClock, Clock } from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { SessionPrepItem } from "@/types/api";

/* ── Pre-Flight Status ── */

export type PreFlightStatus = "ready" | "incomplete" | "risk" | "blocked" | "no_client";

export const PREFLIGHT_META: Record<PreFlightStatus, {
  label: string;
  color: string;
  bg: string;
  dot: string;
  glow: string;
}> = {
  ready:      { label: "Pronta",     color: "text-emerald-700 dark:text-emerald-300", bg: "bg-emerald-500/10", dot: "bg-emerald-500", glow: "oggi-glow-teal" },
  incomplete: { label: "Incompleta", color: "text-amber-700 dark:text-amber-300",     bg: "bg-amber-500/10",   dot: "bg-amber-500",   glow: "oggi-glow-amber" },
  risk:       { label: "Rischio",    color: "text-red-700 dark:text-red-300",         bg: "bg-red-500/10",     dot: "bg-red-500",     glow: "oggi-glow-red" },
  blocked:    { label: "Bloccata",   color: "text-red-800 dark:text-red-200",         bg: "bg-red-500/15",     dot: "bg-red-600",     glow: "oggi-glow-red" },
  no_client:  { label: "",           color: "text-stone-500 dark:text-zinc-400",      bg: "",                  dot: "bg-stone-300 dark:bg-zinc-600", glow: "oggi-glow-neutral" },
};

export function getPreFlightStatus(s: SessionPrepItem): PreFlightStatus {
  if (!s.client_id) return "no_client";
  if (s.contract_credits_remaining !== null && s.contract_credits_remaining <= 0) return "blocked";
  if (s.clinical_alerts.length > 0) return "risk";
  if (s.health_checks.some((c) => c.status !== "ok")) return "incomplete";
  return "ready";
}

/* ── LED indicators ── */

type LedColor = "green" | "amber" | "red" | "gray";

const LED_BG: Record<LedColor, string> = {
  green: "bg-emerald-500",
  amber: "bg-amber-500",
  red: "bg-red-500",
  gray: "bg-stone-300 dark:bg-zinc-600",
};

function getHealthLed(s: SessionPrepItem): LedColor {
  if (!s.client_id || s.health_checks.length === 0) return "gray";
  if (s.health_checks.some((c) => c.status !== "ok" && c.status !== "warning")) return "red";
  if (s.health_checks.some((c) => c.status === "warning")) return "amber";
  return "green";
}

function getContractLed(s: SessionPrepItem): LedColor {
  if (s.contract_credits_remaining === null) return "gray";
  if (s.contract_credits_remaining <= 0) return "red";
  if (s.contract_credits_remaining <= 2) return "amber";
  return "green";
}

function getProgramLed(s: SessionPrepItem): LedColor {
  return s.active_plan_name ? "green" : "gray";
}

function Led({ color, title }: { color: LedColor; title: string }) {
  return (
    <div className="group/led relative">
      <div className={cn("h-[6px] w-[6px] rounded-full", LED_BG[color])} />
      <div className="pointer-events-none absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-stone-900 px-2 py-0.5 text-[9px] font-medium text-white opacity-0 shadow-lg transition-opacity group-hover/led:opacity-100 dark:bg-zinc-100 dark:text-stone-900">
        {title}
      </div>
    </div>
  );
}

/* ── Timeline Row ── */

const TIME_FMT = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });

function TimelineRow({
  session,
  status,
  selected,
  onSelect,
}: {
  session: SessionPrepItem;
  status: PreFlightStatus;
  selected: boolean;
  onSelect: () => void;
}) {
  const meta = PREFLIGHT_META[status];
  const time = TIME_FMT.format(new Date(session.starts_at));
  const name = session.client_name ?? session.event_title ?? session.category;
  const isClient = Boolean(session.client_id);

  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "oggi-lift group flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left transition-all",
        selected && meta.glow,
      )}
      style={{
        border: selected ? "1px solid oklch(0.70 0.12 170 / 0.2)" : "1px solid transparent",
        background: selected
          ? "linear-gradient(135deg, oklch(0.97 0.02 170 / 0.3), oklch(0.99 0.005 170 / 0.15))"
          : undefined,
      }}
    >
      {/* Timeline dot */}
      <span className={cn("h-2 w-2 shrink-0 rounded-full", meta.dot)} />

      {/* Time */}
      <span className="w-11 shrink-0 text-[12px] font-extrabold tabular-nums tracking-tight text-stone-600 dark:text-zinc-400">
        {time}
      </span>

      {/* Name */}
      <span className={cn(
        "min-w-0 flex-1 truncate text-[13px]",
        isClient ? "font-bold text-stone-900 dark:text-zinc-50" : "font-medium text-stone-400 italic dark:text-zinc-500",
      )}>
        {name}
      </span>

      {/* LEDs */}
      {isClient && (
        <div className="flex items-center gap-1.5">
          <Led color={getHealthLed(session)} title="Salute" />
          <Led color={getContractLed(session)} title="Contratto" />
          <Led color={getProgramLed(session)} title="Programma" />
        </div>
      )}

      {/* Pre-flight badge */}
      {status !== "no_client" && (
        <span className={cn(
          "shrink-0 rounded-full px-2 py-0.5 text-[8px] font-bold uppercase tracking-[0.1em]",
          meta.bg, meta.color,
        )}>
          {meta.label}
        </span>
      )}
    </button>
  );
}

/* ── Main Timeline ── */

interface OggiTimelineProps {
  sessions: SessionPrepItem[];
  selectedEventId: number | null;
  onSelect: (eventId: number) => void;
  className?: string;
}

export function OggiTimeline({ sessions, selectedEventId, onSelect, className }: OggiTimelineProps) {
  if (sessions.length === 0) {
    return (
      <div
        className={cn("flex flex-col items-center justify-center rounded-2xl p-10 text-center", className)}
        style={{ border: "1px solid oklch(0.70 0.02 250 / 0.10)" }}
      >
        <CalendarClock className="h-8 w-8 text-stone-200 dark:text-zinc-700" />
        <p className="mt-3 text-sm font-bold text-stone-400 dark:text-zinc-500">Giornata libera</p>
        <p className="mt-1 text-[11px] text-stone-300 dark:text-zinc-600">
          Nessuna sessione in programma
        </p>
      </div>
    );
  }

  return (
    <div
      className={cn("oggi-glow-neutral flex flex-col overflow-hidden rounded-2xl", className)}
      style={{
        border: "1px solid oklch(0.70 0.02 250 / 0.10)",
        background: "linear-gradient(180deg, oklch(0.995 0.003 250 / 0.8), oklch(0.99 0.001 250 / 0.6))",
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-2.5 border-b border-stone-100/80 px-4 py-3 backdrop-blur-sm dark:border-zinc-800/80">
        <Clock className="h-3.5 w-3.5 text-stone-400 dark:text-zinc-500" />
        <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
          Timeline
        </span>
        <span className="text-[10px] tabular-nums text-stone-300 dark:text-zinc-600">
          {sessions.filter((s) => s.client_id).length} clienti
        </span>
      </div>

      {/* Rows */}
      <ScrollArea className="min-h-0 flex-1">
        <div className="space-y-0.5 p-1.5">
          {sessions.map((session) => (
            <TimelineRow
              key={session.event_id}
              session={session}
              status={getPreFlightStatus(session)}
              selected={session.event_id === selectedEventId}
              onSelect={() => onSelect(session.event_id)}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
