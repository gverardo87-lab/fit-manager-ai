"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, ChevronDown, ChevronUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  surfaceChipClassName,
  surfaceRoleClassName,
} from "@/components/ui/surface-role";
import { appendFromParam } from "@/lib/url-state";
import { cn } from "@/lib/utils";
import type { SessionPrepItem } from "@/types/api";
import { getPreFlightStatus, PREFLIGHT_META } from "@/components/workspace/OggiTimeline";

// ── Soglie configurabili — mai magic numbers inline ──────────────────────
const CREDITS_CRITICAL_THRESHOLD = 2;    // ≤N crediti residui → segnala "in esaurimento"
const CONTRACT_EXPIRY_URGENT_DAYS = 7;   // ≤N giorni alla scadenza → urgente
const CONTRACT_EXPIRY_WARNING_DAYS = 14; // ≤N giorni alla scadenza → avviso
const CONTRACT_EXPIRY_VISIBLE_DAYS = 30; // >N giorni → non mostrare la riga scadenza
const SESSION_GAP_NOTABLE_DAYS = 10;     // ≥N giorni senza seduta → mostrare
const CLIENT_SENIORITY_NEW_MONTHS = 3;   // ≤N mesi → "cliente recente"

// ── Formatter ─────────────────────────────────────────────────────────────
const TIME_FMT = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });

// ── Helpers puri ──────────────────────────────────────────────────────────

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

// ── Derivazione chip info (tutti neutrali — il colore vive nel status badge) ──
function buildChips(session: SessionPrepItem): { label: string; value: string }[] {
  const anamnesi = session.health_checks.find((c) => c.domain === "anamnesi");

  const contractValue = (() => {
    if (session.contract_credits_remaining === null) return "n/d";
    if (session.contract_credits_remaining <= 0) return "Scaduto";
    if (session.contract_credits_remaining <= CREDITS_CRITICAL_THRESHOLD) return "In esaurimento";
    const exp = session.contract_expiring_days;
    if (exp !== null && exp <= CONTRACT_EXPIRY_WARNING_DAYS) return "In scadenza";
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
          ? `${session.active_plan_name.slice(0, 12)}…`
          : session.active_plan_name
        : "Nessuna",
    },
    { label: "Contratto", value: contractValue },
  ];
}

// ── Componente principale ─────────────────────────────────────────────────

interface OggiPreSessionCardProps {
  session: SessionPrepItem;
  className?: string;
}

