"use client";

/**
 * BodyReportMap v2 — Clinical Body Scan con visualizzazione progresso.
 *
 * Estetica "scan" su sfondo scuro. Zone corporee colorate per direzione progresso:
 * emerald = miglioramento, rose = peggioramento, slate = stabile.
 * Annotation pills compatte: solo delta + rate settimanale (contesto temporale).
 * Click zona → pannello dettaglio con storico misurazioni.
 */

import { useMemo, useState } from "react";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import Body from "react-muscle-highlighter";
import type { Slug, ExtendedBodyPart } from "react-muscle-highlighter";

import { TrendingDown, TrendingUp, Minus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { FRONT_SLUGS } from "@/lib/muscle-map-utils";
import { computeWeeklyRate, formatRate } from "@/lib/measurement-analytics";
import { getLatestValue } from "@/lib/derived-metrics";
import type { ClientGoal, Measurement, Metric } from "@/types/api";

// ── Annotation positions (tuned for scale 0.85) ──

interface AnnotationConfig {
  metricId: number;
  label: string;
  side: "left" | "right";
  topPct: number;
  slugs: Slug[];
}

const ANNOTATIONS: AnnotationConfig[] = [
  { metricId: 12, label: "Braccio Sx", side: "left",  topPct: 30, slugs: ["biceps", "triceps", "deltoids"] },
  { metricId: 9,  label: "Vita",       side: "left",  topPct: 46, slugs: ["abs", "obliques"] },
  { metricId: 14, label: "Coscia Sx",  side: "left",  topPct: 64, slugs: ["quadriceps", "adductors"] },
  { metricId: 16, label: "Polp. Sx",   side: "left",  topPct: 81, slugs: ["calves"] },
  { metricId: 7,  label: "Collo",      side: "right", topPct: 14, slugs: ["trapezius", "neck"] },
  { metricId: 8,  label: "Torace",     side: "right", topPct: 28, slugs: ["chest"] },
  { metricId: 11, label: "Braccio Dx", side: "right", topPct: 41, slugs: ["biceps", "triceps", "deltoids"] },
  { metricId: 10, label: "Fianchi",    side: "right", topPct: 54, slugs: ["gluteal", "adductors"] },
  { metricId: 13, label: "Coscia Dx",  side: "right", topPct: 68, slugs: ["quadriceps", "adductors"] },
  { metricId: 15, label: "Polp. Dx",   side: "right", topPct: 81, slugs: ["calves"] },
];

const SLUG_TO_METRIC = new Map<string, number>();
for (const a of ANNOTATIONS) {
  for (const s of a.slugs) if (!SLUG_TO_METRIC.has(s)) SLUG_TO_METRIC.set(s, a.metricId);
}

// ── Progress colors — 6 intensity levels ──
// 1=improving, 2=stable, 3=worsening, 4/5/6=selected variants

const SCAN_COLORS = ["#34d399", "#475569", "#fb7185", "#6ee7b7", "#94a3b8", "#fda4af"];
const SCAN_DEFAULT = "#1e293b";

type ZoneProgress = "improving" | "stable" | "worsening";

function getProgress(delta: number | null, direzione?: "aumentare" | "diminuire" | "mantenere" | null): ZoneProgress {
  if (delta === null || delta === 0) return "stable";
  if (direzione === "mantenere") return "stable";
  if (direzione === "aumentare") return delta > 0 ? "improving" : "worsening";
  // "diminuire" oppure nessun obiettivo → default: riduzione = miglioramento
  return delta < 0 ? "improving" : "worsening";
}

function getIntensity(p: ZoneProgress, selected: boolean): number {
  const base = p === "improving" ? 1 : p === "stable" ? 2 : 3;
  return selected ? base + 3 : base;
}

// ── Snapshot ──

interface MetricSnapshot {
  value: number;
  unit: string;
  delta: number | null;
  totalDelta: number | null;
  rate: number | null;
  progress: ZoneProgress;
  history: { date: string; value: number }[];
}

interface BodyReportMapProps {
  measurements: Measurement[];
  metrics: Metric[];
  goals?: ClientGoal[];
  onSelectMetric?: (metricId: number | null) => void;
}

// ── Component ──

export function BodyReportMap({ measurements, metrics, goals, onSelectMetric }: BodyReportMapProps) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const metricMap = useMemo(() => new Map(metrics.map(m => [m.id, m])), [metrics]);

  // Mappa metricId → direzione obiettivo attivo
  const goalDirMap = useMemo(() => {
    const map = new Map<number, "aumentare" | "diminuire" | "mantenere">();
    if (!goals) return map;
    for (const g of goals) {
      if (g.stato === "attivo" && g.id_metrica) map.set(g.id_metrica, g.direzione);
    }
    return map;
  }, [goals]);

  const snapshots = useMemo(() => {
    const map = new Map<number, MetricSnapshot>();
    const sorted = [...measurements].sort((a, b) => a.data_misurazione.localeCompare(b.data_misurazione));
    for (const cfg of ANNOTATIONS) {
      const mid = cfg.metricId;
      const m = metricMap.get(mid);
      if (!m) continue;
      const latest = getLatestValue(measurements, mid);
      if (latest === null) continue;
      const hist: { date: string; value: number }[] = [];
      for (const ms of sorted) {
        const v = ms.valori.find(vl => vl.id_metrica === mid);
        if (v) hist.push({ date: ms.data_misurazione, value: v.valore });
      }
      let delta: number | null = null;
      if (hist.length >= 2) delta = Math.round((hist[hist.length - 1].value - hist[hist.length - 2].value) * 10) / 10;
      let totalDelta: number | null = null;
      if (hist.length >= 2) totalDelta = Math.round((hist[hist.length - 1].value - hist[0].value) * 10) / 10;
      const rate = computeWeeklyRate(measurements, mid);
      const direzione = goalDirMap.get(mid) ?? null;
      map.set(mid, { value: latest, unit: m.unita_misura, delta, totalDelta, rate, progress: getProgress(delta, direzione), history: hist });
    }
    return map;
  }, [measurements, metricMap, goalDirMap]);

  const visible = useMemo(() => ANNOTATIONS.filter(a => snapshots.has(a.metricId)), [snapshots]);
  const leftAnns = visible.filter(a => a.side === "left");
  const rightAnns = visible.filter(a => a.side === "right");

  const bodyData = useMemo(() => {
    const parts: ExtendedBodyPart[] = [];
    const seen = new Set<Slug>();
    for (const ann of visible) {
      const snap = snapshots.get(ann.metricId)!;
      const intensity = getIntensity(snap.progress, ann.metricId === selectedId);
      for (const slug of ann.slugs) {
        if (FRONT_SLUGS.has(slug) && !seen.has(slug)) {
          seen.add(slug);
          parts.push({ slug, intensity });
        }
      }
    }
    return parts;
  }, [visible, selectedId, snapshots]);

  const toggle = (mid: number) => {
    const next = selectedId === mid ? null : mid;
    setSelectedId(next);
    onSelectMetric?.(next);
  };
  const handleBodyPress = (part: { slug?: string }) => {
    if (!part.slug) return;
    const mid = SLUG_TO_METRIC.get(part.slug);
    if (mid && snapshots.has(mid)) toggle(mid);
  };

  const selectedSnap = selectedId ? snapshots.get(selectedId) : null;
  const selectedAnn = selectedId ? ANNOTATIONS.find(a => a.metricId === selectedId) : null;

  if (visible.length === 0) return null;

  return (
    <div className="space-y-3">
      {/* Dark scan container */}
      <div
        className="rounded-xl bg-gradient-to-b from-[#0f172a] to-[#1e293b] border border-slate-700/50 shadow-xl overflow-hidden print:bg-white print:border-slate-300 print:shadow-none"
        style={{ backgroundImage: "radial-gradient(circle, rgba(100,116,139,0.06) 1px, transparent 1px)", backgroundSize: "16px 16px" }}
      >
        {/* Header + legend */}
        <div className="flex items-center justify-between px-4 pt-3 pb-1">
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400 print:text-slate-600">
            Body Scan
          </span>
          <div className="flex items-center gap-3">
            <LegendDot color="#34d399" label="Miglioramento" />
            <LegendDot color="#fb7185" label="Peggioramento" />
            <LegendDot color="#475569" label="Stabile" />
          </div>
        </div>

        {/* Desktop layout */}
        <div className="hidden sm:grid grid-cols-[1fr_auto_1fr] items-stretch px-2 pb-4">
          <AnnotationColumn annotations={leftAnns} snapshots={snapshots} side="left" selectedId={selectedId} onSelect={toggle} />
          <div className="flex items-center justify-center">
            <Body data={bodyData} side="front" gender="male" scale={0.85} colors={SCAN_COLORS} border="none" defaultFill={SCAN_DEFAULT} onBodyPartPress={handleBodyPress} />
          </div>
          <AnnotationColumn annotations={rightAnns} snapshots={snapshots} side="right" selectedId={selectedId} onSelect={toggle} />
        </div>

        {/* Mobile layout */}
        <div className="sm:hidden pb-3">
          <div className="flex justify-center">
            <Body data={bodyData} side="front" gender="male" scale={0.65} colors={SCAN_COLORS} border="none" defaultFill={SCAN_DEFAULT} onBodyPartPress={handleBodyPress} />
          </div>
          <div className="mt-2 grid grid-cols-2 gap-1.5 px-3">
            {visible.map(ann => {
              const snap = snapshots.get(ann.metricId)!;
              return (
                <button key={ann.metricId} type="button" onClick={() => toggle(ann.metricId)}
                  className={`rounded-lg px-2.5 py-1.5 text-left transition-all ${selectedId === ann.metricId ? "bg-slate-700/80 ring-1 ring-teal-500/40" : "bg-slate-800/50 hover:bg-slate-700/40"}`}>
                  <span className="block text-[8px] font-medium uppercase tracking-wider text-slate-500">{ann.label}</span>
                  <DeltaDisplay snap={snap} compact />
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Detail panel (outside scan, normal theme) */}
      {selectedSnap && selectedAnn && (
        <div className="rounded-lg border border-teal-200 bg-teal-50/30 p-3 dark:border-teal-800 dark:bg-teal-950/10 print:break-inside-avoid">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <p className="text-xs font-semibold">{selectedAnn.label}</p>
              <span className="text-lg font-extrabold tabular-nums tracking-tighter">
                {selectedSnap.value} {selectedSnap.unit}
              </span>
            </div>
            {selectedSnap.rate !== null && (
              <Badge variant="outline" className="text-[10px]">{formatRate(selectedSnap.rate, selectedSnap.unit)}</Badge>
            )}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs tabular-nums">
            {selectedSnap.history.slice(-5).map(h => (
              <div key={h.date} className="flex items-baseline gap-1">
                <span className="text-muted-foreground">{format(parseISO(h.date), "d MMM", { locale: it })}</span>
                <span className="font-medium">{h.value} {selectedSnap.unit}</span>
              </div>
            ))}
          </div>
          {selectedSnap.totalDelta !== null && selectedSnap.totalDelta !== 0 && (
            <p className="mt-1.5 text-[10px] text-muted-foreground">
              Variazione totale: <strong className={selectedSnap.totalDelta < 0 ? "text-emerald-600" : "text-rose-500"}>
                {selectedSnap.totalDelta > 0 ? "+" : ""}{selectedSnap.totalDelta} {selectedSnap.unit}
              </strong> in {selectedSnap.history.length} {selectedSnap.history.length === 1 ? "sessione" : "sessioni"}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ── Annotation Column (desktop) ──

function AnnotationColumn({ annotations, snapshots, side, selectedId, onSelect }: {
  annotations: AnnotationConfig[];
  snapshots: Map<number, MetricSnapshot>;
  side: "left" | "right";
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <div className="relative min-h-[320px]">
      {annotations.map(ann => {
        const snap = snapshots.get(ann.metricId);
        if (!snap) return null;
        const isSelected = selectedId === ann.metricId;
        return (
          <button key={ann.metricId} type="button" onClick={() => onSelect(ann.metricId)}
            className="absolute w-full group" style={{ top: `${ann.topPct}%`, transform: "translateY(-50%)" }}>
            <div className={`flex items-center ${side === "right" ? "flex-row" : "flex-row-reverse"}`}>
              <div className={`rounded-md px-2 py-1 transition-all ${side === "left" ? "text-right" : "text-left"} ${
                isSelected
                  ? "bg-slate-700/80 shadow-md shadow-teal-500/10 ring-1 ring-teal-500/30"
                  : "bg-transparent group-hover:bg-slate-800/60"
              }`}>
                <span className={`block text-[8px] font-medium uppercase tracking-[0.12em] ${isSelected ? "text-slate-300" : "text-slate-500"}`}>
                  {ann.label}
                </span>
                <DeltaDisplay snap={snap} />
              </div>
              {/* Leader line */}
              <div className={`w-5 shrink-0 border-t border-dashed transition-colors ${
                isSelected ? "border-teal-500/60" : "border-slate-600/30 group-hover:border-slate-500/50"
              }`} />
            </div>
          </button>
        );
      })}
    </div>
  );
}

// ── Delta Display ──

function DeltaDisplay({ snap, compact }: { snap: MetricSnapshot; compact?: boolean }) {
  const colorClass = snap.progress === "improving"
    ? "text-emerald-400" : snap.progress === "worsening"
      ? "text-rose-400" : "text-slate-400";

  if (snap.rate !== null) {
    const Icon = snap.rate < 0 ? TrendingDown : snap.rate > 0 ? TrendingUp : Minus;
    return (
      <div className={`flex items-center gap-0.5 ${compact ? "mt-0.5" : ""}`}>
        <Icon className={`h-3 w-3 shrink-0 ${colorClass}`} />
        <span className={`${compact ? "text-[10px]" : "text-[11px]"} font-bold tabular-nums ${colorClass}`}>
          {formatRate(snap.rate, snap.unit)}
        </span>
      </div>
    );
  }

  if (snap.delta !== null && snap.delta !== 0) {
    return (
      <span className={`block ${compact ? "text-[10px]" : "text-[11px]"} font-bold tabular-nums ${colorClass}`}>
        {snap.delta > 0 ? "+" : ""}{snap.delta} {snap.unit}
      </span>
    );
  }

  return <span className={`block text-[10px] font-medium ${colorClass}`}>—</span>;
}

// ── Legend Dot ──

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1">
      <div className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
      <span className="text-[8px] text-slate-500 print:text-slate-600">{label}</span>
    </div>
  );
}
