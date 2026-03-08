// src/components/workouts/TonnageSection.tsx
"use client";

/**
 * Sezione 2.5: Profilo Biomeccanico Volume-Load.
 *
 * Vista primaria: tensione meccanica per gruppo muscolare (tonnage × EMG).
 * Vista secondaria (collapsible): tonnellaggio grezzo per sessione + dettaglio slot.
 *
 * Formula: tensione[M] = Σ(tonnage_slot × contribution[pattern][M])
 * dove contribution = coefficiente attivazione EMG dalla matrice 18×15.
 *
 * Fonti: Haff & Triplett (NSCA 2016) cap. 15 — Volume-Load,
 *        Schoenfeld (2010) — Mechanical tension as hypertrophy driver,
 *        Contreras (2010) — EMG analysis, Israetel RP 2020.
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
import type { TSAnalisiTonnellaggio, TSTonnellaggioSlotAnalisi } from "@/types/api";

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
}

// ════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPALE
// ════════════════════════════════════════════════════════════

export function TonnageSection({ tonnellaggio }: TonnageSectionProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [showRaw, setShowRaw] = useState(false);

  const hasTension = Object.keys(tonnellaggio.tensione_per_muscolo).length > 0;
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
                Tonnellaggio:{" "}
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
}: {
  tensioneMeccanica: Record<string, number>;
  tensioneIpertrofica: Record<string, number>;
}) {
  // Ordina per tensione meccanica decrescente
  const sorted = useMemo(() => {
    return Object.entries(tensioneMeccanica)
      .filter(([, v]) => v > 0)
      .sort(([, a], [, b]) => b - a);
  }, [tensioneMeccanica]);

  const maxTension = sorted.length > 0 ? sorted[0][1] : 1;

  if (sorted.length === 0) return null;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2 mb-1">
        <Zap className="h-3.5 w-3.5 text-violet-600" />
        <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
          Tensione meccanica per muscolo
        </span>
      </div>

      {/* Legenda */}
      <div className="flex items-center gap-3 text-[10px] text-muted-foreground mb-1">
        <span className="flex items-center gap-1">
          <span className="inline-block w-2.5 h-2.5 rounded-sm bg-violet-500" />
          Meccanica
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2.5 h-2.5 rounded-sm bg-fuchsia-500" />
          Ipertrofica
        </span>
      </div>

      {sorted.map(([muscolo, mech]) => {
        const hyp = tensioneIpertrofica[muscolo] ?? 0;
        const mechPct = (mech / maxTension) * 100;
        const hypPct = (hyp / maxTension) * 100;

        return (
          <div key={muscolo} className="flex items-center gap-2">
            <span className="text-[10px] w-24 shrink-0 truncate text-muted-foreground">
              {MUSCLE_LABELS[muscolo] ?? muscolo}
            </span>
            <div className="flex-1 relative h-4 bg-muted/30 rounded overflow-hidden">
              {/* Barra meccanica (sfondo) */}
              <div
                className="absolute inset-y-0 left-0 rounded bg-violet-400/40 transition-all"
                style={{ width: `${Math.round(mechPct)}%` }}
              />
              {/* Barra ipertrofica (primo piano) */}
              {hyp > 0 && (
                <div
                  className="absolute inset-y-0 left-0 rounded bg-fuchsia-500/70 transition-all"
                  style={{ width: `${Math.round(hypPct)}%` }}
                />
              )}
            </div>
            <span className="text-[10px] font-mono tabular-nums w-16 text-right shrink-0 text-foreground font-semibold">
              {formatKg(mech)}
            </span>
            {hyp > 0 && hyp < mech && (
              <span className="text-[9px] font-mono tabular-nums w-14 text-right shrink-0 text-fuchsia-600 dark:text-fuchsia-400">
                {formatKg(hyp)}
              </span>
            )}
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
