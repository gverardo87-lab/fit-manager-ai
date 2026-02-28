// src/lib/body-zone-config.ts
/**
 * Configurazione zone corporee per la mappa interattiva.
 *
 * Ogni zona raggruppa: metriche di circonferenza + slugs SVG + body_tags anamnesi.
 * Usato da InteractiveBodyMap.tsx per click su silhouette e cross-referencing dati.
 *
 * Metriche bilaterali (DX/SX) raggruppate in zone uniche.
 */

import type { Slug } from "react-muscle-highlighter";

// ════════════════════════════════════════════════════════════
// ZONE INTERFACE
// ════════════════════════════════════════════════════════════

export interface BodyZone {
  /** Identificativo unico zona */
  id: string;
  /** Label italiano per chip */
  label: string;
  /** IDs metriche di circonferenza associate (1 o 2 per bilaterali) */
  metricIds: number[];
  /** Slugs react-muscle-highlighter per evidenziare la zona */
  slugs: Slug[];
  /** Body tags per matching condizioni anamnesi */
  bodyTags: string[];
  /** Muscle groups (chiave MUSCLE_SLUG_MAP) per matching esercizi */
  muscleGroups: string[];
}

// ════════════════════════════════════════════════════════════
// ZONE CONFIGURATION — 8 aree del corpo
// ════════════════════════════════════════════════════════════

export const BODY_ZONES: BodyZone[] = [
  {
    id: "collo",
    label: "Collo",
    metricIds: [7],
    slugs: ["trapezius", "neck"],
    bodyTags: ["collo", "cervicale"],
    muscleGroups: ["traps"],
  },
  {
    id: "petto",
    label: "Petto",
    metricIds: [8],
    slugs: ["chest"],
    bodyTags: ["respiratorio"],
    muscleGroups: ["chest"],
  },
  {
    id: "vita",
    label: "Vita",
    metricIds: [9],
    slugs: ["abs", "obliques"],
    bodyTags: ["addome"],
    muscleGroups: ["core"],
  },
  {
    id: "fianchi",
    label: "Fianchi",
    metricIds: [10],
    slugs: ["gluteal", "adductors"],
    bodyTags: ["anca"],
    muscleGroups: ["glutes", "adductors"],
  },
  {
    id: "braccia",
    label: "Braccia",
    metricIds: [11, 12],
    slugs: ["biceps", "triceps", "deltoids"],
    bodyTags: ["spalla", "gomito"],
    muscleGroups: ["biceps", "triceps", "shoulders"],
  },
  {
    id: "schiena",
    label: "Schiena",
    metricIds: [], // Nessuna metrica di circonferenza — inclusa per esercizi + anamnesi
    slugs: ["upper-back", "lower-back"],
    bodyTags: ["schiena", "lombare"],
    muscleGroups: ["back", "lats"],
  },
  {
    id: "cosce",
    label: "Cosce",
    metricIds: [13, 14],
    slugs: ["quadriceps", "hamstring", "adductors"],
    bodyTags: ["ginocchio"],
    muscleGroups: ["quadriceps", "hamstrings", "adductors"],
  },
  {
    id: "polpacci",
    label: "Polpacci",
    metricIds: [15, 16],
    slugs: ["calves"],
    bodyTags: ["caviglia", "piede", "gamba"],
    muscleGroups: ["calves"],
  },
];

// ════════════════════════════════════════════════════════════
// REVERSE MAP: slug → zone ID (per onBodyPartPress)
// ════════════════════════════════════════════════════════════

export const SLUG_TO_ZONE_MAP = new Map<string, string>();
for (const zone of BODY_ZONES) {
  for (const slug of zone.slugs) {
    // Se piu' zone condividono uno slug, il primo vince (ok — no conflict nel nostro set)
    if (!SLUG_TO_ZONE_MAP.has(slug)) {
      SLUG_TO_ZONE_MAP.set(slug, zone.id);
    }
  }
}
