// src/components/workouts/RiskBodyMap.tsx
"use client";

/**
 * Mappa corporea del rischio — versione compatta per Safety Overview Panel.
 *
 * Evidenzia zone anatomiche a rischio (rosso = evitare, ambra = cautela)
 * basandosi sui body_tags delle condizioni mediche del cliente.
 * Riusa react-muscle-highlighter e il sistema di mapping da muscle-map-utils.
 */

import { useMemo, useState, useEffect } from "react";
import { useTheme } from "next-themes";
import Body from "react-muscle-highlighter";
import type { ExtendedBodyPart, Slug } from "react-muscle-highlighter";
import { BODY_TAG_SLUG_MAP, FRONT_SLUGS, BACK_SLUGS } from "@/lib/muscle-map-utils";
import type { SafetyConditionDetail } from "@/types/api";

// Colori rischio: intensity 1 = avoid (rosso), intensity 2 = caution (ambra), intensity 3 = modify (blu)
const COLORS_LIGHT = ["#dc2626", "#d97706", "#2563eb"] as const; // red-600, amber-600, blue-600
const COLORS_DARK = ["#ef4444", "#f59e0b", "#3b82f6"] as const;  // red-500, amber-500, blue-500

function getInitialIsMobile() {
  return typeof window !== "undefined" && window.matchMedia("(max-width: 640px)").matches;
}

interface RiskBodyMapProps {
  /** Tutte le condizioni uniche rilevate (con body_tags e severita) */
  conditions: SafetyConditionDetail[];
}

// Gerarchia severity per body map: avoid > modify > caution
const _SEV_RANK: Record<string, number> = { avoid: 3, modify: 2, caution: 1 };

/**
 * Costruisce body data per il risk map.
 * Avoid = intensity 1 (rosso), caution = intensity 2 (ambra), modify = intensity 3 (blu).
 * Se un slug ha piu' severity, la piu' grave vince (avoid > modify > caution).
 */
function buildRiskData(
  conditions: SafetyConditionDetail[],
  sideFilter: Set<Slug>,
): ExtendedBodyPart[] {
  const slugSeverity = new Map<Slug, string>();

  for (const cond of conditions) {
    for (const tag of cond.body_tags) {
      const slugs = BODY_TAG_SLUG_MAP[tag];
      if (!slugs) continue;
      for (const slug of slugs) {
        if (!sideFilter.has(slug)) continue;
        const current = slugSeverity.get(slug);
        if (!current || (_SEV_RANK[cond.severita] ?? 0) > (_SEV_RANK[current] ?? 0)) {
          slugSeverity.set(slug, cond.severita);
        }
      }
    }
  }

  return Array.from(slugSeverity.entries()).map(([slug, severity]) => ({
    slug,
    intensity: severity === "avoid" ? 1 : severity === "caution" ? 2 : 3,
  }));
}

export function RiskBodyMap({ conditions }: RiskBodyMapProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  const [isMobile, setIsMobile] = useState(getInitialIsMobile);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 640px)");
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const bodyScale = isMobile ? 0.35 : 0.45;
  const defaultFill = isDark ? "#3f3f46" : "#e5e7eb";
  const colors = isDark ? [...COLORS_DARK] : [...COLORS_LIGHT];

  const frontData = useMemo(() => buildRiskData(conditions, FRONT_SLUGS), [conditions]);
  const backData = useMemo(() => buildRiskData(conditions, BACK_SLUGS), [conditions]);

  // Se nessun body_tag e' mappabile, non renderizzare
  if (frontData.length === 0 && backData.length === 0) return null;

  return (
    <div className="flex items-start justify-center gap-2">
      <div className="flex flex-col items-center gap-0.5">
        <span className="text-[9px] font-semibold uppercase tracking-widest text-muted-foreground">
          Ant.
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
      <div className="flex flex-col items-center gap-0.5">
        <span className="text-[9px] font-semibold uppercase tracking-widest text-muted-foreground">
          Post.
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
