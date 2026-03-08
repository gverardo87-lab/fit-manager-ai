// src/components/workouts/MuscleCoverageSection.tsx
"use client";

/**
 * Sezione 1: Copertura Muscolare — drill-down volume per muscolo.
 *
 * Body map KPI + lista espandibile per muscolo con:
 * - Barra volume vs target MEV/MAV/MRV
 * - Frequenza stimolazione settimanale
 * - Breakdown contributo per esercizio (serie x EMG = serie ipertrofiche)
 *
 * Dati: TSAnalisiPiano.dettaglio_muscoli dal backend.
 * Fonti: Schoenfeld 2017, Israetel RP 2020.
 */

import { useState, useRef, useCallback, forwardRef } from "react";
import { ChevronDown, Target } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { mapBackendVolumeStatus } from "@/lib/training-science-display";
import { AnatomicalMuscleMap } from "./AnatomicalMuscleMap";
import type { TSAnalisiPiano, TSDettaglioMuscolo } from "@/types/api";

// ════════════════════════════════════════════════════════════
// COSTANTI
// ════════════════════════════════════════════════════════════

const STATUS_CONFIG: Record<string, { label: string; color: string; border: string }> = {
  deficit: {
    label: "Deficit",
    color: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
    border: "border-l-red-500",
  },
  suboptimal: {
    label: "Sotto-ottimale",
    color: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
    border: "border-l-blue-500",
  },
  optimal: {
    label: "Ottimale",
    color: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
    border: "border-l-emerald-500",
  },
  excess: {
    label: "Eccesso",
    color: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
    border: "border-l-amber-500",
  },
};

