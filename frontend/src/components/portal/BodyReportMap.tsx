"use client";

/**
 * BodyReportMap — Referto corporeo clinico con silhouette e annotazioni.
 *
 * Silhouette SVG frontale con misurazioni posizionate come un disegno tecnico.
 * Click su annotazione o zona corpo → dettaglio metrica.
 * Stampabile come referto clinico.
 */

import { useMemo, useState } from "react";
import { useTheme } from "next-themes";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import Body from "react-muscle-highlighter";
import type { Slug } from "react-muscle-highlighter";

import { Badge } from "@/components/ui/badge";
import type { ExtendedBodyPart } from "react-muscle-highlighter";
import { FRONT_SLUGS } from "@/lib/muscle-map-utils";
import { computeWeeklyRate, formatRate } from "@/lib/measurement-analytics";
import { getLatestValue } from "@/lib/derived-metrics";
import type { Measurement, Metric } from "@/types/api";

// ── Annotation configs — posizioni relative al corpo ──

interface AnnotationConfig {
  metricId: number;
  label: string;
  side: "left" | "right";
  topPct: number;
  slugs: Slug[];
}

const ANNOTATIONS: AnnotationConfig[] = [
  { metricId: 12, label: "Braccio Sx", side: "left",  topPct: 28, slugs: ["biceps", "triceps", "deltoids"] },
  { metricId: 9,  label: "Vita",       side: "left",  topPct: 44, slugs: ["abs", "obliques"] },
  { metricId: 14, label: "Coscia Sx",  side: "left",  topPct: 62, slugs: ["quadriceps", "adductors"] },
  { metricId: 16, label: "Polp. Sx",   side: "left",  topPct: 79, slugs: ["calves"] },
  { metricId: 7,  label: "Collo",      side: "right", topPct: 12, slugs: ["trapezius", "neck"] },
  { metricId: 8,  label: "Torace",     side: "right", topPct: 26, slugs: ["chest"] },
  { metricId: 11, label: "Braccio Dx", side: "right", topPct: 38, slugs: ["biceps", "triceps", "deltoids"] },
  { metricId: 10, label: "Fianchi",    side: "right", topPct: 52, slugs: ["gluteal", "adductors"] },
  { metricId: 13, label: "Coscia Dx",  side: "right", topPct: 66, slugs: ["quadriceps", "adductors"] },
  { metricId: 15, label: "Polp. Dx",   side: "right", topPct: 79, slugs: ["calves"] },
];

// ── Slug → metricId reverse map for body click ──

const SLUG_TO_METRIC = new Map<string, number>();
for (const a of ANNOTATIONS) {
  for (const slug of a.slugs) {
    if (!SLUG_TO_METRIC.has(slug)) SLUG_TO_METRIC.set(slug, a.metricId);
  }
}

// ── Component ──

interface BodyReportMapProps {
  measurements: Measurement[];
  metrics: Metric[];
}

interface MetricSnapshot {
  value: number;
  unit: string;
  delta: number | null;
  totalDelta: number | null;
  rate: number | null;
  history: { date: string; value: number }[];
}

