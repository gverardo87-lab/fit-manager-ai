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

const LED_STYLE: Record<LedColor, { bg: string; glow: string }> = {
  green: { bg: "bg-emerald-500", glow: "oklch(0.62 0.15 150 / 0.40)" },
  amber: { bg: "bg-amber-500",   glow: "oklch(0.75 0.12 70 / 0.40)" },
  red:   { bg: "bg-red-500",     glow: "oklch(0.55 0.15 25 / 0.40)" },
  gray:  { bg: "bg-stone-300 dark:bg-zinc-600", glow: "none" },
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
  const style = LED_STYLE[color];
  return (
    <div className="group/led relative">
      <div
        className={cn("h-[6px] w-[6px] rounded-full", style.bg)}
        style={style.glow !== "none" ? { boxShadow: `0 0 6px ${style.glow}` } : undefined}
      />
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
        /* No border — luminosity difference only */
        background: selected
          ? "oklch(0.96 0.015 170 / 0.6)"
          : undefined,
      }}
    >
      {/* Timeline dot */}
      <span
        className={cn("h-2 w-2 shrink-0 rounded-full", meta.dot)}
        style={status === "ready" || status === "risk" || status === "blocked"
          ? { boxShadow: `0 0 5px ${status === "ready" ? "oklch(0.62 0.15 150 / 0.35)" : "oklch(0.55 0.15 25 / 0.35)"}` }
          : undefined}
      />

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

      {/* LEDs — glowing dots */}
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
        className={cn("flex flex-col items-center justify-center rounded-2xl p-10 text-center backdrop-blur-sm", className)}
        style={{
          background: "oklch(0.98 0.003 200 / 0.5)",
        }}
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
      className={cn("oggi-glow-neutral flex flex-col overflow-hidden rounded-2xl backdrop-blur-sm", className)}
      style={{
        /* Glass container — no heavy border, luminosity separation */
        background: "linear-gradient(180deg, oklch(0.99 0.003 200 / 0.7), oklch(0.98 0.002 200 / 0.5))",
        border: "0.5px solid oklch(0.80 0.01 200 / 0.12)",
      }}
    >
      {/* Header */}
      <div
        className="flex items-center gap-2.5 px-4 py-3 backdrop-blur-sm"
        style={{ borderBottom: "0.5px solid oklch(0.80 0.01 200 / 0.08)" }}
      >
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
