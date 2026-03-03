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
import { Badge } from "@/components/ui/badge";
import { getSectionForCategory, type TemplateSection } from "@/lib/workout-templates";
import { parseAvgReps, type SessionCardData } from "./SessionCard";
import { BLOCK_TYPE_LABELS, type WorkoutExerciseRow, type Exercise } from "@/types/api";

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
          {totalVolume != null && (
            <Badge variant="outline" className="text-xs tabular-nums">
              Vol. totale: {totalVolume.toLocaleString("it-IT")} kg
            </Badge>
          )}
        </div>
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
        <span>ProFit AI Studio</span>
        <span>{new Date().toLocaleDateString("it-IT")}</span>
      </div>
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

      {/* Note sessione */}
      {session.note && (
        <p className="text-[10px] text-muted-foreground italic mb-1.5 ml-8">
          {session.note}
        </p>
      )}

      {SECTION_ORDER.map((sectionKey) => {
        const exercises = grouped[sectionKey];
        const isPrincipale = sectionKey === "principale";
        const hasBlocks = isPrincipale && session.blocchi.length > 0;
        if (exercises.length === 0 && !hasBlocks) return null;
        const config = SECTION_PREVIEW_CONFIG[sectionKey];

        return (
          <div key={sectionKey} className="mb-2">
            <p className={`text-[10px] font-semibold uppercase tracking-wider mb-1 ${config.color}`}>
              {config.label}
            </p>

            {/* Esercizi straight */}
            {exercises.length > 0 && (
              <table className="w-full text-xs border-collapse">
                {isPrincipale && (
                  <thead>
                    <tr className="border-b text-muted-foreground">
                      <th className="py-1 text-left font-medium w-8">#</th>
                      <th className="py-1 text-left font-medium">Esercizio</th>
                      <th className="py-1 text-center font-medium w-12">Serie</th>
                      <th className="py-1 text-center font-medium w-14">Rip</th>
                      <th className="py-1 text-center font-medium w-12">Kg</th>
                      <th className="py-1 text-center font-medium w-14">Riposo</th>
                      <th className="py-1 text-left font-medium w-28">Note</th>
                    </tr>
                  </thead>
                )}
                <tbody>
                  {exercises.map((ex, idx) => {
                    return (
                      <tr key={ex.id} className="border-b border-dashed last:border-0">
                        <td className="py-1 text-muted-foreground">{idx + 1}</td>
                        <td className="py-1 font-medium">
                          {ex.esercizio_nome}
                          {ex.tempo_esecuzione && (
                            <span className="ml-1 text-[10px] text-muted-foreground font-normal">
                              ({ex.tempo_esecuzione})
                            </span>
                          )}
                        </td>
                        <td className="py-1 text-center tabular-nums">{ex.serie}</td>
                        <td className="py-1 text-center tabular-nums">{ex.ripetizioni}</td>
                        {isPrincipale && (
                          <>
                            <td className="py-1 text-center tabular-nums">
                              {ex.carico_kg != null ? ex.carico_kg : "—"}
                            </td>
                            <td className="py-1 text-center tabular-nums">{ex.tempo_riposo_sec}s</td>
                            <td className="py-1 text-muted-foreground truncate max-w-[120px]">
                              {ex.note ?? "—"}
                            </td>
                          </>
                        )}
                        {!isPrincipale && (
                          <td colSpan={2} className="py-1 text-muted-foreground truncate max-w-[120px]">
                            {ex.note ?? ""}
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}

            {/* Blocchi strutturati — solo in principale */}
            {isPrincipale && session.blocchi.length > 0 && (
              <div className="mt-1 space-y-1.5">
                {session.blocchi
                  .slice()
                  .sort((a, b) => a.ordine - b.ordine)
                  .map((block) => (
                    <div key={block.id} className="border-l-2 border-muted-foreground/30 pl-2">
                      {/* Header blocco */}
                      <div className="flex items-center gap-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">
                        <span>{BLOCK_TYPE_LABELS[block.tipo_blocco]}</span>
                        {block.giri > 0 && <span>× {block.giri}</span>}
                        {block.durata_lavoro_sec && <span>· {block.durata_lavoro_sec}s on</span>}
                        {block.durata_riposo_sec && <span>· {block.durata_riposo_sec}s off</span>}
                        {block.durata_blocco_sec && <span>· {Math.round(block.durata_blocco_sec / 60)}min</span>}
                        {block.nome && <span className="normal-case">— {block.nome}</span>}
                      </div>
                      {/* Esercizi nel blocco */}
                      {block.esercizi.map((ex, idx) => (
                        <div key={ex.id} className="flex items-center gap-1 text-[11px] py-0.5">
                          <span className="text-muted-foreground/60 tabular-nums w-4">{idx + 1}.</span>
                          <span className="font-medium truncate">{ex.esercizio_nome}</span>
                          {ex.note && <span className="ml-auto text-muted-foreground/60 text-[10px]">{ex.note}</span>}
                        </div>
                      ))}
                    </div>
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
