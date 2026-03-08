// src/components/workouts/TonnageSection.tsx
"use client";

/**
 * Sezione 2.5: Profilo Biomeccanico Volume-Load.
 *
 * Vista primaria: tensione meccanica per gruppo muscolare (tonnage × EMG),
 * colorata per stato volume (deficit/ottimale/eccesso) dalla Sezione 1.
 * Il colore contestualizza il dato: non solo "quanto carico" ma "e' appropriato?".
 *
 * Formula: tensione[M] = Σ(tonnage_slot × contribution[pattern][M])
 * dove contribution = coefficiente attivazione EMG dalla matrice 18×15.
 *
 * Fonti: Schoenfeld 2010 (mechanical tension), Contreras 2010 (EMG),
 *        Israetel RP 2020 (half-set rule), Haff & Triplett NSCA 2016.
 */

import { useState, useMemo } from "react";
import { ChevronDown, Weight, Dumbbell, Zap, BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { mapBackendVolumeStatus } from "@/lib/training-science-display";
import type {
  TSAnalisiTonnellaggio,
  TSTonnellaggioSlotAnalisi,
  TSDettaglioMuscolo,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// COSTANTI
// ════════════════════════════════════════════════════════════

const MUSCLE_LABELS: Record<string, string> = {
  petto: "Petto",
  dorsali: "Dorsali",
  deltoide_anteriore: "Delt. ant.",
  deltoide_laterale: "Delt. lat.",
  deltoide_posteriore: "Delt. post.",
  bicipiti: "Bicipiti",
  tricipiti: "Tricipiti",
  quadricipiti: "Quadricipiti",
  femorali: "Femorali",
  glutei: "Glutei",
  polpacci: "Polpacci",
  trapezio: "Trapezio",
  core: "Core",
  avambracci: "Avambracci",
  adduttori: "Adduttori",
};

/** Colori per stato volume — allineati a MuscleCoverageSection */
const STATUS_BAR_COLORS: Record<string, { bar: string; barHyp: string; text: string; badge: string }> = {
  deficit: {
    bar: "bg-red-400/50",
    barHyp: "bg-red-500/80",
    text: "text-red-700 dark:text-red-400",
    badge: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  },
  suboptimal: {
    bar: "bg-blue-400/50",
    barHyp: "bg-blue-500/80",
    text: "text-blue-700 dark:text-blue-400",
    badge: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
  },
  optimal: {
    bar: "bg-emerald-400/50",
    barHyp: "bg-emerald-500/80",
    text: "text-emerald-700 dark:text-emerald-400",
    badge: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  },
  excess: {
    bar: "bg-amber-400/50",
    barHyp: "bg-amber-500/80",
    text: "text-amber-700 dark:text-amber-400",
    badge: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  },
};

const FALLBACK_COLORS = STATUS_BAR_COLORS.optimal;

const STATUS_LABELS: Record<string, string> = {
  deficit: "Deficit",
  suboptimal: "Sotto-ottimale",
  optimal: "Ottimale",
  excess: "Eccesso",
};

const ZONE_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  massimale: { label: "Massimale", color: "text-red-700 dark:text-red-400", bg: "bg-red-100 dark:bg-red-950" },
  sub_massimale: { label: "Sub-massimale", color: "text-orange-700 dark:text-orange-400", bg: "bg-orange-100 dark:bg-orange-950" },
  ipertrofia: { label: "Ipertrofia", color: "text-blue-700 dark:text-blue-400", bg: "bg-blue-100 dark:bg-blue-950" },
  resistenza: { label: "Resistenza", color: "text-emerald-700 dark:text-emerald-400", bg: "bg-emerald-100 dark:bg-emerald-950" },
  attivazione: { label: "Attivazione", color: "text-zinc-600 dark:text-zinc-400", bg: "bg-zinc-100 dark:bg-zinc-900" },
};

const PATTERN_LABELS: Record<string, string> = {
  squat: "Squat", hinge: "Hinge", push_h: "Push Orizz.", push_v: "Push Vert.",
  pull_h: "Pull Orizz.", pull_v: "Pull Vert.", core: "Core", rotation: "Rotazione",
  carry: "Carry", hip_thrust: "Hip Thrust", curl: "Curl", extension_tri: "Ext. Tricipiti",
  lateral_raise: "Lat. Raise", face_pull: "Face Pull", calf_raise: "Calf Raise",
  leg_curl: "Leg Curl", leg_extension: "Leg Extension", adductor: "Adductor",
};

function formatKg(value: number): string {
  return value >= 1000
    ? `${(value / 1000).toFixed(1).replace(/\.0$/, "")} t`
    : `${Math.round(value)} kg`;
}

// ════════════════════════════════════════════════════════════
// PROPS
// ════════════════════════════════════════════════════════════

interface TonnageSectionProps {
  tonnellaggio: TSAnalisiTonnellaggio;
  dettaglioMuscoli: TSDettaglioMuscolo[];
}

// ════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPALE
// ════════════════════════════════════════════════════════════

export function TonnageSection({ tonnellaggio, dettaglioMuscoli }: TonnageSectionProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [showRaw, setShowRaw] = useState(false);

  const hasTension = Object.keys(tonnellaggio.tensione_per_muscolo).length > 0;
  const zoneConfig = tonnellaggio.zona_prevalente
    ? ZONE_CONFIG[tonnellaggio.zona_prevalente]
    : null;

  // Mappa muscolo → stato volume per colorare le barre
  const volumeStatusMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const d of dettaglioMuscoli) {
      map.set(d.muscolo, mapBackendVolumeStatus(d.stato));
    }
    return map;
  }, [dettaglioMuscoli]);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="border-l-4 border-l-violet-500/50">
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/30 transition-colors py-3 px-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Weight className="h-4 w-4 text-violet-600" />
                <CardTitle className="text-sm font-semibold">
                  Profilo Biomeccanico
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
          <CardContent className="pt-0 px-4 pb-4 space-y-4">
            {/* KPI riga */}
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span>
                Volume-Load:{" "}
                <span className="font-semibold text-foreground tabular-nums">
                  {formatKg(tonnellaggio.tonnellaggio_totale)}
                </span>
              </span>
              {tonnellaggio.intensita_media_ponderata != null && (
                <span>
                  Intensita&apos; media:{" "}
                  <span className="font-semibold text-foreground tabular-nums">
                    {Math.round(tonnellaggio.intensita_media_ponderata * 100)}% 1RM
                  </span>
                </span>
              )}
            </div>

            {/* VISTA PRIMARIA: Tensione meccanica per muscolo */}
            {hasTension && (
              <MuscleTensionBars
                tensioneMeccanica={tonnellaggio.tensione_per_muscolo}
                tensioneIpertrofica={tonnellaggio.tensione_ipertrofica_per_muscolo}
                volumeStatusMap={volumeStatusMap}
              />
            )}

            {/* Toggle dettaglio grezzo */}
            <button
              type="button"
              onClick={() => setShowRaw(!showRaw)}
              className="flex items-center gap-1.5 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
            >
              <BarChart3 className="h-3 w-3" />
              <span>{showRaw ? "Nascondi" : "Mostra"} dettaglio tonnellaggio</span>
              <ChevronDown className={`h-3 w-3 transition-transform ${showRaw ? "rotate-180" : ""}`} />
            </button>

            {/* VISTA SECONDARIA: tonnellaggio grezzo (collapsible) */}
            {showRaw && (
              <div className="space-y-3 pt-1">
                {Object.keys(tonnellaggio.tonnellaggio_per_sessione).length > 1 && (
                  <SessionBars
                    tonnPerSession={tonnellaggio.tonnellaggio_per_sessione}
                    total={tonnellaggio.tonnellaggio_totale}
                  />
                )}
                <SlotDetailTable slots={tonnellaggio.slot_detail} />
              </div>
            )}

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
// TENSIONE MECCANICA PER MUSCOLO — Vista primaria
// ════════════════════════════════════════════════════════════

