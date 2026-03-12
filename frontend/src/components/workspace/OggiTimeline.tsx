"use client";

import { CalendarClock, Clock3 } from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import {
  surfaceChipClassName,
  surfaceRoleClassName,
  type SurfaceTone,
} from "@/components/ui/surface-role";
import { cn } from "@/lib/utils";
import type { SessionPrepItem } from "@/types/api";

export type PreFlightStatus = "ready" | "incomplete" | "risk" | "blocked" | "no_client";

export const PREFLIGHT_META: Record<
  PreFlightStatus,
  {
    label: string;
    color: string;
    bg: string;
    dot: string;
    glow: string;
  }
> = {
  ready: {
    label: "Pronta",
    color: "text-emerald-700 dark:text-emerald-300",
    bg: "bg-emerald-500/10",
    dot: "bg-emerald-500",
    glow: "oggi-glow-teal",
  },
  incomplete: {
    label: "Incompleta",
    color: "text-amber-700 dark:text-amber-300",
    bg: "bg-amber-500/10",
    dot: "bg-amber-500",
    glow: "oggi-glow-amber",
  },
  risk: {
    label: "Rischio",
    color: "text-red-700 dark:text-red-300",
    bg: "bg-red-500/10",
    dot: "bg-red-500",
    glow: "oggi-glow-red",
  },
  blocked: {
    label: "Bloccata",
    color: "text-red-800 dark:text-red-200",
    bg: "bg-red-500/15",
    dot: "bg-red-600",
    glow: "oggi-glow-red",
  },
  no_client: {
    label: "Interna",
    color: "text-stone-500 dark:text-zinc-400",
    bg: "bg-stone-200/70 dark:bg-zinc-800/70",
    dot: "bg-stone-300 dark:bg-zinc-600",
    glow: "oggi-glow-neutral",
  },
};

const TIME_FMT = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });

function getPreflightTone(status: PreFlightStatus): SurfaceTone {
  if (status === "ready") return "teal";
  if (status === "incomplete") return "amber";
  if (status === "risk" || status === "blocked") return "red";
  return "neutral";
}

export function getPreFlightStatus(session: SessionPrepItem): PreFlightStatus {
  if (!session.client_id) return "no_client";
  if (session.contract_credits_remaining !== null && session.contract_credits_remaining <= 0) return "blocked";
  if (session.clinical_alerts.length > 0) return "risk";
  if (session.health_checks.some((check) => check.status !== "ok")) return "incomplete";
  return "ready";
}

function buildSessionSummary(session: SessionPrepItem, status: PreFlightStatus): string {
  if (!session.client_id) {
    return session.event_notes?.trim() || "Impegno interno senza scheda pre-seduta.";
  }

  const parts: string[] = [];
  const reviewChecks = session.health_checks.filter((check) => check.status !== "ok");

  if (session.is_new_client) parts.push("nuovo cliente");
  if (session.clinical_alerts.length > 0) {
    parts.push(
      `${session.clinical_alerts.length} ${session.clinical_alerts.length === 1 ? "alert clinico" : "alert clinici"}`,
    );
  }
  if (reviewChecks.length > 0) {
    parts.push(
      `${reviewChecks.length} ${reviewChecks.length === 1 ? "controllo da rivedere" : "controlli da rivedere"}`,
    );
  }
  if (session.contract_credits_remaining !== null) {
    if (session.contract_credits_remaining <= 0) {
      parts.push("crediti esauriti");
    } else if (session.contract_credits_remaining <= 2) {
      parts.push(`${session.contract_credits_remaining} crediti residui`);
    }
  }
  if (!session.active_plan_name && status !== "blocked") {
    parts.push("programma da verificare");
  }

  if (parts.length === 0 && session.active_plan_name) {
    parts.push(session.active_plan_name);
  }

  if (parts.length === 0 && session.days_since_last_session !== null) {
    parts.push(
      session.days_since_last_session === 0
        ? "allenato oggi"
        : session.days_since_last_session === 1
          ? "ultimo allenamento ieri"
          : `ultimo allenamento ${session.days_since_last_session}g fa`,
    );
  }

  if (parts.length === 0) return "Seduta pronta, nessuna criticita' visibile.";
  return parts.slice(0, 3).join(" | ");
}

