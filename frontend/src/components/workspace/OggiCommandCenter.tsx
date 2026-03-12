"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, CircleAlert, FileText, NotebookPen, Stethoscope } from "lucide-react";

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
import { PREFLIGHT_META, type PreFlightStatus } from "@/components/workspace/OggiTimeline";

// ── Costanti ──────────────────────────────────────────────────────

const NOTES_KEY = "fitmanager.oggi.notes";
const TIME_FMT = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });

// ── Helper functions ──────────────────────────────────────────────

function minutesUntil(isoDate: string, nowMs: number): number | null {
  const t = new Date(isoDate).getTime();
  return Number.isNaN(t) ? null : Math.round((t - nowMs) / 60_000);
}

function getReadinessTone(score: number | null): SurfaceTone {
  if (score === null) return "neutral";
  if (score >= 80) return "teal";
  if (score >= 50) return "amber";
  return "red";
}

function getPreflightTone(status: PreFlightStatus): SurfaceTone {
  if (status === "ready") return "teal";
  if (status === "incomplete") return "amber";
  if (status === "risk" || status === "blocked") return "red";
  return "neutral";
}

function formatSeniority(clientSince: string | null): string | null {
  if (!clientSince) return null;
  const now = new Date();
  const from = new Date(clientSince);
  const months =
    (now.getFullYear() - from.getFullYear()) * 12 + (now.getMonth() - from.getMonth());
  if (months < 0) return null;
  if (months < 3) return "cliente recente";
  if (months < 12) return `da ${months} ${months === 1 ? "mese" : "mesi"}`;
  const y = Math.floor(months / 12);
  const r = months % 12;
  return r === 0 ? `da ${y} ${y === 1 ? "anno" : "anni"}` : `da ${y}a ${r}m`;
}

function formatExpiry(days: number | null): string | null {
  if (days === null || days > 30) return null;
  if (days < 0) return "contratto scaduto";
  if (days === 0) return "scade oggi";
  if (days === 1) return "rinnovo domani";
  return `rinnovo tra ${days}g`;
}

// ── Note locali ───────────────────────────────────────────────────

function loadNote(eventId: number): string {
  if (typeof window === "undefined") return "";
  try {
    const raw = window.localStorage.getItem(NOTES_KEY);
    return raw ? ((JSON.parse(raw) as Record<string, string>)[String(eventId)] ?? "") : "";
  } catch {
    return "";
  }
}

function saveNote(eventId: number, text: string) {
  if (typeof window === "undefined") return;
  try {
    const raw = window.localStorage.getItem(NOTES_KEY);
    const map: Record<string, string> = raw ? (JSON.parse(raw) as Record<string, string>) : {};
    if (text.trim()) map[String(eventId)] = text;
    else delete map[String(eventId)];
    window.localStorage.setItem(NOTES_KEY, JSON.stringify(map));
  } catch { /* noop */ }
}

function PrepNotes({ eventId }: { eventId: number }) {
  const [note, setNote] = useState(() => loadNote(eventId));
  const handleChange = (v: string) => { setNote(v); saveNote(eventId, v); };

  return (
    <div className={surfaceRoleClassName({ role: "context", tone: "neutral" }, "oggi-notes-shell px-3.5 py-3")}>
      <div className="mb-2.5 flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
        <NotebookPen className="h-3 w-3" />
        Note pre-seduta
        {note.trim() && (
          <span className={surfaceChipClassName({ tone: "teal" }, "ml-auto px-2 py-0.5 text-[9px] font-bold")}>
            Salvata
          </span>
        )}
      </div>
      <Textarea
        value={note}
        onChange={(e) => handleChange(e.target.value)}
        placeholder="Annotazione rapida: modifica al programma, vincolo clinico, follow-up."
        rows={3}
        className="min-h-20 resize-none border-border/60 bg-background/70 text-[12px] leading-5 placeholder:text-muted-foreground/50 focus-visible:ring-ring/30"
      />
    </div>
  );
}

