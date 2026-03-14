// src/components/clients/AvatarHero.tsx
"use client";

/**
 * AvatarHero — header avatar-powered per il profilo cliente.
 *
 * Design premium: gradient card con accento readiness, ring prominente,
 * chip dimensionali con icone colorate, highlights con peso visivo.
 */

import Link from "next/link";
import {
  ArrowLeft,
  Mail,
  Phone,
  Pencil,
  Activity,
  CircleAlert,
  FileText,
  Heart,
  Target,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ReadinessRing } from "@/components/ui/readiness-ring";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { ClientAvatar, ClientEnriched, AvatarHighlight, SemaphoreStatus } from "@/types/api";

// ── Helpers ──────────────────────────────────────────────────────

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

function computeAge(dataNascita: string | null): number | null {
  if (!dataNascita) return null;
  const birth = new Date(dataNascita);
  if (Number.isNaN(birth.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const m = now.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) age--;
  return age >= 0 ? age : null;
}

// ── Readiness-driven accent ──────────────────────────────────────

const READINESS_ACCENT = {
  good: {
    border: "border-l-emerald-500",
    gradient: "from-emerald-50/80 to-white dark:from-emerald-950/30 dark:to-zinc-900",
    ringBg: "bg-emerald-50 dark:bg-emerald-950/40",
  },
  medium: {
    border: "border-l-amber-500",
    gradient: "from-amber-50/60 to-white dark:from-amber-950/20 dark:to-zinc-900",
    ringBg: "bg-amber-50 dark:bg-amber-950/40",
  },
  low: {
    border: "border-l-red-500",
    gradient: "from-red-50/60 to-white dark:from-red-950/20 dark:to-zinc-900",
    ringBg: "bg-red-50 dark:bg-red-950/40",
  },
  loading: {
    border: "border-l-zinc-300 dark:border-l-zinc-600",
    gradient: "from-zinc-50/50 to-white dark:from-zinc-900/50 dark:to-zinc-900",
    ringBg: "bg-zinc-100 dark:bg-zinc-800",
  },
} as const;

function getAccent(score: number | null) {
  if (score === null) return READINESS_ACCENT.loading;
  if (score >= 80) return READINESS_ACCENT.good;
  if (score >= 50) return READINESS_ACCENT.medium;
  return READINESS_ACCENT.low;
}

// ── Dimension card styling ───────────────────────────────────────

const DIMENSION_STYLE: Record<SemaphoreStatus, { dot: string; bg: string; iconColor: string }> = {
  green: {
    dot: "bg-emerald-500",
    bg: "bg-emerald-50/80 border-emerald-200/60 dark:bg-emerald-950/30 dark:border-emerald-800/40",
    iconColor: "text-emerald-600 dark:text-emerald-400",
  },
  amber: {
    dot: "bg-amber-500",
    bg: "bg-amber-50/80 border-amber-200/60 dark:bg-amber-950/30 dark:border-amber-800/40",
    iconColor: "text-amber-600 dark:text-amber-400",
  },
  red: {
    dot: "bg-red-500",
    bg: "bg-red-50/80 border-red-200/60 dark:bg-red-950/30 dark:border-red-800/40",
    iconColor: "text-red-600 dark:text-red-400",
  },
};

interface DimensionDef {
  key: string;
  icon: typeof Heart;
  label: string;
  value: string;
  status: SemaphoreStatus;
  tabTarget: string;
}

function buildDimensions(avatar: ClientAvatar): DimensionDef[] {
  const { clinical, contract, training, body_goals } = avatar;
  return [
    {
      key: "clinical",
      icon: Heart,
      label: "Clinica",
      value: clinical.anamnesi_state === "structured" ? "Completa"
        : clinical.anamnesi_state === "legacy" ? "Legacy" : "Mancante",
      status: clinical.status,
      tabTarget: "panoramica",
    },
    {
      key: "contract",
      icon: FileText,
      label: "Contratto",
      value: !contract.has_active_contract ? "Assente"
        : contract.credits_remaining <= 0 ? "Esaurito"
          : `${contract.credits_remaining}/${contract.credits_total}`,
      status: contract.status,
      tabTarget: "contratti",
    },
    {
      key: "training",
      icon: Activity,
      label: "Allenamento",
      value: training.has_active_plan
        ? (training.active_plan_name && training.active_plan_name.length > 14
            ? training.active_plan_name.slice(0, 12) + "\u2026"
            : training.active_plan_name ?? "Attivo")
        : "Nessuna",
      status: training.status,
      tabTarget: "schede",
    },
    {
      key: "body",
      icon: Target,
      label: "Corpo",
      value: body_goals.has_measurements
        ? body_goals.active_goals > 0 ? `${body_goals.active_goals} obiettivi` : "Misurato"
        : "Mancante",
      status: body_goals.status,
      tabTarget: "panoramica",
    },
  ];
}

// ── Highlight rendering ──────────────────────────────────────────

function HighlightChip({ h }: { h: AvatarHighlight }) {
  const isCritical = h.severity === "critical";
  const isWarning = h.severity === "warning";

  const cls = cn(
    "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-semibold transition-colors",
    isCritical && "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
    isWarning && "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
    !isCritical && !isWarning && "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
    h.cta_href && "hover:ring-1 hover:ring-ring/30",
  );

  const content = (
    <>
      {(isCritical || isWarning) && (
        <CircleAlert className={cn("h-3.5 w-3.5 shrink-0", isCritical ? "text-red-500" : "text-amber-500")} />
      )}
      {h.text}
    </>
  );

  if (h.cta_href) {
    return <Link href={h.cta_href} className={cls}>{content}</Link>;
  }
  return <span className={cls}>{content}</span>;
}

// ── Props ────────────────────────────────────────────────────────

interface AvatarHeroProps {
  client: ClientEnriched;
  avatar: ClientAvatar | null;
  isLoading?: boolean;
  onEdit: () => void;
  onTabChange: (tab: string) => void;
  backHref?: string;
  backLabel?: string;
}

// ── Component ────────────────────────────────────────────────────

export function AvatarHero({
  client,
  avatar,
  isLoading,
  onEdit,
  onTabChange,
  backHref = "/clienti",
  backLabel = "Torna ai clienti",
}: AvatarHeroProps) {
  const age = avatar?.identity.age ?? computeAge(client.data_nascita);
  const seniority = formatSeniority(avatar?.identity.client_since ?? null);
  const accent = getAccent(avatar?.readiness_score ?? null);
  const dimensions = avatar ? buildDimensions(avatar) : null;

  const contextParts: string[] = [];
  if (age !== null) contextParts.push(`${age} anni`);
  if (seniority) contextParts.push(seniority);

  return (
    <div className="space-y-3">
      {/* ── Back nav ── */}
      <Link
        href={backHref}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        {backLabel}
      </Link>

      {/* ── Main card ── */}
      <div
        className={cn(
          "rounded-xl border border-l-4 bg-gradient-to-br p-5 shadow-sm sm:p-6",
          accent.border,
          accent.gradient,
        )}
      >
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:gap-6">
          {/* Ring — prominente */}
          <div className="flex flex-col items-center gap-1.5 sm:shrink-0">
            <div className={cn("flex h-24 w-24 items-center justify-center rounded-2xl", accent.ringBg)}>
              {avatar ? (
                <ReadinessRing score={avatar.readiness_score} size={80} />
              ) : isLoading ? (
                <Skeleton className="h-16 w-16 rounded-full" />
              ) : (
                <span className="text-2xl font-bold text-primary">
                  {client.cognome[0]}{client.nome[0]}
                </span>
              )}
            </div>
            {avatar ? (
              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                {avatar.readiness_score >= 80 ? "Pronto" : avatar.readiness_score >= 50 ? "Da verificare" : "Critico"}
              </span>
            ) : null}
          </div>

          {/* Identity + dimensions */}
          <div className="min-w-0 flex-1">
            {/* Name row */}
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight">
                {client.cognome} {client.nome}
              </h1>
              <Badge
                variant={client.stato === "Attivo" ? "default" : "secondary"}
                className={
                  client.stato === "Attivo"
                    ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400"
                    : ""
                }
              >
                {client.stato}
              </Badge>
              <Button variant="outline" size="sm" className="ml-auto shrink-0" onClick={onEdit}>
                <Pencil className="mr-2 h-3.5 w-3.5" />
                <span className="hidden sm:inline">Modifica</span>
              </Button>
            </div>

            {/* Context + contacts */}
            <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
              {contextParts.length > 0 && (
                <span>{contextParts.join(" · ")}</span>
              )}
              {client.email && (
                <span className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5" /> {client.email}
                </span>
              )}
              {client.telefono && (
                <span className="flex items-center gap-1.5">
                  <Phone className="h-3.5 w-3.5" /> {client.telefono}
                </span>
              )}
            </div>

            {/* ── Dimension cards — 2x2 mobile, 4-col desktop ── */}
            <div className="mt-4 grid grid-cols-2 gap-2 lg:grid-cols-4">
              {dimensions ? dimensions.map((dim) => {
                const style = DIMENSION_STYLE[dim.status];
                const Icon = dim.icon;
                return (
                  <button
                    key={dim.key}
                    type="button"
                    onClick={() => onTabChange(dim.tabTarget)}
                    className={cn(
                      "rounded-lg border px-3 py-2.5 text-left transition-all hover:shadow-sm",
                      style.bg,
                    )}
                  >
                    <div className="flex items-center gap-1.5">
                      <Icon className={cn("h-3.5 w-3.5", style.iconColor)} />
                      <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                        {dim.label}
                      </span>
                      <span className={cn("ml-auto h-2 w-2 rounded-full", style.dot)} />
                    </div>
                    <p className="mt-1 truncate text-[13px] font-bold leading-tight text-foreground">
                      {dim.value}
                    </p>
                  </button>
                );
              }) : Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="rounded-lg border bg-white/70 px-3 py-2.5 dark:bg-zinc-800/50">
                  <Skeleton className="mb-2 h-3 w-14" />
                  <Skeleton className="h-4 w-20" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Highlights — con peso visivo ── */}
        {avatar && avatar.highlights.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2 border-t border-border/40 pt-4">
            {avatar.highlights.map((h) => (
              <HighlightChip key={h.code} h={h} />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
