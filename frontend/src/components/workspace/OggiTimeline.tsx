"use client";

import { CalendarClock, Clock3 } from "lucide-react";

import {
  surfaceChipClassName,
  surfaceRoleClassName,
  type SurfaceTone,
} from "@/components/ui/surface-role";
import { cn } from "@/lib/utils";
import type { SessionPrepItem } from "@/types/api";

// ── Tipi e metadati stato pre-seduta ──────────────────────────────

export type PreFlightStatus = "ready" | "incomplete" | "risk" | "blocked" | "no_client";

export const PREFLIGHT_META: Record<
  PreFlightStatus,
  { label: string; dot: string; color: string }
> = {
  ready:      { label: "Pronta",     dot: "bg-emerald-500",                    color: "text-emerald-700 dark:text-emerald-300" },
  incomplete: { label: "Incompleta", dot: "bg-amber-500",                     color: "text-amber-700 dark:text-amber-300" },
  risk:       { label: "Rischio",    dot: "bg-red-500",                        color: "text-red-700 dark:text-red-300" },
  blocked:    { label: "Bloccata",   dot: "bg-red-600",                        color: "text-red-800 dark:text-red-200" },
  no_client:  { label: "Interno",    dot: "bg-stone-300 dark:bg-zinc-600",     color: "text-muted-foreground" },
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
  if (session.contract_credits_remaining !== null && session.contract_credits_remaining <= 0)
    return "blocked";
  if (session.clinical_alerts.length > 0) return "risk";
  if (session.health_checks.some((c) => c.status !== "ok")) return "incomplete";
  return "ready";
}

function getSessionSubline(session: SessionPrepItem, status: PreFlightStatus): string {
  if (!session.client_id) return session.event_notes?.trim() || "Impegno interno";
  const issues: string[] = [];
  if (session.clinical_alerts.length > 0)
    issues.push(`${session.clinical_alerts.length} alert ${session.clinical_alerts.length === 1 ? "clinico" : "clinici"}`);
  const bad = session.health_checks.filter((c) => c.status !== "ok");
  if (bad.length > 0) issues.push(`${bad.length} ${bad.length === 1 ? "controllo" : "controlli"}`);
  if (session.contract_credits_remaining !== null && session.contract_credits_remaining <= 0)
    issues.push("crediti esauriti");
  if (issues.length > 0) return issues.join(" · ");
  if (session.active_plan_name) return session.active_plan_name;
  return status === "ready" ? "Seduta pronta" : "Da verificare";
}

// ── Session Card ──────────────────────────────────────────────────

function SessionItem({
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
  const tone = getPreflightTone(status);
  const name = session.client_name ?? session.event_title ?? session.category;
  const subline = getSessionSubline(session, status);

  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "oggi-session-card relative w-full rounded-xl px-3.5 py-3 text-left",
        selected
          ? cn(
              surfaceRoleClassName({ role: "signal", tone, interactive: true }),
              `oggi-glow-${tone}`,
              "oggi-session-card-selected",
            )
          : "border border-transparent hover:border-border/60 hover:bg-accent/40",
      )}
    >
      {/* Barra status sinistra */}
      <span
        className={cn(
          "absolute inset-y-3 left-0 w-[3px] rounded-r-full transition-opacity",
          meta.dot,
          selected ? "opacity-100" : "opacity-30",
        )}
      />

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span
              className={surfaceChipClassName(
                { tone: selected ? tone : "neutral" },
                "shrink-0 px-2 py-0.5 text-[10px] font-bold tabular-nums",
              )}
            >
              {TIME_FMT.format(new Date(session.starts_at))}
            </span>
            <p className="truncate text-[13px] font-bold text-foreground">{name}</p>
          </div>
          <p className="mt-1 truncate pl-1 text-[10.5px] text-muted-foreground">{subline}</p>
        </div>

        <span
          className={cn(
            "shrink-0 text-[9px] font-bold uppercase tracking-[0.12em]",
            selected ? meta.color : "text-muted-foreground/60",
          )}
        >
          {selected ? "Focus" : meta.label}
        </span>
      </div>
    </button>
  );
}

