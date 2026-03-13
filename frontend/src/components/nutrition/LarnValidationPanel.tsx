// src/components/nutrition/LarnValidationPanel.tsx
"use client";

/**
 * Pannello validazione LARN 2014 per piano alimentare.
 *
 * Mostra: score badge, distribuzione macro vs range, assessment per nutriente,
 * warnings. Collassabile. Chiama usePlanLarnValidation(planId).
 */

import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  ShieldCheck,
  AlertTriangle,
  Info,
  XCircle,
  CheckCircle2,
  MinusCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { usePlanLarnValidation } from "@/hooks/useNutrition";
import type { NutrientAssessment, MacroDistribution } from "@/types/api";

// ── Score badge ──────────────────────────────────────────────────────────

function ScoreBadge({ score }: { score: number }) {
  let color: string;
  let label: string;
  if (score >= 80) {
    color = "bg-emerald-100 text-emerald-700 border-emerald-300";
    label = "Ottimo";
  } else if (score >= 60) {
    color = "bg-blue-100 text-blue-700 border-blue-300";
    label = "Buono";
  } else if (score >= 40) {
    color = "bg-amber-100 text-amber-700 border-amber-300";
    label = "Sufficiente";
  } else {
    color = "bg-red-100 text-red-700 border-red-300";
    label = "Da migliorare";
  }
  return (
    <div className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-semibold ${color}`}>
      <ShieldCheck className="h-4 w-4" />
      {score}/100 — {label}
    </div>
  );
}

// ── Macro range bar ──────────────────────────────────────────────────────

function MacroRangeBar({
  label, value, range, color,
}: {
  label: string;
  value: number;
  range: [number, number];
  color: string;
}) {
  const inRange = value >= range[0] && value <= range[1];
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className={`font-medium tabular-nums ${inRange ? "text-foreground" : "text-amber-600"}`}>
          {value}%
          <span className="text-muted-foreground font-normal ml-1">
            ({range[0]}-{range[1]}%)
          </span>
        </span>
      </div>
      <div className="relative h-2 rounded-full bg-muted overflow-hidden">
        {/* Range zone indicator */}
        <div
          className="absolute h-full bg-muted-foreground/10 rounded-full"
          style={{
            left: `${range[0]}%`,
            width: `${range[1] - range[0]}%`,
          }}
        />
        {/* Actual value marker */}
        <div
          className={`absolute h-full rounded-full transition-all ${color}`}
          style={{ width: `${Math.min(100, value)}%`, opacity: inRange ? 1 : 0.6 }}
        />
      </div>
    </div>
  );
}

// ── Status icon ──────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, {
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  label: string;
}> = {
  ottimale:       { icon: CheckCircle2, color: "text-emerald-500", label: "Ottimale" },
  sufficiente:    { icon: Info,         color: "text-blue-500",    label: "Sufficiente" },
  carente:        { icon: AlertTriangle,color: "text-amber-500",   label: "Carente" },
  eccesso:        { icon: XCircle,      color: "text-red-500",     label: "Eccesso" },
  non_valutabile: { icon: MinusCircle,  color: "text-muted-foreground", label: "N/D" },
};

function NutrientRow({ item }: { item: NutrientAssessment }) {
  const cfg = STATUS_CONFIG[item.status] ?? STATUS_CONFIG.non_valutabile;
  const Icon = cfg.icon;
  const target = item.riferimento.pri ?? item.riferimento.ai;
  const pct = item.percentuale_pri;

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-muted/40 transition-colors cursor-default">
            <Icon className={`h-4 w-4 shrink-0 ${cfg.color}`} />
            <span className="text-sm flex-1 min-w-0 truncate">{item.nutriente}</span>
            {item.apporto_die != null && (
              <span className="text-xs tabular-nums text-muted-foreground shrink-0">
                {Math.round(item.apporto_die * 10) / 10} {item.unita}
              </span>
            )}
            {pct != null && (
              <div className="w-16 shrink-0">
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      pct >= 100 ? "bg-emerald-500"
                        : pct >= 80 ? "bg-blue-400"
                        : pct >= 50 ? "bg-amber-400"
                        : "bg-red-400"
                    }`}
                    style={{ width: `${Math.min(100, pct)}%` }}
                  />
                </div>
              </div>
            )}
            {pct != null && (
              <span className={`text-xs tabular-nums w-10 text-right shrink-0 font-medium ${
                pct >= 100 ? "text-emerald-600" : pct >= 80 ? "text-blue-600" : "text-amber-600"
              }`}>
                {Math.round(pct)}%
              </span>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent side="left" className="max-w-xs text-xs space-y-1">
          <p className="font-semibold">{item.nutriente} — {cfg.label}</p>
          {target != null && (
            <p>
              Target ({item.riferimento.pri != null ? "PRI" : "AI"}): {target} {item.unita}
            </p>
          )}
          {item.riferimento.ar != null && (
            <p>Fabbisogno medio (AR): {item.riferimento.ar} {item.unita}</p>
          )}
          {item.riferimento.ul != null && (
            <p>Livello max (UL): {item.riferimento.ul} {item.unita}</p>
          )}
          {item.nota && <p className="italic text-muted-foreground">{item.nota}</p>}
          <p className="text-muted-foreground">Fonte: {item.riferimento.fonte}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// ── Main panel ───────────────────────────────────────────────────────────

interface LarnValidationPanelProps {
  planId: number;
}

export function LarnValidationPanel({ planId }: LarnValidationPanelProps) {
  const { data, isLoading, isError, error } = usePlanLarnValidation(planId);
  const [expanded, setExpanded] = useState(false);

  // Mostra solo se ci sono dati o sta caricando
  if (isError) {
    const msg = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    if (msg?.includes("Data di nascita") || msg?.includes("Sesso") || msg?.includes("senza pasti") || msg?.includes("senza alimenti")) {
      // Dati mancanti — non mostrare il pannello
      return null;
    }
    return null;
  }

  if (isLoading) {
    return (
      <div className="rounded-lg border p-4 space-y-2">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-8 w-32" />
      </div>
    );
  }

  if (!data) return null;

  const { macro } = data;

  // Count per status
  const counts = { ottimale: 0, sufficiente: 0, carente: 0, eccesso: 0 };
  for (const n of data.nutrienti) {
    if (n.status in counts) counts[n.status as keyof typeof counts]++;
  }

  // Ordina: carente/eccesso prima, poi sufficiente, poi ottimale
  const ORDER: Record<string, number> = {
    eccesso: 0, carente: 1, sufficiente: 2, ottimale: 3, non_valutabile: 4,
  };
  const sorted = [...data.nutrienti].sort(
    (a, b) => (ORDER[a.status] ?? 9) - (ORDER[b.status] ?? 9),
  );

  return (
    <div className="rounded-lg border bg-muted/20">
      {/* ── Header (always visible) ── */}
      <button
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-muted/30 transition-colors rounded-lg"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded
          ? <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
          : <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
        }
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Analisi LARN 2014
            </span>
            <ScoreBadge score={data.score} />
          </div>
        </div>

        {/* Mini summary badges */}
        <div className="flex items-center gap-1.5 shrink-0">
          {counts.carente > 0 && (
            <Badge variant="outline" className="text-[10px] h-5 px-1.5 border-amber-300 text-amber-600">
              {counts.carente} carenti
            </Badge>
          )}
          {counts.eccesso > 0 && (
            <Badge variant="outline" className="text-[10px] h-5 px-1.5 border-red-300 text-red-600">
              {counts.eccesso} eccesso
            </Badge>
          )}
          {counts.carente === 0 && counts.eccesso === 0 && (
            <Badge variant="outline" className="text-[10px] h-5 px-1.5 border-emerald-300 text-emerald-600">
              Tutti OK
            </Badge>
          )}
        </div>
      </button>

      {/* ── Expanded content ── */}
      {expanded && (
        <div className="px-4 pb-4 space-y-4">
          {/* Warnings */}
          {data.warnings.length > 0 && (
            <div className="rounded-md bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 p-3 space-y-1">
              {data.warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-amber-700 dark:text-amber-400">
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                  <span>{w}</span>
                </div>
              ))}
            </div>
          )}

          {/* Macro distribution */}
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Distribuzione macro (% energia)
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <MacroRangeBar
                label="Proteine"
                value={macro.proteine_pct}
                range={macro.proteine_range as [number, number]}
                color="bg-blue-500"
              />
              <MacroRangeBar
                label="Carboidrati"
                value={macro.carboidrati_pct}
                range={macro.carboidrati_range as [number, number]}
                color="bg-amber-500"
              />
              <MacroRangeBar
                label="Grassi"
                value={macro.grassi_pct}
                range={macro.grassi_range as [number, number]}
                color="bg-rose-400"
              />
            </div>
          </div>

          {/* Nutrient assessments */}
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Micronutrienti ({data.nutrienti.length} analizzati)
            </p>
            <div className="divide-y divide-muted/40">
              {sorted.map((item) => (
                <NutrientRow key={item.nutriente} item={item} />
              ))}
            </div>
          </div>

          {/* Profilo e nota metodologica */}
          <div className="text-[10px] text-muted-foreground space-y-0.5 pt-2 border-t">
            <p>
              Profilo: {data.profilo_sesso === "M" ? "Maschio" : "Femmina"}, {data.profilo_eta} anni
              {" · "}{Math.round(data.kcal_die)} kcal/die (media piano)
            </p>
            <p className="italic">{data.note_metodologiche}</p>
          </div>
        </div>
      )}
    </div>
  );
}
