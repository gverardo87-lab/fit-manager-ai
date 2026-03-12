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
  }
> = {
  attention: {
    title: "Da sbloccare",
    description: "Sedute che possono cambiare davvero il lavoro in sala.",
    tone: "red",
  },
  prepared: {
    title: "In linea",
    description: "Sedute pronte o da confermare velocemente.",
    tone: "teal",
  },
  internal: {
    title: "Altri slot",
    description: "Impegni interni o senza scheda cliente da tenere in sfondo.",
    tone: "neutral",
  },
};

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

  return (
    <button
      type="button"
      onClick={onSelect}
      className={surfaceRoleClassName(
        {
          role: "signal",
          tone: selected ? getPreflightTone(status) : "neutral",
          interactive: true,
        },
        cn("w-full px-3.5 py-3 text-left", selected && "ring-1 ring-primary/12"),
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span
              className={surfaceChipClassName(
                { tone: "neutral" },
                "px-2 py-0.5 text-[8.5px] font-bold uppercase tracking-[0.14em]",
              )}
            >
              {TIME_FMT.format(new Date(session.starts_at))}
            </span>
            <span className={cn("h-2 w-2 shrink-0 rounded-full", meta.dot)} />
            <span className="text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
              {session.category}
            </span>
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

          <p
            className={cn(
              "mt-2 text-[13px] font-bold tracking-tight",
              session.client_id
                ? "text-stone-900 dark:text-zinc-50"
                : "text-stone-600 dark:text-zinc-300",
            )}
          >
            {label}
          </p>
          <p className="mt-1 text-[10.5px] leading-5 text-stone-500 dark:text-zinc-400">
            {summary}
          </p>
        </div>

        <span
          className={cn(
            surfaceChipClassName(
              { tone: getPreflightTone(status) },
              "shrink-0 text-[8.5px] font-bold uppercase tracking-[0.12em]",
            ),
            meta.color,
          )}
        >
          {selected ? "In focus" : meta.label}
        </span>
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

  return (
    <section
      className={surfaceRoleClassName(
        { role: "context", tone: meta.tone },
        "flex h-full min-h-0 flex-col px-3.5 py-3.5 sm:px-4",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
            {meta.title}
          </p>
          <p className="mt-1 text-[10.5px] leading-5 text-stone-600 dark:text-zinc-300">
            {meta.description}
          </p>
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

      <div className="mt-3 space-y-2.5">
        {sessions.length > 0 ? (
          sessions.map((session) => (
            <SessionCard
              key={session.event_id}
              session={session}
              status={getPreFlightStatus(session)}
              selected={session.event_id === selectedEventId}
              onSelect={() => onSelect(session.event_id)}
            />
          ))
        ) : (
          <div className={surfaceRoleClassName({ role: "signal", tone: "neutral" }, "px-3.5 py-3")}>
            <p className="text-[11px] font-semibold text-stone-500 dark:text-zinc-400">
              Nessuna seduta in questa fascia.
            </p>
          </div>
        )}
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
        cn("px-4 py-4 sm:px-5 sm:py-5", className),
      )}
    >
      <div className="space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-0">
            <p className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
              <Clock3 className="h-3 w-3" />
              Flusso della giornata
            </p>
            <h3 className="mt-1.5 text-[20px] font-extrabold tracking-tight text-stone-900 dark:text-zinc-50">
              Sedute lette come regia, non come elenco
            </h3>
            <p className="mt-1 text-[11px] leading-5 text-stone-600 dark:text-zinc-300">
              Le fasce della giornata restano compatte: scegli il focus attivo, poi scorri il resto senza aprire una cartella dopo l&apos;altra.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className={surfaceChipClassName({ tone: "neutral" }, "px-2.5 py-1 text-[9px] font-bold tabular-nums")}>
              {clientCount} clienti
            </span>
            <span className={surfaceChipClassName({ tone: "red" }, "px-2.5 py-1 text-[9px] font-bold tabular-nums")}>
              {groups.attention.length} attenzione
            </span>
            <span className={surfaceChipClassName({ tone: "teal" }, "px-2.5 py-1 text-[9px] font-bold tabular-nums")}>
              {groups.prepared.length} in linea
            </span>
          </div>
        </div>

        <div className="grid gap-3 xl:grid-cols-[minmax(0,1.08fr)_minmax(0,1.08fr)_minmax(0,0.84fr)]">
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
          <SessionGroup
            group="internal"
            sessions={groups.internal}
            selectedEventId={selectedEventId}
            onSelect={onSelect}
          />
        </div>
      </div>
    </div>
  );
}
