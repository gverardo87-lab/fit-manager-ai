"use client";

import type { PreFlightStatus } from "@/components/workspace/OggiTimeline";
import {
  surfaceChipClassName,
  surfaceRoleClassName,
  type SurfaceTone,
} from "@/components/ui/surface-role";
import { cn } from "@/lib/utils";
import { getGreeting } from "@/lib/dashboard-helpers";
import { AnalogClock } from "@/components/workspace/AnalogClock";
import type { SessionPrepItem, SessionPrepResponse } from "@/types/api";

const TIME_FMT = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });
const DATE_FMT = new Intl.DateTimeFormat("it-IT", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

function getReferenceDate(value: string | number | Date | null | undefined): Date {
  const nextDate = value ? new Date(value) : new Date();
  return Number.isNaN(nextDate.getTime()) ? new Date() : nextDate;
}

function getSessionTimeLabel(startsAt: string): string {
  return TIME_FMT.format(getReferenceDate(startsAt));
}

function getFocusBrief({
  prep,
  focusSession,
  focusStatus,
}: {
  prep: SessionPrepResponse;
  focusSession: SessionPrepItem | null;
  focusStatus: PreFlightStatus | null;
}): { tone: SurfaceTone; lead: string; detail: string | null } {
  if (!focusSession) {
    if (prep.total_sessions > 0) {
      return {
        tone: "neutral",
        lead: "Seleziona una seduta per aprire il focus operativo",
        detail: "La timeline resta il punto di ingresso per preparazione e verifiche pre-seduta.",
      };
    }
    if (prep.non_client_events.length > 0) {
      return {
        tone: "neutral",
        lead: "Nessuna seduta PT da preparare oggi",
        detail:
          prep.non_client_events.length === 1
            ? "Resta un solo slot interno in agenda."
            : `Restano ${prep.non_client_events.length} slot interni in agenda.`,
      };
    }
    return {
      tone: "neutral",
      lead: "Nessuna seduta PT in agenda oggi",
      detail: "Il workspace resta libero per pianificazione, follow-up o attivita' interne.",
    };
  }

  const timeLabel = getSessionTimeLabel(focusSession.starts_at);

  if (!focusSession.client_id) {
    return {
      tone: "neutral",
      lead: `Focus interno alle ${timeLabel}`,
      detail:
        focusSession.event_title ??
        focusSession.event_notes?.trim() ??
        "Impegno interno in agenda.",
    };
  }

  const name = focusSession.client_name ?? "Seduta cliente";

  if (focusStatus === "blocked") {
    return {
      tone: "red",
      lead: `${name} alle ${timeLabel}: sblocco contrattuale richiesto`,
      detail: "I crediti risultano esauriti: chiarisci il contratto prima della seduta.",
    };
  }

  if (focusStatus === "risk") {
    return {
      tone: "red",
      lead: `${name} alle ${timeLabel}: verifica clinica prima della seduta`,
      detail:
        focusSession.clinical_alerts.length === 1
          ? "E' presente un alert clinico da controllare."
          : `Sono presenti ${focusSession.clinical_alerts.length} alert clinici da controllare.`,
    };
  }

  if (focusStatus === "incomplete") {
    const pendingChecks = focusSession.health_checks.filter((check) => check.status !== "ok").length;
    return {
      tone: "amber",
      lead: `${name} alle ${timeLabel}: check pre-seduta da completare`,
      detail:
        pendingChecks === 1
          ? "Resta un controllo aperto prima della seduta."
          : `Restano ${pendingChecks} controlli aperti prima della seduta.`,
    };
  }

  if (focusStatus === "ready") {
    return {
      tone: "teal",
      lead: `${name} alle ${timeLabel} e' pronto`,
      detail: focusSession.active_plan_name
        ? `Scheda attiva: ${focusSession.active_plan_name}.`
        : "Nessun blocco immediato rilevato per la seduta.",
    };
  }

  return {
    tone: "neutral",
    lead: `${name} alle ${timeLabel}`,
    detail: "Focus aperto sulla seduta selezionata.",
  };
}

export interface OggiHeroProps {
  prep: SessionPrepResponse;
  attentionCount: number;
  readyCount: number;
  internalCount: number;
  focusSession: SessionPrepItem | null;
  focusStatus: PreFlightStatus | null;
  lastUpdatedAt?: number | null;
  isRefreshing?: boolean;
  className?: string;
}

export function OggiHero({
  prep,
  attentionCount,
  readyCount,
  internalCount,
  focusSession,
  focusStatus,
  lastUpdatedAt,
  isRefreshing = false,
  className,
}: OggiHeroProps) {
  const now = getReferenceDate(prep.current_time);
  const { tone, lead, detail } = getFocusBrief({
    prep,
    focusSession,
    focusStatus,
  });
  const syncLabel = lastUpdatedAt ? TIME_FMT.format(getReferenceDate(lastUpdatedAt)) : null;

  const leadColor =
    tone === "red"
      ? "text-red-700 dark:text-red-300"
      : tone === "amber"
        ? "text-amber-700 dark:text-amber-300"
        : tone === "teal"
          ? "text-emerald-700 dark:text-emerald-300"
          : "text-foreground";

  return (
    <section className={cn("oggi-hero-mesh", className)}>
      <div
        className={surfaceRoleClassName(
          { role: "page", tone: "neutral" },
          "oggi-command-bar px-6 py-7 sm:px-8 sm:py-8",
        )}
      >
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0 flex-1">
            <p className="flex items-center gap-2.5 text-[10px] font-bold uppercase tracking-[0.22em] text-muted-foreground/70">
              <span>{DATE_FMT.format(now)}</span>
              <span className="h-0.5 w-3 rounded-full bg-current opacity-20" />
              <span>preparazione sedute</span>
            </p>
            <div className="mt-3 flex items-center gap-5">
              <h1 className="oggi-title-gradient text-[2.6rem] font-black leading-tight tracking-tighter sm:text-[3rem]">
                Oggi
              </h1>
              <AnalogClock className="h-[76px] w-[76px] shrink-0 sm:h-[92px] sm:w-[92px]" />
            </div>
            <p className="mt-3 text-[15px] font-semibold text-primary/90">
              {getGreeting()}, Dott.ssa Chiara Bassani
            </p>
            <div className="oggi-hero-divider mt-4" />
            <p className={cn("mt-4 text-[14.5px] font-semibold leading-snug transition-colors duration-300 sm:text-[15.5px]", leadColor)}>
              {lead}
            </p>
            {detail && (
              <p className="mt-2 max-w-lg text-[11.5px] leading-[1.65] text-muted-foreground/65">
                {detail}
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2 sm:flex-col sm:items-end sm:gap-2.5">
            <span
              className={surfaceChipClassName(
                { tone: "neutral" },
                "px-3.5 py-1.5 text-[11px] font-bold tabular-nums",
              )}
            >
              {prep.total_sessions} {prep.total_sessions === 1 ? "seduta" : "sedute"}
            </span>

            {attentionCount > 0 && (
              <span
                className={surfaceChipClassName(
                  { tone: "red" },
                  "px-3.5 py-1.5 text-[11px] font-bold tabular-nums",
                )}
              >
                {attentionCount} da verificare
              </span>
            )}

            {attentionCount === 0 && readyCount > 0 && (
              <span
                className={surfaceChipClassName(
                  { tone: "teal" },
                  "px-3.5 py-1.5 text-[11px] font-bold tabular-nums",
                )}
              >
                {readyCount} {readyCount === 1 ? "pronta" : "pronte"}
              </span>
            )}

            {internalCount > 0 && (
              <span
                className={surfaceChipClassName(
                  { tone: "neutral" },
                  "px-3.5 py-1.5 text-[11px] font-bold tabular-nums",
                )}
              >
                {internalCount} {internalCount === 1 ? "interno" : "interni"}
              </span>
            )}

            {syncLabel && (
              <span
                className={surfaceChipClassName(
                  { tone: isRefreshing ? "amber" : "neutral" },
                  "px-3 py-1.5 text-[10px] font-bold transition-colors duration-300",
                )}
              >
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full transition-colors duration-300",
                    isRefreshing ? "oggi-pulse-dot bg-amber-500" : "bg-emerald-500",
                  )}
                />
                {isRefreshing ? "Sync" : `Agg. ${syncLabel}`}
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
        cn("oggi-command-bar px-6 py-7 sm:px-8 sm:py-8", className),
      )}
    >
      <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1 space-y-3">
          <div className="h-3 w-44 rounded bg-muted/50" />
          <div className="flex items-center gap-5">
            <div className="h-12 w-28 rounded-xl bg-muted/30" />
            <div className="h-[76px] w-[76px] rounded-full bg-muted/20 sm:h-[92px] sm:w-[92px]" />
          </div>
          <div className="h-4 w-60 rounded bg-muted/40" />
          <div className="h-[1.5px] w-12 rounded bg-muted/30" />
          <div className="h-4 w-72 rounded bg-muted/35" />
          <div className="h-3 w-56 rounded bg-muted/25" />
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:flex-col sm:items-end sm:gap-2.5">
          <div className="h-7 w-20 rounded-full bg-muted/35" />
          <div className="h-7 w-24 rounded-full bg-muted/30" />
          <div className="h-6 w-16 rounded-full bg-muted/25" />
        </div>
      </div>
    </div>
  );
}