function buildGroupLabel(sessions: SessionPrepItem[]): {
  attention: SessionPrepItem[];
  prepared: SessionPrepItem[];
  internal: SessionPrepItem[];
} {
  return sessions.reduce(
    (acc, session) => {
      const status = getPreFlightStatus(session);
      if (!session.client_id) {
        acc.internal.push(session);
      } else if (status === "blocked" || status === "risk" || status === "incomplete") {
        acc.attention.push(session);
      } else {
        acc.prepared.push(session);
      }
      return acc;
    },
    {
      attention: [] as SessionPrepItem[],
      prepared: [] as SessionPrepItem[],
      internal: [] as SessionPrepItem[],
    },
  );
}

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
  const label = session.client_name ?? session.event_title ?? session.category;
  const summary = buildSessionSummary(session, status);

  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "oggi-lift oggi-timeline-row group flex w-full items-start gap-3 rounded-[22px] px-3.5 py-3 text-left transition-all",
        selected && ["oggi-timeline-row-selected", meta.glow],
      )}
    >
      <div className="w-[3.75rem] shrink-0">
        <p className="text-[14px] font-extrabold tabular-nums tracking-tight text-stone-800 dark:text-zinc-100">
          {TIME_FMT.format(new Date(session.starts_at))}
        </p>
        <p className="mt-1 text-[10px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
          {session.category}
        </p>
      </div>

      <span className={cn("mt-1 h-2.5 w-2.5 shrink-0 rounded-full", meta.dot)} />

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p
            className={cn(
              "truncate text-[13px] font-bold tracking-tight",
              session.client_id
                ? "text-stone-900 dark:text-zinc-50"
                : "text-stone-600 dark:text-zinc-300",
            )}
          >
            {label}
          </p>
          {session.is_new_client && (
            <span
              className={surfaceChipClassName(
                { tone: "teal" },
                "px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.14em]",
              )}
            >
              nuovo
            </span>
          )}
        </div>

        <p className="mt-1 text-[11px] leading-5 text-stone-500 dark:text-zinc-400">
          {summary}
        </p>
      </div>

      <span
        className={cn(
          surfaceChipClassName(
            { tone: getPreflightTone(status) },
            "shrink-0 text-[9px] font-bold uppercase tracking-[0.12em]",
          ),
        )}
      >
        {meta.label}
      </span>
    </button>
  );
}

function SessionGroup({
  title,
  count,
  sessions,
  selectedEventId,
  onSelect,
}: {
  title: string;
  count: number;
  sessions: SessionPrepItem[];
  selectedEventId: number | null;
  onSelect: (eventId: number) => void;
}) {
  if (sessions.length === 0) return null;

  return (
    <section className="space-y-2">
      <div className="flex items-center justify-between px-1">
        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
          {title}
        </p>
        <span className="text-[10px] font-semibold tabular-nums text-stone-400 dark:text-zinc-500">
          {count}
        </span>
      </div>
      <div className="space-y-2">
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
    </section>
  );
}

interface OggiTimelineProps {
  sessions: SessionPrepItem[];
  selectedEventId: number | null;
  onSelect: (eventId: number) => void;
  className?: string;
}

export function OggiTimeline({
  sessions,
  selectedEventId,
  onSelect,
  className,
}: OggiTimelineProps) {
  if (sessions.length === 0) {
    return (
      <div
        className={surfaceRoleClassName(
          { role: "page", tone: "neutral" },
          cn("flex flex-col items-center justify-center p-10 text-center", className),
        )}
      >
        <CalendarClock className="h-8 w-8 text-stone-300 dark:text-zinc-600" />
        <p className="mt-3 text-sm font-bold text-stone-500 dark:text-zinc-400">
          Nessuna seduta in agenda oggi
        </p>
        <p className="mt-1 text-[11px] text-stone-400 dark:text-zinc-500">
          La pagina resta pronta per eventuali impegni o follow-up successivi.
        </p>
      </div>
    );
  }

  const groups = buildGroupLabel(sessions);
  const clientCount = sessions.filter((session) => Boolean(session.client_id)).length;

  return (
    <div
      className={surfaceRoleClassName(
        { role: "page", tone: "neutral" },
        cn("flex flex-col overflow-hidden", className),
      )}
    >
      <div className="oggi-timeline-header flex items-center justify-between gap-3 px-4 py-3.5 sm:px-5">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
            <Clock3 className="h-3.5 w-3.5" />
            Sedute di oggi
          </p>
          <p className="mt-1 text-[11px] leading-5 text-stone-600 dark:text-zinc-300">
            Parti dalle sedute che richiedono attenzione, poi scorri la giornata con contesto gia&apos; leggibile.
          </p>
        </div>
        <div className="text-right">
          <p className="text-[22px] font-extrabold tabular-nums tracking-tight text-stone-900 dark:text-zinc-50">
            {clientCount}
          </p>
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-400 dark:text-zinc-500">
            clienti
          </p>
        </div>
      </div>

      <ScrollArea className="min-h-0 flex-1">
        <div className="space-y-4 p-3 sm:p-3.5">
          <SessionGroup
            title="Richiedono attenzione"
            count={groups.attention.length}
            sessions={groups.attention}
            selectedEventId={selectedEventId}
            onSelect={onSelect}
          />
          <SessionGroup
            title="Pronte o in linea"
            count={groups.prepared.length}
            sessions={groups.prepared}
            selectedEventId={selectedEventId}
            onSelect={onSelect}
          />
          <SessionGroup
            title="Altri impegni"
            count={groups.internal.length}
            sessions={groups.internal}
            selectedEventId={selectedEventId}
            onSelect={onSelect}
          />
        </div>
      </ScrollArea>
    </div>
  );
}
