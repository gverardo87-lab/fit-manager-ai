"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  CreditCard,
  FileText,
  HeartPulse,
  ShieldAlert,
  TrendingUp,
  XCircle,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { appendFromParam } from "@/lib/url-state";
import type { SessionPrepItem } from "@/types/api";
import type { PreFlightStatus } from "@/components/workspace/OggiTimeline";
import { PREFLIGHT_META } from "@/components/workspace/OggiTimeline";

/* ── Notes persistence (localStorage) ── */

const NOTES_KEY = "fitmanager.oggi.notes";

function loadNote(eventId: number): string {
  try {
    const data = JSON.parse(localStorage.getItem(NOTES_KEY) ?? "{}");
    return (data[String(eventId)] as string) ?? "";
  } catch { return ""; }
}

function saveNote(eventId: number, text: string) {
  try {
    const data = JSON.parse(localStorage.getItem(NOTES_KEY) ?? "{}");
    if (text.trim()) data[String(eventId)] = text;
    else delete data[String(eventId)];
    localStorage.setItem(NOTES_KEY, JSON.stringify(data));
  } catch { /* noop */ }
}

/* ── Glass Quadrant shell ── */

function Quadrant({
  icon: Icon,
  title,
  accent,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  accent?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="flex flex-col rounded-xl p-4 backdrop-blur-sm"
      style={{
        border: `1px solid oklch(0.70 0.02 250 / 0.08)`,
        background: accent
          ? `linear-gradient(145deg, oklch(0.97 0.01 ${accent} / 0.3), oklch(0.995 0.003 250 / 0.5))`
          : "linear-gradient(145deg, oklch(0.995 0.003 250 / 0.7), oklch(0.99 0.001 250 / 0.5))",
      }}
    >
      <div className="mb-3 flex items-center gap-2">
        <Icon className="h-3.5 w-3.5 text-stone-400 dark:text-zinc-500" />
        <span className="text-[9px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
          {title}
        </span>
      </div>
      {children}
    </div>
  );
}

/* ── Main Command Center ── */

interface OggiCommandCenterProps {
  session: SessionPrepItem | null;
  status: PreFlightStatus;
  className?: string;
}

