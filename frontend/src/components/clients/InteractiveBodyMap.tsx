// src/components/clients/InteractiveBodyMap.tsx
"use client";

/**
 * InteractiveBodyMap — Cartella clinica interattiva.
 *
 * Mappa corporea cliccabile che incrocia 3 fonti dati:
 *   1. Misurazioni (circonferenze → valore + delta + sparkline)
 *   2. Esercizi (dalle schede del cliente → quali esercizi lavorano questa zona)
 *   3. Anamnesi (condizioni cliniche → severity per zona)
 *
 * 2 modi di selezione zona:
 *   - Click diretto su silhouette SVG (onBodyPartPress nativo)
 *   - Click su zone chip buttons
 *
 * Layout: split desktop (body | detail), stacked mobile.
 */

import { useMemo, useState, useEffect } from "react";
import { useTheme } from "next-themes";
import Body from "react-muscle-highlighter";
import type { ExtendedBodyPart } from "react-muscle-highlighter";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  ClipboardList,
  Dumbbell,
  Ruler,
  ShieldAlert,
} from "lucide-react";
import { Line, LineChart, ResponsiveContainer } from "recharts";

import { Card, CardContent } from "@/components/ui/card";
import { FRONT_SLUGS, BACK_SLUGS } from "@/lib/muscle-map-utils";
import { BODY_ZONES, SLUG_TO_ZONE_MAP } from "@/lib/body-zone-config";
import type { BodyZone } from "@/lib/body-zone-config";
import { useClientWorkouts } from "@/hooks/useWorkouts";
import { useExercises, useExerciseSafetyMap } from "@/hooks/useExercises";
import type {
  Measurement,
  Metric,
  Exercise,
  SafetyConditionDetail,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// CONSTANTS
// ════════════════════════════════════════════════════════════

const COLOR_TEAL_LIGHT = "oklch(0.55 0.15 170)";
const COLOR_TEAL_DARK = "oklch(0.70 0.15 170)";

// Metriche dove calare e' positivo (per delta color nel detail)
const LOWER_IS_BETTER_IDS = new Set([9, 10]); // Vita, Fianchi

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

interface InteractiveBodyMapProps {
  clientId: number;
  measurements: Measurement[];
  metrics: Metric[];
}

interface ZoneMetricData {
  metricId: number;
  label: string;
  latestValue: number | null;
  delta: number | null;
  unita: string;
  history: { date: string; value: number }[];
}

interface ZoneExerciseData {
  id: number;
  nome: string;
  categoria: string;
  serie: number;
  ripetizioni: string;
  schedaNome: string;
}

interface ZoneConditionData {
  nome: string;
  severita: "avoid" | "caution";
  nota: string | null;
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function InteractiveBodyMap({
  clientId,
  measurements,
  metrics,
}: InteractiveBodyMapProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);

  // Responsive
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 768px)");
    setIsMobile(mq.matches);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  // ── Hooks per dati incrociati ──
  const { data: workoutsData } = useClientWorkouts(clientId);
  const { data: exercisesData } = useExercises();
  const { data: safetyMap } = useExerciseSafetyMap(clientId);

  // ── Exercise catalog map ──
  const exerciseCatalog = useMemo(() => {
    if (!exercisesData) return new Map<number, Exercise>();
    return new Map(exercisesData.items.map((e) => [e.id, e]));
  }, [exercisesData]);

  // ── Metric map ──
  const metricMap = useMemo(
    () => new Map(metrics.map((m) => [m.id, m])),
    [metrics]
  );

  // ════════════════════════════════════════════════════════════
  // DATA COMPUTATION — Pre-compute per tutte le zone
  // ════════════════════════════════════════════════════════════

  // A. Measurement data per zone
  const zoneMetrics = useMemo(() => {
    const result = new Map<string, ZoneMetricData[]>();

    for (const zone of BODY_ZONES) {
      if (zone.metricIds.length === 0) {
        result.set(zone.id, []);
        continue;
      }

      const zoneData: ZoneMetricData[] = [];
      for (const metricId of zone.metricIds) {
        const metric = metricMap.get(metricId);
        if (!metric) continue;

        // Latest value (measurements[0] = most recent, DESC from API)
        const latestVal = measurements[0]?.valori.find(
          (v) => v.id_metrica === metricId
        );
        const prevVal =
          measurements.length >= 2
            ? measurements[1]?.valori.find((v) => v.id_metrica === metricId)
            : null;

        // History (chronological order for sparkline)
        const history: { date: string; value: number }[] = [];
        for (let i = measurements.length - 1; i >= 0; i--) {
          const val = measurements[i].valori.find(
            (v) => v.id_metrica === metricId
          );
          if (val) {
            history.push({
              date: measurements[i].data_misurazione,
              value: val.valore,
            });
          }
        }

        zoneData.push({
          metricId,
          label: metric.nome,
          latestValue: latestVal?.valore ?? null,
          delta:
            latestVal && prevVal ? latestVal.valore - prevVal.valore : null,
          unita: metric.unita_misura,
          history,
        });
      }
      result.set(zone.id, zoneData);
    }

    return result;
  }, [measurements, metricMap]);

  // B. Exercise data per zone
  const zoneExercises = useMemo(() => {
    const result = new Map<string, ZoneExerciseData[]>();
    if (!workoutsData) return result;

    // Build set of muscle groups per zone
    const zoneGroupSets = new Map<string, Set<string>>();
    for (const zone of BODY_ZONES) {
      zoneGroupSets.set(zone.id, new Set(zone.muscleGroups));
    }

    for (const zone of BODY_ZONES) {
      result.set(zone.id, []);
    }

    // Iterate all workouts → sessions → exercises
    const seenExercises = new Map<string, Set<number>>(); // zone → exercise IDs
    for (const zone of BODY_ZONES) {
      seenExercises.set(zone.id, new Set());
    }

    for (const workout of workoutsData.items) {
      for (const session of workout.sessioni) {
        for (const row of session.esercizi) {
          const exercise = exerciseCatalog.get(row.id_esercizio);
          if (!exercise) continue;

          // Check which zones this exercise targets
          const exerciseMuscles = [
            ...(exercise.muscoli_primari ?? []),
            ...(exercise.muscoli_secondari ?? []),
          ];

          for (const zone of BODY_ZONES) {
            const groups = zoneGroupSets.get(zone.id)!;
            const seen = seenExercises.get(zone.id)!;
            if (seen.has(row.id_esercizio)) continue;

            const matches = exerciseMuscles.some((m) => groups.has(m));
            if (matches) {
              seen.add(row.id_esercizio);
              result.get(zone.id)!.push({
                id: row.id_esercizio,
                nome: row.esercizio_nome,
                categoria: row.esercizio_categoria,
                serie: row.serie,
                ripetizioni: row.ripetizioni,
                schedaNome: workout.nome,
              });
            }
          }
        }
      }
    }

    return result;
  }, [workoutsData, exerciseCatalog]);

  // C. Anamnesi conditions per zone
  const zoneConditions = useMemo(() => {
    const result = new Map<string, ZoneConditionData[]>();
    for (const zone of BODY_ZONES) {
      result.set(zone.id, []);
    }

    if (!safetyMap || safetyMap.condition_count === 0) return result;

    // Collect unique conditions from all exercise entries
    const allConditions = new Map<number, SafetyConditionDetail>();
    for (const entry of Object.values(safetyMap.entries)) {
      for (const c of entry.conditions) {
        if (!allConditions.has(c.id)) {
          allConditions.set(c.id, c);
        }
      }
    }

    // Match conditions to zones via body_tags
    for (const condition of allConditions.values()) {
      for (const zone of BODY_ZONES) {
        const tagOverlap = zone.bodyTags.some((tag) =>
          condition.body_tags.includes(tag)
        );
        if (tagOverlap) {
          result.get(zone.id)!.push({
            nome: condition.nome,
            severita: condition.severita,
            nota: condition.nota,
          });
        }
      }
    }

    return result;
  }, [safetyMap]);

  // D. Data availability per zone (per chip indicators)
  const zoneDataStatus = useMemo(() => {
    const status = new Map<
      string,
      { hasMeasurement: boolean; hasExercises: boolean; hasConditions: boolean }
    >();
    for (const zone of BODY_ZONES) {
      const metrics = zoneMetrics.get(zone.id) ?? [];
      const exercises = zoneExercises.get(zone.id) ?? [];
      const conditions = zoneConditions.get(zone.id) ?? [];
      status.set(zone.id, {
        hasMeasurement: metrics.some((m) => m.latestValue !== null),
        hasExercises: exercises.length > 0,
        hasConditions: conditions.length > 0,
      });
    }
    return status;
  }, [zoneMetrics, zoneExercises, zoneConditions]);

  // ════════════════════════════════════════════════════════════
  // SVG BODY HIGHLIGHT
  // ════════════════════════════════════════════════════════════

  const selectedZone = selectedZoneId
    ? BODY_ZONES.find((z) => z.id === selectedZoneId) ?? null
    : null;

  const frontData = useMemo((): ExtendedBodyPart[] => {
    if (!selectedZone) return [];
    return selectedZone.slugs
      .filter((slug) => FRONT_SLUGS.has(slug))
      .map((slug) => ({ slug, intensity: 1 }));
  }, [selectedZone]);

  const backData = useMemo((): ExtendedBodyPart[] => {
    if (!selectedZone) return [];
    return selectedZone.slugs
      .filter((slug) => BACK_SLUGS.has(slug))
      .map((slug) => ({ slug, intensity: 1 }));
  }, [selectedZone]);

  const bodyScale = isMobile ? 0.85 : 1.1;
  const defaultFill = isDark ? "#3f3f46" : "#e5e7eb";
  const highlightColors = isDark
    ? [COLOR_TEAL_DARK]
    : [COLOR_TEAL_LIGHT];

  // ── Handlers ──
  const handleBodyPartPress = (part: ExtendedBodyPart) => {
    const slug = part.slug;
    if (!slug) return;
    const zoneId = SLUG_TO_ZONE_MAP.get(slug);
    if (zoneId) {
      setSelectedZoneId((prev) => (prev === zoneId ? null : zoneId));
    }
  };

  const handleChipClick = (zoneId: string) => {
    setSelectedZoneId((prev) => (prev === zoneId ? null : zoneId));
  };

  // Se nessun dato in nessuna zona → non mostrare la mappa
  const hasAnyData = [...zoneDataStatus.values()].some(
    (s) => s.hasMeasurement || s.hasExercises || s.hasConditions
  );
  if (!hasAnyData && measurements.length === 0) return null;

  return (
    <Card>
      <CardContent className="pt-6 space-y-4">
        <h3 className="text-sm font-semibold">Mappa Corporea Interattiva</h3>

        {/* ── Zone Chips ── */}
        <div className="flex flex-wrap gap-1.5">
          {BODY_ZONES.map((zone) => {
            const isActive = selectedZoneId === zone.id;
            const status = zoneDataStatus.get(zone.id);
            return (
              <button
                key={zone.id}
                onClick={() => handleChipClick(zone.id)}
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-teal-600 text-white shadow-sm dark:bg-teal-500"
                    : "bg-muted/50 text-muted-foreground hover:bg-muted"
                }`}
              >
                {zone.label}
                {status && (status.hasMeasurement || status.hasExercises || status.hasConditions) && (
                  <span className="flex gap-0.5">
                    {status.hasMeasurement && (
                      <span className={`h-1.5 w-1.5 rounded-full ${isActive ? "bg-white/70" : "bg-emerald-400"}`} />
                    )}
                    {status.hasExercises && (
                      <span className={`h-1.5 w-1.5 rounded-full ${isActive ? "bg-white/70" : "bg-blue-400"}`} />
                    )}
                    {status.hasConditions && (
                      <span className={`h-1.5 w-1.5 rounded-full ${isActive ? "bg-white/70" : "bg-amber-400"}`} />
                    )}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* ── Body + Detail Panel ── */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Left: Body SVG */}
          <div className="flex flex-col items-center">
            <div className="flex items-start justify-center gap-2 sm:gap-4">
              {/* Front */}
              <div className="flex flex-col items-center gap-1">
                <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                  Anteriore
                </span>
                <div className="cursor-pointer overflow-hidden">
                  <Body
                    data={frontData}
                    side="front"
                    gender="male"
                    scale={bodyScale}
                    colors={highlightColors}
                    border="none"
                    defaultFill={defaultFill}
                    onBodyPartPress={handleBodyPartPress}
                  />
                </div>
              </div>

              {/* Back */}
              <div className="flex flex-col items-center gap-1">
                <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                  Posteriore
                </span>
                <div className="cursor-pointer overflow-hidden">
                  <Body
                    data={backData}
                    side="back"
                    gender="male"
                    scale={bodyScale}
                    colors={highlightColors}
                    border="none"
                    defaultFill={defaultFill}
                    onBodyPartPress={handleBodyPartPress}
                  />
                </div>
              </div>
            </div>

            {!selectedZone && (
              <p className="mt-2 text-xs text-muted-foreground">
                Tocca un&apos;area del corpo o seleziona una zona
              </p>
            )}
          </div>

          {/* Right: Detail Panel */}
          {selectedZone && (
            <ZoneDetailPanel
              zone={selectedZone}
              metricsData={zoneMetrics.get(selectedZone.id) ?? []}
              exercisesData={zoneExercises.get(selectedZone.id) ?? []}
              conditionsData={zoneConditions.get(selectedZone.id) ?? []}
              hasAnamnesi={safetyMap?.has_anamnesi ?? false}
              isDark={isDark}
            />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ════════════════════════════════════════════════════════════
// ZONE DETAIL PANEL
// ════════════════════════════════════════════════════════════

function ZoneDetailPanel({
  zone,
  metricsData,
  exercisesData,
  conditionsData,
  hasAnamnesi,
  isDark,
}: {
  zone: BodyZone;
  metricsData: ZoneMetricData[];
  exercisesData: ZoneExerciseData[];
  conditionsData: ZoneConditionData[];
  hasAnamnesi: boolean;
  isDark: boolean;
}) {
  // Narrative string
  const narrative = useMemo(() => {
    if (metricsData.length === 0 || exercisesData.length === 0) return null;
    const bestMetric = metricsData
      .filter((m) => m.delta !== null && m.delta !== 0)
      .sort((a, b) => Math.abs(b.delta ?? 0) - Math.abs(a.delta ?? 0))[0];
    if (!bestMetric || bestMetric.delta === null) return null;

    const sign = bestMetric.delta > 0 ? "+" : "";
    const schedaCount = new Set(exercisesData.map((e) => e.schedaNome)).size;
    return `${bestMetric.label}: ${sign}${bestMetric.delta.toFixed(1)} ${bestMetric.unita} con ${exercisesData.length} ${exercisesData.length === 1 ? "esercizio" : "esercizi"} in ${schedaCount} ${schedaCount === 1 ? "scheda" : "schede"}`;
  }, [metricsData, exercisesData]);

  return (
    <div className="space-y-4">
      {/* Zone title */}
      <div className="flex items-center gap-2">
        <div className="h-3 w-3 rounded-full bg-teal-500" />
        <h4 className="text-base font-bold">{zone.label}</h4>
      </div>

      {/* Narrative */}
      {narrative && (
        <div className="rounded-lg bg-teal-50 px-3 py-2 text-xs font-medium text-teal-800 dark:bg-teal-950/30 dark:text-teal-300">
          {narrative}
        </div>
      )}

      {/* ── Sezione 1: Misurazioni ── */}
      <div className="space-y-2">
        <div className="flex items-center gap-1.5">
          <Ruler className="h-3.5 w-3.5 text-emerald-500" />
          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Misurazioni
          </span>
        </div>

        {metricsData.length === 0 || metricsData.every((m) => m.latestValue === null) ? (
          <p className="text-xs text-muted-foreground">
            Nessuna misurazione per questa zona
          </p>
        ) : (
          <div className={`grid gap-3 ${metricsData.length > 1 ? "grid-cols-2" : "grid-cols-1"}`}>
            {metricsData
              .filter((m) => m.latestValue !== null)
              .map((m) => (
                <div key={m.metricId} className="space-y-1">
                  <span className="text-[10px] font-medium text-muted-foreground">
                    {m.label}
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-extrabold tracking-tighter tabular-nums">
                      {m.latestValue} {m.unita}
                    </span>
                    {m.delta !== null && m.delta !== 0 && (
                      <MetricDeltaBadge
                        delta={m.delta}
                        unita={m.unita}
                        metricId={m.metricId}
                      />
                    )}
                  </div>
                  {m.history.length >= 2 && (
                    <MiniSparkline data={m.history} isDark={isDark} />
                  )}
                </div>
              ))}
          </div>
        )}
      </div>

      {/* ── Sezione 2: Esercizi Collegati ── */}
      <div className="space-y-2">
        <div className="flex items-center gap-1.5">
          <Dumbbell className="h-3.5 w-3.5 text-blue-500" />
          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Esercizi Collegati
          </span>
        </div>

        {exercisesData.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            Nessun esercizio collegato a questa zona
          </p>
        ) : (
          <div className="space-y-1.5">
            {exercisesData.slice(0, 6).map((ex) => (
              <div
                key={ex.id}
                className="flex items-center justify-between rounded-md bg-muted/30 px-2.5 py-1.5"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-xs font-medium truncate">
                    {ex.nome}
                  </span>
                </div>
                <span className="text-[10px] text-muted-foreground whitespace-nowrap ml-2 tabular-nums">
                  {ex.serie}×{ex.ripetizioni}
                </span>
              </div>
            ))}
            {exercisesData.length > 6 && (
              <p className="text-[10px] text-muted-foreground text-center">
                +{exercisesData.length - 6} altri esercizi
              </p>
            )}
          </div>
        )}
      </div>

      {/* ── Sezione 3: Note Cliniche ── */}
      <div className="space-y-2">
        <div className="flex items-center gap-1.5">
          <ClipboardList className="h-3.5 w-3.5 text-amber-500" />
          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Note Cliniche
          </span>
        </div>

        {!hasAnamnesi ? (
          <p className="text-xs text-muted-foreground">
            Compila l&apos;anamnesi per visualizzare le condizioni cliniche
          </p>
        ) : conditionsData.length === 0 ? (
          <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Nessuna condizione clinica per questa zona
          </div>
        ) : (
          <div className="space-y-1.5">
            {conditionsData.map((c) => (
              <div
                key={c.nome}
                className="flex items-start gap-2 rounded-md bg-muted/30 px-2.5 py-1.5"
              >
                {c.severita === "avoid" ? (
                  <ShieldAlert className="h-3.5 w-3.5 shrink-0 text-red-500 mt-0.5" />
                ) : (
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-500 mt-0.5" />
                )}
                <div className="min-w-0">
                  <span className="text-xs font-medium">{c.nome}</span>
                  {c.nota && (
                    <p className="text-[10px] text-muted-foreground mt-0.5">
                      {c.nota}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ════════════════════════════════════════════════════════════

function MetricDeltaBadge({
  delta,
  unita,
  metricId,
}: {
  delta: number;
  unita: string;
  metricId: number;
}) {
  const isPositive = delta > 0;
  const sign = isPositive ? "+" : "";
  const Icon = isPositive ? ArrowUpRight : ArrowDownRight;

  // Verde = aumento, Rosso = diminuzione
  const colorClass = isPositive
    ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400"
    : "bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400";

  return (
    <span
      className={`inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[10px] font-semibold tabular-nums ${colorClass}`}
    >
      <Icon className="h-2.5 w-2.5" />
      {sign}
      {delta.toFixed(1)} {unita}
    </span>
  );
}

function MiniSparkline({
  data,
  isDark,
}: {
  data: { date: string; value: number }[];
  isDark: boolean;
}) {
  if (data.length < 2) return null;
  const color = isDark ? COLOR_TEAL_DARK : COLOR_TEAL_LIGHT;

  return (
    <div className="h-8 w-full max-w-[120px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
