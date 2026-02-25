// src/components/exercises/MuscleMap.tsx
"use client";

/**
 * Mappa muscolare SVG interattiva — corpo anteriore + posteriore.
 * Wrapper per react-muscle-highlighter con mapping dei nostri 14 muscoli.
 * Primari = colore pieno, secondari = colore attenuato.
 */

import { useMemo, useState, useEffect } from "react";
import { useTheme } from "next-themes";
import Body from "react-muscle-highlighter";
import type { ExtendedBodyPart, Slug } from "react-muscle-highlighter";

// ════════════════════════════════════════════════════════════
// MAPPING: nostri nomi muscoli → slug pacchetto
// ════════════════════════════════════════════════════════════

const MUSCLE_SLUG_MAP: Record<string, Slug[]> = {
  quadriceps: ["quadriceps"],
  hamstrings: ["hamstring"],
  glutes: ["gluteal"],
  calves: ["calves"],
  adductors: ["adductors"],
  chest: ["chest"],
  back: ["upper-back", "lower-back"],
  lats: ["upper-back"],
  shoulders: ["deltoids"],
  traps: ["trapezius"],
  biceps: ["biceps"],
  triceps: ["triceps"],
  forearms: ["forearm"],
  core: ["abs", "obliques"],
};

// Slug visibili per vista
const FRONT_SLUGS: Set<Slug> = new Set([
  "abs", "adductors", "biceps", "calves", "chest", "deltoids",
  "forearm", "obliques", "quadriceps", "tibialis", "trapezius",
]);

const BACK_SLUGS: Set<Slug> = new Set([
  "calves", "deltoids", "forearm", "gluteal", "hamstring",
  "lower-back", "neck", "trapezius", "triceps", "upper-back",
]);

// Colori: intensity 1 = primario (pieno), intensity 2 = secondario (attenuato)
const COLORS_LIGHT = ["#2563eb", "#93c5fd"] as const; // blue-600, blue-300
const COLORS_DARK = ["#3b82f6", "#60a5fa"] as const;  // blue-500, blue-400

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

function buildBodyData(
  muscles: string[],
  intensity: number,
  sideFilter: Set<Slug>,
): ExtendedBodyPart[] {
  const seen = new Set<Slug>();
  const parts: ExtendedBodyPart[] = [];

  for (const muscle of muscles) {
    const slugs = MUSCLE_SLUG_MAP[muscle];
    if (!slugs) continue;
    for (const slug of slugs) {
      if (sideFilter.has(slug) && !seen.has(slug)) {
        seen.add(slug);
        parts.push({ slug, intensity });
      }
    }
  }

  return parts;
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

interface MuscleMapProps {
  muscoliPrimari: string[];
  muscoliSecondari: string[];
}

export function MuscleMap({ muscoliPrimari, muscoliSecondari }: MuscleMapProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  // Responsive scale
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 640px)");
    setIsMobile(mq.matches);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const bodyScale = isMobile ? 0.5 : 0.65;
  const defaultFill = isDark ? "#3f3f46" : "#e5e7eb"; // zinc-700 / zinc-200
  const colors = isDark ? [...COLORS_DARK] : [...COLORS_LIGHT];

  // Build data per vista — primari first (intensity 1), secondari dopo (intensity 2)
  // seen set in buildBodyData previene duplicati: se un muscolo e' primario, non viene
  // sovrascritto dalla versione secondaria
  const frontData = useMemo(() => [
    ...buildBodyData(muscoliPrimari, 1, FRONT_SLUGS),
    ...buildBodyData(muscoliSecondari, 2, FRONT_SLUGS),
  ], [muscoliPrimari, muscoliSecondari]);

  const backData = useMemo(() => [
    ...buildBodyData(muscoliPrimari, 1, BACK_SLUGS),
    ...buildBodyData(muscoliSecondari, 2, BACK_SLUGS),
  ], [muscoliPrimari, muscoliSecondari]);

  return (
    <div className="flex items-start justify-center gap-3 sm:gap-5">
      {/* Vista anteriore */}
      <div className="flex flex-col items-center gap-1.5">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Anteriore
        </span>
        <div className="overflow-hidden">
          <Body
            data={frontData}
            side="front"
            gender="male"
            scale={bodyScale}
            colors={colors}
            border="none"
            defaultFill={defaultFill}
          />
        </div>
      </div>

      {/* Vista posteriore */}
      <div className="flex flex-col items-center gap-1.5">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Posteriore
        </span>
        <div className="overflow-hidden">
          <Body
            data={backData}
            side="back"
            gender="male"
            scale={bodyScale}
            colors={colors}
            border="none"
            defaultFill={defaultFill}
          />
        </div>
      </div>
    </div>
  );
}
