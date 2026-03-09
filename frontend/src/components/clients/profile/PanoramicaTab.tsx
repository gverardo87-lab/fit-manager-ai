// src/components/clients/profile/PanoramicaTab.tsx
"use client";

/**
 * Panoramica — Client Journey Hub.
 *
 * 3 sezioni:
 * 1. Path Bar — barra segmentata stile Salesforce (status, non tutorial)
 * 2. Accesso Rapido — 3 card navigazione (Portale, Progressi, Anamnesi)
 * 3. Dettagli Personali — info anagrafiche + note interne
 */

import Link from "next/link";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import {
  FileText, HeartPulse, Ruler, Dumbbell, Calendar,
  Check, ArrowRight, ClipboardList, TrendingUp,
  AlertTriangle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ALERT_SEVERITY_STYLES, buildReadinessAlerts } from "@/lib/client-alerts";
import type { ClientAlert } from "@/lib/client-alerts";
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
  icon: LucideIcon;
  getCompleted: (props: PanoramicaTabProps) => boolean;
  getAction: (props: PanoramicaTabProps) => { type: "link"; href: string } | { type: "tab"; tab: string };
}

const JOURNEY_PHASES: JourneyPhase[] = [
  {
    key: "contratto",
    label: "Contratto",
    icon: FileText,
    getCompleted: (p) => p.hasContracts,
    getAction: () => ({ type: "tab", tab: "contratti" }),
  },
  {
    key: "anamnesi",
    label: "Anamnesi",
    icon: HeartPulse,
    getCompleted: (p) => p.readiness?.anamnesi_state === "structured",
    getAction: (p) => ({ type: "link", href: `/clienti/${p.clientId}/anamnesi?from=clienti-${p.clientId}` }),
  },
  {
    key: "misurazioni",
    label: "Misurazioni",
    icon: Ruler,
    getCompleted: (p) => p.readiness?.has_measurements ?? false,
    getAction: (p) => ({ type: "link", href: `/clienti/${p.clientId}/progressi?from=clienti-${p.clientId}` }),
  },
  {
    key: "scheda",
    label: "Scheda",
    icon: Dumbbell,
    getCompleted: (p) => p.readiness?.has_workout_plan ?? false,
    getAction: () => ({ type: "tab", tab: "schede" }),
  },
  {
    key: "sessione",
    label: "Sessioni",
    icon: Calendar,
    getCompleted: (p) => p.hasEvents,
    getAction: (p) => ({ type: "link", href: `/agenda?newEvent=1&clientId=${p.clientId}` }),
  },
];

const QUICK_ACCESS = [
  {
    key: "portale",
    href: (id: number) => `/monitoraggio/${id}?from=clienti-${id}`,
    icon: ClipboardList,
    label: "Portale Clinico",
    description: "Panoramica 360° con tracking completo",
    borderClass: "border-l-violet-500",
    bgClass: "bg-violet-100 dark:bg-violet-900/30",
    iconClass: "text-violet-600 dark:text-violet-400",
  },
  {
    key: "progressi",
    href: (id: number) => `/clienti/${id}/progressi?from=clienti-${id}`,
    icon: TrendingUp,
    label: "Progressi Fisici",
    description: "Misurazioni, obiettivi e analisi clinica",
    borderClass: "border-l-teal-500",
    bgClass: "bg-teal-100 dark:bg-teal-900/30",
    iconClass: "text-teal-600 dark:text-teal-400",
  },
  {
    key: "anamnesi",
    href: (id: number) => `/clienti/${id}/anamnesi?from=clienti-${id}`,
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
  const allDone = completedCount === JOURNEY_PHASES.length;
  const activeAlerts: ClientAlert[] = buildReadinessAlerts(props.readiness);

  return (
    <div className="space-y-5">
      {/* ── Alert Banners (scheda age + measurement gap) ── */}
      {activeAlerts.length > 0 && (
        <div className="space-y-2">
          {activeAlerts.map((alert) => (
            <AlertBanner key={alert.type} alert={alert} />
          ))}
        </div>
      )}

      {/* ── Sezione 1: Path Bar (Salesforce-style) ── */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">Percorso</CardTitle>
            {allDone ? (
              <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                Profilo completo
              </span>
            ) : (
              <span className="text-xs font-semibold tabular-nums text-muted-foreground">
                {completedCount}/{JOURNEY_PHASES.length}
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent className="pb-4">
          <PathBar phases={JOURNEY_PHASES} tabProps={props} onTabChange={onTabChange} />
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
// PATH BAR — Salesforce Lightning-style segmented bar
// ════════════════════════════════════════════════════════════

function PathBar({
  phases,
  tabProps,
  onTabChange,
}: {
  phases: JourneyPhase[];
  tabProps: PanoramicaTabProps;
  onTabChange: (tab: string) => void;
}) {
  // Find first incomplete phase index
  const firstIncompleteIdx = phases.findIndex((p) => !p.getCompleted(tabProps));

  return (
    <div className="flex flex-col gap-1.5 sm:flex-row sm:gap-0">
      {phases.map((phase, idx) => {
        const done = phase.getCompleted(tabProps);
        const isNext = idx === firstIncompleteIdx;
        const isFuture = !done && !isNext;
        const action = phase.getAction(tabProps);
        const Icon = phase.icon;
        const isFirst = idx === 0;
        const isLast = idx === phases.length - 1;

        const content = (
          <div
            className={`
              flex items-center gap-2 px-3 py-2 text-xs font-medium transition-colors
              sm:flex-1 sm:justify-center
              ${isFirst ? "sm:rounded-l-lg" : ""} ${isLast ? "sm:rounded-r-lg" : ""}
              rounded-md sm:rounded-none
              ${done
                ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400"
                : isNext
                  ? "bg-primary/10 text-primary ring-1 ring-inset ring-primary/20"
                  : "bg-muted/40 text-muted-foreground"
              }
              ${isFuture ? "" : "cursor-pointer hover:brightness-95 dark:hover:brightness-110"}
            `}
          >
            {done ? (
              <Check className="h-3.5 w-3.5 shrink-0" />
            ) : (
              <Icon className="h-3.5 w-3.5 shrink-0" />
            )}
            <span className={done ? "" : isNext ? "font-semibold" : ""}>
              {phase.label}
            </span>
          </div>
        );

        if (isFuture) {
          return <div key={phase.key} className="sm:flex-1">{content}</div>;
        }

        if (action.type === "tab") {
          return (
            <button
              key={phase.key}
              type="button"
              onClick={() => onTabChange(action.tab)}
              className="text-left sm:flex-1"
            >
              {content}
            </button>
          );
        }

        return (
          <Link key={phase.key} href={action.href} className="sm:flex-1">
            {content}
          </Link>
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// ALERT BANNER — scheda age / measurement gap
// ════════════════════════════════════════════════════════════

function AlertBanner({ alert }: { alert: ClientAlert }) {
  const styles = ALERT_SEVERITY_STYLES[alert.severity as "warning" | "critical"];

  return (
    <Link href={alert.href}>
      <div
        className={`flex items-center gap-3 rounded-lg border-l-[3px] ${styles.border} ${styles.bg} px-4 py-3 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md`}
      >
        <AlertTriangle className={`h-4 w-4 shrink-0 ${styles.icon}`} />
        <div className="min-w-0 flex-1">
          <p className={`text-sm font-semibold ${styles.text}`}>{alert.label}</p>
        </div>
        <span className={`shrink-0 text-xs font-semibold ${styles.text}`}>
          {alert.cta} →
        </span>
      </div>
    </Link>
  );
}
