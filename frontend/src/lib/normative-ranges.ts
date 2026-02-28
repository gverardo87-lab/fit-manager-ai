// src/lib/normative-ranges.ts
/**
 * Range Normativi — Dati scientifici OMS/ACSM/AHA/ESH per metriche corporee.
 *
 * Fonti:
 *   - BMI: OMS (WHO) — classificazione universale
 *   - Massa Grassa %: ACSM Guidelines (10th ed.) — per sesso × eta'
 *   - FC Riposo: AHA (American Heart Association) — adulti
 *   - PA Sistolica/Diastolica: ESH/ESC 2023 — classificazione europea
 *   - WHR: OMS (WHO) — per sesso
 *
 * Usato da: KPI cards (badge fascia), MeasurementChart (bande),
 *           GoalFormDialog (hint target), InteractiveBodyMap (range badge).
 */

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

export interface NormativeBand {
  label: string;
  min: number | null; // null = no lower bound
  max: number | null; // null = no upper bound
  color: string; // tailwind color name: "emerald" | "amber" | "rose" etc.
}

interface NormativeEntry {
  metricId: number;
  sesso: "M" | "F" | "tutti";
  etaMin: number;
  etaMax: number;
  bands: NormativeBand[];
}

// ════════════════════════════════════════════════════════════
// NORMATIVE DATA
// ════════════════════════════════════════════════════════════

const NORMATIVE_DATA: NormativeEntry[] = [
  // ── BMI (id=5) — OMS, universale ──
  {
    metricId: 5,
    sesso: "tutti",
    etaMin: 18,
    etaMax: 99,
    bands: [
      { label: "Sottopeso", min: null, max: 18.49, color: "amber" },
      { label: "Normopeso", min: 18.5, max: 24.9, color: "emerald" },
      { label: "Sovrappeso", min: 25.0, max: 29.9, color: "amber" },
      { label: "Obesita' I", min: 30.0, max: 34.9, color: "orange" },
      { label: "Obesita' II", min: 35.0, max: 39.9, color: "rose" },
      { label: "Obesita' III", min: 40.0, max: null, color: "rose" },
    ],
  },

  // ── Massa Grassa % (id=3) — ACSM, Uomo per fascia eta' ──
  ...[
    { etaMin: 20, etaMax: 29, essMax: 5, atlMax: 13, fitMax: 17, accMax: 24 },
    { etaMin: 30, etaMax: 39, essMax: 5, atlMax: 14, fitMax: 18, accMax: 25 },
    { etaMin: 40, etaMax: 49, essMax: 5, atlMax: 16, fitMax: 20, accMax: 27 },
    { etaMin: 50, etaMax: 59, essMax: 5, atlMax: 17, fitMax: 21, accMax: 28 },
    { etaMin: 60, etaMax: 99, essMax: 5, atlMax: 18, fitMax: 22, accMax: 29 },
  ].map(
    (r): NormativeEntry => ({
      metricId: 3,
      sesso: "M",
      etaMin: r.etaMin,
      etaMax: r.etaMax,
      bands: [
        { label: "Essenziale", min: null, max: r.essMax, color: "sky" },
        { label: "Atletico", min: r.essMax + 0.1, max: r.atlMax, color: "emerald" },
        { label: "Fitness", min: r.atlMax + 0.1, max: r.fitMax, color: "teal" },
        { label: "Accettabile", min: r.fitMax + 0.1, max: r.accMax, color: "amber" },
        { label: "Sovrappeso", min: r.accMax + 0.1, max: null, color: "rose" },
      ],
    })
  ),

  // ── Massa Grassa % (id=3) — ACSM, Donna per fascia eta' ──
  ...[
    { etaMin: 20, etaMax: 29, essMax: 13, atlMax: 20, fitMax: 24, accMax: 31 },
    { etaMin: 30, etaMax: 39, essMax: 13, atlMax: 21, fitMax: 25, accMax: 32 },
    { etaMin: 40, etaMax: 49, essMax: 13, atlMax: 23, fitMax: 27, accMax: 34 },
    { etaMin: 50, etaMax: 59, essMax: 13, atlMax: 24, fitMax: 28, accMax: 35 },
    { etaMin: 60, etaMax: 99, essMax: 13, atlMax: 25, fitMax: 29, accMax: 36 },
  ].map(
    (r): NormativeEntry => ({
      metricId: 3,
      sesso: "F",
      etaMin: r.etaMin,
      etaMax: r.etaMax,
      bands: [
        { label: "Essenziale", min: null, max: r.essMax, color: "sky" },
        { label: "Atletico", min: r.essMax + 0.1, max: r.atlMax, color: "emerald" },
        { label: "Fitness", min: r.atlMax + 0.1, max: r.fitMax, color: "teal" },
        { label: "Accettabile", min: r.fitMax + 0.1, max: r.accMax, color: "amber" },
        { label: "Sovrappeso", min: r.accMax + 0.1, max: null, color: "rose" },
      ],
    })
  ),

  // ── FC Riposo (id=17) — AHA, adulti ──
  {
    metricId: 17,
    sesso: "tutti",
    etaMin: 18,
    etaMax: 99,
    bands: [
      { label: "Atletico", min: null, max: 59, color: "sky" },
      { label: "Eccellente", min: 60, max: 64, color: "emerald" },
      { label: "Buono", min: 65, max: 72, color: "teal" },
      { label: "Nella media", min: 73, max: 80, color: "amber" },
      { label: "Sotto la media", min: 81, max: 90, color: "orange" },
      { label: "Scadente", min: 91, max: null, color: "rose" },
    ],
  },

  // ── PA Sistolica (id=18) — ESH/ESC 2023 ──
  {
    metricId: 18,
    sesso: "tutti",
    etaMin: 18,
    etaMax: 99,
    bands: [
      { label: "Ottimale", min: null, max: 119, color: "emerald" },
      { label: "Normale", min: 120, max: 129, color: "teal" },
      { label: "Normale-alta", min: 130, max: 139, color: "amber" },
      { label: "Ipertensione I", min: 140, max: 159, color: "orange" },
      { label: "Ipertensione II", min: 160, max: null, color: "rose" },
    ],
  },

  // ── PA Diastolica (id=19) — ESH/ESC 2023 ──
  {
    metricId: 19,
    sesso: "tutti",
    etaMin: 18,
    etaMax: 99,
    bands: [
      { label: "Ottimale", min: null, max: 79, color: "emerald" },
      { label: "Normale", min: 80, max: 84, color: "teal" },
      { label: "Normale-alta", min: 85, max: 89, color: "amber" },
      { label: "Ipertensione I", min: 90, max: 99, color: "orange" },
      { label: "Ipertensione II", min: 100, max: null, color: "rose" },
    ],
  },
];

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

