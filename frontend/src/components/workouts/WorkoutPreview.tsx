// src/components/workouts/WorkoutPreview.tsx
"use client";

/**
 * Preview professionale stampabile della scheda allenamento.
 *
 * Layout: header, tabella esercizi per sessione (3 sezioni), note, footer.
 * Immagini esecuzione (exec_start.jpg) inline nella sezione principale.
 * Tempo esecuzione mostrato inline accanto al nome (se compilato).
 */

import { useMemo } from "react";
import Image from "next/image";
import type { LucideIcon } from "lucide-react";
import { Activity, Clock3, Dumbbell, Flame, Gauge, Hourglass, Repeat2, StretchHorizontal } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { getSectionForCategory, type TemplateSection } from "@/lib/workout-templates";
import { buildBlockMetrics } from "@/lib/workout-preview-block-metrics";
import { parseAvgReps, type SessionCardData } from "./SessionCard";
import { BLOCK_TYPE_LABELS, type WorkoutExerciseRow, type Exercise } from "@/types/api";
import type { BlockCardData } from "./BlockCard";

// ════════════════════════════════════════════════════════════
// LABELS
// ════════════════════════════════════════════════════════════

const OBIETTIVO_LABELS: Record<string, string> = {
  forza: "Forza",
  ipertrofia: "Ipertrofia",
  resistenza: "Resistenza",
  dimagrimento: "Dimagrimento",
  generale: "Generale",
};

const LIVELLO_LABELS: Record<string, string> = {
  beginner: "Principiante",
  intermedio: "Intermedio",
  avanzato: "Avanzato",
};

const SECTION_PREVIEW_CONFIG: Record<TemplateSection, {
  label: string;
  description: string;
  color: string;
  icon: LucideIcon;
  cardBorder: string;
  cardHeader: string;
  cardHeaderText: string;
  chipClass: string;
}> = {
  avviamento: {
    label: "Avviamento",
    description: "Attivazione progressiva",
    color: "text-amber-600 dark:text-amber-400",
    icon: Flame,
    cardBorder: "border-amber-300 dark:border-amber-700/60",
    cardHeader: "bg-amber-50 dark:bg-amber-950/40",
    cardHeaderText: "text-amber-800 dark:text-amber-200",
    chipClass: "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300",
  },
  principale: {
    label: "Blocco Serie x Ripetizioni",
    description: "Stimolo centrale della sessione",
    color: "text-primary",
    icon: Dumbbell,
    cardBorder: "border-teal-300 dark:border-teal-700/60",
    cardHeader: "bg-teal-50 dark:bg-teal-950/40",
    cardHeaderText: "text-teal-800 dark:text-teal-200",
    chipClass: "bg-teal-100 text-teal-700 dark:bg-teal-900/50 dark:text-teal-300",
  },
  stretching: {
    label: "Stretching & Mobilita",
    description: "Defaticamento e recupero ROM",
    color: "text-cyan-600 dark:text-cyan-400",
    icon: StretchHorizontal,
    cardBorder: "border-cyan-300 dark:border-cyan-700/60",
    cardHeader: "bg-cyan-50 dark:bg-cyan-950/40",
    cardHeaderText: "text-cyan-800 dark:text-cyan-200",
    chipClass: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/50 dark:text-cyan-300",
  },
};

const SECTION_ORDER: TemplateSection[] = ["avviamento", "principale", "stretching"];

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

function groupBySection(esercizi: WorkoutExerciseRow[]) {
  const groups: Record<TemplateSection, WorkoutExerciseRow[]> = {
    avviamento: [],
    principale: [],
    stretching: [],
  };
  for (const ex of esercizi) {
    const section = getSectionForCategory(ex.esercizio_categoria);
    groups[section].push(ex);
  }
  return groups;
}

// ════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════

interface WorkoutPreviewProps {
  nome: string;
  obiettivo: string;
  livello: string;
  clientNome?: string;
  logoDataUrl?: string | null;
  durata_settimane: number;
  sessioni_per_settimana: number;
  sessioni: SessionCardData[];
  note?: string | null;
  exerciseMap?: Map<number, Exercise>;
}

