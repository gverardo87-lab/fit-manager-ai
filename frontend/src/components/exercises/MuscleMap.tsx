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

function getInitialIsMobile() {
  return typeof window !== "undefined" && window.matchMedia("(max-width: 640px)").matches;
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

interface MuscleMapProps {
  muscoliPrimari: string[];
  muscoliSecondari: string[];
  /** Terza categoria (intensity 3) — es. muscoli in deficit nel builder */
  muscoliTerziari?: string[];
  /** Quarta categoria (intensity 4) — es. muscoli in deficit con palette 4 stati */
  muscoliQuaternari?: string[];
  /** Sovrascrive la scala responsive (default: 0.65 desktop / 0.5 mobile) */
  scale?: number;
  /** Sovrascrive i colori tema — array generico: [intensity1, intensity2, intensity3?, intensity4?] */
  colors?: string[];
}

export function MuscleMap({
  muscoliPrimari,
  muscoliSecondari,
  muscoliTerziari,
  muscoliQuaternari,
  scale: scaleProp,
  colors: colorsProp,
}: MuscleMapProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  // Responsive scale — usato solo se scale non è passato dall'esterno
  const [isMobile, setIsMobile] = useState(getInitialIsMobile);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 640px)");
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const bodyScale = scaleProp ?? (isMobile ? 0.5 : 0.65);
  const defaultFill = isDark ? "#3f3f46" : "#e5e7eb"; // zinc-700 / zinc-200
  const colors = colorsProp ? [...colorsProp] : (isDark ? [...COLORS_DARK] : [...COLORS_LIGHT]);

  // Build data per vista — intensity 1 → primari, 2 → secondari, 3 → terziari, 4 → quaternari
  // Ordine: 1 prima degli altri → la priorità è mantenuta (seen set in buildBodyData)
  const frontData = useMemo(() => [
    ...buildBodyData(muscoliPrimari, 1, FRONT_SLUGS),
    ...buildBodyData(muscoliSecondari, 2, FRONT_SLUGS),
    ...(muscoliTerziari ? buildBodyData(muscoliTerziari, 3, FRONT_SLUGS) : []),
    ...(muscoliQuaternari ? buildBodyData(muscoliQuaternari, 4, FRONT_SLUGS) : []),
  ], [muscoliPrimari, muscoliSecondari, muscoliTerziari, muscoliQuaternari]);

  const backData = useMemo(() => [
    ...buildBodyData(muscoliPrimari, 1, BACK_SLUGS),
    ...buildBodyData(muscoliSecondari, 2, BACK_SLUGS),
    ...(muscoliTerziari ? buildBodyData(muscoliTerziari, 3, BACK_SLUGS) : []),
    ...(muscoliQuaternari ? buildBodyData(muscoliQuaternari, 4, BACK_SLUGS) : []),
  ], [muscoliPrimari, muscoliSecondari, muscoliTerziari, muscoliQuaternari]);

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
