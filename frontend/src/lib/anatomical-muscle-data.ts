// src/lib/anatomical-muscle-data.ts
/**
 * Dati SVG per la mappa muscolare anatomica interattiva.
 *
 * ViewBox: 0 0 200 440
 * Due viste: anteriore (front) e posteriore (back).
 * ~27 zone muscolari mappate ai 15 gruppi backend (GruppoMuscolare).
 *
 * Ogni zona e' un path SVG con coordinate derivate da landmark anatomici:
 *   Shoulder peak: y=78, Armpit: y=100, Waist: y=180,
 *   Hip: y=210, Crotch: y=248, Knee: y=325, Ankle: y=410
 */

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

export interface MuscleZone {
  id: string;
  group: string;         // backend GruppoMuscolare name
  view: "front" | "back";
  d: string;             // SVG path d attribute
}

// ════════════════════════════════════════════════════════════
// BODY SILHOUETTE OUTLINES
// ════════════════════════════════════════════════════════════

export const BODY_OUTLINE_FRONT =
  "M100,8 C82,8 78,22 78,36 C78,46 84,52 90,55 L90,68 Q72,72 58,78" +
  " Q40,85 36,98 L28,148 L20,220 L24,230 L32,226 L38,185 Q44,140 50,108" +
  " L58,104 L62,130 Q66,175 68,210 L64,270 Q60,310 58,340 L56,390 L58,415" +
  " L54,432 L86,435 L88,418 Q86,380 88,340 L92,310 Q96,270 98,248" +
  " L100,245 L102,248 Q104,270 108,310 L112,340 Q114,380 112,418" +
  " L114,432 L146,435 L142,415 L142,390 Q140,350 138,340 L136,270" +
  " L132,210 Q134,175 138,130 L142,104 L150,108 Q156,140 162,185" +
  " L168,226 L176,230 L180,220 L172,148 L164,98 Q160,85 142,78" +
  " Q128,72 110,68 L110,55 C116,52 122,46 122,36 C122,22 118,8 100,8Z";

export const BODY_OUTLINE_BACK =
  "M100,8 C82,8 78,22 78,36 C78,46 84,52 90,55 L90,68 Q72,72 58,78" +
  " Q40,85 36,98 L28,148 L20,220 L24,230 L32,226 L38,185 Q44,140 48,108" +
  " L56,104 L60,130 Q64,170 66,200 L64,260 Q60,300 58,335 L56,385" +
  " L58,415 L54,432 L86,435 L88,418 Q86,380 88,340 L90,310 Q94,270 96,248" +
  " L100,242 L104,248 Q106,270 110,310 L112,340 Q114,380 112,418" +
  " L114,432 L146,435 L142,415 L142,385 Q140,350 138,335 L136,300" +
  " L134,260 Q136,170 140,130 L144,104 L152,108 Q156,140 162,185" +
  " L168,226 L176,230 L180,220 L172,148 L164,98 Q160,85 142,78" +
  " Q128,72 110,68 L110,55 C116,52 122,46 122,36 C122,22 118,8 100,8Z";

// ════════════════════════════════════════════════════════════
// FRONT VIEW MUSCLE ZONES
// ════════════════════════════════════════════════════════════

const FRONT_ZONES: MuscleZone[] = [
  // Deltoids (anterior)
  { id: "delt_front_l", group: "deltoide_anteriore", view: "front",
    d: "M58,78 Q48,70 40,80 Q36,90 38,100 L50,104 L60,96 Q62,86 58,78Z" },
  { id: "delt_front_r", group: "deltoide_anteriore", view: "front",
    d: "M142,78 Q152,70 160,80 Q164,90 162,100 L150,104 L140,96 Q138,86 142,78Z" },
  // Pectorals
  { id: "pec_l", group: "petto", view: "front",
    d: "M60,96 L98,90 L98,138 Q86,144 74,136 Q62,126 58,108 L60,96Z" },
  { id: "pec_r", group: "petto", view: "front",
    d: "M140,96 L102,90 L102,138 Q114,144 126,136 Q138,126 142,108 L140,96Z" },
  // Biceps
  { id: "bicep_l", group: "bicipiti", view: "front",
    d: "M38,104 L50,104 Q54,118 52,138 Q50,156 44,166 L32,160 Q28,146 30,128 Q32,114 38,104Z" },
  { id: "bicep_r", group: "bicipiti", view: "front",
    d: "M162,104 L150,104 Q146,118 148,138 Q150,156 156,166 L168,160 Q172,146 170,128 Q168,114 162,104Z" },
  // Forearms
  { id: "forearm_l", group: "avambracci", view: "front",
    d: "M32,164 L44,168 Q46,188 42,212 L36,226 L26,220 Q24,200 28,178Z" },
  { id: "forearm_r", group: "avambracci", view: "front",
    d: "M168,164 L156,168 Q154,188 158,212 L164,226 L174,220 Q176,200 172,178Z" },
  // Core (abs + obliques)
  { id: "core_front", group: "core", view: "front",
    d: "M78,142 L98,138 L102,138 L122,142 Q130,162 132,186 L130,210 Q122,222 108,230" +
       " L100,232 L92,230 Q78,222 70,210 L68,186 Q70,162 78,142Z" },
  // Quadriceps
  { id: "quad_l", group: "quadricipiti", view: "front",
    d: "M70,216 Q76,230 86,244 L92,250 L92,318 Q84,326 76,330 L66,324 Q60,296 64,262 Q66,238 70,216Z" },
  { id: "quad_r", group: "quadricipiti", view: "front",
    d: "M130,216 Q124,230 114,244 L108,250 L108,318 Q116,326 124,330 L134,324 Q140,296 136,262 Q134,238 130,216Z" },
  // Adductors (inner thighs)
  { id: "adductor", group: "adduttori", view: "front",
    d: "M86,244 Q94,252 100,256 Q106,252 114,244 L114,316 Q108,322 100,324 Q92,322 86,316Z" },
  // Calves (tibialis anterior)
  { id: "calf_front_l", group: "polpacci", view: "front",
    d: "M66,334 L76,330 Q80,348 80,372 Q78,396 74,410 L64,414 Q58,396 60,368 Q62,350 66,334Z" },
  { id: "calf_front_r", group: "polpacci", view: "front",
    d: "M134,334 L124,330 Q120,348 120,372 Q122,396 126,410 L136,414 Q142,396 140,368 Q138,350 134,334Z" },
];