// ── Group Label ───────────────────────────────────────────────────

function GroupLabel({
  label,
  count,
  tone,
}: {
  label: string;
  count: number;
  tone: SurfaceTone;
}) {
  const dotClass =
    tone === "red" ? "bg-red-500" : tone === "teal" ? "bg-emerald-500" : "bg-stone-300 dark:bg-zinc-600";
  const textClass =
    tone === "red"
      ? "text-red-700 dark:text-red-400"
      : tone === "teal"
        ? "text-emerald-700 dark:text-emerald-400"
        : "text-muted-foreground";

  return (
    <div className="flex items-center gap-2 px-1">
      <span className={cn("h-2 w-2 shrink-0 rounded-full", dotClass, tone === "red" && "oggi-status-beat")} />
      <p className={cn("text-[10px] font-bold uppercase tracking-[0.16em]", textClass)}>{label}</p>
      <span
        className={surfaceChipClassName(
          { tone },
          "ml-auto px-2 py-0.5 text-[9px] font-bold tabular-nums",
        )}
      >
        {count}
      </span>
    </div>
  );
}

// ── OggiTimeline ──────────────────────────────────────────────────

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
        <CalendarClock className="h-8 w-8 text-muted-foreground/30" />
        <p className="mt-3 text-[13px] font-semibold text-muted-foreground">
          Nessuna seduta in agenda oggi
        </p>
        <p className="mt-1 text-[11px] text-muted-foreground/60">
          Usa l&apos;agenda per eventuali impegni interni.
        </p>
      </div>
    );
  }

  const attention = sessions.filter((s) => {
    const st = getPreFlightStatus(s);
    return s.client_id && (st === "blocked" || st === "risk" || st === "incomplete");
  });
  const prepared = sessions.filter((s) => s.client_id && getPreFlightStatus(s) === "ready");
  const internal = sessions.filter((s) => !s.client_id);

  return (
    <div
      className={surfaceRoleClassName(
        { role: "page", tone: "neutral" },
        cn("oggi-rail-shell px-4 py-4 sm:px-5 sm:py-5", className),
      )}
    >
      {/* Header */}
      <div className="mb-5 flex items-center gap-2.5">
        <Clock3 className="h-4 w-4 text-muted-foreground/50" />
        <h2 className="text-[14px] font-extrabold tracking-tight text-foreground">Sedute di oggi</h2>
        <span
          className={surfaceChipClassName(
            { tone: "neutral" },
            "ml-auto px-2.5 py-1 text-[9px] font-bold tabular-nums",
          )}
        >
          {sessions.filter((s) => s.client_id).length} clienti
        </span>
      </div>

      {/* Gruppi */}
      <div className="space-y-5">
        {attention.length > 0 && (
          <div className="space-y-1.5">
            <GroupLabel label="Da sbloccare" count={attention.length} tone="red" />
            <div className="space-y-1.5">
              {attention.map((s) => (
                <SessionItem
                  key={s.event_id}
                  session={s}
                  status={getPreFlightStatus(s)}
                  selected={s.event_id === selectedEventId}
                  onSelect={() => onSelect(s.event_id)}
                />
              ))}
            </div>
          </div>
        )}

        {prepared.length > 0 && (
          <div className="space-y-1.5">
            <GroupLabel label="In linea" count={prepared.length} tone="teal" />
            <div className="space-y-1.5">
              {prepared.map((s) => (
                <SessionItem
                  key={s.event_id}
                  session={s}
                  status={getPreFlightStatus(s)}
                  selected={s.event_id === selectedEventId}
                  onSelect={() => onSelect(s.event_id)}
                />
              ))}
            </div>
          </div>
        )}

        {internal.length > 0 && (
          <div className="space-y-1.5">
            <GroupLabel label="Interni" count={internal.length} tone="neutral" />
            <div className="space-y-1.5">
              {internal.map((s) => (
                <SessionItem
                  key={s.event_id}
                  session={s}
                  status="no_client"
                  selected={s.event_id === selectedEventId}
                  onSelect={() => onSelect(s.event_id)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