export function OggiPreSessionCard({ session, className }: OggiPreSessionCardProps) {
  const [clinicOpen, setClinicOpen] = useState(false);

  // Un solo segnale cromatico — coerente con SessionCard in OggiTimeline
  const status = getPreFlightStatus(session);
  const meta = PREFLIGHT_META[status];

  const chips = useMemo(() => buildChips(session), [session]);

  // Contesto relativo: testo colorato, nessuna superficie colorata
  const contextLines = useMemo(() => {
    const lines: { text: string; tone: "neutral" | "amber" | "red" }[] = [];

    const seniority = formatSeniority(session.client_since);
    if (seniority) lines.push({ text: seniority, tone: "neutral" });

    const expiryText = formatExpiryUrgency(session.contract_expiring_days ?? null);
    if (expiryText) {
      const isUrgent =
        session.contract_expiring_days !== null &&
        session.contract_expiring_days <= CONTRACT_EXPIRY_URGENT_DAYS;
      lines.push({ text: expiryText, tone: isUrgent ? "red" : "amber" });
    }

    if (
      session.days_since_last_session !== null &&
      session.days_since_last_session >= SESSION_GAP_NOTABLE_DAYS
    ) {
      lines.push({
        text: `Non si allena da ${session.days_since_last_session} giorni`,
        tone: "amber",
      });
    }

    return lines;
  }, [session]);

  const profileHref = appendFromParam(`/clienti/${session.client_id}`, "oggi");
  const planHref = session.active_plan_name
    ? appendFromParam(`/allenamenti?idCliente=${session.client_id}`, "oggi")
    : null;

  const hasClinicDetail =
    session.clinical_alerts.length > 0 ||
    session.health_checks.some((c) => c.status !== "ok");

  return (
    <div className={surfaceRoleClassName({ role: "hero", tone: "neutral" }, cn("p-4 sm:p-5", className))}>

      {/* Header: nome + ora + unico badge stato */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-stone-400 dark:text-zinc-500">
            Prossima seduta
          </p>
          <h2 className="mt-1 truncate text-[20px] font-extrabold tracking-tight text-stone-900 dark:text-zinc-50">
            {session.client_name}
          </h2>
          <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[10px] text-stone-500 dark:text-zinc-400">
            {session.client_age !== null && <span>{session.client_age} anni</span>}
            {session.client_sex && <span>{session.client_sex}</span>}
            {session.is_new_client && (
              <span className={surfaceChipClassName({ tone: "amber" }, "px-2 py-0.5 text-[9px] font-bold")}>
                nuovo
              </span>
            )}
          </div>
        </div>

        {/* Colonna destra: ora + un badge stato (come SessionCard in OggiTimeline) */}
        <div className="flex shrink-0 flex-col items-end gap-1.5">
          <span
            className={surfaceChipClassName(
              { tone: "neutral" },
              "px-2.5 py-1.5 text-[13px] font-bold tabular-nums",
            )}
          >
            {TIME_FMT.format(new Date(session.starts_at))}
          </span>
          <span
            className={cn(
              surfaceChipClassName(
                { tone: "neutral" },
                "px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.12em]",
              ),
              meta.color,
            )}
          >
            {meta.label}
          </span>
        </div>
      </div>

      {/* Level 1: 4 chip informativi — superficie uniforme neutral, valori parlanti */}
      <div className="mt-3.5 grid grid-cols-4 gap-1.5">
        {chips.map((chip) => (
          <div
            key={chip.label}
            className={surfaceRoleClassName({ role: "signal", tone: "neutral" }, "px-2.5 py-2")}
          >
            <p className="truncate text-[8.5px] font-bold uppercase tracking-[0.12em] text-stone-400 dark:text-zinc-500">
              {chip.label}
            </p>
            <p className="mt-0.5 truncate text-[11px] font-bold leading-4 text-stone-800 dark:text-zinc-100">
              {chip.value}
            </p>
          </div>
        ))}
      </div>

      {/* Level 2: contesto relativo — testo colorato, zero superfici colorate */}
      {contextLines.length > 0 && (
        <div className="mt-2.5 space-y-0.5">
          {contextLines.map((line, i) => (
            <p
              key={i}
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

      {/* Level 3: navigazione + toggle clinico */}
      <div className="mt-4 flex flex-wrap items-center gap-2.5">
        <Button asChild size="sm" className="h-8 rounded-full px-3.5 text-[12px] font-bold">
          <Link href={profileHref}>
            Profilo completo
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Button>

        {planHref && (
          <Button
            asChild
            size="sm"
            variant="outline"
            className="h-8 rounded-full px-3.5 text-[12px] font-bold"
          >
            <Link href={planHref}>
              Scheda attiva
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        )}

        {hasClinicDetail && (
          <button
            type="button"
            onClick={() => setClinicOpen((prev) => !prev)}
            className="ml-auto flex items-center gap-1 text-[11px] font-semibold text-stone-400 transition-colors hover:text-stone-700 dark:text-zinc-500 dark:hover:text-zinc-200"
          >
            Clinico
            {clinicOpen ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
          </button>
        )}
      </div>

      {/* Level 3 espanso — solo su richiesta esplicita */}
      {clinicOpen && hasClinicDetail && (
        <div className="mt-3.5 space-y-2 border-t border-stone-200/60 pt-3.5 dark:border-white/10">
          {session.clinical_alerts.length > 0 && (
            <div className={surfaceRoleClassName({ role: "signal", tone: "red" }, "px-3 py-2.5")}>
              <p className="mb-1.5 text-[9px] font-bold uppercase tracking-[0.14em] text-stone-400 dark:text-zinc-500">
                Alert clinici
              </p>
              {session.clinical_alerts.map((alert, i) => (
                <p key={i} className="text-[11px] leading-5 text-stone-700 dark:text-zinc-300">
                  {alert.condition_name}
                  {alert.category && (
                    <span className="text-stone-400 dark:text-zinc-500"> · {alert.category}</span>
                  )}
                </p>
              ))}
            </div>
          )}
          {session.health_checks
            .filter((c) => c.status !== "ok")
            .map((check, i) => (
              <div
                key={i}
                className={surfaceRoleClassName(
                  { role: "signal", tone: check.status === "critical" ? "red" : "amber" },
                  "px-3 py-2",
                )}
              >
                <p className="text-[11px] text-stone-800 dark:text-zinc-200">
                  <span className="font-semibold">{check.label}:</span>{" "}
                  <span>{check.detail}</span>
                </p>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
