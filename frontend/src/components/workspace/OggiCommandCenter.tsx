"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  CircleAlert,
  FileText,
  NotebookPen,
  ShieldAlert,
  Stethoscope,
  UserRound,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  surfaceChipClassName,
  surfaceRoleClassName,
  type SurfaceTone,
} from "@/components/ui/surface-role";
import { Textarea } from "@/components/ui/textarea";
import { appendFromParam } from "@/lib/url-state";
import { cn } from "@/lib/utils";
import type { SessionPrepItem } from "@/types/api";
import type { PreFlightStatus } from "@/components/workspace/OggiTimeline";
import { PREFLIGHT_META } from "@/components/workspace/OggiTimeline";

const CREDITS_CRITICAL_THRESHOLD = 2;
const CONTRACT_EXPIRY_URGENT_DAYS = 7;
const CONTRACT_EXPIRY_WARNING_DAYS = 14;
const CONTRACT_EXPIRY_VISIBLE_DAYS = 30;
const SESSION_GAP_NOTABLE_DAYS = 10;
const CLIENT_SENIORITY_NEW_MONTHS = 3;

function monthsDiff(isoFrom: string): number {
  const from = new Date(isoFrom);
  const now = new Date();
  return (now.getFullYear() - from.getFullYear()) * 12 + (now.getMonth() - from.getMonth());
}

function formatSeniority(clientSince: string | null): string | null {
  if (!clientSince) return null;
  const months = monthsDiff(clientSince);
  if (months < 0) return null;
  if (months < CLIENT_SENIORITY_NEW_MONTHS) return "cliente recente";
  if (months < 12) return `cliente da ${months} ${months === 1 ? "mese" : "mesi"}`;
  const years = Math.floor(months / 12);
  const rem = months % 12;
  const yearLabel = `${years} ${years === 1 ? "anno" : "anni"}`;
  if (rem === 0) return `cliente da ${yearLabel}`;
  return `cliente da ${yearLabel} e ${rem} ${rem === 1 ? "mese" : "mesi"}`;
}

function formatExpiryUrgency(days: number | null): string | null {
  if (days === null || days > CONTRACT_EXPIRY_VISIBLE_DAYS) return null;
  if (days < 0) return "contratto scaduto";
  if (days === 0) return "contratto scade oggi";
  if (days === 1) return "rinnovo domani";
  return `rinnovo tra ${days} giorni`;
}

function buildChips(session: SessionPrepItem): { label: string; value: string }[] {
  const anamnesi = session.health_checks.find((check) => check.domain === "anamnesi");

  const contractValue = (() => {
    if (session.contract_credits_remaining === null) return "n/d";
    if (session.contract_credits_remaining <= 0) return "Scaduto";
    if (session.contract_credits_remaining <= CREDITS_CRITICAL_THRESHOLD) return "In esaurimento";
    const expiryDays = session.contract_expiring_days;
    if (expiryDays !== null && expiryDays <= CONTRACT_EXPIRY_WARNING_DAYS) return "In scadenza";
    return "Ok";
  })();

  return [
    {
      label: "Sedute",
      value:
        session.contract_credits_remaining !== null && session.contract_credits_total !== null
          ? `${session.contract_credits_remaining} / ${session.contract_credits_total}`
          : "n/d",
    },
    {
      label: "Profilo",
      value: !anamnesi ? "n/d" : anamnesi.status === "ok" ? "Completo" : "Incompleto",
    },
    {
      label: "Scheda",
      value: session.active_plan_name
        ? session.active_plan_name.length > 14
          ? `${session.active_plan_name.slice(0, 12)}...`
          : session.active_plan_name
        : "Nessuna",
    },
    { label: "Contratto", value: contractValue },
  ];
}

const NOTES_KEY = "fitmanager.oggi.notes";

const TIME_FMT = new Intl.DateTimeFormat("it-IT", {
  hour: "2-digit",
  minute: "2-digit",
});

function minutesUntilAt(isoDate: string, nowMs: number): number | null {
  const target = new Date(isoDate);
  if (Number.isNaN(target.getTime())) return null;
  return Math.round((target.getTime() - nowMs) / 60_000);
}

function getReadinessTone(score: number | null): SurfaceTone {
  if (score === null) return "neutral";
  if (score >= 80) return "teal";
  if (score >= 50) return "amber";
  return "red";
}