/** Calcola eta' da data di nascita ISO. */
export function computeAge(dataNascita: string | null | undefined): number | null {
  if (!dataNascita) return null;
  const birth = new Date(dataNascita + "T00:00:00");
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}

/** Normalizza sesso per lookup: "Uomo" → "M", "Donna" → "F". */
function normSesso(sesso: string | null | undefined): "M" | "F" | null {
  if (!sesso) return null;
  const s = sesso.toLowerCase();
  if (s === "uomo" || s === "m" || s === "maschio") return "M";
  if (s === "donna" || s === "f" || s === "femmina") return "F";
  return null;
}

/** Trova entry normativa per metrica, sesso, eta'. */
function findEntry(
  metricId: number,
  sesso?: string | null,
  age?: number | null
): NormativeEntry | null {
  const norm = normSesso(sesso);
  const a = age ?? 30; // fallback eta' media se non specificata

  // Prima: cerca entry specifica per sesso
  if (norm) {
    const entry = NORMATIVE_DATA.find(
      (e) =>
        e.metricId === metricId &&
        (e.sesso === norm || e.sesso === "tutti") &&
        a >= e.etaMin &&
        a <= e.etaMax
    );
    if (entry) return entry;
  }

  // Fallback: entry universale
  return (
    NORMATIVE_DATA.find(
      (e) =>
        e.metricId === metricId &&
        e.sesso === "tutti" &&
        a >= e.etaMin &&
        a <= e.etaMax
    ) ?? null
  );
}

/**
 * Classifica un valore nella fascia normativa.
 * @returns { label, color } o null se metrica senza range normativi.
 */
export function classifyValue(
  metricId: number,
  value: number,
  sesso?: string | null,
  age?: number | null
): { label: string; color: string } | null {
  const entry = findEntry(metricId, sesso, age);
  if (!entry) return null;

  for (const band of entry.bands) {
    const aboveMin = band.min === null || value >= band.min;
    const belowMax = band.max === null || value <= band.max;
    if (aboveMin && belowMax) {
      return { label: band.label, color: band.color };
    }
  }

  return null;
}

/**
 * Ritorna le bande normative per una metrica (per chart ReferenceArea).
 * @returns Array di NormativeBand o null se metrica senza range.
 */
export function getNormativeBands(
  metricId: number,
  sesso?: string | null,
  age?: number | null
): NormativeBand[] | null {
  const entry = findEntry(metricId, sesso, age);
  return entry?.bands ?? null;
}

/**
 * Ritorna la fascia "sana" (la prima verde/emerald/teal) per hint target.
 * @returns { min, max, label } o null.
 */
export function getHealthyRange(
  metricId: number,
  sesso?: string | null,
  age?: number | null
): { min: number | null; max: number | null; label: string } | null {
  const entry = findEntry(metricId, sesso, age);
  if (!entry) return null;

  const healthy = entry.bands.find(
    (b) => b.color === "emerald" || b.color === "teal"
  );
  return healthy ? { min: healthy.min, max: healthy.max, label: healthy.label } : null;
}

// ════════════════════════════════════════════════════════════
// COLOR MAP (tailwind class mapping)
// ════════════════════════════════════════════════════════════

/** Mappa color name → classi tailwind per badge. */
export const BAND_COLOR_CLASSES: Record<string, { bg: string; text: string }> = {
  emerald: {
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
    text: "text-emerald-700 dark:text-emerald-400",
  },
  teal: {
    bg: "bg-teal-50 dark:bg-teal-950/30",
    text: "text-teal-700 dark:text-teal-400",
  },
  sky: {
    bg: "bg-sky-50 dark:bg-sky-950/30",
    text: "text-sky-700 dark:text-sky-400",
  },
  amber: {
    bg: "bg-amber-50 dark:bg-amber-950/30",
    text: "text-amber-700 dark:text-amber-400",
  },
  orange: {
    bg: "bg-orange-50 dark:bg-orange-950/30",
    text: "text-orange-700 dark:text-orange-400",
  },
  rose: {
    bg: "bg-rose-50 dark:bg-rose-950/30",
    text: "text-rose-700 dark:text-rose-400",
  },
};

/** Mappa color name → fill color per recharts ReferenceArea. */
export const BAND_CHART_FILLS: Record<string, string> = {
  emerald: "oklch(0.75 0.18 160 / 0.08)",
  teal: "oklch(0.70 0.15 170 / 0.08)",
  sky: "oklch(0.70 0.15 230 / 0.08)",
  amber: "oklch(0.80 0.15 80 / 0.08)",
  orange: "oklch(0.75 0.18 55 / 0.10)",
  rose: "oklch(0.65 0.20 15 / 0.08)",
};
