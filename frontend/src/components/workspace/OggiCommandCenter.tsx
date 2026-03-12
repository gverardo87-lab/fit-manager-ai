"use client";

import { type ComponentType, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  CalendarClock,
  CircleAlert,
  CreditCard,
  FileText,
  NotebookPen,
  ShieldAlert,
  Stethoscope,
  TrendingUp,
  UserRound,
} from "lucide-react";

import { appendFromParam } from "@/lib/url-state";
import { cn } from "@/lib/utils";
import type { SessionPrepItem } from "@/types/api";
import type { PreFlightStatus } from "@/components/workspace/OggiTimeline";
import { PREFLIGHT_META } from "@/components/workspace/OggiTimeline";

const NOTES_KEY = "fitmanager.oggi.notes";

const TIME_FMT = new Intl.DateTimeFormat("it-IT", {
  hour: "2-digit",
  minute: "2-digit",
});

function loadNotesMap(): Record<string, string> {
  if (typeof window === "undefined") return {};

  try {
    const raw = window.localStorage.getItem(NOTES_KEY);
    return raw ? (JSON.parse(raw) as Record<string, string>) : {};
  } catch {
    return {};
  }
}

function loadNote(eventId: number): string {
  return loadNotesMap()[String(eventId)] ?? "";
}

function saveNote(eventId: number, text: string) {
  if (typeof window === "undefined") return;

  try {
    const notes = loadNotesMap();
    if (text.trim()) notes[String(eventId)] = text;
    else delete notes[String(eventId)];
    window.localStorage.setItem(NOTES_KEY, JSON.stringify(notes));
  } catch {
    // noop
  }
}

type AttentionTone = "critical" | "warning" | "neutral";

interface AttentionItem {
  tone: AttentionTone;
  title: string;
  detail: string;
}

function buildAttentionItems(session: SessionPrepItem, status: PreFlightStatus): AttentionItem[] {
  const items: AttentionItem[] = [];

  if (session.clinical_alerts.length > 0) {
    items.push({
      tone: "critical",
      title:
        session.clinical_alerts.length === 1
          ? "Alert clinico da rivedere"
          : `${session.clinical_alerts.length} alert clinici da rivedere`,
      detail: session.clinical_alerts
        .slice(0, 2)
        .map((alert) => alert.condition_name)
        .join(" | "),
    });
  }

  session.health_checks
    .filter((check) => check.status !== "ok")
    .slice(0, 3)
    .forEach((check) => {
      items.push({
        tone: check.status === "critical" ? "critical" : "warning",
        title: check.label,
        detail: check.detail ?? "Da verificare prima della seduta.",
      });
    });

  if (session.contract_credits_remaining !== null) {
    if (session.contract_credits_remaining <= 0) {
      items.push({
        tone: "critical",
        title: "Contratto esaurito",
        detail: "I crediti risultano terminati: la seduta va chiarita prima di procedere.",
      });
    } else if (session.contract_credits_remaining <= 2) {
      items.push({
        tone: "warning",
        title: "Contratto in esaurimento",
        detail: `${session.contract_credits_remaining} crediti residui su ${session.contract_credits_total ?? "n/d"}.`,
      });
    }
  }

  if (!session.active_plan_name) {
    items.push({
      tone: status === "ready" ? "neutral" : "warning",
      title: "Programma da verificare",
      detail: "Non risulta una scheda attiva associata a questa seduta.",
    });
  }

  if (session.is_new_client) {
    items.push({
      tone: "neutral",
      title: "Nuovo cliente",
      detail: "Tieni a vista anamnesi, obiettivo e prime note operative.",
    });
  }

  return items;
}

function formatLastSession(daysSinceLastSession: number | null): string {
  if (daysSinceLastSession === null) return "n/d";
  if (daysSinceLastSession === 0) return "oggi";
  if (daysSinceLastSession === 1) return "ieri";
  return `${daysSinceLastSession} giorni fa`;
}

