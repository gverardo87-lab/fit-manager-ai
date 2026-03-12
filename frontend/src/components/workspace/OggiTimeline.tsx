"use client";

import { CalendarClock, Clock3 } from "lucide-react";

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
    dot: string;
  }
> = {
  ready: {
    label: "Pronta",
    color: "text-emerald-700 dark:text-emerald-300",
    dot: "bg-emerald-500",
  },
  incomplete: {
    label: "Incompleta",
    color: "text-amber-700 dark:text-amber-300",
    dot: "bg-amber-500",
  },
  risk: {
    label: "Rischio",
    color: "text-red-700 dark:text-red-300",
    dot: "bg-red-500",
  },
  blocked: {
    label: "Bloccata",
    color: "text-red-800 dark:text-red-200",
    dot: "bg-red-600",
  },
  no_client: {
    label: "Interna",
    color: "text-stone-500 dark:text-zinc-400",
    dot: "bg-stone-300 dark:bg-zinc-600",
  },
};

const TIME_FMT = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });

const FLOW_GROUP_META: Record<
  "attention" | "prepared" | "internal",
  {
    title: string;
    description: string;
    tone: SurfaceTone;
    titleColor: string;
  }
> = {
  attention: {
    title: "Da sbloccare",
    description: "Le sedute che possono cambiare davvero il lavoro in sala.",
    tone: "red",
    titleColor: "text-red-700 dark:text-red-400",
  },
  prepared: {
    title: "In linea",
    description: "Sedute gia' pronte o da confermare senza attrito.",
    tone: "teal",
    titleColor: "text-emerald-700 dark:text-emerald-400",
  },
  internal: {
    title: "Altri slot",
    description: "Impegni interni o senza scheda cliente.",
    tone: "neutral",
    titleColor: "text-stone-500 dark:text-zinc-400",
  },
};

function getPreflightTone(status: PreFlightStatus): SurfaceTone {
  if (status === "ready") return "teal";
  if (status === "incomplete") return "amber";
  if (status === "risk" || status === "blocked") return "red";
  return "neutral";
}

function getToneMarkerClass(tone: SurfaceTone): string {
  if (tone === "teal") return "bg-emerald-500";
  if (tone === "amber") return "bg-amber-500";
  if (tone === "red") return "bg-red-500";
  return "bg-stone-300 dark:bg-zinc-600";
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

function buildGroups(sessions: SessionPrepItem[]): {
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

function SessionCard({
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
  const tone = getPreflightTone(status);

  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        surfaceRoleClassName(
          {
            role: "signal",
            tone: selected ? tone : "neutral",
            interactive: true,
          },
          "oggi-rail-card w-full px-0 py-0 text-left",
        ),
        selected && "oggi-rail-card-selected",
        selected && `oggi-glow-${tone}`,
      )}
    >
      <span
        className={cn(
          "absolute inset-y-3 left-0 w-1 rounded-r-full",
          meta.dot,
          selected ? "opacity-100" : "opacity-75",
        )}
      />

      <div className="grid gap-2.5 px-3 py-3 sm:grid-cols-[72px_minmax(0,1fr)_auto] sm:items-start">
        <div className="flex items-center gap-2 sm:flex-col sm:items-start sm:gap-0.5">
          <span
            className={surfaceChipClassName(
              { tone: selected ? tone : "neutral" },
              "px-2.5 py-1 text-[10px] font-bold tabular-nums",
            )}
          >
            {TIME_FMT.format(new Date(session.starts_at))}
          </span>
          <span className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
            <span className={cn("h-2 w-2 rounded-full", meta.dot)} />
            {session.category}
          </span>
        </div>

        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p
              className={cn(
                "text-[14px] font-bold tracking-tight",
                session.client_id
                  ? "text-stone-900 dark:text-zinc-50"
                  : "text-stone-700 dark:text-zinc-200",
              )}
            >
              {label}
            </p>
            {session.is_new_client && (
              <span
                className={surfaceChipClassName(
                  { tone: "teal" },
                  "px-2 py-0.5 text-[8px] font-bold uppercase tracking-[0.14em]",
                )}
              >
                nuovo
              </span>
            )}
          </div>
          <p className="mt-1 text-[10.5px] leading-5 text-stone-500 dark:text-zinc-400">
            {summary}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:flex-col sm:items-end">
          <span
            className={cn(
              surfaceChipClassName(
                { tone: selected ? tone : "neutral" },
                "text-[8.5px] font-bold uppercase tracking-[0.14em]",
              ),
              selected && meta.color,
            )}
          >
            {selected ? "In focus" : meta.label}
          </span>
        </div>
      </div>
    </button>
  );
}