export function OggiCommandCenter({ session, status, className }: OggiCommandCenterProps) {
  const [note, setNote] = useState("");

  useEffect(() => {
    if (session?.event_id) setNote(loadNote(session.event_id));
    else setNote("");
  }, [session?.event_id]);

  const handleNote = useCallback((text: string) => {
    setNote(text);
    if (session?.event_id) saveNote(session.event_id, text);
  }, [session?.event_id]);

  /* Empty state */
  if (!session) {
    return (
      <div
        className={cn("flex items-center justify-center rounded-2xl p-16 text-center", className)}
        style={{ border: "1px solid oklch(0.70 0.02 250 / 0.10)" }}
      >
        <div>
          <HeartPulse className="mx-auto h-10 w-10 text-stone-200 dark:text-zinc-700" />
          <p className="mt-4 text-sm font-bold text-stone-400 dark:text-zinc-500">
            Seleziona una sessione
          </p>
          <p className="mt-1 text-[11px] text-stone-300 dark:text-zinc-600">
            Il Command Center si attiverà
          </p>
        </div>
      </div>
    );
  }

  /* Non-client event */
  if (!session.client_id) {
    return (
      <div
        className={cn("flex items-center justify-center rounded-2xl p-16 text-center", className)}
        style={{ border: "1px solid oklch(0.70 0.02 250 / 0.10)" }}
      >
        <div>
          <p className="text-xl font-extrabold tracking-tight text-stone-800 dark:text-zinc-100">
            {session.event_title ?? session.category}
          </p>
          <p className="mt-2 text-[12px] text-stone-400 dark:text-zinc-500">
            Evento senza cliente associato
          </p>
        </div>
      </div>
    );
  }

  const meta = PREFLIGHT_META[status];
  const alertCount = session.clinical_alerts.length;
  const readiness = session.readiness_score;

  return (
    <div className={cn("space-y-3", className)}>
      {/* Session header with pre-flight badge */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-extrabold tracking-tight text-stone-900 dark:text-zinc-50">
          {session.client_name}
        </h2>
        {status !== "no_client" && (
          <span className={cn("rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-wider", meta.bg, meta.color)}>
            {meta.label}
          </span>
        )}
      </div>

      {/* 4 Quadrants — Bento Grid */}
      <div className="grid gap-3 sm:grid-cols-2">
        {/* A. Clinical Readiness */}
        <Quadrant icon={ShieldAlert} title="Readiness Clinica" accent={alertCount > 0 ? "25" : "170"}>
          <div className="flex items-start gap-4">
            {readiness !== null && (
              <div className="shrink-0 text-center">
                <span className="text-[36px] font-extrabold tabular-nums leading-none tracking-tighter text-stone-900 dark:text-zinc-50">
                  {readiness}
                </span>
                <p className="mt-0.5 text-[8px] font-bold uppercase tracking-[0.2em] text-stone-400 dark:text-zinc-500">
                  score
                </p>
              </div>
            )}
            <div className="min-w-0 flex-1 space-y-1">
              {session.health_checks.map((check) => (
                <div key={check.domain} className="flex items-center gap-1.5 text-[11px]">
                  {check.status === "ok"
                    ? <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-500" />
                    : <XCircle className="h-3 w-3 shrink-0 text-red-500" />
                  }
                  <span className="truncate text-stone-600 dark:text-zinc-400">{check.label}</span>
                </div>
              ))}
            </div>
          </div>
          {alertCount > 0 && (
            <div className="mt-3 rounded-lg bg-red-500/8 px-3 py-2">
              <p className="text-[11px] font-bold text-red-700 dark:text-red-300">
                {alertCount} alert {alertCount === 1 ? "clinico" : "clinici"}
              </p>
              {session.clinical_alerts.slice(0, 2).map((a, i) => (
                <p key={i} className="mt-0.5 text-[10px] text-red-600/80 dark:text-red-400/80">
                  {a.condition_name}
                </p>
              ))}
            </div>
          )}
          <Link
            href={appendFromParam(`/clienti/${session.client_id}`, "oggi")}
            className="mt-3 inline-flex items-center gap-1 text-[11px] font-semibold text-teal-700 transition-colors hover:text-teal-900 dark:text-teal-400"
          >
            Profilo completo <ArrowRight className="h-3 w-3" />
          </Link>
        </Quadrant>

        {/* B. Performance Snapshot */}
        <Quadrant icon={TrendingUp} title="Performance">
          {session.active_plan_name ? (
            <p className="text-[13px] font-bold text-stone-800 dark:text-zinc-200">
              {session.active_plan_name}
            </p>
          ) : (
            <p className="text-[12px] italic text-stone-400 dark:text-zinc-500">
              Nessun programma attivo
            </p>
          )}
          <div className="mt-3 space-y-2.5">
            <div className="flex items-baseline justify-between">
              <span className="text-[9px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
                Sessioni totali
              </span>
              <span className="text-[22px] font-extrabold tabular-nums tracking-tighter text-stone-900 dark:text-zinc-50">
                {session.total_sessions}
              </span>
            </div>
            {session.days_since_last_session !== null && session.days_since_last_session > 0 && (
              <div className="flex items-baseline justify-between">
                <span className="text-[9px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
                  Ultimo allenamento
                </span>
                <span className="text-[13px] font-bold tabular-nums text-stone-700 dark:text-zinc-300">
                  {session.days_since_last_session === 1 ? "ieri" : `${session.days_since_last_session}g fa`}
                </span>
              </div>
            )}
          </div>
          {session.quality_hints.length > 0 && (
            <div className="mt-3 space-y-1 border-t border-stone-100/60 pt-2 dark:border-zinc-800/40">
              {session.quality_hints.slice(0, 2).map((hint, i) => (
                <p key={i} className="text-[10px] leading-snug text-amber-700 dark:text-amber-400">
                  {hint.text}
                </p>
              ))}
            </div>
          )}
        </Quadrant>

        {/* C. Contract & Business */}
        <Quadrant icon={CreditCard} title="Contratto">
          {session.contract_credits_remaining !== null && session.contract_credits_total !== null ? (
            <>
              <div className="flex items-baseline gap-1">
                <span className="text-[36px] font-extrabold tabular-nums leading-none tracking-tighter text-stone-900 dark:text-zinc-50">
                  {session.contract_credits_remaining}
                </span>
                <span className="text-[14px] font-medium text-stone-400 dark:text-zinc-500">
                  /{session.contract_credits_total}
                </span>
              </div>
              <p className="mt-1 text-[9px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
                Crediti rimanenti
              </p>
              {session.contract_credits_remaining <= 2 && session.contract_credits_remaining > 0 && (
                <div className="mt-3 rounded-lg bg-amber-500/8 px-3 py-2">
                  <p className="text-[11px] font-bold text-amber-700 dark:text-amber-300">
                    In esaurimento
                  </p>
                </div>
              )}
              {session.contract_credits_remaining <= 0 && (
                <div className="mt-3 rounded-lg bg-red-500/8 px-3 py-2">
                  <p className="text-[11px] font-bold text-red-700 dark:text-red-300">
                    Crediti esauriti — rinnovo necessario
                  </p>
                </div>
              )}
            </>
          ) : (
            <p className="text-[12px] italic text-stone-400 dark:text-zinc-500">
              Nessun contratto attivo
            </p>
          )}
        </Quadrant>

        {/* D. Prep Notes */}
        <Quadrant icon={FileText} title="Note Sessione">
          <textarea
            value={note}
            onChange={(e) => handleNote(e.target.value)}
            placeholder="Note rapide per questa sessione..."
            rows={4}
            className="w-full resize-none rounded-lg bg-transparent text-[12px] leading-relaxed text-stone-700 placeholder:text-stone-300 focus:outline-none dark:text-zinc-300 dark:placeholder:text-zinc-600"
          />
          {note.trim() && (
            <p className="mt-1 text-[9px] text-stone-300 dark:text-zinc-600">
              Salvato localmente
            </p>
          )}
        </Quadrant>
      </div>
    </div>
  );
}
