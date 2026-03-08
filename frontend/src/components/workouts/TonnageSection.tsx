// src/components/workouts/TonnageSection.tsx
"use client";

/**
 * Sezione 2.5: Profilo Volume-Load — Tonnellaggio e intensita'.
 *
 * Visibile SOLO quando almeno un esercizio ha carico_kg assegnato.
 * Mostra tonnellaggio per sessione, intensita' relativa, zona NSCA.
 *
 * Fonti: Haff & Triplett (NSCA 2016), Zourdos et al. 2016, McBride 2009.
 */

import { useState } from "react";
import { ChevronDown, Weight, Dumbbell } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { TSAnalisiTonnellaggio, TSTonnellaggioSlotAnalisi } from "@/types/api";

// ════════════════════════════════════════════════════════════
// PROPS
// ════════════════════════════════════════════════════════════

interface TonnageSectionProps {
  tonnellaggio: TSAnalisiTonnellaggio;
}

// ════════════════════════════════════════════════════════════
// ZONE NSCA — COLORI + LABEL
// ════════════════════════════════════════════════════════════

const ZONE_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  massimale: {
    label: "Massimale",
    color: "text-red-700 dark:text-red-400",
    bg: "bg-red-100 dark:bg-red-950",
  },
  sub_massimale: {
    label: "Sub-massimale",
    color: "text-orange-700 dark:text-orange-400",
    bg: "bg-orange-100 dark:bg-orange-950",
  },
  ipertrofia: {
    label: "Ipertrofia",
    color: "text-blue-700 dark:text-blue-400",
    bg: "bg-blue-100 dark:bg-blue-950",
  },
  resistenza: {
    label: "Resistenza",
    color: "text-emerald-700 dark:text-emerald-400",
    bg: "bg-emerald-100 dark:bg-emerald-950",
  },
  attivazione: {
    label: "Attivazione",
    color: "text-zinc-600 dark:text-zinc-400",
    bg: "bg-zinc-100 dark:bg-zinc-900",
  },
};

const PATTERN_LABELS: Record<string, string> = {
  squat: "Squat",
  hinge: "Hinge",
  push_h: "Push Orizz.",
  push_v: "Push Vert.",
  pull_h: "Pull Orizz.",
  pull_v: "Pull Vert.",
  core: "Core",
  rotation: "Rotazione",
  carry: "Carry",
  hip_thrust: "Hip Thrust",
  curl: "Curl",
  extension_tri: "Extension Tri",
  lateral_raise: "Lateral Raise",
  face_pull: "Face Pull",
  calf_raise: "Calf Raise",
  leg_curl: "Leg Curl",
  leg_extension: "Leg Extension",
  adductor: "Adductor",
};

function formatKg(value: number): string {
  return value >= 1000
    ? `${(value / 1000).toFixed(1).replace(/\.0$/, "")} t`
    : `${Math.round(value)} kg`;
}

// ════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPALE
// ════════════════════════════════════════════════════════════

