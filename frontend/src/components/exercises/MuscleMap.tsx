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
import { buildBodyData, FRONT_SLUGS, BACK_SLUGS } from "@/lib/muscle-map-utils";

// Colori: intensity 1 = primario (pieno), intensity 2 = secondario (attenuato)
const COLORS_LIGHT = ["#2563eb", "#93c5fd"] as const; // blue-600, blue-300
const COLORS_DARK = ["#3b82f6", "#60a5fa"] as const;  // blue-500, blue-400

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