export function BodyReportMap({ measurements, metrics }: BodyReportMapProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const metricMap = useMemo(() => new Map(metrics.map((m) => [m.id, m])), [metrics]);

  // Compute snapshot for each metric
  const snapshots = useMemo(() => {
    const map = new Map<number, MetricSnapshot>();
    const sorted = [...measurements].sort((a, b) => a.data_misurazione.localeCompare(b.data_misurazione));

    for (const cfg of ANNOTATIONS) {
      const mid = cfg.metricId;
      const m = metricMap.get(mid);
      if (!m) continue;

      const latest = getLatestValue(measurements, mid);
      if (latest === null) continue;

      // History (chronological)
      const hist: { date: string; value: number }[] = [];
      for (const ms of sorted) {
        const v = ms.valori.find((vl) => vl.id_metrica === mid);
        if (v) hist.push({ date: ms.data_misurazione, value: v.valore });
      }

      // Delta from previous session
      let delta: number | null = null;
      if (hist.length >= 2) {
        delta = Math.round((hist[hist.length - 1].value - hist[hist.length - 2].value) * 10) / 10;
      }

      // Total delta (first → last)
      let totalDelta: number | null = null;
      if (hist.length >= 2) {
        totalDelta = Math.round((hist[hist.length - 1].value - hist[0].value) * 10) / 10;
      }

      const rate = computeWeeklyRate(measurements, mid);

      map.set(mid, { value: latest, unit: m.unita_misura, delta, totalDelta, rate, history: hist });
    }
    return map;
  }, [measurements, metricMap]);

  // Only show annotations with data
  const visible = useMemo(() => ANNOTATIONS.filter((a) => snapshots.has(a.metricId)), [snapshots]);
  const leftAnns = visible.filter((a) => a.side === "left");
  const rightAnns = visible.filter((a) => a.side === "right");

  // Body zone coloring — tracked zones teal, selected brighter
  const bodyData = useMemo(() => {
    const parts: ExtendedBodyPart[] = [];
    const seen = new Set<Slug>();
    for (const ann of visible) {
      const intensity = ann.metricId === selectedId ? 2 : 1;
      for (const slug of ann.slugs) {
        if (FRONT_SLUGS.has(slug) && !seen.has(slug)) {
          seen.add(slug);
          parts.push({ slug, intensity });
        }
      }
    }
    return parts;
  }, [visible, selectedId]);

  const colors = isDark ? ["#5eead4", "#14b8a6"] : ["#99f6e4", "#0d9488"]; // teal-300/500 light, teal-300/600 dark
  const defaultFill = isDark ? "#3f3f46" : "#e4e4e7"; // zinc-700 / zinc-200

  const handleBodyPress = (part: { slug?: string }) => {
    if (!part.slug) return;
    const mid = SLUG_TO_METRIC.get(part.slug);
    if (mid && snapshots.has(mid)) setSelectedId((prev) => (prev === mid ? null : mid));
  };

  const toggleMetric = (mid: number) => setSelectedId((prev) => (prev === mid ? null : mid));

  const selectedSnap = selectedId ? snapshots.get(selectedId) : null;
  const selectedAnn = selectedId ? ANNOTATIONS.find((a) => a.metricId === selectedId) : null;

  if (visible.length === 0) return null;

  return (
    <div className="space-y-3">
      {/* Desktop: 3-column layout */}
      <div className="hidden sm:grid grid-cols-[minmax(90px,150px)_auto_minmax(90px,150px)] items-stretch gap-0">
        <AnnotationColumn annotations={leftAnns} snapshots={snapshots} side="left" selectedId={selectedId} onSelect={toggleMetric} />
        <div className="flex items-center justify-center print:scale-90">
          <Body data={bodyData} side="front" gender="male" scale={0.9} colors={colors} border="none" defaultFill={defaultFill} onBodyPartPress={handleBodyPress} />
        </div>
        <AnnotationColumn annotations={rightAnns} snapshots={snapshots} side="right" selectedId={selectedId} onSelect={toggleMetric} />
      </div>

      {/* Mobile: body + grid annotations */}
      <div className="sm:hidden">
        <div className="flex justify-center">
          <Body data={bodyData} side="front" gender="male" scale={0.7} colors={colors} border="none" defaultFill={defaultFill} onBodyPartPress={handleBodyPress} />
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2">
          {visible.map((ann) => {
            const snap = snapshots.get(ann.metricId)!;
            return (
              <button key={ann.metricId} type="button" onClick={() => toggleMetric(ann.metricId)}
                className={`rounded-lg border p-2 text-left transition-all ${selectedId === ann.metricId ? "border-teal-500 bg-teal-50/50 dark:bg-teal-950/20" : "hover:bg-muted/30"}`}>
                <span className="text-[9px] font-medium text-muted-foreground">{ann.label}</span>
                <p className="text-sm font-bold tabular-nums">{snap.value} {snap.unit}</p>
                {snap.delta !== null && snap.delta !== 0 && (
                  <span className={`text-[10px] font-medium ${snap.delta < 0 ? "text-emerald-600" : "text-amber-600"}`}>
                    {snap.delta > 0 ? "+" : ""}{snap.delta} {snap.unit}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Detail panel */}
      {selectedSnap && selectedAnn && (
        <div className="rounded-lg border border-teal-200 bg-teal-50/30 p-3 dark:border-teal-800 dark:bg-teal-950/10 print:break-inside-avoid">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-semibold">{selectedAnn.label}</p>
            {selectedSnap.rate !== null && (
              <Badge variant="outline" className="text-[10px]">
                {formatRate(selectedSnap.rate, selectedSnap.unit)}
              </Badge>
            )}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs tabular-nums">
            {selectedSnap.history.slice(-5).map((h) => (
              <div key={h.date} className="flex items-baseline gap-1">
                <span className="text-muted-foreground">{format(parseISO(h.date), "d MMM", { locale: it })}</span>
                <span className="font-medium">{h.value} {selectedSnap.unit}</span>
              </div>
            ))}
          </div>
          {selectedSnap.totalDelta !== null && selectedSnap.totalDelta !== 0 && (
            <p className="mt-1.5 text-[10px] text-muted-foreground">
              Variazione totale: <strong className={selectedSnap.totalDelta < 0 ? "text-emerald-600" : "text-amber-600"}>
                {selectedSnap.totalDelta > 0 ? "+" : ""}{selectedSnap.totalDelta} {selectedSnap.unit}
              </strong> in {selectedSnap.history.length} {selectedSnap.history.length === 1 ? "sessione" : "sessioni"}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ── Annotation Column ──

function AnnotationColumn({ annotations, snapshots, side, selectedId, onSelect }: {
  annotations: AnnotationConfig[];
  snapshots: Map<number, MetricSnapshot>;
  side: "left" | "right";
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <div className="relative">
      {annotations.map((ann) => {
        const snap = snapshots.get(ann.metricId);
        if (!snap) return null;
        const isSelected = selectedId === ann.metricId;
        return (
          <button key={ann.metricId} type="button" onClick={() => onSelect(ann.metricId)}
            className="absolute w-full group" style={{ top: `${ann.topPct}%`, transform: "translateY(-50%)" }}>
            <div className={`flex items-center gap-0 ${side === "right" ? "flex-row" : "flex-row-reverse"}`}>
              <div className={`flex-1 rounded-md border px-2 py-1 text-${side === "left" ? "right" : "left"} transition-all ${
                isSelected ? "border-teal-500 bg-teal-50 shadow-sm dark:bg-teal-950/30" : "border-transparent group-hover:border-zinc-200 group-hover:bg-muted/30 dark:group-hover:border-zinc-700"
              }`}>
                <span className="block text-[9px] font-medium uppercase tracking-wider text-muted-foreground">{ann.label}</span>
                <span className="block text-sm font-extrabold tabular-nums tracking-tighter">{snap.value}</span>
                <span className="block text-[10px] text-muted-foreground">{snap.unit}</span>
                {snap.delta !== null && snap.delta !== 0 && (
                  <span className={`block text-[10px] font-semibold ${snap.delta < 0 ? "text-emerald-600" : "text-amber-600"}`}>
                    {snap.delta > 0 ? "+" : ""}{snap.delta}
                  </span>
                )}
              </div>
              <div className={`w-3 shrink-0 border-t border-dashed ${isSelected ? "border-teal-400" : "border-zinc-300 dark:border-zinc-600"}`} />
            </div>
          </button>
        );
      })}
    </div>
  );
}