// ── Readiness Ring ────────────────────────────────────────────────

function ReadinessRing({ score, size = 48 }: { score: number; size?: number }) {
  const sw = 3.5;
  const r = (size - sw) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - Math.min(score / 100, 1) * circ;
  const hue = score >= 80 ? 155 : score >= 50 ? 85 : 25;
  const chroma = score >= 80 ? 0.17 : 0.18;
  const l = score >= 80 ? 0.72 : score >= 50 ? 0.73 : 0.65;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="absolute inset-0">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth={sw} className="dark:stroke-white/[0.06]" />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={`oklch(${l} ${chroma} ${hue})`}
          strokeWidth={sw} strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-700 ease-out"
          style={{ transformOrigin: "center", transform: "rotate(-90deg)" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-[12px] font-extrabold tabular-nums text-foreground">{score}</span>
      </div>
    </div>
  );
}

// ── OggiCommandCenter ─────────────────────────────────────────────

interface OggiCommandCenterProps {
  session: SessionPrepItem | null;
  status: PreFlightStatus;
  className?: string;
}

export function OggiCommandCenter({ session, status, className }: OggiCommandCenterProps) {
  const [clockMs, setClockMs] = useState(() => Date.now());

  useEffect(() => {
    const id = window.setInterval(() => setClockMs(Date.now()), 15_000);
    return () => window.clearInterval(id);
  }, []);

  // ── Empty state ──
  if (!session) {
    return (
      <div className={cn(surfaceRoleClassName({ role: "hero", tone: "neutral" }, cn("flex items-center justify-center p-8 text-center", className)), "oggi-lift oggi-glow-neutral")}>
        <div className="max-w-xs">
          <Stethoscope className="mx-auto h-8 w-8 text-muted-foreground/30" />
          <p className="mt-3 text-[13px] font-bold text-muted-foreground">Nessuna seduta in focus</p>
          <p className="mt-1 text-[11px] leading-5 text-muted-foreground/60">
            Seleziona una seduta dalla timeline per vedere il contesto pre-seduta.
          </p>
        </div>
      </div>
    );
  }

  // ── Slot interno (no cliente) ──
  if (!session.client_id) {
    return (
      <div className={cn(surfaceRoleClassName({ role: "hero", tone: "neutral" }, cn("p-5", className)), "oggi-lift oggi-glow-neutral")}>
        <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-muted-foreground">Slot interno</p>
        <h2 className="mt-1.5 text-[22px] font-extrabold tracking-tight text-foreground">
          {session.event_title ?? session.category}
        </h2>
        {session.event_notes && (
          <div className={surfaceRoleClassName({ role: "context", tone: "neutral" }, "mt-4 px-3.5 py-3")}>
            <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
              <FileText className="h-3 w-3" />
              Note evento
            </div>
            <p className="mt-2.5 text-[12px] leading-5 text-foreground/80">{session.event_notes}</p>
          </div>
        )}
        <Button asChild size="sm" className="mt-5 h-8 rounded-full px-3.5 text-[12px] font-semibold">
          <Link href="/agenda">Apri agenda <ArrowRight className="h-3.5 w-3.5" /></Link>
        </Button>
      </div>
    );
  }

  // ── Sessione cliente ──
  const mins = minutesUntil(session.starts_at, clockMs);
  const isOngoing = mins !== null && mins <= 0;
  const isImminent = mins !== null && mins > 0 && mins <= 15;

  const glowClass = isOngoing ? "oggi-glow-teal" : isImminent ? "oggi-glow-amber" : session.clinical_alerts.length > 0 ? "oggi-glow-red" : "oggi-glow-neutral";
  const timingLabel = isOngoing ? "In corso" : isImminent && mins !== null ? `Tra ${mins} min` : TIME_FMT.format(new Date(session.starts_at));
  const timingTone: SurfaceTone = isOngoing ? "teal" : isImminent ? "amber" : "neutral";

  const meta = PREFLIGHT_META[status];
  const statusTone = getPreflightTone(status);
  const readinessTone = getReadinessTone(session.readiness_score);

  // Chips statistiche
  const anamnesiCheck = session.health_checks.find((c) => c.domain === "anamnesi");
  const creditsRem = session.contract_credits_remaining;
  const creditsTotal = session.contract_credits_total;
  const chips: { label: string; value: string; tone: SurfaceTone }[] = [
    {
      label: "Sedute",
      value: creditsRem !== null && creditsTotal !== null ? `${creditsRem}/${creditsTotal}` : "n/d",
      tone: creditsRem !== null && creditsRem <= 0 ? "red" : creditsRem !== null && creditsRem <= 2 ? "amber" : "neutral",
    },
    {
      label: "Profilo",
      value: anamnesiCheck?.status === "ok" ? "Completo" : "Incompleto",
      tone: anamnesiCheck?.status === "ok" ? "neutral" : "amber",
    },
    {
      label: "Scheda",
      value: session.active_plan_name ? (session.active_plan_name.length > 14 ? session.active_plan_name.slice(0, 12) + "…" : session.active_plan_name) : "Nessuna",
      tone: session.active_plan_name ? "neutral" : "amber",
    },
    {
      label: "Contratto",
      value: creditsRem !== null && creditsRem <= 0 ? "Esaurito" : session.contract_expiring_days !== null && session.contract_expiring_days <= 14 ? "In scadenza" : "Ok",
      tone: creditsRem !== null && creditsRem <= 0 ? "red" : session.contract_expiring_days !== null && session.contract_expiring_days <= 14 ? "amber" : "neutral",
    },
  ];

  // Alerts
  const alerts: { title: string; detail: string; critical: boolean }[] = [];
  if (session.clinical_alerts.length > 0) {
    alerts.push({ title: session.clinical_alerts.length === 1 ? "Alert clinico" : `${session.clinical_alerts.length} alert clinici`, detail: session.clinical_alerts.slice(0, 2).map((a) => a.condition_name).join(" · "), critical: true });
  }
  session.health_checks.filter((c) => c.status !== "ok").slice(0, 2).forEach((c) => {
    alerts.push({ title: c.label, detail: c.detail ?? "Da verificare prima della seduta.", critical: c.status === "critical" });
  });
  if (creditsRem !== null && creditsRem <= 0) alerts.push({ title: "Contratto esaurito", detail: "I crediti risultano terminati: chiarire prima di procedere.", critical: true });
  else if (creditsRem !== null && creditsRem <= 2) alerts.push({ title: "Crediti in esaurimento", detail: `${creditsRem} ${creditsRem === 1 ? "credito residuo" : "crediti residui"}.`, critical: false });
  if (!session.active_plan_name) alerts.push({ title: "Programma da verificare", detail: "Non risulta una scheda attiva associata.", critical: false });

  const primaryAlert = alerts[0] ?? null;
  const secondaryAlerts = alerts.slice(1, 3);

  // Contesto inline
  const contextParts: string[] = [];
  if (session.client_age !== null) contextParts.push(`${session.client_age} anni`);
  const seniority = formatSeniority(session.client_since ?? null);
  if (seniority) contextParts.push(seniority);
  const expiry = formatExpiry(session.contract_expiring_days ?? null);
  if (expiry) contextParts.push(expiry);
  if (session.days_since_last_session !== null && session.days_since_last_session >= 10)
    contextParts.push(`${session.days_since_last_session}g senza allenamento`);

  const profileHref = appendFromParam(`/clienti/${session.client_id}`, "oggi");
  const planHref = session.active_plan_name
    ? appendFromParam(`/allenamenti?idCliente=${session.client_id}`, "oggi")
    : null;

  return (
    <div className={cn(surfaceRoleClassName({ role: "hero", tone: "neutral" }, cn("oggi-dossier-shell p-4 sm:p-5", className)), "oggi-lift", glowClass)}>
      <div className="space-y-4">

        {/* HEADER: Ring + Nome + Status */}
        <div className="flex items-start gap-3">
          {session.readiness_score !== null && (
            <div className={surfaceRoleClassName({ role: "signal", tone: readinessTone }, "flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-xl")}>
              <ReadinessRing score={session.readiness_score} size={40} />
            </div>
          )}
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[9px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                Focus attivo
              </span>
              <span className={surfaceChipClassName({ tone: timingTone }, "px-2 py-0.5 text-[10px] font-bold")}>
                {timingLabel}
              </span>
              <span className={cn(surfaceChipClassName({ tone: statusTone, emphasis: "strong" }, "text-[9px] font-bold uppercase tracking-[0.1em]"), meta.color)}>
                {meta.label}
              </span>
            </div>
            <h2 className="mt-1 text-[1.7rem] font-black tracking-tight text-foreground leading-none">
              {session.client_name}
            </h2>
            {contextParts.length > 0 && (
              <p className="mt-1 text-[11px] text-muted-foreground">{contextParts.join(" · ")}</p>
            )}
          </div>
        </div>

        {/* STAT CHIPS */}
        <div className="flex flex-wrap gap-1.5">
          {chips.map((chip) => (
            <span key={chip.label} className={surfaceChipClassName({ tone: chip.tone }, "px-2.5 py-1.5 text-[10px] font-semibold")}>
              <span className="text-muted-foreground">{chip.label}</span>
              <span className="ml-1.5 font-bold text-foreground">{chip.value}</span>
            </span>
          ))}
        </div>

        {/* ALERT BLOCK */}
        {primaryAlert ? (
          <div className={surfaceRoleClassName({ role: "signal", tone: primaryAlert.critical ? "red" : "amber" }, "px-4 py-3.5")}>
            <div className="flex items-start gap-2.5">
              <CircleAlert className={cn("mt-0.5 h-4 w-4 shrink-0", primaryAlert.critical ? "text-red-600 dark:text-red-400" : "text-amber-600 dark:text-amber-400")} />
              <div className="min-w-0">
                <p className="text-[13px] font-bold text-foreground">{primaryAlert.title}</p>
                <p className="mt-0.5 text-[11px] leading-5 text-muted-foreground">{primaryAlert.detail}</p>
                {secondaryAlerts.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {secondaryAlerts.map((a, i) => (
                      <span key={i} className={surfaceChipClassName({ tone: a.critical ? "red" : "amber" }, "px-2 py-0.5 text-[9.5px] font-semibold")}>
                        {a.title}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className={surfaceRoleClassName({ role: "signal", tone: "teal" }, "px-4 py-3")}>
            <p className="text-[12px] font-bold text-emerald-700 dark:text-emerald-300">Seduta pronta</p>
            <p className="mt-0.5 text-[11px] text-muted-foreground/80">Nessun blocco clinico-operativo immediato.</p>
          </div>
        )}

        {/* NOTE */}
        <PrepNotes key={session.event_id} eventId={session.event_id} />

        {/* AZIONI */}
        <div className="flex flex-wrap gap-2">
          <Button asChild size="sm" className="h-8 rounded-full px-3.5 text-[12px] font-semibold">
            <Link href={profileHref}>Profilo <ArrowRight className="h-3.5 w-3.5" /></Link>
          </Button>
          {planHref && (
            <Button asChild variant="outline" size="sm" className="h-8 rounded-full px-3.5 text-[12px] font-semibold">
              <Link href={planHref}>Scheda attiva <ArrowRight className="h-3.5 w-3.5" /></Link>
            </Button>
          )}
          <Button asChild variant="ghost" size="sm" className="h-8 rounded-full px-3.5 text-[12px] font-semibold text-muted-foreground">
            <Link href="/agenda">Agenda</Link>
          </Button>
        </div>

      </div>
    </div>
  );
}