export function TonnageSection({ tonnellaggio }: TonnageSectionProps) {
  const [isOpen, setIsOpen] = useState(true);

  const sessionNames = Object.keys(tonnellaggio.tonnellaggio_per_sessione);
  const zoneConfig = tonnellaggio.zona_prevalente
    ? ZONE_CONFIG[tonnellaggio.zona_prevalente]
    : null;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="border-l-4 border-l-violet-500/50">
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/30 transition-colors py-3 px-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Weight className="h-4 w-4 text-violet-600" />
                <CardTitle className="text-sm font-semibold">
                  Profilo Volume-Load
                </CardTitle>
                <Badge className="text-xs font-bold tabular-nums bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300">
                  {formatKg(tonnellaggio.tonnellaggio_totale)}
                </Badge>
                {zoneConfig && (
                  <Badge className={`text-xs ${zoneConfig.bg} ${zoneConfig.color}`}>
                    {zoneConfig.label}
                  </Badge>
                )}
              </div>
              <ChevronDown
                className={`h-4 w-4 text-muted-foreground transition-transform ${
                  isOpen ? "rotate-180" : ""
                }`}
              />
            </div>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="pt-0 px-4 pb-4 space-y-3">
            {/* KPI riga */}
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span>
                Tonnellaggio totale:{" "}
                <span className="font-semibold text-foreground tabular-nums">
                  {formatKg(tonnellaggio.tonnellaggio_totale)}
                </span>
              </span>
              {tonnellaggio.intensita_media_ponderata != null && (
                <span>
                  Intensita' media:{" "}
                  <span className="font-semibold text-foreground tabular-nums">
                    {Math.round(tonnellaggio.intensita_media_ponderata * 100)}% 1RM
                  </span>
                </span>
              )}
            </div>

            {/* Barre per sessione */}
            {sessionNames.length > 1 && (
              <SessionBars
                tonnPerSession={tonnellaggio.tonnellaggio_per_sessione}
                total={tonnellaggio.tonnellaggio_totale}
              />
            )}

            {/* Dettaglio slot */}
            <SlotDetailTable slots={tonnellaggio.slot_detail} />

            {/* Fonte */}
            <p className="text-[10px] text-muted-foreground">
              {tonnellaggio.fonte}
            </p>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

// ════════════════════════════════════════════════════════════
// BARRE PER SESSIONE
// ════════════════════════════════════════════════════════════

function SessionBars({
  tonnPerSession,
  total,
}: {
  tonnPerSession: Record<string, number>;
  total: number;
}) {
  const entries = Object.entries(tonnPerSession);

  return (
    <div className="space-y-1">
      <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
        Tonnellaggio per sessione
      </span>
      {entries.map(([nome, tonn]) => {
        const pct = total > 0 ? (tonn / total) * 100 : 0;
        return (
          <div key={nome} className="flex items-center gap-2">
            <span className="text-[10px] w-28 shrink-0 truncate text-muted-foreground">
              {nome}
            </span>
            <div className="flex-1 h-2.5 bg-muted/40 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-violet-500 transition-all"
                style={{ width: `${Math.round(pct)}%` }}
              />
            </div>
            <span className="text-[10px] font-mono tabular-nums w-14 text-right shrink-0 text-muted-foreground">
              {formatKg(tonn)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// TABELLA DETTAGLIO SLOT
// ════════════════════════════════════════════════════════════

function SlotDetailTable({ slots }: { slots: TSTonnellaggioSlotAnalisi[] }) {
  if (slots.length === 0) return null;

  return (
    <div className="space-y-1">
      <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
        Dettaglio esercizi
      </span>
      <div className="space-y-0.5">
        {slots.map((slot, i) => {
          const zone = slot.zona_intensita ? ZONE_CONFIG[slot.zona_intensita] : null;
          return (
            <div
              key={`${slot.sessione}-${slot.pattern}-${i}`}
              className="flex items-center gap-2 px-2 py-1 rounded hover:bg-muted/20 transition-colors"
            >
              <Dumbbell className="h-3 w-3 text-muted-foreground shrink-0" />
              <span className="text-[11px] font-medium w-24 shrink-0 truncate">
                {PATTERN_LABELS[slot.pattern] ?? slot.pattern}
              </span>
              <span className="text-[10px] text-muted-foreground w-20 shrink-0">
                {slot.serie}×{slot.rep_medie} × {slot.carico_kg} kg
              </span>
              <span className="text-[10px] font-mono tabular-nums text-foreground w-14 shrink-0 text-right font-semibold">
                {formatKg(slot.tonnellaggio)}
              </span>
              {zone && (
                <Badge className={`text-[9px] px-1.5 py-0 ${zone.bg} ${zone.color}`}>
                  {zone.label}
                </Badge>
              )}
              {slot.intensita_relativa != null && (
                <span className="text-[9px] text-muted-foreground tabular-nums">
                  ~{Math.round(slot.intensita_relativa * 100)}%
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
