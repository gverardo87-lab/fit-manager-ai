"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, CircleAlert, FileText, NotebookPen, Stethoscope } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ReadinessRing } from "@/components/ui/readiness-ring";
import { SemaphoreDot } from "@/components/ui/semaphore-dot";
import {
  surfaceChipClassName,
  surfaceRoleClassName,
  type SurfaceTone,
} from "@/components/ui/surface-role";
import { Textarea } from "@/components/ui/textarea";
import { AvatarBriefing } from "@/components/workspace/AvatarBriefing";
import { appendFromParam } from "@/lib/url-state";
import { cn } from "@/lib/utils";
import type { ClientAvatar, SessionPrepItem } from "@/types/api";
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
  const [note, setNote] = useState("");

  useEffect(() => {
    setNote(loadNote(eventId));
  }, [eventId]);

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

// ── OggiCommandCenter ─────────────────────────────────────────────

interface OggiCommandCenterProps {
  session: SessionPrepItem | null;
  status: PreFlightStatus;
  avatar: ClientAvatar | null;
  className?: string;
}

export function OggiCommandCenter({ session, status, avatar, className }: OggiCommandCenterProps) {
  const [clockMs, setClockMs] = useState(0);

  useEffect(() => {
    setClockMs(Date.now());
    const id = window.setInterval(() => setClockMs(Date.now()), 15_000);
    return () => window.clearInterval(id);
  }, []);

  // ── Empty state ──
  if (!session) {
    return (
      <div className={cn(surfaceRoleClassName({ role: "hero", tone: "neutral" }, cn("oggi-dossier-shell flex items-center justify-center px-8 py-14 text-center", className)), "oggi-lift oggi-glow-neutral")}>
        <div className="max-w-xs">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-muted/30">
            <Stethoscope className="h-7 w-7 text-muted-foreground/40" />
          </div>
          <p className="mt-4 text-[14px] font-bold text-muted-foreground">Nessuna seduta in focus</p>
          <p className="mt-1.5 text-[11.5px] leading-5 text-muted-foreground/60">
            Seleziona una seduta dalla timeline per aprire il contesto pre-seduta.
          </p>
        </div>
      </div>
    );
  }

  // ── Slot interno (no cliente) ──
  if (!session.client_id) {
    return (
      <div className={cn(surfaceRoleClassName({ role: "hero", tone: "neutral" }, cn("oggi-dossier-shell oggi-dossier-enter p-5 sm:p-6", className)), "oggi-lift oggi-glow-neutral")}>
        <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-muted-foreground">Slot interno</p>
        <h2 className="mt-2 text-[22px] font-extrabold tracking-tight text-foreground">
          {session.event_title ?? session.category}
        </h2>
        {session.event_notes && (
          <div className={surfaceRoleClassName({ role: "context", tone: "neutral" }, "oggi-notes-shell mt-4 px-3.5 py-3")}>
            <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
              <FileText className="h-3 w-3" />
              Note evento
            </div>
            <p className="mt-2.5 text-[12px] leading-5 text-foreground/80">{session.event_notes}</p>
          </div>
        )}
        <Button asChild size="sm" className="mt-5 h-9 rounded-full px-4 text-[12px] font-semibold">
          <Link href="/agenda">Apri agenda <ArrowRight className="ml-1 h-3.5 w-3.5" /></Link>
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

  // Chips statistiche — enriched con avatar semaphores se disponibili
  const anamnesiCheck = session.health_checks.find((c) => c.domain === "anamnesi");
  const creditsRem = avatar ? avatar.contract.credits_remaining : session.contract_credits_remaining;
  const creditsTotal = avatar ? avatar.contract.credits_total : session.contract_credits_total;

  const chips: { label: string; value: string; tone: SurfaceTone; semaphore?: "green" | "amber" | "red" }[] = avatar
    ? [
        {
          label: "Clinica",
          value: avatar.clinical.anamnesi_state === "structured" ? "Completa" : avatar.clinical.anamnesi_state === "legacy" ? "Legacy" : "Mancante",
          tone: avatar.clinical.status === "red" ? "red" : avatar.clinical.status === "amber" ? "amber" : "neutral",
          semaphore: avatar.clinical.status,
        },
        {
          label: "Contratto",
          value: !avatar.contract.has_active_contract ? "Assente" : avatar.contract.credits_remaining <= 0 ? "Esaurito" : `${avatar.contract.credits_remaining}/${avatar.contract.credits_total}`,
          tone: avatar.contract.status === "red" ? "red" : avatar.contract.status === "amber" ? "amber" : "neutral",
          semaphore: avatar.contract.status,
        },
        {
          label: "Allenamento",
          value: avatar.training.has_active_plan ? (avatar.training.active_plan_name && avatar.training.active_plan_name.length > 12 ? avatar.training.active_plan_name.slice(0, 10) + "…" : avatar.training.active_plan_name ?? "Attivo") : "Nessuna",
          tone: avatar.training.status === "red" ? "red" : avatar.training.status === "amber" ? "amber" : "neutral",
          semaphore: avatar.training.status,
        },
        {
          label: "Corpo",
          value: avatar.body_goals.has_measurements ? (avatar.body_goals.active_goals > 0 ? `${avatar.body_goals.active_goals} obiettivi` : "Misurato") : "Mancante",
          tone: avatar.body_goals.status === "red" ? "red" : avatar.body_goals.status === "amber" ? "amber" : "neutral",
          semaphore: avatar.body_goals.status,
        },
      ]
    : [
        {
          label: "Sedute",
          value: creditsRem !== null && creditsTotal !== null ? `${creditsRem}/${creditsTotal}` : "n/d",
          tone: (creditsRem !== null && creditsRem <= 0 ? "red" : creditsRem !== null && creditsRem <= 2 ? "amber" : "neutral") as SurfaceTone,
        },
        {
          label: "Profilo",
          value: anamnesiCheck?.status === "ok" ? "Completo" : "Incompleto",
          tone: (anamnesiCheck?.status === "ok" ? "neutral" : "amber") as SurfaceTone,
        },
        {
          label: "Scheda",
          value: session.active_plan_name ? (session.active_plan_name.length > 14 ? session.active_plan_name.slice(0, 12) + "…" : session.active_plan_name) : "Nessuna",
          tone: (session.active_plan_name ? "neutral" : "amber") as SurfaceTone,
        },
        {
          label: "Contratto",
          value: creditsRem !== null && creditsRem <= 0 ? "Esaurito" : session.contract_expiring_days !== null && session.contract_expiring_days <= 14 ? "In scadenza" : "Ok",
          tone: (creditsRem !== null && creditsRem <= 0 ? "red" : session.contract_expiring_days !== null && session.contract_expiring_days <= 14 ? "amber" : "neutral") as SurfaceTone,
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
    <div className={cn(surfaceRoleClassName({ role: "hero", tone: "neutral" }, cn("oggi-dossier-shell oggi-scrollbar p-5 sm:p-6", className)), "oggi-lift oggi-dossier-enter", glowClass)}>
      <div className="space-y-5" role="region" aria-label={`Focus seduta: ${session.client_name ?? "Slot"}`}>

        {/* HEADER: Ring + Nome + Status */}
        <div className="flex items-start gap-4">
          {session.readiness_score !== null && (
            <div className="oggi-readiness-halo" data-tone={readinessTone === "teal" ? "teal" : readinessTone === "red" ? "red" : "amber"}>
              <div className={surfaceRoleClassName({ role: "signal", tone: readinessTone }, "oggi-dossier-glass flex h-[68px] w-[68px] shrink-0 items-center justify-center rounded-2xl")}>
                <ReadinessRing score={session.readiness_score} size={54} />
              </div>
            </div>
          )}
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[9px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                Focus attivo
              </span>
              <span className={surfaceChipClassName({ tone: timingTone }, "px-2.5 py-0.5 text-[10px] font-bold")}>
                {timingLabel}
              </span>
              <span className={cn(surfaceChipClassName({ tone: statusTone, emphasis: "strong" }, "text-[9px] font-bold uppercase tracking-[0.1em]"), meta.color)}>
                {meta.label}
              </span>
            </div>
            <h2 className="mt-1.5 text-[1.8rem] font-black tracking-tight text-foreground leading-none sm:text-[2rem]">
              {session.client_name}
            </h2>
            {contextParts.length > 0 && (
              <p className="mt-1.5 flex items-center gap-1.5 text-[11px] text-muted-foreground">
                {contextParts.map((part, i) => (
                  <span key={i} className="flex items-center gap-1.5">
                    {i > 0 && <span className="h-0.5 w-0.5 rounded-full bg-current opacity-30" />}
                    {part}
                  </span>
                ))}
              </p>
            )}
          </div>
        </div>

        {/* BRIEFING NARRATIVO (se avatar disponibile) */}
        {avatar ? <AvatarBriefing avatar={avatar} /> : null}

        {/* STAT CHIPS — grid 2x2 */}
        <div className="grid grid-cols-2 gap-2">
          {chips.map((chip) => (
            <span key={chip.label} className={surfaceChipClassName({ tone: chip.tone }, "flex items-center justify-between px-3 py-2.5 text-[10.5px] font-semibold transition-colors duration-200")}>
              <span className="flex items-center gap-1.5 text-muted-foreground/70">
                {chip.semaphore ? <SemaphoreDot status={chip.semaphore} /> : null}
                {chip.label}
              </span>
              <span className="font-bold text-foreground">{chip.value}</span>
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
          <div className={surfaceRoleClassName({ role: "signal", tone: "teal" }, "px-4 py-4")}>
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500/10 dark:bg-emerald-400/10">
                <span className="oggi-clear-dot h-2.5 w-2.5 rounded-full bg-emerald-500 dark:bg-emerald-400" />
              </span>
              <div>
                <p className="text-[13px] font-bold text-emerald-700 dark:text-emerald-300">Seduta pronta</p>
                <p className="mt-0.5 text-[11px] leading-5 text-muted-foreground/70">Nessun blocco clinico-operativo immediato.</p>
              </div>
            </div>
          </div>
        )}

        {/* AVATAR HIGHLIGHTS — clickabili con cta_href */}
        {avatar && avatar.highlights.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {avatar.highlights.map((h) => {
              const tone: SurfaceTone = h.severity === "critical" ? "red" : h.severity === "warning" ? "amber" : "neutral";
              if (h.cta_href) {
                return (
                  <Link
                    key={h.code}
                    href={h.cta_href}
                    className={surfaceChipClassName(
                      { tone },
                      "px-2.5 py-1 text-[10px] font-semibold transition-colors hover:ring-1 hover:ring-ring/20",
                    )}
                  >
                    {h.text}
                  </Link>
                );
              }
              return (
                <span
                  key={h.code}
                  className={surfaceChipClassName(
                    { tone },
                    "px-2.5 py-1 text-[10px] font-semibold",
                  )}
                >
                  {h.text}
                </span>
              );
            })}
          </div>
        ) : null}

        {/* NOTE */}
        <PrepNotes key={session.event_id} eventId={session.event_id} />

        {/* AZIONI */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <Button asChild size="sm" className="h-9 rounded-full px-4 text-[12px] font-bold shadow-sm transition-shadow hover:shadow-md">
            <Link href={profileHref}>Profilo <ArrowRight className="ml-1 h-3.5 w-3.5" /></Link>
          </Button>
          {planHref && (
            <Button asChild variant="outline" size="sm" className="h-9 rounded-full px-4 text-[12px] font-bold transition-colors">
              <Link href={planHref}>Scheda attiva <ArrowRight className="ml-1 h-3.5 w-3.5" /></Link>
            </Button>
          )}
          <Button asChild variant="ghost" size="sm" className="h-9 rounded-full px-4 text-[12px] font-semibold text-muted-foreground transition-colors hover:text-foreground">
            <Link href="/agenda">Agenda</Link>
          </Button>
        </div>

      </div>
    </div>
  );
}
