// src/components/workouts/AnatomicalMuscleMap.tsx
"use client";

/**
 * Mappa muscolare anatomica SVG interattiva.
 *
 * Due viste (anteriore + posteriore) affiancate, ~27 zone muscolari
 * colorate per stato volume (deficit/suboptimal/optimal/excess/untrained).
 * Hover tooltip con nome muscolo + serie + stato.
 * Click per scroll-to-row nel drill-down MuscleCoverageSection.
 *
 * ViewBox: 0 0 200 440 per ciascuna vista.
 */

import { useState, useMemo, useCallback, useRef, useEffect } from "react";

import {
  ALL_ZONES,
  BODY_OUTLINE_FRONT,
  BODY_OUTLINE_BACK,
  FRONT_VIEW_ZONES,
  BACK_VIEW_ZONES,
  MUSCLE_GROUP_LABELS,
  STATUS_FILLS,
  STATUS_LABELS,
} from "@/lib/anatomical-muscle-data";
import { mapBackendVolumeStatus } from "@/lib/training-science-display";
import type { TSDettaglioMuscolo } from "@/types/api";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

type VolumeStatus = "deficit" | "suboptimal" | "optimal" | "excess" | "untrained";

interface MuscleStatus {
  status: VolumeStatus;
  serie: number;
  frequenza: number;
  label: string;
}

interface TooltipData {
  x: number;
  y: number;
  group: string;
  info: MuscleStatus;
}

interface AnatomicalMuscleMapProps {
  dettaglioMuscoli: TSDettaglioMuscolo[];
  onMuscleClick?: (group: string) => void;
}

// ════════════════════════════════════════════════════════════
// COMPONENTE
// ════════════════════════════════════════════════════════════

