// src/components/workouts/WorkoutPreview.tsx
"use client";

/**
 * Preview professionale stampabile della scheda allenamento.
 *
 * V2: supporta commentary a blocchi (JSON) con rendering distribuito
 * per sessione. V1 fallback per commentary monolitico (markdown plain).
 */

import { useMemo, useState } from "react";
import { ChevronDown, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { getSectionForCategory, type TemplateSection } from "@/lib/workout-templates";
import { getMediaUrl } from "@/lib/media";
import type { SessionCardData } from "./SessionCard";
import type { WorkoutExerciseRow, Exercise } from "@/types/api";

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

const SECTION_PREVIEW_CONFIG: Record<TemplateSection, { label: string; color: string }> = {
  avviamento: { label: "Avviamento", color: "text-amber-600 dark:text-amber-400" },
  principale: { label: "Esercizio Principale", color: "text-primary" },
  stretching: { label: "Stretching & Mobilita", color: "text-cyan-600 dark:text-cyan-400" },
};

const SECTION_ORDER: TemplateSection[] = ["avviamento", "principale", "stretching"];

// ════════════════════════════════════════════════════════════
// COMMENTARY V2 — TYPES + PARSER
// ════════════════════════════════════════════════════════════

interface CommentaryBlockSession {
  type: "session";
  session_numero: number;
  session_nome: string;
  content: string;
  error?: string;
}

interface CommentaryBlockGeneric {
  type: "panoramica" | "consigli";
  content: string;
  error?: string;
}

type CommentaryBlock = CommentaryBlockSession | CommentaryBlockGeneric;

interface CommentaryV2 {
  version: 2;
  blocks: CommentaryBlock[];
}

type ParsedCommentary =
  | { version: 1; text: string }
  | CommentaryV2;

function parseCommentary(raw: string): ParsedCommentary {
  try {
    const parsed = JSON.parse(raw);
    if (parsed?.version === 2 && Array.isArray(parsed?.blocks)) {
      return parsed as CommentaryV2;
    }
  } catch {
    // Not JSON — v1 markdown
  }
  return { version: 1, text: raw };
}

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
  durata_settimane: number;
  sessioni_per_settimana: number;
  sessioni: SessionCardData[];
  note?: string | null;
  aiCommentary?: string | null;
  exerciseMap?: Map<number, Exercise>;
}