function ContextTile({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div
      className="rounded-[22px] px-3.5 py-3"
      style={{
        border: "0.5px solid oklch(0.82 0.02 170 / 0.12)",
        background:
          "linear-gradient(180deg, oklch(0.998 0.006 95 / 0.94), oklch(0.988 0.01 170 / 0.76))",
      }}
    >
      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className="mt-2 text-[15px] font-extrabold tracking-tight text-stone-900 dark:text-zinc-50">
        {value}
      </p>
      <p className="mt-1 text-[10px] leading-5 text-stone-500 dark:text-zinc-400">
        {detail}
      </p>
    </div>
  );
}

function PrepNotesField({
  eventId,
  className,
}: {
  eventId: number;
  className?: string;
}) {
  const [note, setNote] = useState(() => loadNote(eventId));

  const handleChange = (value: string) => {
    setNote(value);
    saveNote(eventId, value);
  };

  return (
    <div
      className={cn("rounded-[24px] px-4 py-4", className)}
      style={{
        border: "0.5px solid oklch(0.80 0.03 165 / 0.14)",
        background:
          "linear-gradient(180deg, oklch(0.997 0.008 95 / 0.98), oklch(0.988 0.014 170 / 0.78))",
      }}
    >
      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
        <NotebookPen className="h-3.5 w-3.5" />
        Note pre-seduta
      </div>
      <textarea
        value={note}
        onChange={(event) => handleChange(event.target.value)}
        placeholder="Annota una modifica al programma, un vincolo clinico o un follow-up da non dimenticare."
        rows={3}
        className="mt-3 w-full resize-none rounded-xl bg-white/55 px-3 py-2.5 text-[13px] leading-6 text-stone-700 placeholder:text-stone-300 focus:outline-none dark:bg-zinc-950/30 dark:text-zinc-300 dark:placeholder:text-zinc-600"
      />
      <p className="mt-2 text-[10px] text-stone-400 dark:text-zinc-500">
        {note.trim() ? "Salvato localmente su questo dispositivo." : "Vuoto: usa questo spazio per preparare la seduta."}
      </p>
    </div>
  );
}

interface OggiCommandCenterProps {
  session: SessionPrepItem | null;
  status: PreFlightStatus;
  className?: string;
}