export function AnatomicalMuscleMap({
  dettaglioMuscoli,
  onMuscleClick,
}: AnatomicalMuscleMapProps) {
  const [hovered, setHovered] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDark, setIsDark] = useState(false);

  // Detect dark mode via media query (works without ThemeProvider)
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    setIsDark(mq.matches || document.documentElement.classList.contains("dark"));
    const handler = () => {
      setIsDark(mq.matches || document.documentElement.classList.contains("dark"));
    };
    mq.addEventListener("change", handler);
    // Also observe class changes on <html> for manual toggle
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains("dark"));
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => {
      mq.removeEventListener("change", handler);
      observer.disconnect();
    };
  }, []);

  // Build status map: group name -> MuscleStatus
  const statusMap = useMemo(() => {
    const map = new Map<string, MuscleStatus>();
    for (const m of dettaglioMuscoli) {
      const status = mapBackendVolumeStatus(m.stato);
      map.set(m.muscolo, {
        status,
        serie: m.serie_effettive,
        frequenza: m.frequenza,
        label: MUSCLE_GROUP_LABELS[m.muscolo] ?? m.muscolo,
      });
    }
    return map;
  }, [dettaglioMuscoli]);

  const getFill = useCallback(
    (group: string): string => {
      const info = statusMap.get(group);
      if (!info) {
        return isDark ? STATUS_FILLS.untrained.dark : STATUS_FILLS.untrained.light;
      }
      const fills = STATUS_FILLS[info.status];
      return isDark ? fills.dark : fills.light;
    },
    [statusMap, isDark],
  );

  const handleMouseEnter = useCallback(
    (group: string, e: React.MouseEvent<SVGPathElement>) => {
      setHovered(group);
      const info = statusMap.get(group) ?? {
        status: "untrained" as const,
        serie: 0,
        frequenza: 0,
        label: MUSCLE_GROUP_LABELS[group] ?? group,
      };
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setTooltip({
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
          group,
          info,
        });
      }
    },
    [statusMap],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<SVGPathElement>) => {
      if (!tooltip || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      setTooltip((prev) => prev ? { ...prev, x: e.clientX - rect.left, y: e.clientY - rect.top } : null);
    },
    [tooltip],
  );

  const handleMouseLeave = useCallback(() => {
    setHovered(null);
    setTooltip(null);
  }, []);

  const handleClick = useCallback(
    (group: string) => {
      onMuscleClick?.(group);
    },
    [onMuscleClick],
  );

  // Collect unique active groups for legend
  const activeStatuses = useMemo(() => {
    const set = new Set<VolumeStatus>();
    for (const info of statusMap.values()) {
      set.add(info.status);
    }
    // Check if any zone has no data
    const allGroups = new Set(ALL_ZONES.map((z) => z.group));
    for (const g of allGroups) {
      if (!statusMap.has(g)) set.add("untrained");
    }
    return set;
  }, [statusMap]);

  return (
    <div ref={containerRef} className="relative select-none">
      {/* Body views side by side */}
      <div className="flex justify-center gap-2">
        {/* Front view */}
        <div className="flex-1 max-w-[200px]">
          <p className="text-[10px] text-center text-muted-foreground mb-1 font-medium">
            Anteriore
          </p>
          <BodyView
            outline={BODY_OUTLINE_FRONT}
            zones={FRONT_VIEW_ZONES}
            hovered={hovered}
            getFill={getFill}
            isDark={isDark}
            onMouseEnter={handleMouseEnter}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            onClick={handleClick}
          />
        </div>

        {/* Back view */}
        <div className="flex-1 max-w-[200px]">
          <p className="text-[10px] text-center text-muted-foreground mb-1 font-medium">
            Posteriore
          </p>
          <BodyView
            outline={BODY_OUTLINE_BACK}
            zones={BACK_VIEW_ZONES}
            hovered={hovered}
            getFill={getFill}
            isDark={isDark}
            onMouseEnter={handleMouseEnter}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            onClick={handleClick}
          />
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 mt-2">
        {(["optimal", "suboptimal", "deficit", "excess", "untrained"] as VolumeStatus[])
          .filter((s) => activeStatuses.has(s))
          .map((status) => (
            <div key={status} className="flex items-center gap-1">
              <span
                className="inline-block w-2.5 h-2.5 rounded-sm"
                style={{
                  backgroundColor: isDark
                    ? STATUS_FILLS[status].dark
                    : STATUS_FILLS[status].light,
                }}
              />
              <span className="text-[10px] text-muted-foreground">
                {STATUS_LABELS[status]}
              </span>
            </div>
          ))}
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute z-50 pointer-events-none px-2.5 py-1.5 rounded-md shadow-lg border text-xs bg-popover text-popover-foreground"
          style={{
            left: Math.min(tooltip.x + 12, (containerRef.current?.offsetWidth ?? 300) - 140),
            top: tooltip.y - 48,
          }}
        >
          <p className="font-semibold text-[11px]">{tooltip.info.label}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{
                backgroundColor: isDark
                  ? STATUS_FILLS[tooltip.info.status].dark
                  : STATUS_FILLS[tooltip.info.status].light,
              }}
            />
            <span className="text-[10px]">{STATUS_LABELS[tooltip.info.status]}</span>
          </div>
          {tooltip.info.status !== "untrained" && (
            <p className="text-[10px] text-muted-foreground mt-0.5 tabular-nums">
              {tooltip.info.serie.toFixed(1)} serie · {tooltip.info.frequenza}x/sett
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// BODY VIEW — Single SVG (front or back)
// ════════════════════════════════════════════════════════════

interface BodyViewProps {
  outline: string;
  zones: typeof FRONT_VIEW_ZONES;
  hovered: string | null;
  getFill: (group: string) => string;
  isDark: boolean;
  onMouseEnter: (group: string, e: React.MouseEvent<SVGPathElement>) => void;
  onMouseMove: (e: React.MouseEvent<SVGPathElement>) => void;
  onMouseLeave: () => void;
  onClick: (group: string) => void;
}

function BodyView({
  outline,
  zones,
  hovered,
  getFill,
  isDark,
  onMouseEnter,
  onMouseMove,
  onMouseLeave,
  onClick,
}: BodyViewProps) {
  return (
    <svg
      viewBox="0 0 200 440"
      className="w-full h-auto"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Body silhouette outline */}
      <path
        d={outline}
        fill={isDark ? "#27272a" : "#f4f4f5"}
        stroke={isDark ? "#52525b" : "#d4d4d8"}
        strokeWidth="1"
      />

      {/* Muscle zones */}
      {zones.map((zone) => (
        <path
          key={zone.id}
          d={zone.d}
          fill={getFill(zone.group)}
          fillOpacity={hovered === zone.group ? 0.95 : 0.75}
          stroke={hovered === zone.group ? (isDark ? "#ffffff" : "#18181b") : "transparent"}
          strokeWidth={hovered === zone.group ? 1.2 : 0}
          className="cursor-pointer"
          style={{ transition: "fill 0.3s ease, fill-opacity 0.2s ease, stroke 0.2s ease" }}
          onMouseEnter={(e) => onMouseEnter(zone.group, e)}
          onMouseMove={onMouseMove}
          onMouseLeave={onMouseLeave}
          onClick={() => onClick(zone.group)}
        />
      ))}
    </svg>
  );
}