function MuscleTensionBars({
  tensioneMeccanica,
  tensioneIpertrofica,
  volumeStatusMap,
}: {
  tensioneMeccanica: Record<string, number>;
  tensioneIpertrofica: Record<string, number>;
  volumeStatusMap: Map<string, string>;
}) {
  const sorted = useMemo(() => {
    return Object.entries(tensioneMeccanica)
      .filter(([, v]) => v > 0)
      .sort(([, a], [, b]) => b - a);
  }, [tensioneMeccanica]);

  const maxTension = sorted.length > 0 ? sorted[0][1] : 1;
  const totalTension = useMemo(
    () => sorted.reduce((acc, [, v]) => acc + v, 0),
    [sorted],
  );

  if (sorted.length === 0) return null;

  // Conta stati per legenda
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const [muscolo] of sorted) {
      const status = volumeStatusMap.get(muscolo) ?? "optimal";
      counts[status] = (counts[status] ?? 0) + 1;
    }
    return counts;
  }, [sorted, volumeStatusMap]);

  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2 mb-1">
        <Zap className="h-3.5 w-3.5 text-violet-600" />
        <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
          Tensione meccanica per muscolo
        </span>
      </div>

      {/* Legenda: stati volume */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[10px] text-muted-foreground mb-1">
        {(["optimal", "suboptimal", "deficit", "excess"] as const).map(
          (status) =>
            (statusCounts[status] ?? 0) > 0 && (
              <span key={status} className="flex items-center gap-1">
                <span
                  className={`inline-block w-2.5 h-2.5 rounded-sm ${
                    STATUS_BAR_COLORS[status]?.barHyp ?? "bg-zinc-400"
                  }`}
                />
                {STATUS_LABELS[status]} ({statusCounts[status]})
              </span>
            ),
        )}
      </div>

      {sorted.map(([muscolo, mech]) => {
        const hyp = tensioneIpertrofica[muscolo] ?? 0;
        const mechPct = (mech / maxTension) * 100;
        const hypPct = (hyp / maxTension) * 100;
        const distPct = totalTension > 0 ? (mech / totalTension) * 100 : 0;
        const status = volumeStatusMap.get(muscolo) ?? "optimal";
        const colors = STATUS_BAR_COLORS[status] ?? FALLBACK_COLORS;

        return (
          <div key={muscolo} className="flex items-center gap-2">
            <span className="text-[10px] w-24 shrink-0 truncate text-muted-foreground">
              {MUSCLE_LABELS[muscolo] ?? muscolo}
            </span>
            <div className="flex-1 relative h-4 bg-muted/30 rounded overflow-hidden">
              {/* Barra meccanica (sfondo) */}
              <div
                className={`absolute inset-y-0 left-0 rounded ${colors.bar} transition-all`}
                style={{ width: `${Math.round(mechPct)}%` }}
              />
              {/* Barra ipertrofica (primo piano) */}
              {hyp > 0 && (
                <div
                  className={`absolute inset-y-0 left-0 rounded ${colors.barHyp} transition-all`}
                  style={{ width: `${Math.round(hypPct)}%` }}
                />
              )}
            </div>
            <span className={`text-[10px] font-mono tabular-nums w-14 text-right shrink-0 font-semibold ${colors.text}`}>
              {formatKg(mech)}
            </span>
            <span className="text-[9px] font-mono tabular-nums w-10 text-right shrink-0 text-muted-foreground">
              {distPct.toFixed(0)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// BARRE PER SESSIONE — Vista secondaria
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
// TABELLA DETTAGLIO SLOT — Vista secondaria
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
                {slot.serie}&times;{slot.rep_medie} &times; {slot.carico_kg} kg
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
