// src/components/clients/AvatarHero.tsx
"use client";

/**
 * AvatarHero — header avatar-powered per il profilo cliente.
 *
 * Sostituisce ClientProfileHeader + ClientProfileKpi con una vista
 * che mostra il cliente come lo vede il trainer: readiness, semafori
 * dimensionali, highlight actionable.
 */

import Link from "next/link";
import {
  ArrowLeft,
  Mail,
  Phone,
  Pencil,
  Activity,
  FileText,
  Heart,
  Target,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ReadinessRing } from "@/components/ui/readiness-ring";
import { Skeleton } from "@/components/ui/skeleton";
import { SemaphoreDot } from "@/components/ui/semaphore-dot";
import {
  surfaceChipClassName,
  surfaceRoleClassName,
  type SurfaceTone,
} from "@/components/ui/surface-role";
import { cn } from "@/lib/utils";
import type { ClientAvatar, ClientEnriched, SemaphoreStatus } from "@/types/api";

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

function semaphoreToTone(status: SemaphoreStatus): SurfaceTone {
  if (status === "red") return "red";
  if (status === "amber") return "amber";
  return "neutral";
}

// ── Dimension chip data ──────────────────────────────────────────

interface DimensionChip {
  key: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  tone: SurfaceTone;
  semaphore: SemaphoreStatus;
  tabTarget?: string;
}

function buildDimensionChips(avatar: ClientAvatar): DimensionChip[] {
  const { clinical, contract, training, body_goals } = avatar;

  return [
    {
      key: "clinical",
      icon: Heart,
      label: "Clinica",
      value:
        clinical.anamnesi_state === "structured"
          ? "Completa"
          : clinical.anamnesi_state === "legacy"
            ? "Legacy"
            : "Mancante",
      tone: semaphoreToTone(clinical.status),
      semaphore: clinical.status,
      tabTarget: "panoramica",
    },
    {
      key: "contract",
      icon: FileText,
      label: "Contratto",
      value: !contract.has_active_contract
        ? "Assente"
        : contract.credits_remaining <= 0
          ? "Esaurito"
          : `${contract.credits_remaining}/${contract.credits_total}`,
      tone: semaphoreToTone(contract.status),
      semaphore: contract.status,
      tabTarget: "contratti",
    },
    {
      key: "training",
      icon: Activity,
      label: "Allenamento",
      value: training.has_active_plan
        ? training.active_plan_name && training.active_plan_name.length > 12
          ? training.active_plan_name.slice(0, 10) + "\u2026"
          : training.active_plan_name ?? "Attivo"
        : "Nessuna",
      tone: semaphoreToTone(training.status),
      semaphore: training.status,
      tabTarget: "schede",
    },
    {
      key: "body",
      icon: Target,
      label: "Corpo",
      value: body_goals.has_measurements
        ? body_goals.active_goals > 0
          ? `${body_goals.active_goals} obiettivi`
          : "Misurato"
        : "Mancante",
      tone: semaphoreToTone(body_goals.status),
      semaphore: body_goals.status,
      tabTarget: "panoramica",
    },
  ];
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

  const contextParts: string[] = [];
  if (age !== null) contextParts.push(`${age} anni`);
  if (seniority) contextParts.push(seniority);
  if (client.stato) contextParts.push(client.stato);

  const chips = avatar ? buildDimensionChips(avatar) : null;

  return (
    <div className={surfaceRoleClassName({ role: "hero", tone: "neutral" }, "rounded-2xl p-5 sm:p-6")}>
      <div className="space-y-5">
        {/* ── HEADER ROW: Back + Ring + Identity + Edit ── */}
        <div className="flex items-start gap-3 sm:gap-4">
          <Link
            href={backHref}
            title={backLabel}
            className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border bg-background transition-colors hover:bg-accent"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>

          {/* Readiness ring or initials fallback */}
          {avatar ? (
            <div className="shrink-0">
              <div className={surfaceRoleClassName(
                { role: "signal", tone: avatar.readiness_score >= 80 ? "teal" : avatar.readiness_score >= 50 ? "amber" : "red" },
                "flex h-[68px] w-[68px] items-center justify-center rounded-2xl",
              )}>
                <ReadinessRing score={avatar.readiness_score} size={54} />
              </div>
            </div>
          ) : (
            <div className="flex h-[68px] w-[68px] shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-xl font-semibold text-primary">
              {isLoading ? (
                <Skeleton className="h-8 w-8 rounded-full" />
              ) : (
                `${client.cognome[0]}${client.nome[0]}`
              )}
            </div>
          )}

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight sm:text-2xl">
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
            </div>

            {/* Context line */}
            {contextParts.length > 0 && (
              <p className="mt-1 flex flex-wrap items-center gap-1.5 text-[12px] text-muted-foreground">
                {contextParts.map((part, i) => (
                  <span key={i} className="flex items-center gap-1.5">
                    {i > 0 && <span className="h-0.5 w-0.5 rounded-full bg-current opacity-30" />}
                    {part}
                  </span>
                ))}
              </p>
            )}

            {/* Contatti */}
            <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-muted-foreground">
              {client.email && (
                <span className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5" />
                  {client.email}
                </span>
              )}
              {client.telefono && (
                <span className="flex items-center gap-1.5">
                  <Phone className="h-3.5 w-3.5" />
                  {client.telefono}
                </span>
              )}
            </div>
          </div>

          {/* Edit button */}
          <Button variant="outline" size="sm" className="shrink-0" onClick={onEdit}>
            <Pencil className="mr-2 h-4 w-4" />
            <span className="hidden sm:inline">Modifica</span>
          </Button>
        </div>

        {/* ── DIMENSION CHIPS — 2x2 mobile, 4-col desktop ── */}
        {chips ? (
          <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
            {chips.map((chip) => (
              <button
                key={chip.key}
                type="button"
                onClick={() => { if (chip.tabTarget) onTabChange(chip.tabTarget); }}
                className={cn(
                  surfaceChipClassName({ tone: chip.tone }, "flex w-full items-center gap-2.5 px-3 py-2.5 text-left text-[11px] transition-colors duration-200"),
                  "cursor-pointer hover:ring-1 hover:ring-ring/20",
                )}
              >
                <SemaphoreDot status={chip.semaphore} />
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] text-muted-foreground/70">{chip.label}</p>
                  <p className="truncate font-bold text-foreground">{chip.value}</p>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className={surfaceChipClassName({ tone: "neutral" }, "px-3 py-2.5")}>
                <Skeleton className="mb-1 h-3 w-12" />
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
        )}

        {/* ── HIGHLIGHTS — actionable chips ── */}
        {avatar && avatar.highlights.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {avatar.highlights.map((h) => {
              const tone: SurfaceTone =
                h.severity === "critical" ? "red" : h.severity === "warning" ? "amber" : "neutral";

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
      </div>
    </div>
  );
}