export function WorkoutPreview({
  nome,
  obiettivo,
  livello,
  clientNome,
  logoDataUrl,
  durata_settimane,
  sessioni_per_settimana,
  sessioni,
  note,
}: WorkoutPreviewProps) {
  // Volume totale scheda (solo esercizi principali con carico)
  const totalVolume = useMemo(() => {
    let total = 0;
    for (const session of sessioni) {
      for (const ex of session.esercizi) {
        if (getSectionForCategory(ex.esercizio_categoria) !== "principale") continue;
        if (!ex.carico_kg || ex.carico_kg <= 0) continue;
        total += ex.serie * parseAvgReps(ex.ripetizioni) * ex.carico_kg;
      }
    }
    return total > 0 ? Math.round(total) : null;
  }, [sessioni]);

  return (
    <div className="workout-preview bg-white text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 rounded-lg border p-6 space-y-6 print:space-y-3">
      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1 border-l-4 border-primary pl-4">
          <h2 className="text-xl font-bold tracking-tight">{nome}</h2>
          {clientNome && (
            <p className="text-sm text-muted-foreground mt-0.5">{clientNome}</p>
          )}
          <div className="flex flex-wrap gap-2 mt-2">
            <Badge variant="outline" className="text-xs">
              {OBIETTIVO_LABELS[obiettivo] ?? obiettivo}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {LIVELLO_LABELS[livello] ?? livello}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {sessioni_per_settimana}x / settimana
            </Badge>
            <Badge variant="outline" className="text-xs">
              {durata_settimane} settimane
            </Badge>
            {totalVolume != null && (
              <Badge variant="outline" className="text-xs tabular-nums">
                Vol. totale: {totalVolume.toLocaleString("it-IT")} kg
              </Badge>
            )}
          </div>
        </div>

        {logoDataUrl && (
          <div className="shrink-0 rounded-md border border-zinc-200 bg-white p-2 print:border-zinc-300">
            <Image
              src={logoDataUrl}
              alt="Logo cliente"
              width={180}
              height={72}
              unoptimized
              className="h-14 w-auto max-w-[150px] object-contain print:h-12"
            />
          </div>
        )}
      </div>

      {/* ── Sessioni ── */}
      {sessioni.map((session) => (
        <SessionPreview
          key={session.id}
          session={session}
        />
      ))}

      {/* ── Note ── */}
      {note && (
        <div className="text-xs text-muted-foreground border-t pt-3">
          <p className="font-medium mb-1">Note:</p>
          <p>{note}</p>
        </div>
      )}

      {/* ── Footer ── */}
      <div className="flex items-center justify-between border-t pt-3 text-[10px] text-muted-foreground">
        <span>FitManager AI Studio</span>
        <span>{new Date().toLocaleDateString("it-IT")}</span>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// BLOCK PREVIEW — Format-specific
// ════════════════════════════════════════════════════════════

// Configurazione visiva per tipo di blocco — colori distinti dai classici esercizi
const BLOCK_TYPE_PREVIEW_CONFIG: Record<string, {
  icon: LucideIcon;
  flowHint: string;
  border: string;
  headerBg: string;
  headerText: string;
  accentText: string;
}> = {
  circuit:  {
    icon: Repeat2,
    flowHint: "Esegui in sequenza continua.",
    border: "border-violet-400",
    headerBg: "bg-violet-50 dark:bg-violet-950/40",
    headerText: "text-violet-800 dark:text-violet-200",
    accentText: "text-violet-600 dark:text-violet-400",
  },
  superset: {
    icon: Activity,
    flowHint: "Alterna A1/A2 con pausa minima.",
    border: "border-amber-400",
    headerBg: "bg-amber-50 dark:bg-amber-950/40",
    headerText: "text-amber-800 dark:text-amber-200",
    accentText: "text-amber-600 dark:text-amber-400",
  },
  tabata:   {
    icon: Hourglass,
    flowHint: "Focus su ritmo e tempo di lavoro.",
    border: "border-red-400",
    headerBg: "bg-red-50 dark:bg-red-950/40",
    headerText: "text-red-800 dark:text-red-200",
    accentText: "text-red-600 dark:text-red-400",
  },
  amrap:    {
    icon: Gauge,
    flowHint: "Massimizza la qualita nel tempo dato.",
    border: "border-emerald-400",
    headerBg: "bg-emerald-50 dark:bg-emerald-950/40",
    headerText: "text-emerald-800 dark:text-emerald-200",
    accentText: "text-emerald-600 dark:text-emerald-400",
  },
  emom:     {
    icon: Clock3,
    flowHint: "Parti a ogni minuto, ritmo regolare.",
    border: "border-teal-400",
    headerBg: "bg-teal-50 dark:bg-teal-950/40",
    headerText: "text-teal-800 dark:text-teal-200",
    accentText: "text-teal-600 dark:text-teal-400",
  },
  for_time: {
    icon: Clock3,
    flowHint: "Completa il volume nel minor tempo.",
    border: "border-orange-400",
    headerBg: "bg-orange-50 dark:bg-orange-950/40",
    headerText: "text-orange-800 dark:text-orange-200",
    accentText: "text-orange-600 dark:text-orange-400",
  },
};

const BLOCK_TYPE_PREVIEW_FALLBACK = {
  icon: Dumbbell,
  flowHint: "Mantieni esecuzione controllata.",
  border: "border-primary/40",
  headerBg: "bg-primary/5",
  headerText: "text-primary",
  accentText: "text-primary",
};

const PRIMARY_BLOCK_PREVIEW_CONFIG = {
  border: "border-teal-400",
  headerBg: "bg-teal-50 dark:bg-teal-950/40",
  headerText: "text-teal-800 dark:text-teal-200",
  accentText: "text-teal-600 dark:text-teal-400",
};

function PrimaryExerciseCard({
  ex,
  idx,
}: {
  ex: WorkoutExerciseRow;
  idx: number;
}) {
  const cfg = PRIMARY_BLOCK_PREVIEW_CONFIG;
  return (
    <div className={`border-l-4 ${cfg.border} pl-3 mb-2 rounded-r print:mb-1 print:pl-2`}>
      <div className={`${cfg.headerBg} rounded px-2 py-1 mb-1 print:px-1.5 print:py-0.5 print:mb-0.5`}>
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className={`text-[10px] font-bold tabular-nums ${cfg.accentText} print:text-[9px]`}>
            {idx + 1}.
          </span>
          <span className={`text-[11px] font-semibold ${cfg.headerText} print:text-[10px]`}>
            {ex.esercizio_nome}
          </span>
          {ex.tempo_esecuzione && (
            <span className={`text-[10px] ${cfg.accentText} print:text-[9px]`}>
              Tempo {ex.tempo_esecuzione}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-1 px-1 print:gap-0.5">
        <div className="rounded bg-muted/40 px-1.5 py-1 text-center print:px-1 print:py-0.5">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground">Serie</div>
          <div className="text-[11px] font-semibold tabular-nums print:text-[10px]">{ex.serie}</div>
        </div>
        <div className="rounded bg-muted/40 px-1.5 py-1 text-center print:px-1 print:py-0.5">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground">Rip</div>
          <div className="text-[11px] font-semibold tabular-nums print:text-[10px]">{ex.ripetizioni}</div>
        </div>
        <div className="rounded bg-muted/40 px-1.5 py-1 text-center print:px-1 print:py-0.5">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground">Kg</div>
          <div className="text-[11px] font-semibold tabular-nums print:text-[10px]">
            {ex.carico_kg != null ? ex.carico_kg : "—"}
          </div>
        </div>
        <div className="rounded bg-muted/40 px-1.5 py-1 text-center print:px-1 print:py-0.5">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground">Riposo</div>
          <div className="text-[11px] font-semibold tabular-nums print:text-[10px]">{ex.tempo_riposo_sec}s</div>
        </div>
      </div>

      {ex.note && (
        <p className="mt-1 px-1 text-[10px] text-muted-foreground leading-relaxed print:mt-0.5 print:text-[9px]">
          {ex.note}
        </p>
      )}
    </div>
  );
}

function SectionExerciseCard({
  sectionKey,
  ex,
  idx,
}: {
  sectionKey: Exclude<TemplateSection, "principale">;
  ex: WorkoutExerciseRow;
  idx: number;
}) {
  const cfg = SECTION_PREVIEW_CONFIG[sectionKey];
  const effortLabel = sectionKey === "avviamento" ? "Attiva" : "Recupero";
  const effortHint =
    sectionKey === "avviamento"
      ? "Graduale"
      : "Controllato";

  return (
    <div className={`border-l-4 ${cfg.cardBorder} pl-3 mb-2 rounded-r print:hidden`}>
      <div className={`${cfg.cardHeader} rounded px-2 py-1 mb-1`}>
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className={`text-[10px] font-bold tabular-nums ${cfg.cardHeaderText}`}>
            {idx + 1}.
          </span>
          <span className={`text-[11px] font-semibold ${cfg.cardHeaderText}`}>
            {ex.esercizio_nome}
          </span>
          {ex.tempo_esecuzione && (
            <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[9px] ${cfg.chipClass}`}>
              <Clock3 className="mr-1 h-2.5 w-2.5" />
              {ex.tempo_esecuzione}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-1 px-1">
        <div className="rounded bg-muted/40 px-1.5 py-1 text-center">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground">Serie</div>
          <div className="text-[11px] font-semibold tabular-nums">{ex.serie}</div>
        </div>
        <div className="rounded bg-muted/40 px-1.5 py-1 text-center">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground">Rip</div>
          <div className="text-[11px] font-semibold tabular-nums">{ex.ripetizioni}</div>
        </div>
        <div className="rounded bg-muted/40 px-1.5 py-1 text-center">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground">{effortLabel}</div>
          <div className="text-[11px] font-semibold tabular-nums">{effortHint}</div>
        </div>
      </div>

      {ex.note && (
        <p className="mt-1 px-1 text-[10px] text-muted-foreground leading-relaxed">
          {ex.note}
        </p>
      )}
    </div>
  );
}

function BlockPreview({ block }: { block: BlockCardData }) {
  const tipo = block.tipo_blocco;
  const cfg = BLOCK_TYPE_PREVIEW_CONFIG[tipo] ?? BLOCK_TYPE_PREVIEW_FALLBACK;
  const Icon = cfg.icon;
  const metrics = buildBlockMetrics(block, tipo);
  const showRip = tipo !== "tabata";
  const showKg  = tipo === "superset" || tipo === "circuit" || tipo === "for_time";
  const isSuperset = tipo === "superset";

  return (
    <div className={`border-l-4 ${cfg.border} pl-3 mb-2 rounded-r print:mb-1 print:pl-2 print:pr-1 print:py-1 print:border print:border-zinc-300`}>
      {/* Header blocco — sfondo colorato specifico del tipo */}
      <div className={`${cfg.headerBg} rounded px-2 py-1 mb-1 print:px-1.5 print:py-0.5 print:mb-0.5`}>
        <div className="flex items-center gap-1.5 flex-wrap">
          <Icon className={`h-3.5 w-3.5 ${cfg.headerText}`} />
          <span className={`text-[10px] font-bold uppercase tracking-wider ${cfg.headerText}`}>
            {BLOCK_TYPE_LABELS[tipo]}
          </span>
          {block.giri > 0 && (
            <span className={`hidden text-[10px] font-medium ${cfg.headerText}`}>
              × {block.giri} {tipo === "emom" ? "min" : "giri"}
            </span>
          )}
          {block.durata_lavoro_sec && (
            <span className={`hidden text-[10px] ${cfg.headerText}`}>{block.durata_lavoro_sec}s on</span>
          )}
          {block.durata_riposo_sec && (
            <span className={`hidden text-[10px] ${cfg.headerText}`}>{block.durata_riposo_sec}s off</span>
          )}
          {block.durata_blocco_sec && (
            <span className={`hidden text-[10px] ${cfg.headerText}`}>
              {Math.round(block.durata_blocco_sec / 60)} min
            </span>
          )}
          {block.nome && (
            <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[9px] font-medium ${cfg.accentText} bg-white/60 dark:bg-black/20`}>
              {block.nome}
            </span>
          )}
        </div>
        {metrics.length > 0 && (
          <div className="mt-1 grid grid-cols-2 gap-1 sm:grid-cols-4 print:mt-0.5 print:gap-0.5">
            {metrics.map((metric, idx) => (
              <div
                key={`${block.id}-${metric.label}`}
                className={`rounded border px-1.5 py-0.5 print:border-zinc-300 print:bg-transparent ${
                  idx === 0
                    ? "border-black/25 bg-white dark:border-white/25 dark:bg-black/25 ring-1 ring-black/10 dark:ring-white/10"
                    : "border-black/10 bg-white/80 dark:border-white/15 dark:bg-black/15"
                }`}
              >
                <div className={`text-[8px] uppercase tracking-wide ${cfg.accentText} print:text-[7px]`}>
                  {metric.label}
                  {idx === 0 && <span className="ml-1 font-bold">P</span>}
                </div>
                <div className={`font-semibold tabular-nums ${cfg.headerText} ${
                  idx === 0 ? "text-[13px] print:text-[11px] tracking-tight" : "text-[11px] print:text-[10px]"
                }`}>
                  {metric.value}
                </div>
              </div>
            ))}
          </div>
        )}
        {metrics.length === 0 && (
          <p className={`mt-1 text-[9px] ${cfg.accentText}`}>Parametri blocco non impostati</p>
        )}
        <p className={`mt-0.5 text-[9px] ${cfg.accentText} print:hidden`}>{cfg.flowHint}</p>
      </div>

      {/* Header colonne (non per tabata) */}
      {(showRip || showKg) && (
        <div
          className={`grid ${showKg ? "grid-cols-[16px_1fr_40px_40px]" : "grid-cols-[16px_1fr_40px]"} gap-1 text-[9px] text-muted-foreground/60 mb-0.5 px-1 print:gap-0.5 print:text-[8px]`}
        >
          <span />
          <span>Esercizio</span>
          {showRip && <span className="text-center">{tipo === "emom" ? "Rip/min" : "Rip"}</span>}
          {showKg  && <span className="text-center">Kg</span>}
        </div>
      )}

      {/* Esercizi */}
      {block.esercizi.map((ex, idx) => (
        <div
          key={ex.id}
          className={`grid ${showKg ? "grid-cols-[16px_1fr_40px_40px]" : showRip ? "grid-cols-[16px_1fr_40px]" : "grid-cols-[16px_1fr]"} items-center gap-1 text-[11px] py-0.5 px-1 print:gap-0.5 print:text-[10px]`}
        >
          {isSuperset ? (
            <span className={`text-[10px] font-bold tabular-nums ${cfg.accentText}`}>A{idx + 1}</span>
          ) : tipo === "tabata" ? (
            <span className={`text-[10px] ${cfg.accentText}`}>•</span>
          ) : (
            <span className="text-[10px] text-muted-foreground/60 tabular-nums">{idx + 1}.</span>
          )}
          <span className="font-medium truncate">{ex.esercizio_nome}</span>
          {showRip && (
            <span className="text-center tabular-nums text-muted-foreground">
              {ex.ripetizioni || "—"}
            </span>
          )}
          {showKg && (
            <span className="text-center tabular-nums text-muted-foreground">
              {ex.carico_kg ?? "—"}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SESSION SUB-COMPONENT
// ════════════════════════════════════════════════════════════

function SessionPreview({
  session,
}: {
  session: SessionCardData;
}) {
  const grouped = useMemo(() => groupBySection(session.esercizi), [session.esercizi]);

  return (
    <div className="workout-session print:pb-1">
      <div className="flex items-center gap-2 mb-2 print:mb-1">
        <span className="flex h-6 w-6 items-center justify-center rounded bg-primary/10 text-xs font-bold text-primary print:h-5 print:w-5 print:text-[10px]">
          {session.numero_sessione}
        </span>
        <h3 className="text-sm font-semibold print:text-[12px]">{session.nome_sessione}</h3>
        {session.focus_muscolare && (
          <span className="text-xs text-muted-foreground print:text-[10px]">
            — {session.focus_muscolare}
          </span>
        )}
      </div>

      {/* Note sessione */}
      {session.note && (
        <p className="text-[10px] text-muted-foreground italic mb-1.5 ml-8 print:mb-1 print:ml-6 print:text-[9px]">
          {session.note}
        </p>
      )}

      {SECTION_ORDER.map((sectionKey) => {
        const exercises = grouped[sectionKey];
        const isPrincipale = sectionKey === "principale";
        const hasBlocks = isPrincipale && session.blocchi.length > 0;
        if (exercises.length === 0 && !hasBlocks) return null;
        const config = SECTION_PREVIEW_CONFIG[sectionKey];
        const SectionIcon = config.icon;

        return (
          <div key={sectionKey} className="mb-2 print:mb-1">
            <div className="mb-1 flex items-center justify-between gap-2 print:mb-0.5">
              <p className={`inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider ${config.color} print:text-[9px]`}>
                <SectionIcon className="h-3.5 w-3.5" />
                {config.label}
              </p>
              <span className="text-[9px] text-muted-foreground print:text-[8px]">{config.description}</span>
            </div>

            {/* Esercizi straight */}
            {exercises.length > 0 && isPrincipale && (
              <div className="space-y-0">
                {exercises.map((ex, idx) => (
                  <PrimaryExerciseCard key={ex.id} ex={ex} idx={idx} />
                ))}
              </div>
            )}

            {exercises.length > 0 && !isPrincipale && (
              <>
                <div className="space-y-0 print:hidden">
                  {exercises.map((ex, idx) => (
                    <SectionExerciseCard
                      key={ex.id}
                      sectionKey={sectionKey as Exclude<TemplateSection, "principale">}
                      ex={ex}
                      idx={idx}
                    />
                  ))}
                </div>

                <table className="hidden print:table w-full text-[10px] border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-300 text-zinc-600">
                      <th className="py-0.5 text-left font-medium w-6">#</th>
                      <th className="py-0.5 text-left font-medium">Esercizio</th>
                      <th className="py-0.5 text-center font-medium w-10">Serie</th>
                      <th className="py-0.5 text-center font-medium w-12">Rip</th>
                      <th className="py-0.5 text-left font-medium w-24">Nota</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exercises.map((ex, idx) => (
                      <tr key={ex.id} className="border-b border-dashed border-zinc-200 last:border-0">
                        <td className="py-0.5 text-zinc-500">{idx + 1}</td>
                        <td className="py-0.5 font-medium">
                          {ex.esercizio_nome}
                          {ex.tempo_esecuzione && (
                            <span className="ml-1 text-[9px] text-zinc-500">
                              ({ex.tempo_esecuzione})
                            </span>
                          )}
                        </td>
                        <td className="py-0.5 text-center tabular-nums">{ex.serie}</td>
                        <td className="py-0.5 text-center tabular-nums">{ex.ripetizioni}</td>
                        <td className="py-0.5 text-zinc-500 truncate max-w-[120px]">{ex.note ?? ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}

            {/* Blocchi strutturati — solo in principale */}
            {isPrincipale && session.blocchi.length > 0 && (
              <div className="mt-1 space-y-0">
                {session.blocchi
                  .slice()
                  .sort((a, b) => a.ordine - b.ordine)
                  .map((block) => (
                    <BlockPreview key={block.id} block={block} />
                  ))}
              </div>
            )}
          </div>
        );
      })}

      {session.esercizi.length === 0 && session.blocchi.length === 0 && (
        <p className="py-4 text-center text-xs text-muted-foreground italic">
          Nessun esercizio
        </p>
      )}
    </div>
  );
}