// ════════════════════════════════════════════════════════════
// BACK VIEW MUSCLE ZONES
// ════════════════════════════════════════════════════════════

const BACK_ZONES: MuscleZone[] = [
  // Trapezius
  { id: "trap", group: "trapezio", view: "back",
    d: "M76,66 Q84,56 100,52 Q116,56 124,66 L134,80 Q128,88 118,86 L100,84" +
       " L82,86 Q72,88 66,80Z" },
  // Lats / Back
  { id: "lat_l", group: "dorsali", view: "back",
    d: "M64,92 L82,88 L98,84 L98,182 Q84,188 72,178 Q62,158 58,132 Q58,110 64,92Z" },
  { id: "lat_r", group: "dorsali", view: "back",
    d: "M136,92 L118,88 L102,84 L102,182 Q116,188 128,178 Q138,158 142,132 Q142,110 136,92Z" },
  // Rear deltoids
  { id: "delt_rear_l", group: "deltoide_posteriore", view: "back",
    d: "M58,78 Q48,70 40,80 Q36,90 38,100 L48,104 L58,96 Q60,86 58,78Z" },
  { id: "delt_rear_r", group: "deltoide_posteriore", view: "back",
    d: "M142,78 Q152,70 160,80 Q164,90 162,100 L152,104 L142,96 Q140,86 142,78Z" },
  // Triceps
  { id: "tricep_l", group: "tricipiti", view: "back",
    d: "M38,104 L48,104 Q52,120 50,140 Q48,158 42,168 L30,162 Q26,148 28,130 Q30,114 38,104Z" },
  { id: "tricep_r", group: "tricipiti", view: "back",
    d: "M162,104 L152,104 Q148,120 150,140 Q152,158 158,168 L170,162 Q174,148 172,130 Q170,114 162,104Z" },
  // Forearms (back)
  { id: "forearm_back_l", group: "avambracci", view: "back",
    d: "M30,166 L42,170 Q44,190 40,214 L34,228 L24,222 Q22,202 26,182Z" },
  { id: "forearm_back_r", group: "avambracci", view: "back",
    d: "M170,166 L158,170 Q156,190 160,214 L166,228 L176,222 Q178,202 174,182Z" },
  // Glutes
  { id: "glute_l", group: "glutei", view: "back",
    d: "M68,196 Q78,190 98,188 L98,242 L86,250 Q72,248 64,234 Q62,218 68,196Z" },
  { id: "glute_r", group: "glutei", view: "back",
    d: "M132,196 Q122,190 102,188 L102,242 L114,250 Q128,248 136,234 Q138,218 132,196Z" },
  // Hamstrings
  { id: "ham_l", group: "femorali", view: "back",
    d: "M64,252 L86,254 L88,320 Q82,328 74,334 L62,328 Q56,308 58,282 Q60,264 64,252Z" },
  { id: "ham_r", group: "femorali", view: "back",
    d: "M136,252 L114,254 L112,320 Q118,328 126,334 L138,328 Q144,308 142,282 Q140,264 136,252Z" },
  // Calves (gastrocnemius)
  { id: "calf_back_l", group: "polpacci", view: "back",
    d: "M62,338 L74,334 Q80,350 82,374 Q80,398 76,412 L64,416 Q58,398 58,370 Q60,352 62,338Z" },
  { id: "calf_back_r", group: "polpacci", view: "back",
    d: "M138,338 L126,334 Q120,350 118,374 Q120,398 124,412 L136,416 Q142,398 142,370 Q140,352 138,338Z" },
];

// ════════════════════════════════════════════════════════════
// EXPORTS
// ════════════════════════════════════════════════════════════

export const ALL_ZONES: MuscleZone[] = [...FRONT_ZONES, ...BACK_ZONES];

/** Zones visible in front view */
export const FRONT_VIEW_ZONES = FRONT_ZONES;

/** Zones visible in back view */
export const BACK_VIEW_ZONES = BACK_ZONES;

/** Italian labels for backend muscle group names */
export const MUSCLE_GROUP_LABELS: Record<string, string> = {
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

/** Status → fill color for light and dark themes */
export const STATUS_FILLS = {
  deficit:    { light: "#ef4444", dark: "#f87171" },   // red-500 / red-400
  suboptimal: { light: "#3b82f6", dark: "#60a5fa" },   // blue-500 / blue-400
  optimal:    { light: "#10b981", dark: "#34d399" },    // emerald-500 / emerald-400
  excess:     { light: "#f59e0b", dark: "#fbbf24" },    // amber-500 / amber-400
  untrained:  { light: "#e5e7eb", dark: "#3f3f46" },    // zinc-200 / zinc-700
} as const;

/** Status → Italian label */
export const STATUS_LABELS: Record<string, string> = {
  deficit: "Deficit",
  suboptimal: "Sotto-ottimale",
  optimal: "Ottimale",
  excess: "Eccesso",
  untrained: "Non allenato",
};