function SessionGroup({
  group,
  sessions,
  selectedEventId,
  onSelect,
}: {
  group: "attention" | "prepared" | "internal";
  sessions: SessionPrepItem[];
  selectedEventId: number | null;
  onSelect: (eventId: number) => void;
}) {
  const meta = FLOW_GROUP_META[group];
  const toneMarkerClass = getToneMarkerClass(meta.tone);

  return (
    <section className="space-y-2">
      <div className="flex items-start gap-3">
        <span className={cn("mt-1 h-2.5 w-2.5 shrink-0 rounded-full", toneMarkerClass)} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <p className={cn("text-[10px] font-bold uppercase tracking-[0.18em]", meta.titleColor)}>
              {meta.title}
            </p>
            <p className="text-[11px] text-stone-500 dark:text-zinc-400">
              {meta.description}
            </p>
          </div>
        </div>
        <span
          className={surfaceChipClassName(
            { tone: meta.tone },
            "px-2.5 py-1 text-[9px] font-bold tabular-nums",
          )}
        >
          {sessions.length}
        </span>
      </div>

      {sessions.length > 0 ? (
        <div className="oggi-rail-group space-y-2 pl-4 sm:pl-5">
          {sessions.map((session) => (
            <SessionCard
              key={session.event_id}
              session={session}
              status={getPreFlightStatus(session)}
              selected={session.event_id === selectedEventId}
              onSelect={() => onSelect(session.event_id)}
            />
          ))}
        </div>
      ) : (
        <div className="ml-4 rounded-[20px] border border-dashed border-stone-200/80 bg-stone-50/70 px-3.5 py-2.5 text-[11px] font-medium text-stone-500 dark:border-zinc-800 dark:bg-zinc-950/40 dark:text-zinc-400">
          Nessuna seduta in questa fascia.
        </div>
      )}
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
          cn("flex flex-col items-center justify-center p-8 text-center", className),
        )}
      >
        <CalendarClock className="h-7 w-7 text-stone-300 dark:text-zinc-600" />
        <p className="mt-2.5 text-[13px] font-bold text-stone-500 dark:text-zinc-400">
          Nessuna seduta in agenda oggi
        </p>
        <p className="mt-1 text-[10px] leading-5 text-stone-400 dark:text-zinc-500">
          La giornata resta libera: usa l&apos;agenda solo per eventuali impegni interni o follow-up.
        </p>
      </div>
    );
  }

  const groups = buildGroups(sessions);
  const clientCount = sessions.filter((session) => Boolean(session.client_id)).length;

  return (
    <div
      className={surfaceRoleClassName(
        { role: "page", tone: "neutral" },
        cn("oggi-rail-shell h-full px-4 py-4 sm:px-5 sm:py-5", className),
      )}
    >
      <div className="space-y-3">
        <div className="flex flex-col gap-2.5 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0">
            <p className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
              <Clock3 className="h-3 w-3" />
              Timeline sedute
            </p>
            <h2 className="mt-1 text-[1rem] font-black tracking-tight text-stone-900 dark:text-zinc-50">
              Flusso operativo della giornata
            </h2>
            <p className="mt-0.5 text-[10.5px] leading-5 text-stone-500 dark:text-zinc-400">
              Leggi prima cosa sbloccare, poi cosa resta in linea.
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <span
              className={surfaceChipClassName(
                { tone: "neutral" },
                "px-2.5 py-1 text-[9px] font-bold tabular-nums",
              )}
            >
              {clientCount} clienti
            </span>
            <span
              className={surfaceChipClassName(
                { tone: "red" },
                "px-2.5 py-1 text-[9px] font-bold tabular-nums",
              )}
            >
              {groups.attention.length} attenzione
            </span>
            <span
              className={surfaceChipClassName(
                { tone: "teal" },
                "px-2.5 py-1 text-[9px] font-bold tabular-nums",
              )}
            >
              {groups.prepared.length} in linea
            </span>
          </div>
        </div>

        <div className="space-y-3">
          <SessionGroup
            group="attention"
            sessions={groups.attention}
            selectedEventId={selectedEventId}
            onSelect={onSelect}
          />
          <SessionGroup
            group="prepared"
            sessions={groups.prepared}
            selectedEventId={selectedEventId}
            onSelect={onSelect}
          />
          {groups.internal.length > 0 && (
            <SessionGroup
              group="internal"
              sessions={groups.internal}
              selectedEventId={selectedEventId}
              onSelect={onSelect}
            />
          )}
        </div>
      </div>
    </div>
  );
}