export function OggiCommandCenter({
  session,
  status,
  className,
}: OggiCommandCenterProps) {
  if (!session) {
    return (
      <div
        className={cn("flex items-center justify-center rounded-[28px] p-10 text-center", className)}
        style={{
          border: "0.5px solid oklch(0.82 0.02 170 / 0.12)",
          background:
            "linear-gradient(180deg, oklch(0.998 0.006 95 / 0.96), oklch(0.988 0.01 175 / 0.74))",
        }}
      >
        <div className="max-w-sm">
          <Stethoscope className="mx-auto h-10 w-10 text-stone-300 dark:text-zinc-600" />
          <p className="mt-4 text-sm font-bold text-stone-600 dark:text-zinc-300">
            Apri una seduta dalla lista
          </p>
          <p className="mt-1 text-[12px] leading-5 text-stone-500 dark:text-zinc-400">
            Qui vedrai la scheda pre-seduta con i punti da verificare, il contesto utile e le note operative.
          </p>
        </div>
      </div>
    );
  }

  if (!session.client_id) {
    return (
      <div
        className={cn("rounded-[28px] p-6 sm:p-7", className)}
        style={{
          border: "0.5px solid oklch(0.82 0.02 170 / 0.12)",
          background:
            "linear-gradient(180deg, oklch(0.998 0.006 95 / 0.96), oklch(0.988 0.01 175 / 0.74))",
        }}
      >
        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
          Impegno interno
        </p>
        <h2 className="mt-2 text-2xl font-extrabold tracking-tight text-stone-900 dark:text-zinc-50">
          {session.event_title ?? session.category}
        </h2>
        <p className="mt-3 text-[13px] leading-6 text-stone-600 dark:text-zinc-300">
          Questo slot non ha un cliente associato, quindi non richiede una scheda pre-seduta clinica.
        </p>
        {session.event_notes && (
          <div
            className="mt-5 rounded-2xl px-4 py-4"
            style={{
              border: "0.5px solid oklch(0.82 0.02 170 / 0.12)",
              background:
                "linear-gradient(180deg, oklch(0.998 0.006 95 / 0.92), oklch(0.988 0.01 170 / 0.74))",
            }}
          >
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
              <FileText className="h-3.5 w-3.5" />
              Note evento
            </div>
            <p className="mt-3 text-[13px] leading-6 text-stone-700 dark:text-zinc-300">
              {session.event_notes}
            </p>
          </div>
        )}
        <div className="mt-6">
          <Link
            href="/agenda"
            className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-bold text-white"
            style={{
              background: "linear-gradient(135deg, oklch(0.47 0.11 168), oklch(0.41 0.09 198))",
            }}
          >
            Apri agenda
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    );
  }

  const meta = PREFLIGHT_META[status];
  const attentionItems = buildAttentionItems(session, status);
  const hasQuickContext = session.quality_hints.length > 0 || Boolean(session.event_notes);

  return (
    <div
      className={cn("rounded-[28px] p-5 sm:p-6", className)}
      style={{
        border: "0.5px solid oklch(0.80 0.03 165 / 0.14)",
        background:
          "linear-gradient(180deg, oklch(0.998 0.008 92 / 0.98), oklch(0.989 0.013 170 / 0.86) 42%, oklch(0.985 0.016 195 / 0.74))",
      }}
    >
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
              Scheda pre-seduta
            </p>
            <h2 className="mt-2 text-2xl font-extrabold tracking-tight text-stone-900 dark:text-zinc-50">
              {session.client_name}
            </h2>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-[12px] text-stone-500 dark:text-zinc-400">
              <span
                className="rounded-full px-2.5 py-1 font-semibold shadow-sm dark:bg-zinc-950/40"
                style={{ background: "oklch(1 0 0 / 0.72)" }}
              >
                {TIME_FMT.format(new Date(session.starts_at))}
              </span>
              {session.client_age !== null && <span>{session.client_age} anni</span>}
              {session.is_new_client && <span>nuovo cliente</span>}
              {session.client_sex && <span>{session.client_sex}</span>}
            </div>
            <p className="mt-2 max-w-2xl text-[12px] leading-5 text-stone-600 dark:text-zinc-300">
              Tieni in alto i punti che possono cambiare la seduta, poi usa note e contesto rapido per entrare in sala senza riaprire tutto il profilo.
            </p>
          </div>

          <span
            className={cn(
              "inline-flex items-center self-start rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.14em]",
              meta.color,
            )}
            style={{
              background:
                status === "ready"
                  ? "oklch(0.62 0.15 150 / 0.10)"
                  : status === "incomplete"
                    ? "oklch(0.75 0.12 70 / 0.10)"
                    : "oklch(0.55 0.15 25 / 0.10)",
            }}
          >
            {meta.label}
          </span>
        </div>

        <div className="grid gap-4 2xl:grid-cols-[minmax(0,1.02fr)_minmax(290px,0.98fr)]">
          <div className="space-y-4">
            <section
              className="rounded-[24px] px-4 py-4"
              style={{
                border: "0.5px solid oklch(0.80 0.03 165 / 0.14)",
                background:
                  "linear-gradient(180deg, oklch(0.997 0.008 95 / 0.98), oklch(0.989 0.014 170 / 0.78))",
              }}
            >
              <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
                <ShieldAlert className="h-3.5 w-3.5" />
                Da verificare adesso
              </div>

              {attentionItems.length > 0 ? (
                <div className="mt-4 grid gap-2.5 md:grid-cols-2">
                  {attentionItems.map((item, index) => (
                    <div
                      key={`${item.title}-${index}`}
                      className="rounded-[20px] px-3.5 py-3"
                      style={{
                        background:
                          item.tone === "critical"
                            ? "linear-gradient(180deg, oklch(0.995 0.012 35 / 0.94), oklch(0.982 0.016 25 / 0.72))"
                            : item.tone === "warning"
                              ? "linear-gradient(180deg, oklch(0.997 0.016 88 / 0.96), oklch(0.987 0.022 82 / 0.76))"
                              : "linear-gradient(180deg, oklch(0.998 0.006 95 / 0.92), oklch(0.988 0.01 170 / 0.72))",
                      }}
                    >
                      <div className="flex items-start gap-3">
                        <CircleAlert
                          className={cn(
                            "mt-0.5 h-4 w-4 shrink-0",
                            item.tone === "critical"
                              ? "text-red-600 dark:text-red-300"
                              : item.tone === "warning"
                                ? "text-amber-600 dark:text-amber-300"
                                : "text-stone-500 dark:text-zinc-400",
                          )}
                        />
                        <div>
                          <p className="text-[13px] font-bold text-stone-900 dark:text-zinc-50">
                            {item.title}
                          </p>
                          <p className="mt-1 text-[12px] leading-5 text-stone-600 dark:text-zinc-300">
                            {item.detail}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div
                  className="mt-4 rounded-[20px] px-4 py-4"
                  style={{
                    background:
                      "linear-gradient(180deg, oklch(0.992 0.014 150 / 0.86), oklch(0.982 0.02 160 / 0.62))",
                  }}
                >
                  <p className="text-[13px] font-bold text-emerald-700 dark:text-emerald-300">
                    Seduta pronta
                  </p>
                  <p className="mt-1 text-[12px] leading-5 text-emerald-800/80 dark:text-emerald-200/80">
                    Non emergono blocchi clinico-operativi immediati. Usa note e contesto rapido per entrare in sala con la seduta gia&apos; chiara.
                  </p>
                </div>
              )}
            </section>

            <PrepNotesField key={session.event_id} eventId={session.event_id} />

            <div className="flex flex-wrap gap-3">
              <Link
                href={appendFromParam(`/clienti/${session.client_id}`, "oggi")}
                className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-bold text-white"
                style={{
                  background: "linear-gradient(135deg, oklch(0.47 0.11 168), oklch(0.41 0.09 198))",
                }}
              >
                Apri profilo cliente
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/agenda"
                className="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold text-stone-700 transition-colors hover:bg-white/70 dark:border-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-950/40"
                style={{ borderColor: "oklch(0.82 0.02 170 / 0.18)" }}
              >
                Vai in agenda
              </Link>
            </div>
          </div>

          <div className="space-y-4">
            <section className="grid gap-3 sm:grid-cols-2">
              <ContextTile
                icon={TrendingUp}
                label="Readiness"
                value={session.readiness_score !== null ? `${session.readiness_score}/100` : "n/d"}
                detail="Punteggio sintetico pre-seduta."
              />
              <ContextTile
                icon={FileText}
                label="Programma"
                value={session.active_plan_name ?? "Nessuna scheda"}
                detail="Scheda attiva collegata alla seduta."
              />
              <ContextTile
                icon={CalendarClock}
                label="Ultima seduta"
                value={formatLastSession(session.days_since_last_session)}
                detail={`${session.completed_sessions}/${session.total_sessions} completate in storico.`}
              />
              <ContextTile
                icon={CreditCard}
                label="Contratto"
                value={
                  session.contract_credits_remaining !== null && session.contract_credits_total !== null
                    ? `${session.contract_credits_remaining}/${session.contract_credits_total}`
                    : "n/d"
                }
                detail="Crediti residui prima della seduta."
              />
            </section>

            {hasQuickContext && (
              <section
                className="rounded-[24px] px-4 py-4"
                style={{
                  border: "0.5px solid oklch(0.82 0.02 170 / 0.12)",
                  background:
                    "linear-gradient(180deg, oklch(0.998 0.006 95 / 0.94), oklch(0.988 0.01 170 / 0.76))",
                }}
              >
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
                  <UserRound className="h-3.5 w-3.5" />
                  Contesto seduta
                </div>

                {session.quality_hints.length > 0 && (
                  <div className="mt-4 space-y-2.5">
                    {session.quality_hints.slice(0, 3).map((hint, index) => (
                      <p
                        key={`${hint.code}-${index}`}
                        className="text-[12px] leading-5 text-stone-600 dark:text-zinc-300"
                      >
                        {hint.text}
                      </p>
                    ))}
                  </div>
                )}

                {session.event_notes && (
                  <div
                    className={cn(
                      "rounded-[20px] px-3.5 py-3",
                      session.quality_hints.length > 0 && "mt-4",
                    )}
                    style={{
                      background: "oklch(1 0 0 / 0.62)",
                    }}
                  >
                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
                      <FileText className="h-3.5 w-3.5" />
                      Note appuntamento
                    </div>
                    <p className="mt-3 text-[13px] leading-6 text-stone-700 dark:text-zinc-300">
                      {session.event_notes}
                    </p>
                  </div>
                )}
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