export function WorkoutPreview({
  nome,
  obiettivo,
  livello,
  clientNome,
  durata_settimane,
  sessioni_per_settimana,
  sessioni,
  note,
  aiCommentary,
  exerciseMap,
}: WorkoutPreviewProps) {
  const parsed = useMemo(
    () => (aiCommentary ? parseCommentary(aiCommentary) : null),
    [aiCommentary],
  );

  const isV2 = parsed?.version === 2;
  const v2 = isV2 ? (parsed as CommentaryV2) : null;

  // Pre-compute session blocks map for O(1) lookup
  const sessionBlockMap = useMemo(() => {
    if (!v2) return null;
    const map = new Map<number, CommentaryBlockSession>();
    for (const block of v2.blocks) {
      if (block.type === "session") {
        map.set((block as CommentaryBlockSession).session_numero, block as CommentaryBlockSession);
      }
    }
    return map;
  }, [v2]);

  const panoramicaBlock = v2?.blocks.find((b) => b.type === "panoramica");
  const consigliBlock = v2?.blocks.find((b) => b.type === "consigli");

  return (
    <div className="workout-preview bg-white text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 rounded-lg border p-6 space-y-6">
      {/* ── Header ── */}
      <div className="border-l-4 border-primary pl-4">
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
        </div>
      </div>

      {/* ── V2: Panoramica block ── */}
      {isV2 && panoramicaBlock && panoramicaBlock.content && (
        <CommentaryBlockWrapper title="Panoramica del Programma" defaultOpen>
          <CommentaryContent text={panoramicaBlock.content} />
        </CommentaryBlockWrapper>
      )}

      {/* ── Sessioni (con commentary inline per v2) ── */}
      {sessioni.map((session) => {
        const sessionBlock = sessionBlockMap?.get(session.numero_sessione);
        return (
          <div key={session.id}>
            <SessionPreview
              session={session}
              exerciseMap={exerciseMap}
            />
            {/* V2: session commentary dopo la tabella esercizi */}
            {isV2 && sessionBlock && sessionBlock.content && (
              <CommentaryBlockWrapper
                title={`Guida — ${session.nome_sessione}`}
                defaultOpen
              >
                <CommentaryContent text={sessionBlock.content} />
              </CommentaryBlockWrapper>
            )}
            {/* V2: session error placeholder */}
            {isV2 && sessionBlock && sessionBlock.error && !sessionBlock.content && (
              <div className="mt-2 rounded border border-amber-200 bg-amber-50 p-3 text-xs text-amber-700 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-400">
                Generazione guida sessione non riuscita: {sessionBlock.error}
              </div>
            )}
          </div>
        );
      })}

      {/* ── Note ── */}
      {note && (
        <div className="text-xs text-muted-foreground border-t pt-3">
          <p className="font-medium mb-1">Note:</p>
          <p>{note}</p>
        </div>
      )}

      {/* ── V2: Consigli block ── */}
      {isV2 && consigliBlock && consigliBlock.content && (
        <CommentaryBlockWrapper title="Consigli Generali" defaultOpen>
          <CommentaryContent text={consigliBlock.content} />
        </CommentaryBlockWrapper>
      )}

      {/* ── V1: AI Commentary monolitico (fallback) ── */}
      {!isV2 && aiCommentary && (
        <div className="ai-commentary border-t pt-4 space-y-3">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-bold text-primary">Guida alla Scheda</h3>
          </div>
          <CommentaryContent text={aiCommentary} />
        </div>
      )}

      {/* ── Footer ── */}
      <div className="flex items-center justify-between border-t pt-3 text-[10px] text-muted-foreground">
        <span>ProFit AI Studio</span>
        <span>{new Date().toLocaleDateString("it-IT")}</span>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// COMMENTARY BLOCK WRAPPER (Collapsible)
// ════════════════════════════════════════════════════════════

function CommentaryBlockWrapper({
  title,
  defaultOpen = true,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="mt-3">
      <CollapsibleTrigger className="flex w-full items-center gap-2 rounded-md border border-primary/20 bg-primary/5 px-3 py-2 text-left transition-colors hover:bg-primary/10">
        <Sparkles className="h-3.5 w-3.5 text-primary shrink-0" />
        <span className="text-xs font-semibold text-primary flex-1">{title}</span>
        <ChevronDown
          className={`h-3.5 w-3.5 text-primary/60 transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        />
      </CollapsibleTrigger>
      <CollapsibleContent className="pt-3 space-y-1.5">
        {children}
      </CollapsibleContent>
    </Collapsible>
  );
}

// ════════════════════════════════════════════════════════════
// COMMENTARY CONTENT RENDERER (markdown light parser)
// ════════════════════════════════════════════════════════════

function CommentaryContent({ text }: { text: string }) {
  const elements = useMemo(() => {
    const lines = text.split("\n");
    const result: React.ReactNode[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      if (!trimmed) continue;

      if (trimmed.startsWith("## ")) {
        result.push(
          <h3 key={i} className="text-sm font-bold text-primary border-b border-primary/20 pb-1 mt-4 first:mt-0">
            {formatInline(trimmed.slice(3))}
          </h3>,
        );
      } else if (trimmed.startsWith("### ")) {
        result.push(
          <h4 key={i} className="text-xs font-bold mt-3">
            {formatInline(trimmed.slice(4))}
          </h4>,
        );
      } else if (trimmed.startsWith("- ")) {
        result.push(
          <p key={i} className="text-xs text-muted-foreground pl-3 leading-relaxed">
            <span className="text-primary mr-1">&bull;</span>
            {formatInline(trimmed.slice(2))}
          </p>,
        );
      } else {
        result.push(
          <p key={i} className="text-xs text-muted-foreground leading-relaxed">
            {formatInline(trimmed)}
          </p>,
        );
      }
    }

    return result;
  }, [text]);

  return <div className="space-y-1.5">{elements}</div>;
}

/** Replace **bold** markers with <strong> */
function formatInline(text: string): React.ReactNode {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  if (parts.length === 1) return text;
  return parts.map((part, i) =>
    i % 2 === 1 ? <strong key={i} className="font-semibold text-foreground">{part}</strong> : part,
  );
}

// ════════════════════════════════════════════════════════════
// SESSION SUB-COMPONENT
// ════════════════════════════════════════════════════════════

function SessionPreview({
  session,
  exerciseMap,
}: {
  session: SessionCardData;
  exerciseMap?: Map<number, Exercise>;
}) {
  const grouped = useMemo(() => groupBySection(session.esercizi), [session.esercizi]);

  return (
    <div className="workout-session">
      <div className="flex items-center gap-2 mb-2">
        <span className="flex h-6 w-6 items-center justify-center rounded bg-primary/10 text-xs font-bold text-primary">
          {session.numero_sessione}
        </span>
        <h3 className="text-sm font-semibold">{session.nome_sessione}</h3>
        {session.focus_muscolare && (
          <span className="text-xs text-muted-foreground">
            — {session.focus_muscolare}
          </span>
        )}
      </div>

      {SECTION_ORDER.map((sectionKey) => {
        const exercises = grouped[sectionKey];
        if (exercises.length === 0) return null;
        const config = SECTION_PREVIEW_CONFIG[sectionKey];
        const showMuscleMap = sectionKey === "principale" && exerciseMap;

        return (
          <div key={sectionKey} className="mb-2">
            <p className={`text-[10px] font-semibold uppercase tracking-wider mb-1 ${config.color}`}>
              {config.label}
            </p>
            <table className="w-full text-xs border-collapse">
              {sectionKey === "principale" && (
                <thead>
                  <tr className="border-b text-muted-foreground">
                    <th className="py-1 text-left font-medium w-8">#</th>
                    {showMuscleMap && (
                      <th className="py-1 text-center font-medium w-12"></th>
                    )}
                    <th className="py-1 text-left font-medium">Esercizio</th>
                    <th className="py-1 text-center font-medium w-14">Serie</th>
                    <th className="py-1 text-center font-medium w-16">Rip</th>
                    <th className="py-1 text-center font-medium w-16">Riposo</th>
                    <th className="py-1 text-left font-medium w-24">Note</th>
                  </tr>
                </thead>
              )}
              <tbody>
                {exercises.map((ex, idx) => {
                  const fullExercise = exerciseMap?.get(ex.id_esercizio);
                  const muscleMapUrl = fullExercise?.muscle_map_url
                    ? getMediaUrl(fullExercise.muscle_map_url)
                    : null;

                  return (
                    <tr key={ex.id} className="border-b border-dashed last:border-0">
                      <td className="py-1 text-muted-foreground">{idx + 1}</td>
                      {showMuscleMap && (
                        <td className="py-1 text-center">
                          {muscleMapUrl ? (
                            <img
                              src={muscleMapUrl}
                              alt=""
                              className="inline-block h-10 w-auto opacity-80"
                              loading="lazy"
                            />
                          ) : (
                            <div className="inline-block h-10 w-5" />
                          )}
                        </td>
                      )}
                      <td className="py-1 font-medium">{ex.esercizio_nome}</td>
                      <td className="py-1 text-center tabular-nums">{ex.serie}</td>
                      <td className="py-1 text-center tabular-nums">{ex.ripetizioni}</td>
                      {sectionKey === "principale" && (
                        <>
                          <td className="py-1 text-center tabular-nums">{ex.tempo_riposo_sec}s</td>
                          <td className="py-1 text-muted-foreground truncate max-w-[100px]">
                            {ex.note ?? "—"}
                          </td>
                        </>
                      )}
                      {sectionKey !== "principale" && (
                        <td colSpan={2} className="py-1 text-muted-foreground truncate max-w-[100px]">
                          {ex.note ?? ""}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );
      })}

      {session.esercizi.length === 0 && (
        <p className="py-4 text-center text-xs text-muted-foreground italic">
          Nessun esercizio
        </p>
      )}
    </div>
  );
}