function ReadinessRing({ score, size = 52 }: { score: number; size?: number }) {
  const strokeWidth = 3.5;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const ratio = Math.min(score / 100, 1);
  const offset = circumference - ratio * circumference;
  const hue = score >= 80 ? 155 : score >= 50 ? 85 : 25;
  const chroma = score >= 80 ? 0.17 : score >= 50 ? 0.15 : 0.2;
  const lightness = score >= 80 ? 0.72 : score >= 50 ? 0.75 : 0.65;
  const strokeColor = `oklch(${lightness} ${chroma} ${hue})`;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="absolute inset-0">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(0,0,0,0.05)"
          strokeWidth={strokeWidth}
          className="dark:stroke-white/[0.06]"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-700 ease-out"
          style={{ transformOrigin: "center", transform: "rotate(-90deg)" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-[13px] font-extrabold tabular-nums text-stone-800 dark:text-zinc-100">
          {score}
        </span>
      </div>
    </div>
  );
}

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

function getPreflightTone(status: PreFlightStatus): SurfaceTone {
  if (status === "ready") return "teal";
  if (status === "incomplete") return "amber";
  if (status === "risk" || status === "blocked") return "red";
  return "neutral";
}

function getAttentionTone(tone: AttentionTone): SurfaceTone {
  if (tone === "critical") return "red";
  if (tone === "warning") return "amber";
  return "neutral";
}

function getAttentionIconClassName(tone: AttentionTone): string {
  if (tone === "critical") return "text-red-600 dark:text-red-300";
  if (tone === "warning") return "text-amber-600 dark:text-amber-300";
  return "text-stone-500 dark:text-zinc-400";
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

function FocusStatCell({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="px-3 py-2.5">
      <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
        {label}
      </p>
      <p className="mt-0.5 text-[12px] font-bold tracking-tight text-stone-900 dark:text-zinc-50">
        {value}
      </p>
    </div>
  );
}

function AttentionStrip({
  item,
  prominent = false,
}: {
  item: AttentionItem;
  prominent?: boolean;
}) {
  return (
    <div
      className={surfaceRoleClassName(
        {
          role: prominent ? "hero" : "signal",
          tone: getAttentionTone(item.tone),
        },
        prominent ? "px-4 py-3.5" : "px-3 py-2.5",
      )}
    >
      <div className="flex items-start gap-2.5">
        <CircleAlert className={cn("mt-0.5 h-4 w-4 shrink-0", getAttentionIconClassName(item.tone))} />
        <div className="min-w-0">
          <p className={cn("font-bold text-stone-900 dark:text-zinc-50", prominent ? "text-[13px]" : "text-[12px]")}>
            {item.title}
          </p>
          <p className={cn("mt-0.5 leading-5 text-stone-600 dark:text-zinc-300", prominent ? "text-[11.5px]" : "text-[11px]")}>
            {item.detail}
          </p>
        </div>
      </div>
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
    <div className={surfaceRoleClassName({ role: "context", tone: "neutral" }, cn("oggi-notes-shell px-3.5 py-3.5", className))}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
          <NotebookPen className="h-3 w-3" />
          Note pre-seduta
        </div>
        <span
          className={surfaceChipClassName(
            { tone: note.trim() ? "teal" : "neutral" },
            "px-2.5 py-1 text-[9px] font-bold",
          )}
        >
          {note.trim() ? "Bozza locale" : "Pronta a scrivere"}
        </span>
      </div>

      <Textarea
        value={note}
        onChange={(event) => handleChange(event.target.value)}
        placeholder="Annota una modifica al programma, un vincolo clinico o un follow-up da non dimenticare."
        rows={3}
        className="mt-3 min-h-24 resize-none border-stone-200/80 bg-white/75 text-[12px] leading-5 text-stone-700 placeholder:text-stone-400 focus-visible:border-ring/60 focus-visible:ring-ring/40 dark:border-zinc-800 dark:bg-zinc-950/50 dark:text-zinc-300 dark:placeholder:text-zinc-500"
      />

      <p className="mt-2 text-[9px] text-stone-400 dark:text-zinc-500">
        {note.trim()
          ? "Salvato localmente su questo dispositivo."
          : "Vuoto: usa questo spazio per preparare la seduta senza sporcare il CRM."}
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
  const [clockMs, setClockMs] = useState(() => Date.now());

  useEffect(() => {
    const id = window.setInterval(() => setClockMs(Date.now()), 15_000);
    return () => window.clearInterval(id);
  }, []);

  const mins = session ? minutesUntilAt(session.starts_at, clockMs) : null;

  const isOngoing = mins !== null && mins <= 0;
  const isImminent = mins !== null && mins <= 15 && mins > 0;
  const hasClinicalAlerts = Boolean(session?.clinical_alerts.length);
  const glowClass = isOngoing
    ? "oggi-glow-teal"
    : isImminent
      ? "oggi-glow-amber"
      : hasClinicalAlerts
        ? "oggi-glow-red"
        : "oggi-glow-neutral";

  if (!session) {
    return (
      <div
        className={cn(
          surfaceRoleClassName({ role: "hero", tone: "neutral" }, cn("flex items-center justify-center p-8 text-center", className)),
          "oggi-lift oggi-glow-neutral",
        )}
      >
        <div className="max-w-sm">
          <Stethoscope className="mx-auto h-8 w-8 text-stone-300 dark:text-zinc-600" />
          <p className="mt-3 text-[13px] font-bold text-stone-600 dark:text-zinc-300">
            Nessuna seduta in focus
          </p>
          <p className="mt-1 text-[11px] leading-5 text-stone-500 dark:text-zinc-400">
            Quando scegli una seduta dal flusso di oggi, qui resta davanti solo il contesto che puo&apos; cambiare il lavoro in sala.
          </p>
        </div>
      </div>
    );
  }

  if (!session.client_id) {
    return (
      <div className={cn(surfaceRoleClassName({ role: "hero", tone: "neutral" }, cn("p-5 sm:p-6", className)), "oggi-lift", glowClass)}>
        <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
          Focus interno
        </p>
        <h2 className="mt-1.5 text-[22px] font-extrabold tracking-tight text-stone-900 dark:text-zinc-50">
          {session.event_title ?? session.category}
        </h2>
        <p className="mt-2.5 text-[12px] leading-5 text-stone-600 dark:text-zinc-300">
          Questo slot non ha un cliente associato, quindi resta fuori dalla preparazione pre-seduta vera e propria.
        </p>
        {session.event_notes && (
          <div className={surfaceRoleClassName({ role: "context", tone: "neutral" }, "mt-4 px-3.5 py-3.5")}>
            <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
              <FileText className="h-3 w-3" />
              Note evento
            </div>
            <p className="mt-2.5 text-[12px] leading-5 text-stone-700 dark:text-zinc-300">
              {session.event_notes}
            </p>
          </div>
        )}
        <div className="mt-5">
          <Button asChild className="h-9 rounded-full px-3.5 text-[13px] font-bold">
            <Link href="/agenda">
              Apri agenda
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const meta = PREFLIGHT_META[status];
  const attentionItems = buildAttentionItems(session, status);
  const primaryAttention = attentionItems[0] ?? null;
  const secondaryAttention = attentionItems.slice(1, 4);
  const hasQuickContext = session.quality_hints.length > 0 || Boolean(session.event_notes);
  const chips = buildChips(session);
  const statusTone = getPreflightTone(status);
  const readinessTone = getReadinessTone(session.readiness_score);

  const contextLines: { text: string; tone: "neutral" | "amber" | "red" }[] = [];
  const seniority = formatSeniority(session.client_since ?? null);
  if (seniority) contextLines.push({ text: seniority, tone: "neutral" });

  const expiryText = formatExpiryUrgency(session.contract_expiring_days ?? null);
  if (expiryText) {
    const isUrgent =
      session.contract_expiring_days !== null && session.contract_expiring_days <= CONTRACT_EXPIRY_URGENT_DAYS;
    contextLines.push({ text: expiryText, tone: isUrgent ? "red" : "amber" });
  }

  if (session.days_since_last_session !== null && session.days_since_last_session >= SESSION_GAP_NOTABLE_DAYS) {
    contextLines.push({
      text: `Non si allena da ${session.days_since_last_session} giorni`,
      tone: "amber",
    });
  }

  const timingLabel = (() => {
    if (isOngoing) return "In corso";
    if (isImminent && mins !== null) return `Tra ${mins} min`;
    return TIME_FMT.format(new Date(session.starts_at));
  })();

  const profileHref = appendFromParam(`/clienti/${session.client_id}`, "oggi");
  const planHref = session.active_plan_name
    ? appendFromParam(`/allenamenti?idCliente=${session.client_id}`, "oggi")
    : null;

  return (
    <div className={cn(surfaceRoleClassName({ role: "hero", tone: "neutral" }, cn("oggi-dossier-shell p-4 sm:p-5", className)), "oggi-lift", glowClass)}>
      <div className="flex flex-col gap-3.5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex items-start gap-3">
              {session.readiness_score !== null && (
                <div
                  className={surfaceRoleClassName(
                    { role: "signal", tone: readinessTone },
                    "flex h-14 w-14 shrink-0 items-center justify-center px-2 py-2",
                  )}
                >
                  <ReadinessRing score={session.readiness_score} />
                </div>
              )}

              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
                    Focus attivo
                  </p>
                  <span
                    className={surfaceChipClassName(
                      { tone: isOngoing ? "teal" : isImminent ? "amber" : "neutral" },
                      "px-2.5 py-1 text-[10px] font-bold",
                    )}
                  >
                    {timingLabel}
                  </span>
                </div>

                <h2 className="mt-1.5 text-[26px] font-black tracking-tight text-stone-900 dark:text-zinc-50 sm:text-[30px]">
                  {session.client_name}
                </h2>

                <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-stone-500 dark:text-zinc-400">
                  {session.client_age !== null && <span>{session.client_age} anni</span>}
                  {session.is_new_client && <span>nuovo cliente</span>}
                  {session.client_sex && <span>{session.client_sex}</span>}
                  {session.readiness_score !== null && <span>readiness {session.readiness_score}</span>}
                </div>
              </div>
            </div>
          </div>

          <span
            className={cn(
              surfaceChipClassName(
                { tone: statusTone, emphasis: "strong" },
                "inline-flex items-center self-start text-[10px] font-bold uppercase tracking-[0.14em]",
              ),
              meta.color,
            )}
          >
            {meta.label}
          </span>
        </div>

        <div className="oggi-dossier-stats overflow-hidden rounded-[24px] border border-stone-200/90 bg-stone-50/80 dark:border-zinc-800 dark:bg-zinc-950/50">
          <div className="grid gap-px bg-stone-200/80 sm:grid-cols-2 lg:grid-cols-4 dark:bg-zinc-800">
            {chips.map((chip) => (
              <div key={chip.label} className="bg-white/80 dark:bg-zinc-950/70">
                <FocusStatCell label={chip.label} value={chip.value} />
              </div>
            ))}
          </div>
        </div>

        {contextLines.length > 0 && (
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {contextLines.map((line) => (
              <p
                key={line.text}
                className={cn(
                  "text-[11px] leading-5",
                  line.tone === "red"
                    ? "text-red-600 dark:text-red-400"
                    : line.tone === "amber"
                      ? "text-amber-700 dark:text-amber-400"
                      : "text-stone-500 dark:text-zinc-400",
                )}
              >
                {line.text}
              </p>
            ))}
          </div>
        )}

        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.08fr)_minmax(280px,0.92fr)]">
          <div className="space-y-3">
            <section className={surfaceRoleClassName({ role: "context", tone: "neutral" }, "px-3.5 py-3.5")}>
              <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
                <ShieldAlert className="h-3 w-3" />
                Prima di entrare in sala
              </div>

              {primaryAttention ? (
                <div className="mt-3 space-y-2.5">
                  <AttentionStrip item={primaryAttention} prominent />
                  {secondaryAttention.length > 0 && (
                    <div className="grid gap-2 sm:grid-cols-2">
                      {secondaryAttention.map((item, index) => (
                        <AttentionStrip key={`${item.title}-${index}`} item={item} />
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className={surfaceRoleClassName({ role: "signal", tone: "teal" }, "mt-3 px-3.5 py-3")}>
                  <p className="text-[12px] font-bold text-emerald-700 dark:text-emerald-300">
                    Seduta pronta
                  </p>
                  <p className="mt-0.5 text-[11px] leading-5 text-emerald-800/80 dark:text-emerald-200/80">
                    Non emergono blocchi clinico-operativi immediati.
                  </p>
                </div>
              )}
            </section>

          </div>

          <div className="space-y-3">
            <PrepNotesField key={session.event_id} eventId={session.event_id} />

            {hasQuickContext && (
              <section className={surfaceRoleClassName({ role: "context", tone: "neutral" }, "px-3.5 py-3.5")}>
                <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
                  <UserRound className="h-3 w-3" />
                  Contesto seduta
                </div>

                {session.quality_hints.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {session.quality_hints.slice(0, 3).map((hint, index) => (
                      <p
                        key={`${hint.code}-${index}`}
                        className="text-[11px] leading-5 text-stone-600 dark:text-zinc-300"
                      >
                        {hint.text}
                      </p>
                    ))}
                  </div>
                )}

                {session.event_notes && (
                  <div
                    className={surfaceRoleClassName(
                      { role: "signal", tone: "neutral" },
                      cn(session.quality_hints.length > 0 && "mt-3", "px-3 py-2.5"),
                    )}
                  >
                    <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
                      <FileText className="h-3 w-3" />
                      Note appuntamento
                    </div>
                    <p className="mt-2.5 text-[12px] leading-5 text-stone-700 dark:text-zinc-300">
                      {session.event_notes}
                    </p>
                  </div>
                )}
              </section>
            )}

            <section className={surfaceRoleClassName({ role: "context", tone: "neutral" }, "px-3.5 py-3.5")}>
              <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.16em] text-stone-400 dark:text-zinc-500">
                <ArrowRight className="h-3 w-3" />
                Azioni rapide
              </div>

              <div className="mt-3 flex flex-wrap gap-2.5">
                <Button asChild className="h-9 rounded-full px-3.5 text-[13px] font-bold">
                  <Link href={profileHref}>
                    Profilo completo
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                {planHref && (
                  <Button asChild variant="outline" className="h-9 rounded-full px-3.5 text-[13px] font-bold">
                    <Link href={planHref}>
                      Scheda attiva
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                )}
                <Button asChild variant="outline" className="h-9 rounded-full px-3.5 text-[13px] font-bold">
                  <Link href="/agenda">Vai in agenda</Link>
                </Button>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
