"use client";

/**
 * MuscleMapPanel — Pannello Copertura Muscolare nel Workout Builder
 *
 * Aggrega tutti i muscoli di tutte le sessioni della scheda e mostra
 * la silhouette anatomica con i gruppi muscolari illuminati in teal.
 *
 * - Primari (pieno): muscoli target principali degli esercizi
 * - Secondari (attenuato): muscoli stabilizzatori/sinergici
 * - Coverage badge: "X / 14 gruppi attivi" aggiornato live
 * - Collassabile. Si aggiorna ad ogni modifica della scheda (reactive).
 * - Empty state quando non ci sono ancora esercizi.
 *
 * Colori teal (invece di blue) per differenziare dal contesto
 * "esercizio singolo" → qui si guarda la scheda come un sistema.
 */

import { useMemo, useState } from "react";
import { useTheme } from "next-themes";
import { Activity, ChevronDown } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { MuscleMap } from "@/components/exercises/MuscleMap";
import { MUSCLE_SLUG_MAP } from "@/lib/muscle-map-utils";

// ── Palette teal — identità del builder (differente da blue del dettaglio esercizio)
const TEAL_COLORS_LIGHT = ["#0d9488", "#99f6e4"] as const; // teal-600 / teal-200
const TEAL_COLORS_DARK  = ["#2dd4bf", "#0f766e"] as const; // teal-400 / teal-700

const TOTAL_GROUPS = Object.keys(MUSCLE_SLUG_MAP).length; // 14

// ── Tipi minimi — non dipende da SessionCardData per restare riusabile
interface ExerciseInSession {
  id_esercizio: number;
}
interface SessionInput {
  esercizi: ExerciseInSession[];
}
interface ExerciseMuscleSummary {
  muscoli_primari: string[];
  muscoli_secondari: string[];
}

interface MuscleMapPanelProps {
  sessions: SessionInput[];
  exerciseMap: Map<number, ExerciseMuscleSummary> | null;
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function MuscleMapPanel({ sessions, exerciseMap }: MuscleMapPanelProps) {
  const [open, setOpen] = useState(true);
  const { resolvedTheme } = useTheme();
  const tealColors = resolvedTheme === "dark" ? TEAL_COLORS_DARK : TEAL_COLORS_LIGHT;

  // Aggrega muscoli da tutte le sessioni in modo reattivo
  const { muscoliPrimari, muscoliSecondari, activeGroups } = useMemo(() => {
    const primari  = new Set<string>();
    const secondari = new Set<string>();

    for (const session of sessions) {
      for (const row of session.esercizi) {
        const ex = exerciseMap?.get(row.id_esercizio);
        if (!ex) continue;
        ex.muscoli_primari.forEach((m) => primari.add(m));
        ex.muscoli_secondari.forEach((m) => secondari.add(m));
      }
    }

    // I primari hanno priorità: rimuovili dai secondari se presenti in entrambi
    primari.forEach((m) => secondari.delete(m));

    // Conta solo i muscoli riconosciuti da MUSCLE_SLUG_MAP
    const activeGroups = [...primari].filter((m) => m in MUSCLE_SLUG_MAP).length;

    return {
      muscoliPrimari:  [...primari],
      muscoliSecondari: [...secondari],
      activeGroups,
    };
  }, [sessions, exerciseMap]);

  const hasData = muscoliPrimari.length > 0 || muscoliSecondari.length > 0;

  // Badge colore: verde se copertura buona (≥6), ambra se parziale, grigio se niente
  const badgeStyle =
    activeGroups >= 6
      ? "bg-teal-100 text-teal-700 border-teal-200 dark:bg-teal-900/30 dark:text-teal-400 dark:border-teal-800"
      : activeGroups >= 1
      ? "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800"
      : "bg-muted text-muted-foreground";

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card className="border-l-4 border-l-teal-500 transition-all duration-200">
        <CardContent className="p-4 space-y-3">

          {/* ── Header ── */}
          <CollapsibleTrigger asChild>
            <button className="flex w-full items-center justify-between text-left group">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-teal-500" />
                <span className="text-sm font-semibold">Mappa Muscolare</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold tabular-nums ${badgeStyle}`}>
                  {activeGroups} / {TOTAL_GROUPS} gruppi
                </span>
                <ChevronDown
                  className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${open ? "rotate-180" : ""}`}
                />
              </div>
            </button>
          </CollapsibleTrigger>

          {/* ── Body collassabile ── */}
          <CollapsibleContent>
            {hasData ? (
              <div className="pt-1">
                {/* Legenda */}
                <div className="mb-3 flex items-center gap-4 text-[11px] text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-teal-500" />
                    Primari
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-teal-200 dark:bg-teal-700" />
                    Secondari
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-zinc-200 dark:bg-zinc-700" />
                    Non allenato
                  </span>
                </div>

                {/* MuscleMap a scala compatta (0.5) con teal */}
                <div className="flex justify-center">
                  <MuscleMap
                    muscoliPrimari={muscoliPrimari}
                    muscoliSecondari={muscoliSecondari}
                    scale={0.5}
                    colors={tealColors}
                  />
                </div>
              </div>
            ) : (
              // Empty state — nessun esercizio ancora
              <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed py-6 text-center">
                <Activity className="h-7 w-7 text-muted-foreground/30" />
                <p className="text-sm text-muted-foreground">
                  Nessun muscolo mappato
                </p>
                <p className="text-xs text-muted-foreground/60">
                  Aggiungi esercizi per vedere la copertura muscolare
                </p>
              </div>
            )}
          </CollapsibleContent>

        </CardContent>
      </Card>
    </Collapsible>
  );
}
