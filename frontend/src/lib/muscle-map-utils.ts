// src/lib/muscle-map-utils.ts
/**
 * Costanti e helper condivisi per muscle map rendering.
 *
 * Usato da:
 * - MuscleMap.tsx (componente interattivo pagina esercizio)
 * - tools/admin_scripts/generate-muscle-maps.ts (generazione SVG statici)
 * - WorkoutPreview.tsx (display SVG pre-generati)
 */

import type { ExtendedBodyPart, Slug } from "react-muscle-highlighter";

// ════════════════════════════════════════════════════════════
// MAPPING: nostri 14 muscoli → slug react-muscle-highlighter
// ════════════════════════════════════════════════════════════

export const MUSCLE_SLUG_MAP: Record<string, Slug[]> = {
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
export const FRONT_SLUGS: Set<Slug> = new Set([
  "abs", "adductors", "biceps", "calves", "chest", "deltoids",
  "forearm", "obliques", "quadriceps", "tibialis", "trapezius",
]);

export const BACK_SLUGS: Set<Slug> = new Set([
  "calves", "deltoids", "forearm", "gluteal", "hamstring",
  "lower-back", "neck", "trapezius", "triceps", "upper-back",
]);

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

/**
 * Costruisce l'array data per Body component di react-muscle-highlighter.
 * Filtra per vista (front/back) e evita duplicati.
 */
export function buildBodyData(
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
