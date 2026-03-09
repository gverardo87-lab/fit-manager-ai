// src/components/clients/profile/PanoramicaTab.tsx
"use client";

/**
 * Panoramica — Client Journey Hub.
 *
 * 3 sezioni:
 * 1. "Il Percorso" — timeline visiva 5 fasi del ciclo professionale
 * 2. "Accesso Rapido" — 3 card navigazione (Portale, Progressi, Anamnesi)
 * 3. "Dettagli Personali" — info anagrafiche + note interne
 */

import Link from "next/link";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import {
  FileText, HeartPulse, Ruler, Dumbbell, Calendar,
  Check, ArrowRight, ClipboardList, TrendingUp,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { ClinicalReadinessClientItem } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

interface PanoramicaTabProps {
  client: {
    data_nascita: string | null;
    sesso: string | null;
    note_interne: string | null;
  };
  clientId: number;
  readiness: ClinicalReadinessClientItem | null;
  hasContracts: boolean;
  hasEvents: boolean;
  onTabChange: (tab: string) => void;
}

// ════════════════════════════════════════════════════════════
// JOURNEY CONFIG
// ════════════════════════════════════════════════════════════

interface JourneyPhase {
  key: string;
  label: string;
  description: string;
  icon: LucideIcon;
  color: { bg: string; text: string; border: string; ring: string };
  getCompleted: (props: PanoramicaTabProps) => boolean;
  getAction: (props: PanoramicaTabProps) => { type: "link"; href: string } | { type: "tab"; tab: string };
}

const JOURNEY_PHASES: JourneyPhase[] = [
  {
    key: "contratto",
    label: "Contratto",
    description: "Pacchetto e piano pagamento",
    icon: FileText,
    color: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-600 dark:text-blue-400", border: "border-blue-300 dark:border-blue-700", ring: "ring-blue-500" },
    getCompleted: (p) => p.hasContracts,
    getAction: (_p) => ({ type: "tab", tab: "contratti" }),
  },
  {
    key: "anamnesi",
    label: "Anamnesi",
    description: "Questionario clinico",
    icon: HeartPulse,
    color: { bg: "bg-rose-100 dark:bg-rose-900/30", text: "text-rose-600 dark:text-rose-400", border: "border-rose-300 dark:border-rose-700", ring: "ring-rose-500" },
    getCompleted: (p) => p.readiness?.anamnesi_state === "structured",
    getAction: (p) => ({ type: "link", href: `/clienti/${p.clientId}/anamnesi` }),
  },
  {
    key: "misurazioni",
    label: "Misurazioni",
    description: "Peso e composizione corporea",
    icon: Ruler,
    color: { bg: "bg-amber-100 dark:bg-amber-900/30", text: "text-amber-600 dark:text-amber-400", border: "border-amber-300 dark:border-amber-700", ring: "ring-amber-500" },
    getCompleted: (p) => p.readiness?.has_measurements ?? false,
    getAction: (p) => ({ type: "link", href: `/clienti/${p.clientId}/progressi` }),
  },
  {
    key: "scheda",
    label: "Scheda",
    description: "Programma allenamento",
    icon: Dumbbell,
    color: { bg: "bg-violet-100 dark:bg-violet-900/30", text: "text-violet-600 dark:text-violet-400", border: "border-violet-300 dark:border-violet-700", ring: "ring-violet-500" },
    getCompleted: (p) => p.readiness?.has_workout_plan ?? false,
    getAction: (_p) => ({ type: "tab", tab: "schede" }),
  },
  {
    key: "sessione",
    label: "Sessioni",
    description: "Appuntamenti in agenda",
    icon: Calendar,
    color: { bg: "bg-teal-100 dark:bg-teal-900/30", text: "text-teal-600 dark:text-teal-400", border: "border-teal-300 dark:border-teal-700", ring: "ring-teal-500" },
    getCompleted: (p) => p.hasEvents,
    getAction: (p) => ({ type: "link", href: `/agenda?newEvent=1&clientId=${p.clientId}` }),
  },
];

const QUICK_ACCESS = [
  {
    key: "portale",
    href: (id: number) => `/monitoraggio/${id}`,
    icon: ClipboardList,
    label: "Portale Clinico",
    description: "Panoramica 360° con tracking completo",
    borderClass: "border-l-violet-500",
    bgClass: "bg-violet-100 dark:bg-violet-900/30",
    iconClass: "text-violet-600 dark:text-violet-400",
  },
  {
    key: "progressi",
    href: (id: number) => `/clienti/${id}/progressi`,
    icon: TrendingUp,
    label: "Progressi Fisici",
    description: "Misurazioni, obiettivi e analisi clinica",
    borderClass: "border-l-teal-500",
    bgClass: "bg-teal-100 dark:bg-teal-900/30",
    iconClass: "text-teal-600 dark:text-teal-400",
  },
  {
    key: "anamnesi",
    href: (id: number) => `/clienti/${id}/anamnesi`,
    icon: HeartPulse,
    label: "Anamnesi",
    description: "Questionario clinico e stile di vita",
    borderClass: "border-l-rose-500",
    bgClass: "bg-rose-100 dark:bg-rose-900/30",
    iconClass: "text-rose-600 dark:text-rose-400",
  },
] as const;

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function PanoramicaTab(props: PanoramicaTabProps) {
  const { client, clientId, onTabChange } = props;
  const completedCount = JOURNEY_PHASES.filter((p) => p.getCompleted(props)).length;

  return (
    <div className="space-y-5">
      {/* ── Sezione 1: Il Percorso ── */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">
              Il Percorso del Cliente
            </CardTitle>
            <span className="text-xs font-semibold tabular-nums text-muted-foreground">
              {completedCount}/{JOURNEY_PHASES.length} completati
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            Ogni cliente attraversa 5 fasi. Clicca su uno step per procedere.
          </p>
        </CardHeader>
        <CardContent>
          <JourneyTimeline phases={JOURNEY_PHASES} tabProps={props} onTabChange={onTabChange} />
        </CardContent>
      </Card>

      {/* ── Sezione 2: Accesso Rapido ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {QUICK_ACCESS.map((card) => (
          <Link key={card.key} href={card.href(clientId)}>
            <Card className={`group cursor-pointer border-l-4 ${card.borderClass} transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg`}>
              <CardContent className="flex items-center gap-4 p-4">
                <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${card.bgClass}`}>
                  <card.icon className={`h-5 w-5 ${card.iconClass}`} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">{card.label}</p>
                  <p className="text-xs text-muted-foreground">{card.description}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* ── Sezione 3: Dettagli Personali ── */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Dettagli Personali</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Data di nascita</span>
            <span className="font-medium">
              {client.data_nascita
                ? format(new Date(client.data_nascita + "T00:00:00"), "dd MMMM yyyy", { locale: it })
                : "—"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Sesso</span>
            <span className="font-medium">{client.sesso ?? "—"}</span>
          </div>
          {client.note_interne && (
            <>
              <Separator />
              <div>
                <span className="text-xs font-medium text-muted-foreground">Note interne</span>
                <p className="mt-1 whitespace-pre-line">{client.note_interne}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// JOURNEY TIMELINE
// ════════════════════════════════════════════════════════════

function JourneyTimeline({
  phases,
  tabProps,
  onTabChange,
}: {
  phases: JourneyPhase[];
  tabProps: PanoramicaTabProps;
  onTabChange: (tab: string) => void;
}) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:gap-0">
      {phases.map((phase, idx) => {
        const done = phase.getCompleted(tabProps);
        const action = phase.getAction(tabProps);
        const isLast = idx === phases.length - 1;

        return (
          <div key={phase.key} className="flex items-center sm:flex-1 sm:flex-col">
            {/* Node + label */}
            <PhaseNode
              phase={phase}
              done={done}
              action={action}
              onTabChange={onTabChange}
            />
            {/* Connector line (not on last) */}
            {!isLast && (
              <div className="mx-2 h-px w-6 bg-border sm:mx-0 sm:mt-2 sm:h-px sm:w-full" />
            )}
          </div>
        );
      })}
    </div>
  );
}

function PhaseNode({
  phase,
  done,
  action,
  onTabChange,
}: {
  phase: JourneyPhase;
  done: boolean;
  action: { type: "link"; href: string } | { type: "tab"; tab: string };
  onTabChange: (tab: string) => void;
}) {
  const Icon = phase.icon;

  const content = (
    <div className="flex items-center gap-3 sm:flex-col sm:gap-1.5 sm:text-center">
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 transition-all duration-200 ${
          done
            ? "border-emerald-500 bg-emerald-100 dark:bg-emerald-900/30"
            : `${phase.color.border} ${phase.color.bg}`
        }`}
      >
        {done ? (
          <Check className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
        ) : (
          <Icon className={`h-5 w-5 ${phase.color.text}`} />
        )}
      </div>
      <div className="sm:max-w-[100px]">
        <p className={`text-xs font-semibold ${done ? "text-emerald-600 dark:text-emerald-400" : ""}`}>
          {phase.label}
        </p>
        <p className="hidden text-[10px] text-muted-foreground sm:block">
          {phase.description}
        </p>
      </div>
    </div>
  );

  const hoverClass = "group cursor-pointer rounded-lg p-1.5 transition-colors hover:bg-muted/50";

  if (action.type === "tab") {
    return (
      <button
        type="button"
        onClick={() => onTabChange(action.tab)}
        className={`${hoverClass} text-left`}
      >
        {content}
      </button>
    );
  }

  return (
    <Link href={action.href} className={hoverClass}>
      {content}
    </Link>
  );
}
