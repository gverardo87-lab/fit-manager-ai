// src/components/portal/AvatarContextBar.tsx
/**
 * AvatarContextBar — striscia compatta avatar sopra PortalNav.
 *
 * ReadinessRing piccolo + 4 semafori dimensionali + top highlight.
 * Sempre visibile nel portale monitoraggio, da contesto operativo
 * alle 8 sezioni analitiche sottostanti.
 */

import Link from "next/link";

import { ReadinessRing } from "@/components/ui/readiness-ring";
import { SemaphoreDot } from "@/components/ui/semaphore-dot";
import { Skeleton } from "@/components/ui/skeleton";
import {
  surfaceChipClassName,
  surfaceRoleClassName,
  type SurfaceTone,
} from "@/components/ui/surface-role";
import type { ClientAvatar } from "@/types/api";

// ── Dimension label map ──────────────────────────────────────────

const DIMENSIONS: { key: keyof Pick<ClientAvatar, "clinical" | "contract" | "training" | "body_goals">; label: string }[] = [
  { key: "clinical", label: "Clinica" },
  { key: "contract", label: "Contratto" },
  { key: "training", label: "Allenamento" },
  { key: "body_goals", label: "Corpo" },
];

// ── Component ────────────────────────────────────────────────────

interface AvatarContextBarProps {
  avatar: ClientAvatar | null;
  isLoading?: boolean;
}

export function AvatarContextBar({ avatar, isLoading }: AvatarContextBarProps) {
  if (isLoading && !avatar) {
    return (
      <div className={surfaceRoleClassName({ role: "context", tone: "neutral" }, "flex items-center gap-3 rounded-xl px-4 py-2.5")}>
        <Skeleton className="h-9 w-9 rounded-full" />
        <div className="flex gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-5 w-16 rounded-full" />
          ))}
        </div>
      </div>
    );
  }

  if (!avatar) return null;

  const topHighlight = avatar.highlights[0] ?? null;

  return (
    <div
      className={surfaceRoleClassName(
        { role: "context", tone: "neutral" },
        "flex flex-wrap items-center gap-3 rounded-xl px-4 py-2.5",
      )}
    >
      {/* Readiness ring — compact */}
      <ReadinessRing score={avatar.readiness_score} size={36} />

      {/* Semaphore dots with labels */}
      <div className="flex flex-wrap items-center gap-1.5">
        {DIMENSIONS.map((dim) => {
          const status = avatar[dim.key].status;
          return (
            <span
              key={dim.key}
              className={surfaceChipClassName(
                { tone: status === "red" ? "red" : status === "amber" ? "amber" : "neutral" },
                "flex items-center gap-1.5 px-2 py-1 text-[10px] font-semibold",
              )}
              title={dim.label}
            >
              <SemaphoreDot status={status} />
              <span className="hidden sm:inline">{dim.label}</span>
            </span>
          );
        })}
      </div>

      {/* Top highlight */}
      {topHighlight ? (
        <div className="ml-auto">
          {topHighlight.cta_href ? (
            <Link
              href={topHighlight.cta_href}
              className={surfaceChipClassName(
                { tone: (topHighlight.severity === "critical" ? "red" : topHighlight.severity === "warning" ? "amber" : "neutral") as SurfaceTone },
                "px-2.5 py-1 text-[10px] font-semibold transition-colors hover:ring-1 hover:ring-ring/20",
              )}
            >
              {topHighlight.text}
            </Link>
          ) : (
            <span
              className={surfaceChipClassName(
                { tone: (topHighlight.severity === "critical" ? "red" : topHighlight.severity === "warning" ? "amber" : "neutral") as SurfaceTone },
                "px-2.5 py-1 text-[10px] font-semibold",
              )}
            >
              {topHighlight.text}
            </span>
          )}
        </div>
      ) : null}
    </div>
  );
}