const MUSCLE_LABELS: Record<string, string> = {
  petto: "Petto",
  dorsali: "Dorsali",
  deltoide_anteriore: "Deltoide ant.",
  deltoide_laterale: "Deltoide lat.",
  deltoide_posteriore: "Deltoide post.",
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

// ════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPALE
// ════════════════════════════════════════════════════════════

interface MuscleCoverageSectionProps {
  analysis: TSAnalisiPiano;
}

function formatKg(value: number): string {
  return value >= 1000
    ? `${(value / 1000).toFixed(1).replace(/\.0$/, "")} t`
    : `${Math.round(value)} kg`;
}

export function MuscleCoverageSection({ analysis }: MuscleCoverageSectionProps) {
  const [isOpen, setIsOpen] = useState(true);
  const dettagli = analysis.dettaglio_muscoli;
  const rowRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const hasLoad = analysis.volume.has_load_data;

  // KPI rapidi
  const optimal = dettagli.filter((m) => mapBackendVolumeStatus(m.stato) === "optimal").length;
  const deficit = dettagli.filter((m) => mapBackendVolumeStatus(m.stato) === "deficit").length;
  const total = dettagli.length;

  // Click su muscolo nella mappa → scroll alla riga corrispondente
  const handleMuscleClick = useCallback(
    (group: string) => {
      if (!isOpen) setIsOpen(true);
      // Delay per permettere all'animazione di collapsible di aprirsi
      requestAnimationFrame(() => {
        const el = rowRefs.current.get(group);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
          el.classList.add("ring-2", "ring-primary/50");
          setTimeout(() => el.classList.remove("ring-2", "ring-primary/50"), 1500);
        }
      });
    },
    [isOpen],
  );

  const setRowRef = useCallback((group: string, el: HTMLDivElement | null) => {
    if (el) rowRefs.current.set(group, el);
    else rowRefs.current.delete(group);
  }, []);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="border-l-4 border-l-primary/50">
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/30 transition-colors py-3 px-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-primary" />
                <CardTitle className="text-sm font-semibold">Copertura Muscolare</CardTitle>
                <Badge variant="secondary" className="text-xs tabular-nums">
                  {optimal}/{total} ottimali
                </Badge>
                {deficit > 0 && (
                  <Badge variant="destructive" className="text-xs tabular-nums">
                    {deficit} deficit
                  </Badge>
                )}
                {hasLoad && analysis.volume.tonnellaggio_totale != null && (
                  <Badge className="text-xs tabular-nums bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300">
                    {formatKg(analysis.volume.tonnellaggio_totale)}
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
            {/* Mappa anatomica interattiva */}
            <AnatomicalMuscleMap
              dettaglioMuscoli={dettagli}
              onMuscleClick={handleMuscleClick}
            />

            {/* Drill-down per muscolo */}
            <div className="space-y-1">
              {dettagli.map((muscolo) => (
                <MuscleRow
                  key={muscolo.muscolo}
                  muscolo={muscolo}
                  ref={(el) => setRowRef(muscolo.muscolo, el)}
                />
              ))}
            </div>

            <p className="text-[10px] text-muted-foreground pt-2">
              {hasLoad
                ? "Dose-response: serie pesate per intensita' relativa (NSCA 2016, Israetel RP 2020)."
                : "Volume ipertrofico pesato (Israetel RP 2020, Schoenfeld 2017). Soglia EMG 40% MVC."
              }
            </p>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

// ════════════════════════════════════════════════════════════
// RIGA MUSCOLO — Espandibile con dettaglio contributi
// ════════════════════════════════════════════════════════════

const MuscleRow = forwardRef<HTMLDivElement, { muscolo: TSDettaglioMuscolo }>(
  function MuscleRow({ muscolo }, ref) {
  const [expanded, setExpanded] = useState(false);
  const status = mapBackendVolumeStatus(muscolo.stato);
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.optimal;
  const label = MUSCLE_LABELS[muscolo.muscolo] ?? muscolo.muscolo;

  // Barra: posizione relativa del valore nel range 0..MRV
  const maxBar = muscolo.target_mrv > 0 ? muscolo.target_mrv : 20;
  const fillPct = Math.min(100, (muscolo.serie_effettive / maxBar) * 100);

  // Segmenti MEV e MAV per la barra di riferimento
  const mevPct = (muscolo.target_mev / maxBar) * 100;
  const mavMaxPct = (muscolo.target_mav_max / maxBar) * 100;

  return (
    <div
      ref={ref}
      className={`border-l-2 ${config.border} rounded-r transition-all ${
        expanded ? "bg-muted/20" : "hover:bg-muted/10"
      }`}
    >
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-3 py-1.5 flex items-center gap-2"
      >
        {/* Nome + badge */}
        <span className="text-xs font-medium w-24 shrink-0 truncate">{label}</span>
        <Badge className={`text-[10px] px-1.5 py-0 ${config.color}`}>
          {config.label}
        </Badge>

        {/* Barra volume */}
        <div className="flex-1 h-3 bg-muted/40 rounded-full relative overflow-hidden">
          {/* Zona MEV-MAV (range ottimale) */}
          <div
            className="absolute inset-y-0 bg-emerald-200/40 dark:bg-emerald-900/30"
            style={{ left: `${mevPct}%`, width: `${mavMaxPct - mevPct}%` }}
          />
          {/* Fill attuale */}
          <div
            className={`absolute inset-y-0 left-0 rounded-full transition-all ${
              status === "deficit"
                ? "bg-red-400"
                : status === "excess"
                  ? "bg-amber-400"
                  : status === "suboptimal"
                    ? "bg-blue-400"
                    : "bg-emerald-500"
            }`}
            style={{ width: `${fillPct}%` }}
          />
        </div>

        {/* Valore numerico */}
        <span className="text-[11px] font-mono tabular-nums text-muted-foreground w-12 text-right shrink-0">
          {muscolo.serie_effettive.toFixed(1)}s
        </span>

        {/* Tensione in kg (se presente) */}
        {muscolo.tensione_kg != null && (
          <span className="text-[10px] font-mono tabular-nums text-violet-600 dark:text-violet-400 w-14 text-right shrink-0">
            {formatKg(muscolo.tensione_kg)}
          </span>
        )}

        {/* Frequenza */}
        <span className="text-[10px] text-muted-foreground w-8 text-right shrink-0">
          {muscolo.frequenza}x
        </span>

        <ChevronDown
          className={`h-3 w-3 text-muted-foreground transition-transform shrink-0 ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Drill-down */}
      {expanded && (
        <div className="px-3 pb-2 space-y-1">
          {/* Range target */}
          <div className="text-[10px] text-muted-foreground flex gap-3">
            <span>MEV {muscolo.target_mev}</span>
            <span>MAV {muscolo.target_mav_min}-{muscolo.target_mav_max}</span>
            <span>MRV {muscolo.target_mrv}</span>
            <span className="ml-auto">Freq: {muscolo.frequenza}x/sett</span>
          </div>

          {/* Contributi per esercizio */}
          {muscolo.contributi.length > 0 && (
            <div className="space-y-0.5 pt-1">
              <p className="text-[10px] font-medium text-muted-foreground">
                Contributo per esercizio:
              </p>
              {muscolo.contributi.map((c, idx) => (
                <div key={idx} className="flex items-center gap-2 text-[10px]">
                  <span className="truncate flex-1 text-muted-foreground">
                    {c.nome_esercizio.split(" — ")[1] ?? c.nome_esercizio}
                  </span>
                  {c.carico_kg != null && (
                    <span className="font-mono tabular-nums text-violet-600 dark:text-violet-400 shrink-0">
                      {c.carico_kg}kg
                    </span>
                  )}
                  <span className="font-mono tabular-nums text-muted-foreground shrink-0">
                    {c.serie}s x {c.contributo_emg.toFixed(1)}
                  </span>
                  <span className="font-mono tabular-nums shrink-0">
                    = {c.serie_ipertrofiche.toFixed(1)}
                    {c.contributo_emg < 0.4 && (
                      <span className="text-muted-foreground ml-1">*</span>
                    )}
                  </span>
                </div>
              ))}
              {muscolo.contributi.some((c) => c.contributo_emg < 0.4) && (
                <p className="text-[9px] text-muted-foreground italic">
                  * Sotto soglia EMG 40% — non conta per ipertrofia
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
});
